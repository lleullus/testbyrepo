# Ready boundary-tools dependency map

## Contract producer and consumer

Product Scope/Behavior/Spec/Ticket remain the approved authority. `ready-ticket-plan` produces a project-local method Plan and an outside-root `iis-plan-review/v1` result from actual independent review. Plan byte pairing does not prove semantic sufficiency.

The actual implementing actor calls `ready_contract check_plan_admission` before the first source mutation and immediately before COMPLETE. Between those checks it uses ordinary host-native tools. No IIS execution/session/assignment state is created.

`ready-ticket-verify` captures one immutable outside-root verification binding over current product authority, stable implementation targets, declared scenario-effect paths and optional method navigation. It owns full Flow/AC semantic judgment and returns one terminal verdict with the exact binding path/SHA. The verifier does not write Ticket status. The caller separately invokes `ready_finalize` with the unchanged verdict.

Adaptive/caller consumers keep preparation COMPLETE, implementation COMPLETE, semantic verdict, status progression/basis and actual Ticket status separate. A current `done` string without attributable caller finalization is not completion proof.

## Modules

- `delivery-tools/ready-ticket/src/core.js`: host-neutral public boundary API plus the ordinary Node argv executor used by CLI/tests.
- `authority-binding.js`: canonical Ticket/product/validator bytes and authority digest.
- `plan-binding.js`: exact outside-root independent review, Plan/current-product byte pairing and per-Ticket ADMIT decision.
- `verification-binding.js`: immutable stable-target snapshot, separate scenario-effect paths, optional method navigation and outside-root binding creation/currentness.
- `finalization.js`: semantic-verdict consumer, exact status-only compare-and-swap, canonical post-validation and conditional restoration of this call's exact candidate.
- `omp.js`: registers exactly `ready_contract` and `ready_finalize`; it does not install global dispatch hooks.
- `cli.js`: optional direct host integration using the same boundary functions.
- `index.js`: package exports.

There is no command proxy, general observation ledger, retry latch, worker lease, active-Ticket reservation database, service supervisor, mutation recovery database, pause/release workflow, or persistent execution state in this package.

## Host and release boundary

The immutable `ready-boundary-tools` release contains the boundary package, producer/consumer Skills and canonical validator. `bundle.json` supplies protocol/family/bundle identity; boundary-enabled host stages receive exact `IIS_READY_VALIDATOR_PATH` and `IIS_READY_BUNDLE_ID`. There is no IIS runtime-data root for the new family.

Candidate packaging rejects retired delivery payloads and scans all payload roots for retired delivery dependencies. An installed older protocol-2 release is validated against its own manifest/signature rather than the new candidate file set.

When an installation still manages the previous delivery extension, old-to-new activation requires an exact retired runtime root. A read-only retirement scan distinguishes terminal history, evidence-backed stale records and blockers. Live or unattributed workers/processes/services/effects block activation. Accepted old state bytes are copied into the activation snapshot before host links switch; rollback restores the previous release/link identity.

Historical `baseline.md`, dated 2026-09-05 preparation/roadmap records and Click feature-selection notes describe earlier implementations and are not evidence for the current boundary-tools protocol.
