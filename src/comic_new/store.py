"""comic-new transactional store: single durable SQLite authority."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


DEFAULT_GENERATION_MODEL = "oauth/gpt-image-2.5-flare"
PROMPT_ORIGINS = frozenset(("user", "llm_draft", "intelligent_default"))


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

class BaselineRequiredError(TransactionalStoreError):
    """Raised when an operation requires an active structural baseline but none exists."""

class TransactionalStore:
    """Concrete single SQLite transactional authority for comic_new."""

    APPLICATION_ID: int = 0x434F4D43  # 'COMC'
    SCHEMA_VERSION: int = 7
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
        "trg_cuts_no_delete",
        "trg_cuts_no_update_cut_id",
        "trg_cuts_keep_one_active",
        "trg_cut_intents_active_baseline",
    })
    REQUIRED_INDEXES: frozenset[str] = frozenset({
        "idx_active_release_authorization",
        "idx_generation_jobs_queued",
        "idx_active_cut_display_order",
    })

    @staticmethod
    def _validate_cut_id(cut_id: Any) -> int:
        if isinstance(cut_id, bool) or not isinstance(cut_id, int) or cut_id < 1:
            raise ValidationError(f"Invalid cut_id {cut_id!r}; must be a positive integer")
        return cut_id

    @staticmethod
    def _active_cuts(con: sqlite3.Connection, *, require_nonempty: bool = True) -> list[sqlite3.Row]:
        rows = con.execute(
            "SELECT cut_id, is_active, display_order, desired_revision, latest_generation_request_seq, "
            "realized_revision, realized_asset_id, realized_asset_path, realized_content_hash "
            "FROM cuts WHERE is_active = 1 ORDER BY display_order ASC"
        ).fetchall()
        ids = [row["cut_id"] for row in rows]
        orders = [row["display_order"] for row in rows]
        if require_nonempty and not rows:
            raise StoreCorruptionError("Active cut set must not be empty")
        if len(set(ids)) != len(ids) or any(not isinstance(cid, int) or cid < 1 for cid in ids):
            raise StoreCorruptionError(f"Active cut IDs must be unique positive integers, found {ids}")
        if orders != list(range(1, len(rows) + 1)):
            raise StoreCorruptionError(f"Active cut display_order must be contiguous from 1, found {orders}")
        return rows

    @staticmethod
    def _active_cut_ids(con: sqlite3.Connection) -> list[int]:
        return [row["cut_id"] for row in TransactionalStore._active_cuts(con)]

    @staticmethod
    def _ordered_ids(value: Any, *, field_name: str) -> list[int]:
        if not isinstance(value, list) or not value:
            raise ValidationError(f"{field_name} must be a non-empty list")
        ids = [TransactionalStore._validate_cut_id(item) for item in value]
        if len(set(ids)) != len(ids):
            raise ValidationError(f"{field_name} must contain unique cut IDs")
        return ids

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(
            str(self.db_path),
            timeout=self.BUSY_TIMEOUT_MS / 1000.0,
            isolation_level=None,  # Explicit manual transaction control
        )
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        con.execute(f"PRAGMA busy_timeout = {self.BUSY_TIMEOUT_MS};")
        return con
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()

    @property
    def project_dir(self) -> Path:
        return self.db_path.parent

    @staticmethod
    def _require_active_baseline(con: sqlite3.Connection) -> str:
        row = con.execute(
            "SELECT current_baseline_id FROM authority WHERE singleton_id = 1"
        ).fetchone()
        cur_base_id = row["current_baseline_id"] if row else None
        if not cur_base_id:
            raise BaselineRequiredError("Operation requires an active structural baseline")
        return cur_base_id

    @staticmethod
    def _parse_structured_intent(intent_payload: Any) -> dict[str, str]:
        """Parse the structural shape without imposing generation eligibility."""
        if not isinstance(intent_payload, dict):
            raise ValidationError("Intent payload must be a JSON object with 'prompt' and 'dialogue'")
        prompt = intent_payload.get("prompt")
        dialogue = intent_payload.get("dialogue")
        if prompt is None or not isinstance(prompt, str):
            raise ValidationError("Intent prompt must be a string")
        if dialogue is None or not isinstance(dialogue, str):
            raise ValidationError("Intent dialogue must be a string")
        parsed = {"prompt": prompt, "dialogue": dialogue}
        if "prompt_origin" in intent_payload:
            origin = intent_payload["prompt_origin"]
            if not isinstance(origin, str) or origin not in PROMPT_ORIGINS:
                raise ValidationError(
                    "Intent prompt_origin must be one of user, llm_draft, intelligent_default"
                )
            parsed["prompt_origin"] = origin
        return parsed

    @classmethod
    def _resolve_baseline_intent(
        cls,
        intent_payload: Any,
        structure: Any,
        cut_id: int,
    ) -> dict[str, str]:
        parsed = cls._parse_structured_intent(intent_payload)
        prompt = parsed["prompt"]
        if prompt.strip():
            return {
                "prompt": prompt,
                "dialogue": parsed["dialogue"],
                "prompt_origin": parsed.get("prompt_origin", "user"),
            }

        if not isinstance(structure, dict):
            raise ValidationError("Baseline structure must be a JSON object to resolve an empty prompt")
        source_brief = structure.get("source_brief")
        cuts = structure.get("cuts")
        if not isinstance(source_brief, str) or not isinstance(cuts, list):
            raise ValidationError(
                "Baseline structure must include source_brief and ordered cuts to resolve an empty prompt"
            )
        if not cuts or any(not isinstance(cut, dict) for cut in cuts):
            raise ValidationError("Baseline structure cuts must be a non-empty list")
        ids = [cls._validate_cut_id(cut.get("cut_id")) for cut in cuts]
        if len(set(ids)) != len(ids):
            raise ValidationError("Baseline structure cuts must contain unique positive cut IDs")
        by_id = {cut.get("cut_id"): cut for cut in cuts}
        cut = by_id.get(cut_id)
        if not isinstance(cut, dict):
            raise ValidationError(f"Baseline structure is missing cut {cut_id}")
        role = cut.get("role")
        beat = cut.get("beat")
        if not isinstance(role, str) or not isinstance(beat, str):
            raise ValidationError(f"Baseline cut {cut_id} role and beat must be strings")
        effective_prompt = f"{source_brief.strip()} - 컷 {cut_id} ({role.strip()}: {beat.strip()})".strip()
        if not effective_prompt:
            raise ValidationError(f"Cut {cut_id} could not resolve a non-empty effective prompt")
        return {
            "prompt": effective_prompt,
            "dialogue": parsed["dialogue"],
            "prompt_origin": "intelligent_default",
        }

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
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
    def create_project(cls, project_dir: str | Path, cut_count: int = 5) -> TransactionalStore:
        if isinstance(cut_count, bool) or not isinstance(cut_count, int) or cut_count < 1:
            raise ValidationError("cut_count must be a positive integer")
        p = Path(project_dir).resolve()
        if p.exists() and not p.is_dir():
            raise ValidationError(f"Target path {p} exists and is not a directory")
        p.mkdir(parents=True, exist_ok=True)
        db_path = p / cls.DB_FILENAME

        if db_path.exists():
            if db_path.stat().st_size == 0:
                db_path.unlink()
            else:
                try:
                    cls(db_path).verify_schema()
                    raise ProjectAlreadyExistsError(f"Project already initialized at {p}")
                except ProjectAlreadyExistsError:
                    raise
                except Exception as e:
                    raise StoreCorruptionError(f"Unrecognized or partially initialized database at {db_path}: {e}") from e

        schema_sql_path = Path(__file__).parent / "schema.sql"
        if not schema_sql_path.is_file():
            raise StoreCorruptionError(f"Missing schema definition at {schema_sql_path}")
        sql_text = schema_sql_path.read_text(encoding="utf-8")
        tmp_db_path = p / f".{cls.DB_FILENAME}.tmp.{uuid4().hex}"
        con = sqlite3.connect(str(tmp_db_path), timeout=cls.BUSY_TIMEOUT_MS / 1000.0)
        try:
            con.execute("PRAGMA foreign_keys = ON;")
            cut_rows_sql = "\n".join(
                f"INSERT INTO cuts (cut_id, is_active, display_order) VALUES ({cut_id}, 1, {cut_id});"
                for cut_id in range(1, cut_count + 1)
            )
            init_script = (
                "BEGIN IMMEDIATE;\n"
                f"PRAGMA application_id = {cls.APPLICATION_ID};\n"
                f"PRAGMA user_version = {cls.SCHEMA_VERSION};\n"
                f"{sql_text}\n"
                f"{cut_rows_sql}\n"
                "COMMIT;\n"
            )
            con.executescript(init_script)
            con.close()
            cls(tmp_db_path).verify_schema()
            os.replace(tmp_db_path, db_path)
        except Exception as e:
            try:
                if con.in_transaction:
                    con.execute("ROLLBACK;")
            except Exception:
                pass
            try:
                con.close()
            except Exception:
                pass
            tmp_db_path.unlink(missing_ok=True)
            if isinstance(e, (ValidationError, StoreCorruptionError, ProjectAlreadyExistsError)):
                raise
            raise StoreCorruptionError(f"Database initialization failed: {e}") from e

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
                v1_required_triggers = {"trg_cuts_no_insert", "trg_cuts_no_delete", "trg_cuts_no_update_cut_id"}
                missing_triggers = v1_required_triggers - existing_triggers
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
                user_ver = 2

            if user_ver == 2:
                mig_path_v3 = Path(__file__).parent / "migrations" / "v2_to_v3.sql"
                if not mig_path_v3.is_file():
                    raise StoreCorruptionError(f"Missing migration script at {mig_path_v3}")
                mig_sql_v3 = mig_path_v3.read_text(encoding="utf-8")
                statements_v3 = [s.strip() for s in mig_sql_v3.split(";") if s.strip()]
                try:
                    con.execute("BEGIN IMMEDIATE;")
                    for stmt in statements_v3:
                        con.execute(stmt)
                    con.execute("COMMIT;")
                except Exception as e:
                    if con.in_transaction:
                        con.execute("ROLLBACK;")
                    raise StoreCorruptionError(f"Migration from v2 to v3 failed: {e}") from e
                user_ver = 3

            if user_ver == 3:
                mig_path_v4 = Path(__file__).parent / "migrations" / "v3_to_v4.sql"
                if not mig_path_v4.is_file():
                    raise StoreCorruptionError(f"Missing migration script at {mig_path_v4}")
                mig_sql_v4 = mig_path_v4.read_text(encoding="utf-8")
                statements_v4 = [s.strip() for s in mig_sql_v4.split(";") if s.strip()]
                try:
                    con.execute("BEGIN IMMEDIATE;")
                    # Preserve attributable history from older baselines. Only the five
                    # current desired intents must belong to the active baseline.
                    cur_base = con.execute(
                        "SELECT current_baseline_id FROM authority WHERE singleton_id = 1"
                    ).fetchone()
                    cur_base_id = cur_base["current_baseline_id"] if cur_base else None
                    intent_cnt = con.execute("SELECT COUNT(*) AS cnt FROM cut_intents").fetchone()["cnt"]
                    if intent_cnt > 0 and cur_base_id is None:
                        raise StoreCorruptionError(
                            "Migration from v3 to v4 failed: legacy intent rows exist without an active baseline"
                        )
                    unattributable_count = con.execute(
                        """
                        SELECT COUNT(*) AS cnt
                        FROM cut_intents AS i
                        LEFT JOIN structural_baselines AS b ON b.baseline_id = i.baseline_id
                        WHERE i.baseline_id IS NULL OR b.baseline_id IS NULL
                        """
                    ).fetchone()["cnt"]
                    if unattributable_count > 0:
                        raise StoreCorruptionError(
                            "Migration from v3 to v4 failed: legacy intent rows have no attributable baseline"
                        )

                    # Synchronize composition only after proving that every current cut
                    # resolves to one intent on the active baseline.
                    if cur_base_id is not None:
                        from comic_new.composition import canonical_json_dumps

                        intent_rows = con.execute(
                            """
                            SELECT c.cut_id, i.payload_json
                            FROM cuts AS c
                            JOIN cut_intents AS i
                              ON c.cut_id = i.cut_id AND c.desired_revision = i.revision
                            WHERE i.baseline_id = ?
                            ORDER BY c.cut_id
                            """,
                            (cur_base_id,),
                        ).fetchall()
                        if [row["cut_id"] for row in intent_rows] != [1, 2, 3, 4, 5]:
                            raise StoreCorruptionError(
                                "Migration from v3 to v4 failed: current intents are not fully bound to the active baseline"
                            )
                        dialogue_by_cut: dict[int, str] = {}
                        for row in intent_rows:
                            payload = self._parse_structured_intent(json.loads(row["payload_json"]))
                            dialogue_by_cut[row["cut_id"]] = payload["dialogue"]

                        comp_row = con.execute("SELECT revision, state_json FROM composition WHERE singleton_id = 1").fetchone()
                        if comp_row and comp_row["state_json"]:
                            comp_state = json.loads(comp_row["state_json"])
                            bubbles = comp_state.get("bubbles", [])
                            changed = False
                            for b in bubbles:
                                cid = b.get("cut_id")
                                if cid in dialogue_by_cut:
                                    target_d = dialogue_by_cut[cid]
                                    if b.get("text") != target_d:
                                        b["text"] = target_d
                                        changed = True
                            if changed:
                                new_comp_rev = comp_row["revision"] + 1
                                auth_rev = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()["authority_revision"]
                                new_auth_rev = auth_rev + 1
                                now_iso = datetime.now(timezone.utc).isoformat()
                                new_state_json = canonical_json_dumps(comp_state)
                                con.execute(
                                    "UPDATE composition SET revision = ?, state_json = ?, updated_at = ? WHERE singleton_id = 1",
                                    (new_comp_rev, new_state_json, now_iso),
                                )
                                con.execute(
                                    "UPDATE authority SET authority_revision = ? WHERE singleton_id = 1",
                                    (new_auth_rev,),
                                )
                                self._revoke_active_authorization(con, new_auth_rev, now_iso)
                    con.execute(
                        """
                        CREATE TRIGGER trg_cut_intents_active_baseline
                        BEFORE INSERT ON cut_intents
                        FOR EACH ROW
                        BEGIN
                            SELECT CASE
                                WHEN NEW.baseline_id IS NULL
                                  OR (SELECT current_baseline_id FROM authority WHERE singleton_id = 1) IS NULL
                                  OR NEW.baseline_id != (SELECT current_baseline_id FROM authority WHERE singleton_id = 1)
                                THEN RAISE(ABORT, 'cut_intents insert requires active baseline')
                            END;
                        END;
                        """
                    )
                    con.execute("PRAGMA user_version = 4;")
                    con.execute("COMMIT;")
                except Exception as e:
                    if con.in_transaction:
                        con.execute("ROLLBACK;")
                    if isinstance(e, StoreCorruptionError):
                        raise
                    raise StoreCorruptionError(f"Migration from v3 to v4 failed: {e}") from e
                user_ver = 4

            if user_ver == 4:
                mig_path_v5 = Path(__file__).parent / "migrations" / "v4_to_v5.sql"
                if not mig_path_v5.is_file():
                    raise StoreCorruptionError(f"Missing migration script at {mig_path_v5}")
                mig_sql_v5 = mig_path_v5.read_text(encoding="utf-8")
                statements_v5 = [stmt.strip() for stmt in mig_sql_v5.split(";") if stmt.strip()]
                if not statements_v5:
                    raise StoreCorruptionError(f"Migration script at {mig_path_v5} is empty")
                try:
                    con.execute("BEGIN IMMEDIATE;")
                    for stmt in statements_v5:
                        con.execute(stmt)
                    self._migrate_v4_to_v5(con)
                    con.execute("PRAGMA user_version = 5;")
                    con.execute("COMMIT;")
                except Exception as e:
                    if con.in_transaction:
                        con.execute("ROLLBACK;")
                    if isinstance(e, StoreCorruptionError):
                        raise
                    raise StoreCorruptionError(f"Migration from v4 to v5 failed: {e}") from e
                user_ver = 5

            if user_ver == 5:
                mig_path_v6 = Path(__file__).parent / "migrations" / "v5_to_v6.sql"
                if not mig_path_v6.is_file():
                    raise StoreCorruptionError(f"Missing migration script at {mig_path_v6}")
                statements_v6 = [stmt.strip() for stmt in mig_path_v6.read_text(encoding="utf-8").split(";") if stmt.strip()]
                if not statements_v6:
                    raise StoreCorruptionError(f"Migration script at {mig_path_v6} is empty")
                try:
                    con.execute("BEGIN IMMEDIATE;")
                    for stmt in statements_v6:
                        con.execute(stmt)
                    self._migrate_v5_to_v6(con)
                    con.execute("PRAGMA user_version = 6;")
                    con.execute("COMMIT;")
                except Exception as e:
                    if con.in_transaction:
                        con.execute("ROLLBACK;")
                    if isinstance(e, StoreCorruptionError):
                        raise
                    raise StoreCorruptionError(f"Migration from v5 to v6 failed: {e}") from e
                user_ver = 6
            if user_ver == 6:
                mig_path_v7 = Path(__file__).parent / "migrations" / "v6_to_v7.sql"
                if not mig_path_v7.is_file():
                    raise StoreCorruptionError(f"Missing migration script at {mig_path_v7}")
                statements_v7 = [stmt.strip() for stmt in mig_path_v7.read_text(encoding="utf-8").split(";") if stmt.strip()]
                if not statements_v7:
                    raise StoreCorruptionError(f"Migration script at {mig_path_v7} is empty")
                try:
                    con.execute("PRAGMA foreign_keys = OFF;")
                    con.execute("BEGIN IMMEDIATE;")
                    for stmt in statements_v7:
                        con.execute(stmt)
                    self._migrate_v6_to_v7(con)
                    con.execute("PRAGMA user_version = 7;")
                    con.execute("COMMIT;")
                except Exception as e:
                    if con.in_transaction:
                        con.execute("ROLLBACK;")
                    if isinstance(e, StoreCorruptionError):
                        raise
                    raise StoreCorruptionError(f"Migration from v6 to v7 failed: {e}") from e
                finally:
                    con.execute("PRAGMA foreign_keys = ON;")
                user_ver = 7

            if user_ver != 7:
                raise StoreCorruptionError(f"Unrecognized schema version: {user_ver}")


    def _migrate_v6_to_v7(self, con: sqlite3.Connection) -> None:
        """Rebuild fixed-range v6 tables into the dynamic active-set v7 schema."""
        old_names = (
            "authority", "structural_baselines", "cut_intents", "cuts", "baseline_intents",
            "generation_jobs", "generation_attempts", "artifact_cuts",
        )
        # Drop objects whose names would otherwise conflict with the v7 guards.
        for trigger in (
            "trg_cuts_no_insert", "trg_cuts_no_delete", "trg_cuts_no_update_cut_id",
            "trg_cuts_keep_one_active", "trg_cut_intents_active_baseline",
        ):
            con.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        con.execute("DROP INDEX IF EXISTS idx_generation_jobs_queued")
        con.execute("DROP INDEX IF EXISTS idx_active_cut_display_order")
        con.execute("DROP INDEX IF EXISTS idx_active_release_authorization")

        for name in old_names:
            con.execute(f"ALTER TABLE {name} RENAME TO {name}_v6")

        v7_schema = """
            CREATE TABLE structural_baselines (
                baseline_id TEXT PRIMARY KEY,
                structure_json TEXT NOT NULL CHECK (json_valid(structure_json)),
                authority_revision INTEGER NOT NULL CHECK (authority_revision >= 0),
                created_at TEXT NOT NULL
            );
            CREATE TABLE cut_intents (
                cut_id INTEGER NOT NULL CHECK (cut_id >= 1),
                revision INTEGER NOT NULL CHECK (revision > 0),
                baseline_id TEXT NULL REFERENCES structural_baselines(baseline_id),
                payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
                authority_revision INTEGER NOT NULL CHECK (authority_revision >= 0),
                created_at TEXT NOT NULL,
                PRIMARY KEY (cut_id, revision)
            );
            CREATE TABLE cuts (
                cut_id INTEGER PRIMARY KEY CHECK (cut_id >= 1),
                is_active INTEGER NOT NULL CHECK (is_active IN (0, 1)),
                display_order INTEGER NULL CHECK (display_order IS NULL OR display_order >= 1),
                desired_revision INTEGER NULL CHECK (desired_revision IS NULL OR desired_revision > 0),
                latest_generation_request_seq INTEGER NOT NULL DEFAULT 0 CHECK (latest_generation_request_seq >= 0),
                realized_revision INTEGER NULL CHECK (realized_revision IS NULL OR realized_revision > 0),
                realized_asset_id TEXT NULL,
                realized_asset_path TEXT NULL,
                realized_content_hash TEXT NULL,
                CHECK ((is_active = 1 AND display_order IS NOT NULL) OR (is_active = 0 AND display_order IS NULL)),
                CHECK ((realized_revision IS NULL AND realized_asset_id IS NULL AND realized_asset_path IS NULL AND realized_content_hash IS NULL) OR
                      (realized_revision IS NOT NULL AND realized_asset_id IS NOT NULL AND realized_asset_path IS NOT NULL AND realized_content_hash IS NOT NULL)),
                FOREIGN KEY (cut_id, desired_revision) REFERENCES cut_intents(cut_id, revision)
            );
            CREATE TABLE authority (
                singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                authority_revision INTEGER NOT NULL CHECK (authority_revision >= 0),
                current_baseline_id TEXT NULL REFERENCES structural_baselines(baseline_id)
            );
            CREATE TABLE baseline_intents (
                baseline_id TEXT NOT NULL REFERENCES structural_baselines(baseline_id) ON DELETE CASCADE,
                cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id >= 1),
                intent_revision INTEGER NOT NULL CHECK (intent_revision > 0),
                PRIMARY KEY (baseline_id, cut_id),
                FOREIGN KEY (cut_id, intent_revision) REFERENCES cut_intents(cut_id, revision)
            );
            CREATE TABLE generation_jobs (
                job_id TEXT PRIMARY KEY,
                cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id >= 1),
                target_desired_revision INTEGER NOT NULL CHECK (target_desired_revision > 0),
                request_seq INTEGER NOT NULL CHECK (request_seq > 0),
                model TEXT NOT NULL CHECK (length(trim(model)) > 0),
                effective_prompt TEXT NOT NULL CHECK (length(trim(effective_prompt)) > 0),
                effective_prompt_origin TEXT NOT NULL CHECK (effective_prompt_origin IN ('user', 'llm_draft', 'intelligent_default')),
                effective_prompt_sha256 TEXT NOT NULL CHECK (length(effective_prompt_sha256) = 64),
                status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled', 'interrupted', 'superseded')),
                terminal_detail TEXT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE generation_attempts (
                attempt_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL REFERENCES generation_jobs(job_id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL CHECK (ordinal >= 1),
                status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed', 'interrupted', 'cancelled')),
                started_at TEXT NOT NULL,
                finished_at TEXT NULL,
                detail TEXT NULL,
                runner_id TEXT NULL,
                process_pid INTEGER NULL,
                process_group_id INTEGER NULL,
                process_start_token TEXT NULL,
                staging_path TEXT NULL,
                provider_request_id TEXT NULL,
                UNIQUE (job_id, ordinal),
                CHECK ((process_pid IS NULL AND process_group_id IS NULL AND process_start_token IS NULL) OR
                       (process_pid IS NOT NULL AND process_group_id IS NOT NULL AND process_start_token IS NOT NULL))
            );
            CREATE TABLE artifact_cuts (
                artifact_id TEXT NOT NULL REFERENCES review_artifacts(artifact_id) ON DELETE CASCADE,
                cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id >= 1),
                display_order INTEGER NOT NULL CHECK (display_order >= 1),
                realized_revision INTEGER NOT NULL CHECK (realized_revision > 0),
                asset_id TEXT NOT NULL,
                PRIMARY KEY (artifact_id, cut_id),
                UNIQUE (artifact_id, display_order)
            );
        """
        for statement in v7_schema.split(";"):
            statement = statement.strip()
            if statement:
                con.execute(statement)

        old_counts: dict[str, int] = {}
        for name in old_names:
            old_counts[name] = con.execute(f"SELECT COUNT(*) FROM {name}_v6").fetchone()[0]

        con.execute("INSERT INTO structural_baselines SELECT baseline_id, structure_json, authority_revision, created_at FROM structural_baselines_v6")
        con.execute(
            """INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at)
               SELECT cut_id, revision, baseline_id, payload_json, authority_revision, created_at FROM cut_intents_v6"""
        )
        con.execute(
            """INSERT INTO cuts (cut_id, is_active, display_order, desired_revision, latest_generation_request_seq,
                                  realized_revision, realized_asset_id, realized_asset_path, realized_content_hash)
               SELECT cut_id, 1, cut_id, desired_revision, latest_generation_request_seq,
                      realized_revision, realized_asset_id, realized_asset_path, realized_content_hash
               FROM cuts_v6 ORDER BY cut_id"""
        )
        con.execute("INSERT INTO authority SELECT singleton_id, authority_revision, current_baseline_id FROM authority_v6")
        con.execute("INSERT INTO baseline_intents SELECT baseline_id, cut_id, intent_revision FROM baseline_intents_v6")
        con.execute(
            """INSERT INTO generation_jobs (job_id, cut_id, target_desired_revision, request_seq, model,
                                               effective_prompt, effective_prompt_origin, effective_prompt_sha256,
                                               status, terminal_detail, created_at, updated_at)
               SELECT job_id, cut_id, target_desired_revision, request_seq, model,
                      effective_prompt, effective_prompt_origin, effective_prompt_sha256,
                      status, terminal_detail, created_at, updated_at FROM generation_jobs_v6"""
        )
        con.execute(
            """INSERT INTO generation_attempts (attempt_id, job_id, ordinal, status, started_at, finished_at, detail,
                                                  runner_id, process_pid, process_group_id, process_start_token,
                                                  staging_path, provider_request_id)
               SELECT attempt_id, job_id, ordinal, status, started_at, finished_at, detail,
                      runner_id, process_pid, process_group_id, process_start_token,
                      staging_path, provider_request_id FROM generation_attempts_v6"""
        )
        con.execute(
            """INSERT INTO artifact_cuts (artifact_id, cut_id, display_order, realized_revision, asset_id)
               SELECT artifact_id, cut_id, cut_id, realized_revision, asset_id FROM artifact_cuts_v6 ORDER BY artifact_id, cut_id"""
        )

        for name in reversed(old_names):
            con.execute(f"DROP TABLE {name}_v6")

        for name in old_names:
            actual = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            if actual != old_counts[name]:
                raise StoreCorruptionError(f"v6-to-v7 row count mismatch for {name}: {old_counts[name]} -> {actual}")
        active = con.execute("SELECT cut_id, display_order FROM cuts WHERE is_active = 1 ORDER BY display_order").fetchall()
        if not active or [tuple(row) for row in active] != [(row[0], row[0]) for row in con.execute("SELECT cut_id FROM cuts ORDER BY cut_id")]:
            raise StoreCorruptionError("v6-to-v7 active cut order backfill failed")
        con.execute("CREATE INDEX idx_generation_jobs_queued ON generation_jobs (status, created_at, job_id)")
        con.execute("CREATE UNIQUE INDEX idx_active_cut_display_order ON cuts (display_order) WHERE is_active = 1")
        con.execute("CREATE UNIQUE INDEX idx_active_release_authorization ON release_authorizations ((1)) WHERE revoked_authority_revision IS NULL")
        con.execute(
            """CREATE TRIGGER trg_cuts_no_delete BEFORE DELETE ON cuts
               BEGIN SELECT RAISE(ABORT, 'cut history is immutable; retire cuts instead'); END"""
        )
        con.execute(
            """CREATE TRIGGER trg_cuts_no_update_cut_id BEFORE UPDATE OF cut_id ON cuts
               BEGIN SELECT RAISE(ABORT, 'cut_id identity is immutable'); END"""
        )
        con.execute(
            """CREATE TRIGGER trg_cuts_keep_one_active BEFORE UPDATE OF is_active ON cuts
               WHEN OLD.is_active = 1 AND NEW.is_active = 0
                AND (SELECT COUNT(*) FROM cuts WHERE is_active = 1) <= 1
               BEGIN SELECT RAISE(ABORT, 'at least one active cut is required'); END"""
        )
        con.execute(
            """CREATE TRIGGER trg_cut_intents_active_baseline BEFORE INSERT ON cut_intents
               FOR EACH ROW BEGIN
                 SELECT CASE WHEN NEW.baseline_id IS NULL
                   OR (SELECT current_baseline_id FROM authority WHERE singleton_id = 1) IS NULL
                   OR NEW.baseline_id != (SELECT current_baseline_id FROM authority WHERE singleton_id = 1)
                   THEN RAISE(ABORT, 'cut_intents insert requires active baseline') END;
               END"""
        )
    def _migrate_v4_to_v5(self, con: sqlite3.Connection) -> None:
        """Rebuild generation tables while freezing attributable job inputs."""
        old_job_cols = {row["name"] for row in con.execute("PRAGMA table_info(generation_jobs)").fetchall()}
        old_attempt_cols = {row["name"] for row in con.execute("PRAGMA table_info(generation_attempts)").fetchall()}
        job_rows = con.execute("SELECT * FROM generation_jobs ORDER BY created_at ASC, job_id ASC").fetchall()

        model_columns = [name for name in ("model", "provider_model") if name in old_job_cols]
        attempt_model_columns = [name for name in ("model", "provider_model") if name in old_attempt_cols]
        frozen_jobs: list[dict[str, Any]] = []
        for row in job_rows:
            model: str | None = row[model_columns[0]] if model_columns else None
            if (not isinstance(model, str) or not model.strip()) and attempt_model_columns:
                model_row = con.execute(
                    f"SELECT {attempt_model_columns[0]} FROM generation_attempts WHERE job_id = ? "
                    "ORDER BY ordinal ASC LIMIT 1",
                    (row["job_id"],),
                ).fetchone()
                model = model_row[0] if model_row else None
            if not isinstance(model, str) or not model.strip():
                raise StoreCorruptionError(
                    f"Migration from v4 to v5 cannot attribute historical model for job {row['job_id']}"
                )

            intent_row = con.execute(
                "SELECT payload_json FROM cut_intents WHERE cut_id = ? AND revision = ?",
                (row["cut_id"], row["target_desired_revision"]),
            ).fetchone()
            if not intent_row:
                raise StoreCorruptionError(
                    f"Migration from v4 to v5 cannot resolve prompt for job {row['job_id']}"
                )
            raw_payload = json.loads(intent_row["payload_json"])
            if isinstance(raw_payload, dict):
                prompt = raw_payload.get("prompt")
                origin = raw_payload.get("prompt_origin", "user")
            elif isinstance(raw_payload, str):
                prompt = raw_payload
                origin = "user"
            else:
                prompt = None
                origin = "user"
            if not isinstance(prompt, str) or not prompt.strip():
                raise StoreCorruptionError(
                    f"Migration from v4 to v5 cannot resolve non-empty prompt for job {row['job_id']}"
                )
            if not isinstance(origin, str) or origin not in PROMPT_ORIGINS:
                raise StoreCorruptionError(
                    f"Migration from v4 to v5 found invalid prompt origin for job {row['job_id']}"
                )
            frozen_jobs.append(
                {
                    "job_id": row["job_id"],
                    "cut_id": row["cut_id"],
                    "target_desired_revision": row["target_desired_revision"],
                    "request_seq": row["request_seq"],
                    "model": model,
                    "effective_prompt": prompt,
                    "effective_prompt_origin": origin,
                    "effective_prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "status": row["status"],
                    "terminal_detail": row["terminal_detail"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )

        con.execute("ALTER TABLE generation_attempts RENAME TO generation_attempts_v4")
        con.execute("ALTER TABLE generation_jobs RENAME TO generation_jobs_v4")
        con.execute(
            """
            CREATE TABLE generation_jobs (
                job_id TEXT PRIMARY KEY,
                cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id >= 1),
                target_desired_revision INTEGER NOT NULL CHECK (target_desired_revision > 0),
                request_seq INTEGER NOT NULL CHECK (request_seq > 0),
                model TEXT NOT NULL CHECK (length(trim(model)) > 0),
                effective_prompt TEXT NOT NULL CHECK (length(trim(effective_prompt)) > 0),
                effective_prompt_origin TEXT NOT NULL CHECK (effective_prompt_origin IN ('user', 'llm_draft', 'intelligent_default')),
                effective_prompt_sha256 TEXT NOT NULL CHECK (length(effective_prompt_sha256) = 64),
                status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled', 'interrupted', 'superseded')),
                terminal_detail TEXT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE generation_attempts (
                attempt_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL REFERENCES generation_jobs(job_id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL CHECK (ordinal >= 1),
                status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed', 'interrupted', 'cancelled')),
                started_at TEXT NOT NULL,
                finished_at TEXT NULL,
                detail TEXT NULL,
                runner_id TEXT NULL,
                process_pid INTEGER NULL,
                process_group_id INTEGER NULL,
                process_start_token TEXT NULL,
                staging_path TEXT NULL,
                provider_request_id TEXT NULL,
                UNIQUE (job_id, ordinal),
                CHECK (
                    (process_pid IS NULL AND process_group_id IS NULL AND process_start_token IS NULL) OR
                    (process_pid IS NOT NULL AND process_group_id IS NOT NULL AND process_start_token IS NOT NULL)
                )
            )
            """
        )
        for job in frozen_jobs:
            con.execute(
                """
                INSERT INTO generation_jobs (
                    job_id, cut_id, target_desired_revision, request_seq, model,
                    effective_prompt, effective_prompt_origin, effective_prompt_sha256,
                    status, terminal_detail, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(job[field] for field in (
                    "job_id", "cut_id", "target_desired_revision", "request_seq", "model",
                    "effective_prompt", "effective_prompt_origin", "effective_prompt_sha256",
                    "status", "terminal_detail", "created_at", "updated_at",
                )),
            )
        old_attempt_rows = con.execute("SELECT * FROM generation_attempts_v4").fetchall()
        for row in old_attempt_rows:
            con.execute(
                """
                INSERT INTO generation_attempts (
                    attempt_id, job_id, ordinal, status, started_at, finished_at, detail,
                    runner_id, process_pid, process_group_id, process_start_token,
                    staging_path, provider_request_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(row[name] if name in old_attempt_cols else None for name in (
                    "attempt_id", "job_id", "ordinal", "status", "started_at", "finished_at", "detail",
                    "runner_id", "process_pid", "process_group_id", "process_start_token",
                    "staging_path", "provider_request_id",
                )),
            )
        con.execute("DROP TABLE generation_attempts_v4")
        con.execute("DROP INDEX IF EXISTS idx_generation_jobs_queued")
        con.execute("DROP TABLE generation_jobs_v4")
        con.execute("CREATE INDEX idx_generation_jobs_queued ON generation_jobs (status, created_at, job_id)")

    def _migrate_v5_to_v6(self, con: sqlite3.Connection) -> None:
        """Convert legacy global bubble coordinates to composition schema v2."""
        from decimal import Decimal, ROUND_HALF_UP
        from comic_new.composition import (
            CANONICAL_WIDTH,
            LEGACY_CANONICAL_HEIGHT,
            compute_bubble_geometry,
        )

        row = con.execute("SELECT revision, state_json FROM composition WHERE singleton_id = 1").fetchone()
        if not row:
            raise StoreCorruptionError("Missing composition singleton during v5 to v6 migration")
        try:
            state = json.loads(row["state_json"])
        except Exception as exc:
            raise StoreCorruptionError(f"Migration from v5 to v6 cannot parse composition state: {exc}") from exc
        if state == {}:
            return
        if not isinstance(state, dict):
            raise StoreCorruptionError("Migration from v5 to v6 requires composition state object")
        if state.get("schema_version") == 2:
            return
        if state.get("schema_version") != 1:
            raise StoreCorruptionError(f"Migration from v5 to v6 found unsupported composition schema {state.get('schema_version')!r}")
        if set(state) - {"schema_version", "gap_px", "font_sha256", "bubbles"}:
            raise StoreCorruptionError("Migration from v5 to v6 found unknown legacy composition fields")
        gap_px = state.get("gap_px")
        if isinstance(gap_px, bool) or not isinstance(gap_px, int) or gap_px < 0 or LEGACY_CANONICAL_HEIGHT - 4 * gap_px < 5:
            raise StoreCorruptionError(f"Migration from v5 to v6 found invalid legacy gap_px {gap_px!r}")
        font_sha256 = state.get("font_sha256")
        if not isinstance(font_sha256, str):
            raise StoreCorruptionError("Migration from v5 to v6 found invalid font_sha256")
        bubbles = state.get("bubbles")
        if not isinstance(bubbles, list):
            raise StoreCorruptionError("Migration from v5 to v6 found invalid bubbles list")

        usable = LEGACY_CANONICAL_HEIGHT - 4 * gap_px
        legacy_slots: list[tuple[int, int, int]] = []
        for index in range(5):
            top = (index * usable) // 5 + index * gap_px
            bottom = ((index + 1) * usable) // 5 + index * gap_px
            legacy_slots.append((index + 1, top, bottom))
        legacy_style_keys = {
            "bubble_id", "cut_id", "shape", "text", "font_size_pct", "line_spacing_pct",
            "text_align", "text_rgba", "fill_rgba", "outline_rgba", "outline_width_pct", "padding_pct",
        }
        converted: list[dict[str, Any]] = []
        for index, bubble in enumerate(bubbles):
            if not isinstance(bubble, dict):
                raise StoreCorruptionError(f"Migration from v5 to v6 bubble {index} is not an object")
            required = legacy_style_keys | {"x_pct", "y_pct", "w_pct", "h_pct"}
            if set(bubble) != required:
                raise StoreCorruptionError(f"Migration from v5 to v6 bubble {index} has unsupported fields")
            try:
                cut_id = bubble["cut_id"]
                if isinstance(cut_id, bool) or not isinstance(cut_id, int) or cut_id not in range(1, 6):
                    raise ValueError("invalid cut_id")
                vals = {key: Decimal(str(bubble[key])) for key in ("x_pct", "y_pct", "w_pct", "h_pct")}
                if any(not value.is_finite() for value in vals.values()):
                    raise ValueError("non-finite coordinate")
                old_edges = (
                    int((vals["x_pct"] * CANONICAL_WIDTH / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
                    int((vals["y_pct"] * LEGACY_CANONICAL_HEIGHT / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
                    int(((vals["x_pct"] + vals["w_pct"]) * CANONICAL_WIDTH / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
                    int(((vals["y_pct"] + vals["h_pct"]) * LEGACY_CANONICAL_HEIGHT / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
                )
            except (ArithmeticError, TypeError, ValueError) as exc:
                raise StoreCorruptionError(f"Migration from v5 to v6 bubble {index} has invalid coordinates") from exc
            center_y = (old_edges[1] + old_edges[3]) / 2
            owner = next((slot for slot in legacy_slots if slot[1] <= center_y < slot[2]), None)
            safe = owner is not None and owner[0] == cut_id and old_edges[1] >= owner[1] and old_edges[3] <= owner[2] and old_edges[3] > old_edges[1]
            common = {key: bubble[key] for key in legacy_style_keys}
            if safe:
                _, slot_top, slot_bottom = owner
                slot_height = slot_bottom - slot_top
                local_y = ((Decimal(old_edges[1] - slot_top) * 100) / slot_height).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                local_h = ((Decimal(old_edges[3] - old_edges[1]) * 100) / slot_height).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                candidate = {
                    "anchor_status": "ANCHORED", **common,
                    "local_x_pct": float(vals["x_pct"]),
                    "local_y_pct": float(local_y),
                    "local_w_pct": float(vals["w_pct"]),
                    "local_h_pct": float(local_h),
                }
                try:
                    projected = compute_bubble_geometry(candidate, {"cut_id": cut_id, "top_px": slot_top, "bottom_px": slot_bottom, "height_px": slot_height}, CANONICAL_WIDTH)
                except Exception:
                    safe = False
                if safe and projected == old_edges:
                    converted.append(candidate)
                    continue
            converted.append({
                "anchor_status": "REANCHOR_REQUIRED", **common,
                "legacy_global_rect": {key: bubble[key] for key in ("x_pct", "y_pct", "w_pct", "h_pct")},
            })

        new_state = {
            "schema_version": 2,
            "canvas_width_px": CANONICAL_WIDTH,
            "gap_px": gap_px,
            "slot_heights_px": [bottom - top for _, top, bottom in legacy_slots],
            "fit": "contain",
            "font_sha256": font_sha256,
            "bubbles": converted,
        }
        from comic_new.composition import canonical_json_dumps
        new_comp_rev = row["revision"] + 1
        auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
        if not auth_row:
            raise StoreCorruptionError("Missing authority singleton during v5 to v6 migration")
        new_auth_rev = auth_row["authority_revision"] + 1
        now_iso = datetime.now(timezone.utc).isoformat()
        con.execute(
            "UPDATE composition SET revision = ?, state_json = ?, updated_at = ? WHERE singleton_id = 1",
            (new_comp_rev, canonical_json_dumps(new_state), now_iso),
        )
        self._revoke_active_authorization(con, new_auth_rev, now_iso)
        con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_auth_rev,))

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

            all_cut_rows = con.execute("SELECT cut_id, is_active, display_order FROM cuts ORDER BY cut_id;").fetchall()
            if not all_cut_rows:
                raise StoreCorruptionError("cuts table must contain at least one stable cut")
            active_rows = self._active_cuts(con)
            active_ids = [row["cut_id"] for row in active_rows]
            if any(row["is_active"] not in (0, 1) for row in all_cut_rows):
                raise StoreCorruptionError("cuts contains invalid is_active value")
            if any(row["is_active"] == 0 and row["display_order"] is not None for row in all_cut_rows):
                raise StoreCorruptionError("inactive cuts must have NULL display_order")
            cut_cols = {row["name"] for row in con.execute("PRAGMA table_info(cuts);").fetchall()}
            if not {"is_active", "display_order", "latest_generation_request_seq"}.issubset(cut_cols):
                raise StoreCorruptionError("cuts missing v7 active-set columns")
            if active_ids != [row["cut_id"] for row in active_rows]:
                raise StoreCorruptionError("active cut order is not stable")

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

            cut_cols = {row["name"] for row in con.execute("PRAGMA table_info(cuts);").fetchall()}
            if "latest_generation_request_seq" not in cut_cols:
                raise StoreCorruptionError("cuts missing column: latest_generation_request_seq")

            job_cols_info = con.execute("PRAGMA table_info(generation_jobs);").fetchall()
            job_cols = {row["name"] for row in job_cols_info}
            required_job_cols = {
                "request_seq", "model", "effective_prompt", "effective_prompt_origin", "effective_prompt_sha256",
            }
            missing_job_cols = required_job_cols - job_cols
            if missing_job_cols:
                raise StoreCorruptionError(f"generation_jobs missing columns: {sorted(missing_job_cols)}")
            not_null_by_col = {row["name"]: row["notnull"] for row in job_cols_info}
            missing_not_null = {name for name in required_job_cols if not_null_by_col.get(name) != 1}
            if missing_not_null:
                raise StoreCorruptionError(f"generation_jobs columns must be NOT NULL: {sorted(missing_not_null)}")
            for row in con.execute(
                "SELECT model, effective_prompt, effective_prompt_origin, effective_prompt_sha256 FROM generation_jobs"
            ).fetchall():
                model = row["model"]
                prompt = row["effective_prompt"]
                origin = row["effective_prompt_origin"]
                prompt_hash = row["effective_prompt_sha256"]
                if not isinstance(model, str) or not model.strip():
                    raise StoreCorruptionError("generation_jobs contains an empty model")
                if not isinstance(prompt, str) or not prompt.strip():
                    raise StoreCorruptionError("generation_jobs contains an empty effective prompt")
                if origin not in PROMPT_ORIGINS:
                    raise StoreCorruptionError(f"generation_jobs contains invalid prompt origin: {origin!r}")
                if (
                    not isinstance(prompt_hash, str)
                    or len(prompt_hash) != 64
                    or any(char not in "0123456789abcdef" for char in prompt_hash.lower())
                    or hashlib.sha256(prompt.encode("utf-8")).hexdigest() != prompt_hash.lower()
                ):
                    raise StoreCorruptionError("generation_jobs contains an invalid effective prompt hash")

            invalid_seq_jobs = con.execute("SELECT COUNT(*) FROM generation_jobs WHERE request_seq <= 0").fetchone()[0]
            if invalid_seq_jobs > 0:
                raise StoreCorruptionError(f"Found {invalid_seq_jobs} generation_jobs with nonpositive request_seq")

            invalid_seq_cuts = con.execute("SELECT COUNT(*) FROM cuts WHERE latest_generation_request_seq < 0").fetchone()[0]
            if invalid_seq_cuts > 0:
                raise StoreCorruptionError(f"Found {invalid_seq_cuts} cuts with negative latest_generation_request_seq")

            comp_state_row = con.execute("SELECT state_json FROM composition WHERE singleton_id = 1").fetchone()
            if not comp_state_row:
                raise StoreCorruptionError("Missing composition singleton state")
            try:
                persisted_state = json.loads(comp_state_row["state_json"])
            except Exception as exc:
                raise StoreCorruptionError(f"Composition state is not valid JSON: {exc}") from exc
            if persisted_state != {}:
                from comic_new.composition import normalize_state
                try:
                    normalize_state(persisted_state)
                except Exception as exc:
                    raise StoreCorruptionError(f"Persisted composition state is invalid: {exc}") from exc
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
    def _validate_cuts_sequence_current(self, con: sqlite3.Connection) -> list[sqlite3.Row]:
        cuts_rows = self._active_cuts(con)
        for r in cuts_rows:
            cid = r["cut_id"]
            d_rev = r["desired_revision"]
            r_rev = r["realized_revision"]
            latest_seq = r["latest_generation_request_seq"]
            if d_rev is None or r_rev != d_rev:
                raise RealizationIncompleteError(f"Cut {cid} is not current (desired={d_rev}, realized={r_rev})")
            if latest_seq > 0:
                latest_job = con.execute(
                    "SELECT status FROM generation_jobs WHERE cut_id = ? AND request_seq = ?",
                    (cid, latest_seq),
                ).fetchone()
                if latest_job is None or latest_job["status"] != "succeeded":
                    raise RealizationIncompleteError(
                        f"Cut {cid} latest generation sequence {latest_seq} is not succeeded"
                    )
        return cuts_rows

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
            active_rows = self._active_cuts(con)
            active_ids = [row["cut_id"] for row in active_rows]

            baseline_data: dict[str, Any] | None = None
            if current_baseline_id is not None:
                b_row = con.execute(
                    "SELECT baseline_id, structure_json, authority_revision, created_at FROM structural_baselines WHERE baseline_id = ?",
                    (current_baseline_id,),
                ).fetchone()
                if b_row:
                    intents_rows = con.execute(
                        """SELECT bi.cut_id, bi.intent_revision
                           FROM baseline_intents bi JOIN cuts c ON c.cut_id = bi.cut_id
                          WHERE bi.baseline_id = ? AND c.is_active = 1
                          ORDER BY c.display_order ASC""",
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
                """SELECT c.cut_id, c.display_order, c.desired_revision, c.latest_generation_request_seq,
                          c.realized_revision, c.realized_asset_id, c.realized_asset_path,
                          c.realized_content_hash, i.payload_json AS effective_intent_json
                     FROM cuts c
                     LEFT JOIN cut_intents i ON c.cut_id = i.cut_id AND c.desired_revision = i.revision
                    WHERE c.is_active = 1 ORDER BY c.display_order ASC"""
            ).fetchall()
            if [row["cut_id"] for row in cuts_rows] != active_ids:
                raise StoreCorruptionError("Active cut snapshot changed during read")

            cuts_data: list[dict[str, Any]] = []
            all_current = True
            for row in cuts_rows:
                cid = row["cut_id"]
                d_rev = row["desired_revision"]
                latest_seq = row["latest_generation_request_seq"]
                r_rev = row["realized_revision"]
                eff_intent = json.loads(row["effective_intent_json"]) if row["effective_intent_json"] is not None else None
                if isinstance(eff_intent, dict) and "prompt_origin" not in eff_intent:
                    eff_intent["prompt_origin"] = "user"
                rev_match = d_rev is not None and r_rev is not None and d_rev == r_rev
                if latest_seq == 0:
                    is_current = rev_match
                else:
                    latest_job = con.execute(
                        "SELECT status FROM generation_jobs WHERE cut_id = ? AND request_seq = ?",
                        (cid, latest_seq),
                    ).fetchone()
                    is_current = rev_match and latest_job is not None and latest_job["status"] == "succeeded"
                currency = "CURRENT" if is_current else "STALE"
                all_current = all_current and is_current
                cuts_data.append({
                    "cut_id": cid,
                    "display_order": row["display_order"],
                    "desired_revision": d_rev,
                    "latest_generation_request_seq": latest_seq,
                    "effective_intent": eff_intent,
                    "realized_revision": r_rev,
                    "realized_asset_id": row["realized_asset_id"],
                    "realized_asset_path": row["realized_asset_path"],
                    "realized_content_hash": row["realized_content_hash"],
                    "currency": currency,
                })
            realization_complete = {
                "complete": all_current and bool(cuts_data),
                "status": "COMPLETE" if all_current and cuts_data else "UNRESOLVED",
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
                        "request_seq": j["request_seq"],
                        "model": j["model"],
                        "effective_prompt": j["effective_prompt"],
                        "effective_prompt_origin": j["effective_prompt_origin"],
                        "effective_prompt_sha256": j["effective_prompt_sha256"],
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
                    "SELECT cut_id, display_order, realized_revision, asset_id FROM artifact_cuts WHERE artifact_id = ? ORDER BY display_order ASC",
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
                                "display_order": ac["display_order"],
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
                    "revoked_authority_revision": active_auth_row["revoked_authority_revision"],
                    "created_at": active_auth_row["created_at"],
                    "revoked_at": active_auth_row["revoked_at"],
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
        from comic_new.composition import canonical_json_dumps

        if not isinstance(baseline_id, str) or not baseline_id.strip():
            raise ValidationError("baseline_id must be a non-empty string")
        if isinstance(structure, str):
            try:
                structure_obj = json.loads(structure)
            except Exception as exc:
                raise ValidationError("structure must be a JSON object") from exc
        else:
            structure_obj = structure
        if not isinstance(structure_obj, dict):
            raise ValidationError("structure must be a JSON object")
        cuts = structure_obj.get("cuts")
        if not isinstance(cuts, list) or not cuts:
            raise ValidationError("structure.cuts must be a non-empty list")
        structure_ids = [self._validate_cut_id(c.get("cut_id")) if isinstance(c, dict) else 0 for c in cuts]
        if len(set(structure_ids)) != len(structure_ids):
            raise ValidationError("structure.cuts must contain ordered unique positive IDs")
        if not isinstance(intents_by_cut, dict) or set(intents_by_cut) != set(structure_ids):
            raise ValidationError("intents_by_cut keys must exactly match structure cuts")
        parsed_intents = {
            cid: self._resolve_baseline_intent(intents_by_cut[cid], structure_obj, cid)
            for cid in structure_ids
        }
        struct_json = canonical_json_dumps(structure_obj)
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            active_rows = self._active_cuts(con)
            active_ids = [row["cut_id"] for row in active_rows]
            current_base = con.execute("SELECT current_baseline_id FROM authority WHERE singleton_id = 1").fetchone()
            current_base_id = current_base["current_baseline_id"] if current_base else None
            requested_ids = structure_ids
            pristine = (
                current_base_id is None
                and con.execute("SELECT COUNT(*) FROM cut_intents").fetchone()[0] == 0
                and con.execute("SELECT COUNT(*) FROM generation_jobs").fetchone()[0] == 0
                and con.execute("SELECT COUNT(*) FROM artifact_cuts").fetchone()[0] == 0
            )
            if pristine and structure_ids != list(range(1, len(cuts) + 1)):
                raise ValidationError("First baseline must use stable cut IDs 1..N")
            if not pristine and active_ids != requested_ids:
                raise ValidationError("Baseline cut order must match active cuts")
            if pristine:
                physical_ids = [row["cut_id"] for row in con.execute("SELECT cut_id FROM cuts ORDER BY cut_id").fetchall()]
                max_physical = max(physical_ids, default=0)
                for cid in physical_ids:
                    if cid > len(requested_ids):
                        con.execute("UPDATE cuts SET is_active = 0, display_order = NULL WHERE cut_id = ?", (cid,))
                for cid in range(1, len(requested_ids) + 1):
                    if cid in physical_ids:
                        con.execute("UPDATE cuts SET is_active = 1, display_order = ? WHERE cut_id = ?", (cid, cid))
                    else:
                        if cid <= max_physical:
                            raise StoreCorruptionError("Cannot allocate non-monotonic initial cut identity")
                        con.execute("INSERT INTO cuts (cut_id, is_active, display_order) VALUES (?, 1, ?)", (cid, cid))
            active_rows = self._active_cuts(con)
            active_ids = [row["cut_id"] for row in active_rows]
            if active_ids != requested_ids:
                raise StoreCorruptionError("Active cuts do not match approved baseline structure")
            con.execute(
                "INSERT INTO structural_baselines (baseline_id, structure_json, authority_revision, created_at) VALUES (?, ?, ?, ?)",
                (baseline_id, struct_json, new_rev, now_iso),
            )
            con.execute(
                "UPDATE authority SET current_baseline_id = ?, authority_revision = ? WHERE singleton_id = 1",
                (baseline_id, new_rev),
            )
            for cid in active_ids:
                cur_row = con.execute("SELECT desired_revision FROM cuts WHERE cut_id = ?", (cid,)).fetchone()
                new_intent_rev = (cur_row["desired_revision"] or 0) + 1 if cur_row else 1
                payload_json = canonical_json_dumps(parsed_intents[cid])
                con.execute(
                    "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (cid, new_intent_rev, baseline_id, payload_json, new_rev, now_iso),
                )
                con.execute("UPDATE cuts SET desired_revision = ? WHERE cut_id = ?", (new_intent_rev, cid))
                con.execute(
                    "INSERT INTO baseline_intents (baseline_id, cut_id, intent_revision) VALUES (?, ?, ?)",
                    (baseline_id, cid, new_intent_rev),
                )

            comp_row = con.execute("SELECT revision, state_json FROM composition WHERE singleton_id = 1").fetchone()
            if comp_row and comp_row["state_json"]:
                comp_state = json.loads(comp_row["state_json"])
                changed = False
                for bubble in comp_state.get("bubbles", []):
                    cid = bubble.get("cut_id")
                    if cid in parsed_intents and bubble.get("text") != parsed_intents[cid]["dialogue"]:
                        bubble["text"] = parsed_intents[cid]["dialogue"]
                        changed = True
                if changed:
                    con.execute(
                        "UPDATE composition SET revision = ?, state_json = ?, updated_at = ? WHERE singleton_id = 1",
                        (comp_row["revision"] + 1, canonical_json_dumps(comp_state), now_iso),
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
        from comic_new.composition import canonical_json_dumps

        self._validate_cut_id(cut_id)
        parsed_intent = self._parse_structured_intent(intent_payload)
        parsed_intent = {
            "prompt": parsed_intent["prompt"],
            "dialogue": parsed_intent["dialogue"],
            "prompt_origin": parsed_intent.get("prompt_origin", "user"),
        }
        payload_json = json.dumps(parsed_intent, sort_keys=True)
        now_iso = datetime.now(timezone.utc).isoformat()

        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            cur_base_id = self._require_active_baseline(con)

            active_ids = {row["cut_id"] for row in self._active_cuts(con)}
            if cut_id not in active_ids:
                raise ValidationError(f"Cut {cut_id} is not an active cut")
            cur_des_row = con.execute("SELECT desired_revision FROM cuts WHERE cut_id = ?", (cut_id,)).fetchone()
            cur_des = cur_des_row["desired_revision"] if cur_des_row else None
            new_intent_rev = (cur_des or 0) + 1

            con.execute(
                "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (cut_id, new_intent_rev, cur_base_id, payload_json, new_rev, now_iso),
            )
            con.execute(
                "UPDATE cuts SET desired_revision = ? WHERE cut_id = ?", (new_intent_rev, cut_id)
            )

            # Acceptance D: Synchronize affected cut bubbles with the new dialogue
            comp_row = con.execute(
                "SELECT revision, state_json FROM composition WHERE singleton_id = 1"
            ).fetchone()
            if comp_row and comp_row["state_json"]:
                comp_state = json.loads(comp_row["state_json"])
                bubbles = comp_state.get("bubbles", [])
                changed = False
                for b in bubbles:
                    if b.get("cut_id") == cut_id:
                        target_d = parsed_intent["dialogue"]
                        if b.get("text") != target_d:
                            b["text"] = target_d
                            changed = True
                if changed:
                    new_comp_rev = comp_row["revision"] + 1
                    new_state_json = canonical_json_dumps(comp_state)
                    con.execute(
                        "UPDATE composition SET revision = ?, state_json = ?, updated_at = ? WHERE singleton_id = 1",
                        (new_comp_rev, new_state_json, now_iso),
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
        if not norm_state["slot_heights_px"]:
            raise ValidationError("Composition slot heights must be non-empty")
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            cur_base_id = self._require_active_baseline(con)

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

            # Inspect bubbles per cut
            active_rows = self._active_cuts(con)
            active_ids = [row["cut_id"] for row in active_rows]
            if len(norm_state["slot_heights_px"]) != len(active_ids):
                raise ValidationError(f"Composition slot heights must match active cuts ({len(active_ids)}), got {len(norm_state['slot_heights_px'])}")
            bubbles_by_cut: dict[int, list[dict[str, Any]]] = {cid: [] for cid in active_ids}
            for b in norm_state.get("bubbles", []):
                cid = b.get("cut_id")
                if cid not in bubbles_by_cut:
                    raise ValidationError(f"Bubble {b.get('bubble_id')} belongs to inactive or unknown cut {cid}")
                bubbles_by_cut[cid].append(b)

            # Fetch active current cut intents.
            current_intents: dict[int, dict[str, Any]] = {}
            for cid in active_ids:
                cut_row = con.execute("SELECT desired_revision FROM cuts WHERE cut_id = ?", (cid,)).fetchone()
                if not cut_row or cut_row["desired_revision"] is None:
                    raise BaselineRequiredError(f"Cut {cid} has no active intent binding")
                d_rev = cut_row["desired_revision"]
                intent_row = con.execute(
                    "SELECT revision, baseline_id, payload_json FROM cut_intents WHERE cut_id = ? AND revision = ?",
                    (cid, d_rev),
                ).fetchone()
                if not intent_row or intent_row["baseline_id"] != cur_base_id:
                    raise BaselineRequiredError(f"Cut {cid} intent is not bound to active baseline {cur_base_id}")
                payload = json.loads(intent_row["payload_json"])
                current_intents[cid] = {"desired_revision": d_rev, "prompt": payload.get("prompt", ""), "dialogue": payload.get("dialogue", ""), "prompt_origin": payload.get("prompt_origin", "user")}

            # Acceptance E & F & G:
            # For each cut:
            # - If multiple bubbles exist for the cut, all must have identical text.
            #   If texts differ for the same cut, reject with ValidationError.
            # - If submitted bubble text differs from current CutIntent.dialogue:
            #   create exactly ONE new CutIntent revision for this cut (retaining prompt, active baseline).
            #   advance cuts.desired_revision.
            # - If no bubbles exist for the cut, or submitted text equals current dialogue:
            #   no CutIntent revision created.
            for cid in active_ids:
                cut_bubbles = bubbles_by_cut[cid]
                if not cut_bubbles:
                    continue
                distinct_texts = {b["text"] for b in cut_bubbles}
                if len(distinct_texts) > 1:
                    raise ValidationError(
                        f"Cut {cid} has conflicting bubble texts: {sorted(distinct_texts)}. All bubbles for a cut must share uniform text."
                    )
                submitted_text = distinct_texts.pop()
                cur_dialogue = current_intents[cid]["dialogue"]
                if submitted_text != cur_dialogue:
                    # Create new CutIntent revision
                    new_intent_rev = current_intents[cid]["desired_revision"] + 1
                    new_payload = {
                        "prompt": current_intents[cid]["prompt"],
                        "dialogue": submitted_text,
                        "prompt_origin": current_intents[cid]["prompt_origin"],
                    }
                    con.execute(
                        "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (cid, new_intent_rev, cur_base_id, json.dumps(new_payload, sort_keys=True), new_rev, now_iso),
                    )
                    con.execute(
                        "UPDATE cuts SET desired_revision = ? WHERE cut_id = ?",
                        (new_intent_rev, cid),
                    )

            # Advance composition revision by 1
            new_comp_rev = cur_comp_rev + 1
            state_json = canonical_json_dumps(norm_state)
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
        if cut_id is not None:
            self._validate_cut_id(cut_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            cur_base_id = self._require_active_baseline(con)

            active_ids = self._active_cut_ids(con)
            if cut_id is not None and cut_id not in active_ids:
                raise ValidationError(f"Cut {cut_id} is not an active cut")
            target_cuts = active_ids if cut_id is None else [cut_id]
            # Validate only requested cuts, then freeze their effective identity.
            cuts_to_enqueue: list[dict[str, Any]] = []
            for cid in target_cuts:
                cut_row = con.execute("SELECT desired_revision FROM cuts WHERE cut_id = ?", (cid,)).fetchone()
                if not cut_row or cut_row["desired_revision"] is None:
                    raise ValidationError(f"Cut {cid} has no desired intent to generate")
                d_rev = cut_row["desired_revision"]
                intent_row = con.execute(
                    "SELECT baseline_id, payload_json FROM cut_intents WHERE cut_id = ? AND revision = ?",
                    (cid, d_rev),
                ).fetchone()
                if not intent_row:
                    raise ValidationError(f"Cut {cid} revision {d_rev} intent record not found")
                if intent_row["baseline_id"] != cur_base_id:
                    raise BaselineRequiredError(
                        f"Cut {cid} revision {d_rev} intent is bound to baseline {intent_row['baseline_id']!r}, not active baseline {cur_base_id!r}"
                    )
                payload = self._parse_structured_intent(json.loads(intent_row["payload_json"]))
                effective_prompt = payload["prompt"]
                if not effective_prompt.strip():
                    raise ValidationError(
                        f"Cut {cid} revision {d_rev} intent payload does not contain a non-empty effective prompt"
                    )
                origin = payload.get("prompt_origin", "user")
                if origin not in PROMPT_ORIGINS:
                    raise ValidationError(f"Cut {cid} revision {d_rev} has invalid prompt origin")
                cuts_to_enqueue.append(
                    {
                        "cut_id": cid,
                        "target_desired_revision": d_rev,
                        "model": DEFAULT_GENERATION_MODEL,
                        "effective_prompt": effective_prompt,
                        "effective_prompt_origin": origin,
                        "effective_prompt_sha256": hashlib.sha256(effective_prompt.encode("utf-8")).hexdigest(),
                    }
                )

            created_jobs: list[dict[str, Any]] = []
            for target in cuts_to_enqueue:
                cid = target["cut_id"]
                d_rev = target["target_desired_revision"]
                job_id = f"job-{cid}-r{d_rev}-{uuid4().hex[:8]}"
                # Increment cut's latest_generation_request_seq
                con.execute(
                    "UPDATE cuts SET latest_generation_request_seq = latest_generation_request_seq + 1 WHERE cut_id = ?",
                    (cid,),
                )
                seq_row = con.execute("SELECT latest_generation_request_seq FROM cuts WHERE cut_id = ?", (cid,)).fetchone()
                req_seq = seq_row["latest_generation_request_seq"]

                con.execute(
                    """
                    INSERT INTO generation_jobs (
                        job_id, cut_id, target_desired_revision, request_seq, model,
                        effective_prompt, effective_prompt_origin, effective_prompt_sha256,
                        status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)
                    """,
                    (
                        job_id, cid, d_rev, req_seq, target["model"], target["effective_prompt"],
                        target["effective_prompt_origin"], target["effective_prompt_sha256"], now_iso, now_iso,
                    ),
                )
                created_jobs.append({
                    "job_id": job_id,
                    "cut_id": cid,
                    "target_desired_revision": d_rev,
                    "request_seq": req_seq,
                    "model": target["model"],
                    "effective_prompt": target["effective_prompt"],
                    "effective_prompt_origin": target["effective_prompt_origin"],
                    "effective_prompt_sha256": target["effective_prompt_sha256"],
                })
            self._revoke_active_authorization(con, new_rev, now_iso)
            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
            con.execute("COMMIT;")
            return (new_rev, created_jobs)
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    @staticmethod
    def _rewrite_active_order(con: sqlite3.Connection, ordered_ids: list[int]) -> None:
        if not ordered_ids or len(set(ordered_ids)) != len(ordered_ids):
            raise ValidationError("ordered active cut IDs must be non-empty and unique")
        max_order = con.execute("SELECT COALESCE(MAX(display_order), 0) FROM cuts").fetchone()[0]
        for index, cid in enumerate(ordered_ids, 1):
            con.execute("UPDATE cuts SET display_order = ? WHERE cut_id = ? AND is_active = 1", (max_order + index, cid))
        for index, cid in enumerate(ordered_ids, 1):
            con.execute("UPDATE cuts SET display_order = ? WHERE cut_id = ? AND is_active = 1", (index, cid))

    @staticmethod
    def _transform_composition_membership(
        con: sqlite3.Connection,
        old_ids: list[int],
        new_ids: list[int],
        now_iso: str,
        *,
        added_cut: bool = False,
    ) -> None:
        row = con.execute("SELECT revision, state_json FROM composition WHERE singleton_id = 1").fetchone()
        if not row or row["state_json"] == "{}":
            return
        from comic_new.composition import canonical_json_dumps, normalize_state
        state = normalize_state(json.loads(row["state_json"]))
        if len(state["slot_heights_px"]) != len(old_ids):
            raise StoreCorruptionError("Composition slots do not match the previous active cut set")
        heights = dict(zip(old_ids, state["slot_heights_px"], strict=True))
        default_height = max(1, (7680 - (len(new_ids) - 1) * state["gap_px"]) // len(new_ids))
        state["slot_heights_px"] = [heights.get(cid, default_height) for cid in new_ids]
        state["bubbles"] = [b for b in state.get("bubbles", []) if b.get("cut_id") in set(new_ids)]
        con.execute(
            "UPDATE composition SET revision = ?, state_json = ?, updated_at = ? WHERE singleton_id = 1",
            (row["revision"] + 1, canonical_json_dumps(state), now_iso),
        )

    def _clone_baseline_for_membership(
        self,
        con: sqlite3.Connection,
        baseline_id: str,
        structure: dict[str, Any],
        ordered_ids: list[int],
        new_rev: int,
        now_iso: str,
        *,
        added_cut: tuple[int, dict[str, Any]] | None = None,
    ) -> None:
        from comic_new.composition import canonical_json_dumps
        con.execute(
            "INSERT INTO structural_baselines (baseline_id, structure_json, authority_revision, created_at) VALUES (?, ?, ?, ?)",
            (baseline_id, canonical_json_dumps(structure), new_rev, now_iso),
        )
        con.execute("UPDATE authority SET current_baseline_id = ?, authority_revision = ? WHERE singleton_id = 1", (baseline_id, new_rev))
        added_id = added_cut[0] if added_cut else None
        if added_cut:
            payload = self._resolve_baseline_intent(added_cut[1], structure, added_id)
            con.execute(
                "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) VALUES (?, 1, ?, ?, ?, ?)",
                (added_id, baseline_id, canonical_json_dumps(payload), new_rev, now_iso),
            )
            con.execute("UPDATE cuts SET desired_revision = 1 WHERE cut_id = ?", (added_id,))
        for cid in ordered_ids:
            row = con.execute("SELECT desired_revision FROM cuts WHERE cut_id = ? AND is_active = 1", (cid,)).fetchone()
            if not row or row["desired_revision"] is None:
                raise BaselineRequiredError(f"Cut {cid} has no desired intent binding")
            con.execute(
                "INSERT INTO baseline_intents (baseline_id, cut_id, intent_revision) VALUES (?, ?, ?)",
                (baseline_id, cid, row["desired_revision"]),
            )
            # Rebind existing cut_intent row to the new cloned baseline so enqueue_generation_jobs can target it
            con.execute(
                "UPDATE cut_intents SET baseline_id = ? WHERE cut_id = ? AND revision = ?",
                (baseline_id, cid, row["desired_revision"]),
            )

    @staticmethod
    def _baseline_structure(con: sqlite3.Connection, baseline_id: str) -> dict[str, Any]:
        row = con.execute("SELECT structure_json FROM structural_baselines WHERE baseline_id = ?", (baseline_id,)).fetchone()
        if not row:
            raise BaselineRequiredError(f"Baseline {baseline_id} not found")
        structure = json.loads(row["structure_json"])
        if not isinstance(structure, dict) or not isinstance(structure.get("cuts"), list):
            raise StoreCorruptionError("Active baseline structure is invalid")
        return structure

    def add_cut(
        self,
        expected_authority_revision: int,
        baseline_id: str,
        role: str,
        beat: str,
        prompt: str = "",
        dialogue: str = "",
        position: int | None = None,
    ) -> tuple[int, int]:
        if not isinstance(baseline_id, str) or not baseline_id.strip() or not isinstance(role, str) or not isinstance(beat, str):
            raise ValidationError("baseline_id, role, and beat are required strings")
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            current_base = self._require_active_baseline(con)
            if baseline_id != current_base:
                raise ValidationError("baseline_id does not match active baseline")
            old_ids = self._active_cut_ids(con)
            new_id = con.execute("SELECT COALESCE(MAX(cut_id), 0) + 1 FROM cuts").fetchone()[0]
            insert_at = len(old_ids) + 1 if position is None else position
            if isinstance(insert_at, bool) or not isinstance(insert_at, int) or not 1 <= insert_at <= len(old_ids) + 1:
                raise ValidationError("position must be between 1 and active cut count + 1")
            con.execute("INSERT INTO cuts (cut_id, is_active, display_order) VALUES (?, 1, ?)", (new_id, len(old_ids) + 1))
            new_ids = old_ids[: insert_at - 1] + [new_id] + old_ids[insert_at - 1 :]
            self._rewrite_active_order(con, new_ids)
            structure = self._baseline_structure(con, current_base)
            structure["cuts"] = [*structure["cuts"]]
            structure["cuts"].insert(insert_at - 1, {"cut_id": new_id, "role": role, "beat": beat})
            payload = {"prompt": prompt, "dialogue": dialogue, "prompt_origin": "user"}
            self._clone_baseline_for_membership(con, f"{baseline_id}-m{new_rev}", structure, new_ids, new_rev, now_iso, added_cut=(new_id, payload))
            self._transform_composition_membership(con, old_ids, new_ids, now_iso, added_cut=True)
            self._revoke_active_authorization(con, new_rev, now_iso)
            con.execute("COMMIT;")
            return new_rev, new_id
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def retire_cut(self, expected_authority_revision: int, cut_id: int, baseline_id: str) -> int:
        self._validate_cut_id(cut_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            current_base = self._require_active_baseline(con)
            if baseline_id != current_base:
                raise ValidationError("baseline_id does not match active baseline")
            old_ids = self._active_cut_ids(con)
            if cut_id not in old_ids:
                raise ValidationError(f"Cut {cut_id} is not active")
            if len(old_ids) <= 1:
                raise ValidationError("At least one active cut is required")
            new_ids = [cid for cid in old_ids if cid != cut_id]
            structure = self._baseline_structure(con, current_base)
            structure["cuts"] = [c for c in structure["cuts"] if c.get("cut_id") != cut_id]
            con.execute("UPDATE cuts SET is_active = 0, display_order = NULL WHERE cut_id = ?", (cut_id,))
            self._rewrite_active_order(con, new_ids)
            self._clone_baseline_for_membership(con, f"{baseline_id}-m{new_rev}", structure, new_ids, new_rev, now_iso)
            self._transform_composition_membership(con, old_ids, new_ids, now_iso)
            self._revoke_active_authorization(con, new_rev, now_iso)
            con.execute("COMMIT;")
            return new_rev
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK;")
            raise
        finally:
            con.close()

    def reorder_cuts(self, expected_authority_revision: int, ordered_ids: list[int], baseline_id: str) -> int:
        ordered_ids = self._ordered_ids(ordered_ids, field_name="ordered_cut_ids")
        now_iso = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            new_rev = self._begin_mutation(con, expected_authority_revision)
            current_base = self._require_active_baseline(con)
            if baseline_id != current_base:
                raise ValidationError("baseline_id does not match active baseline")
            old_ids = self._active_cut_ids(con)
            if set(ordered_ids) != set(old_ids):
                raise ValidationError("ordered_cut_ids must exactly match the active cut set")
            structure = self._baseline_structure(con, current_base)
            structure["cuts"] = sorted(structure["cuts"], key=lambda c: ordered_ids.index(c.get("cut_id")))
            self._rewrite_active_order(con, ordered_ids)
            self._clone_baseline_for_membership(con, f"{baseline_id}-m{new_rev}", structure, ordered_ids, new_rev, now_iso)
            self._transform_composition_membership(con, old_ids, ordered_ids, now_iso)
            self._revoke_active_authorization(con, new_rev, now_iso)
            con.execute("COMMIT;")
            return new_rev
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
                    "SELECT job_id, cut_id, target_desired_revision, request_seq, model, effective_prompt, "
                    "effective_prompt_origin, effective_prompt_sha256 FROM generation_jobs "
                    "WHERE status = 'queued' ORDER BY created_at ASC, job_id ASC LIMIT 1"
                ).fetchone()
                if not row:
                    con.execute("COMMIT;")
                    return None

                job_id = row["job_id"]
                cut_id = row["cut_id"]
                target_rev = row["target_desired_revision"]
                job_req_seq = row["request_seq"]

                cut_row = con.execute(
                    "SELECT desired_revision, latest_generation_request_seq FROM cuts WHERE cut_id = ?",
                    (cut_id,),
                ).fetchone()
                cur_desired = cut_row["desired_revision"] if cut_row else None
                latest_seq = cut_row["latest_generation_request_seq"] if cut_row else 0
                now_iso = datetime.now(timezone.utc).isoformat()

                if cur_desired != target_rev or job_req_seq != latest_seq:
                    # Stale: supersede immediately without spawning
                    detail = (
                        f"Target revision superseded before claim (target {target_rev} vs current {cur_desired})"
                        if cur_desired != target_rev
                        else f"Target request sequence superseded before claim (job seq {job_req_seq} vs latest {latest_seq})"
                    )
                    con.execute(
                        "UPDATE generation_jobs SET status = 'superseded', terminal_detail = ?, updated_at = ? WHERE job_id = ?",
                        (detail, now_iso, job_id),
                    )
                    auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
                    new_rev = auth_row[0] + 1
                    con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
                    # Loop to check next queued job
                    continue
                prompt = row["effective_prompt"]
                if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != row["effective_prompt_sha256"].lower():
                    raise StoreCorruptionError(f"Generation job {job_id} effective prompt hash mismatch")

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
                    "request_seq": job_req_seq,
                    "model": row["model"],
                    "attempt_id": attempt_id,
                    "effective_prompt": prompt,
                    "effective_prompt_origin": row["effective_prompt_origin"],
                    "effective_prompt_sha256": row["effective_prompt_sha256"],
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
            job = con.execute("SELECT cut_id, target_desired_revision, request_seq, status FROM generation_jobs WHERE job_id = ?", (job_id,)).fetchone()
            att = con.execute("SELECT status, runner_id FROM generation_attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()

            if not job or not att or job["status"] != "running" or att["status"] != "running" or att["runner_id"] != runner_id:
                con.execute("ROLLBACK;")
                candidate_png_path.unlink(missing_ok=True)
                return {"status": "discarded", "job_status": job["status"] if job else "unknown"}

            cut_id = job["cut_id"]
            target_rev = job["target_desired_revision"]
            job_req_seq = job["request_seq"]
            cut_row = con.execute("SELECT is_active, desired_revision, latest_generation_request_seq FROM cuts WHERE cut_id = ?", (cut_id,)).fetchone()
            is_active = bool(cut_row["is_active"]) if cut_row else False
            cur_desired = cut_row["desired_revision"] if cut_row else None
            latest_seq = cut_row["latest_generation_request_seq"] if cut_row else 0

            if not is_active or cur_desired != target_rev or job_req_seq != latest_seq:
                # Inactive, superseded revision, or superseded sequence: candidate is never canonical.
                detail = (
                    f"Cut {cut_id} is inactive" if not is_active
                    else f"Target revision {target_rev} superseded by current desired revision {cur_desired}"
                    if cur_desired != target_rev
                    else f"Target request sequence {job_req_seq} superseded by latest request sequence {latest_seq}"
                )
                con.execute(
                    "UPDATE generation_attempts SET status = 'succeeded', finished_at = ?, provider_request_id = ?, detail = 'Process succeeded but candidate superseded' WHERE attempt_id = ?",
                    (now_iso, provider_request_id, attempt_id),
                )
                con.execute(
                    "UPDATE generation_jobs SET status = 'superseded', terminal_detail = ?, updated_at = ? WHERE job_id = ?",
                    (detail, now_iso, job_id),
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
                # Atomically mark running attempt and job as cancelled before process termination
                if att_dict and att_dict.get("attempt_id"):
                    con.execute(
                        "UPDATE generation_attempts SET status = 'cancelled', finished_at = ?, detail = 'Cancelled by user' WHERE attempt_id = ? AND status = 'running'",
                        (now_iso, att_dict["attempt_id"]),
                    )
                con.execute(
                    "UPDATE generation_jobs SET status = 'cancelled', terminal_detail = 'Cancelled by user', updated_at = ? WHERE job_id = ? AND status = 'running'",
                    (now_iso, job_id),
                )
                auth_row = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()
                new_rev = auth_row[0] + 1
                con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
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
                    "UPDATE generation_attempts SET status = 'cancelled', finished_at = ?, detail = ? WHERE attempt_id = ? AND status = 'running'",
                    (now_iso, detail, attempt_id),
                )
            con.execute(
                "UPDATE generation_jobs SET status = 'cancelled', terminal_detail = ?, updated_at = ? WHERE job_id = ? AND status = 'running'",
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

            # Atomically mark running attempts and jobs as interrupted before process termination
            con.execute(
                "UPDATE generation_attempts SET status = 'interrupted', finished_at = ?, detail = 'global_stop' WHERE status = 'running'",
                (now_iso,),
            )
            con.execute(
                "UPDATE generation_jobs SET status = 'interrupted', terminal_detail = 'global_stop', updated_at = ? WHERE status = 'running'",
                (now_iso,),
            )

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
        if not isinstance(cut_closure, list) or not cut_closure:
            raise ValidationError("cut_closure must be a non-empty list")
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

            cuts_rows = self._validate_cuts_sequence_current(con)
            active_ids = [row["cut_id"] for row in cuts_rows]
            closure_ids = [item.get("cut_id") for item in cut_closure]
            if closure_ids != active_ids or len(set(closure_ids)) != len(closure_ids):
                raise ValidationError("Artifact closure must exactly match ordered active cuts")
            for index, (r, c_item) in enumerate(zip(cuts_rows, cut_closure, strict=True), 1):
                if c_item.get("display_order") != index:
                    raise ValidationError("Artifact closure display_order must be contiguous from 1")
                if c_item.get("realized_revision") != r["realized_revision"] or c_item.get("asset_id") != r["realized_asset_id"]:
                    raise ValidationError(
                        f"Cut {r['cut_id']} closure mismatch: closure has rev={c_item.get('realized_revision')}, asset={c_item.get('asset_id')}; actual has rev={r['realized_revision']}, asset={r['realized_asset_id']}"
                    )

            con.execute(
                "INSERT INTO review_artifacts (artifact_id, content_hash, composition_revision, created_at) VALUES (?, ?, ?, ?)",
                (artifact_id, content_hash, composition_revision, now_iso),
            )
            for index, item in enumerate(cut_closure, 1):
                con.execute(
                    "INSERT INTO artifact_cuts (artifact_id, cut_id, display_order, realized_revision, asset_id) VALUES (?, ?, ?, ?, ?)",
                    (artifact_id, item["cut_id"], index, item["realized_revision"], item["asset_id"]),
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
                "SELECT cut_id, display_order, realized_revision, asset_id FROM artifact_cuts WHERE artifact_id = ? ORDER BY display_order ASC",
                (artifact_id,),
            ).fetchall()
            active_ids = [row["cut_id"] for row in self._active_cuts(con)]
            if [ac["cut_id"] for ac in art_cuts] != active_ids or [ac["display_order"] for ac in art_cuts] != list(range(1, len(active_ids) + 1)):
                raise InvalidArtifactClosureError("Artifact closure does not match ordered active cuts")
            art_closure = {ac["cut_id"]: (ac["realized_revision"], ac["asset_id"]) for ac in art_cuts}

            cuts_rows = self._validate_cuts_sequence_current(con)
            for cr in cuts_rows:
                cid = cr["cut_id"]
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
            art_row = con.execute(
                "SELECT artifact_id, composition_revision FROM review_artifacts WHERE artifact_id = ?",
                (art_id,),
            ).fetchone()
            comp_row = con.execute("SELECT revision FROM composition WHERE singleton_id = 1").fetchone()
            if not comp_row or not art_row or comp_row["revision"] != art_row["composition_revision"]:
                cur_comp = comp_row["revision"] if comp_row else None
                art_comp = art_row["composition_revision"] if art_row else None
                raise InvalidArtifactClosureError(
                    f"Composition has changed (current {cur_comp} != artifact {art_comp})"
                )

            art_cuts = con.execute(
                "SELECT cut_id, display_order, realized_revision, asset_id FROM artifact_cuts WHERE artifact_id = ? ORDER BY display_order ASC",
                (art_id,),
            ).fetchall()
            active_rows = self._active_cuts(con)
            active_ids = [row["cut_id"] for row in active_rows]
            if [ac["cut_id"] for ac in art_cuts] != active_ids or [ac["display_order"] for ac in art_cuts] != list(range(1, len(active_ids) + 1)):
                raise InvalidArtifactClosureError("Artifact closure does not match ordered active cuts")
            art_closure = {ac["cut_id"]: (ac["realized_revision"], ac["asset_id"]) for ac in art_cuts}
            cuts_rows = self._validate_cuts_sequence_current(con)
            for cr in cuts_rows:
                cid = cr["cut_id"]
                if cid not in art_closure or art_closure[cid] != (cr["realized_revision"], cr["realized_asset_id"]):
                    raise InvalidArtifactClosureError(f"Cut {cid} realization does not match artifact closure")

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

    def get_delivery_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        """Return a single delivery attempt joined with its authorization artifact hash, or None."""
        con = self._connect()
        try:
            row = con.execute(
                """
                SELECT
                    da.attempt_id,
                    da.kind,
                    da.authorization_id,
                    da.artifact_id,
                    da.request_id,
                    da.outcome,
                    da.destination_id,
                    da.destination_url,
                    da.evidence_json,
                    da.observed_authority_revision,
                    da.created_at,
                    da.updated_at,
                    ra.artifact_content_hash,
                    ra.revoked_authority_revision
                FROM delivery_attempts da
                JOIN release_authorizations ra ON da.authorization_id = ra.authorization_id
                WHERE da.attempt_id = ?
                """,
                (attempt_id,),
            ).fetchone()
            if not row:
                return None
            ev = None
            if row["evidence_json"]:
                try:
                    ev = json.loads(row["evidence_json"])
                except Exception:
                    ev = row["evidence_json"]
            return {
                "attempt_id": row["attempt_id"],
                "kind": row["kind"],
                "authorization_id": row["authorization_id"],
                "artifact_id": row["artifact_id"],
                "request_id": row["request_id"],
                "outcome": row["outcome"],
                "destination_id": row["destination_id"],
                "destination_url": row["destination_url"],
                "evidence": ev,
                "evidence_json": row["evidence_json"],
                "observed_authority_revision": row["observed_authority_revision"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "artifact_content_hash": row["artifact_content_hash"],
                "revoked_authority_revision": row["revoked_authority_revision"],
            }
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
                "SELECT attempt_id, outcome FROM delivery_attempts WHERE attempt_id = ?", (attempt_id,)
            ).fetchone()
            if not att:
                raise ValidationError(f"Delivery attempt {attempt_id} not found")

            current_outcome = att["outcome"]
            if current_outcome != "unknown":
                raise ConflictError(
                    expected_authority_revision,
                    expected_authority_revision,
                    f"Cannot record observation on terminal delivery attempt {attempt_id} (current outcome: {current_outcome})",
                )

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
