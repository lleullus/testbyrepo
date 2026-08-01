# Implementation Failure Routing

## Order

1. Reconcile ownership and source integrity.
2. Confirm planning input currentness and Ticket authority.
3. Inspect the actual source-review finding and current source.
4. Classify it as Worker-caused implementation remediation, missed due-now initial work,
   pre-existing out-of-scope defect, environment failure, or unresolved authority.

## Worker remediation

`worker_remediation_authorized` is true only before terminal completion, when a source-review finding
is attributable to the selected Worker's bounded task, the Ticket authorizes the correction, current
source ownership is clear, and the same Worker can fix it inside a fresh frozen mutation envelope.

Capture a new ownership-only before snapshot, send only the bounded finding/context to the same Worker,
inspect the actual delta, reopen affected dependency closure review, and return the task to
`IMPLEMENTED` only after source-level review. Never replace the original pre-Worker Capsule.

## Other routes

- Missed due-now work: reopen decomposition as a new initial task, not remediation.
- Out-of-scope pre-existing defect: report it; block only if the Ticket cannot complete safely.
- Capsule or local environment failure before first Worker: return `INCOMPLETE`; do not mutate product.
- Mixed ownership or changed planning authority: `BLOCKED`.
- A finding returned by a later independent Verification invocation: start a new Implementation Lead
  invocation if the user requests authorized product changes. Never reopen or rewrite the prior result.
