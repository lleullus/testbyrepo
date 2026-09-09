# Ready Ticket Boundary Tools

`delivery-tools/ready-ticket` is the stateless delivery boundary for IIS Ready Tickets. It is intentionally not an execution scheduler, worker lease manager, command proxy, retry gate, or persistent workflow runtime.

## Public tool surface

The OMP extension registers exactly two IIS tools and does not install global tool-dispatch hooks:

- `ready_contract`
  - `inspect_authority`: validate and bind the current Ticket/product authority bytes.
  - `check_plan_admission`: require an exact current independent `iis-plan-review/v1` ADMIT before implementation work.
  - `capture_verification`: create one immutable verifier binding outside Project Root.
  - `seal_verdict`: bind the verifier's terminal semantic verdict to that exact binding in a new immutable outside-root record.
- `ready_finalize`
  - consume only an immutable verifier-owned verdict-record path/SHA;
  - verify its binding and current loaded bundle/protocol identities before mutation;
  - perform at most the narrow canonical Ticket `ready -> done` status progression without interpreting semantic verification.

The optional CLI exposes the same two surfaces for host integration without creating persistent IIS execution state.

## Implementation boundary

The actual implementing actor calls `ready_contract check_plan_admission` immediately before the first source mutation and again immediately before claiming `Completion: COMPLETE`. Between those checks, ordinary reads, edits, tests, builds, lint and CLI work use the host's native tools.

A settled process exit with a nonzero status is an ordinary command failure. The actor inspects it, makes a Plan-consistent correction and reruns the command. IIS does not convert that ordinary failure into a global execution lock.

If a real non-idempotent or external effect loses its response, do not blindly replay it. Use the Ticket/Plan-authorized readback and cleanup path. Continue when the effect is attributable as applied or not applied; otherwise stop dependent work and return the exact evidence limit.

A material implementation method change ends the current implementation invocation. Revise the affected Plan, run Heuristic and independent review, then start a fresh actor only after the prior worker/process is actually settled.

## Verification binding

`capture_verification` records:

- canonical Project Root and Ticket identity;
- protected authority and validator identities;
- immutable stable implementation targets and recursive byte/mode identities;
- explicitly declared scenario-effect paths, which must be disjoint from stable targets and protected authority/method paths;
- optional exact Plan Review navigation;
- bundle/protocol identity.

The binding is created as a mode-0600 outside-root file and is never overwritten. Scenario-effect paths may change during the authored verification scenario; stable targets may not. Stable-target or authority drift makes later status progression fail rather than silently reusing stale evidence.

After closing the semantic cycle, the verifier calls `ready_contract seal_verdict` and returns both binding and verdict-record path/SHA. It does not write Ticket status. The caller passes only that exact verdict-record identity to `ready_finalize`; it cannot supply or rewrite the semantic verdict.

The verdict record is a mode-0600, non-overwritable outside-root evidence file. It copies Ticket, binding, bundle and protocol identity from the verified binding. It is not execution/session/workflow state.

## Finalization and provenance

For a verdict record referencing a binding captured from `Status: ready`:

- `FAILED` and `INCONCLUSIVE` never mutate the Ticket.
- `VERIFIED` may perform only the exact top-metadata status replacement after verdict-record/binding/current-bundle/current-protocol, currentness and canonical validation checks.
- any record/binding/current bundle or protocol mismatch performs no Ticket mutation.
- post-write validation failure conditionally restores only this finalizer call's exact candidate when protected state is still unchanged.
- an already-`done` Ticket matching the binding is current-state confirmation, not proof that the current call performed completion.

A completion result is attributable only when the finalizer actually performed the write in the current call or when the same host process has captured provenance for that exact verdict record's prior finalizer result. Semantic verdict, verdict provenance, progression result, progression basis and observed Ticket status remain separate fields.

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

The suite covers authority/admission currentness, immutable verification binding and verdict records, bundle/protocol identity gates, stable/effect separation, exact finalization/rollback semantics, ordinary settled command failure followed by edit/retry, and zero global interception hooks.
