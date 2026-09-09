# Ready boundary-tools dependency map

## Contract producer and consumer

Product Scope/Behavior/Spec/Ticket remain the approved authority. `ready-ticket-plan` produces a project-local method Plan and an outside-root `iis-plan-review/v1` result from actual independent review. Plan byte pairing does not prove semantic sufficiency.

The actual implementing actor calls `ready_contract check_plan_admission` before the first source mutation and immediately before COMPLETE. Between those checks it uses ordinary host-native tools. No IIS execution/session/assignment state is created.

`ready-ticket-verify` is always exactly one delegated verifier. It captures one immutable outside-root verification binding over current product authority, stable implementation targets, declared scenario-effect paths, and optional method navigation; owns full Flow/AC semantic judgment; and returns one successful strict terminal with readable binding identity and verdict. It does not write Ticket status or mint a portable verdict credential. OMP accepts that exact designated-worker terminal, validates its structured/readable/binding facts, persists it privately, and delivers an opaque `terminal_handle`. The caller submits only that handle to `ready_finalize`.

Adaptive/caller consumers keep preparation COMPLETE, implementation COMPLETE, readable verifier semantic verdict/binding, host terminal provenance, status progression/basis, and actual Ticket status separate. A current `done` string without attributable caller finalization is not completion proof.

## Modules

- `delivery-tools/ready-ticket/src/core.js`: host-neutral public boundary API plus the ordinary Node argv executor used by CLI/tests.
- `authority-binding.js`: canonical Ticket/product/validator bytes and authority digest.
- `plan-binding.js`: exact outside-root independent review, Plan/current-product byte pairing and per-Ticket ADMIT decision.
- `verification-binding.js`: immutable stable-target snapshot, separate scenario-effect paths, optional method navigation, outside-root binding creation/currentness, and private verdict/binding record validation helpers.
- `finalization.js`: host-record consumer, binding/current bundle/protocol gate, exact status-only compare-and-swap, canonical post-validation, and conditional restoration of this call's exact candidate.
- `omp.js`: registers exactly `ready_contract` and `ready_finalize`; resolves the caller/session-bound OMP terminal handle, threads current bundle/protocol identity into finalization, records the exact result through the OMP replay ledger, and installs no global tool-dispatch interception.
- `cli.js`: optional direct `ready_contract` integration for non-OMP testing/diagnostics; protected `ready_finalize` fails because CLI has no OMP terminal authority.
- `index.js`: package exports.

There is no command proxy, general observation ledger, retry latch, worker lease, active-Ticket reservation database, service supervisor, mutation recovery database, pause/release workflow, or persistent execution state in this package.

OMP host modules own the narrow cross-restart provenance boundary: `task/authority-profile.ts` fixes the verifier prompt/schema/topology, `task/ready-verifier-terminal.ts` validates and privately persists accepted terminals plus exact finalization results, and the Task tool attaches the opaque handle only after a clean strict result. This is terminal/finalization idempotency state, not IIS execution/session/assignment state.

## Host and release boundary

The immutable `ready-boundary-tools` release contains the boundary package, producer/consumer Skills and canonical validator. `bundle.json` supplies protocol/family/bundle identity; boundary-enabled host stages receive exact `IIS_READY_VALIDATOR_PATH` and `IIS_READY_BUNDLE_ID`. There is no IIS runtime-data root for the new family.

Candidate packaging rejects retired delivery payloads and scans all payload roots for retired delivery dependencies. An installed older protocol-2 release is validated against its own manifest/signature rather than the new candidate file set.

When an installation still manages the previous delivery extension, old-to-new activation requires an exact retired runtime root. A read-only retirement scan distinguishes terminal history, evidence-backed stale records and blockers. Live or unattributed workers/processes/services/effects block activation. Accepted old state bytes are copied into the activation snapshot before host links switch; rollback restores the previous release/link identity.

Historical `baseline.md`, dated 2026-09-05 preparation/roadmap records and Click feature-selection notes describe earlier implementations and are not evidence for the current boundary-tools protocol.
