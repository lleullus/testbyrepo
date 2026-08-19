# Adaptive Planning Mandate Contract

## Purpose

The Mandate fixes **how to judge a good plan** and the maximum success-continuation authority available to Adaptive. It does not fix the exact Increment, Spec shape, Ticket count, internal design, future roadmap, or the terminal condition of every invocation.

A useful Mandate is stable enough to support reshaping while leaving planning hypotheses and invocation-local completion mutable.

```text
Intent and decision criteria: comparatively stable
Maximum success-continuation authority: comparatively stable
Current invocation terminal: closed by the Adaptive Run Contract
Current INC / planning shape: mutable
Canonical IIS artifacts: durable and traceable
```

## Required meaning

Normalize the current user authority into these fields:

1. **Desired Product Outcome** — the durable user/operator result the initiative should move toward.
2. **Why / User Value** — why that outcome matters; use it to distinguish product value from implementation convenience.
3. **Decision Priorities** — ordered criteria for resolving multiple acceptable planning shapes.
4. **Hard Constraints** — existing behavior, compatibility, authority, data, external contract, or other boundary the user does not delegate away.
5. **Non-Goals** — capabilities or maturity explicitly outside the intended direction.
6. **Delegated Planning Authority** — what Scope/INC reshaping and product-planning recommendation classes may be settled without a new per-artifact user response.
7. **Continuation Authority** — the maximum success-continuation ceiling available after a delivered current Increment: `CURRENT_INCREMENT`, `BOUNDED_OUTCOME`, or `MANDATE_OUTCOME`.
8. **Return-to-User Boundary** — material choices that must return to the user when current authority cannot select one answer.
9. **Applicability** — exact project root when available and the bounded initiative/scope/work context to which the Mandate applies.

Use [../templates/ADAPTIVE-PLANNING-MANDATE.template.md](../templates/ADAPTIVE-PLANNING-MANDATE.template.md) when a durable project-local record is available.

## Do not force a form ceremony

The user may provide the Mandate entirely in natural language. Do not ask them to fill every field if current intent and evidence let you derive a noncontroversial value.

Examples:

- If the user says "기존 동작을 깨지 말고 가능한 작은 완결 결과를 우선해", record compatibility as a Hard Constraint and smallest durable observable outcome as a higher Decision Priority.
- If no meaningful Non-Goal has been supplied and none is needed to choose the current planning boundary, `None explicitly fixed` is acceptable; do not invent exclusions merely to fill a template.
- If the exact project root is already known from the current request/repository, record it without asking.

Ask only for a missing fact whose different answers would materially change product intent, Scope, ownership, observable behavior, completion meaning, or another Return-to-User Boundary.

## Continuation Authority ceiling

Use exactly one value:

- `CURRENT_INCREMENT` — no success continuation is authorized beyond the fully delivered current Increment. This is the default when the user did not explicitly authorize a broader success boundary.
- `BOUNDED_OUTCOME` — after each fully delivered Increment, Adaptive may re-evaluate one exact bounded outcome and, while that outcome remains unsatisfied, may let Scope Shaper select another current Increment from fresh actual product state.
- `MANDATE_OUTCOME` — after each fully delivered Increment, Adaptive may re-evaluate the Mandate's Desired Product Outcome and, while it remains unsatisfied, may let Scope Shaper select another current Increment from fresh actual product state.

Continuation Authority is a **ceiling**, not the actual terminal of the current invocation. The invocation-local Run Completion Boundary and Completion Predicate in [09-run-contract.md](09-run-contract.md) define when that exact run succeeds.

A Run Completion Boundary must fit within this ceiling:

- `CURRENT_INCREMENT` permits planning-only completion, current-Increment implementation completion, and current-Increment delivery completion. A named-required-items boundary is also within this ceiling only when current authority establishes that every required item is contained in the current Increment; otherwise it requires broader continuation authority.
- `BOUNDED_OUTCOME` permits success continuation only as far as the exact bounded outcome authorized for the run.
- `MANDATE_OUTCOME` permits success continuation as far as the Desired Product Outcome.

If the current user instruction explicitly requires a Run Completion Boundary broader than the stored Mandate ceiling, revise or adopt the Mandate before the first mutation. If the current instruction does not grant that broader authority, return the exact authority gap. Never close a smaller Run Contract merely to avoid the revision, and never silently expand the Mandate.

Do not infer `BOUNDED_OUTCOME` or `MANDATE_OUTCOME` merely because `Applies-To` names an initiative, Scope, or Work Package. `BOUNDED_OUTCOME` requires one exact bounded Completion Predicate in the Run Contract; applicability alone is not a completion test.

For an existing Adaptive Mandate created before this field existed, treat missing Continuation Authority as `CURRENT_INCREMENT`. Do not require reapproval merely to preserve that prior behavior; serialize the explicit field the next time the Mandate is materially revised.

Success continuation never means consuming a pre-authored WP list or provisional horizon in order. After a delivered Increment, compare fresh actual product state with the active Run Completion Predicate; only when more construction is still required and the ceiling permits it does Scope Shaper choose the next Increment.

## Recommended default delegation when user says "권장안으로 진행"

When the user explicitly selects Adaptive and broadly delegates recommended planning decisions, interpret that delegation as authorizing, when the delegated-decision test passes:

- INC split/merge/reorder/replace/shrink;
- deferring or dropping unsupported provisional future work;
- selecting the smallest durable product state that advances the Desired Product Outcome;
- selecting among equivalent planning shapes using the ordered Decision Priorities;
- adopting existing applicable approved Behavior/UI authority unchanged;
- resolving product details already determined by current approved authority;
- resolving any genuinely user-owned planning choice that remains after current Baseline leaf self-review; and
- allowing faithful Spec/Ticket structural projection to proceed under the current Baseline self-review/adoption guards without adding a redundant approval ceremony.

Do not interpret broad delegation as authority to:

- change the Desired Product Outcome;
- violate Hard Constraints or Non-Goals;
- choose among materially different unresolved user experiences, ownership models, compatibility trade-offs, irreversible external commitments, or similar user-owned alternatives when priorities do not decide them;
- use the Mandate itself to expand implementation/verification authority beyond the explicit Adaptive current-Increment handoff, or to deploy, use credentials, mutate production/shared external resources, or perform destructive actions;
- activate optional adversarial planning consensus or choose its Challenger.

## Decision Priorities

Priorities should be ordered, not scored. Apply the highest relevant priority first and use lower priorities to break remaining ties.

Good examples:

```text
1. Preserve product meaning and existing authority.
2. Prefer a complete observable user result over technical preparation.
3. Preserve existing compatible behavior.
4. Prefer the smallest durable product surface.
5. Prefer simpler internal commitments over speculative future flexibility.
```

or:

```text
1. Long-term domain-model correctness.
2. Data integrity and recoverability.
3. Backward compatibility.
4. Delivery speed.
```

Do not invent numerical weights or confidence thresholds.

## Return-to-User Boundary

Return only when all current authority has been applied and at least two materially different acceptable product results still remain.

Typical boundaries:

- actor/role/permission or ownership choice;
- identity or membership semantics;
- lifecycle, persistence, recovery, interruption, or ordering semantics;
- materially different rendered/user-visible behavior;
- backward-compatibility or migration trade-off;
- meaningful external effect, recurring cost, lock-in, or irreversibility;
- change to Desired Product Outcome, Hard Constraint, or Non-Goal;
- authoritative readback/completion meaning when alternatives imply different product promises;
- independent verification requirement when it changes the product acceptance contract.

A decision is not user-owned merely because it is technically important. If current approved authority and the Mandate already determine it, resolve it.

## Mandate revision

The user may change the Mandate at any time.

On a material change:

1. record the new current Mandate revision in the companion file;
2. record the changed authority/priorities in the Adaptive trace;
3. re-evaluate the active Run Contract, current provisional planning artifacts, and the current INC;
4. reshape only what the new Mandate materially affects; and
5. never rewrite immutable Baseline Scope revisions or delivered `done` history.

A later Mandate does not falsify prior history. It changes current planning authority from that point forward.

## No project root yet

Follow current Baseline greenfield rules. The Mandate may exist in the current conversation before a project root exists, but do not invent a durable external planning location. Once one exact intended project root exists, write the companion Mandate under that project and revalidate whether new actual evidence changes any material decision.
