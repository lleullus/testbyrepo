# Implementation Failure Routing

## Order

1. Reconcile physical scope, actor attribution, preservation, and source integrity.
2. Confirm planning input currentness and Ticket authority.
3. Inspect the actual source-review finding and current source.
4. Classify it as Worker-caused implementation remediation, missed due-now initial work,
   pre-existing out-of-scope defect, environment failure, or unresolved authority.

An unexpected delta is nonterminal while this order is being applied. Do not report `BLOCKED` merely
because the scope comparison returned `OUTSIDE_ENVELOPE`.

## Unexpected delta routes

| Condition | Disposition |
| --- | --- |
| Preserved external change, disjoint from planning authority and task impact | `CONTINUE`; record and exclude it from task evidence |
| Worker-attributable scope violation, Ticket-authorized and safe to correct | `REMEDIATE` with the same Worker |
| Planning input or approved UI authority changed | `BLOCKED` for the Ticket/Spec owner |
| Overlapping product path with unclear actor, overwritten pre-existing work, or preservation loss | `BLOCKED` for reconciliation with the user/repository owner |
| Invalid snapshot/artifact or persistent source-capture instability without an authority conflict | `INCOMPLETE` |

Path location alone is not actor evidence. A path inside the envelope can still be externally edited,
and a path outside it can be concurrent unrelated work.

## Worker remediation

`worker_remediation_authorized` is true only before terminal completion, when a source-review finding
or scope violation is attributable to the selected Worker's bounded task, the Ticket authorizes the
correction, pre-existing work remains recoverable without guesswork, and the same Worker can fix it
inside a fresh frozen mutation envelope.

Capture a new ownership-only before snapshot, send only the bounded finding/context to the same Worker,
inspect the actual delta, reopen affected dependency closure review, and return the task to
`IMPLEMENTED` only after source-level review. Never replace the original pre-Worker Capsule.

## Representative runtime exercise outcomes

- An expected effect that is absent, or an authoritative readback that contradicts the claimed behavior,
  is task feedback. Use bounded Worker remediation only when current source review establishes a
  Ticket-authorized defect attributable to the task; select a new initial task when it exposes missing
  due-now behavior instead.
- Without an authoritative readback, the runtime-dependent Acceptance Criterion remains `PARTIAL`.
  Return its owning task to `REVIEWING` for a no-mutation focused check only when a real readback path
  exists; otherwise return `INCOMPLETE`.
- An unavailable safe target, execution capability, credential, or reliable target-to-source binding is
  `INCOMPLETE`; do not reinterpret an environment failure as a product defect or alter source merely to
  obtain a pass.
- Unclear target authority, an unapproved external effect, or a required action that is unsafe to run is
  `BLOCKED` for the user or authority owner.
- A project delta during a no-mutation focused check follows the ordinary ownership capture and
  reconciliation rules; it is not an exception that can support runtime coverage.

## Frontend guidance, authority, and renderer outcomes

| Condition | Disposition |
| --- | --- |
| Lead cannot resolve/read active `ima2-front`, its loader-returned base, or its canonical `SKILL.md` before a frontend-bearing dispatch | `INCOMPLETE`; do not approximate or substitute guidance |
| Worker cannot read the passed guidance path or a routed required reference and returns `GUIDANCE_UNAVAILABLE` without mutation | `INCOMPLETE`; preserve the attempt evidence |
| Ticket `UI: no` conflicts with a due-now rendered-contract change or required direct rendered exercise | `BLOCKED` for the Ticket/Spec owner before Worker dispatch |
| Current approved UI authority or task locator is missing, insufficient, changed, or conflicts with unresolved higher authority | `BLOCKED` for the Ticket/Spec owner; Worker returns `AUTHORITY_GAP` without mutation if discovered during dispatch |
| Intended renderer, safe target, execution capability, or reliable source binding is unavailable | `INCOMPLETE`; do not call it a product defect or authority blocker |
| Actual renderer lacks the expected effect or rendered readback contradicts it | Task feedback; use existing Worker-attributable remediation or new-initial-task routing after Lead source review |

Do not apply the no-delta generic Worker-call retry to deterministic `GUIDANCE_UNAVAILABLE` or
`AUTHORITY_GAP` outcomes. Guidance availability is an environment/capability condition; UI authority
and locator sufficiency are Ticket/Spec authority conditions. Neither permits a best-effort mutation.

## Other routes

- Missed due-now work: reopen decomposition as a new initial task, not remediation.
- Out-of-scope pre-existing defect: report it; block only if the Ticket cannot complete safely.
- `SOURCE_CHANGED_DURING_CAPTURE`: retry one fresh full capture; a second occurrence is `INCOMPLETE`.
- Ownership compare exit `10`: enter `RECONCILING`; this is not a terminal exit. Exit `2` caused by
  invalid input, policy mismatch, or invalid artifact is `INCOMPLETE`.
- Worker call failure: always capture and compare the post-call source first. If there is attributable
  delta, review and reconcile it without blindly retrying. If there is no delta, recheck planning,
  Capsule, Worker availability, and source identity, then retry the same bounded call once. A second
  no-delta runtime failure is `INCOMPLETE`.
- Capsule missing, expired, corrupt, unsupported, or unavailable after product mutation: `INCOMPLETE`;
  retain the original run evidence and never re-seal.
- Other snapshot artifact, store, or local environment failures: `INCOMPLETE`; do not invent product or
  authority remediation.
- Final-review or publication source-identity mismatch: reconcile the intervening delta and restart the
  full final review once when disjoint; overlap or authority change is `BLOCKED`, repeated disjoint drift
  is `INCOMPLETE`.
- ImplementationResult `PLANNING_INPUT_CHANGED`: `BLOCKED`. Malformed request, result-store failure,
  Capsule failure, or capability failure: `INCOMPLETE`. Do not claim completion without publication.
- Changed planning authority or unresolved overlapping ownership: `BLOCKED`.
- A finding returned by a later independent Verification invocation: start a new Implementation Lead
  invocation if the user requests authorized product changes. Never reopen or rewrite the prior result.
