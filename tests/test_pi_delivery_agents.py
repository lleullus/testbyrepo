from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
AGENTS = ROOT / ".pi" / "agents"
IMPLEMENT = AGENTS / "iis-ready-implement.md"
VERIFY = AGENTS / "iis-ready-verify.md"
IMPLEMENT_AUDITOR = AGENTS / "iis-implement-auditor.md"
VERIFY_AUDITOR = AGENTS / "iis-verify-auditor.md"
EXTENSION = ROOT / ".pi" / "extensions" / "iis-ready-audit" / "index.ts"
IMPLEMENT_SKILL = ROOT / "companion-skills" / "ready-ticket-implement" / "SKILL.md"
VERIFY_SKILL = ROOT / "companion-skills" / "ready-ticket-verify" / "SKILL.md"
IMPLEMENT_RUNNER = ROOT / "companion-skills" / "ready-ticket-implement" / "pi" / "iis-ready-implement-runner.mjs"
VERIFY_RUNNER = ROOT / "companion-skills" / "ready-ticket-verify" / "pi" / "iis-ready-verify-runner.mjs"
TRANSITION = ROOT / ".pi" / "lib" / "ticket-transition.mjs"
RUNNER_CORE = ROOT / ".pi" / "lib" / "pi-owner-runner.mjs"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def frontmatter(path: Path) -> str:
    parts = path.read_text(encoding="utf-8").split("---", 2)
    if len(parts) != 3:
        raise AssertionError(f"invalid frontmatter: {path}")
    return parts[1]


class PiDeliveryAgentTests(unittest.TestCase):
    def test_owner_agents_are_fresh_isolated_and_use_only_async_audit_tools(self) -> None:
        for path, name in (
            (IMPLEMENT, "iis-ready-implement"),
            (VERIFY, "iis-ready-verify"),
        ):
            meta = frontmatter(path)
            body = normalized(path)
            self.assertIn(f"name: {name}", meta)
            self.assertIn("iis_audit_start", meta)
            self.assertIn("iis_audit_reply", meta)
            self.assertIn("iis_audit_cancel", meta)
            self.assertIn("iis_audit_fan_in", meta)
            self.assertIn("maxDepth: 0", meta)
            self.assertNotIn("subagent", meta.split("tools:", 1)[1].splitlines()[0])
            self.assertIn("PI_SUBAGENT_SESSION", body)
            self.assertIn("must resolve to `none`", body)
            self.assertIn("unique run ID", body)
            self.assertIn("Never poll", body)

    def test_implement_owner_preserves_delivery_authority_boundary(self) -> None:
        body = normalized(IMPLEMENT)
        for required in (
            "references/lifecycle.md",
            "references/implement.md",
            "references/concurrent-auditors.md",
            "Never reinterpret planning authority",
            "write `Status: done`",
            "issue a verification verdict",
            "canonical companion `IMPLEMENT RESULT`",
        ):
            self.assertIn(required, body)

    def test_verify_owner_is_fresh_and_preserves_verifier_authority(self) -> None:
        body = normalized(VERIFY)
        for required in (
            "references/lifecycle.md",
            "references/verify.md",
            "references/ac-runtime-auditors.md",
            "Do not inherit or trust an Implement PI transcript",
            "Never use `bash` or any generic mutation tool for Ticket progression",
            "iis_ticket_mark_done",
            "canonical companion `READY TICKET VERIFICATION RESULT`",
        ):
            self.assertIn(required, body)

        meta = frontmatter(VERIFY)
        tools = meta.split("tools:", 1)[1].splitlines()[0]
        self.assertIn("iis_ticket_mark_done", tools)
        self.assertNotIn("edit", tools)
        self.assertNotIn("write", tools)

    def test_auditors_are_nonrecursive_read_only_profiles(self) -> None:
        for path in (IMPLEMENT_AUDITOR, VERIFY_AUDITOR):
            meta = frontmatter(path)
            body = normalized(path)
            tools = meta.split("tools:", 1)[1].splitlines()[0]
            self.assertIn("iis_audit_handoff", tools)
            self.assertNotIn("edit", tools)
            self.assertNotIn("write", tools)
            self.assertNotIn("subagent", tools)
            self.assertIn("maxDepth: 0", meta)
            self.assertIn("fresh isolated Pi session", body)
            self.assertIn("Oracle Browser only when", body)
            self.assertIn("Terminal Status: COMPLETED | BLOCKED | FAILED | CANCELLED", body)

    def test_project_agent_entries_link_to_companion_owned_sources(self) -> None:
        expected = {
            IMPLEMENT: ROOT / "companion-skills/ready-ticket-implement/pi/iis-ready-implement.md",
            IMPLEMENT_AUDITOR: ROOT
            / "companion-skills/ready-ticket-implement/pi/iis-implement-auditor.md",
            VERIFY: ROOT / "companion-skills/ready-ticket-verify/pi/iis-ready-verify.md",
            VERIFY_AUDITOR: ROOT
            / "companion-skills/ready-ticket-verify/pi/iis-verify-auditor.md",
        }
        for link, target in expected.items():
            self.assertTrue(link.is_symlink(), link)
            self.assertEqual(link.resolve(), target.resolve())

    def test_extension_discovers_oracle_without_copying_its_contract(self) -> None:
        source = EXTENSION.read_text(encoding="utf-8")
        self.assertIn("IIS_ORACLE_BROWSER_SKILL", source)
        self.assertIn("/home/user01/.codex/skills/oracle-browser/SKILL.md", source)
        self.assertIn('name: "oracle-browser"', source)
        self.assertIn("skillsOverride", source)
        self.assertIn("params.oracleBrowser ? await oracleSkill() : undefined", source)
        self.assertIn('if (input.oracleSkill) enabledTools.push("bash")', source)
        self.assertNotIn("browser-timeout 2h", source)

    def test_extension_exposes_background_handoff_fanin_and_containment(self) -> None:
        source = EXTENSION.read_text(encoding="utf-8")
        for required in (
            'name: "iis_audit_start"',
            'name: "iis_audit_handoff"',
            'name: "iis_audit_reply"',
            'name: "iis_audit_cancel"',
            'name: "iis_audit_fan_in"',
            'pi.on("session_shutdown"',
            "SessionManager.inMemory(spec.cwd)",
            'deliverAs: "steer"',
            "triggerTurn: true",
        ):
            self.assertIn(required, source)

    def test_public_skills_default_to_pi_and_preserve_only_explicit_direct_mode(self) -> None:
        for path, runner in (
            (IMPLEMENT_SKILL, "pi/iis-ready-implement-runner.mjs"),
            (VERIFY_SKILL, "pi/iis-ready-verify-runner.mjs"),
        ):
            body = normalized(path)
            self.assertIn("default and normal mode is `PI`", body)
            self.assertIn(runner, body)
            self.assertIn("private mode-`0600` temporary invocation JSON", body)
            self.assertIn("`DIRECT` is a preserved compatibility mode only", body)
            self.assertIn("Never choose it as fallback", body)
            self.assertIn("references/lifecycle.md", body)
            self.assertIn("cursor-based log follow", body)
            self.assertIn("before process exit", body)
            self.assertIn("`iis.pi.progress/v1`", body)
            self.assertIn("deduplicate replayed lower or equal sequences", body)

    def test_runners_enforce_deterministic_preflight_and_verify_postcondition(self) -> None:
        implement = IMPLEMENT_RUNNER.read_text(encoding="utf-8")
        verify = VERIFY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("runTicketPreflight", implement)
        self.assertIn("runTicketPreflight", verify)
        self.assertIn("captureVerificationPostcondition", verify)
        self.assertIn("verifyVerificationPostcondition", verify)
        self.assertIn("validateWorkflowPostcondition", verify)
        self.assertNotIn('"edit"', verify)

    def test_extension_exposes_only_guarded_ticket_progression_in_verify_mode(self) -> None:
        source = EXTENSION.read_text(encoding="utf-8")
        transition = TRANSITION.read_text(encoding="utf-8")
        self.assertIn('process.env.IIS_READY_TICKET_MODE === "VERIFY"', source)
        self.assertIn('name: "iis_ticket_mark_done"', source)
        self.assertIn("expectedSha256", source)
        self.assertIn("markTicketDone", source)
        self.assertIn('before.replace(/^Status: ready$/m, "Status: done")', transition)
        self.assertIn("rollback ${rollback}", transition)

    def test_runner_isolates_parent_environment_and_redacts_terminal_text(self) -> None:
        source = RUNNER_CORE.read_text(encoding="utf-8")
        self.assertIn("const env = {};", source)
        self.assertNotIn("...process.env", source)
        self.assertIn("sanitizeTerminalText", source)
        self.assertIn("invocation file must not grant group or other permissions", source)
        self.assertNotIn("process.stderr.write(text)", source)
        self.assertIn('const PROGRESS_SCHEMA = "iis.pi.progress/v1"', source)
        self.assertIn("parseAuditProgress", source)
        self.assertIn("IIS_PI_PROGRESS_PROTOCOL", source)
        self.assertIn("[invalid child audit progress event]", source)


if __name__ == "__main__":
    unittest.main()
