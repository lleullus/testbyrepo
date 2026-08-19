from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
import time
from pathlib import Path

from tests.test_ticket_validator import TicketFixture

ROOT = Path(__file__).parents[1]
IMPLEMENT = (
    ROOT
    / "companion-skills/ready-ticket-implement/pi/iis-ready-implement-runner.mjs"
)
VERIFY = ROOT / "companion-skills/ready-ticket-verify/pi/iis-ready-verify-runner.mjs"
EXTENSION = ROOT / ".pi/extensions/iis-ready-audit/index.ts"


class PiReadyRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)
        self.fixture = TicketFixture()
        self.fixture.write()
        self.project = self.fixture.root
        self.ticket = self.fixture.ticket_path
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        subprocess.run(["git", "config", "user.email", "pi-runner@example.invalid"], cwd=self.project, check=True)
        subprocess.run(["git", "config", "user.name", "Pi Runner Test"], cwd=self.project, check=True)
        subprocess.run(["git", "add", "."], cwd=self.project, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.project, check=True)
        self.agent_dir = self.work / "agent"
        self.agent_dir.mkdir()
        thinking = {
            "minimal": "minimal",
            "low": "low",
            "medium": "medium",
            "high": "high",
            "xhigh": "xhigh",
            "max": "max",
        }
        self.agent_models = {
            "providers": {
                "test": {
                    "api": "openai-responses",
                    "apiKey": "test-key",
                    "models": [
                        {"id": "implement-owner", "reasoning": True, "thinkingLevelMap": thinking},
                        {"id": "configured-owner", "reasoning": True, "thinkingLevelMap": thinking},
                        {"id": "auditor", "reasoning": True, "thinkingLevelMap": thinking},
                        {
                            "id": "limited-auditor",
                            "reasoning": True,
                            "thinkingLevelMap": {**thinking, "high": None},
                        },
                        {"id": "unavailable-owner", "reasoning": True, "thinkingLevelMap": thinking},
                    ],
                },
                "opencodex": {
                    "api": "openai-responses",
                    "apiKey": "test-key",
                    "models": [
                        {"id": "gpt-5.6-luna", "reasoning": True, "thinkingLevelMap": thinking},
                        {"id": "gpt-5.6-sol", "reasoning": True, "thinkingLevelMap": thinking},
                    ],
                },
            }
        }
        (self.agent_dir / "models.json").write_text(
            json.dumps(self.agent_models), encoding="utf-8"
        )
        (self.agent_dir / "models.json").chmod(0o600)
        self.stub = self.work / "pi-stub.py"
        self.stub.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import signal
                import sys
                import time

                def emit_audit_progress(event, **fields):
                    print(
                        "IIS_PI_AUDIT_EVENT " + json.dumps({"event": event, **fields}),
                        file=sys.stderr,
                        flush=True,
                    )

                args = sys.argv[1:]
                signal.alarm(2)
                sys.stdin.read()
                signal.alarm(0)
                if "--list-models" in args:
                    provider_filter = args[-1]
                    with open(os.path.join(os.environ["PI_CODING_AGENT_DIR"], "models.json"), encoding="utf-8") as stream:
                        config = json.load(stream)
                    hidden = os.environ.get("PI_STUB_HIDE_MODEL")
                    print("provider  model  context  max-out  thinking  images")
                    for provider, provider_config in config["providers"].items():
                        if provider != provider_filter:
                            continue
                        for model in provider_config.get("models", []):
                            binding = f"{provider}/{model['id']}"
                            if binding != hidden:
                                print(f"{provider}  {model['id']}  1K  1K  yes  no")
                    sys.exit(0)
                prompt_index = args.index("--append-system-prompt") + 1
                capture = {
                    "args": args,
                    "agent": os.environ.get("PI_SUBAGENT_NAME"),
                    "session": os.environ.get("PI_SUBAGENT_SESSION"),
                    "depth": os.environ.get("PI_SUBAGENT_DEPTH"),
                    "maxDepth": os.environ.get("PI_SUBAGENT_MAX_DEPTH"),
                    "allowed": os.environ.get("PI_SUBAGENT_ALLOWED"),
                    "agentDir": os.environ.get("PI_CODING_AGENT_DIR"),
                    "prompt": open(args[prompt_index], encoding="utf-8").read(),
                    "ticketMode": os.environ.get("IIS_READY_TICKET_MODE"),
                    "ticketPath": os.environ.get("IIS_READY_TICKET_PATH"),
                    "ticketValidator": os.environ.get("IIS_CANONICAL_TICKET_VALIDATOR"),
                    "leakedSecret": os.environ.get("PI_TEST_PARENT_SECRET"),
                }
                with open(os.environ["PI_STUB_CAPTURE"], "w", encoding="utf-8") as stream:
                    json.dump(capture, stream)
                mutation_path = os.environ.get("PI_STUB_MUTATE_PRODUCT")
                if mutation_path:
                    with open(mutation_path, "w", encoding="utf-8") as stream:
                        stream.write("unauthorized product mutation\\n")
                if os.environ.get("PI_STUB_TRANSITION_TICKET") == "1":
                    ticket_path = capture["ticketPath"]
                    with open(ticket_path, encoding="utf-8") as stream:
                        ticket_content = stream.read()
                    with open(ticket_path, "w", encoding="utf-8") as stream:
                        stream.write(ticket_content.replace("Status: ready", "Status: done", 1))
                raw_stderr = os.environ.get("PI_STUB_RAW_STDERR")
                if raw_stderr:
                    print(raw_stderr, file=sys.stderr, flush=True)
                if os.environ.get("PI_STUB_INVALID_AUDIT_PROGRESS") == "1":
                    print("IIS_PI_AUDIT_EVENT {not-json secret-body", file=sys.stderr, flush=True)


                delay = os.environ.get("PI_STUB_DELAY_SECONDS")
                if delay:
                    time.sleep(float(delay))
                elif os.environ.get("PI_STUB_WAIT") == "1":
                    time.sleep(30)
                agent = capture["agent"]
                if os.environ.get("PI_STUB_NOT_STARTED") == "1":
                    output = (
                        "Pi Owner Agent: iis-ready-verify\\n"
                        "Pi Owner Session: none\\n"
                        "Pi Audit Run IDs: None\\n"
                        "Pi Audit Fan-In: NOT REQUESTED\\n\\n"
                        "VERIFICATION NOT STARTED\\n"
                        "Ticket: /fixture/TICKET.md\\n"
                        "Reason: CANONICAL TICKET INVALID\\n"
                        "AC verdicts: Not issued"
                    )
                elif os.environ.get("PI_STUB_INVALID") == "1":
                    output = "invalid terminal output"
                elif agent == "iis-ready-implement":
                    output = (
                        "Pi Owner Agent: iis-ready-implement\\n"
                        "Pi Owner Session: none\\n"
                        "Pi Audit Run IDs:\\n"
                        "Pi Audit Fan-In: NOT REQUESTED\\n\\n"
                        "IMPLEMENT RESULT\\n"
                        "Credential echo: apiKey=supersecret123\\n"
                        "Completion: COMPLETE"
                    )
                elif os.environ.get("PI_STUB_QUOTED_RESULT") == "1":
                    output = (
                        "Pi Owner Agent: iis-ready-verify\\n"
                        "Pi Owner Session: none\\n"
                        "Pi Audit Run IDs:\\n"
                        "Pi Audit Fan-In: NOT REQUESTED\\n\\n"
                        "READY TICKET VERIFICATION RESULT\\n"
                        "Verification Verdict: `FAILED`\\n"
                        "Ticket Progression: `NOT APPLICABLE`\\n"
                        "Ticket status after verification: `ready`"
                    )
                elif os.environ.get("PI_STUB_COMPLETED") == "1":
                    output = (
                        "Pi Owner Agent: iis-ready-verify\\n"
                        "Pi Owner Session: none\\n"
                        "Pi Audit Run IDs:\\n"
                        "Pi Audit Fan-In: NOT REQUESTED\\n\\n"
                        "READY TICKET VERIFICATION RESULT\\n"
                        "Verification Verdict: VERIFIED\\n"
                        "Ticket Progression: COMPLETED\\n"
                        "Ticket status after verification: `done`"
                    )
                else:
                    output = (
                        "Pi Owner Agent: iis-ready-verify\\n"
                        "Pi Owner Session: none\\n"
                        "Pi Audit Run IDs:\\n"
                        "Pi Audit Fan-In: NOT REQUESTED\\n\\n"
                        "READY TICKET VERIFICATION RESULT\\n"
                        "Verification Verdict: FAILED\\n"
                        "Ticket Progression: NOT APPLICABLE\\n"
                        "Ticket status after verification: ready"
                    )

                if os.environ.get("PI_STUB_AUDIT_PROGRESS") == "1":
                    audit_run_id = "iis-audit-11111111-1111-4111-8111-111111111111"
                    audit_base = {"auditRunId": audit_run_id, "role": "verification"}
                    emit_audit_progress(
                        "AUDITOR_STARTING",
                        **audit_base,
                        handoffSequence=0,
                        task="progress secret must be dropped",
                    )
                    emit_audit_progress("AUDITOR_RUNNING", **audit_base, handoffSequence=0)
                    emit_audit_progress("AUDITOR_WAITING_REPLY", **audit_base, handoffSequence=1)
                    emit_audit_progress("AUDITOR_RESUMED", **audit_base, handoffSequence=1)
                    emit_audit_progress(
                        "AUDITOR_TERMINAL",
                        **audit_base,
                        handoffSequence=1,
                        terminalStatus="COMPLETED",
                    )
                    emit_audit_progress(
                        "FAN_IN_COMPLETE",
                        auditRunIds=[audit_run_id],
                        terminalAuditors=1,
                    )

                print(json.dumps({"type": "tool_execution_start", "toolName": "read"}))
                print(json.dumps({"type": "tool_execution_end", "toolName": "read", "isError": False}))
                print(json.dumps({
                    "type": "message_end",
                    "message": {"role": "assistant", "content": [{"type": "text", "text": output}]},
                }))
                sys.exit(int(os.environ.get("PI_STUB_EXIT", "0")))
                """
            ),
            encoding="utf-8",
        )
        self.stub.chmod(0o755)

    def tearDown(self) -> None:
        self.fixture.close()
        self.temp.cleanup()

    def run_runner(
        self,
        runner: Path,
        invocation: dict[str, object],
        *,
        extra_env: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object], dict[str, object] | None]:
        input_path = self.work / "invocation.json"
        capture_path = self.work / "capture.json"
        input_path.write_text(json.dumps(invocation), encoding="utf-8")
        input_path.chmod(0o600)
        env = {
            **os.environ,
            "IIS_PI_BIN": str(self.stub),
            "NODE_ENV": "test",
            "PI_STUB_CAPTURE": str(capture_path),
            "IIS_PI_AGENT_DIR": str(self.agent_dir),
            **(extra_env or {}),
        }
        completed = subprocess.run(
            [str(runner), "--input", str(input_path)],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        terminal = json.loads(completed.stdout)
        capture = (
            json.loads(capture_path.read_text(encoding="utf-8"))
            if capture_path.exists()
            else None
        )
        return completed, terminal, capture

    def progress_events(self, stderr: str) -> list[dict[str, object]]:
        events = [json.loads(line) for line in stderr.splitlines() if line]
        for event in events:
            self.assertEqual(event["schema"], "iis.pi.progress/v1")
            self.assertIsInstance(event["sequence"], int)
            self.assertIsInstance(event["timestamp"], str)
            self.assertIsInstance(event["elapsedMs"], int)
        self.assertEqual(
            [event["sequence"] for event in events],
            list(range(1, len(events) + 1)),
        )
        return events

    def implement_invocation(self) -> dict[str, object]:
        return {
            "schema": "iis.pi.ready-ticket-implement/v1",
            "runId": "implement-001",
            "ticket": str(self.ticket),
            "projectRoot": str(self.project),
            "targetIdentity": "git:abc123+clean",
            "additionalInstructions": "Preserve the approved non-goals.",
            "ownerModel": "test/implement-owner",
            "auditors": [],
        }

    def verify_invocation(self) -> dict[str, object]:
        return {
            "schema": "iis.pi.ready-ticket-verify/v1",
            "runId": "verify-001",
            "ticket": str(self.ticket),
            "projectRoot": str(self.project),
            "targetIdentity": "git:def456+clean",
            "candidateTarget": "candidate:def456",
            "implementationReport": "artifact://implement-result",
            "auditors": [],
            "diagnosticReverify": False,
        }

    def assert_fixed_runtime(self, capture: dict[str, object], expected_tools: str) -> None:
        args = capture["args"]
        self.assertIsInstance(args, list)
        for flag in (
            "--no-session",
            "--no-context-files",
            "--no-skills",
            "--no-prompt-templates",
            "--no-extensions",
        ):
            self.assertIn(flag, args)
        self.assertEqual(args[args.index("--extension") + 1], str(EXTENSION))
        self.assertEqual(args[args.index("--tools") + 1], expected_tools)
        self.assertEqual(args[args.index("--thinking") + 1], "max")
        self.assertEqual(capture["session"], "none")
        self.assertEqual(capture["depth"], "1")
        self.assertEqual(capture["maxDepth"], "0")
        self.assertEqual(capture["allowed"], "")
        self.assertEqual(capture["agentDir"], str(self.agent_dir))

    def test_implement_runner_is_fully_bound_and_emits_terminal_envelope(self) -> None:
        completed, terminal, capture = self.run_runner(
            IMPLEMENT,
            self.implement_invocation(),
            extra_env={"PI_TEST_PARENT_SECRET": "parent-secret-must-not-leak"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["schema"], "iis.pi.ready-ticket-run/v1")
        self.assertEqual(terminal["processStatus"], "COMPLETED")
        self.assertEqual(terminal["workflow"], {"completion": "COMPLETE"})
        self.assertEqual(terminal["session"], "none")
        self.assertNotIn("supersecret123", terminal["output"])
        self.assertIn("apiKey=[REDACTED]", terminal["output"])
        self.assertIsNotNone(capture)
        assert capture is not None
        self.assertIsNone(capture["leakedSecret"])
        self.assert_fixed_runtime(
            capture,
            "read,grep,find,ls,bash,edit,write,iis_audit_start,iis_audit_reply,iis_audit_cancel,iis_audit_fan_in",
        )
        self.assertEqual(capture["agent"], "iis-ready-implement")
        self.assertIn("dedicated implementation lifecycle owner", capture["prompt"])
        self.assertIn("PI READY TICKET IMPLEMENT INVOCATION", capture["args"][-1])
        self.assertIn("Auditor Count: 0", capture["args"][-1])
        self.assertEqual(
            terminal["preflight"]["modelBindings"],
            [
                {
                    "role": "implement owner",
                    "model": "test/implement-owner",
                    "thinking": "max",
                    "api": "openai-responses",
                }
            ],
        )

    def test_verify_runner_is_fully_bound_without_general_write_tool(self) -> None:
        completed, terminal, capture = self.run_runner(
            VERIFY, self.verify_invocation()
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["processStatus"], "COMPLETED")
        self.assertEqual(
            terminal["workflow"],
            {
                "verdict": "FAILED",
                "progression": "NOT APPLICABLE",
                "ticketStatus": "ready",
            },
        )
        self.assertEqual(terminal["ownerModel"], "opencodex/gpt-5.6-luna")
        self.assertEqual(terminal["ownerThinking"], "max")
        self.assertIsNotNone(capture)
        assert capture is not None
        self.assert_fixed_runtime(
            capture,
            "read,grep,find,ls,bash,iis_ticket_mark_done,iis_audit_start,iis_audit_reply,iis_audit_cancel,iis_audit_fan_in",
        )
        self.assertEqual(capture["agent"], "iis-ready-verify")
        args = capture["args"]
        self.assertEqual(args[args.index("--model") + 1], "opencodex/gpt-5.6-luna")
        self.assertNotIn("write", capture["args"][capture["args"].index("--tools") + 1].split(","))
        self.assertIn("dedicated independent verification lifecycle owner", capture["prompt"])
        self.assertIn("Candidate Target Hint: candidate:def456", capture["args"][-1])
        self.assertEqual(capture["ticketMode"], "VERIFY")
        self.assertEqual(capture["ticketPath"], str(self.ticket))
        self.assertTrue(str(capture["ticketValidator"]).endswith("matt/skills/to-tickets/validate_ticket.py"))
        self.assertIn("Auditor Count: 0", capture["args"][-1])

    def test_runner_emits_versioned_observed_progress_and_one_final_stdout_envelope(self) -> None:
        completed, terminal, _capture = self.run_runner(
            IMPLEMENT, self.implement_invocation()
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        self.assertEqual(terminal["processStatus"], "COMPLETED")
        events = self.progress_events(completed.stderr)
        self.assertEqual(
            [event["event"] for event in events],
            [
                "RUN_STARTED",
                "PREFLIGHT_PASSED",
                "OWNER_PROCESS_STARTED",
                "OWNER_ACTIVITY",
                "OWNER_ACTIVITY",
                "RUN_COMPLETED",
            ],
        )
        self.assertEqual(events[3]["activity"], "TOOL_STARTED")
        self.assertEqual(events[3]["toolName"], "read")
        self.assertEqual(events[4]["activity"], "TOOL_FINISHED")
        self.assertEqual(events[4]["toolFinishes"], 1)
        self.assertNotIn("summary", completed.stderr)

    def test_verify_reports_postcondition_before_terminal_progress(self) -> None:
        completed, _terminal, _capture = self.run_runner(
            VERIFY, self.verify_invocation()
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        events = self.progress_events(completed.stderr)
        names = [event["event"] for event in events]
        self.assertLess(names.index("POSTCONDITION_STARTED"), names.index("POSTCONDITION_PASSED"))
        self.assertLess(names.index("POSTCONDITION_PASSED"), names.index("RUN_COMPLETED"))

    def test_runner_relays_only_sanitized_auditor_progress(self) -> None:
        invocation = self.verify_invocation()
        invocation["auditors"] = [{"acOrdinal": 1, "linkedFlows": [1]}]
        completed, terminal, _capture = self.run_runner(
            VERIFY,
            invocation,
            extra_env={
                "PI_STUB_AUDIT_PROGRESS": "1",
                "PI_STUB_RAW_STDERR": "private child diagnostic",
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        events = self.progress_events(completed.stderr)
        audit_events = [
            event
            for event in events
            if str(event["event"]).startswith("AUDITOR_")
            or event["event"] == "FAN_IN_COMPLETE"
        ]
        self.assertEqual(
            [event["event"] for event in audit_events],
            [
                "AUDITOR_STARTING",
                "AUDITOR_RUNNING",
                "AUDITOR_WAITING_REPLY",
                "AUDITOR_RESUMED",
                "AUDITOR_TERMINAL",
                "FAN_IN_COMPLETE",
            ],
        )
        self.assertEqual(audit_events[2]["handoffSequence"], 1)
        self.assertEqual(audit_events[4]["terminalStatus"], "COMPLETED")
        self.assertEqual(audit_events[4]["terminalAuditors"], 1)
        self.assertEqual(audit_events[5]["configuredAuditors"], 1)
        self.assertNotIn("private child diagnostic", completed.stderr)
        self.assertIn("private child diagnostic", terminal["stderr"])
        for forbidden in ("assignment", "task", "body", "prompt", "reasoning"):
            self.assertNotIn(forbidden, completed.stderr)

    def test_malformed_child_progress_fails_without_live_payload_leak(self) -> None:
        completed, terminal, _capture = self.run_runner(
            IMPLEMENT,
            self.implement_invocation(),
            extra_env={"PI_STUB_INVALID_AUDIT_PROGRESS": "1"},
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(terminal["processStatus"], "FAILED")
        self.assertEqual(terminal["error"], "invalid child audit progress event")
        self.assertNotIn("secret-body", completed.stderr)
        self.assertIn("[invalid child audit progress event]", terminal["stderr"])
        self.assertEqual(self.progress_events(completed.stderr)[-1]["event"], "RUN_FAILED")

    def test_silent_owner_emits_fact_only_heartbeat_before_exit(self) -> None:
        input_path = self.work / "heartbeat-invocation.json"
        capture_path = self.work / "heartbeat-capture.json"
        input_path.write_text(json.dumps(self.implement_invocation()), encoding="utf-8")
        input_path.chmod(0o600)
        env = {
            **os.environ,
            "IIS_PI_BIN": str(self.stub),
            "NODE_ENV": "test",
            "PI_STUB_CAPTURE": str(capture_path),
            "IIS_PI_AGENT_DIR": str(self.agent_dir),
            "PI_STUB_DELAY_SECONDS": "0.25",
            "PI_STUB_PROGRESS_HEARTBEAT_MS": "50",
        }
        process = subprocess.Popen(
            [str(IMPLEMENT), "--input", str(input_path)],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stderr is not None
        heartbeat = None
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            line = process.stderr.readline()
            if not line:
                break
            event = json.loads(line)
            if event["event"] == "RUN_ALIVE":
                heartbeat = event
                self.assertIsNone(process.poll())
                break
        stdout, _stderr = process.communicate(timeout=10)
        self.assertEqual(process.returncode, 0, stdout)
        self.assertIsNotNone(heartbeat)
        assert heartbeat is not None
        self.assertGreaterEqual(heartbeat["inactiveMs"], 50)
        self.assertNotIn("thinking", heartbeat)
        self.assertNotIn("provider", heartbeat)
        self.assertEqual(json.loads(stdout)["processStatus"], "COMPLETED")

    def test_implement_runner_defaults_to_luna_max(self) -> None:
        invocation = self.implement_invocation()
        invocation.pop("ownerModel")
        completed, terminal, capture = self.run_runner(IMPLEMENT, invocation)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["ownerModel"], "opencodex/gpt-5.6-luna")
        self.assertEqual(terminal["ownerThinking"], "max")
        assert capture is not None
        args = capture["args"]
        self.assertEqual(args[args.index("--model") + 1], "opencodex/gpt-5.6-luna")
        self.assertEqual(args[args.index("--thinking") + 1], "max")

    def test_owner_thinking_invocation_overrides_role_defaults(self) -> None:
        implement_invocation = self.implement_invocation()
        implement_invocation["ownerThinking"] = "xhigh"
        completed, terminal, capture = self.run_runner(
            IMPLEMENT, implement_invocation
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["ownerThinking"], "xhigh")
        self.assertEqual(
            terminal["preflight"]["modelBindings"][0]["thinking"], "xhigh"
        )
        assert capture is not None
        args = capture["args"]
        self.assertEqual(args[args.index("--thinking") + 1], "xhigh")

        verify_invocation = self.verify_invocation()
        verify_invocation["ownerThinking"] = "low"
        completed, terminal, capture = self.run_runner(VERIFY, verify_invocation)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["ownerThinking"], "low")
        self.assertEqual(
            terminal["preflight"]["modelBindings"][0]["thinking"], "low"
        )
        assert capture is not None
        args = capture["args"]
        self.assertEqual(args[args.index("--thinking") + 1], "low")

    def test_invalid_owner_thinking_fails_before_owner_start(self) -> None:
        invocation = self.implement_invocation()
        invocation["ownerThinking"] = "ultra"
        completed, terminal, capture = self.run_runner(IMPLEMENT, invocation)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("ownerThinking is not a supported thinking level", terminal["error"])
        self.assertIsNone(capture)

    def test_both_auditor_roles_default_to_luna_xhigh(self) -> None:
        implement_invocation = self.implement_invocation()
        implement_invocation["auditors"] = [
            {"slot": "default", "assignment": "Observe implementation"}
        ]
        completed, terminal, capture = self.run_runner(
            IMPLEMENT, implement_invocation
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            terminal["preflight"]["modelBindings"][1],
            {
                "role": "implement auditor 1",
                "model": "opencodex/gpt-5.6-luna",
                "thinking": "xhigh",
                "api": "openai-responses",
            },
        )
        assert capture is not None
        self.assertIn("- Model: opencodex/gpt-5.6-luna", capture["args"][-1])
        self.assertIn("- Thinking: xhigh", capture["args"][-1])

        verify_invocation = self.verify_invocation()
        verify_invocation["auditors"] = [{"acOrdinal": 1, "linkedFlows": [1]}]
        completed, terminal, capture = self.run_runner(VERIFY, verify_invocation)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            terminal["preflight"]["modelBindings"][1],
            {
                "role": "verify auditor 1",
                "model": "opencodex/gpt-5.6-luna",
                "thinking": "xhigh",
                "api": "openai-responses",
            },
        )
        assert capture is not None
        self.assertIn("- Model: opencodex/gpt-5.6-luna", capture["args"][-1])
        self.assertIn("- Thinking: xhigh", capture["args"][-1])

    def test_explicit_auditor_bindings_override_luna_xhigh_defaults(self) -> None:
        implement_invocation = self.implement_invocation()
        implement_invocation["auditors"] = [
            {
                "slot": "override",
                "assignment": "Observe implementation",
                "model": "test/auditor",
                "thinking": "low",
            }
        ]
        completed, terminal, _capture = self.run_runner(
            IMPLEMENT, implement_invocation
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            terminal["preflight"]["modelBindings"][1]["model"], "test/auditor"
        )
        self.assertEqual(
            terminal["preflight"]["modelBindings"][1]["thinking"], "low"
        )

        verify_invocation = self.verify_invocation()
        verify_invocation["auditors"] = [
            {
                "acOrdinal": 1,
                "linkedFlows": [1],
                "model": "test/auditor",
                "thinking": "low",
            }
        ]
        completed, terminal, _capture = self.run_runner(VERIFY, verify_invocation)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            terminal["preflight"]["modelBindings"][1]["model"], "test/auditor"
        )
        self.assertEqual(
            terminal["preflight"]["modelBindings"][1]["thinking"], "low"
        )

    def test_role_specific_model_environment_supplies_deployment_binding(self) -> None:
        invocation = self.implement_invocation()
        invocation.pop("ownerModel")
        completed, terminal, capture = self.run_runner(
            IMPLEMENT,
            invocation,
            extra_env={"IIS_READY_IMPLEMENT_MODEL": "test/configured-owner"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["ownerModel"], "test/configured-owner")
        assert capture is not None
        args = capture["args"]
        self.assertEqual(args[args.index("--model") + 1], "test/configured-owner")

    def test_binding_preflight_reads_config_without_rewriting_it(self) -> None:
        before = (self.agent_dir / "models.json").read_bytes()
        completed, terminal, capture = self.run_runner(
            IMPLEMENT, self.implement_invocation()
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual((self.agent_dir / "models.json").read_bytes(), before)
        self.assertEqual(
            terminal["preflight"]["modelBindings"][0]["api"],
            "openai-responses",
        )
        self.assertIsNotNone(capture)

    def test_missing_exact_model_binding_fails_before_owner_start(self) -> None:
        invocation = self.implement_invocation()
        invocation["ownerModel"] = "test/missing-owner"
        completed, terminal, capture = self.run_runner(IMPLEMENT, invocation)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("absent from Pi models.json", terminal["error"])
        self.assertIsNone(capture)

    def test_unsupported_requested_thinking_fails_before_owner_start(self) -> None:
        invocation = self.implement_invocation()
        invocation["auditors"] = [
            {
                "slot": "limited",
                "assignment": "Observe implementation",
                "model": "test/limited-auditor",
                "thinking": "high",
                "oracleBrowser": False,
            }
        ]
        completed, terminal, capture = self.run_runner(IMPLEMENT, invocation)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("unsupported thinking=high", terminal["error"])
        self.assertIsNone(capture)

    def test_unavailable_model_api_auth_fails_before_owner_start(self) -> None:
        invocation = self.implement_invocation()
        invocation["ownerModel"] = "test/unavailable-owner"
        completed, terminal, capture = self.run_runner(
            IMPLEMENT,
            invocation,
            extra_env={"PI_STUB_HIDE_MODEL": "test/unavailable-owner"},
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("model/API/auth is unavailable", terminal["error"])
        self.assertIsNone(capture)

    def test_invalid_role_configuration_fails_before_pi_start(self) -> None:
        invocation = self.implement_invocation()
        invocation["auditors"] = [
            {
                "slot": f"slot-{index}",
                "assignment": "Observe implementation",
                "model": "test/auditor",
                "thinking": "high",
            }
            for index in range(4)
        ]
        completed, terminal, capture = self.run_runner(IMPLEMENT, invocation)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(terminal["processStatus"], "FAILED")
        self.assertIn("between 0 and 3", terminal["error"])
        self.assertIsNone(capture)

    def test_missing_canonical_terminal_result_is_transport_failure(self) -> None:
        completed, terminal, capture = self.run_runner(
            VERIFY,
            self.verify_invocation(),
            extra_env={"PI_STUB_INVALID": "1"},
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(terminal["processStatus"], "FAILED")
        self.assertIn("missing Verify Pi owner identity", terminal["error"])
        self.assertIsNotNone(capture)

    def test_verify_accepts_markdown_quoted_canonical_result_fields(self) -> None:
        completed, terminal, capture = self.run_runner(
            VERIFY,
            self.verify_invocation(),
            extra_env={"PI_STUB_QUOTED_RESULT": "1"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            terminal["workflow"],
            {
                "verdict": "FAILED",
                "progression": "NOT APPLICABLE",
                "ticketStatus": "ready",
            },
        )
        self.assertIsNotNone(capture)

    def test_verify_admission_failure_is_a_completed_not_started_workflow(self) -> None:
        completed, terminal, capture = self.run_runner(
            VERIFY,
            self.verify_invocation(),
            extra_env={"PI_STUB_NOT_STARTED": "1"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["processStatus"], "COMPLETED")
        self.assertEqual(
            terminal["workflow"],
            {"status": "NOT_STARTED", "reason": "CANONICAL TICKET INVALID"},
        )
        self.assertIsNotNone(capture)

    def test_deterministic_invalid_ticket_stops_before_pi_start(self) -> None:
        invalid_ticket = self.work / "TICKET-invalid.md"
        invalid_ticket.write_text("Status: ready\n", encoding="utf-8")
        invocation = self.implement_invocation()
        invocation["ticket"] = str(invalid_ticket)
        completed, terminal, capture = self.run_runner(IMPLEMENT, invocation)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["processStatus"], "COMPLETED")
        self.assertEqual(terminal["workflow"]["completion"], "BLOCKED")
        self.assertTrue(terminal["preflight"]["validatorResult"].startswith("INVALID:"))
        self.assertIsNone(capture)
        self.assertEqual(
            [event["event"] for event in self.progress_events(completed.stderr)],
            ["RUN_STARTED", "PREFLIGHT_FAILED", "RUN_COMPLETED"],
        )

    def test_project_root_mismatch_stops_before_pi_start(self) -> None:
        other_root = self.work / "other-project"
        other_root.mkdir()
        invocation = self.implement_invocation()
        invocation["projectRoot"] = str(other_root)
        completed, terminal, capture = self.run_runner(IMPLEMENT, invocation)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["workflow"]["completion"], "BLOCKED")
        self.assertIn("PROJECT ROOT MISMATCH", terminal["workflow"]["reason"])
        self.assertIsNone(capture)

    def test_done_ticket_requires_explicit_diagnostic_reverification(self) -> None:
        content = self.ticket.read_text(encoding="utf-8")
        self.ticket.write_text(content.replace("Status: ready", "Status: done", 1), encoding="utf-8")
        completed, terminal, capture = self.run_runner(VERIFY, self.verify_invocation())
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["workflow"]["status"], "NOT_STARTED")
        self.assertIn("status gate rejected done", terminal["workflow"]["reason"])
        self.assertIsNone(capture)

    def test_verify_rejects_product_mutation_after_child_exit(self) -> None:
        mutation = self.project / ".pi-runner-mutation-test.tmp"
        mutation.unlink(missing_ok=True)
        try:
            completed, terminal, capture = self.run_runner(
                VERIFY,
                self.verify_invocation(),
                extra_env={"PI_STUB_MUTATE_PRODUCT": str(mutation)},
            )
        finally:
            mutation.unlink(missing_ok=True)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(terminal["processStatus"], "FAILED")
        self.assertIn("mutated protected product content", terminal["error"])
        self.assertEqual(terminal["postcondition"]["status"], "FAILED")
        self.assertIsNotNone(capture)
        progress_names = [event["event"] for event in self.progress_events(completed.stderr)]
        self.assertLess(progress_names.index("POSTCONDITION_FAILED"), progress_names.index("RUN_FAILED"))

    def test_verify_uses_bounded_filesystem_guard_for_non_git_project(self) -> None:
        fixture = TicketFixture()
        fixture.write()
        try:
            invocation = self.verify_invocation()
            invocation["ticket"] = str(fixture.ticket_path)
            invocation["projectRoot"] = str(fixture.root)
            completed, terminal, capture = self.run_runner(VERIFY, invocation)
        finally:
            fixture.close()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["processStatus"], "COMPLETED")
        self.assertEqual(
            terminal["postcondition"]["scope"],
            "Full non-Git Project Root content excluding .git and the Ticket",
        )
        self.assertIsNotNone(capture)

    def test_verify_rejects_completed_claim_without_ticket_transition(self) -> None:
        completed, terminal, capture = self.run_runner(
            VERIFY,
            self.verify_invocation(),
            extra_env={"PI_STUB_COMPLETED": "1"},
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(terminal["processStatus"], "FAILED")
        self.assertIn("reported Ticket status done does not match observed ready", terminal["error"])
        self.assertIsNotNone(capture)

    def test_verify_accepts_exact_transition_and_normalizes_quoted_done_status(self) -> None:
        completed, terminal, capture = self.run_runner(
            VERIFY,
            self.verify_invocation(),
            extra_env={"PI_STUB_COMPLETED": "1", "PI_STUB_TRANSITION_TICKET": "1"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(terminal["processStatus"], "COMPLETED")
        self.assertEqual(terminal["workflow"]["ticketStatus"], "done")
        self.assertEqual(terminal["postcondition"]["ticketChange"], "READY_TO_DONE")
        self.assertIsNotNone(capture)


    def test_runner_forwards_cancellation_and_emits_cancelled_envelope(self) -> None:
        input_path = self.work / "cancel-invocation.json"
        capture_path = self.work / "cancel-capture.json"
        input_path.write_text(json.dumps(self.implement_invocation()), encoding="utf-8")
        input_path.chmod(0o600)
        env = {
            **os.environ,
            "IIS_PI_BIN": str(self.stub),
            "NODE_ENV": "test",
            "PI_STUB_CAPTURE": str(capture_path),
            "IIS_PI_AGENT_DIR": str(self.agent_dir),
            "PI_STUB_WAIT": "1",
        }
        process = subprocess.Popen(
            [str(IMPLEMENT), "--input", str(input_path)],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 5
        while not capture_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(capture_path.exists(), "Pi stub did not start")
        process.terminate()
        stdout, stderr = process.communicate(timeout=10)
        terminal = json.loads(stdout)
        self.assertEqual(process.returncode, 143, stderr)
        self.assertEqual(terminal["processStatus"], "CANCELLED")
        self.assertEqual(terminal["error"], "runner received SIGTERM")
        progress_names = [event["event"] for event in self.progress_events(stderr)]
        self.assertEqual(progress_names[-1], "RUN_CANCELLED")

    def test_world_readable_invocation_is_rejected_before_pi_start(self) -> None:
        input_path = self.work / "public-invocation.json"
        capture_path = self.work / "public-capture.json"
        input_path.write_text(json.dumps(self.implement_invocation()), encoding="utf-8")
        input_path.chmod(0o644)
        completed = subprocess.run(
            [str(IMPLEMENT), "--input", str(input_path)],
            cwd=ROOT,
            env={
                **os.environ,
                "NODE_ENV": "test",
                "IIS_PI_BIN": str(self.stub),
                "PI_STUB_CAPTURE": str(capture_path),
            },
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        terminal = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("must not grant group or other permissions", terminal["error"])
        self.assertFalse(capture_path.exists())


if __name__ == "__main__":
    unittest.main()
