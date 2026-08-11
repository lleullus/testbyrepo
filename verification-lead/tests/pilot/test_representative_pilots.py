from __future__ import annotations

import hashlib
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


LEAF = Path(__file__).resolve().parents[2]
REPO = LEAF.parent
VALIDATOR = REPO / "matt/skills/to-tickets/validate_ticket.py"
if str(LEAF) not in sys.path:
    sys.path.insert(0, str(LEAF))

from verdict_contract import aggregate, classify_boundary


def spec_flow(
    *,
    boundary: str,
    trigger: str,
    expected: str,
    readback: str,
    disposition: str = "Independent",
    required: str = "yes",
    surface: str = "Existing | disposable local product",
    external: str = "None",
    conditional: str = "",
) -> str:
    return f"""- Outcome: {expected}
  Acceptance boundary: {boundary}
  Trigger or inspection target: {trigger}
  Expected observable result: {expected}
  Authoritative readback: {readback}
  Disposition: {disposition}
  Independent verification required: {required}
  Acceptance surface: {surface}
  External condition: {external}{conditional}"""


def ticket_flow(
    *,
    boundary: str,
    trigger: str,
    expected: str,
    readback: str,
    decision: str,
    disposition: str = "Independent",
    required: str = "yes",
    surface: str = "Existing | disposable local product",
    external: str = "None",
    conditional: str = "",
) -> str:
    return f"""- AC ordinals: 1
  Initial state: disposable fixture initial state
  Trigger or inspection target: {trigger}
  Acceptance boundary: {boundary}
  Expected observable result: {expected}
  Authoritative readback: {readback}
  Decision boundary: {decision}
  Disposition: {disposition}
  Independent verification required: {required}
  Acceptance surface: {surface}
  External condition: {external}{conditional}"""


class PilotFixture:
    def __init__(self, name: str) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.work = self.root / "docs/planning/work" / name
        self.tickets = self.work / "tickets"
        self.product = self.root / "product"
        self.tickets.mkdir(parents=True)
        self.product.mkdir()
        self.spec = self.work / "SPEC.md"
        self.ticket = self.tickets / "TICKET-001.md"

    def close(self) -> None:
        self.temporary.cleanup()

    def write_contract(self, spec_verification: str, ticket_verification: str) -> None:
        self.spec.write_text(
            f"""# Pilot Spec

Status: approved
Owner: pilot

## Verification Expectations

{spec_verification}

## Open Questions

None
""",
            encoding="utf-8",
        )
        self.ticket.write_text(
            f"""# Pilot Ticket

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: {self.root}
Worker:
UI: no

## Acceptance Criteria

- {ticket_verification.splitlines()[4].split(': ', 1)[1]}

## Scope

Disposable local product and its declared readback.

## Blockers

None

## Verification

{ticket_verification}
""",
            encoding="utf-8",
        )

    def validate(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(VALIDATOR), str(self.ticket)],
            cwd=self.root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def command(self, *argv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(argv),
            cwd=self.root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )


class RepresentativeVerificationPilots(unittest.TestCase):
    def test_a_local_cli_recipe_free_pass_and_direct_contradiction(self) -> None:
        for product_output, expected_verdict, expected_aggregate in (
            ("HELLO", "PASS", "VERIFIED"),
            ("WRONG", "FAIL", "FAILED"),
        ):
            with self.subTest(product_output=product_output):
                fixture = PilotFixture("pilot-a")
                self.addCleanup(fixture.close)
                cli = fixture.product / "cli.py"
                cli.write_text(
                    "import sys\n"
                    f"print({product_output!r} if sys.argv[1] == 'hello' else 'REJECTED')\n",
                    encoding="utf-8",
                )
                spec = spec_flow(
                    boundary="CLI stdout",
                    trigger="invoke product/cli.py with hello",
                    expected="stdout is HELLO",
                    readback="completed process stdout",
                )
                flow = ticket_flow(
                    boundary="CLI stdout",
                    trigger="invoke product/cli.py with hello",
                    expected="stdout is HELLO",
                    readback="completed process stdout",
                    decision="trimmed stdout equals HELLO or directly differs",
                )
                fixture.write_contract(spec, flow)
                self.assertNotIn("Recipe", fixture.ticket.read_text(encoding="utf-8"))
                self.assertEqual(fixture.validate().returncode, 0)
                source_before = cli.read_bytes()

                completed = fixture.command(sys.executable, "-B", str(cli), "hello")

                self.assertEqual(completed.returncode, 0)
                self.assertEqual(completed.stdout.strip(), product_output)
                verdict = "PASS" if completed.stdout.strip() == "HELLO" else "FAIL"
                self.assertEqual(verdict, expected_verdict)
                self.assertEqual(cli.read_bytes(), source_before)
                if expected_verdict == "PASS":
                    cli.write_text("print('CONCURRENT EDIT')\n", encoding="utf-8")
                    currentness_matches = cli.read_bytes() == source_before
                    self.assertFalse(currentness_matches)
                    verdict = classify_boundary(
                        admission_complete=True,
                        attempted=True,
                        contradiction=False,
                    )
                    self.assertEqual(verdict, "INCONCLUSIVE")
                    self.assertEqual(aggregate(1, [(1, verdict)]), "INCONCLUSIVE")
                else:
                    self.assertEqual(aggregate(1, [(1, verdict)]), expected_aggregate)

    def test_b_source_structure_uses_current_canonical_source_without_runtime(self) -> None:
        fixture = PilotFixture("pilot-b")
        self.addCleanup(fixture.close)
        source = fixture.product / "public_api.py"
        source.write_text("def exported_name():\n    return 'available'\n", encoding="utf-8")
        spec = spec_flow(
            boundary="current canonical source",
            trigger="inspect product/public_api.py",
            expected="source defines exported_name",
            readback="current file content",
        )
        flow = ticket_flow(
            boundary="current canonical source",
            trigger="inspect product/public_api.py",
            expected="source defines exported_name",
            readback="current file content",
            decision="the canonical source contains the exported_name definition",
        )
        fixture.write_contract(spec, flow)
        self.assertEqual(fixture.validate().returncode, 0)
        before = source.read_bytes()

        observed = source.resolve(strict=True).read_text(encoding="utf-8")

        self.assertIn("def exported_name():", observed)
        self.assertEqual(aggregate(1, [(1, "PASS")]), "VERIFIED")
        self.assertEqual(source.read_bytes(), before)

    def test_c_negative_rejection_and_unchanged_authoritative_state(self) -> None:
        fixture = PilotFixture("pilot-c")
        self.addCleanup(fixture.close)
        state = fixture.product / "state.txt"
        state.write_text("original\n", encoding="utf-8")
        cli = fixture.product / "rejecting_cli.py"
        cli.write_text(
            "import pathlib, sys\n"
            "state = pathlib.Path(sys.argv[1])\n"
            "if sys.argv[2] == 'forbidden':\n"
            "    print('REJECTED: forbidden input', file=sys.stderr)\n"
            "    raise SystemExit(2)\n"
            "state.write_text(sys.argv[2] + '\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        spec = spec_flow(
            boundary="product CLI rejection and state file",
            trigger="invoke rejecting_cli.py with forbidden",
            expected="input is rejected and state remains unchanged",
            readback="process status and current state.txt bytes",
        )
        flow = ticket_flow(
            boundary="product CLI rejection and state file",
            trigger="invoke rejecting_cli.py with forbidden",
            expected="input is rejected and state remains unchanged",
            readback="process status and current state.txt bytes",
            decision="status is 2 with authoritative rejection and byte-identical state",
        )
        fixture.write_contract(spec, flow)
        self.assertEqual(fixture.validate().returncode, 0)
        source_before = cli.read_bytes()
        state_before = hashlib.sha256(state.read_bytes()).hexdigest()

        completed = fixture.command(sys.executable, "-B", str(cli), str(state), "forbidden")

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr.strip(), "REJECTED: forbidden input")
        self.assertEqual(hashlib.sha256(state.read_bytes()).hexdigest(), state_before)
        self.assertEqual(aggregate(1, [(1, "PASS")]), "VERIFIED")
        self.assertEqual(cli.read_bytes(), source_before)

    def test_d_persistence_crosses_process_lifecycle_with_same_sqlite_identity(self) -> None:
        fixture = PilotFixture("pilot-d")
        self.addCleanup(fixture.close)
        database = fixture.product / "product.sqlite3"
        cli = fixture.product / "persistent_cli.py"
        cli.write_text(
            "import sqlite3, sys\n"
            "db, action = sys.argv[1:3]\n"
            "with sqlite3.connect(db) as connection:\n"
            "    connection.execute('create table if not exists values_seen (value text)')\n"
            "    if action == 'write':\n"
            "        connection.execute('insert into values_seen values (?)', (sys.argv[3],))\n"
            "        connection.commit()\n"
            "        print('STORED')\n"
            "    else:\n"
            "        print(connection.execute('select value from values_seen order by rowid').fetchone()[0])\n",
            encoding="utf-8",
        )
        conditional = (
            "\n  Persistence storage identity and lifecycle boundary: same canonical SQLite path after writer process exit"
        )
        spec = spec_flow(
            boundary="SQLite-backed product CLI",
            trigger="write retained-value, end process, then run read",
            expected="post-boundary read returns retained-value",
            readback="read process stdout and same SQLite database path",
            conditional=conditional,
        )
        flow = ticket_flow(
            boundary="SQLite-backed product CLI",
            trigger="write retained-value, end process, then run read",
            expected="post-boundary read returns retained-value",
            readback="read process stdout and same SQLite database path",
            decision="fresh read process and direct database read both return retained-value",
            conditional=conditional,
        )
        fixture.write_contract(spec, flow)
        self.assertEqual(fixture.validate().returncode, 0)
        source_before = cli.read_bytes()

        writer = fixture.command(sys.executable, "-B", str(cli), str(database), "write", "retained-value")
        reader = fixture.command(sys.executable, "-B", str(cli), str(database), "read")
        with sqlite3.connect(database.resolve(strict=True)) as connection:
            direct_readback = connection.execute("select value from values_seen order by rowid").fetchone()[0]

        self.assertEqual((writer.returncode, writer.stdout.strip()), (0, "STORED"))
        self.assertEqual((reader.returncode, reader.stdout.strip()), (0, "retained-value"))
        self.assertEqual(direct_readback, "retained-value")
        self.assertTrue(database.is_file())
        self.assertEqual(aggregate(1, [(1, "PASS")]), "VERIFIED")
        self.assertEqual(cli.read_bytes(), source_before)

    def test_e_external_effect_boundaries_never_execute_without_exact_authority(self) -> None:
        fixture = PilotFixture("pilot-e")
        self.addCleanup(fixture.close)
        marker = fixture.product / "external-effect.marker"
        unsafe = fixture.product / "unsafe_effect.py"
        unsafe.write_text(
            "import pathlib, sys\npathlib.Path(sys.argv[1]).write_text('executed', encoding='utf-8')\n",
            encoding="utf-8",
        )
        operator_kwargs = {
            "disposition": "Operator-assisted",
            "required": "no",
            "surface": "Operator-owned | shared production account",
            "external": "named operator credential and exact production authorization",
        }
        fixture.write_contract(
            spec_flow(
                boundary="shared production side effect",
                trigger="send production action",
                expected="production action is observed",
                readback="operator-owned production audit",
                **operator_kwargs,
            ),
            ticket_flow(
                boundary="shared production side effect",
                trigger="send production action",
                expected="production action is observed",
                readback="operator-owned production audit",
                decision="operator confirms exact production audit entry",
                **operator_kwargs,
            ),
        )
        self.assertEqual(fixture.validate().returncode, 0)
        chat_approval = "yes, approved in chat"

        non_independent = classify_boundary(
            admission_complete=False,
            attempted=False,
            contradiction=False,
        )

        self.assertEqual(non_independent, "VERIFICATION NOT STARTED")
        self.assertNotEqual(chat_approval, "named operator credential and exact production authorization")
        self.assertFalse(marker.exists())

        independent = PilotFixture("pilot-e-independent")
        self.addCleanup(independent.close)
        independent_marker = independent.product / "external-effect.marker"
        independent_unsafe = independent.product / "unsafe_effect.py"
        independent_unsafe.write_bytes(unsafe.read_bytes())
        independent.write_contract(
            spec_flow(
                boundary="authorized external-effect endpoint",
                trigger="perform exact authorized action",
                expected="external audit contains the action",
                readback="exact external audit readback",
                external="IIS_PILOT_EXTERNAL_AUTH token must remain present",
            ),
            ticket_flow(
                boundary="authorized external-effect endpoint",
                trigger="perform exact authorized action",
                expected="external audit contains the action",
                readback="exact external audit readback",
                decision="exact external audit contains the attributable action",
                external="IIS_PILOT_EXTERNAL_AUTH token must remain present",
            ),
        )
        self.assertEqual(independent.validate().returncode, 0)
        environment = {**os.environ, "IIS_PILOT_EXTERNAL_AUTH": "exact-authority"}
        self.assertEqual(environment["IIS_PILOT_EXTERNAL_AUTH"], "exact-authority")
        environment.pop("IIS_PILOT_EXTERNAL_AUTH")

        authority_present_at_attempt = environment.get("IIS_PILOT_EXTERNAL_AUTH") == "exact-authority"
        runtime_boundary = classify_boundary(
            admission_complete=True,
            attempted=True,
            contradiction=False,
        )

        self.assertFalse(authority_present_at_attempt)
        self.assertEqual(runtime_boundary, "INCONCLUSIVE")
        self.assertFalse(independent_marker.exists())
        self.assertEqual(independent_unsafe.read_bytes(), unsafe.read_bytes())

    def test_f_undefined_contract_readback_stops_before_product_execution(self) -> None:
        fixture = PilotFixture("pilot-f")
        self.addCleanup(fixture.close)
        marker = fixture.product / "execution.marker"
        product = fixture.product / "product.py"
        product.write_text(
            "import pathlib, sys\npathlib.Path(sys.argv[1]).write_text('executed', encoding='utf-8')\n",
            encoding="utf-8",
        )
        spec = spec_flow(
            boundary="local product output",
            trigger="invoke product.py",
            expected="product completes",
            readback="current product output",
        )
        flow = ticket_flow(
            boundary="local product output",
            trigger="invoke product.py",
            expected="product completes",
            readback="current product output",
            decision="defined readback shows completion",
        ).replace("  Authoritative readback: current product output\n", "")
        fixture.write_contract(spec, flow)

        validation = fixture.validate()
        result = classify_boundary(admission_complete=False, attempted=False, contradiction=False)

        self.assertEqual(validation.returncode, 2)
        self.assertIn("core labels", validation.stderr)
        self.assertEqual(result, "VERIFICATION NOT STARTED")
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
