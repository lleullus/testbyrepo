from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Callable, Iterator
from urllib.parse import quote

from implementation_verification import (
    Candidate,
    CriterionOutcome,
    CriterionResult,
    Currentness,
    Inspection,
    NoConclusiveResult,
    PublicResult,
    VerificationResult,
    VerificationStatus,
)


class DurableWorkError(RuntimeError):
    pass


class DurableResultIntegrityError(DurableWorkError):
    pass


class TransitionDisposition(str, Enum):
    STARTED = "STARTED"
    REENTER = "REENTER"
    BUSY = "BUSY"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class TransitionDecision:
    disposition: TransitionDisposition
    transition_identity: str
    result: Candidate | VerificationResult | None = None


@dataclass(frozen=True)
class OccupancyDecision:
    acquired: bool
    source_matches: bool | None
    observed_source: object | None = None


def _json_default(value: object) -> object:
    if isinstance(value, Path):
        return {"$path": str(value)}
    raise TypeError(f"unsupported durable value: {type(value).__name__}")


def _json_object_hook(value: dict[str, object]) -> object:
    if set(value) == {"$path"} and isinstance(value["$path"], str):
        return Path(value["$path"])
    return value


def _encode(value: object) -> bytes:
    return json.dumps(
        value,
        default=_json_default,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _decode(value: bytes) -> object:
    return json.loads(value, object_hook=_json_object_hook)


def _canonical_work(work: str | Path) -> str:
    path = Path(work).expanduser().resolve(strict=True)
    if not path.is_file():
        raise DurableWorkError("work must be an exact canonical Ticket file")
    return str(path)


def _canonical_domain(project_root: str | Path) -> str:
    path = Path(project_root).expanduser().resolve(strict=True)
    if not path.is_dir():
        raise DurableWorkError("mutation domain must be a canonical product directory")
    return str(path)


def _overlaps(left: str, right: str) -> bool:
    left_path = Path(left)
    right_path = Path(right)
    return left_path == right_path or left_path in right_path.parents or right_path in left_path.parents


class DurableWorkStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve(strict=False)

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self.database_path,
            timeout=30.0,
            isolation_level=None,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _connect_read_only(self) -> sqlite3.Connection | None:
        if not self.database_path.is_file():
            return None
        uri = f"file:{quote(str(self.database_path), safe='/')}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _initialize_locked(connection: sqlite3.Connection) -> None:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS work_streams (
                work TEXT PRIMARY KEY,
                head_result_ref TEXT,
                active_transition_ref TEXT
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS results (
                result_ref TEXT PRIMARY KEY,
                work TEXT NOT NULL REFERENCES work_streams(work),
                kind TEXT NOT NULL CHECK (kind IN ('CANDIDATE', 'VERIFICATION')),
                predecessor_ref TEXT REFERENCES results(result_ref),
                candidate_ref TEXT REFERENCES results(result_ref),
                payload_json BLOB NOT NULL,
                payload_sha256 TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS transitions (
                transition_ref TEXT PRIMARY KEY,
                work TEXT NOT NULL REFERENCES work_streams(work),
                kind TEXT NOT NULL CHECK (kind IN ('IMPLEMENT', 'VERIFY')),
                expected_head_ref TEXT REFERENCES results(result_ref),
                semantic_input_json BLOB NOT NULL,
                semantic_input_sha256 TEXT NOT NULL,
                progress_ref TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('ACTIVE', 'CLOSED')),
                result_ref TEXT REFERENCES results(result_ref),
                closed_without_result INTEGER NOT NULL DEFAULT 0 CHECK (closed_without_result IN (0, 1))
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS mutation_occupancy (
                transition_ref TEXT PRIMARY KEY REFERENCES transitions(transition_ref),
                domain_root TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS result_private_state (
                result_ref TEXT PRIMARY KEY REFERENCES results(result_ref),
                payload_json BLOB NOT NULL,
                payload_sha256 TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS one_active_transition_per_work
               ON transitions(work) WHERE state = 'ACTIVE'"""
        )
        connection.execute(
            """CREATE TRIGGER IF NOT EXISTS results_no_update
               BEFORE UPDATE ON results BEGIN SELECT RAISE(ABORT, 'immutable results'); END"""
        )
        connection.execute(
            """CREATE TRIGGER IF NOT EXISTS results_no_delete
               BEFORE DELETE ON results BEGIN SELECT RAISE(ABORT, 'immutable results'); END"""
        )
        connection.execute(
            """CREATE TRIGGER IF NOT EXISTS result_private_state_no_update
               BEFORE UPDATE ON result_private_state BEGIN SELECT RAISE(ABORT, 'immutable private result state'); END"""
        )
        connection.execute(
            """CREATE TRIGGER IF NOT EXISTS result_private_state_no_delete
               BEFORE DELETE ON result_private_state BEGIN SELECT RAISE(ABORT, 'immutable private result state'); END"""
        )

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._initialize_locked(connection)
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
            if self.database_path.exists():
                os.chmod(self.database_path, 0o600)

    @staticmethod
    def _candidate_payload(candidate: Candidate) -> dict[str, object]:
        return {
            "planning": candidate.planning,
            "acceptanceCriteria": list(candidate.acceptance_criteria),
            "source": candidate.source,
            "implementationChanges": list(candidate.implementation_changes),
            "preservedChanges": list(candidate.preserved_changes),
        }

    @staticmethod
    def _verification_payload(result: VerificationResult) -> dict[str, object]:
        return {
            "status": result.status.value,
            "criterionResults": [
                {
                    "criterion": item.criterion,
                    "outcome": item.outcome.value,
                    "evidence": list(item.evidence),
                }
                for item in result.criterion_results
            ],
        }

    @staticmethod
    def _private_result_state_locked(
        connection: sqlite3.Connection,
        result_ref: str,
    ) -> dict[str, object]:
        row = connection.execute(
            "SELECT payload_json, payload_sha256 FROM result_private_state WHERE result_ref = ?",
            (result_ref,),
        ).fetchone()
        if row is None:
            raise DurableWorkError("durable result private state is absent")
        encoded = bytes(row["payload_json"])
        if hashlib.sha256(encoded).hexdigest() != row["payload_sha256"]:
            raise DurableWorkError("durable result private state differs")
        payload = _decode(encoded)
        if (
            not isinstance(payload, dict)
            or set(payload)
            != {
                "unresolvedObservations",
                "resolvedObservationIdentities",
                "effectSafetyProjections",
            }
            or not isinstance(payload["unresolvedObservations"], list)
            or not isinstance(payload["resolvedObservationIdentities"], list)
            or not isinstance(payload["effectSafetyProjections"], list)
        ):
            raise DurableWorkError("durable result private state is malformed")
        return payload

    def _read_result_locked(
        self,
        connection: sqlite3.Connection,
        result_ref: str,
    ) -> Candidate | VerificationResult:
        row = connection.execute(
            "SELECT * FROM results WHERE result_ref = ?", (result_ref,)
        ).fetchone()
        if row is None:
            raise DurableWorkError("durable result is absent")
        encoded = bytes(row["payload_json"])
        if hashlib.sha256(encoded).hexdigest() != row["payload_sha256"]:
            raise DurableWorkError("durable result payload differs")
        payload = _decode(encoded)
        if not isinstance(payload, dict):
            raise DurableWorkError("durable result payload is malformed")
        if row["kind"] == "CANDIDATE":
            try:
                result = Candidate(
                    work=Path(row["work"]),
                    planning=payload["planning"],
                    acceptance_criteria=tuple(payload["acceptanceCriteria"]),
                    source=payload["source"],
                    implementation_changes=tuple(payload["implementationChanges"]),
                    preserved_changes=tuple(payload["preservedChanges"]),
                    result_identity=result_ref,
                )
            except (KeyError, TypeError) as exc:
                raise DurableWorkError("durable Candidate payload is malformed") from exc
            self._private_result_state_locked(connection, result_ref)
            return result
        if row["kind"] != "VERIFICATION" or not isinstance(row["candidate_ref"], str):
            raise DurableWorkError("durable result kind is malformed")
        candidate = self._read_result_locked(connection, row["candidate_ref"])
        if not isinstance(candidate, Candidate) or candidate.work != Path(row["work"]):
            raise DurableWorkError("VerificationResult candidate binding differs")
        try:
            criterion_results = tuple(
                CriterionResult(
                    item["criterion"],
                    CriterionOutcome(item["outcome"]),
                    tuple(item["evidence"]),
                )
                for item in payload["criterionResults"]
            )
            result = VerificationResult(
                candidate,
                criterion_results,
                result_identity=result_ref,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DurableWorkError("durable VerificationResult payload is malformed") from exc
        if payload.get("status") != result.status.value:
            raise DurableWorkError("durable VerificationResult status differs")
        self._private_result_state_locked(connection, result_ref)
        return result

    def read_candidate(self, result_ref: str) -> Candidate:
        connection = self._connect_read_only()
        if connection is None:
            raise DurableWorkError("durable Candidate store is absent")
        try:
            connection.execute("BEGIN")
            result = self._read_result_locked(connection, result_ref)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        if not isinstance(result, Candidate):
            raise DurableWorkError("durable result is not a Candidate")
        return result

    def unresolved_observations(self, candidate: Candidate) -> tuple[object, ...]:
        if candidate.result_identity is None:
            raise DurableWorkError("unresolved observation lookup requires a durable Candidate")
        connection = self._connect_read_only()
        if connection is None:
            raise DurableWorkError("durable Candidate store is absent")
        try:
            connection.execute("BEGIN")
            durable_candidate = self._read_result_locked(connection, candidate.result_identity)
            if durable_candidate != candidate:
                raise DurableWorkError("unresolved observation lookup Candidate differs")
            rows = connection.execute(
                """SELECT result_ref FROM results
                   WHERE work = ? AND kind = 'VERIFICATION' AND candidate_ref = ?
                   ORDER BY rowid""",
                (str(candidate.work), candidate.result_identity),
            ).fetchall()
            unresolved: dict[str, object] = {}
            resolved: set[str] = set()
            for row in rows:
                state = self._private_result_state_locked(connection, row["result_ref"])
                for identity in state["resolvedObservationIdentities"]:
                    if not isinstance(identity, str):
                        raise DurableWorkError("resolved observation identity is malformed")
                    resolved.add(identity)
                    unresolved.pop(identity, None)
                for item in state["unresolvedObservations"]:
                    if not isinstance(item, dict) or not isinstance(item.get("identity"), str):
                        raise DurableWorkError("unresolved observation item is malformed")
                    if item["identity"] not in resolved:
                        unresolved[item["identity"]] = item
            connection.commit()
            return tuple(unresolved.values())
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def effect_safety_facts(self, candidate: Candidate) -> tuple[object, ...]:
        if candidate.result_identity is None:
            raise DurableWorkError("effect safety lookup requires a durable Candidate")
        connection = self._connect_read_only()
        if connection is None:
            raise DurableWorkError("durable Candidate store is absent")
        try:
            connection.execute("BEGIN")
            durable_candidate = self._read_result_locked(connection, candidate.result_identity)
            if durable_candidate != candidate:
                raise DurableWorkError("effect safety lookup Candidate differs")
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.effect_safety_facts_for_work(candidate.work)

    def effect_safety_facts_for_work(self, work: str | Path) -> tuple[object, ...]:
        exact_work = _canonical_work(work)
        connection = self._connect_read_only()
        if connection is None:
            raise DurableWorkError("durable Candidate store is absent")
        try:
            connection.execute("BEGIN")
            rows = connection.execute(
                "SELECT result_ref FROM results WHERE work = ? ORDER BY rowid",
                (exact_work,),
            ).fetchall()
            facts: dict[str, object] = {}
            resolved: set[str] = set()
            for row in rows:
                state = self._private_result_state_locked(connection, row["result_ref"])
                for identity in state["resolvedObservationIdentities"]:
                    if not isinstance(identity, str):
                        raise DurableWorkError("resolved observation identity is malformed")
                    resolved.add(identity)
                    facts.pop(identity, None)
                for item in (
                    list(state["unresolvedObservations"])
                    + list(state["effectSafetyProjections"])
                ):
                    if not isinstance(item, dict) or not isinstance(item.get("identity"), str):
                        raise DurableWorkError("effect safety fact is malformed")
                    if item["identity"] not in resolved:
                        facts[item["identity"]] = item
            connection.commit()
            return tuple(facts.values())
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _validate_lineage_locked(
        connection: sqlite3.Connection,
        work: str,
        head_ref: str,
    ) -> None:
        seen: set[str] = set()
        current: str | None = head_ref
        while current is not None:
            if current in seen:
                raise DurableWorkError("durable result lineage contains a cycle")
            seen.add(current)
            row = connection.execute(
                "SELECT work, predecessor_ref FROM results WHERE result_ref = ?", (current,)
            ).fetchone()
            if row is None or row["work"] != work:
                raise DurableWorkError("durable result lineage differs from work")
            current = row["predecessor_ref"]

    def begin(
        self,
        work: str | Path,
        kind: str,
        semantic_input: object,
        progress_ref: str,
    ) -> TransitionDecision:
        if kind not in {"IMPLEMENT", "VERIFY"}:
            raise DurableWorkError("unsupported transition kind")
        exact_work = _canonical_work(work)
        semantic_json = _encode(semantic_input)
        semantic_digest = hashlib.sha256(semantic_json).hexdigest()
        with self._transaction() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO work_streams(work) VALUES (?)", (exact_work,)
            )
            stream = connection.execute(
                "SELECT * FROM work_streams WHERE work = ?", (exact_work,)
            ).fetchone()
            active_ref = stream["active_transition_ref"]
            if active_ref is not None:
                active = connection.execute(
                    "SELECT * FROM transitions WHERE transition_ref = ?", (active_ref,)
                ).fetchone()
                if active is None or active["state"] != "ACTIVE":
                    raise DurableWorkError("active transition binding differs")
                same = (
                    active["kind"] == kind
                    and active["semantic_input_sha256"] == semantic_digest
                    and bytes(active["semantic_input_json"]) == semantic_json
                )
                return TransitionDecision(
                    TransitionDisposition.REENTER if same else TransitionDisposition.BUSY,
                    active_ref,
                )
            completed = connection.execute(
                """SELECT * FROM transitions
                   WHERE work = ? AND kind = ? AND state = 'CLOSED'
                     AND result_ref = ? AND semantic_input_sha256 = ?
                     AND semantic_input_json = ?
                   ORDER BY rowid DESC LIMIT 1""",
                (exact_work, kind, stream["head_result_ref"], semantic_digest, semantic_json),
            ).fetchone()
            if completed is not None and completed["result_ref"] is not None:
                completed_result = self._read_result_locked(connection, completed["result_ref"])
                if not (
                    isinstance(completed_result, VerificationResult)
                    and completed_result.status is VerificationStatus.UNDETERMINED
                ):
                    return TransitionDecision(
                        TransitionDisposition.COMPLETED,
                        completed["transition_ref"],
                        completed_result,
                    )
            transition_ref = f"transition:{uuid.uuid4().hex}"
            connection.execute(
                """INSERT INTO transitions(
                       transition_ref, work, kind, expected_head_ref,
                       semantic_input_json, semantic_input_sha256, progress_ref, state
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE')""",
                (
                    transition_ref,
                    exact_work,
                    kind,
                    stream["head_result_ref"],
                    semantic_json,
                    semantic_digest,
                    progress_ref,
                ),
            )
            updated = connection.execute(
                """UPDATE work_streams SET active_transition_ref = ?
                   WHERE work = ? AND active_transition_ref IS NULL""",
                (transition_ref, exact_work),
            )
            if updated.rowcount != 1:
                raise DurableWorkError("active transition changed during begin")
            return TransitionDecision(TransitionDisposition.STARTED, transition_ref)

    def publish(
        self,
        transition_ref: str,
        result: Candidate | VerificationResult,
        *,
        private_state: object | None = None,
    ) -> Candidate | VerificationResult:
        with self._transaction() as connection:
            transition = connection.execute(
                "SELECT * FROM transitions WHERE transition_ref = ?", (transition_ref,)
            ).fetchone()
            if transition is None:
                raise DurableWorkError("transition is absent")
            if transition["state"] == "CLOSED":
                if transition["result_ref"] is None:
                    raise DurableWorkError("transition closed without a public result")
                return self._read_result_locked(connection, transition["result_ref"])
            stream = connection.execute(
                "SELECT * FROM work_streams WHERE work = ?", (transition["work"],)
            ).fetchone()
            if (
                stream is None
                or stream["active_transition_ref"] != transition_ref
                or stream["head_result_ref"] != transition["expected_head_ref"]
            ):
                raise DurableWorkError("transition no longer owns the expected work head")
            result_work = result.work if isinstance(result, Candidate) else result.candidate.work
            if result_work != Path(transition["work"]):
                raise DurableWorkError("result differs from transition work")
            if isinstance(result, Candidate):
                if transition["kind"] != "IMPLEMENT":
                    raise DurableWorkError("Candidate requires an IMPLEMENT transition")
                kind = "CANDIDATE"
                candidate_ref = None
                payload = self._candidate_payload(result)
            else:
                if transition["kind"] != "VERIFY" or result.candidate.result_identity is None:
                    raise DurableWorkError("VerificationResult requires a durable Candidate")
                durable_candidate = self._read_result_locked(
                    connection,
                    result.candidate.result_identity,
                )
                if not isinstance(durable_candidate, Candidate) or durable_candidate != result.candidate:
                    raise DurableWorkError("VerificationResult candidate is not durable for this work")
                kind = "VERIFICATION"
                candidate_ref = result.candidate.result_identity
                payload = self._verification_payload(result)
            result_ref = f"result:{uuid.uuid4().hex}"
            encoded = _encode(payload)
            connection.execute(
                """INSERT INTO results(
                       result_ref, work, kind, predecessor_ref, candidate_ref,
                       payload_json, payload_sha256
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    result_ref,
                    transition["work"],
                    kind,
                    transition["expected_head_ref"],
                    candidate_ref,
                    encoded,
                    hashlib.sha256(encoded).hexdigest(),
                ),
            )
            if private_state is None:
                private_state = {
                    "unresolvedObservations": [],
                    "resolvedObservationIdentities": [],
                    "effectSafetyProjections": [],
                }
            private_encoded = _encode(private_state)
            decoded_private = _decode(private_encoded)
            if (
                not isinstance(decoded_private, dict)
                or set(decoded_private)
                != {
                    "unresolvedObservations",
                    "resolvedObservationIdentities",
                    "effectSafetyProjections",
                }
                or not isinstance(decoded_private["unresolvedObservations"], list)
                or not isinstance(decoded_private["resolvedObservationIdentities"], list)
                or not isinstance(decoded_private["effectSafetyProjections"], list)
            ):
                raise DurableWorkError("result private state is malformed")
            connection.execute(
                """INSERT INTO result_private_state(result_ref, payload_json, payload_sha256)
                   VALUES (?, ?, ?)""",
                (
                    result_ref,
                    private_encoded,
                    hashlib.sha256(private_encoded).hexdigest(),
                ),
            )
            connection.execute(
                "DELETE FROM mutation_occupancy WHERE transition_ref = ?", (transition_ref,)
            )
            closed = connection.execute(
                """UPDATE transitions SET state = 'CLOSED', result_ref = ?
                   WHERE transition_ref = ? AND state = 'ACTIVE'""",
                (result_ref, transition_ref),
            )
            advanced = connection.execute(
                """UPDATE work_streams
                   SET head_result_ref = ?, active_transition_ref = NULL
                   WHERE work = ? AND head_result_ref IS ? AND active_transition_ref = ?""",
                (
                    result_ref,
                    transition["work"],
                    transition["expected_head_ref"],
                    transition_ref,
                ),
            )
            if closed.rowcount != 1 or advanced.rowcount != 1:
                raise DurableWorkError("atomic result publication conflict")
            return self._read_result_locked(connection, result_ref)

    def close_without_result(self, transition_ref: str) -> None:
        with self._transaction() as connection:
            transition = connection.execute(
                "SELECT * FROM transitions WHERE transition_ref = ?", (transition_ref,)
            ).fetchone()
            if transition is None:
                raise DurableWorkError("transition is absent")
            if transition["state"] == "CLOSED":
                return
            connection.execute(
                "DELETE FROM mutation_occupancy WHERE transition_ref = ?", (transition_ref,)
            )
            closed = connection.execute(
                """UPDATE transitions
                   SET state = 'CLOSED', closed_without_result = 1
                   WHERE transition_ref = ? AND state = 'ACTIVE'""",
                (transition_ref,),
            )
            released = connection.execute(
                """UPDATE work_streams SET active_transition_ref = NULL
                   WHERE work = ? AND active_transition_ref = ?""",
                (transition["work"], transition_ref),
            )
            if closed.rowcount != 1 or released.rowcount != 1:
                raise DurableWorkError("atomic transition closure conflict")

    def occupy_mutation_domain(
        self,
        transition_ref: str,
        project_root: str | Path,
        expected_source: object,
        observe_source: Callable[[Path], object],
    ) -> OccupancyDecision:
        domain_root = _canonical_domain(project_root)
        with self._transaction() as connection:
            transition = connection.execute(
                "SELECT * FROM transitions WHERE transition_ref = ?", (transition_ref,)
            ).fetchone()
            if transition is None or transition["state"] != "ACTIVE" or transition["kind"] != "IMPLEMENT":
                raise DurableWorkError("mutation occupancy requires an active IMPLEMENT transition")
            stream = connection.execute(
                "SELECT active_transition_ref FROM work_streams WHERE work = ?",
                (transition["work"],),
            ).fetchone()
            if stream is None or stream["active_transition_ref"] != transition_ref:
                raise DurableWorkError("transition does not own its work stream")
            existing = connection.execute(
                "SELECT domain_root FROM mutation_occupancy WHERE transition_ref = ?",
                (transition_ref,),
            ).fetchone()
            if existing is not None and existing["domain_root"] != domain_root:
                raise DurableWorkError("transition already occupies another mutation domain")
            if existing is None:
                occupied = connection.execute(
                    "SELECT transition_ref, domain_root FROM mutation_occupancy"
                ).fetchall()
                if any(_overlaps(domain_root, row["domain_root"]) for row in occupied):
                    return OccupancyDecision(False, None)
                connection.execute(
                    "INSERT INTO mutation_occupancy(transition_ref, domain_root) VALUES (?, ?)",
                    (transition_ref, domain_root),
                )
            observed = observe_source(Path(domain_root))
            return OccupancyDecision(True, observed == expected_source, observed)

    def transition_state(self, transition_ref: str) -> dict[str, object] | None:
        connection = self._connect_read_only()
        if connection is None:
            return None
        try:
            row = connection.execute(
                "SELECT * FROM transitions WHERE transition_ref = ?", (transition_ref,)
            ).fetchone()
            if row is None:
                return None
            occupancy = connection.execute(
                "SELECT domain_root FROM mutation_occupancy WHERE transition_ref = ?",
                (transition_ref,),
            ).fetchone()
            return {
                "transitionIdentity": row["transition_ref"],
                "state": row["state"],
                "resultIdentity": row["result_ref"],
                "mutationDomain": None if occupancy is None else occupancy["domain_root"],
            }
        finally:
            connection.close()

    def inspect(
        self,
        work: str | Path,
        observe_currentness: Callable[[PublicResult], Currentness] | None = None,
    ) -> Inspection:
        exact_work = _canonical_work(work)
        connection = self._connect_read_only()
        if connection is None:
            return Inspection(
                NoConclusiveResult(Path(exact_work), "no complete result"),
                Currentness.UNKNOWN,
            )
        try:
            connection.execute("BEGIN")
            stream = connection.execute(
                "SELECT head_result_ref FROM work_streams WHERE work = ?", (exact_work,)
            ).fetchone()
            if stream is None or stream["head_result_ref"] is None:
                result: PublicResult = NoConclusiveResult(Path(exact_work), "no complete result")
            else:
                self._validate_lineage_locked(connection, exact_work, stream["head_result_ref"])
                result = self._read_result_locked(connection, stream["head_result_ref"])
            connection.commit()
        except (sqlite3.Error, DurableWorkError):
            connection.rollback()
            result = NoConclusiveResult(Path(exact_work), "durable result cannot be verified")
        finally:
            connection.close()
        if isinstance(result, NoConclusiveResult) or observe_currentness is None:
            currentness = Currentness.UNKNOWN
        else:
            try:
                currentness = observe_currentness(result)
            except DurableResultIntegrityError:
                result = NoConclusiveResult(
                    Path(exact_work),
                    "durable result source cannot be verified",
                )
                currentness = Currentness.UNKNOWN
            except Exception:
                currentness = Currentness.UNKNOWN
            if not isinstance(currentness, Currentness):
                currentness = Currentness.UNKNOWN
        return Inspection(result, currentness)
