from __future__ import annotations

import json
import hashlib
import multiprocessing
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import zipfile

from oracle_browser_slots.attachments import (
    AttachmentPreparationError,
    FileAttachmentPolicy,
    MANIFEST_RELATIVE_PATH,
    MAX_SAFE_FILE_SIZE_BYTES,
    normalize_zip_member_path,
)
from oracle_browser_slots.allocator import AutoAllocator
from oracle_browser_slots.cdp import (
    CDPClient,
    CDPError,
    LoginResult,
    _archived_ui_fallback_expression,
)
from oracle_browser_slots.coordination import QueueCoordinator
from oracle_browser_slots.launcher import (
    ChromeLauncher,
    PrepareError,
    _has_flag,
    _is_chrome_process,
)
from oracle_browser_slots.model import AVAILABLE, OCCUPIED, SLOT_IDS, UNAVAILABLE, Settings
from oracle_browser_slots.runner import CANONICAL_ORACLE_CLI, JobRunner
from oracle_browser_slots.service import SlotService, process_starttime
from oracle_browser_slots.state import StateError, StateStore


TEST_ORACLE_CLI = "/tmp/oracle-test-bin/oracle"


def oracle_argv(port: int, *extra: str) -> list[str]:
    return [
        TEST_ORACLE_CLI,
        "--engine",
        "browser",
        "--browser-model-strategy",
        "current",
        "--remote-chrome",
        f"127.0.0.1:{port}",
        *extra,
    ]


class FakeLauncher:
    def __init__(self, failures: set[int] | None = None) -> None:
        self.failures = failures or set()

    def ensure_running(self, slot):
        if slot.slot_id in self.failures:
            from oracle_browser_slots.launcher import PrepareError

            raise PrepareError(
                f"slot {slot.slot_id} failed",
                f"repair slot {slot.slot_id}",
            )
        return None


class FakeCDP:
    def __init__(self, results: dict[int, LoginResult | Exception]) -> None:
        self.results = results
        self.calls: list[int] = []

    def check_login(self, slot):
        self.calls.append(slot.slot_id)
        result = self.results[slot.slot_id]
        if isinstance(result, Exception):
            raise result
        return result

    def browser_version(self, slot):
        return {
            "Browser": "FakeChrome/1",
            "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/browser/fake",
        }


class ReadyCDP:
    def is_ready(self, slot):
        return True

    def check_login(self, slot):
        raise AssertionError("login check must not run when existing CDP ownership is rejected")


class LaunchCDP:
    def is_ready(self, slot):
        return False

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


class BlockingChild:
    def __init__(self, started: threading.Event, release: threading.Event) -> None:
        self.started = started
        self.release = release

    def wait(self):
        self.started.set()
        self.release.wait(timeout=5)
        return 0


class SignalBlockingChild:
    def __init__(self, started: threading.Event) -> None:
        self.started = started
        self.terminated = False

    def wait(self, timeout=None):
        self.started.set()
        while not self.terminated:
            time.sleep(0.01)
        return -15

    def terminate(self):
        self.terminated = True


def auto_waiter_process(settings, result_queue):
    service = SlotService(
        settings,
        cdp=FakeCDP(
            {
                1: LoginResult(True, "ready", "없음"),
                2: LoginResult(True, "ready", "없음"),
                3: LoginResult(True, "ready", "없음"),
            }
        ),
        launcher=FakeLauncher(),
    )
    runner = JobRunner(
        service,
        popen_factory=lambda argv, *, env, close_fds: ReturnCodeChild(0),
        oracle_cli_path=TEST_ORACLE_CLI,
    )
    result = AutoAllocator(service, runner=runner, poll_interval=0.01).submit(
        "waiting-cancel",
        [TEST_ORACLE_CLI, "-p", "task"],
        emit=result_queue.put,
    )
    result_queue.put({"result": result})


def auto_running_sighup_process(settings, result_queue):
    service = SlotService(
        settings,
        cdp=FakeCDP(
            {
                1: LoginResult(True, "ready", "없음"),
                2: LoginResult(True, "ready", "없음"),
                3: LoginResult(True, "ready", "없음"),
            }
        ),
        launcher=FakeLauncher(),
    )
    child_started = threading.Event()
    popen_calls: list[list[str]] = []

    def popen(argv, *, env, close_fds):
        popen_calls.append(argv)
        return SignalBlockingChild(child_started)

    runner = JobRunner(service, popen_factory=popen, oracle_cli_path=TEST_ORACLE_CLI)

    def send_sighup():
        child_started.wait(timeout=5)
        os.kill(os.getpid(), signal.SIGHUP)

    sender = threading.Thread(target=send_sighup)
    sender.start()
    result = AutoAllocator(service, runner=runner, poll_interval=0.01).submit(
        "running-sighup",
        [TEST_ORACLE_CLI, "-p", "task"],
        emit=result_queue.put,
    )
    sender.join(timeout=5)
    result_queue.put({"result": result, "popen_count": len(popen_calls)})


class InterruptingChild:
    def __init__(self) -> None:
        self.terminated = False

    def wait(self, timeout=None):
        if not self.terminated:
            raise KeyboardInterrupt
        return -15

    def terminate(self):
        self.terminated = True


class ExplodingWaitChild:
    def __init__(self) -> None:
        self.terminated = False

    def wait(self, timeout=None):
        if not self.terminated:
            raise RuntimeError("wait failed")
        return -15

    def terminate(self):
        self.terminated = True


class FailingWriteStore(StateStore):
    def write_unlocked(self, slot_id, value):
        raise StateError("injected write failure")


class MismatchedReadbackStore(StateStore):
    def read_unlocked(self, slot_id):
        value = super().read_unlocked(slot_id)
        if isinstance(value, dict) and value.get("prepared") is True:
            value = dict(value)
            value["profile_dir"] = "/wrong/profile"
        return value


def claim_and_hold_worker(settings, job_id, result_queue, release_event):
    service = SlotService(
        settings,
        cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
        launcher=FakeLauncher(),
    )
    result = service.claim_job(1, job_id)
    result_queue.put(
        {
            "accepted": result["accepted"],
            "status": result["record"]["status"],
        }
    )
    if result["accepted"]:
        release_event.wait(timeout=5)


def settings_for(root: Path) -> Settings:
    return Settings(
        state_root=root / "state",
        profile_root=root / "profiles",
        chrome_path=root / "fake-chrome",
        port_base=19222,
        cdp_start_timeout=0.1,
        cdp_request_timeout=0.1,
    )


class CDPConversationRestoreTests(unittest.TestCase):
    def test_restore_requires_same_conversation_url_and_usable_composer(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            slot = settings.slot(1)
            conversation_url = "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555"
            requests: list[tuple[str, dict[str, object]]] = []

            class FakeWebSocket:
                def __init__(self, _url, _timeout):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, _exc_type, _exc, _traceback):
                    return None

                def request(self, method, params):
                    requests.append((method, params))
                    if method == "Page.navigate":
                        return {"result": {"frameId": "frame-1"}}
                    expression = params["expression"]
                    value = (
                        {
                            "restored": True,
                            "auth_status": 200,
                            "patch_status": 200,
                            "readback_status": 200,
                            "is_archived": False,
                        }
                        if "backend-api/conversation" in expression
                        else {
                            "conversation_url": conversation_url,
                            "same_conversation": True,
                            "composer_ready": True,
                        }
                    )
                    return {"result": {"result": {"value": value}}}

            targets = [
                {
                    "id": "chatgpt-target",
                    "type": "page",
                    "url": "https://chatgpt.com/",
                    "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/fake",
                }
            ]
            client = CDPClient(request_timeout=0.01)
            with patch.object(client, "_get_json", return_value=targets), patch(
                "oracle_browser_slots.cdp._WebSocket", FakeWebSocket
            ):
                restored = client.restore_archived_conversation(slot, conversation_url)

            self.assertEqual(restored.conversation_url, conversation_url)
            self.assertEqual(
                restored.conversation_id, "11111111-2222-3333-4444-555555555555"
            )
            restore_request = next(
                params
                for method, params in requests
                if method == "Runtime.evaluate" and "backend-api/conversation" in params["expression"]
            )
            expression = restore_request["expression"]
            self.assertIn('fetch("/api/auth/session"', expression)
            self.assertIn('credentials: "include"', expression)
            self.assertIn(
                'const accessToken = typeof session?.accessToken === "string"',
                expression,
            )
            self.assertEqual(
                expression.count('"Authorization": `Bearer ${accessToken}`'), 2
            )
            self.assertIn('body: JSON.stringify({ is_archived: false })', expression)
            self.assertIn('method: "GET"', expression)
            self.assertEqual(expression.count("fetch(conversationPath"), 2)
            self.assertIn("readback_status: readbackResponse.status", expression)
            self.assertIn("is_archived: isArchived", expression)
            self.assertNotIn("is_visible", expression)
            return_lines = [
                line.strip()
                for line in expression.splitlines()
                if line.strip().startswith("return")
            ]
            self.assertTrue(return_lines)
            self.assertTrue(all("accessToken" not in line for line in return_lines))
            self.assertIn(
                ("Page.navigate", {"url": conversation_url}),
                requests,
            )

    def test_backend_unarchive_readback_failure_is_bounded_and_does_not_navigate(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            slot = settings.slot(1)
            conversation_url = "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555"
            targets = [
                {
                    "id": "chatgpt-target",
                    "type": "page",
                    "url": "https://chatgpt.com/",
                    "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/fake",
                }
            ]
            failures = (
                (
                    {
                        "restored": False,
                        "auth_status": 401,
                        "patch_status": None,
                        "readback_status": None,
                        "is_archived": None,
                    },
                    "auth HTTP 401",
                ),
                (
                    {
                        "restored": False,
                        "auth_status": 200,
                        "patch_status": 401,
                        "readback_status": None,
                        "is_archived": None,
                    },
                    "patch HTTP 401",
                ),
                (
                    {
                        "restored": False,
                        "auth_status": 200,
                        "patch_status": 200,
                        "readback_status": 401,
                        "is_archived": None,
                    },
                    "readback HTTP 401",
                ),
                (
                    {
                        "restored": False,
                        "auth_status": 200,
                        "patch_status": 200,
                        "readback_status": 200,
                        "is_archived": True,
                    },
                    "is_archived true",
                ),
                (
                    {
                        "restored": False,
                        "auth_status": 200,
                        "patch_status": 200,
                        "readback_status": 200,
                        "is_archived": "false",
                    },
                    "is_archived unavailable",
                ),
                (
                    {
                        "restored": True,
                        "auth_status": 200,
                        "patch_status": 200,
                        "readback_status": 200,
                        "is_archived": True,
                    },
                    "is_archived true",
                ),
                (
                    {
                        "restored": False,
                        "auth_status": "secret-token",
                        "patch_status": None,
                        "readback_status": None,
                        "is_archived": None,
                    },
                    "status unavailable",
                ),
            )
            for readback, expected_error in failures:
                with self.subTest(readback=readback):
                    requests: list[tuple[str, dict[str, object]]] = []

                    class FakeWebSocket:
                        def __init__(self, _url, _timeout):
                            pass

                        def __enter__(self):
                            return self

                        def __exit__(self, _exc_type, _exc, _traceback):
                            return None

                        def request(self, method, params):
                            requests.append((method, params))
                            if method == "Page.navigate":
                                raise AssertionError("failed restoration must not navigate")
                            return {"result": {"result": {"value": readback}}}

                    client = CDPClient(request_timeout=0.01)
                    with patch.object(client, "_get_json", return_value=targets), patch(
                        "oracle_browser_slots.cdp._WebSocket", FakeWebSocket
                    ), self.assertRaisesRegex(CDPError, expected_error) as raised:
                        client.restore_archived_conversation(slot, conversation_url)

                    self.assertNotIn("secret-token", str(raised.exception))
                    self.assertEqual([method for method, _params in requests], ["Runtime.evaluate"])

    def test_restore_activates_exact_unarchive_fallback_before_composer_success(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            slot = settings.slot(1)
            conversation_url = "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555"
            requests: list[tuple[str, dict[str, object]]] = []
            websocket_urls: list[str] = []
            native_websocket_urls: list[str] = []
            composer_readbacks = iter(
                (
                    {
                        "conversation_url": conversation_url,
                        "same_conversation": True,
                        "page_ready": True,
                        "composer_ready": False,
                    },
                    {
                        "conversation_url": conversation_url,
                        "same_conversation": True,
                        "page_ready": True,
                        "composer_ready": True,
                    },
                )
            )

            class FakeWebSocket:
                def __init__(self, url, _timeout):
                    self.url = url
                    websocket_urls.append(url)

                def __enter__(self):
                    return self

                def __exit__(self, _exc_type, _exc, _traceback):
                    return None

                def request(self, method, params):
                    requests.append((method, params))
                    if method == "Page.navigate":
                        return {"result": {"frameId": "frame-1"}}
                    if method == "Input.dispatchMouseEvent":
                        native_websocket_urls.append(self.url)
                        return {"result": {}}
                    expression = params["expression"]
                    if "backend-api/conversation" in expression:
                        value = {
                            "restored": True,
                            "auth_status": 200,
                            "patch_status": 200,
                            "readback_status": 200,
                            "is_archived": False,
                        }
                    elif "const currentConversationControl" in expression:
                        value = {
                            "state": "native_activation_ready",
                            "same_conversation": True,
                            "archived": True,
                            "action": "unarchive",
                            "geometry": {
                                "center_x": 60,
                                "center_y": 20,
                                "width": 121,
                                "height": 36,
                                "viewport_width": 1280,
                                "viewport_height": 720,
                            },
                        }
                    elif "const composerReady" in expression:
                        value = next(composer_readbacks)
                    else:
                        raise AssertionError(f"unexpected expression: {expression}")
                    return {"result": {"result": {"value": value}}}

            initial_targets = [
                {
                    "id": "chatgpt-target",
                    "type": "page",
                    "url": conversation_url,
                    "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/initial",
                }
            ]
            current_targets = [
                {
                    "id": "chatgpt-target",
                    "type": "page",
                    "url": conversation_url,
                    "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/current",
                }
            ]
            client = CDPClient(request_timeout=0.01)
            with patch.object(
                client,
                "_get_json",
                side_effect=(initial_targets, current_targets, current_targets),
            ), patch(
                "oracle_browser_slots.cdp._WebSocket", FakeWebSocket
            ):
                restored = client.restore_archived_conversation(slot, conversation_url)

            self.assertEqual(restored.conversation_url, conversation_url)
            self.assertEqual(
                set(websocket_urls),
                {
                    "ws://127.0.0.1/devtools/page/initial",
                    "ws://127.0.0.1/devtools/page/current",
                },
            )
            self.assertEqual(
                native_websocket_urls,
                ["ws://127.0.0.1/devtools/page/current"] * 3,
            )
            runtime_expressions = [
                params["expression"]
                for method, params in requests
                if method == "Runtime.evaluate"
            ]
            kinds = [
                "restore"
                if "backend-api/conversation" in expression
                else "fallback"
                if "const currentConversationControl" in expression
                else "composer"
                for expression in runtime_expressions
            ]
            self.assertEqual(kinds, ["restore", "composer", "fallback", "composer"])
            fallback_expression = runtime_expressions[2]
            self.assertIn('action === "unarchive"', fallback_expression)
            self.assertIn('action === "restore" && archiveContext(candidate)', fallback_expression)
            self.assertIn("isVisible(candidate)", fallback_expression)
            self.assertIn('result("native_activation_ready"', fallback_expression)
            native_events = [
                params
                for method, params in requests
                if method == "Input.dispatchMouseEvent"
            ]
            self.assertEqual(
                native_events,
                [
                    {"type": "mouseMoved", "x": 60.0, "y": 20.0},
                    {
                        "type": "mousePressed",
                        "x": 60.0,
                        "y": 20.0,
                        "button": "left",
                        "clickCount": 1,
                    },
                    {
                        "type": "mouseReleased",
                        "x": 60.0,
                        "y": 20.0,
                        "button": "left",
                        "clickCount": 1,
                    },
                ],
            )

    def test_archived_ui_fallback_returns_native_geometry_without_synthetic_activation(self):
        expression = _archived_ui_fallback_expression(
            "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555"
        )

        self.assertIn('return result("native_activation_ready"', expression)
        self.assertIn("center_x: rect.left + rect.width / 2", expression)
        self.assertIn("center_y: rect.top + rect.height / 2", expression)
        self.assertIn("viewport_width: window.innerWidth", expression)
        self.assertIn("viewport_height: window.innerHeight", expression)
        self.assertIn("geometry: values.geometry || null", expression)
        self.assertNotIn("control.click()", expression)
        self.assertNotIn("document.dispatchEvent", expression)
        self.assertNotIn("dispatchEvent(", expression)

    def test_native_click_coordinates_reject_malformed_or_out_of_bounds_geometry(self):
        valid = {
            "same_conversation": True,
            "archived": True,
            "action": "unarchive",
            "geometry": {
                "center_x": 60,
                "center_y": 20,
                "width": 121,
                "height": 36,
                "viewport_width": 1280,
                "viewport_height": 720,
            },
        }
        self.assertEqual(CDPClient._native_click_coordinates(valid), (60.0, 20.0))

        failures = (
            (None, "geometry 형식"),
            ({"center_x": float("nan")}, "finite numeric"),
            ({"center_y": True}, "finite numeric"),
            ({"width": 0}, "geometry가 양수"),
            ({"viewport_width": 0}, "viewport geometry"),
            ({"center_x": 1280}, "viewport 범위"),
        )
        for changes, expected_error in failures:
            with self.subTest(changes=changes):
                fallback = dict(valid)
                if changes is None:
                    fallback["geometry"] = None
                else:
                    geometry = dict(valid["geometry"])
                    geometry.update(changes)
                    fallback["geometry"] = geometry
                with self.assertRaisesRegex(CDPError, expected_error):
                    CDPClient._native_click_coordinates(fallback)

        invalid_action = dict(valid)
        invalid_action["action"] = "send"
        with self.assertRaisesRegex(CDPError, "native 활성화 조건"):
            CDPClient._native_click_coordinates(invalid_action)

    def test_native_click_stops_on_cdp_error(self):
        requests: list[tuple[str, dict[str, object]]] = []

        class FailingWebSocket:
            def request(self, method, params):
                requests.append((method, params))
                return {"error": {"message": "injected"}}

        with self.assertRaisesRegex(CDPError, "native CDP 활성화 응답"):
            CDPClient._dispatch_native_click(FailingWebSocket(), 60.0, 20.0)

        self.assertEqual(
            requests,
            [("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 60.0, "y": 20.0})],
        )

    def test_restore_native_activation_requires_subsequent_composer_success(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            slot = settings.slot(1)
            conversation_url = "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555"
            requests: list[tuple[str, dict[str, object]]] = []
            composer_readbacks = iter(
                (
                    {
                        "conversation_url": conversation_url,
                        "same_conversation": True,
                        "page_ready": True,
                        "composer_ready": False,
                    },
                    {
                        "conversation_url": conversation_url,
                        "same_conversation": True,
                        "page_ready": True,
                        "composer_ready": False,
                    },
                )
            )

            class FakeWebSocket:
                def __init__(self, _url, _timeout):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, _exc_type, _exc, _traceback):
                    return None

                def request(self, method, params):
                    requests.append((method, params))
                    if method == "Page.navigate":
                        return {"result": {"frameId": "frame-1"}}
                    if method == "Input.dispatchMouseEvent":
                        return {"result": {}}
                    expression = params["expression"]
                    if "backend-api/conversation" in expression:
                        value = {
                            "restored": True,
                            "auth_status": 200,
                            "patch_status": 200,
                            "readback_status": 200,
                            "is_archived": False,
                        }
                    elif "const currentConversationControl" in expression:
                        value = {
                            "state": "native_activation_ready",
                            "same_conversation": True,
                            "archived": True,
                            "action": "unarchive",
                            "geometry": {
                                "center_x": 60,
                                "center_y": 20,
                                "width": 121,
                                "height": 36,
                                "viewport_width": 1280,
                                "viewport_height": 720,
                            },
                        }
                    elif "const composerReady" in expression:
                        value = next(composer_readbacks)
                    else:
                        raise AssertionError(f"unexpected expression: {expression}")
                    return {"result": {"result": {"value": value}}}

            targets = [
                {
                    "id": "chatgpt-target",
                    "type": "page",
                    "url": conversation_url,
                    "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/fake",
                }
            ]
            client = CDPClient(request_timeout=0.01)
            with patch.object(client, "_get_json", return_value=targets), patch(
                "oracle_browser_slots.cdp._WebSocket", FakeWebSocket
            ), patch(
                "oracle_browser_slots.cdp.time.monotonic", side_effect=(0.0, 1.0, 11.0)
            ), patch("oracle_browser_slots.cdp.time.sleep"), self.assertRaisesRegex(
                CDPError, "안정적인 URL과 composer"
            ):
                client.restore_archived_conversation(slot, conversation_url)

            self.assertEqual(
                [
                    params["type"]
                    for method, params in requests
                    if method == "Input.dispatchMouseEvent"
                ],
                ["mouseMoved", "mousePressed", "mouseReleased"],
            )

    def test_archived_ui_fallback_excludes_unrelated_and_prompt_controls(self):
        expression = _archived_ui_fallback_expression(
            "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555"
        )

        self.assertIn('document.querySelectorAll("button,[role=\'button\'],[role=\'menuitem\']")', expression)
        self.assertIn("main,[role='main']", expression)
        self.assertIn("const archived = Array.from(document.querySelectorAll(\"main,[role='main']\"))", expression)
        self.assertIn("this (conversation|chat) (is|has been|was) archived", expression)
        self.assertIn("nav,aside,[role='navigation'],[role='complementary'],form", expression)
        self.assertIn("[data-testid*='composer' i]", expression)
        self.assertIn("[data-testid*='prompt' i]", expression)
        self.assertNotIn("textarea", expression)
        self.assertNotIn("contenteditable", expression)
        self.assertNotIn("Page.navigate", expression)
        self.assertNotIn("Input.", expression)

    def test_restore_without_exact_archive_control_is_bounded_without_activation(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            slot = settings.slot(1)
            conversation_url = "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555"
            requests: list[tuple[str, dict[str, object]]] = []

            class FakeWebSocket:
                def __init__(self, _url, _timeout):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, _exc_type, _exc, _traceback):
                    return None

                def request(self, method, params):
                    requests.append((method, params))
                    if method == "Page.navigate":
                        return {"result": {"frameId": "frame-1"}}
                    expression = params["expression"]
                    if "backend-api/conversation" in expression:
                        value = {
                            "restored": True,
                            "auth_status": 200,
                            "patch_status": 200,
                            "readback_status": 200,
                            "is_archived": False,
                        }
                    elif "const currentConversationControl" in expression:
                        value = {
                            "state": "no_exact_control",
                            "same_conversation": True,
                            "archived": False,
                            "activated": False,
                            "action": None,
                        }
                    elif "const composerReady" in expression:
                        value = {
                            "conversation_url": conversation_url,
                            "same_conversation": True,
                            "page_ready": True,
                            "composer_ready": False,
                        }
                    else:
                        raise AssertionError(f"unexpected expression: {expression}")
                    return {"result": {"result": {"value": value}}}

            targets = [
                {
                    "id": "chatgpt-target",
                    "type": "page",
                    "url": conversation_url,
                    "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/fake",
                }
            ]
            client = CDPClient(request_timeout=0.01)
            with patch.object(client, "_get_json", return_value=targets), patch(
                "oracle_browser_slots.cdp._WebSocket", FakeWebSocket
            ), patch(
                "oracle_browser_slots.cdp.time.monotonic", side_effect=(0.0, 11.0)
            ), self.assertRaisesRegex(CDPError, "exact archive control"):
                client.restore_archived_conversation(slot, conversation_url)

            self.assertEqual(
                [method for method, _params in requests],
                ["Runtime.evaluate", "Page.navigate", "Runtime.evaluate", "Runtime.evaluate"],
            )

    def test_restore_stops_without_stock_ready_state_when_ui_fallback_fails(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            slot = settings.slot(1)
            conversation_url = "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555"
            targets = [
                {
                    "id": "chatgpt-target",
                    "type": "page",
                    "url": conversation_url,
                    "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/fake",
                }
            ]
            failures = (
                (
                    {
                        "state": "activation_failed",
                        "same_conversation": True,
                        "archived": True,
                        "activated": False,
                        "action": "unarchive",
                    },
                    "control 활성화",
                ),
                (
                    {
                        "state": "url_mismatch",
                        "same_conversation": False,
                        "archived": False,
                        "activated": False,
                        "action": None,
                    },
                    "대화 URL이 변경",
                ),
            )
            for fallback_readback, expected_error in failures:
                with self.subTest(fallback_readback=fallback_readback):
                    requests: list[tuple[str, dict[str, object]]] = []

                    class FakeWebSocket:
                        def __init__(self, _url, _timeout):
                            pass

                        def __enter__(self):
                            return self

                        def __exit__(self, _exc_type, _exc, _traceback):
                            return None

                        def request(self, method, params):
                            requests.append((method, params))
                            if method == "Page.navigate":
                                return {"result": {"frameId": "frame-1"}}
                            expression = params["expression"]
                            if "backend-api/conversation" in expression:
                                value = {
                                    "restored": True,
                                    "auth_status": 200,
                                    "patch_status": 200,
                                    "readback_status": 200,
                                    "is_archived": False,
                                }
                            elif "const currentConversationControl" in expression:
                                value = fallback_readback
                            elif "const composerReady" in expression:
                                value = {
                                    "conversation_url": conversation_url,
                                    "same_conversation": True,
                                    "page_ready": True,
                                    "composer_ready": False,
                                }
                            else:
                                raise AssertionError(f"unexpected expression: {expression}")
                            return {"result": {"result": {"value": value}}}

                    client = CDPClient(request_timeout=0.01)
                    with patch.object(client, "_get_json", return_value=targets), patch(
                        "oracle_browser_slots.cdp._WebSocket", FakeWebSocket
                    ), self.assertRaisesRegex(CDPError, expected_error):
                        client.restore_archived_conversation(slot, conversation_url)

                    self.assertEqual(
                        [method for method, _params in requests],
                        [
                            "Runtime.evaluate",
                            "Page.navigate",
                            "Runtime.evaluate",
                            "Runtime.evaluate",
                        ],
                    )


class LauncherTests(unittest.TestCase):
    def test_new_chrome_is_detached_from_prepare_process(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            settings.chrome_path.write_text("#!/bin/sh\n", encoding="utf-8")
            settings.chrome_path.chmod(0o755)
            launcher = ChromeLauncher(settings, LaunchCDP())
            process = Mock(pid=12345)

            with patch.object(launcher, "_port_is_open", return_value=False), patch.object(
                launcher, "_profile_process_exists", return_value=False
            ), patch("oracle_browser_slots.launcher.subprocess.Popen", return_value=process) as popen:
                self.assertEqual(launcher.ensure_running(settings.slot(2)), 12345)

            self.assertTrue(popen.call_args.kwargs["start_new_session"])

    def test_ready_cdp_with_wrong_profile_is_not_reused(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            cdp = ReadyCDP()
            launcher = ChromeLauncher(settings, cdp)
            slot = settings.slot(1)
            wrong_profile = root / "other-profile"
            process_arguments = (
                "/usr/bin/google-chrome",
                f"--remote-debugging-port={slot.port}",
                f"--user-data-dir={wrong_profile}",
            )

            with patch(
                "oracle_browser_slots.launcher._proc_arguments",
                return_value=iter((process_arguments,)),
            ), patch("oracle_browser_slots.launcher.subprocess.Popen") as popen:
                with self.assertRaisesRegex(PrepareError, "정확한 프로필") as raised:
                    launcher.ensure_running(slot)

            self.assertTrue(raised.exception.operator_action.startswith("포트"))
            popen.assert_not_called()

            service = SlotService(settings, cdp=cdp, launcher=launcher)
            with patch(
                "oracle_browser_slots.launcher._proc_arguments",
                return_value=iter((process_arguments,)),
            ):
                result = service.prepare(1)
            self.assertEqual(result["status"], UNAVAILABLE)
            self.assertIn("CDP", result["reason"])
            self.assertTrue(result["operator_action"])

    def test_ready_cdp_without_local_chrome_owner_is_not_reused(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            launcher = ChromeLauncher(settings, ReadyCDP())
            slot = settings.slot(1)

            with patch(
                "oracle_browser_slots.launcher._proc_arguments",
                return_value=iter(()),
            ):
                with self.assertRaisesRegex(PrepareError, "/proc"):
                    launcher.ensure_running(slot)

    def test_flattened_cmdline_chrome_owner_is_reused(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            launcher = ChromeLauncher(settings, ReadyCDP())
            slot = settings.slot(1)
            flattened = (
                f"/usr/bin/google-chrome --remote-debugging-port={slot.port} "
                f"--remote-debugging-address=127.0.0.1 "
                f"--user-data-dir={slot.profile_dir} https://chatgpt.com/",
            )

            with patch(
                "oracle_browser_slots.launcher._proc_arguments",
                return_value=iter((flattened,)),
            ):
                self.assertIsNone(launcher.ensure_running(slot))

    def test_flattened_cmdline_other_port_is_not_owner(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            launcher = ChromeLauncher(settings, ReadyCDP())
            slot = settings.slot(1)
            flattened = (
                "/usr/bin/google-chrome "
                f"--remote-debugging-port={slot.port + 1} "
                f"--user-data-dir={slot.profile_dir} https://chatgpt.com/",
            )

            with patch(
                "oracle_browser_slots.launcher._proc_arguments",
                return_value=iter((flattened,)),
            ):
                with self.assertRaisesRegex(PrepareError, "/proc"):
                    launcher.ensure_running(slot)

    def test_is_chrome_process_accepts_flattened_cmdline(self):
        flattened = (
            "/opt/google/chrome/chrome --remote-debugging-port=19222 "
            "--user-data-dir=/home/user01/.oracle/browser-profiles/slot-1 "
            "https://chatgpt.com/",
        )
        self.assertTrue(_is_chrome_process(flattened))

    def test_flattened_cmdline_profile_in_use_blocks_launch(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            settings.chrome_path.write_text("#!/bin/sh\n", encoding="utf-8")
            settings.chrome_path.chmod(0o755)
            launcher = ChromeLauncher(settings, LaunchCDP())
            slot = settings.slot(1)
            flattened = (
                f"/usr/bin/google-chrome --remote-debugging-port={slot.port} "
                f"--user-data-dir={slot.profile_dir} https://chatgpt.com/",
            )

            with patch.object(
                launcher, "_port_is_open", return_value=False
            ), patch(
                "oracle_browser_slots.launcher._proc_arguments",
                return_value=iter((flattened,)),
            ):
                with self.assertRaisesRegex(PrepareError, "프로필은 사용 중"):
                    launcher.ensure_running(slot)

    def test_has_flag_does_not_match_longer_port_token(self):
        flattened = (
            "/opt/google/chrome/chrome --remote-debugging-port=192220 "
            "--user-data-dir=/tmp/slot-1 https://chatgpt.com/",
        )
        self.assertFalse(_has_flag(flattened, "--remote-debugging-port=19222"))


class SlotServiceTests(unittest.TestCase):
    def test_slot_ports_and_profiles_are_fixed_and_distinct(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            slots = [settings.slot(slot_id) for slot_id in SLOT_IDS]
            self.assertEqual(
                [slot.port for slot in slots],
                [19222, 19223, 19224, 19225, 19226, 19231],
            )
            self.assertEqual(
                [str(slot.profile_dir) for slot in slots],
                [
                    f"{directory}/profiles/slot-1",
                    f"{directory}/profiles/slot-2",
                    f"{directory}/profiles/slot-3",
                    f"{directory}/profiles/slot-4",
                    f"{directory}/profiles/slot-5",
                    f"{directory}/profiles/slot-10",
                ],
            )

            for unmanaged_slot in (6, 7, 8, 9, 11):
                with self.subTest(unmanaged_slot=unmanaged_slot):
                    with self.assertRaises(ValueError):
                        settings.slot(unmanaged_slot)

    def test_one_slot_failure_does_not_hide_other_statuses(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP(
                {
                    1: CDPError("slot 1 CDP failed"),
                    2: LoginResult(True, "slot 2 ready", "없음"),
                    3: LoginResult(False, "login required", "sign in"),
                    4: LoginResult(True, "slot 4 ready", "없음"),
                    5: LoginResult(True, "slot 5 ready", "없음"),
                    10: LoginResult(True, "slot 10 ready", "없음"),
                }
            )
            service = SlotService(
                settings,
                cdp=cdp,
                launcher=FakeLauncher(),
            )

            prepared = [service.prepare(slot_id) for slot_id in SLOT_IDS]
            self.assertEqual(prepared[0]["status"], UNAVAILABLE)
            self.assertEqual(prepared[1]["status"], AVAILABLE)
            self.assertEqual(prepared[2]["status"], UNAVAILABLE)
            self.assertEqual(prepared[3]["status"], AVAILABLE)
            self.assertEqual(prepared[4]["status"], AVAILABLE)
            self.assertEqual(prepared[5]["status"], AVAILABLE)

            statuses = service.status_all()
            self.assertEqual(
                [record["slot_id"] for record in statuses], list(SLOT_IDS)
            )
            self.assertEqual(statuses[0]["status"], UNAVAILABLE)
            self.assertEqual(statuses[1]["status"], AVAILABLE)
            self.assertEqual(statuses[2]["status"], UNAVAILABLE)
            self.assertEqual(statuses[3]["status"], AVAILABLE)
            self.assertEqual(statuses[4]["status"], AVAILABLE)
            self.assertEqual(statuses[5]["status"], AVAILABLE)
            self.assertIn(2, cdp.calls)
            self.assertIn(3, cdp.calls)
            self.assertIn(4, cdp.calls)
            self.assertIn(5, cdp.calls)
            self.assertIn(10, cdp.calls)

    def test_slot_ten_has_independent_state_single_occupancy_and_duplicate_boundary(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            service = SlotService(
                settings,
                cdp=FakeCDP(
                    {
                        1: LoginResult(True, "slot 1 ready", "없음"),
                        10: LoginResult(True, "slot 10 ready", "없음"),
                    }
                ),
                launcher=FakeLauncher(),
            )
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            self.assertEqual(service.prepare(10)["status"], AVAILABLE)

            first = service.claim_job(10, "slot-ten-job")
            self.assertTrue(first["accepted"])
            duplicate = service.claim_job(10, "slot-ten-job")
            competing = service.claim_job(10, "other-slot-ten-job")

            self.assertFalse(duplicate["accepted"])
            self.assertFalse(competing["accepted"])
            self.assertEqual(duplicate["record"]["current_job_id"], "slot-ten-job")
            self.assertEqual(competing["record"]["status"], OCCUPIED)
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(10)["status"], OCCUPIED)
            self.assertTrue(
                service.finish_job(
                    10,
                    "slot-ten-job",
                    first["record"]["started_at"],
                    "success",
                    0,
                    "complete",
                    "없음",
                )["released"]
            )
            self.assertEqual(service.status(10)["status"], AVAILABLE)
            self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_occupancy_is_readable_and_abandoned_work_requires_reprepare(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP({2: LoginResult(True, "slot 2 ready", "없음")})
            store = StateStore(settings.state_root)
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(2)["status"], AVAILABLE)

            state = store.read(2)
            self.assertIsNotNone(state)
            state["occupancy"] = {
                "job_id": "task-2",
                "started_at": "2026-08-01T00:00:00Z",
                "owner_pid": os.getpid(),
                "owner_starttime": process_starttime(os.getpid()),
            }
            store.write(2, state)
            occupied = service.status(2)
            self.assertEqual(occupied["status"], OCCUPIED)
            self.assertEqual(occupied["job_id"], "task-2")
            self.assertEqual(occupied["started_at"], "2026-08-01T00:00:00Z")

            state = store.read(2)
            state["occupancy"]["owner_pid"] = 999999999
            store.write(2, state)
            abandoned = service.status(2)
            self.assertEqual(abandoned["status"], UNAVAILABLE)
            self.assertIn("identity", abandoned["reason"])

            recovered = service.prepare(2)
            self.assertEqual(recovered["status"], AVAILABLE)


class SettingsTests(unittest.TestCase):
    def test_port_base_maximum_is_accepted_and_derives_slot_ten_port(self):
        settings = Settings.from_env(
            {
                "HOME": "/home/test",
                "ORACLE_BROWSER_SLOTS_PORT_BASE": "65526",
            }
        )
        self.assertEqual(settings.port_base, 65526)
        self.assertEqual(settings.slot(10).port, 65535)
        self.assertEqual(
            settings.slot(10).profile_dir,
            Path("/home/test/.oracle/browser-profiles/slot-10"),
        )

    def test_port_base_at_or_above_65527_is_rejected(self):
        for port_base in (65527, 65528, 65531, 65535, 65536):
            with self.subTest(port_base=port_base):
                with self.assertRaisesRegex(ValueError, "between 1 and 65526"):
                    Settings.from_env(
                        {
                            "HOME": "/home/test",
                            "ORACLE_BROWSER_SLOTS_PORT_BASE": str(port_base),
                        }
                    )


class PreparePersistenceTests(unittest.TestCase):
    def test_prepare_write_failure_is_not_reported_as_available(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            service = SlotService(
                settings,
                store=FailingWriteStore(settings.state_root),
                cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            result = service.prepare(1)
            self.assertEqual(result["status"], UNAVAILABLE)
            self.assertIn("저장하지 못했습니다", result["reason"])
            self.assertTrue(result["operator_action"])

    def test_prepare_readback_mismatch_is_not_reported_as_available(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            service = SlotService(
                settings,
                store=MismatchedReadbackStore(settings.state_root),
                cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            result = service.prepare(1)
            self.assertEqual(result["status"], UNAVAILABLE)
            self.assertIn("readback", result["reason"])
            self.assertIn("prepare", result["operator_action"])

    def test_prepare_success_has_authoritative_prepared_readback(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            store = StateStore(settings.state_root)
            service = SlotService(
                settings,
                store=store,
                cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            result = service.prepare(1)
            self.assertEqual(result["status"], AVAILABLE)
            state = store.read(1)
            self.assertEqual(state["slot_id"], 1)
            self.assertEqual(state["port"], 19222)
            self.assertEqual(state["profile_dir"], str(settings.slot(1).profile_dir))
            self.assertTrue(state["prepared"])
            self.assertFalse(state["requires_reprepare"])


class JobRunnerTests(unittest.TestCase):
    def test_compatible_slots_use_exact_model_and_reasoning_capabilities(self):
        with TemporaryDirectory() as directory:
            service = SlotService(settings_for(Path(directory)))
            runner = JobRunner(service, oracle_cli_path=TEST_ORACLE_CLI)

            capabilities = {
                None: (1, 2, 3, 4, 5, 10),
                "standard": (1, 2, 3, 4, 5, 10),
                "medium": (1, 2, 3, 4, 5, 10),
                "light": (1, 2, 10),
                "instant": (1, 2, 10),
                "low": (1, 2, 10),
                "heavy": (1, 2, 10),
                "extra-high": (1, 2, 10),
                "extrahigh": (1, 2, 10),
                "xhigh": (1, 2, 10),
                "pro": (1, 2, 10),
                "extended": (3, 4, 5, 1, 2, 10),
                "high": (3, 4, 5, 1, 2, 10),
            }
            for reasoning, expected in capabilities.items():
                with self.subTest(reasoning=reasoning):
                    command = [TEST_ORACLE_CLI, "--model", "gpt-5.6-sol"]
                    if reasoning is not None:
                        command.extend(("--browser-thinking-time", reasoning))
                    self.assertEqual(runner.compatible_slots(command), expected)

            self.assertEqual(
                runner.compatible_slots(
                    [
                        TEST_ORACLE_CLI,
                        "--model=gpt-5.6",
                        "--browser-thinking-time=extended",
                    ]
                ),
                (3, 4, 5, 1, 2, 10),
            )
            self.assertEqual(
                runner.compatible_slots([TEST_ORACLE_CLI, "--model", "gpt-5.5-pro"]),
                (),
            )

    def test_missing_oracle_flags_are_injected_for_selected_slot(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            service = SlotService(
                settings,
                cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            captured: dict[str, object] = {}

            def popen(argv, *, env, close_fds):
                captured["argv"] = argv
                return ReturnCodeChild(0)

            result = JobRunner(
                service,
                popen_factory=popen,
                oracle_cli_path=TEST_ORACLE_CLI,
            ).run(1, "inject-flags", [TEST_ORACLE_CLI, "-p", "task"])
            self.assertTrue(result["accepted"])
            self.assertEqual(
                captured["argv"],
                [
                    TEST_ORACLE_CLI,
                    "-p",
                    "task",
                    "--engine",
                    "browser",
                    "--browser-model-strategy",
                    "current",
                    "--remote-chrome",
                    "127.0.0.1:19222",
                ],
            )

    def test_oracle_equals_flags_are_accepted_and_transport_is_selected(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            service = SlotService(
                settings,
                cdp=FakeCDP({2: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            self.assertEqual(service.prepare(2)["status"], AVAILABLE)
            captured: dict[str, object] = {}

            def popen(argv, *, env, close_fds):
                captured["argv"] = argv
                return ReturnCodeChild(0)

            command = [
                TEST_ORACLE_CLI,
                "--engine=browser",
                "--browser-model-strategy=current",
                "--remote-chrome=127.0.0.1:19223",
                "--browser-archive=auto",
            ]
            result = JobRunner(
                service,
                popen_factory=popen,
                oracle_cli_path=TEST_ORACLE_CLI,
            ).run(2, "equals-flags", command)
            self.assertTrue(result["accepted"])
            self.assertEqual(captured["argv"], command)

    def test_conflicting_duplicate_or_noncanonical_transport_is_rejected_before_claim(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            service = SlotService(
                settings,
                cdp=FakeCDP({2: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            self.assertEqual(service.prepare(2)["status"], AVAILABLE)
            popen_calls: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                popen_calls.append(argv)
                return ReturnCodeChild(0)

            runner = JobRunner(
                service,
                popen_factory=popen,
                oracle_cli_path=TEST_ORACLE_CLI,
            )
            invalid_commands = (
                (
                    "wrong-slot-remote",
                    [
                        TEST_ORACLE_CLI,
                        "--engine",
                        "browser",
                        "--browser-model-strategy",
                        "current",
                        "--remote-chrome",
                        "127.0.0.1:19222",
                    ],
                    "충돌",
                ),
                (
                    "duplicate-engine",
                    [TEST_ORACLE_CLI, "--engine", "browser", "--engine=browser"],
                    "중복",
                ),
                (
                    "other-transport",
                    [TEST_ORACLE_CLI, "--browser-manual-login"],
                    "외부 transport",
                ),
                (
                    "basename-only",
                    ["oracle", "--engine", "browser"],
                    "canonical",
                ),
            )
            for job_id, command, reason_fragment in invalid_commands:
                with self.subTest(job_id=job_id):
                    with patch.object(service, "claim_job", wraps=service.claim_job) as claim:
                        result = runner.run(2, job_id, command)
                    self.assertFalse(result["accepted"])
                    self.assertEqual(result["exit_code"], 2)
                    self.assertIn(reason_fragment, result["record"]["reason"])
                    claim.assert_not_called()
            self.assertEqual(popen_calls, [])

    def test_success_and_nonzero_failure_release_occupancy(self):
        for return_code, expected_outcome in ((0, "success"), (7, "failed")):
            with self.subTest(return_code=return_code), TemporaryDirectory() as directory:
                settings = settings_for(Path(directory))
                cdp = FakeCDP({1: LoginResult(True, "ready", "없음")})
                service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
                self.assertEqual(service.prepare(1)["status"], AVAILABLE)
                captured: dict[str, object] = {}

                def popen(argv, *, env, close_fds):
                    captured["argv"] = argv
                    captured["env"] = env
                    captured["close_fds"] = close_fds
                    return ReturnCodeChild(return_code)

                records: list[dict[str, object]] = []
                result = JobRunner(
                    service,
                    popen_factory=popen,
                    oracle_cli_path=TEST_ORACLE_CLI,
                ).run(
                    1,
                    f"job-{return_code}",
                    oracle_argv(19222, "--arg"),
                    emit=records.append,
                )
                self.assertEqual(result["exit_code"], return_code)
                self.assertEqual(result["record"]["outcome"], expected_outcome)
                self.assertTrue(result["record"]["released"])
                self.assertEqual(len(records), 2)
                self.assertEqual(records[0]["state_after"], OCCUPIED)
                self.assertEqual(records[1]["state_after"], AVAILABLE)
                self.assertEqual(captured["argv"], oracle_argv(19222, "--arg"))
                self.assertEqual(captured["env"]["ORACLE_BROWSER_REMOTE_CHROME"], "127.0.0.1:19222")
                self.assertEqual(captured["env"]["ORACLE_BROWSER_SLOT_PORT"], "19222")
                self.assertTrue(captured["close_fds"])
                self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_different_slots_run_independently(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP(
                {
                    1: LoginResult(True, "ready", "없음"),
                    2: LoginResult(True, "ready", "없음"),
                }
            )
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            self.assertEqual(service.prepare(2)["status"], AVAILABLE)
            commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return ReturnCodeChild(0)

            runner = JobRunner(
                service,
                popen_factory=popen,
                oracle_cli_path=TEST_ORACLE_CLI,
            )
            first = runner.run(1, "slot-1-job", oracle_argv(19222, "one"))
            second = runner.run(2, "slot-2-job", oracle_argv(19223, "two"))
            self.assertTrue(first["accepted"])
            self.assertTrue(second["accepted"])
            self.assertEqual(
                commands,
                [oracle_argv(19222, "one"), oracle_argv(19223, "two")],
            )
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(2)["status"], AVAILABLE)

    def test_spawn_error_is_reported_and_releases_occupancy(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP({1: LoginResult(True, "ready", "없음")})
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)

            def failing_popen(argv, *, env, close_fds):
                raise FileNotFoundError("missing command")

            result = JobRunner(
                service,
                popen_factory=failing_popen,
                oracle_cli_path=TEST_ORACLE_CLI,
            ).run(
                1, "spawn-error", oracle_argv(19222, "missing-command")
            )
            self.assertEqual(result["exit_code"], 127)
            self.assertEqual(result["record"]["outcome"], "spawn_error")
            self.assertTrue(result["record"]["released"])
            self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_general_popen_exception_is_reported_and_releases_occupancy(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP({1: LoginResult(True, "ready", "없음")})
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)

            def failing_popen(argv, *, env, close_fds):
                raise RuntimeError("unexpected popen failure")

            result = JobRunner(
                service,
                popen_factory=failing_popen,
                oracle_cli_path=TEST_ORACLE_CLI,
            ).run(1, "general-spawn-error", oracle_argv(19222))
            self.assertEqual(result["record"]["outcome"], "spawn_error")
            self.assertIn("예외", result["record"]["reason"])
            self.assertTrue(result["record"]["released"])
            self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_general_wait_exception_cleans_child_and_releases_occupancy(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP({1: LoginResult(True, "ready", "없음")})
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            result = JobRunner(
                service,
                popen_factory=lambda argv, *, env, close_fds: ExplodingWaitChild(),
                oracle_cli_path=TEST_ORACLE_CLI,
            ).run(1, "general-wait-error", oracle_argv(19222))
            self.assertEqual(result["record"]["outcome"], "failed")
            self.assertIn("예외", result["record"]["reason"])
            self.assertTrue(result["record"]["released"])
            self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_interrupt_is_reported_and_releases_occupancy(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP({1: LoginResult(True, "ready", "없음")})
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            result = JobRunner(
                service,
                popen_factory=lambda argv, *, env, close_fds: InterruptingChild(),
                oracle_cli_path=TEST_ORACLE_CLI,
            ).run(1, "interrupted", oracle_argv(19222))
            self.assertEqual(result["exit_code"], 143)
            self.assertEqual(result["record"]["outcome"], "interrupted")
            self.assertTrue(result["record"]["released"])
            self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_competing_runs_start_one_child_and_reject_the_other(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP({1: LoginResult(True, "ready", "없음")})
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            child_started = threading.Event()
            release_child = threading.Event()
            popen_calls: list[list[str]] = []
            calls_lock = threading.Lock()

            def popen(argv, *, env, close_fds):
                with calls_lock:
                    popen_calls.append(argv)
                return BlockingChild(child_started, release_child)

            runner = JobRunner(
                service,
                popen_factory=popen,
                oracle_cli_path=TEST_ORACLE_CLI,
            )
            barrier = threading.Barrier(2)
            results: list[dict[str, object]] = []

            def invoke(job_id: str) -> None:
                barrier.wait()
                results.append(runner.run(1, job_id, oracle_argv(19222, job_id)))

            first = threading.Thread(target=invoke, args=("job-a",))
            second = threading.Thread(target=invoke, args=("job-b",))
            first.start()
            second.start()
            self.assertTrue(child_started.wait(timeout=5))
            running_status = service.status(1)
            self.assertEqual(running_status["status"], OCCUPIED)
            self.assertIn(running_status["job_id"], {"job-a", "job-b"})
            self.assertTrue(running_status["started_at"])
            deadline = time.monotonic() + 5
            while len(results) < 1 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(len(popen_calls), 1)
            release_child.set()
            first.join(timeout=5)
            second.join(timeout=5)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(sum(bool(result["accepted"]) for result in results), 1)
            rejected = next(result for result in results if not result["accepted"])
            self.assertEqual(rejected["record"]["status"], OCCUPIED)
            self.assertIn("두 번째", rejected["record"]["reason"])
            self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_pid_starttime_mismatch_blocks_run_until_prepare(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP({1: LoginResult(True, "ready", "없음")})
            store = StateStore(settings.state_root)
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            state = store.read(1)
            state["occupancy"] = {
                "job_id": "orphaned",
                "started_at": "2026-08-01T00:00:00Z",
                "owner_pid": os.getpid(),
                "owner_starttime": "not-the-current-starttime",
            }
            store.write(1, state)

            status = service.status(1)
            self.assertEqual(status["status"], UNAVAILABLE)
            self.assertIn("identity", status["reason"])
            rejected = service.claim_job(1, "new-job")
            self.assertFalse(rejected["accepted"])
            self.assertEqual(rejected["record"]["status"], UNAVAILABLE)
            self.assertIn("prepare", rejected["record"]["operator_action"])

            recovered = service.prepare(1)
            self.assertEqual(recovered["status"], AVAILABLE)

    def test_runner_process_loss_leaves_unavailable_until_prepare(self):
        with TemporaryDirectory() as directory:
            settings = settings_for(Path(directory))
            cdp = FakeCDP({1: LoginResult(True, "ready", "없음")})
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)

            context = multiprocessing.get_context("fork")
            result_queue = context.Queue()
            release_event = context.Event()
            runner_process = context.Process(
                target=claim_and_hold_worker,
                args=(settings, "lost-runner", result_queue, release_event),
            )
            runner_process.start()
            claim_result = result_queue.get(timeout=5)
            self.assertTrue(claim_result["accepted"])
            runner_process.kill()
            runner_process.join(timeout=5)
            self.assertFalse(runner_process.is_alive())

            status = service.status(1)
            self.assertEqual(status["status"], UNAVAILABLE)
            self.assertEqual(status["job_id"], "lost-runner")
            rejected = service.claim_job(1, "replacement")
            self.assertFalse(rejected["accepted"])
            self.assertEqual(rejected["record"]["status"], UNAVAILABLE)
            recovered = service.prepare(1)
            self.assertEqual(recovered["status"], AVAILABLE)


class CliTests(unittest.TestCase):
    def test_direct_cli_status_uses_safe_empty_runtime(self):
        project_root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["ORACLE_BROWSER_SLOTS_STATE_ROOT"] = f"{directory}/state"
            environment["ORACLE_BROWSER_SLOTS_PROFILE_ROOT"] = f"{directory}/profiles"
            completed = subprocess.run(
                [str(project_root / "bin" / "oracle-browser-slots"), "status"],
                cwd=project_root,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["operation"], "status")
            self.assertEqual(
                [slot["slot_id"] for slot in payload["slots"]], list(SLOT_IDS)
            )
            self.assertEqual({slot["status"] for slot in payload["slots"]}, {"미준비"})
            self.assertEqual(
                [slot["port"] for slot in payload["slots"]],
                [19222, 19223, 19224, 19225, 19226, 19231],
            )
            self.assertEqual(
                [slot["profile_dir"] for slot in payload["slots"]],
                [
                    f"{directory}/profiles/slot-1",
                    f"{directory}/profiles/slot-2",
                    f"{directory}/profiles/slot-3",
                    f"{directory}/profiles/slot-4",
                    f"{directory}/profiles/slot-5",
                    f"{directory}/profiles/slot-10",
                ],
            )

    def test_parser_accepts_slot_ten_and_rejects_unmanaged_slots(self):
        from oracle_browser_slots.cli import build_parser

        parser = build_parser()
        self.assertEqual(parser.parse_args(["prepare", "--slot", "10"]).slot, 10)
        self.assertEqual(parser.parse_args(["status", "--slot", "4"]).slot, 4)
        self.assertEqual(
            parser.parse_args(
                [
                    "run",
                    "--slot",
                    "10",
                    "--job-id",
                    "job-ten",
                    "--",
                    CANONICAL_ORACLE_CLI,
                    "-p",
                    "task",
                ]
            ).slot,
            10,
        )
        for unmanaged_slot in (6, 7, 8, 9, 11):
            with self.subTest(unmanaged_slot=unmanaged_slot):
                with self.assertRaises(SystemExit) as invalid:
                    parser.parse_args(
                        ["prepare", "--slot", str(unmanaged_slot)]
                    )
                self.assertEqual(invalid.exception.code, 2)

    def test_public_run_rejects_unprepared_slot_without_starting_command(self):
        project_root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["ORACLE_BROWSER_SLOTS_STATE_ROOT"] = f"{directory}/state"
            environment["ORACLE_BROWSER_SLOTS_PROFILE_ROOT"] = f"{directory}/profiles"
            completed = subprocess.run(
                [
                    str(project_root / "bin" / "oracle-browser-slots"),
                    "run",
                    "--slot",
                    "2",
                    "--job-id",
                    "unprepared-job",
                    "--",
                    CANONICAL_ORACLE_CLI,
                    "--engine",
                    "browser",
                    "--browser-model-strategy",
                    "current",
                    "--remote-chrome",
                    "127.0.0.1:19223",
                ],
                cwd=project_root,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(completed.stdout, "")
            events = [json.loads(line) for line in completed.stderr.splitlines()]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event"], "rejected")
            self.assertEqual(events[0]["slot_id"], 2)
            self.assertEqual(events[0]["job_id"], "unprepared-job")
            self.assertEqual(events[0]["status"], "미준비")

    def test_public_submit_all_unavailable_is_safe_and_jsonl(self):
        project_root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["ORACLE_BROWSER_SLOTS_STATE_ROOT"] = f"{directory}/state"
            environment["ORACLE_BROWSER_SLOTS_PROFILE_ROOT"] = f"{directory}/profiles"
            environment["ORACLE_BROWSER_SLOTS_ORACLE_CLI"] = TEST_ORACLE_CLI
            completed = subprocess.run(
                [
                    str(project_root / "bin" / "oracle-browser-slots"),
                    "submit",
                    "--request-id",
                    "cli-unavailable",
                    "--",
                    TEST_ORACLE_CLI,
                    "-p",
                    "task",
                ],
                cwd=project_root,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stdout, "")
            events = [json.loads(line) for line in completed.stderr.splitlines()]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["operation"], "submit")
            self.assertEqual(events[0]["event"], "failed")
            self.assertEqual(events[0]["request_id"], "cli-unavailable")
            self.assertEqual(
                [slot["slot_id"] for slot in events[0]["slot_diagnostics"]],
                list(SLOT_IDS),
            )


class AutoAllocatorTests(unittest.TestCase):
    def _ready_service(self, root: Path, ready_slots=SLOT_IDS) -> SlotService:
        settings = settings_for(root)
        cdp = FakeCDP(
            {
                slot_id: LoginResult(True, f"slot {slot_id} ready", "없음")
                for slot_id in ready_slots
            }
        )
        service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
        for slot_id in ready_slots:
            self.assertEqual(service.prepare(slot_id)["status"], AVAILABLE)
        return service

    def _runner(self, service: SlotService, popen_factory):
        return JobRunner(
            service,
            popen_factory=popen_factory,
            oracle_cli_path=TEST_ORACLE_CLI,
        )

    def test_submit_rejects_incompatibility_and_missing_identity_before_file_preparation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            runner = self._runner(
                service,
                lambda _argv, **_kwargs: self.fail("child must not start"),
            )
            allocator = AutoAllocator(service, runner=runner, poll_interval=0.01)

            with patch.object(runner, "prepare_file_request") as prepare:
                incompatible = allocator.submit(
                    "incompatible-before-zip",
                    [
                        TEST_ORACLE_CLI,
                        "--browser-thinking-time",
                        "unsupported",
                        "--file",
                        "/must/not/be/read",
                    ],
                )
            self.assertEqual(incompatible["exit_code"], 2)
            prepare.assert_not_called()

            with patch(
                "oracle_browser_slots.allocator.current_process_identity",
                return_value=None,
            ), patch.object(runner, "prepare_file_request") as prepare:
                missing_identity = allocator.submit(
                    "identity-before-zip",
                    [TEST_ORACLE_CLI, "--file", "/must/not/be/read"],
                )
            self.assertEqual(missing_identity["exit_code"], 1)
            prepare.assert_not_called()

    def test_allocator_diagnostics_probe_only_deduplicated_compatible_slots(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root, ready_slots=(3, 5))
            allocator = AutoAllocator(service, poll_interval=0.01)

            with patch.object(service, "status", wraps=service.status) as status, patch.object(
                service,
                "status_all",
                side_effect=AssertionError("allocator admission must not probe all slots"),
            ):
                diagnostics = allocator._diagnostics((5, 3, 5))

            self.assertEqual([record["slot_id"] for record in diagnostics], [3, 5])
            self.assertEqual(
                [call.args[0] for call in status.call_args_list],
                [3, 5],
            )

    def test_non_head_waiter_probes_viability_once_until_promoted(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            held = [
                service.claim_job(slot_id, f"held-{slot_id}")
                for slot_id in SLOT_IDS
            ]
            self.assertTrue(all(result["accepted"] for result in held))
            first_queued = threading.Event()
            second_queued = threading.Event()
            first = AutoAllocator(
                service,
                runner=self._runner(
                    service, lambda _argv, **_kwargs: ReturnCodeChild(0)
                ),
                poll_interval=0.01,
            )
            second = AutoAllocator(
                service,
                runner=self._runner(
                    service, lambda _argv, **_kwargs: ReturnCodeChild(0)
                ),
                poll_interval=0.01,
            )
            results: dict[str, dict[str, object]] = {}

            def submit(allocator, request_id, queued):
                results[request_id] = allocator.submit(
                    request_id,
                    [TEST_ORACLE_CLI, "-p", request_id],
                    emit=lambda record: queued.set()
                    if record["event"] == "queued"
                    else None,
                )

            first_thread = threading.Thread(
                target=submit, args=(first, "probe-head", first_queued)
            )
            second_thread = threading.Thread(
                target=submit, args=(second, "probe-non-head", second_queued)
            )
            first_thread.start()
            self.assertTrue(first_queued.wait(timeout=5))
            with patch.object(
                second, "_diagnostics", wraps=second._diagnostics
            ) as diagnostics:
                second_thread.start()
                self.assertTrue(second_queued.wait(timeout=5))
                deadline = time.monotonic() + 1
                while (
                    not any(call.args for call in diagnostics.call_args_list)
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                viability_calls = [
                    call
                    for call in diagnostics.call_args_list
                    if call.args == (SLOT_IDS,)
                ]
                self.assertEqual(len(viability_calls), 1)
                time.sleep(0.05)
                viability_calls = [
                    call
                    for call in diagnostics.call_args_list
                    if call.args == (SLOT_IDS,)
                ]
                self.assertEqual(len(viability_calls), 1)

                self.assertTrue(
                    service.finish_job(
                        1,
                        "held-1",
                        held[0]["record"]["started_at"],
                        "success",
                        0,
                        "release",
                        "없음",
                    )["released"]
                )
                first_thread.join(timeout=5)
                second_thread.join(timeout=5)

            self.assertFalse(first_thread.is_alive())
            self.assertFalse(second_thread.is_alive())
            self.assertEqual(results["probe-head"]["exit_code"], 0)
            self.assertEqual(results["probe-non-head"]["exit_code"], 0)

    def test_submit_uses_first_available_slot_in_order(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root, ready_slots=(2, 3))
            commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return ReturnCodeChild(0)

            events: list[dict[str, object]] = []
            result = AutoAllocator(
                service,
                runner=self._runner(service, popen),
                poll_interval=0.01,
            ).submit(
                "auto-priority",
                [TEST_ORACLE_CLI, "-p", "task"],
                emit=events.append,
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["record"]["assigned_slot"], 2)
            self.assertEqual(result["record"]["attempted_slots"], [2])
            self.assertEqual(commands[0][-1], "127.0.0.1:19223")
            self.assertEqual([event["event"] for event in events], ["started", "finished"])
            self.assertEqual(service.status(2)["status"], AVAILABLE)

    def test_submit_uses_slot_five_endpoint_when_first_available(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root, ready_slots=(5,))
            commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return ReturnCodeChild(0)

            events: list[dict[str, object]] = []
            result = AutoAllocator(
                service,
                runner=self._runner(service, popen),
                poll_interval=0.01,
            ).submit(
                "auto-slot-five",
                [TEST_ORACLE_CLI, "-p", "task"],
                emit=events.append,
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["record"]["assigned_slot"], 5)
            self.assertEqual(result["record"]["attempted_slots"], [5])
            self.assertEqual(commands[0][-1], "127.0.0.1:19226")
            self.assertEqual(
                commands[0][commands[0].index("--remote-chrome") + 1],
                "127.0.0.1:19226",
            )
            self.assertEqual(
                [event["event"] for event in events], ["started", "finished"]
            )
            self.assertEqual(service.status(5)["status"], AVAILABLE)

    def test_submit_uses_slot_ten_endpoint_when_only_available(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root, ready_slots=(10,))
            commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return ReturnCodeChild(0)

            events: list[dict[str, object]] = []
            result = AutoAllocator(
                service,
                runner=self._runner(service, popen),
                poll_interval=0.01,
            ).submit(
                "auto-slot-ten",
                [TEST_ORACLE_CLI, "-p", "task"],
                emit=events.append,
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["record"]["assigned_slot"], 10)
            self.assertEqual(result["record"]["attempted_slots"], [10])
            self.assertEqual(
                commands[0][commands[0].index("--remote-chrome") + 1],
                "127.0.0.1:19231",
            )
            self.assertEqual(
                [event["event"] for event in events], ["started", "finished"]
            )
            self.assertEqual(service.status(10)["status"], AVAILABLE)

    def test_duplicate_request_running_rejects_before_second_claim_or_popen(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            child_started = threading.Event()
            child_release = threading.Event()
            commands: list[list[str]] = []
            first_result: dict[str, object] = {}

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return BlockingChild(child_started, child_release)

            allocator = AutoAllocator(
                service,
                runner=self._runner(service, popen),
                poll_interval=0.01,
            )

            def first_submit():
                first_result["result"] = allocator.submit(
                    "same-request", [TEST_ORACLE_CLI, "-p", "first"]
                )

            first = threading.Thread(target=first_submit)
            first.start()
            self.assertTrue(child_started.wait(timeout=5))

            duplicate_events: list[dict[str, object]] = []
            duplicate = allocator.submit(
                "same-request", [TEST_ORACLE_CLI, "-p", "duplicate"], emit=duplicate_events.append
            )

            self.assertEqual(duplicate["exit_code"], 2)
            self.assertEqual(len(commands), 1)
            self.assertEqual(len(duplicate_events), 1)
            self.assertEqual(duplicate_events[0]["event"], "rejected")
            self.assertEqual(duplicate_events[0]["outcome"], "rejected")
            self.assertIsNone(duplicate_events[0]["assigned_slot"])
            self.assertIsNone(duplicate_events[0]["existing_assigned_slot"])
            self.assertIn("동일 request ID", duplicate_events[0]["reason"])

            child_release.set()
            first.join(timeout=5)
            self.assertFalse(first.is_alive())
            self.assertEqual(first_result["result"]["record"]["outcome"], "success")

    def test_submit_rejects_request_id_held_by_manual_run(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            manual_claim = service.claim_job(1, "manual-same-request")
            self.assertTrue(manual_claim["accepted"])
            commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return ReturnCodeChild(0)

            events: list[dict[str, object]] = []
            result = AutoAllocator(
                service,
                runner=self._runner(service, popen),
                poll_interval=0.01,
            ).submit(
                "manual-same-request",
                [TEST_ORACLE_CLI, "-p", "duplicate-manual"],
                emit=events.append,
            )

            self.assertEqual(result["exit_code"], 2)
            self.assertEqual(len(commands), 0)
            self.assertEqual(events[0]["event"], "rejected")
            self.assertEqual(events[0]["existing_assigned_slot"], 1)
            self.assertEqual(service.status(2)["status"], AVAILABLE)
            self.assertTrue(
                service.finish_job(
                    1,
                    "manual-same-request",
                    manual_claim["record"]["started_at"],
                    "success",
                    0,
                    "release",
                    "없음",
                )["released"]
            )

    def test_submit_rejects_request_id_held_by_slot_ten(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root, ready_slots=(1, 10))
            slot_ten_claim = service.claim_job(10, "slot-ten-same-request")
            self.assertTrue(slot_ten_claim["accepted"])
            commands: list[list[str]] = []

            result = AutoAllocator(
                service,
                runner=self._runner(
                    service,
                    lambda argv, **_kwargs: commands.append(argv),
                ),
                poll_interval=0.01,
            ).submit(
                "slot-ten-same-request",
                [TEST_ORACLE_CLI, "-p", "must not start"],
            )

            self.assertEqual(result["exit_code"], 2)
            self.assertTrue(result["record"]["duplicate_request"])
            self.assertEqual(result["record"]["existing_assigned_slot"], 10)
            self.assertEqual(commands, [])
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(10)["status"], OCCUPIED)
            self.assertTrue(
                service.finish_job(
                    10,
                    "slot-ten-same-request",
                    slot_ten_claim["record"]["started_at"],
                    "success",
                    0,
                    "release",
                    "없음",
                )["released"]
            )

    def test_simultaneous_duplicate_submits_start_exactly_one_child(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            child_started = threading.Event()
            child_release = threading.Event()
            duplicate_done = threading.Event()
            commands: list[list[str]] = []
            results: list[dict[str, object]] = []
            results_lock = threading.Lock()
            barrier = threading.Barrier(2)

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return BlockingChild(child_started, child_release)

            allocator = AutoAllocator(
                service,
                runner=self._runner(service, popen),
                poll_interval=0.01,
            )

            def invoke():
                barrier.wait()
                result = allocator.submit("race-request", [TEST_ORACLE_CLI, "-p", "race"])
                with results_lock:
                    results.append(result)
                    if result["record"]["event"] == "rejected":
                        duplicate_done.set()

            threads = [threading.Thread(target=invoke) for _ in range(2)]
            for thread in threads:
                thread.start()
            self.assertTrue(child_started.wait(timeout=5))
            deadline = time.monotonic() + 5
            while not duplicate_done.is_set() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(duplicate_done.is_set())
            self.assertEqual(len(commands), 1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["record"]["event"], "rejected")
            self.assertFalse(results[0]["accepted"])

            child_release.set()
            for thread in threads:
                thread.join(timeout=5)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(len(commands), 1)
            self.assertEqual(sum(result["record"]["event"] == "rejected" for result in results), 1)
            self.assertEqual(sum(result["record"]["event"] == "finished" for result in results), 1)
            self.assertEqual(sum(result["record"]["outcome"] == "success" for result in results), 1)

    def test_completed_request_replay_never_starts_a_second_child(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return ReturnCodeChild(0)

            allocator = AutoAllocator(
                service,
                runner=self._runner(service, popen),
                poll_interval=0.01,
            )
            first = allocator.submit(
                "completed-request", [TEST_ORACLE_CLI, "-p", "first"]
            )
            duplicate_events: list[dict[str, object]] = []
            replay = allocator.submit(
                "completed-request",
                [TEST_ORACLE_CLI, "-p", "must not submit duplicate"],
                emit=duplicate_events.append,
            )

            self.assertEqual(first["record"]["outcome"], "success")
            self.assertEqual(replay["exit_code"], 2)
            self.assertEqual(len(commands), 1)
            self.assertEqual(len(duplicate_events), 1)
            self.assertEqual(duplicate_events[0]["event"], "rejected")
            self.assertTrue(duplicate_events[0]["duplicate_request"])

    def test_duplicate_queue_request_is_rejected_with_existing_queue_position(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            held = [
                service.claim_job(slot_id, f"held-{slot_id}")
                for slot_id in SLOT_IDS
            ]
            self.assertTrue(all(result["accepted"] for result in held))
            queued = threading.Event()
            first_result: dict[str, object] = {}
            first_events: list[dict[str, object]] = []
            duplicate_events: list[dict[str, object]] = []
            commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return ReturnCodeChild(0)

            allocator = AutoAllocator(
                service,
                runner=self._runner(service, popen),
                poll_interval=0.01,
            )

            def first_submit():
                def emit(record):
                    first_events.append(record)
                    if record["event"] == "queued":
                        queued.set()

                first_result["result"] = allocator.submit(
                    "queued-duplicate", [TEST_ORACLE_CLI, "-p", "first"], emit=emit
                )

            first = threading.Thread(target=first_submit)
            first.start()
            self.assertTrue(queued.wait(timeout=5))

            duplicate = allocator.submit(
                "queued-duplicate",
                [TEST_ORACLE_CLI, "-p", "duplicate"],
                emit=duplicate_events.append,
            )
            self.assertEqual(duplicate["exit_code"], 2)
            self.assertEqual(len(commands), 0)
            self.assertEqual(len(duplicate_events), 1)
            self.assertEqual(duplicate_events[0]["event"], "rejected")
            self.assertEqual(duplicate_events[0]["outcome"], "rejected")
            self.assertIsNone(duplicate_events[0]["queue_position"])
            self.assertIsNone(duplicate_events[0]["existing_queue_position"])
            self.assertEqual(duplicate_events[0]["existing_request_location"], {"assigned_slot": None})

            self.assertTrue(
                service.finish_job(
                    1,
                    "held-1",
                    held[0]["record"]["started_at"],
                    "success",
                    0,
                    "release",
                    "없음",
                )["released"]
            )
            first.join(timeout=5)
            self.assertFalse(first.is_alive())
            self.assertEqual(first_result["result"]["record"]["outcome"], "success")
            self.assertEqual(len(commands), 1)

    def test_concurrent_submits_claim_distinct_slots(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            allocator = AutoAllocator(service, poll_interval=0.01)
            child_started = [threading.Event() for _ in range(3)]
            child_release = [threading.Event() for _ in range(3)]
            children: list[BlockingChild] = []
            children_lock = threading.Lock()
            results: dict[str, dict[str, object]] = {}
            barrier = threading.Barrier(3)

            def popen(argv, *, env, close_fds):
                with children_lock:
                    index = len(children)
                    child = BlockingChild(child_started[index], child_release[index])
                    children.append(child)
                    return child

            allocator.runner = self._runner(service, popen)

            def invoke(request_id: str) -> None:
                barrier.wait()
                results[request_id] = allocator.submit(
                    request_id, [TEST_ORACLE_CLI, "-p", request_id]
                )

            threads = [
                threading.Thread(target=invoke, args=(f"parallel-{index}",))
                for index in range(3)
            ]
            for thread in threads:
                thread.start()
            deadline = time.monotonic() + 5
            while len(children) < 3 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(len(children), 3)
            for event in child_started:
                self.assertTrue(event.wait(timeout=5))
            for event in child_release:
                event.set()
            for thread in threads:
                thread.join(timeout=5)

            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(
                {result["record"]["assigned_slot"] for result in results.values()}, {1, 2, 3}
            )

    def test_submit_all_unavailable_fails_with_slot_diagnostics_without_queue(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            service = SlotService(settings, cdp=FakeCDP({}), launcher=FakeLauncher())
            events: list[dict[str, object]] = []
            result = AutoAllocator(
                service,
                runner=self._runner(service, lambda argv, *, env, close_fds: ReturnCodeChild(0)),
                poll_interval=0.01,
            ).submit("auto-unavailable", [TEST_ORACLE_CLI, "-p", "task"], emit=events.append)

            self.assertEqual(result["exit_code"], 1)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event"], "failed")
            self.assertEqual(
                [item["slot_id"] for item in events[0]["slot_diagnostics"]],
                list(SLOT_IDS),
            )
            self.assertTrue(all(item["operator_action"] for item in events[0]["slot_diagnostics"]))
            self.assertFalse((settings.state_root / "allocator-queue.json").exists())

    def test_pre_submit_failure_reassigns_once_and_post_submit_failure_does_not_retry(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return ReturnCodeChild(7)

            runner = self._runner(service, popen)
            readiness = [
                {"ready": False, "reason": "slot 1 lost CDP", "operator_action": "repair slot 1"},
                {"ready": True, "reason": "ready", "operator_action": "없음"},
            ]
            events: list[dict[str, object]] = []
            with patch.object(runner, "pre_submit_check", side_effect=readiness):
                result = AutoAllocator(
                    service, runner=runner, poll_interval=0.01
                ).submit("auto-reassign", [TEST_ORACLE_CLI, "-p", "task"], emit=events.append)

            self.assertEqual(result["record"]["outcome"], "failed")
            self.assertEqual(result["record"]["assigned_slot"], 2)
            self.assertEqual(result["record"]["attempted_slots"], [1, 2])
            self.assertEqual(result["record"]["reassignment_reasons"], ["slot 1 lost CDP"])
            self.assertEqual(len(commands), 1)
            self.assertEqual(commands[0][-1], "127.0.0.1:19223")
            self.assertEqual(
                [event["event"] for event in events],
                ["started", "pre_submit_reassigned", "started", "finished"],
            )
            self.assertEqual(
                [event["assigned_slot"] for event in events if event["event"] == "started"],
                [1, 2],
            )
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(2)["status"], AVAILABLE)

    def test_occupied_submits_are_fifo_and_new_submit_cannot_overtake(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            held = [
                service.claim_job(slot_id, f"held-{slot_id}")
                for slot_id in SLOT_IDS
            ]
            self.assertTrue(all(result["accepted"] for result in held))
            events_by_request: dict[str, list[dict[str, object]]] = {"first": [], "second": []}
            results: dict[str, dict[str, object]] = {}
            lock = threading.Lock()
            queued = {request_id: threading.Event() for request_id in events_by_request}

            child_start_order: list[str] = []

            def popen(argv, *, env, close_fds):
                child_start_order.append(argv[argv.index("-p") + 1])
                return ReturnCodeChild(0)

            allocator = AutoAllocator(
                service,
                runner=self._runner(service, popen),
                poll_interval=0.01,
            )

            def invoke(request_id: str) -> None:
                def emit(record):
                    with lock:
                        events_by_request[request_id].append(record)
                    if record["event"] == "queued":
                        queued[request_id].set()

                results[request_id] = allocator.submit(
                    request_id, [TEST_ORACLE_CLI, "-p", request_id], emit=emit
                )

            first = threading.Thread(target=invoke, args=("first",))
            second = threading.Thread(target=invoke, args=("second",))
            first.start()
            self.assertTrue(queued["first"].wait(timeout=5))
            second.start()
            self.assertTrue(queued["second"].wait(timeout=5))

            first_position = next(
                event["queue_position"]
                for event in events_by_request["first"]
                if event["event"] == "queued"
            )
            second_position = next(
                event["queue_position"]
                for event in events_by_request["second"]
                if event["event"] == "queued"
            )
            self.assertEqual((first_position, second_position), (1, 2))

            self.assertTrue(
                service.finish_job(
                    1,
                    "held-1",
                    held[0]["record"]["started_at"],
                    "success",
                    0,
                    "release",
                    "없음",
                )["released"]
            )
            first.join(timeout=5)
            second.join(timeout=5)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(child_start_order, ["first", "second"])
            self.assertEqual(results["first"]["record"]["assigned_slot"], 1)
            self.assertEqual(results["second"]["record"]["assigned_slot"], 1)
            self.assertFalse((settings_for(root).state_root / "allocator-queue.json").exists())

    def test_waiting_cancel_removes_queue_entry_without_assignment(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            held = [
                service.claim_job(slot_id, f"held-{slot_id}")
                for slot_id in SLOT_IDS
            ]
            self.assertTrue(all(result["accepted"] for result in held))
            context = multiprocessing.get_context("fork")
            result_queue = context.Queue()
            waiter = context.Process(target=auto_waiter_process, args=(settings_for(root), result_queue))
            waiter.start()
            queued = result_queue.get(timeout=5)
            self.assertEqual(queued["event"], "queued")
            os.kill(waiter.pid, signal.SIGINT)
            cancelled = result_queue.get(timeout=5)
            waiter.join(timeout=5)

            self.assertFalse(waiter.is_alive())
            self.assertEqual(cancelled["event"], "cancelled")
            self.assertIsNone(cancelled["assigned_slot"])
            self.assertEqual(cancelled["outcome"], "cancelled")
            self.assertFalse((settings_for(root).state_root / "allocator-queue.json").exists())
            self.assertEqual(
                [service.status(slot_id)["status"] for slot_id in SLOT_IDS],
                [OCCUPIED] * len(SLOT_IDS),
            )

    def test_waiting_sighup_removes_queue_entry_and_cancels_without_assignment(self):
        if not hasattr(signal, "SIGHUP"):
            self.skipTest("SIGHUP is not available on this platform")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            held = [
                service.claim_job(slot_id, f"held-{slot_id}")
                for slot_id in SLOT_IDS
            ]
            self.assertTrue(all(result["accepted"] for result in held))
            context = multiprocessing.get_context("fork")
            result_queue = context.Queue()
            waiter = context.Process(
                target=auto_waiter_process, args=(settings_for(root), result_queue)
            )
            waiter.start()
            queued = result_queue.get(timeout=5)
            self.assertEqual(queued["event"], "queued")
            os.kill(waiter.pid, signal.SIGHUP)
            cancelled = result_queue.get(timeout=5)
            payload = result_queue.get(timeout=5)
            waiter.join(timeout=5)

            self.assertFalse(waiter.is_alive())
            self.assertEqual(cancelled["event"], "cancelled")
            self.assertEqual(cancelled["outcome"], "cancelled")
            self.assertIsNone(cancelled["assigned_slot"])
            self.assertIn("SIGHUP", cancelled["reason"])
            self.assertEqual(payload["result"]["record"]["outcome"], "cancelled")
            self.assertFalse((settings_for(root).state_root / "allocator-queue.json").exists())
            self.assertEqual(
                [service.status(slot_id)["status"] for slot_id in SLOT_IDS],
                [OCCUPIED] * len(SLOT_IDS),
            )

    def test_running_cancel_finishes_claim_without_retry(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            child_started = threading.Event()
            commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                commands.append(argv)
                return SignalBlockingChild(child_started)

            runner = self._runner(service, popen)

            def cancel_after_start():
                self.assertTrue(child_started.wait(timeout=5))
                os.kill(os.getpid(), signal.SIGINT)

            canceller = threading.Thread(target=cancel_after_start)
            canceller.start()
            events: list[dict[str, object]] = []
            result = AutoAllocator(
                service, runner=runner, poll_interval=0.01
            ).submit("running-cancel", [TEST_ORACLE_CLI, "-p", "task"], emit=events.append)
            canceller.join(timeout=5)

            self.assertEqual(result["record"]["outcome"], "cancelled")
            self.assertEqual(result["record"]["assigned_slot"], 1)
            self.assertTrue(result["record"]["released"])
            self.assertEqual(len(commands), 1)
            self.assertEqual([event["event"] for event in events], ["started", "finished"])
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            self.assertEqual(service.status(2)["status"], AVAILABLE)

    def test_running_sighup_terminates_child_finishes_claim_and_does_not_retry(self):
        if not hasattr(signal, "SIGHUP"):
            self.skipTest("SIGHUP is not available on this platform")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = self._ready_service(root)
            context = multiprocessing.get_context("fork")
            result_queue = context.Queue()
            runner_process = context.Process(
                target=auto_running_sighup_process,
                args=(settings_for(root), result_queue),
            )
            runner_process.start()
            started = result_queue.get(timeout=5)
            finished = result_queue.get(timeout=5)
            payload = result_queue.get(timeout=5)
            runner_process.join(timeout=5)

            self.assertFalse(runner_process.is_alive())
            self.assertEqual(started["event"], "started")
            self.assertEqual(finished["event"], "finished")
            self.assertEqual(finished["outcome"], "cancelled")
            self.assertIn("SIGHUP", finished["reason"])
            self.assertTrue(finished["released"])
            self.assertEqual(payload["popen_count"], 1)
            self.assertEqual(payload["result"]["record"]["outcome"], "cancelled")
            self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_dead_waiter_is_purged_without_recovery(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            coordinator = QueueCoordinator(root / "state")
            with coordinator.locked() as locked:
                locked.append_unlocked(
                    {
                        "request_id": "dead-request",
                        "owner_pid": 999999999,
                        "owner_starttime": "dead-starttime",
                        "queued_at": "2026-08-01T00:00:00Z",
                    }
                )
                self.assertTrue(locked.queue_path.exists())
            with coordinator.locked() as locked:
                self.assertEqual(locked.load_unlocked(), [])
                self.assertFalse(locked.queue_path.exists())


class AttachmentPolicyTests(unittest.TestCase):
    @staticmethod
    def _policy(root: Path, selector=None) -> FileAttachmentPolicy:
        temporary_root = root / "zip-temp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        return FileAttachmentPolicy(
            selector=selector,
            oracle_home=root / "oracle-home",
            temporary_root=temporary_root,
        )

    @staticmethod
    def _write_session(prepared, *, prompt_submitted: bool, log: str = "") -> Path:
        session_directory = prepared.oracle_home / "sessions" / prepared.session_id
        (session_directory / "artifacts").mkdir(parents=True, exist_ok=True)
        (session_directory / "meta.json").write_text(
            json.dumps(
                {
                    "id": prepared.session_id,
                    "status": "completed",
                    "options": {"file": [str(prepared.zip_path)]},
                    "browser": {"runtime": {"promptSubmitted": prompt_submitted}},
                    "artifacts": [],
                }
            ),
            encoding="utf-8",
        )
        (session_directory / "output.log").write_text(log, encoding="utf-8")
        return session_directory

    def test_stock_selection_preserves_directory_glob_exclusion_and_ignores(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cwd = root / "workspace"
            cwd.mkdir()
            src = cwd / "src"
            src.mkdir()
            (src / "keep.py").write_text("keep", encoding="utf-8")
            (src / "excluded.py").write_text("excluded", encoding="utf-8")
            (src / "gitignored.py").write_text("ignored", encoding="utf-8")
            (src / ".hidden.py").write_text("hidden", encoding="utf-8")
            (cwd / ".gitignore").write_text("src/gitignored.py\n", encoding="utf-8")
            (cwd / "node_modules").mkdir()
            (cwd / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")
            (cwd / "dist").mkdir()
            (cwd / "dist" / "ignored.js").write_text("ignored", encoding="utf-8")

            prepared = self._policy(root).prepare(
                [
                    TEST_ORACLE_CLI,
                    "-p",
                    "task",
                    "--file",
                    ".",
                    "--file",
                    "src/**/*.py",
                    "--file",
                    "!src/excluded.py",
                ],
                "selection-parity",
                cwd=cwd,
            )
            self.assertIsNotNone(prepared)
            self.assertEqual(
                [item.relative_path for item in prepared.selected_files],
                ["src/keep.py"],
            )
            prepared.cleanup()

    def test_one_and_many_files_are_deflated_and_paths_are_preserved(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cwd = root / "workspace"
            nested = cwd / "nested"
            nested.mkdir(parents=True)
            first = cwd / "first.txt"
            second = nested / "second.txt"
            first.write_text("x" * 20_000, encoding="utf-8")
            second.write_text("y" * 20_000, encoding="utf-8")
            prepared = self._policy(
                root,
                selector=lambda _groups, _cwd: [first, second],
            ).prepare(
                [TEST_ORACLE_CLI, "-p", "task", "--file", str(first)],
                "zip-shape",
                cwd=cwd,
            )
            self.assertIsNotNone(prepared)
            with zipfile.ZipFile(prepared.zip_path) as archive:
                self.assertEqual(
                    archive.namelist(), ["first.txt", "nested/second.txt"]
                )
                self.assertTrue(
                    all(info.compress_type == zipfile.ZIP_DEFLATED for info in archive.infolist())
                )
                self.assertEqual(archive.read("nested/second.txt"), b"y" * 20_000)
                self.assertTrue(
                    all(info.compress_size < info.file_size for info in archive.infolist())
                )
            self.assertEqual(prepared.zip_name, "oracle-attachments.zip")
            self.assertEqual(
                prepared.zip_sha256,
                hashlib.sha256(prepared.zip_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                [item.relative_path for item in prepared.selected_files],
                ["first.txt", "nested/second.txt"],
            )
            cleanup = prepared.cleanup()
            self.assertTrue(cleanup["removed"])
            self.assertFalse(prepared.zip_path.exists())

    def test_normalized_member_collision_fails_without_renaming(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cwd = root / "workspace"
            cwd.mkdir()
            inside = cwd / "same.txt"
            outside = root / "same.txt"
            inside.write_text("inside", encoding="utf-8")
            outside.write_text("outside", encoding="utf-8")
            policy = self._policy(root, selector=lambda _groups, _cwd: [outside, inside])
            with self.assertRaisesRegex(AttachmentPreparationError, "충돌"):
                policy.prepare(
                    [TEST_ORACLE_CLI, "--file", str(inside)],
                    "collision",
                    cwd=cwd,
                )

            self.assertEqual(normalize_zip_member_path("../same.txt"), "same.txt")

    def test_no_local_source_or_zip_cap_and_conflicting_options_are_overridden(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cwd = root / "workspace"
            cwd.mkdir()
            source = cwd / "large.bin"
            source.write_bytes(b"z" * (1024 * 1024 + 1))
            prepared = self._policy(root).prepare(
                [
                    TEST_ORACLE_CLI,
                    "--file",
                    str(source),
                    "--max-file-size-bytes",
                    "1",
                    "--browser-attachments",
                    "never",
                    "--browser-inline-files",
                    "--browser-bundle-files",
                    "--browser-bundle-format",
                    "text",
                    "--no-wait",
                    "--slug",
                    "caller-slug",
                ],
                "override-options",
                cwd=cwd,
            )
            self.assertIsNotNone(prepared)
            command = prepared.command
            self.assertEqual(command.count("--file"), 1)
            self.assertEqual(command[command.index("--file") + 1], str(prepared.zip_path))
            self.assertEqual(
                command[command.index("--max-file-size-bytes") + 1],
                str(MAX_SAFE_FILE_SIZE_BYTES),
            )
            self.assertEqual(
                command[command.index("--browser-attachments") + 1], "always"
            )
            self.assertNotIn("--browser-inline-files", command)
            self.assertNotIn("--browser-bundle-files", command)
            self.assertNotIn("--browser-bundle-format", command)
            self.assertNotIn("--no-wait", command)
            self.assertEqual(command[command.index("--wait")], "--wait")
            self.assertEqual(command[command.index("--slug") + 1], "caller-slug")
            prepared.cleanup()

    def test_manifest_is_stored_without_contents_or_zip_retention(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cwd = root / "workspace"
            cwd.mkdir()
            source = cwd / "secret.txt"
            source.write_text("do not put this content in manifest", encoding="utf-8")
            prepared = self._policy(
                root,
                selector=lambda _groups, _cwd: [source],
            ).prepare(
                [TEST_ORACLE_CLI, "--file", str(source)],
                "manifest-request",
                cwd=cwd,
            )
            session_directory = self._write_session(
                prepared,
                prompt_submitted=True,
                log="All attachments uploaded\n",
            )
            result = prepared.write_manifest(
                child_started=True,
                outcome="success",
                exit_code=0,
            )
            self.assertTrue(result["written"])
            manifest_path = session_directory / MANIFEST_RELATIVE_PATH
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["selected_files"], [{"relative_path": "secret.txt", "size_bytes": source.stat().st_size}])
            self.assertEqual(manifest["zip"]["name"], "oracle-attachments.zip")
            self.assertEqual(manifest["attachment_registration"]["status"], "succeeded")
            self.assertEqual(manifest["prompt_submission"]["status"], "succeeded")
            serialized = manifest_path.read_text(encoding="utf-8")
            self.assertNotIn(source.read_text(encoding="utf-8"), serialized)
            self.assertNotIn(str(prepared.zip_path), serialized)
            metadata = json.loads((session_directory / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(
                metadata["oracle_browser_slots"]["attachment_manifest"],
                MANIFEST_RELATIVE_PATH,
            )
            self.assertNotIn(str(prepared.zip_path), json.dumps(metadata))
            self.assertTrue(prepared.cleanup()["removed"])
            self.assertFalse(prepared.zip_path.exists())

    def test_runner_fails_before_claim_on_selection_error_and_cleans_zip_on_child_failure(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            service = SlotService(
                settings,
                cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            policy = self._policy(root, selector=lambda _groups, _cwd: [source])
            popen_calls: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                popen_calls.append(argv)
                self.assertTrue(Path(argv[argv.index("--file") + 1]).exists())
                return ReturnCodeChild(7)

            runner = JobRunner(
                service,
                popen_factory=popen,
                oracle_cli_path=TEST_ORACLE_CLI,
                attachment_policy=policy,
            )
            events: list[dict[str, object]] = []
            result = runner.run(
                1,
                "upload-failure",
                [TEST_ORACLE_CLI, "--file", str(source)],
                emit=events.append,
            )
            self.assertEqual(result["exit_code"], 7)
            self.assertEqual(result["record"]["outcome"], "failed")
            self.assertEqual(len(popen_calls), 1)
            self.assertEqual(
                [event["event"] for event in events],
                ["attachment_prepared", "started", "finished"],
            )
            prepared_event = events[0]
            self.assertEqual(prepared_event["selected_file_count"], 1)
            self.assertEqual(prepared_event["selected_file_bytes"], source.stat().st_size)
            self.assertEqual(prepared_event["generated_zip"]["name"], "oracle-attachments.zip")
            self.assertNotIn("selected_files", prepared_event)
            self.assertNotIn(str(root), json.dumps(prepared_event))
            self.assertEqual(service.status(1)["status"], AVAILABLE)
            generated_zip = Path(popen_calls[0][popen_calls[0].index("--file") + 1])
            self.assertFalse(generated_zip.exists())

            failing_policy = self._policy(
                root,
                selector=lambda _groups, _cwd: (_ for _ in ()).throw(
                    AttachmentPreparationError("selection failed", "fix selection")
                ),
            )
            with patch.object(service, "claim_job", wraps=service.claim_job) as claim:
                rejected = JobRunner(
                    service,
                    popen_factory=popen,
                    oracle_cli_path=TEST_ORACLE_CLI,
                    attachment_policy=failing_policy,
                ).run(1, "selection-failure", [TEST_ORACLE_CLI, "--file", str(source)])
            self.assertFalse(rejected["accepted"])
            self.assertIn("selection failed", rejected["record"]["reason"])
            claim.assert_not_called()

    def test_attachment_event_failure_cleans_zip_without_claim(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            service = SlotService(
                settings,
                cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            policy = self._policy(root, selector=lambda _groups, _cwd: [source])
            runner = JobRunner(
                service,
                popen_factory=lambda _argv, **_kwargs: self.fail("child must not start"),
                oracle_cli_path=TEST_ORACLE_CLI,
                attachment_policy=policy,
            )

            def failing_emit(record):
                if record["event"] == "attachment_prepared":
                    raise RuntimeError("event sink failed")

            with patch.object(service, "claim_job", wraps=service.claim_job) as claim:
                with self.assertRaisesRegex(RuntimeError, "event sink failed"):
                    runner.run(
                        1,
                        "event-failure",
                        [TEST_ORACLE_CLI, "--file", str(source)],
                        emit=failing_emit,
                    )

            claim.assert_not_called()
            self.assertEqual(list((root / "zip-temp").iterdir()), [])

    def test_successful_child_with_missing_or_failed_manifest_fails_and_releases_slot(self):
        for manifest_result in (
            None,
            {"written": False, "error": "manifest write failed"},
        ):
            with self.subTest(manifest_result=manifest_result), TemporaryDirectory() as directory:
                root = Path(directory)
                settings = settings_for(root)
                service = SlotService(
                    settings,
                    cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                    launcher=FakeLauncher(),
                )
                self.assertEqual(service.prepare(1)["status"], AVAILABLE)
                source = root / "source.txt"
                source.write_text("source", encoding="utf-8")
                policy = self._policy(root, selector=lambda _groups, _cwd: [source])
                child_calls: list[list[str]] = []

                def popen(argv, *, env, close_fds):
                    child_calls.append(argv)
                    return ReturnCodeChild(0)

                with patch(
                    "oracle_browser_slots.attachments.PreparedAttachment.write_manifest",
                    return_value=manifest_result,
                ):
                    result = JobRunner(
                        service,
                        popen_factory=popen,
                        oracle_cli_path=TEST_ORACLE_CLI,
                        attachment_policy=policy,
                    ).run(1, "post-child-manifest-failure", [TEST_ORACLE_CLI, "--file", str(source)])

                self.assertEqual(result["exit_code"], 1)
                self.assertEqual(result["record"]["outcome"], "failed")
                self.assertIn("post-child attachment", result["record"]["reason"])
                self.assertIn("manifest", result["record"]["reason"])
                self.assertTrue(result["record"]["prompt_submission_may_have_occurred"])
                self.assertEqual(result["record"]["child_exit_code"], 0)
                self.assertEqual(len(child_calls), 1)
                self.assertFalse(Path(child_calls[0][child_calls[0].index("--file") + 1]).exists())
                self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_sessionless_dry_run_does_not_require_manifest(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            service = SlotService(
                settings,
                cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            policy = self._policy(root, selector=lambda _groups, _cwd: [source])
            child_calls: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                child_calls.append(argv)
                return ReturnCodeChild(0)

            with patch(
                "oracle_browser_slots.attachments.PreparedAttachment.write_manifest",
                return_value=None,
            ):
                result = JobRunner(
                    service,
                    popen_factory=popen,
                    oracle_cli_path=TEST_ORACLE_CLI,
                    attachment_policy=policy,
                ).run(
                    1,
                    "sessionless-dry-run",
                    [
                        TEST_ORACLE_CLI,
                        "--dry-run",
                        "json",
                        "-p",
                        "preview",
                        "--file",
                        str(source),
                    ],
                )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["record"]["outcome"], "success")
            self.assertEqual(len(child_calls), 1)
            self.assertFalse(Path(child_calls[0][child_calls[0].index("--file") + 1]).exists())
            self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_successful_child_with_cleanup_failure_fails_without_retry_and_releases_slot(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            service = SlotService(
                settings,
                cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            policy = self._policy(root, selector=lambda _groups, _cwd: [source])
            child_calls: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                child_calls.append(argv)
                return ReturnCodeChild(0)

            with patch(
                "oracle_browser_slots.attachments.PreparedAttachment.write_manifest",
                return_value={"written": True, "path": "/tmp/manifest.json"},
            ), patch(
                "oracle_browser_slots.attachments.PreparedAttachment.cleanup",
                return_value={"removed": False, "error": "permission denied"},
            ):
                result = JobRunner(
                    service,
                    popen_factory=popen,
                    oracle_cli_path=TEST_ORACLE_CLI,
                    attachment_policy=policy,
                ).run(1, "post-child-cleanup-failure", [TEST_ORACLE_CLI, "--file", str(source)])

            self.assertEqual(result["exit_code"], 1)
            self.assertEqual(result["record"]["outcome"], "failed")
            self.assertIn("cleanup", result["record"]["reason"])
            self.assertIn("재시도하지 않았습니다", result["record"]["reason"])
            self.assertTrue(result["record"]["prompt_submission_may_have_occurred"])
            self.assertEqual(len(child_calls), 1)
            self.assertTrue(Path(child_calls[0][child_calls[0].index("--file") + 1]).exists())
            self.assertEqual(service.status(1)["status"], AVAILABLE)

    def test_zip_creation_failure_and_interruption_do_not_reach_or_retain_child(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            service = SlotService(
                settings,
                cdp=FakeCDP({1: LoginResult(True, "ready", "없음")}),
                launcher=FakeLauncher(),
            )
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            failing_policy = self._policy(
                root,
                selector=lambda _groups, _cwd: [source],
            )
            with patch(
                "oracle_browser_slots.attachments._create_compressed_zip",
                side_effect=OSError("zip write failed"),
            ), patch.object(service, "claim_job", wraps=service.claim_job) as claim:
                result = JobRunner(
                    service,
                    popen_factory=lambda _argv, **_kwargs: self.fail("child must not start"),
                    oracle_cli_path=TEST_ORACLE_CLI,
                    attachment_policy=failing_policy,
                ).run(1, "zip-create-failure", [TEST_ORACLE_CLI, "--file", str(source)])
            self.assertFalse(result["accepted"])
            self.assertIn("ZIP", result["record"]["reason"])
            claim.assert_not_called()

            policy = self._policy(root, selector=lambda _groups, _cwd: [source])
            child_calls: list[list[str]] = []

            def interrupting_popen(argv, *, env, close_fds):
                child_calls.append(argv)
                return InterruptingChild()

            result = JobRunner(
                service,
                popen_factory=interrupting_popen,
                oracle_cli_path=TEST_ORACLE_CLI,
                attachment_policy=policy,
            ).run(1, "zip-interrupted", [TEST_ORACLE_CLI, "--file", str(source)])
            self.assertEqual(result["exit_code"], 143)
            self.assertEqual(result["record"]["outcome"], "interrupted")
            self.assertEqual(len(child_calls), 1)
            self.assertFalse(Path(child_calls[0][child_calls[0].index("--file") + 1]).exists())

    def test_submit_uses_one_zip_and_correlates_manifest_under_concurrency(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = settings_for(root)
            cdp = FakeCDP(
                {
                    1: LoginResult(True, "ready", "없음"),
                    2: LoginResult(True, "ready", "없음"),
                }
            )
            service = SlotService(settings, cdp=cdp, launcher=FakeLauncher())
            self.assertEqual(service.prepare(1)["status"], AVAILABLE)
            self.assertEqual(service.prepare(2)["status"], AVAILABLE)
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            policy = self._policy(root, selector=lambda _groups, _cwd: [source])
            child_commands: list[list[str]] = []

            def popen(argv, *, env, close_fds):
                child_commands.append(argv)
                zip_argument = Path(argv[argv.index("--file") + 1])
                session_id = "fake-submit-session"
                session_directory = policy.oracle_home / "sessions" / session_id
                session_directory.mkdir(parents=True)
                (session_directory / "meta.json").write_text(
                    json.dumps(
                        {
                            "id": session_id,
                            "status": "completed",
                            "options": {"file": [str(zip_argument)]},
                            "browser": {"runtime": {"promptSubmitted": True}},
                            "artifacts": [],
                        }
                    ),
                    encoding="utf-8",
                )
                (session_directory / "output.log").write_text(
                    "All attachments uploaded\n", encoding="utf-8"
                )
                return ReturnCodeChild(0)

            events: list[dict[str, object]] = []
            result = AutoAllocator(
                service,
                runner=JobRunner(
                    service,
                    popen_factory=popen,
                    oracle_cli_path=TEST_ORACLE_CLI,
                    attachment_policy=policy,
                ),
                poll_interval=0.01,
            ).submit(
                "submit-zip",
                [TEST_ORACLE_CLI, "--file", str(source)],
                emit=events.append,
            )
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(len(child_commands), 1)
            prepared_events = [
                event for event in events if event["event"] == "attachment_prepared"
            ]
            self.assertEqual(len(prepared_events), 1)
            self.assertEqual(events[0]["event"], "attachment_prepared")
            self.assertEqual(prepared_events[0]["selected_file_count"], 1)
            command = child_commands[0]
            self.assertEqual(command.count("--file"), 1)
            self.assertEqual(command[command.index("--browser-attachments") + 1], "always")
            manifest_path = policy.oracle_home / "sessions" / "fake-submit-session" / MANIFEST_RELATIVE_PATH
            self.assertTrue(manifest_path.exists())
            self.assertFalse(Path(command[command.index("--file") + 1]).exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                prepared_events[0]["generated_zip"]["sha256"],
                manifest["zip"]["sha256"],
            )
            self.assertEqual(manifest["prompt_submission"]["submitted"], True)

            second_policy = self._policy(root, selector=lambda _groups, _cwd: [source])
            first = second_policy.prepare([TEST_ORACLE_CLI, "--file", str(source)], "same-request", cwd=root)
            second = second_policy.prepare([TEST_ORACLE_CLI, "--file", str(source)], "same-request", cwd=root)
            self.assertNotEqual(first.session_id, second.session_id)
            first.cleanup()
            second.cleanup()


if __name__ == "__main__":
    unittest.main()
