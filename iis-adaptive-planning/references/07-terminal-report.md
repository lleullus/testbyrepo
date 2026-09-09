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

When an owner result is not the whole-run result, also include `Owner status`, `Invocation status`, and `Returned to`. Use the existing `Observed condition`, `Effect`, and `Next allowed action` entries to identify the remaining assigned Goal/required scope and actual blocker or continuation; do not add a Goal report schema. Preserve exact owner results and tool/transport limits without inventing a domain cause or exposing hidden reasoning. Successful whole-run completion needs no extra provenance block beyond its terminal facts.

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
Why different answers change the run: <required scope | candidate freedom | delivery stage | model/effort selection | continuation authority | completion meaning>
Options:
- <option and consequence>

Mutation started: no
Next action after resolution: re-evaluate remaining fields; only if all are resolved, close the Run Contract, then request direct approval of the rendered CLOSED contract if its Approval Gate is required, otherwise enter the current owning planning leaf
STOP
```

Do not ask the user to restate settled fields. Do not ask approval of a fully derived form unless the current Run Contract Approval Gate is `required`; when it is required, resolving the missing input does not release that separate gate. If other material fields remain unresolved, keep `USER_INPUT_REQUIRED` instead of promising planning entry.

For unresolved delivery models, preserve settled stage choices and present one combined recommendation for only the missing selections, with the guide path/version, workload reason and meaningful alternatives. Ask the user to accept or revise that configuration. Do not describe recommended models as selected, start their dispatch, or turn this input question into a full Run Contract approval gate.

## Current-Increment planning phase complete

Use only after the current canonical IIS terminal conditions are actually satisfied: one approved current Spec plus its reviewed, validated complete Ready Ticket Set.

```text
IIS ADAPTIVE PLANNING PHASE COMPLETE

Mandate: <exact companion path/revision or current-conversation authority>
Mandate Continuation Ceiling: CURRENT_INCREMENT | BOUNDED_OUTCOME | MANDATE_OUTCOME
Implementation: yes | no
Verification: yes | no
Run Completion Boundary: READY_TICKET_SET | READY_EXECUTION_PLANS | CURRENT_INCREMENT_IMPLEMENTED | CURRENT_INCREMENT_DELIVERED | NAMED_REQUIRED_ITEMS_DELIVERED | BOUNDED_OUTCOME_SATISFIED | MANDATE_OUTCOME_SATISFIED
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
Decision: RUN_COMPLETE | CONTINUE_TO_PREPARATION | CONTINUE_TO_IMPLEMENTATION | CONTINUE_TO_VERIFICATION | RETURN_AUTHORITY_GAP
Governing authority: iis-adaptive-planning / Terminal boundary + active Run Contract
Observed condition: <validated complete Ready Ticket Set plus current Completion Predicate result>
Effect: IIS Planning ownership ends here; the Adaptive invocation <completes | continues under Outer Main | returns an authority gap>
Next allowed action: <Outer Main terminal report | preparation | implementation | verification | authority return>
Owner status: COMPLETE
Invocation status: COMPLETE | INCOMPLETE
Whole-run predicate satisfied: yes | no
Returned to: Outer Main
Outer disposition: RUN_COMPLETE | CONTINUE_TO_PREPARATION | CONTINUE_TO_IMPLEMENTATION | CONTINUE_TO_VERIFICATION | RETURN_AUTHORITY_GAP
```

Do not append an offer to implement, verify, or plan the next provisional Increment as though those actions are part of IIS Planning.

Return the Ready Ticket Set and the closed Run Contract to Outer Main. Under explicit Adaptive activation, Outer Main continues the current Increment through exactly the enabled delivery stages without another approval merely because ownership changes. The planning owner STOP is not an invocation STOP.

When `READY_TICKET_SET` faithfully covers the current planning-only assignment under `09-run-contract.md`, the completed planning phase also closes the run and Outer Main emits the report below. It cannot replace a broader assigned product Goal; other boundaries require their own actual completion evidence.

## Execution preparation complete or limited

Preserve the actual READY TICKET PLAN RESULT, Completion, exact Tickets/Plans, outside-root Plan Review, per-Ticket decisions and raw evidence/limits. Emit whole-run completion at READY_EXECUTION_PLANS only when every explicitly required preparation Ticket has current independent ADMIT. Both Implementation/Verification are no. REVISE/EVIDENCE_NEEDED, missing/stale review or unavailable independence preserves the exact preparation owner result and Whole-run completion no; it is not final FAILED/INCONCLUSIVE or an Adaptive defect classification. Planner/Heuristic intermediate output and structurally valid JSON never substitute for an actual independent reviewer result.

Do not create another preparation terminal label: the lead's READY TICKET PLAN RESULT is the producer consumed by Outer Main and the Run Complete form. Plan files alone do not satisfy product obligations, and preparation-only authorizes no source implementation, final discovery/verdict or done progression.

## Current Increment implemented

Use when `Implementation: yes`, `Verification: no`, the active `CURRENT_INCREMENT_IMPLEMENTED` contract passes Goal/required-item coverage in `09-run-contract.md`, and every current canonical Ticket has an exact implementation lifecycle result with `Completion: COMPLETE`. This reports only the requested implementation/self-check scope, not verified product delivery.

```text
IIS ADAPTIVE CURRENT INCREMENT IMPLEMENTED

Current Increment: <exact INC path>
Implementation denominator: <complete>/<total>
Implementation results:
- <Ticket path — exact implementation terminal report>
Verification requested: no
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

An implementation-only terminal does not authorize success re-entry. If assigned Goal or required scope remains outside the current Increment, return the smallest Verification or boundary decision rather than claiming broader completion.

## Adaptive run complete

Use only after [Goal and required-item coverage](09-run-contract.md#goal-and-required-item-coverage-invariant) is revalidated against relevant actual Source Authority and fresh evidence satisfies the sufficient Predicate. A Predicate true with assigned Goal unmet is contract mismatch, not success. For `CURRENT_INCREMENT_DELIVERED`, require the complete exact `done` denominator and existing acceptance ownership/current attributable closure for every applicable parent obligation. Exclude unassigned future/candidate/Non-Goal work, not assigned Goal obligations merely deferred from this Increment. Explicit stage-only success closes only its requested result.

```text
IIS ADAPTIVE RUN COMPLETE

Mandate: <exact companion path/revision or current-conversation authority>
Mandate Continuation Ceiling: CURRENT_INCREMENT | BOUNDED_OUTCOME | MANDATE_OUTCOME
Run Completion Boundary: READY_TICKET_SET | READY_EXECUTION_PLANS | CURRENT_INCREMENT_IMPLEMENTED | CURRENT_INCREMENT_DELIVERED | NAMED_REQUIRED_ITEMS_DELIVERED | BOUNDED_OUTCOME_SATISFIED | MANDATE_OUTCOME_SATISFIED
Goal Outcome: <exact current outcome faithful to the user's assignment>
Required Named Items:
- <item or None required>
Candidate Named Items:
- <item or None named>
Required Item Policy: EXACT_REQUIRED_SET | REQUIRED_FLOOR | NONE_REQUIRED
Implementation: yes | no
Verification: yes | no
Completion Predicate: <exact sufficient predicate for the assigned Goal and Required Named Items>
Authoritative Readback: <fresh attributable evidence at the actual approved boundary, within its claim limits>
Final Current Increment: <exact INC path or None>
Final Ticket evidence:
- <exact Ticket path — current preparation review if preparation-only | implementation terminal result | readable verifier semantic result and binding identity | caller ready_finalize verdict/progression result/basis | actual canonical status>
Disposition: RUN_CONTRACT_SATISFIED
Remaining provisional horizon: non-authoritative; not a completion blocker
STOP
```

Populate the existing `Authoritative Readback` and `Final Ticket evidence` with actual closure evidence and the effect of owner-reported `Evidence limit`/`Remaining uncertainty`; do not add a second verdict or acceptance matrix. Apply `09-run-contract.md`'s actual-boundary rule: limited PASS or a substitute cannot prove an unobserved runtime/operator/external result. Actual canonical artifact inspection and real authorized disposable execution remain valid for the approved claims they observe.

Do not emit this report from an unfaithful Goal summary, weak Predicate, planning leaf STOP, one delivered Increment or named-item list with assigned Goal still unmet, an implementation-only result when delivery is required, a blocked/inconclusive return, or roadmap exhaustion.

VERIFIED with Ticket Progression FAILED is not completed delivery even if actual Ticket bytes say done. Preserve verdict, exact progression failure, actual status and owning recovery evidence; the caller must not infer COMPLETED from the status string or repair authority itself.

Candidate Named Items do not block this report unless the user revised them into Required Named Items.

## Current Increment delivered and broader completion assessment

Use only after the current Increment satisfies the full delivered boundary in [09-run-contract.md](09-run-contract.md)—complete exact `done` denominator, acceptance ownership for every applicable current parent obligation, and current attributable closure—when the active boundary is `NAMED_REQUIRED_ITEMS_DELIVERED`, `BOUNDED_OUTCOME_SATISFIED`, or `MANDATE_OUTCOME_SATISFIED`. Fresh actual product state and attributable authoritative readback must produce exactly one disposition:

- `RUN_CONTRACT_SATISFIED` — use the single `IIS ADAPTIVE RUN COMPLETE` report above; do not emit a second Mandate-complete terminal.
- `NEXT_INCREMENT_REQUIRED` — record the nonterminal transition below and continue through Outer Main to Scope Shaper in the same invocation.
- `USER_DECISION_REQUIRED` — use the material product decision report below.
- `EVIDENCE_REQUIRED` — obtain reachable authorized readback; use the completion-evidence return below only for a remaining genuine evidence/authority/condition limit, without inferring completion or Scope Shaper re-entry.

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

Use when an existing acceptance owner is established but current attributable evidence cannot decide an obligation required by the faithful Goal/Predicate, after obtaining the reachable authorized readback. This includes missing, stale, inconclusive, or claim-limited current evidence despite a complete `done` denominator. A missing truthful acceptance owner is the exact To Tickets/upstream gap; a weak Predicate is outer contract correction. Do not disguise either as an evidence request or end an invocation while a valid authorized next action can resolve the gap.

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

Adaptive trace may record the disposition, but does not replace the owning result. Such a return is whole-run incomplete unless Goal/required-item coverage and actual completion evidence independently satisfy `09-run-contract.md`.

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
Whole-run completion: no unless faithful Goal/required-item coverage and the sufficient predicate are independently satisfied
```

Unless the user explicitly disabled corrective re-entry, a material triage result continues to its owning correction route after an actual correction/new evidence rather than stopping merely to announce the classification. Report the triage at the eventual user-return, planning-phase, current-Increment, or Run Contract terminal boundary. Success continuation into another Increment remains governed by the Mandate ceiling and closed Run Contract.
