#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from implementation_verification import ImplementationStopped
from production_adapters import TerraWorker
from production_entrypoint import create_production_module


def main() -> int:
    opencode = shutil.which("opencode")
    if opencode is None:
        raise RuntimeError("OpenCode executable is unavailable")
    with tempfile.TemporaryDirectory(prefix="iv-production-smoke-") as temporary:
        root = Path(temporary)
        product = root / "product"
        product.mkdir()
        (product / "app.txt").write_text("baseline", encoding="utf-8")
        spec = root / "SPEC.md"
        spec.write_text(
            "# Spec\nStatus: approved\nOwner: smoke\n\n"
            + "".join(
                f"## {name}\nvalue\n\n"
                for name in (
                    "Problem",
                    "Desired Outcome",
                    "Requirements",
                    "Non-Goals",
                    "Implementation Constraints",
                    "Verification Expectations",
                    "UI / UX",
                    "Open Questions",
                )
            ),
            encoding="utf-8",
        )
        ticket = root / "TICKET.md"
        ticket.write_text(
            "# Ticket\nStatus: ready\n"
            f"Parent-Spec: {spec}\nProject-Root: {product}\nWorker: \nUI: no\n\n"
            "## Goal\nImplement.\n\n## Acceptance Criteria\n- app is implemented\n\n"
            "## Scope\napp.txt\n\n## Non-Goals\nNone.\n\n## Blockers\nNone.\n\n"
            "## Verification\nRead app.\n\n## References\nNone.\n",
            encoding="utf-8",
        )

        module = create_production_module(
            root / "state",
            opencode,
        )
        result = module.implement(
            ticket,
            TerraWorker(),
        )
        if not isinstance(result, ImplementationStopped):
            raise RuntimeError(f"production smoke failed to stop at source adoption: {result}")
        if result.reason != "conditional source adoption is unavailable":
            raise RuntimeError(f"production smoke had unexpected blocker: {result.reason}")
        print(
            json.dumps(
                {
                    "canonicalSource": (product / "app.txt").read_text(encoding="utf-8"),
                    "reason": result.reason,
                    "status": "IMPLEMENTATION_STOPPED",
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
