#!/usr/bin/env python3
"""Clean installed-artifact E2E harness for B4-CLEAN-E2E.

The harness deliberately imports no product modules.  It packages the npm and
Python distributions, installs both below a disposable work root, and observes
only installed entry points.  Every decisive consumer command is executed
under strace and recorded in a durable evidence bundle.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from typing import Any, Iterable, Mapping, Sequence
import uuid

PROJECT_ROOT = Path("/home/user01/project/oracle")
ORACLE_VERSION = "0.16.1"
SELECTOR_SCHEMA = "oracle-file-selection/v1"
DEFAULT_SYSTEM_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
PERSONAL_PATH_PARTS = ("/home/user01", "/.nvm/", "/nvm/versions/")
TERMINAL = {"PASS", "FAIL", "EVIDENCE_NEEDED"}


class HarnessStop(RuntimeError):
    def __init__(self, reason: str, *, status: str = "FAIL") -> None:
        super().__init__(reason)
        if status not in TERMINAL:
            raise ValueError(f"invalid stop status: {status}")
        self.status = status
        self.reason = reason


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()




def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def json_objects(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def path_is_below(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def option_pairs(argv: Sequence[str], flag: str) -> list[tuple[int, str | None]]:
    pairs: list[tuple[int, str | None]] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--":
            break
        if token == flag:
            value = argv[index + 1] if index + 1 < len(argv) else None
            pairs.append((index, value))
            index += 2
            continue
        if token.startswith(flag + "="):
            pairs.append((index, token.split("=", 1)[1]))
        index += 1
    return pairs


class Harness:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.project_root = args.project_root.resolve(strict=True)
        if args.resume:
            self.work_root = args.resume.resolve(strict=True)
        elif args.work_root:
            self.work_root = args.work_root.resolve(strict=False)
            self.work_root.mkdir(parents=True, exist_ok=False)
        else:
            self.work_root = Path(tempfile.mkdtemp(prefix="oracle-b4-clean-e2e-"))
        self.evidence = (args.evidence_dir or self.work_root / "evidence").resolve(strict=False)
        self.logs = self.evidence / "logs"
        self.traces = self.evidence / "traces"
        self.before = self.evidence / "state-before"
        self.after = self.evidence / "state-after"
        for directory in (self.evidence, self.logs, self.traces, self.before, self.after):
            directory.mkdir(parents=True, exist_ok=True)
        self.commands_path = self.evidence / "commands.jsonl"
        self.artifacts_path = self.evidence / "artifacts.json"
        self.summary_path = self.evidence / "summary.json"
        self.system_path = args.system_path
        self.denied = tuple(dict.fromkeys((*PERSONAL_PATH_PARTS, str(self.project_root))))
        self.tool_paths: dict[str, Path] = {}
        self.artifacts: dict[str, Any] = {}
        self.summary: dict[str, Any] = {
            "schema": "oracle-b4-clean-e2e/v1",
            "started_at": utc_now(),
            "work_root": str(self.work_root),
            "evidence_dir": str(self.evidence),
            "project_root": str(self.project_root),
            "scenarios": {},
            "overall": "EVIDENCE_NEEDED",
            "external_effect": "not-submitted",
        }
        self.consumer_env: dict[str, str] = {}
        self._write_summary()

    def _write_summary(self) -> None:
        write_json(self.summary_path, self.summary)

    def result(self, name: str, status: str, reason: str, **evidence: Any) -> None:
        if status not in TERMINAL:
            raise ValueError(status)
        self.summary["scenarios"][name] = {"status": status, "reason": reason, **evidence}
        self._write_summary()

    def finish(self) -> int:
        statuses = [entry["status"] for entry in self.summary["scenarios"].values()]
        if statuses and all(status == "PASS" for status in statuses):
            overall = "PASS"
        elif "FAIL" in statuses:
            overall = "FAIL"
        else:
            overall = "EVIDENCE_NEEDED"
        self.summary["overall"] = overall
        self.summary["finished_at"] = utc_now()
        self._write_summary()
        return 0 if overall == "PASS" else 2 if overall == "EVIDENCE_NEEDED" else 1

    def _append_command(self, record: Mapping[str, Any]) -> None:
        with self.commands_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def run(
        self,
        name: str,
        argv: Sequence[str | Path],
        *,
        cwd: Path,
        env: Mapping[str, str],
        traced: bool = False,
        timeout: float = 600,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [str(value) for value in argv]
        trace_path: Path | None = None
        if traced:
            trace_path = self.traces / f"{name}.log"
            command = [
                str(self.tool_paths["strace"]), "-f", "-qq", "-s", "8192",
                "-e", "trace=%file,process", "-o", str(trace_path), "--", *command,
            ]
        stdout_path = self.logs / f"{name}.stdout.log"
        stderr_path = self.logs / f"{name}.stderr.log"
        start = utc_now()
        monotonic_start = time.monotonic()
        process: subprocess.Popen[str] | None = None
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=dict(env),
                text=True,
                stdin=subprocess.PIPE if input_text is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stdout, stderr = process.communicate(input=input_text, timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, stderr = process.communicate(timeout=5)
                stdout_path.write_text(stdout, encoding="utf-8")
                stderr_path.write_text(stderr, encoding="utf-8")
                self._append_command({
                    "name": name, "argv": command, "cwd": str(cwd), "env_keys": sorted(env),
                    "started_at": start, "ended_at": utc_now(), "duration_seconds": time.monotonic() - monotonic_start,
                    "exit_code": process.returncode, "error": f"timeout after {timeout}s", "stdout_log": str(stdout_path),
                    "stderr_log": str(stderr_path), "trace": str(trace_path) if trace_path else None,
                })
                raise HarnessStop(f"{name} timed out after {timeout}s; process group terminated", status="EVIDENCE_NEEDED") from exc
            completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        except OSError as exc:
            stdout_path.write_text("", encoding="utf-8")
            stderr_path.write_text(str(exc) + "\n", encoding="utf-8")
            self._append_command({
                "name": name, "argv": command, "cwd": str(cwd), "env_keys": sorted(env),
                "started_at": start, "ended_at": utc_now(), "duration_seconds": time.monotonic() - monotonic_start,
                "exit_code": None, "error": str(exc), "stdout_log": str(stdout_path),
                "stderr_log": str(stderr_path), "trace": str(trace_path) if trace_path else None,
            })
            raise HarnessStop(f"{name} could not execute: {exc}", status="EVIDENCE_NEEDED") from exc
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        self._append_command({
            "name": name, "argv": command, "cwd": str(cwd), "env_keys": sorted(env),
            "started_at": start, "ended_at": utc_now(), "duration_seconds": time.monotonic() - monotonic_start,
            "exit_code": completed.returncode, "stdout_log": str(stdout_path),
            "stderr_log": str(stderr_path), "trace": str(trace_path) if trace_path else None,
        })
        if trace_path is not None:
            self.assert_clean_trace(name, trace_path)
        return completed

    def assert_clean_text(self, label: str, text: str, *, allow_project: bool = False) -> None:
        denied = PERSONAL_PATH_PARTS if allow_project else self.denied
        hits = [needle for needle in denied if needle in text]
        if hits:
            raise HarnessStop(f"{label} contains denied path material: {hits}")

    def assert_clean_trace(self, name: str, trace_path: Path) -> None:
        if not trace_path.is_file() or trace_path.stat().st_size == 0:
            raise HarnessStop(f"{name} did not produce a usable strace", status="EVIDENCE_NEEDED")
        self.assert_clean_text(f"trace {name}", trace_path.read_text(encoding="utf-8", errors="replace"))

    def preflight(self) -> None:
        if self.project_root != PROJECT_ROOT:
            raise HarnessStop(f"unexpected project root: {self.project_root}")
        self.assert_clean_text("work root", str(self.work_root), allow_project=True)
        self.assert_clean_text("evidence directory", str(self.evidence), allow_project=True)
        if any(not element or not os.path.isabs(element) for element in self.system_path.split(os.pathsep)):
            raise HarnessStop("--system-path must contain only non-empty absolute directories")
        self.assert_clean_text("system PATH", self.system_path)

        required = ("node", "npm", "pnpm", "python3", "strace")
        versions: dict[str, str] = {}
        clean_env = {"HOME": str(self.work_root / "build-home"), "PATH": self.system_path, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        Path(clean_env["HOME"]).mkdir(parents=True, exist_ok=True)
        for name in required:
            candidate = shutil.which(name, path=self.system_path)
            if candidate is None:
                raise HarnessStop(f"required clean tool is unavailable: {name}", status="EVIDENCE_NEEDED")
            resolved = Path(candidate).resolve(strict=True)
            self.assert_clean_text(f"{name} realpath", str(resolved))
            self.tool_paths[name] = resolved
            version_args = [str(resolved), "--version"]
            completed = self.run(f"preflight-{name}", version_args, cwd=self.work_root, env=clean_env, timeout=30)
            if completed.returncode != 0:
                raise HarnessStop(f"{name} --version failed", status="EVIDENCE_NEEDED")
            versions[name] = (completed.stdout or completed.stderr).strip().splitlines()[0]
        node_match = re.search(r"(?:^|\D)(\d+)(?:\.\d+)", versions["node"])
        if node_match is None or int(node_match.group(1)) < 24:
            raise HarnessStop(f"Node >=24 required, observed {versions['node']}", status="EVIDENCE_NEEDED")
        python_match = re.search(r"Python\s+(\d+)\.(\d+)", versions["python3"])
        if python_match is None or (int(python_match.group(1)), int(python_match.group(2))) < (3, 11):
            raise HarnessStop(f"Python >=3.11 required, observed {versions['python3']}", status="EVIDENCE_NEEDED")

        chrome = self.args.chrome_path
        if chrome is None:
            for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
                candidate = shutil.which(name, path=self.system_path)
                if candidate:
                    chrome = Path(candidate)
                    break
        if chrome is None:
            raise HarnessStop("approved Chrome executable is unavailable", status="EVIDENCE_NEEDED")
        chrome = chrome.resolve(strict=True)
        self.assert_clean_text("Chrome realpath", str(chrome))
        self.tool_paths["chrome"] = chrome
        chrome_version = self.run("preflight-chrome", [chrome, "--version"], cwd=self.work_root, env=clean_env, timeout=30)
        if chrome_version.returncode != 0:
            raise HarnessStop("Chrome --version failed", status="EVIDENCE_NEEDED")
        versions["chrome"] = (chrome_version.stdout or chrome_version.stderr).strip().splitlines()[0]
        write_json(self.evidence / "env.json", {
            "system_path": self.system_path,
            "tools": {name: str(path) for name, path in self.tool_paths.items()},
            "versions": versions,
            "denied_path_parts": list(self.denied),
        })
        self.result("preflight", "PASS", "clean system toolchain passed denylist and version gates", env=str(self.evidence / "env.json"))

    def build_env(self) -> dict[str, str]:
        return {
            "HOME": str(self.work_root / "build-home"),
            "PATH": self.system_path,
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
            "TMPDIR": str(self.work_root / "tmp"),
            "npm_config_userconfig": str(self.work_root / "empty-npmrc"),
            "NPM_CONFIG_USERCONFIG": str(self.work_root / "empty-npmrc"),
        }

    def make_consumer_env(self) -> dict[str, str]:
        venv_bin = self.work_root / "venv" / "bin"
        npm_bin = self.work_root / "npm" / "node_modules" / ".bin"
        env = {
            "HOME": str(self.work_root / "home"),
            "ORACLE_HOME_DIR": str(self.work_root / "home" / ".oracle"),
            "ORACLE_BROWSER_SLOTS_STATE_ROOT": str(self.work_root / "slot-state"),
            "ORACLE_BROWSER_SLOTS_PROFILE_ROOT": str(self.work_root / "profiles"),
            "ORACLE_BROWSER_SLOTS_CHROME_PATH": str(self.tool_paths["chrome"]),
            "ORACLE_BROWSER_SLOTS_PORT_BASE": str(self.args.port_base),
            "ORACLE_BROWSER_SLOTS_CDP_START_TIMEOUT": "30",
            "ORACLE_BROWSER_SLOTS_CDP_REQUEST_TIMEOUT": "2",
            "ORACLE_BROWSER_SLOTS_QUEUE_POLL_INTERVAL": "0.05",
            "TMPDIR": str(self.work_root / "tmp"),
            "PATH": os.pathsep.join((str(venv_bin), str(npm_bin), self.system_path)),
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
        }
        for key, value in env.items():
            self.assert_clean_text(f"consumer env {key}", value)
        return env

    def stage(self) -> None:
        if self.args.resume:
            if not self.artifacts_path.is_file():
                raise HarnessStop("resume requires evidence/artifacts.json")
            self.artifacts = read_json(self.artifacts_path)
            for key in ("npm_tarball", "python_wheel"):
                record = self.artifacts.get(key)
                if not isinstance(record, dict):
                    raise HarnessStop(f"resume artifact record missing: {key}")
                path = Path(str(record.get("path", ""))).resolve(strict=True)
                if sha256_file(path) != record.get("sha256"):
                    raise HarnessStop(f"resume artifact digest changed: {key}")
            self.consumer_env = self.make_consumer_env()
            self.result("staging", "PASS", "resumed immutable staged artifacts after SHA-256 readback", artifacts=str(self.artifacts_path))
            return

        for relative in ("artifacts/npm", "artifacts/python", "run/nested", "tmp", "home", "slot-state", "profiles"):
            (self.work_root / relative).mkdir(parents=True, exist_ok=True)
        (self.work_root / "empty-npmrc").write_text("", encoding="utf-8")
        build_env = self.build_env()
        pack = self.run(
            "pack-npm",
            [self.tool_paths["pnpm"], "pack", "--pack-destination", self.work_root / "artifacts/npm"],
            cwd=self.project_root, env=build_env, timeout=1800,
        )
        if pack.returncode != 0:
            raise HarnessStop("pnpm pack failed")
        wheel = self.run(
            "build-wheel",
            [self.tool_paths["python3"], "-m", "pip", "wheel", "--no-deps", "--wheel-dir", self.work_root / "artifacts/python", self.project_root / "oracle-browser-slots"],
            cwd=self.project_root, env=build_env, timeout=600,
        )
        if wheel.returncode != 0:
            raise HarnessStop("pip wheel failed")
        tarballs = list((self.work_root / "artifacts/npm").glob("*.tgz"))
        wheels = list((self.work_root / "artifacts/python").glob("*.whl"))
        if len(tarballs) != 1 or len(wheels) != 1:
            raise HarnessStop(f"expected exactly one npm tarball and wheel, got {len(tarballs)} and {len(wheels)}")
        tarball, wheel_path = tarballs[0].resolve(), wheels[0].resolve()
        self.artifacts = {
            "npm_tarball": {"path": str(tarball), "sha256": sha256_file(tarball)},
            "python_wheel": {"path": str(wheel_path), "sha256": sha256_file(wheel_path)},
        }
        write_json(self.artifacts_path, self.artifacts)

        create_venv = self.run("create-venv", [self.tool_paths["python3"], "-m", "venv", self.work_root / "venv"], cwd=self.work_root, env=build_env)
        if create_venv.returncode != 0:
            raise HarnessStop("venv creation failed")
        install_wheel = self.run(
            "install-wheel", [self.work_root / "venv/bin/python", "-m", "pip", "install", "--no-index", "--no-deps", wheel_path],
            cwd=self.work_root, env=build_env,
        )
        if install_wheel.returncode != 0:
            raise HarnessStop("wheel installation failed")
        install_npm = self.run(
            "install-npm", [self.tool_paths["npm"], "install", "--prefix", self.work_root / "npm", "--ignore-scripts", "--no-audit", "--no-fund", tarball],
            cwd=self.work_root, env=build_env, timeout=600,
        )
        if install_npm.returncode != 0:
            raise HarnessStop("npm artifact installation failed")
        self.consumer_env = self.make_consumer_env()
        self.result("staging", "PASS", "packed artifacts installed into isolated npm prefix and venv", artifacts=str(self.artifacts_path))

    @property
    def oracle(self) -> Path:
        return self.work_root / "npm/node_modules/.bin/oracle"

    @property
    def wrapper(self) -> Path:
        return self.work_root / "venv/bin/oracle-browser-slots"

    def scenario1(self) -> None:
        run_cwd = self.work_root / "run"
        python = self.work_root / "venv/bin/python"
        for path in (self.oracle, self.wrapper, python):
            if not path.exists():
                raise HarnessStop(f"installed entry is missing: {path}")
        version = self.run("s1-version", [self.oracle, "--version"], cwd=run_cwd, env=self.consumer_env, traced=True)
        if version.returncode != 0 or version.stdout.strip() != ORACLE_VERSION:
            raise HarnessStop(f"installed oracle version mismatch: {version.stdout.strip()!r}")
        capability = self.run(
            "s1-capability", [self.oracle, "runtime", "file-selection", "--capability", "--json"],
            cwd=run_cwd, env=self.consumer_env, traced=True,
        )
        try:
            capability_json = json.loads(capability.stdout)
        except json.JSONDecodeError as exc:
            raise HarnessStop("file-selection capability did not return JSON") from exc
        package = capability_json.get("package", {}) if isinstance(capability_json, dict) else {}
        if not (
            capability.returncode == 0 and capability_json.get("ok") is True
            and capability_json.get("schema") == SELECTOR_SCHEMA
            and package.get("name") == "@steipete/oracle" and package.get("version") == ORACLE_VERSION
        ):
            raise HarnessStop("installed selector capability identity mismatch")
        status = self.run("s1-wrapper-status", [self.wrapper, "status"], cwd=run_cwd, env=self.consumer_env, traced=True)
        if status.returncode != 0:
            raise HarnessStop("installed wrapper status failed")
        probe_code = (
            "import dataclasses,json,oracle_browser_slots;"
            "from oracle_browser_slots.runtime import resolve_oracle_runtime;"
            "r=resolve_oracle_runtime();"
            "print(json.dumps({'module':oracle_browser_slots.__file__,'runtime':dataclasses.asdict(r)},sort_keys=True,default=str))"
        )
        probe = self.run("s1-runtime-probe", [python, "-c", probe_code], cwd=run_cwd, env=self.consumer_env, traced=True)
        if probe.returncode != 0:
            raise HarnessStop("installed Python runtime resolver probe failed")
        identity = json.loads(probe.stdout)
        module_path = Path(identity["module"]).resolve(strict=True)
        runtime = identity["runtime"]
        entry = Path(runtime["oracle_entry"]).resolve(strict=True)
        package_root = Path(runtime["package_root"]).resolve(strict=True)
        node = Path(runtime["node_path"]).resolve(strict=True)
        if not path_is_below(module_path, self.work_root / "venv"):
            raise HarnessStop(f"Python module escaped venv: {module_path}")
        if not path_is_below(entry, self.work_root / "npm") or not path_is_below(package_root, self.work_root / "npm"):
            raise HarnessStop("resolved Oracle entry/package escaped isolated npm prefix")
        if node != self.tool_paths["node"]:
            raise HarnessStop(f"resolved Node differs from approved tool: {node}")
        if runtime.get("package_version") != ORACLE_VERSION or runtime.get("selector_protocol") != SELECTOR_SCHEMA:
            raise HarnessStop("resolver identity fields mismatch")
        entry_sha = sha256_file(entry)
        if runtime.get("oracle_entry_sha256") != entry_sha:
            raise HarnessStop("resolver entry SHA-256 mismatch")
        if capability_json.get("entry_sha256") not in (None, entry_sha):
            raise HarnessStop("selector entry SHA-256 mismatch")
        self.artifacts["installed_runtime"] = {
            "oracle_entry": str(entry), "oracle_entry_sha256": entry_sha,
            "package_root": str(package_root), "python_module": str(module_path), "node": str(node),
            "capability": capability_json,
        }
        write_json(self.artifacts_path, self.artifacts)

    def prepare_slot(self) -> None:
        if self.args.cookie_seed is not None:
            source = self.args.cookie_seed.resolve(strict=True)
            destination = self.work_root / "profiles" / f"slot-{self.args.slot}" / "Default" / "Cookies"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            write_json(self.before / "login-seed.json", {
                "destination": str(destination),
                "sha256": sha256_file(destination),
                "size_bytes": destination.stat().st_size,
            })
        prepare = self.run("slot-prepare", [self.wrapper, "prepare", "--slot", str(self.args.slot)], cwd=self.work_root / "run", env=self.consumer_env, timeout=60)
        status = self.run("slot-status", [self.wrapper, "status", "--slot", str(self.args.slot)], cwd=self.work_root / "run", env=self.consumer_env, traced=True)
        write_json(self.before / "prepared-slot.json", {"prepare": self._json_or_text(prepare.stdout), "status": self._json_or_text(status.stdout)})
        if prepare.returncode != 0 or status.returncode != 0:
            raise HarnessStop("isolated slot could not be prepared; manual login may be required", status="EVIDENCE_NEEDED")
        payload = self._json_or_text(status.stdout)
        slot = payload.get("slot", {}) if isinstance(payload, dict) else {}
        if slot.get("status") != "사용 가능" or slot.get("occupancy") is not None or slot.get("requires_reprepare") is True:
            raise HarnessStop("isolated slot is not AVAILABLE with null occupancy", status="EVIDENCE_NEEDED")
        self.result("prepared-slot", "PASS", "isolated slot is prepared and available", state=str(self.before / "prepared-slot.json"))

    @staticmethod
    def _json_or_text(text: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def dry_run_argv(self, job_id: str, *, files: bool) -> list[str]:
        argv = [
            str(self.wrapper), "run", "--slot", str(self.args.slot), "--job-id", job_id, "--",
            "oracle", "--engine", "browser", "--browser-model-strategy", "current", "--dry-run", "summary",
        ]
        if files:
            argv.extend([
                "--files-report", "-p", f"B4 clean files {job_id}",
                "--file", "a.txt", "--file", "nested",
            ])
        else:
            argv.extend(["-p", f"B4 clean no-file {job_id}"])
        return argv

    def _trace_execve_argvs(self, trace: Path) -> list[list[str]]:
        argvs: list[list[str]] = []
        pattern = re.compile(r'execve\("(?:[^"\\]|\\.)*", \[(.*?)\],')
        quoted = re.compile(r'"((?:[^"\\]|\\.)*)"')
        for line in trace.read_text(encoding="utf-8", errors="replace").splitlines():
            match = pattern.search(line)
            if not match:
                continue
            values = []
            for item in quoted.findall(match.group(1)):
                try:
                    values.append(json.loads('"' + item + '"'))
                except json.JSONDecodeError:
                    values.append(item)
            if values:
                argvs.append(values)
        return argvs

    def _assert_child_timeout(self, name: str) -> list[str]:
        argvs = self._trace_execve_argvs(self.traces / f"{name}.log")
        children = [
            argv for argv in argvs
            if any("oracle-cli.js" in token for token in argv) and "--dry-run" in argv
        ]
        if len(children) != 1:
            raise HarnessStop(f"{name} expected one installed Oracle child execve, observed {len(children)}")
        child = children[0]
        occurrences = option_pairs(child, "--browser-timeout")
        if len(occurrences) != 1 or occurrences[0][1] != "2h":
            raise HarnessStop(f"{name} child did not contain exactly one intrinsic --browser-timeout 2h")
        return child

    def scenario2(self) -> None:
        nonce = uuid.uuid4().hex[:12]
        run_cwd = self.work_root / "run"
        (run_cwd / "a.txt").write_text("alpha\n", encoding="utf-8")
        (run_cwd / "nested/b.txt").write_text("beta\n", encoding="utf-8")

        nofile = self.run(
            "s2-nofile", self.dry_run_argv(f"b4-nofile-{nonce}", files=False),
            cwd=run_cwd, env=self.consumer_env, traced=True, timeout=180,
        )
        if nofile.returncode != 0:
            raise HarnessStop("no-file dry-run failed")
        nofile_records = json_objects(nofile.stderr)
        if any(record.get("event") == "attachment_prepared" for record in nofile_records):
            raise HarnessStop("no-file dry-run emitted attachment_prepared")
        nofile_child = self._assert_child_timeout("s2-nofile")
        nofile_trace = (self.traces / "s2-nofile.log").read_text(encoding="utf-8", errors="replace")
        if "oracle-browser-slots-zip-" in nofile_trace or "oracle-attachments.zip" in nofile_trace:
            raise HarnessStop("no-file dry-run trace observed ZIP creation or access")
        if list((self.work_root / "tmp").glob("oracle-browser-slots-zip-*/*.zip")):
            raise HarnessStop("no-file dry-run left a ZIP")

        name = "s2-files"
        files_argv = self.dry_run_argv(f"b4-files-{nonce}", files=True)
        process, stdout_file, stderr_file, started = self._start_traced(name, files_argv)
        stderr_path = self.logs / f"{name}.stderr.log"
        deadline = time.monotonic() + 180
        paused = False
        while time.monotonic() < deadline and process.poll() is None:
            text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
            if any(record.get("event") == "attachment_prepared" for record in json_objects(text)):
                os.killpg(process.pid, signal.SIGSTOP)
                paused = True
                break
            time.sleep(0.01)
        if not paused:
            code = self._settle_async(name, process, stdout_file, stderr_file, started, timeout=10)
            raise HarnessStop(f"file-bearing process ended before deterministic ZIP pause (exit {code})", status="EVIDENCE_NEEDED")
        try:
            zip_paths = list((self.work_root / "tmp").glob("oracle-browser-slots-zip-*/oracle-attachments.zip"))
            if len(zip_paths) != 1:
                raise HarnessStop(f"paused file-bearing request expected one live ZIP, observed {len(zip_paths)}")
            captured_zip = self.logs / "s2-files.generated.zip"
            shutil.copyfile(zip_paths[0], captured_zip)
            with zipfile.ZipFile(captured_zip) as archive:
                file_infos = [info for info in archive.infolist() if not info.is_dir()]
                members = sorted(info.filename for info in file_infos)
                compressed = bool(file_infos) and all(info.compress_type == zipfile.ZIP_DEFLATED for info in file_infos)
            if members != ["a.txt", "nested/b.txt"] or not compressed:
                raise HarnessStop(f"generated ZIP mismatch: members={members}, compressed={compressed}")
            if any(Path(member).is_absolute() or ".." in Path(member).parts for member in members):
                raise HarnessStop(f"generated ZIP contains unsafe member path: {members}")
        finally:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGCONT)

        files_code = self._settle_async(name, process, stdout_file, stderr_file, started, timeout=60)
        files_stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
        if files_code != 0:
            raise HarnessStop("file-bearing dry-run failed after ZIP inspection")
        file_records = json_objects(files_stderr)
        prepared = [record for record in file_records if record.get("event") == "attachment_prepared"]
        if len(prepared) != 1:
            raise HarnessStop(f"expected one attachment_prepared record, observed {len(prepared)}")
        selected = prepared[0].get("selected_files")
        selected_paths = sorted(item.get("relative_path") for item in selected if isinstance(item, dict)) if isinstance(selected, list) else []
        if selected_paths != ["a.txt", "nested/b.txt"]:
            raise HarnessStop(f"selected file set mismatch: {selected_paths}")
        generated = prepared[0].get("generated_zip")
        captured_sha = sha256_file(captured_zip)
        if not isinstance(generated, dict) or generated.get("name") != "oracle-attachments.zip" or generated.get("sha256") != captured_sha:
            raise HarnessStop("lifecycle ZIP identity does not match captured ZIP")
        final_records = [record for record in file_records if "generated_zip_cleanup" in record]
        if not final_records or final_records[-1]["generated_zip_cleanup"].get("removed") is not True:
            raise HarnessStop("generated ZIP cleanup was not observed")
        file_child = self._assert_child_timeout(name)
        child_files = [value for _, value in option_pairs(file_child, "--file")]
        if len(child_files) != 1 or not child_files[0] or not child_files[0].endswith("oracle-attachments.zip"):
            raise HarnessStop("file-bearing child did not receive exactly one normalized ZIP")
        if list((self.work_root / "tmp").glob("oracle-browser-slots-zip-*")):
            raise HarnessStop("file-bearing request-owned temp directory was not cleaned")
        final_slot = self._slot_state(self.args.slot)
        if not isinstance(final_slot, dict) or final_slot.get("occupancy") is not None:
            raise HarnessStop("prepared slot occupancy did not close after dry-runs")
        write_json(self.after / "scenario2.json", {
            "no_file_child_argv": nofile_child,
            "file_child_argv": file_child,
            "attachment_prepared": prepared[0],
            "terminal": final_records[-1],
            "captured_zip": {"path": str(captured_zip), "sha256": captured_sha, "members": members, "compressed": compressed},
            "final_slot": final_slot,
        })
        self.result("scenario1", "PASS", "clean installed identity, status, prepare, and no-file dry-run completed", artifacts=str(self.artifacts_path), slot=str(self.before / "prepared-slot.json"))
        self.result("scenario2", "PASS", "file-free zero ZIP and deterministic single compressed ZIP lifecycle passed", readback=str(self.after / "scenario2.json"))

    def _start_traced(self, name: str, argv: Sequence[str]) -> tuple[subprocess.Popen[str], Any, Any, float]:
        trace = self.traces / f"{name}.log"
        command = [str(self.tool_paths["strace"]), "-f", "-qq", "-s", "8192", "-e", "trace=%file,process", "-o", str(trace), "--", *argv]
        stdout_path = self.logs / f"{name}.stdout.log"
        stderr_path = self.logs / f"{name}.stderr.log"
        stdout_file = stdout_path.open("w", encoding="utf-8")
        stderr_file = stderr_path.open("w", encoding="utf-8")
        started = time.monotonic()
        process = subprocess.Popen(command, cwd=self.work_root / "run", env=self.consumer_env, text=True, stdout=stdout_file, stderr=stderr_file, start_new_session=True)
        self._append_command({"name": name, "argv": command, "cwd": str(self.work_root / "run"), "env_keys": sorted(self.consumer_env), "started_at": utc_now(), "exit_code": "pending", "stdout_log": str(stdout_path), "stderr_log": str(stderr_path), "trace": str(trace)})
        return process, stdout_file, stderr_file, started

    def _settle_async(self, name: str, process: subprocess.Popen[str], stdout_file: Any, stderr_file: Any, started: float, timeout: float = 30) -> int:
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait(timeout=5)
        stdout_file.close()
        stderr_file.close()
        self._append_command({"name": name, "settled_at": utc_now(), "duration_seconds": time.monotonic() - started, "exit_code": code})
        trace = self.traces / f"{name}.log"
        if trace.exists():
            self.assert_clean_trace(name, trace)
        return code

    def _slot_state(self, slot_id: int) -> dict[str, Any] | None:
        path = self.work_root / "slot-state" / f"slot-{slot_id}.json"
        try:
            value = read_json(path)
        except (OSError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def _state_bytes(self, slot_id: int) -> bytes | None:
        path = self.work_root / "slot-state" / f"slot-{slot_id}.json"
        return path.read_bytes() if path.is_file() else None
    @staticmethod
    def _slot_ownership(value: bytes | None) -> dict[str, Any] | None:
        if value is None:
            return None
        state = json.loads(value)
        return {
            key: state.get(key)
            for key in ("schema_version", "slot_id", "port", "profile_dir", "prepared", "requires_reprepare", "prepared_at", "browser_pid", "occupancy")
        }

    def _oracle_child_count(self, trace_name: str) -> int:
        return sum(
            1 for argv in self._trace_execve_argvs(self.traces / f"{trace_name}.log")
            if any("oracle-cli.js" in token for token in argv) and "--dry-run" in argv
        )

    def _session_snapshot(self) -> list[str]:
        root = self.work_root / "home/.oracle/sessions"
        if not root.exists():
            return []
        return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())

    def scenario3(self) -> None:
        nonce = uuid.uuid4().hex[:12]
        unready_slot = next(slot for slot in (1, 2, 3, 4, 5, 10) if slot != self.args.slot)
        run_cwd = self.work_root / "run"
        sessions_before = self._session_snapshot()

        unready_status_before = self.run(
            "s3-unready-status-before", [self.wrapper, "status", "--slot", str(unready_slot)],
            cwd=run_cwd, env=self.consumer_env, traced=True,
        )
        unready_state_before = self._state_bytes(unready_slot)
        unready_argv = [
            str(self.wrapper), "run", "--slot", str(unready_slot), "--job-id", f"b4-unready-{nonce}", "--",
            "oracle", "--engine", "browser", "--browser-model-strategy", "current",
            "--dry-run", "summary", "-p", f"B4 unready {nonce}",
        ]
        unready = self.run("s3-unready", unready_argv, cwd=run_cwd, env=self.consumer_env, traced=True)
        unready_state_after = self._state_bytes(unready_slot)
        unready_status_after = self.run(
            "s3-unready-status-after", [self.wrapper, "status", "--slot", str(unready_slot)],
            cwd=run_cwd, env=self.consumer_env, traced=True,
        )
        unready_records = json_objects(unready.stderr)
        if unready_status_before.returncode != 0 or unready_status_after.returncode != 0:
            raise HarnessStop("unready slot status readback failed")
        if unready.returncode != 2 or not any(record.get("event") == "rejected" for record in unready_records):
            raise HarnessStop("unready slot did not reject with lifecycle event and exit 2")
        if self._oracle_child_count("s3-unready") != 0:
            raise HarnessStop("unready slot rejection spawned an Oracle child")
        if unready_state_before != unready_state_after:
            raise HarnessStop("unready slot rejection polluted slot state")
        unready_payload = self._json_or_text(unready_status_after.stdout)
        unready_record = unready_payload.get("slot", {}) if isinstance(unready_payload, dict) else {}
        if unready_record.get("occupancy") is not None:
            raise HarnessStop("unready slot acquired occupancy")

        prepared_status_before = self.run(
            "s3-invalid-status-before", [self.wrapper, "status", "--slot", str(self.args.slot)],
            cwd=run_cwd, env=self.consumer_env, traced=True,
        )
        prepared_state_before = self._state_bytes(self.args.slot)
        invalid_argv = [
            str(self.wrapper), "run", "--slot", str(self.args.slot), "--job-id", f"b4-invalid-{nonce}", "--",
            "oracle", "--engine", "browser", "--browser-model-strategy", "current",
            "--browser-timeout", "1h", "--browser-timeout", "2h",
            "--dry-run", "summary", "-p", f"B4 invalid {nonce}",
        ]
        invalid = self.run("s3-invalid", invalid_argv, cwd=run_cwd, env=self.consumer_env, traced=True)
        prepared_state_after = self._state_bytes(self.args.slot)
        if self._slot_ownership(prepared_state_before) != self._slot_ownership(prepared_state_after):
            raise HarnessStop("invalid pre-claim rejection changed prepared slot ownership state")
        prepared_status_after = self.run(
            "s3-invalid-status-after", [self.wrapper, "status", "--slot", str(self.args.slot)],
            cwd=run_cwd, env=self.consumer_env, traced=True,
        )
        invalid_records = json_objects(invalid.stderr)
        if prepared_status_before.returncode != 0 or prepared_status_after.returncode != 0:
            raise HarnessStop("prepared slot status readback failed around invalid command")
        if invalid.returncode != 2 or not any(record.get("event") == "rejected" for record in invalid_records):
            raise HarnessStop("invalid duplicate timeout did not reject with lifecycle event and exit 2")
        if self._oracle_child_count("s3-invalid") != 0:
            raise HarnessStop("invalid option rejection spawned an Oracle child")
        if self._session_snapshot() != sessions_before:
            raise HarnessStop("negative scenarios created session artifacts")

        write_json(self.after / "scenario3.json", {
            "unready_slot": unready_slot,
            "unready_exit_code": unready.returncode,
            "unready_records": unready_records,
            "unready_state_unchanged": unready_state_before == unready_state_after,
            "prepared_state_unchanged": self._slot_ownership(prepared_state_before) == self._slot_ownership(prepared_state_after),
            "prepared_state_sha256": {
                "before": hashlib.sha256(prepared_state_before).hexdigest() if prepared_state_before is not None else None,
                "after": hashlib.sha256(prepared_state_after).hexdigest() if prepared_state_after is not None else None,
            },
            "invalid_exit_code": invalid.returncode,
            "invalid_records": invalid_records,
            "oracle_child_exec_count": {"unready": 0, "invalid": 0},
            "sessions_unchanged": True,
        })
        self.result("scenario3", "PASS", "unready slot and invalid options failed closed with exit 2, zero child, and unchanged state", readback=str(self.after / "scenario3.json"))

    def execute(self) -> int:
        try:
            self.preflight()
            if self.args.preflight_only:
                return self.finish()
            self.stage()
            self.scenario1()
            if self.args.stage_only:
                return self.finish()
            self.prepare_slot()
            self.scenario2()
            self.scenario3()
        except HarnessStop as exc:
            self.result("halt", exc.status, exc.reason)
        except KeyboardInterrupt:
            self.result("halt", "EVIDENCE_NEEDED", "operator interrupted execution; work root preserved")
        except Exception as exc:
            self.result("halt", "FAIL", f"unexpected harness failure: {type(exc).__name__}: {exc}")
        return self.finish()


def build_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run B4 clean installed-artifact E2E scenarios without prompt submission.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--system-path", default=DEFAULT_SYSTEM_PATH)
    parser.add_argument("--chrome-path", type=Path)
    parser.add_argument("--slot", type=int, choices=(1, 2, 3, 4, 5, 10), default=1)
    parser.add_argument("--port-base", type=int, default=29222)
    parser.add_argument("--cookie-seed", type=Path, help="approved read-only Chrome Cookies DB copied into the isolated slot profile before prepare")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--stage-only", action="store_true")
    args = parser.parse_args()
    if args.resume and args.work_root:
        parser.error("--resume and --work-root are mutually exclusive")
    if args.preflight_only and args.stage_only:
        parser.error("--preflight-only and --stage-only are mutually exclusive")
    if not 1 <= args.port_base <= 65526:
        parser.error("--port-base must be between 1 and 65526")
    return args


def main() -> int:
    return Harness(build_parser()).execute()


if __name__ == "__main__":
    raise SystemExit(main())
