"""Slot-wise ChatGPT workspace URL mapping (approved design v0.2, D1-D9)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from oracle_browser_slots.cdp import LoginResult
from oracle_browser_slots.launcher import ChromeLauncher
from oracle_browser_slots.model import (
    CHATGPT_URLS_ENV,
    DEFAULT_CHATGPT_URL,
    Settings,
    validate_chatgpt_url,
)
from oracle_browser_slots.runner import JobRunner, OracleTransportError
from oracle_browser_slots.service import SlotService


TEST_ORACLE_CLI = "/tmp/oracle-test-bin/oracle"
SLOT3_URL = "https://chatgpt.com/g/g-p-69f9e842469881918478d6362f949164-codex/project"


class FakeLauncher:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def ensure_running(self, slot):
        self.calls.append(slot.slot_id)
        return None


class FakeCDP:
    def __init__(self, results: dict[int, LoginResult | Exception]) -> None:
        self.results = results

    def check_login(self, slot):
        result = self.results[slot.slot_id]
        if isinstance(result, Exception):
            raise result
        return result

    def browser_version(self, slot):
        return {
            "Browser": "FakeChrome/1",
            "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/browser/fake",
        }


class ReturnCodeChild:
    def __init__(self, return_code: int) -> None:
        self.return_code = return_code

    def wait(self):
        return self.return_code


def settings_for(root: Path, **overrides) -> Settings:
    values = dict(
        state_root=root / "state",
        profile_root=root / "profiles",
        chrome_path=root / "fake-chrome",
        port_base=19222,
        cdp_start_timeout=0.1,
        cdp_request_timeout=0.1,
    )
    values.update(overrides)
    return Settings(**values)


def ready_service(root: Path, **settings_overrides) -> SlotService:
    settings = settings_for(root, **settings_overrides)
    return SlotService(
        settings,
        cdp=FakeCDP({slot: LoginResult(True, "ready", "없음") for slot in (1, 2, 3, 4, 5)}),
        launcher=FakeLauncher(),
    )


class SettingsMappingTests(unittest.TestCase):
    def test_unset_env_has_no_mappings(self):
        env = {"HOME": "/home/test"}
        settings = Settings.from_env(env)
        self.assertEqual(settings.slot_chatgpt_urls, {})
        self.assertEqual(settings.chatgpt_url, DEFAULT_CHATGPT_URL)
        self.assertIsNone(settings.slot_chatgpt_url_override(3))
        self.assertEqual(settings.effective_launcher_url(3), DEFAULT_CHATGPT_URL)

    def test_partial_mapping_parses(self):
        env = {"HOME": "/home/test", CHATGPT_URLS_ENV: json.dumps({"3": SLOT3_URL})}
        settings = Settings.from_env(env)
        self.assertEqual(settings.slot_chatgpt_urls, {3: SLOT3_URL})
        self.assertEqual(settings.slot_chatgpt_url_override(3), SLOT3_URL)
        self.assertIsNone(settings.slot_chatgpt_url_override(4))

    def test_full_mapping_and_override_validation(self):
        env = {
            "HOME": "/home/test",
            CHATGPT_URLS_ENV: json.dumps(
                {"1": "https://chatgpt.com/g/a", "5": "https://chat.openai.com/g/b"}
            ),
        }
        settings = Settings.from_env(env)
        self.assertEqual(settings.slot_chatgpt_urls, {1: "https://chatgpt.com/g/a", 5: "https://chat.openai.com/g/b"})
        with self.assertRaises(ValueError):
            settings.slot_chatgpt_url_override(6)

    def test_malformed_json_raises(self):
        env = {"HOME": "/home/test", CHATGPT_URLS_ENV: "{not-json"}
        with self.assertRaises(ValueError):
            Settings.from_env(env)

    def test_non_object_json_raises(self):
        for raw in ("null", "[1]", '"x"', "3"):
            env = {"HOME": "/home/test", CHATGPT_URLS_ENV: raw}
            with self.assertRaises(ValueError):
                Settings.from_env(env)

    def test_invalid_key_raises(self):
        for key in ("6", "0", "x", "3.0"):
            env = {"HOME": "/home/test", CHATGPT_URLS_ENV: json.dumps({key: SLOT3_URL})}
            with self.assertRaises(ValueError):
                Settings.from_env(env)

    def test_non_string_value_raises(self):
        env = {"HOME": "/home/test", CHATGPT_URLS_ENV: '{"3": 42}'}
        with self.assertRaises(ValueError):
            Settings.from_env(env)

    def test_empty_and_whitespace_values_raise(self):
        for value in ("", "   "):
            env = {"HOME": "/home/test", CHATGPT_URLS_ENV: json.dumps({"3": value})}
            with self.assertRaises(ValueError):
                Settings.from_env(env)

    def test_duplicate_keys_raise(self):
        env = {
            "HOME": "/home/test",
            CHATGPT_URLS_ENV: '{"3":"https://chatgpt.com/g/a","3":"https://chatgpt.com/g/b"}',
        }
        with self.assertRaises(ValueError):
            Settings.from_env(env)

    def test_url_validation_matrix(self):
        invalid = [
            "http://chatgpt.com/g/x",
            "https://example.com/g/x",
            "https://chatgpt.com.evil.com/g/x",
            "https://chatgpt.com:8443/g/x",
            "https://user@chatgpt.com/g/x",
            "https://user:pass@chatgpt.com/g/x",
            "-https://chatgpt.com/g/x",
            "not a url",
            "ftp://chatgpt.com/g/x",
        ]
        for value in invalid:
            with self.assertRaises(ValueError, msg=value):
                validate_chatgpt_url(value, "test")
        valid = [
            "https://chatgpt.com/",
            "https://chatgpt.com/g/g-p-xxxx/project?tab=files",
            "https://chat.openai.com/g/y",
        ]
        for value in valid:
            self.assertEqual(validate_chatgpt_url(value, "test"), value)

    def test_global_url_validation_applies(self):
        env = {"HOME": "/home/test", "ORACLE_BROWSER_SLOTS_CHATGPT_URL": "https://example.com/"}
        with self.assertRaises(ValueError):
            Settings.from_env(env)
        env = {
            "HOME": "/home/test",
            "ORACLE_BROWSER_SLOTS_CHATGPT_URL": "https://chatgpt.com/g/global",
        }
        self.assertEqual(Settings.from_env(env).chatgpt_url, "https://chatgpt.com/g/global")

    def test_effective_launcher_url_priority(self):
        env = {
            "HOME": "/home/test",
            "ORACLE_BROWSER_SLOTS_CHATGPT_URL": "https://chatgpt.com/g/global",
            CHATGPT_URLS_ENV: json.dumps({"3": SLOT3_URL}),
        }
        settings = Settings.from_env(env)
        self.assertEqual(settings.effective_launcher_url(3), SLOT3_URL)
        self.assertEqual(settings.effective_launcher_url(1), "https://chatgpt.com/g/global")
        self.assertEqual(settings.effective_launcher_url(2), "https://chatgpt.com/g/global")


class RunnerMappingTests(unittest.TestCase):
    def _runner(self, root: Path, **overrides) -> JobRunner:
        service = ready_service(root, **overrides)
        return JobRunner(service, oracle_cli_path=TEST_ORACLE_CLI)

    def test_injection_when_slot_mapped(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(
                Path(directory),
                slot_chatgpt_urls={3: SLOT3_URL},
            )
            command = runner._validated_oracle_command(
                3, [TEST_ORACLE_CLI, "-p", "task"]
            )
            self.assertIn("--chatgpt-url", command)
            self.assertEqual(
                command[command.index("--chatgpt-url") + 1],
                SLOT3_URL,
            )

    def test_no_injection_without_mapping(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(Path(directory))
            command = runner._validated_oracle_command(
                3, [TEST_ORACLE_CLI, "-p", "task"]
            )
            self.assertNotIn("--chatgpt-url", command)
            self.assertNotIn("--browser-url", command)

    def test_caller_split_url_prevents_injection(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(
                Path(directory),
                slot_chatgpt_urls={3: SLOT3_URL},
            )
            caller = "https://chatgpt.com/g/caller"
            command = runner._validated_oracle_command(
                3, [TEST_ORACLE_CLI, "--chatgpt-url", caller, "-p", "task"]
            )
            self.assertEqual(
                command[command.index("--chatgpt-url") + 1],
                caller,
            )
            self.assertEqual(command.count("--chatgpt-url"), 1)

    def test_caller_equals_url_prevents_injection(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(
                Path(directory),
                slot_chatgpt_urls={3: SLOT3_URL},
            )
            caller = "https://chatgpt.com/g/caller"
            command = runner._validated_oracle_command(
                3, [TEST_ORACLE_CLI, f"--chatgpt-url={caller}", "-p", "task"]
            )
            self.assertIn(f"--chatgpt-url={caller}", command)
            self.assertEqual(command.count("--chatgpt-url"), 0)

    def test_browser_url_alias_prevents_injection(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(
                Path(directory),
                slot_chatgpt_urls={3: SLOT3_URL},
            )
            caller = "https://chatgpt.com/g/caller"
            command = runner._validated_oracle_command(
                3, [TEST_ORACLE_CLI, "--browser-url", caller, "-p", "task"]
            )
            self.assertEqual(
                command[command.index("--browser-url") + 1],
                caller,
            )
            self.assertNotIn("--chatgpt-url", command)

    def test_duplicate_alias_rejected(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(Path(directory))
            with self.assertRaises(OracleTransportError):
                runner._validated_oracle_command(
                    3,
                    [
                        TEST_ORACLE_CLI,
                        "--chatgpt-url",
                        "https://chatgpt.com/g/a",
                        "--chatgpt-url",
                        "https://chatgpt.com/g/b",
                        "-p",
                        "task",
                    ],
                )

    def test_cross_alias_rejected_even_when_same_value(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(Path(directory))
            with self.assertRaises(OracleTransportError):
                runner._validated_oracle_command(
                    3,
                    [
                        TEST_ORACLE_CLI,
                        "--chatgpt-url",
                        SLOT3_URL,
                        "--browser-url",
                        SLOT3_URL,
                        "-p",
                        "task",
                    ],
                )

    def test_empty_equals_rejected(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(Path(directory))
            with self.assertRaises(OracleTransportError):
                runner._validated_oracle_command(
                    3, [TEST_ORACLE_CLI, "--chatgpt-url=", "-p", "task"]
                )

    def test_missing_value_rejected(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(Path(directory))
            with self.assertRaises(OracleTransportError):
                runner._validated_oracle_command(
                    3, [TEST_ORACLE_CLI, "--chatgpt-url"]
                )

    def test_flag_like_value_rejected(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(Path(directory))
            with self.assertRaises(OracleTransportError):
                runner._validated_oracle_command(
                    3, [TEST_ORACLE_CLI, "--chatgpt-url", "-p", "task"]
                )

    def test_invalid_url_rejected(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(Path(directory))
            with self.assertRaises(OracleTransportError):
                runner._validated_oracle_command(
                    3,
                    [TEST_ORACLE_CLI, "--chatgpt-url", "https://example.com/x", "-p", "task"],
                )

    def test_injection_before_terminator_and_tokens_preserved(self):
        with TemporaryDirectory() as directory:
            runner = self._runner(
                Path(directory),
                slot_chatgpt_urls={3: SLOT3_URL},
            )
            command = runner._validated_oracle_command(
                3,
                [TEST_ORACLE_CLI, "-p", "task", "--", "-x", "--y"],
            )
            terminator = command.index("--")
            self.assertIn("--chatgpt-url", command[:terminator])
            self.assertEqual(command[terminator:], ["--", "-x", "--y"])

    def test_followup_suppresses_injection_through_claim(self):
        with TemporaryDirectory() as directory:
            service = ready_service(
                Path(directory),
                slot_chatgpt_urls={3: SLOT3_URL},
            )
            self.assertEqual(service.prepare(3)["status"], "사용 가능")
            runner = JobRunner(service, oracle_cli_path=TEST_ORACLE_CLI)
            claim = runner.claim_for_auto(
                3,
                "followup-request",
                [TEST_ORACLE_CLI, "-p", "continue"],
                apply_workspace_mapping=False,
            )
            self.assertTrue(claim["accepted"])
            self.assertNotIn("--chatgpt-url", claim["command"])

    def test_claim_injects_for_auto_assignment(self):
        with TemporaryDirectory() as directory:
            service = ready_service(
                Path(directory),
                slot_chatgpt_urls={3: SLOT3_URL},
            )
            self.assertEqual(service.prepare(3)["status"], "사용 가능")
            runner = JobRunner(service, oracle_cli_path=TEST_ORACLE_CLI)
            claim = runner.claim_for_auto(
                3,
                "auto-request",
                [TEST_ORACLE_CLI, "-p", "task"],
            )
            self.assertTrue(claim["accepted"])
            command = claim["command"]
            self.assertEqual(
                command[command.index("--chatgpt-url") + 1],
                SLOT3_URL,
            )

    def test_reallocation_recalculates_per_slot(self):
        with TemporaryDirectory() as directory:
            service = ready_service(
                Path(directory),
                slot_chatgpt_urls={
                    1: "https://chatgpt.com/g/one",
                    2: "https://chatgpt.com/g/two",
                },
            )
            self.assertEqual(service.prepare(1)["status"], "사용 가능")
            self.assertEqual(service.prepare(2)["status"], "사용 가능")
            runner = JobRunner(service, oracle_cli_path=TEST_ORACLE_CLI)
            first = runner.claim_for_auto(
                1, "request", [TEST_ORACLE_CLI, "-p", "task"]
            )
            second = runner.claim_for_auto(
                2, "request", [TEST_ORACLE_CLI, "-p", "task"]
            )
            self.assertIn("https://chatgpt.com/g/one", first["command"])
            self.assertIn("https://chatgpt.com/g/two", second["command"])

    def test_run_path_injects_mapping(self):
        with TemporaryDirectory() as directory:
            service = ready_service(
                Path(directory),
                slot_chatgpt_urls={3: SLOT3_URL},
            )
            self.assertEqual(service.prepare(3)["status"], "사용 가능")
            captured: dict[str, object] = {}

            def popen(argv, *, env, close_fds):
                captured["argv"] = argv
                return ReturnCodeChild(0)

            result = JobRunner(
                service,
                popen_factory=popen,
                oracle_cli_path=TEST_ORACLE_CLI,
            ).run(3, "mapped-run", [TEST_ORACLE_CLI, "-p", "task"])
            self.assertTrue(result["accepted"])
            argv = captured["argv"]
            self.assertIn("--chatgpt-url", argv)
            self.assertEqual(argv[argv.index("--chatgpt-url") + 1], SLOT3_URL)
            self.assertEqual(
                argv[argv.index("--remote-chrome") + 1],
                "127.0.0.1:19224",
            )


class LauncherMappingTests(unittest.TestCase):
    def test_initial_tab_uses_slot_mapping(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(
                Path(directory),
                slot_chatgpt_urls={3: SLOT3_URL},
            )
            launcher = ChromeLauncher(settings, cdp=FakeCDP({}))
            command = launcher._command(settings.slot(3))
            self.assertEqual(command[-1], SLOT3_URL)

    def test_initial_tab_uses_global_when_unmapped(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(
                Path(directory),
                chatgpt_url="https://chatgpt.com/g/global",
            )
            launcher = ChromeLauncher(settings, cdp=FakeCDP({}))
            command = launcher._command(settings.slot(2))
            self.assertEqual(command[-1], "https://chatgpt.com/g/global")

    def test_initial_tab_default_when_unset(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            launcher = ChromeLauncher(settings, cdp=FakeCDP({}))
            command = launcher._command(settings.slot(1))
            self.assertEqual(command[-1], DEFAULT_CHATGPT_URL)


if __name__ == "__main__":
    unittest.main()
