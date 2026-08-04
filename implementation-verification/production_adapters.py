from __future__ import annotations

import ctypes
import json
import os
import shutil
import stat
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from implementation_execution import AdoptionConflict, ImplementationBlocker, _capture, _entry, _sha256_bytes
from implementation_verification import Candidate


_RENAME_NOREPLACE = 1
_RENAME_EXCHANGE = 2
_AT_FDCWD = -100
_LIBC = ctypes.CDLL(None, use_errno=True)
_RENAMEAT2 = getattr(_LIBC, "renameat2", None)


def _json_default(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        default=_json_default,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _artifact_identity(value: object) -> str:
    return __import__("hashlib").sha256(_json_bytes(value)).hexdigest()


def _candidate_projection(candidate: Candidate) -> dict[str, object]:
    return {
        "work": str(candidate.work),
        "planning": candidate.planning,
        "acceptanceCriteria": list(candidate.acceptance_criteria),
        "sourceIdentity": candidate.source["identity"],
        "implementationChanges": list(candidate.implementation_changes),
        "preservedChanges": list(candidate.preserved_changes),
        "candidateIdentity": candidate.result_identity,
    }


def _require_bwrap() -> str:
    executable = shutil.which("bwrap")
    if executable is None:
        raise RuntimeError("bubblewrap is required for physical isolation")
    probe = subprocess.run(
        [
            executable,
            "--unshare-all",
            "--die-with-parent",
            "--ro-bind",
            "/",
            "/",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "/usr/bin/true",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=10,
        check=False,
    )
    if probe.returncode != 0:
        raise RuntimeError("bubblewrap user/mount namespaces are unavailable")
    return executable


def _runtime_mounts() -> list[str]:
    arguments: list[str] = []
    for path in ("/usr", "/bin", "/lib", "/lib64", "/etc/alternatives"):
        if Path(path).exists():
            arguments.extend(("--ro-bind", path, path))
    return arguments


def _sandbox_command(
    *,
    writable: Iterable[tuple[Path, str]] = (),
    readable: Iterable[tuple[Path, str]] = (),
    cwd: str,
    argv: tuple[str, ...],
) -> list[str]:
    bwrap = _require_bwrap()
    command = [
        bwrap,
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/input",
    ]
    command.extend(_runtime_mounts())
    for source, target in readable:
        command.extend(("--ro-bind", str(source), target))
    for source, target in writable:
        command.extend(("--bind", str(source), target))
    command.extend(("--chdir", cwd, "--"))
    command.extend(argv)
    return command


@dataclass(frozen=True)
class ProcessWorker:
    durable_identity: str
    argv: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.durable_identity or not self.argv:
            raise ValueError("process Worker requires an identity and argv")


@dataclass(frozen=True)
class ProcessImplementationReview:
    argv: tuple[str, ...]
    timeout_seconds: float = 300

    def __post_init__(self) -> None:
        if not self.argv or any(not isinstance(item, str) or not item for item in self.argv):
            raise TypeError("implementation review requires a non-empty argv tuple")
        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0:
            raise ValueError("implementation review timeout must be positive")


@dataclass(frozen=True)
class ProcessImplementationCheck:
    argv: tuple[str, ...]
    timeout_seconds: float = 300
    requires_effect_adapter: bool = False

    def __post_init__(self) -> None:
        if not self.argv or any(not isinstance(item, str) or not item for item in self.argv):
            raise TypeError("implementation check requires a non-empty argv tuple")
        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0:
            raise ValueError("implementation check timeout must be positive")
        if not isinstance(self.requires_effect_adapter, bool):
            raise TypeError("implementation check effect requirement must be boolean")


class LinuxImplementationReviewAdapter:
    """Runs Module-owned review and check processes in read-only source namespaces."""

    variant = "bubblewrap-module-owned-implementation-review-v1"
    _MAX_OUTPUT_BYTES = 1_000_000

    def __init__(
        self,
        review: ProcessImplementationReview,
        check: ProcessImplementationCheck,
        *,
        effect_adapter_enabled: bool,
    ) -> None:
        self._review = review
        self._check = check
        self._effect_adapter_enabled = effect_adapter_enabled

    @staticmethod
    def _projection(work: Path, source: Path, operation: str) -> dict[str, object]:
        source_root = source.resolve(strict=True)
        _, source_identity = _capture(source_root)
        raw_work = work.read_bytes()
        return {
            "operation": operation,
            "work": {
                "path": "/input/ticket.md",
                "sha256": _sha256_bytes(raw_work),
            },
            "source": {"root": "/source", "identity": source_identity},
        }

    def _run_json_process(
        self,
        *,
        work: Path,
        source: Path,
        operation: str,
        argv: tuple[str, ...],
        timeout_seconds: float,
        label: str,
    ) -> dict[str, object] | ImplementationBlocker:
        executable = Path(argv[0])
        if not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK):
            return ImplementationBlocker(f"production implementation {label} is unavailable")
        try:
            projection = self._projection(work, source, operation)
        except Exception:
            return ImplementationBlocker(f"production implementation {label} input is unavailable")
        try:
            with tempfile.TemporaryDirectory(prefix=f"iv-{label}-input-") as temporary:
                request = Path(temporary) / "request.json"
                request.write_bytes(_json_bytes(projection))
                request.chmod(0o444)
                command = _sandbox_command(
                    readable=(
                        (source.resolve(strict=True), "/source"),
                        (work.resolve(strict=True), "/input/ticket.md"),
                        (request, "/input/request.json"),
                    ),
                    cwd="/source",
                    argv=argv,
                )
                completed = subprocess.run(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout_seconds,
                    check=False,
                )
        except subprocess.TimeoutExpired:
            return ImplementationBlocker(f"production implementation {label} timed out")
        except (OSError, RuntimeError):
            return ImplementationBlocker(f"production implementation {label} is unavailable")
        if completed.returncode != 0:
            return ImplementationBlocker(f"production implementation {label} failed")
        if len(completed.stdout) > self._MAX_OUTPUT_BYTES:
            return ImplementationBlocker(f"production implementation {label} result is unreadable")
        try:
            value = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return ImplementationBlocker(f"production implementation {label} result is unreadable")
        if not isinstance(value, dict):
            return ImplementationBlocker(f"production implementation {label} result is unreadable")
        return value

    def next_assignment(self, work: Path, source: Path) -> object | ImplementationBlocker | None:
        result = self._run_json_process(
            work=work,
            source=source,
            operation="ASSIGNMENT",
            argv=self._review.argv,
            timeout_seconds=self._review.timeout_seconds,
            label="review",
        )
        if isinstance(result, ImplementationBlocker):
            return result
        if result.get("decision") == "CLOSE" and set(result) == {"decision"}:
            return None
        assignment = result.get("assignment")
        if (
            result.get("decision") != "ASSIGN"
            or set(result) != {"decision", "assignment"}
            or not isinstance(assignment, dict)
            or set(assignment) != {"path", "value"}
            or not isinstance(assignment.get("path"), str)
            or not isinstance(assignment.get("value"), str)
        ):
            return ImplementationBlocker("production implementation review result is invalid")
        path = Path(assignment["path"])
        if path.is_absolute() or ".." in path.parts or not path.parts:
            return ImplementationBlocker("production implementation review result is invalid")
        try:
            encoded = _json_bytes(assignment)
        except TypeError:
            return ImplementationBlocker("production implementation review result is invalid")
        if len(encoded) > self._MAX_OUTPUT_BYTES:
            return ImplementationBlocker("production implementation review result is invalid")
        return assignment

    def close(self, work: Path, source: Path) -> ImplementationBlocker | None:
        review = self._run_json_process(
            work=work,
            source=source,
            operation="CLOSURE",
            argv=self._review.argv,
            timeout_seconds=self._review.timeout_seconds,
            label="review",
        )
        if isinstance(review, ImplementationBlocker):
            return review
        if review.get("decision") != "CLOSE" or set(review) != {"decision"}:
            return ImplementationBlocker("production implementation closure did not pass")
        return None

    def check(self, work: Path, source: Path) -> ImplementationBlocker | None:
        if self._check.requires_effect_adapter and not self._effect_adapter_enabled:
            return ImplementationBlocker("dangerous implementation check authority is unavailable")
        check = self._run_json_process(
            work=work,
            source=source,
            operation="CHECK",
            argv=self._check.argv,
            timeout_seconds=self._check.timeout_seconds,
            label="check",
        )
        if isinstance(check, ImplementationBlocker):
            return check
        if check != {"status": "PASSED"}:
            return ImplementationBlocker("production implementation check result is unreadable")
        return None


class LinuxWorkerAdapter:
    isolation_enforced = True
    variant = "bubblewrap-private-workspace-v1"

    def run(
        self,
        worker: object,
        work: Path,
        workspace_root: Path,
        assignment: object,
    ) -> None:
        if not isinstance(worker, ProcessWorker):
            raise TypeError("production Worker must be a ProcessWorker")
        with tempfile.TemporaryDirectory(prefix="iv-worker-input-") as temporary:
            input_root = Path(temporary)
            request = input_root / "request.json"
            request.write_bytes(
                _json_bytes(
                    {
                        "ticket": work.read_text(encoding="utf-8"),
                        "assignment": assignment,
                    }
                )
            )
            request.chmod(0o444)
            command = _sandbox_command(
                writable=((workspace_root.resolve(strict=True), "/workspace"),),
                readable=((request, "/input/request.json"),),
                cwd="/workspace",
                argv=worker.argv,
            )
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,
                check=False,
            )
        if completed.returncode != 0:
            error = completed.stderr.decode("utf-8", errors="replace")[-4000:]
            raise RuntimeError(f"isolated Worker failed ({completed.returncode}): {error}")


@dataclass(frozen=True)
class ProcessVerifier:
    argv: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.argv:
            raise ValueError("fresh verifier requires argv")


class _ProcessVerifierContext:
    def __init__(self, argv: tuple[str, ...], candidate: Candidate, retained_source: Path) -> None:
        self.identity = f"fresh-process:{uuid.uuid4().hex}"
        self._argv = argv
        self._candidate = candidate
        self._retained_source = retained_source.resolve(strict=True)

    def _invoke(self, value: dict[str, object]) -> object:
        with tempfile.TemporaryDirectory(prefix="iv-verifier-input-") as temporary:
            request = Path(temporary) / "request.json"
            request.write_bytes(_json_bytes(value))
            request.chmod(0o444)
            command = _sandbox_command(
                readable=(
                    (self._retained_source, "/candidate"),
                    (request, "/input/request.json"),
                ),
                cwd="/candidate",
                argv=self._argv,
            )
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,
                check=False,
            )
        if completed.returncode != 0:
            raise RuntimeError("isolated fresh verifier failed")
        output = completed.stdout[:1_000_000]
        return json.loads(output.decode("utf-8"))

    def plan(
        self,
        candidate: Candidate,
        retained_source: Path,
        supported_observations: tuple[str, ...],
    ) -> object:
        if candidate != self._candidate or retained_source.resolve(strict=True) != self._retained_source:
            raise ValueError("fresh verifier input changed")
        return self._invoke(
            {
                "operation": "plan",
                "candidate": _candidate_projection(candidate),
                "candidateRoot": "/candidate",
                "supportedObservations": list(supported_observations),
            }
        )

    def assess(
        self,
        candidate: Candidate,
        plan: dict[str, object],
        evidence: tuple[dict[str, object], ...],
    ) -> object:
        if candidate != self._candidate:
            raise ValueError("fresh verifier Candidate changed")
        return self._invoke(
            {
                "operation": "assess",
                "candidate": _candidate_projection(candidate),
                "plan": plan,
                "evidence": list(evidence),
            }
        )


class LinuxFreshVerifierAdapter:
    fresh_context_enforced = True
    read_only_enforced = True
    variant = "bubblewrap-fresh-projection-v1"

    def __init__(self, verifier: ProcessVerifier) -> None:
        self._verifier = verifier

    def open(
        self,
        candidate: Candidate,
        retained_source: Path,
        supported_observations: tuple[str, ...],
        effect_safety: str,
    ) -> _ProcessVerifierContext:
        _require_bwrap()
        return _ProcessVerifierContext(self._verifier.argv, candidate, retained_source)


class LinuxEvidenceRunnerAdapter:
    read_only_enforced = True
    effect_observation_enforced = False
    variant = "bubblewrap-runner-owned-evidence-v1"

    def __init__(self) -> None:
        self.authenticated_read_enforced = False
        self.supported_observations = ("SOURCE", "LOCAL")

    def read_authority(self, candidate: Candidate, observation: dict[str, object]) -> object:
        return None

    @staticmethod
    def _read_only_result(
        readable_root: Path,
        mount_point: str,
        observation: dict[str, object],
        *,
        redacted: bool = False,
    ) -> dict[str, object]:
        attempts: list[dict[str, object]] = []
        status = "COMPLETE"
        for request in observation["requests"]:
            if not isinstance(request, dict) or set(request) != {"path"}:
                attempts.append(
                    {
                        "request": request,
                        "status": "INVALID_REQUEST",
                        "observed": None,
                        "artifact": None,
                        "artifactIdentity": None,
                    }
                )
                status = "TOOL_ERROR"
                continue
            relative = Path(str(request["path"]))
            if relative.is_absolute() or ".." in relative.parts:
                attempts.append(
                    {
                        "request": request,
                        "status": "INVALID_REQUEST",
                        "observed": None,
                        "artifact": None,
                        "artifactIdentity": None,
                    }
                )
                status = "TOOL_ERROR"
                continue
            try:
                command = _sandbox_command(
                    readable=((readable_root.resolve(strict=True), mount_point),),
                    cwd=mount_point,
                    argv=(
                        "/usr/bin/python3",
                        "-c",
                        "import pathlib,sys;sys.stdout.buffer.write(pathlib.Path(sys.argv[1]).read_bytes())",
                        f"{mount_point}/{relative.as_posix()}",
                    ),
                )
                completed = subprocess.run(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=300,
                    check=False,
                )
                if completed.returncode != 0:
                    raise RuntimeError("isolated read failed")
                raw = completed.stdout[:100_000]
                if redacted:
                    observed = {
                        "path": relative.as_posix(),
                        "sha256": __import__("hashlib").sha256(raw).hexdigest(),
                        "byteCount": len(raw),
                    }
                    artifact = dict(observed)
                else:
                    observed = raw.decode("utf-8")
                    artifact = {
                        "path": relative.as_posix(),
                        "sha256": __import__("hashlib").sha256(raw).hexdigest(),
                        "text": observed,
                    }
                attempts.append(
                    {
                        "request": request,
                        "status": "FINISHED",
                        "observed": observed,
                        "artifact": artifact,
                        "artifactIdentity": _artifact_identity(artifact),
                    }
                )
            except Exception:
                attempts.append(
                    {
                        "request": request,
                        "status": "TOOL_ERROR",
                        "observed": None,
                        "artifact": None,
                        "artifactIdentity": None,
                    }
                )
                status = "TOOL_ERROR"
        observed_values = [attempt["observed"] for attempt in attempts]
        artifacts = [attempt["artifact"] for attempt in attempts]
        observed_value: object = observed_values[0] if len(observed_values) == 1 else observed_values
        artifact_value: object = artifacts[0] if len(artifacts) == 1 else {
            "subattemptArtifacts": artifacts
        }
        result = {
            "status": status,
            "subattempts": attempts,
            "observed": observed_value,
            "artifact": artifact_value,
        }
        if redacted:
            result["redacted"] = True
        return result

    def run(
        self,
        candidate: Candidate,
        retained_source: Path,
        scratch_root: Path,
        observation: dict[str, object],
    ) -> object:
        if observation.get("kind") == "SOURCE":
            return self._read_only_result(retained_source, "/candidate", observation)
        if observation.get("kind") == "READ":
            raise RuntimeError("production authenticated read authority is unavailable")
        attempts: list[dict[str, object]] = []
        status = "COMPLETE"
        for request_value in observation["requests"]:
            if (
                not isinstance(request_value, dict)
                or not isinstance(request_value.get("argv"), list)
                or not request_value["argv"]
                or any(not isinstance(item, str) for item in request_value["argv"])
            ):
                attempts.append(
                    {
                        "request": request_value,
                        "status": "INVALID_REQUEST",
                        "observed": None,
                        "artifact": None,
                        "artifactIdentity": None,
                    }
                )
                status = "TOOL_ERROR"
                continue
            request_root = Path(tempfile.mkdtemp(prefix="request-", dir=scratch_root))
            command = _sandbox_command(
                writable=((request_root.resolve(strict=True), "/scratch"),),
                readable=((retained_source.resolve(strict=True), "/candidate"),),
                cwd="/candidate",
                argv=tuple(request_value["argv"]),
            )
            try:
                completed = subprocess.run(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=float(request_value.get("timeoutSeconds", 300)),
                    check=False,
                )
            except (subprocess.TimeoutExpired, OSError):
                attempts.append(
                    {
                        "request": request_value,
                        "status": "TOOL_ERROR",
                        "observed": None,
                        "artifact": None,
                        "artifactIdentity": None,
                    }
                )
                status = "TOOL_ERROR"
                continue
            observed = completed.stdout.decode("utf-8", errors="replace").rstrip("\n")[:100_000]
            artifact = {
                "exitCode": completed.returncode,
                "stdout": observed,
                "stderr": completed.stderr.decode("utf-8", errors="replace")[-100_000:],
            }
            attempt_status = "FINISHED" if completed.returncode == 0 else "NONZERO_EXIT"
            attempts.append(
                {
                    "request": request_value,
                    "status": attempt_status,
                    "observed": observed,
                    "artifact": artifact,
                    "artifactIdentity": _artifact_identity(artifact),
                }
            )
            if completed.returncode != 0:
                status = "TOOL_ERROR"
        observed_values = [attempt["observed"] for attempt in attempts]
        artifacts = [attempt["artifact"] for attempt in attempts]
        observed_value: object = observed_values[0] if len(observed_values) == 1 else observed_values
        artifact_value: object = artifacts[0] if len(artifacts) == 1 else {
            "subattemptArtifacts": artifacts
        }
        return {
            "status": status,
            "subattempts": attempts,
            "observed": observed_value,
            "artifact": artifact_value,
        }


def _renameat2(source: Path, destination: Path, flags: int) -> None:
    if _RENAMEAT2 is None:
        raise RuntimeError("renameat2 is required for conditional source adoption")
    result = _RENAMEAT2(
        _AT_FDCWD,
        os.fsencode(source),
        _AT_FDCWD,
        os.fsencode(destination),
        flags,
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def _physical_entry(path: Path) -> dict[str, object] | None:
    if not path.exists() and not path.is_symlink():
        return None
    return _entry(path)


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        path.rmdir()
    else:
        path.unlink()


def _materialize_intended(source: Path, destination: Path, intended: dict[str, object] | None) -> None:
    if intended is None:
        destination.mkdir(mode=0o700)
    elif intended["kind"] == "directory":
        destination.mkdir(mode=int(intended["mode"]))
    elif intended["kind"] == "symlink":
        destination.symlink_to(os.readlink(source))
    else:
        shutil.copy2(source, destination, follow_symlinks=False)


class LinuxSourceAdoptionAdapter:
    # Linux has no pathname CAS for replacing or deleting an existing entry.
    # RENAME_EXCHANGE can expose the displaced entry to a competing writer before
    # rollback, so this production adapter must not start canonical mutation.
    conditional_mutation = False
    variant = "unsupported-uncooperative-writer-fail-closed-v1"

    def _apply_one(
        self,
        project_root: Path,
        workspace_root: Path,
        change: dict[str, object],
    ) -> None:
        raise AdoptionConflict(
            "production conditional source adoption is unavailable for uncooperative writers"
        )

    def apply(
        self,
        project_root: Path,
        workspace_root: Path,
        changes: tuple[dict[str, object], ...],
        planning_is_current: Callable[[], bool],
    ) -> None:
        if not changes:
            return
        raise AdoptionConflict(
            "production conditional source adoption is unavailable for uncooperative writers"
        )
