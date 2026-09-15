#!/usr/bin/env python3
"""Validate the direct Thesis-to-Scope artifact boundary, not product meaning."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from iis_path_contract import (PathContractError, canonical_project_root,
                               require_canonical_regular_file, require_work_slug)


class ScopeValidationError(ValueError):
    pass


def sections(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    current: str | None = None
    body: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("```") or line.startswith("~~~"):
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


def validate(scope: Path) -> dict:
    require_canonical_regular_file(scope)
    text = scope.read_text(encoding="utf-8")
    if metadata(text, "Schema") != "iis-scope/v1":
        raise ScopeValidationError("unsupported Scope schema")
    root = canonical_project_root(metadata(text, "Project-Root"), writable=False)
    relative = scope.relative_to(root)
    if (len(relative.parts) != 5 or relative.parts[:3] != ("docs", "planning", "work")
            or relative.name != "SCOPE.md"):
        raise ScopeValidationError("Scope must be docs/planning/work/<slug>/SCOPE.md")
    require_work_slug(relative.parts[3])
    status = metadata(text, "Status")
    if status not in {"draft", "ready", "done", "superseded"}:
        raise ScopeValidationError("invalid Scope status")
    content = sections(text)
    for name in ("Outcome", "Acceptance", "Product Authority"):
        if not content.get(name):
            raise ScopeValidationError(f"missing nonempty section: {name}")
    if status in {"ready", "done"} and content.get("Open Decisions", "None") != "None":
        raise ScopeValidationError("ready/done Scope has unresolved product decisions")
    bound = {}
    seen = {scope}
    for section_name, key in (("Product Authority", "product_authorities"),
                              ("Transition Authority", "transition_authorities")):
        authorities = []
        for line in content.get(section_name, "").splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(r"- (/.+) sha256:([0-9a-f]{64})", line)
            if not match:
                raise ScopeValidationError("authority must be '- /canonical/path sha256:<digest>'")
            source = require_canonical_regular_file(Path(match[1]))
            if source in seen:
                raise ScopeValidationError("duplicate or self-referential authority")
            if not source.is_relative_to(root):
                raise ScopeValidationError("authority must be project-local")
            if key == "product_authorities" and not source.is_relative_to(root / "docs" / "planning" / "product-thesis"):
                raise ScopeValidationError("product authority must be a project-local Thesis source")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != match[2]:
                raise ScopeValidationError(f"authority changed: {source}")
            seen.add(source)
            authorities.append({"path": str(source), "sha256": digest})
        if section_name in content and not authorities:
            raise ScopeValidationError(f"{section_name} needs at least one exact source")
        if authorities:
            bound[key] = authorities
    return {"schema": "iis-scope/v1", "project_root": str(root), "scope_path": str(scope),
            "status": status, **bound}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate(args.scope)
    except (ValueError, OSError, PathContractError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False) if args.json else "VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
