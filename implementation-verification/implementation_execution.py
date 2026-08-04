from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import fcntl
from pathlib import Path
from typing import Callable, Iterable, Protocol

from durable_work import DurableResultIntegrityError, DurableWorkStore
from implementation_verification import (
    Candidate,
    Currentness,
    ImplementationStopped,
    PublicResult,
    VerificationResult,
)


class AdoptionConflict(RuntimeError):
    pass


class SourceAdoptionAdapter(Protocol):
    conditional_mutation: bool

    def apply(
        self,
        project_root: Path,
        workspace_root: Path,
        changes: tuple[dict[str, object], ...],
    ) -> None: ...


class WorkerAdapter(Protocol):
    isolation_enforced: bool

    def run(
        self,
        worker: object,
        work: Path,
        workspace_root: Path,
        assignment: object,
    ) -> None: ...


_TICKET_FIELDS = ("Status", "Parent-Spec", "Project-Root", "Worker", "UI")
_TICKET_SECTIONS = (
    "Goal",
    "Acceptance Criteria",
    "Scope",
    "Non-Goals",
    "Blockers",
    "Verification",
    "References",
)
_SPEC_SECTIONS = (
    "Problem",
    "Desired Outcome",
    "Requirements",
    "Non-Goals",
    "Implementation Constraints",
    "Verification Expectations",
    "UI / UX",
    "Open Questions",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _metadata(raw: bytes, required: tuple[str, ...]) -> dict[str, str]:
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("planning input must be UTF-8") from exc
    first_h2 = next((index for index, line in enumerate(lines) if line.startswith("## ")), len(lines))
    values: dict[str, str] = {}
    for key in required:
        matches = [line[len(key) + 2 :] for line in lines[:first_h2] if line.startswith(f"{key}: ")]
        if len(matches) != 1:
            raise ValueError(f"planning input must contain one exact {key} metadata entry")
        values[key] = matches[0]
    return values


def _require_sections(raw: bytes, required: tuple[str, ...]) -> None:
    headings = [line[3:] for line in raw.decode("utf-8").splitlines() if line.startswith("## ")]
    for section in required:
        if headings.count(section) != 1:
            raise ValueError(f"planning input must contain one exact ## {section} heading")


def _acceptance_criteria(raw: bytes) -> tuple[dict[str, object], ...]:
    lines = raw.splitlines(keepends=True)

    def content(line: bytes) -> bytes:
        if line.endswith(b"\r\n"):
            return line[:-2]
        if line.endswith((b"\n", b"\r")):
            return line[:-1]
        return line

    headings = [index for index, line in enumerate(lines) if content(line) == b"## Acceptance Criteria"]
    if len(headings) != 1:
        raise ValueError("Ticket must contain one exact Acceptance Criteria section")
    start = headings[0] + 1
    end = next(
        (index for index in range(start, len(lines)) if content(lines[index]).startswith(b"## ")),
        len(lines),
    )
    body = lines[start:end]
    while body and content(body[0]) == b"":
        body.pop(0)
    while body and content(body[-1]) == b"":
        body.pop()
    items: list[bytes] = []
    current: list[bytes] = []
    for line in body:
        value = content(line)
        if value.startswith(b"- ") and value[2:].strip():
            if current:
                items.append(b"".join(current))
            current = [line]
        elif current and (value == b"" or value.startswith(b"  ")):
            current.append(line)
        else:
            raise ValueError("Acceptance Criteria must contain exact top-level list items")
    if current:
        items.append(b"".join(current))
    if not items:
        raise ValueError("Acceptance Criteria must not be empty")
    return tuple(
        {"criterionIndex": index, "criterionRawSha256": _sha256_bytes(item)}
        for index, item in enumerate(items, start=1)
    )


def _read_planning(work: Path) -> tuple[dict[str, object], tuple[dict[str, object], ...], Path]:
    raw = work.read_bytes()
    ticket = _metadata(raw, _TICKET_FIELDS)
    _require_sections(raw, _TICKET_SECTIONS)
    if ticket["Status"] != "ready":
        raise ValueError("Ticket is not ready")
    authored_root = Path(ticket["Project-Root"])
    if not authored_root.is_absolute():
        raise ValueError("Project-Root must be absolute")
    project_root = authored_root.resolve(strict=True)
    if not project_root.is_dir():
        raise ValueError("Project-Root must be a directory")
    authored_spec = Path(ticket["Parent-Spec"])
    spec_path = authored_spec if authored_spec.is_absolute() else work.parent / authored_spec
    spec_path = spec_path.resolve(strict=True)
    if not spec_path.is_file():
        raise ValueError("Parent-Spec must be a file")
    spec_raw = spec_path.read_bytes()
    spec = _metadata(spec_raw, ("Status", "Owner"))
    _require_sections(spec_raw, _SPEC_SECTIONS)
    if spec["Status"] != "approved" or not spec["Owner"]:
        raise ValueError("Parent-Spec is not approved")
    criteria = _acceptance_criteria(raw)
    planning: dict[str, object] = {
        "ticketPath": str(work),
        "ticketSha256": _sha256_bytes(raw),
        "specPath": str(spec_path),
        "specSha256": _sha256_bytes(spec_raw),
        "projectRoot": str(project_root),
    }
    return planning, criteria, project_root


def _entry(path: Path) -> dict[str, object]:
    info = path.lstat()
    mode = stat.S_IMODE(info.st_mode)
    if stat.S_ISDIR(info.st_mode):
        return {"kind": "directory", "mode": mode}
    if stat.S_ISREG(info.st_mode):
        return {"kind": "file", "mode": mode, "sha256": _sha256_bytes(path.read_bytes())}
    if stat.S_ISLNK(info.st_mode):
        return {"kind": "symlink", "target": os.readlink(path)}
    raise ValueError(f"unsupported physical source entry: {path}")


def _capture_once(root: Path) -> dict[str, dict[str, object]]:
    if not root.is_dir():
        raise ValueError("source root is not a directory")
    manifest: dict[str, dict[str, object]] = {}

    def visit(directory: Path) -> None:
        for child in sorted(directory.iterdir(), key=lambda item: os.fsencode(item.name)):
            relative = child.relative_to(root).as_posix()
            value = _entry(child)
            manifest[relative] = value
            if value["kind"] == "directory":
                visit(child)

    visit(root)
    return manifest


def _identity(manifest: dict[str, dict[str, object]]) -> str:
    encoded = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return _sha256_bytes(encoded)


def _value_identity(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


def _capture(root: Path) -> tuple[dict[str, dict[str, object]], str]:
    first = _capture_once(root)
    second = _capture_once(root)
    if first != second:
        raise RuntimeError("source did not remain stable during capture")
    return first, _identity(first)


def _copy_exact(source: Path, destination: Path) -> str:
    if destination.exists():
        raise RuntimeError("retained source destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, symlinks=True, copy_function=shutil.copy2)
    source_manifest, source_identity = _capture(source)
    destination_manifest, destination_identity = _capture(destination)
    if source_manifest != destination_manifest or source_identity != destination_identity:
        raise RuntimeError("retained source differs from captured source")
    return destination_identity


def _overlaps(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _write_json_once(path: Path, value: dict[str, object]) -> None:
    if path.exists():
        if _read_json(path) != value:
            raise RuntimeError("immutable private record differs")
        return
    _write_json(path, value)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("private implementation progress is malformed")
    return value


class ImplementationExecution:
    def __init__(
        self,
        state_root: str | Path,
        store: DurableWorkStore,
        worker_adapter: WorkerAdapter,
        adoption: SourceAdoptionAdapter,
        implementation_review: Callable[[Path, Path], object | None],
    ) -> None:
        self._state_root = Path(state_root).expanduser().resolve(strict=False)
        self._store = store
        self._worker_adapter = worker_adapter
        self._adoption = adoption
        self._implementation_review = implementation_review

    def _transition_root(self, transition_identity: str) -> Path:
        return self._state_root / "implementation" / _sha256_bytes(transition_identity.encode())

    def _stopped_source(self, transition_root: Path, project_root: Path) -> dict[str, object]:
        _, identity = _capture(project_root)
        retained = transition_root / "stopped" / identity
        if not retained.exists():
            _copy_exact(project_root, retained)
        else:
            _, retained_identity = _capture(retained)
            if retained_identity != identity:
                raise RuntimeError("retained stopped source differs")
        return {"identity": identity, "retainedRoot": str(retained)}

    def _stop(
        self,
        work: Path,
        transition_root: Path,
        project_root: Path,
        reason: str,
    ) -> ImplementationStopped:
        return ImplementationStopped(work, reason, self._stopped_source(transition_root, project_root))

    @staticmethod
    def _candidate_from_progress(work: Path, value: dict[str, object]) -> Candidate:
        return Candidate(
            work=work,
            planning=value["planning"],
            acceptance_criteria=tuple(value["acceptanceCriteria"]),
            source=value["source"],
            implementation_changes=tuple(value["implementationChanges"]),
            preserved_changes=tuple(value["preservedChanges"]),
        )

    @staticmethod
    def _validate_retained_source(candidate: Candidate) -> None:
        source = candidate.source
        if not isinstance(source, dict):
            raise DurableResultIntegrityError("Candidate source record is malformed")
        identity = source.get("identity")
        retained_root = source.get("retainedRoot")
        if not isinstance(identity, str) or not isinstance(retained_root, str):
            raise DurableResultIntegrityError("Candidate source record is malformed")
        try:
            _, retained_identity = _capture(Path(retained_root))
        except Exception as exc:
            raise DurableResultIntegrityError("retained Candidate source is unreadable") from exc
        if retained_identity != identity:
            raise DurableResultIntegrityError("retained Candidate source differs")

    def implement(
        self,
        work: Path,
        worker: object,
        transition_identity: str,
        *,
        reenter: bool,
    ) -> Candidate | ImplementationStopped:
        transition_root = self._transition_root(transition_identity)
        transition_root.mkdir(parents=True, exist_ok=True)
        with (transition_root / "execution.lock").open("a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            return self._implement_locked(work, worker, transition_identity, reenter=reenter)

    def _implement_locked(
        self,
        work: Path,
        worker: object,
        transition_identity: str,
        *,
        reenter: bool,
    ) -> Candidate | ImplementationStopped:
        planning, criteria, project_root = _read_planning(work)
        transition_root = self._transition_root(transition_identity)
        progress_path = transition_root / "progress.json"

        if progress_path.exists():
            progress = _read_json(progress_path)
            if progress.get("work") != str(work) or progress.get("planning") != planning:
                return self._stop(work, transition_root, project_root, "planning changed during implementation")
            candidate_value = progress.get("candidate")
            if isinstance(candidate_value, dict):
                candidate = self._candidate_from_progress(work, candidate_value)
                self._validate_retained_source(candidate)
                return candidate
            if progress.get("adoptionMayHaveStarted") is True:
                return self._stop(
                    work,
                    transition_root,
                    project_root,
                    "canonical adoption may have started; automatic writes are disabled",
                )
        else:
            if reenter:
                raise RuntimeError("private implementation progress is absent")
            if _overlaps(self._state_root, project_root):
                return ImplementationStopped(work, "private state overlaps product source", {"identity": "unknown"})
            baseline_root = transition_root / "baseline"
            workspace_root = transition_root / "workspace"
            _, baseline_identity = _capture(project_root)
            copied_identity = _copy_exact(project_root, baseline_root)
            if copied_identity != baseline_identity:
                raise RuntimeError("baseline source changed while it was retained")
            _copy_exact(baseline_root, workspace_root)
            progress = {
                "work": str(work),
                "planning": planning,
                "acceptanceCriteria": list(criteria),
                "baselineRoot": str(baseline_root),
                "baselineIdentity": baseline_identity,
                "workspaceRoot": str(workspace_root),
                "workerMayHaveStarted": False,
                "adoptionMayHaveStarted": False,
            }
            _write_json(progress_path, progress)

        baseline_root = Path(str(progress["baselineRoot"]))
        workspace_root = Path(str(progress["workspaceRoot"]))
        baseline_manifest, baseline_identity = _capture(baseline_root)
        if baseline_identity != progress["baselineIdentity"]:
            raise RuntimeError("private baseline source differs")

        workspace_manifest, workspace_identity = _capture(workspace_root)
        if progress.get("workerMayHaveStarted") is True:
            assignment_record = progress.get("assignment")
            if not isinstance(assignment_record, dict) or not isinstance(
                assignment_record.get("beforeWorkspaceIdentity"), str
            ):
                raise RuntimeError("active Worker assignment progress is malformed")
            progress["reconciledWorkspaceIdentity"] = workspace_identity
            if workspace_identity == assignment_record["beforeWorkspaceIdentity"]:
                _write_json(progress_path, progress)
                return self._stop(
                    work,
                    transition_root,
                    project_root,
                    "Worker response was lost without an observable workspace result",
                )
            progress["workerMayHaveStarted"] = False
            progress.pop("assignment", None)
            _write_json(progress_path, progress)

        while True:
            assignment = self._implementation_review(work, workspace_root)
            if assignment is None:
                workspace_manifest, workspace_identity = _capture(workspace_root)
                progress["reconciledWorkspaceIdentity"] = workspace_identity
                _write_json(progress_path, progress)
                break
            if getattr(self._worker_adapter, "isolation_enforced", False) is not True:
                return self._stop(work, transition_root, project_root, "Worker isolation is unavailable")
            workspace_manifest, workspace_identity = _capture(workspace_root)
            assignment_record = {
                "assignmentIdentity": _value_identity(
                    {"assignment": assignment, "beforeWorkspaceIdentity": workspace_identity}
                ),
                "assignment": assignment,
                "beforeWorkspaceIdentity": workspace_identity,
            }
            progress["assignment"] = assignment_record
            progress["workerMayHaveStarted"] = True
            _write_json(progress_path, progress)
            self._worker_adapter.run(worker, work, workspace_root, assignment)
            workspace_manifest, reconciled_identity = _capture(workspace_root)
            progress["reconciledWorkspaceIdentity"] = reconciled_identity
            progress["workerMayHaveStarted"] = False
            progress.pop("assignment", None)
            _write_json(progress_path, progress)
            if reconciled_identity == workspace_identity:
                return self._stop(
                    work,
                    transition_root,
                    project_root,
                    "Worker produced no source change for the bounded assignment",
                )

        current_planning, current_criteria, current_root = _read_planning(work)
        if current_planning != planning or current_criteria != criteria or current_root != project_root:
            return self._stop(work, transition_root, project_root, "planning changed before source adoption")

        occupancy = self._store.occupy_mutation_domain(
            transition_identity,
            project_root,
            baseline_identity,
            lambda root: _capture(root)[1],
        )
        if not occupancy.acquired:
            return self._stop(work, transition_root, project_root, "product source mutation domain is busy")
        live_manifest, live_identity = _capture(project_root)
        if live_identity != occupancy.observed_source:
            raise RuntimeError("live source changed after mutation occupancy observation")

        changes: list[dict[str, object]] = []
        implementation_paths: list[str] = []
        preserved_paths: set[str] = set()
        for path in sorted(set(baseline_manifest) | set(workspace_manifest) | set(live_manifest)):
            baseline = baseline_manifest.get(path)
            workspace = workspace_manifest.get(path)
            live = live_manifest.get(path)
            worker_changed = workspace != baseline
            live_changed = live != baseline
            if worker_changed and live_changed and workspace != live:
                return self._stop(work, transition_root, project_root, f"overlap conflict at {path}")
            if worker_changed and not live_changed:
                implementation_paths.append(path)
                changes.append({"path": path, "expected": live, "intended": workspace})
            else:
                preserved_paths.add(path)

        adoption_plan = {
            "expectedLiveIdentity": live_identity,
            "changes": changes,
        }
        adoption_plan_path = transition_root / "adoption-plan.json"
        _write_json_once(adoption_plan_path, adoption_plan)
        progress["adoptionPlanRef"] = str(adoption_plan_path)
        _write_json(progress_path, progress)
        if changes:
            if getattr(self._adoption, "conditional_mutation", False) is not True:
                return self._stop(work, transition_root, project_root, "conditional source adoption is unavailable")
            progress["adoptionMayHaveStarted"] = True
            _write_json(progress_path, progress)
            try:
                self._adoption.apply(project_root, workspace_root, tuple(changes))
            except AdoptionConflict as exc:
                return self._stop(work, transition_root, project_root, str(exc))

        final_manifest, final_identity = _capture(project_root)
        expected_final = dict(live_manifest)
        for change in changes:
            path = str(change["path"])
            intended = change["intended"]
            if intended is None:
                expected_final.pop(path, None)
            else:
                expected_final[path] = intended  # type: ignore[assignment]
        if final_manifest != expected_final:
            return self._stop(work, transition_root, project_root, "final source differs from adoption plan")
        final_planning, final_criteria, final_root = _read_planning(work)
        if final_planning != planning or final_criteria != criteria or final_root != project_root:
            return self._stop(work, transition_root, project_root, "planning changed before Candidate publication")
        if self._implementation_review(work, project_root) is not None:
            return self._stop(work, transition_root, project_root, "final implementation closure check did not pass")

        retained_root = transition_root / "candidate"
        retained_identity = _copy_exact(project_root, retained_root)
        if retained_identity != final_identity:
            raise RuntimeError("retained Candidate source differs")
        source = {"identity": final_identity, "retainedRoot": str(retained_root)}
        candidate_value: dict[str, object] = {
            "planning": planning,
            "acceptanceCriteria": list(criteria),
            "source": source,
            "implementationChanges": implementation_paths,
            "preservedChanges": sorted(preserved_paths),
        }
        progress["candidate"] = candidate_value
        _write_json(progress_path, progress)
        return self._candidate_from_progress(work, candidate_value)

    def verify(
        self,
        candidate: Candidate,
        transition_identity: str,
        *,
        reenter: bool,
    ) -> Iterable[object]:
        raise NotImplementedError("independent verification belongs to Phase 5")

    def observe_currentness(self, result: PublicResult) -> Currentness:
        candidate = result.candidate if isinstance(result, VerificationResult) else result
        if not isinstance(candidate, Candidate):
            return Currentness.UNKNOWN
        self._validate_retained_source(candidate)
        try:
            planning, criteria, project_root = _read_planning(candidate.work)
            _, source_identity = _capture(project_root)
        except Exception:
            return Currentness.UNKNOWN
        source = candidate.source
        if (
            planning == candidate.planning
            and criteria == candidate.acceptance_criteria
            and source.get("identity") == source_identity
        ):
            return Currentness.CURRENT
        return Currentness.NOT_CURRENT
