# Current IIS verification boundaries

The dated records beside this file are historical. Current IIS uses ordinary tools and independent role invocations; no custom host profile, Scope plugin or dedicated execution CLI is required.

## Source and utility verification

From the repository root:

```text
python3 -B -m unittest discover -s tests
PYTHONPATH=observatory/src python3 -B -m unittest discover -s observatory/tests
python3 -B scope-shaper/tools/validate_scope.py /absolute/project/docs/planning/work/example/SCOPE.md --json
```

The tests cover standalone document checks, retained offline evaluation utilities and skill installation. Installer behavior includes immutable payload inspection without loading a client, current v3-to-v4 migration, Scope extension retirement, unrelated user-entry/history preservation, rollback, and refusal to overwrite intervening changes. Migration fixtures do not prove product acceptance or a real verifier's independence.

Use the existing prepare/inspect commands with a disposable store to verify packaging. Exercise activate/rollback/remove only against disposable client roots unless operating changes are explicitly authorized. Observe the actual linked skill bytes, absent retired extension, preserved unrelated entries and restored previous state. No Node execution runtime is part of the new payload.

## Semantic verification and completion

A real product result requires its actual independent verifier invocation and discriminating observations of every authored Scope Acceptance obligation. Preserve exact originals, relevant file-set/runtime identities, scenario-effect boundaries, primary evidence, settlement and the unchanged verdict. Neither test counts nor structural validation nor a matching report label establishes semantic success.

After `VERIFIED`, Main obtains an independent read-only Coverage result. Main checks result attribution, no unresolved material gaps, current original/target identities and settled effects. Main then changes only the Scope's ready-to-done status through ordinary file tools and reads it back. A failed, inconclusive, missing or stale result does not permit recording completion. The procedure does not claim host-enforced authentication, atomic locking or exclusive filesystem authority.

Ordinary settled command failure remains a command result, not a workflow lock. Unknown external/non-idempotent effects require authoritative settlement/readback rather than blind replay. Cancellation receipts do not establish worker or effect settlement.

## Operating activation

Source tests and disposable installation do not prove operating installation or an existing session's loaded identity. Operating activation requires current authorization, settled affected work and exact link/readback checks. Existing sessions are not restarted by the installer. Restoration of historical client-dependent releases also requires their matching host source; the installer never restores product or external effects.
