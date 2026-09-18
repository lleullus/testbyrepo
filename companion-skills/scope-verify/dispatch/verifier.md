# Independent Scope Verifier dispatch projection

This projection selects inputs for one independent semantic verification invocation. The complete cycle and verdict remain owned by `scope-verify/SKILL.md` and `references/verify.md`.

## Required

- Exact Project Root.
- Every Scope-bound Thesis original and exact Scope path/status with actual-byte SHA-256.
- Applicable Transition Authority paths/digests, or `None` when absent.
- Exact stable implementation target paths and known byte/runtime identities.
- Declared scenario-effect paths, permitted effects, settlement/cleanup authority and external limits.
- Current verification request, stop/no-reentry limits and selected verifier model/effort.
- Actual separate verifier invocation identity and ordinary result/report destination.
- Exact role source paths/source identity for `scope-verify` entry and reference.
- Implementation result/evidence and mutation attribution for a normal delivery or corrective handoff; `None supplied` is valid for genuine standalone verification-only work.
- Exact predecessor Verify/Probe finding, primary evidence and reproducer/limit when applicable.

## Optional

- Current Plan Review and implementation-grounded frontier as navigation only.
- Prior primary observations with original target/invocation attribution and applicability information.
- Established build/command/fixture/readback/reset/cleanup handoff.

## Forbidden framing

- Do not require a fresh Plan or Plan Review for genuine verification-only work.
- Do not seed `VERIFIED`, `FAILED`, `INCONCLUSIVE`, a finding count or an execution-reduction decision.
- Do not instruct the verifier to accept the implementation report's impact assessment.
- Do not authorize product/shared-tool repair, Scope mutation, Probe dispatch or completion recording.
- Do not carry forward a historical PASS as a current-target verdict.

## Assignment pattern

```text
Independently adjudicate the complete exact Scope against the stable current target from sufficient discriminating evidence and authoritative readback.
```

## Independence guard

Implementation reports and Plan Review are navigation only. Resolve the actual target, current source/runtime identities, authored obligations and bounded as-built failure frontier independently. The verifier alone decides evidence breadth and the one current semantic verdict.

## Result

Return one complete `SCOPE VERIFICATION RESULT` with the actual independent invocation, exact originals/target/effect identities, every authored scenario disposition, primary evidence, currentness, cleanup/settlement, finding dispositions, limits and `VERIFIED | FAILED | INCONCLUSIVE`. The worker never repairs or records `done`.
