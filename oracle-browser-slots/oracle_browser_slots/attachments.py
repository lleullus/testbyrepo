"""Single-ZIP policy for file-bearing stock Oracle Browser requests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import shutil
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from typing import Any, Callable, Mapping, Sequence
import zipfile


CANONICAL_ORACLE_CLI = "/home/user01/.nvm/versions/node/v24.18.0/bin/oracle"
MAX_SAFE_FILE_SIZE_BYTES = 9_007_199_254_740_991
CONFLICTING_OPTIONS = {
    "--browser-attachments",
    "--browser-inline-files",
    "--browser-bundle-files",
    "--browser-bundle-format",
    "--max-file-size-bytes",
    "--wait",
    "--no-wait",
}
SESSIONLESS_FLAGS = {
    "--copy",
    "--copy-markdown",
    "--dry-run",
    "--exec-session",
    "--preflight",
    "--preview",
    "--render",
    "--render-markdown",
    "--route",
    "--session",
    "--status",
}
MANIFEST_FILENAME = "oracle-browser-slots-attachments.json"
MANIFEST_RELATIVE_PATH = f"artifacts/{MANIFEST_FILENAME}"


class AttachmentPreparationError(Exception):
    """A file-bearing request cannot be prepared safely before claim."""

    def __init__(self, reason: str, operator_action: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.operator_action = operator_action


class AttachmentPreparationInterrupted(Exception):
    """The operator interrupted file preparation before a slot claim."""

    def __init__(self, signal_number: int) -> None:
        super().__init__(signal_number)
        self.signal_number = signal_number


@dataclass(frozen=True)
class SelectedFile:
    path: Path
    relative_path: str
    zip_path: str
    size_bytes: int


@dataclass
class PreparedAttachment:
    """A request-owned ZIP and its post-run evidence context."""

    command: list[str]
    selected_files: tuple[SelectedFile, ...]
    zip_path: Path
    zip_name: str
    zip_size_bytes: int
    zip_sha256: str
    temporary_directory: Path
    session_id: str
    oracle_home: Path
    original_file_inputs: tuple[str, ...]
    request_id: str
    requires_session_manifest: bool
    include_file_report: bool
    _cleaned: bool = False

    def write_manifest(
        self,
        *,
        child_started: bool,
        outcome: str,
        exit_code: int | None,
        cleanup_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Persist evidence in the stock session artifact directory if it exists."""

        session_directory = self._resolve_session_directory()
        if session_directory is None:
            return None

        metadata_path = session_directory / "meta.json"
        metadata = _read_json_object(metadata_path)
        if metadata is None:
            return None

        browser_metadata = metadata.get("browser")
        runtime = browser_metadata.get("runtime", {}) if isinstance(browser_metadata, dict) else {}
        if not isinstance(runtime, dict):
            runtime = {}
        prompt_submitted = runtime.get("promptSubmitted") is True
        output_log = _read_text(session_directory / "output.log")
        attachment_registered = prompt_submitted or "All attachments uploaded" in output_log
        if child_started:
            attachment_status = "succeeded" if attachment_registered else "failed"
            prompt_status = "succeeded" if prompt_submitted else "failed"
        else:
            attachment_status = "not_attempted"
            prompt_status = "not_attempted"
        actual_session_id = metadata.get("id")
        if not isinstance(actual_session_id, str) or not actual_session_id:
            actual_session_id = self.session_id

        manifest: dict[str, Any] = {
            "schema_version": 1,
            "request_id": self.request_id,
            "session_id": actual_session_id,
            "created_at": _utc_now(),
            "selected_files": [
                {
                    "relative_path": selected.relative_path,
                    "size_bytes": selected.size_bytes,
                }
                for selected in self.selected_files
            ],
            "zip": {
                "name": self.zip_name,
                "size_bytes": self.zip_size_bytes,
                "sha256": self.zip_sha256,
            },
            "attachment_registration": {
                "status": attachment_status,
                "attempts": 1 if child_started else 0,
                "attachment_count": 1 if child_started else 0,
                "attachment_name": self.zip_name if child_started else None,
            },
            "prompt_submission": {
                "status": prompt_status,
                "submitted": prompt_submitted,
            },
            "session_result": {
                "outcome": outcome,
                "exit_code": exit_code,
            },
        }
        if cleanup_result is not None:
            manifest["generated_zip_cleanup"] = cleanup_result

        artifact_directory = session_directory / "artifacts"
        manifest_path = artifact_directory / MANIFEST_FILENAME
        try:
            artifact_directory.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(manifest_path, manifest)

            metadata_options = metadata.get("options")
            if isinstance(metadata_options, dict):
                updated_options = dict(metadata_options)
                updated_options["file"] = list(self.original_file_inputs)
                metadata["options"] = updated_options

            existing_pointer = metadata.get("oracle_browser_slots")
            pointer = dict(existing_pointer) if isinstance(existing_pointer, dict) else {}
            pointer["attachment_manifest"] = MANIFEST_RELATIVE_PATH
            metadata["oracle_browser_slots"] = pointer

            artifacts = metadata.get("artifacts")
            artifact_entries = list(artifacts) if isinstance(artifacts, list) else []
            manifest_artifact = {
                "kind": "oracle-browser-slots-attachment-manifest",
                "path": str(manifest_path),
                "label": "Oracle Browser attachment manifest",
                "mimeType": "application/json",
                "sizeBytes": manifest_path.stat().st_size,
                "origin": {"mode": "local"},
            }
            artifact_entries = [
                entry
                for entry in artifact_entries
                if not (
                    isinstance(entry, dict)
                    and entry.get("kind") == manifest_artifact["kind"]
                )
            ]
            artifact_entries.append(manifest_artifact)
            metadata["artifacts"] = artifact_entries
            _write_json_atomic(metadata_path, metadata)
            manifest_readback = _read_json_object(manifest_path)
            metadata_readback = _read_json_object(metadata_path)
            if manifest_readback != manifest or not isinstance(metadata_readback, dict):
                raise OSError("manifest authoritative readback이 일치하지 않습니다")
            readback_pointer = metadata_readback.get("oracle_browser_slots")
            if not isinstance(readback_pointer, dict) or readback_pointer.get(
                "attachment_manifest"
            ) != MANIFEST_RELATIVE_PATH:
                raise OSError(
                    "manifest session pointer authoritative readback이 일치하지 않습니다"
                )
        except (OSError, TypeError, ValueError) as exc:
            return {
                "path": str(manifest_path),
                "written": False,
                "error": str(exc),
            }

        return {
            "path": str(manifest_path),
            "relative_path": MANIFEST_RELATIVE_PATH,
            "written": True,
        }

    def cleanup(self) -> dict[str, Any]:
        """Remove the request-owned ZIP and its temporary directory idempotently."""

        if self._cleaned:
            return {
                "removed": not self.zip_path.exists() and not self.temporary_directory.exists()
            }
        self._cleaned = True
        error: str | None = None
        try:
            shutil.rmtree(self.temporary_directory)
        except FileNotFoundError:
            pass
        except OSError as exc:
            error = str(exc)
            try:
                self.zip_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as inner:
                error = f"{error}; {inner}"
        if self.zip_path.exists() or self.temporary_directory.exists():
            error = error or "temporary ZIP path still exists after cleanup"
        result: dict[str, Any] = {"removed": error is None}
        if error is not None:
            result["error"] = error
        return result

    def _resolve_session_directory(self) -> Path | None:
        sessions_directory = self.oracle_home / "sessions"
        expected = sessions_directory / self.session_id
        expected_metadata = _read_json_object(expected / "meta.json")
        if expected_metadata is not None and _metadata_contains_zip(expected_metadata, self.zip_path):
            return expected

        # Stock Oracle appends a numeric suffix if a slug is already occupied.
        # Correlate only against the request-owned generated ZIP while it still
        # exists; a prefix-only match would be unsafe under concurrent runs.
        try:
            candidates = list(sessions_directory.iterdir())
        except OSError:
            return None
        for candidate in candidates:
            if not candidate.is_dir():
                continue
            metadata = _read_json_object(candidate / "meta.json")
            if _metadata_contains_zip(metadata, self.zip_path):
                return candidate
        return None


@dataclass(frozen=True)
class _FileArgumentGroups:
    file: tuple[str, ...]
    include: tuple[str, ...]
    files: tuple[str, ...]
    path: tuple[str, ...]
    paths: tuple[str, ...]

    @property
    def has_values(self) -> bool:
        return any(
            part.strip()
            for values in (self.file, self.include, self.files, self.path, self.paths)
            for value in values
            for part in value.split(",")
        )

    def as_payload(self) -> dict[str, list[str]]:
        return {
            "file": list(self.file),
            "include": list(self.include),
            "files": list(self.files),
            "path": list(self.path),
            "paths": list(self.paths),
        }


class FileAttachmentPolicy:
    """Select with stock Oracle, then pass one compressed ZIP to stock Oracle."""

    def __init__(
        self,
        *,
        selector: Callable[[Mapping[str, list[str]], Path], Sequence[str | Path]] | None = None,
        oracle_home: Path | None = None,
        temporary_root: Path | None = None,
    ) -> None:
        self.selector = selector or select_stock_files
        self.oracle_home = oracle_home or _oracle_home_from_environment()
        self.temporary_root = temporary_root

    def prepare(
        self,
        argv: Sequence[str],
        request_id: str,
        *,
        cwd: Path | None = None,
    ) -> PreparedAttachment | None:
        command = list(argv)
        working_directory = (cwd or Path.cwd()).resolve()
        groups = _extract_file_arguments(command)
        if not groups.has_values:
            return None

        temporary_directory: Path | None = None
        try:
            with _preparation_signal_guard():
                selected_paths: Sequence[str | Path]
                try:
                    selected_paths = self.selector(groups.as_payload(), working_directory)
                except AttachmentPreparationError:
                    raise
                except Exception as exc:
                    raise AttachmentPreparationError(
                        f"stock Oracle 파일 선택 중 오류가 발생했습니다: {exc}",
                        "--file 입력과 현재 작업 디렉터리, stock Oracle 설치 상태를 확인하십시오.",
                    ) from exc

                if not selected_paths:
                    raise AttachmentPreparationError(
                        "--file 입력에서 선택된 파일이 없습니다.",
                        "파일 경로, glob, 제외 패턴과 .gitignore를 확인하십시오.",
                    )

                selected_files = _build_selected_files(selected_paths, working_directory)
                temporary_directory = Path(
                    tempfile.mkdtemp(
                        prefix="oracle-browser-slots-zip-",
                        dir=str(self.temporary_root) if self.temporary_root else None,
                    )
                )
                zip_path = temporary_directory / "oracle-attachments.zip"
                _create_compressed_zip(zip_path, selected_files)
                zip_size_bytes = zip_path.stat().st_size
                zip_sha256 = _sha256_file(zip_path)
                session_id = _new_session_id(
                    self.oracle_home,
                    request_id,
                )
                normalized_command = _normalize_file_command(
                    command,
                    zip_path,
                )
                return PreparedAttachment(
                    command=normalized_command,
                    selected_files=tuple(selected_files),
                    zip_path=zip_path,
                    zip_name=zip_path.name,
                    zip_size_bytes=zip_size_bytes,
                    zip_sha256=zip_sha256,
                    temporary_directory=temporary_directory,
                    session_id=session_id,
                    oracle_home=self.oracle_home,
                    original_file_inputs=tuple(_merged_file_inputs(groups)),
                    request_id=request_id,
                    requires_session_manifest=_requires_session_manifest(command),
                    include_file_report=_has_option_before_terminator(
                        command, "--files-report"
                    ),
                )
        except AttachmentPreparationError:
            if temporary_directory is not None:
                shutil.rmtree(temporary_directory, ignore_errors=True)
            raise
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
            if temporary_directory is not None:
                shutil.rmtree(temporary_directory, ignore_errors=True)
            raise AttachmentPreparationError(
                f"단일 압축 ZIP을 생성하지 못했습니다: {exc}",
                "선택 파일의 접근 권한과 디스크 상태를 확인한 뒤 다시 실행하십시오.",
            ) from exc
        except BaseException:
            if temporary_directory is not None:
                shutil.rmtree(temporary_directory, ignore_errors=True)
            raise


def select_stock_files(groups: Mapping[str, list[str]], cwd: Path) -> list[Path]:
    """Reuse stock 0.16.1's readFiles and CLI path-input normalization."""

    node_path = Path(CANONICAL_ORACLE_CLI).parent / "node"
    version_root = node_path.parent.parent
    files_module = version_root / "lib/node_modules/@steipete/oracle/dist/src/oracle/files.js"
    options_module = version_root / "lib/node_modules/@steipete/oracle/dist/src/cli/options.js"
    if not node_path.is_file() or not files_module.is_file() or not options_module.is_file():
        raise AttachmentPreparationError(
            "stock Oracle 0.16.1 파일 선택기를 찾을 수 없습니다.",
            "canonical stock Oracle와 같은 Node 설치를 확인하십시오.",
        )

    payload = {key: list(groups.get(key, [])) for key in ("file", "include", "files", "path", "paths")}
    script = f"""
import {{ readFiles }} from {json.dumps(files_module.as_uri())};
import {{ mergePathLikeOptions, dedupePathInputs }} from {json.dumps(options_module.as_uri())};
let raw = "";
for await (const chunk of process.stdin) raw += chunk;
const request = JSON.parse(raw);
const cwd = request.cwd;
const merged = mergePathLikeOptions(
  request.file,
  request.include,
  request.files,
  request.path,
  request.paths,
);
const normalized = dedupePathInputs(merged, {{ cwd }}).deduped;
console.log = (...args) => console.error(...args);
try {{
  const files = await readFiles(normalized, {{
    cwd,
    maxFileSizeBytes: 0,
    readContents: false,
  }});
  process.stdout.write(JSON.stringify({{ ok: true, files: files.map((file) => file.path) }}));
}} catch (error) {{
  process.stdout.write(JSON.stringify({{
    ok: false,
    error: {{
      name: error?.name ?? "Error",
      message: error?.message ?? String(error),
    }},
  }}));
  process.exitCode = 1;
}}
"""
    try:
        completed = subprocess.run(
            [str(node_path), "--input-type=module", "-e", script],
            cwd=str(cwd),
            input=json.dumps({**payload, "cwd": str(cwd)}),
            text=True,
            capture_output=True,
            check=False,
        )
    except (OSError, ValueError) as exc:
        raise AttachmentPreparationError(
            f"stock Oracle 파일 선택기를 시작하지 못했습니다: {exc}",
            "canonical stock Oracle의 Node 실행 파일과 설치 경로를 확인하십시오.",
        ) from exc

    try:
        result = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        detail = completed.stderr.strip() or completed.stdout.strip() or "응답 없음"
        raise AttachmentPreparationError(
            f"stock Oracle 파일 선택기 응답을 해석하지 못했습니다: {detail}",
            "stock Oracle 0.16.1 설치와 Node 런타임을 확인하십시오.",
        ) from exc
    if not isinstance(result, dict) or result.get("ok") is not True:
        error = result.get("error") if isinstance(result, dict) else None
        message = error.get("message") if isinstance(error, dict) else "알 수 없는 선택 오류"
        raise AttachmentPreparationError(
            f"stock Oracle 파일 선택에 실패했습니다: {message}",
            "파일 입력, glob/제외 패턴, .gitignore와 기본 제외 규칙을 확인하십시오.",
        )
    files = result.get("files")
    if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
        raise AttachmentPreparationError(
            "stock Oracle 파일 선택 결과 형식이 올바르지 않습니다.",
            "stock Oracle 0.16.1 설치를 확인하십시오.",
        )
    if completed.returncode != 0:
        raise AttachmentPreparationError(
            "stock Oracle 파일 선택이 비정상 종료되었습니다.",
            "파일 입력과 stock Oracle 설치를 확인하십시오.",
        )
    return [Path(item) for item in files]


def _extract_file_arguments(argv: Sequence[str]) -> _FileArgumentGroups:
    values: dict[str, list[str]] = {
        "file": [],
        "include": [],
        "files": [],
        "path": [],
        "paths": [],
    }
    option_to_key = {
        "--file": "file",
        "-f": "file",
        "--include": "include",
        "--files": "files",
        "--path": "path",
        "--paths": "paths",
    }
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--":
            break
        key = option_to_key.get(token)
        if key is None:
            for option, option_key in option_to_key.items():
                prefix = f"{option}="
                if token.startswith(prefix):
                    key = option_key
                    values[key].append(token[len(prefix) :])
                    break
            if key is None:
                index += 1
                continue
            index += 1
            continue

        index += 1
        while index < len(argv) and not argv[index].startswith("-"):
            values[key].append(argv[index])
            index += 1
    return _FileArgumentGroups(
        file=tuple(values["file"]),
        include=tuple(values["include"]),
        files=tuple(values["files"]),
        path=tuple(values["path"]),
        paths=tuple(values["paths"]),
    )


def _merged_file_inputs(groups: _FileArgumentGroups) -> list[str]:
    merged: list[str] = []
    for values in (groups.file, groups.include, groups.files, groups.path, groups.paths):
        for value in values:
            merged.extend(part.strip() for part in value.split(",") if part.strip())
    return merged


def _build_selected_files(paths: Sequence[str | Path], cwd: Path) -> list[SelectedFile]:
    selected: list[SelectedFile] = []
    seen: dict[str, str] = {}
    for raw_path in paths:
        path = Path(raw_path)
        absolute = path if path.is_absolute() else cwd / path
        relative = _display_relative_path(absolute, cwd)
        zip_path = normalize_zip_member_path(relative)
        previous = seen.get(zip_path)
        if previous is not None:
            raise AttachmentPreparationError(
                f"정규화된 ZIP 내부 경로가 충돌합니다: {previous} 및 {relative} -> {zip_path}",
                "충돌하는 파일 경로를 하나만 선택하도록 --file 입력을 수정하십시오.",
            )
        try:
            size_bytes = absolute.stat().st_size
        except OSError as exc:
            raise AttachmentPreparationError(
                f"선택 파일을 확인하지 못했습니다: {relative}: {exc}",
                "선택 파일의 존재와 접근 권한을 확인하십시오.",
            ) from exc
        if not absolute.is_file():
            raise AttachmentPreparationError(
                f"선택 결과가 일반 파일이 아닙니다: {relative}",
                "파일 선택 결과를 확인한 뒤 다시 실행하십시오.",
            )
        seen[zip_path] = relative
        selected.append(
            SelectedFile(
                path=absolute,
                relative_path=relative,
                zip_path=zip_path,
                size_bytes=size_bytes,
            )
        )
    return selected


def normalize_zip_member_path(relative_path: str) -> str:
    """Match stock ZIP path normalization without its auto-renaming behavior."""

    normalized = relative_path.replace("\\", "/")
    normalized = re.sub(r"^[a-zA-Z]:/", "", normalized)
    normalized = normalized.lstrip("/")
    segments = [
        segment
        for segment in normalized.split("/")
        if segment and segment not in {".", ".."}
    ]
    result = "/".join(segments)
    if not result:
        raise AttachmentPreparationError(
            f"ZIP 내부 경로를 정규화할 수 없습니다: {relative_path}",
            "ZIP 내부에서 비어 있지 않은 상대 파일 경로가 되도록 입력을 수정하십시오.",
        )
    return result


def _create_compressed_zip(zip_path: Path, selected_files: Sequence[SelectedFile]) -> None:
    try:
        with zipfile.ZipFile(
            zip_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
            strict_timestamps=False,
        ) as archive:
            for selected in selected_files:
                archive.write(selected.path, arcname=selected.zip_path)
            for selected in selected_files:
                info = archive.getinfo(selected.zip_path)
                if info.file_size != selected.size_bytes:
                    raise OSError(
                        f"선택 파일 크기가 ZIP 작성 중 변경되었습니다: {selected.relative_path}"
                    )
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile):
        try:
            zip_path.unlink()
        except FileNotFoundError:
            pass
        raise


def _normalize_file_command(
    argv: Sequence[str],
    zip_path: Path,
) -> list[str]:
    normalized: list[str] = [argv[0]]
    option_to_key = {
        "--file": "file",
        "-f": "file",
        "--include": "include",
        "--files": "files",
        "--path": "path",
        "--paths": "paths",
    }
    index = 1
    terminator_position: int | None = None
    while index < len(argv):
        token = argv[index]
        if token == "--":
            terminator_position = len(normalized)
            normalized.extend(argv[index:])
            break
        if token in option_to_key:
            index += 1
            while index < len(argv) and not argv[index].startswith("-"):
                index += 1
            continue
        if any(token.startswith(f"{option}=") for option in option_to_key):
            index += 1
            continue

        option = token.split("=", 1)[0]
        if option in CONFLICTING_OPTIONS:
            if "=" not in token and option not in {"--browser-inline-files", "--browser-bundle-files", "--wait", "--no-wait"}:
                if index + 1 < len(argv) and not argv[index + 1].startswith("-"):
                    index += 2
                    continue
            index += 1
            continue
        normalized.append(token)
        index += 1

    policy_options = (
        "--file",
        str(zip_path),
        "--max-file-size-bytes",
        str(MAX_SAFE_FILE_SIZE_BYTES),
        "--browser-attachments",
        "always",
        "--wait",
    )
    if terminator_position is None:
        normalized.extend(policy_options)
    else:
        normalized[terminator_position:terminator_position] = policy_options
    return normalized


def _requires_session_manifest(argv: Sequence[str]) -> bool:
    return not any(token.split("=", 1)[0] in SESSIONLESS_FLAGS for token in argv[1:])


def _has_option_before_terminator(argv: Sequence[str], flag: str) -> bool:
    for token in argv[1:]:
        if token == "--":
            return False
        if token == flag:
            return True
    return False


def _display_relative_path(path: Path, cwd: Path) -> str:
    return os.path.relpath(str(path), str(cwd)).replace(os.sep, "/")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _oracle_home_from_environment() -> Path:
    configured = os.environ.get("ORACLE_HOME_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    home = Path(os.environ.get("HOME", str(Path.home()))).expanduser()
    return (home / ".oracle").resolve()


def _new_session_id(oracle_home: Path, request_id: str) -> str:
    sessions_directory = oracle_home / "sessions"
    request_hint = re.sub(r"[^a-z0-9]+", "", str(request_id).lower())
    request_hint = request_hint[:8] or "request"
    for _ in range(20):
        candidate = f"slots-{request_hint}-p{os.getpid()}-{secrets.token_hex(5)}"
        if not (sessions_directory / candidate).exists():
            return candidate
    raise AttachmentPreparationError(
        "동시 실행을 위한 stock Oracle 세션 식별자를 확보하지 못했습니다.",
        "상태 경로를 확인하고 잠시 후 다시 실행하십시오.",
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _metadata_contains_zip(metadata: dict[str, Any] | None, zip_path: Path) -> bool:
    if not isinstance(metadata, dict):
        return False
    options = metadata.get("options")
    file_values = options.get("file") if isinstance(options, dict) else None
    return isinstance(file_values, list) and str(zip_path) in file_values


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@contextmanager
def _preparation_signal_guard():
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    previous_handlers: dict[int, Any] = {}

    def interrupt_handler(signal_number: int, _frame: Any) -> None:
        raise AttachmentPreparationInterrupted(signal_number)

    signals = [signal.SIGINT, signal.SIGTERM]
    sighup = getattr(signal, "SIGHUP", None)
    if sighup is not None:
        signals.append(sighup)
    try:
        for signal_number in signals:
            previous_handlers[signal_number] = signal.getsignal(signal_number)
            signal.signal(signal_number, interrupt_handler)
        yield
    finally:
        for signal_number, previous_handler in previous_handlers.items():
            signal.signal(signal_number, previous_handler)
