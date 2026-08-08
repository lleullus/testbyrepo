"""Safe continuation of one stored Oracle Browser conversation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import tempfile
import threading
import time
from typing import Any, Callable, Sequence
from urllib.parse import urlsplit, urlunsplit

from .attachments import (
    AttachmentPreparationError,
    AttachmentPreparationInterrupted,
    PreparedAttachment,
)
from .cdp import CDPError
from .model import AVAILABLE, OCCUPIED, SLOT_IDS, Settings, utc_now
from .runner import JobRunner, LifecycleEmitter, OracleTransportError
from .service import SlotService


_SESSION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_CONVERSATION_ID = re.compile(r"^[A-Za-z0-9-]+$")
_CONVERSATION_PATH = re.compile(r"/c/([A-Za-z0-9-]+)(?=/|$)")


class FollowupError(Exception):
    """A follow-up cannot safely proceed or be persisted."""

    def __init__(self, reason: str, operator_action: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.operator_action = operator_action


@dataclass(frozen=True)
class ConversationIdentity:
    conversation_id: str
    conversation_url: str


@dataclass(frozen=True)
class ParentSession:
    session_id: str
    slot_id: int
    context_id: str
    conversation: ConversationIdentity
    created_timestamp: float
    metadata: dict[str, Any]


class OracleSessionRepository:
    """Read and atomically annotate stock Oracle session metadata."""

    def __init__(
        self,
        settings: Settings,
        *,
        oracle_home: Path | None = None,
    ) -> None:
        self.settings = settings
        self.oracle_home = (oracle_home or self._oracle_home_from_env()).expanduser()
        self.sessions_root = self.oracle_home / "sessions"

    @staticmethod
    def normalize_context_id(value: str) -> str:
        context_id = value.strip() if isinstance(value, str) else ""
        if not context_id:
            raise FollowupError(
                "OpenCode conversation ID가 비어 있습니다.",
                "현재 대화의 비어 있지 않은 --opencode-conversation-id를 지정하십시오.",
            )
        if len(context_id) > 200 or any(ord(character) < 32 for character in context_id):
            raise FollowupError(
                "OpenCode conversation ID 형식이 올바르지 않습니다.",
                "제어 문자가 없고 200자 이하인 durable conversation ID를 지정하십시오.",
            )
        return context_id

    def select_parent(
        self,
        context_id: str,
        explicit_session_id: str | None = None,
    ) -> tuple[ParentSession, str]:
        normalized_context = self.normalize_context_id(context_id)
        if explicit_session_id is not None:
            try:
                session_id = self._normalize_session_id(explicit_session_id)
                metadata = self._read_required_session(session_id)
                return self._eligible_parent(metadata, require_context=False), "explicit"
            except FollowupError as exc:
                display_id = (
                    explicit_session_id.strip()
                    if isinstance(explicit_session_id, str) and explicit_session_id.strip()
                    else "<empty>"
                )
                raise FollowupError(
                    f"명시한 부모 세션 {display_id}은 재개할 수 없습니다: {exc.reason}",
                    (
                        f"세션 {display_id}의 종료·conversation·원 슬롯 증거를 확인한 뒤 "
                        "같은 --parent-session-id로 다시 실행하십시오. 다른 세션으로 자동 전환하지 않았습니다."
                    ),
                ) from exc

        owned: list[dict[str, Any]] = []
        rejection_reasons: list[str] = []
        for metadata in self._list_sessions():
            namespace = metadata.get("oracle_browser_slots")
            if not isinstance(namespace, dict):
                continue
            if namespace.get("opencode_conversation_id") != normalized_context:
                continue
            owned.append(metadata)

        eligible: list[ParentSession] = []
        for metadata in owned:
            try:
                eligible.append(self._eligible_parent(metadata))
            except FollowupError as exc:
                rejection_reasons.append(exc.reason)
        if eligible:
            eligible.sort(
                key=lambda parent: (parent.created_timestamp, parent.session_id),
                reverse=True,
            )
            return eligible[0], "implicit"

        if not owned:
            reason = (
                "현재 OpenCode conversation ID로 기록된 종료 Oracle Browser 세션이 없습니다."
            )
        else:
            distinct_reasons = list(dict.fromkeys(rejection_reasons))
            detail = "; ".join(distinct_reasons[:3]) or "재개 자격 증거가 없습니다."
            reason = (
                f"현재 OpenCode 대화의 세션 {len(owned)}개가 모두 재개 자격을 충족하지 않습니다: "
                f"{detail}"
            )
        raise FollowupError(
            reason,
            (
                "현재 --opencode-conversation-id를 확인하거나, 재개 자격이 있는 로컬 세션을 "
                "--parent-session-id <session-id>로 명시하십시오. 새 ChatGPT 대화는 만들지 않았습니다."
            ),
        )

    def new_session_id(self, kind: str, request_id: str) -> str:
        request_hint = re.sub(r"[^a-z0-9]+", "", request_id.lower())[:8] or "request"
        kind_hint = re.sub(r"[^a-z0-9]+", "", kind.lower())[:10] or "session"
        for _ in range(50):
            candidate = f"slots-{kind_hint}-{request_hint}-{secrets.token_hex(5)}"
            if not (self.sessions_root / candidate).exists():
                return candidate
        raise FollowupError(
            "고유한 stock Oracle 자식 세션 ID를 만들 수 없습니다.",
            "ORACLE_HOME_DIR의 sessions 경로를 확인한 뒤 다시 실행하십시오.",
        )

    def prepare_new_run_command(
        self,
        argv: Sequence[str],
        request_id: str,
    ) -> tuple[list[str], str]:
        child_session_id = self.new_session_id("context", request_id)
        command = self._prepare_owned_command(
            argv,
            child_session_id=child_session_id,
            parent_session_id=None,
        )
        return command, child_session_id

    def prepare_followup_command(
        self,
        argv: Sequence[str],
        parent_session_id: str,
        child_session_id: str,
    ) -> list[str]:
        return self._prepare_owned_command(
            argv,
            child_session_id=child_session_id,
            parent_session_id=parent_session_id,
        )

    def record_origin(
        self,
        child_session_id: str,
        *,
        context_id: str,
        slot_id: int,
        request_id: str,
        operation: str,
        exit_code: int,
    ) -> dict[str, Any]:
        context_id = self.normalize_context_id(context_id)
        metadata = self._read_required_session(child_session_id)
        self._validate_created_session(metadata, child_session_id)
        options = metadata.get("options")
        if isinstance(options, dict) and options.get("followupSessionId"):
            raise FollowupError(
                f"새 요청 세션 {child_session_id}에 예상하지 않은 follow-up parent가 있습니다.",
                "해당 세션 메타데이터를 확인하고 요청을 자동 재시도하지 마십시오.",
            )
        self._validate_stock_slot(metadata, slot_id, require_runtime=False)
        namespace = self._namespace(metadata)
        namespace.update(
            {
                "schema_version": 1,
                "opencode_conversation_id": context_id,
                "originating_slot": self._slot_evidence(slot_id),
                "oracle_cli": {
                    "operation": operation,
                    "request_id": request_id,
                    "terminated": True,
                    "terminated_at": utc_now(),
                    "exit_code": exit_code,
                },
            }
        )
        readback = self._write_namespace(child_session_id, namespace)
        persisted_metadata = self._read_required_session(child_session_id)
        return {
            "metadata_path": str(self._metadata_path(child_session_id)),
            "child_session_id": child_session_id,
            "opencode_conversation_id": context_id,
            "originating_slot": readback["originating_slot"],
            "oracle_cli": readback["oracle_cli"],
            "stock_status": persisted_metadata.get("status"),
        }

    def record_followup(
        self,
        child_session_id: str,
        *,
        parent: ParentSession,
        selection_mode: str,
        context_id: str,
        request_id: str,
        exit_code: int,
    ) -> dict[str, Any]:
        context_id = self.normalize_context_id(context_id)
        metadata = self._read_required_session(child_session_id)
        self._validate_created_session(metadata, child_session_id)
        failures: list[str] = []

        options = metadata.get("options")
        stock_parent = options.get("followupSessionId") if isinstance(options, dict) else None
        if stock_parent != parent.session_id:
            failures.append(
                f"stock lineage parent가 {parent.session_id}와 일치하지 않습니다: {stock_parent!r}"
            )

        actual_conversation: ConversationIdentity | None = None
        try:
            actual_conversation = self._conversation_identity(metadata)
        except FollowupError as exc:
            failures.append(exc.reason)
        same_conversation = bool(
            actual_conversation
            and actual_conversation.conversation_id == parent.conversation.conversation_id
            and actual_conversation.conversation_url == parent.conversation.conversation_url
        )
        if not same_conversation:
            failures.append("자식의 conversation ID/URL이 부모와 동일하지 않습니다.")

        try:
            self._validate_stock_slot(metadata, parent.slot_id, require_runtime=True)
        except FollowupError as exc:
            failures.append(exc.reason)

        browser = metadata.get("browser")
        runtime = browser.get("runtime") if isinstance(browser, dict) else None
        prompt_submitted = isinstance(runtime, dict) and runtime.get("promptSubmitted") is True
        if not prompt_submitted:
            failures.append("stock runtime에서 후속 프롬프트 제출을 확인하지 못했습니다.")

        stock_status = metadata.get("status")
        completed = exit_code == 0 and stock_status == "completed"
        if exit_code != 0:
            failures.append(f"canonical stock Oracle가 exit code {exit_code}로 종료되었습니다.")
        elif stock_status != "completed":
            failures.append(f"stock 자식 세션 상태가 completed가 아닙니다: {stock_status!r}")

        result = self._result_evidence(child_session_id, metadata)
        if result["status"] != "available":
            failures.append("저장된 follow-up 응답 로그 또는 transcript를 확인하지 못했습니다.")

        slot_evidence = self._slot_evidence(parent.slot_id)
        namespace = self._namespace(metadata)
        namespace.update(
            {
                "schema_version": 1,
                "opencode_conversation_id": context_id,
                "originating_slot": slot_evidence,
                "oracle_cli": {
                    "operation": "followup",
                    "request_id": request_id,
                    "terminated": True,
                    "terminated_at": utc_now(),
                    "exit_code": exit_code,
                },
                "followup": {
                    "selection_mode": selection_mode,
                    "parent_session_id": parent.session_id,
                    "child_session_id": child_session_id,
                    "original_slot": slot_evidence,
                    "conversation": {
                        "expected_id": parent.conversation.conversation_id,
                        "expected_url": parent.conversation.conversation_url,
                        "actual_id": (
                            actual_conversation.conversation_id
                            if actual_conversation is not None
                            else None
                        ),
                        "actual_url": (
                            actual_conversation.conversation_url
                            if actual_conversation is not None
                            else None
                        ),
                        "same_as_parent": same_conversation,
                    },
                    "prompt_submission": {
                        "submitted": prompt_submitted,
                        "status": "submitted" if prompt_submitted else "not_confirmed",
                    },
                    "completion": {
                        "completed": completed,
                        "stock_status": stock_status,
                        "oracle_cli_exit_code": exit_code,
                    },
                    "result": result,
                    "verification": {
                        "ok": not failures,
                        "failures": failures,
                    },
                },
            }
        )
        readback = self._write_namespace(child_session_id, namespace)
        persisted_metadata = self._read_required_session(child_session_id)
        return self._followup_readback(persisted_metadata, readback)

    def read_followup(self, session_id: str) -> dict[str, Any]:
        metadata = self._read_required_session(self._normalize_session_id(session_id))
        namespace = metadata.get("oracle_browser_slots")
        if not isinstance(namespace, dict) or not isinstance(namespace.get("followup"), dict):
            raise FollowupError(
                f"세션 {session_id}에 Oracle Browser Slots follow-up readback이 없습니다.",
                "followup 명령이 반환한 child_session_id를 확인하십시오.",
            )
        return self._followup_readback(metadata, namespace)

    def _eligible_parent(
        self, metadata: dict[str, Any], *, require_context: bool = True
    ) -> ParentSession:
        session_id = metadata.get("id")
        if not isinstance(session_id, str) or not session_id:
            raise FollowupError("세션 ID가 없습니다.", "올바른 stock Oracle meta.json을 확인하십시오.")
        mode = metadata.get("mode")
        options = metadata.get("options")
        if mode is None and isinstance(options, dict):
            mode = options.get("mode")
        if mode != "browser":
            raise FollowupError("Oracle Browser 세션이 아닙니다.", "browser 세션을 지정하십시오.")
        if metadata.get("status") == "running":
            raise FollowupError(
                "실행 중인 Oracle Browser 세션은 재개할 수 없습니다.",
                "세션이 종료된 뒤 다시 시도하십시오.",
            )

        namespace = metadata.get("oracle_browser_slots")
        if not isinstance(namespace, dict):
            raise FollowupError(
                "관리되는 원 슬롯 증거가 없습니다.",
                "--opencode-conversation-id를 사용해 슬롯 wrapper에서 만든 세션을 지정하십시오.",
            )
        context_id = namespace.get("opencode_conversation_id")
        if require_context and (not isinstance(context_id, str) or not context_id):
            raise FollowupError(
                "OpenCode conversation 소유권 증거가 없습니다.",
                "context-aware run 또는 submit으로 만든 세션을 지정하십시오.",
            )
        if not isinstance(context_id, str):
            context_id = ""
        oracle_cli = namespace.get("oracle_cli")
        if not isinstance(oracle_cli, dict) or oracle_cli.get("terminated") is not True:
            raise FollowupError(
                "canonical stock Oracle child 종료를 확인할 수 없습니다.",
                "실행 중인 세션이 끝난 뒤 다시 시도하십시오.",
            )
        origin = namespace.get("originating_slot")
        if not isinstance(origin, dict):
            raise FollowupError(
                "관리되는 원 슬롯·프로필을 확인할 수 없습니다.",
                "원 슬롯 증거가 있는 세션을 지정하십시오.",
            )
        slot_id = origin.get("slot_id")
        if isinstance(slot_id, bool) or slot_id not in SLOT_IDS:
            raise FollowupError("원 슬롯 ID가 올바르지 않습니다.", "세션 원 슬롯 증거를 확인하십시오.")
        expected_origin = self._slot_evidence(int(slot_id))
        if origin != expected_origin:
            raise FollowupError(
                "세션의 원 슬롯·포트·프로필이 현재 관리 슬롯 설정과 일치하지 않습니다.",
                f"현재 profile root를 확인하고 슬롯 {slot_id} 세션을 다시 준비하십시오.",
            )
        self._validate_stock_slot(metadata, int(slot_id), require_runtime=True)
        conversation = self._conversation_identity(metadata)
        created_timestamp = self._created_timestamp(metadata)
        return ParentSession(
            session_id=session_id,
            slot_id=int(slot_id),
            context_id=context_id,
            conversation=conversation,
            created_timestamp=created_timestamp,
            metadata=metadata,
        )

    def _validate_stock_slot(
        self,
        metadata: dict[str, Any],
        slot_id: int,
        *,
        require_runtime: bool,
    ) -> None:
        slot = self.settings.slot(slot_id)
        browser = metadata.get("browser")
        options = metadata.get("options")
        config = browser.get("config") if isinstance(browser, dict) else None
        if not isinstance(config, dict) and isinstance(options, dict):
            config = options.get("browserConfig")
        remote = config.get("remoteChrome") if isinstance(config, dict) else None
        if not isinstance(remote, dict) or remote.get("host") != "127.0.0.1" or remote.get(
            "port"
        ) != slot.port:
            raise FollowupError(
                f"stock 세션의 remote Chrome이 관리 슬롯 {slot_id} endpoint와 일치하지 않습니다.",
                f"슬롯 {slot_id}에서 생성된 세션을 지정하십시오.",
            )

        runtime = browser.get("runtime") if isinstance(browser, dict) else None
        if runtime is None and not require_runtime:
            return
        if not isinstance(runtime, dict):
            raise FollowupError(
                "stock browser runtime 증거가 없습니다.",
                "종료된 browser 세션의 runtime 메타데이터를 확인하십시오.",
            )
        if runtime.get("chromeHost") != "127.0.0.1" or runtime.get("chromePort") != slot.port:
            raise FollowupError(
                f"stock browser runtime이 원 슬롯 {slot_id}과 일치하지 않습니다.",
                "원 슬롯의 host/port runtime 증거를 확인하십시오.",
            )

    def _conversation_identity(self, metadata: dict[str, Any]) -> ConversationIdentity:
        browser = metadata.get("browser")
        if not isinstance(browser, dict):
            raise FollowupError(
                "browser conversation 메타데이터가 없습니다.",
                "안정적인 ChatGPT conversation URL이 있는 세션을 지정하십시오.",
            )
        runtime = browser.get("runtime")
        harvest = browser.get("harvest")
        runtime = runtime if isinstance(runtime, dict) else {}
        harvest = harvest if isinstance(harvest, dict) else {}

        identities: list[ConversationIdentity] = []
        for candidate in (harvest.get("url"), runtime.get("tabUrl")):
            identity = self._parse_conversation_url(candidate)
            if identity is not None:
                identities.append(identity)

        runtime_id = runtime.get("conversationId")
        if runtime_id is not None:
            if not isinstance(runtime_id, str) or not _CONVERSATION_ID.fullmatch(runtime_id.strip()):
                raise FollowupError(
                    "runtime conversation ID가 안정적인 형식이 아닙니다.",
                    "persisted ChatGPT /c/<id> URL을 확인하십시오.",
                )
            runtime_id = runtime_id.strip()

        if identities:
            first = identities[0]
            if any(identity != first for identity in identities[1:]):
                raise FollowupError(
                    "저장된 ChatGPT conversation URL들이 서로 일치하지 않습니다.",
                    "harvest/runtime conversation 증거를 확인하십시오.",
                )
            if runtime_id and runtime_id != first.conversation_id:
                raise FollowupError(
                    "저장된 conversation ID와 URL의 ID가 일치하지 않습니다.",
                    "runtime conversation 증거를 확인하십시오.",
                )
            return first

        if not runtime_id:
            raise FollowupError(
                "안정적인 ChatGPT conversation ID/URL이 없습니다.",
                "chatgpt.com/c/<id> URL이 저장된 종료 세션을 지정하십시오.",
            )
        config = browser.get("config")
        options = metadata.get("options")
        if not isinstance(config, dict) and isinstance(options, dict):
            config = options.get("browserConfig")
        base = config.get("url") if isinstance(config, dict) else None
        base_url = base if isinstance(base, str) and base.strip() else "https://chatgpt.com/"
        try:
            parsed = urlsplit(base_url)
        except ValueError as exc:
            raise FollowupError(
                "저장된 ChatGPT base URL이 올바르지 않습니다.",
                "browser config URL을 확인하십시오.",
            ) from exc
        if (
            parsed.scheme != "https"
            or parsed.port is not None
            or (parsed.hostname or "").lower() not in {"chatgpt.com", "chat.openai.com"}
        ):
            raise FollowupError(
                "저장된 ChatGPT base URL을 안전하게 사용할 수 없습니다.",
                "https://chatgpt.com 기반 browser 세션을 지정하십시오.",
            )
        prefix = parsed.path.rstrip("/")
        built = urlunsplit(("https", (parsed.hostname or "").lower(), f"{prefix}/c/{runtime_id}", "", ""))
        identity = self._parse_conversation_url(built)
        if identity is None:
            raise FollowupError(
                "conversation ID에서 안전한 ChatGPT URL을 만들 수 없습니다.",
                "runtime conversation 증거를 확인하십시오.",
            )
        return identity

    @staticmethod
    def _parse_conversation_url(value: Any) -> ConversationIdentity | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            parsed = urlsplit(value.strip())
            host = (parsed.hostname or "").lower()
            if (
                parsed.scheme != "https"
                or parsed.port is not None
                or host not in {"chatgpt.com", "chat.openai.com"}
            ):
                return None
        except ValueError:
            return None
        match = _CONVERSATION_PATH.search(parsed.path)
        if match is None:
            return None
        conversation_id = match.group(1)
        canonical_path = parsed.path.rstrip("/")
        canonical_url = urlunsplit(("https", host, canonical_path, "", ""))
        return ConversationIdentity(conversation_id, canonical_url)

    def _prepare_owned_command(
        self,
        argv: Sequence[str],
        *,
        child_session_id: str,
        parent_session_id: str | None,
    ) -> list[str]:
        command = list(argv)
        if not command:
            raise FollowupError(
                "실행할 canonical stock Oracle command가 없습니다.",
                "-- 뒤에 canonical Oracle argv를 지정하십시오.",
            )
        if "--" in command[1:]:
            raise FollowupError(
                "stock Oracle argv 내부의 -- terminator는 context 세션 플래그와 함께 사용할 수 없습니다.",
                "prompt와 옵션을 명시적 stock Oracle 플래그로 전달하십시오.",
            )
        for owned in ("--slug", "--followup", "--browser-archive"):
            if self._option_values(command, owned):
                raise FollowupError(
                    f"{owned}는 Oracle Browser Slots가 소유하는 옵션입니다.",
                    f"caller argv에서 {owned}를 제거하십시오.",
                )
        if self._option_count(command, "--no-wait"):
            raise FollowupError(
                "context-aware Oracle 요청은 --no-wait를 사용할 수 없습니다.",
                "--no-wait를 제거하십시오. child 종료 후에만 session 증거를 기록합니다.",
            )
        wait_count = self._option_count(command, "--wait")
        if wait_count > 1:
            raise FollowupError("--wait가 중복 지정되었습니다.", "--wait를 한 번만 지정하십시오.")
        normalized = list(command)
        if parent_session_id is not None:
            normalized.extend(("--followup", parent_session_id))
        normalized.extend(("--slug", child_session_id))
        if wait_count == 0:
            normalized.append("--wait")
        normalized.extend(("--browser-archive", "never"))
        return normalized

    @staticmethod
    def _option_count(argv: Sequence[str], flag: str) -> int:
        return sum(
            token == flag or token.startswith(f"{flag}=") for token in argv[1:]
        )

    @staticmethod
    def _option_values(argv: Sequence[str], flag: str) -> list[str | None]:
        values: list[str | None] = []
        index = 1
        while index < len(argv):
            token = argv[index]
            if token == flag:
                value = argv[index + 1] if index + 1 < len(argv) and not argv[index + 1].startswith("--") else None
                values.append(value)
                index += 2 if value is not None else 1
                continue
            prefix = f"{flag}="
            if token.startswith(prefix):
                values.append(token[len(prefix) :])
            index += 1
        return values

    def _validate_created_session(
        self, metadata: dict[str, Any], expected_session_id: str
    ) -> None:
        if metadata.get("id") != expected_session_id:
            raise FollowupError(
                f"stock session ID readback이 예상한 자식 ID와 일치하지 않습니다: {metadata.get('id')!r}",
                "자식 세션 경로를 확인하고 요청을 자동 재시도하지 마십시오.",
            )
        options = metadata.get("options")
        if not isinstance(options, dict) or options.get("slug") != expected_session_id:
            raise FollowupError(
                "stock session slug readback이 wrapper가 만든 자식 ID와 일치하지 않습니다.",
                "자식 meta.json을 확인하고 요청을 자동 재시도하지 마십시오.",
            )
        mode = metadata.get("mode") or options.get("mode")
        if mode != "browser":
            raise FollowupError(
                "생성된 자식이 Oracle Browser 세션이 아닙니다.",
                "canonical stock Oracle --engine browser 실행 결과를 확인하십시오.",
            )

    def _slot_evidence(self, slot_id: int) -> dict[str, Any]:
        slot = self.settings.slot(slot_id)
        return {
            "slot_id": slot.slot_id,
            "port": slot.port,
            "profile_dir": str(slot.profile_dir),
            "remote_chrome": f"127.0.0.1:{slot.port}",
        }

    def _result_evidence(
        self, session_id: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        session_directory = self._session_directory(session_id)
        candidates: list[Path] = [session_directory / "output.log"]
        models_directory = session_directory / "models"
        try:
            candidates.extend(
                sorted(
                    (
                        path
                        for path in models_directory.iterdir()
                        if path.is_file() and path.suffix == ".log"
                    ),
                    key=lambda path: path.name,
                )
            )
        except OSError:
            pass
        artifacts = metadata.get("artifacts")
        if isinstance(artifacts, list):
            for artifact in artifacts:
                if not isinstance(artifact, dict) or artifact.get("kind") != "transcript":
                    continue
                artifact_path = artifact.get("path")
                if isinstance(artifact_path, str) and artifact_path:
                    candidate = Path(artifact_path)
                    candidates.append(
                        candidate if candidate.is_absolute() else session_directory / candidate
                    )

        root = session_directory.resolve()
        seen: set[Path] = set()
        paths: list[str] = []
        digest = hashlib.sha256()
        total_bytes = 0
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
                if not resolved.is_relative_to(root) or resolved in seen or not resolved.is_file():
                    continue
                size = resolved.stat().st_size
                if size <= 0:
                    continue
                relative = resolved.relative_to(root).as_posix()
                digest.update(relative.encode("utf-8"))
                digest.update(b"\0")
                with resolved.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
                        total_bytes += len(chunk)
                seen.add(resolved)
                paths.append(relative)
            except OSError:
                continue
        return {
            "status": "available" if paths else "not_recorded",
            "paths": paths,
            "bytes": total_bytes,
            "sha256": digest.hexdigest() if paths else None,
        }

    def _write_namespace(
        self, session_id: str, namespace: dict[str, Any]
    ) -> dict[str, Any]:
        metadata_path = self._metadata_path(session_id)
        metadata = self._read_required_session(session_id)
        updated = dict(metadata)
        updated["oracle_browser_slots"] = namespace
        try:
            mode = stat.S_IMODE(metadata_path.stat().st_mode)
            fd, temporary = tempfile.mkstemp(
                prefix=f".{metadata_path.name}.", suffix=".tmp", dir=metadata_path.parent
            )
            temporary_path = Path(temporary)
            try:
                os.fchmod(fd, mode)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(updated, handle, ensure_ascii=False, indent=2, sort_keys=True)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_path, metadata_path)
                directory_fd = os.open(metadata_path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            finally:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
        except (OSError, TypeError, ValueError) as exc:
            raise FollowupError(
                f"자식 session 메타데이터를 원자적으로 저장하지 못했습니다: {exc}",
                "자식 meta.json과 ORACLE_HOME_DIR 권한을 확인하고 요청을 자동 재시도하지 마십시오.",
            ) from exc

        readback = self._read_required_session(session_id)
        persisted = readback.get("oracle_browser_slots")
        if persisted != namespace:
            raise FollowupError(
                "자식 session 메타데이터 authoritative readback이 저장 내용과 일치하지 않습니다.",
                "자식 meta.json을 확인하고 요청을 자동 재시도하지 마십시오.",
            )
        return persisted

    def _followup_readback(
        self, metadata: dict[str, Any], namespace: dict[str, Any]
    ) -> dict[str, Any]:
        followup = namespace["followup"]
        conversation = followup["conversation"]
        options = metadata.get("options")
        return {
            "metadata_path": str(self._metadata_path(str(metadata["id"]))),
            "selection_mode": followup["selection_mode"],
            "opencode_conversation_id": namespace["opencode_conversation_id"],
            "parent_session_id": followup["parent_session_id"],
            "child_session_id": followup["child_session_id"],
            "stock_parent_session_id": (
                options.get("followupSessionId") if isinstance(options, dict) else None
            ),
            "original_slot": followup["original_slot"],
            "conversation_id": conversation["actual_id"],
            "conversation_url": conversation["actual_url"],
            "same_conversation": conversation["same_as_parent"],
            "prompt_submission": followup["prompt_submission"],
            "completion": followup["completion"],
            "result": followup["result"],
            "verification": followup["verification"],
            "stock_status": metadata.get("status"),
        }

    def _list_sessions(self) -> list[dict[str, Any]]:
        try:
            entries = list(self.sessions_root.iterdir())
        except FileNotFoundError:
            return []
        except OSError as exc:
            raise FollowupError(
                f"stock Oracle sessions 경로를 읽을 수 없습니다: {self.sessions_root}",
                "ORACLE_HOME_DIR 경로와 권한을 확인하십시오.",
            ) from exc
        sessions: list[dict[str, Any]] = []
        for entry in entries:
            if entry.is_symlink() or not entry.is_dir() or not _SESSION_ID.fullmatch(entry.name):
                continue
            metadata = self._read_json(entry / "meta.json")
            if isinstance(metadata, dict) and metadata.get("id") == entry.name:
                sessions.append(metadata)
        return sessions

    def _read_required_session(self, session_id: str) -> dict[str, Any]:
        session_id = self._normalize_session_id(session_id)
        directory = self._session_directory(session_id)
        if directory.is_symlink():
            raise FollowupError(
                f"세션 경로가 symlink이므로 사용하지 않습니다: {session_id}",
                "ORACLE_HOME_DIR의 실제 stock session 디렉터리를 지정하십시오.",
            )
        metadata = self._read_json(directory / "meta.json")
        if not isinstance(metadata, dict):
            raise FollowupError(
                f"로컬 stock Oracle 세션을 읽을 수 없습니다: {session_id}",
                "oracle session 목록과 ORACLE_HOME_DIR을 확인하십시오.",
            )
        if metadata.get("id") != session_id:
            raise FollowupError(
                f"세션 디렉터리와 meta.json ID가 일치하지 않습니다: {session_id}",
                "stock session 메타데이터를 복구한 뒤 다시 실행하십시오.",
            )
        return metadata

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def _session_directory(self, session_id: str) -> Path:
        return self.sessions_root / self._normalize_session_id(session_id)

    def _metadata_path(self, session_id: str) -> Path:
        return self._session_directory(session_id) / "meta.json"

    @staticmethod
    def _normalize_session_id(value: str) -> str:
        session_id = value.strip() if isinstance(value, str) else ""
        if not _SESSION_ID.fullmatch(session_id):
            raise FollowupError(
                "stock Oracle session ID 형식이 올바르지 않습니다.",
                "oracle session 목록에 표시된 로컬 session ID를 지정하십시오.",
            )
        return session_id

    @staticmethod
    def _created_timestamp(metadata: dict[str, Any]) -> float:
        value = metadata.get("createdAt")
        if not isinstance(value, str) or not value:
            raise FollowupError(
                "세션 생성 시각이 없습니다.",
                "stock Oracle createdAt 메타데이터를 확인하십시오.",
            )
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.timestamp()
        except ValueError as exc:
            raise FollowupError(
                "세션 생성 시각 형식이 올바르지 않습니다.",
                "stock Oracle createdAt 메타데이터를 확인하십시오.",
            ) from exc

    @staticmethod
    def _namespace(metadata: dict[str, Any]) -> dict[str, Any]:
        existing = metadata.get("oracle_browser_slots")
        return dict(existing) if isinstance(existing, dict) else {}

    @staticmethod
    def _oracle_home_from_env() -> Path:
        configured = os.environ.get("ORACLE_HOME_DIR")
        if configured:
            return Path(configured)
        return Path(os.environ.get("HOME", str(Path.home()))) / ".oracle"


class FollowupRunner:
    """Select one parent and run stock Oracle on only its originating slot."""

    def __init__(
        self,
        service: SlotService,
        *,
        runner: JobRunner | None = None,
        repository: OracleSessionRepository | None = None,
        poll_interval: float | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.service = service
        self.runner = runner or JobRunner(service)
        self.repository = repository or OracleSessionRepository(service.settings)
        self.poll_interval = poll_interval or service.settings.queue_poll_interval
        self.sleep = sleep

    def _reserve_request(self, request_id: str) -> None:
        reservation_root = self.service.settings.state_root / "followup-requests"
        reservation_root.mkdir(parents=True, exist_ok=True)
        request_key = hashlib.sha256(request_id.encode("utf-8")).hexdigest()
        path = reservation_root / f"{request_key}.json"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            payload = json.dumps(
                {"request_id": request_id, "reserved_at": utc_now()},
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
            os.write(descriptor, payload + b"\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def run(
        self,
        request_id: str,
        context_id: str,
        argv: Sequence[str],
        *,
        parent_session_id: str | None = None,
        emit: LifecycleEmitter | None = None,
    ) -> dict[str, Any]:
        selection_mode = "explicit" if parent_session_id is not None else "implicit"
        if not isinstance(request_id, str) or not request_id:
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="rejected",
                exit_code=2,
                reason="request ID가 비어 있습니다.",
                operator_action="비어 있지 않은 --request-id를 지정하십시오.",
                emit=emit,
            )
        try:
            self._reserve_request(request_id)
        except FileExistsError:
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="rejected",
                exit_code=2,
                reason="동일 request ID의 follow-up이 이미 접수되었습니다.",
                operator_action="기존 요청의 결과를 확인하고 새 lifecycle에는 다른 request ID를 사용하십시오.",
                emit=emit,
            )
        except OSError:
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="failed",
                exit_code=1,
                reason="follow-up request ID를 안전하게 예약할 수 없습니다.",
                operator_action="managed browser 상태 경로의 권한과 디스크 상태를 확인하십시오.",
                emit=emit,
            )
        try:
            context_id = self.repository.normalize_context_id(context_id)
            parent, selection_mode = self.repository.select_parent(
                context_id, parent_session_id
            )
        except FollowupError as exc:
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="failed",
                exit_code=1,
                reason=exc.reason,
                operator_action=exc.operator_action,
                context_id=context_id if isinstance(context_id, str) else None,
                emit=emit,
            )

        child_session_id = self.repository.new_session_id("followup", request_id)
        selected = self._record(
            request_id,
            event="parent_selected",
            outcome="selected",
            selection_mode=selection_mode,
            context_id=context_id,
            parent=parent,
            child_session_id=child_session_id,
            reason=(
                f"{selection_mode} 방식으로 부모 {parent.session_id}을 선택하고 원 슬롯 "
                f"{parent.slot_id}에 고정했습니다."
            ),
            operator_action="없음",
        )
        self._emit(emit, selected)

        try:
            command = self.repository.prepare_followup_command(
                argv, parent.session_id, child_session_id
            )
            command = self.runner.validate_auto_command(command)
            self.runner.assert_slot_compatible(parent.slot_id, command)
        except (FollowupError, OracleTransportError, ValueError) as exc:
            reason = exc.reason if isinstance(exc, (FollowupError, OracleTransportError)) else str(exc)
            action = (
                exc.operator_action
                if isinstance(exc, (FollowupError, OracleTransportError))
                else "canonical stock Oracle argv를 확인하십시오."
            )
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="rejected",
                exit_code=2,
                reason=reason,
                operator_action=action,
                context_id=context_id,
                parent=parent,
                child_session_id=child_session_id,
                emit=emit,
            )

        prepared: PreparedAttachment | None = None
        try:
            command, prepared = self.runner.prepare_file_request(command, request_id)
        except AttachmentPreparationInterrupted as exc:
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="cancelled",
                exit_code=130,
                reason=(
                    f"follow-up 파일 준비가 {signal.Signals(exc.signal_number).name} 신호로 "
                    "중단되었습니다."
                ),
                operator_action="파일 입력을 확인한 뒤 다시 실행하십시오.",
                context_id=context_id,
                parent=parent,
                child_session_id=child_session_id,
                emit=emit,
            )
        except KeyboardInterrupt:
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="cancelled",
                exit_code=130,
                reason="follow-up 파일 준비가 운영자 중단으로 종료되었습니다.",
                operator_action="파일 입력을 확인한 뒤 다시 실행하십시오.",
                context_id=context_id,
                parent=parent,
                child_session_id=child_session_id,
                emit=emit,
            )
        except AttachmentPreparationError as exc:
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="failed",
                exit_code=2,
                reason=exc.reason,
                operator_action=exc.operator_action,
                context_id=context_id,
                parent=parent,
                child_session_id=child_session_id,
                emit=emit,
            )

        cancellation: dict[str, int | bool | None] = {
            "requested": False,
            "signal": None,
        }
        previous_handlers: dict[int, Any] = {}
        install_handlers = threading.current_thread() is threading.main_thread()

        def cancel_handler(signal_number: int, _frame: Any) -> None:
            cancellation["requested"] = True
            cancellation["signal"] = signal_number

        claim: dict[str, Any] | None = None
        execution_started = False
        waiting_emitted = False
        try:
            if install_handlers:
                for signal_number in self._cancel_signals():
                    previous_handlers[signal_number] = signal.getsignal(signal_number)
                    signal.signal(signal_number, cancel_handler)

            while claim is None:
                if cancellation["requested"]:
                    return self._cancel_before_claim(
                        request_id,
                        selection_mode,
                        context_id,
                        parent,
                        child_session_id,
                        cancellation["signal"],
                        emit,
                    )
                status = self.service.status(parent.slot_id)
                if status.get("status") == OCCUPIED:
                    if not waiting_emitted:
                        waiting_emitted = True
                        waiting = self._record(
                            request_id,
                            event="waiting",
                            outcome="waiting",
                            selection_mode=selection_mode,
                            context_id=context_id,
                            parent=parent,
                            child_session_id=child_session_id,
                            reason=(
                                f"부모의 원 슬롯 {parent.slot_id}이 점유 중이므로 이 슬롯만 "
                                "자동 만료 없이 기다립니다."
                            ),
                            operator_action="호출자 취소 또는 원 슬롯 해제를 기다리십시오.",
                        )
                        self._emit(emit, waiting)
                    self.sleep(self.poll_interval)
                    continue
                if status.get("status") != AVAILABLE:
                    return self._terminal(
                        request_id,
                        selection_mode=selection_mode,
                        event="failed",
                        exit_code=1,
                        reason=(
                            f"부모의 원 슬롯 {parent.slot_id}을 사용할 수 없습니다: "
                            f"{status.get('reason', status.get('status'))}"
                        ),
                        operator_action=(
                            f"다른 슬롯으로 전환하지 않았습니다. {status.get('operator_action', '')}"
                        ).strip(),
                        context_id=context_id,
                        parent=parent,
                        child_session_id=child_session_id,
                        emit=emit,
                    )

                attempted = self.runner.claim_for_auto(
                    parent.slot_id,
                    request_id,
                    command,
                    apply_workspace_mapping=False,
                )
                if attempted.get("accepted"):
                    claim = attempted
                    break
                if attempted.get("record", {}).get("status") == OCCUPIED:
                    continue
                record = attempted.get("record", {})
                return self._terminal(
                    request_id,
                    selection_mode=selection_mode,
                    event="failed",
                    exit_code=2,
                    reason=str(record.get("reason", "원 슬롯 claim에 실패했습니다.")),
                    operator_action=(
                        f"다른 슬롯으로 전환하지 않았습니다. "
                        f"{record.get('operator_action', '원 슬롯 상태를 확인하십시오.')}"
                    ),
                    context_id=context_id,
                    parent=parent,
                    child_session_id=child_session_id,
                    emit=emit,
                )

            self._emit(
                emit,
                self._annotate_runner_record(
                    claim["record"],
                    request_id,
                    selection_mode,
                    context_id,
                    parent,
                    child_session_id,
                ),
            )
            readiness = self.runner.pre_submit_check(parent.slot_id)
            if not readiness["ready"]:
                finished = self.service.finish_job(
                    parent.slot_id,
                    request_id,
                    claim["record"]["started_at"],
                    "pre_submit_failed",
                    None,
                    readiness["reason"],
                    readiness["operator_action"],
                )
                record = self._annotate_runner_record(
                    finished["record"],
                    request_id,
                    selection_mode,
                    context_id,
                    parent,
                    child_session_id,
                )
                record.update(
                    {
                        "event": "failed",
                        "outcome": "failed",
                        "reason": (
                            "원 슬롯이 제출 직전 사용할 수 없게 되어 fallback 없이 실패했습니다: "
                            f"{readiness['reason']}"
                        ),
                        "operator_action": readiness["operator_action"],
                    }
                )
                self._emit(emit, record)
                return {"accepted": True, "exit_code": 1, "record": record}

            if self._parent_is_archived(parent):
                try:
                    self.service.cdp.restore_archived_conversation(
                        self.service.settings.slot(parent.slot_id),
                        parent.conversation.conversation_url,
                    )
                except CDPError as exc:
                    finished = self.service.finish_job(
                        parent.slot_id,
                        request_id,
                        claim["record"]["started_at"],
                        "pre_submit_failed",
                        None,
                        f"보관된 부모 ChatGPT 대화를 복원하지 못했습니다: {exc}",
                        "원 슬롯의 ChatGPT 대화를 복원한 뒤 다시 시도하십시오.",
                    )
                    record = self._annotate_runner_record(
                        finished["record"],
                        request_id,
                        selection_mode,
                        context_id,
                        parent,
                        child_session_id,
                    )
                    record.update(
                        {
                            "event": "failed",
                            "outcome": "failed",
                            "reason": (
                                "보관된 부모 ChatGPT 대화 복원 또는 composer readback에 실패해 "
                                f"stock Oracle를 시작하지 않았습니다: {exc}"
                            ),
                            "operator_action": (
                                "다른 슬롯으로 전환하지 않았습니다. 원 슬롯의 ChatGPT 대화를 "
                                "복원한 뒤 다시 시도하십시오."
                            ),
                        }
                    )
                    self._emit(emit, record)
                    return {"accepted": True, "exit_code": 1, "record": record}

            if cancellation["requested"]:
                return self._cancel_claimed(
                    request_id,
                    selection_mode,
                    context_id,
                    parent,
                    child_session_id,
                    claim,
                    cancellation["signal"],
                    emit,
                )

            def emit_runner(record: dict[str, Any]) -> None:
                self._emit(
                    emit,
                    self._annotate_runner_record(
                        record,
                        request_id,
                        selection_mode,
                        context_id,
                        parent,
                        child_session_id,
                    ),
                )

            execution_started = True
            execute_kwargs: dict[str, Any] = {
                "emit": emit_runner,
                "cancelled_outcome": "cancelled",
            }
            if prepared is not None:
                execute_kwargs["prepared"] = prepared
            child_result = self.runner.execute_claimed(
                parent.slot_id,
                request_id,
                claim["command"],
                claim,
                **execute_kwargs,
            )
            prepared = None
        except Exception as exc:
            if claim is not None and not execution_started:
                self.service.finish_job(
                    parent.slot_id,
                    request_id,
                    claim["record"]["started_at"],
                    "failed",
                    None,
                    f"follow-up 조정 중 예외가 발생했습니다: {exc}",
                    "원 슬롯 상태를 확인하십시오.",
                )
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="failed",
                exit_code=1,
                reason=f"follow-up 실행 중 예외가 발생했습니다: {exc}",
                operator_action="원 슬롯과 자식 session 메타데이터를 확인하십시오.",
                context_id=context_id,
                parent=parent,
                child_session_id=child_session_id,
                emit=emit,
                prompt_submission_may_have_occurred=execution_started,
                accepted=execution_started,
            )
        finally:
            if prepared is not None:
                prepared.cleanup()
            for signal_number, previous_handler in previous_handlers.items():
                signal.signal(signal_number, previous_handler)

        try:
            readback = self.repository.record_followup(
                child_session_id,
                parent=parent,
                selection_mode=selection_mode,
                context_id=context_id,
                request_id=request_id,
                exit_code=int(child_result["exit_code"]),
            )
        except FollowupError as exc:
            return self._terminal(
                request_id,
                selection_mode=selection_mode,
                event="failed",
                exit_code=(
                    int(child_result["exit_code"])
                    if int(child_result["exit_code"]) != 0
                    else 1
                ),
                reason=(
                    f"stock Oracle child 종료 후 lineage/readback 보장에 실패했습니다: {exc.reason} "
                    "프롬프트가 이미 제출되었을 수 있으므로 자동 재시도하지 않았습니다."
                ),
                operator_action=exc.operator_action,
                context_id=context_id,
                parent=parent,
                child_session_id=child_session_id,
                emit=emit,
                prompt_submission_may_have_occurred=True,
                accepted=True,
            )

        verification_ok = readback["verification"]["ok"] is True
        child_exit_code = int(child_result["exit_code"])
        final_exit_code = child_exit_code if child_exit_code != 0 else (0 if verification_ok else 1)
        persisted = self._record(
            request_id,
            event="session_persisted",
            outcome="success" if final_exit_code == 0 else "failed",
            selection_mode=selection_mode,
            context_id=context_id,
            parent=parent,
            child_session_id=child_session_id,
            reason=(
                "follow-up 자식 session과 authoritative readback을 확인했습니다."
                if verification_ok
                else "follow-up 자식 session은 저장했지만 검증 항목이 실패했습니다."
            ),
            operator_action=(
                "없음"
                if verification_ok
                else "authoritative_readback.verification.failures를 확인하고 자동 재시도하지 마십시오."
            ),
        )
        persisted["authoritative_readback"] = readback
        persisted["child_exit_code"] = child_exit_code
        self._emit(emit, persisted)
        return {"accepted": True, "exit_code": final_exit_code, "record": persisted}

    def _cancel_before_claim(
        self,
        request_id: str,
        selection_mode: str,
        context_id: str,
        parent: ParentSession,
        child_session_id: str,
        signal_number: int | bool | None,
        emit: LifecycleEmitter | None,
    ) -> dict[str, Any]:
        return self._terminal(
            request_id,
            selection_mode=selection_mode,
            event="cancelled",
            exit_code=130,
            reason=(
                f"원 슬롯 대기 중 호출자가 {self._signal_name(signal_number)} 신호로 "
                "follow-up을 취소했습니다."
            ),
            operator_action="없음",
            context_id=context_id,
            parent=parent,
            child_session_id=child_session_id,
            emit=emit,
        )

    def _cancel_claimed(
        self,
        request_id: str,
        selection_mode: str,
        context_id: str,
        parent: ParentSession,
        child_session_id: str,
        claim: dict[str, Any],
        signal_number: int | bool | None,
        emit: LifecycleEmitter | None,
    ) -> dict[str, Any]:
        finished = self.service.finish_job(
            parent.slot_id,
            request_id,
            claim["record"]["started_at"],
            "cancelled",
            130,
            f"Oracle 제출 전에 호출자가 {self._signal_name(signal_number)} 신호로 취소했습니다.",
            "없음",
        )
        record = self._annotate_runner_record(
            finished["record"],
            request_id,
            selection_mode,
            context_id,
            parent,
            child_session_id,
        )
        record["event"] = "cancelled"
        record["outcome"] = "cancelled"
        self._emit(emit, record)
        return {
            "accepted": True,
            "exit_code": 130 if finished["released"] else 1,
            "record": record,
        }

    def _terminal(
        self,
        request_id: str,
        *,
        selection_mode: str,
        event: str,
        exit_code: int,
        reason: str,
        operator_action: str,
        emit: LifecycleEmitter | None,
        context_id: str | None = None,
        parent: ParentSession | None = None,
        child_session_id: str | None = None,
        prompt_submission_may_have_occurred: bool = False,
        accepted: bool = False,
    ) -> dict[str, Any]:
        record = self._record(
            request_id,
            event=event,
            outcome="cancelled" if event == "cancelled" else "failed",
            selection_mode=selection_mode,
            context_id=context_id,
            parent=parent,
            child_session_id=child_session_id,
            reason=reason,
            operator_action=operator_action,
        )
        if prompt_submission_may_have_occurred:
            record["prompt_submission_may_have_occurred"] = True
        self._emit(emit, record)
        return {"accepted": accepted, "exit_code": exit_code, "record": record}

    @staticmethod
    def _record(
        request_id: str,
        *,
        event: str,
        outcome: str,
        selection_mode: str,
        context_id: str | None,
        parent: ParentSession | None,
        child_session_id: str | None,
        reason: str,
        operator_action: str,
    ) -> dict[str, Any]:
        return {
            "operation": "followup",
            "event": event,
            "outcome": outcome,
            "request_id": request_id,
            "job_id": request_id,
            "selection_mode": selection_mode,
            "opencode_conversation_id": context_id,
            "parent_session_id": parent.session_id if parent is not None else None,
            "child_session_id": child_session_id,
            "slot_id": parent.slot_id if parent is not None else None,
            "assigned_slot": parent.slot_id if parent is not None else None,
            "attempted_slots": [parent.slot_id] if parent is not None else [],
            "conversation_id": (
                parent.conversation.conversation_id if parent is not None else None
            ),
            "conversation_url": (
                parent.conversation.conversation_url if parent is not None else None
            ),
            "reason": reason,
            "operator_action": operator_action,
            "recorded_at": utc_now(),
        }

    def _annotate_runner_record(
        self,
        source: dict[str, Any],
        request_id: str,
        selection_mode: str,
        context_id: str,
        parent: ParentSession,
        child_session_id: str,
    ) -> dict[str, Any]:
        record = dict(source)
        record.update(
            {
                "operation": "followup",
                "request_id": request_id,
                "selection_mode": selection_mode,
                "opencode_conversation_id": context_id,
                "parent_session_id": parent.session_id,
                "child_session_id": child_session_id,
                "slot_id": parent.slot_id,
                "assigned_slot": parent.slot_id,
                "attempted_slots": [parent.slot_id],
                "conversation_id": parent.conversation.conversation_id,
                "conversation_url": parent.conversation.conversation_url,
            }
        )
        return record

    @staticmethod
    def _parent_is_archived(parent: ParentSession) -> bool:
        browser = parent.metadata.get("browser")
        archive = browser.get("archive") if isinstance(browser, dict) else None
        return isinstance(archive, dict) and archive.get("archived") is True

    @staticmethod
    def _emit(emitter: LifecycleEmitter | None, record: dict[str, Any]) -> None:
        if emitter is not None:
            emitter(record)

    @staticmethod
    def _cancel_signals() -> tuple[int, ...]:
        signals = (signal.SIGINT, signal.SIGTERM)
        sighup = getattr(signal, "SIGHUP", None)
        if sighup is not None:
            signals += (sighup,)
        return signals

    @staticmethod
    def _signal_name(signal_number: int | bool | None) -> str:
        if not isinstance(signal_number, int) or isinstance(signal_number, bool):
            return "취소"
        try:
            return signal.Signals(signal_number).name
        except ValueError:
            return f"signal {signal_number}"
