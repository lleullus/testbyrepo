-- Migration v2 -> v3: Add request sequence tracking to cuts and generation_jobs

-- 1. Add latest_generation_request_seq column to cuts table
ALTER TABLE cuts ADD COLUMN latest_generation_request_seq INTEGER NOT NULL DEFAULT 0;

-- 2. Add request_seq column to generation_jobs table with temporary default 0
ALTER TABLE generation_jobs ADD COLUMN request_seq INTEGER NOT NULL DEFAULT 0;

-- 3. Deterministically backfill existing generation_jobs.request_seq per cut in (created_at, job_id) order (1..N)
WITH numbered_jobs AS (
    SELECT
        job_id,
        ROW_NUMBER() OVER (
            PARTITION BY cut_id
            ORDER BY created_at ASC, job_id ASC
        ) AS seq
    FROM generation_jobs
)
UPDATE generation_jobs
SET request_seq = (
    SELECT numbered_jobs.seq
    FROM numbered_jobs
    WHERE numbered_jobs.job_id = generation_jobs.job_id
)
WHERE EXISTS (
    SELECT 1
    FROM numbered_jobs
    WHERE numbered_jobs.job_id = generation_jobs.job_id
);

-- 4. Update cuts.latest_generation_request_seq to the maximum backfilled request_seq (or 0 if no jobs exist)
UPDATE cuts
SET latest_generation_request_seq = COALESCE(
    (SELECT MAX(request_seq) FROM generation_jobs WHERE generation_jobs.cut_id = cuts.cut_id),
    0
);

-- 5. Advance schema version to 3
PRAGMA user_version = 3;
