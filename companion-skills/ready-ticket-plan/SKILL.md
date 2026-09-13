---
name: ready-ticket-plan
description: "Prepare execution methods for exact existing IIS Ready Tickets through a grounded Planner and independent Plan Review. Return a current per-Ticket ADMIT, REVISE or EVIDENCE_NEEDED review without changing product authority, implementing, or issuing final verification verdicts. Preserve current user-selected execution modes and models."
---

# Ready Ticket Plan

## Purpose and authority

Prepare the method for one exact Ready Ticket or the Tickets affected by one important shared decision. This is a delivery-preparation companion, not IIS product planning and not a new Ticket lifecycle. Product `approved/ready/done`, Scope, Behavior/UI, Spec, ACs and authored Verification flows remain unchanged. Planning-only IIS ends at its existing Ready Ticket Set; a caller requesting preparation stops here; only a current implementation request authorizes a later implementation owner.

The preparation lead binds the requested Ticket denominator, coordinates Planner → Independent Plan Review, preserves actual evidence and returns one terminal result. Planner owns grounded method writing and revision. The independent reviewer owns original-contract-first counterexample/unknown judgment and start sufficiency. The lead checks attribution/currentness and requested coverage, not a second substantive review. No finding is not admission; a plan file or structurally valid JSON is not proof that an independent review occurred.

Read both references before preparation: [plan.md](references/plan.md) and [review.md](references/review.md). They are self-contained; an external investigation-method Skill is optional, never required.

## Inputs and entry

- Project Root: exact canonical root.
- Tickets: exact existing canonical Ticket paths constituting this preparation request.
- Plan Review Output: exact outside-Project-Root output path supplied/selected for this invocation, never a latest-file lookup.
- Current user instructions, selected execution mode/model scope and permitted actions.
- Optional navigation: existing plans/common plans, repository-investigation artifact, Matt/Scope evidence, implementation observations and actual independent-review evidence.

Validate every selected Ticket with the current canonical `validate_ticket.py` from the same pinned IIS bundle; require exact `VALID` and `Status: ready`. Resolve the whole Ticket, Parent Spec, applicable Behavior/UI and current references. `ready_contract inspect_authority` provides current flat `project_root`, `ticket_path`, `authority_digest` and validator/bundle identity without arming or beginning implementation. Skill reads and preparation artifact writing are not implementation admission. Do not begin an execution to obtain a review digest.

Do not implement `draft/blocked/done` Tickets through preparation. Preserve any exact admission failure and useful reachable method evidence without creating ADMIT. Existing implemented ready targets requested only for verification go directly to `ready-ticket-verify`; no new plan/review is required.

## Execution and independence

Use current explicit instructions first and the caller's applicable selected model/effort; do not invent defaults, fixed worker counts, permanent rosters or three different models. A current selection clearly covering preparation roles carries forward. For actual delegated roles only, resolve missing model selections once under the caller's existing model policy. Never promote a recommendation or host default into user selection.

DIRECT preparation uses current Main for the roles it performs, but the author cannot independently approve its own plan in that same writing invocation. Plan Review must read the original contract in an invocation separate from the writer. Use currently authorized host subagents, a separate conversation/session, or an attributable existing independent review that is still current. Do not silently switch a user-selected mode or create hidden fan-out to obtain independence. If an independent invocation cannot be obtained, return useful plans and the exact capability/independence limit; do not manufacture an ADMIT artifact. No reviewer-authentication system or extra independence gate is created: actual invocation provenance and raw evidence establish what happened.

For actual delegated roles, the preparation caller resolves the following references from the current pinned IIS bundle and includes their exact readable paths and an instruction to read and apply them before work in each assignment. Include exact Ticket paths/Project Root, applicable authority and current plan/evidence inputs, role-specific output locations and these return boundaries; a role name or the caller's own read/summary does not replace this handoff.

When invoked under Adaptive, receive and forward its unchanged Common original sources block to both Planner and Plan Reviewer, using [the shared source assignment](../../iis-adaptive-planning/templates/SHARED-SOURCE-ASSIGNMENT.template.md). Each role reads those originals independently before adopting the caller's method framing; retain the exact Ticket/start scope and existing return contract. Standalone preparation retains its existing inputs and does not require Adaptive activation.

- Planner: [plan.md](references/plan.md). Write/revise the approved execution method and return the plan, grounding, any conditional first work and exact unresolved limits. Do not approve your own plan, implement the product or perform final verification.
- Independent Plan Reviewer: [review.md](references/review.md) for the review procedure/result and [plan.md](references/plan.md) for Code Grounding and conditional-start criteria, not as a Planner assignment. Return the exact outside-Project-Root review artifact, `ADMIT | REVISE | EVIDENCE_NEEDED` judgment and evidence, then end this invocation. Do not write/revise the plan or take over the lead's revision loop.

## Preparation flow

1. Bind exact requested Tickets and current product authority. Identify which important decisions genuinely couple producer/consumer Tickets; unrelated Tickets do not wait for whole-Set detailed design.
2. Planner investigates current load-bearing anchors and writes only necessary method detail under the Code Grounding requirements in [plan.md](references/plan.md), normally at `<Project-Root>/docs/planning/work/<work-slug>/plans/PLAN-NNN.md`. Reuse current evidence and a shared section/reference instead of duplicating it. Future file paths are method navigation, not product obligations.
3. Independent reviewer first reads the complete applicable original obligations, current product path and primary evidence before accepting the Planner's diagnosis as a frame. It directly judges the current method's load-bearing dependencies for realistic wrong-cause, ordinary-entry bypass, second writer/reader or external owner, producer/consumer mismatch, ordering/interruption/partial-effect, stale/weak readback, repair-induced state/order/ownership and preserved-behavior failure paths. It distinguishes observed contradiction, inference and missing evidence, derives a bounded check frontier from the proposed method, and writes the single JSON result in [review.md](references/review.md) with per-Ticket `ADMIT | REVISE | EVIDENCE_NEEDED`.
4. `REVISE` returns the affected method to the owning Planner; `EVIDENCE_NEEDED` returns the exact observation/authority gap to its evidence owner. Repeat only affected work after substantive method/evidence change, never by quota or automatic resubmission. The lead fan-in preserves the actual reviewer result, exact requested denominator, current identities and evidence limits for every outcome; only a current `ADMIT` for the corresponding required Ticket may be forwarded as `plan_review_path` when implementation is requested. Runtime independently checks current bytes at every implementation admission.

Preparation permits only authorized inspection and method/review artifact work. A reviewed conditional first implementation is executed later by the admitted implementation owner, not as unbound preparation mutation. Any genuinely needed external or mutation-capable experiment still needs its exact existing authority; absence of permission becomes a precise evidence limit.

## Result boundary

```text
READY TICKET PLAN RESULT
Project Root: <exact canonical root>
Tickets:
- <every required exact Ticket path>
Plans:
- <exact plan/common-plan paths>
Plan Review: <exact outside-root JSON path | None>
Decisions:
- <Ticket path — ADMIT | REVISE | EVIDENCE_NEEDED, rationale/start scope>
Evidence: <actual independent invocation and primary evidence references>
Limitations: None | <exact unavailable evidence/independence/capability/currentness>
Completion: COMPLETE | BLOCKED | PARTIAL
```

`COMPLETE` requires an actual current independent review with ADMIT for every required Ticket; a smaller admitted subset, missing independent review, REVISE or EVIDENCE_NEEDED cannot close it. `PARTIAL` preserves useful preparation with unresolved required work; `BLOCKED` means a required authority/capability/evidence boundary prevents valid continuation. State the exact next owner/action and do not invent a final product `FAILED/INCONCLUSIVE` verdict. Intermediate Planner or reviewer outputs are not this terminal and must not be parsed as review completion.

For stopped no-progress preparation or an exhausted caller-specified execution budget, return useful unresolved work as `PARTIAL`, or `BLOCKED` only when an identified required authority, capability or evidence boundary prevents valid continuation. Preserve the last actual review decision, unresolved scope, attempted observations and next owner/action in Evidence/Limitations. A rejection count or budget is not an ADMIT rule, a new meaning for BLOCKED, or permission to kill/restart a session or block unrelated Tickets.

No source remediation, Ticket status mutation, final verification or automatic later-Increment continuation occurs in this Skill. Review artifact loss requires the necessary current review again, not reconstructing approval from a past conversational claim.
