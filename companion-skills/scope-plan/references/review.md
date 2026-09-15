# Independent Scope Plan Review

## Judgment owner

Run this review in an invocation separate from the method writer. Read every bound Thesis source, the complete current Scope, current implementation path and primary evidence before accepting the Planner's diagnosis as a frame. The writer's self-check, agreement, finding count, JSON shape or binding hash does not establish independent semantic review. Preserve actual reviewer identity and raw invocation/evidence provenance without inventing another approval gate.

The Scope is the acceptance authority. Judge the proposed method against its complete `Outcome`, every authored `Acceptance` scenario and product success/failure/recovery/preservation condition, not merely the Plan's summary. A missing or contradictory obligation is a Scope/Thesis issue, not permission to narrow the method. Approved future details and explicit Non-Goals remain excluded.
When the Scope contains `## Transition Authority`, review its exact project-local baseline paths/digests and selected Block/conditions as part of the current method; an absent section is not a missing requirement. A hash proves bytes, not approval or continuation authority.

## Bounded review frontier

For this exact Scope, derive a bounded frontier from the method and its load-bearing dependencies. Directly inspect where relevant:

- purpose and complete user/operator result, including plausible false successes;
- current entrypoint, ordinary-entry bypasses and alternate callers;
- competing causes, second writers/readers and external owners;
- shared interfaces, producer/consumer or publisher/subscriber mismatches;
- identity, state lifetime, persistence, reset, ordering, interruption and partial effects;
- stale identity, weak proxy readback, cleanup and settlement;
- failure/recovery, late or duplicate response and preservation paths;
- implementation prerequisites, self-check and final authoritative readback;
- conditional first work, prohibited expansion and return conditions.

Distinguish observed contradiction, inference and missing evidence. Reject a method that defers a currently cheap load-bearing choice into implementation. Accept conditional first work only when its permitted work, discriminating readback, forbidden expansion and refutation owner are all explicit. Do not require fixed counts, a repository-wide audit or a new approval ceremony.

For each material candidate, preserve:

- exact Thesis/Scope anchor;
- actual implementation path and assumption that can fail;
- reachable condition and materially wrong result;
- why the proposed method/readback cannot distinguish that result;
- narrowest next observation or exact authority/environment limit;
- responsible next owner/action.

A method can be admitted with a genuine non-material advisory unresolved. `ADMIT` cannot coexist with an unresolved material finding, unresolved `contract_gap`, or unavailable evidence needed to decide the reviewed start scope. Do not manufacture findings from style, hypothetical unreachable paths or optional improvements.

## Current JSON artifact

Write exactly one JSON artifact at the caller-supplied outside-Project-Root path. Never search for a newest review, create a project-local review database, or duplicate the machine judgment in a second verdict file.

```json
{
  "schema": "iis-scope-plan-review/v2",
  "project_root": "<canonical absolute root>",
  "plans": [{"path": "<exact Plan/common Plan>", "sha256": "<actual bytes sha256>"}],
  "contracts": [{"scope_path": "<exact Scope>", "scope_sha256": "<actual bytes sha256>", "thesis_sources": [{"path": "<exact bound Thesis>", "sha256": "<actual bytes sha256>"}], "transition_authorities": []}],
  "review_origin": {"reviewer": "<actual independent reviewer>", "evidence_reference": "<raw invocation/primary evidence>"},
  "decisions": [{
    "scope_path": "<exact Scope>",
    "decision": "ADMIT",
    "rationale": "<substantive basis against every applicable Scope obligation>",
    "start_scope": "<exact work this Scope may start>",
    "findings": [],
    "conditions": []
  }]
}
```

Use the actual decision enum `ADMIT`, `REVISE` or `EVIDENCE_NEEDED`. Include exactly one current decision for this Scope and every Plan used by it. `findings` items contain `kind` (`contract_gap`, `method` or `evidence_limit`), `anchor`, `observation`, boolean `material`, `disposition` (`unresolved`, `dismissed` or `resolved`), `basis` and `next_owner`; optional `evidence_refs` contain exact ordinary-file `{path, sha256, locator}` references. `conditions` contain `plan_anchor`, `permitted_initial_work`, `discriminating_observation`, `dependent_work_not_yet_permitted` and `response_if_refuted`.

Hash bytes actually reviewed using ordinary file/CLI tools, not copied hash claims. Include every bound Thesis in `thesis_sources` and every applicable bound Transition original in `transition_authorities` using `{path, sha256}`; use an empty transition array when absent. Before writing, recheck reviewed Scope/Thesis/Transition/Plan bytes and load-bearing premises. If a material premise changed, review the affected method again before ADMIT. Byte currentness is not proof of reviewer independence or semantic truth. Preserve the actual completed independent invocation and primary evidence; historical review shapes are not active aliases for v2.

## Return boundary

Return the exact artifact path and digest, primary evidence and one current decision to the preparation lead. The lead forwards the artifact unchanged, including findings, conditions and limits. It must not turn a prose summary into ADMIT, erase an unresolved finding or reinterpret `EVIDENCE_NEEDED` as product failure. Lost or stale artifacts require a new independent review.
