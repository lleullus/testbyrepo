-- Migration v4 -> v5: frozen generation job identity.
--
-- The table rebuild and historical identity backfill are intentionally executed
-- by TransactionalStore in Python so effective_prompt_sha256 is computed from
-- the exact UTF-8 bytes and historical model attribution can be rejected when
-- it is not authoritative. This file is the migration's reviewed marker.
SELECT 1;
