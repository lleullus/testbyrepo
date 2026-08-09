from __future__ import annotations

from datetime import datetime, timezone
import json
import multiprocessing
import os
from pathlib import Path
import signal
import socketserver
import struct
import subprocess
import sys
import threading
import time
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from oracle_browser_slots.attachments import FileAttachmentPolicy
from oracle_browser_slots.cdp import CDPError, LoginResult
from oracle_browser_slots.followup import (
    FollowupError,
    FollowupRunner,
    OracleSessionRepository,
)
from oracle_browser_slots.model import AVAILABLE, OCCUPIED, Settings
from oracle_browser_slots.runner import JobRunner
from oracle_browser_slots.service import SlotService


TEST_ORACLE_CLI = "/tmp/oracle-followup-test-bin/oracle"
CONVERSATION_ID = "11111111-2222-3333-4444-555555555555"
CONVERSATION_URL = f"https://chatgpt.com/c/{CONVERSATION_ID}"


class FakeLauncher:
    def ensure_running(self, slot):
        return None


class FakeCDP:
    def __init__(
        self, slot_ids=(1, 2, 3, 4, 5), *, restore_error: Exception | None = None
    ) -> None:
        self.slot_ids = set(slot_ids)
        self.restore_error = restore_error
        self.restore_calls: list[tuple[int, str]] = []

    def check_login(self, slot):
        if slot.slot_id not in self.slot_ids:
            raise AssertionError(f"unexpected login check for slot {slot.slot_id}")
        return LoginResult(True, "ready", "없음")

    def browser_version(self, slot):
        return {
            "Browser": "FakeChrome/1",
            "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/browser/fake",
        }

    def restore_archived_conversation(self, slot, conversation_url):
        self.restore_calls.append((slot.slot_id, conversation_url))
        if self.restore_error is not None:
            raise self.restore_error
        return {"conversation_url": conversation_url}


class ReturnCodeChild:
    def __init__(self, return_code: int) -> None:
        self.return_code = return_code

    def wait(self, timeout=None):
        return self.return_code


def settings_for(root: Path, *, port_base: int = 29222) -> Settings:
    return Settings(
        state_root=root / "state",
        profile_root=root / "profiles",
        chrome_path=root / "fake-chrome",
        port_base=port_base,
        cdp_start_timeout=0.1,
        cdp_request_timeout=0.2,
        queue_poll_interval=0.01,
    )


def _iso(hour: int) -> str:
    return f"2026-08-01T{hour:02d}:00:00Z"


def write_stock_session(
    oracle_home: Path,
    settings: Settings,
    session_id: str,
    *,
    context_id: str = "ctx-main",
    slot_id: int = 2,
    status: str = "completed",
    created_at: str = "2026-08-01T00:00:00Z",
    terminated: bool = True,
    conversation_id: str | None = CONVERSATION_ID,
    conversation_url: str | None = CONVERSATION_URL,
    archived: bool = False,
    include_origin: bool = True,
    include_context: bool = True,
    parent_session_id: str | None = None,
    prompt_submitted: bool = True,
    response: str = "stored answer",
) -> Path:
    slot = settings.slot(slot_id)
    browser_config = {
        "remoteChrome": {"host": "127.0.0.1", "port": slot.port},
        "url": "https://chatgpt.com/",
        "modelStrategy": "current",
    }
    runtime = {
        "chromeHost": "127.0.0.1",
        "chromePort": slot.port,
        "promptSubmitted": prompt_submitted,
    }
    if conversation_id is not None:
        runtime["conversationId"] = conversation_id
    if conversation_url is not None:
        runtime["tabUrl"] = conversation_url
    options = {
        "slug": session_id,
        "mode": "browser",
        "model": "gpt-5.6",
        "browserConfig": browser_config,
    }
    if parent_session_id is not None:
        options["followupSessionId"] = parent_session_id
    metadata = {
        "id": session_id,
        "createdAt": created_at,
        "completedAt": created_at,
        "status": status,
        "mode": "browser",
        "model": "gpt-5.6",
        "options": options,
        "browser": {
            "config": browser_config,
            "runtime": runtime,
            "archive": {"archived": archived},
        },
    }
    namespace = {
        "schema_version": 1,
        "oracle_cli": {
            "operation": "followup" if parent_session_id else "submit",
            "request_id": session_id,
            "terminated": terminated,
            "terminated_at": created_at,
            "exit_code": 0,
        },
    }
    if include_context:
        namespace["opencode_conversation_id"] = context_id
    if include_origin:
        namespace["originating_slot"] = {
            "slot_id": slot_id,
            "port": slot.port,
            "profile_dir": str(slot.profile_dir),
            "remote_chrome": f"127.0.0.1:{slot.port}",
        }
    metadata["oracle_browser_slots"] = namespace
    session_directory = oracle_home / "sessions" / session_id
    session_directory.mkdir(parents=True)
    (session_directory / "meta.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (session_directory / "output.log").write_text(response, encoding="utf-8")
    return session_directory


def write_unregistered_stock_session(
    oracle_home: Path,
    settings: Settings,
    session_id: str,
    *,
    slot_id: int,
) -> None:
    directory = write_stock_session(
        oracle_home,
        settings,
        session_id,
        slot_id=slot_id,
    )
    metadata_path = directory / "meta.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.pop("oracle_browser_slots")
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")


def option_value(argv: list[str], flag: str) -> str | None:
    for index, token in enumerate(argv):
        if token == flag and index + 1 < len(argv):
            return argv[index + 1]
        if token.startswith(f"{flag}="):
            return token.split("=", 1)[1]
    return None


class FakeOracleFactory:
    def __init__(self, oracle_home: Path) -> None:
        self.oracle_home = oracle_home
        self.calls: list[dict[str, object]] = []

    def __call__(self, argv, *, env, close_fds):
        command = list(argv)
        self.calls.append({"argv": command, "env": dict(env), "close_fds": close_fds})
        parent_id = option_value(command, "--followup")
        child_id = option_value(command, "--slug")
        remote = option_value(command, "--remote-chrome")
        if parent_id is None or child_id is None or remote is None:
            raise AssertionError(f"missing follow-up correlation options: {command}")
        parent = json.loads(
            (self.oracle_home / "sessions" / parent_id / "meta.json").read_text(
                encoding="utf-8"
            )
        )
        host, raw_port = remote.rsplit(":", 1)
        port = int(raw_port)
        prompt = option_value(command, "-p") or "follow-up"
        browser_config = dict(parent["browser"]["config"])
        browser_config["remoteChrome"] = {"host": host, "port": port}
        child = {
            "id": child_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "completedAt": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "mode": "browser",
            "model": "gpt-5.6",
            "options": {
                "slug": child_id,
                "mode": "browser",
                "model": "gpt-5.6",
                "prompt": prompt,
                "followupSessionId": parent_id,
                "browserConfig": browser_config,
            },
            "browser": {
                "config": browser_config,
                "runtime": {
                    "chromeHost": host,
                    "chromePort": port,
                    "conversationId": parent["browser"]["runtime"]["conversationId"],
                    "tabUrl": parent["browser"]["runtime"]["tabUrl"],
                    "promptSubmitted": True,
                },
                "archive": {"archived": False},
            },
        }
        file_value = option_value(command, "--file")
        if file_value is not None:
            child["options"]["file"] = [file_value]
        child_directory = self.oracle_home / "sessions" / child_id
        child_directory.mkdir(parents=True)
        (child_directory / "meta.json").write_text(
            json.dumps(child, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (child_directory / "output.log").write_text(
            f"Answer:\ncontinued response for {prompt}\n", encoding="utf-8"
        )
        return ReturnCodeChild(0)


def cancellation_waiter_process(settings, oracle_home, result_queue):
    service = SlotService(settings, cdp=FakeCDP(), launcher=FakeLauncher())

    def forbidden_popen(argv, *, env, close_fds):
        raise AssertionError("cancelled waiter must not spawn stock Oracle")

    runner = JobRunner(
        service,
        popen_factory=forbidden_popen,
        oracle_cli_path=TEST_ORACLE_CLI,
    )
    repository = OracleSessionRepository(settings, oracle_home=oracle_home)
    result = FollowupRunner(
        service,
        runner=runner,
        repository=repository,
        poll_interval=0.01,
    ).run(
        "cancel-waiter",
        "ctx-main",
        [TEST_ORACLE_CLI, "-p", "cancel me"],
        emit=result_queue.put,
    )
    result_queue.put({"result": result})


class ParentSelectionTests(unittest.TestCase):
    def test_newest_eligible_uses_termination_conversation_and_managed_origin_not_labels(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            oracle_home = root / "oracle-home"
            repository = OracleSessionRepository(settings, oracle_home=oracle_home)

            write_stock_session(
                oracle_home,
                settings,
                "eligible-completed",
                status="completed",
                created_at=_iso(1),
            )
            write_stock_session(
                oracle_home,
                settings,
                "eligible-error-archived",
                status="error",
                archived=True,
                created_at=_iso(2),
            )
            write_stock_session(
                oracle_home,
                settings,
                "eligible-cancelled",
                status="cancelled",
                created_at=_iso(3),
            )
            write_stock_session(
                oracle_home,
                settings,
                "active-running",
                status="running",
                terminated=True,
                created_at=_iso(8),
            )
            write_stock_session(
                oracle_home,
                settings,
                "missing-conversation",
                conversation_id=None,
                conversation_url=None,
                created_at=_iso(9),
            )
            write_stock_session(
                oracle_home,
                settings,
                "missing-origin",
                include_origin=False,
                created_at=_iso(10),
            )
            write_stock_session(
                oracle_home,
                settings,
                "foreign-context",
                context_id="ctx-other",
                created_at=_iso(11),
            )

            parent, mode = repository.select_parent("ctx-main")
            self.assertEqual(mode, "implicit")
            self.assertEqual(parent.session_id, "eligible-cancelled")
            self.assertEqual(parent.slot_id, 2)

            for session_id in (
                "eligible-completed",
                "eligible-error-archived",
                "eligible-cancelled",
            ):
                with self.subTest(session_id=session_id):
                    explicit, explicit_mode = repository.select_parent(
                        "ctx-main", session_id
                    )
                    self.assertEqual(explicit.session_id, session_id)
                    self.assertEqual(explicit_mode, "explicit")

    def test_explicit_parent_precedes_auto_and_ineligible_explicit_fails_closed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            oracle_home = root / "oracle-home"
            repository = OracleSessionRepository(settings, oracle_home=oracle_home)
            write_stock_session(
                oracle_home, settings, "auto-newest", created_at=_iso(5)
            )
            write_stock_session(
                oracle_home,
                settings,
                "explicit-older-foreign",
                context_id="ctx-other",
                created_at=_iso(1),
            )
            write_stock_session(
                oracle_home,
                settings,
                "explicit-bad",
                conversation_id=None,
                conversation_url=None,
                created_at=_iso(6),
            )

            selected, mode = repository.select_parent(
                "ctx-main", "explicit-older-foreign"
            )
            self.assertEqual((selected.session_id, mode), ("explicit-older-foreign", "explicit"))
            write_stock_session(
                oracle_home,
                settings,
                "explicit-without-context",
                include_context=False,
                created_at=_iso(2),
            )
            contextless, contextless_mode = repository.select_parent(
                "ctx-main", "explicit-without-context"
            )
            self.assertEqual(
                (contextless.session_id, contextless_mode),
                ("explicit-without-context", "explicit"),
            )
            with self.assertRaisesRegex(FollowupError, "명시한 부모.*재개할 수 없습니다"):
                repository.select_parent("ctx-main", "explicit-bad")

            implicit, _ = repository.select_parent("ctx-main")
            self.assertEqual(implicit.session_id, "auto-newest")

    def test_context_registration_is_explicit_durable_and_not_inferred_from_cwd(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            oracle_home = root / "oracle-home"
            repository = OracleSessionRepository(settings, oracle_home=oracle_home)
            command, session_id = repository.prepare_new_run_command(
                [TEST_ORACLE_CLI, "-p", "initial"], "initial-request"
            )
            self.assertEqual(option_value(command, "--slug"), session_id)
            self.assertIn("--wait", command)
            self.assertEqual(option_value(command, "--browser-archive"), "never")
            write_unregistered_stock_session(
                oracle_home, settings, session_id, slot_id=1
            )
            readback = repository.record_origin(
                session_id,
                context_id="ctx-explicit",
                slot_id=1,
                request_id="initial-request",
                operation="submit",
                exit_code=0,
            )
            self.assertEqual(readback["opencode_conversation_id"], "ctx-explicit")
            selected, _ = repository.select_parent("ctx-explicit")
            self.assertEqual(selected.session_id, session_id)

            write_stock_session(
                oracle_home,
                settings,
                "same-cwd-no-context",
                include_context=False,
                created_at=_iso(9),
            )
            with self.assertRaisesRegex(FollowupError, "기록된 종료.*없습니다"):
                repository.select_parent("unrelated-context")

    def test_context_owned_archive_policy_rejects_caller_values(self):
        with TemporaryDirectory() as directory:
            repository = OracleSessionRepository(
                settings_for(Path(directory)), oracle_home=Path(directory) / "oracle-home"
            )
            for archive_option in (
                ["--browser-archive", "auto"],
                ["--browser-archive=never"],
            ):
                with self.subTest(archive_option=archive_option):
                    with self.assertRaisesRegex(FollowupError, "browser-archive.*소유"):
                        repository.prepare_new_run_command(
                            [TEST_ORACLE_CLI, *archive_option, "-p", "initial"],
                            "archive-owned",
                        )


class FollowupExecutionTests(unittest.TestCase):
    def _ready_service(self, root: Path, ready_slots=(1, 2, 3, 4, 5)) -> SlotService:
        settings = settings_for(root)
        service = SlotService(
            settings,
            cdp=FakeCDP(ready_slots),
            launcher=FakeLauncher(),
        )
        for slot_id in ready_slots:
            self.assertEqual(service.prepare(slot_id)["status"], AVAILABLE)
        return service

    def test_exact_parent_slot_waits_releases_runs_and_persists_child_lineage(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            oracle_home = root / "oracle-home"
            parent_directory = write_stock_session(
                oracle_home, service.settings, "parent-slot-two", slot_id=2
            )
            parent_before = (parent_directory / "meta.json").read_bytes()
            held = service.claim_job(2, "held-slot-two")
            self.assertTrue(held["accepted"])

            factory = FakeOracleFactory(oracle_home)
            runner = JobRunner(
                service,
                popen_factory=factory,
                oracle_cli_path=TEST_ORACLE_CLI,
            )
            repository = OracleSessionRepository(service.settings, oracle_home=oracle_home)
            followup = FollowupRunner(
                service,
                runner=runner,
                repository=repository,
                poll_interval=0.01,
            )
            events: list[dict[str, object]] = []
            result_holder: dict[str, object] = {}

            def invoke():
                result_holder["result"] = followup.run(
                    "followup-release",
                    "ctx-main",
                    [TEST_ORACLE_CLI, "-p", "continue this"],
                    emit=events.append,
                )

            with patch.object(service, "status", wraps=service.status) as status:
                thread = threading.Thread(target=invoke)
                thread.start()
                deadline = time.monotonic() + 5
                while (
                    not any(event["event"] == "waiting" for event in events)
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                self.assertTrue(any(event["event"] == "waiting" for event in events))
                self.assertEqual(factory.calls, [])

                released = service.finish_job(
                    2,
                    "held-slot-two",
                    held["record"]["started_at"],
                    "success",
                    0,
                    "release",
                    "없음",
                )
                self.assertTrue(released["released"])
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                self.assertEqual(status.call_count, 1)
                self.assertEqual(status.call_args.args, (2,))

            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(3)["status"], AVAILABLE)

            result = result_holder["result"]
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(len(factory.calls), 1)
            command = factory.calls[0]["argv"]
            self.assertEqual(option_value(command, "--followup"), "parent-slot-two")
            self.assertEqual(
                option_value(command, "--remote-chrome"),
                f"127.0.0.1:{service.settings.slot(2).port}",
            )
            self.assertEqual(option_value(command, "--browser-archive"), "never")
            self.assertEqual(factory.calls[0]["env"]["ORACLE_BROWSER_SLOT_ID"], "2")
            self.assertEqual(service.cdp.restore_calls, [])
            self.assertEqual((parent_directory / "meta.json").read_bytes(), parent_before)

            final = result["record"]["authoritative_readback"]
            child_id = final["child_session_id"]
            self.assertNotEqual(child_id, "parent-slot-two")
            self.assertEqual(final["selection_mode"], "implicit")
            self.assertEqual(final["parent_session_id"], "parent-slot-two")
            self.assertEqual(final["stock_parent_session_id"], "parent-slot-two")
            self.assertEqual(final["original_slot"]["slot_id"], 2)
            self.assertTrue(final["same_conversation"])
            self.assertTrue(final["prompt_submission"]["submitted"])
            self.assertTrue(final["completion"]["completed"])
            self.assertEqual(final["result"]["status"], "available")
            self.assertTrue(final["verification"]["ok"])
            self.assertEqual(repository.read_followup(child_id), final)

            next_parent, mode = repository.select_parent("ctx-main")
            self.assertEqual((next_parent.session_id, mode), (child_id, "implicit"))
            self.assertEqual(service.status(2)["status"], AVAILABLE)

    def test_file_followup_emits_one_prepared_event_before_status_claim_and_child(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            oracle_home = root / "oracle-home"
            write_stock_session(
                oracle_home, service.settings, "file-followup-parent", slot_id=2
            )
            source = root / "source.txt"
            source.write_text("source evidence", encoding="utf-8")
            temporary_root = root / "zip-temp"
            temporary_root.mkdir()
            policy = FileAttachmentPolicy(
                selector=lambda _groups, _cwd: [source],
                oracle_home=oracle_home,
                temporary_root=temporary_root,
            )
            events: list[dict[str, object]] = []
            factory = FakeOracleFactory(oracle_home)
            result = FollowupRunner(
                service,
                runner=JobRunner(
                    service,
                    popen_factory=factory,
                    oracle_cli_path=TEST_ORACLE_CLI,
                    attachment_policy=policy,
                ),
                repository=OracleSessionRepository(
                    service.settings, oracle_home=oracle_home
                ),
            ).run(
                "file-followup",
                "ctx-main",
                [
                    TEST_ORACLE_CLI,
                    "--files-report",
                    "--file",
                    str(source),
                    "-p",
                    "continue with file",
                ],
                emit=events.append,
            )

            self.assertEqual(result["exit_code"], 0)
            prepared = [
                event for event in events if event["event"] == "attachment_prepared"
            ]
            self.assertEqual(len(prepared), 1)
            self.assertLess(
                events.index(prepared[0]),
                next(
                    index
                    for index, event in enumerate(events)
                    if event["event"] == "started"
                ),
            )
            self.assertEqual(prepared[0]["operation"], "followup")
            self.assertEqual(prepared[0]["assigned_slot"], 2)
            self.assertEqual(
                prepared[0]["selected_files"],
                [
                    {
                        "relative_path": os.path.relpath(source, Path.cwd()).replace(
                            os.sep, "/"
                        ),
                        "size_bytes": source.stat().st_size,
                    }
                ],
            )
            self.assertNotIn(str(temporary_root), json.dumps(prepared[0]))

    def test_duplicate_request_id_never_creates_a_second_child(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            oracle_home = root / "oracle-home"
            write_stock_session(oracle_home, service.settings, "duplicate-parent", slot_id=1)
            held = service.claim_job(1, "held-for-duplicate")
            self.assertTrue(held["accepted"])
            waiting = threading.Event()
            factory = FakeOracleFactory(oracle_home)
            followup = FollowupRunner(
                service,
                runner=JobRunner(service, popen_factory=factory, oracle_cli_path=TEST_ORACLE_CLI),
                repository=OracleSessionRepository(service.settings, oracle_home=oracle_home),
                poll_interval=0.01,
            )
            first_result: dict[str, object] = {}

            def invoke_first():
                first_result["result"] = followup.run(
                    "duplicate-followup",
                    "ctx-main",
                    [TEST_ORACLE_CLI, "-p", "first"],
                    emit=lambda record: waiting.set() if record["event"] == "waiting" else None,
                )

            first = threading.Thread(target=invoke_first)
            first.start()
            self.assertTrue(waiting.wait(timeout=5))

            duplicate = followup.run(
                "duplicate-followup", "ctx-main", [TEST_ORACLE_CLI, "-p", "duplicate"]
            )
            self.assertEqual(duplicate["exit_code"], 2)
            self.assertEqual(duplicate["record"]["event"], "rejected")
            self.assertIn("동일 request ID", duplicate["record"]["reason"])
            self.assertEqual(factory.calls, [])

            service.finish_job(
                1,
                "held-for-duplicate",
                held["record"]["started_at"],
                "success",
                0,
                "release",
                "없음",
            )
            first.join(timeout=5)
            self.assertFalse(first.is_alive())
            self.assertEqual(len(factory.calls), 1)
            retry = followup.run(
                "duplicate-followup", "ctx-main", [TEST_ORACLE_CLI, "-p", "retry"]
            )
            self.assertEqual(retry["exit_code"], 2)
            self.assertEqual(len(factory.calls), 1)

    def test_incompatible_occupied_origin_rejects_before_wait_or_child(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            oracle_home = root / "oracle-home"
            write_stock_session(
                oracle_home, service.settings, "incompatible-parent", slot_id=3
            )
            held = service.claim_job(3, "held-incompatible-origin")
            self.assertTrue(held["accepted"])
            factory = FakeOracleFactory(oracle_home)
            events: list[dict[str, object]] = []

            result = FollowupRunner(
                service,
                runner=JobRunner(
                    service,
                    popen_factory=factory,
                    oracle_cli_path=TEST_ORACLE_CLI,
                ),
                repository=OracleSessionRepository(
                    service.settings, oracle_home=oracle_home
                ),
                poll_interval=0.01,
            ).run(
                "incompatible-occupied-origin",
                "ctx-main",
                [
                    TEST_ORACLE_CLI,
                    "--model",
                    "gpt-5.6-sol",
                    "--browser-thinking-time",
                    "pro",
                    "-p",
                    "must not wait or run",
                ],
                emit=events.append,
            )

            self.assertEqual(result["exit_code"], 2)
            self.assertEqual(events[-1]["event"], "rejected")
            self.assertFalse(any(event["event"] == "waiting" for event in events))
            self.assertIn("호환되지 않습니다", result["record"]["reason"])
            self.assertEqual(factory.calls, [])
            self.assertEqual(service.status(3)["status"], OCCUPIED)
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(2)["status"], AVAILABLE)

    def test_archived_parent_restores_before_spawning_stock_child(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cdp = FakeCDP()
            service = SlotService(
                settings_for(root), cdp=cdp, launcher=FakeLauncher()
            )
            for slot_id in (1, 2, 3, 4, 5):
                self.assertEqual(service.prepare(slot_id)["status"], AVAILABLE)
            oracle_home = root / "oracle-home"
            parent_directory = write_stock_session(
                oracle_home,
                service.settings,
                "archived-parent",
                slot_id=2,
                status="error",
                archived=True,
            )
            parent_before = (parent_directory / "meta.json").read_bytes()
            factory = FakeOracleFactory(oracle_home)
            call_order: list[str] = []

            def popen(argv, *, env, close_fds):
                call_order.append("spawn")
                return factory(argv, env=env, close_fds=close_fds)

            original_restore = cdp.restore_archived_conversation

            def restore(slot, conversation_url):
                call_order.append("restore")
                return original_restore(slot, conversation_url)

            cdp.restore_archived_conversation = restore
            result = FollowupRunner(
                service,
                runner=JobRunner(
                    service,
                    popen_factory=popen,
                    oracle_cli_path=TEST_ORACLE_CLI,
                ),
                repository=OracleSessionRepository(
                    service.settings, oracle_home=oracle_home
                ),
            ).run(
                "restore-archived-parent",
                "ctx-main",
                [TEST_ORACLE_CLI, "-p", "continue archived conversation"],
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(call_order, ["restore", "spawn"])
            self.assertEqual(cdp.restore_calls, [(2, CONVERSATION_URL)])
            self.assertEqual((parent_directory / "meta.json").read_bytes(), parent_before)
            self.assertEqual(service.status(2)["status"], AVAILABLE)

    def test_archived_parent_restore_failure_releases_without_child_or_fallback(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cdp = FakeCDP(restore_error=CDPError("composer readback failed"))
            service = SlotService(
                settings_for(root), cdp=cdp, launcher=FakeLauncher()
            )
            for slot_id in (1, 2, 3, 4, 5):
                self.assertEqual(service.prepare(slot_id)["status"], AVAILABLE)
            oracle_home = root / "oracle-home"
            parent_directory = write_stock_session(
                oracle_home,
                service.settings,
                "archived-restore-failure",
                slot_id=2,
                archived=True,
            )
            parent_before = (parent_directory / "meta.json").read_bytes()
            factory = FakeOracleFactory(oracle_home)
            events: list[dict[str, object]] = []
            result = FollowupRunner(
                service,
                runner=JobRunner(
                    service,
                    popen_factory=factory,
                    oracle_cli_path=TEST_ORACLE_CLI,
                ),
                repository=OracleSessionRepository(
                    service.settings, oracle_home=oracle_home
                ),
            ).run(
                "restore-failure",
                "ctx-main",
                [TEST_ORACLE_CLI, "-p", "must not submit"],
                emit=events.append,
            )

            self.assertEqual(result["exit_code"], 1)
            self.assertEqual(cdp.restore_calls, [(2, CONVERSATION_URL)])
            self.assertEqual(factory.calls, [])
            self.assertEqual(events[-1]["event"], "failed")
            self.assertTrue(events[-1]["released"])
            self.assertEqual(events[-1]["attempted_slots"], [2])
            self.assertEqual((parent_directory / "meta.json").read_bytes(), parent_before)
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(2)["status"], AVAILABLE)
            self.assertEqual(service.status(3)["status"], AVAILABLE)
            self.assertEqual(
                sorted(path.name for path in (oracle_home / "sessions").iterdir()),
                ["archived-restore-failure"],
            )

    def test_unavailable_origin_fails_without_wait_fallback_or_child(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root, ready_slots=(1, 3))
            oracle_home = root / "oracle-home"
            write_stock_session(
                oracle_home, service.settings, "parent-unready-two", slot_id=2
            )
            factory = FakeOracleFactory(oracle_home)
            result = FollowupRunner(
                service,
                runner=JobRunner(
                    service,
                    popen_factory=factory,
                    oracle_cli_path=TEST_ORACLE_CLI,
                ),
                repository=OracleSessionRepository(
                    service.settings, oracle_home=oracle_home
                ),
                poll_interval=0.01,
            ).run(
                "unavailable-origin",
                "ctx-main",
                [TEST_ORACLE_CLI, "-p", "must not run"],
            )
            self.assertEqual(result["exit_code"], 1)
            self.assertIn("다른 슬롯으로 전환하지 않았습니다", result["record"]["operator_action"])
            self.assertEqual(result["record"]["attempted_slots"], [2])
            self.assertEqual(factory.calls, [])
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(3)["status"], AVAILABLE)
            self.assertEqual(
                sorted(path.name for path in (oracle_home / "sessions").iterdir()),
                ["parent-unready-two"],
            )

    def test_slot_five_origin_runs_on_slot_five_endpoint(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            oracle_home = root / "oracle-home"
            write_stock_session(
                oracle_home, service.settings, "parent-slot-five", slot_id=5
            )
            factory = FakeOracleFactory(oracle_home)
            events: list[dict[str, object]] = []
            result = FollowupRunner(
                service,
                runner=JobRunner(
                    service,
                    popen_factory=factory,
                    oracle_cli_path=TEST_ORACLE_CLI,
                ),
                repository=OracleSessionRepository(
                    service.settings, oracle_home=oracle_home
                ),
                poll_interval=0.01,
            ).run(
                "slot-five-followup",
                "ctx-main",
                [TEST_ORACLE_CLI, "-p", "continue on slot five"],
                emit=events.append,
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(len(factory.calls), 1)
            command = factory.calls[0]["argv"]
            self.assertEqual(option_value(command, "--followup"), "parent-slot-five")
            self.assertEqual(
                option_value(command, "--remote-chrome"),
                f"127.0.0.1:{service.settings.slot(5).port}",
            )
            self.assertEqual(factory.calls[0]["env"]["ORACLE_BROWSER_SLOT_ID"], "5")
            readback = result["record"]["authoritative_readback"]
            self.assertEqual(readback["original_slot"]["slot_id"], 5)
            self.assertEqual(readback["parent_session_id"], "parent-slot-five")
            self.assertTrue(readback["verification"]["ok"])
            self.assertEqual(service.status(5)["status"], AVAILABLE)

    def test_unavailable_slot_four_origin_fails_without_fallback(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root, ready_slots=(1, 2, 3, 5))
            oracle_home = root / "oracle-home"
            write_stock_session(
                oracle_home, service.settings, "parent-unready-four", slot_id=4
            )
            factory = FakeOracleFactory(oracle_home)
            result = FollowupRunner(
                service,
                runner=JobRunner(
                    service,
                    popen_factory=factory,
                    oracle_cli_path=TEST_ORACLE_CLI,
                ),
                repository=OracleSessionRepository(
                    service.settings, oracle_home=oracle_home
                ),
                poll_interval=0.01,
            ).run(
                "unavailable-slot-four-origin",
                "ctx-main",
                [TEST_ORACLE_CLI, "-p", "must not run"],
            )

            self.assertEqual(result["exit_code"], 1)
            self.assertIn(
                "다른 슬롯으로 전환하지 않았습니다",
                result["record"]["operator_action"],
            )
            self.assertEqual(result["record"]["attempted_slots"], [4])
            self.assertEqual(factory.calls, [])
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(5)["status"], AVAILABLE)
            self.assertEqual(
                sorted(path.name for path in (oracle_home / "sessions").iterdir()),
                ["parent-unready-four"],
            )

    def test_missing_or_explicit_ineligible_parent_never_spawns_child(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            oracle_home = root / "oracle-home"
            write_stock_session(
                oracle_home,
                service.settings,
                "bad-explicit",
                conversation_id=None,
                conversation_url=None,
            )
            write_stock_session(
                oracle_home,
                service.settings,
                "running-explicit",
                status="running",
                terminated=True,
            )
            factory = FakeOracleFactory(oracle_home)
            followup = FollowupRunner(
                service,
                runner=JobRunner(
                    service,
                    popen_factory=factory,
                    oracle_cli_path=TEST_ORACLE_CLI,
                ),
                repository=OracleSessionRepository(
                    service.settings, oracle_home=oracle_home
                ),
            )
            explicit = followup.run(
                "bad-explicit-request",
                "ctx-main",
                [TEST_ORACLE_CLI, "-p", "must not run"],
                parent_session_id="bad-explicit",
            )
            running_explicit = followup.run(
                "running-explicit-request",
                "ctx-main",
                [TEST_ORACLE_CLI, "-p", "must not run"],
                parent_session_id="running-explicit",
            )
            missing = followup.run(
                "missing-context-request",
                "ctx-no-sessions",
                [TEST_ORACLE_CLI, "-p", "must not run"],
            )
            self.assertEqual(explicit["exit_code"], 1)
            self.assertEqual(explicit["record"]["selection_mode"], "explicit")
            self.assertIn("다른 세션으로 자동 전환하지 않았습니다", explicit["record"]["operator_action"])
            self.assertEqual(running_explicit["exit_code"], 1)
            self.assertEqual(running_explicit["record"]["selection_mode"], "explicit")
            self.assertIn("다른 세션으로 자동 전환하지 않았습니다", running_explicit["record"]["operator_action"])
            self.assertEqual(missing["exit_code"], 1)
            self.assertIn("--parent-session-id", missing["record"]["operator_action"])
            self.assertEqual(factory.calls, [])

    def test_occupied_origin_wait_is_signal_cancellable_without_child(self):
        if not hasattr(os, "kill"):
            self.skipTest("process signals are not available")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            oracle_home = root / "oracle-home"
            write_stock_session(
                oracle_home, service.settings, "cancel-parent", slot_id=2
            )
            held = service.claim_job(2, "held-for-cancel")
            self.assertTrue(held["accepted"])
            context = multiprocessing.get_context("fork")
            result_queue = context.Queue()
            process = context.Process(
                target=cancellation_waiter_process,
                args=(service.settings, oracle_home, result_queue),
            )
            process.start()
            waiting = None
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                event = result_queue.get(timeout=5)
                if event.get("event") == "waiting":
                    waiting = event
                    break
            self.assertIsNotNone(waiting)
            self.assertEqual(waiting["assigned_slot"], 2)
            os.kill(process.pid, signal.SIGINT)
            cancelled = result_queue.get(timeout=5)
            payload = result_queue.get(timeout=5)
            process.join(timeout=5)
            self.assertFalse(process.is_alive())
            self.assertEqual(cancelled["event"], "cancelled")
            self.assertEqual(cancelled["assigned_slot"], 2)
            self.assertEqual(payload["result"]["exit_code"], 130)
            self.assertEqual(service.status(2)["status"], OCCUPIED)
            self.assertEqual(
                sorted(path.name for path in (oracle_home / "sessions").iterdir()),
                ["cancel-parent"],
            )
            self.assertTrue(
                service.finish_job(
                    2,
                    "held-for-cancel",
                    held["record"]["started_at"],
                    "success",
                    0,
                    "release",
                    "없음",
                )["released"]
            )


class _FakeCDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        request = bytearray()
        while b"\r\n\r\n" not in request:
            chunk = self.request.recv(4096)
            if not chunk:
                return
            request.extend(chunk)
        header = bytes(request)
        first_line = header.split(b"\r\n", 1)[0].decode("ascii")
        path = first_line.split(" ")[1]
        if b"upgrade: websocket" in header.lower():
            self.request.sendall(
                b"HTTP/1.1 101 Switching Protocols\r\n"
                b"Upgrade: websocket\r\n"
                b"Connection: Upgrade\r\n\r\n"
            )
            payload = self._read_websocket_payload()
            request_id = json.loads(payload.decode("utf-8"))["id"]
            response = json.dumps(
                {
                    "id": request_id,
                    "result": {
                        "result": {
                            "value": {"logged_in": True, "page_ready": True}
                        }
                    },
                }
            ).encode("utf-8")
            self.request.sendall(self._websocket_frame(response))
            return
        if path == "/json/version":
            payload = {
                "Browser": "FakeChrome/1",
                "webSocketDebuggerUrl": (
                    f"ws://127.0.0.1:{self.server.server_address[1]}/devtools/browser/fake"
                ),
            }
        elif path == "/json/list":
            payload = [
                {
                    "type": "page",
                    "url": "https://chatgpt.com/",
                    "webSocketDebuggerUrl": (
                        f"ws://127.0.0.1:{self.server.server_address[1]}/devtools/page/fake"
                    ),
                }
            ]
        else:
            payload = {}
        body = json.dumps(payload).encode("utf-8")
        self.request.sendall(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            + f"Content-Length: {len(body)}\r\n".encode("ascii")
            + b"Connection: close\r\n\r\n"
            + body
        )

    def _read_websocket_payload(self) -> bytes:
        first, second = self._read_exact(2)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        mask = self._read_exact(4) if second & 0x80 else b""
        payload = bytearray(self._read_exact(length))
        if mask:
            for index in range(length):
                payload[index] ^= mask[index % 4]
        return bytes(payload)

    def _read_exact(self, length: int) -> bytes:
        data = bytearray()
        while len(data) < length:
            data.extend(self.request.recv(length - len(data)))
        return bytes(data)

    @staticmethod
    def _websocket_frame(payload: bytes) -> bytes:
        if len(payload) < 126:
            return bytes((0x81, len(payload))) + payload
        return bytes((0x81, 126)) + struct.pack("!H", len(payload)) + payload


class _ThreadedTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def write_fake_oracle_executable(path: Path) -> None:
    script = f"""#!{sys.executable}
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

args = sys.argv[1:]
def value(flag):
    for index, token in enumerate(args):
        if token == flag and index + 1 < len(args):
            return args[index + 1]
        if token.startswith(flag + '='):
            return token.split('=', 1)[1]
    return None

home = Path(os.environ['ORACLE_HOME_DIR'])
home.mkdir(parents=True, exist_ok=True)
parent_id = value('--followup')
child_id = value('--slug')
remote = value('--remote-chrome')
prompt = value('-p') or 'follow-up prompt'
with (home / 'fake-invocations.jsonl').open('a', encoding='utf-8') as handle:
    handle.write(json.dumps({{'argv': args, 'slot': os.environ.get('ORACLE_BROWSER_SLOT_ID')}}) + '\\n')
host, port_text = remote.rsplit(':', 1)
port = int(port_text)
if parent_id:
    parent = json.loads((home / 'sessions' / parent_id / 'meta.json').read_text(encoding='utf-8'))
    config = dict(parent['browser']['config'])
    conversation_id = parent['browser']['runtime']['conversationId']
    conversation_url = parent['browser']['runtime']['tabUrl']
else:
    config = {{'url': 'https://chatgpt.com/', 'modelStrategy': 'current'}}
    conversation_id = {CONVERSATION_ID!r}
    conversation_url = {CONVERSATION_URL!r}
config['remoteChrome'] = {{'host': host, 'port': port}}
now = datetime.now(timezone.utc).isoformat()
options = {{
    'slug': child_id,
    'mode': 'browser',
    'model': 'gpt-5.6',
    'prompt': prompt,
    'browserConfig': config,
}}
if parent_id:
    options['followupSessionId'] = parent_id
metadata = {{
    'id': child_id,
    'createdAt': now,
    'completedAt': now,
    'status': 'completed',
    'mode': 'browser',
    'model': 'gpt-5.6',
    'options': options,
    'browser': {{
        'config': config,
        'runtime': {{
            'chromeHost': host,
            'chromePort': port,
            'conversationId': conversation_id,
            'tabUrl': conversation_url,
            'promptSubmitted': True,
        }},
        'archive': {{'archived': False}},
    }},
}}
session = home / 'sessions' / child_id
session.mkdir(parents=True)
(session / 'meta.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
answer = 'isolated continued result' if parent_id else 'isolated initial result'
(session / 'output.log').write_text('Answer:\\n' + answer + '\\n', encoding='utf-8')
print(answer)
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


class IsolatedCliExerciseTests(unittest.TestCase):
    def test_actual_cli_followup_and_no_parent_fail_closed(self):
        project_root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            oracle_home = root / "oracle-home"
            state_root = root / "state"
            profile_root = root / "profiles"
            executable = root / "bin" / "oracle"
            executable.parent.mkdir(parents=True)
            write_fake_oracle_executable(executable)

            while True:
                server = _ThreadedTCPServer(("127.0.0.1", 0), _FakeCDPHandler)
                if server.server_address[1] <= 65532:
                    break
                server.server_close()
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            try:
                slot_two_port = server.server_address[1]
                settings = Settings(
                    state_root=state_root,
                    profile_root=profile_root,
                    chrome_path=root / "fake-chrome",
                    port_base=slot_two_port - 1,
                    cdp_start_timeout=0.1,
                    cdp_request_timeout=1,
                    queue_poll_interval=0.01,
                )
                slot = settings.slot(2)
                state_root.mkdir(parents=True)
                (state_root / "slot-2.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "slot_id": 2,
                            "port": slot.port,
                            "profile_dir": str(slot.profile_dir),
                            "prepared": True,
                            "requires_reprepare": False,
                            "occupancy": None,
                            "prepared_at": "2026-08-01T00:00:00Z",
                        }
                    ),
                    encoding="utf-8",
                )
                environment = os.environ.copy()
                environment.update(
                    {
                        "ORACLE_HOME_DIR": str(oracle_home),
                        "ORACLE_BROWSER_SLOTS_STATE_ROOT": str(state_root),
                        "ORACLE_BROWSER_SLOTS_PROFILE_ROOT": str(profile_root),
                        "ORACLE_BROWSER_SLOTS_PORT_BASE": str(settings.port_base),
                        "ORACLE_BROWSER_SLOTS_CDP_REQUEST_TIMEOUT": "1",
                        "ORACLE_BROWSER_SLOTS_QUEUE_POLL_INTERVAL": "0.01",
                        "ORACLE_BROWSER_SLOTS_ORACLE_CLI": str(executable),
                    }
                )
                initial_command = [
                    str(project_root / "bin" / "oracle-browser-slots"),
                    "submit",
                    "--request-id",
                    "isolated-initial",
                    "--opencode-conversation-id",
                    "ctx-cli",
                    "--",
                    str(executable),
                    "-p",
                    "initial consult",
                ]
                initial = subprocess.run(
                    initial_command,
                    cwd=project_root,
                    env=environment,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=10,
                )
                self.assertEqual(initial.returncode, 0, initial.stderr)
                initial_events = [
                    json.loads(line) for line in initial.stderr.splitlines()
                ]
                self.assertEqual(initial_events[-1]["event"], "session_registered")
                initial_readback = initial_events[-1]["authoritative_readback"]
                parent_id = initial_readback["child_session_id"]
                self.assertEqual(
                    initial_readback["opencode_conversation_id"], "ctx-cli"
                )
                self.assertEqual(initial_readback["originating_slot"]["slot_id"], 2)

                command = [
                    str(project_root / "bin" / "oracle-browser-slots"),
                    "followup",
                    "--request-id",
                    "isolated-followup",
                    "--opencode-conversation-id",
                    "ctx-cli",
                    "--",
                    str(executable),
                    "-p",
                    "continue safely",
                ]
                completed = subprocess.run(
                    command,
                    cwd=project_root,
                    env=environment,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=10,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                events = [json.loads(line) for line in completed.stderr.splitlines()]
                self.assertEqual(events[0]["event"], "parent_selected")
                self.assertEqual(events[0]["assigned_slot"], 2)
                persisted = events[-1]
                self.assertEqual(persisted["event"], "session_persisted")
                readback = persisted["authoritative_readback"]
                child_id = readback["child_session_id"]
                child_metadata = json.loads(
                    (oracle_home / "sessions" / child_id / "meta.json").read_text(
                        encoding="utf-8"
                    )
                )
                invocation_lines = (
                    oracle_home / "fake-invocations.jsonl"
                ).read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(invocation_lines), 2)
                initial_invocation = json.loads(invocation_lines[0])
                invocation = json.loads(invocation_lines[1])
                self.assertIsNone(option_value(initial_invocation["argv"], "--followup"))
                self.assertEqual(
                    option_value(initial_invocation["argv"], "--browser-archive"),
                    "never",
                )
                self.assertEqual(invocation["slot"], "2")
                self.assertEqual(
                    option_value(invocation["argv"], "--followup"), parent_id
                )
                self.assertEqual(
                    option_value(invocation["argv"], "--remote-chrome"),
                    f"127.0.0.1:{slot.port}",
                )
                followup_metadata = child_metadata["oracle_browser_slots"]["followup"]
                self.assertEqual(followup_metadata["selection_mode"], "implicit")
                self.assertEqual(
                    followup_metadata["parent_session_id"], parent_id
                )
                self.assertEqual(followup_metadata["child_session_id"], child_id)
                self.assertTrue(followup_metadata["conversation"]["same_as_parent"])
                self.assertTrue(followup_metadata["prompt_submission"]["submitted"])
                self.assertTrue(followup_metadata["completion"]["completed"])
                self.assertEqual(followup_metadata["result"]["status"], "available")
                self.assertIn(
                    "isolated continued result",
                    (oracle_home / "sessions" / child_id / "output.log").read_text(
                        encoding="utf-8"
                    ),
                )

                no_parent_command = [
                    str(project_root / "bin" / "oracle-browser-slots"),
                    "followup",
                    "--request-id",
                    "isolated-no-parent",
                    "--opencode-conversation-id",
                    "ctx-without-parent",
                    "--",
                    str(executable),
                    "-p",
                    "must not submit",
                ]
                no_parent = subprocess.run(
                    no_parent_command,
                    cwd=project_root,
                    env=environment,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=10,
                )
                self.assertEqual(no_parent.returncode, 1)
                no_parent_events = [
                    json.loads(line) for line in no_parent.stderr.splitlines()
                ]
                self.assertEqual(no_parent_events[-1]["event"], "failed")
                self.assertIn(
                    "--parent-session-id", no_parent_events[-1]["operator_action"]
                )
                invocation_after = (
                    oracle_home / "fake-invocations.jsonl"
                ).read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(invocation_after), 2)

                print(
                    json.dumps(
                        {
                            "isolated_cli_evidence": {
                                "initial_request": initial_invocation,
                                "initial_registration": initial_readback,
                                "request": invocation,
                                "selected_slot": events[0]["assigned_slot"],
                                "parent_session_id": readback["parent_session_id"],
                                "child_session_id": child_id,
                                "lineage": {
                                    "selection_mode": readback["selection_mode"],
                                    "stock_parent_session_id": readback[
                                        "stock_parent_session_id"
                                    ],
                                },
                                "conversation_id": readback["conversation_id"],
                                "conversation_url": readback["conversation_url"],
                                "same_conversation": readback["same_conversation"],
                                "prompt_submission": readback["prompt_submission"],
                                "completion": readback["completion"],
                                "result": readback["result"],
                                "metadata_path": readback["metadata_path"],
                                "no_parent": {
                                    "exit_code": no_parent.returncode,
                                    "event": no_parent_events[-1]["event"],
                                    "child_spawned": len(invocation_after) != 2,
                                },
                            }
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                )
            finally:
                server.shutdown()
                server.server_close()
                server_thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
