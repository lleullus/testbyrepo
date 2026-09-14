# Ready Ticket Boundary Tools

`delivery-tools/ready-ticket` is the stateless delivery boundary for IIS Ready Tickets. It is intentionally not an execution scheduler, worker lease manager, command proxy, retry gate, or persistent workflow runtime.

## Public tool surface

The OMP extension registers exactly two IIS tools and does not install global tool-dispatch hooks:

- `ready_contract`
  - `inspect_authority`: validate and bind the current Ticket/product authority bytes.
  - `check_plan_admission`: require an exact current `iis-plan-review/v2` ADMIT before implementation work; reject declared projection/material-finding contradictions and changed evidence files. Independent execution and semantic truth remain role responsibilities.
  - `capture_verification`: create one immutable verifier binding outside Project Root.
- `ready_finalize`
  - accept only `{ "terminal_handle": "<opaque host-delivered handle>" }` for a successful delegated Ready Verify worker;
  - consume host-owned binding/verdict provenance and verify current loaded bundle/protocol identities before mutation;
  - perform at most the narrow canonical Ticket `ready -> done` status progression without interpreting semantic verification.

Implementation admission now requires the independent reviewer's original `iis-plan-review/v2` artifact. Historical v1 reviews remain evidence only; callers must not convert them into current approval. V2 preserves projection, findings, conditional scope and optional ordinary-file evidence references. Hash checks detect supplied-byte mismatch, not authorship or runtime truth.

Authority inspection and admission expose the module's canonical `bundle_root` and explicit `role_document_paths`. Installed execution rejects a validator outside that release and drift in required role/validator files; source mode remains explicitly `source`. This does not pin a host's autoload resolver or prove which other documents it loaded. Preserve unavailable loaded identity as unknown.

The ordinary Node CLI can inspect authority and check admission without OMP. Protected finalization still requires its supported host. Coverage findings and material evidence limits require caller withholding, not a new finalizer argument or machine Coverage gate.

The optional CLI exposes `ready_contract`; its `ready_finalize` name fails with `CAPABILITY_UNAVAILABLE` because only the live OMP host can resolve terminal authority.

## Implementation boundary

The actual implementing actor calls `ready_contract check_plan_admission` immediately before the first source mutation and again immediately before claiming `Completion: COMPLETE`. Between those checks, ordinary reads, edits, tests, builds, lint and CLI work use the host's native tools.

A settled process exit with a nonzero status is an ordinary command failure. The actor inspects it, makes a Plan-consistent correction and reruns the command. IIS does not convert that ordinary failure into a global execution lock.

If a real non-idempotent or external effect loses its response, do not blindly replay it. Use the Ticket/Plan-authorized readback and cleanup path. Continue when the effect is attributable as applied or not applied; otherwise stop dependent work and return the exact evidence limit.

A material implementation method change ends the current implementation invocation. Revise the affected Plan, obtain a current independent review, then start a fresh actor only after the prior worker/process is actually settled.

## Verification binding

`capture_verification` records:

- canonical Project Root and Ticket identity;
- protected authority and validator identities;
- immutable stable implementation targets and recursive byte/mode identities;
- explicitly declared scenario-effect paths, which must be disjoint from stable targets and protected authority/method paths;
- optional exact Plan Review navigation;
- bundle/protocol identity.

The binding is created as a mode-0600 outside-root file and is never overwritten. Scenario-effect paths may change during the authored verification scenario; stable targets may not. Stable-target or authority drift makes later status progression fail rather than silently reusing stale evidence.

After closing the semantic cycle, the delegated verifier returns one successful terminal report with the binding identity and semantic verdict. It does not write Ticket status or create a portable verdict credential. OMP recognizes the exact Ready Verify worker terminal, validates its shape and immutable binding, persists it privately, and delivers an opaque terminal handle out-of-band.

The caller submits exactly that host-delivered handle as the sole `ready_finalize` input. It cannot supply, rewrite, extract, serialize, copy, or recreate the semantic verdict authority. Binding paths, verdict text, task output copied into a new object, CLI JSON, a fabricated handle, or another caller/session's handle are insufficient.

## Finalization and provenance

For host terminal authority referencing a binding captured from `Status: ready`:

- `FAILED` and `INCONCLUSIVE` never mutate the Ticket.
- `VERIFIED` may perform only the exact top-metadata status replacement after terminal/binding/current-bundle/current-protocol, currentness, and canonical validation checks.
- any terminal authority, binding, current-bundle, or protocol mismatch performs no Ticket mutation.
- post-write validation failure conditionally restores only this finalizer call's exact candidate when protected state is still unchanged.
- an already-`done` Ticket matching the binding is current-state confirmation, not proof that the current call performed completion.

A completion result is attributable only when the finalizer actually performed the write in the current call or recovered the exact captured result from its host-owned consumed-terminal ledger. Semantic verdict, terminal provenance, progression result, progression basis, and observed Ticket status remain separate fields. The ledger is minimal idempotency provenance, not execution/session/workflow state, and stores no verifier transcript or reusable credential.

A binding captured from an already-`done` Ticket is diagnostic only and never reopens status.

## Installation and legacy cutover

The immutable installer packages this directory as the `ready-boundary-tools` release family. Candidate validation rejects retired runtime payloads and scans all installed payload roots for retired delivery dependencies before packaging.

When an existing managed installation still exposes the previous delivery extension, activation requires an exact retired runtime state root. The installer performs a read-only retirement scan before changing any host link. Terminal history is archival. A nonterminal stale record is cutover-safe only with exact record/owner identity plus independent evidence that workers/processes/services are absent, ownership is retired, and any external effect has an attributable settlement/readback. Live, unsettled or record-only ambiguity blocks activation.

Approved retired state bytes are copied into the activation snapshot before link switching. Rollback restores the previous release and link identity. Real operating activation remains a separate operator-approved step; building and validating an isolated candidate does not activate it.

## Tests

Run:

```text
npm test
```

The suite covers authority/admission currentness, immutable verification binding, host terminal authority capture/consumption, restart-safe exact-result replay, bundle/protocol identity gates, stable/effect separation, exact finalization/rollback semantics, ordinary settled command failure followed by edit/retry, and zero global tool interception hooks.
