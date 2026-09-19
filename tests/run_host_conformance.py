#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import pwd
import stat
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iis_artifacts.linux_worker import LinuxWorkerCommands
from iis_artifacts.host import HostSupervisor

if os.geteuid() != 0:
    raise SystemExit("host conformance must run as root")

nobody = pwd.getpwnam("nobody")
with tempfile.TemporaryDirectory(prefix="iis-host-conformance-", dir="/tmp") as raw:
    arena = Path(raw)
    arena.chmod(0o755)
    project = arena / "project"
    project.mkdir(mode=0o755)
    command = project / "main.py"
    command.write_text("print('actual-value')\n", encoding="utf-8")
    command.chmod(0o555)
    os.chown(project, nobody.pw_uid, nobody.pw_gid)

    store_base = arena / "store"
    handoff = arena / "handoff"
    worker_script = arena / "worker.py"
    worker_script.write_text(
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import json\n"
        "import os\n"
        "from pathlib import Path\n"
        "import sys\n\n"
        "payload = json.load(sys.stdin)\n"
        "store = Path(os.environ[\"IIS_TEST_STORE_PATH\"])\n"
        "blocked = False\n"
        "try:\n"
        "    list(store.iterdir())\n"
        "except PermissionError:\n"
        "    blocked = True\n"
        "if not blocked:\n"
        "    print(json.dumps({\"error\": \"worker could read supervisor store\"}))\n"
        "    raise SystemExit(9)\n\n"
        "inputs = payload.get(\"inputs\", [])\n"
        "if not inputs:\n"
        "    print(json.dumps({\"error\": \"no fixed handoff inputs\"}))\n"
        "    raise SystemExit(10)\n"
        "for item in inputs:\n"
        "    path = Path(item[\"path\"])\n"
        "    if not path.is_file():\n"
        "        print(json.dumps({\"error\": f\"missing handoff {path}\"}))\n"
        "        raise SystemExit(11)\n"
        "    path.read_bytes()\n\n"
        "if payload[\"kind\"] == \"product-thesis-review\":\n"
        "    print(json.dumps({\n"
        "        \"result\": {\n"
        "            \"host_terminal\": True,\n"
        "            \"worker_uid\": os.geteuid(),\n"
        "            \"store_access\": \"blocked\",\n"
        "        },\n"
        "        \"frontier\": [],\n"
        "        \"findings\": [],\n"
        "    }))\n"
        "elif payload[\"kind\"] == \"iis-role\":\n"
        "    thesis = Path(payload[\"project_root\"]) / \"docs/planning/product-thesis/demo/THESIS-001.md\"\n"
        "    try:\n"
        "        thesis_text = thesis.read_text(encoding=\"utf-8\")\n"
        "    except OSError as exc:\n"
        "        print(json.dumps({\"error\": f\"project Thesis is unreadable: {exc}\"}))\n"
        "        raise SystemExit(13)\n"
        "    if \"Product Thesis\" not in thesis_text:\n"
        "        print(json.dumps({\"error\": \"project Thesis content mismatch\"}))\n"
        "        raise SystemExit(14)\n"
        "    print(json.dumps({\n"
        "        \"worker_uid\": os.geteuid(),\n"
        "        \"store_access\": \"blocked\",\n"
        "        \"role\": payload[\"role\"],\n"
        "        \"project_thesis\": \"readable\",\n"
        "    }))\n"
        "else:\n"
        "    print(json.dumps({\"error\": \"unknown payload kind\"}))\n"
        "    raise SystemExit(12)\n",
        encoding="utf-8",
    )
    worker_script.chmod(0o555)

    from iis_artifacts.store import ArtifactStore

    probe_store = ArtifactStore(store_base, "conformance")
    private_store = probe_store.root
    assert private_store.stat().st_mode & 0o077 == 0
    command_snapshot = probe_store.capture_files(
        project,
        [command],
        kind="source",
        origin="conformance-command",
    )
    command_ref = {"snapshot": command_snapshot, "path": "main.py"}

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
    supervisor.apply_thesis_proposal(
        run_id,
        {
            "kind": "frontier",
            "item_id": "truth",
            "origin": "trusted current request",
            "question": "What establishes attribution?",
            "material_change": "Changing attribution changes product success.",
            "decision_bearing": True,
        },
    )
    supervisor.apply_thesis_proposal(
        run_id,
        {
            "kind": "frontier_disposition",
            "item_id": "truth",
            "disposition": "RESOLVED",
            "basis": "The trusted request requires attribution to the triggering identity.",
        },
    )
    supervisor.drive_thesis(run_id)
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

    published_thesis = project / "docs/planning/product-thesis/demo/THESIS-001.md"
    published_details = published_thesis.stat()
    if published_details.st_uid != nobody.pw_uid or published_details.st_gid != nobody.pw_gid:
        raise SystemExit(f"published Thesis owner mismatch: {published_details}")
    if stat.S_IMODE(published_details.st_mode) != 0o444:
        raise SystemExit(f"published Thesis mode mismatch: {oct(stat.S_IMODE(published_details.st_mode))}")

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
    if role["result"].get("project_thesis") != "readable":
        raise SystemExit(f"worker could not read project Thesis: {role}")

    assurance_admission = supervisor.admit_scope_bytes(
        role="assurance",
        scope_bytes=scope,
        logical_path="docs/planning/work/demo/SCOPE.md",
    )
    baseline = {
        "schema": "iis-assurance/v2",
        "scope": assurance_admission["scope"],
        "obligations": [
            {
                "anchor": "The triggering identity reads its own result.",
                "evidence": ["readback"],
            }
        ],
        "gates": [
            {
                "id": "native",
                "argv": [sys.executable, "-B", str(command)],
                "cwd": str(project),
                "timeout": 10,
                "mechanisms": [command_ref],
                "jobs": [],
                "jobs_path": None,
            }
        ],
        "observations": [
            {
                "id": "readback",
                "initial_state": "captured conformance project",
                "trigger": "python -B main.py",
                "readback": "native stdout",
                "predicate": "stdout is actual-value",
            }
        ],
        "surfaces": [],
        "lanes": [],
        "no_probe_reason": "Host boundary conformance uses a non-behavioral fixture.",
    }
    baseline_path = arena / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    binding = supervisor.bind_assurance(
        baseline_path,
        {
            "artifacts": [],
            "runtime": [],
            "mechanisms": [command_ref],
            "note": "Conformance source fixture; no external service.",
        },
    )
    gate = supervisor.run_assurance_gate(
        baseline_path,
        binding,
        "native",
        arena / "gate-output",
    )
    if gate["capture"]["returncode"] != 0:
        raise SystemExit(f"native Assurance gate failed: {gate}")
    invocation = supervisor.begin_assurance_invocation(
        binding,
        "observation",
        "readback",
    )["invocation_id"]
    evidence = supervisor.capture_assurance_evidence(
        binding,
        invocation,
        {"readback/stdout": b"actual-value\n"},
    )
    supervisor.complete_assurance_invocation(
        binding,
        invocation,
        {
            "schema": "iis-assurance-result/v3",
            "kind": "observation",
            **baseline["observations"][0],
            "invocation": invocation,
            "binding": binding["binding_id"],
            "completion": "COMPLETE",
            "evidence": evidence,
            "effects": [],
            "outcome": "SATISFIED",
        },
    )
    assurance_closure = supervisor.close_assurance(baseline_path, binding)
    if assurance_closure.get("status") != "EVIDENCE_COMPLETE":
        raise SystemExit(f"Assurance closure failed: {assurance_closure}")

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

    print(
        json.dumps(
            {
                "status": "PASS",
                "worker_uid": nobody.pw_uid,
                "store_mode": oct(private_store.stat().st_mode & 0o777),
                "thesis": closed["result"],
                "assurance": assurance_closure["status"],
                "role_invocation": role["invocation_id"],
            },
            sort_keys=True,
        )
    )
