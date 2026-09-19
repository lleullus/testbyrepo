#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import pwd
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iis_artifacts.linux_worker import LinuxWorkerCommands
from iis_artifacts.supervisor import HostSupervisor

if os.geteuid() != 0:
    raise SystemExit("host conformance must run as root")

nobody = pwd.getpwnam("nobody")
with tempfile.TemporaryDirectory(prefix="iis-host-conformance-", dir="/tmp") as raw:
    arena = Path(raw)
    arena.chmod(0o755)
    project = arena / "project"
    project.mkdir(mode=0o755)
    store_base = arena / "store"
    handoff = arena / "handoff"
    worker_script = arena / "worker.py"
    worker_script.write_text("#!/usr/bin/env python3\nfrom __future__ import annotations\nimport json\nimport os\nfrom pathlib import Path\nimport sys\n\npayload = json.load(sys.stdin)\nstore = Path(os.environ[\"IIS_TEST_STORE_PATH\"])\nblocked = False\ntry:\n    list(store.iterdir())\nexcept PermissionError:\n    blocked = True\nif not blocked:\n    print(json.dumps({\"error\": \"worker could read supervisor store\"}))\n    raise SystemExit(9)\n\ninputs = payload.get(\"inputs\", [])\nif not inputs:\n    print(json.dumps({\"error\": \"no fixed handoff inputs\"}))\n    raise SystemExit(10)\nfor item in inputs:\n    path = Path(item[\"path\"])\n    if not path.is_file():\n        print(json.dumps({\"error\": f\"missing handoff {path}\"}))\n        raise SystemExit(11)\n    path.read_bytes()\n\nif payload[\"kind\"] == \"product-thesis-review\":\n    print(json.dumps({\n        \"result\": {\n            \"host_terminal\": True,\n            \"worker_uid\": os.geteuid(),\n            \"store_access\": \"blocked\",\n        },\n        \"frontier\": [],\n        \"findings\": [],\n    }))\nelif payload[\"kind\"] == \"iis-role\":\n    print(json.dumps({\n        \"worker_uid\": os.geteuid(),\n        \"store_access\": \"blocked\",\n        \"role\": payload[\"role\"],\n    }))\nelse:\n    print(json.dumps({\"error\": \"unknown payload kind\"}))\n    raise SystemExit(12)\n", encoding="utf-8")
    worker_script.chmod(0o555)

    # Construct the store once so the test can pass its private path to the hostile worker.
    from iis_artifacts.store import ArtifactStore
    probe_store = ArtifactStore(store_base, "conformance")
    private_store = probe_store.root
    assert private_store.stat().st_mode & 0o077 == 0

    adapter = LinuxWorkerCommands(
        store=probe_store,
        project_root=project,
        worker_uid=nobody.pw_uid,
        worker_gid=nobody.pw_gid,
        handoff_root=handoff,
        review_command=[sys.executable, str(worker_script)],
        role_command=[sys.executable, str(worker_script)],
        worker_env={"IIS_TEST_STORE_PATH": str(private_store)},
    )
    supervisor = HostSupervisor(
        store_base=store_base,
        project_id="conformance",
        project_root=project,
        worker_uid=nobody.pw_uid,
        current_request="Define and preserve the attributable result.",
        review_budget=2,
        review_dispatcher=adapter.review,
        role_dispatcher=adapter.role,
        gate_runner=adapter.gate,
        assurance_execution_base=adapter.execution_base,
    )

    state = supervisor.start_thesis()
    run_id = state["run_id"]
    supervisor.apply_thesis_proposal(run_id, {
        "kind": "frontier",
        "item_id": "truth",
        "origin": "trusted current request",
        "question": "What establishes attribution?",
        "material_change": "Changing attribution changes product success.",
        "decision_bearing": True,
    })
    supervisor.apply_thesis_proposal(run_id, {
        "kind": "frontier_disposition",
        "item_id": "truth",
        "disposition": "RESOLVED",
        "basis": "The trusted request requires attribution to the triggering identity.",
    })
    source_review = supervisor.drive_thesis(run_id)
    source_uid = source_review["state"]["reviews"][-1]["result_ref_json"]
    candidate_bytes = (
        b"# Product Thesis\n\n"
        b"## Core Utility\nReturn the result attributable to the triggering identity.\n"
    )
    candidate = supervisor.submit_candidate(
        run_id,
        candidate_bytes,
        "docs/planning/product-thesis/demo/THESIS-001.md",
        expected_generation=0,
    )
    supervisor.drive_thesis(run_id)
    closed = supervisor.close_thesis(run_id)
    if closed.get("result") != "CALIBRATED":
        raise SystemExit(f"closure failed: {closed}")

    sources = json.dumps([candidate], indent=2)
    scope = (
        "# Demo\n"
        "Schema: iis-scope/v2\n"
        f"Project-Root: {project}\n"
        "Status: ready\n\n"
        "## Product Authority\n"
        "```iis-sources\n" + sources + "\n```\n\n"
        "## Outcome\nReturn the attributable result.\n\n"
        "## Acceptance\nThe triggering identity reads its own result.\n\n"
        "## Open Decisions\nNone\n"
    ).encode("utf-8")
    role = supervisor.admit_and_start(
        role="scope-plan",
        scope_bytes=scope,
        logical_path="docs/planning/work/demo/SCOPE.md",
    )
    if role["result"].get("worker_uid") != nobody.pw_uid:
        raise SystemExit(f"role did not run as nobody: {role}")
    if role["result"].get("store_access") != "blocked":
        raise SystemExit(f"worker store access was not blocked: {role}")

    code, stdout, stderr, failure = adapter.gate(
        [sys.executable, "-c", "import os; print(os.geteuid())"],
        str(project),
        {},
        10,
    )
    if code != 0 or failure is not None:
        raise SystemExit(f"gate UID probe failed: {code} {failure} {stderr!r}")
    if stdout.strip() != str(nobody.pw_uid).encode():
        raise SystemExit(f"gate runner did not drop UID: {stdout!r}")

    print(json.dumps({
        "status": "PASS",
        "worker_uid": nobody.pw_uid,
        "store_mode": oct(private_store.stat().st_mode & 0o777),
        "thesis": closed["result"],
        "role_invocation": role["invocation_id"],
    }, sort_keys=True))
