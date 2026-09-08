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

## Pre-consensus delegated Intent Anchor finalization

Ordinary Baseline adversarial consensus still requires direct user confirmation of the Intent Anchor. In explicit Adaptive mode only, that confirmation event may instead be satisfied through standing delegation after the user explicitly activates adversarial consensus and designates the exact Challenger.

Ask Matt first constructs the same current Baseline Intent Anchor, then compares it in authority order against: the current user conversation including later explicit changes; the current user-adopted Mandate; the closed Run Contract; applicable current Scope/Behavior/UI/verification authority; and directly verified current facts. The Anchor remains a derivative representation and never replaces or outranks the user's words.

Standing delegated Intent Anchor finalization is valid only when all of the following hold:

1. Adaptive is currently explicitly active and the applicable Mandate/Run Contract remain current;
2. the user explicitly activated adversarial consensus and designated the exact Challenger;
3. the Anchor contains every applicable Baseline Intent Anchor field and the exact designated Challenger;
4. the Anchor does not materially omit, weaken, reorder, or contradict current user authority, and any still-provisional interpretation is clearly marked provisional;
5. the delegated-decision test above passes and current authority determines one faithful Anchor rather than two materially different user-owned interpretations;
6. no Return-to-User Boundary or unresolved authority conflict exists;
7. the Challenger disclosure remains within current user/host authority and does not require sensitive/private, unrelated-repository, or other material disclosure expansion; and
8. the current user has not explicitly required direct Intent Anchor review for this Adaptive invocation.

If an Anchor omission or mismatch can be corrected deterministically from current authority without a new user-owned choice, correct it and re-run this test instead of asking for confirmation. Do not return to the user for wording polish or a restatement of already-settled authority.

When all eight conditions hold, finalize the exact current Intent Anchor as `DELEGATED_RECOMMENDATION` and invoke the exact designated Challenger without another user approval. Carry that provenance in the current invocation context; do not claim the user directly confirmed the Anchor and do not create a new receipt, sidecar, or persistent gate state merely for this event. A routine faithful delegated Anchor finalization is not a material Adaptive trace event by itself; trace only a material correction or user-return decision when later interpretation requires it under the artifact contract.

If the test does not close, return only the smallest unresolved material Anchor, authority, or disclosure decision. Direct user confirmation of the exact current Anchor has provenance `USER_EXPLICIT`. If the user's response materially changes product meaning or the Challenger binding, update the affected authority and re-evaluate the current Anchor before Challenger invocation.

## Post-consensus delegated finalization

In explicit Adaptive mode, Ask Matt alone owns the authority-delta review after `ADVERSARIAL CONSENSUS REACHED` for the latest complete candidate. The Challenger owns review and objection closure; To Spec owns admission/projection after finalization and must not independently reinterpret the Mandate or rerun this review.

Compare the latest reviewed candidate against, in authority order: the current user conversation including later explicit changes; the current user-adopted Mandate; the closed Run Contract; the current finalized Intent Anchor as a derivative representation that never replaces the user's words; applicable current Scope/Behavior/UI/verification authority; and directly verified current facts. The Anchor finalization provenance may be `USER_EXPLICIT` or `DELEGATED_RECOMMENDATION` under the pre-consensus Adaptive rule above. Facts constrain the review but do not become product authority by themselves.

Classify the authority delta exactly once as:

- `NONE` — the latest candidate requires no new user-owned product authority and remains determinable inside the current delegated authority;
- `MATERIAL` — accepting the candidate requires a user-owned product meaning, boundary, priority, or authority change not already delegated; or
- `UNCERTAIN` — current authority is insufficient to determine whether such a material change exists.

Standing delegated post-consensus finalization is valid only when all of the following hold:

1. Adaptive is currently explicitly active and the applicable Mandate/Run Contract remain current;
2. the user explicitly activated adversarial consensus, designated the exact Challenger, and the current Intent Anchor finalization provenance is `USER_EXPLICIT` or `DELEGATED_RECOMMENDATION`;
3. the latest complete candidate has current `ADVERSARIAL CONSENSUS REACHED` and no material candidate change occurred after the Challenger's final review;
4. the delegated-decision test above still passes;
5. authority delta is exactly `NONE`;
6. no Return-to-User Boundary or unresolved authority conflict exists; and
7. finalization remains inside the current Run Contract, including its Required Named Items, delivery stages, Run Completion Boundary, and Completion Predicate.

When all seven conditions hold, Ask Matt may approve the applicable completed Behavior/UI authority, finalize the exact integrated shared understanding, record `DELEGATED_RECOMMENDATION`, and continue to To Spec without another user approval. This is not a claim that the user directly approved that candidate and does not revise the outer Run Contract.

For `MATERIAL` or `UNCERTAIN`, return only the exact unresolved authority decision to the user. If the user accepts the exact latest candidate without changing its meaning, finalization provenance is `USER_EXPLICIT`. If the user materially changes the candidate while responding and adversarial activation remains current, the affected consensus is no longer current and the changed latest candidate must return to the exact designated Challenger before finalization.

## Special gates not covered by standing delegation

Unless the current Baseline later changes them, do not use standing delegation for:

- activating adversarial planning consensus;
- selecting/designating the exact Adversarial Planning Challenger;
- the invocation-local Run Contract Approval Gate explicitly activated by the affirmative `/승인게이트` modifier;
- accepting an unconfirmed delivery model/effort recommendation or changing an applicable user-selected delivery configuration; the model guide may inform recommendations but cannot supply consent;
- authority owned by an external operator/credential holder rather than IIS planning;
- concrete destructive/production/external-effect authorization.

Ordinary non-Adaptive Intent Anchor confirmation remains direct-user-only. In explicit Adaptive mode, only the exact pre-consensus faithful-Anchor rule above may satisfy that confirmation event through standing delegation; an explicit current request for direct Anchor review still requires the user response.

Only direct user approval of the exact rendered current `CLOSED` Run Contract satisfies an active Run Contract Approval Gate. Do not use `DELEGATED_RECOMMENDATION`, inherited authority, structural projection, reviewer agreement, or a downstream leaf confirmation to release it.

The Baseline post-consensus direct final approval remains the ordinary non-Adaptive rule. Only the exact explicit-Adaptive post-consensus rule above may satisfy that finalization event through standing delegation.

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
