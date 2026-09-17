-- comic-new v7 schema: dynamic active cuts with stable identity and ordered membership

CREATE TABLE authority (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    authority_revision INTEGER NOT NULL CHECK (authority_revision >= 0),
    current_baseline_id TEXT NULL REFERENCES structural_baselines(baseline_id)
);

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
    CHECK (
        (is_active = 1 AND display_order IS NOT NULL) OR
        (is_active = 0 AND display_order IS NULL)
    ),
    CHECK (
        (realized_revision IS NULL AND realized_asset_id IS NULL AND realized_asset_path IS NULL AND realized_content_hash IS NULL) OR
        (realized_revision IS NOT NULL AND realized_asset_id IS NOT NULL AND realized_asset_path IS NOT NULL AND realized_content_hash IS NOT NULL)
    ),
    FOREIGN KEY (cut_id, desired_revision) REFERENCES cut_intents(cut_id, revision)
);

CREATE TABLE baseline_intents (
    baseline_id TEXT NOT NULL REFERENCES structural_baselines(baseline_id) ON DELETE CASCADE,
    cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id >= 1),
    intent_revision INTEGER NOT NULL CHECK (intent_revision > 0),
    PRIMARY KEY (baseline_id, cut_id),
    FOREIGN KEY (cut_id, intent_revision) REFERENCES cut_intents(cut_id, revision)
);

CREATE TABLE composition (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    revision INTEGER NOT NULL CHECK (revision >= 0),
    state_json TEXT NOT NULL CHECK (json_valid(state_json)),
    updated_at TEXT NOT NULL
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

CREATE INDEX idx_generation_jobs_queued
ON generation_jobs (status, created_at, job_id);

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
);

CREATE TABLE generation_control (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    stop_epoch INTEGER NOT NULL DEFAULT 0 CHECK (stop_epoch >= 0),
    runner_id TEXT NULL,
    runner_pid INTEGER NULL,
    runner_start_token TEXT NULL,
    runner_started_at TEXT NULL,
    CHECK (
        (runner_id IS NULL AND runner_pid IS NULL AND runner_start_token IS NULL AND runner_started_at IS NULL) OR
        (runner_id IS NOT NULL AND runner_pid IS NOT NULL AND runner_start_token IS NOT NULL AND runner_started_at IS NOT NULL)
    )
);

CREATE TABLE review_artifacts (
    artifact_id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    composition_revision INTEGER NOT NULL CHECK (composition_revision >= 0),
    created_at TEXT NOT NULL
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

CREATE TABLE release_authorizations (
    authorization_id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL REFERENCES review_artifacts(artifact_id),
    artifact_content_hash TEXT NOT NULL,
    authorized_authority_revision INTEGER NOT NULL CHECK (authorized_authority_revision >= 0),
    revoked_authority_revision INTEGER NULL CHECK (revoked_authority_revision IS NULL OR revoked_authority_revision >= 0),
    created_at TEXT NOT NULL,
    revoked_at TEXT NULL
);

CREATE UNIQUE INDEX idx_active_release_authorization
ON release_authorizations ((1))
WHERE revoked_authority_revision IS NULL;

CREATE UNIQUE INDEX idx_active_cut_display_order
ON cuts (display_order)
WHERE is_active = 1;

CREATE TABLE delivery_attempts (
    attempt_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('png', 'blogger')),
    authorization_id TEXT NOT NULL REFERENCES release_authorizations(authorization_id),
    artifact_id TEXT NOT NULL REFERENCES review_artifacts(artifact_id),
    request_id TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('unknown', 'confirmed_success', 'confirmed_failure')),
    destination_id TEXT NULL,
    destination_url TEXT NULL,
    evidence_json TEXT NULL CHECK (evidence_json IS NULL OR json_valid(evidence_json)),
    observed_authority_revision INTEGER NULL CHECK (observed_authority_revision IS NULL OR observed_authority_revision >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (
        outcome != 'confirmed_success' OR (
            destination_id IS NOT NULL AND
            destination_url IS NOT NULL AND
            evidence_json IS NOT NULL
        )
    )
);

-- Seed initial singleton rows. Dynamic cut rows are inserted atomically by create_project().
INSERT INTO authority (singleton_id, authority_revision, current_baseline_id)
VALUES (1, 0, NULL);

INSERT INTO composition (singleton_id, revision, state_json, updated_at)
VALUES (1, 0, '{}', '2026-09-15T00:00:00Z');

INSERT INTO generation_control (singleton_id, stop_epoch, runner_id, runner_pid, runner_start_token, runner_started_at)
VALUES (1, 0, NULL, NULL, NULL, NULL);

-- Stable identity/history guards. Active membership and display order are mutable by store transactions.
CREATE TRIGGER trg_cuts_no_delete BEFORE DELETE ON cuts
BEGIN
    SELECT RAISE(ABORT, 'cut history is immutable; retire cuts instead');
END;

CREATE TRIGGER trg_cuts_no_update_cut_id BEFORE UPDATE OF cut_id ON cuts
BEGIN
    SELECT RAISE(ABORT, 'cut_id identity is immutable');
END;

CREATE TRIGGER trg_cuts_keep_one_active BEFORE UPDATE OF is_active ON cuts
WHEN OLD.is_active = 1 AND NEW.is_active = 0
 AND (SELECT COUNT(*) FROM cuts WHERE is_active = 1) <= 1
BEGIN
    SELECT RAISE(ABORT, 'at least one active cut is required');
END;

-- Baseline precondition trigger: cut_intents insert requires active baseline
CREATE TRIGGER trg_cut_intents_active_baseline BEFORE INSERT ON cut_intents
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.baseline_id IS NULL
          OR (SELECT current_baseline_id FROM authority WHERE singleton_id = 1) IS NULL
          OR NEW.baseline_id != (SELECT current_baseline_id FROM authority WHERE singleton_id = 1)
        THEN RAISE(ABORT, 'cut_intents insert requires active baseline')
    END;
END;
