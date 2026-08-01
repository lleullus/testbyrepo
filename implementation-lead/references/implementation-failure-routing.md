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
- Focused-check failure: task feedback; use Ticket-authorized source remediation when attributable.
- Final-review or publication source-identity mismatch: reconcile the intervening delta and restart the
  full final review once when disjoint; overlap or authority change is `BLOCKED`, repeated disjoint drift
  is `INCOMPLETE`.
- ImplementationResult `PLANNING_INPUT_CHANGED`: `BLOCKED`. Malformed request, result-store failure,
  Capsule failure, or capability failure: `INCOMPLETE`. Do not claim completion without publication.
- Changed planning authority or unresolved overlapping ownership: `BLOCKED`.
- A finding returned by a later independent Verification invocation: start a new Implementation Lead
  invocation if the user requests authorized product changes. Never reopen or rewrite the prior result.
