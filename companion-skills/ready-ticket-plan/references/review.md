# Independent Plan Review

## Judgment owner

Use an actual review invocation separate from the method writer. Read the complete applicable original Ticket/Spec/Behavior/UI obligations, current product path, current plan/common-plan bytes and primary evidence before accepting the Planner's diagnosis as a frame. A writer's self-check, agreement, finding count, JSON schema pass or runtime binding pass does not establish independent semantic review. Preserve actual reviewer identity and raw invocation/evidence provenance without inventing reviewer authentication or another approval gate.

Compare parent obligations to actual acceptance ownership in the current Ticket Set, not only Ticket clauses back to the parent. A covered outcome ordinal may still omit one obligation within that outcome. Read an exact sibling Ticket when relying on its ownership; exclude approved future/Non-Goal work. An applicable ownerless obligation is a projection gap, never a non-blocking observation merely because this AC omits it. Return REVISE to To Tickets when parent meaning is correct, or to To Spec/the existing meaning owner when it is not; uncertain applicability returns EVIDENCE_NEEDED. Do not repair product authority in the method.

For each Ticket decide whether the current method is sufficient to start within its stated scope. Derive a bounded check frontier from the proposed method and its load-bearing dependencies rather than a fixed quota. Directly judge purpose and preserved behavior, wrong/competing cause, ordinary-entry bypass, second writers/readers or external owners, shared interfaces/callers, producer/consumer mismatch, ordering/interruption/partial effects, stale identity or weak proxy readback, repair-induced state/order/ownership paths, prerequisite/effect boundaries, actual self-check and final readback, and local/material return conditions. Distinguish observed contradiction, inference and missing evidence. Reject a method that defers a currently cheap load-bearing discriminating check to the final verifier, or treats unit/helper/source/mock success as product success while bypassing the approved acceptance path/readback. When several reported findings exist, ensure each finding or evidence-supported common-cause group is present in the start scope and self-check. Judge required shared decisions before their first dependent implementation; do not block unrelated Tickets behind whole-Set planning.

## Decisions

- `ADMIT`: current method and evidence suffice for the exact `start_scope`, including any reviewed conditional first work. This is implementation admission, not product correctness or a Ticket status.
- `REVISE`: identify a concrete inadequate/incorrect method or unresolved material decision and the affected Planner/authority route.
- `EVIDENCE_NEEDED`: name the smallest missing discriminating observation/authority/environment fact preventing a responsible start decision.

Review a condition's permitted first work, discriminating observation, prohibited expansion and response if refuted together. Reject a plan that defers all important choices into implementation. Support later allows already-reviewed expansion without renewed parent approval; refutation or insufficient evidence does not.

No finding does not decide ADMIT. Resolve all material findings and inspect the complete obligations independently. Do not reinterpret a pre-implementation REVISE as final FAILED or Adaptive implementation defect.

ADMIT requires the Code Grounding in [plan.md](plan.md) for load-bearing existing premises of the stated start scope plus reviewer-owned primary evidence that is current for the method and premises. Assess safely unresolved implementation-time premises through the existing conditional-first-work bundle. Evidence-field presence is not an additional approval or a substitute for semantic sufficiency; material contradictions or unknowns support an independent `REVISE` or `EVIDENCE_NEEDED` decision.

For REVISE, identify the applicable obligation or plan anchor, concrete inadequate method or material unresolved decision, consequence, smallest closure observation and responsible owner. Provide current source/schema anchors when asserting implementation facts; do not invent them for contract ambiguity or proposed design. Distinguish observed contradictions, reachable proposed-method counterexamples and missing evidence. Do not move closure conditions through taste, Scope-excluded promises or unreachable sequences; legitimate new evidence and repair-induced failures remain reviewable against the complete original obligations.

## One current result

Write one JSON artifact at the exact invocation-supplied outside-Project-Root path. Never search for a newest review, create a project-local approval DB, or duplicate the judgment in a second Markdown verdict. This one artifact contains both semantic explanation and current machine links:

```json
{
  "schema": "iis-plan-review/v2",
  "project_root": "<canonical absolute root>",
  "plans": [{"path": "<exact absolute plan/common-plan path>", "sha256": "<actual bytes sha256>"}],
  "contracts": [{"ticket_path": "<exact canonical Ticket>", "ticket_sha256": "<actual bytes sha256>", "authority_digest": "<inspect_authority result>"}],
  "review_origin": {"reviewer": "<actual independent reviewer>", "evidence_reference": "<raw invocation/primary evidence reference>"},
  "decisions": [{
    "ticket_path": "<exact canonical Ticket>",
    "decision": "ADMIT",
    "rationale": "<substantive basis against all applicable obligations>",
    "start_scope": "<exact work this Ticket may start>",
    "projection": {"status": "preserved", "basis": "<parent clauses and actual current Ticket/AC/Flow ownership or exact gap>"},
    "findings": [],
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

Preserve every material finding and non-material advisory in `findings`, not only in caller prose. Each item contains `kind` (`contract_gap | method | evidence_limit`), `anchor`, `observation`, boolean `material`, `disposition` (`unresolved | dismissed | resolved`), `basis` (evidence and disposition reason), and `next_owner` (exact owner/action or `None`). Optional `evidence_refs` contains ordinary file `{path, sha256, locator}` references; resolve relative paths from the review directory and hash actual bytes. Missing/changed referenced files are stale evidence, not no finding. Do not require a file when the deciding evidence is the directly readable authority already bound by contracts/plans.

Read evidence at the exact path authored in its owning plan/report; absolute outside-project evidence paths stay absolute. Before reporting a missing file, compare the attempted path with that original reference and correct any transcription or resolution error. A failed lookup at a different path is not evidence that the referenced observation is unavailable.

`projection.status` is `preserved | gap | unknown` and always includes substantive `basis`. ADMIT cannot coexist with gap/unknown projection, an unresolved contract_gap, or an unresolved material finding. A genuine non-material advisory may remain unresolved without blocking; preserve it rather than erase it. Resolved/dismissed findings require current evidence, not a change of label. These fields replace a second verdict artifact or evidence ledger; they do not authenticate the reviewer or prove semantic truth.

Calculate hashes from bytes actually reviewed. Obtain `authority_digest` via read-only `ready_contract inspect_authority` (exact Ticket/root, current pinned canonical validator/bundle) or the same core API. Do not synthesize that digest from a guessed schema, trust a caller's copied hash, or begin implementation first. Before writing, recheck that reviewed bytes and load-bearing source/search/runtime premises remain current; if changed, inspect the impact and revise only the necessary review.

If a material method or source/search/runtime premise changes, the current reviewer must judge the affected scope and evidence again before ADMIT. Preserve directly checked non-material carry-forward evidence rather than relabeling old work; a matching plan hash alone does not establish unchanged premises.

`rationale`, `projection`, `findings`, `start_scope` and `conditions` express semantic judgment. The file checker verifies current plan/review/Ticket/authority bytes, declared evidence files and ADMIT consistency, not source meaning, reviewer identity or observation truth. Missing review yields `PLAN_REVIEW_REQUIRED`, malformed/stale links `PLAN_REVIEW_STALE`, and non-admitted or contradictory ADMIT `PLAN_NOT_ADMITTED`. These are admission outcomes, not product verdicts. No host session lookup or new terminal protocol is required.

Return this exact artifact, its actual SHA256 and primary evidence to the preparation lead. The lead reads and forwards it unchanged, including findings, limitations and conditional scope; a user-facing summary never becomes a replacement machine review. A digest detects change relative to the supplied original, not a caller rewriting both file and claimed digest. The lead may report COMPLETE only for its entire required current ADMIT denominator. Lost/stale artifacts require the owning review, not reconstruction from an old conversation or caller conversion of v1 to v2.
