#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from implementation_verification import ImplementationStopped
from production_adapters import ProcessImplementationCheck, ProcessImplementationReview, ProcessWorker
from production_entrypoint import create_production_module


WORKER = (
    "import json,pathlib;"
    "r=json.loads(pathlib.Path('/input/request.json').read_text());a=r['assignment'];"
    "(pathlib.Path('/workspace')/a['path']).write_text(a['value'])"
)
VERIFIER = (
    "import json,pathlib;r=json.loads(pathlib.Path('/input/request.json').read_text());"
    "\nif r['operation']=='plan':\n"
    " print(json.dumps([{'observationIdentity':'smoke','kind':'SOURCE','criterionIndexes':[1],"
    "'requests':[{'path':'app.txt'}],'expected':'implemented'}]))\n"
    "else:\n"
    " e=r['evidence'];ok=bool(e) and e[0].get('complete') and e[0].get('observed')=='implemented';"
    " print(json.dumps([{'criterionIndex':1,'outcome':'SATISFIED' if ok else 'UNDETERMINED',"
    "'evidenceObservationIdentities':['smoke'] if e else []}]))"
)
REVIEW = (
    "import json,pathlib;"
    "r=json.loads(pathlib.Path('/input/request.json').read_text());"
    "p=pathlib.Path('/source/app.txt');"
    "print(json.dumps({'decision':'CLOSE'} if p.read_text()=='implemented' else "
    "{'decision':'ASSIGN','assignment':{'path':'app.txt','value':'implemented'}}))"
)
CHECK = "import json,pathlib;pathlib.Path('/input/request.json').read_text();print(json.dumps({'status':'PASSED'}))"


def main() -> int:
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
            ("/usr/bin/python3", "-c", VERIFIER),
            ProcessImplementationReview(("/usr/bin/python3", "-c", REVIEW)),
            ProcessImplementationCheck(("/usr/bin/python3", "-c", CHECK)),
        )
        result = module.implement(
            ticket,
            ProcessWorker("production-smoke-worker", ("/usr/bin/python3", "-c", WORKER)),
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
