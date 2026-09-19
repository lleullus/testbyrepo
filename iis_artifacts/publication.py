"""Atomic publication of fixed store files into a project working tree."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile

from .refs import validate_ref, validate_relative_path
from .store import ArtifactStore, ArtifactStoreError


class RevisionConflict(ArtifactStoreError):
    pass


def _target(project_root: Path, logical_path: str) -> Path:
    relative = validate_relative_path(logical_path)
    root = Path(project_root).resolve(strict=True)
    target = root.joinpath(*relative.split("/"))
    current = root
    for part in relative.split("/")[:-1]:
        current = current / part
        if current.is_symlink():
            raise RevisionConflict("publication path traverses a symlink")
    return target


def publish_ref(
    store: ArtifactStore,
    source_ref: object,
    project_root: Path,
    logical_path: str,
    *,
    expected_prior: object | None,
) -> dict[str, str]:
    source = validate_ref(source_ref)
    if source["path"] != validate_relative_path(logical_path):
        raise RevisionConflict("candidate logical path does not match publication path")
    target = _target(project_root, logical_path)
    sequence = store.next_sequence()
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT snapshot_id, snapshot_path, generation FROM publications WHERE logical_path = ?",
            (logical_path,),
        ).fetchone()
        current = None if row is None else {"snapshot": row["snapshot_id"], "path": row["snapshot_path"]}
        expected = None if expected_prior is None else validate_ref(expected_prior)
        if current != expected:
            db.execute("ROLLBACK")
            raise RevisionConflict("REVISION_CONFLICT")
        if current is None:
            if target.exists() or target.is_symlink():
                if not target.is_file() or target.is_symlink() or target.read_bytes() != store.read_bytes(source):
                    db.execute("ROLLBACK")
                    raise RevisionConflict("unregistered project file conflicts with publication")
        elif not store.same_as_file(current, target):
            db.execute("ROLLBACK")
            raise RevisionConflict("published project file changed outside the store")
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix="." + target.name + ".", dir=target.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(store.read_bytes(source))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            generation = 1 if row is None else int(row["generation"]) + 1
            db.execute(
                "INSERT INTO publications(logical_path, snapshot_id, snapshot_path, generation, published_sequence) "
                "VALUES(?, ?, ?, ?, ?) "
                "ON CONFLICT(logical_path) DO UPDATE SET snapshot_id=excluded.snapshot_id, "
                "snapshot_path=excluded.snapshot_path, generation=excluded.generation, "
                "published_sequence=excluded.published_sequence",
                (logical_path, source["snapshot"], source["path"], generation, sequence),
            )
            db.execute("COMMIT")
        except BaseException:
            temporary.unlink(missing_ok=True)
            try:
                db.execute("ROLLBACK")
            except Exception:
                pass
            raise
    return source
