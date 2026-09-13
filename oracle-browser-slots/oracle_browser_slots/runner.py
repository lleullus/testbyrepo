"""argv-preserving child execution around the atomic slot lifecycle."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
from typing import Any, Callable, Sequence

from .attachments import (
    AttachmentPreparationError,
    AttachmentPreparationInterrupted,
    FileAttachmentPolicy,
    PreparedAttachment,
)
from .cdp import CDPError
from .model import validate_chatgpt_url
from .service import SlotService


LifecycleEmitter = Callable[[dict[str, Any]], None]
CANONICAL_ORACLE_CLI = "/home/user01/.nvm/versions/node/v24.18.0/bin/oracle"
REQUIRED_ORACLE_FLAGS = (("--engine", "browser"),)
MODEL_STRATEGY_FLAG = "--browser-model-strategy"
URL_ALIAS_FLAGS = ("--chatgpt-url", "--browser-url")
FORBIDDEN_TRANSPORT_FLAGS = (
    "--browser-manual-login",
    "--browser-chrome-path",
    "--browser-keep-browser",
    "--remote-host",
    "--bridge",
)
MODEL_FLAGS = ("--model", "-m", "--models")
REASONING_FLAG = "--browser-thinking-time"


class _RunInterrupted(Exception):
    def __init__(self, signal_number: int) -> None:
        super().__init__(signal_number)
        self.signal_number = signal_number


class JobRunner:
    def __init__(
        self,
        service: SlotService,
        *,
        popen_factory: Callable[..., Any] = subprocess.Popen,
        oracle_cli_path: str | None = None,
        attachment_policy: FileAttachmentPolicy | None = None,
    ) -> None:
        self.service = service
        self.popen_factory = popen_factory
        self.oracle_cli_path = oracle_cli_path or os.environ.get(
            "ORACLE_BROWSER_SLOTS_ORACLE_CLI", CANONICAL_ORACLE_CLI
        )
        self.attachment_policy = attachment_policy or FileAttachmentPolicy()

    def run(
        self,
        slot_id: int,
        job_id: str,
        argv: Sequence[str],
        *,
        emit: LifecycleEmitter | None = None,
    ) -> dict[str, Any]:
        command = list(argv)
        if not command:
            raise ValueError("실행할 command가 없습니다.")

        try:
            self.assert_slot_compatible(slot_id, command)
            command = self._validated_oracle_command(slot_id, command)
        except OracleTransportError as exc:
            record = self.service.run_rejection(
                slot_id,
                job_id,
                exc.reason,
                exc.operator_action,
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 2, "record": record}

        prepared: PreparedAttachment | None = None
        try:
            command, prepared = self.prepare_file_request(command, job_id)
        except AttachmentPreparationInterrupted as exc:
            signal_name = signal.Signals(exc.signal_number).name
            record = self.service.run_rejection(
                slot_id,
                job_id,
                f"파일 선택과 ZIP 준비가 {signal_name} 신호로 중단되었습니다.",
                "중단 원인과 파일 선택 경로를 확인한 뒤 다시 실행하십시오.",
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 130, "record": record}
        except KeyboardInterrupt:
            record = self.service.run_rejection(
                slot_id,
                job_id,
                "파일 선택과 ZIP 준비가 운영자 중단으로 종료되었습니다.",
                "중단 원인과 파일 선택 경로를 확인한 뒤 다시 실행하십시오.",
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 130, "record": record}
        except AttachmentPreparationError as exc:
            record = self.service.run_rejection(
                slot_id,
                job_id,
                exc.reason,
                exc.operator_action,
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 2, "record": record}

        if prepared is not None:
            try:
                self._emit(
                    emit,
                    self.attachment_prepared_record(
                        prepared,
                        operation="run",
                        request_id=job_id,
                        slot_id=slot_id,
                    ),
                )
            except BaseException:
                prepared.cleanup()
                raise

        try:
            claim = self.service.claim_job(slot_id, job_id)
        except BaseException:
            if prepared is not None:
                prepared.cleanup()
            raise
        try:
            self._emit(emit, claim["record"])
        except BaseException:
            if prepared is not None:
                prepared.cleanup()
            raise
        if not claim["accepted"]:
            if prepared is not None:
                prepared.cleanup()
            return {"accepted": False, "exit_code": 2, "record": claim["record"]}

        if prepared is None:
            return self.execute_claimed(
                slot_id,
                job_id,
                command,
                claim,
                emit=emit,
            )
        return self.execute_claimed(
            slot_id,
            job_id,
            command,
            claim,
            prepared=prepared,
            emit=emit,
        )

    def validate_auto_command(self, argv: Sequence[str]) -> list[str]:
        """Validate transport-independent argv for the slot-free submit command."""

        command = list(argv)
        if not command:
            raise ValueError("실행할 command가 없습니다.")
        return self._validated_oracle_command(None, command)

    @classmethod
    def _parse_model_request(
        cls, argv: Sequence[str]
    ) -> tuple[str, str | None, bool] | None:
        """Parse the single model/reasoning request used by routing and transport."""

        model_occurrences = cls._option_occurrences(argv, MODEL_FLAGS)
        reasoning_occurrences = cls._option_occurrences(argv, (REASONING_FLAG,))
        if (
            len(model_occurrences) > 1
            or len(reasoning_occurrences) > 1
            or any(flag == "--models" for flag, _, _ in model_occurrences)
        ):
            return None

        if model_occurrences:
            model_flag, model, model_form = model_occurrences[0]
            if model is None or not model.strip() or (
                model_flag == "-m" and model_form == "equals"
            ):
                return None
            normalized_model = model.strip().lower()
            explicit_model = True
        else:
            normalized_model = "gpt-5.6-sol"
            explicit_model = False

        if reasoning_occurrences:
            _, reasoning, _ = reasoning_occurrences[0]
            if reasoning is None or not reasoning.strip():
                return None
            normalized_reasoning = (
                reasoning.strip().lower().replace("_", "-").replace(" ", "-")
            )
            if normalized_reasoning not in (
                "heavy",
                "extra-high",
                "extrahigh",
                "xhigh",
                "pro",
                "extended",
                "high",
                "light",
                "instant",
                "low",
                "standard",
                "medium",
            ):
                return None
        else:
            normalized_reasoning = None

        return normalized_model, normalized_reasoning, explicit_model

    @classmethod
    def _expected_model_strategy(cls, argv: Sequence[str]) -> str:
        """Choose exact-row selection only for the Ticket-owned Pro requests."""

        parsed = cls._parse_model_request(argv)
        if parsed is None:
            return "current"
        model, reasoning, explicit_model = parsed
        if not explicit_model:
            return "current"
        if model == "gpt-6-pro" or (
            reasoning == "pro" and model in ("gpt-5.6-sol", "gpt-5.5")
        ):
            return "select"
        return "current"

    def compatible_slots(self, argv: Sequence[str]) -> tuple[int, ...]:
        """Return slots with an approved capability for the canonical request."""

        parsed = self._parse_model_request(argv)
        if parsed is None:
            return ()
        normalized_model, normalized_reasoning, _ = parsed

        if normalized_model not in (
            "gpt-5.5",
            "gpt-5.6",
            "gpt-5.6-sol",
            "gpt-6",
            "gpt-6-pro",
        ):
            return ()
        if normalized_model == "gpt-6-pro" or normalized_reasoning in (
            "heavy",
            "extra-high",
            "extrahigh",
            "xhigh",
            "pro",
            "light",
            "instant",
            "low",
        ):
            return (1, 2, 10)
        if normalized_reasoning in ("extended", "high"):
            return (3, 4, 5, 1, 2, 10)
        return (1, 2, 3, 4, 5, 10)

    def assert_slot_compatible(self, slot_id: int, argv: Sequence[str]) -> None:
        if slot_id in self.compatible_slots(argv):
            return
        raise OracleTransportError(
            f"슬롯 {slot_id}은 요청된 model/reasoning 조합과 호환되지 않습니다.",
            "요청 수준을 변경하지 말고 해당 조합을 지원하는 managed slot을 사용하십시오.",
        )

    def prepare_file_request(
        self,
        argv: Sequence[str],
        request_id: str,
    ) -> tuple[list[str], PreparedAttachment | None]:
        """Prepare file-bearing argv before a slot claim; leave file-free argv unchanged."""

        prepared = self.attachment_policy.prepare(argv, request_id)
        if prepared is None:
            return list(argv), None
        return prepared.command, prepared

    @staticmethod
    def attachment_prepared_record(
        prepared: PreparedAttachment,
        *,
        operation: str,
        request_id: str,
        slot_id: int | None = None,
    ) -> dict[str, Any]:
        """Describe one prepared ZIP without treating it as upload evidence."""

        record: dict[str, Any] = {
            "operation": operation,
            "event": "attachment_prepared",
            "outcome": "prepared",
            "request_id": request_id,
            "job_id": request_id,
            "slot_id": slot_id,
            "assigned_slot": slot_id,
            "selected_file_count": len(prepared.selected_files),
            "selected_file_bytes": sum(
                selected.size_bytes for selected in prepared.selected_files
            ),
            "generated_zip": {
                "name": prepared.zip_name,
                "size_bytes": prepared.zip_size_bytes,
                "sha256": prepared.zip_sha256,
            },
            "requires_session_manifest": prepared.requires_session_manifest,
        }
        if prepared.include_file_report:
            record["selected_files"] = [
                {
                    "relative_path": selected.relative_path,
                    "size_bytes": selected.size_bytes,
                }
                for selected in prepared.selected_files
            ]
        return record

    def claim_for_auto(
        self,
        slot_id: int,
        request_id: str,
        argv: Sequence[str],
        *,
        apply_workspace_mapping: bool = True,
    ) -> dict[str, Any]:
        """Validate for one selected slot and atomically claim it without Popen."""

        command = list(argv)
        try:
            self.assert_slot_compatible(slot_id, command)
            command = self._validated_oracle_command(
                slot_id,
                command,
                apply_workspace_mapping=apply_workspace_mapping,
            )
        except OracleTransportError as exc:
            record = self.service.run_rejection(
                slot_id,
                request_id,
                exc.reason,
                exc.operator_action,
            )
            return {
                "accepted": False,
                "exit_code": 2,
                "record": record,
                "command": command,
            }

        claim = self.service.claim_job(slot_id, request_id)
        claim["command"] = command
        return claim

    def pre_submit_check(self, slot_id: int) -> dict[str, Any]:
        """Recheck CDP/login after claim and before the irreversible child call."""

        slot = self.service.settings.slot(slot_id)
        try:
            login = self.service.cdp.check_login(slot)
        except CDPError as exc:
            return {
                "ready": False,
                "reason": str(exc),
                "operator_action": (
                    f"슬롯 {slot_id}의 Chrome/CDP 상태를 확인한 뒤 prepare --slot "
                    f"{slot_id}을 다시 실행하십시오."
                ),
            }
        except Exception as exc:
            return {
                "ready": False,
                "reason": f"슬롯 {slot_id} 제출 전 CDP/login 확인 중 예외가 발생했습니다: {exc}",
                "operator_action": (
                    f"슬롯 {slot_id}의 Chrome/CDP 상태와 로그를 확인한 뒤 prepare --slot "
                    f"{slot_id}을 다시 실행하십시오."
                ),
            }
        if not login.valid:
            return {
                "ready": False,
                "reason": login.reason,
                "operator_action": login.operator_action,
            }
        return {"ready": True, "reason": login.reason, "operator_action": "없음"}

    def execute_claimed(
        self,
        slot_id: int,
        job_id: str,
        command: Sequence[str],
        claim: dict[str, Any],
        *,
        prepared: PreparedAttachment | None = None,
        emit: LifecycleEmitter | None = None,
        cancelled_outcome: str = "interrupted",
    ) -> dict[str, Any]:
        """Run exactly one already-claimed child and finish that same claim."""

        claim_record = claim["record"]
        started_at = claim_record["started_at"]
        environment = os.environ.copy()
        environment.update(claim["environment"])

        child: Any = None
        outcome = "success"
        exit_code: int | None = None
        reason = "작업이 정상 종료되었습니다."
        operator_action = "없음"
        previous_handlers: dict[int, Any] = {}
        install_handlers = threading.current_thread() is threading.main_thread()

        def interrupt_handler(signal_number: int, _frame: Any) -> None:
            raise _RunInterrupted(signal_number)

        try:
            if install_handlers:
                for signal_number in self._interrupt_signals():
                    previous_handlers[signal_number] = signal.getsignal(signal_number)
                    signal.signal(signal_number, interrupt_handler)
            child = self.popen_factory(command, env=environment, close_fds=True)
            try:
                exit_code = int(child.wait())
            except (KeyboardInterrupt, _RunInterrupted) as exc:
                outcome = cancelled_outcome
                exit_code = self._interrupt_child(child)
                if isinstance(exc, _RunInterrupted):
                    signal_name = signal.Signals(exc.signal_number).name
                    reason = f"작업이 {signal_name} 신호로 중단되었습니다."
                else:
                    reason = "작업이 운영자 중단으로 종료되었습니다."
                operator_action = "작업 중단 원인과 child 로그를 확인하십시오."
            else:
                if exit_code == 0:
                    outcome = "success"
                    reason = "작업이 정상 종료되었습니다."
                else:
                    outcome = "failed"
                    reason = f"작업이 비제로 종료되었습니다 (exit code {exit_code})."
                    operator_action = "작업 로그와 종료 코드를 확인하십시오."
        except (OSError, ValueError) as exc:
            if child is None:
                outcome = "spawn_error"
                exit_code = 127
                reason = f"작업 child를 시작하지 못했습니다: {exc}"
                operator_action = "command 경로와 실행 권한을 확인하십시오."
            else:
                outcome = "failed"
                exit_code = 1
                reason = f"작업 child 종료 결과를 확인하지 못했습니다: {exc}"
                operator_action = "child 상태와 로그를 확인하십시오."
                self._cleanup_child(child)
        except _RunInterrupted as exc:
            outcome = cancelled_outcome
            exit_code = self._interrupt_child(child) if child is not None else 130
            signal_name = signal.Signals(exc.signal_number).name
            reason = f"작업이 {signal_name} 신호로 중단되었습니다."
            operator_action = "작업 중단 원인과 child 로그를 확인하십시오."
        except Exception as exc:
            if child is None:
                outcome = "spawn_error"
                exit_code = 127
                reason = f"작업 child를 시작하는 중 예외가 발생했습니다: {exc}"
                operator_action = "command 경로와 실행 권한을 확인하십시오."
            else:
                outcome = "failed"
                exit_code = 1
                reason = f"작업 child 실행 중 예외가 발생했습니다: {exc}"
                operator_action = "child 상태와 로그를 확인하십시오."
                self._cleanup_child(child)
        finally:
            for signal_number, previous_handler in previous_handlers.items():
                signal.signal(signal_number, previous_handler)

        manifest_result: dict[str, Any] | None = None
        cleanup_result: dict[str, Any] | None = None
        post_child_failures: list[str] = []
        submission_may_have_occurred = child is not None
        if prepared is not None:
            submission_may_have_occurred = (
                child is not None and prepared.requires_session_manifest
            )
            try:
                cleanup_result = prepared.cleanup()
                if not isinstance(cleanup_result, dict):
                    cleanup_result = {
                        "removed": False,
                        "error": "generated ZIP cleanup 결과 형식이 올바르지 않습니다",
                    }
            except Exception as exc:
                cleanup_result = {
                    "removed": False,
                    "error": f"generated ZIP cleanup 중 예외가 발생했습니다: {exc}",
                }
            if cleanup_result.get("removed") is not True:
                detail = cleanup_result.get("error", "cleanup 결과가 확인되지 않았습니다")
                post_child_failures.append(f"generated ZIP cleanup 실패: {detail}")

            manifest_outcome = outcome
            manifest_exit_code = exit_code
            if child is not None and outcome == "success" and cleanup_result.get("removed") is not True:
                manifest_outcome = "failed"
                manifest_exit_code = 1
            try:
                manifest_result = prepared.write_manifest(
                    child_started=child is not None,
                    outcome=manifest_outcome,
                    exit_code=manifest_exit_code,
                    cleanup_result=cleanup_result,
                )
            except Exception as exc:
                manifest_result = {
                    "written": False,
                    "error": f"manifest 기록 중 예외가 발생했습니다: {exc}",
                }
            if (
                child is not None
                and prepared.requires_session_manifest
                and manifest_result is None
            ):
                manifest_result = {
                    "written": False,
                    "error": "stock Oracle session/artifact surface에서 manifest를 찾지 못했습니다.",
                }
            if (
                child is not None
                and prepared.requires_session_manifest
                and (
                    not isinstance(manifest_result, dict)
                    or manifest_result.get("written") is not True
                )
            ):
                detail = (
                    manifest_result.get("error", "manifest 기록 결과가 확인되지 않았습니다")
                    if isinstance(manifest_result, dict)
                    else "manifest 기록 결과 형식이 올바르지 않습니다"
                )
                post_child_failures.append(f"manifest 기록 실패: {detail}")

            if post_child_failures:
                child_outcome = outcome
                child_exit_code = exit_code
                if child is not None and outcome == "success":
                    outcome = "failed"
                    exit_code = 1
                reason = (
                    f"{reason} post-child attachment 보장에 실패했습니다: "
                    f"{'; '.join(post_child_failures)}."
                )
                if submission_may_have_occurred:
                    reason = (
                        f"{reason} 프롬프트가 이미 제출되었을 수 있으므로 자동 재시도하지 않았습니다."
                    )
                    operator_action = (
                        "manifest와 generated ZIP cleanup 상태를 확인하십시오. "
                        "프롬프트가 이미 제출되었을 수 있으므로 Oracle 요청을 재실행하지 마십시오."
                    )
                else:
                    operator_action = "generated ZIP cleanup 상태를 확인하십시오."
            else:
                child_outcome = None
                child_exit_code = None
        else:
            child_outcome = None
            child_exit_code = None

        finished = self.service.finish_job(
            slot_id,
            job_id,
            started_at,
            outcome,
            exit_code,
            reason,
            operator_action,
        )
        final_record = finished["record"]
        if manifest_result is not None:
            final_record["attachment_manifest"] = manifest_result
        if cleanup_result is not None:
            final_record["generated_zip_cleanup"] = cleanup_result
        if post_child_failures:
            final_record["post_child_failures"] = post_child_failures
            if submission_may_have_occurred:
                final_record["prompt_submission_may_have_occurred"] = True
            final_record["child_outcome"] = child_outcome
            final_record["child_exit_code"] = child_exit_code
        self._emit(emit, final_record)
        if not finished["released"]:
            return {
                "accepted": True,
                "exit_code": 1,
                "record": final_record,
                "child_started": child is not None,
            }
        return {
            "accepted": True,
            "exit_code": self._shell_exit_code(exit_code),
            "record": final_record,
            "child_started": child is not None,
        }

    def _validated_oracle_command(
        self,
        slot_id: int | None,
        argv: list[str],
        *,
        apply_workspace_mapping: bool = True,
    ) -> list[str]:
        expected_executable = self.oracle_cli_path
        if not os.path.isabs(expected_executable) or argv[0] != expected_executable:
            raise OracleTransportError(
                "public Oracle 요청은 canonical stock Oracle CLI만 실행할 수 있습니다.",
                f"{expected_executable}를 argv[0]으로 지정하고 shell/env wrapper 없이 다시 실행하십시오.",
            )

        expected_remote: str | None = None
        if slot_id is not None:
            slot = self.service.settings.slot(slot_id)
            expected_remote = f"127.0.0.1:{slot.port}"
        for token in argv[1:]:
            if any(
                token == flag or token.startswith(f"{flag}=")
                for flag in FORBIDDEN_TRANSPORT_FLAGS
            ):
                raise OracleTransportError(
                    f"Oracle 요청에 stock Oracle 외부 transport 옵션이 포함되어 있습니다: {token}",
                    "browser-manual-login, browser-chrome-path, browser-keep-browser, remote-host, bridge를 제거하십시오.",
                )

        caller_url = self._caller_chatgpt_url(argv)
        injection: str | None = None
        if (
            apply_workspace_mapping
            and caller_url is None
            and slot_id is not None
        ):
            injection = self.service.settings.slot_chatgpt_url_override(slot_id)

        values: dict[str, list[str]] = {
            flag: [] for flag, _ in REQUIRED_ORACLE_FLAGS
        }
        values[MODEL_STRATEGY_FLAG] = []
        values["--remote-chrome"] = []
        required_values = dict(REQUIRED_ORACLE_FLAGS)
        required_values[MODEL_STRATEGY_FLAG] = self._expected_model_strategy(argv)
        if expected_remote is not None:
            required_values["--remote-chrome"] = expected_remote
        index = 1
        while index < len(argv):
            token = argv[index]
            flag = None
            value: str | None = None
            if token in values:
                flag = token
                if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
                    raise OracleTransportError(
                        f"{token} 값이 없습니다.",
                        f"{token}에 명시적 값을 지정하십시오.",
                    )
                value = argv[index + 1]
                index += 1
            else:
                for candidate in values:
                    prefix = f"{candidate}="
                    if token.startswith(prefix):
                        flag = candidate
                        value = token[len(prefix) :]
                        break
            if flag is not None:
                values[flag].append(value or "")
            index += 1

        for flag, expected in required_values.items():
            occurrences = values[flag]
            if len(occurrences) > 1:
                raise OracleTransportError(
                    f"{flag}가 중복 지정되었습니다.",
                    f"{flag}를 한 번만 지정하십시오.",
                )
            if (
                occurrences
                and occurrences[0] != expected
                and not (flag == MODEL_STRATEGY_FLAG and expected == "current")
            ):
                raise OracleTransportError(
                    (
                        f"{flag} 값이 선택 슬롯과 충돌합니다: {occurrences[0]}"
                        if expected_remote is not None
                        else f"{flag} 값이 stock Oracle 요구값과 충돌합니다: {occurrences[0]}"
                    ),
                    f"{flag}를 {expected}로 지정하십시오.",
                )

        if expected_remote is None and values["--remote-chrome"]:
            raise OracleTransportError(
                "submit은 --remote-chrome를 직접 받을 수 없습니다.",
                "submit argv에서 --remote-chrome를 제거하면 자동 배정 슬롯 endpoint가 주입됩니다.",
            )

        normalized = list(argv)
        for flag, expected in required_values.items():
            if not values[flag]:
                normalized = self._insert_before_terminator(
                    normalized, (flag, expected)
                )
        if injection is not None:
            normalized = self._insert_before_terminator(
                normalized, ("--chatgpt-url", injection)
            )
        return normalized

    @staticmethod
    def _option_occurrences(
        argv: Sequence[str], flags: Sequence[str]
    ) -> list[tuple[str, str | None, str]]:
        occurrences: list[tuple[str, str | None, str]] = []
        index = 1
        while index < len(argv):
            token = argv[index]
            if token == "--":
                break
            if token in flags:
                value = None
                if index + 1 < len(argv) and not argv[index + 1].startswith("-"):
                    value = argv[index + 1]
                    index += 1
                occurrences.append((token, value, "separated"))
            else:
                for flag in flags:
                    prefix = f"{flag}="
                    if token.startswith(prefix):
                        occurrences.append((flag, token[len(prefix) :], "equals"))
                        break
            index += 1
        return occurrences

    @staticmethod
    def _option_values(argv: Sequence[str], flags: Sequence[str]) -> list[str]:
        values: list[str] = []
        index = 1
        while index < len(argv):
            token = argv[index]
            if token == "--":
                break
            if token in flags:
                if index + 1 < len(argv) and not argv[index + 1].startswith("--"):
                    values.append(argv[index + 1])
                    index += 1
            else:
                for flag in flags:
                    prefix = f"{flag}="
                    if token.startswith(prefix):
                        values.append(token[len(prefix) :])
                        break
            index += 1
        return values

    @staticmethod
    def _caller_chatgpt_url(argv: list[str]) -> str | None:
        """Validate caller URL aliases before the first standalone `--`."""

        seen: dict[str, str] = {}
        caller_url: str | None = None
        index = 1
        while index < len(argv):
            token = argv[index]
            if token == "--":
                break
            flag: str | None = None
            value: str | None = None
            if token in URL_ALIAS_FLAGS:
                flag = token
                if (
                    index + 1 >= len(argv)
                    or argv[index + 1].startswith("-")
                ):
                    raise OracleTransportError(
                        f"{token} 값이 없습니다.",
                        f"{token}에 https URL을 지정하십시오.",
                    )
                value = argv[index + 1]
                index += 1
            else:
                for candidate in URL_ALIAS_FLAGS:
                    prefix = f"{candidate}="
                    if token.startswith(prefix):
                        flag = candidate
                        value = token[len(prefix) :]
                        break
            if flag is not None:
                if not value or value.startswith("-"):
                    raise OracleTransportError(
                        f"{flag} 값이 비어 있거나 옵션으로 해석될 수 있습니다.",
                        f"{flag}에 https URL을 지정하십시오.",
                    )
                try:
                    validate_chatgpt_url(value, flag)
                except ValueError as exc:
                    raise OracleTransportError(
                        str(exc),
                        f"{flag}에 https://chatgpt.com 또는 "
                        "https://chat.openai.com URL을 지정하십시오.",
                    ) from exc
                if flag in seen:
                    raise OracleTransportError(
                        f"{flag}가 중복 지정되었습니다.",
                        f"{flag}를 한 번만 지정하십시오.",
                    )
                seen[flag] = value
                if len(seen) > 1:
                    raise OracleTransportError(
                        "--chatgpt-url과 --browser-url을 함께 지정할 수 없습니다.",
                        "URL alias는 둘 중 하나만 지정하십시오.",
                    )
                caller_url = value
            index += 1
        return caller_url

    @staticmethod
    def _insert_before_terminator(
        normalized: list[str], pair: Sequence[str]
    ) -> list[str]:
        """Insert injected options before the first standalone `--`."""

        try:
            terminator = normalized.index("--")
        except ValueError:
            normalized.extend(pair)
        else:
            normalized[terminator:terminator] = list(pair)
        return normalized

    @staticmethod
    def _emit(emitter: LifecycleEmitter | None, record: dict[str, Any]) -> None:
        if emitter is not None:
            emitter(record)

    @staticmethod
    def _shell_exit_code(exit_code: int | None) -> int:
        if exit_code is None:
            return 1
        if exit_code < 0:
            return min(255, 128 + abs(exit_code))
        return min(255, exit_code)

    @staticmethod
    def _interrupt_child(child: Any) -> int:
        try:
            child.terminate()
        except Exception:
            return 130
        try:
            return int(child.wait(timeout=2))
        except Exception:
            try:
                child.kill()
            except Exception:
                return 130
            try:
                return int(child.wait())
            except Exception:
                return 130

    @staticmethod
    def _cleanup_child(child: Any) -> None:
        try:
            JobRunner._interrupt_child(child)
        except Exception:
            pass

    @staticmethod
    def _interrupt_signals() -> tuple[int, ...]:
        signals = (signal.SIGINT, signal.SIGTERM)
        sighup = getattr(signal, "SIGHUP", None)
        if sighup is not None:
            signals += (sighup,)
        return signals


class OracleTransportError(Exception):
    def __init__(self, reason: str, operator_action: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.operator_action = operator_action
