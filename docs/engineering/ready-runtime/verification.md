# Ready runtime v2 verification boundary

This is the candidate verification plan and evidence boundary. The prior runtime's historical pass counts do not validate this redesign. Runtime tests were rewritten during parallel implementation; no formatter/linter/build/test was run by the runtime worker in that phase. Integration Main owns execution and final acceptance.

## Deterministic behavior

From `delivery-runtime/ready-ticket-implement`, run `node --test tests/*.test.js`.

- `runtime-core.test.js`: missing plan rejection before reservation, actual first file/CLI change, one-use assignment, old-owner late operations, plan drift/resume fence, uncertain effect retention, reservation interruption→attributed cleanup→new admission with late commit rejection, v1 rejection and no old-live-lock theft.
- `plan-binding.test.js`: wrong Ticket, REVISE, stale actual plan/review bytes, inside-root review rejection, recheck at assignment consumption. Fixture ADMIT JSON is byte-pairing input, never independent semantic review proof.
- `authority-service.test.js`: product authority versus ordinary code, product/context manifest separation and undeclared file drift, plan-free verification and delegated PRE_RUNTIME.
- `omp-adapter.test.js`: real host initialization order and host-provided schema boundary; reading/inspection does not arm; guarded file change; unknown native/device and paused effect denial; current-owner checklist closure without late product dispatch; real loopback timeout, report-only recovery and replay exclusion; native/device nested service callbacks with one exact reservation. Synthetic daemon events establish policy behavior only, not host settlement equivalence.
- `finalization.test.js` and `finalization-storage.test.js`: real canonical validator/status-only transition, DIRECT without parent checkpoint versus delegated release, unrelated bytes/mode preservation, post-validator failure with conditional restoration, external-write preservation, persisted candidate recovery, source-drift failure and durable terminal/index cleanup interruptions.

A direct Node consumer must import the core with no OMP environment/config/module, supply structured execution, inspect authority, and exercise admission/actual output/closure. No complete alternate-client adapter is claimed by that smoke.

## Real host checks required

Use a fresh isolated top-level OMP loaded from the coherent candidate bundle, not a child of an already cached old host. Inspect registered schemas and loaded module/bundle identity. Exercise native and supported device action paths, exact parent versus worker, superseded late dispatch, structured argv literal arguments, normal/nonzero/killed/abort/timeout/full output and loopback external readback. Code 0 plus killed is interrupted, not success. Local file hash equality is never evidence of absent external effect.

For services, observe native hub start readiness timeout retaining a live handle, explicit logs/wait/stop, owner and id/startedAt/restartCount generation, and wrong same-name generation rejection. Explicit cleanup must precede terminal/suspend/replacement. Root process exit or cancellation receipt is not broad escaped-descendant/external-effect settlement. Hub's name-only stop and host result fidelity remain capability limits; do not reinstate a Ready raw supervisor to hide them.

Inject finalization failures before write, during replacement/postvalidate/durable terminal/index cleanup, and across restart. No failure may fabricate COMPLETED from done bytes. Current foreign bytes/authority must prevent rollback. An orphan reservation is released only by the current designated owner's exact attributed evidence, absence of execution/assignment, and locked identity match. No age-based orphan auto-expiry or blind admission replay is allowed.

## Integration and historical evidence

The integrating owner runs `python3 run_tests.py` once after fan-in and owns candidate installer/evaluation smoke. Actual author/reviewer and final-verifier traces must adjudicate semantic V1–V6/V10–V13 separately from structural JSON tests. Product planning-only, preparation-only, implementation-only, verification-only and full delivery retain distinct terminals and obligation denominators.

Earlier v1 reports and Click selection documents remain historical. They do not imply v2 test success, production installation, an active host migration, or support for every custom/MCP/browser/program effect surface.
