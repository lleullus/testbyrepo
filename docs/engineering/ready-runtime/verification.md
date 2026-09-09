# Ready boundary-tools verification boundary

This document defines current source-side and isolated-candidate verification for the Ready delivery boundary. Dated runtime reports in this directory are historical records and do not establish current boundary-tool behavior or live-host activation.

## Deterministic boundary behavior

From `delivery-tools/ready-ticket`, run `npm test`.

- `authority-plan.test.js`: canonical product authority and exact independent Plan Review admission, including missing/stale/non-admitted review behavior and the fact that ordinary implementation source edits do not by themselves stale an unchanged reviewed Plan.
- `verification-binding.test.js`: immutable outside-root verification bindings, recursive stable-target identity, separately declared scenario-effect paths, stable/effect overlap rejection, protected authority/method effect rejection, and effect mutation that does not invalidate an unchanged stable target.
- `finalization.test.js`: semantic verdict versus status progression separation, exact ready-to-done status-only write, post-write validation and conditional exact restoration, stable/authority drift rejection, diagnostic done capture, and no fresh-completion inference from already-done bytes.
- `omp-tools.test.js`: exactly two registered Ready boundary tools, zero global interception hooks, caller-owned finalization, and the incident regression in which a settled exit status 1 is followed by an ordinary source edit and successful retry.

These tests use the canonical Ticket validator and real files in disposable project roots. Fixture review JSON establishes exact byte pairing only; it is not semantic proof of independent review quality.

## Evaluation and anti-fake boundaries

Run the focused Python contract tests:

```text
python3 -m unittest discover -s tests -p test_ready_agent_capture.py
python3 -m unittest discover -s tests -p test_ready_verification_fixture_boundaries.py
python3 -m unittest discover -s tests -p test_goal_calibration.py
python3 -m unittest discover -s tests -p test_ready_completion_calibration.py
```

Required properties include:

- verifier terminal output may establish a semantic verdict and immutable binding identity, but cannot itself manufacture caller status progression;
- evaluator drift injected after verification capture makes later VERIFIED progression fail while preserving the semantic verdict;
- narration containing VERIFIED/done/completed is not delivery evidence;
- completion requires the same binding path/SHA at semantic terminal and caller finalization, an attributable completion basis, and current canonical done bytes that correspond exactly to the binding's captured ready Ticket with only the status transition.

## Dependency and installer boundaries

Run:

```text
python3 -B scripts/check-ready-boundary-deps.py --root .
python3 -m unittest discover -s tests -p test_ready_ticket_boundary_tools.py
```

The dependency scan covers only candidate payload roots and fails on retired delivery dependencies. Historical documentation and installer migration signatures are not candidate payload dependencies.

The installer contract tests cover:

- candidate `ready-boundary-tools` manifest/self-validation;
- legacy protocol-2 release validation against that release's own manifest/signature rather than the new candidate file set;
- explicit old-extension to new-extension link migration in isolated host roots;
- read-only retired-runtime state classification into terminal history, evidence-backed stale records, and blockers;
- activation rejection before link switching for live, unsettled, or unattributed legacy work/effects;
- immutable archival snapshot of approved retired state;
- rollback to the exact previous release/link identity without rewriting retired state bytes;
- refusal to overwrite intervening user changes.

## Isolated candidate verification

Build a candidate in a disposable release store with `scripts/sync_installed_iis.py prepare`, then run `check` against the returned bundle id. Activation tests, when needed, use only disposable host roots and explicit quiescent confirmation. Inspect the new extension link, the absence of the retired extension, installed family/bundle identity, and rollback/remove behavior.

Candidate preparation and isolated activation do not establish actual loaded identity in a real operating OMP/Codex process. `loaded_identity: NOT_CHECKED` must remain explicit until a separately authorized live-host check is actually performed.

## Host-native execution semantics

Ready boundary tools do not proxy ordinary shell/argv execution or globally intercept host tools. Therefore command failure/retry coverage focuses on observable host semantics:

- settled nonzero result is an ordinary command failure, not a workflow lock;
- the implementing actor may inspect, edit within the admitted Plan, and rerun immediately;
- interruption/timeout/response loss is distinguished from settled nonzero;
- a real non-idempotent/external effect with lost response is never blindly replayed and must use its authored authoritative readback/cleanup path.

Service/process settlement and worker replacement remain host/caller lifecycle responsibilities. A cancellation receipt alone is not settlement evidence.

## Operating activation boundary

Do not infer production readiness from source tests, an immutable candidate bundle, isolated host-root activation, or fixture settlement evidence. Actual operating activation is a separate change requiring explicit authorization, a current cutover scan of the real retired runtime root when applicable, host quiescence/settlement evidence, and post-activation loaded-identity/readback checks. Rollback restores the previous release/link identity; it does not attempt to recreate retired runtime semantics in the new family.
