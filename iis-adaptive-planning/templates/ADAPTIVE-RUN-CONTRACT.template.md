# IIS Adaptive Run Contract

Status: CLOSED | USER_INPUT_REQUIRED
Project-Root: <exact absolute project root | Not established yet>
Mandate: <companion path/revision | current-conversation authority>
Run Contract Approval Gate: required | not_required

## Goal Outcome

<durable result assigned to this invocation>

## Required Named Items

- <exact required user-named capability/change/outcome>

or exact:

None required

## Candidate Named Items

- <exact candidate capability/change/outcome>

or exact:

None named

## Required Item Policy

EXACT_REQUIRED_SET | REQUIRED_FLOOR | NONE_REQUIRED

## Delivery Stages

Implementation: yes | no
Verification: yes | no

## Delivery Model Selection

Guide consulted: <resolved guide path and authored version | Not needed — no recommendation required>

| Stage | Execution mode | Selected model / effort | User-selection basis |
| --- | --- | --- | --- |
| Implementation | SUBAGENT / DIRECT / disabled | <exact configuration / Not selected / Not applicable> | <current user instruction or confirmation / unresolved / Not applicable> |
| Verification | SUBAGENT / DIRECT / disabled | <exact configuration / Not selected / Not applicable> | <current user instruction or confirmation / unresolved / Not applicable> |

Recommendations awaiting confirmation: None | <missing stage -> proposed model/effort, workload reason, guide section, meaningful alternative>

Preparation selections: None needed | <actual delegated Planner/Heuristic/Plan Review invocation -> current selected model/effort and user-selection basis>. Reuse an applicable selection; do not require three models or add a preparation switch. DIRECT writing still cannot self-approve as independent review; report an unavailable independent invocation without ADMIT.

These are invocation-local execution choices, not a worker roster or another stage switch. Apply [Delivery Model Selection](../references/09-run-contract.md#delivery-model-selection): preserve supplied choices, leave recommendations unselected until confirmed, and use USER_INPUT_REQUIRED only for actual missing selections. DIRECT and disabled stages need no child-model question. Verification no does not disable pre-implementation review for Implementation yes.

## Run Completion Boundary

READY_TICKET_SET | READY_EXECUTION_PLANS | CURRENT_INCREMENT_IMPLEMENTED | CURRENT_INCREMENT_DELIVERED | NAMED_REQUIRED_ITEMS_DELIVERED | BOUNDED_OUTCOME_SATISFIED | MANDATE_OUTCOME_SATISFIED

## Completion Predicate

<one observable condition that proves whole-run success>

## Authoritative Readback

<exact product surface, canonical Ticket state, implementation result, operator evidence, or Not yet established>

For READY_EXECUTION_PLANS: <exact required preparation Tickets, actual READY TICKET PLAN RESULT, outside-root current independent ADMIT review/evidence for every required Ticket>. Both delivery switches are no; this is not product planning, implementation or delivery completion.

## Source Authority

<concise current instruction and applicable Mandate revision; do not fabricate a quote>

## Unresolved Field

None

or, only when `Status: USER_INPUT_REQUIRED`:

<smallest exact field and options whose different answers materially change the run, including missing delivery model/effort selections>

## Notes

- Auto-fill every field current authority determines; do not ask the user to restate it.
- A recommendation from the model guide or a host default is not a user selection. Confirm missing active SUBAGENT model/effort choices together; do not ask again for choices already fixed by current user authority.
- Required Named Items and Candidate Named Items may coexist; no item may appear in both.
- Default `Run Contract Approval Gate` to `not_required`. Set it to `required` only when exact `/승인게이트` is an affirmative directive/modifier on the current explicitly active Adaptive invocation; quoted, explanatory, hypothetical, or negated mentions do not activate it, and the token does not activate Adaptive by itself.
- A `CLOSED` form proceeds without redundant confirmation when the gate is `not_required`. When the gate is `required`, render this exact `CLOSED` form and STOP before the first planning or delivery mutation until direct user approval.
- The gate is Run Contract-only. It does not add Mandate, Scope, Ask Matt, Spec, Ticket, implementation, or verification approval gates and cannot be satisfied through standing delegation.
- If direct approval materially revises decision-critical Run Contract meaning, re-close and re-render the revised form before requesting approval again; downstream changes already allowed by the approved contract do not retrigger the gate.
- Do not begin planning or delivery mutation while a material field remains unresolved.
- Implementation and Verification are independent invocation fields; preserve explicit `do not implement` and `do not verify` overrides.
- With explicit Adaptive activation and no narrower stop or broader named-item/outcome terminal, the default current-Increment terminal is `CURRENT_INCREMENT_DELIVERED`, subject to Required-item coverage and the Mandate ceiling.
- Continuation Authority is the Mandate ceiling; this form's Run Completion Boundary is the actual invocation terminal within that ceiling.
- This form is invocation-local and is not a canonical IIS artifact or required durable companion file.
