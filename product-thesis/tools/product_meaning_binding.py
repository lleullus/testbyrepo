#!/usr/bin/env python3
"""Mechanical Product Meaning Binding validation.

This module deliberately validates only serialization, fingerprint consistency,
and exact source/target preservation. It does not judge Product Thesis quality or
semantic fidelity between a thesis/binding or binding/Spec prose.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


SCHEMA = "iis-product-meaning/v1"
SOURCE_SCHEMA = "iis-product-meaning/v2"
SECTION = "Product Meaning Binding"
FINGERPRINT_RE = re.compile(r"sha256:([0-9a-f]{64})\Z")
SCOPE_INCREMENT_RE = re.compile(
    r"docs/planning/scope-shaping/([a-z0-9](?:[a-z0-9-]*[a-z0-9])?)/increments/(INC-\d{3})\.md\Z"
)
SCOPE_REVISION_REF_RE = re.compile(r"\.\./revisions/(SHAPE-\d{3})\.md\Z")

FIELD_ORDER = (
    "Core Utility",
    "Core Completion Loop",
    "Required Outcomes / Means",
    "Truth / Causal Invariants",
    "Success Observation",
)


class ProductMeaningBindingError(ValueError):
    pass


@dataclass(frozen=True)
class ProductMeaningBinding:
    schema: str
    fingerprint: str
    core_utility: str
    core_completion_loop: str
    required_outcomes_means: tuple[str, ...]
    truth_causal_invariants: tuple[str, ...]
    success_observation: str

    def canonical_payload(self) -> str:
        return canonical_payload(self)

    def computed_fingerprint(self) -> str:
        digest = hashlib.sha256(self.canonical_payload().encode("utf-8")).hexdigest()
        return f"sha256:{digest}"


@dataclass(frozen=True)
class ProductMeaningSource:
    schema: str
    fingerprint: str
    source: str

    def computed_fingerprint(self) -> str:
        path = Path(self.source)
        if not path.is_absolute():
            raise ProductMeaningBindingError("Source must be an exact absolute path")
        path = _require_regular_non_symlink(path, "Product Thesis source")
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except OSError as exc:
            raise ProductMeaningBindingError(f"Product Thesis source is not readable: {path}") from exc
        except UnicodeError as exc:
            raise ProductMeaningBindingError("Product Thesis source must be UTF-8") from exc
        if not text.strip():
            raise ProductMeaningBindingError("Product Thesis source must not be empty")
        return "sha256:" + hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class SpecBindingValidation:
    spec_path: Path
    mode: str
    source_revision: Path | None
    binding: ProductMeaningBinding | ProductMeaningSource


def _newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def normalize_scalar(value: str) -> str:
    """Canonicalize one scalar without semantic or internal-whitespace folding."""
    value = unicodedata.normalize("NFC", _newlines(value))
    lines = [line.rstrip(" \t") for line in value.split("\n")]
    while lines and not lines[0].strip(" \t"):
        lines.pop(0)
    while lines and not lines[-1].strip(" \t"):
        lines.pop()
    if not lines:
        return ""
    return "\n".join(lines).strip(" \t")


def _normalize_list(block: str, field: str) -> tuple[str, ...]:
    normalized = normalize_scalar(block)
    if normalized == "None":
        return ()
    if not normalized:
        raise ProductMeaningBindingError(f"{field} must be top-level list items or exact None")
    items: list[str] = []
    for line in normalized.split("\n"):
        if not line.startswith("- "):
            raise ProductMeaningBindingError(f"{field} must be top-level list items or exact None")
        item = normalize_scalar(line[2:])
        if not item:
            raise ProductMeaningBindingError(f"{field} contains an empty list item")
        items.append(item)
    return tuple(items)


def _render_list(items: tuple[str, ...]) -> str:
    return "None" if not items else "\n".join(f"- {item}" for item in items)


def _extract_section(text: str) -> str:
    text = _newlines(text)
    marker = f"## {SECTION}"
    matches = list(re.finditer(rf"(?m)^{re.escape(marker)}[ \t]*$", text))
    if len(matches) != 1:
        raise ProductMeaningBindingError(f"expected exactly one section: {marker}")
    match = matches[0]
    start = match.end()
    next_heading = re.search(r"(?m)^#{1,2}\s+", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip("\n")


def _metadata(block: str, key: str) -> str:
    matches = re.findall(rf"(?m)^{re.escape(key)}:[ \t]*(.+?)[ \t]*$", block)
    if len(matches) != 1:
        raise ProductMeaningBindingError(f"expected exactly one {key} line in Product Meaning Binding")
    return matches[0].strip()


def _parse_field_blocks(section: str) -> dict[str, str]:
    positions: list[tuple[str, int, int]] = []
    for field in FIELD_ORDER:
        matches = list(re.finditer(rf"(?m)^{re.escape(field)}:[ \t]*$", section))
        if len(matches) != 1:
            raise ProductMeaningBindingError(f"expected exactly one {field} field")
        match = matches[0]
        positions.append((field, match.start(), match.end()))
    if [field for field, _, _ in sorted(positions, key=lambda item: item[1])] != list(FIELD_ORDER):
        raise ProductMeaningBindingError("Product Meaning Binding fields must use the canonical field order")

    preamble = section[: positions[0][1]]
    schema = _metadata(preamble, "Schema")
    fingerprint = _metadata(preamble, "Fingerprint")
    allowed_preamble = re.sub(r"(?m)^(?:Schema|Fingerprint):[^\n]*$", "", preamble)
    if allowed_preamble.strip():
        raise ProductMeaningBindingError("unexpected content before Product Meaning Binding fields")
    if schema != SCHEMA:
        raise ProductMeaningBindingError(f"Schema must be exactly {SCHEMA}")
    if FINGERPRINT_RE.fullmatch(fingerprint) is None:
        raise ProductMeaningBindingError("Fingerprint must be sha256:<64 lowercase hex>")

    result: dict[str, str] = {"Schema": schema, "Fingerprint": fingerprint}
    for index, (field, _start, end) in enumerate(positions):
        next_start = positions[index + 1][1] if index + 1 < len(positions) else len(section)
        result[field] = section[end:next_start]
    return result


def parse_binding(text: str, *, verify_fingerprint: bool = True) -> ProductMeaningBinding | ProductMeaningSource:
    section = _extract_section(text)
    if _metadata(section, "Schema") == SOURCE_SCHEMA:
        source = ProductMeaningSource(SOURCE_SCHEMA, _metadata(section, "Fingerprint"), _metadata(section, "Source"))
        if re.sub(r"(?m)^(?:Schema|Fingerprint|Source):[^\n]*$", "", section).strip():
            raise ProductMeaningBindingError("unexpected content in source binding")
        if not FINGERPRINT_RE.fullmatch(source.fingerprint):
            raise ProductMeaningBindingError("Fingerprint must be sha256:<64 lowercase hex>")
        if verify_fingerprint and source.fingerprint != source.computed_fingerprint():
            raise ProductMeaningBindingError("stale Product Meaning Binding fingerprint: source bytes changed")
        return source
    raw = _parse_field_blocks(section)
    core_utility = normalize_scalar(raw["Core Utility"])
    core_completion_loop = normalize_scalar(raw["Core Completion Loop"])
    success_observation = normalize_scalar(raw["Success Observation"])
    for field, value in (
        ("Core Utility", core_utility),
        ("Core Completion Loop", core_completion_loop),
        ("Success Observation", success_observation),
    ):
        if not value:
            raise ProductMeaningBindingError(f"{field} must not be empty")

    binding = ProductMeaningBinding(
        schema=raw["Schema"],
        fingerprint=raw["Fingerprint"],
        core_utility=core_utility,
        core_completion_loop=core_completion_loop,
        required_outcomes_means=_normalize_list(raw["Required Outcomes / Means"], "Required Outcomes / Means"),
        truth_causal_invariants=_normalize_list(raw["Truth / Causal Invariants"], "Truth / Causal Invariants"),
        success_observation=success_observation,
    )
    if verify_fingerprint and binding.fingerprint != binding.computed_fingerprint():
        raise ProductMeaningBindingError(
            f"stale Product Meaning Binding fingerprint: recorded {binding.fingerprint}, "
            f"computed {binding.computed_fingerprint()}"
        )
    return binding


def canonical_payload(binding: ProductMeaningBinding) -> str:
    parts = [
        f"Schema: {SCHEMA}",
        "Core Utility:", binding.core_utility,
        "Core Completion Loop:", binding.core_completion_loop,
        "Required Outcomes / Means:", _render_list(binding.required_outcomes_means),
        "Truth / Causal Invariants:", _render_list(binding.truth_causal_invariants),
        "Success Observation:", binding.success_observation,
    ]
    return "\n".join(parts) + "\n"


def stamp_fingerprint(text: str) -> str:
    binding = parse_binding(text, verify_fingerprint=False)
    computed = binding.computed_fingerprint()
    section = _extract_section(text)
    old = _metadata(section, "Fingerprint")
    pattern = rf"(?m)^Fingerprint:[ \t]*{re.escape(old)}[ \t]*$"
    stamped, count = re.subn(pattern, f"Fingerprint: {computed}", _newlines(text), count=1)
    if count != 1:
        raise ProductMeaningBindingError("could not replace Product Meaning Binding fingerprint")
    return stamped


def binding_differences(source: ProductMeaningBinding | ProductMeaningSource, target: ProductMeaningBinding | ProductMeaningSource) -> tuple[str, ...]:
    if source.schema != target.schema:
        return ("Schema",)
    if isinstance(source, ProductMeaningSource) and isinstance(target, ProductMeaningSource):
        return () if source.source == target.source else ("Source",)
    pairs = (
        ("Core Utility", source.core_utility, target.core_utility),
        ("Core Completion Loop", source.core_completion_loop, target.core_completion_loop),
        ("Required Outcomes / Means", source.required_outcomes_means, target.required_outcomes_means),
        ("Truth / Causal Invariants", source.truth_causal_invariants, target.truth_causal_invariants),
        ("Success Observation", source.success_observation, target.success_observation),
    )
    return tuple(label for label, source_value, target_value in pairs if source_value != target_value)


def compare_binding_texts(source_text: str, target_text: str) -> None:
    source = parse_binding(source_text)
    target = parse_binding(target_text)
    differences = binding_differences(source, target)
    if differences:
        raise ProductMeaningBindingError("Product Meaning Binding mismatch in: " + ", ".join(differences))
    if source.fingerprint != target.fingerprint:
        raise ProductMeaningBindingError("Product Meaning Binding fingerprint mismatch")


def _require_regular_non_symlink(path: Path, context: str) -> Path:
    if path.is_symlink():
        raise ProductMeaningBindingError(f"{context} must not be a symlink: {path}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ProductMeaningBindingError(f"{context} is not readable: {path}") from exc
    if not resolved.is_file():
        raise ProductMeaningBindingError(f"{context} must be a regular file: {path}")
    if resolved != path.absolute():
        raise ProductMeaningBindingError(f"{context} must use its canonical path: {path}")
    return resolved


def _project_root_from_spec(spec_path: Path) -> Path:
    spec_path = _require_regular_non_symlink(spec_path, "SPEC.md")
    if spec_path.name != "SPEC.md":
        raise ProductMeaningBindingError("Spec path must end in SPEC.md")
    parents = spec_path.parents
    if len(parents) < 5 or parents[1].name != "work" or parents[2].name != "planning" or parents[3].name != "docs":
        raise ProductMeaningBindingError("Spec must be under <Project-Root>/docs/planning/work/<work-slug>/SPEC.md")
    return parents[4]


def _artifact_metadata(text: str, key: str) -> str:
    matches = re.findall(rf"(?m)^{re.escape(key)}:[ \t]*(.+?)[ \t]*$", _newlines(text))
    if len(matches) != 1:
        raise ProductMeaningBindingError(f"expected exactly one {key} metadata line")
    return matches[0].strip()


def validate_spec_binding(spec_path: Path) -> SpecBindingValidation:
    spec_path = _require_regular_non_symlink(spec_path.expanduser(), "SPEC.md")
    project_root = _project_root_from_spec(spec_path)
    spec_text = spec_path.read_text(encoding="utf-8")
    target = parse_binding(spec_text)
    source_ref = _artifact_metadata(spec_text, "Source-Increment")
    if source_ref == "None":
        return SpecBindingValidation(spec_path, "direct", None, target)

    posix_ref = PurePosixPath(source_ref)
    if posix_ref.is_absolute() or ".." in posix_ref.parts or "." in posix_ref.parts:
        raise ProductMeaningBindingError("Source-Increment must be one canonical project-relative path")
    match = SCOPE_INCREMENT_RE.fullmatch(source_ref)
    if match is None:
        raise ProductMeaningBindingError(
            "Source-Increment must be docs/planning/scope-shaping/<slug>/increments/INC-NNN.md"
        )
    scope_slug, increment_id = match.groups()
    increment_path = _require_regular_non_symlink(project_root / posix_ref, "Source-Increment")
    if increment_path.name != f"{increment_id}.md" or increment_path.parent.parent.name != scope_slug:
        raise ProductMeaningBindingError("Source-Increment path identity drift")

    increment_text = increment_path.read_text(encoding="utf-8")
    if _artifact_metadata(increment_text, "Project-Root") != str(project_root):
        raise ProductMeaningBindingError("Source-Increment Project-Root drift")
    if _artifact_metadata(increment_text, "Increment") != increment_id:
        raise ProductMeaningBindingError("Source-Increment Increment identity drift")
    revision_ref = _artifact_metadata(increment_text, "Source-Scope-Revision")
    revision_match = SCOPE_REVISION_REF_RE.fullmatch(revision_ref)
    if revision_match is None:
        raise ProductMeaningBindingError("Source-Increment has invalid Source-Scope-Revision")

    revision_id = revision_match.group(1)
    expected_revision_parent = increment_path.parent.parent / "revisions"
    if expected_revision_parent.is_symlink():
        raise ProductMeaningBindingError("Source-Scope-Revision directory must not be a symlink")
    try:
        resolved_revision_parent = expected_revision_parent.resolve(strict=True)
    except OSError as exc:
        raise ProductMeaningBindingError("Source-Scope-Revision directory is not readable") from exc
    if not resolved_revision_parent.is_dir() or resolved_revision_parent != expected_revision_parent.absolute():
        raise ProductMeaningBindingError("Source-Scope-Revision directory must be canonical")
    revision_path = _require_regular_non_symlink(
        resolved_revision_parent / f"{revision_id}.md",
        "Source-Scope-Revision",
    )
    revision_text = revision_path.read_text(encoding="utf-8")
    if _artifact_metadata(revision_text, "Scope-Revision") != revision_id:
        raise ProductMeaningBindingError("Source-Scope-Revision identity drift")
    if _artifact_metadata(revision_text, "Project-Root") != str(project_root):
        raise ProductMeaningBindingError("Source-Scope-Revision Project-Root drift")
    if _artifact_metadata(revision_text, "Work-Slug") != scope_slug:
        raise ProductMeaningBindingError("Source-Scope-Revision Work-Slug drift")
    if _artifact_metadata(revision_text, "Status") != "confirmed":
        raise ProductMeaningBindingError("Source-Scope-Revision Status must be confirmed")

    source = parse_binding(revision_text)
    differences = binding_differences(source, target)
    if differences:
        raise ProductMeaningBindingError("Product Meaning Binding mismatch in: " + ", ".join(differences))
    if source.fingerprint != target.fingerprint:
        raise ProductMeaningBindingError("Product Meaning Binding fingerprint mismatch")
    return SpecBindingValidation(spec_path, "scope", revision_path, target)


def _main_validate(path: Path) -> None:
    parse_binding(_require_regular_non_symlink(path.expanduser(), "artifact").read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("artifact", type=Path)
    fingerprint_parser = subparsers.add_parser("fingerprint")
    fingerprint_parser.add_argument("artifact", type=Path)
    spec_parser = subparsers.add_parser("validate-spec")
    spec_parser.add_argument("spec", type=Path)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("source", type=Path)
    compare_parser.add_argument("target", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            _main_validate(args.artifact)
        elif args.command == "fingerprint":
            artifact = _require_regular_non_symlink(args.artifact.expanduser(), "artifact")
            draft_binding = parse_binding(artifact.read_text(encoding="utf-8"), verify_fingerprint=False)
            print(draft_binding.computed_fingerprint())
            return 0
        elif args.command == "validate-spec":
            result = validate_spec_binding(args.spec)
            if result.source_revision is None:
                print("VALID: direct Product Meaning Binding")
                return 0
            print(f"VALID: Product Meaning Binding matches {result.source_revision}")
            return 0
        elif args.command == "compare":
            source = _require_regular_non_symlink(args.source.expanduser(), "source artifact")
            target = _require_regular_non_symlink(args.target.expanduser(), "target artifact")
            compare_binding_texts(source.read_text(encoding="utf-8"), target.read_text(encoding="utf-8"))
        else:  # pragma: no cover
            raise AssertionError(args.command)
    except (OSError, ProductMeaningBindingError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
