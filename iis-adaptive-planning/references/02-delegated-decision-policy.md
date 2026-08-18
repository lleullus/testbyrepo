# Delegated Decision and Confirmation Policy

## Decision provenance

Classify each material planning decision by where its authority came from:

- `USER_EXPLICIT` — the user directly fixed the exact decision in the current applicable authority.
- `DELEGATED_RECOMMENDATION` — the active Mandate authorized the agent to choose and current evidence/priorities yielded one materially preferred answer.
- `INHERITED_AUTHORITY` — an already approved applicable Scope/Behavior/UI/Spec authority directly determines the answer without a new product choice.
- `STRUCTURAL_PROJECTION` — the downstream artifact only serializes, splits, or restates approved meaning without changing observable product meaning.

Do not create additional provenance categories merely for implementation choices, tool use, model confidence, or reviewer agreement.

## Delegated-decision test

Before treating a material decision as `DELEGATED_RECOMMENDATION`, perform this test:

1. **Authority completeness** — identify the exact user/Mandate, approved planning authority, and current evidence relevant to the choice.
2. **Mandate containment** — every candidate under consideration remains inside Desired Product Outcome, Hard Constraints, and Non-Goals.
3. **Priority resolution** — apply ordered Decision Priorities. One candidate must be materially preferred for the product outcome, not merely easier to implement.
4. **Counterexample check** — try a reasonable alternative and ask whether a user/operator would observe a materially different product promise, ownership model, compatibility result, lifecycle, or completion meaning.
5. **Return-boundary check** — if that difference is material and the Mandate does not decide it, return to the user.
6. **Baseline-special-gate check** — do not use delegation to satisfy a direct-user-only gate preserved in the Adaptive Delta.

Only after all six checks pass may standing delegated confirmation be used.

## What counts as one clear recommendation

One recommendation is clear when the alternatives either:

- are implementation-owned and do not change approved observable meaning; or
- are planning variants whose material differences are decisively ordered by the Mandate; or
- are dominated because one violates current authority, current product facts, a Hard Constraint, or a higher Decision Priority.

Do not require artificial certainty. Do not use a numeric confidence threshold.

## What must return to the user

Return when two or more viable outcomes remain and choosing between them would materially change a user-owned product result not resolved by existing authority.

Examples:

- invite-only ownership vs open shared ownership when both satisfy the broad goal;
- preserving a legacy data meaning vs performing a breaking migration when priorities do not decide it;
- immediate visible partial behavior vs later atomic release when each provides a materially different user promise and neither is mandated;
- operator-assisted acceptance vs requiring a new independently verifiable product surface when that changes the product contract and the Mandate is silent.

Ask the smallest question that resolves the branch. Do not re-present already settled decisions.

## Standing delegated confirmation by leaf

When the delegated-decision test passes, the following user-owned planning confirmation events may be satisfied through standing delegation in Adaptive mode:

- Scope Shaper's confirmation of the connected Scope-owned landscape, decomposition, and one selected next Increment;
- ordinary Ask Matt approval of new/changed Behavior authority, UI authority, and integrated shared understanding after all material decisions are closed.

To Spec and To Tickets now use their Baseline leaf-local self-review/adoption guards for faithful structural projection. Adaptive does not relabel those default transitions as delegated confirmation or add another approval ceremony. This policy changes only genuinely user-owned planning decisions, not the substantive completion criteria.

For each event:

1. complete the current leaf's investigation/audit first;
2. ensure no material Open Question remains;
3. run the same validators/reviews Baseline requires;
4. perform the same canonical status transition Baseline would perform after direct approval;
5. add one concise material trace entry identifying the artifact and `DELEGATED_RECOMMENDATION` basis.

Do not add a fake user quote or write `user explicitly approved`.

## Special gates not covered by standing delegation

Unless the current Baseline later changes them, do not use standing delegation for:

- activating adversarial planning consensus;
- selecting/designating the exact Adversarial Planning Challenger;
- the adversarial gate's exact user-confirmed Intent Anchor;
- the adversarial gate's post-consensus direct final user approval when the current Baseline explicitly requires it;
- authority owned by an external operator/credential holder rather than IIS planning;
- concrete destructive/production/external-effect authorization.

These are not ordinary repeated IIS artifact reviews.

## Facts versus decisions

Do not ask the user to decide an inspectable fact.

Examples to inspect directly when available:

- whether the current product already exposes an acceptance surface;
- whether an existing approved Behavior authority covers the current scope;
- whether a canonical path/status/validator condition holds;
- whether current runtime behavior contradicts a claimed result.

Facts constrain planning but do not automatically become product authority.

## Projection is not a new product decision

When To Spec or To Tickets has only one accurate way to preserve approved meaning, classify the operation as `STRUCTURAL_PROJECTION` and complete it without a user prompt.

If several decompositions are possible but all preserve the same observable contract, choose the smallest/clearest decomposition under current Baseline rules. Do not turn Ticket count or internal sequence into user decisions.

If a downstream artifact cannot be accurate without changing product meaning, it is no longer projection. Return to the owning upstream leaf.

## Trace materiality

Record only decisions whose provenance matters to later interpretation:

- selected/reshaped Increment;
- material product-policy or Behavior/UI choice made through delegation;
- a material delegated Scope/Behavior/UI/shared-understanding decision whose provenance affects later interpretation;
- verification triage that changes planning direction;
- user-return decision and its resolution.

Do not log every inherited fact, mechanical serialization, tool call, validator rerun, or implementation possibility.
