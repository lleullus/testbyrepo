"""Configuration and persisted state models for Oracle Browser slots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import os
from pathlib import Path
from typing import Any, Mapping


SLOT_IDS = (1, 2, 3)
NOT_READY = "미준비"
AVAILABLE = "사용 가능"
OCCUPIED = "점유 중"
UNAVAILABLE = "사용 불가"
STATUSES = (NOT_READY, AVAILABLE, OCCUPIED, UNAVAILABLE)


def utc_now() -> str:
    """Return a compact, unambiguous timestamp for operator output."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _path_from_env(value: str) -> Path:
    return Path(value).expanduser()


@dataclass(frozen=True)
class Slot:
    slot_id: int
    port: int
    profile_dir: Path

    @property
    def label(self) -> str:
        return f"슬롯 {self.slot_id}"


@dataclass(frozen=True)
class Settings:
    """Runtime boundaries. Defaults match the WSL Oracle Browser runtime."""

    state_root: Path
    profile_root: Path
    chrome_path: Path
    port_base: int = 19222
    chatgpt_url: str = "https://chatgpt.com/"
    cdp_start_timeout: float = 15.0
    cdp_request_timeout: float = 2.0
    queue_poll_interval: float = 0.2

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if environ is None else environ
        home = _path_from_env(env.get("HOME", str(Path.home())))
        oracle_home = _path_from_env(env.get("ORACLE_HOME_DIR", str(home / ".oracle")))

        state_root = _path_from_env(
            env.get(
                "ORACLE_BROWSER_SLOTS_STATE_ROOT",
                str(oracle_home / "browser-slots"),
            )
        )
        profile_root = _path_from_env(
            env.get(
                "ORACLE_BROWSER_SLOTS_PROFILE_ROOT",
                str(oracle_home / "browser-profiles"),
            )
        )
        chrome_path = _path_from_env(
            env.get(
                "ORACLE_BROWSER_SLOTS_CHROME_PATH",
                env.get("CHROME_PATH", "/usr/bin/google-chrome"),
            )
        )

        try:
            port_base = int(env.get("ORACLE_BROWSER_SLOTS_PORT_BASE", "19222"))
        except ValueError as exc:
            raise ValueError("ORACLE_BROWSER_SLOTS_PORT_BASE must be an integer") from exc
        if not 1 <= port_base <= 65533:
            raise ValueError("ORACLE_BROWSER_SLOTS_PORT_BASE must be between 1 and 65533")

        try:
            cdp_start_timeout = float(
                env.get("ORACLE_BROWSER_SLOTS_CDP_START_TIMEOUT", "15")
            )
            cdp_request_timeout = float(
                env.get("ORACLE_BROWSER_SLOTS_CDP_REQUEST_TIMEOUT", "2")
            )
            queue_poll_interval = float(
                env.get("ORACLE_BROWSER_SLOTS_QUEUE_POLL_INTERVAL", "0.2")
            )
        except ValueError as exc:
            raise ValueError("CDP and queue polling values must be numbers") from exc
        if cdp_start_timeout <= 0 or cdp_request_timeout <= 0:
            raise ValueError("CDP timeouts must be greater than zero")
        if not math.isfinite(queue_poll_interval) or queue_poll_interval <= 0 or queue_poll_interval > 60:
            raise ValueError("queue polling interval must be between 0 and 60 seconds")

        return cls(
            state_root=state_root,
            profile_root=profile_root,
            chrome_path=chrome_path,
            port_base=port_base,
            chatgpt_url=env.get("ORACLE_BROWSER_SLOTS_CHATGPT_URL", "https://chatgpt.com/"),
            cdp_start_timeout=cdp_start_timeout,
            cdp_request_timeout=cdp_request_timeout,
            queue_poll_interval=queue_poll_interval,
        )

    def slot(self, slot_id: int) -> Slot:
        if slot_id not in SLOT_IDS:
            raise ValueError(f"slot must be one of {', '.join(map(str, SLOT_IDS))}")
        return Slot(
            slot_id=slot_id,
            port=self.port_base + slot_id - 1,
            profile_dir=self.profile_root / f"slot-{slot_id}",
        )


def empty_record(slot: Slot, *, checked_at: str | None = None) -> dict[str, Any]:
    """Create the stable operator-facing shape used by both commands."""

    return {
        "slot_id": slot.slot_id,
        "slot_label": slot.label,
        "port": slot.port,
        "profile_dir": str(slot.profile_dir),
        "status": NOT_READY,
        "checked_at": checked_at or utc_now(),
        "reason": "슬롯이 아직 준비되지 않았습니다.",
        "operator_action": f"prepare --slot {slot.slot_id}을 실행하십시오.",
        "job_id": None,
        "started_at": None,
        "occupancy": None,
    }
