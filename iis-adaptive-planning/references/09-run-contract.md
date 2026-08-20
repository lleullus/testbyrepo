# Adaptive Run Contract Closure

## Purpose

Close the meaning of one explicit Adaptive invocation before planning mutation so the outer execution cannot stop at a smaller result than the user assigned, silently treat required work as disposable, or collapse a mixed required/candidate assignment into one inaccurate list-wide label.

The Run Contract answers five questions:

1. what result this invocation must produce;
2. which user-named items are required obligations and which are candidate means;
3. which delivery stages the user authorized for this invocation;
4. which execution boundary counts as whole-run completion; and
5. what observable evidence proves that boundary is satisfied.

It is a compact invocation contract, not a second Mandate, approval ceremony, workflow database, execution ledger, or roadmap.

## Admission rule

Before the first Adaptive planning mutation:

1. inspect the current user instruction, applicable Mandate, canonical planning authority, and inspectable current facts;
2. normalize them into the form in [../templates/ADAPTIVE-RUN-CONTRACT.template.md](../templates/ADAPTIVE-RUN-CONTRACT.template.md);
3. mark the form `CLOSED` only when every material field is determined by current authority;
4. when one or more material fields remain unresolved, mark it `USER_INPUT_REQUIRED` and ask only for the smallest unresolved field whose different answers would change required scope, candidate freedom, delivery stages, success continuation, or completion meaning; and
5. do not begin Scope, Behavior/UI, Spec, Ticket, implementation, or verification mutation until the contract is `CLOSED`.

Read-only inspection needed to close inspectable facts is allowed. Do not ask the user to restate information that current authority already determines. A fully derived `CLOSED` form proceeds without another approval prompt.

## Required fields

### Goal Outcome

State the durable user/operator result assigned to this invocation. It may equal the Mandate's Desired Product Outcome or be a narrower current assignment.

### Required Named Items

List every exact user-named capability, change, or outcome that must remain an obligation until successful run termination, or exact `None required`.

### Candidate Named Items

List every exact user-named capability, change, or outcome offered as a candidate means that Adaptive may preserve, replace, defer, or drop under current Mandate authority, or exact `None named`.

Required and candidate lists may coexist. This is the normal representation for mixed instructions such as:

```text
A와 B는 반드시 구현하고, C는 필요하면 사용해.
```

which closes as:

```text
Required Named Items: A, B
Candidate Named Items: C
Required Item Policy: EXACT_REQUIRED_SET
```

Do not silently convert an implementation suggestion, example, or candidate into a required product promise. Likewise, do not silently weaken imperative assignments into candidates. No item may appear in both lists.

### Required Item Policy

Use exactly one value:

- `EXACT_REQUIRED_SET` — the Required Named Items are the complete user-named required result for this invocation. Adaptive may add supporting work needed to deliver them, but may not add another independent user-visible outcome as a new completion obligation without a Run Contract revision.
- `REQUIRED_FLOOR` — every Required Named Item is a required floor. Adaptive may add other product outcomes when current authority establishes they are required or materially necessary for the Goal Outcome.
- `NONE_REQUIRED` — there are no separately tracked required named items. Candidate Named Items may still exist.

`EXACT_REQUIRED_SET` and `REQUIRED_FLOOR` require a non-empty Required Named Items list. `NONE_REQUIRED` requires exact `None required`.

Natural language may close these fields without a question when it is unambiguous, for example:

- `A와 B를 모두 구현해`, `A도 하고 B도 해`, or an exact must-have list -> Required Named Items `A, B`, `EXACT_REQUIRED_SET`;
- `A와 B는 최소 요구야; 필요한 결과는 추가해도 돼` -> Required Named Items `A, B`, `REQUIRED_FLOOR`;
- `A와 B는 후보야; 더 나은 형태면 바꿔도 돼` -> Candidate Named Items `A, B`, `NONE_REQUIRED`;
- `A와 B는 반드시, C는 후보` -> Required Named Items `A, B`, Candidate Named Items `C`, `EXACT_REQUIRED_SET`.

When wording leaves an item genuinely ambiguous between the two lists and the distinction changes completion or reshaping freedom, ask only for that item's classification.

### Delivery Stages

Record these independently:

```text
Implementation: yes | no
Verification: yes | no
```

Preserve the current Adaptive default: explicit Adaptive activation selects `Implementation: yes` and `Verification: yes` unless current user authority overrides either stage.

Apply exact overrides independently:

- planning-only, stop-at-Ready-Tickets, no implementation and no verification -> `no` / `no`;
- implement but do not verify -> `yes` / `no`;
- verify an already implemented current target without implementation -> `no` / `yes` when current evidence and the separate verifier admission permit it;
- do not implement -> never infer implementation authority merely because verification or a broader outcome was requested;
- do not verify -> never run the verifier or claim `done`.

The fields express the outer invocation envelope only. They do not change the exact authority, admission, or result ownership of `ready-ticket-implement` or `ready-ticket-verify`.

### Run Completion Boundary

Use exactly one value:

- `READY_TICKET_SET`
- `CURRENT_INCREMENT_IMPLEMENTED`
- `CURRENT_INCREMENT_DELIVERED`
- `NAMED_REQUIRED_ITEMS_DELIVERED`
- `BOUNDED_OUTCOME_SATISFIED`
- `MANDATE_OUTCOME_SATISFIED`

Boundary meaning:

- `READY_TICKET_SET` — one approved current Spec plus its validated complete Ready Ticket Set exists.
- `CURRENT_INCREMENT_IMPLEMENTED` — every current canonical Ticket in the validated Ready Ticket Set has one exact implementation lifecycle result with `Completion: COMPLETE`; verification was not requested and Ticket status remains governed by the verifier.
- `CURRENT_INCREMENT_DELIVERED` — every current canonical Ticket in the approved Ready Ticket Set has reached exact `Status: done` through the owning verification lifecycle.
- `NAMED_REQUIRED_ITEMS_DELIVERED` — every Required Named Item is delivered and its applicable observable result is confirmed. Candidate Named Items do not block this boundary. This boundary may span more than one Increment.
- `BOUNDED_OUTCOME_SATISFIED` — the exact bounded outcome assigned to this run is satisfied in fresh actual product state.
- `MANDATE_OUTCOME_SATISFIED` — the Mandate's Desired Product Outcome is satisfied in fresh actual product state.

An implementation-only multi-Increment promise is not silently invented. If required named items cannot fit in the current Increment and the user disables verification, current verified success-re-entry rules cannot safely guarantee `NAMED_REQUIRED_ITEMS_DELIVERED`; return the smallest boundary or verification decision instead of silently reducing the required list.

### Completion Predicate

Write one concise observable predicate that distinguishes successful whole-run completion from a planning phase, one Ticket, one Increment, or roadmap progress.

Examples:

```text
Every Ticket in the current validated Ready Ticket Set has an exact implementation report with Completion: COMPLETE, and Verification is no.
```

```text
Every Ticket in the current validated Ready Ticket Set is exact Status: done.
```

```text
Every Required Named Item exposes the user-visible result assigned in this Run Contract and its authoritative readback confirms it.
```

Do not use `all planned work is done`, WP exhaustion, provisional-horizon exhaustion, Ticket titles, or agent reports alone as an outcome-satisfaction predicate.

### Authoritative Readback

Identify the current product surface, canonical Ticket state, exact implementation result, operator evidence, or other authority that can prove the Completion Predicate.

For `CURRENT_INCREMENT_IMPLEMENTED`, use the complete current Ticket denominator, each exact implementation result, and the unchanged canonical Ticket statuses. An implementation report proves implementation lifecycle completion only; it does not prove independent verification or `done`.

Use `Not yet established` only when establishing the readback is itself legitimate planning work. The run cannot terminate successfully until an attributable readback exists.

### Source Authority

Record the current instruction and applicable Mandate revision concisely. Do not fabricate a user quote.

## Consistency checks

Before marking the form `CLOSED`:

- no item may appear in both Required Named Items and Candidate Named Items;
- `EXACT_REQUIRED_SET` and `REQUIRED_FLOOR` require non-empty Required Named Items;
- `NONE_REQUIRED` requires exact `None required`;
- `READY_TICKET_SET` requires `Implementation: no` and `Verification: no`;
- `CURRENT_INCREMENT_IMPLEMENTED` requires `Implementation: yes` and `Verification: no`;
- `CURRENT_INCREMENT_DELIVERED` requires `Verification: yes`; Implementation may be `yes` or `no` according to current authority and actual state;
- `NAMED_REQUIRED_ITEMS_DELIVERED` requires non-empty Required Named Items and `Verification: yes`;
- Candidate Named Items never become completion obligations merely because they are listed;
- an unsatisfied outcome-satisfaction boundary that requires new delivery needs sufficient implementation/verification authority; an outcome already satisfied in fresh actual state may close without starting those stages;
- `CURRENT_INCREMENT_DELIVERED` always means the complete current canonical Ticket denominator, never one selected Ticket;
- outcome-satisfaction boundaries require fresh actual product evidence and an authoritative readback;
- the Run Completion Boundary must remain within current user authority and the Mandate's Continuation Authority ceiling.

### Required-item coverage invariant

A form is `CLOSED` only when satisfying its Run Completion Boundary and Completion Predicate necessarily satisfies every currently unsatisfied Required Named Item to the completion meaning promised by that boundary.

`READY_TICKET_SET`, `CURRENT_INCREMENT_IMPLEMENTED`, and `CURRENT_INCREMENT_DELIVERED` are current-Increment terminals. When Required Named Items exist, one of those boundaries may close only when every currently unsatisfied Required Named Item is either already satisfied by fresh authoritative readback or current authority establishes that the selected current Increment covers it in its approved Includes and completion contract.

If the current Increment is not yet shaped, or required-item coverage is unknown or partial, do not infer that the broader Required Named Items are covered by a current-Increment terminal. This does not prohibit a current-Increment boundary when there are no Required Named Items or current authority independently establishes that the required scope is exactly the selected current Increment.

`NAMED_REQUIRED_ITEMS_DELIVERED`, `BOUNDED_OUTCOME_SATISFIED`, and `MANDATE_OUTCOME_SATISFIED` may span multiple Increments when the enabled delivery stages and Mandate ceiling permit that continuation. Do not force those outer obligations into one selected Increment merely to make coverage look complete.

Ceiling checks use actual continuation requirements, not the boundary label alone:

- `CURRENT_INCREMENT` permits `READY_TICKET_SET`, `CURRENT_INCREMENT_IMPLEMENTED`, and `CURRENT_INCREMENT_DELIVERED`. It permits `NAMED_REQUIRED_ITEMS_DELIVERED` only when current authority establishes every Required Named Item is covered by the current Increment.
- a named-item or bounded predicate that requires another Increment needs at least `BOUNDED_OUTCOME`;
- `MANDATE_OUTCOME_SATISFIED` requires `MANDATE_OUTCOME`.

The Mandate Continuation Authority is only the maximum success-continuation ceiling; the active Run Completion Boundary remains the invocation terminal. A broader ceiling does not silently upgrade a narrower active boundary. If current user authority already establishes a broader boundary than the stored ceiling, revise/adopt the Mandate before mutation. If current authority establishes a broader active boundary within the existing ceiling, revise the Run Contract before mutation. Otherwise return only the exact unresolved boundary or authority gap. Never close a smaller boundary merely to avoid that revision, and never shrink Required Named Items to fit it.

Concrete counterexample:

```text
Mandate Continuation Authority: CURRENT_INCREMENT
Run Completion Boundary: NAMED_REQUIRED_ITEMS_DELIVERED
Required Named Items: A, B
Current evidence: A and B require multiple Increments
```

This form is not `CLOSED`. It requires an explicit Mandate revision or a user-owned boundary change.

### Normative cross-field scenarios

| Scenario | Condition | Required result |
| --- | --- | --- |
| `WHOLE_REQUIRED_NO_INCREMENT` | broader Required Named Items exist, current-Increment coverage is not established, and the boundary is `READY_TICKET_SET`, `CURRENT_INCREMENT_IMPLEMENTED`, or `CURRENT_INCREMENT_DELIVERED` | `CLOSED` is forbidden; revise from already-clear broader current authority or return `USER_INPUT_REQUIRED`. |
| `WHOLE_REQUIRED_FOUNDATION_INCREMENT` | a selected foundation/partial Increment leaves unsatisfied Required Named Items outside it while the active boundary is a current-Increment terminal | `CONTRACT_DRIFT`; do not enter Ask Matt until the Run Contract is revised from current authority or the exact boundary decision returns to the user. |
| `CURRENT_INCREMENT_REQUIRED_ONLY` | every unsatisfied Required Named Item is covered by the selected current Increment and the delivery-stage combination matches the boundary | the corresponding current-Increment boundary is allowed. |
| `WHOLE_REQUIRED_BOUNDED_OUTCOME` | broader Required Named Items remain, the boundary is `BOUNDED_OUTCOME_SATISFIED`, and the Mandate ceiling permits it | `CLOSED` is allowed; project only one current Increment while preserving outer Required Named Items and the Completion Predicate. |
| `LEAF_APPROVAL_ONLY` | Scope, Intent Anchor, Behavior/UI, Spec, Ticket, or current Increment receives only its owning leaf approval/confirmation | outer Goal Outcome, required/candidate classification, delivery stages, Run Completion Boundary, and Completion Predicate remain unchanged. |
| `REQUIRED_REMAINS_AFTER_DELIVERY` | the current Increment is delivered but broader Required Named Items or the broader outcome predicate remain unsatisfied | `RUN_COMPLETE` is forbidden; use fresh-state success re-entry and its existing next disposition. |

## Carry-forward and reshaping

Keep the closed Run Contract active across Scope Shaper, Ask Matt, To Spec, To Tickets, separate delivery, corrective re-entry, and success re-entry for this invocation.

Pass only its decision-critical fields to another owner:

- Goal Outcome;
- Required Named Items;
- Candidate Named Items;
- Required Item Policy;
- Implementation and Verification;
- Run Completion Boundary;
- Completion Predicate; and
- Authoritative Readback.

Approval or confirmation of Scope, an Intent Anchor, Behavior/UI authority, a Spec, a Ticket, or the current Increment is leaf-local and is not by itself an outer Run Contract revision. Goal Outcome, required/candidate classification, Required Item Policy, Implementation, Verification, Run Completion Boundary, and Completion Predicate change only when current user authority actually changes or already clearly determines that outer-run meaning. Natural-language user authority is sufficient; do not require the user to name Run Contract fields explicitly, but do not treat a leaf approval as withdrawal or narrowing of broader authority.

A reshape may change the current Increment, Spec, Ticket Set, ordering, and denominator. It does not erase Required Named Items, convert them into candidates, or lower the Run Completion Boundary. Recompute the current canonical denominator after a valid reshape and continue against the same Run Contract.

Candidate Named Items may be preserved, replaced, deferred, or dropped when the Mandate and evidence establish a materially better route. A material user revision may move an item between lists or change the Required Item Policy. Apply the new authority prospectively and record a concise material trace entry when the revision changes planning meaning or completion.

## Completion discipline

Planning phase completion is not Adaptive run completion unless the active boundary is `READY_TICKET_SET`.

Likewise:

- one implementation result is not `CURRENT_INCREMENT_IMPLEMENTED`;
- `CURRENT_INCREMENT_IMPLEMENTED` is not independent verification and does not mark Tickets `done`;
- one Ticket `done` is not `CURRENT_INCREMENT_DELIVERED`;
- one delivered Increment is not `NAMED_REQUIRED_ITEMS_DELIVERED` when Required Named Items remain;
- Candidate Named Items never block completion unless the user revises them into Required Named Items;
- delivered Tickets are not proof of an outcome-satisfaction boundary without fresh authoritative readback; and
- a provisional Work Package or Increment list is never a completion queue.

Emit whole-run success only when the active Completion Predicate is actually satisfied. `RETURN_TO_USER`, `BLOCKED`, `INCONCLUSIVE`, `CONTRACT_DRIFT`, unavailable authority, and no-material-progress are incomplete returns, not successful completion.

## Persistence boundary

The Run Contract is invocation-local authority. Render it at activation and carry it in the current request/context; do not create a required third durable companion artifact or persistent run state.

When its meaning materially affects later interpretation, summarize the relevant user-owned required/candidate classification, delivery-stage revision, or completion revision in `ADAPTIVE-PLANNING-TRACE.md`. Do not log routine phase transitions, delivery progress, retry counts, or private reasoning.
