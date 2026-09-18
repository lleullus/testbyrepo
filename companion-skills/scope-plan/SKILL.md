---
name: scope-plan
description: "Prepare an execution method for one exact ready IIS Scope and obtain an independent Plan Review without changing product meaning, implementing, or issuing a verification verdict."
---

# Scope Plan

## Caller contract

The caller supplies one complete, immutable source assignment before any role-specific instruction:

- **Project Root:** exact canonical absolute path.
- **Thesis:** every exact project-local Thesis source bound by the Scope, with its recorded revision and full UTF-8 SHA-256. Preserve inherited sources; do not select a newer source by name or latest-file lookup.
- **Scope:** exact canonical `docs/planning/work/<slug>/SCOPE.md` path.
- **Repository investigation:** exact immutable artifact and recorded identity, or `None supplied`.
- **Transition Authority:** if the exact Scope contains `## Transition Authority`, preserve each approved project-local baseline path and full SHA-256 exactly as bound; if absent, use `None` and do not invent a required baseline. A transition hash proves bytes only, not approval or continuation authority.
- **User instructions:** the current request, permitted actions, selected execution mode and selected model/effort policy.

Tell every worker: **read each bound Thesis source and the exact Scope directly before role judgment or editing, including purpose, complete product loop, false-success distinctions, failure/recovery meaning, and authoritative success readback.** A summary, role name, or latest-file search is not a substitute. Reading originals never expands the Scope.

### Evidence boundary — copy into each assignment

> **Evidence boundary — apply before role-specific work**
> - Do not use mocks, stubs, canned responses, seeded success states or surrogate readbacks as completion or verification evidence for the real acceptance boundary they replace.
> - When the approved outcome requires real execution, state transitions or external effects, the method must identify the real path and authoritative readback. Internal success or HTTP acceptance alone is not proof of the external result.
> - A double for an ancillary dependency does not invalidate an unrelated real boundary. Distinguish observed boundaries from boundaries replaced by doubles.
> - If required evidence is unavailable, preserve the gap under the role's return contract. Do not infer success or obtain evidence through unauthorized actions.

Forward the source assignment unchanged to both the Planner and the independent Plan Reviewer, then append only their exact role documents, scope, outputs and authority limits. The caller does not silently change the selected mode/model to obtain independence.

## Purpose and authority

This companion prepares the method for one exact ready Scope fixed by Main before method writing. It does not select the outcome, design Thesis, implement, verify or finalize delivery. The Scope remains the current outcome/acceptance contract: its `Outcome`, `Acceptance`, `Product Authority`, `Open Decisions` and `Non-Goals` are read as written. Preparation may write the method Plan and one outside-Project-Root review artifact. Only the Planner may additionally run bounded disposable scratch experiments under the current request's execution authority; the Reviewer's authority is unchanged. Neither role may change Thesis, Baseline or Scope bytes, product source/data, shared runtime, external systems or Scope status.

The preparation lead binds one Scope, coordinates a method writer and an independent reviewer, preserves primary evidence and returns one result. The Planner owns grounded method writing. The independent Reviewer reads the original Thesis and Scope first and owns the ADMIT/REVISE/EVIDENCE_NEEDED judgment. The lead checks exact paths, currentness and requested coverage; it is not a second semantic reviewer. A valid file or an absence of findings is not an admission by itself.

## Inputs and entry

- Exact canonical Project Root, Thesis source paths and Scope path.
- Optional current repository-investigation artifact and applicable Transition Authority evidence.
- Exact outside-Project-Root `plan_review_path` selected for this invocation; never discover a latest review.
- Current user instructions, permitted actions, selected execution mode and model/effort.

Before preparation, run the supplied `scope-shaper/tools/validate_scope.py` against the exact Scope and require exact `VALID` with `Status: ready`. A `draft`, `blocked`, `superseded` or `done` Scope is not a normal implementation-planning input. Read the exact Scope and bound Thesis originals and calculate their SHA-256 from actual bytes with ordinary tools; structural validity does not prove semantic sufficiency.
When `validate_scope.py --json` returns `transition_authorities`, compare and preserve those exact path/digest records. Apply only the selected approved Block and conditions described by the Scope; do not turn optional transition authority into a new mode or mandatory stage.

Use the caller-supplied exact readable role and validator paths from the same source or installed skills snapshot. Installation in a particular host is optional. An observed source or validator mismatch is an environment limit to return to the caller. Do not begin implementation to obtain a review digest.

The Plan normally lives at `<Project-Root>/docs/planning/work/<work-slug>/plans/PLAN-NNN.md`. The number is a navigation locator, not a product obligation. A shared method may be used only when the exact Scope impact is genuinely shared; unrelated Scopes do not wait for one another.

## Execution and independence

Preserve a clearly selected execution mode/model/effort for each role. Resolve a genuinely missing selection only through the caller's current policy. Never promote a host default or recommendation into a user selection.

Corrective method revision and fresh independent review do not change the user-selected implementation actor/model/effort/mode; only an applicable explicit user change does. Expected output-byte changes within the reviewed method do not alone require Plan revision. This continuity creates no permission beyond current stage, stop or effect limits.

Planner and Reviewer are separate invocations. The writer cannot approve its own Plan in the same invocation. There is no hidden fan-out, fixed roster, extra reviewer, consensus ceremony or automatic DIRECT fallback. If an independent invocation or required capability is unavailable, return the useful Plan plus the exact independence limit; do not manufacture ADMIT.

The Planner reads `references/plan.md`. The independent Reviewer reads `references/review.md` and the relevant grounding/conditional-start rules in `references/plan.md`. A permitted DIRECT role reads its own reference. No worker implements product code or issues a verification verdict.

## Preparation flow

1. Bind the exact Scope and all Thesis sources; confirm current bytes, Scope status and applicable user instructions.
2. The Planner traces the actual product entry/read path, deciding writers/readers, state/effect ownership, preserved behavior and authoritative readback, then records the implementation-grounded failure frontier and only the method detail needed for this Scope. The frontier is bounded by actual implementation clues and approved obligations, not a fixed risk roster or Cartesian matrix.
3. The Reviewer independently reads the complete original meaning, current implementation and primary evidence before accepting the Planner's diagnosis or frontier as a frame. It checks every authored Acceptance scenario and product success/failure condition, realistic bypasses, competing causes, other writers/readers, ordering/interruption/partial effects, identity, persistence, resource or scheduler boundaries, external-effect settlement and the proposed self-check/readback. It challenges material-looking omissions and transition traces that stop before recovery or the contract-allowed terminal result.
4. The Reviewer writes exactly one JSON artifact at the supplied outside-root path using schema `iis-scope-plan-review/v2`. Preserve its bytes, digest, rationale, findings, limits and conditional start scope unchanged; do not rewrite it into a prose approval or introduce a second failure-model artifact.
5. `ADMIT` is valid only for the exact current Scope method and start scope, with no unresolved material finding or unresolved contract gap. `REVISE` returns a method issue to the Planner; contract issues return to Main for the owning Thesis, Baseline or Scope correction under `iis-workflow`'s re-entry rules. Missing evidence returns to the authority/environment owner. Repeat affected work only after substantive change and a current independent review.

Preparation may inspect sources and write Plan/review artifacts. Planner experiments may change only a temporary scratch area isolated from product originals, the project working tree, shared services, real data and external systems. Preserve inputs, reproduction method, observations and limits in Plan evidence, then clean up temporary outputs. This permission never overrides current read-only, stage-only or no-execution instructions; return work outside current authority to its existing owner. Apply `references/plan.md` for scratch grounding and effectful conditional first work, not product mutation during preparation.

## Plan Review artifact contract

The review is one outside-root JSON artifact, not a second approval store:

```json
{
  "schema": "iis-scope-plan-review/v2",
  "project_root": "<canonical absolute root>",
  "plans": [{"path": "<exact project-local Plan>", "sha256": "<actual bytes digest>"}],
  "contracts": [{"scope_path": "<exact Scope>", "scope_sha256": "<actual bytes digest>", "thesis_sources": [{"path": "<exact bound Thesis>", "sha256": "<actual bytes digest>"}], "transition_authorities": []}],
  "review_origin": {"reviewer": "<actual independent reviewer>", "evidence_reference": "<raw invocation or primary evidence reference>"},
  "decisions": [{
    "scope_path": "<exact Scope>",
    "decision": "ADMIT",
    "rationale": "<substantive basis against the complete Scope meaning>",
    "start_scope": "<exact work this Scope may start>",
    "findings": [],
    "conditions": []
  }]
}
```

Use one contract and one decision for the exact Scope. Every Plan/common Plan used by the decision appears in `plans`. Within the existing v2 shape, `rationale` identifies the reviewed Plan frontier anchor and makes the independent basis inspectable: the implementation-grounded frontier considered, the admission-controlling minimal counterexamples or discriminators, and any load-bearing exclusion basis. Do not add a mandatory field or schema alias merely to restate that prose. `findings` preserve each material observation or advisory with `kind` (`contract_gap`, `method` or `evidence_limit`), `anchor`, `observation`, `material`, `disposition` (`unresolved`, `dismissed` or `resolved`), `basis`, `next_owner`, and optional exact byte/evidence references. `conditions` use `plan_anchor`, `permitted_initial_work`, `discriminating_observation`, `dependent_work_not_yet_permitted` and `response_if_refuted`. Keep the artifact limited to current Scope method admission; no legacy delivery artifact is accepted.

Hashes are calculated with ordinary tools from bytes actually reviewed. `thesis_sources` contains every bound Thesis source; `transition_authorities` contains each applicable bound original as `{path, sha256}`, or `[]` when absent. Recheck Scope, Thesis, applicable Transition and Plan bytes before returning the review. Currentness checks detect changed bytes, not reviewer identity or semantic truth. A plan/review file or field presence cannot replace a completed independent judgment and its attributable primary evidence. Historical review shapes remain history, not active aliases for v2.

## Terminal result

```text
SCOPE PLAN RESULT
Project Root: <exact canonical root>
Scope: <exact Scope path>
Plans:
- <exact Plan/common-Plan paths>
Plan Review: <exact outside-root JSON path | None>
Decisions:
- <Scope path — ADMIT | REVISE | EVIDENCE_NEEDED, rationale/start scope>
Evidence: <actual independent invocation and primary evidence references>
Limitations: None | <exact unavailable evidence/independence/capability/currentness>
Completion: COMPLETE | BLOCKED | PARTIAL
```

`COMPLETE` requires a current independent review with `ADMIT` for this exact Scope. A missing reviewer, `REVISE`, `EVIDENCE_NEEDED`, stale artifact or smaller result is `PARTIAL` or `BLOCKED` according to the actual boundary. Preserve the exact next owner/action. This role never marks Scope `done`, implements it, verifies it, or starts a later Scope.
