"""Slot preparation, status, and single-job lifecycle transitions."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .cdp import CDPClient, CDPError
from .launcher import ChromeLauncher, PrepareError
from .model import (
    AVAILABLE,
    NOT_READY,
    OCCUPIED,
    SLOT_IDS,
    UNAVAILABLE,
    Settings,
    Slot,
    empty_record,
    utc_now,
)
from .state import StateError, StateStore


def process_starttime(pid: int) -> str | None:
    """Read Linux process starttime field 22 from /proc/<pid>/stat."""

    try:
        contents = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    closing_parenthesis = contents.rfind(")")
    if closing_parenthesis < 0:
        return None
    fields_after_name = contents[closing_parenthesis + 2 :].split()
    # The first item is field 3 (state), so field 22 is index 19 here.
    if len(fields_after_name) <= 19:
        return None
    return fields_after_name[19]


def current_process_identity() -> tuple[int, str] | None:
    pid = os.getpid()
    starttime = process_starttime(pid)
    if starttime is None:
        return None
    return pid, starttime


class SlotService:
    def __init__(
        self,
        settings: Settings,
        *,
        store: StateStore | None = None,
        cdp: CDPClient | None = None,
        launcher: ChromeLauncher | None = None,
    ) -> None:
        self.settings = settings
        self.store = store or StateStore(settings.state_root)
        self.cdp = cdp or CDPClient(settings.cdp_request_timeout)
        self.launcher = launcher or ChromeLauncher(settings, self.cdp)

    def prepare(self, slot_id: int) -> dict[str, Any]:
        slot = self.settings.slot(slot_id)
        try:
            with self.store.locked(slot_id):
                return self._prepare_locked(slot)
        except StateError as exc:
            return self._record(
                slot,
                UNAVAILABLE,
                reason=str(exc),
                operator_action=(
                    f"슬롯 {slot.slot_id} 상태 잠금과 저장 경로를 확인한 뒤 prepare --slot "
                    f"{slot.slot_id}을 다시 실행하십시오."
                ),
                occupancy=None,
            )

    def _prepare_locked(self, slot: Slot) -> dict[str, Any]:
        try:
            existing = self.store.read_unlocked(slot.slot_id)
        except StateError:
            existing = None

        occupancy: dict[str, Any] | None = None
        if existing is not None:
            try:
                self._validate_state(slot, existing)
                occupancy = self._occupancy_from_state(existing)
            except StateError:
                # Explicit prepare is the recovery boundary for invalid old state.
                existing = None

        if occupancy is not None and not self._owner_is_gone(occupancy):
            record = self._record(
                slot,
                OCCUPIED,
                reason="현재 작업이 슬롯을 점유하고 있어 prepare를 실행할 수 없습니다.",
                operator_action="현재 작업 종료 후 status를 다시 확인하십시오.",
                occupancy=occupancy,
            )
            self._save_status(slot, existing or {}, record)
            return record

        state: dict[str, Any] = {
            "schema_version": 1,
            "slot_id": slot.slot_id,
            "port": slot.port,
            "profile_dir": str(slot.profile_dir),
            "prepared": False,
            "requires_reprepare": True,
            "occupancy": None,
            "prepared_at": None,
        }
        try:
            browser_pid = self.launcher.ensure_running(slot)
            login = self.cdp.check_login(slot)
            state["prepared"] = True
            state["requires_reprepare"] = False
            state["prepared_at"] = utc_now()
            if browser_pid is not None:
                state["browser_pid"] = browser_pid

            if login.valid:
                record = self._record(
                    slot,
                    AVAILABLE,
                    reason=login.reason,
                    operator_action="없음",
                    occupancy=None,
                )
            else:
                record = self._record(
                    slot,
                    UNAVAILABLE,
                    reason=login.reason,
                    operator_action=login.operator_action,
                    occupancy=None,
                )
        except PrepareError as exc:
            record = self._record(
                slot,
                UNAVAILABLE,
                reason=exc.reason,
                operator_action=exc.operator_action,
                occupancy=None,
            )
        except CDPError as exc:
            record = self._record(
                slot,
                UNAVAILABLE,
                reason=str(exc),
                operator_action=(
                    f"슬롯 {slot.slot_id}의 Chrome/CDP 상태와 로그를 확인한 뒤 "
                    "prepare를 다시 실행하십시오."
                ),
                occupancy=None,
            )
        except OSError as exc:
            record = self._record(
                slot,
                UNAVAILABLE,
                reason=f"슬롯 {slot.slot_id} 준비 중 운영체제 오류가 발생했습니다.",
                operator_action="권한과 경로를 확인한 뒤 prepare를 다시 실행하십시오.",
                occupancy=None,
            )
            state["error_detail"] = str(exc)

        return self._persist_prepare_state(slot, state, record)

    def status(self, slot_id: int) -> dict[str, Any]:
        slot = self.settings.slot(slot_id)
        try:
            with self.store.locked(slot_id):
                return self._status_locked(slot)
        except StateError as exc:
            return self._record(
                slot,
                UNAVAILABLE,
                reason=str(exc),
                operator_action=(
                    f"슬롯 {slot.slot_id} 상태 파일과 잠금을 확인한 뒤 status --slot "
                    f"{slot.slot_id}을 다시 실행하십시오."
                ),
                occupancy=None,
            )

    def _status_locked(self, slot: Slot) -> dict[str, Any]:
        try:
            state = self.store.read_unlocked(slot.slot_id)
        except StateError as exc:
            return self._record(
                slot,
                UNAVAILABLE,
                reason=str(exc),
                operator_action=(
                    f"슬롯 {slot.slot_id} 상태 파일을 확인하고 prepare --slot {slot.slot_id}을 "
                    "다시 실행하십시오."
                ),
                occupancy=None,
            )

        if state is None:
            return empty_record(slot)

        try:
            self._validate_state(slot, state)
            occupancy = self._occupancy_from_state(state)
        except StateError as exc:
            return self._record(
                slot,
                UNAVAILABLE,
                reason=str(exc),
                operator_action=(
                    f"슬롯 {slot.slot_id} 상태를 확인하고 prepare --slot {slot.slot_id}을 "
                    "다시 실행하십시오."
                ),
                occupancy=None,
            )

        if state.get("requires_reprepare") is True:
            record = self._latched_unavailable_record(slot, state, occupancy)
            self._save_status(slot, state, record)
            return record

        if state.get("prepared") is not True:
            previous = state.get("last_status")
            if isinstance(previous, dict) and previous.get("status") == UNAVAILABLE:
                record = self._record(
                    slot,
                    UNAVAILABLE,
                    reason=str(previous.get("reason", "슬롯 준비가 완료되지 않았습니다.")),
                    operator_action=str(
                        previous.get(
                            "operator_action", f"prepare --slot {slot.slot_id}을 실행하십시오."
                        )
                    ),
                    occupancy=occupancy,
                )
            else:
                record = empty_record(slot)
            self._save_status(slot, state, record)
            return record

        if occupancy is not None:
            try:
                self.cdp.browser_version(slot)
            except CDPError as exc:
                record = self._record(
                    slot,
                    UNAVAILABLE,
                    reason=f"작업 중 CDP 연결이 사용할 수 없게 되었습니다: {exc}",
                    operator_action=(
                        f"prepare --slot {slot.slot_id}을 실행해 슬롯을 다시 준비한 뒤 "
                        "새 작업을 시작하십시오."
                    ),
                    occupancy=occupancy,
                )
                state["requires_reprepare"] = True
                self._save_status(slot, state, record)
                return record
            if self._owner_is_gone(occupancy):
                record = self._record(
                    slot,
                    UNAVAILABLE,
                    reason="작업 실행 주체의 PID identity가 사라졌거나 달라져 슬롯을 자동 재사용하지 않습니다.",
                    operator_action=(
                        f"prepare --slot {slot.slot_id}을 실행해 슬롯을 다시 준비한 뒤 "
                        "새 작업을 시작하십시오."
                    ),
                    occupancy=occupancy,
                )
                state["requires_reprepare"] = True
            else:
                record = self._record(
                    slot,
                    OCCUPIED,
                    reason="현재 작업이 슬롯을 점유하고 있어 새 작업을 시작할 수 없습니다.",
                    operator_action="현재 작업 종료 후 status를 다시 확인하십시오.",
                    occupancy=occupancy,
                )
            self._save_status(slot, state, record)
            return record

        try:
            login = self.cdp.check_login(slot)
        except CDPError as exc:
            record = self._record(
                slot,
                UNAVAILABLE,
                reason=str(exc),
                operator_action=(
                    f"슬롯 {slot.slot_id}의 Chrome/CDP 상태를 확인하고 prepare --slot "
                    f"{slot.slot_id}을 다시 실행하십시오."
                ),
                occupancy=None,
            )
            state["requires_reprepare"] = True
            self._save_status(slot, state, record)
            return record

        if not login.valid:
            record = self._record(
                slot,
                UNAVAILABLE,
                reason=login.reason,
                operator_action=login.operator_action,
                occupancy=None,
            )
        else:
            record = self._record(
                slot,
                AVAILABLE,
                reason="CDP 응답, ChatGPT 작업 시작에 필요한 로그인, 비점유를 모두 확인했습니다.",
                operator_action="없음",
                occupancy=None,
            )
        self._save_status(slot, state, record)
        return record

    def status_all(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for slot_id in SLOT_IDS:
            try:
                records.append(self.status(slot_id))
            except Exception as exc:  # one broken slot must not hide the others
                slot = self.settings.slot(slot_id)
                records.append(
                    self._record(
                        slot,
                        UNAVAILABLE,
                        reason=f"슬롯 {slot_id} 상태 확인 중 예외가 발생했습니다.",
                        operator_action=(
                            f"오류를 확인하고 prepare --slot {slot_id}을 다시 실행하십시오."
                        ),
                        occupancy=None,
                        error_detail=str(exc),
                    )
                )
        return records

    def run_rejection(
        self,
        slot_id: int,
        job_id: str,
        reason: str,
        operator_action: str,
    ) -> dict[str, Any]:
        """Return a structured pre-claim rejection without changing occupancy."""

        slot = self.settings.slot(slot_id)
        current = self.status(slot_id)
        return self._lifecycle_record(
            slot,
            event="rejected",
            state_before=current["status"],
            state_after=current["status"],
            job_id=job_id,
            timestamp_key="rejected_at",
            reason=reason,
            operator_action=operator_action,
            occupancy=current.get("occupancy"),
        )

    def claim_job(self, slot_id: int, job_id: str) -> dict[str, Any]:
        """Atomically verify readiness and claim one slot for the current runner."""

        slot = self.settings.slot(slot_id)
        identity = current_process_identity()
        if identity is None:
            return {
                "accepted": False,
                "record": self._lifecycle_record(
                    slot,
                    event="rejected",
                    state_before=UNAVAILABLE,
                    state_after=UNAVAILABLE,
                    job_id=job_id,
                    timestamp_key="rejected_at",
                    reason="현재 runner의 Linux process starttime을 확인할 수 없습니다.",
                    operator_action="/proc 상태를 확인한 뒤 run을 다시 실행하십시오.",
                ),
            }

        if not isinstance(job_id, str) or not job_id:
            return {
                "accepted": False,
                "record": self._lifecycle_record(
                    slot,
                    event="rejected",
                    state_before=NOT_READY,
                    state_after=NOT_READY,
                    job_id=job_id,
                    timestamp_key="rejected_at",
                    reason="job ID가 비어 있습니다.",
                    operator_action="비어 있지 않은 --job-id를 지정하십시오.",
                ),
            }

        try:
            with self.store.locked(slot_id):
                return self._claim_locked(slot, job_id, identity)
        except StateError as exc:
            return {
                "accepted": False,
                "record": self._lifecycle_record(
                    slot,
                    event="rejected",
                    state_before=UNAVAILABLE,
                    state_after=UNAVAILABLE,
                    job_id=job_id,
                    timestamp_key="rejected_at",
                    reason=str(exc),
                    operator_action=(
                        f"슬롯 {slot.slot_id} 상태 잠금을 확인한 뒤 run --slot {slot.slot_id}을 "
                        "다시 실행하십시오."
                    ),
                ),
            }

    def _claim_locked(
        self, slot: Slot, job_id: str, identity: tuple[int, str]
    ) -> dict[str, Any]:
        try:
            state = self.store.read_unlocked(slot.slot_id)
        except StateError as exc:
            return self._rejection(
                slot, job_id, UNAVAILABLE, str(exc), "상태 파일을 확인한 뒤 prepare를 다시 실행하십시오."
            )

        if state is None:
            return self._rejection(
                slot,
                job_id,
                NOT_READY,
                "슬롯이 아직 준비되지 않았습니다.",
                f"prepare --slot {slot.slot_id}을 실행하십시오.",
            )

        try:
            self._validate_state(slot, state)
            occupancy = self._occupancy_from_state(state)
        except StateError as exc:
            return self._rejection(
                slot,
                job_id,
                UNAVAILABLE,
                str(exc),
                f"prepare --slot {slot.slot_id}을 실행해 상태를 복구하십시오.",
            )

        if occupancy is not None:
            if self._owner_is_gone(occupancy):
                record = self._record(
                    slot,
                    UNAVAILABLE,
                    reason="기존 작업 실행 주체의 PID identity가 사라졌거나 달라졌습니다.",
                    operator_action=(
                        f"prepare --slot {slot.slot_id}을 실행해 슬롯을 다시 준비한 뒤 "
                        "새 작업을 시작하십시오."
                    ),
                    occupancy=occupancy,
                )
                state["requires_reprepare"] = True
                self._save_status(slot, state, record)
                return {"accepted": False, "record": self._rejection_from_record(record, job_id)}
            return self._rejection(
                slot,
                job_id,
                OCCUPIED,
                "현재 작업이 슬롯을 점유하고 있어 두 번째 작업을 즉시 거절했습니다.",
                "현재 작업 종료 후 status를 다시 확인하십시오.",
                occupancy,
            )

        if state.get("requires_reprepare") is True:
            record = self._latched_unavailable_record(slot, state, None)
            self._save_status(slot, state, record)
            return {"accepted": False, "record": self._rejection_from_record(record, job_id)}

        if state.get("prepared") is not True:
            previous = state.get("last_status")
            return self._rejection(
                slot,
                job_id,
                UNAVAILABLE if isinstance(previous, dict) else NOT_READY,
                str(
                    previous.get("reason", "슬롯 준비가 완료되지 않았습니다.")
                    if isinstance(previous, dict)
                    else "슬롯 준비가 완료되지 않았습니다."
                ),
                str(
                    previous.get("operator_action", f"prepare --slot {slot.slot_id}을 실행하십시오.")
                    if isinstance(previous, dict)
                    else f"prepare --slot {slot.slot_id}을 실행하십시오."
                ),
            )

        try:
            login = self.cdp.check_login(slot)
        except CDPError as exc:
            record = self._record(
                slot,
                UNAVAILABLE,
                reason=str(exc),
                operator_action=(
                    f"슬롯 {slot.slot_id}의 Chrome/CDP 상태를 확인한 뒤 prepare --slot "
                    f"{slot.slot_id}을 다시 실행하십시오."
                ),
                occupancy=None,
            )
            state["requires_reprepare"] = True
            self._save_status(slot, state, record)
            return {"accepted": False, "record": self._rejection_from_record(record, job_id)}

        if not login.valid:
            record = self._record(
                slot,
                UNAVAILABLE,
                reason=login.reason,
                operator_action=login.operator_action,
                occupancy=None,
            )
            self._save_status(slot, state, record)
            return {"accepted": False, "record": self._rejection_from_record(record, job_id)}

        started_at = utc_now()
        occupancy = {
            "job_id": job_id,
            "started_at": started_at,
            "owner_pid": identity[0],
            "owner_starttime": identity[1],
        }
        state["occupancy"] = occupancy
        state["requires_reprepare"] = False
        record = self._lifecycle_record(
            slot,
            event="started",
            state_before=AVAILABLE,
            state_after=OCCUPIED,
            job_id=job_id,
            timestamp_key="started_at",
            timestamp=started_at,
            reason="슬롯 claim을 원자적으로 완료했고 작업을 시작할 수 있습니다.",
            operator_action="없음",
            occupancy=occupancy,
        )
        state["last_status"] = record
        try:
            self.store.write_unlocked(slot.slot_id, state)
        except StateError as exc:
            return self._rejection(
                slot,
                job_id,
                UNAVAILABLE,
                f"슬롯 claim 상태를 저장하지 못했습니다: {exc}",
                "상태 저장 경로를 확인한 뒤 prepare와 run을 다시 실행하십시오.",
            )
        return {
            "accepted": True,
            "record": record,
            "environment": self.job_environment(slot),
        }

    def finish_job(
        self,
        slot_id: int,
        job_id: str,
        started_at: str,
        outcome: str,
        exit_code: int | None,
        reason: str,
        operator_action: str,
    ) -> dict[str, Any]:
        slot = self.settings.slot(slot_id)
        identity = current_process_identity()
        finished_at = utc_now()
        if identity is None:
            return {
                "released": False,
                "record": self._finish_failure_record(
                    slot,
                    job_id,
                    started_at,
                    finished_at,
                    outcome,
                    exit_code,
                    "현재 runner의 process identity를 확인할 수 없어 점유를 해제하지 않았습니다.",
                    "운영자가 상태를 확인하고 prepare로 슬롯을 복구해야 합니다.",
                ),
            }

        try:
            with self.store.locked(slot_id):
                return self._finish_locked(
                    slot,
                    job_id,
                    started_at,
                    outcome,
                    exit_code,
                    reason,
                    operator_action,
                    finished_at,
                    identity,
                )
        except StateError as exc:
            return {
                "released": False,
                "record": self._finish_failure_record(
                    slot,
                    job_id,
                    started_at,
                    finished_at,
                    outcome,
                    exit_code,
                    f"점유 해제 중 상태 잠금 오류가 발생했습니다: {exc}",
                    "상태를 확인하고 prepare로 슬롯을 복구해야 합니다.",
                ),
            }

    def _finish_locked(
        self,
        slot: Slot,
        job_id: str,
        started_at: str,
        outcome: str,
        exit_code: int | None,
        reason: str,
        operator_action: str,
        finished_at: str,
        identity: tuple[int, str],
    ) -> dict[str, Any]:
        try:
            state = self.store.read_unlocked(slot.slot_id)
            if state is None:
                raise StateError("점유 상태 파일이 없습니다.")
            self._validate_state(slot, state)
            occupancy = self._occupancy_from_state(state)
        except StateError as exc:
            return {
                "released": False,
                "record": self._finish_failure_record(
                    slot,
                    job_id,
                    started_at,
                    finished_at,
                    outcome,
                    exit_code,
                    f"점유 해제 전 상태를 확인할 수 없습니다: {exc}",
                    f"prepare --slot {slot.slot_id}을 실행해 슬롯 상태를 복구하십시오.",
                ),
            }

        if (
            occupancy is None
            or occupancy.get("job_id") != job_id
            or occupancy.get("started_at") != started_at
            or occupancy.get("owner_pid") != identity[0]
            or occupancy.get("owner_starttime") != identity[1]
        ):
            record = self._finish_failure_record(
                slot,
                job_id,
                started_at,
                finished_at,
                outcome,
                exit_code,
                "점유 레코드의 job ID 또는 runner process identity가 달라 점유를 해제하지 않았습니다.",
                f"status --slot {slot.slot_id}을 확인하고 prepare로 슬롯을 복구하십시오.",
                occupancy=occupancy,
            )
            state["requires_reprepare"] = True
            self._save_status(slot, state, record)
            return {"released": False, "record": record}

        state["occupancy"] = None
        final_state = AVAILABLE
        final_reason = reason
        final_action = operator_action or "없음"
        if state.get("requires_reprepare") is True:
            final_state = UNAVAILABLE
            final_reason = f"{reason} 슬롯은 다시 준비가 필요합니다."
            final_action = f"prepare --slot {slot.slot_id}을 실행하십시오."
        else:
            try:
                login = self.cdp.check_login(slot)
            except CDPError as exc:
                state["requires_reprepare"] = True
                final_state = UNAVAILABLE
                final_reason = f"{reason} 점유는 해제했지만 CDP 확인에 실패했습니다: {exc}"
                final_action = f"prepare --slot {slot.slot_id}을 실행하십시오."
            else:
                if not login.valid:
                    final_state = UNAVAILABLE
                    final_reason = f"{reason} 점유는 해제했지만 {login.reason}"
                    final_action = login.operator_action
                else:
                    final_reason = f"{reason} 슬롯 점유를 해제했습니다."

        record = self._lifecycle_record(
            slot,
            event="finished",
            state_before=OCCUPIED,
            state_after=final_state,
            job_id=job_id,
            timestamp_key="finished_at",
            timestamp=finished_at,
            reason=final_reason,
            operator_action=final_action,
            occupancy=None,
        )
        record["outcome"] = outcome
        record["exit_code"] = exit_code
        record["started_at"] = started_at
        record["released"] = True
        state["last_status"] = record
        try:
            self.store.write_unlocked(slot.slot_id, state)
        except StateError as exc:
            record["state_after"] = UNAVAILABLE
            record["status"] = UNAVAILABLE
            record["released"] = False
            record["reason"] = f"{reason} 점유 해제 상태를 저장하지 못했습니다: {exc}"
            record["operator_action"] = f"prepare --slot {slot.slot_id}을 실행하십시오."
            return {"released": False, "record": record}
        return {"released": True, "record": record}

    @staticmethod
    def job_environment(slot: Slot) -> dict[str, str]:
        remote_chrome = f"127.0.0.1:{slot.port}"
        return {
            "ORACLE_BROWSER_SLOT_ID": str(slot.slot_id),
            "ORACLE_BROWSER_SLOT_PORT": str(slot.port),
            "ORACLE_BROWSER_REMOTE_CHROME": remote_chrome,
        }

    @staticmethod
    def _validate_state(slot: Slot, state: dict[str, Any]) -> None:
        if state.get("slot_id") != slot.slot_id:
            raise StateError(f"슬롯 {slot.slot_id} 상태 파일의 슬롯 ID가 일치하지 않습니다.")
        if state.get("port") != slot.port:
            raise StateError(f"슬롯 {slot.slot_id} 상태 파일의 포트가 일치하지 않습니다.")
        if state.get("profile_dir") != str(slot.profile_dir):
            raise StateError(f"슬롯 {slot.slot_id} 상태 파일의 프로필 위치가 일치하지 않습니다.")

    @staticmethod
    def _occupancy_from_state(state: dict[str, Any]) -> dict[str, Any] | None:
        value = state.get("occupancy")
        if value is None:
            return None
        if not isinstance(value, dict):
            raise StateError("점유 상태 모델 형식이 올바르지 않습니다.")
        if not value.get("job_id") or not value.get("started_at"):
            raise StateError("점유 상태에 작업 식별자와 시작 시각이 필요합니다.")
        owner_pid = value.get("owner_pid")
        owner_starttime = value.get("owner_starttime")
        if isinstance(owner_pid, bool) or not isinstance(owner_pid, int) or owner_pid <= 0:
            raise StateError("점유 상태에 올바른 owner PID가 필요합니다.")
        if not isinstance(owner_starttime, str) or not owner_starttime:
            raise StateError("점유 상태에 Linux owner starttime이 필요합니다.")
        return value

    @staticmethod
    def _owner_is_gone(occupancy: dict[str, Any]) -> bool:
        actual_starttime = process_starttime(occupancy["owner_pid"])
        return actual_starttime != occupancy["owner_starttime"]

    def _record(
        self,
        slot: Slot,
        status: str,
        *,
        reason: str | None = None,
        operator_action: str | None = None,
        occupancy: dict[str, Any] | None,
        error_detail: str | None = None,
    ) -> dict[str, Any]:
        record = empty_record(slot, checked_at=utc_now())
        record["status"] = status
        record["reason"] = reason or ""
        record["operator_action"] = operator_action or "없음"
        record["occupancy"] = occupancy
        if occupancy is not None:
            record["job_id"] = occupancy.get("job_id")
            record["started_at"] = occupancy.get("started_at")
        if error_detail:
            record["error_detail"] = error_detail
        return record

    def _lifecycle_record(
        self,
        slot: Slot,
        *,
        event: str,
        state_before: str,
        state_after: str,
        job_id: str | None,
        timestamp_key: str,
        reason: str,
        operator_action: str,
        timestamp: str | None = None,
        occupancy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        timestamp = timestamp or utc_now()
        record = self._record(
            slot,
            state_after,
            reason=reason,
            operator_action=operator_action,
            occupancy=occupancy,
        )
        record.update(
            {
                "operation": "run",
                "event": event,
                "state_before": state_before,
                "state_after": state_after,
                "job_id": job_id,
                timestamp_key: timestamp,
                "remote_chrome": f"127.0.0.1:{slot.port}",
            }
        )
        if occupancy is not None:
            record["current_job_id"] = occupancy.get("job_id")
            record["current_started_at"] = occupancy.get("started_at")
        return record

    def _rejection(
        self,
        slot: Slot,
        job_id: str,
        state: str,
        reason: str,
        operator_action: str,
        occupancy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = self._lifecycle_record(
            slot,
            event="rejected",
            state_before=state,
            state_after=state,
            job_id=job_id,
            timestamp_key="rejected_at",
            reason=reason,
            operator_action=operator_action,
            occupancy=occupancy,
        )
        return {"accepted": False, "record": record}

    @staticmethod
    def _rejection_from_record(record: dict[str, Any], job_id: str) -> dict[str, Any]:
        record = dict(record)
        record.update(
            {
                "operation": "run",
                "event": "rejected",
                "state_before": record["status"],
                "state_after": record["status"],
                "job_id": job_id,
                "rejected_at": record["checked_at"],
            }
        )
        return record

    def _latched_unavailable_record(
        self,
        slot: Slot,
        state: dict[str, Any],
        occupancy: dict[str, Any] | None,
    ) -> dict[str, Any]:
        previous = state.get("last_status")
        reason = (
            previous.get("reason")
            if isinstance(previous, dict) and previous.get("reason")
            else "슬롯이 다시 준비될 때까지 사용할 수 없습니다."
        )
        action = (
            previous.get("operator_action")
            if isinstance(previous, dict) and previous.get("operator_action")
            else f"prepare --slot {slot.slot_id}을 실행하십시오."
        )
        return self._record(
            slot,
            UNAVAILABLE,
            reason=reason,
            operator_action=action,
            occupancy=occupancy,
        )

    def _finish_failure_record(
        self,
        slot: Slot,
        job_id: str,
        started_at: str,
        finished_at: str,
        outcome: str,
        exit_code: int | None,
        reason: str,
        operator_action: str,
        occupancy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = self._lifecycle_record(
            slot,
            event="finished",
            state_before=OCCUPIED,
            state_after=UNAVAILABLE,
            job_id=job_id,
            timestamp_key="finished_at",
            timestamp=finished_at,
            reason=reason,
            operator_action=operator_action,
            occupancy=occupancy,
        )
        record["started_at"] = started_at
        record["outcome"] = outcome
        record["exit_code"] = exit_code
        record["released"] = False
        return record

    def _write_state(
        self, slot: Slot, state: dict[str, Any], record: dict[str, Any]
    ) -> None:
        state["last_status"] = record
        try:
            self.store.write_unlocked(slot.slot_id, state)
        except StateError:
            record["operator_action"] = (
                f"상태 저장에 실패했습니다. 경로 권한을 확인하고 prepare --slot "
                f"{slot.slot_id}을 다시 실행하십시오."
            )

    def _persist_prepare_state(
        self, slot: Slot, state: dict[str, Any], record: dict[str, Any]
    ) -> dict[str, Any]:
        state["last_status"] = record
        try:
            self.store.write_unlocked(slot.slot_id, state)
        except Exception as exc:
            return self._prepare_storage_failure(
                slot,
                f"준비 상태 파일을 저장하지 못했습니다: {exc}",
            )

        try:
            readback = self.store.read_unlocked(slot.slot_id)
        except Exception as exc:
            return self._prepare_storage_failure(
                slot,
                f"준비 상태 저장 후 authoritative readback에 실패했습니다: {exc}",
            )

        if not self._prepare_readback_matches(slot, state, record, readback):
            return self._prepare_storage_failure(
                slot,
                "준비 상태 저장 후 authoritative readback이 슬롯 설정과 일치하지 않습니다.",
            )
        return record

    @staticmethod
    def _prepare_readback_matches(
        slot: Slot,
        expected: dict[str, Any],
        record: dict[str, Any],
        readback: dict[str, Any] | None,
    ) -> bool:
        if not isinstance(readback, dict):
            return False
        for key in ("slot_id", "port", "profile_dir", "prepared", "requires_reprepare", "occupancy"):
            if readback.get(key) != expected.get(key):
                return False
        last_status = readback.get("last_status")
        return isinstance(last_status, dict) and last_status.get("status") == record.get("status")

    def _prepare_storage_failure(self, slot: Slot, detail: str) -> dict[str, Any]:
        return self._record(
            slot,
            UNAVAILABLE,
            reason=detail,
            operator_action=(
                f"슬롯 {slot.slot_id} 상태 저장 경로와 권한을 확인한 뒤 prepare --slot "
                f"{slot.slot_id}을 다시 실행하십시오. 이미 시작된 Chrome은 자동 종료하지 않았습니다."
            ),
            occupancy=None,
        )

    def _save_status(
        self, slot: Slot, state: dict[str, Any], record: dict[str, Any]
    ) -> None:
        self._write_state(slot, state, record)
