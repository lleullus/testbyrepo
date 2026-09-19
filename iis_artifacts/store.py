"""Executor-owned immutable file snapshots without content-derived identities."""
from __future__ import annotations

from contextlib import contextmanager
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

    def next_sequence(self, name: str = "global") -> int:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT value FROM counters WHERE name = ?", (name,)).fetchone()
            value = 1 if row is None else int(row["value"]) + 1
            db.execute(
                "INSERT INTO counters(name, value) VALUES(?, ?) "
                "ON CONFLICT(name) DO UPDATE SET value = excluded.value",
                (name, value),
            )
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
                    data, mode = raw_value
                else:
                    data, mode = raw_value, 0o444
                if not isinstance(data, (bytes, bytearray)):
                    raise ArtifactStoreError("snapshot content must be bytes")
                source_mode = int(mode) & 0o777
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
                lexical = raw.relative_to(root)
            except ValueError as exc:
                raise ArtifactStoreError(f"capture path escapes root: {raw}") from exc
            current = root
            for part in lexical.parts:
                current = current / part
                if current.is_symlink():
                    raise ArtifactStoreError(f"snapshot input may not traverse a symlink: {raw}")
            try:
                details = current.lstat()
            except OSError as exc:
                raise ArtifactStoreError(f"cannot inspect snapshot input: {raw}") from exc
            if not stat.S_ISREG(details.st_mode):
                raise ArtifactStoreError(f"snapshot input must be a regular file: {raw}")
            canonical = current.resolve(strict=True)
            try:
                relative = canonical.relative_to(root).as_posix()
            except ValueError as exc:
                raise ArtifactStoreError(f"capture path escapes root: {raw}") from exc
            values[relative] = (canonical.read_bytes(), stat.S_IMODE(details.st_mode))
        return self.capture_mapping(
            values,
            kind=kind,
            origin=origin,
            producer_run=producer_run,
            producer_invocation=producer_invocation,
        )

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
        paths: list[Path] = []
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if relative.parts and relative.parts[0] in exclude_top:
                continue
            if path.is_symlink():
                raise ArtifactStoreError(f"snapshot tree contains a symlink: {relative.as_posix()}")
            if path.is_file():
                paths.append(path)
        return self.capture_files(
            root,
            paths,
            kind=kind,
            origin=origin,
            producer_run=producer_run,
            producer_invocation=producer_invocation,
        )

    def snapshot_files(self, snapshot_id: str) -> list[dict[str, int | str]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT path, mode FROM snapshot_files WHERE snapshot_id = ? ORDER BY path",
                (snapshot_id,),
            ).fetchall()
        if not rows:
            raise ArtifactStoreError(f"unknown or empty snapshot: {snapshot_id}")
        return [{"path": row["path"], "mode": int(row["mode"])} for row in rows]

    def resolve(self, value: object) -> Path:
        item = validate_ref(value)
        path = self.root / "snapshots" / item["snapshot"]
        if path.is_symlink() or not path.is_dir():
            raise ArtifactStoreError("snapshot reference names an unknown or unsafe snapshot")
        for part in item["path"].split("/"):
            path = path / part
            if path.is_symlink():
                raise ArtifactStoreError("snapshot reference traverses a symlink")
        if not path.is_file():
            raise ArtifactStoreError("snapshot reference does not name a stored file")
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
        current: dict[str, Path] = {}
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if relative.parts and relative.parts[0] in exclude_top:
                continue
            if path.is_symlink():
                return False
            if path.is_file():
                current[relative.as_posix()] = path
        if set(stored) != set(current):
            return False
        for relative, row in stored.items():
            path = current[relative]
            stored_path = self.root / "snapshots" / snapshot_id / relative
            if path.read_bytes() != stored_path.read_bytes():
                return False
            if stat.S_IMODE(path.stat().st_mode) != int(row["mode"]):
                return False
        return True
