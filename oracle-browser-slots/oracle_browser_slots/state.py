"""Atomic, per-slot JSON state storage."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from contextlib import contextmanager
from typing import Any, Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - the supported runtime is Linux/WSL.
    fcntl = None


class StateError(Exception):
    """A slot state file cannot be read or written safely."""


class StateStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path_for(self, slot_id: int) -> Path:
        return self.root / f"slot-{slot_id}.json"

    def read(self, slot_id: int) -> dict[str, Any] | None:
        with self.locked(slot_id):
            return self.read_unlocked(slot_id)

    def read_unlocked(self, slot_id: int) -> dict[str, Any] | None:
        path = self.path_for(slot_id)
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except FileNotFoundError:
            return None
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StateError(f"상태 파일을 읽을 수 없습니다: {path}") from exc
        if not isinstance(value, dict):
            raise StateError(f"상태 파일 형식이 올바르지 않습니다: {path}")
        return value

    def write(self, slot_id: int, value: dict[str, Any]) -> None:
        with self.locked(slot_id):
            self.write_unlocked(slot_id, value)

    def write_unlocked(self, slot_id: int, value: dict[str, Any]) -> None:
        try:
            fd, temporary_path = tempfile.mkstemp(
                prefix=f".slot-{slot_id}.", suffix=".tmp", dir=self.root
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_path, self.path_for(slot_id))
            finally:
                try:
                    os.unlink(temporary_path)
                except FileNotFoundError:
                    pass
        except OSError as exc:
            raise StateError(f"상태 파일을 저장할 수 없습니다: {self.path_for(slot_id)}") from exc

    @contextmanager
    def locked(self, slot_id: int) -> Iterator[None]:
        """Hold one slot's lock across a complete state transition."""

        try:
            self.root.mkdir(parents=True, exist_ok=True)
            lock_path = self.root / f"slot-{slot_id}.lock"
            lock = lock_path.open("a+", encoding="utf-8")
        except OSError as exc:
            raise StateError(f"슬롯 {slot_id} 상태 잠금을 열 수 없습니다.") from exc

        try:
            if fcntl is None:
                raise StateError("Linux 파일 잠금을 사용할 수 없어 슬롯 상태를 안전하게 변경할 수 없습니다.")
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            except OSError as exc:
                raise StateError(f"슬롯 {slot_id} 상태 잠금을 획득할 수 없습니다.") from exc
            yield
        finally:
            try:
                if fcntl is not None:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            finally:
                lock.close()
