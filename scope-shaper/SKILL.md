---
name: scope-shaper
description: "Main's instructions for fixing one current IIS Scope during current-state reconciliation, before method writing. Preserve approved boundaries and serialize the implementation/verification contract without a separate Shaper stage."
---

# Current Scope Contract

Main uses these instructions while reconciling current state, not as a separate Shaper stage, delegated role or approval gate. Fix the current outcome and Acceptance in `SCOPE.md` before writing its method; reuse a sufficient current contract rather than reselecting it. An explicit Scope-only request stops with that contract, while a broader authorized request continues to Plan.

## Inputs

Read the latest user assignment and exact applicable Thesis originals. Inspect actual current product state, reusing supplied current investigation where sufficient. Read any explicitly applicable approved Transition Baseline and the current measured Block. No source is created merely to fill an input field.

Distinguish evidence from product authority. A past report or a candidate name is not a current product observation. Re-establish only load-bearing facts whose changes could alter the choice. Do not investigate every subsystem or re-run already reported failures just to confirm the user's observation.

## Choose the current result

Understand the connected product landscape before choosing: delivered capabilities, unmet required outcomes/means, candidate means, actual constraints and independently acceptable sibling outcomes. Preserve long-term intent without preapproving a future execution queue. For a small change this can be a short explanation, not a Work Package document hierarchy.

Reuse an applicable approved construction boundary under the transition rules below. Where no boundary is fixed, Main selects the smallest durable observable state change that advances the assigned result without severing necessary behavior, then fixes it in Scope before method writing. Actor, trigger/inspection, current→target result and authoritative readback must be identifiable in the explanation, not repeated as mandatory fields. Technical layers and file count do not define product scope. One Scope may require several internal technical tasks. Split only independently acceptable outcomes; keep inseparable preservation/integration obligations with the outcome they qualify.

A narrow current Scope must not erase the broader assigned Goal or required named items. Keep their original references and actual remaining state available to Main. Candidate removal does not waive the outcome it supported. If the user assigned only this stage or a narrow result, do not import the entire Thesis as extra work.

## Product gaps

Read relevant Thesis behavior, failure/recovery, UI, identity and truth boundaries. If a material product choice changes candidate selection or the current result, return to its exact Thesis section for resolution under current authority. Resolve determinable choices without another ceremony. Ask only for genuinely unresolved user-owned alternatives. Do not introduce policy in Scope merely because implementation would be convenient.

Product-Thesis exploration or a supplied Completion Brief may identify a gap, but neither is a required handoff artifact or a readiness verdict. Consume the exact adopted source and any supplied deciding evidence, rationale and limits; a question, hypothesis, local coverage label or selected locator is not product authority. Keep evidence-only unknowns separate from unresolved product choices. A missing fact that changes the promised boundary prevents ready; a method-only premise may remain for reviewed conditional first work. After meaning changes, assess which current Outcome/Acceptance actually needs revision under existing re-entry rules. Do not silently bind the latest Thesis, refresh hashes to hide drift, add every explored sibling to Scope or rewrite completed history.

## Transition contract

When an approved BASELINE-NNN applies, reconcile the current measured Block and relevant actual state against its entry/exit/readback, global/path invariants, continuation/abort limits and remaining Goal obligations. A Block number alone does not establish runtime, config, persistent-state or external-effect readiness. Re-establish only evidence that can change the current boundary; a boundary-critical unknown prevents making that contract ready, while a method-only premise may remain for Plan's reviewed conditional first work.

Reuse a Block Exit when it is the appropriate durable completion unit. If the approved original fixes an internal construction boundary or selection order, preserve it; do not split, merge or reorder it for method convenience. Otherwise a coarse non-atomic Block may allow Main to select a smaller independently acceptable result without revising the Baseline. HARD_ATOMIC remains one Scope with internal implementation steps. Record the selected Block and any applicable original boundary locator in Outcome/Acceptance, referencing existing conditions rather than copying a second policy. Block exit is not final transformation completion, and continuation authority never expands a narrower user stage request.

## Scope source

Write `docs/planning/work/<kebab-case-slug>/SCOPE.md` under the exact canonical Project Root. The direct artifact uses `Schema: iis-scope/v1`, `Project-Root` and `Status`. Use `draft` while current product decisions remain unresolved, `ready` once meaning and executable observation are sufficient. `done` is Main's completion record after independent verification, Coverage and currentness checks under `scope-verify`, not a planning or implementer write. `superseded` records a replaced unconsumed contract without rewriting delivered history.

Include:
- `## Product Authority`: one line per exact project-local Thesis source, `- /absolute/path sha256:<full UTF-8 digest>`. Reuse original revisions; do not create a per-Scope copy.
- `## Transition Authority` only when an approved transition contract applies: bind its exact project-local original with the same path/SHA-256 syntax. Record applicability, selected Block and relevant conditions in Outcome/Acceptance; a file hash does not grant approval or continuation authority.
- `## Outcome`: actual current state and evidence, the selected result, includes/excludes and relevant dependencies in ordinary prose.
- `## Acceptance`: observable scenarios sufficient to distinguish the promised result and applicable preservation/failure boundaries. Use meaningful subheadings when several scenarios are genuinely distinct; reuse those headings with the exact Scope path/revision as local Plan and evidence anchors, without a global ID scheme.
- `## Open Decisions` only when needed; any material current choice must be resolved before ready.

Add transition, migration, external conditions or re-entry notes only when they change what can be promised or done. Do not require Owner/Workstreams/None filler for a single simple result. Do not copy full Thesis policies into Scope; explain their current application and reference the originals. Some repetition needed to express a concrete observation is not a second policy authority.

Use `tools/validate_scope.py /absolute/path/to/SCOPE.md` for structural validation. Exact `VALID` proves canonical structure and source bytes, not semantic completeness or user approval. Check semantic fidelity directly: could this Scope pass while its adopted current product obligation is false? Resolve omissions without inventing unassigned requirements. Existing user-directed approval gates remain at their owning boundaries; faithful serialization adds no new approval.

## Acceptance and verification feasibility

Describe initial observable state, action/inspection, expected product result and authoritative readback wherever needed to distinguish success from a plausible failure. Include actual failure, late/duplicate response, identity and preservation cases that are material, not a fixed checklist. Do not prescribe implementation files, mocks, framework assertions or worker topology. A real artifact result can be checked by inspecting that artifact; an external-effect promise requires that effect's actual boundary. Mark unavailable evidence or permission honestly instead of substituting a surrogate.

The verifier judges all applicable authored obligations against the stable implementation. Return contract gaps to Main for the owning Thesis, Baseline or Scope correction under `iis-workflow`'s re-entry rules. Do not add ad hoc ACs during verification, weaken requirements to force PASS or regard internal test success as product completion.

## Contract revision and continuation

New actual evidence may change Main's current construction choice only where the adopted originals leave that choice open. A change to fixed transition geography first requires its Baseline revision; product meaning belongs to Thesis, and method alone to Plan, under `iis-workflow`'s re-entry rules. Preserve the assigned Goal, required items and source history. Never change Outcome/Acceptance as a method edit or overwrite a delivered Scope; changed contracts require affected planning/review before dependent implementation. An unchanged historical success is not current integration evidence.

Keep the exact Scope path, bound originals, chosen outcome, validation result and material open limits available to the requested next stage. A ready Scope goes directly to execution planning when the current request permits it, without a separate Shaper handoff. No shared-understanding document, Spec, Ticket Set, ready-for-matt transition or duplicate Increment handoff is generated.
