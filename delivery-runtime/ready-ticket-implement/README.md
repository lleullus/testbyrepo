# IIS Ready runtime v2

A small host-neutral owner/admission/effect/finalization kernel. `src/core.js` (package export `.`) has no OMP import, configuration lookup or session API. `index.js` (export `./omp`) installs the OMP adapter. This is not a universal sandbox or a semantic AC/review judge.

## Public core

- `bindAuthority({ticketPath, projectRoot, validatorPath?, executeArgv, runtimeProtocol?, bundleIdentity?})` runs the canonical validator and returns flat canonical product identity including `authority_digest`.
- `checkAuthorityCurrentness(binding)` compares protected product and validator bytes, not Git HEAD or ordinary implementation edits.
- `RuntimeStore(stateRoot?)` uses schema v2 and `IIS_READY_RUNTIME_DATA`, otherwise `${XDG_STATE_HOME:-~/.local/state}/iis/ready-runtime`. Legacy records are rejected, never silently migrated or ignored.
- `ReadyLifecycle({store, executeArgv, validatorPath?, bundleIdentity?, recoveryOwner?})` owns exact admission, one-use assignment, dispatch fences, pauses, one active effect, one ephemeral host service and terminal closure.
- `captureVerificationTarget(...)` and `checkVerificationTarget(binding,{executeArgv})` are async. Inventory includes Git tracked/untracked plus explicit targets. Exact supplied method paths have a separate context manifest; explicit targets/product paths win. Dynamic runtime/provider claims still need authoritative readback.
- `bindPlanReview`, `checkPlanCurrentness` check actual bytes and Ticket pairing, not reviewer independence or semantic sufficiency.
- `finalizeVerification(lifecycle,id,actor,verdict)` owns status-only progression and recovery, not the semantic verdict.

The host supplies opaque actor identity and `executeArgv(argv,{cwd,signal,timeout}) -> {exitCode,interrupted,terminationState,stdout,stderr}`. Validator calls require complete stdout and exact `VALID`. The default validator is relative to the same source/immutable bundle. There is no workflow-Markdown regex or OMP/Codex home fallback.

## Guard actions

`inspect_authority` is read-only and returns flat authority identity. Reading Skills, references, device docs, or preparation artifacts does not arm or bind a session.

Implementation `begin_direct`, `assign_subagent`, and `begin_delegated` all consume current `plan_review_path` (`iis-plan-review/v1`, exact outside-root reviewer JSON). Missing/stale/unadmitted are `PLAN_REVIEW_REQUIRED`, `PLAN_REVIEW_STALE`, and `PLAN_NOT_ADMITTED`. Correct direct/delegated implementation starts `ACTIVE` without a pre-edit checkpoint. Assignment consumption rechecks current bytes and one-use ownership.

`begin_verify` directly binds approved authority and actual product target, without implementation preparation. Optional `plan_review_path` supplies confirmed navigation context only. If a plan is itself a required product output, include its exact path in `target_paths`; do not hide a product obligation as method context.

`checkpoint` takes `kind: PRE_RUNTIME | MATERIAL_TURN | PRE_PROGRESSION`. Delegated verifier starts paused at `PRE_RUNTIME`. `release_checkpoint` is the exact parent (or DIRECT owner) operation; material method/plan drift requires current reviewer evidence, not a bare CONTINUE. Delegated VERIFIED progression requires PRE_PROGRESSION release; DIRECT does not invent a parent checkpoint. Phases are `ACTIVE`, `PAUSED`, `EFFECT_UNCERTAIN`, `COMPLETE`, `BLOCKED`. Pause reasons are fixed; paused executions permit safe reads, not source mutation.

`suspend_worker` requires owned operations, service and uncertainty already settled and revokes old dispatch. `replace_worker` rechecks current authority/method/target, supersedes old ownership, and issues a new one-use assignment. Late old results cannot alter the replacement. Host agent/job/session IDs are not interchangeable.

`complete` checks current ownership, authority/method and work/service/effect closure. It does not manufacture self-check evidence from read counts. `block` cannot release an uncertain-effect slot. `cancel_admission` closes only an unconsumed assignment; no implicit armed state exists.

## Effect and recovery boundary

`ready_argv` uses native `pi.exec(command,args,options)`, never a Ready raw process executor. `inspect` uses a restricted read-only argv grammar (plus exact bound canonical validator); normal reads have no durable ledger, quota or repeat latch. `execute` and `mutate` reserve an opaque program effect. A nonzero/interrupted/lost result is not proof of non-application even when source hashes are unchanged. Full raw result is stored in an execution-owned outside-root output file; inline command stdout/stderr are limited.

The adapter fences builtin file mutation and exact outside-root output files, protects authority and bound plans/review, and rejects unknown native/device effect surfaces with `CAPABILITY_UNAVAILABLE`. Structured argv and declared paths are a reviewed operation contract, not an OS sandbox for arbitrary executable code. Use only the approved operation; remote/dynamic claims need actual readback. Generic evaluator/browser scripting cannot bypass the fence by calling itself read-only.

Exact declared outside-root report files remain writable by the current owner/controller while paused or effect-uncertain so recovery evidence can be authored. Such a report does not clear uncertainty or permit product replay. Do not use report permission to modify product runtime state or manufacture an outcome. Builtin `todo` is host-session bookkeeping: a non-revoked terminal owner (`COMPLETE` or `BLOCKED`) may close its checklist, while source/effect dispatch and superseded workers stay fenced.

`resolve_mutation` requires `operation_id`, `effect_surface`, `evidence_reference`, `outcome`. The exact evidence JSON contains `execution_id`, `operation_id`, `effect_surface`, current controlling `owner`, matching `outcome`, and `readback_reference`. This records an explicit authorized recovery-owner judgment. It is not automatic external-effect proof or a signed approval system. Inconclusive evidence preserves uncertainty.

`recover_admission` takes exact `project_root`, `ticket_path`, `reservation_id`, `recovery_evidence_reference`. The designated owner (creator or host-configured recovery owner) supplies a JSON with those root/Ticket/reservation identities, `owner`, `admission_disposition: terminated_or_withdrawn`, `live_work: absent`, `uncertain_effects: absent`, and `readback_reference`. Meaningful absence/termination is the owner's judgment of actual evidence, not caller boolean automation. The locked implementation also requires the same reservation and no execution/assignment record. Otherwise it preserves exclusion. A delayed old admission cannot commit after recovery because it must compare the same reservation identity. Host-configured recovery ownership supports designated recovery after creator termination without introducing another lifecycle database.

## Native services

Use builtin `hub start/logs/wait/stop`, not a Ready service tool. One ephemeral service is supported with name `ready-<execution_id>`, exact Project Root cwd, explicit log/port readiness, `persist:false`, `detached:false`, `restart:no`. Readiness timeout retains its returned live handle. The adapter consumes `details.daemon` id, owner, startedAt/restartCount generation, readiness and terminal state; same-name different-generation results cannot settle the old handle. Explicit stop/wait and attributable host settlement precede terminal/suspension. The host has name-based stop: concurrent noncooperating replacement and escaped descendants/external effects are not guaranteed by this adapter. Unsupported/missing handle results remain uncertain; no raw supervisor fallback is installed.

## Finalization

VERIFIED, Ticket progression and actual status are separate. The finalizer requires current product authority/target and, for delegated verification, released progression. It validates the canonical Ticket, persists exact before/candidate intent, fsyncs a same-directory status-only replacement, and runs post-validation at the actual canonical path. Only its exact ready→done bytes are exempted from ordinary drift. Other source/authority changes remain failures. Candidate rollback is conditional on current bytes/authority/owner; external edits are preserved. Crash intent is retained for the same finalization owner to retry postcheck or recover. Durable terminal state is written before slot cleanup. Failed progression never becomes COMPLETED just because the file says done.

## Candidate verification

Run from this directory after integration: `node --test tests/*.test.js` (or `npm test`). Permanent cases cover wrong/stale review admission, first actual edit/CLI output, one-use/replacement/late owner, orphan reservation recovery, opaque loopback timeout, context/product drift, and status-only/validator/crash recovery. Adapter doubles defend policy boundaries, not actual host equivalence. Fresh OMP structured execution, service readiness/generation/settlement, device transport, and installer-loaded identity require separate real-host smoke. This document records the candidate contract, not a claim that those checks have already passed. Repository suite is owned by the integrating Main.
