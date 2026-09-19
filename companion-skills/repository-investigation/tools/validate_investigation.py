#!/usr/bin/env python3
"""Structurally validate one immutable repository-investigation artifact."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from iis_path_contract import (  # noqa: E402
    PathContractError,
    canonical_project_root,
    require_canonical_regular_file,
    require_work_slug,
)


REQUIRED_METADATA = (
    "Artifact-Type",
    "Format-Version",
    "Status",
    "Project-Root",
    "Repository-Root",
    "Investigation-Slug",
    "Investigation-Revision",
    "Observed-At",
    "Git-Branch",
    "Git-Head",
    "Working-Tree-Before-Artifact",
    "Evidence-Authority",
)

REQUIRED_SECTIONS = (
    "Evidence Handoff",
    "Investigation Charter",
    "Repository Binding",
    "Investigation Frontier",
    "Current System Model",
    "Verified Findings",
    "Inferences",
    "Alternate, Legacy And Bypass Paths",
    "Documentation, Tests And Runtime Alignment",
    "Absence Claims",
    "Contradictions And Surprises",
    "Coverage Boundary",
    "Completion",
)

REQUIRED_FRONTIER = (
    "FLOW_AND_READBACK",
    "STATE_AND_AUTHORITY",
    "ALTERNATE_PATHS",
    "EVIDENCE_ALIGNMENT",
)

FRONTIER_DISPOSITIONS = {"INVESTIGATE", "COVERED_BY_OTHER_LANE", "NOT_APPLICABLE"}
PLANNING_RELEVANCE = {
    "CURRENT_STATE",
    "PLANNING_CONSTRAINT_CANDIDATE",
    "PRODUCT_DEPENDENCY_CANDIDATE",
    "ACCEPTANCE_SURFACE_CANDIDATE",
    "DELIVERY_CONTEXT",
    "NONE",
}
FRESHNESS = {"ANCHOR_LOCAL", "SEARCH_UNIVERSE", "RUNTIME_STATE", "EXTERNAL_VERSION"}
ANCHOR_KINDS = {"SOURCE", "SEARCH", "TEST", "RUNTIME", "DOC"}
REVISION_PATTERN = re.compile(r"^INV-(\d{3})$")
ANCHOR_PATTERN = re.compile(
    r"^-\s+(A\d+)\s*\|\s*(SOURCE|SEARCH|TEST|RUNTIME|DOC)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*(ANCHOR_LOCAL|SEARCH_UNIVERSE|RUNTIME_STATE|EXTERNAL_VERSION)\s*$"
)
EVIDENCE_REFERENCE_PATTERN = re.compile(r"\b(Finding|Inference)\s+(\d+)\b")
TEMPLATE_PLACEHOLDERS = frozenset(
    {
        "<Title>",
        "<canonical absolute project root>",
        "<canonical absolute repository root>",
        "<lowercase-kebab-slug>",
        "<offset-aware ISO-8601 timestamp>",
        "<branch or detached>",
        "<commit sha>",
        "<concise answer to the exact investigation objective>",
        "<Finding/Inference ordinals>",
        "<directly observed current product/operator state>",
        "<trigger or inspection target>",
        "<surface>",
        "<actual product/canonical readback>",
        "<state/configuration/lifecycle/ownership fact>",
        "<path>",
        "<line/symbol>",
        "<fixed snapshot ref or native Git identity>",
        "<user request>",
        "<exact bounded question>",
        "<why the answer matters without importing a desired conclusion>",
        "<excluded surface, or exact None>",
        "<entry/component/state/config/test/runtime/doc surface>",
        "<question>",
        "<bounded result>",
        "<current evidence-grounded flow>",
        "<current evidence-grounded owners>",
        "<current precedence/registration/extension facts>",
        "<actual observable/canonical readback surfaces>",
        "<title>",
        "<directly observed fact>",
        "<counterpath/source checked>",
        "<bounded limitation or None>",
        "<path checked and result, or exact None>",
        "<alignment/contradiction finding, or exact None>",
        "<material contradiction/surprise, or exact None>",
        "<connected material surface>",
        "<surface, or exact None>",
        "<materiality explanation>",
    }
)


class ValidationError(RuntimeError):
    pass


def _metadata(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# ") or lines[0].startswith("## "):
        raise ValidationError("artifact must begin with one H1 title")

    first_h2 = next((i for i, line in enumerate(lines) if line.startswith("## ")), None)
    if first_h2 is None:
        raise ValidationError("artifact has no H2 sections")
    header = lines[1:first_h2]

    values: dict[str, str] = {}
    for key in REQUIRED_METADATA:
        matches = [line for line in header if line.startswith(f"{key}:")]
        if len(matches) != 1:
            raise ValidationError(f"metadata key must occur exactly once: {key}")
        value = matches[0].split(":", 1)[1].strip()
        if not value:
            raise ValidationError(f"metadata value must be non-empty: {key}")
        values[key] = value
    return values


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    matches = list(re.finditer(rf"^{re.escape(marker)}\s*$", text, re.MULTILINE))
    if len(matches) != 1:
        raise ValidationError(f"required H2 must occur exactly once: {heading}")
    start = matches[0].end()
    next_h2 = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_h2.start() if next_h2 else len(text)
    return text[start:end].strip()


def _subsection(section: str, heading: str) -> str:
    marker = f"### {heading}"
    matches = list(re.finditer(rf"^{re.escape(marker)}\s*$", section, re.MULTILINE))
    if len(matches) != 1:
        raise ValidationError(f"required H3 must occur exactly once: {heading}")
    start = matches[0].end()
    next_h3 = re.search(r"^###\s+", section[start:], re.MULTILINE)
    end = start + next_h3.start() if next_h3 else len(section)
    return section[start:end].strip()


def _field(block: str, key: str) -> str:
    matches = re.findall(rf"^{re.escape(key)}:\s*(.+?)\s*$", block, re.MULTILINE)
    if len(matches) != 1:
        raise ValidationError(f"field must occur exactly once: {key}")
    value = matches[0].strip()
    if not value:
        raise ValidationError(f"field value must be non-empty: {key}")
    return value


def _validate_path(path: Path, meta: dict[str, str]) -> None:
    try:
        artifact = require_canonical_regular_file(path)
        project = canonical_project_root(meta["Project-Root"], writable=False)
        repository = canonical_project_root(meta["Repository-Root"], writable=False)
        require_work_slug(meta["Investigation-Slug"])
    except PathContractError as exc:
        raise ValidationError(str(exc)) from exc

    if project != repository and repository not in project.parents:
        raise ValidationError("Project-Root must equal or be contained by Repository-Root")

    revision = meta["Investigation-Revision"]
    if REVISION_PATTERN.fullmatch(revision) is None:
        raise ValidationError("Investigation-Revision must be exact INV-NNN")
    expected = project / "docs" / "investigation" / meta["Investigation-Slug"] / f"{revision}.md"
    if artifact != expected:
        raise ValidationError(f"artifact path must be exact canonical investigation path: {expected}")


def _validate_metadata(meta: dict[str, str]) -> None:
    if meta["Artifact-Type"] != "repository-investigation":
        raise ValidationError("Artifact-Type must be repository-investigation")
    if meta["Format-Version"] != "1":
        raise ValidationError("Format-Version must be 1")
    if meta["Status"] not in {"complete", "partial", "blocked"}:
        raise ValidationError("Status must be complete, partial, or blocked")
    if meta["Working-Tree-Before-Artifact"] not in {"clean", "dirty"}:
        raise ValidationError("Working-Tree-Before-Artifact must be clean or dirty")
    if meta["Evidence-Authority"] != "repository evidence only; not IIS planning authority":
        raise ValidationError("Evidence-Authority must preserve the exact evidence-only boundary")

    try:
        observed = datetime.fromisoformat(meta["Observed-At"])
    except ValueError as exc:
        raise ValidationError("Observed-At must be ISO-8601") from exc
    if observed.tzinfo is None:
        raise ValidationError("Observed-At must be offset-aware")


def _validate_template_placeholders(text: str, *, status: str) -> None:
    if status not in {"complete", "partial"}:
        return
    remaining = sorted(token for token in TEMPLATE_PLACEHOLDERS if token in text)
    if remaining:
        raise ValidationError(
            "complete/partial artifact must not contain template placeholders: " + ", ".join(remaining)
        )


def _validate_frontier(section: str) -> None:
    rows: dict[str, tuple[str, str]] = {}
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("| ---") or stripped.startswith("| Area"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 4:
            continue
        area, question, disposition, result = cells
        if area in REQUIRED_FRONTIER:
            if area in rows:
                raise ValidationError(f"frontier area occurs more than once: {area}")
            rows[area] = (question, disposition)
            if not question or not result:
                raise ValidationError(f"frontier row must have question and result: {area}")
            if disposition not in FRONTIER_DISPOSITIONS:
                raise ValidationError(f"invalid frontier disposition for {area}: {disposition}")
    missing = [area for area in REQUIRED_FRONTIER if area not in rows]
    if missing:
        raise ValidationError(f"missing required frontier areas: {', '.join(missing)}")


def _validate_anchors(handoff: str, *, required: bool) -> set[str]:
    anchors = _subsection(handoff, "Load-Bearing Anchors")
    ids: set[str] = set()
    for line in anchors.splitlines():
        if not line.strip():
            continue
        match = ANCHOR_PATTERN.fullmatch(line.strip())
        if match is None:
            raise ValidationError(f"invalid load-bearing anchor: {line.strip()}")
        anchor_id, kind, target, detail, identity, freshness = match.groups()
        if anchor_id in ids:
            raise ValidationError(f"duplicate anchor id: {anchor_id}")
        if kind not in ANCHOR_KINDS or freshness not in FRESHNESS:
            raise ValidationError(f"invalid anchor kind/freshness: {anchor_id}")
        if not target.strip() or not detail.strip() or not identity.strip():
            raise ValidationError(f"anchor fields must be non-empty: {anchor_id}")
        ids.add(anchor_id)
    if required and not ids:
        raise ValidationError("complete/partial artifact requires at least one load-bearing anchor")
    return ids


def _validate_findings(section: str, anchors: set[str], *, required: bool) -> set[int]:
    pattern = re.compile(
        r"^### Finding (\d+) — .+?\n\n(.*?)(?=^### Finding \d+ — |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(section))
    if required and not matches:
        raise ValidationError("complete/partial artifact requires at least one verified Finding")

    ordinals: set[int] = set()
    for match in matches:
        ordinal = int(match.group(1))
        block = match.group(2)
        if ordinal in ordinals:
            raise ValidationError(f"duplicate Finding ordinal: {ordinal}")
        ordinals.add(ordinal)
        if _field(block, "Classification") != "FACT":
            raise ValidationError(f"Finding {ordinal} Classification must be FACT")
        _field(block, "Statement")
        evidence = _field(block, "Primary Evidence")
        evidence_ids = {item.strip() for item in evidence.split(",") if item.strip()}
        if not evidence_ids or not evidence_ids.issubset(anchors):
            raise ValidationError(f"Finding {ordinal} Primary Evidence must reference defined anchors")
        counter = _field(block, "Counterevidence Checked")
        if counter == "None":
            raise ValidationError(f"Finding {ordinal} must record a counterpath/source or boundary condition")
        _field(block, "Boundary / Limitation")
        relevance = _field(block, "Planning Relevance Candidate")
        if relevance not in PLANNING_RELEVANCE:
            raise ValidationError(f"Finding {ordinal} has invalid Planning Relevance Candidate")
        freshness = _field(block, "Freshness Sensitivity")
        if freshness not in FRESHNESS:
            raise ValidationError(f"Finding {ordinal} has invalid Freshness Sensitivity")
    return ordinals


def _validate_inferences(section: str, findings: set[int]) -> set[int]:
    if section.strip() == "None":
        return set()
    pattern = re.compile(
        r"^### Inference (\d+) — .+?\n\n(.*?)(?=^### Inference \d+ — |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(section))
    if not matches:
        raise ValidationError("Inferences must be exact None or structured Inference blocks")
    seen: set[int] = set()
    for match in matches:
        ordinal = int(match.group(1))
        block = match.group(2)
        if ordinal in seen:
            raise ValidationError(f"duplicate Inference ordinal: {ordinal}")
        seen.add(ordinal)
        _field(block, "Statement")
        supported = _field(block, "Supported By")
        references = {int(value) for value in re.findall(r"Finding\s+(\d+)", supported)}
        if not references or not references.issubset(findings):
            raise ValidationError(f"Inference {ordinal} must reference existing Findings")
        if _field(block, "Plausible Alternative") == "None":
            raise ValidationError(f"Inference {ordinal} requires a plausible alternative")
        _field(block, "Evidence Needed To Disprove")
        relevance = _field(block, "Planning Relevance Candidate")
        if relevance not in PLANNING_RELEVANCE:
            raise ValidationError(f"Inference {ordinal} has invalid Planning Relevance Candidate")
    return seen


def _validate_evidence_reference_value(
    value: str,
    findings: set[int],
    inferences: set[int],
    *,
    context: str,
) -> None:
    references = [(kind, int(number)) for kind, number in EVIDENCE_REFERENCE_PATTERN.findall(value)]
    if not references:
        raise ValidationError(f"{context} must reference at least one Finding or Inference")
    for kind, ordinal in references:
        defined = findings if kind == "Finding" else inferences
        if ordinal not in defined:
            raise ValidationError(f"{context} references undefined {kind} {ordinal}")


def _handoff_list_blocks(section: str, *, heading: str) -> list[str]:
    if section.strip() == "- None":
        return []
    blocks = [match.group(0).strip() for match in re.finditer(r"(?ms)^- .+?(?=^- |\Z)", section.strip())]
    if not blocks:
        raise ValidationError(f"{heading} must be exact - None or structured list entries")
    return blocks


def _indented_field(block: str, key: str) -> str:
    matches = re.findall(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", block, re.MULTILINE)
    if len(matches) != 1:
        raise ValidationError(f"field must occur exactly once: {key}")
    value = matches[0].strip()
    if not value:
        raise ValidationError(f"field value must be non-empty: {key}")
    return value


def _validate_handoff_references(handoff: str, findings: set[int], inferences: set[int]) -> None:
    for kind, number in EVIDENCE_REFERENCE_PATTERN.findall(handoff):
        ordinal = int(number)
        defined = findings if kind == "Finding" else inferences
        if ordinal not in defined:
            raise ValidationError(f"Evidence Handoff references undefined {kind} {ordinal}")

    answer = _subsection(handoff, "Investigation Answer")
    _field(answer, "Answer")
    _validate_evidence_reference_value(
        _field(answer, "Based On"),
        findings,
        inferences,
        context="Investigation Answer Based On",
    )

    for heading in (
        "Observed Current Product State",
        "Existing Product Surfaces And Readbacks",
        "State And Authority",
        "Planning Constraint Candidates",
        "Product Dependency Candidates",
    ):
        section = _subsection(handoff, heading)
        for index, block in enumerate(_handoff_list_blocks(section, heading=heading), start=1):
            supporting = _indented_field(block, "Supporting Findings")
            _validate_evidence_reference_value(
                supporting,
                findings,
                inferences,
                context=f"{heading} entry {index} Supporting Findings",
            )


def _validate_absence_claims(section: str) -> None:
    if section.strip() == "None":
        return
    pattern = re.compile(
        r"^### Absence Claim (\d+)\s*$\n\n(.*?)(?=^### Absence Claim \d+\s*$|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(section))
    if not matches:
        raise ValidationError("Absence Claims must be exact None or structured claim blocks")
    for match in matches:
        block = match.group(2)
        _field(block, "Claim")
        _field(block, "Search Universe")
        _field(block, "Method")
        _field(block, "Result")
        _field(block, "Boundary")


def validate(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"cannot read artifact: {exc}") from exc

    meta = _metadata(text)
    _validate_metadata(meta)
    _validate_template_placeholders(text, status=meta["Status"])
    _validate_path(path, meta)

    for heading in REQUIRED_SECTIONS:
        _section(text, heading)

    handoff = _section(text, "Evidence Handoff")
    for heading in (
        "Investigation Answer",
        "Observed Current Product State",
        "Existing Product Surfaces And Readbacks",
        "State And Authority",
        "Planning Constraint Candidates",
        "Product Dependency Candidates",
        "Material Unknowns",
        "Load-Bearing Anchors",
    ):
        _subsection(handoff, heading)

    status = meta["Status"]
    required_evidence = status in {"complete", "partial"}
    anchors = _validate_anchors(handoff, required=required_evidence)
    findings = _validate_findings(_section(text, "Verified Findings"), anchors, required=required_evidence)
    inferences = _validate_inferences(_section(text, "Inferences"), findings)
    if required_evidence:
        _validate_handoff_references(handoff, findings, inferences)
    _validate_absence_claims(_section(text, "Absence Claims"))
    _validate_frontier(_section(text, "Investigation Frontier"))

    coverage = _section(text, "Coverage Boundary")
    for label in ("Inspected:", "Not Inspected:", "Why Current Coverage Is Sufficient Or Insufficient:"):
        if label not in coverage:
            raise ValidationError(f"Coverage Boundary missing: {label}")

    completion = _section(text, "Completion")
    completion_value = _field(completion, "Investigation Completion")
    expected_completion = status.upper()
    if completion_value != expected_completion:
        raise ValidationError("Status and Investigation Completion must match")
    unknowns = _field(completion, "Decision-Critical Unknowns")
    handoff_unknowns = _subsection(handoff, "Material Unknowns").strip()
    if status == "complete":
        if unknowns != "None" or handoff_unknowns != "- None":
            raise ValidationError("complete artifact requires no decision-critical/material unknowns")
    elif status == "partial":
        if unknowns == "None" or handoff_unknowns == "- None":
            raise ValidationError("partial artifact must identify remaining decision-critical/material unknowns")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    try:
        validate(args.artifact)
    except (OSError, ValidationError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
