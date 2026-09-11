# Independent Plan Review

## Judgment owner

Use an actual review invocation separate from the method writer. Read the complete applicable original Ticket/Spec/Behavior/UI obligations, current plan/common-plan bytes and primary evidence, not merely a Heuristic summary. A writer's self-check, agreement, finding count, JSON schema pass or runtime binding pass does not establish independent semantic review. Preserve actual reviewer identity and raw invocation/evidence provenance without inventing reviewer authentication or another approval gate.

For each Ticket decide whether the current method is sufficient to start within its stated scope. Review purpose and preserved behavior, cause alternatives where relevant, shared writers/readers/interfaces/callers, prerequisite/effect boundaries, actual self-check and final readback, and local/material return conditions. Reject a method that defers a currently cheap load-bearing discriminating check to the final verifier, or treats unit/helper/source/mock success as product success while bypassing the approved acceptance path/readback. When several reported findings exist, ensure each finding or evidence-supported common-cause group is present in the start scope and self-check. Judge required shared decisions before their first dependent implementation; do not block unrelated Tickets behind whole-Set planning.

## Decisions

- `ADMIT`: current method and evidence suffice for the exact `start_scope`, including any reviewed conditional first work. This is implementation admission, not product correctness or a Ticket status.
- `REVISE`: identify a concrete inadequate/incorrect method or unresolved material decision and the affected Planner/authority route.
- `EVIDENCE_NEEDED`: name the smallest missing discriminating observation/authority/environment fact preventing a responsible start decision.

Review a condition's permitted first work, discriminating observation, prohibited expansion and response if refuted together. Reject a plan that defers all important choices into implementation. Support later allows already-reviewed expansion without renewed parent approval; refutation or insufficient evidence does not.

Heuristic no-finding does not decide ADMIT. Resolve all material findings and inspect the complete obligations independently. Do not reinterpret a pre-implementation REVISE as final FAILED or Adaptive implementation defect.

ADMIT requires the Code Grounding in [plan.md](plan.md) for load-bearing existing premises of the stated start scope and Heuristic evidence valid for the current method and premises, including justified non-material carry-forward under [heuristic.md](heuristic.md). Assess safely unresolved implementation-time premises through the existing conditional-first-work bundle. Evidence-field presence and Heuristic completion are not additional approvals or substitutes for semantic sufficiency; unresolved Heuristic findings can support an independent `REVISE` or `EVIDENCE_NEEDED` decision.

For REVISE, identify the applicable obligation or plan anchor, concrete inadequate method or material unresolved decision, consequence, smallest closure observation and responsible owner. Provide current source/schema anchors when asserting implementation facts; do not invent them for contract ambiguity or proposed design. Distinguish observed contradictions, reachable proposed-method counterexamples and missing evidence. Do not move closure conditions through taste, Scope-excluded promises or unreachable sequences; legitimate new evidence and repair-induced failures remain reviewable against the complete original obligations.

## One current result

Write one JSON artifact at the exact invocation-supplied outside-Project-Root path. Never search for a newest review, create a project-local approval DB, or duplicate the judgment in a second Markdown verdict. This one artifact contains both semantic explanation and current machine links:

```json
{
  "schema": "iis-plan-review/v1",
  "project_root": "<canonical absolute root>",
  "plans": [{"path": "<exact absolute plan/common-plan path>", "sha256": "<actual bytes sha256>"}],
  "contracts": [{"ticket_path": "<exact canonical Ticket>", "ticket_sha256": "<actual bytes sha256>", "authority_digest": "<inspect_authority result>"}],
  "review_origin": {"reviewer": "<actual independent reviewer>", "evidence_reference": "<raw invocation/primary evidence reference>"},
  "heuristic": {"evidence_reference": "<actual independent exploration evidence>", "disposition_summary": "<material findings/unknowns/dismissals and resolution>"},
  "decisions": [{
    "ticket_path": "<exact canonical Ticket>",
    "decision": "ADMIT",
    "rationale": "<substantive basis against all applicable obligations>",
    "start_scope": "<exact work this Ticket may start>",
    "conditions": [{
      "plan_anchor": "<exact plan section>",
      "permitted_initial_work": "<bounded first work>",
      "discriminating_observation": "<actual decisive readback>",
      "dependent_work_not_yet_permitted": "<forbidden expansion>",
      "response_if_refuted": "<stop/return boundary>"
    }]
  }]
}
```

This is a shape illustration, not a completed review. Use `conditions: []` when no conditional start exists; use the actual decision enum and substantive explanation. Include every reviewed Ticket exactly once in contracts/decisions and every used common plan in plans; per-Ticket decisions may differ. Do not fill examples or fixture JSON and claim semantic success.

Use the existing `heuristic.evidence_reference` and primary evidence references to preserve Grounding observations, actual Heuristic input identities and refresh/carry-forward evidence. Summarize dispositions in `heuristic.disposition_summary` and semantic judgment in each decision's `rationale`; no additional schema fields or verdict artifacts are required.

Calculate hashes from bytes actually reviewed. Obtain `authority_digest` via read-only `ready_contract inspect_authority` (exact Ticket/root, current pinned canonical validator/bundle) or the same core API. Do not synthesize that digest from a guessed schema, trust a caller's copied hash, or begin implementation first. Before writing, recheck that reviewed bytes and load-bearing source/search/runtime premises remain current; if changed, inspect the impact and revise only the necessary review.

If a material method or source/search/runtime premise change invalidates Heuristic evidence, obtain the necessary affected refresh before ADMIT. Preserve independently checked non-material carry-forward evidence rather than relabeling old work; a matching plan hash alone does not establish unchanged premises.

`rationale`, `start_scope` and `conditions` express semantic judgment; the stateless boundary check does not score their length or infer sufficiency from string presence. `ready_contract check_plan_admission` independently recomputes plan/review/Ticket/authority identity and checks selected ADMIT without creating execution/session state. Missing review yields `PLAN_REVIEW_REQUIRED`, stale links `PLAN_REVIEW_STALE`, non-admitted Ticket `PLAN_NOT_ADMITTED`; these are admission outcomes, not product verdicts.

These Grounding and revision obligations are semantic review requirements, not a claim that the current stateless checker automatically verifies source meaning or observation truth. Do not infer a new machine-enforced gate, schema version or admission error from this document change.

Return the actual artifact and raw evidence to the preparation lead. The lead may report COMPLETE only for its entire required current ADMIT denominator. Lost/stale artifacts cannot be repaired by relabeling an old conversation or changing REVISE to ADMIT; the owning reviewer must perform the needed current judgment.
