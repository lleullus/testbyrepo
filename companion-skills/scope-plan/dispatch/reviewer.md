# Independent Scope Plan Reviewer dispatch projection

This projection selects inputs for the independent Plan Reviewer. The review method and judgment remain owned by `scope-plan/SKILL.md`, `references/review.md` and the relevant grounding/conditional-start rules in `references/plan.md`.

## Required

- Exact Project Root.
- Every bound Thesis original with exact path/revision and actual-byte SHA-256.
- Exact ready Scope path and actual-byte SHA-256.
- Applicable Transition Authority exact paths/digests, or `None` when absent.
- Exact current Plan path and actual-byte SHA-256.
- Current implementation/repository identity and every load-bearing primary-evidence locator the method relies on.
- Exact predecessor finding/reproducer/limit when corrective planning applies.
- Current review-only authority, stop limits and selected reviewer model/effort.
- Actual separate reviewer invocation identity/result destination.
- Exact outside-Project-Root `iis-scope-plan-review/v2` output path and successor-readability requirement.

## Optional

- Supplied Repository Investigation as evidence navigation.
- Planner-declared failure frontier, checks and exclusions as Plan content to assess.

## Forbidden framing

- Do not ask the Reviewer to check only named frontier items or requirements selected by Main.
- Do not seed `ADMIT`, `REVISE`, `EVIDENCE_NEEDED` or an expected finding count.
- Do not describe the Planner's diagnosis as established fact.
- Do not authorize implementation, Scope/Thesis mutation or effectful evidence acquisition.

## Assignment pattern

```text
Independently determine whether the exact Plan is a sufficient, executable method for the exact Scope and bound product meaning.
```

## Independence guard

Derive the material implementation-grounded review frontier from the original Thesis, Scope, current implementation and primary evidence before accepting the Planner's diagnosis, frontier, proposed checks or exclusions. Planner findings are navigation only and are not presumed complete, correct or admission-controlling.

## Result

Write exactly one current `iis-scope-plan-review/v2` artifact at the supplied path and return its path/digest, primary evidence and one role-owned decision. Preserve rationale, findings, conditions, prerequisites, evidence locators and limits unchanged for the implementation handoff.
