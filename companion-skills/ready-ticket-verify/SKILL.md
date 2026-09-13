---
name: ready-ticket-verify
description: "Verify one existing IIS Ready Ticket against a stable current implementation target, semantically check every authored AC/Verification flow and adjudicate all obligations from fresh discriminating verifier-owned evidence. Exactly one SUBAGENT verifier owns each semantic cycle; after VERIFIED the caller obtains one read-only Coverage review before submitting the exact opaque handle to ready_finalize."
---

# Ready Ticket Verify

## Purpose and readers

Exactly one delegated verifier owns the exact Ticket's semantic preflight, authored Flow/AC adjudication and fresh discriminating evidence. Parent Main owns dispatch, passive terminal fan-in, post-success Coverage and finalization, not a second semantic verdict.

The caller reads this entry contract. The actual verifier reads this entry and [references/verify.md](references/verify.md) in full and performs only the verifier core. The caller does not load or rewrite that core to construct the assignment.

## Inputs and dispatch

Bind one exact absolute canonical Ticket path, its Project Root and applicable original parent/Behavior/UI/user authority. Normal input is `Status: ready`; `draft` or `blocked` cannot enter verification, and `done` requires explicit diagnostic authority without reopening status. The verifier derives and validates the authored contract directly.

Resolve this SKILL.md and references/verify.md from the current pinned IIS bundle and supply both exact readable paths with an instruction to read and apply them before work. Supply the following existing assignment inputs; missing navigation stays `None`, never a fabricated value:

```text
Ticket: <exact absolute canonical TICKET-NNN.md path>
Candidate Verification Target: None | <current source/config/build/artifact/runtime hint>
Implementation Report / Evidence: None | <navigation/reference only>
Execution Plan / Review: None | <exact optional outside-root plan_review_path>
Known Coverage Findings: None | <exact prior result and correction/new evidence>
Additional User Instructions: <current instructions and permitted execution/readback/effects>
Delegated Verifier: yes
```

Include required evidence/report locations and the current host Communication contract. Reports, suggested tests and target hints are navigation, not authority or proof. Verification-only needs no new implementation plan ADMIT; the verifier resolves its actual stable/effect target and captures its own binding.

Under Adaptive, forward the unchanged Common original sources block from [the shared source assignment](../../iis-adaptive-planning/templates/SHARED-SOURCE-ASSIGNMENT.template.md). The verifier reads originals before accepting caller framing and reports a weaker Ticket projection through semantic preflight; access to the Thesis does not expand Ticket scope. Standalone verification retains its existing authority inputs.

Dispatch exactly one task with `authorityProfile: iis-ready-verifier/v1` and the current user-selected model/effort. Do not set caller `outputSchema` or `schemaMode`. There is no DIRECT verifier, fallback roster or nested verification delegation. If required capability is unavailable, return `SUBAGENT CAPABILITY UNAVAILABLE` with the observed capability limit and no product/runtime/status mutation.

The worker returns admission failure without AC verdicts, or one host-owned strict terminal under references/verify.md after all applicable authored obligations, settlement and cleanup. It must not remediate implementation, dispatch Coverage or finalize.

## Terminal fan-in and settlement

After successful background dispatch, stand by for the exact host-delivered terminal. Do not poll normal progress, send status requests or duplicate repository/runtime inspection to observe the owner. A bounded diagnostic snapshot is permitted only for an explicit user status/stop request, host timeout/failure, malformed/missing terminal delivery or actual replacement/settlement diagnosis; normal execution returns to passive fan-in.

Do not replace an owner on the same mutable/effect surface until actual prior worker/process settlement is established. A cancellation receipt is not settlement. Replacement requires a fresh verifier invocation and binding, not resumption of an ended result.

Preserve the exact returned Ticket/target identity, verdict, evidence limits and host provenance. Admission failure is not a product FAIL. A valid FAILED result remains a completed verdict even when its contract permits unrelated flows to remain explicitly INCONCLUSIVE. Implementation test counts, narration and copied terminal fields cannot establish independent verification or finalization authority.

## Caller-owned post-success Coverage

OMP privately accepts the designated verifier's strict terminal and supplies an opaque terminal handle. For `VERIFIED` captured from `ready`, the finalization-owning caller dispatches exactly one independent [ready-ticket-coverage](../ready-ticket-coverage/SKILL.md) worker after verifier settlement. Read its caller input/result contract and forward exact original authority, completed verifier report, primary-evidence locations, target/binding identities and any prior finding/correction. Keep the opaque handle private. Adaptive Outer Main performs this directly without another top-level verify wrapper.

Only `COMPLETE` with no unresolved material finding or evidence gap permits submission of that original handle while target and authority remain current. A material finding, PARTIAL/BLOCKED, failed or missing review withholds submission: preserve VERIFIED and actual Ticket status, report the review/limit and `Finalization: not called`. No response is not no-finding; do not invent a finalizer failure or another AC verdict. FAILED/INCONCLUSIVE and diagnostic non-progressing terminals skip normal-success Coverage.

Supplementary execution/adjudication requires a fresh verifier invocation, binding and terminal. Forward the exact finding as navigation; the verifier owns every applicable Flow/AC, not just an extra test. No redispatch of unchanged findings/evidence without material change or an unattempted authorized discriminating observation. Follow-up Coverage reviews the new exact report and affected gap, not unrelated paths. Remediation requires its existing implementation/planning authority; standalone verification does not authorize automatic repair.

## Caller finalization and report

Call `ready_finalize` only with `{ "terminal_handle": "<exact host-delivered handle>" }`. Do not reconstruct authority from a verdict, Ticket, binding path/SHA, bundle, copied report or another session's handle. Normal FAILED/INCONCLUSIVE and diagnostic terminals retain the existing non-progressing finalization path.

The finalizer checks current bundle/protocol, authority, stable target and canonical Ticket validity. Only VERIFIED from a ready binding may change exact top metadata `ready` to `done`. Unknown/foreign/malformed authority or drift cannot progress. A provenance-free already-done state is not new completion. An exact same-handle retry returns its captured result without another status write. Coverage is a caller obligation, not mechanically enforced by this finalizer.

Append the actual `Verification Verdict`, `Ticket Progression`, `Progression Basis`, `Ticket Status After`, host provenance and progression detail to the verifier result. Preserve semantic VERIFIED if progression fails; do not claim delivery completion. For an authority/currentness/evidence/progression limit report `Decision`, `Governing authority`, `Observed condition`, `Effect` and `Next allowed action`; do not infer a product defect from transport failure. When Coverage withholds submission, report `Finalization: not called` instead.

Verification does not authorize implementation, planning continuation, new observability/hooks/evidence stores, or external actions beyond current exact authority. The caller routes any further work under the user's actual request.
