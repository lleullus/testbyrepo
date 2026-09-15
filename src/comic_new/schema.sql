-- comic-new v1 schema: Single Transactional Authority

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
    cut_id INTEGER NOT NULL CHECK (cut_id BETWEEN 1 AND 5),
    revision INTEGER NOT NULL CHECK (revision > 0),
    baseline_id TEXT NULL REFERENCES structural_baselines(baseline_id),
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
    authority_revision INTEGER NOT NULL CHECK (authority_revision >= 0),
    created_at TEXT NOT NULL,
    PRIMARY KEY (cut_id, revision)
);

CREATE TABLE cuts (
    cut_id INTEGER PRIMARY KEY CHECK (cut_id BETWEEN 1 AND 5),
    desired_revision INTEGER NULL CHECK (desired_revision IS NULL OR desired_revision > 0),
    realized_revision INTEGER NULL CHECK (realized_revision IS NULL OR realized_revision > 0),
    realized_asset_id TEXT NULL,
    realized_asset_path TEXT NULL,
    realized_content_hash TEXT NULL,
    CHECK (
        (realized_revision IS NULL AND realized_asset_id IS NULL AND realized_asset_path IS NULL AND realized_content_hash IS NULL) OR
        (realized_revision IS NOT NULL AND realized_asset_id IS NOT NULL AND realized_asset_path IS NOT NULL AND realized_content_hash IS NOT NULL)
    ),
    FOREIGN KEY (cut_id, desired_revision) REFERENCES cut_intents(cut_id, revision)
);

CREATE TABLE baseline_intents (
    baseline_id TEXT NOT NULL REFERENCES structural_baselines(baseline_id) ON DELETE CASCADE,
    cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id BETWEEN 1 AND 5),
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
    cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id BETWEEN 1 AND 5),
    target_desired_revision INTEGER NOT NULL CHECK (target_desired_revision > 0),
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
    UNIQUE (job_id, ordinal)
);

CREATE TABLE review_artifacts (
    artifact_id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    composition_revision INTEGER NOT NULL CHECK (composition_revision >= 0),
    created_at TEXT NOT NULL
);

CREATE TABLE artifact_cuts (
    artifact_id TEXT NOT NULL REFERENCES review_artifacts(artifact_id) ON DELETE CASCADE,
    cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id BETWEEN 1 AND 5),
    realized_revision INTEGER NOT NULL CHECK (realized_revision > 0),
    asset_id TEXT NOT NULL,
    PRIMARY KEY (artifact_id, cut_id)
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

-- Seed initial singleton and cuts rows
INSERT INTO authority (singleton_id, authority_revision, current_baseline_id)
VALUES (1, 0, NULL);

INSERT INTO composition (singleton_id, revision, state_json, updated_at)
VALUES (1, 0, '{}', '2026-09-15T00:00:00Z');

INSERT INTO cuts (cut_id) VALUES (1), (2), (3), (4), (5);

-- Exactly five cuts triggers: protect table cuts from row insertion, deletion, and cut_id changes
CREATE TRIGGER trg_cuts_no_insert BEFORE INSERT ON cuts
BEGIN
    SELECT RAISE(ABORT, 'exactly five cuts are immutable');
END;

CREATE TRIGGER trg_cuts_no_delete BEFORE DELETE ON cuts
BEGIN
    SELECT RAISE(ABORT, 'exactly five cuts are immutable');
END;

CREATE TRIGGER trg_cuts_no_update_cut_id BEFORE UPDATE OF cut_id ON cuts
BEGIN
    SELECT RAISE(ABORT, 'exactly five cuts are immutable');
END;
