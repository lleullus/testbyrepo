-- Migration v3 -> v4: Strict Structural Baseline Precondition and Dialogue Authority

-- 1. Install trigger preventing baseline-less cut_intents insertion
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

-- 2. Advance schema version to 4
PRAGMA user_version = 4;
