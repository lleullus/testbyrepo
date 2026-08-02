"""Short-lived, process-safe coordination for automatic slot allocation."""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - the supported runtime is Linux/WSL.
    fcntl = None

from .service import process_starttime


QUEUE_SCHEMA_VERSION = 1


class CoordinationError(Exception):
    """The allocator coordination lock or queue cannot be used safely."""

    def __init__(self, reason: str, operator_action: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.operator_action = operator_action


class QueueCoordinator:
    """Serialize queue admission and head assignment without persisting history."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.lock_path = root / "allocator.lock"
        self.queue_path = root / "allocator-queue.json"

    @contextmanager
    def locked(self) -> Iterator["QueueCoordinator"]:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            lock = self.lock_path.open("a+", encoding="utf-8")
        except OSError as exc:
            raise CoordinationError(
                "자동 배정 coordination lock을 열 수 없습니다.",
                "상태 경로의 권한과 디스크 상태를 확인하십시오.",
            ) from exc

        try:
            if fcntl is None:
                raise CoordinationError(
                    "Linux 파일 잠금을 사용할 수 없어 자동 배정을 안전하게 조정할 수 없습니다.",
                    "Linux/WSL 파일 잠금 환경에서 submit을 다시 실행하십시오.",
                )
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            except OSError as exc:
                raise CoordinationError(
                    "자동 배정 coordination lock을 획득할 수 없습니다.",
                    "상태 경로의 lock 파일과 권한을 확인하십시오.",
                ) from exc
            yield self
        finally:
            try:
                if fcntl is not None:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            finally:
                lock.close()

    def load_unlocked(self) -> list[dict[str, Any]]:
        try:
            with self.queue_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except FileNotFoundError:
            return []
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CoordinationError(
                f"자동 배정 queue 파일을 읽을 수 없습니다: {self.queue_path}",
                "queue 파일을 백업한 뒤 상태 경로와 JSON 형식을 확인하십시오.",
            ) from exc

        entries = self._validate_payload(payload)
        live_entries = [entry for entry in entries if self._owner_is_live(entry)]
        if len(live_entries) != len(entries):
            # A dead waiter is never recovered.  Its entry is only removed while
            # another live submit process owns the coordination lock.
            self._save_unlocked(live_entries)
        return live_entries

    def append_unlocked(self, entry: dict[str, Any]) -> int:
        entries = self.load_unlocked()
        request_id = entry.get("request_id")
        if any(existing.get("request_id") == request_id for existing in entries):
            raise CoordinationError(
                f"request ID가 이미 자동 배정 queue에 있습니다: {request_id}",
                "동일 request ID의 실행이 끝나거나 다른 request ID를 사용하십시오.",
            )
        entries.append(dict(entry))
        self._save_unlocked(entries)
        return len(entries)

    def remove_unlocked(
        self, request_id: str, owner_pid: int, owner_starttime: str
    ) -> tuple[bool, int | None]:
        entries = self.load_unlocked()
        position: int | None = None
        retained: list[dict[str, Any]] = []
        removed = False
        for index, entry in enumerate(entries):
            matches = (
                entry.get("request_id") == request_id
                and entry.get("owner_pid") == owner_pid
                and entry.get("owner_starttime") == owner_starttime
            )
            if matches and not removed:
                removed = True
                position = index + 1
                continue
            retained.append(entry)

        if removed:
            self._save_unlocked(retained)
        return removed, position

    def position_unlocked(
        self, request_id: str, owner_pid: int, owner_starttime: str
    ) -> int | None:
        entries = self.load_unlocked()
        for index, entry in enumerate(entries):
            if (
                entry.get("request_id") == request_id
                and entry.get("owner_pid") == owner_pid
                and entry.get("owner_starttime") == owner_starttime
            ):
                return index + 1
        return None

    def _save_unlocked(self, entries: list[dict[str, Any]]) -> None:
        if not entries:
            try:
                self.queue_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise CoordinationError(
                    "자동 배정 queue를 비우지 못했습니다.",
                    "queue 파일 권한과 상태 경로를 확인하십시오.",
                ) from exc
            return

        payload = {"schema_version": QUEUE_SCHEMA_VERSION, "queue": entries}
        try:
            fd, temporary_path = tempfile.mkstemp(
                prefix=".allocator-queue.", suffix=".tmp", dir=self.root
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_path, self.queue_path)
            finally:
                try:
                    os.unlink(temporary_path)
                except FileNotFoundError:
                    pass
        except OSError as exc:
            raise CoordinationError(
                "자동 배정 queue를 원자적으로 저장하지 못했습니다.",
                "상태 경로의 권한과 디스크 상태를 확인하십시오.",
            ) from exc

    @staticmethod
    def _validate_payload(payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict) or payload.get("schema_version") != QUEUE_SCHEMA_VERSION:
            raise CoordinationError(
                "자동 배정 queue의 schema가 올바르지 않습니다.",
                "queue 파일을 백업한 뒤 상태 경로를 복구하고 submit을 다시 실행하십시오.",
            )
        entries = payload.get("queue")
        if not isinstance(entries, list):
            raise CoordinationError(
                "자동 배정 queue 목록 형식이 올바르지 않습니다.",
                "queue 파일을 백업한 뒤 상태 경로를 복구하고 submit을 다시 실행하십시오.",
            )

        validated: list[dict[str, Any]] = []
        seen_request_ids: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise CoordinationError(
                    "자동 배정 queue 항목 형식이 올바르지 않습니다.",
                    "queue 파일을 백업한 뒤 상태 경로를 복구하십시오.",
                )
            request_id = entry.get("request_id")
            owner_pid = entry.get("owner_pid")
            owner_starttime = entry.get("owner_starttime")
            queued_at = entry.get("queued_at")
            if (
                not isinstance(request_id, str)
                or not request_id
                or request_id in seen_request_ids
                or isinstance(owner_pid, bool)
                or not isinstance(owner_pid, int)
                or owner_pid <= 0
                or not isinstance(owner_starttime, str)
                or not owner_starttime
                or not isinstance(queued_at, str)
                or not queued_at
            ):
                raise CoordinationError(
                    "자동 배정 queue 항목에 request ID, PID identity, 접수 시각이 필요합니다.",
                    "queue 파일을 백업한 뒤 상태 경로를 복구하십시오.",
                )
            seen_request_ids.add(request_id)
            validated.append(dict(entry))
        return validated

    @staticmethod
    def _owner_is_live(entry: dict[str, Any]) -> bool:
        actual_starttime = process_starttime(int(entry["owner_pid"]))
        return actual_starttime == entry["owner_starttime"]
