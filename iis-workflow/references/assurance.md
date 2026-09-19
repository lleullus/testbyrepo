# Assurance: evidence execution and closure

Assurance v2 uses executor-owned fixed snapshots and actual invocation IDs. It does not use content-derived IIS identities, does not create product authority, and does not make a semantic verdict. Thesis/Scope and any approved Transition remain authoritative.

## Baseline

Use exactly one `iis-assurance` JSON fence under `## Assurance Baseline`, or the same JSON as an assurance-only input. The schema is `iis-assurance/v2`.

- `scope` is an executor-owned `{snapshot, path}` reference to the admitted ready Scope.
- `obligations` maps every nonempty Acceptance paragraph to declared gate/observation IDs. This checks authored coverage, not completeness of natural-language meaning.
- `gates` keep argv, cwd, timeout, executor-owned mechanism refs and optional native job export.
- `observations` keep the actual initial state, trigger, authoritative readback and predicate.
- `surfaces` and `lanes` retain bounded independent counterexample search.
- `no_probe_reason` is allowed only for a genuinely non-behavioral artifact.

Baseline authorship still belongs to Planner or Main in assurance-only work. Implementer/Prober do not edit it.

## Fixed inputs and binding

The UID-separated trusted supervisor owns the `ArtifactStore` outside the mutable target. Worker-facing execution commands cannot select a store or supply a binding ledger. Snapshot IDs are randomly allocated store identities and are never derived from content. The store preserves the actual file bytes, path and required executable mode.

`bind` is a trusted-host operation. It requires a registered `assurance` admission for the exact fixed Scope, captures the current source tree and exact Baseline, materializes an isolated execution copy, and registers `binding_id`/`run_id` in the supervisor ledger. A dirty Git worktree is not automatically rejected; the captured source tree itself is the execution target. Native Git commit IDs may still be reported as repository provenance, but IIS does not add a file or diff checksum layer.

Currentness is checked by direct comparison of stored source bytes/modes with the live target and by direct comparison of the stored Baseline bytes with the current Baseline input. A changed target or Baseline blocks reuse. External runtime/service state still requires its own authoritative readback.

Execution identity input remains `{artifacts, runtime, mechanisms, note}`, but each file reference is an executor-owned `{snapshot, path}`. Mechanisms are nonempty. Capturing a file is not proof that the runtime currently uses it; runtime identity and service/config readback remain separate obligations where load-bearing.

## Native gate capture

A host gate invocation executes the declared foreground command against the captured execution copy, not the mutable working-tree source. stdout, stderr and native job export are stored with the actual registered run/invocation producer. Exit zero alone does not establish product observations.

Every result uses `iis-assurance-result/v3` and records the actual `binding_id`, invocation, evidence refs and effects. Copying a result JSON or guessing an opaque ID does not create a new invocation or producer record.

## Results and activity

Observation results still distinguish `SATISFIED`, `VIOLATED`, and `UNOBSERVABLE`. Probe results still distinguish `COUNTEREXAMPLE_FOUND`, `NO_COUNTEREXAMPLE_WITHIN_BUDGET`, and `UNOBSERVABLE`. Hypotheses and action evidence use executor-owned refs.

Main supplies actual started-invocation/effect information from the host, not a model-authored denominator. Unknown or unsettled effects block. Several no-finding results never offset one unresolved material finding.

## Closure

`close` reads the supervisor ledger for the denominator, every started invocation and every effect; caller-supplied activity/result lists are not the authority. Required gates, observations and lanes must have attributable terminal results; direct observations must be SATISFIED; started effects must be SETTLED with evidence; a material counterexample cannot be hidden by other lanes.

Output is `iis-assurance-closure/v3` with `EVIDENCE_COMPLETE` or `BLOCKED`. This is structural evidence closure, not product approval or write authority.

## Recording

Immediately before ready→done, Main still checks current request authority, final target, originals, all started work/effects and closure. The recording helper verifies only the exact status-only byte delta. It does not emit or require a checksum.

## Independent search and correction

Probe isolation, safety, settlement and re-entry rules remain unchanged. A finding routes to the earliest bound decision owner that must change. New target evidence is reacquired after a correction; an old run is not relabeled onto a new target.

## Trust boundary

Strong enforcement requires the shipped Linux supervisor (or a conforming host with equivalent OS/process isolation) so workers cannot modify the store, binding/invocation ledger or trusted current request. When a host cannot provide that separation, it may still use the documents for advisory work but must not claim enforced binding or closure. File permissions, mtimes, sizes, path strings and model-produced receipts are not substitutes for that host boundary.
