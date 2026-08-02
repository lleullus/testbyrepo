"""Small standard-library CDP client used by the slot runtime."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import json
import math
import os
import re
import socket
import ssl
import struct
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .model import Slot


class CDPError(Exception):
    """The loopback browser did not provide a usable CDP response."""


@dataclass(frozen=True)
class LoginResult:
    valid: bool
    reason: str
    operator_action: str


@dataclass(frozen=True)
class ConversationRestoreResult:
    conversation_id: str
    conversation_url: str


_CONVERSATION_PATH = re.compile(r"^/c/([A-Za-z0-9-]+)$")


def _is_chatgpt_url(url: str) -> bool:
    try:
        host = (urlsplit(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    return host == "chatgpt.com" or host.endswith(".chatgpt.com") or host in {
        "chat.openai.com",
    } or host.endswith(".chat.openai.com")


class CDPClient:
    def __init__(self, request_timeout: float = 2.0) -> None:
        self.request_timeout = request_timeout

    def browser_version(self, slot: Slot) -> dict[str, Any]:
        value = self._get_json(slot, "/json/version")
        if not isinstance(value, dict):
            raise CDPError(f"슬롯 {slot.slot_id}의 CDP 응답 형식이 올바르지 않습니다.")
        if not isinstance(value.get("Browser"), str) or not value.get("Browser"):
            raise CDPError(
                f"슬롯 {slot.slot_id}의 CDP 응답에 Chrome Browser 정보가 없습니다."
            )
        if not isinstance(value.get("webSocketDebuggerUrl"), str):
            raise CDPError(
                f"슬롯 {slot.slot_id}의 CDP 응답에 디버거 연결 정보가 없습니다."
            )
        return value

    def is_ready(self, slot: Slot) -> bool:
        try:
            self.browser_version(slot)
        except CDPError:
            return False
        return True

    def check_login(self, slot: Slot) -> LoginResult:
        self.browser_version(slot)
        targets = self._get_json(slot, "/json/list")
        if not isinstance(targets, list):
            raise CDPError(f"슬롯 {slot.slot_id}의 CDP 대상 목록 형식이 올바르지 않습니다.")

        target = next(
            (
                candidate
                for candidate in targets
                if isinstance(candidate, dict)
                and candidate.get("type") == "page"
                and _is_chatgpt_url(str(candidate.get("url", "")))
            ),
            None,
        )
        if target is None:
            return LoginResult(
                valid=False,
                reason="ChatGPT 페이지가 해당 슬롯에서 열려 있지 않거나 아직 로드되지 않았습니다.",
                operator_action=(
                    f"슬롯 {slot.slot_id} 프로필에서 ChatGPT를 열고 로그인한 뒤 "
                    "status를 다시 실행하십시오."
                ),
            )

        websocket_url = target.get("webSocketDebuggerUrl")
        if not isinstance(websocket_url, str) or not websocket_url:
            raise CDPError(
                f"슬롯 {slot.slot_id}의 ChatGPT 페이지에 CDP 연결 정보가 없습니다."
            )

        try:
            with _WebSocket(websocket_url, self.request_timeout) as websocket:
                response = websocket.request(
                    "Runtime.evaluate",
                    {
                        "expression": _LOGIN_CHECK_SCRIPT,
                        "awaitPromise": True,
                        "returnByValue": True,
                    },
                )
        except (OSError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
            raise CDPError(
                f"슬롯 {slot.slot_id}의 ChatGPT 로그인 상태를 확인할 수 없습니다."
            ) from exc

        if not isinstance(response, dict):
            raise CDPError(
                f"슬롯 {slot.slot_id}의 ChatGPT 로그인 상태 응답 형식이 올바르지 않습니다."
            )
        result = response.get("result")
        if not isinstance(result, dict) or "exceptionDetails" in result:
            raise CDPError(
                f"슬롯 {slot.slot_id}의 ChatGPT 로그인 상태 확인 중 페이지 오류가 발생했습니다."
            )
        remote_result = result.get("result")
        value = remote_result.get("value") if isinstance(remote_result, dict) else None
        if not isinstance(value, dict):
            raise CDPError(
                f"슬롯 {slot.slot_id}의 ChatGPT 로그인 상태 응답 형식이 올바르지 않습니다."
            )

        if value.get("logged_in") is True:
            return LoginResult(
                valid=True,
                reason="CDP 응답과 ChatGPT 작업 시작에 필요한 로그인 상태를 확인했습니다.",
                operator_action="없음",
            )

        if value.get("page_ready") is False:
            return LoginResult(
                valid=False,
                reason="ChatGPT 페이지가 아직 준비되지 않았습니다.",
                operator_action="잠시 후 status를 다시 실행하십시오.",
            )
        return LoginResult(
            valid=False,
            reason="ChatGPT 로그인이 필요하거나 작업 시작에 필요한 로그인 상태가 아닙니다.",
            operator_action=(
                f"슬롯 {slot.slot_id} 프로필에서 ChatGPT에 로그인한 뒤 status를 다시 "
                "실행하십시오. 이 도구는 계정 신원을 확인하지 않습니다."
            ),
        )

    def restore_archived_conversation(
        self, slot: Slot, conversation_url: str
    ) -> ConversationRestoreResult:
        """Unarchive one saved conversation and confirm its composer is usable."""

        conversation_id, expected_url = _canonical_conversation_url(conversation_url)
        target = self._chatgpt_target(slot)
        if target is None:
            raise CDPError(
                f"슬롯 {slot.slot_id}에서 보관된 대화를 복원할 ChatGPT 페이지를 찾을 수 없습니다."
            )
        target_id = target.get("id")
        websocket_url = target.get("webSocketDebuggerUrl")
        if not isinstance(target_id, str) or not target_id:
            raise CDPError(f"슬롯 {slot.slot_id}의 ChatGPT 대상 ID가 없습니다.")
        if not isinstance(websocket_url, str) or not websocket_url:
            raise CDPError(
                f"슬롯 {slot.slot_id}의 ChatGPT 페이지에 CDP 연결 정보가 없습니다."
            )

        try:
            with _WebSocket(websocket_url, self.request_timeout) as websocket:
                restored = self._runtime_value(
                    websocket,
                    _restore_conversation_expression(conversation_id),
                    await_promise=True,
                )
                if (
                    not isinstance(restored, dict)
                    or restored.get("restored") is not True
                    or restored.get("is_archived") is not False
                ):
                    auth_status = restored.get("auth_status") if isinstance(restored, dict) else None
                    patch_status = restored.get("patch_status") if isinstance(restored, dict) else None
                    readback_status = (
                        restored.get("readback_status") if isinstance(restored, dict) else None
                    )
                    is_archived = restored.get("is_archived") if isinstance(restored, dict) else None
                    auth_status = (
                        auth_status
                        if isinstance(auth_status, int)
                        and not isinstance(auth_status, bool)
                        and 0 <= auth_status <= 999
                        else None
                    )
                    patch_status = (
                        patch_status
                        if isinstance(patch_status, int)
                        and not isinstance(patch_status, bool)
                        and 0 <= patch_status <= 999
                        else None
                    )
                    readback_status = (
                        readback_status
                        if isinstance(readback_status, int)
                        and not isinstance(readback_status, bool)
                        and 0 <= readback_status <= 999
                        else None
                    )
                    is_archived = is_archived if isinstance(is_archived, bool) else None
                    statuses = []
                    if auth_status is not None:
                        statuses.append(f"auth HTTP {auth_status}")
                    if patch_status is not None:
                        statuses.append(f"patch HTTP {patch_status}")
                    if readback_status is not None:
                        statuses.append(f"readback HTTP {readback_status}")
                    archive_status = (
                        "is_archived false"
                        if is_archived is False
                        else "is_archived true"
                        if is_archived is True
                        else "is_archived unavailable"
                    )
                    raise CDPError(
                        "ChatGPT 보관 대화 backend unarchive readback이 확인되지 않았습니다 "
                        f"({', '.join(statuses) or 'status unavailable'}, {archive_status})."
                    )
                navigation = websocket.request("Page.navigate", {"url": expected_url})
                if not isinstance(navigation, dict) or navigation.get("error"):
                    raise CDPError("복원된 ChatGPT 대화로 이동하지 못했습니다.")
                result = navigation.get("result")
                if isinstance(result, dict) and result.get("errorText"):
                    raise CDPError(
                        f"복원된 ChatGPT 대화로 이동하지 못했습니다: {result['errorText']}"
                    )
        except CDPError:
            raise
        except (OSError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
            raise CDPError(
                f"슬롯 {slot.slot_id}의 ChatGPT 보관 대화 복원 CDP 요청에 실패했습니다."
            ) from exc

        deadline = time.monotonic() + max(10.0, self.request_timeout * 10)
        last_observation = "복원된 대화의 composer readback이 없습니다."
        ui_fallback_checked = False
        ui_fallback_activated = False
        while True:
            fatal_observation: str | None = None
            try:
                current = self._page_target(slot, target_id=target_id)
                if current is None:
                    last_observation = "복원 중인 ChatGPT 페이지를 찾을 수 없습니다."
                else:
                    current_websocket = current.get("webSocketDebuggerUrl")
                    if not isinstance(current_websocket, str) or not current_websocket:
                        last_observation = "복원 중인 ChatGPT 페이지에 CDP 연결 정보가 없습니다."
                    else:
                        with _WebSocket(current_websocket, self.request_timeout) as websocket:
                            readback = self._runtime_value(
                                websocket,
                                _composer_readback_expression(expected_url),
                                await_promise=False,
                            )
                        if isinstance(readback, dict):
                            same_conversation = readback.get("same_conversation") is True
                            composer_ready = readback.get("composer_ready") is True
                            if ui_fallback_activated and not same_conversation:
                                fatal_observation = (
                                    "보관 대화 UI fallback 활성화 후 대화 URL이 변경되었습니다."
                                )
                            elif same_conversation and composer_ready:
                                return ConversationRestoreResult(
                                    conversation_id=conversation_id,
                                    conversation_url=expected_url,
                                )
                            elif (
                                same_conversation
                                and readback.get("page_ready") is True
                                and not ui_fallback_checked
                            ):
                                ui_fallback_checked = True
                                native_activation_error: str | None = None
                                native_activation_dispatched = False
                                with _WebSocket(
                                    current_websocket, self.request_timeout
                                ) as websocket:
                                    fallback = self._runtime_value(
                                        websocket,
                                        _archived_ui_fallback_expression(expected_url),
                                        await_promise=False,
                                    )
                                    if (
                                        isinstance(fallback, dict)
                                        and fallback.get("same_conversation") is True
                                        and fallback.get("state")
                                        == "native_activation_ready"
                                    ):
                                        try:
                                            center_x, center_y = self._native_click_coordinates(
                                                fallback
                                            )
                                            self._dispatch_native_click(
                                                websocket, center_x, center_y
                                            )
                                        except CDPError as exc:
                                            native_activation_error = str(exc)
                                        except (
                                            OSError,
                                            ValueError,
                                            TimeoutError,
                                            json.JSONDecodeError,
                                        ):
                                            native_activation_error = (
                                                "보관 대화 UI fallback native CDP 활성화에 실패했습니다."
                                            )
                                        else:
                                            native_activation_dispatched = True
                                if not isinstance(fallback, dict):
                                    last_observation = (
                                        "보관 대화 UI fallback readback이 올바르지 않습니다."
                                    )
                                elif fallback.get("same_conversation") is not True:
                                    fatal_observation = (
                                        "보관 대화 UI fallback 중 대화 URL이 변경되었습니다."
                                    )
                                elif fallback.get("state") == "activation_failed":
                                    fatal_observation = (
                                        "보관 대화 UI fallback control 활성화에 실패했습니다."
                                    )
                                elif (
                                    fallback.get("state") == "native_activation_ready"
                                    and native_activation_error is not None
                                ):
                                    fatal_observation = native_activation_error
                                elif fallback.get("state") == "native_activation_ready":
                                    if not native_activation_dispatched:
                                        fatal_observation = (
                                            "보관 대화 UI fallback native CDP 활성화를 확인하지 못했습니다."
                                        )
                                    else:
                                        ui_fallback_activated = True
                                        last_observation = (
                                            "보관 대화 UI fallback native CDP 활성화 뒤 composer를 기다리는 중입니다."
                                        )
                                elif fallback.get("state") == "no_exact_control":
                                    last_observation = (
                                        "보관 대화 UI fallback에서 exact archive control을 찾지 못했습니다."
                                    )
                                else:
                                    last_observation = (
                                        "보관 대화 UI fallback 상태를 확인하지 못했습니다."
                                    )
                            else:
                                last_observation = (
                                    "복원된 대화 URL 또는 composer가 아직 준비되지 않았습니다."
                                )
                        else:
                            last_observation = "복원된 대화 URL 또는 composer가 아직 준비되지 않았습니다."
            except (OSError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
                last_observation = f"composer readback CDP 오류: {exc}"
            except CDPError as exc:
                last_observation = str(exc)

            if fatal_observation is not None:
                raise CDPError(
                    f"슬롯 {slot.slot_id}에서 보관 대화 UI fallback을 안전하게 완료하지 못했습니다: "
                    f"{fatal_observation}"
                )
            if time.monotonic() >= deadline:
                raise CDPError(
                    f"슬롯 {slot.slot_id}에서 보관 대화 복원 후 안정적인 URL과 composer를 확인하지 못했습니다: "
                    f"{last_observation}"
                )
            time.sleep(0.2)

    def _chatgpt_target(self, slot: Slot) -> dict[str, Any] | None:
        targets = self._get_json(slot, "/json/list")
        if not isinstance(targets, list):
            raise CDPError(f"슬롯 {slot.slot_id}의 CDP 대상 목록 형식이 올바르지 않습니다.")
        for candidate in targets:
            if (
                isinstance(candidate, dict)
                and candidate.get("type") == "page"
                and _is_chatgpt_url(str(candidate.get("url", "")))
            ):
                return candidate
        return None

    def _page_target(self, slot: Slot, *, target_id: str) -> dict[str, Any] | None:
        targets = self._get_json(slot, "/json/list")
        if not isinstance(targets, list):
            raise CDPError(f"슬롯 {slot.slot_id}의 CDP 대상 목록 형식이 올바르지 않습니다.")
        for candidate in targets:
            if (
                isinstance(candidate, dict)
                and candidate.get("type") == "page"
                and candidate.get("id") == target_id
            ):
                return candidate
        return None

    @staticmethod
    def _runtime_value(
        websocket: "_WebSocket", expression: str, *, await_promise: bool
    ) -> Any:
        response = websocket.request(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": await_promise,
                "returnByValue": True,
            },
        )
        if not isinstance(response, dict):
            raise CDPError("ChatGPT CDP Runtime.evaluate 응답 형식이 올바르지 않습니다.")
        result = response.get("result")
        if not isinstance(result, dict) or "exceptionDetails" in result:
            raise CDPError("ChatGPT CDP Runtime.evaluate 중 페이지 오류가 발생했습니다.")
        remote_result = result.get("result")
        if not isinstance(remote_result, dict) or "value" not in remote_result:
            raise CDPError("ChatGPT CDP Runtime.evaluate readback이 없습니다.")
        return remote_result["value"]

    @staticmethod
    def _native_click_coordinates(fallback: dict[str, Any]) -> tuple[float, float]:
        if (
            fallback.get("same_conversation") is not True
            or fallback.get("archived") is not True
            or fallback.get("action") not in {"unarchive", "restore"}
        ):
            raise CDPError("보관 대화 UI fallback native 활성화 조건이 올바르지 않습니다.")
        geometry = fallback.get("geometry")
        if not isinstance(geometry, dict):
            raise CDPError("보관 대화 UI fallback geometry 형식이 올바르지 않습니다.")

        numbers: dict[str, float] = {}
        for name in (
            "center_x",
            "center_y",
            "width",
            "height",
            "viewport_width",
            "viewport_height",
        ):
            value = geometry.get(name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise CDPError("보관 대화 UI fallback geometry가 finite numeric 값이 아닙니다.")
            try:
                number = float(value)
            except OverflowError as exc:
                raise CDPError(
                    "보관 대화 UI fallback geometry가 finite numeric 값이 아닙니다."
                ) from exc
            if not math.isfinite(number):
                raise CDPError("보관 대화 UI fallback geometry가 finite numeric 값이 아닙니다.")
            numbers[name] = number

        if numbers["width"] <= 0 or numbers["height"] <= 0:
            raise CDPError("보관 대화 UI fallback control geometry가 양수가 아닙니다.")
        if numbers["viewport_width"] <= 0 or numbers["viewport_height"] <= 0:
            raise CDPError("보관 대화 UI fallback viewport geometry가 올바르지 않습니다.")
        if not (
            0 <= numbers["center_x"] < numbers["viewport_width"]
            and 0 <= numbers["center_y"] < numbers["viewport_height"]
        ):
            raise CDPError("보관 대화 UI fallback control 좌표가 viewport 범위를 벗어났습니다.")
        return numbers["center_x"], numbers["center_y"]

    @staticmethod
    def _dispatch_native_click(
        websocket: "_WebSocket", center_x: float, center_y: float
    ) -> None:
        events = (
            {"type": "mouseMoved", "x": center_x, "y": center_y},
            {
                "type": "mousePressed",
                "x": center_x,
                "y": center_y,
                "button": "left",
                "clickCount": 1,
            },
            {
                "type": "mouseReleased",
                "x": center_x,
                "y": center_y,
                "button": "left",
                "clickCount": 1,
            },
        )
        for event in events:
            response = websocket.request("Input.dispatchMouseEvent", event)
            if (
                not isinstance(response, dict)
                or response.get("error")
                or not isinstance(response.get("result"), dict)
            ):
                raise CDPError("보관 대화 UI fallback native CDP 활성화 응답이 올바르지 않습니다.")

    def _get_json(self, slot: Slot, path: str) -> Any:
        url = f"http://127.0.0.1:{slot.port}{path}"
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.request_timeout) as response:
                return json.load(response)
        except HTTPError as exc:
            raise CDPError(
                f"슬롯 {slot.slot_id}의 CDP endpoint가 HTTP {exc.code}을 반환했습니다."
            ) from exc
        except (
            URLError,
            TimeoutError,
            socket.timeout,
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:
            raise CDPError(f"슬롯 {slot.slot_id}의 CDP endpoint가 응답하지 않습니다.") from exc


_LOGIN_CHECK_SCRIPT = r"""
(async () => {
  const host = location.hostname.toLowerCase();
  const isChatGPT = host === "chatgpt.com" || host.endsWith(".chatgpt.com") ||
    host === "chat.openai.com" || host.endsWith(".chat.openai.com");
  if (!isChatGPT) {
    return { chatgpt: false, logged_in: false, page_ready: false };
  }

  const bodyText = (document.body?.innerText || "").toLowerCase();
  const loginPrompt = /\b(log in|login|sign up|create account|continue with google|continue with microsoft|continue with apple)\b/i.test(bodyText);
  const composer = Boolean(document.querySelector("textarea, [contenteditable='true']"));
  let sessionAuthenticated = false;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 1500);
    const response = await fetch("/api/auth/session", {
      credentials: "include",
      signal: controller.signal
    });
    clearTimeout(timer);
    if (response.ok) {
      const session = await response.json();
      sessionAuthenticated = Boolean(session && session.user);
    }
  } catch (_) {
    // The DOM check below remains useful when the session endpoint changes.
  }

  return {
    chatgpt: true,
    page_ready: document.readyState !== "loading",
    logged_in: sessionAuthenticated || (composer && !loginPrompt)
  };
})()
"""


def _canonical_conversation_url(value: str) -> tuple[str, str]:
    if not isinstance(value, str) or not value.strip():
        raise CDPError("복원할 ChatGPT conversation URL이 없습니다.")
    try:
        parsed = urlsplit(value.strip())
    except ValueError as exc:
        raise CDPError("복원할 ChatGPT conversation URL 형식이 올바르지 않습니다.") from exc
    host = (parsed.hostname or "").lower()
    match = _CONVERSATION_PATH.fullmatch(parsed.path)
    if (
        parsed.scheme != "https"
        or parsed.port is not None
        or host not in {"chatgpt.com", "chat.openai.com"}
        or match is None
    ):
        raise CDPError("복원할 ChatGPT conversation URL이 안정적인 /c/<id> URL이 아닙니다.")
    conversation_id = match.group(1)
    return conversation_id, urlunsplit(("https", host, parsed.path, "", ""))


def _restore_conversation_expression(conversation_id: str) -> str:
    return _RESTORE_CONVERSATION_SCRIPT.replace(
        "__CONVERSATION_ID__", json.dumps(conversation_id)
    )


def _composer_readback_expression(expected_url: str) -> str:
    return _COMPOSER_READBACK_SCRIPT.replace("__EXPECTED_URL__", json.dumps(expected_url))


def _archived_ui_fallback_expression(expected_url: str) -> str:
    return _ARCHIVED_UI_FALLBACK_SCRIPT.replace(
        "__EXPECTED_URL__", json.dumps(expected_url)
    )


_RESTORE_CONVERSATION_SCRIPT = r"""
(async () => {
  const conversationId = __CONVERSATION_ID__;
  const failure = (authStatus = null, patchStatus = null, readbackStatus = null, isArchived = null) => ({
    restored: false,
    auth_status: Number.isInteger(authStatus) ? authStatus : null,
    patch_status: Number.isInteger(patchStatus) ? patchStatus : null,
    readback_status: Number.isInteger(readbackStatus) ? readbackStatus : null,
    is_archived: typeof isArchived === "boolean" ? isArchived : null,
  });
  try {
    const sessionResponse = await fetch("/api/auth/session", {
      credentials: "include",
    });
    if (!sessionResponse.ok) return failure(sessionResponse.status);
    let session;
    try {
      session = await sessionResponse.json();
    } catch (_) {
      return failure(sessionResponse.status);
    }
    const accessToken = typeof session?.accessToken === "string" ? session.accessToken.trim() : "";
    if (!accessToken) return failure(sessionResponse.status);
    const conversationPath = `/backend-api/conversation/${encodeURIComponent(conversationId)}`;
    const patchResponse = await fetch(conversationPath, {
      method: "PATCH",
      credentials: "include",
      headers: {
        "content-type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ is_archived: false }),
    });
    if (!patchResponse.ok) return failure(sessionResponse.status, patchResponse.status);
    let readbackResponse;
    try {
      readbackResponse = await fetch(conversationPath, {
        method: "GET",
        credentials: "include",
        headers: {
          "Authorization": `Bearer ${accessToken}`,
        },
      });
    } catch (_) {
      return failure(sessionResponse.status, patchResponse.status);
    }
    let isArchived = null;
    if (readbackResponse.ok) {
      try {
        const conversation = await readbackResponse.json();
        isArchived = typeof conversation?.is_archived === "boolean" ? conversation.is_archived : null;
      } catch (_) {
        isArchived = null;
      }
    }
    return {
      restored: readbackResponse.ok === true && isArchived === false,
      auth_status: sessionResponse.status,
      patch_status: patchResponse.status,
      readback_status: readbackResponse.status,
      is_archived: isArchived,
    };
  } catch (_) {
    return failure();
  }
})()
"""


_COMPOSER_READBACK_SCRIPT = r"""
(() => {
  const expectedUrl = __EXPECTED_URL__;
  const actualUrl = `${location.origin}${location.pathname}`;
  const isVisible = (element) => {
    if (!(element instanceof HTMLElement)) return false;
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
  };
  const composerReady = Array.from(document.querySelectorAll("textarea,[contenteditable='true']"))
    .some((element) => {
      if (!isVisible(element)) return false;
      if (element.closest("[aria-hidden='true']")) return false;
      return !element.disabled && element.getAttribute("aria-disabled") !== "true";
    });
  return {
    conversation_url: actualUrl,
    same_conversation: actualUrl === expectedUrl,
    page_ready: document.readyState === "complete",
    composer_ready: composerReady,
  };
})()
"""


_ARCHIVED_UI_FALLBACK_SCRIPT = r"""
(() => {
  const expectedUrl = __EXPECTED_URL__;
  const actualUrl = `${location.origin}${location.pathname}`;
  const result = (state, values = {}) => ({
    state,
    same_conversation: values.sameConversation === true,
    archived: values.archived === true,
    action: values.action === "unarchive" || values.action === "restore" ? values.action : null,
    geometry: values.geometry || null,
  });
  if (actualUrl !== expectedUrl) return result("url_mismatch");
  if (document.readyState !== "complete") return result("page_not_ready", { sameConversation: true });

  const normalize = (value) => String(value || "")
    .normalize("NFKC")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase();
  const isVisible = (element) => {
    if (!(element instanceof HTMLElement)) return false;
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
  };
  const isEnabled = (element) => !element.matches(":disabled") &&
    element.getAttribute("aria-disabled") !== "true" &&
    !element.closest("[aria-hidden='true']");
  const archivedState = (surface) => /\b(this (conversation|chat) (is|has been|was) archived|you are viewing an archived (conversation|chat)|archived (conversation|chat))\b/
    .test(normalize(surface.innerText || surface.textContent));
  const currentConversationControl = (element) => Boolean(element.closest("main,[role='main']")) &&
    !element.closest("nav,aside,[role='navigation'],[role='complementary'],form,[data-testid*='composer' i],[data-testid*='prompt' i]");
  const controlLabel = (element) => normalize(
    element.getAttribute("aria-label") || element.innerText || element.textContent
  );
  const archiveContext = (element) => Boolean(element.closest(
    "[data-testid*='archive' i],[aria-label*='archive' i],[title*='archive' i]"
  ));
  const archived = Array.from(document.querySelectorAll("main,[role='main']"))
    .some((surface) => archivedState(surface));
  if (!archived) return result("not_archived", { sameConversation: true });
  const control = Array.from(document.querySelectorAll("button,[role='button'],[role='menuitem']"))
    .find((candidate) => {
      if (!isVisible(candidate) || !isEnabled(candidate) || !currentConversationControl(candidate)) {
        return false;
      }
      const action = controlLabel(candidate);
      return action === "unarchive" || (action === "restore" && archiveContext(candidate));
    });
  if (!control) return result("no_exact_control", {
    sameConversation: true,
    archived: true,
  });

  const action = controlLabel(control);
  const rect = control.getBoundingClientRect();
  return result("native_activation_ready", {
    sameConversation: true,
    archived: true,
    action,
    geometry: {
      center_x: rect.left + rect.width / 2,
      center_y: rect.top + rect.height / 2,
      width: rect.width,
      height: rect.height,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
    },
  });
})()
"""


class _WebSocket:
    """The CDP websocket subset needed for one Runtime.evaluate call."""

    def __init__(self, url: str, timeout: float) -> None:
        self.url = url
        self.timeout = timeout
        self.socket: socket.socket | ssl.SSLSocket | None = None
        self._next_id = 1

    def __enter__(self) -> "_WebSocket":
        parsed = urlsplit(self.url)
        if parsed.scheme not in {"ws", "wss"} or not parsed.hostname:
            raise ValueError("invalid CDP websocket URL")
        port = parsed.port or (443 if parsed.scheme == "wss" else 80)
        raw_socket = socket.create_connection((parsed.hostname, port), self.timeout)
        if parsed.scheme == "wss":
            context = ssl.create_default_context()
            raw_socket = context.wrap_socket(raw_socket, server_hostname=parsed.hostname)
        self.socket = raw_socket
        self.socket.settimeout(self.timeout)

        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"
        host_header = parsed.hostname
        if parsed.port:
            host_header += f":{parsed.port}"
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).encode("ascii")
        self.socket.sendall(handshake)
        response = self._read_until_headers()
        if not response.startswith(b"HTTP/1.1 101") and not response.startswith(b"HTTP/1.0 101"):
            raise OSError("CDP websocket handshake failed")
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        if self.socket is not None:
            try:
                self.socket.close()
            finally:
                self.socket = None

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self.socket is None:
            raise OSError("CDP websocket is not connected")
        request_id = self._next_id
        self._next_id += 1
        payload = json.dumps(
            {"id": request_id, "method": method, "params": params},
            separators=(",", ":"),
        ).encode("utf-8")
        self._send_frame(0x1, payload)
        while True:
            opcode, message = self._read_message()
            if opcode != 0x1:
                continue
            value = json.loads(message.decode("utf-8"))
            if value.get("id") == request_id:
                return value

    def _read_until_headers(self) -> bytes:
        if self.socket is None:
            raise OSError("CDP websocket is not connected")
        data = bytearray()
        while b"\r\n\r\n" not in data:
            chunk = self.socket.recv(4096)
            if not chunk:
                raise OSError("CDP websocket closed during handshake")
            data.extend(chunk)
            if len(data) > 65536:
                raise OSError("CDP websocket handshake is too large")
        return bytes(data)

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        if self.socket is None:
            raise OSError("CDP websocket is not connected")
        length = len(payload)
        first = 0x80 | opcode
        if length < 126:
            header = bytes((first, 0x80 | length))
        elif length < 65536:
            header = bytes((first, 0x80 | 126)) + struct.pack("!H", length)
        else:
            header = bytes((first, 0x80 | 127)) + struct.pack("!Q", length)
        mask = os.urandom(4)
        masked_payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.socket.sendall(header + mask + masked_payload)

    def _read_message(self) -> tuple[int, bytes]:
        fragments = bytearray()
        message_opcode: int | None = None
        while True:
            first, second = self._read_exact(2)
            fin = bool(first & 0x80)
            opcode = first & 0x0F
            masked = bool(second & 0x80)
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._read_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._read_exact(8))[0]
            mask = self._read_exact(4) if masked else None
            payload = bytearray(self._read_exact(length))
            if mask is not None:
                for index in range(length):
                    payload[index] ^= mask[index % 4]

            if opcode == 0x9:
                self._send_frame(0xA, bytes(payload))
                continue
            if opcode == 0x8:
                raise OSError("CDP websocket closed")
            if opcode in {0x1, 0x2}:
                message_opcode = opcode
            elif opcode != 0x0:
                continue
            fragments.extend(payload)
            if fin:
                return message_opcode or 0x1, bytes(fragments)

    def _read_exact(self, length: int) -> bytes:
        if self.socket is None:
            raise OSError("CDP websocket is not connected")
        data = bytearray()
        while len(data) < length:
            chunk = self.socket.recv(length - len(data))
            if not chunk:
                raise OSError("CDP websocket closed")
            data.extend(chunk)
        return bytes(data)
