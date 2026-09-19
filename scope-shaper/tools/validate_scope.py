#!/usr/bin/env python3
"""Validate hashless iis-scope/v2 structure. Semantic closure is a separate admission check."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from iis_artifacts.refs import RefError, validate_ref
from iis_path_contract import PathContractError, canonical_project_root, require_canonical_regular_file, require_work_slug


class ScopeValidationError(ValueError):
    pass


def sections(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    current: str | None = None
    body: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("~~~") or line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            if current is not None:
                result[current] = "\n".join(body).strip()
            current = line[3:].strip()
            if current in result:
                raise ScopeValidationError(f"duplicate section: {current}")
            body = []
        elif current is not None:
            body.append(line)
    if current is not None:
        if current in result:
            raise ScopeValidationError(f"duplicate section: {current}")
        result[current] = "\n".join(body).strip()
    return result


def metadata(text: str, name: str) -> str:
    header = text.split("\n## ", 1)[0]
    values = re.findall(rf"^{re.escape(name)}: (.+)$", header, re.MULTILINE)
    if len(values) != 1:
        raise ScopeValidationError(f"exactly one {name} is required in top metadata")
    return values[0].strip()


def source_refs(body: str, label: str) -> list[dict[str, str]]:
    blocks = re.findall(r"^```iis-sources\s*\n(.*?)^```\s*$", body, re.M | re.S)
    if len(blocks) != 1:
        raise ScopeValidationError(f"{label} requires one iis-sources JSON block")
    try:
        value = json.loads(blocks[0])
    except json.JSONDecodeError as exc:
        raise ScopeValidationError(f"invalid {label} JSON") from exc
    if not isinstance(value, list) or not value:
        raise ScopeValidationError(f"{label} needs at least one source reference")
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in value:
        try:
            ref = validate_ref(item)
        except RefError as exc:
            raise ScopeValidationError(f"invalid {label} source reference: {exc}") from exc
        key = (ref["snapshot"], ref["path"])
        if key in seen:
            raise ScopeValidationError(f"duplicate {label} source reference")
        seen.add(key)
        result.append(ref)
    return result


def validate_text(text: str, logical_path: str, *, live_scope: Path | None = None) -> dict:
    if metadata(text, "Schema") != "iis-scope/v2":
        raise ScopeValidationError("unsupported Scope schema; current admission requires iis-scope/v2")
    root = canonical_project_root(metadata(text, "Project-Root"), writable=False)
    expected = Path(logical_path)
    if expected.is_absolute():
        try:
            expected = expected.relative_to(root)
        except ValueError as exc:
            raise ScopeValidationError("Scope path is outside Project-Root") from exc
    if len(expected.parts) != 5 or expected.parts[:3] != ("docs", "planning", "work") or expected.name != "SCOPE.md":
        raise ScopeValidationError("Scope must be docs/planning/work/<slug>/SCOPE.md")
    require_work_slug(expected.parts[3])
    if live_scope is not None and live_scope != root / expected:
        raise ScopeValidationError("Scope path does not match declared Project-Root")
    status = metadata(text, "Status")
    if status not in {"draft", "ready", "done", "superseded"}:
        raise ScopeValidationError("invalid Scope status")
    content = sections(text)
    for name in ("Outcome", "Acceptance", "Product Authority"):
        if not content.get(name):
            raise ScopeValidationError(f"missing nonempty section: {name}")
    if status in {"ready", "done"} and content.get("Open Decisions", "None") != "None":
        raise ScopeValidationError("ready/done Scope has unresolved product decisions")
    product = source_refs(content["Product Authority"], "Product Authority")
    transition = source_refs(content["Transition Authority"], "Transition Authority") if "Transition Authority" in content else []
    if any(not item["path"].startswith("docs/planning/product-thesis/") for item in product):
        raise ScopeValidationError("Product Authority must reference Product Thesis paths")
    return {
        "schema": "iis-scope/v2",
        "project_root": str(root),
        "scope_path": str(root / expected),
        "logical_path": expected.as_posix(),
        "status": status,
        "product_authorities": product,
        **({"transition_authorities": transition} if transition else {}),
    }


def validate(scope: Path) -> dict:
    scope = require_canonical_regular_file(scope)
    text = scope.read_text(encoding="utf-8")
    root = canonical_project_root(metadata(text, "Project-Root"), writable=False)
    try:
        logical = scope.relative_to(root).as_posix()
    except ValueError as exc:
        raise ScopeValidationError("Scope is outside Project-Root") from exc
    return validate_text(text, logical, live_scope=scope)


def validate_bytes(data: bytes, logical_path: str) -> dict:
    return validate_text(data.decode("utf-8"), logical_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate(args.scope)
    except (ValueError, OSError, PathContractError, RefError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False) if args.json else "VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
