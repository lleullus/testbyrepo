"""Recoverable publication of executor-owned fixed files into a project working tree."""
from __future__ import annotations

import errno
import os
from pathlib import Path
import re
import stat
import uuid

from .refs import validate_ref, validate_relative_path
from .store import ArtifactStore, ArtifactStoreError


THESIS_REVISION = re.compile(r"^docs/planning/product-thesis/[^/]+/THESIS-[0-9]{3,}\.md$")


class RevisionConflict(ArtifactStoreError):
    pass


def _schema(store: ArtifactStore) -> None:
    with store.connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS pending_publications(
              publication_id TEXT PRIMARY KEY,
              logical_path TEXT NOT NULL,
              source_snapshot TEXT NOT NULL,
              source_path TEXT NOT NULL,
              prior_snapshot TEXT,
              prior_path TEXT,
              state TEXT NOT NULL,
              created_sequence INTEGER NOT NULL
            );
            """
        )


def _open_parent(project_root: Path, logical_path: str, *, create: bool) -> tuple[int, str]:
    logical = validate_relative_path(logical_path)
    parts = logical.split("/")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        root_fd = os.open(Path(project_root).resolve(strict=True), flags)
    except OSError as exc:
        raise RevisionConflict("cannot open canonical project root") from exc
    root_details = os.fstat(root_fd)
    current_fd = root_fd
    opened: list[int] = []
    try:
        for part in parts[:-1]:
            try:
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, mode=0o755, dir_fd=current_fd)
                next_fd = os.open(part, flags, dir_fd=current_fd)
                details = os.fstat(next_fd)
                if (details.st_uid, details.st_gid) != (root_details.st_uid, root_details.st_gid):
                    os.fchown(next_fd, root_details.st_uid, root_details.st_gid)
                os.fchmod(next_fd, 0o755)
            except OSError as exc:
                raise RevisionConflict("publication path is unsafe") from exc
            opened.append(next_fd)
            current_fd = next_fd
        duplicate = os.dup(current_fd)
        return duplicate, parts[-1]
    except FileNotFoundError as exc:
        raise RevisionConflict("publication parent does not exist") from exc
    finally:
        for fd in reversed(opened):
            os.close(fd)
        os.close(root_fd)


def _read_live(project_root: Path, logical_path: str) -> bytes | None:
    try:
        parent_fd, leaf = _open_parent(project_root, logical_path, create=False)
    except RevisionConflict as exc:
        if "does not exist" in str(exc):
            return None
        raise
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(leaf, flags, dir_fd=parent_fd)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise RevisionConflict("publication target is unsafe") from exc
        try:
            details = os.fstat(fd)
            if not stat.S_ISREG(details.st_mode):
                raise RevisionConflict("publication target is not a regular file")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(fd)
    finally:
        os.close(parent_fd)


def _replace_live(project_root: Path, logical_path: str, data: bytes, *, mode: int) -> None:
    owner = Path(project_root).resolve(strict=True).stat()
    parent_fd, leaf = _open_parent(project_root, logical_path, create=True)
    temporary = f".{leaf}.publication-{uuid.uuid4().hex}"
    fd: int | None = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(temporary, flags, 0o600, dir_fd=parent_fd)
        details = os.fstat(fd)
        if (details.st_uid, details.st_gid) != (owner.st_uid, owner.st_gid):
            os.fchown(fd, owner.st_uid, owner.st_gid)
        os.fchmod(fd, mode)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.replace(temporary, leaf, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        os.fsync(parent_fd)
    except OSError as exc:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(temporary, dir_fd=parent_fd)
        except OSError:
            pass
        raise RevisionConflict("publication replace failed safely") from exc
    finally:
        os.close(parent_fd)
    if _read_live(project_root, logical_path) != data:
        raise RevisionConflict("publication path changed during replace")


def _finalize(store: ArtifactStore, publication_id: str, logical_path: str, source: dict[str, str]) -> None:
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        pending = db.execute(
            "SELECT * FROM pending_publications WHERE publication_id=?",
            (publication_id,),
        ).fetchone()
        if pending is None:
            db.execute("ROLLBACK")
            raise RevisionConflict("pending publication disappeared before finalize")
        row = db.execute(
            "SELECT generation FROM publications WHERE logical_path=?",
            (logical_path,),
        ).fetchone()
        generation = 1 if row is None else int(row["generation"]) + 1
        db.execute(
            "INSERT INTO publications(logical_path,snapshot_id,snapshot_path,generation,published_sequence) "
            "VALUES(?,?,?,?,?) "
            "ON CONFLICT(logical_path) DO UPDATE SET snapshot_id=excluded.snapshot_id,"
            "snapshot_path=excluded.snapshot_path,generation=excluded.generation,"
            "published_sequence=excluded.published_sequence",
            (
                logical_path,
                source["snapshot"],
                source["path"],
                generation,
                store.sequence_in(db, "publication-finalize"),
            ),
        )
        db.execute("DELETE FROM pending_publications WHERE publication_id=?", (publication_id,))
        db.execute("COMMIT")


def pending_publications(store: ArtifactStore) -> list[dict[str, object]]:
    _schema(store)
    with store.connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM pending_publications ORDER BY created_sequence")]


def recover_pending(store: ArtifactStore, project_root: Path) -> None:
    _schema(store)
    for row in pending_publications(store):
        source = {"snapshot": row["source_snapshot"], "path": row["source_path"]}
        prior = None
        if row["prior_snapshot"] is not None:
            prior = {"snapshot": row["prior_snapshot"], "path": row["prior_path"]}
        live = _read_live(project_root, str(row["logical_path"]))
        if live == store.read_bytes(source):
            _finalize(store, str(row["publication_id"]), str(row["logical_path"]), source)
            continue
        if prior is None and live is None:
            with store.connect() as db:
                db.execute("DELETE FROM pending_publications WHERE publication_id=?", (row["publication_id"],))
            continue
        if prior is not None and live == store.read_bytes(prior):
            with store.connect() as db:
                db.execute("DELETE FROM pending_publications WHERE publication_id=?", (row["publication_id"],))
            continue
        raise RevisionConflict(f"PENDING_PUBLICATION_CONFLICT:{row['logical_path']}")


def ensure_no_pending(store: ArtifactStore) -> None:
    if pending_publications(store):
        raise RevisionConflict("PENDING_PUBLICATION_RECOVERY_REQUIRED")


def published_ref(store: ArtifactStore, logical_path: str) -> dict[str, str] | None:
    logical = validate_relative_path(logical_path)
    with store.connect() as db:
        row = db.execute(
            "SELECT snapshot_id,snapshot_path FROM publications WHERE logical_path=?",
            (logical,),
        ).fetchone()
    if row is None:
        return None
    return {"snapshot": row["snapshot_id"], "path": row["snapshot_path"]}


def publish_ref(
    store: ArtifactStore,
    source_ref: object,
    project_root: Path,
    logical_path: str,
    *,
    expected_prior: object | None,
    fault_after_replace: bool = False,
) -> dict[str, str]:
    _schema(store)
    recover_pending(store, project_root)
    source = validate_ref(source_ref)
    logical = validate_relative_path(logical_path)
    if source["path"] != logical:
        raise RevisionConflict("candidate logical path does not match publication path")
    store.resolve(source)
    expected = None if expected_prior is None else validate_ref(expected_prior)
    if expected is not None:
        store.resolve(expected)

    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT snapshot_id,snapshot_path,generation FROM publications WHERE logical_path=?",
            (logical,),
        ).fetchone()
        current = None if row is None else {"snapshot": row["snapshot_id"], "path": row["snapshot_path"]}
        if current != expected:
            db.execute("ROLLBACK")
            raise RevisionConflict("REVISION_CONFLICT")
        if current is not None and THESIS_REVISION.fullmatch(logical):
            if store.read_bytes(current) != store.read_bytes(source):
                db.execute("ROLLBACK")
                raise RevisionConflict("IMMUTABLE_THESIS_REVISION")
        live = _read_live(project_root, logical)
        if current is None:
            if live is not None and live != store.read_bytes(source):
                db.execute("ROLLBACK")
                raise RevisionConflict("unregistered project file conflicts with publication")
        elif live != store.read_bytes(current):
            db.execute("ROLLBACK")
            raise RevisionConflict("published project file changed outside the store")
        publication_id = "pub-" + uuid.uuid4().hex
        db.execute(
            "INSERT INTO pending_publications(publication_id,logical_path,source_snapshot,source_path,"
            "prior_snapshot,prior_path,state,created_sequence) VALUES(?,?,?,?,?,?,'PREPARED',?)",
            (
                publication_id,
                logical,
                source["snapshot"],
                source["path"],
                None if current is None else current["snapshot"],
                None if current is None else current["path"],
                store.sequence_in(db, "publication-prepare"),
            ),
        )
        db.execute("COMMIT")

    source_mode = int(store.ref_record(source)["mode"])
    published_mode = 0o444 | (source_mode & 0o111)
    _replace_live(project_root, logical, store.read_bytes(source), mode=published_mode)
    if fault_after_replace:
        raise OSError("injected publication failure after replace")
    _finalize(store, publication_id, logical, source)
    return source
