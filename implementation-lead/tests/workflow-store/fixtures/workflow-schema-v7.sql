BEGIN TRANSACTION;
CREATE TABLE actors (
                    actor_ref TEXT PRIMARY KEY,
                    role TEXT NOT NULL CHECK (role IN ('COORDINATOR', 'ASSESSOR', 'REMEDIATOR', 'WORKER')),
                    root_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    invocation_ref TEXT NOT NULL REFERENCES invocations(invocation_ref),
                    capability_sha256 TEXT NOT NULL UNIQUE,
                    bound_claim_ref TEXT UNIQUE,
                    created_at TEXT NOT NULL
                );
CREATE TABLE authorizations (
                    authorization_ref TEXT PRIMARY KEY,
                    invocation_ref TEXT NOT NULL REFERENCES invocations(invocation_ref),
                    scope_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
CREATE TABLE budget_reservations (
                    reservation_ref TEXT PRIMARY KEY,
                    invocation_ref TEXT NOT NULL REFERENCES invocations(invocation_ref),
                    transition_kind TEXT NOT NULL CHECK (transition_kind IN ('VERIFY', 'REMEDIATE')),
                    spend_reserved_json BLOB NOT NULL,
                    closure_reserved_json BLOB NOT NULL,
                    spend_used_json BLOB NOT NULL,
                    closure_used_json BLOB NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('ACTIVE', 'CLOSED')),
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );
CREATE TABLE claims (
                    claim_ref TEXT PRIMARY KEY,
                    root_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    tip_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    transition_kind TEXT NOT NULL CHECK (transition_kind IN ('VERIFY', 'REMEDIATE')),
                    coordinator_actor_ref TEXT NOT NULL REFERENCES actors(actor_ref),
                    claimant_actor_ref TEXT NOT NULL UNIQUE REFERENCES actors(actor_ref),
                    planning_identity TEXT NOT NULL,
                    source_identity TEXT NOT NULL,
                    execution_ref TEXT NOT NULL UNIQUE,
                    budget_reservation_ref TEXT NOT NULL UNIQUE REFERENCES budget_reservations(reservation_ref),
                    state TEXT NOT NULL CHECK (state IN ('ACTIVE', 'CONSUMED', 'RELEASED')),
                    successor_ref TEXT REFERENCES nodes(node_ref),
                    closure_ref TEXT,
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );
CREATE TABLE edges (
                    predecessor_ref TEXT PRIMARY KEY REFERENCES nodes(node_ref),
                    successor_ref TEXT NOT NULL UNIQUE REFERENCES nodes(node_ref),
                    transition_kind TEXT NOT NULL CHECK (transition_kind IN ('VERIFY', 'REMEDIATE')),
                    claim_ref TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );
CREATE TABLE implementation_checks (
                    check_ref TEXT PRIMARY KEY,
                    transaction_ref TEXT NOT NULL REFERENCES implementation_transactions(transaction_ref),
                    request_json BLOB NOT NULL,
                    request_sha256 TEXT NOT NULL,
                    result_json BLOB NOT NULL,
                    result_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
CREATE TABLE implementation_deltas (
                    delta_ref TEXT PRIMARY KEY,
                    transaction_ref TEXT NOT NULL UNIQUE REFERENCES implementation_transactions(transaction_ref),
                    payload_json BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
CREATE TABLE implementation_envelopes (
                    envelope_ref TEXT PRIMARY KEY,
                    transaction_ref TEXT NOT NULL REFERENCES implementation_transactions(transaction_ref),
                    task_id TEXT NOT NULL,
                    criterion_refs_json BLOB NOT NULL,
                    allowed_paths_json BLOB NOT NULL,
                    forbidden_paths_json BLOB NOT NULL,
                    before_snapshot_json BLOB NOT NULL,
                    before_snapshot_sha256 TEXT NOT NULL,
                    after_snapshot_json BLOB,
                    after_snapshot_sha256 TEXT,
                    delta_json BLOB,
                    reconciliation_json BLOB,
                    state TEXT NOT NULL CHECK (state IN ('FROZEN', 'DISPATCHED', 'CAPTURED', 'RECONCILED')),
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    UNIQUE(transaction_ref, task_id)
                );
CREATE TABLE implementation_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_ref TEXT NOT NULL REFERENCES implementation_transactions(transaction_ref),
                    event_kind TEXT NOT NULL,
                    payload_json BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
CREATE TABLE implementation_transactions (
                    transaction_ref TEXT PRIMARY KEY,
                    mode TEXT NOT NULL CHECK (mode IN ('INITIAL_IMPLEMENTATION', 'VERIFICATION_REMEDIATION')),
                    root_ref TEXT REFERENCES nodes(node_ref),
                    claim_ref TEXT UNIQUE REFERENCES claims(claim_ref),
                    owner_actor_ref TEXT REFERENCES actors(actor_ref),
                    worker_actor_ref TEXT REFERENCES actors(actor_ref),
                    selected_worker TEXT NOT NULL,
                    capability_sha256 TEXT NOT NULL UNIQUE,
                    worker_capability_sha256 TEXT NOT NULL,
                    project_root TEXT NOT NULL,
                    planning_identity TEXT NOT NULL,
                    baseline_capsule_ref TEXT NOT NULL,
                    baseline_source_identity TEXT NOT NULL,
                    admission_json BLOB,
                    state TEXT NOT NULL CHECK (
                        state IN ('OPEN', 'WORKER_ACTIVE', 'RECONCILING', 'READY_FOR_HANDOFF',
                                  'CLOSED_WITH_HANDOFF', 'CLOSED_NO_SUCCESSOR', 'FAILED')
                    ),
                    final_source_identity TEXT,
                    implementation_delta_ref TEXT,
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );
CREATE TABLE invocations (
                    invocation_ref TEXT PRIMARY KEY,
                    root_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    deadline_at TEXT NOT NULL,
                    limits_json BLOB NOT NULL,
                    consumed_json BLOB NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('ACTIVE', 'CLOSED')),
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );
CREATE TABLE nodes (
                    node_ref TEXT PRIMARY KEY,
                    node_kind TEXT NOT NULL CHECK (node_kind IN ('IMPLEMENTATION_HANDOFF', 'VERIFICATION_RESULT')),
                    protocol_version TEXT NOT NULL,
                    root_ref TEXT NOT NULL,
                    planning_identity TEXT NOT NULL,
                    source_identity TEXT NOT NULL,
                    verification_status TEXT,
                    payload_json BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
CREATE TABLE store_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
INSERT INTO "store_meta" VALUES('schema_version','7');
CREATE TABLE verification_artifacts (
                    artifact_ref TEXT PRIMARY KEY,
                    run_ref TEXT NOT NULL REFERENCES verification_runs(run_ref),
                    media_type TEXT NOT NULL,
                    payload BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    byte_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
CREATE TABLE verification_attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_ref TEXT NOT NULL REFERENCES verification_runs(run_ref),
                    flow_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    step_role TEXT NOT NULL CHECK (step_role IN ('ACTION', 'READBACK', 'CLEANUP')),
                    poll_index INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    request_sha256 TEXT NOT NULL,
                    source_identity_before TEXT,
                    source_identity_after TEXT,
                    artifact_ref TEXT,
                    result_json BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(run_ref, flow_id, step_id, poll_index)
                );
CREATE TABLE verification_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_ref TEXT NOT NULL REFERENCES verification_runs(run_ref),
                    event_kind TEXT NOT NULL,
                    payload_json BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
CREATE TABLE verification_runs (
                    run_ref TEXT PRIMARY KEY,
                    root_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    claim_ref TEXT NOT NULL UNIQUE REFERENCES claims(claim_ref),
                    assessor_actor_ref TEXT NOT NULL UNIQUE REFERENCES actors(actor_ref),
                    implementation_handoff_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    project_root TEXT NOT NULL,
                    planning_identity TEXT NOT NULL,
                    source_identity TEXT NOT NULL,
                    preflight_json BLOB NOT NULL,
                    sealed_plan_json BLOB,
                    sealed_plan_sha256 TEXT,
                    state TEXT NOT NULL CHECK (state IN ('PREFLIGHT', 'SEALED', 'CLOSED')),
                    closure_json BLOB,
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );
CREATE TABLE verification_step_executions (
                    run_ref TEXT NOT NULL REFERENCES verification_runs(run_ref),
                    flow_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('STARTED', 'COMPLETED', 'NOT_RUN')),
                    request_sha256 TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    PRIMARY KEY(run_ref, flow_id, step_id)
                );
CREATE UNIQUE INDEX one_active_claim_per_tip
                    ON claims(tip_ref) WHERE state = 'ACTIVE';
CREATE UNIQUE INDEX one_active_claim_per_root
                    ON claims(root_ref) WHERE state = 'ACTIVE';
CREATE TRIGGER nodes_no_update
                BEFORE UPDATE ON nodes BEGIN SELECT RAISE(ABORT, 'immutable nodes'); END;
CREATE TRIGGER nodes_no_delete
                BEFORE DELETE ON nodes BEGIN SELECT RAISE(ABORT, 'immutable nodes'); END;
CREATE TRIGGER edges_no_update
                BEFORE UPDATE ON edges BEGIN SELECT RAISE(ABORT, 'immutable edges'); END;
CREATE TRIGGER edges_no_delete
                BEFORE DELETE ON edges BEGIN SELECT RAISE(ABORT, 'immutable edges'); END;
CREATE TRIGGER implementation_checks_no_update
                BEFORE UPDATE ON implementation_checks BEGIN SELECT RAISE(ABORT, 'immutable implementation checks'); END;
CREATE TRIGGER implementation_checks_no_delete
                BEFORE DELETE ON implementation_checks BEGIN SELECT RAISE(ABORT, 'immutable implementation checks'); END;
CREATE TRIGGER implementation_deltas_no_update
                BEFORE UPDATE ON implementation_deltas BEGIN SELECT RAISE(ABORT, 'immutable implementation deltas'); END;
CREATE TRIGGER implementation_deltas_no_delete
                BEFORE DELETE ON implementation_deltas BEGIN SELECT RAISE(ABORT, 'immutable implementation deltas'); END;
CREATE TRIGGER implementation_events_no_update
                BEFORE UPDATE ON implementation_events BEGIN SELECT RAISE(ABORT, 'immutable implementation events'); END;
CREATE TRIGGER implementation_events_no_delete
                BEFORE DELETE ON implementation_events BEGIN SELECT RAISE(ABORT, 'immutable implementation events'); END;
CREATE TRIGGER authorizations_no_update
                BEFORE UPDATE ON authorizations BEGIN SELECT RAISE(ABORT, 'immutable authorizations'); END;
CREATE TRIGGER authorizations_no_delete
                BEFORE DELETE ON authorizations BEGIN SELECT RAISE(ABORT, 'immutable authorizations'); END;
CREATE TRIGGER verification_attempts_no_update
                BEFORE UPDATE ON verification_attempts BEGIN SELECT RAISE(ABORT, 'immutable verification attempts'); END;
CREATE TRIGGER verification_attempts_no_delete
                BEFORE DELETE ON verification_attempts BEGIN SELECT RAISE(ABORT, 'immutable verification attempts'); END;
CREATE TRIGGER verification_step_executions_no_delete
                BEFORE DELETE ON verification_step_executions BEGIN SELECT RAISE(ABORT, 'immutable verification step executions'); END;
CREATE TRIGGER verification_artifacts_no_update
                BEFORE UPDATE ON verification_artifacts BEGIN SELECT RAISE(ABORT, 'immutable verification artifacts'); END;
CREATE TRIGGER verification_artifacts_no_delete
                BEFORE DELETE ON verification_artifacts BEGIN SELECT RAISE(ABORT, 'immutable verification artifacts'); END;
CREATE TRIGGER verification_events_no_update
                BEFORE UPDATE ON verification_events BEGIN SELECT RAISE(ABORT, 'immutable verification events'); END;
CREATE TRIGGER verification_events_no_delete
                BEFORE DELETE ON verification_events BEGIN SELECT RAISE(ABORT, 'immutable verification events'); END;
DELETE FROM "sqlite_sequence";
COMMIT;
