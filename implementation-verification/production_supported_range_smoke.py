#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from implementation_verification import Candidate, Currentness, VerificationResult, VerificationStatus
from production_adapters import TerraWorker
from production_entrypoint import create_production_module


def main() -> int:
    opencode = shutil.which("opencode")
    if opencode is None:
        raise RuntimeError("OpenCode executable is unavailable")
    with tempfile.TemporaryDirectory(prefix="iv-production-supported-range-") as temporary:
        root = Path(temporary)
        product = root / "product"
        product.mkdir()
        (product / "app.txt").write_text("implemented", encoding="utf-8")
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
        candidate = module.implement(
            ticket,
            TerraWorker(),
        )
        if not isinstance(candidate, Candidate) or candidate.implementation_changes:
            raise RuntimeError(f"supported-range implementation did not publish a zero-mutation Candidate: {candidate}")
        result = module.verify(candidate)
        if not isinstance(result, VerificationResult) or result.status is not VerificationStatus.VERIFIED:
            raise RuntimeError(f"supported-range verification did not publish VERIFIED: {result}")
        inspection = module.inspect(ticket)
        if inspection.result != result or inspection.currentness is not Currentness.CURRENT:
            raise RuntimeError(f"supported-range inspect readback differs: {inspection}")
        if (product / "app.txt").read_text(encoding="utf-8") != "implemented":
            raise RuntimeError("supported-range flow changed canonical source")
        print(
            json.dumps(
                {
                    "candidateImplementationChanges": len(candidate.implementation_changes),
                    "canonicalSource": "implemented",
                    "inspectionCurrentness": inspection.currentness.value,
                    "inspectionResult": type(inspection.result).__name__,
                    "verificationStatus": result.status.value,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
