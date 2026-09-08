# Ready runtime v2 dependency map

## Contract producer and consumer

Product Scope/Behavior/Spec/Ticket remain the approved authority. `ready-ticket-plan` produces a project-local method plan and an outside-root `iis-plan-review/v1` result from actual independent review. Runtime implementation admission consumes its exact current Ticket ADMIT; plan byte pairing does not prove semantic sufficiency. `ready-ticket-verify` directly binds the actual product and owns full Flow/AC judgment plus integrated heuristic exploration. No separate post-implementation Probe artifact or lifecycle is consumed.

`ready_guard inspect_authority` is a read-only producer of canonical flat authority identity; it does not require or create implementation admission. Implementation admission starts ACTIVE after current review. Checkpoints are PRE_RUNTIME, MATERIAL_TURN and PRE_PROGRESSION; the product ready/done status vocabulary is unchanged. Adaptive/caller consumers distinguish preparation COMPLETE, implementation COMPLETE, semantic VERIFIED, progression COMPLETED/FAILED, and actual Ticket status.

## Modules

- `src/core.js`: host-neutral exports; no OMP loader/config/session dependencies.
- `authority-binding.js`: canonical product/validator bytes and digest. Explicit validator or same-bundle relative validator; no client-home/workflow-route discovery.
- `plan-binding.js`: exact outside-root review, plan/current product byte pairing and per-Ticket decision.
- `verification-target.js`: async injected Git inventory, product manifest versus exact method context. Explicit product targets override context.
- `state-store.js`: schema v2 execution/session/assignment/active-Ticket records, sync lock, atomic durable JSON replacement. No age-based live-lock stealing or legacy conversion.
- `lifecycle.js`: common admission, reservation-first one-use ownership, parent/worker fences, pause/currentness, effect uncertainty, native service handle, explicit orphan recovery and terminal closure.
- `finalization.js`: exact status-only candidate/CAS/canonical post-validation and conditional recovery intent.
- `argv-policy.js`: structured argv and bounded read-only grammar only; no spawn/timers/output collection.
- `tool-map.js`: adapter-only builtin provenance.
- `omp-adapter.js`: OMP identity, native/device normalization, event fence, Zod tool schema, `pi.exec` results and native `hub details.daemon` attribution.
- `index.js`: OMP loader. Package `.` resolves core; `./omp` resolves loader.

Removed policies have no substitute ledger: general observation history, inventory quota, retry latch, mutation-evidence revision latch, standalone Probe binding, and raw process/service supervision.

## Host and release boundary

The immutable complete release contains runtime, producer Skills and canonical validators. Installer manifest `bundle.json` supplies protocol 2/bundle identity; the adapter also accepts `IIS_READY_VALIDATOR_PATH` and `IIS_READY_BUNDLE_ID`. Neutral state is separate from installed code. Installer/evaluation are independent writer-owned integration surfaces, not implemented by the runtime.

The adapter uses actual OMP `registerTool`, `getAllTools().sourceInfo`, `tool_call`, `tool_result`, resource/session events, `sessionManager.getSessionId()`, structured `pi.exec`, and builtin hub process result fields. Native host exec loses some termination distinctions; killed/interrupted must dominate code. Hub has name-based control, so exact UUID-name/generation checks are a cooperative boundary, not an OS-wide service lock. Unknown effects stop with CAPABILITY_UNAVAILABLE instead of silently becoming read-only.

Historical `baseline.md`, dated verification reports and Click feature selection describe the older runtime; they are not evidence for v2 behavior.
