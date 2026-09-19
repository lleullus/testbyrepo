"""Executor-owned immutable file snapshots without content-derived identities."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
from functools import wraps
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import tempfile
import uuid

from .refs import validate_ref, validate_relative_path

PROJECT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ArtifactStoreError(RuntimeError):
    pass


def store_serialized(name: str):
    """Exclude concurrent filesystem/SQLite transition owners; process exit releases it."""
    def decorate(operation):
        @wraps(operation)
        def run(store, *args, **kwargs):
            fd = os.open(store.root / f".{name}.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise ArtifactStoreError(f"STORE_OPERATION_IN_PROGRESS:{name}") from exc
                return operation(store, *args, **kwargs)
            finally:
                os.close(fd)
        return run
    return decorate


class ArtifactStore:
    def __init__(self, base: Path, project_id: str) -> None:
        if PROJECT_ID.fullmatch(project_id) is None:
            raise ArtifactStoreError("invalid project id")
        raw_base = Path(base).expanduser()
        if raw_base.exists() and raw_base.is_symlink():
            raise ArtifactStoreError("store base must not be a symlink")
        self.base = raw_base.resolve()
        self.project_id = project_id
        self.root = self.base / project_id
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.is_symlink() or not self.root.is_dir():
            raise ArtifactStoreError("project store must be a real directory")
        os.chmod(self.root, 0o700)
        (self.root / "snapshots").mkdir(mode=0o700, exist_ok=True)
        (self.root / "executions").mkdir(mode=0o700, exist_ok=True)
        self.db_path = self.root / "state.sqlite"
        self._init_schema()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
        finally:
            connection.close()

    def _init_schema(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS counters(
                  name TEXT PRIMARY KEY,
                  value INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshots(
                  id TEXT PRIMARY KEY,
                  kind TEXT NOT NULL,
                  origin TEXT,
                  producer_run TEXT,
                  producer_invocation TEXT,
                  created_sequence INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshot_files(
                  snapshot_id TEXT NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
                  path TEXT NOT NULL,
                  mode INTEGER NOT NULL,
                  PRIMARY KEY(snapshot_id, path)
                );
                CREATE TABLE IF NOT EXISTS publications(
                  logical_path TEXT PRIMARY KEY,
                  snapshot_id TEXT NOT NULL,
                  snapshot_path TEXT NOT NULL,
                  generation INTEGER NOT NULL,
                  published_sequence INTEGER NOT NULL
                );
                """
            )

    @staticmethod
    def sequence_in(db: sqlite3.Connection, name: str = "global") -> int:
        row = db.execute("SELECT value FROM counters WHERE name = ?", (name,)).fetchone()
        value = 1 if row is None else int(row["value"]) + 1
        db.execute(
            "INSERT INTO counters(name, value) VALUES(?, ?) "
            "ON CONFLICT(name) DO UPDATE SET value = excluded.value",
            (name, value),
        )
        return value

    def next_sequence(self, name: str = "global") -> int:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            value = self.sequence_in(db, name)
            db.execute("COMMIT")
            return value

    def capture_mapping(
        self,
        files: dict[str, bytes | tuple[bytes, int]],
        *,
        kind: str,
        origin: str | None = None,
        producer_run: str | None = None,
        producer_invocation: str | None = None,
    ) -> str:
        if not files:
            raise ArtifactStoreError("cannot capture an empty snapshot")
        snapshot_id = "snap-" + uuid.uuid4().hex
        snapshots = self.root / "snapshots"
        staging = Path(tempfile.mkdtemp(prefix=".capture-", dir=snapshots))
        destination = snapshots / snapshot_id
        rows: list[tuple[str, int]] = []
        try:
            for raw_path, raw_value in sorted(files.items()):
                relative = validate_relative_path(raw_path)
                if isinstance(raw_value, tuple):
                    data, source_mode = raw_value
                else:
                    data, source_mode = raw_value, 0o444
                if not isinstance(data, (bytes, bytearray)):
                    raise ArtifactStoreError("snapshot content must be bytes")
                source_mode = int(source_mode) & 0o777
                stored_mode = source_mode & 0o555
                target = staging.joinpath(*relative.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with target.open("xb") as stream:
                    stream.write(bytes(data))
                    stream.flush()
                    os.fsync(stream.fileno())
                target.chmod(stored_mode or 0o444)
                rows.append((relative, source_mode))
            os.replace(staging, destination)
            sequence = self.next_sequence()
            with self.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "INSERT INTO snapshots(id, kind, origin, producer_run, producer_invocation, created_sequence) "
                    "VALUES(?, ?, ?, ?, ?, ?)",
                    (snapshot_id, kind, origin, producer_run, producer_invocation, sequence),
                )
                db.executemany(
                    "INSERT INTO snapshot_files(snapshot_id, path, mode) VALUES(?, ?, ?)",
                    [(snapshot_id, path, mode) for path, mode in rows],
                )
                db.execute("COMMIT")
            return snapshot_id
        except BaseException:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            raise

    @staticmethod
    def _read_regular_beneath(root: Path, relative: str) -> tuple[bytes, int]:
        relative = validate_relative_path(relative)
        parts = relative.split("/")
        flags_dir = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        flags_file = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
        root_fd = os.open(root, flags_dir)
        current_fd = root_fd
        opened: list[int] = []
        try:
            for part in parts[:-1]:
                next_fd = os.open(part, flags_dir, dir_fd=current_fd)
                opened.append(next_fd)
                current_fd = next_fd
            file_fd = os.open(parts[-1], flags_file, dir_fd=current_fd)
            try:
                details = os.fstat(file_fd)
                if not stat.S_ISREG(details.st_mode):
                    raise ArtifactStoreError(f"snapshot input must be a regular file: {relative}")
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(file_fd, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                return b"".join(chunks), stat.S_IMODE(details.st_mode)
            finally:
                os.close(file_fd)
        except OSError as exc:
            raise ArtifactStoreError(f"unsafe or unavailable snapshot input: {relative}") from exc
        finally:
            for fd in reversed(opened):
                os.close(fd)
            os.close(root_fd)

    def capture_files(
        self,
        root: Path,
        paths: list[Path],
        *,
        kind: str,
        origin: str | None = None,
        producer_run: str | None = None,
        producer_invocation: str | None = None,
    ) -> str:
        root = Path(root).resolve(strict=True)
        values: dict[str, tuple[bytes, int]] = {}
        for supplied in paths:
            raw = Path(supplied)
            if not raw.is_absolute():
                raw = root / raw
            try:
                relative = raw.relative_to(root).as_posix()
            except ValueError as exc:
                raise ArtifactStoreError(f"capture path escapes root: {raw}") from exc
            values[relative] = self._read_regular_beneath(root, relative)
        return self.capture_mapping(
            values,
            kind=kind,
            origin=origin,
            producer_run=producer_run,
            producer_invocation=producer_invocation,
        )

    def _tree_paths(self, root: Path, exclude_top: tuple[str, ...]) -> list[str]:
        root = Path(root).resolve(strict=True)
        result: list[str] = []
        for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current)
            relative_dir = current_path.relative_to(root)
            if relative_dir.parts and relative_dir.parts[0] in exclude_top:
                dirs[:] = []
                continue
            kept_dirs = []
            for name in sorted(dirs):
                child = current_path / name
                relative = child.relative_to(root)
                if relative.parts and relative.parts[0] in exclude_top:
                    continue
                if child.is_symlink():
                    raise ArtifactStoreError(f"snapshot tree contains a symlink: {relative.as_posix()}")
                kept_dirs.append(name)
            dirs[:] = kept_dirs
            for name in sorted(files):
                child = current_path / name
                relative = child.relative_to(root)
                if relative.parts and relative.parts[0] in exclude_top:
                    continue
                if child.is_symlink():
                    raise ArtifactStoreError(f"snapshot tree contains a symlink: {relative.as_posix()}")
                result.append(relative.as_posix())
        return sorted(result)

    def capture_tree(
        self,
        root: Path,
        *,
        kind: str,
        origin: str | None = None,
        exclude_top: tuple[str, ...] = (".git",),
        producer_run: str | None = None,
        producer_invocation: str | None = None,
    ) -> str:
        root = Path(root).resolve(strict=True)
        before = self._tree_paths(root, exclude_top)
        values: dict[str, tuple[bytes, int]] = {}
        for relative in before:
            values[relative] = self._read_regular_beneath(root, relative)
        after = self._tree_paths(root, exclude_top)
        if before != after:
            raise ArtifactStoreError("INPUT_CAPTURE_UNAVAILABLE: source file set changed during capture")
        for relative, expected in values.items():
            if self._read_regular_beneath(root, relative) != expected:
                raise ArtifactStoreError(f"INPUT_CAPTURE_UNAVAILABLE: source changed during capture: {relative}")
        return self.capture_mapping(
            values,
            kind=kind,
            origin=origin,
            producer_run=producer_run,
            producer_invocation=producer_invocation,
        )

    def snapshot_record(self, snapshot_id: str) -> dict[str, object]:
        with self.connect() as db:
            row = db.execute(
                "SELECT id, kind, origin, producer_run, producer_invocation, created_sequence "
                "FROM snapshots WHERE id=?",
                (snapshot_id,),
            ).fetchone()
        if row is None:
            raise ArtifactStoreError(f"unknown snapshot: {snapshot_id}")
        return dict(row)

    def snapshot_files(self, snapshot_id: str) -> list[dict[str, int | str]]:
        self.snapshot_record(snapshot_id)
        with self.connect() as db:
            rows = db.execute(
                "SELECT path, mode FROM snapshot_files WHERE snapshot_id = ? ORDER BY path",
                (snapshot_id,),
            ).fetchall()
        if not rows:
            raise ArtifactStoreError(f"empty snapshot: {snapshot_id}")
        return [{"path": row["path"], "mode": int(row["mode"])} for row in rows]

    def ref_record(self, value: object) -> dict[str, object]:
        item = validate_ref(value)
        with self.connect() as db:
            row = db.execute(
                "SELECT s.id AS snapshot, s.kind, s.origin, s.producer_run, s.producer_invocation, "
                "s.created_sequence, f.path, f.mode "
                "FROM snapshots s JOIN snapshot_files f ON f.snapshot_id=s.id "
                "WHERE s.id=? AND f.path=?",
                (item["snapshot"], item["path"]),
            ).fetchone()
        if row is None:
            raise ArtifactStoreError("snapshot reference is not registered")
        return dict(row)

    def assert_producer(
        self,
        value: object,
        *,
        run_id: str | None = None,
        invocation_id: str | None = None,
        kind: str | None = None,
    ) -> dict[str, object]:
        row = self.ref_record(value)
        if run_id is not None and row["producer_run"] != run_id:
            raise ArtifactStoreError("EVIDENCE_RUN_MISMATCH")
        if invocation_id is not None and row["producer_invocation"] != invocation_id:
            raise ArtifactStoreError("EVIDENCE_INVOCATION_MISMATCH")
        if kind is not None and row["kind"] != kind:
            raise ArtifactStoreError("EVIDENCE_KIND_MISMATCH")
        return row

    def resolve(self, value: object) -> Path:
        item = validate_ref(value)
        self.ref_record(item)
        path = self.root / "snapshots" / item["snapshot"]
        if path.is_symlink() or not path.is_dir():
            raise ArtifactStoreError("snapshot reference names an unknown or unsafe snapshot")
        for part in item["path"].split("/"):
            path = path / part
            if path.is_symlink():
                raise ArtifactStoreError("snapshot reference traverses a symlink")
        if not path.is_file():
            raise ArtifactStoreError("registered snapshot file is missing")
        return path

    def read_bytes(self, value: object) -> bytes:
        return self.resolve(value).read_bytes()

    def make_ref(self, snapshot_id: str, path: str) -> dict[str, str]:
        item = validate_ref({"snapshot": snapshot_id, "path": path})
        self.resolve(item)
        return item

    def same_as_file(self, value: object, live: Path) -> bool:
        live = Path(live)
        return live.is_file() and not live.is_symlink() and self.read_bytes(value) == live.read_bytes()

    def compare_tree(self, snapshot_id: str, root: Path, *, exclude_top: tuple[str, ...] = (".git",)) -> bool:
        root = Path(root).resolve(strict=True)
        stored = {str(row["path"]): row for row in self.snapshot_files(snapshot_id)}
        try:
            current_paths = self._tree_paths(root, exclude_top)
        except ArtifactStoreError:
            return False
        if set(stored) != set(current_paths):
            return False
        for relative, row in stored.items():
            try:
                data, mode = self._read_regular_beneath(root, relative)
            except ArtifactStoreError:
                return False
            stored_path = self.root / "snapshots" / snapshot_id / relative
            if data != stored_path.read_bytes() or mode != int(row["mode"]):
                return False
        return True

    def materialize_snapshot(self, snapshot_id: str, destination: Path, *, read_only: bool = False) -> Path:
        destination = Path(destination)
        if destination.exists() or destination.is_symlink():
            raise ArtifactStoreError("execution destination already exists")
        destination.mkdir(parents=True, mode=0o755 if read_only else 0o700)
        directories: set[Path] = {destination}
        try:
            for row in self.snapshot_files(snapshot_id):
                relative = str(row["path"])
                target = destination.joinpath(*relative.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o755 if read_only else 0o700)
                current = target.parent
                while current != destination.parent and current.is_relative_to(destination):
                    directories.add(current)
                    if current == destination:
                        break
                    current = current.parent
                source = self.root / "snapshots" / snapshot_id / relative
                with target.open("xb") as stream:
                    stream.write(source.read_bytes())
                source_mode = int(row["mode"])
                if read_only:
                    target.chmod(0o555 if source_mode & 0o111 else 0o444)
                else:
                    target.chmod(source_mode)
            if read_only:
                for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
                    directory.chmod(0o555)
            return destination
        except BaseException:
            for directory in sorted(directories, key=lambda item: len(item.parts)):
                try:
                    directory.chmod(0o755)
                except OSError:
                    pass
            shutil.rmtree(destination, ignore_errors=True)
            raise

    def delete_snapshot(self, snapshot_id: str) -> None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM snapshots WHERE id=?", (snapshot_id,))
            db.execute("COMMIT")
        shutil.rmtree(self.root / "snapshots" / snapshot_id, ignore_errors=True)
