"""Start one isolated WSL Chrome process without touching the stock Oracle runtime."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import time
from typing import Iterator

from .cdp import CDPClient, CDPError
from .model import Settings, Slot


class PrepareError(Exception):
    def __init__(self, reason: str, operator_action: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.operator_action = operator_action


class ChromeLauncher:
    def __init__(self, settings: Settings, cdp: CDPClient) -> None:
        self.settings = settings
        self.cdp = cdp

    def ensure_running(self, slot: Slot) -> int | None:
        """Reuse a ready endpoint or launch Chrome for this slot's fixed runtime."""

        try:
            slot.profile_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise PrepareError(
                f"슬롯 {slot.slot_id} 프로필 위치를 만들 수 없습니다: {slot.profile_dir}",
                "프로필 경로의 권한과 디스크 상태를 확인한 뒤 prepare를 다시 실행하십시오.",
            ) from exc

        if self.cdp.is_ready(slot):
            self._verify_existing_cdp_owner(slot)
            return None

        if self._port_is_open(slot.port):
            raise PrepareError(
                f"슬롯 {slot.slot_id} 포트 {slot.port}가 Chrome CDP가 아닌 프로세스에 사용 중입니다.",
                f"포트 {slot.port}의 프로세스를 확인하고 정리한 뒤 prepare를 다시 실행하십시오.",
            )

        if not self.settings.chrome_path.is_file() or not os.access(
            self.settings.chrome_path, os.X_OK
        ):
            raise PrepareError(
                f"Chrome 실행 파일을 사용할 수 없습니다: {self.settings.chrome_path}",
                "WSL Linux Chrome 경로와 실행 권한을 확인한 뒤 prepare를 다시 실행하십시오.",
            )

        if self._profile_process_exists(slot.profile_dir):
            raise PrepareError(
                f"슬롯 {slot.slot_id} 프로필은 사용 중이지만 CDP가 응답하지 않습니다.",
                "해당 프로필을 사용하는 Chrome 프로세스와 로그를 확인한 뒤 prepare를 다시 실행하십시오.",
            )

        self._remove_stale_locks(slot.profile_dir)
        stdout_path = self.settings.state_root / f"slot-{slot.slot_id}.chrome.stdout.log"
        stderr_path = self.settings.state_root / f"slot-{slot.slot_id}.chrome.stderr.log"
        try:
            self.settings.state_root.mkdir(parents=True, exist_ok=True)
            with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
                process = subprocess.Popen(
                    self._command(slot),
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    close_fds=True,
                    start_new_session=True,
                )
        except OSError as exc:
            raise PrepareError(
                f"슬롯 {slot.slot_id} Chrome을 시작하지 못했습니다.",
                f"{stderr_path}를 확인하고 Chrome 실행 파일을 점검한 뒤 prepare를 다시 실행하십시오.",
            ) from exc

        deadline = time.monotonic() + self.settings.cdp_start_timeout
        while time.monotonic() < deadline:
            try:
                self.cdp.browser_version(slot)
                return process.pid
            except CDPError:
                if process.poll() is not None:
                    raise PrepareError(
                        f"슬롯 {slot.slot_id} Chrome이 CDP 준비 전에 종료되었습니다.",
                        f"{stderr_path}를 확인하고 원인을 해결한 뒤 prepare를 다시 실행하십시오.",
                    )
                time.sleep(0.2)

        raise PrepareError(
            f"슬롯 {slot.slot_id} Chrome이 {slot.port}에서 CDP를 노출하지 않았습니다.",
            f"{stderr_path}와 포트 {slot.port}를 확인한 뒤 prepare를 다시 실행하십시오.",
        )

    def _command(self, slot: Slot) -> list[str]:
        return [
            str(self.settings.chrome_path),
            f"--remote-debugging-port={slot.port}",
            "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={slot.profile_dir}",
            "--profile-directory=Default",
            "--password-store=basic",
            "--use-mock-keychain",
            "--no-first-run",
            "--no-default-browser-check",
            self.settings.effective_launcher_url(slot.slot_id),
        ]

    @staticmethod
    def _port_is_open(port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return True
        except OSError:
            return False

    @staticmethod
    def _profile_process_exists(profile_dir: Path) -> bool:
        expected = f"--user-data-dir={profile_dir}"
        for arguments in _proc_arguments():
            if _has_flag(arguments, expected):
                return True
        return False

    @staticmethod
    def _verify_existing_cdp_owner(slot: Slot) -> None:
        expected_port = f"--remote-debugging-port={slot.port}"
        expected_profile = f"--user-data-dir={slot.profile_dir}"
        chrome_processes = [
            arguments for arguments in _proc_arguments() if _is_chrome_process(arguments)
        ]
        matching_processes = [
            arguments
            for arguments in chrome_processes
            if _has_flag(arguments, expected_port)
            and _has_flag(arguments, expected_profile)
        ]
        if matching_processes:
            return

        port_processes = [
            arguments
            for arguments in chrome_processes
            if _has_flag(arguments, expected_port)
        ]
        if port_processes:
            raise PrepareError(
                f"슬롯 {slot.slot_id} CDP는 응답하지만 포트 {slot.port}의 Chrome 프로세스가 "
                f"정확한 프로필 {slot.profile_dir}로 실행되지 않았습니다.",
                f"포트 {slot.port}의 Chrome 명령행과 --user-data-dir를 확인하고, "
                f"슬롯 {slot.slot_id} 전용 프로필 상태가 된 뒤 prepare를 다시 실행하십시오.",
            )

        raise PrepareError(
            f"슬롯 {slot.slot_id} CDP는 응답하지만 /proc에서 포트 {slot.port}와 "
            "슬롯 프로필의 Chrome 소유 증거를 확립할 수 없습니다.",
            f"포트 {slot.port}의 Chrome 명령행을 확인하고 다른 프로세스가 점유하지 않는 "
            "상태에서 prepare를 다시 실행하십시오.",
        )

    @staticmethod
    def _remove_stale_locks(profile_dir: Path) -> None:
        for name in ("SingletonCookie", "SingletonLock", "SingletonSocket"):
            try:
                (profile_dir / name).unlink()
            except FileNotFoundError:
                pass


def _proc_arguments() -> Iterator[tuple[str, ...]]:
    proc_root = Path("/proc")
    try:
        entries = proc_root.iterdir()
    except OSError:
        return
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            raw_arguments = (entry / "cmdline").read_bytes().split(b"\x00")
        except OSError:
            continue
        arguments = tuple(
            argument.decode("utf-8", errors="replace")
            for argument in raw_arguments
            if argument
        )
        if arguments:
            yield arguments


def _is_chrome_process(arguments: tuple[str, ...]) -> bool:
    if not arguments:
        return False
    executable = Path(arguments[0].split(maxsplit=1)[0]).name.lower()
    return "chrome" in executable or "chromium" in executable


def _has_flag(arguments: tuple[str, ...], flag: str) -> bool:
    """True when the flag appears as one argv element or whitespace token.

    Chrome in this runtime can collapse the entire command line into a single
    argv element (`/proc/<pid>/cmdline` then has one NUL-separated part), so
    element-exact matching would never see a live slot owner. Token matching
    keeps the check exact while tolerating that collapsed form.
    """

    if flag in arguments:
        return True
    return any(
        token == flag for argument in arguments for token in argument.split()
    )
