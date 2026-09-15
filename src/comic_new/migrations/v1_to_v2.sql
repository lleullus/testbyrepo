-- Migration v1 -> v2: Add generation_control and process identity columns

CREATE TABLE IF NOT EXISTS generation_control (
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

INSERT OR IGNORE INTO generation_control (singleton_id, stop_epoch, runner_id, runner_pid, runner_start_token, runner_started_at)
VALUES (1, 0, NULL, NULL, NULL, NULL);

ALTER TABLE generation_attempts ADD COLUMN runner_id TEXT NULL;
ALTER TABLE generation_attempts ADD COLUMN process_pid INTEGER NULL;
ALTER TABLE generation_attempts ADD COLUMN process_group_id INTEGER NULL;
ALTER TABLE generation_attempts ADD COLUMN process_start_token TEXT NULL;
ALTER TABLE generation_attempts ADD COLUMN staging_path TEXT NULL;
ALTER TABLE generation_attempts ADD COLUMN provider_request_id TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_generation_jobs_queued ON generation_jobs (status, created_at, job_id);

PRAGMA user_version = 2;
