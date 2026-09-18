# Independent Scope Plan Review

## Judgment owner

Run this review in an invocation separate from the method writer. Read every bound Thesis source, the complete current Scope, current implementation path and primary evidence before accepting the Planner's diagnosis as a frame. The writer's self-check, agreement, finding count, JSON shape or binding hash does not establish independent semantic review. Preserve actual reviewer identity and raw invocation/evidence provenance without inventing another approval gate.

The Scope is the current acceptance contract. In this same review, distinguish its fidelity to bound originals from the proposed method's sufficiency for its complete `Outcome`, every authored `Acceptance` scenario and product success/failure/recovery/preservation condition. A missing or contradictory obligation is a `contract_gap` for Main to route under `iis-workflow`, not permission to narrow the method. Approved future details and explicit Non-Goals remain excluded.
When the Scope contains `## Transition Authority`, read its exact project-local baseline paths/digests and compare the selected Block and any fixed construction boundary/order with the approved original and current evidence. Do not require a new internal boundary where the Baseline leaves construction choice open. An absent section is not a missing requirement. A hash proves bytes, not approval or continuation authority; this check adds no review stage or artifact.

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
- probe evidence's observed boundaries and limits, conditional first work, prohibited expansion and return conditions.

Independently derive the important implementation-grounded failure frontier before accepting the Planner's candidates. Identify the load-bearing state, owner, identity, resource and asynchronous boundaries whose failure can falsify the approved result; compare them with the Plan's assumptions and minimal discriminators. Do not require a fixed roster, fixed finding count or Cartesian matrix. If a material-looking boundary is excluded as unreachable, non-material or out of Scope, the review basis must be sufficient to distinguish a reasoned exclusion from a boundary that was never examined.

Challenge whether each selected self-check distinguishes a conforming implementation from the reachable failure, rather than merely confirming an intermediate effect. For a material state transition, ownership transfer, interruption, threshold crossing or terminal-state change, require the trace to reach the contract-allowed recovery or terminal result and the smallest subsequent operation or authoritative readback needed to expose stalled progress, residue or duplicate effect. Reinitializing the relevant identity or state before that observation does not close the trace unless recreation is the approved recovery behavior.

For every material discriminator, inspect its proposed executable disposition. An existing test name is insufficient unless its setup activates the same condition and its assertion/readback changes between the conforming and failing implementation. When the Plan expects implementation to add a case, confirm that it fits the existing project test/build/CI path and remains within the reviewed mutation surface. When automation is unsafe or unsuitable, require the narrow repeatable alternative and exact evidence/authority limit rather than generic future hardening.

Inspect non-obvious execution prerequisites when they control whether the admitted self-check or later real-boundary verification can run: actual build/launcher, fixture creation, selector or endpoint, authoritative readback, cleanup, reusable preparation resources, scenario state that must be reset, permissions and external conditions. Do not pre-run the verifier's semantic cycle, but do not admit a method whose required observation is already known to be inaccessible without an explicit conditional-first-work or evidence path.

Distinguish observed contradiction, inference and missing evidence. Reject deferral of a cheap load-bearing choice only when it can be discriminated in the current authorized environment. Do not pressure the Planner to perform an effectful experiment before review or treat scratch results as deployed/provider evidence. Accept conditional first work only when its required authority/environment, permitted work, discriminating readback, forbidden expansion and refutation owner are explicit; effectful initial work remains with the implementation owner after `ADMIT` and the necessary user authorization. Do not require fixed counts, a repository-wide audit or a new approval ceremony.

For each material candidate, preserve:

- exact Thesis/Scope anchor;
- actual implementation path and assumption that can fail;
- reachable condition and materially wrong result;
- why the proposed method/readback cannot distinguish that result;
- narrowest next observation or exact authority/environment limit;
- responsible next owner/action.

For a correction of a known Verify/Probe finding, also inspect the predecessor finding/evidence locator, repeatable reproducer or exact limitation, expected regression disposition, directly connected same-assumption sibling, and execution/readback prerequisites. These items are navigation for implementation and later independent verification; they are not a carried-forward verdict or a reviewer decision that other Acceptance evidence is unaffected.

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

Use the actual decision enum `ADMIT`, `REVISE` or `EVIDENCE_NEEDED`. Include exactly one current decision for this Scope and every Plan used by it. The existing `rationale` must identify the exact Plan frontier anchor and make the independent review basis inspectable: the implementation-grounded frontier considered, the minimal counterexamples or discriminators that control admission, their executable disposition and non-obvious prerequisites where load-bearing, and any load-bearing exclusion basis. This remains prose within the existing v2 decision; do not add a second artifact or silently require a new schema field. `findings` items contain `kind` (`contract_gap`, `method` or `evidence_limit`), `anchor`, `observation`, boolean `material`, `disposition` (`unresolved`, `dismissed` or `resolved`), `basis` and `next_owner`; optional `evidence_refs` contain exact ordinary-file `{path, sha256, locator}` references. `conditions` contain `plan_anchor`, `permitted_initial_work`, `discriminating_observation`, `dependent_work_not_yet_permitted` and `response_if_refuted`.

Hash bytes actually reviewed using ordinary file/CLI tools, not copied hash claims. Include every bound Thesis in `thesis_sources` and every applicable bound Transition original in `transition_authorities` using `{path, sha256}`; use an empty transition array when absent. Before writing, recheck reviewed Scope/Thesis/Transition/Plan bytes and load-bearing premises. If a material premise changed, review the affected method again before ADMIT. Byte currentness is not proof of reviewer independence or semantic truth. Preserve the actual completed independent invocation and primary evidence; historical review shapes are not active aliases for v2.

The caller-supplied outside-root path must remain readable by the admitted implementation handoff and any correction re-entry that the current request reasonably requires. Before returning, confirm that the exact artifact and its provenance/evidence reference are retrievable from the next-role environment or report the access/retention limit. Do not copy a new authoritative verdict, create a review registry or reconstruct a lost review from prose. If the original becomes unavailable, the existing fresh-review rule still applies.

## Return boundary

Return the exact artifact path and digest, primary evidence and one current decision to the preparation lead. The lead forwards the artifact unchanged, including rationale, findings, conditions, execution prerequisites, evidence locators and limits. It must not turn a prose summary into ADMIT, erase an unresolved finding or reinterpret `EVIDENCE_NEEDED` as product failure. Lost or stale artifacts require a new independent review.
