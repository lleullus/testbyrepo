from __future__ import annotations

import importlib.util
import inspect
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


interface = load("implementation_verification", ROOT / "implementation_verification.py")
load("durable_work", ROOT / "durable_work.py")
load("durable_backend", ROOT / "durable_backend.py")
load("implementation_execution", ROOT / "implementation_execution.py")
load("verification_execution", ROOT / "verification_execution.py")
production = load("production_adapters", ROOT / "production_adapters.py")
entrypoint = load("production_entrypoint", ROOT / "production_entrypoint.py")


FAKE_OPENCODE = """#!/usr/bin/python3
import json, os, sys, time

scenario = os.environ.get('FAKE_OPENCODE_SCENARIO', 'valid')
if sys.argv[1:3] == ['agent', 'list']:
    print('luna (primary)' if scenario == 'missing-agent' else 'terra (primary)\\nluna (primary)')
    raise SystemExit(0)
if scenario == 'nonzero':
    raise SystemExit(7)
if scenario == 'timeout':
    time.sleep(1)
if scenario == 'warning':
    sys.stderr.write('default agent warning')
if scenario == 'malformed-jsonl':
    print('{not json')
    raise SystemExit(0)
if scenario == 'missing-finish':
    print(json.dumps({'type': 'step_start', 'sessionID': 's'}))
    print(json.dumps({'type': 'text', 'sessionID': 's', 'part': {'type': 'text', 'text': '{"decision":"CLOSE"}'}}))
    raise SystemExit(0)
if scenario == 'multiple-text':
    print(json.dumps({'type': 'step_start', 'sessionID': 's'}))
    print(json.dumps({'type': 'text', 'sessionID': 's', 'part': {'type': 'text', 'text': '{"decision":"CLOSE"}'}}))
    print(json.dumps({'type': 'text', 'sessionID': 's', 'part': {'type': 'text', 'text': '{"decision":"CLOSE"}'}}))
    print(json.dumps({'type': 'step_finish', 'sessionID': 's'}))
    raise SystemExit(0)
if scenario == 'wrong-order':
    print(json.dumps({'type': 'text', 'sessionID': 's', 'part': {'type': 'text', 'text': '{"decision":"CLOSE"}'} }))
    print(json.dumps({'type': 'step_start', 'sessionID': 's'}))
    print(json.dumps({'type': 'step_finish', 'sessionID': 's'}))
    raise SystemExit(0)
if scenario == 'malformed-text':
    response = 'not-json'
elif scenario == 'singleton-plan':
    response = '{"observationIdentity":"source","kind":"SOURCE","criterionIndexes":[1],"requests":[{"path":"app.txt"}],"expected":"implemented"}'
elif scenario == 'assessment-envelope':
    response = '{"responses":[{"criterionIndex":1,"outcome":"SATISFIED","evidenceObservationIdentities":["source"]}]}'
elif scenario == 'fallback-agent':
    response = '{"decision":"CLOSE"}'
else:
    prompt = sys.argv[-1]
    if '"operation":"PLAN"' in prompt:
        response = '[{"observationIdentity":"source","kind":"SOURCE","criterionIndexes":[1],"requests":[{"path":"app.txt"}],"expected":"implemented"}]'
    elif '"operation":"ASSESS"' in prompt:
        response = '[{"criterionIndex":1,"outcome":"SATISFIED","evidenceObservationIdentities":["source"]}]'
    elif '"operation":"ASSIGNMENT"' in prompt and scenario == 'assign' and '"text":"baseline"' in prompt:
        response = '{"decision":"ASSIGN","assignment":{"path":"app.txt","value":"implemented"}}'
    else:
        response = '{"decision":"CLOSE"}'
agent = 'luna' if scenario == 'fallback-agent' else sys.argv[sys.argv.index('--agent') + 1]
print(json.dumps({'type': 'step_start', 'sessionID': 's', 'agent': agent}))
print(json.dumps({'type': 'text', 'sessionID': 's', 'agent': agent, 'part': {'type': 'text', 'text': response}}))
print(json.dumps({'type': 'step_finish', 'sessionID': 's', 'agent': agent}))
"""


class OpenCodeRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fake = self.root / "fake-opencode"
        self.fake.write_text(FAKE_OPENCODE, encoding="utf-8")
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IXUSR)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def runner(self, *, timeout: float = 2):
        return production.OpenCodeRunner(self.fake, timeout_seconds=timeout)

    def test_jsonl_parser_accepts_only_one_strict_text_value(self) -> None:
        with patch.dict(os.environ, {"FAKE_OPENCODE_SCENARIO": "valid"}):
            self.assertEqual({"decision": "CLOSE"}, self.runner().invoke("terra", {"operation": "TEST"}))

    def test_jsonl_parser_fails_closed_for_process_and_protocol_failures(self) -> None:
        for scenario in (
            "nonzero",
            "timeout",
            "warning",
            "malformed-jsonl",
            "missing-finish",
            "multiple-text",
            "wrong-order",
            "malformed-text",
            "fallback-agent",
            "missing-agent",
        ):
            with self.subTest(scenario=scenario), patch.dict(
                os.environ, {"FAKE_OPENCODE_SCENARIO": scenario}
            ):
                with self.assertRaises(production.OpenCodeInvocationError):
                    self.runner(timeout=0.01 if scenario == "timeout" else 2).invoke(
                        "terra", {"operation": "TEST"}
                    )

    def _ticket(self, product: Path) -> Path:
        spec = self.root / "SPEC.md"
        spec.write_text(
            "# Spec\nStatus: approved\nOwner: test\n\n"
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
        ticket = self.root / "TICKET.md"
        ticket.write_text(
            "# Ticket\nStatus: ready\n"
            f"Parent-Spec: {spec}\nProject-Root: {product}\nWorker: ignored\nUI: no\n\n"
            "## Goal\nImplement.\n\n## Acceptance Criteria\n- app is implemented\n\n"
            "## Scope\napp.txt\n\n## Non-Goals\nNone.\n\n## Blockers\nNone.\n\n"
            "## Verification\nRead app.\n\n## References\nNone.\n",
            encoding="utf-8",
        )
        return ticket

    def test_fixed_route_exercises_zero_mutation_verify_and_inspect(self) -> None:
        product = self.root / "product"
        product.mkdir()
        (product / "app.txt").write_text("implemented", encoding="utf-8")
        ticket = self._ticket(product)
        with patch.dict(os.environ, {"FAKE_OPENCODE_SCENARIO": "valid"}):
            module = entrypoint.create_production_module(self.root / "state", self.fake)
            candidate = module.implement(ticket, production.TerraWorker())
            result = module.verify(candidate)
            inspection = module.inspect(ticket)
        self.assertIsInstance(candidate, interface.Candidate)
        self.assertEqual((), candidate.implementation_changes)
        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(result, inspection.result)
        self.assertEqual(interface.Currentness.CURRENT, inspection.currentness)
        self.assertEqual("implemented", (product / "app.txt").read_text(encoding="utf-8"))

    def test_fixed_route_stops_assignment_before_canonical_write(self) -> None:
        product = self.root / "product"
        product.mkdir()
        (product / "app.txt").write_text("baseline", encoding="utf-8")
        ticket = self._ticket(product)
        with patch.dict(os.environ, {"FAKE_OPENCODE_SCENARIO": "assign"}):
            module = entrypoint.create_production_module(self.root / "state", self.fake)
            result = module.implement(ticket, production.TerraWorker())
        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual("conditional source adoption is unavailable", result.reason)
        self.assertEqual("baseline", (product / "app.txt").read_text(encoding="utf-8"))

    def test_open_code_projection_excludes_canonical_and_state_paths(self) -> None:
        product = self.root / "product"
        product.mkdir()
        (product / "app.txt").write_text("implemented", encoding="utf-8")
        ticket = self._ticket(product)
        observed: list[str] = []
        original = production.OpenCodeRunner.invoke

        def recording_invoke(runner, agent, request):
            observed.append(production._json_bytes(request).decode("utf-8"))
            return original(runner, agent, request)

        with patch.dict(os.environ, {"FAKE_OPENCODE_SCENARIO": "valid"}), patch.object(
            production.OpenCodeRunner, "invoke", recording_invoke
        ):
            module = entrypoint.create_production_module(self.root / "state", self.fake)
            candidate = module.implement(ticket, production.TerraWorker())
            module.verify(candidate)

        self.assertTrue(observed)
        for value in observed:
            self.assertNotIn(str(product), value)
            self.assertNotIn(str(self.root / "state"), value)
            self.assertNotIn(str(ticket), value)

    def test_same_plan_and_evidence_reuses_the_fresh_luna_assessment(self) -> None:
        product = self.root / "product"
        product.mkdir()
        (product / "app.txt").write_text("implemented", encoding="utf-8")
        ticket = self._ticket(product)
        calls: list[tuple[str, str]] = []
        original = production.OpenCodeRunner.invoke

        def recording_invoke(runner, agent, request):
            calls.append((agent, str(request["operation"])))
            return original(runner, agent, request)

        with patch.dict(os.environ, {"FAKE_OPENCODE_SCENARIO": "valid"}), patch.object(
            production.OpenCodeRunner, "invoke", recording_invoke
        ):
            module = entrypoint.create_production_module(self.root / "state", self.fake)
            candidate = module.implement(ticket, production.TerraWorker())
            result = module.verify(candidate)

        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(1, calls.count(("luna", "ASSESS")))

    def test_luna_singleton_plan_and_exact_assessment_envelope_are_canonicalized(self) -> None:
        self.assertEqual(
            [{"observationIdentity": "source"}],
            production._luna_plan_items({"observationIdentity": "source"}),
        )
        self.assertEqual(
            [{"criterionIndex": 1}],
            production._luna_assessment_items({"responses": [{"criterionIndex": 1}]}),
        )
        with self.assertRaises(ValueError):
            production._luna_assessment_items({"responses": [], "unexpected": True})

    def test_public_surface_accepts_only_ticket_and_fixed_terra_designation(self) -> None:
        self.assertEqual(
            ("self", "work", "worker"),
            tuple(inspect.signature(interface.ImplementationVerificationModule.implement).parameters),
        )
        self.assertEqual(
            ("self", "candidate"),
            tuple(inspect.signature(interface.ImplementationVerificationModule.verify).parameters),
        )
        self.assertEqual(
            ("self", "work"),
            tuple(inspect.signature(interface.ImplementationVerificationModule.inspect).parameters),
        )
        with self.assertRaises(ValueError):
            production.TerraWorker("not-terra")


if __name__ == "__main__":
    unittest.main()
