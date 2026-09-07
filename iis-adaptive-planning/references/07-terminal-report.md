# Adaptive Terminal and User-Return Reports

## Decision provenance

For an Adaptive report that stops or redirects because of an authority/gate/evidence boundary, or for an owner-level STOP while the Adaptive invocation may still continue, preserve the owning result and include the same compact provenance semantics used by Baseline IIS:

```text
Decision: <existing result/disposition or exact route>
Governing authority: <skill/owner> / <stable section or rule>
Observed condition: <smallest current fact, unknown, or unresolved item that triggered the rule>
Effect: <what cannot continue or which owner boundary has ended>
Next allowed action: <exact owner/action or None>
```

When an owner result is not the whole-run result, also include `Owner status`, `Invocation status`, and `Returned to`. Do not infer a domain cause from a tool/transport/protocol failure, do not replace the exact owner result with an Adaptive wrapper, and do not expose hidden reasoning. Successful whole-run completion needs no extra provenance block beyond the facts already required by its terminal report.

When current attributable readback directly contradicts the Completion Predicate and the current user has disabled corrective continuation, use the existing provenance form above as the terminal: state the unsatisfied predicate, exact counterexample and existing owner, `Next allowed action: None`, `Whole-run completion: no`, then STOP. Do not call a known contradiction evidence insufficiency, ask the user to reconsider an already-settled read-only instruction, or use the Mandate-ceiling authority-gap report for a disabled stage. Recognizing that whole-run completion is false does not issue a new AC/Ticket verdict or authorize reopening `done`.

## Run Contract input required

Use before any planning or delivery mutation when [09-run-contract.md](09-run-contract.md) cannot close one material field from current authority and inspectable facts.

```text
IIS ADAPTIVE RUN CONTRACT: USER INPUT REQUIRED

Goal Outcome: <settled outcome or unresolved>
Required Named Items: <settled list or None required>
Candidate Named Items: <settled list or None named>
Resolved fields:
- <field: value>

Decision required: <smallest exact unresolved field>
Why different answers change the run: <required scope | candidate freedom | delivery stage | continuation authority | completion meaning>
Options:
- <option and consequence>

Mutation started: no
Next action after resolution: close Run Contract and enter <Scope Shaper | Ask Matt | To Spec | To Tickets>
STOP
```

Do not ask the user to restate settled fields or approve a fully derived form.

## Current-Increment planning phase complete

Use only after the current canonical IIS terminal conditions are actually satisfied: one approved current Spec plus its reviewed, validated complete Ready Ticket Set.

```text
IIS ADAPTIVE PLANNING PHASE COMPLETE

Mandate: <exact companion path/revision or current-conversation authority>
Mandate Continuation Ceiling: CURRENT_INCREMENT | BOUNDED_OUTCOME | MANDATE_OUTCOME
Implementation: yes | no
Verification: yes | no
Run Completion Boundary: READY_TICKET_SET | CURRENT_INCREMENT_IMPLEMENTED | CURRENT_INCREMENT_DELIVERED | NAMED_REQUIRED_ITEMS_DELIVERED | BOUNDED_OUTCOME_SATISFIED | MANDATE_OUTCOME_SATISFIED
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
Planning owner terminal: validated complete Ready Ticket Set
Planning owner result: STOP — terminal IIS Planning output
Decision: <RUN_COMPLETE | CONTINUE_TO_IMPLEMENTATION | CONTINUE_TO_HEURISTIC_PROBE | RETURN_AUTHORITY_GAP>
Governing authority: iis-adaptive-planning / Terminal boundary + active Run Contract
Observed condition: <validated complete Ready Ticket Set plus current Completion Predicate result>
Effect: IIS Planning ownership ends here; the Adaptive invocation <completes | continues under Outer Main | returns an authority gap>
Next allowed action: <Outer Main terminal report | implementation | heuristic probe | authority return>
Owner status: COMPLETE
Invocation status: COMPLETE | INCOMPLETE
Whole-run predicate satisfied: yes | no
Returned to: Outer Main
Outer disposition: RUN_COMPLETE | CONTINUE_TO_IMPLEMENTATION | CONTINUE_TO_HEURISTIC_PROBE | RETURN_AUTHORITY_GAP
```

Do not append an offer to implement, verify, or plan the next provisional Increment as though those actions are part of IIS Planning.

Return the Ready Ticket Set and the closed Run Contract to Outer Main. Under explicit Adaptive activation, Outer Main continues the current Increment through exactly the enabled delivery stages without another approval merely because ownership changes. The planning owner STOP is not an invocation STOP.

When the active Run Completion Boundary is `READY_TICKET_SET`, the planning phase also satisfies whole-run completion and Outer Main emits the Run Complete report below. For every broader boundary, planning phase completion alone is not whole-run success.

## Current Increment implemented

Use when `Implementation: yes`, `Verification: no`, and every current canonical Ticket in the validated Ready Ticket Set has one exact implementation lifecycle result with `Completion: COMPLETE`.

```text
IIS ADAPTIVE CURRENT INCREMENT IMPLEMENTED

Current Increment: <exact INC path>
Implementation denominator: <complete>/<total>
Implementation results:
- <Ticket path — exact implementation report/checkpoint>
Verification requested: no
Heuristic probe claimed: no
Final Ticket states:
- <Ticket path — exact current status>
Run Completion Boundary: CURRENT_INCREMENT_IMPLEMENTED
Completion Predicate satisfied: yes
Independent verification claimed: no
Ticket progression to done claimed: no
Disposition: RUN_CONTRACT_SATISFIED
STOP
```

Do not emit this report from one Ticket result, a partial denominator, or an implementation result that changed a Ticket to `done`.

An implementation-only terminal does not authorize success re-entry into another Increment. If Required Named Items remain outside the current Increment, return the smallest Verification or Run Completion Boundary decision rather than claiming the broader run complete.

## Adaptive run complete

Use only when the active Run Contract's exact Completion Predicate is actually satisfied. For `CURRENT_INCREMENT_DELIVERED`, this requires not just the complete exact `done` denominator but also an existing Ticket acceptance owner and current attributable evidence/readback for every approved parent obligation applicable to that Increment. For every boundary, preserve the claim limits of the owning evidence and exclude future, candidate, Non-Goal, and unrelated obligations that the active boundary does not make applicable.

```text
IIS ADAPTIVE RUN COMPLETE

Mandate: <exact companion path/revision or current-conversation authority>
Mandate Continuation Ceiling: CURRENT_INCREMENT | BOUNDED_OUTCOME | MANDATE_OUTCOME
Run Completion Boundary: READY_TICKET_SET | CURRENT_INCREMENT_IMPLEMENTED | CURRENT_INCREMENT_DELIVERED | NAMED_REQUIRED_ITEMS_DELIVERED | BOUNDED_OUTCOME_SATISFIED | MANDATE_OUTCOME_SATISFIED
Goal Outcome: <exact Run Contract outcome>
Required Named Items:
- <item or None required>
Candidate Named Items:
- <item or None named>
Required Item Policy: EXACT_REQUIRED_SET | REQUIRED_FLOOR | NONE_REQUIRED
Implementation: yes | no
Verification: yes | no
Completion Predicate: <exact predicate>
Authoritative Readback: <fresh attributable evidence>
Final Current Increment: <exact INC path or None>
Final Ticket evidence:
- <exact Ticket path — implementation result | heuristic-probe result when Verification is yes | final canonical status>
Disposition: RUN_CONTRACT_SATISFIED
Remaining provisional horizon: non-authoritative; not a completion blocker
STOP
```

Populate the existing `Authoritative Readback` and `Final Ticket evidence` entries with the actual closure evidence used, including the effect of any owner-reported `Evidence limit` or `Remaining uncertainty`; do not add a second verdict or acceptance matrix. A limited PASS may support only the approved canonical fact or absence it actually establishes. It cannot support an unobserved runtime, operator, external, or integrated result. Canonical source/artifact/document/structure inspection is sufficient when that is the approved acceptance boundary.

Do not emit this report for a planning leaf STOP, one completed Ticket, one delivered Increment when Required Named Items remain, an implementation-only result when the boundary requires delivery, a blocked/inconclusive return, or roadmap exhaustion.

Candidate Named Items do not block this report unless the user revised them into Required Named Items.

## Current Increment delivered and broader completion assessment

Use only after the current Increment satisfies the full delivered boundary in [09-run-contract.md](09-run-contract.md)—complete exact `done` denominator, acceptance ownership for every applicable current parent obligation, and current attributable closure—when the active boundary is `NAMED_REQUIRED_ITEMS_DELIVERED`, `BOUNDED_OUTCOME_SATISFIED`, or `MANDATE_OUTCOME_SATISFIED`. Fresh actual product state and attributable authoritative readback must produce exactly one disposition:

- `RUN_CONTRACT_SATISFIED` — use the single `IIS ADAPTIVE RUN COMPLETE` report above; do not emit a second Mandate-complete terminal.
- `NEXT_INCREMENT_REQUIRED` — record the nonterminal transition below and continue through Outer Main to Scope Shaper in the same invocation.
- `USER_DECISION_REQUIRED` — use the material product decision report below.
- `EVIDENCE_REQUIRED` — use the completion-evidence report below and do not infer completion or Scope Shaper re-entry.

For `NEXT_INCREMENT_REQUIRED`:

```text
IIS ADAPTIVE CURRENT INCREMENT DELIVERED

Current Increment: <exact INC path>
Delivered Ticket denominator: <done>/<total>
Run Completion Boundary: <active broader boundary>
Required Named Items remaining:
- <item or None>
Completion Predicate satisfied: no
Fresh actual product result: <observable result>
Next disposition: NEXT_INCREMENT_REQUIRED
Returned to: Outer Main -> Scope Shaper
Invocation STOP: no
```

This is a nonterminal transition, not whole-run success. Do not stop merely to announce it, and do not declare completion from Ticket `done` status, WP exhaustion, or a provisional horizon alone. Completion requires fresh actual outcome evidence.

## Return to user for a material product decision

Use only when the active Mandate or closed Run Contract cannot resolve a real user-owned branch.

```text
IIS ADAPTIVE PLANNING: USER DECISION REQUIRED

Current planning unit: <Scope / INC / Ask Matt unit>
Mandate Continuation Ceiling: <active ceiling>
Run Completion Boundary: <active boundary>
Decision required: <smallest exact unresolved decision>
Why current authority cannot select one answer: <reason>

Recommended option: <option and concise basis, when one exists but authority still requires user choice>
Material alternatives:
- <alternative and product consequence>

What remains unchanged:
- <settled authority that will not be reopened>

Next leaf after resolution: <Scope Shaper | Ask Matt | To Spec | To Tickets>
Whole-run completion: no
STOP
```

Do not dump the entire planning analysis. Ask only for the branch that blocks authoritative continuation.

## Completion evidence required

Use when an existing acceptance owner is established but current attributable evidence cannot decide an obligation required by the active Completion Predicate. This includes a complete exact `done` denominator whose required current observation is missing, stale, `INCONCLUSIVE`, or limited beyond the claim, as well as a fully delivered current Increment whose broader outcome assessment cannot determine whether more product construction is required. A missing truthful acceptance owner is instead the exact To Tickets or upstream planning gap; do not disguise it as an evidence request.

```text
IIS ADAPTIVE COMPLETION EVIDENCE REQUIRED

Current Increment: <exact INC path>
Run Completion Boundary: <active boundary>
Completion Predicate: <exact predicate>
Available readback: <what was established>
Missing evidence: <smallest exact authoritative readback, operator evidence, or external condition>
Why completion cannot be decided: <attribution or availability gap>
Disposition: EVIDENCE_REQUIRED
Scope Shaper re-entry inferred: no
Whole-run completion: no
STOP
```

Do not classify missing completion evidence as product failure, Run Contract satisfaction, or a need for another Increment. Resume only when the missing attributable evidence or changed external condition can make one of the other dispositions valid.

This report is unavailable when current attributable evidence already contradicts the predicate. In that case preserve the observed non-completion and the existing owner/authorized route; if continuation is disabled, use Decision provenance above instead of requesting evidence that is already present.

## Run Contract authority gap

Use when the requested Run Completion Boundary exceeds the Mandate's current Continuation Authority ceiling and the current instruction does not itself authorize an exact Mandate revision.

```text
IIS ADAPTIVE RUN CONTRACT: AUTHORITY GAP

Mandate Continuation Ceiling: <CURRENT_INCREMENT | BOUNDED_OUTCOME | MANDATE_OUTCOME>
Requested Run Completion Boundary: <boundary>
Required continuation: <why another Increment or broader outcome authority is needed>
Smallest decision required: <revise Mandate ceiling | choose a narrower boundary>
Mutation started: no | stopped before broader re-entry
Whole-run completion: no
STOP
```

Do not silently lower the Run Completion Boundary or expand the Mandate.

## Baseline contract drift

Use when current Baseline changes make the Adaptive Delta impossible to apply without altering IIS product/artifact meaning.

```text
IIS ADAPTIVE PLANNING: CONTRACT DRIFT

Current Baseline rule: <exact rule/leaf>
Adaptive delta affected: <confirmation | continuation | reshaping | triage | run completion>
Conflict: <why both cannot be preserved>
Baseline IIS remains usable: yes
Adaptive planning continued: no
Whole-run completion: no
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

Adaptive trace may record the disposition, but does not replace the owning result. Every such return is whole-run incomplete unless the active Completion Predicate was already independently satisfied.

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
Whole-run completion: no unless the active predicate is independently satisfied
```

Unless the user explicitly disabled corrective re-entry, a material triage result continues to its owning correction route after an actual correction/new evidence rather than stopping merely to announce the classification. Report the triage at the eventual user-return, planning-phase, current-Increment, or Run Contract terminal boundary. Success continuation into another Increment remains governed by the Mandate ceiling and closed Run Contract.
