"""comic-new transactional store: single durable SQLite authority."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


class TransactionalStoreError(Exception):
    """Base exception for all transactional store errors."""


class ConflictError(TransactionalStoreError):
    """Raised when expected authority or composition revision does not match actual authoritative revision."""

    def __init__(self, expected: int, actual: int, message: str | None = None) -> None:
        self.expected = expected
        self.actual = actual
        msg = message or f"Conflict: expected authority revision {expected}, actual is {actual}"
        super().__init__(msg)


class StoreCorruptionError(TransactionalStoreError):
    """Raised when database invariants or schema integrity are violated."""


class ProjectAlreadyExistsError(TransactionalStoreError):
    """Raised when attempting to initialize a project where one already exists."""


class ProjectNotFoundError(TransactionalStoreError):
    """Raised when attempting to open a non-existent project database."""


class RealizationIncompleteError(TransactionalStoreError):
    """Raised when an operation requires all cuts to be current but one or more are not."""


class InvalidArtifactClosureError(TransactionalStoreError):
    """Raised when an artifact closure does not match current authoritative state."""


class AuthorizationRevokedError(TransactionalStoreError):
    """Raised when an operation references a revoked or inactive release authorization."""


class StaleRealizationError(TransactionalStoreError):
    """Raised when a realization commit is rejected because job target revision is stale."""


class InvalidJobStateError(TransactionalStoreError):
    """Raised when attempting an invalid transition on a generation job or attempt."""


class ValidationError(TransactionalStoreError):
    """Raised when input parameters fail domain validation rules."""


class RunnerAlreadyActiveError(TransactionalStoreError):
    """Raised when another runner is already active for this project."""

class TransactionalStore:
    """Concrete single SQLite transactional authority for comic_new."""

    APPLICATION_ID: int = 0x434F4D43  # 'COMC'
    SCHEMA_VERSION: int = 2
    DB_FILENAME: str = "comic-new.sqlite3"
    BUSY_TIMEOUT_MS: int = 5000

    REQUIRED_TABLES: frozenset[str] = frozenset({
        "authority",
        "structural_baselines",
        "cut_intents",
        "cuts",
        "baseline_intents",
        "composition",
        "generation_jobs",
        "generation_attempts",
        "generation_control",
        "review_artifacts",
        "artifact_cuts",
        "release_authorizations",
        "delivery_attempts",
    })
    REQUIRED_TRIGGERS: frozenset[str] = frozenset({
        "trg_cuts_no_insert",
        "trg_cuts_no_delete",
        "trg_cuts_no_update_cut_id",
    })
    REQUIRED_INDEXES: frozenset[str] = frozenset({
        "idx_active_release_authorization",
        "idx_generation_jobs_queued",
    })
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()

    @property
    def project_dir(self) -> Path:
        return self.db_path.parent

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(
            str(self.db_path),
            timeout=self.BUSY_TIMEOUT_MS / 1000.0,
            isolation_level=None,  # Explicit manual transaction control
        )
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        con.execute(f"PRAGMA busy_timeout = {self.BUSY_TIMEOUT_MS};")
        return con

    @classmethod
    def create_project(cls, project_dir: str | Path) -> TransactionalStore:
        p = Path(project_dir).resolve()
        if p.exists() and not p.is_dir():
            raise ValidationError(f"Target path {p} exists and is not a directory")
        p.mkdir(parents=True, exist_ok=True)
        db_path = p / cls.DB_FILENAME

        if db_path.exists():
            try:
                if db_path.stat().st_size == 0:
                    pass  # Empty crashed placeholder, safe to reinitialize
                else:
                    try:
                        cls(db_path).verify_schema()
                        raise ProjectAlreadyExistsError(f"Project already initialized at {p}")
                    except ProjectAlreadyExistsError:
                        raise
                    except Exception as e:
                        raise StoreCorruptionError(
                            f"Unrecognized or partially initialized database at {db_path}: {e}"
                        ) from e
            except (ProjectAlreadyExistsError, StoreCorruptionError):
                raise
            except Exception as e:
                raise StoreCorruptionError(f"Cannot inspect existing database at {db_path}: {e}") from e

        schema_sql_path = Path(__file__).parent / "schema.sql"
        if not schema_sql_path.is_file():
            raise StoreCorruptionError(f"Missing schema definition at {schema_sql_path}")
        sql_text = schema_sql_path.read_text(encoding="utf-8")

        tmp_db_path = p / f".{cls.DB_FILENAME}.tmp.{uuid4().hex}"
        con = sqlite3.connect(str(tmp_db_path), timeout=cls.BUSY_TIMEOUT_MS / 1000.0)
        try:
            con.execute("PRAGMA foreign_keys = ON;")
            init_script = (
                "BEGIN IMMEDIATE;\n"
                f"PRAGMA application_id = {cls.APPLICATION_ID};\n"
                f"PRAGMA user_version = {cls.SCHEMA_VERSION};\n"
                f"{sql_text}\n"
                "COMMIT;\n"
            )
            con.executescript(init_script)
            con.close()
            cls(tmp_db_path).verify_schema()
            os.replace(tmp_db_path, db_path)
        except Exception as e:
            try:
                con.rollback()
            except Exception:
                pass
            try:
                con.close()
            except Exception:
                pass
            tmp_db_path.unlink(missing_ok=True)
            if not isinstance(e, StoreCorruptionError):
                raise StoreCorruptionError(f"Database initialization failed: {e}") from e
            raise

        store = cls(db_path)
        store.verify_schema()
        return store

    @classmethod
    def open_project(cls, project_dir: str | Path) -> TransactionalStore:
        p = Path(project_dir).resolve()
        db_path = p / cls.DB_FILENAME
        if not db_path.is_file():
            raise ProjectNotFoundError(f"No comic-new database found at {db_path}")
        store = cls(db_path)
        store._check_and_apply_migrations()
        store.verify_schema()
        return store

    def _check_and_apply_migrations(self) -> None:
        with self._connect() as con:
            app_id_row = con.execute("PRAGMA application_id;").fetchone()
            app_id = app_id_row[0] if app_id_row else 0
            if app_id != self.APPLICATION_ID:
                raise StoreCorruptionError(f"Expected application_id {self.APPLICATION_ID}, got {app_id}")

            user_ver_row = con.execute("PRAGMA user_version;").fetchone()
            user_ver = user_ver_row[0] if user_ver_row else 0
            if user_ver == 1:
                master_rows = con.execute("SELECT type, name FROM sqlite_master;").fetchall()
                existing_tables = {row["name"] for row in master_rows if row["type"] == "table"}
                v1_missing = (self.REQUIRED_TABLES - {"generation_control"}) - existing_tables
                if v1_missing:
                    raise StoreCorruptionError(f"Missing required tables: {sorted(v1_missing)}")
                existing_triggers = {row["name"] for row in master_rows if row["type"] == "trigger"}
                missing_triggers = self.REQUIRED_TRIGGERS - existing_triggers
                if missing_triggers:
                    raise StoreCorruptionError(f"Missing required triggers: {sorted(missing_triggers)}")
                mig_path = Path(__file__).parent / "migrations" / "v1_to_v2.sql"
                if not mig_path.is_file():
                    raise StoreCorruptionError(f"Missing migration script at {mig_path}")
                mig_sql = mig_path.read_text(encoding="utf-8")
                statements = [s.strip() for s in mig_sql.split(";") if s.strip()]
                try:
                    con.execute("BEGIN IMMEDIATE;")
                    for stmt in statements:
                        con.execute(stmt)
                    con.execute("COMMIT;")
                except Exception as e:
                    if con.in_transaction:
                        con.execute("ROLLBACK;")
                    raise StoreCorruptionError(f"Migration from v1 to v2 failed: {e}") from e
            elif user_ver == 2:
                pass
            else:
                raise StoreCorruptionError(f"Unrecognized schema version: {user_ver}")

    def verify_schema(self) -> None:
        with self._connect() as con:
            app_id_row = con.execute("PRAGMA application_id;").fetchone()
            app_id = app_id_row[0] if app_id_row else 0
            if app_id != self.APPLICATION_ID:
                raise StoreCorruptionError(f"Expected application_id {self.APPLICATION_ID}, got {app_id}")

            user_ver_row = con.execute("PRAGMA user_version;").fetchone()
            user_ver = user_ver_row[0] if user_ver_row else 0
            if user_ver != self.SCHEMA_VERSION:
                raise StoreCorruptionError(f"Expected schema version {self.SCHEMA_VERSION}, got {user_ver}")

            master_rows = con.execute("SELECT type, name FROM sqlite_master;").fetchall()
            existing_tables = {row["name"] for row in master_rows if row["type"] == "table"}
            existing_triggers = {row["name"] for row in master_rows if row["type"] == "trigger"}
            existing_indexes = {row["name"] for row in master_rows if row["type"] == "index"}

            missing_tables = self.REQUIRED_TABLES - existing_tables
            if missing_tables:
                raise StoreCorruptionError(f"Missing required tables: {sorted(missing_tables)}")

            missing_triggers = self.REQUIRED_TRIGGERS - existing_triggers
            if missing_triggers:
                raise StoreCorruptionError(f"Missing required triggers: {sorted(missing_triggers)}")

            missing_indexes = self.REQUIRED_INDEXES - existing_indexes
            if missing_indexes:
                raise StoreCorruptionError(f"Missing required indexes: {sorted(missing_indexes)}")

            cut_rows = con.execute("SELECT cut_id FROM cuts ORDER BY cut_id;").fetchall()
            cut_ids = [row[0] for row in cut_rows]
            if cut_ids != [1, 2, 3, 4, 5]:
                raise StoreCorruptionError(f"Expected cuts [1, 2, 3, 4, 5], found {cut_ids}")

            auth_row = con.execute("SELECT count(*) FROM authority WHERE singleton_id = 1;").fetchone()
            auth = auth_row[0] if auth_row else 0
            if auth != 1:
                raise StoreCorruptionError("Missing authority singleton")

            comp_row = con.execute("SELECT count(*) FROM composition WHERE singleton_id = 1;").fetchone()
            comp = comp_row[0] if comp_row else 0
            if comp != 1:
                raise StoreCorruptionError("Missing composition singleton")

            ctrl_row = con.execute("SELECT count(*) FROM generation_control WHERE singleton_id = 1;").fetchone()
            ctrl = ctrl_row[0] if ctrl_row else 0
            if ctrl != 1:
                raise StoreCorruptionError("Missing generation_control singleton")

            att_cols = {row["name"] for row in con.execute("PRAGMA table_info(generation_attempts);").fetchall()}
            expected_att_cols = {
                "attempt_id", "job_id", "ordinal", "status", "started_at", "finished_at", "detail",
                "runner_id", "process_pid", "process_group_id", "process_start_token", "staging_path", "provider_request_id"
            }
            missing_att_cols = expected_att_cols - att_cols
            if missing_att_cols:
                raise StoreCorruptionError(f"generation_attempts missing columns: {sorted(missing_att_cols)}")
    def _begin_mutation(self, con: sqlite3.Connection, expected_authority_revision: int) -> int:
        con.execute("BEGIN IMMEDIATE;")
        row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
        if row is None:
            raise StoreCorruptionError("Missing authority singleton")
        actual_rev = row["authority_revision"]
        if actual_rev != expected_authority_revision:
            raise ConflictError(expected=expected_authority_revision, actual=actual_rev)
        return actual_rev + 1

    def _revoke_active_authorization(
        self, con: sqlite3.Connection, new_authority_revision: int, now_iso: str
    ) -> bool:
        cur = con.execute(
            """
            UPDATE release_authorizations
            SET revoked_authority_revision = ?, revoked_at = ?
            WHERE revoked_authority_revision IS NULL
            """,
            (new_authority_revision, now_iso),
        )
        return cur.rowcount > 0

    def snapshot(self) -> dict[str, Any]:
        with self._connect() as con:
            con.execute("BEGIN DEFERRED;")
            user_ver = con.execute("PRAGMA user_version").fetchone()[0]
            auth_row = con.execute(
                "SELECT authority_revision, current_baseline_id FROM authority WHERE singleton_id = 1"
            ).fetchone()
            if not auth_row:
                raise StoreCorruptionError("Missing authority singleton")
            auth_rev = auth_row["authority_revision"]
            current_baseline_id = auth_row["current_baseline_id"]

            baseline_data: dict[str, Any] | None = None
            if current_baseline_id is not None:
                b_row = con.execute(
                    "SELECT baseline_id, structure_json, authority_revision, created_at FROM structural_baselines WHERE baseline_id = ?",
                    (current_baseline_id,),
                ).fetchone()
                if b_row:
                    intents_rows = con.execute(
                        "SELECT cut_id, intent_revision FROM baseline_intents WHERE baseline_id = ? ORDER BY cut_id ASC",
                        (current_baseline_id,),
                    ).fetchall()
                    baseline_data = {
                        "baseline_id": b_row["baseline_id"],
                        "structure": json.loads(b_row["structure_json"]),
                        "authority_revision": b_row["authority_revision"],
                        "created_at": b_row["created_at"],
                        "intents": [
                            {"cut_id": ir["cut_id"], "intent_revision": ir["intent_revision"]}
                            for ir in intents_rows
                        ],
                    }

            cuts_rows = con.execute(
                """
                SELECT c.cut_id, c.desired_revision, c.realized_revision,
                       c.realized_asset_id, c.realized_asset_path, c.realized_content_hash,
                       i.payload_json AS effective_intent_json
                FROM cuts c
                LEFT JOIN cut_intents i ON c.cut_id = i.cut_id AND c.desired_revision = i.revision
                ORDER BY c.cut_id ASC
                """
            ).fetchall()

            if len(cuts_rows) != 5:
                raise StoreCorruptionError(f"Expected exactly 5 cuts, found {len(cuts_rows)}")

            cuts_data: list[dict[str, Any]] = []
            all_current = True
            for row in cuts_rows:
                cid = row["cut_id"]
                d_rev = row["desired_revision"]
                r_rev = row["realized_revision"]
                eff_intent = (
                    json.loads(row["effective_intent_json"])
                    if row["effective_intent_json"] is not None
                    else None
                )

                is_current = d_rev is not None and r_rev is not None and d_rev == r_rev
                currency = "CURRENT" if is_current else "STALE"
                if not is_current:
                    all_current = False

                cuts_data.append(
                    {
                        "cut_id": cid,
                        "desired_revision": d_rev,
                        "effective_intent": eff_intent,
                        "realized_revision": r_rev,
                        "realized_asset_id": row["realized_asset_id"],
                        "realized_asset_path": row["realized_asset_path"],
                        "realized_content_hash": row["realized_content_hash"],
                        "currency": currency,
                    }
                )

            realization_complete = {
                "complete": all_current,
                "status": "COMPLETE" if all_current else "UNRESOLVED",
            }

            comp_row = con.execute(
                "SELECT revision, state_json, updated_at FROM composition WHERE singleton_id = 1"
            ).fetchone()
            if not comp_row:
                raise StoreCorruptionError("Missing composition singleton")
            composition_data = {
                "revision": comp_row["revision"],
                "state": json.loads(comp_row["state_json"]),
                "updated_at": comp_row["updated_at"],
            }

            jobs_rows = con.execute("SELECT * FROM generation_jobs ORDER BY created_at ASC").fetchall()
            jobs_data: list[dict[str, Any]] = []
            for j in jobs_rows:
                jid = j["job_id"]
                att_rows = con.execute(
                    "SELECT * FROM generation_attempts WHERE job_id = ? ORDER BY ordinal ASC", (jid,)
                ).fetchall()
                jobs_data.append(
                    {
                        "job_id": jid,
                        "cut_id": j["cut_id"],
                        "target_desired_revision": j["target_desired_revision"],
                        "status": j["status"],
                        "terminal_detail": j["terminal_detail"],
                        "created_at": j["created_at"],
                        "updated_at": j["updated_at"],
                        "attempts": [
                            {
                                "attempt_id": a["attempt_id"],
                                "ordinal": a["ordinal"],
                                "status": a["status"],
                                "started_at": a["started_at"],
                                "finished_at": a["finished_at"],
                                "detail": a["detail"],
                                "runner_id": a["runner_id"],
                                "process_pid": a["process_pid"],
                                "process_group_id": a["process_group_id"],
                                "process_start_token": a["process_start_token"],
                                "staging_path": a["staging_path"],
                                "provider_request_id": a["provider_request_id"],
                            }
                            for a in att_rows
                        ],
                    }
                )

            art_rows = con.execute("SELECT * FROM review_artifacts ORDER BY created_at ASC").fetchall()
            artifacts_data: list[dict[str, Any]] = []
            for art in art_rows:
                aid = art["artifact_id"]
                ac_rows = con.execute(
                    "SELECT cut_id, realized_revision, asset_id FROM artifact_cuts WHERE artifact_id = ? ORDER BY cut_id ASC",
                    (aid,),
                ).fetchall()
                artifacts_data.append(
                    {
                        "artifact_id": aid,
                        "content_hash": art["content_hash"],
                        "composition_revision": art["composition_revision"],
                        "created_at": art["created_at"],
                        "cuts": [
                            {
                                "cut_id": ac["cut_id"],
                                "realized_revision": ac["realized_revision"],
                                "asset_id": ac["asset_id"],
                            }
                            for ac in ac_rows
                        ],
                    }
                )

            active_auth_row = con.execute(
                "SELECT * FROM release_authorizations WHERE revoked_authority_revision IS NULL"
            ).fetchone()
            active_auth = None
            if active_auth_row:
                active_auth = {
                    "authorization_id": active_auth_row["authorization_id"],
                    "artifact_id": active_auth_row["artifact_id"],
                    "artifact_content_hash": active_auth_row["artifact_content_hash"],
                    "authorized_authority_revision": active_auth_row["authorized_authority_revision"],
                    "created_at": active_auth_row["created_at"],
                }

            revoked_auth_rows = con.execute(
                "SELECT * FROM release_authorizations WHERE revoked_authority_revision IS NOT NULL ORDER BY created_at ASC"
            ).fetchall()
            revoked_auths = [
                {
                    "authorization_id": r["authorization_id"],
                    "artifact_id": r["artifact_id"],
                    "artifact_content_hash": r["artifact_content_hash"],
                    "authorized_authority_revision": r["authorized_authority_revision"],
                    "revoked_authority_revision": r["revoked_authority_revision"],
                    "created_at": r["created_at"],
                    "revoked_at": r["revoked_at"],
                }
                for r in revoked_auth_rows
            ]

            del_rows = con.execute("SELECT * FROM delivery_attempts ORDER BY created_at ASC").fetchall()
            delivery_data: list[dict[str, Any]] = []
            for d in del_rows:
                delivery_data.append(
                    {
                        "attempt_id": d["attempt_id"],
                        "kind": d["kind"],
                        "authorization_id": d["authorization_id"],
                        "artifact_id": d["artifact_id"],
                        "request_id": d["request_id"],
                        "outcome": d["outcome"],
                        "destination_id": d["destination_id"],
                        "destination_url": d["destination_url"],
                        "evidence": (
                            json.loads(d["evidence_json"]) if d["evidence_json"] is not None else None
                        ),
                        "observed_authority_revision": d["observed_authority_revision"],
                        "created_at": d["created_at"],
                        "updated_at": d["updated_at"],
                    }
                )

            ctrl_row = con.execute(
                "SELECT stop_epoch, runner_id, runner_pid, runner_start_token, runner_started_at FROM generation_control WHERE singleton_id = 1"
            ).fetchone()
            ctrl_data = {
                "stop_epoch": ctrl_row["stop_epoch"] if ctrl_row else 0,
                "runner_id": ctrl_row["runner_id"] if ctrl_row else None,
                "runner_pid": ctrl_row["runner_pid"] if ctrl_row else None,
                "runner_start_token": ctrl_row["runner_start_token"] if ctrl_row else None,
                "runner_started_at": ctrl_row["runner_started_at"] if ctrl_row else None,
            }

            con.execute("COMMIT;")
            return {
                "schema_version": user_ver,
                "authority_revision": auth_rev,
                "baseline": baseline_data,
                "cuts": cuts_data,
                "realization_complete": realization_complete,
                "composition": composition_data,
                "jobs": jobs_data,
                "review_artifacts": artifacts_data,
                "release_authorization": {
                    "active": active_auth,
                    "history": revoked_auths,
                },
                "delivery_attempts": delivery_data,
                "generation_control": ctrl_data,
            }

    def approve_structural_baseline(
        self,
        expected_authority_revision: int,
        baseline_id: str,
        structure: dict[str, Any] | str,
        intents_by_cut: dict[int, dict[str, Any] | str],
    ) -> int:
        if not baseline_id or not isinstance(baseline_id, str):
            raise ValidationError("baseline_id must be a non-empty string")
        if set(intents_by_cut.keys()) != {1, 2, 3, 4, 5}:
            raise ValidationError("intents_by_cut must contain exactly keys 1 through 5")

        struct_json = (
            json.dumps(structure, sort_keys=True) if isinstance(structure, dict) else str(structure)
        )
        now_iso = datetime.now(timezone.utc).isoformat()

        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            con.execute(
                "INSERT INTO structural_baselines (baseline_id, structure_json, authority_revision, created_at) VALUES (?, ?, ?, ?)",
                (baseline_id, struct_json, new_rev, now_iso),
            )

            for cut_id in (1, 2, 3, 4, 5):
                cur_des_row = con.execute(
                    "SELECT desired_revision FROM cuts WHERE cut_id = ?", (cut_id,)
                ).fetchone()
                cur_des = cur_des_row["desired_revision"] if cur_des_row else None
                new_intent_rev = (cur_des or 0) + 1
                payload_val = intents_by_cut[cut_id]
                payload_json = (
                    json.dumps(payload_val, sort_keys=True)
                    if isinstance(payload_val, dict)
                    else str(payload_val)
                )

                con.execute(
                    "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (cut_id, new_intent_rev, baseline_id, payload_json, new_rev, now_iso),
                )
                con.execute(
                    "UPDATE cuts SET desired_revision = ? WHERE cut_id = ?", (new_intent_rev, cut_id)
                )
                con.execute(
                    "INSERT INTO baseline_intents (baseline_id, cut_id, intent_revision) VALUES (?, ?, ?)",
                    (baseline_id, cut_id, new_intent_rev),
                )

            con.execute(
                "UPDATE authority SET current_baseline_id = ?, authority_revision = ? WHERE singleton_id = 1",
                (baseline_id, new_rev),
            )
            self._revoke_active_authorization(con, new_rev, now_iso)
            con.execute("COMMIT;")
            return new_rev
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def accept_cut_intent(
        self, expected_authority_revision: int, cut_id: int, intent_payload: dict[str, Any] | str
    ) -> int:
        if cut_id not in (1, 2, 3, 4, 5):
            raise ValidationError(f"Invalid cut_id {cut_id}; must be between 1 and 5")
        payload_json = (
            json.dumps(intent_payload, sort_keys=True)
            if isinstance(intent_payload, dict)
            else str(intent_payload)
        )
        now_iso = datetime.now(timezone.utc).isoformat()

        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            cur_base_row = con.execute(
                "SELECT current_baseline_id FROM authority WHERE singleton_id = 1"
            ).fetchone()
            cur_base_id = cur_base_row["current_baseline_id"] if cur_base_row else None

            cur_des_row = con.execute(
                "SELECT desired_revision FROM cuts WHERE cut_id = ?", (cut_id,)
            ).fetchone()
            cur_des = cur_des_row["desired_revision"] if cur_des_row else None
            new_intent_rev = (cur_des or 0) + 1

            con.execute(
                "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (cut_id, new_intent_rev, cur_base_id, payload_json, new_rev, now_iso),
            )
            con.execute(
                "UPDATE cuts SET desired_revision = ? WHERE cut_id = ?", (new_intent_rev, cut_id)
            )
            self._revoke_active_authorization(con, new_rev, now_iso)
            con.execute(
                "UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,)
            )
            con.execute("COMMIT;")
            return new_rev
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def accept_composition(
        self,
        expected_authority_revision: int,
        expected_composition_revision: int,
        state: dict[str, Any],
    ) -> tuple[int, int]:
        from comic_new.composition import canonical_json_dumps, normalize_state

        norm_state = normalize_state(state)
        state_json = canonical_json_dumps(norm_state)
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            comp_row = con.execute("SELECT revision FROM composition WHERE singleton_id = 1").fetchone()
            if not comp_row:
                raise StoreCorruptionError("Missing composition singleton")
            cur_comp_rev = comp_row["revision"]
            if cur_comp_rev != expected_composition_revision:
                raise ConflictError(
                    expected=expected_composition_revision,
                    actual=cur_comp_rev,
                    message=f"Composition conflict: expected composition revision {expected_composition_revision}, actual is {cur_comp_rev}",
                )

            new_comp_rev = cur_comp_rev + 1
            con.execute(
                "UPDATE composition SET revision = ?, state_json = ?, updated_at = ? WHERE singleton_id = 1",
                (new_comp_rev, state_json, now_iso),
            )
            self._revoke_active_authorization(con, new_rev, now_iso)
            con.execute(
                "UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,)
            )
            con.execute("COMMIT;")
            return (new_rev, new_comp_rev)
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def enqueue_generation_jobs(
        self,
        expected_authority_revision: int,
        cut_id: int | None = None,
    ) -> tuple[int, list[dict[str, Any]]]:
        if cut_id is not None and cut_id not in (1, 2, 3, 4, 5):
            raise ValidationError(f"Invalid cut_id {cut_id}; must be between 1 and 5")
        target_cuts = [1, 2, 3, 4, 5] if cut_id is None else [cut_id]
        now_iso = datetime.now(timezone.utc).isoformat()

        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)

            # Pre-validate all target cuts have desired intent and non-empty prompt
            cuts_to_enqueue: list[tuple[int, int]] = []
            for cid in target_cuts:
                cut_row = con.execute("SELECT desired_revision FROM cuts WHERE cut_id = ?", (cid,)).fetchone()
                if not cut_row or cut_row["desired_revision"] is None:
                    raise ValidationError(f"Cut {cid} has no desired intent to generate")
                d_rev = cut_row["desired_revision"]
                intent_row = con.execute(
                    "SELECT payload_json FROM cut_intents WHERE cut_id = ? AND revision = ?",
                    (cid, d_rev),
                ).fetchone()
                if not intent_row:
                    raise ValidationError(f"Cut {cid} revision {d_rev} intent record not found")
                payload = json.loads(intent_row["payload_json"])
                prompt_str = payload if isinstance(payload, str) else (payload.get("prompt") or payload.get("text") if isinstance(payload, dict) else None)
                if not prompt_str or not isinstance(prompt_str, str) or not prompt_str.strip():
                    raise ValidationError(f"Cut {cid} revision {d_rev} intent payload does not contain a non-empty prompt")
                cuts_to_enqueue.append((cid, d_rev))

            created_jobs: list[dict[str, Any]] = []
            for cid, d_rev in cuts_to_enqueue:
                job_id = f"job-{cid}-r{d_rev}-{uuid4().hex[:8]}"
                con.execute(
                    "INSERT INTO generation_jobs (job_id, cut_id, target_desired_revision, status, created_at, updated_at) VALUES (?, ?, ?, 'queued', ?, ?)",
                    (job_id, cid, d_rev, now_iso, now_iso),
                )
                created_jobs.append({
                    "job_id": job_id,
                    "cut_id": cid,
                    "target_desired_revision": d_rev,
                })

            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
            con.execute("COMMIT;")
            return (new_rev, created_jobs)
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def acquire_runner_ownership(
        self,
        runner_id: str,
        runner_pid: int,
        runner_start_token: str,
        is_pid_alive_fn: Any = None,
    ) -> int:
        if is_pid_alive_fn is None:
            from comic_new.generation import is_process_alive_with_token
            is_pid_alive_fn = is_process_alive_with_token
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            row = con.execute(
                "SELECT stop_epoch, runner_id, runner_pid, runner_start_token FROM generation_control WHERE singleton_id = 1"
            ).fetchone()
            if not row:
                raise StoreCorruptionError("Missing generation_control singleton")

            if row["runner_pid"] is not None:
                if is_pid_alive_fn(row["runner_pid"], row["runner_start_token"]):
                    raise RunnerAlreadyActiveError(
                        f"Runner {row['runner_id']} (pid {row['runner_pid']}) is currently active"
                    )

            con.execute(
                "UPDATE generation_control SET runner_id = ?, runner_pid = ?, runner_start_token = ?, runner_started_at = ? WHERE singleton_id = 1",
                (runner_id, runner_pid, runner_start_token, now_iso),
            )
            stop_epoch = row["stop_epoch"]
            con.execute("COMMIT;")
            return stop_epoch
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def release_runner_ownership(self, runner_id: str) -> None:
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            con.execute(
                "UPDATE generation_control SET runner_id = NULL, runner_pid = NULL, runner_start_token = NULL, runner_started_at = NULL WHERE singleton_id = 1 AND runner_id = ?",
                (runner_id,),
            )
            con.execute("COMMIT;")
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def reconcile_startup_orphans(self) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            rows = con.execute(
                """
                SELECT a.attempt_id, a.job_id, a.runner_id, a.process_pid, a.process_group_id, a.process_start_token, a.staging_path
                FROM generation_attempts a
                JOIN generation_jobs j ON a.job_id = j.job_id
                WHERE a.status = 'running'
                """
            ).fetchall()
            con.execute("COMMIT;")
            return [dict(r) for r in rows]
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def mark_startup_orphans_interrupted(self, running_items: list[tuple[str, str]]) -> None:
        if not running_items:
            return
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            for job_id, attempt_id in running_items:
                con.execute(
                    "UPDATE generation_attempts SET status = 'interrupted', finished_at = ?, detail = 'startup_recovery' WHERE attempt_id = ? AND status = 'running'",
                    (now_iso, attempt_id),
                )
                con.execute(
                    "UPDATE generation_jobs SET status = 'interrupted', terminal_detail = 'startup_recovery', updated_at = ? WHERE job_id = ? AND status = 'running'",
                    (now_iso, job_id),
                )
            auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
            new_rev = auth_row[0] + 1
            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
            con.execute("COMMIT;")
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def claim_next_generation_job(
        self,
        runner_id: str,
        runner_pid: int,
        runner_start_token: str,
        captured_stop_epoch: int,
        staging_base_dir: Path,
    ) -> dict[str, Any] | None:
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            ctrl_row = con.execute(
                "SELECT stop_epoch, runner_id, runner_pid, runner_start_token FROM generation_control WHERE singleton_id = 1"
            ).fetchone()
            if not ctrl_row:
                con.execute("ROLLBACK;")
                return None
            if ctrl_row["stop_epoch"] != captured_stop_epoch:
                con.execute("ROLLBACK;")
                return None
            if ctrl_row["runner_id"] != runner_id:
                con.execute("ROLLBACK;")
                return None

            while True:
                row = con.execute(
                    "SELECT job_id, cut_id, target_desired_revision FROM generation_jobs WHERE status = 'queued' ORDER BY created_at ASC, job_id ASC LIMIT 1"
                ).fetchone()
                if not row:
                    con.execute("COMMIT;")
                    return None

                job_id = row["job_id"]
                cut_id = row["cut_id"]
                target_rev = row["target_desired_revision"]

                cut_row = con.execute("SELECT desired_revision FROM cuts WHERE cut_id = ?", (cut_id,)).fetchone()
                cur_desired = cut_row["desired_revision"] if cut_row else None
                now_iso = datetime.now(timezone.utc).isoformat()

                if cur_desired != target_rev:
                    # Stale: supersede immediately without spawning
                    con.execute(
                        "UPDATE generation_jobs SET status = 'superseded', terminal_detail = 'Target revision superseded before claim', updated_at = ? WHERE job_id = ?",
                        (now_iso, job_id),
                    )
                    auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
                    new_rev = auth_row[0] + 1
                    con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
                    # Loop to check next queued job
                    continue

                # Intent matches current desired: claim this job
                intent_row = con.execute(
                    "SELECT payload_json FROM cut_intents WHERE cut_id = ? AND revision = ?",
                    (cut_id, target_rev),
                ).fetchone()
                payload = json.loads(intent_row["payload_json"])
                prompt = payload if isinstance(payload, str) else (payload.get("prompt") or payload.get("text"))

                attempt_id = f"att-{job_id}-1"
                staging_dir = staging_base_dir / job_id
                staging_dir.mkdir(parents=True, exist_ok=True)
                candidate_path = staging_dir / "candidate.png"

                con.execute(
                    "UPDATE generation_jobs SET status = 'running', updated_at = ? WHERE job_id = ?",
                    (now_iso, job_id),
                )
                con.execute(
                    """
                    INSERT INTO generation_attempts (
                        attempt_id, job_id, ordinal, status, started_at, runner_id, staging_path
                    ) VALUES (?, ?, 1, 'running', ?, ?, ?)
                    """,
                    (attempt_id, job_id, now_iso, runner_id, str(candidate_path)),
                )
                auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
                new_rev = auth_row[0] + 1
                con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
                con.execute("COMMIT;")
                return {
                    "job_id": job_id,
                    "cut_id": cut_id,
                    "target_desired_revision": target_rev,
                    "attempt_id": attempt_id,
                    "prompt": prompt,
                    "staging_path": str(candidate_path),
                }
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def attach_attempt_process(
        self,
        job_id: str,
        attempt_id: str,
        runner_id: str,
        pid: int,
        pgid: int,
        start_token: str,
        captured_stop_epoch: int,
    ) -> bool:
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            ctrl_row = con.execute("SELECT stop_epoch FROM generation_control WHERE singleton_id = 1").fetchone()
            if not ctrl_row or ctrl_row["stop_epoch"] != captured_stop_epoch:
                con.execute("ROLLBACK;")
                return False

            att = con.execute(
                "SELECT status, runner_id FROM generation_attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
            if not att or att["status"] != "running" or att["runner_id"] != runner_id:
                con.execute("ROLLBACK;")
                return False

            con.execute(
                "UPDATE generation_attempts SET process_pid = ?, process_group_id = ?, process_start_token = ? WHERE attempt_id = ?",
                (pid, pgid, start_token, attempt_id),
            )
            con.execute("COMMIT;")
            return True
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def commit_candidate(
        self,
        runner_id: str,
        job_id: str,
        attempt_id: str,
        candidate_png_path: Path,
        content_hash: str,
        provider_request_id: str | None = None,
    ) -> dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        created_canonical: Path | None = None
        try:
            con.execute("BEGIN IMMEDIATE;")
            job = con.execute("SELECT cut_id, target_desired_revision, status FROM generation_jobs WHERE job_id = ?", (job_id,)).fetchone()
            att = con.execute("SELECT status, runner_id FROM generation_attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()

            if not job or not att or job["status"] != "running" or att["status"] != "running" or att["runner_id"] != runner_id:
                con.execute("ROLLBACK;")
                candidate_png_path.unlink(missing_ok=True)
                return {"status": "discarded", "job_status": job["status"] if job else "unknown"}

            cut_id = job["cut_id"]
            target_rev = job["target_desired_revision"]
            cut_row = con.execute("SELECT desired_revision FROM cuts WHERE cut_id = ?", (cut_id,)).fetchone()
            cur_desired = cut_row["desired_revision"] if cut_row else None

            if cur_desired != target_rev:
                # Target revision is stale: attempt succeeded, job superseded, cut unchanged
                con.execute(
                    "UPDATE generation_attempts SET status = 'succeeded', finished_at = ?, provider_request_id = ?, detail = 'Process succeeded but target revision superseded' WHERE attempt_id = ?",
                    (now_iso, provider_request_id, attempt_id),
                )
                con.execute(
                    "UPDATE generation_jobs SET status = 'superseded', terminal_detail = ?, updated_at = ? WHERE job_id = ?",
                    (f"Target revision {target_rev} superseded by current desired revision {cur_desired}", now_iso, job_id),
                )
                auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
                new_rev = auth_row[0] + 1
                con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
                con.execute("COMMIT;")
                candidate_png_path.unlink(missing_ok=True)
                return {"status": "superseded"}

            # Target revision matches current desired: promote candidate to canonical asset
            canonical_rel = f"assets/realizations/cut-{cut_id}/rev-{target_rev}-{job_id}.png"
            canonical_abs = (self.db_path.parent / canonical_rel).resolve()
            canonical_abs.parent.mkdir(parents=True, exist_ok=True)
            asset_id = f"asset-cut-{cut_id}-rev-{target_rev}-{job_id}"

            os.replace(candidate_png_path, canonical_abs)
            created_canonical = canonical_abs

            con.execute(
                "UPDATE cuts SET realized_revision = ?, realized_asset_id = ?, realized_asset_path = ?, realized_content_hash = ? WHERE cut_id = ?",
                (target_rev, asset_id, str(canonical_abs), content_hash, cut_id),
            )
            con.execute(
                "UPDATE generation_attempts SET status = 'succeeded', finished_at = ?, provider_request_id = ?, detail = 'Realization committed' WHERE attempt_id = ?",
                (now_iso, provider_request_id, attempt_id),
            )
            con.execute(
                "UPDATE generation_jobs SET status = 'succeeded', terminal_detail = 'Realization committed', updated_at = ? WHERE job_id = ?",
                (now_iso, job_id),
            )
            auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
            new_rev = auth_row[0] + 1
            self._revoke_active_authorization(con, new_rev, now_iso)
            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
            con.execute("COMMIT;")
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            if created_canonical is not None:
                created_canonical.unlink(missing_ok=True)
            raise
        finally:
            con.close()

        # Step 7: Fresh connection readback to ensure committed receipt
        with self._connect() as con2:
            check_cut = con2.execute("SELECT realized_revision, realized_asset_path, realized_content_hash FROM cuts WHERE cut_id = ?", (cut_id,)).fetchone()
            check_job = con2.execute("SELECT status FROM generation_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not check_cut or check_cut["realized_revision"] != target_rev or check_job["status"] != "succeeded":
                raise StoreCorruptionError(f"Post-commit readback failed for cut {cut_id} job {job_id}")
            if not canonical_abs.is_file():
                raise StoreCorruptionError(f"Canonical file missing after commit: {canonical_abs}")

        return {
            "status": "committed",
            "asset_id": asset_id,
            "canonical_path": str(canonical_abs),
            "content_hash": content_hash,
        }

    def fail_job_and_attempt(
        self,
        runner_id: str,
        job_id: str,
        attempt_id: str,
        detail: str,
        provider_request_id: str | None = None,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            job = con.execute("SELECT status FROM generation_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not job or job["status"] != "running":
                con.execute("ROLLBACK;")
                return

            con.execute(
                "UPDATE generation_attempts SET status = 'failed', finished_at = ?, detail = ?, provider_request_id = ? WHERE attempt_id = ? AND status = 'running'",
                (now_iso, detail, provider_request_id, attempt_id),
            )
            con.execute(
                "UPDATE generation_jobs SET status = 'failed', terminal_detail = ?, updated_at = ? WHERE job_id = ? AND status = 'running'",
                (detail, now_iso, job_id),
            )
            auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
            new_rev = auth_row[0] + 1
            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
            con.execute("COMMIT;")
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()
    def cancel_job_in_store(self, job_id: str) -> tuple[str, dict[str, Any] | None]:
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            job = con.execute("SELECT status FROM generation_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not job:
                raise ValidationError(f"Job {job_id} not found")

            status = job["status"]
            if status == "queued":
                con.execute(
                    "UPDATE generation_jobs SET status = 'cancelled', terminal_detail = 'Cancelled by user', updated_at = ? WHERE job_id = ?",
                    (now_iso, job_id),
                )
                auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
                new_rev = auth_row[0] + 1
                con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
                con.execute("COMMIT;")
                return ("cancelled_queued", None)

            if status == "running":
                att = con.execute(
                    "SELECT attempt_id, process_pid, process_group_id, process_start_token, staging_path FROM generation_attempts WHERE job_id = ? AND status = 'running'",
                    (job_id,),
                ).fetchone()
                att_dict = dict(att) if att else None
                con.execute("COMMIT;")
                return ("running", att_dict)

            con.execute("COMMIT;")
            return (status, None)
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def mark_job_and_attempt_cancelled(self, job_id: str, attempt_id: str | None, detail: str = "Cancelled by user") -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            if attempt_id:
                con.execute(
                    "UPDATE generation_attempts SET status = 'cancelled', finished_at = ?, detail = ? WHERE attempt_id = ?",
                    (now_iso, detail, attempt_id),
                )
            con.execute(
                "UPDATE generation_jobs SET status = 'cancelled', terminal_detail = ?, updated_at = ? WHERE job_id = ?",
                (detail, now_iso, job_id),
            )
            auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
            new_rev = auth_row[0] + 1
            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
            con.execute("COMMIT;")
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def stop_all_and_cancel_queued(self) -> tuple[int, list[dict[str, Any]]]:
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            con.execute("UPDATE generation_control SET stop_epoch = stop_epoch + 1 WHERE singleton_id = 1")
            epoch_row = con.execute("SELECT stop_epoch FROM generation_control WHERE singleton_id = 1").fetchone()
            new_epoch = epoch_row["stop_epoch"]

            con.execute(
                "UPDATE generation_jobs SET status = 'cancelled', terminal_detail = 'global_stop', updated_at = ? WHERE status = 'queued'",
                (now_iso,),
            )
            running_rows = con.execute(
                """
                SELECT a.attempt_id, a.job_id, a.process_pid, a.process_group_id, a.process_start_token, a.staging_path
                FROM generation_attempts a
                JOIN generation_jobs j ON a.job_id = j.job_id
                WHERE a.status = 'running'
                """
            ).fetchall()

            auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
            new_rev = auth_row[0] + 1
            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
            con.execute("COMMIT;")
            return (new_epoch, [dict(r) for r in running_rows])
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def mark_attempts_and_jobs_interrupted(self, running_items: list[tuple[str, str]], reason: str = "global_stop") -> None:
        if not running_items:
            return
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE;")
            for job_id, attempt_id in running_items:
                con.execute(
                    "UPDATE generation_attempts SET status = 'interrupted', finished_at = ?, detail = ? WHERE attempt_id = ? AND status = 'running'",
                    (now_iso, reason, attempt_id),
                )
                con.execute(
                    "UPDATE generation_jobs SET status = 'interrupted', terminal_detail = ?, updated_at = ? WHERE job_id = ? AND status = 'running'",
                    (reason, now_iso, job_id),
                )
            auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
            new_rev = auth_row[0] + 1
            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
            con.execute("COMMIT;")
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()
    def register_review_artifact(
        self,
        expected_authority_revision: int,
        artifact_id: str,
        content_hash: str,
        composition_revision: int,
        cut_closure: list[dict[str, Any]],
    ) -> int:
        if not artifact_id or not content_hash:
            raise ValidationError("artifact_id and content_hash must be non-empty strings")
        if len(cut_closure) != 5:
            raise ValidationError(f"cut_closure must have exactly 5 elements, got {len(cut_closure)}")
        now_iso = datetime.now(timezone.utc).isoformat()

        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            comp_row = con.execute("SELECT revision FROM composition WHERE singleton_id = 1").fetchone()
            if not comp_row:
                raise StoreCorruptionError("Missing composition singleton")
            if comp_row["revision"] != composition_revision:
                raise ValidationError(
                    f"Composition revision mismatch: expected {comp_row['revision']}, got {composition_revision}"
                )

            cuts_rows = con.execute(
                "SELECT cut_id, desired_revision, realized_revision, realized_asset_id FROM cuts ORDER BY cut_id ASC"
            ).fetchall()
            for r in cuts_rows:
                cid = r["cut_id"]
                d_rev = r["desired_revision"]
                r_rev = r["realized_revision"]
                if d_rev is None or r_rev != d_rev:
                    raise RealizationIncompleteError(
                        f"Cut {cid} is not current (desired={d_rev}, realized={r_rev})"
                    )

            closure_map = {item["cut_id"]: item for item in cut_closure}
            for r in cuts_rows:
                cid = r["cut_id"]
                if cid not in closure_map:
                    raise ValidationError(f"Missing cut {cid} in closure")
                c_item = closure_map[cid]
                if (
                    c_item.get("realized_revision") != r["realized_revision"]
                    or c_item.get("asset_id") != r["realized_asset_id"]
                ):
                    raise ValidationError(
                        f"Cut {cid} closure mismatch: closure has rev={c_item.get('realized_revision')}, asset={c_item.get('asset_id')}; actual has rev={r['realized_revision']}, asset={r['realized_asset_id']}"
                    )

            con.execute(
                "INSERT INTO review_artifacts (artifact_id, content_hash, composition_revision, created_at) VALUES (?, ?, ?, ?)",
                (artifact_id, content_hash, composition_revision, now_iso),
            )
            for item in cut_closure:
                con.execute(
                    "INSERT INTO artifact_cuts (artifact_id, cut_id, realized_revision, asset_id) VALUES (?, ?, ?, ?)",
                    (artifact_id, item["cut_id"], item["realized_revision"], item["asset_id"]),
                )

            con.execute(
                "UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,)
            )
            con.execute("COMMIT;")
            return new_rev
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def authorize_release(
        self,
        expected_authority_revision: int,
        authorization_id: str,
        artifact_id: str,
        content_hash: str,
    ) -> int:
        if not authorization_id or not artifact_id or not content_hash:
            raise ValidationError("authorization_id, artifact_id, and content_hash must be non-empty strings")
        now_iso = datetime.now(timezone.utc).isoformat()

        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            art = con.execute(
                "SELECT artifact_id, content_hash, composition_revision FROM review_artifacts WHERE artifact_id = ?",
                (artifact_id,),
            ).fetchone()
            if not art:
                raise ValidationError(f"Review artifact {artifact_id} not found")
            if art["content_hash"] != content_hash:
                raise ValidationError(
                    f"Artifact content hash mismatch: expected {art['content_hash']}, got {content_hash}"
                )

            comp_row = con.execute("SELECT revision FROM composition WHERE singleton_id = 1").fetchone()
            if not comp_row or comp_row["revision"] != art["composition_revision"]:
                cur_comp = comp_row["revision"] if comp_row else None
                raise InvalidArtifactClosureError(
                    f"Composition has changed (current {cur_comp} != artifact {art['composition_revision']})"
                )

            art_cuts = con.execute(
                "SELECT cut_id, realized_revision, asset_id FROM artifact_cuts WHERE artifact_id = ? ORDER BY cut_id ASC",
                (artifact_id,),
            ).fetchall()
            art_closure = {
                ac["cut_id"]: (ac["realized_revision"], ac["asset_id"]) for ac in art_cuts
            }

            cuts_rows = con.execute(
                "SELECT cut_id, desired_revision, realized_revision, realized_asset_id FROM cuts ORDER BY cut_id ASC"
            ).fetchall()
            for cr in cuts_rows:
                cid = cr["cut_id"]
                if cr["desired_revision"] is None or cr["realized_revision"] != cr["desired_revision"]:
                    raise RealizationIncompleteError(f"Cut {cid} is not current")
                if cid not in art_closure or art_closure[cid] != (
                    cr["realized_revision"],
                    cr["realized_asset_id"],
                ):
                    raise InvalidArtifactClosureError(
                        f"Cut {cid} realization does not match artifact closure"
                    )

            self._revoke_active_authorization(con, new_rev, now_iso)
            con.execute(
                "INSERT INTO release_authorizations (authorization_id, artifact_id, artifact_content_hash, authorized_authority_revision, revoked_authority_revision, created_at, revoked_at) VALUES (?, ?, ?, ?, NULL, ?, NULL)",
                (authorization_id, artifact_id, content_hash, new_rev, now_iso),
            )
            con.execute(
                "UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,)
            )
            con.execute("COMMIT;")
            return new_rev
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def start_delivery_attempt(
        self,
        expected_authority_revision: int,
        attempt_id: str,
        kind: str,
        authorization_id: str,
        request_id: str,
    ) -> int:
        if kind not in ("png", "blogger"):
            raise ValidationError(f"Invalid delivery kind: {kind}; must be 'png' or 'blogger'")
        if not attempt_id or not authorization_id or not request_id:
            raise ValidationError("attempt_id, authorization_id, and request_id must be non-empty strings")
        now_iso = datetime.now(timezone.utc).isoformat()

        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            auth = con.execute(
                "SELECT authorization_id, artifact_id, revoked_authority_revision FROM release_authorizations WHERE authorization_id = ?",
                (authorization_id,),
            ).fetchone()
            if not auth:
                raise ValidationError(f"Authorization {authorization_id} not found")
            if auth["revoked_authority_revision"] is not None:
                raise AuthorizationRevokedError(f"Authorization {authorization_id} has been revoked")

            art_id = auth["artifact_id"]
            art_cuts = con.execute(
                "SELECT cut_id, realized_revision, asset_id FROM artifact_cuts WHERE artifact_id = ? ORDER BY cut_id ASC",
                (art_id,),
            ).fetchall()
            art_closure = {
                ac["cut_id"]: (ac["realized_revision"], ac["asset_id"]) for ac in art_cuts
            }

            cuts_rows = con.execute(
                "SELECT cut_id, desired_revision, realized_revision, realized_asset_id FROM cuts ORDER BY cut_id ASC"
            ).fetchall()
            for cr in cuts_rows:
                cid = cr["cut_id"]
                if cr["desired_revision"] is None or cr["realized_revision"] != cr["desired_revision"]:
                    raise RealizationIncompleteError(f"Cut {cid} is not current")
                if cid not in art_closure or art_closure[cid] != (
                    cr["realized_revision"],
                    cr["realized_asset_id"],
                ):
                    raise InvalidArtifactClosureError(
                        f"Cut {cid} realization does not match artifact closure"
                    )

            con.execute(
                "INSERT INTO delivery_attempts (attempt_id, kind, authorization_id, artifact_id, request_id, outcome, destination_id, destination_url, evidence_json, observed_authority_revision, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'unknown', NULL, NULL, NULL, NULL, ?, ?)",
                (attempt_id, kind, authorization_id, art_id, request_id, now_iso, now_iso),
            )
            con.execute(
                "UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,)
            )
            con.execute("COMMIT;")
            return new_rev
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def record_delivery_observation(
        self,
        expected_authority_revision: int,
        attempt_id: str,
        outcome: str,
        evidence: dict[str, Any] | str | None = None,
        destination_id: str | None = None,
        destination_url: str | None = None,
    ) -> int:
        if outcome not in ("unknown", "confirmed_success", "confirmed_failure"):
            raise ValidationError(f"Invalid delivery outcome: {outcome}")
        if outcome == "confirmed_success":
            if not destination_id or not destination_url or evidence is None:
                raise ValidationError("confirmed_success requires destination_id, destination_url, and evidence")

        evidence_json = (
            json.dumps(evidence, sort_keys=True)
            if isinstance(evidence, dict)
            else (str(evidence) if evidence is not None else None)
        )
        now_iso = datetime.now(timezone.utc).isoformat()

        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            att = con.execute(
                "SELECT attempt_id FROM delivery_attempts WHERE attempt_id = ?", (attempt_id,)
            ).fetchone()
            if not att:
                raise ValidationError(f"Delivery attempt {attempt_id} not found")

            con.execute(
                "UPDATE delivery_attempts SET outcome = ?, destination_id = ?, destination_url = ?, evidence_json = ?, observed_authority_revision = ?, updated_at = ? WHERE attempt_id = ?",
                (outcome, destination_id, destination_url, evidence_json, new_rev, now_iso, attempt_id),
            )
            con.execute(
                "UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,)
            )
            con.execute("COMMIT;")
            return new_rev
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()
