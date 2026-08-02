"""Automatic slot allocation, FIFO waiting, and request lifecycle output."""

from __future__ import annotations

from dataclasses import dataclass
import signal
import threading
import time
from typing import Any, Sequence

from .attachments import (
    AttachmentPreparationError,
    AttachmentPreparationInterrupted,
    PreparedAttachment,
)
from .coordination import CoordinationError, QueueCoordinator
from .model import AVAILABLE, OCCUPIED, SLOT_IDS, utc_now
from .runner import JobRunner, LifecycleEmitter, OracleTransportError
from .service import SlotService, current_process_identity


class _SubmitCancelled(Exception):
    def __init__(self, signal_number: int | None = None) -> None:
        super().__init__(signal_number)
        self.signal_number = signal_number


@dataclass
class _Assignment:
    slot_id: int
    command: list[str]
    claim: dict[str, Any]
    prepared: PreparedAttachment | None
    attempted_slots: list[int]
    reassignment_reasons: list[str]
    queue_position: int | None
    queued_at: str | None


class AutoAllocator:
    """Coordinate one slot-free request until it finishes or is cancelled."""

    def __init__(
        self,
        service: SlotService,
        *,
        runner: JobRunner | None = None,
        coordinator: QueueCoordinator | None = None,
        poll_interval: float | None = None,
    ) -> None:
        self.service = service
        self.runner = runner or JobRunner(service)
        self.coordinator = coordinator or QueueCoordinator(service.settings.state_root)
        self.poll_interval = poll_interval or service.settings.queue_poll_interval

    def submit(
        self,
        request_id: str,
        argv: Sequence[str],
        *,
        emit: LifecycleEmitter | None = None,
    ) -> dict[str, Any]:
        command = list(argv)
        if not isinstance(request_id, str) or not request_id:
            record = self._request_record(
                request_id,
                event="rejected",
                outcome="rejected",
                reason="request ID가 비어 있습니다.",
                operator_action="비어 있지 않은 --request-id를 지정하십시오.",
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 2, "record": record}

        try:
            normalized_command = self.runner.validate_auto_command(command)
        except ValueError as exc:
            record = self._request_record(
                request_id,
                event="rejected",
                outcome="rejected",
                reason=str(exc),
                operator_action="canonical stock Oracle argv를 지정하십시오.",
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 2, "record": record}
        except OracleTransportError as exc:
            record = self._request_record(
                request_id,
                event="rejected",
                outcome="rejected",
                reason=exc.reason,
                operator_action=exc.operator_action,
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 2, "record": record}

        prepared: PreparedAttachment | None = None
        try:
            normalized_command, prepared = self.runner.prepare_file_request(
                normalized_command,
                request_id,
            )
        except AttachmentPreparationInterrupted as exc:
            signal_name = self._signal_name(exc.signal_number)
            record = self._request_record(
                request_id,
                event="cancelled",
                outcome="cancelled",
                reason=f"파일 선택과 ZIP 준비가 {signal_name} 신호로 중단되었습니다.",
                operator_action="중단 원인과 파일 선택 경로를 확인한 뒤 다시 실행하십시오.",
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 130, "record": record}
        except KeyboardInterrupt:
            record = self._request_record(
                request_id,
                event="cancelled",
                outcome="cancelled",
                reason="파일 선택과 ZIP 준비가 운영자 중단으로 종료되었습니다.",
                operator_action="중단 원인과 파일 선택 경로를 확인한 뒤 다시 실행하십시오.",
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 130, "record": record}
        except AttachmentPreparationError as exc:
            record = self._request_record(
                request_id,
                event="failed",
                outcome="failed",
                reason=exc.reason,
                operator_action=exc.operator_action,
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 2, "record": record}

        identity = current_process_identity()
        if identity is None:
            if prepared is not None:
                prepared.cleanup()
            record = self._request_record(
                request_id,
                event="failed",
                outcome="failed",
                reason="현재 submit process의 Linux process starttime을 확인할 수 없습니다.",
                operator_action="/proc 상태를 확인한 뒤 submit을 다시 실행하십시오.",
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 1, "record": record}

        state: dict[str, Any] = {
            "entry": None,
            "assignment": None,
            "execution_started": False,
            "attempted_slots": [],
            "reassignment_reasons": [],
            "queued_at": None,
            "queue_position": None,
            "cancel_requested": False,
            "cancel_signal": None,
            "prepared": prepared,
        }
        previous_handlers: dict[int, Any] = {}
        install_handlers = threading.current_thread() is threading.main_thread()

        def cancel_handler(signal_number: int, _frame: Any) -> None:
            # Defer queue mutation until the current lock/I/O operation has
            # returned.  Raising from a JSON/file-lock operation can strand a
            # live waiter in an interrupted stdio or flock call.
            state["cancel_requested"] = True
            state["cancel_signal"] = signal_number

        try:
            if install_handlers:
                for signal_number in self._cancel_signals():
                    previous_handlers[signal_number] = signal.getsignal(signal_number)
                    signal.signal(signal_number, cancel_handler)

            result = self._allocate_or_queue(
                request_id,
                normalized_command,
                identity,
                state,
                emit,
            )
            self._raise_if_cancelled(state)
            if result["kind"] == "queued":
                result = self._wait_for_turn(
                    request_id,
                    normalized_command,
                    identity,
                    state,
                    emit,
                )

            if result["kind"] == "terminal":
                return result["result"]

            assignment = result["assignment"]
            self._raise_if_cancelled(state)
            return self._execute_assignment(request_id, assignment, state, emit)
        except _SubmitCancelled as exc:
            return self._cancel_pending(request_id, state, identity, exc, emit)
        except Exception as exc:
            return self._handle_unexpected(request_id, state, identity, exc, emit)
        finally:
            if state["entry"] is not None:
                self._remove_entry_safely(request_id, identity, state)
            if state.get("prepared") is not None:
                state["prepared"].cleanup()
                state["prepared"] = None
            for signal_number, previous_handler in previous_handlers.items():
                signal.signal(signal_number, previous_handler)

    def _allocate_or_queue(
        self,
        request_id: str,
        command: list[str],
        identity: tuple[int, str],
        state: dict[str, Any],
        emit: LifecycleEmitter | None,
    ) -> dict[str, Any]:
        with self.coordinator.locked() as coordinator:
            entries = coordinator.load_unlocked()
            queued_duplicate = self._queued_duplicate(entries, request_id)
            if queued_duplicate is not None:
                result = self._duplicate_result(
                    request_id,
                    queue_position=queued_duplicate[0],
                    assigned_slot=None,
                    reason=(
                        f"동일 request ID가 FIFO queue {queued_duplicate[0]}번에서 이미 대기 중입니다."
                    ),
                    operator_action=(
                        "기존 요청이 완료되거나 취소된 뒤 새 lifecycle을 시작하십시오."
                    ),
                )
                self._emit(emit, result["record"])
                return {"kind": "terminal", "result": result}

            active_duplicate = self._active_duplicate_locked(request_id)
            if active_duplicate is not None:
                result = self._duplicate_result(
                    request_id,
                    queue_position=None,
                    assigned_slot=active_duplicate["slot_id"],
                    reason=(
                        f"동일 request ID가 슬롯 {active_duplicate['slot_id']}에서 이미 claim/실행 중입니다."
                    ),
                    operator_action=(
                        f"기존 슬롯 {active_duplicate['slot_id']} 작업의 완료와 finish를 확인한 뒤 submit하십시오."
                    ),
                )
                self._emit(emit, result["record"])
                return {"kind": "terminal", "result": result}

            if entries:
                self._enqueue_locked(request_id, identity, state, coordinator, emit)
                return {"kind": "queued"}

            attempt = self._try_assign_locked(
                request_id,
                command,
                state,
                queue_position=None,
                queued_at=None,
                emit=emit,
            )
            if attempt["terminal"] is not None:
                return {"kind": "terminal", "result": attempt["terminal"]}
            if attempt["assignment"] is not None:
                return {"kind": "assignment", "assignment": attempt["assignment"]}

            diagnostics = self._diagnostics()
            if self._should_wait(diagnostics, state["attempted_slots"]):
                self._enqueue_locked(request_id, identity, state, coordinator, emit)
                return {"kind": "queued"}
            result = self._no_slot_result(
                request_id,
                diagnostics,
                state["attempted_slots"],
                reassignment_reasons=state["reassignment_reasons"],
                reason="현재 배정할 수 있는 슬롯이 없습니다.",
                operator_action="슬롯별 원인과 operator_action을 확인한 뒤 prepare 또는 상태 복구를 수행하십시오.",
            )
            self._emit(emit, result["record"])
            return {
                "kind": "terminal",
                "result": result,
            }

    def _wait_for_turn(
        self,
        request_id: str,
        command: list[str],
        identity: tuple[int, str],
        state: dict[str, Any],
        emit: LifecycleEmitter | None,
    ) -> dict[str, Any]:
        last_position: int | None = state["queue_position"]

        while True:
            self._raise_if_cancelled(state)
            with self.coordinator.locked() as coordinator:
                position = coordinator.position_unlocked(request_id, identity[0], identity[1])
                if position is None:
                    raise CoordinationError(
                        "현재 submit의 queue 항목을 확인할 수 없습니다.",
                        "queue 파일을 확인하고 submit을 다시 실행하십시오.",
                    )
                state["queue_position"] = position
                if last_position is not None and position != last_position:
                    self._emit(
                        emit,
                        self._queued_record(
                            request_id,
                            state["queued_at"],
                            position,
                            state["attempted_slots"],
                            state["reassignment_reasons"],
                            reason="앞선 queue 항목이 정리되어 현재 FIFO 순번이 변경되었습니다.",
                        ),
                    )
                last_position = position

                diagnostics = self._diagnostics()
                self._raise_if_cancelled(state)
                has_eligible_available = self._has_eligible_available(
                    diagnostics, state["attempted_slots"]
                )
                has_occupied = self._has_status(diagnostics, OCCUPIED)

                if not has_occupied and not has_eligible_available:
                    removed, _ = coordinator.remove_unlocked(
                        request_id, identity[0], identity[1]
                    )
                    if not removed:
                        raise CoordinationError(
                            "자동 배정 queue에서 현재 요청을 원자적으로 제거하지 못했습니다.",
                            "queue 파일과 상태 경로를 확인하십시오.",
                        )
                    state["entry"] = None
                    result = self._no_slot_result(
                        request_id,
                        diagnostics,
                        state["attempted_slots"],
                        reassignment_reasons=state["reassignment_reasons"],
                        reason="대기 중 더는 해제를 기다릴 점유 슬롯이 없고 사용 가능한 슬롯도 없습니다.",
                        operator_action="슬롯별 operator_action을 수행한 뒤 prepare와 submit을 다시 실행하십시오.",
                    )
                    self._emit(emit, result["record"])
                    return {"kind": "terminal", "result": result}

                if position == 1 and has_eligible_available:
                    attempt = self._try_assign_locked(
                        request_id,
                        command,
                        state,
                        queue_position=position,
                        queued_at=state["queued_at"],
                        emit=emit,
                    )
                    if attempt["terminal"] is not None:
                        removed, _ = coordinator.remove_unlocked(
                            request_id, identity[0], identity[1]
                        )
                        if not removed:
                            raise CoordinationError(
                                "자동 배정 queue에서 실패한 요청을 제거하지 못했습니다.",
                                "queue 파일과 상태 경로를 확인하십시오.",
                            )
                        state["entry"] = None
                        return {"kind": "terminal", "result": attempt["terminal"]}
                    if attempt["assignment"] is not None:
                        removed, _ = coordinator.remove_unlocked(
                            request_id, identity[0], identity[1]
                        )
                        if not removed:
                            self._release_unstarted(
                                request_id,
                                attempt["assignment"],
                                reason="queue head를 제거하지 못해 child 제출을 중단했습니다.",
                                operator_action="queue 파일을 확인하고 prepare로 슬롯 상태를 점검하십시오.",
                            )
                            state["assignment"] = None
                            raise CoordinationError(
                                "자동 배정 queue head를 원자적으로 제거하지 못했습니다.",
                                "queue 파일과 상태 경로를 확인하고 슬롯 상태를 점검하십시오.",
                            )
                        state["entry"] = None
                        return {"kind": "assignment", "assignment": attempt["assignment"]}

                    diagnostics = self._diagnostics()
                    if not self._should_wait(diagnostics, state["attempted_slots"]):
                        removed, _ = coordinator.remove_unlocked(
                            request_id, identity[0], identity[1]
                        )
                        if not removed:
                            raise CoordinationError(
                                "자동 배정 queue에서 현재 요청을 제거하지 못했습니다.",
                                "queue 파일과 상태 경로를 확인하십시오.",
                            )
                        state["entry"] = None
                        result = self._no_slot_result(
                            request_id,
                            diagnostics,
                            state["attempted_slots"],
                            reassignment_reasons=state["reassignment_reasons"],
                            reason="FIFO head가 사용할 수 있는 슬롯을 확보하지 못했습니다.",
                            operator_action="슬롯별 원인과 operator_action을 확인하십시오.",
                        )
                        self._emit(emit, result["record"])
                        return {"kind": "terminal", "result": result}

            time.sleep(self.poll_interval)

    def _try_assign_locked(
        self,
        request_id: str,
        command: list[str],
        state: dict[str, Any],
        *,
        queue_position: int | None,
        queued_at: str | None,
        emit: LifecycleEmitter | None,
    ) -> dict[str, Any]:
        for slot_id in SLOT_IDS:
            if slot_id in state["attempted_slots"]:
                continue
            self._raise_if_cancelled(state)
            claim = self.runner.claim_for_auto(slot_id, request_id, command)
            if not claim.get("accepted"):
                active_duplicate = self._duplicate_from_record(request_id, claim["record"])
                if active_duplicate is not None:
                    result = self._duplicate_result(
                        request_id,
                        queue_position=None,
                        assigned_slot=active_duplicate["slot_id"],
                        reason=(
                            f"동일 request ID가 슬롯 {active_duplicate['slot_id']}에서 claim/실행 중으로 확인되었습니다."
                        ),
                        operator_action=(
                            f"기존 슬롯 {active_duplicate['slot_id']} 작업의 완료와 finish를 확인한 뒤 submit하십시오."
                        ),
                    )
                    self._emit(emit, result["record"])
                    return {"assignment": None, "terminal": result}
                continue

            state["attempted_slots"].append(slot_id)
            assignment = _Assignment(
                slot_id=slot_id,
                command=list(claim["command"]),
                claim=claim,
                prepared=state.get("prepared"),
                attempted_slots=list(state["attempted_slots"]),
                reassignment_reasons=list(state["reassignment_reasons"]),
                queue_position=queue_position,
                queued_at=queued_at,
            )
            state["assignment"] = assignment
            self._emit(
                emit,
                self._assignment_record(request_id, assignment),
            )

            readiness = self.runner.pre_submit_check(slot_id)
            self._raise_if_cancelled(state)
            if readiness["ready"]:
                active_duplicate = self._active_duplicate_locked(
                    request_id, exclude_slot_id=slot_id
                )
                if active_duplicate is not None:
                    finished = self.service.finish_job(
                        slot_id,
                        request_id,
                        assignment.claim["record"]["started_at"],
                        "duplicate_rejected",
                        None,
                        "제출 직전에 동일 request ID의 다른 slot 점유가 확인되었습니다.",
                        f"기존 슬롯 {active_duplicate['slot_id']} 작업의 finish를 확인하십시오.",
                    )
                    state["assignment"] = None
                    result = self._duplicate_result(
                        request_id,
                        queue_position=queue_position,
                        assigned_slot=active_duplicate["slot_id"],
                        reason=(
                            f"동일 request ID가 슬롯 {active_duplicate['slot_id']}에서 이미 claim/실행 중입니다."
                        ),
                        operator_action=(
                            f"기존 슬롯 {active_duplicate['slot_id']} 작업의 완료와 finish를 확인한 뒤 submit하십시오."
                        ),
                    )
                    result["record"]["claim_released_slot"] = slot_id
                    result["record"]["released"] = finished["released"]
                    result["record"]["release_after_status"] = finished["record"].get(
                        "state_after"
                    )
                    if not finished["released"]:
                        result["record"]["operator_action"] = (
                            f"슬롯 {slot_id} 점유 해제에 실패했습니다. status와 prepare로 복구하십시오."
                        )
                    self._emit(emit, result["record"])
                    return {"assignment": None, "terminal": result}
                return {"assignment": assignment, "terminal": None}

            finished = self.service.finish_job(
                slot_id,
                request_id,
                assignment.claim["record"]["started_at"],
                "pre_submit_failed",
                None,
                readiness["reason"],
                readiness["operator_action"],
            )
            state["assignment"] = None
            if not finished["released"]:
                terminal = self._finish_as_terminal(
                    request_id,
                    assignment,
                    finished["record"],
                    reason="Oracle 제출 전에 선택 슬롯을 사용할 수 없게 되었고 점유 해제도 확정되지 않았습니다.",
                    operator_action="해당 슬롯을 자동 재사용하지 말고 status와 prepare로 복구하십시오.",
                )
                self._emit(emit, terminal["record"])
                return {"assignment": None, "terminal": terminal}

            self._emit(
                emit,
                self._reassignment_record(
                    request_id,
                    assignment,
                    finished["record"],
                    readiness["reason"],
                ),
            )
            state["reassignment_reasons"].append(readiness["reason"])

        return {"assignment": None, "terminal": None}

    def _enqueue_locked(
        self,
        request_id: str,
        identity: tuple[int, str],
        state: dict[str, Any],
        coordinator: QueueCoordinator,
        emit: LifecycleEmitter | None,
    ) -> None:
        queued_at = utc_now()
        entry = {
            "request_id": request_id,
            "owner_pid": identity[0],
            "owner_starttime": identity[1],
            "queued_at": queued_at,
        }
        position = coordinator.append_unlocked(entry)
        state["entry"] = entry
        state["queued_at"] = queued_at
        state["queue_position"] = position
        self._emit(
            emit,
            self._queued_record(
                request_id,
                queued_at,
                position,
                state["attempted_slots"],
                state["reassignment_reasons"],
            ),
        )

    def _execute_assignment(
        self,
        request_id: str,
        assignment: _Assignment,
        state: dict[str, Any],
        emit: LifecycleEmitter | None,
    ) -> dict[str, Any]:
        self._raise_if_cancelled(state)
        with self.coordinator.locked():
            active_duplicate = self._active_duplicate_locked(
                request_id, exclude_slot_id=assignment.slot_id
            )
            if active_duplicate is not None:
                finished = self.service.finish_job(
                    assignment.slot_id,
                    request_id,
                    assignment.claim["record"]["started_at"],
                    "duplicate_rejected",
                    None,
                    "child 제출 직전에 동일 request ID의 다른 slot 점유가 확인되었습니다.",
                    f"기존 슬롯 {active_duplicate['slot_id']} 작업의 finish를 확인하십시오.",
                )
                state["assignment"] = None
                result = self._duplicate_result(
                    request_id,
                    queue_position=assignment.queue_position,
                    assigned_slot=active_duplicate["slot_id"],
                    reason=(
                        f"동일 request ID가 슬롯 {active_duplicate['slot_id']}에서 이미 claim/실행 중입니다."
                    ),
                    operator_action=(
                        f"기존 슬롯 {active_duplicate['slot_id']} 작업의 완료와 finish를 확인한 뒤 submit하십시오."
                    ),
                )
                result["record"]["claim_released_slot"] = assignment.slot_id
                result["record"]["released"] = finished["released"]
                result["record"]["release_after_status"] = finished["record"].get(
                    "state_after"
                )
                if not finished["released"]:
                    result["record"]["operator_action"] = (
                        f"슬롯 {assignment.slot_id} 점유 해제에 실패했습니다. status와 prepare로 복구하십시오."
                    )
                self._emit(emit, result["record"])
                return result

        state["execution_started"] = True

        def emit_result(record: dict[str, Any]) -> None:
            annotated = self._runner_record(request_id, assignment, record)
            self._emit(emit, annotated)

        try:
            execute_kwargs: dict[str, Any] = {
                "emit": emit_result,
                "cancelled_outcome": "cancelled",
            }
            if assignment.prepared is not None:
                execute_kwargs["prepared"] = assignment.prepared
            result = self.runner.execute_claimed(
                assignment.slot_id,
                request_id,
                assignment.command,
                assignment.claim,
                **execute_kwargs,
            )
            result = dict(result)
            result["record"] = self._runner_record(
                request_id, assignment, result["record"]
            )
            return result
        finally:
            state["execution_started"] = False
            state["assignment"] = None

    def _cancel_pending(
        self,
        request_id: str,
        state: dict[str, Any],
        identity: tuple[int, str],
        cancelled: _SubmitCancelled,
        emit: LifecycleEmitter | None,
    ) -> dict[str, Any]:
        assignment = state.get("assignment")
        if assignment is not None and not state["execution_started"]:
            signal_name = self._signal_name(cancelled.signal_number)
            finished = self.service.finish_job(
                assignment.slot_id,
                request_id,
                assignment.claim["record"]["started_at"],
                "cancelled",
                130,
                f"Oracle 제출 전에 호출자가 {signal_name} 신호로 요청을 취소했습니다.",
                "취소 원인과 슬롯 상태를 확인하십시오.",
            )
            state["assignment"] = None
            record = self._runner_record(request_id, assignment, finished["record"])
            record["event"] = "cancelled"
            record["outcome"] = "cancelled"
            self._emit(emit, record)
            return {
                "accepted": True,
                "exit_code": 130 if finished["released"] else 1,
                "record": record,
            }

        if state["entry"] is not None:
            position = state.get("queue_position")
            try:
                with self.coordinator.locked() as coordinator:
                    current_position = coordinator.position_unlocked(
                        request_id, identity[0], identity[1]
                    )
                    if current_position is not None:
                        position = current_position
                    removed, _ = coordinator.remove_unlocked(
                        request_id, identity[0], identity[1]
                    )
                    if not removed:
                        raise CoordinationError(
                            "취소된 요청을 queue에서 원자적으로 제거하지 못했습니다.",
                            "queue 파일을 확인하고 stale waiter를 정리하십시오.",
                        )
                state["entry"] = None
            except CoordinationError as exc:
                record = self._request_record(
                    request_id,
                    event="cancelled",
                    outcome="cancelled",
                    queue_position=position,
                    queued_at=state.get("queued_at"),
                    attempted_slots=state["attempted_slots"],
                    reason=f"취소 요청은 받았지만 queue 제거를 확인하지 못했습니다: {exc.reason}",
                    operator_action=exc.operator_action,
                )
                self._emit(emit, record)
                return {"accepted": False, "exit_code": 1, "record": record}

            record = self._request_record(
                request_id,
                event="cancelled",
                outcome="cancelled",
                queue_position=position,
                queued_at=state.get("queued_at"),
                attempted_slots=state["attempted_slots"],
                reason=(
                    f"대기 중 호출자가 {self._signal_name(cancelled.signal_number)} 신호로 "
                    "요청을 취소해 FIFO queue에서 제거했습니다."
                ),
                operator_action="없음",
            )
            self._emit(emit, record)
            return {"accepted": False, "exit_code": 130, "record": record}

        record = self._request_record(
            request_id,
            event="cancelled",
            outcome="cancelled",
            attempted_slots=state["attempted_slots"],
            reason=(
                f"Oracle 요청이 {self._signal_name(cancelled.signal_number)} 신호로 "
                "child 제출 전에 취소되었습니다."
            ),
            operator_action="없음",
        )
        self._emit(emit, record)
        return {"accepted": False, "exit_code": 130, "record": record}

    def _handle_unexpected(
        self,
        request_id: str,
        state: dict[str, Any],
        identity: tuple[int, str],
        error: Exception,
        emit: LifecycleEmitter | None,
    ) -> dict[str, Any]:
        assignment = state.get("assignment")
        if assignment is not None and not state["execution_started"]:
            self._release_unstarted(
                request_id,
                assignment,
                reason="자동 배정 조정 중 예외가 발생해 child 제출을 중단했습니다.",
                operator_action="슬롯 상태와 조정 queue를 확인하십시오.",
            )
            state["assignment"] = None

        record = self._request_record(
            request_id,
            event="failed",
            outcome="failed",
            queue_position=state.get("queue_position"),
            queued_at=state.get("queued_at"),
            assigned_slot=assignment.slot_id if assignment is not None else None,
            attempted_slots=state["attempted_slots"],
            reason=f"자동 배정 조정 중 예외가 발생했습니다: {error}",
            operator_action=(
                error.operator_action
                if isinstance(error, CoordinationError)
                else "상태 파일, allocator lock/queue와 슬롯별 상태를 확인하십시오."
            ),
        )
        self._emit(emit, record)
        return {"accepted": False, "exit_code": 1, "record": record}

    def _remove_entry_safely(
        self,
        request_id: str,
        identity: tuple[int, str],
        state: dict[str, Any],
    ) -> None:
        try:
            with self.coordinator.locked() as coordinator:
                coordinator.remove_unlocked(request_id, identity[0], identity[1])
        except Exception:
            # The caller's process is already leaving.  A later live submit
            # purges this PID/starttime instead of recovering the request.
            pass
        finally:
            state["entry"] = None

    def _release_unstarted(
        self,
        request_id: str,
        assignment: _Assignment,
        *,
        reason: str,
        operator_action: str,
    ) -> dict[str, Any]:
        return self.service.finish_job(
            assignment.slot_id,
            request_id,
            assignment.claim["record"]["started_at"],
            "failed",
            None,
            reason,
            operator_action,
        )

    def _diagnostics(self) -> list[dict[str, Any]]:
        try:
            return [dict(record) for record in self.service.status_all()]
        except Exception as exc:
            records: list[dict[str, Any]] = []
            for slot_id in SLOT_IDS:
                slot = self.service.settings.slot(slot_id)
                records.append(
                    {
                        "slot_id": slot_id,
                        "status": "사용 불가",
                        "reason": f"슬롯 {slot_id} 상태 확인 중 예외가 발생했습니다: {exc}",
                        "operator_action": f"prepare --slot {slot_id}을 실행하십시오.",
                        "profile_dir": str(slot.profile_dir),
                        "port": slot.port,
                    }
                )
            return records

    @staticmethod
    def _has_status(diagnostics: list[dict[str, Any]], status: str) -> bool:
        return any(record.get("status") == status for record in diagnostics)

    @staticmethod
    def _has_eligible_available(
        diagnostics: list[dict[str, Any]], attempted_slots: list[int]
    ) -> bool:
        return any(
            record.get("status") == AVAILABLE
            and record.get("slot_id") not in attempted_slots
            for record in diagnostics
        )

    def _should_wait(
        self, diagnostics: list[dict[str, Any]], attempted_slots: list[int]
    ) -> bool:
        return self._has_status(diagnostics, OCCUPIED) and bool(
            set(SLOT_IDS) - set(attempted_slots)
        )

    @staticmethod
    def _queued_duplicate(
        entries: list[dict[str, Any]], request_id: str
    ) -> tuple[int, dict[str, Any]] | None:
        for index, entry in enumerate(entries):
            if entry.get("request_id") == request_id:
                return index + 1, entry
        return None

    def _active_duplicate_locked(
        self, request_id: str, *, exclude_slot_id: int | None = None
    ) -> dict[str, Any] | None:
        # Read persisted occupancy first so a live manual `run` is still
        # visible even when a concurrent CDP status refresh is unavailable.
        for slot_id in SLOT_IDS:
            if slot_id == exclude_slot_id:
                continue
            try:
                state = self.service.store.read(slot_id)
            except Exception:
                state = None
            occupancy = state.get("occupancy") if isinstance(state, dict) else None
            if isinstance(occupancy, dict) and occupancy.get("job_id") == request_id:
                return {"slot_id": slot_id, "record": state}

        for record in self._diagnostics():
            if record.get("slot_id") == exclude_slot_id:
                continue
            duplicate = self._duplicate_from_record(request_id, record)
            if duplicate is not None:
                return duplicate
        return None

    @staticmethod
    def _duplicate_from_record(
        request_id: str, record: dict[str, Any]
    ) -> dict[str, Any] | None:
        occupancy = record.get("occupancy")
        if isinstance(occupancy, dict) and occupancy.get("job_id") == request_id:
            return {"slot_id": record.get("slot_id"), "record": record}
        if record.get("current_job_id") == request_id:
            return {"slot_id": record.get("slot_id"), "record": record}
        return None

    def _duplicate_result(
        self,
        request_id: str,
        *,
        queue_position: int | None,
        assigned_slot: int | None,
        reason: str,
        operator_action: str,
    ) -> dict[str, Any]:
        record = self._request_record(
            request_id,
            event="rejected",
            outcome="rejected",
            queue_position=queue_position,
            assigned_slot=assigned_slot,
            reason=reason,
            operator_action=operator_action,
        )
        record.update(
            {
                "duplicate_request": True,
                "existing_queue_position": queue_position,
                "existing_assigned_slot": assigned_slot,
                "existing_request_location": (
                    {"queue_position": queue_position}
                    if queue_position is not None
                    else {"assigned_slot": assigned_slot}
                ),
            }
        )
        return {"accepted": False, "exit_code": 2, "record": record}

    def _assignment_record(
        self, request_id: str, assignment: _Assignment
    ) -> dict[str, Any]:
        return self._runner_record(request_id, assignment, assignment.claim["record"])

    def _runner_record(
        self,
        request_id: str,
        assignment: _Assignment,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        record = dict(source)
        record.update(
            {
                "operation": "submit",
                "request_id": request_id,
                "job_id": request_id,
                "assigned_slot": assignment.slot_id,
                "attempted_slots": list(assignment.attempted_slots),
                "reassignment_reasons": list(assignment.reassignment_reasons),
                "queue_position": assignment.queue_position,
                "queued_at": assignment.queued_at,
                "release_after_status": record.get("state_after"),
            }
        )
        if assignment.reassignment_reasons:
            record["reassignment_reason"] = assignment.reassignment_reasons[-1]
        if source.get("event") == "started":
            record["lifecycle_status"] = "started"
            record["request_status"] = "started"
            record["outcome"] = "started"
            record["released"] = False
            record["release_after_status"] = None
        elif source.get("event") == "finished":
            record["request_status"] = str(source.get("outcome", "finished"))
        return record

    def _reassignment_record(
        self,
        request_id: str,
        assignment: _Assignment,
        source: dict[str, Any],
        reassignment_reason: str,
    ) -> dict[str, Any]:
        record = self._runner_record(request_id, assignment, source)
        record.update(
            {
                "event": "pre_submit_reassigned",
                "lifecycle_status": "reassigned",
                "request_status": "reassigned",
                "outcome": "reassigned",
                "reassignment_reason": reassignment_reason,
                "reassignment_reasons": list(assignment.reassignment_reasons)
                + [reassignment_reason],
                "reason": f"{reassignment_reason} {source.get('reason', '')}".strip(),
                "released": source.get("released"),
                "release_after_status": source.get("state_after"),
            }
        )
        return record

    def _finish_as_terminal(
        self,
        request_id: str,
        assignment: _Assignment,
        source: dict[str, Any],
        *,
        reason: str,
        operator_action: str,
    ) -> dict[str, Any]:
        record = self._runner_record(request_id, assignment, source)
        record.update(
            {
                "event": "failed",
                "lifecycle_status": "failed",
                "request_status": "failed",
                "outcome": "failed",
                "reason": f"{reason} {source.get('reason', '')}".strip(),
                "operator_action": operator_action,
                "released": source.get("released", False),
                "release_after_status": source.get("state_after"),
            }
        )
        return {"accepted": True, "exit_code": 1, "record": record}

    def _no_slot_result(
        self,
        request_id: str,
        diagnostics: list[dict[str, Any]],
        attempted_slots: list[int],
        *,
        reassignment_reasons: list[str] | None = None,
        reason: str,
        operator_action: str,
    ) -> dict[str, Any]:
        record = self._request_record(
            request_id,
            event="failed",
            outcome="failed",
            attempted_slots=attempted_slots,
            reassignment_reasons=reassignment_reasons,
            reason=reason,
            operator_action=operator_action,
        )
        record["slot_diagnostics"] = diagnostics
        return {"accepted": False, "exit_code": 1, "record": record}

    def _queued_record(
        self,
        request_id: str,
        queued_at: str,
        position: int,
        attempted_slots: list[int],
        reassignment_reasons: list[str] | None = None,
        *,
        reason: str = "사용 가능한 슬롯이 없어 FIFO queue에 접수했습니다.",
    ) -> dict[str, Any]:
        return self._request_record(
            request_id,
            event="queued",
            outcome="queued",
            queue_position=position,
            queued_at=queued_at,
            attempted_slots=attempted_slots,
            reassignment_reasons=reassignment_reasons,
            reason=reason,
            operator_action="앞선 요청 종료 또는 슬롯 준비를 기다리십시오. 자동 만료되지 않습니다.",
        )

    def _request_record(
        self,
        request_id: str,
        *,
        event: str,
        outcome: str,
        queue_position: int | None = None,
        queued_at: str | None = None,
        assigned_slot: int | None = None,
        attempted_slots: list[int] | None = None,
        reassignment_reasons: list[str] | None = None,
        reason: str,
        operator_action: str,
    ) -> dict[str, Any]:
        return {
            "operation": "submit",
            "event": event,
            "request_id": request_id,
            "job_id": request_id,
            "queue_position": queue_position,
            "queued_at": queued_at,
            "slot_id": assigned_slot,
            "assigned_slot": assigned_slot,
            "attempted_slots": list(attempted_slots or []),
            "reassignment_reasons": list(reassignment_reasons or []),
            "started_at": None,
            "finished_at": utc_now() if event in {"failed", "rejected", "cancelled"} else None,
            "outcome": outcome,
            "request_status": outcome,
            "reason": reason,
            "operator_action": operator_action,
            "released": None,
            "release_after_status": None,
            "lifecycle_status": outcome,
        }

    @staticmethod
    def _emit(emitter: LifecycleEmitter | None, record: dict[str, Any]) -> None:
        if emitter is not None:
            emitter(record)

    @staticmethod
    def _raise_if_cancelled(state: dict[str, Any]) -> None:
        if state.get("cancel_requested"):
            raise _SubmitCancelled(state.get("cancel_signal"))

    @staticmethod
    def _cancel_signals() -> tuple[int, ...]:
        signals = (signal.SIGINT, signal.SIGTERM)
        sighup = getattr(signal, "SIGHUP", None)
        if sighup is not None:
            signals += (sighup,)
        return signals

    @staticmethod
    def _signal_name(signal_number: int | None) -> str:
        if signal_number is None:
            return "취소"
        try:
            return signal.Signals(signal_number).name
        except ValueError:
            return f"signal {signal_number}"
