# Adaptive Run Contract Closure

## Purpose

Close the meaning of one explicit Adaptive invocation before planning mutation so that it preserves the user's assigned Goal Outcome and required work through every lower contract and completion claim, without treating candidates as obligations or substituted evidence as actual achievement.

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

1. inspect the current user instruction, applicable Mandate, applicable Product Thesis conclusion, canonical planning authority, and inspectable current facts;
2. after Product Thesis has formed any newly required product meaning and the Mandate has been normalized or revalidated, normalize the current invocation into the form in [../templates/ADAPTIVE-RUN-CONTRACT.template.md](../templates/ADAPTIVE-RUN-CONTRACT.template.md), including the guide-backed delivery model selection below;
3. set `Run Contract Approval Gate: required` only when the current user uses exact `/승인게이트` as an affirmative directive/modifier on the current explicitly active Adaptive invocation; otherwise set `not_required`. Quoted, explanatory, hypothetical, or negated mentions do not activate the gate, and `/승인게이트` does not activate Adaptive by itself;
4. mark the form `CLOSED` only when every material field is determined by current authority, the Goal and required-item coverage invariant below holds, stage/ceiling meaning is consistent, and each applicable delivery model selection is user-specified or user-confirmed, not merely recommended;
5. when one or more material fields remain unresolved, mark it `USER_INPUT_REQUIRED` and ask only for the smallest unresolved field whose different answers would change required scope, candidate freedom, delivery stages, delivery model/effort selection, success continuation, or completion meaning;
6. when the form is `CLOSED` and `Run Contract Approval Gate: required`, render the exact current form and STOP before mutation until the user directly approves that rendered contract; and
7. do not begin Scope, Behavior/UI, Spec, Ticket, implementation, or verification mutation until the contract is `CLOSED` and any required Run Contract Approval Gate has been directly satisfied.

Read-only inspection needed to close inspectable facts is allowed. Do not ask the user to restate information that current authority already determines. A fully derived `CLOSED` form proceeds without another approval prompt only when `Run Contract Approval Gate: not_required`; the explicit gate is the only Run Contract-local pre-mutation approval exception.

## Required fields

### Goal Outcome

State the durable user/operator result assigned to this invocation as a faithful derivative of the current user's words, not background aspiration or a new source of authority. Applicable user instructions, constraints, and explicit stage/stop limits outrank this summary and every Boundary, Predicate, Increment, Spec, Ticket, method, and owner report. It may equal the Mandate's Desired Product Outcome or be a narrower current assignment; a broad long-term Mandate alone does not enlarge this invocation.

When current product meaning was established through Product Thesis Design, keep Goal Outcome and named-item meaning faithful to that conclusion and current user authority. Run Contract closure preserves product meaning; it does not recreate the Reason to Exist, Core Utility, Core Completion Loop, truth/causal framing, or non-core classification. Newer explicit user authority takes precedence, and a narrower current assignment remains narrow.

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

Explicit Adaptive activation preserves Implementation yes and Verification yes unless current authority overrides either independently. Implementation yes first needs current execution-method review. Verification yes invokes the integrated final verifier directly on a stable actual target; discovery is inside that cycle, not a third switch or separate whole-run terminal.

The default current-Increment terminal is `CURRENT_INCREMENT_DELIVERED` only when the Goal and required-item coverage invariant establishes that it closes the entire current assignment and no explicit stage/stop override applies. A clear natural-language assignment of a broader outcome supplies its completion authority without naming an enum or saying `끝까지` or `여러 Increment를 돌려`. Do not replace it with the default or bypass an unresolved coverage or Mandate-ceiling decision.

Apply exact overrides independently:

- planning-only, stop-at-Ready-Tickets, no implementation and no verification -> `no` / `no`;
- execution-preparation-only -> no / no with READY_EXECUTION_PLANS and exact required preparation Tickets, not READY_TICKET_SET;
- implement but do not verify -> `yes` / `no`;
- verify an already implemented current target without implementation -> no / yes when the actual stable target is attributable and the verifier can capture its immutable verification binding; no new execution plan ADMIT is required;
- do not implement -> never infer implementation authority from verification or a broader outcome;
- do not verify -> no final discovery/verdict/done, but a current pre-implementation independent Plan Review still applies when Implementation is yes.

These two fields express the invocation envelope, not exact owner authority or admission. Preparation belongs to ready-ticket-plan, implementation to ready-ticket-implement, integrated semantic adjudication to ready-ticket-verify, and the narrow post-verdict Ticket status progression to the caller's ready_finalize step.

Explicit planning-only, preparation-only, and implementation-only assignments close only their requested stage's actual result, not unperformed product delivery or verification. Do not invent a stage-only interpretation to shrink an assigned product Goal. A pause/stop is not a successful narrower Goal unless current user authority actually changes the assignment; preserve any unresolved distinction and disabled stages.

Implementation and verification delivery ownership remains invocation-local and terminal-result based. A material implementation method change ends the affected implementation invocation and returns to preparation; a verifier returns one terminal semantic result and binding before caller finalization. These owner boundaries do not add a Run Contract field, do not modify `Implementation` or `Verification`, do not activate or satisfy the `/승인게이트` Run Contract Approval Gate, and do not require a template change.

### Delivery Model Selection

Use the repository-level guide at `~/project/iis-skills/model-selection-guide.md` as the single replaceable recommendation source; expand `~` against the current user's home directory, not the working directory or Skill directory. Its initial contents are the user-supplied IIS Model Selection Guide v4.3. Both the repository Skill and its installed copy read this file directly from the repository root; do not bundle a copy or symlink in the Skill payload. Update or replace that file at the same path to change future recommendations; guide-only edits require no Skill synchronization. Do not copy its rankings, prices, named-model defaults or escalation ladders into Skill prompts, templates or code. A current user-supplied alternative guide path overrides this default path for this invocation only. Record the resolved guide path and authored version actually read, without introducing a guide registry or digest gate.

The guide supplies operational recommendations, not product authority, capability proof, model-selection consent, actual per-Ticket cost, or evidence that a model can satisfy an IIS role. Read its applicable role/effort sections and its score-interpretation limits before recommending a configuration. Do not select the highest score or effort automatically.

Apply each role/stage's current execution-mode contract before model selection. Explicit DIRECT uses current Main and needs no child-model question. Disabled implementation/verification has no model row selection. For actual delegated preparation roles or enabled SUBAGENT stages, preserve explicit current model/effort and any unambiguous confirmed selection covering those roles. Reuse a broad applicable user choice, let exact overrides affect only their scope, and check actual exposed configuration availability without inventing identifiers. Verification no excludes the final verifier, not the current independent Plan Review needed by Implementation yes.

When a required selection is missing:

1. Inspect the currently available model/agent configurations exposed by the active harness. Resolve guide labels and effort to an exact available configuration; do not invent identifiers, aliases or availability. An exposed host default is not user consent to use it.
2. Read the current guide and recommend one coherent configuration for the missing stages from the present Goal/constraints: routine versus broad execution/debugging, reasoning/authority ambiguity, failure cost, and any user budget/latency preference. Explain the recommendation with the applicable guide section and the workload fact, plus a meaningful cost/quality alternative when useful. Recommend under current known scope; do not demand future Ticket implementation details merely to choose models.
3. Show the recommendation separately from selected values. Ask once for all missing selections, allowing acceptance of the recommendation, one model/effort for all applicable stages, or stage-specific choices. Keep settled choices unchanged. Until the user confirms, keep `Status: USER_INPUT_REQUIRED` and include those exact missing model/effort choices in `Unresolved Field` without dropping unrelated unresolved fields; do not start mutation or dispatch the recommendation.
4. On confirmation, record the selected model/effort and its current user-instruction/confirmation basis, then close the form if all other fields are resolved. Model selection is input resolution, not a new approval gate and not satisfaction of an active `/승인게이트` release. Standing delegated planning confirmation cannot turn a recommendation into model-selection consent.

If the guide is missing or unreadable, say so and request an accessible replacement or direct model choices; do not recommend from a remembered table. If a user-selected model/effort is unavailable or ambiguous, retain that choice as unresolved, explain the exact mismatch and ask for a confirmed available alternative or clarification. Never silently substitute another model, effort or execution mode. A model that is already fully user-specified needs no guide-based recommendation or extra confirmation merely because the guide is unavailable.

Include preparation selections only for actual delegated Planner and Plan Review invocations. One current user choice may cover both applicable roles; two different models or mandatory per-role child rows are not required. Lead fan-in is the writer-side continuation and does not create another selection row. DIRECT preparation does not permit writer self-approval in its writing invocation: an actual separate reviewer invocation must be available under current authority, otherwise return the preparation limit without ADMIT. Reuse an attributable current independent review where valid; do not create hidden delegation or a model-selection ceremony for work not being dispatched. Final discovery assistance is permitted only by the current verification-stage delegation contract, never a hidden separate model row.

Outer Main remains the current main session; a guide recommendation does not switch its model. The guide's Challenger advice never activates adversarial consensus or designates a Challenger. Only when the user separately requests an Outer Main recommendation or explicitly activates the Challenger gate may its relevant guide section inform a recommendation, subject to the existing user-owned model change/designation boundary. Do not add either role to the mandatory delivery-model questions.

Carry confirmed choices across Tickets and re-entry within this invocation. Guide updates, a failed attempt, or a newly attractive ranking do not change them. If a different model/effort would now be appropriate, recommend only the affected revision and obtain user confirmation before dependent dispatch. This does not revise Goal, Scope, delivery-stage authority or the Completion Predicate. Keep these choices in the invocation-local Run Contract and delivery assignments, not canonical Spec/Ticket metadata or a persistent worker roster.


### Run Completion Boundary

Use exactly one value:

- `READY_TICKET_SET`
- `READY_EXECUTION_PLANS`
- `CURRENT_INCREMENT_IMPLEMENTED`
- `CURRENT_INCREMENT_DELIVERED`
- `NAMED_REQUIRED_ITEMS_DELIVERED`
- `BOUNDED_OUTCOME_SATISFIED`
- `MANDATE_OUTCOME_SATISFIED`

Boundary meaning:

- `READY_TICKET_SET` — one approved current Spec plus its validated complete Ready Ticket Set exists.
- `READY_EXECUTION_PLANS` — the exact requested preparation Ticket set has actual current independent ADMIT in the outside-root review artifact(s) returned by READY TICKET PLAN RESULT; no implementation or final verification is claimed.
- `CURRENT_INCREMENT_IMPLEMENTED` — every current canonical Ticket in the validated Ready Ticket Set has one exact implementation lifecycle result with `Completion: COMPLETE`; verification was not requested and Ticket status remains governed by the verifier.
- `CURRENT_INCREMENT_DELIVERED` — every current canonical Ticket in the approved Ready Ticket Set has reached exact `Status: done` through the owning one-exact-Ticket verification lifecycle, every approved parent-Spec/Behavior/UI obligation applicable to this current Increment has an acceptance owner in the existing Ticket Set, and that owner's current attributable evidence/readback closes the obligation at its authored boundary. The complete `done` denominator is necessary but is not sufficient by itself. Future, Non-Goal, candidate, and unrelated preserved obligations that do not apply to the current Increment are outside this boundary.
- `NAMED_REQUIRED_ITEMS_DELIVERED` — every Required Named Item is delivered and its applicable observable result is confirmed. Candidate Named Items do not block this boundary. This boundary may span more than one Increment.
- `BOUNDED_OUTCOME_SATISFIED` — the exact bounded outcome assigned to this run is satisfied in fresh actual product state.
- `MANDATE_OUTCOME_SATISFIED` — the Mandate's Desired Product Outcome is satisfied in fresh actual product state.

An implementation-only multi-Increment promise is not silently invented. If the assigned Goal or Required Named Items need another Increment and the user disables verification, current verified success-re-entry rules cannot guarantee that broader delivery; return the smallest boundary or verification decision instead of silently reducing the obligation.

### Completion Predicate

Write one concise observable predicate whose satisfaction at the declared boundary is sufficient for the assigned Goal Outcome and every Required Named Item under the coverage invariant below, without adding unassigned outcomes or stronger acceptance. For a delivered current-Increment predicate, name both the complete canonical `done` denominator and closure of every applicable parent obligation through its existing acceptance owner and current attributable readback; do not make status aggregation the whole predicate.

Examples:

For preparation-only: every explicitly required preparation Ticket has actual current independent ADMIT, with current plan/review/product-authority identities and attributable review evidence; no smaller subset closes the request.

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

Identify the actual product surface, canonical Ticket state, exact implementation result, operator evidence, or other authority that can decide the assigned result through the Completion Predicate, not merely a weaker proxy.

A mock, stub, canned response, seeded success state, or surrogate readback cannot prove the acceptance boundary it replaces. A test runner may supply valid evidence when it executes the actual required path and observes the required state/effect. An authorized disposable environment may qualify when it uses the approved real implementation, entrypoint, storage, lifecycle, and readback. Supporting dependency doubles do not invalidate unrelated real observations, but never prove the boundary they replace. For required external effects, helper success, HTTP acceptance, or logs alone do not replace the approved effect readback.

When the requested result is an artifact, document, schema, source, plan, or simulator itself, inspect that actual deliverable and its approved meaning; do not inflate its claim into an unobserved product/runtime/external effect. A Ticket-authored fake boundary cannot override its parent meaning or current user instructions. Missing real access, environment, or authority preserves the original obligation as unknown/incomplete rather than licensing fake success.

Tool-route non-support or an argv inspection allowlist rejection alone establishes neither product-surface unavailability nor missing external authority. For an already requested and authorized actual trigger/readback, use another supported, normally authorized execution route only if it preserves active Ready binding/effect ownership, user stops, disabled stages, and side-effect authority; never bypass a guard or security/authority denial. Source evidence of contradiction does not complete an explicitly required actual observation left unperformed.

For READY_EXECUTION_PLANS use the exact required Ticket denominator, actual preparation terminal and current independent review artifact/evidence. A plan file, reviewer no-finding, JSON structure or historical ADMIT label is not sufficient. This method-readiness boundary neither satisfies product-delivery obligations nor changes named-item meaning.

For `CURRENT_INCREMENT_IMPLEMENTED`, use the complete current Ticket denominator, each exact implementation result, and the unchanged canonical Ticket statuses. An implementation report proves implementation lifecycle completion only; it does not prove independent verification or `done`.

For `CURRENT_INCREMENT_DELIVERED`, use the current approved parent and validated Ticket Set to determine which obligations apply, the exact existing Ticket acceptance boundary that owns each obligation, the complete canonical status denominator, and the current evidence/readback produced or directly inspected at those boundaries. An exact `done` status or historical owner report establishes only the scope it actually adjudicated. A required `INCONCLUSIVE`, unknown, `Evidence limit`, or `Remaining uncertainty` is not erased by aggregation; if it leaves an applicable obligation undecidable, whole-run success is unavailable. An approved limited result may close only the canonical fact or approved absence it actually establishes, never a direct runtime/operator/external result that it did not observe. Source, artifact, document, or structure obligations whose approved acceptance boundary is canonical inspection remain valid without invented runtime evidence.

An attributable current contradiction establishes that the active predicate is not satisfied; it is not an unknown merely because an earlier owner report claimed acceptance. Outer Main may report that whole-run fact without issuing a new AC/Ticket verdict. Keep the exact counterexample and existing owner, then obey the current continuation authority; a user-imposed read-only stop needs no new product-choice prompt.

Use `Not yet established` only when establishing the readback is itself legitimate planning work. The run cannot terminate successfully until an attributable readback exists.

### Source Authority

Record concise anchors to the relevant actual user instructions, constraints, explicit revisions, and applicable Mandate revision, not another copy of the derived Goal. Preserve enough source wording or an exact current-conversation reference to recover an omission in Goal/Required Named Items; do not fabricate a quote or copy the whole conversation downstream.

### Run Contract Approval Gate

Use exactly one value:

- `not_required` — default. No affirmative gate modifier applies to this exact Adaptive invocation, so a fully derived `CLOSED` contract proceeds under the normal Adaptive rules.
- `required` — the current user explicitly applied `/승인게이트` as an affirmative directive/modifier to this exact Adaptive invocation. Render the complete current `CLOSED` Run Contract and STOP before the first planning or delivery mutation until the user directly approves that rendered contract.

This gate is Run Contract-local execution release only. It is not Adaptive activation, a Mandate field, a product requirement, a Run Completion Boundary, a Return-to-User Boundary, a Baseline leaf approval, or a delivery approval. Do not infer it from risk, size, uncertainty, Required Named Items, enabled verification, or any other inference. Do not activate it from quoted, explanatory, hypothetical, or negated uses of `/승인게이트`.

`Run Contract Approval Gate: required` does not change `Status: CLOSED` into `USER_INPUT_REQUIRED`: the contract meaning is already closed; mutation release is merely withheld. Do not create `AWAITING_APPROVAL`, `APPROVED`, `REJECTED`, expiry, attempt, or other approval-state machinery. Current-conversation direct user approval of the exact rendered contract is sufficient, and standing delegation cannot satisfy this gate.

If the user's approval response materially changes Goal Outcome, Required Named Items, Candidate Named Items, Required Item Policy, Implementation, Verification, Run Completion Boundary, Completion Predicate, or the completion meaning of Authoritative Readback, apply the new authority, re-close and re-render the revised Run Contract, and require fresh direct approval. Scope shape, Increment decomposition, faithful Spec/Ticket projection, candidate treatment already allowed by the closed contract, implementation details, or delivery progress do not retrigger this Run Contract gate by themselves.

## Consistency checks

Before marking the form `CLOSED`:

At closure and when these structural fields materially change, pass the rendered current form to `../tools/check_run_contract.py` through stdin or exact `--file`. Do not rerun it on owner returns or ordinary product changes that leave the structure unchanged.

`STRUCTURE_VALID` confirms only deterministic field, list, stage, and boundary consistency below. It is not Goal/Source Authority fidelity, user approval, delivery admission, verification, finalization, or run-completion evidence; those existing owners and checks remain authoritative.

- apply the Goal and required-item coverage invariant below against relevant Source Authority, including on a supplied preclosed form; matching derived Goal/Predicate text or a `CLOSED` label is not proof of fidelity;

- no item may appear in both Required Named Items and Candidate Named Items;
- `EXACT_REQUIRED_SET` and `REQUIRED_FLOOR` require non-empty Required Named Items;
- `NONE_REQUIRED` requires exact `None required`;
- `READY_TICKET_SET` requires `Implementation: no` and `Verification: no`;
- `READY_EXECUTION_PLANS` requires both switches no, explicit execution-preparation scope and an exact required Ticket denominator whose eventual terminal requires all current independent ADMIT. Initial CLOSED authorizes preparation; it does not require reviews already to exist or silently replace requested product delivery.
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

### Goal and required-item coverage invariant

A form is `CLOSED` only when Goal Outcome and Required Named Items faithfully preserve the current user's actual assignment and satisfaction of the Completion Predicate at its declared boundary necessarily satisfies that Goal and every Required Named Item. `None required` waives no Goal obligation. Judge promised results, not word inclusion or agreement between two derived summaries; do not add unassigned outcomes or stronger acceptance to make the check conservative.

At closure, post-shape/material reshape, and owner-return/final assessment, ask: **Could this contract count as successful while the result the user assigned is still unmet?** If yes, correct the derived Goal/items/Boundary/Predicate from already-clear current authority before proceeding; return `USER_INPUT_REQUIRED` only for an actual unresolved user-owned meaning. A Predicate that is true while the assigned Goal is false is contract mismatch, not success, including in a previously `CLOSED` form. Do not lower Goal/items to fit a chosen terminal. A material recovery is traced; leaf approval, Challenger agreement, Ticket `ready`/`done`, or Parent `CONTINUE` cannot withdraw the outer obligation.

For product or feature construction with an applicable Product Thesis conclusion, test preservation specifically: could every named feature be present and the Completion Predicate pass while the applicable Core Utility is still absent? If yes, the form is not `CLOSED`. Correct Goal/items/Boundary/Predicate from the current Product Thesis and Source Authority; return to the product-meaning owner only when those sources leave a genuine product-meaning conflict or fresh evidence invalidates the thesis. This fidelity check must not expand the invocation into the whole Core Completion Loop, unassigned strategy, polish, or adjacent features.

`READY_TICKET_SET`, `CURRENT_INCREMENT_IMPLEMENTED`, and `CURRENT_INCREMENT_DELIVERED` are current-Increment terminals. They are valid only when fresh authoritative readback supports already-satisfied parts of the assignment and current authority establishes that every outstanding part of the Goal and required scope is covered by that Increment's Includes and completion contract. Unknown or partial coverage, including before shaping, cannot be assumed complete merely because no Required Named Items exist. One Increment may legitimately close the remaining whole Goal; do not force multiple Increments when coverage is established.

READY_EXECUTION_PLANS is bounded by the exact preparation Tickets named in this invocation, not automatically by the whole current Set. It may close only the preparation meaning explicitly requested for every required item; it cannot satisfy an outstanding promise to implement/deliver them or silently authorize a later Increment. Other explicit stage-only or narrow assignments likewise preserve their actual requested result and claim limits, not an unassigned broader product outcome.

`NAMED_REQUIRED_ITEMS_DELIVERED`, `BOUNDED_OUTCOME_SATISFIED`, and `MANDATE_OUTCOME_SATISFIED` may span multiple Increments when enabled stages and the Mandate ceiling permit it. Named-item delivery is insufficient if a broader assigned Goal still remains. Keep a smaller current construction choice separate from the whole-run promise; do not force all outer obligations into one Increment.

Ceiling checks use actual continuation requirements, not the boundary label alone:

- `CURRENT_INCREMENT` permits the current-Increment terminals only with full Goal/required-item coverage. It permits `NAMED_REQUIRED_ITEMS_DELIVERED` only when the current Increment closes that same full assignment.
- READY_EXECUTION_PLANS creates no success-continuation authority beyond its exact approved preparation scope; it never uses a planning-only terminal to shrink required product delivery.
- a named-item or bounded predicate that requires another Increment needs at least `BOUNDED_OUTCOME`;
- `MANDATE_OUTCOME_SATISFIED` requires `MANDATE_OUTCOME`.

The Mandate Continuation Authority is only the maximum success-continuation ceiling; the active Run Completion Boundary remains the invocation terminal. A broader ceiling does not silently upgrade a narrower assignment. If current user authority already assigns a broader outcome than the stored ceiling, revise/adopt the Mandate before mutation; if it fits the ceiling, correct the Run Contract. Natural-language outcome authority is sufficient. If completion meaning remains materially ambiguous, return only that meaning or authority gap, not a convenient current-Increment default. Never shrink Goal or Required Named Items to avoid the revision, or add an independent outcome under `EXACT_REQUIRED_SET` without current authority.

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
| `WHOLE_REQUIRED_NO_INCREMENT` | the assigned Goal or Required Named Items are broader, current-Increment coverage is not established, and the boundary is a current-Increment terminal | `CLOSED` is forbidden; revise from already-clear broader current authority or return `USER_INPUT_REQUIRED`. |
| `WHOLE_REQUIRED_FOUNDATION_INCREMENT` | a selected foundation/partial Increment leaves assigned Goal or required scope outside it while the active boundary is a current-Increment terminal | `CONTRACT_DRIFT`; do not enter Ask Matt until the Run Contract is corrected from current authority or the exact boundary decision returns to the user. |
| `CURRENT_INCREMENT_REQUIRED_ONLY` | the entire current Goal and every unsatisfied Required Named Item are covered by the selected current Increment and the stage combination matches | the corresponding current-Increment boundary is allowed, even for a broadly worded Goal. |
| `WHOLE_REQUIRED_BOUNDED_OUTCOME` | broader Goal/Required Named Items remain, the boundary is `BOUNDED_OUTCOME_SATISFIED`, and the Mandate ceiling permits it | `CLOSED` is allowed; project one current Increment while preserving outer Goal, Required Named Items, and the sufficient Predicate. |
| `LEAF_APPROVAL_ONLY` | Scope, Intent Anchor, Behavior/UI, Spec, Ticket, or current Increment receives only its owning leaf approval/confirmation | outer Goal Outcome, required/candidate classification, delivery stages, Run Completion Boundary, and Completion Predicate remain unchanged. |
| `DEFAULT_ADAPTIVE_CURRENT_INCREMENT` | explicit Adaptive activation supplies no narrower stop and full Goal/required-item coverage in the current Increment is established | close `Implementation: yes`, `Verification: yes`, and `CURRENT_INCREMENT_DELIVERED` as the default. |
| `REQUIRED_REMAINS_AFTER_DELIVERY` | the current Increment is delivered but assigned Goal or Required Named Items remain unsatisfied | `RUN_COMPLETE` is forbidden; correct a weak derived contract if needed and use fresh-state success re-entry and its existing next disposition. |
| `POST_DELIVERY_EVIDENCE_GAP` | attributable authoritative readback cannot determine satisfaction or the need for more construction | use `EVIDENCE_REQUIRED`; obtain reachable authorized readback before returning, without inferring completion, product defect, or Scope Shaper re-entry. |
| `CURRENT_INCREMENT_DONE_WITH_GAP` | every current Ticket is exact `done`, but an applicable parent obligation has no existing Ticket acceptance owner or its required current evidence/readback is absent, limited beyond the approved claim, stale, or inconclusive | `RUN_COMPLETE` is forbidden; return the exact Ticket-projection/upstream planning gap when ownership is missing, or `EVIDENCE_REQUIRED` when the owner exists but attributable evidence cannot decide the obligation. Do not create another verifier or reopen `done` history. |
| `CURRENT_INCREMENT_FUTURE_ONLY` | all assigned Goal/required scope and applicable current obligations are closed; only unassigned future, candidate, Non-Goal, or unrelated obligations remain | the current-Increment boundary may complete; do not enlarge this invocation with unassigned whole-product work. |
| `GOAL_ONLY_BROAD` | the user assigns a broader lifecycle result with `None required`, but only its first capability fits the current Increment | preserve the full Goal and derive a sufficient outcome boundary/ceiling; no enum or extra continuation phrase is needed. |
| `SOURCE_OMISSION` | the source assigns A+B, but derived Goal/items and Predicate agree only on A | restore B from Source Authority; summary self-consistency cannot close the form. |
| `WEAK_PREDICATE_PRECLOSED` | a supplied `CLOSED` form uses a broad Goal/boundary label but a Predicate satisfied by only a subset | correct the derived contract from current authority or return the exact unresolved meaning; the label does not authorize mutation or success. |
| `SUBSTITUTED_READBACK` | mocked/seeded success replaces the runtime or external boundary required by the assigned Goal | that evidence cannot close the obligation; use the existing semantic-projection owner for an invalid flow, or preserve unknown/contradiction according to real evidence. |
| `EXPLICIT_NARROW_OR_STAGE` | current user authority explicitly limits this invocation to the current result or a planning/preparation/implementation-only result | close that actual limited assignment when its evidence is sufficient; do not import the long-term Mandate as extra work or claim unperformed delivery. |
| `REAL_DISPOSABLE_OR_ARTIFACT` | authorized disposable execution observes the approved real boundary, or the actual requested artifact is directly inspected | accept only the observed approved claim; neither disposable location nor test format makes it fake. |

## Carry-forward and reshaping

Keep the closed Run Contract active across Scope Shaper, Ask Matt, To Spec, To Tickets, separate delivery, corrective re-entry, and success re-entry for this invocation.

Pass only its decision-critical fields to another owner:

- Goal Outcome;
- Required Named Items;
- Candidate Named Items;
- Required Item Policy;
- Implementation and Verification;
- Run Completion Boundary;
- Completion Predicate;
- Authoritative Readback; and
- relevant Source Authority anchors and current user constraints for that owner's scope, not the entire conversation or roadmap.

Outer Main also carries the selected Delivery Model Selection and user-confirmation basis to the relevant delivery owner only. Pass that stage's resolved model/effort through its existing assignment path; do not ask planning leaves to select models or write them into canonical artifacts. If current exposed capability cannot execute the selection, return that exact selection/capability issue rather than substituting a guide recommendation.

Approval or confirmation of Scope, an Intent Anchor, Behavior/UI authority, a Spec, a Ticket, or the current Increment is leaf-local and is not by itself an outer Run Contract revision. Goal Outcome, required/candidate classification, Required Item Policy, Implementation, Verification, Run Completion Boundary, and Completion Predicate change only when current user authority actually changes or already clearly determines that outer-run meaning. Natural-language user authority is sufficient; do not require the user to name Run Contract fields explicitly, but do not treat a leaf approval as withdrawal or narrowing of broader authority.

Do not pass `Run Contract Approval Gate` downstream as a Scope, Ask Matt, Spec, Ticket, implementation, or verification approval requirement. It remains an outer Run Contract release control. Once the exact rendered contract has been directly approved, downstream owners follow their existing authority unless the Run Contract's decision-critical meaning is materially revised as described above.

A reshape may change the current Increment, Spec, Ticket Set, ordering, and denominator. It does not erase or weaken the assigned Goal, erase Required Named Items, convert them into candidates, or lower the whole-run promise. Defer from the current Increment without removing obligations from this invocation; revalidate coverage and recompute the current canonical denominator after a valid reshape.

Candidate Named Items may be preserved, replaced, deferred, or dropped when the Mandate and evidence establish a materially better route that still satisfies the Goal. Dropping a candidate means does not waive an outcome needed for the Goal. A material user revision may change Goal or item meaning; apply only that delta prospectively, re-close affected fields and existing gates, and trace its basis without rewriting prior verdicts or `done` history.

## Completion discipline

Planning phase completion is not Adaptive run completion unless the active boundary is `READY_TICKET_SET`.

Likewise:

- one implementation result is not `CURRENT_INCREMENT_IMPLEMENTED`;
- `CURRENT_INCREMENT_IMPLEMENTED` is not independent verification and does not mark Tickets `done`;
- a complete Ticket `done` denominator is not `CURRENT_INCREMENT_DELIVERED` while an applicable parent obligation lacks an existing acceptance owner or current attributable closure;
- one delivered Increment or delivered named-item list is not whole-run completion when the assigned Goal or Required Named Items remain;
- Candidate Named Items never block completion unless the user revises them into Required Named Items;
- delivered Tickets are not proof of an outcome-satisfaction boundary without fresh authoritative readback; and
- a provisional Work Package or Increment list is never a completion queue.
- `SAFE_INCOMPLETE_HANDOFF` is a narrow non-success exception for an explicitly approved Transition Baseline at a measured safe Block boundary; it does not add a Run Completion Boundary, Run status, Ticket verdict, or whole-run success meaning.


Emit whole-run success only when the coverage invariant still holds and fresh attributable evidence satisfies the Goal and Required Named Items through the sufficient Predicate at the approved stage/claim boundary. `RETURN_TO_USER`, `EVIDENCE_REQUIRED`, `BLOCKED`, `INCONCLUSIVE`, `CONTRACT_DRIFT`, unavailable authority, and no-material-progress are incomplete returns, not success.

While the Goal is unmet and current authority/evidence determines a valid next action, continue through its existing owner in this invocation. The only exception is the measured, approved safe Block-boundary transfer defined below; otherwise obtain reachable authorized readback rather than merely announcing `EVIDENCE_REQUIRED`, and require actual fresh-state Scope Shaper re-entry for `NEXT_INCREMENT_REQUIRED`. Preserve user stops, disabled stages, external authority and the existing no-material-progress guard. Do not call an available action never attempted a no-progress repetition.

### Goal-preserving `SAFE_INCOMPLETE_HANDOFF` and fresh successor invocation

`SAFE_INCOMPLETE_HANDOFF` may terminate the current invocation incomplete only when every condition below is directly established:

1. Transition Baseline mode is explicitly opted in, the exact approved Baseline identity/revision is supplied, and its one-time approval explicitly includes inter-Block auto-continuation within the applicable Mandate/authority ceiling.
2. The current Active Block's Exit predicate is measured true through its approved readback, and the Safe Continuation Predicate is measured true through the required safety/readback facts.
3. All active effects are settled or safely contained. No unknown or response-lost non-idempotent effect is treated as safe merely because no danger is currently visible.
4. The full Goal, Required Named Items, final Completion Predicate, authoritative readback boundary, applicable Global/Path Invariants, and remaining obligations are carried forward unchanged. A Block-specific predicate never substitutes for the final transformation predicate; Required work is not narrowed, promoted to candidate, or silently dropped.
5. The handoff names the exact Baseline, Mandate, and Source Authority identities; departing Block; actual Entry/Exit and safety readbacks plus limits; remaining Goal/Required obligations; next entry inspection; successor authority/ceiling; and the caller/host action that is authorized to start the successor.

This is an ordinary incomplete terminal handoff, not `RUN_CONTRACT_SATISFIED`, `RUN_COMPLETE`, or a new completion-boundary value. The narrow rule takes precedence over the ordinary same-invocation/reporting instructions in `references/07-terminal-report.md` and `references/08-delivery-continuation.md` only for this proven approved safe transfer; those consumers remain unchanged and govern every other case. If Block Exit, Safe Continuation, effect settlement/containment, remaining-obligation preservation, or successor authority is false or unknown, do not use this disposition. Continue the authorized current owner/evidence route, or execute only the approved Safe Abort action and prove its safe-state readback when its trigger applies. If caller/host transport is unavailable, report that actual capability limit and do not claim a successor started.

The caller/host owns autonomous successor start; this protocol does not create a scheduler, controller, queue, or new approval ledger. Within the already approved continuation ceiling, a human prompt is not required for each Block, but actual dispatch/start evidence is required. The successor invocation must:

- read fresh actual state and the exact approved Baseline/Mandate/Source Authority identities;
- resolve the next eligible Block from measured entry state and ordering/invariants rather than consuming a pre-authored Increment queue;
- project exactly one new Active Block Envelope and pass only its applicable slice to Scope;
- close a fresh existing-form Run Contract preserving the full Goal/Required obligations, current stages, model choices, completion predicate, readback, gate applicability, and current source anchors, then run the normal structural consistency check; and
- enter the existing Scope route only after that fresh contract is closed and any newly applicable gate is satisfied.

The successor never resumes a serialized prior Run Contract, copies stale status/Boundary bytes as active authority, or treats the handoff text itself as proof of current state. The prior invocation remains closed and incomplete; final transformation completion still requires the fresh successor's actual authoritative readback.


## Persistence boundary

The Run Contract is invocation-local authority. Render it at activation and carry it in the current request/context; do not create a required third durable companion artifact, persistent run state, or approval ledger. An active `/승인게이트` is likewise invocation-local and does not persist into later Adaptive invocations unless the user explicitly applies it again.
An approved Transition Baseline may be durable authority for its exact map/revision and continuation ceiling, but it is separate from the invocation-local Run Contract. It is not a cursor, completion ledger, successor queue, retry log, or permission to resume prior Run Contract bytes. A successor always closes from fresh actual state and current durable authority.

When its meaning materially affects later interpretation, summarize the relevant user-owned required/candidate classification, delivery-stage revision, or completion revision in `ADAPTIVE-PLANNING-TRACE.md`. Do not log routine phase transitions, delivery progress, retry counts, or private reasoning.
