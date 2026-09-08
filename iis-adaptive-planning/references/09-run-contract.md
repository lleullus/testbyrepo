# Adaptive Run Contract Closure

## Purpose

Close the meaning of one explicit Adaptive invocation before planning mutation so that current invocation cannot stop at a smaller result than the user assigned, silently treat required work as disposable, or collapse a mixed required/candidate assignment into one inaccurate list-wide label.

The Run Contract answers seven questions:

1. what result this invocation must produce;
2. which user-named items are required obligations and which are candidate means;
3. which delivery stages the user authorized for this invocation;
4. which execution boundary counts as whole-run completion;
5. what observable evidence proves that boundary is satisfied;
6. whether this exact closed contract requires direct user release before the first mutation; and
7. which user-selected model and effort each enabled SUBAGENT delivery stage will use.

It is a compact invocation contract, not a second Mandate, approval ceremony, workflow database, execution ledger, or roadmap.

## Admission rule

Before the first Adaptive planning mutation:

1. inspect the current user instruction, applicable Mandate, canonical planning authority, and inspectable current facts;
2. normalize them into the form in [../templates/ADAPTIVE-RUN-CONTRACT.template.md](../templates/ADAPTIVE-RUN-CONTRACT.template.md), including the guide-backed delivery model selection below;
3. set `Run Contract Approval Gate: required` only when the current user uses exact `/승인게이트` as an affirmative directive/modifier on the current explicitly active Adaptive invocation; otherwise set `not_required`. Quoted, explanatory, hypothetical, or negated mentions do not activate the gate, and `/승인게이트` does not activate Adaptive by itself;
4. mark the form `CLOSED` only when every material field is determined by current authority and each applicable delivery model selection is user-specified or user-confirmed, not merely recommended;
5. when one or more material fields remain unresolved, mark it `USER_INPUT_REQUIRED` and ask only for the smallest unresolved field whose different answers would change required scope, candidate freedom, delivery stages, delivery model/effort selection, success continuation, or completion meaning;
6. when the form is `CLOSED` and `Run Contract Approval Gate: required`, render the exact current form and STOP before mutation until the user directly approves that rendered contract; and
7. do not begin Scope, Behavior/UI, Spec, Ticket, implementation, or verification mutation until the contract is `CLOSED` and any required Run Contract Approval Gate has been directly satisfied.

Read-only inspection needed to close inspectable facts is allowed. Do not ask the user to restate information that current authority already determines. A fully derived `CLOSED` form proceeds without another approval prompt only when `Run Contract Approval Gate: not_required`; the explicit gate is the only Run Contract-local pre-mutation approval exception.

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

Preserve the current Adaptive default: explicit Adaptive activation selects `Implementation: yes` and `Verification: yes` unless current user authority overrides either stage. `Verification: yes` means the current Ticket must pass the required `ready-ticket-heuristic-probe` gate before final `ready-ticket-verify`; heuristic probing is an internal verification-enabled delivery gate, not a third Run Contract field or separate whole-run terminal.

When current authority supplies no planning-only, implementation-only, no-verification, named-required-item, bounded-outcome, or Mandate-outcome terminal, the default current-Increment terminal is `CURRENT_INCREMENT_DELIVERED`. Close that default only when the Required-item coverage invariant permits a current-Increment boundary; do not use it to shrink broader Required Named Items, replace a broader outcome already assigned by the user, or bypass an unresolved coverage or Mandate-ceiling decision.

Apply exact overrides independently:

- planning-only, stop-at-Ready-Tickets, no implementation and no verification -> `no` / `no`;
- implement but do not verify -> `yes` / `no`;
- verify an already implemented current target without implementation -> `no` / `yes` when current evidence can bind one stable current target and the separate heuristic-probe/verifier admissions permit it;
- do not implement -> never infer implementation authority merely because verification or a broader outcome was requested;
- do not verify -> never run the heuristic-probe gate or verifier and never claim `done`.

The fields express the outer invocation envelope only. They do not change the exact authority, admission, or result ownership of `ready-ticket-implement`, `ready-ticket-heuristic-probe`, or `ready-ticket-verify`.

Delegated implementation/verification checkpoints and Parent continuation decisions are invocation-local delivery messages only. They do not add a Run Contract field, do not modify `Implementation` or `Verification`, do not activate or satisfy the `/승인게이트` Run Contract Approval Gate, and do not require a template change. Their phase-release authority comes from the already closed Run Contract, current user instructions, and the exact delivery skill contract.

### Delivery Model Selection

Use the repository-level guide at `~/project/iis-skills/model-selection-guide.md` as the single replaceable recommendation source; expand `~` against the current user's home directory, not the working directory or Skill directory. Its initial contents are the user-supplied IIS Model Selection Guide v4.3. Both the repository Skill and its installed copy read this file directly from the repository root; do not bundle a copy or symlink in the Skill payload. Update or replace that file at the same path to change future recommendations; guide-only edits require no Skill synchronization. Do not copy its rankings, prices, named-model defaults or escalation ladders into Skill prompts, templates or code. A current user-supplied alternative guide path overrides this default path for this invocation only. Record the resolved guide path and authored version actually read, without introducing a guide registry or digest gate.

The guide supplies operational recommendations, not product authority, capability proof, model-selection consent, actual per-Ticket cost, or evidence that a model can satisfy an IIS role. Read its applicable role/effort sections and its score-interpretation limits before recommending a configuration. Do not select the highest score or effort automatically.

For each enabled delivery stage, first apply the execution-mode contract. A stage explicitly set to `DIRECT` uses the current Main and needs no child-model question. A disabled stage has no model selection. `Verification: no` excludes both the probe and verifier rows from selection; this table adds no third delivery-stage switch. For `SUBAGENT`, bind the model and effort from an explicit current user instruction or an already user-confirmed selection applicable to this invocation. Reuse an unambiguous instruction covering all delivery stages, and let an exact stage override affect only that stage. Preserve any already specified model or effort when completing a partial choice; ask only for its missing or ambiguous components. Check the exact currently available executable configuration for every selected choice, including fully supplied choices. Do not ask the user to repeat a settled choice.

When a required selection is missing:

1. Inspect the currently available model/agent configurations exposed by the active harness. Resolve guide labels and effort to an exact available configuration; do not invent identifiers, aliases or availability. An exposed host default is not user consent to use it.
2. Read the current guide and recommend one coherent configuration for the missing stages from the present Goal/constraints: routine versus broad execution/debugging, reasoning/authority ambiguity, failure cost, and any user budget/latency preference. Explain the recommendation with the applicable guide section and the workload fact, plus a meaningful cost/quality alternative when useful. Recommend under current known scope; do not demand future Ticket implementation details merely to choose models.
3. Show the recommendation separately from selected values. Ask once for all missing selections, allowing acceptance of the recommendation, one model/effort for all applicable stages, or stage-specific choices. Keep settled choices unchanged. Until the user confirms, keep `Status: USER_INPUT_REQUIRED` and include those exact missing model/effort choices in `Unresolved Field` without dropping unrelated unresolved fields; do not start mutation or dispatch the recommendation.
4. On confirmation, record the selected model/effort and its current user-instruction/confirmation basis, then close the form if all other fields are resolved. Model selection is input resolution, not a new approval gate and not satisfaction of an active `/승인게이트` release. Standing delegated planning confirmation cannot turn a recommendation into model-selection consent.

If the guide is missing or unreadable, say so and request an accessible replacement or direct model choices; do not recommend from a remembered table. If a user-selected model/effort is unavailable or ambiguous, retain that choice as unresolved, explain the exact mismatch and ask for a confirmed available alternative or clarification. Never silently substitute another model, effort or execution mode. A model that is already fully user-specified needs no guide-based recommendation or extra confirmation merely because the guide is unavailable.

The probe row chooses its delegated lane-executor model, not a new Probe Lead: Main remains Lead and worker count remains derived from admitted lanes. One selected configuration covers that stage's lanes unless the user explicitly selects a bounded lane-specific configuration. Only an applicable current owner result establishing zero delegated lanes makes the enabled probe's model `Not applicable`; do not predict this from task simplicity or start early delivery admission to decide it. Otherwise select the stage's model configuration without inventing lanes, workers or a fixed worker count.

Outer Main remains the current main session; a guide recommendation does not switch its model. The guide's Challenger advice never activates adversarial consensus or designates a Challenger. Only when the user separately requests an Outer Main recommendation or explicitly activates the Challenger gate may its relevant guide section inform a recommendation, subject to the existing user-owned model change/designation boundary. Do not add either role to the mandatory delivery-model questions.

Carry confirmed choices across Tickets and re-entry within this invocation. Guide updates, a failed attempt, or a newly attractive ranking do not change them. If a different model/effort would now be appropriate, recommend only the affected revision and obtain user confirmation before dependent dispatch. This does not revise Goal, Scope, delivery-stage authority or the Completion Predicate. Keep these choices in the invocation-local Run Contract and delivery assignments, not canonical Spec/Ticket metadata or a persistent worker roster.


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
- `CURRENT_INCREMENT_DELIVERED` — every current canonical Ticket in the approved Ready Ticket Set has reached exact `Status: done` through the owning one-exact-Ticket verification lifecycle, every approved parent-Spec/Behavior/UI obligation applicable to this current Increment has an acceptance owner in the existing Ticket Set, and that owner's current attributable evidence/readback closes the obligation at its authored boundary. The complete `done` denominator is necessary but is not sufficient by itself. Future, Non-Goal, candidate, and unrelated preserved obligations that do not apply to the current Increment are outside this boundary.
- `NAMED_REQUIRED_ITEMS_DELIVERED` — every Required Named Item is delivered and its applicable observable result is confirmed. Candidate Named Items do not block this boundary. This boundary may span more than one Increment.
- `BOUNDED_OUTCOME_SATISFIED` — the exact bounded outcome assigned to this run is satisfied in fresh actual product state.
- `MANDATE_OUTCOME_SATISFIED` — the Mandate's Desired Product Outcome is satisfied in fresh actual product state.

An implementation-only multi-Increment promise is not silently invented. If required named items cannot fit in the current Increment and the user disables verification, current verified success-re-entry rules cannot safely guarantee `NAMED_REQUIRED_ITEMS_DELIVERED`; return the smallest boundary or verification decision instead of silently reducing the required list.

### Completion Predicate

Write one concise observable predicate that distinguishes successful whole-run completion from a planning phase, one Ticket, one Increment, or roadmap progress. For a delivered current-Increment predicate, name both the complete canonical `done` denominator and closure of every applicable parent obligation through its existing acceptance owner and current attributable readback; do not make status aggregation the whole predicate.

Examples:

```text
Every Ticket in the current validated Ready Ticket Set has an exact implementation report with Completion: COMPLETE, and Verification is no.
```

```text
Every Ticket in the current validated Ready Ticket Set is exact Status: done, and every approved parent obligation applicable to this Increment is acceptance-owned in that Set and closed by the owning Ticket's current attributable evidence and authoritative readback.
```

```text
Every Required Named Item exposes the user-visible result assigned in this Run Contract and its authoritative readback confirms it.
```

Do not use `all planned work is done`, WP exhaustion, provisional-horizon exhaustion, Ticket titles, or agent reports alone as an outcome-satisfaction predicate.

### Authoritative Readback

Identify the current product surface, canonical Ticket state, exact implementation result, operator evidence, or other authority that can prove the Completion Predicate.

For `CURRENT_INCREMENT_IMPLEMENTED`, use the complete current Ticket denominator, each exact implementation result, and the unchanged canonical Ticket statuses. An implementation report proves implementation lifecycle completion only; it does not prove independent verification or `done`.

For `CURRENT_INCREMENT_DELIVERED`, use the current approved parent and validated Ticket Set to determine which obligations apply, the exact existing Ticket acceptance boundary that owns each obligation, the complete canonical status denominator, and the current evidence/readback produced or directly inspected at those boundaries. An exact `done` status or historical owner report establishes only the scope it actually adjudicated. A required `INCONCLUSIVE`, unknown, `Evidence limit`, or `Remaining uncertainty` is not erased by aggregation; if it leaves an applicable obligation undecidable, whole-run success is unavailable. An approved limited result may close only the canonical fact or approved absence it actually establishes, never a direct runtime/operator/external result that it did not observe. Source, artifact, document, or structure obligations whose approved acceptance boundary is canonical inspection remain valid without invented runtime evidence.

An attributable current contradiction establishes that the active predicate is not satisfied; it is not an unknown merely because an earlier owner report claimed acceptance. Outer Main may report that whole-run fact without issuing a new AC/Ticket verdict. Keep the exact counterexample and existing owner, then obey the current continuation authority; a user-imposed read-only stop needs no new product-choice prompt.

Use `Not yet established` only when establishing the readback is itself legitimate planning work. The run cannot terminate successfully until an attributable readback exists.

### Source Authority

Record the current instruction and applicable Mandate revision concisely. Do not fabricate a user quote.

### Run Contract Approval Gate

Use exactly one value:

- `not_required` — default. No affirmative gate modifier applies to this exact Adaptive invocation, so a fully derived `CLOSED` contract proceeds under the normal Adaptive rules.
- `required` — the current user explicitly applied `/승인게이트` as an affirmative directive/modifier to this exact Adaptive invocation. Render the complete current `CLOSED` Run Contract and STOP before the first planning or delivery mutation until the user directly approves that rendered contract.

This gate is Run Contract-local execution release only. It is not Adaptive activation, a Mandate field, a product requirement, a Run Completion Boundary, a Return-to-User Boundary, a Baseline leaf approval, or a delivery approval. Do not infer it from risk, size, uncertainty, Required Named Items, enabled verification, or any other heuristic. Do not activate it from quoted, explanatory, hypothetical, or negated uses of `/승인게이트`.

`Run Contract Approval Gate: required` does not change `Status: CLOSED` into `USER_INPUT_REQUIRED`: the contract meaning is already closed; mutation release is merely withheld. Do not create `AWAITING_APPROVAL`, `APPROVED`, `REJECTED`, expiry, attempt, or other approval-state machinery. Current-conversation direct user approval of the exact rendered contract is sufficient, and standing delegation cannot satisfy this gate.

If the user's approval response materially changes Goal Outcome, Required Named Items, Candidate Named Items, Required Item Policy, Implementation, Verification, Run Completion Boundary, Completion Predicate, or the completion meaning of Authoritative Readback, apply the new authority, re-close and re-render the revised Run Contract, and require fresh direct approval. Scope shape, Increment decomposition, faithful Spec/Ticket projection, candidate treatment already allowed by the closed contract, implementation details, or delivery progress do not retrigger this Run Contract gate by themselves.

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
- `CURRENT_INCREMENT_DELIVERED` always defines success as the complete current canonical Ticket denominator plus current closure of every applicable parent obligation through an existing Ticket acceptance owner; it is never one selected Ticket or status aggregation alone;
- the Authoritative Readback must identify how current attributable evidence will decide each applicable authored acceptance boundary; successful outcome or delivered-boundary assessment requires that evidence, but evidence legitimately created by the planned delivery may remain `Not yet established` at initial Run Contract closure;
- the Run Completion Boundary must remain within current user authority and the Mandate's Continuation Authority ceiling;
- each enabled SUBAGENT stage that needs a child configuration has an exact user-specified or user-confirmed model/effort; recommendations and host defaults alone cannot close that field;
- disabled or explicit DIRECT stages do not require child-model selection, and model/effort choices neither enable a stage nor change its mode;
- `Run Contract Approval Gate` is `required` only from the affirmative exact invocation modifier above and otherwise is `not_required`; and
- an active required gate preserves `Status: CLOSED` but forbids mutation until direct user approval of the rendered current form.

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
| `DEFAULT_ADAPTIVE_CURRENT_INCREMENT` | explicit Adaptive activation supplies no narrower stop, broader named-item/outcome terminal, or unresolved required-item coverage | close `Implementation: yes`, `Verification: yes`, and `CURRENT_INCREMENT_DELIVERED` as the default current-Increment terminal. |
| `REQUIRED_REMAINS_AFTER_DELIVERY` | the current Increment is delivered but broader Required Named Items or the broader outcome predicate remain unsatisfied | `RUN_COMPLETE` is forbidden; use fresh-state success re-entry and its existing next disposition. |
| `POST_DELIVERY_EVIDENCE_GAP` | the current Increment is delivered under a broader boundary but attributable authoritative readback cannot determine satisfaction or the need for more construction | return `EVIDENCE_REQUIRED`; do not infer completion, product defect, or Scope Shaper re-entry. |
| `CURRENT_INCREMENT_DONE_WITH_GAP` | every current Ticket is exact `done`, but an applicable parent obligation has no existing Ticket acceptance owner or its required current evidence/readback is absent, limited beyond the approved claim, stale, or inconclusive | `RUN_COMPLETE` is forbidden; return the exact Ticket-projection/upstream planning gap when ownership is missing, or `EVIDENCE_REQUIRED` when the owner exists but attributable evidence cannot decide the obligation. Do not create another verifier or reopen `done` history. |
| `CURRENT_INCREMENT_FUTURE_ONLY` | every applicable current-Increment obligation is owned and currently closed, and only future, candidate, Non-Goal, or unrelated obligations remain | the current-Increment boundary may complete; do not enlarge it with non-applicable whole-Goal work. |

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

Outer Main also carries the selected Delivery Model Selection and user-confirmation basis to the relevant delivery owner only. Pass that stage's resolved model/effort through its existing assignment path; do not ask planning leaves to select models or write them into canonical artifacts. If current exposed capability cannot execute the selection, return that exact selection/capability issue rather than substituting a guide recommendation.

Approval or confirmation of Scope, an Intent Anchor, Behavior/UI authority, a Spec, a Ticket, or the current Increment is leaf-local and is not by itself an outer Run Contract revision. Goal Outcome, required/candidate classification, Required Item Policy, Implementation, Verification, Run Completion Boundary, and Completion Predicate change only when current user authority actually changes or already clearly determines that outer-run meaning. Natural-language user authority is sufficient; do not require the user to name Run Contract fields explicitly, but do not treat a leaf approval as withdrawal or narrowing of broader authority.

Do not pass `Run Contract Approval Gate` downstream as a Scope, Ask Matt, Spec, Ticket, implementation, or verification approval requirement. It remains an outer Run Contract release control. Once the exact rendered contract has been directly approved, downstream owners follow their existing authority unless the Run Contract's decision-critical meaning is materially revised as described above.

A reshape may change the current Increment, Spec, Ticket Set, ordering, and denominator. It does not erase Required Named Items, convert them into candidates, or lower the Run Completion Boundary. Recompute the current canonical denominator after a valid reshape and continue against the same Run Contract.

Candidate Named Items may be preserved, replaced, deferred, or dropped when the Mandate and evidence establish a materially better route. A material user revision may move an item between lists or change the Required Item Policy. Apply the new authority prospectively and record a concise material trace entry when the revision changes planning meaning or completion.

## Completion discipline

Planning phase completion is not Adaptive run completion unless the active boundary is `READY_TICKET_SET`.

Likewise:

- one implementation result is not `CURRENT_INCREMENT_IMPLEMENTED`;
- `CURRENT_INCREMENT_IMPLEMENTED` is not independent verification and does not mark Tickets `done`;
- a complete Ticket `done` denominator is not `CURRENT_INCREMENT_DELIVERED` while an applicable parent obligation lacks an existing acceptance owner or current attributable closure;
- one delivered Increment is not `NAMED_REQUIRED_ITEMS_DELIVERED` when Required Named Items remain;
- Candidate Named Items never block completion unless the user revises them into Required Named Items;
- delivered Tickets are not proof of an outcome-satisfaction boundary without fresh authoritative readback; and
- a provisional Work Package or Increment list is never a completion queue.

Emit whole-run success only when the active Completion Predicate is actually satisfied. `RETURN_TO_USER`, `EVIDENCE_REQUIRED`, `BLOCKED`, `INCONCLUSIVE`, `CONTRACT_DRIFT`, unavailable authority, and no-material-progress are incomplete returns, not successful completion.

## Persistence boundary

The Run Contract is invocation-local authority. Render it at activation and carry it in the current request/context; do not create a required third durable companion artifact, persistent run state, or approval ledger. An active `/승인게이트` is likewise invocation-local and does not persist into later Adaptive invocations unless the user explicitly applies it again.

When its meaning materially affects later interpretation, summarize the relevant user-owned required/candidate classification, delivery-stage revision, or completion revision in `ADAPTIVE-PLANNING-TRACE.md`. Do not log routine phase transitions, delivery progress, retry counts, or private reasoning.
