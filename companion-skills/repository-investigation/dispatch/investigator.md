# Repository Investigation delegated-lane projection

Use this projection only for a bounded investigator lane after the Repository Investigation Lead has performed reconnaissance and the current user explicitly selected `SUBAGENT`. The lead remains the investigation owner and writes any durable artifact.

## Required

- Exact Project Root and Repository Root.
- Exact Investigation Objective and one assigned lane area/question.
- Why the lane is material to the objective.
- Current read/effect authority and explicit exclusions.
- Allowed evidence and any exact required source anchors.
- Current source/repository identity when material to the evidence.
- `Delegated Investigator: yes` and ordinary result destination back to the lead.

## Optional

- Decision context that explains why the answer matters without selecting a preferred conclusion.
- Existing attributable evidence anchors for this lane.
- A bounded runtime readback target when currently authorized.

## Forbidden framing

- Do not supply a preferred conclusion or an implementation recommendation as the objective.
- Do not provide other worker conclusions as a voting or consensus frame.
- Do not ask the worker to choose product policy, Scope or method.
- Do not ask the lane worker to write the durable investigation artifact or delegate again.
- Do not expand the lane into a repository-wide inventory.

## Assignment pattern

```text
Investigate this one bounded lane from current primary evidence, challenge its first model with a plausible counterpath, and return attributable facts, inferences, unknowns and limits to the lead.
```

## Independence guard

Other worker agreement is not evidence. Derive the lane answer from primary sources and preserve any attributable contradiction or counterexample even when it conflicts with the lead's initial model.

## Result

Return `REPOSITORY INVESTIGATION WORKER RESULT` to the lead with actual roots, inspected scope, facts, inferences, counterevidence, absence-search boundaries, unknowns, anchors and lane completion. Do not start planning, remediation or verification.
