from __future__ import annotations

from pathlib import Path
import json
import uuid
import shutil
import sys


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def direct_scope(repo: Path, slug: str, status: str, outcome: str, *, remaining: str | None = None) -> None:
    (repo / ".git").mkdir(parents=True, exist_ok=True)
    thesis = repo / "docs/planning/product-thesis" / slug / "THESIS-001.md"
    write(
        thesis,
        f"""# {slug} Product Thesis

## Required Outcomes / Means
- {outcome}
{f'- {remaining}' if remaining else ''}
""",
    )
    source_ref = {"snapshot": "snap-" + uuid.uuid4().hex, "path": thesis.relative_to(repo).as_posix()}
    write(
        repo / "docs/planning/work" / slug / "SCOPE.md",
        f"""# {slug.replace('-', ' ').title()}
Schema: iis-scope/v2
Project-Root: {repo}
Status: {status}

## Product Authority
```iis-sources
{json.dumps([source_ref], indent=2)}
```

## Outcome
{outcome}

## Acceptance
Observe the authoritative result for {outcome.lower()}.

## Open Decisions
None
""",
    )


def legacy_history(repo: Path) -> None:
    (repo / ".git").mkdir(parents=True, exist_ok=True)
    write(
        repo / "docs/planning/scope-shaping/old/SCOPE-SHAPING-RESULT.md",
        """# Historical Scope
Status: confirmed
Selected-Increment: INC-001
""",
    )
    write(
        repo / "docs/planning/work/legacy-cleanup/tickets/TICKET-001.md",
        """# TKT-001 Historical Ticket
Status: ready
""",
    )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".demo-projects").resolve()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    tax = root / "tax"
    direct_scope(tax, "vat-readback", "ready", "Preserve VAT authoritative readback", remaining="Expose operator reconciliation")

    ima2 = root / "ima2"
    direct_scope(ima2, "job-inspection", "draft", "Inspect a submitted job")

    oracle = root / "oracle"
    (oracle / ".git").mkdir(parents=True)
    (oracle / "docs/planning").mkdir(parents=True)

    watcher = root / "watcher"
    direct_scope(watcher, "release-alert", "done", "Preserve release alert identity")

    legacy = root / "legacy-api"
    legacy_history(legacy)

    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
