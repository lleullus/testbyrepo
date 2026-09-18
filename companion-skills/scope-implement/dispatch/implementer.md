# Scope Implementer dispatch projection

This projection selects invocation inputs for the admitted implementing actor. Implementation procedure and boundaries remain owned by `scope-implement/SKILL.md` and `references/implement.md`.

## Required

- Exact Project Root.
- Every bound Thesis original and exact ready Scope with actual-byte SHA-256.
- Applicable Transition Authority paths/digests, or `None` when absent.
- Exact reviewed Plan paths/digests.
- Exact current `iis-scope-plan-review/v2` artifact, digest, independent provenance, `ADMIT`, start scope, findings and conditions.
- Exact stable target and baseline working-tree/effect state, including pre-existing changes.
- Current implementation authority, permitted mutations/effects, stop/no-reentry limits and selected actor/mode/model/effort.
- Exact predecessor Verify/Probe finding, primary evidence, usable reproducer/limit, correction authority and prior-effect settlement when applicable.
- Non-obvious build/command/fixture/readback/reset/cleanup handoff when already established.
- Ordinary implementation-result destination or exact requested report path.

## Optional

- Existing implementation evidence and current environment limits.
- Navigation claims about unaffected obligations, never as verification exemptions.

## Forbidden framing

- Do not authorize Thesis, Scope, Plan or Plan Review mutation.
- Do not widen the reviewed method or external-effect authority.
- Do not treat `ADMIT`, a passing self-check or a historical verdict as product verification.
- Do not prescribe blind retry after an uncertain non-idempotent effect.

## Assignment pattern

```text
Implement the exact admitted method for this Scope, perform the cheapest valid self-checks for the changed behavior, and return the stable current target and evidence handoff without issuing a semantic verification verdict.
```

## Independence guard

The Plan and Review bind the admitted method; they do not prove implementation success or authorize Scope expansion. Predecessor findings are correction inputs, not current-target verdicts.

## Result

Return `SCOPE IMPLEMENT RESULT` under the owning contract with actual delta and attribution, finding dispositions, discriminating self-checks and limits, execution handoff, current admission, stable verification target and `COMPLETE | PARTIAL | BLOCKED`. Never change Scope status.
