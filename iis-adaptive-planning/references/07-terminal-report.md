# Adaptive Terminal and User-Return Reports

## Current-Increment planning complete

Use only after the current canonical IIS terminal conditions are actually satisfied: one approved current Spec plus its reviewed, validated complete Ready Ticket Set.

```text
IIS ADAPTIVE PLANNING COMPLETE

Mandate: <exact companion path/revision or current-conversation authority>
Continuation Authority: CURRENT_INCREMENT | BOUNDED_OUTCOME | MANDATE_OUTCOME
Current Scope: <exact current Scope result or None for direct next-increment-ready work>
Current Increment: <exact current INC or None for direct next-increment-ready work>
Spec: <exact approved Spec>
Ready Tickets:
- <exact ready Ticket path>
Validation: PASS

Material delegated decisions:
- <decision and provenance, or None>

Reshaping:
- <old -> new INC summary, or None>

Unresolved user decisions: None
Planning terminal: validated complete Ready Ticket Set
STOP
```

Do not append an offer to implement, verify, or plan the next provisional Increment as though those actions are part of IIS Planning.

Under explicit Adaptive activation, this `STOP` is the IIS Planning ownership boundary. Unless the current user explicitly selected planning-only/stop-at-Ready-Tickets/no implementation/no verification, return the Ready Ticket Set to the outer caller, which continues the current Increment through the separate delivery skills without another approval merely because ownership changes. The caller is not IIS Adaptive Planning; see `08-delivery-continuation.md`.

## Mandate success completion

Use only after a fully delivered current Increment has entered success re-entry and fresh actual product state establishes `MANDATE_SATISFIED` for the applicable `BOUNDED_OUTCOME` or `MANDATE_OUTCOME`.

```text
IIS ADAPTIVE MANDATE COMPLETE

Mandate: <exact companion path/revision or current-conversation authority>
Continuation Authority: BOUNDED_OUTCOME | MANDATE_OUTCOME
Applicable outcome: <exact bounded or Desired Product Outcome>
Final delivered Increment: <exact INC path>
Actual product result: <observable result>
Authoritative readback: <fresh readback>
Disposition: MANDATE_SATISFIED
Remaining provisional horizon: non-authoritative; not a completion blocker
STOP
```

Do not declare Mandate completion from Ticket `done` status, WP exhaustion, or a provisional horizon alone. Completion requires fresh actual outcome evidence.

## Return to user for a material product decision

Use only when the active Mandate cannot resolve a real user-owned branch.

```text
IIS ADAPTIVE PLANNING: USER DECISION REQUIRED

Current planning unit: <Scope / INC / Ask Matt unit>
Decision: <smallest exact unresolved decision>
Why current authority cannot select one answer: <reason>

Recommended option: <option and concise basis, when one exists but authority still requires user choice>
Material alternatives:
- <alternative and product consequence>

What remains unchanged:
- <settled authority that will not be reopened>

Next leaf after resolution: <Scope Shaper | Ask Matt | To Spec | To Tickets>
STOP
```

Do not dump the entire planning analysis. Ask only for the branch that blocks authoritative continuation.

## Baseline contract drift

Use when current Baseline changes make the Adaptive Delta impossible to apply without altering IIS product/artifact meaning.

```text
IIS ADAPTIVE PLANNING: CONTRACT DRIFT

Current Baseline rule: <exact rule/leaf>
Adaptive delta affected: <confirmation | continuation | reshaping | triage>
Conflict: <why both cannot be preserved>
Baseline IIS remains usable: yes
Adaptive planning continued: no
STOP
```

Do not modify Baseline automatically to restore Adaptive behavior.

## Planning evidence insufficient

Use current Baseline leaf's own blocked/waiting result when it defines one. Adaptive should not invent a generic failure wrapper that hides the actual owner.

Examples:

- Scope Shaper missing project root -> Scope Shaper's current result
- canonical validator invalid -> current leaf's exact blocked/invalid result
- active adversarial gate missing Challenger/Intent Anchor -> current gate's exact result
- external/operator verification evidence unavailable -> verifier/triage result as applicable

Adaptive trace may record the disposition, but does not replace the owning result.

## Verification triage report

When Adaptive is invoked specifically to interpret a current verifier result, include:

```text
IIS ADAPTIVE VERIFICATION TRIAGE

Ticket: <exact Ticket>
Original verifier verdict: <exact verdict>
Classification: IMPLEMENTATION_DEFECT | VERIFICATION_MECHANISM_DEFECT | CONTRACT_OVERREACH | CURRENT_INCREMENT_MISMATCH | INCONCLUSIVE
Primary authority basis: <exact parent authority>
Disposition: <implementation | verification mechanism | Scope Shaper | Ask Matt | To Tickets | evidence required>
Contract changed: yes | no
Fresh verification required: yes | pending evidence
```

Unless the user explicitly disabled corrective re-entry, a material triage result continues to its owning correction route after an actual correction/new evidence rather than stopping merely to announce the classification. Report the triage at the eventual user-return or current-Increment terminal boundary. Success continuation into another Increment remains a separate Mandate decision.
