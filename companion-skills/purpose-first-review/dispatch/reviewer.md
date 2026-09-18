# Purpose-First Reviewer dispatch projection

This projection selects inputs for a delegated purpose-first review. The review order, finding discipline and verdict meanings remain owned by `purpose-first-review/SKILL.md`.

## Required

- Exact proposed change, policy, artifact or diff to review and its current identity.
- Current user review request and stop/read-only limits.
- Intended purpose, or the exact authoritative source from which the reviewer must derive it.
- Applicable higher-authority constraints and existing mechanisms relevant to that purpose, or explicit `None`.
- Primary evidence needed to judge concrete behavior, material effect and tradeoffs.
- Selected reviewer model/effort and ordinary result destination when delegated.

## Optional

- Realistic alternatives that preserve the same mandatory purpose.
- Attributable proposer rationale as navigation, not proof.
- Explicit user request for non-blocking improvement exploration.

## Forbidden framing

- Do not seed `NO PROBLEM`, `REQUIRED CHANGE`, `CANNOT DETERMINE` or a required finding count.
- Do not demand a finding merely because the change concerns security, audit, governance or verification.
- Do not present a preferred architecture as the review criterion.
- Do not request unsolicited optional improvements when the user asked only whether a material problem exists.

## Assignment pattern

```text
Determine whether this exact change has a concrete material problem or purpose failure, and require only the minimum correction that preserves its intended purpose.
```

## Independence guard

The proposal's label and rationale do not establish necessity or effectiveness. Judge actual behavior and system effect, separate introduced/worsened problems from pre-existing ones, and stop with `NO PROBLEM` when no material defect is established.

## Result

Return the compact owning-role review: verdict, concrete purpose, material findings if any, purpose-gate result, necessary tradeoffs and minimum required action only when needed. Do not manufacture findings or add a new review stage.
