# Adaptive Routing and Planning Re-entry

## Execution model

Adaptive is an alternate execution contract, not an edit to Baseline leaf files.

For each leaf:

1. read the current canonical Baseline leaf;
2. preserve all of its product semantics, evidence requirements, authority ownership, admission checks, canonical artifact rules, validators, and non-approval completion criteria;
3. apply the exact Adaptive confirmation/continuation delta below;
4. preserve the closed invocation-local Run Contract from [09-run-contract.md](09-run-contract.md) across every leaf and ownership return; and
5. if an unlisted conflict appears, treat it as Baseline contract drift rather than inventing another override.

Apply the current Baseline leaf directly. Use the Adaptive Mandate only for genuinely user-owned planning decisions/continuation; do not reimplement a Baseline self-review/adoption guard or add another approval layer around To Spec/To Tickets.

## Run Contract admission precedes routing

Before the Starting route below can perform any planning mutation, Outer Main for the current explicit Adaptive invocation must close and render one Run Contract.

- If current authority determines Goal Outcome, Required Named Items, Candidate Named Items, Required Item Policy, Implementation, Verification, Run Completion Boundary, Completion Predicate, and Authoritative Readback, mark it `CLOSED` and route without another approval prompt.
- If a material field remains unresolved, mark it `USER_INPUT_REQUIRED`, ask only for that smallest field, and hard STOP before mutation.
- Read-only inspection needed to establish inspectable facts may precede closure.
- A later leaf may expose a genuine material contradiction that requires a Run Contract revision; return only that decision and preserve all settled fields.
- A Run Completion Boundary broader than the Mandate's Continuation Authority ceiling cannot close unless the current user instruction explicitly revises/adopts that broader authority.

Do not treat this as a new Baseline admission gate. It belongs to the explicit outer Adaptive invocation and does not alter ordinary IIS requests.

## Starting route

Use current `iis-workflow` admission unchanged.

- explicit Scope Shaper request -> Scope Shaper admission
- explicit Ask Matt request -> Ask Matt admission; it may still return to Scope Shaper
- explicit To Spec / To Tickets -> their current admission gates
- ordinary Adaptive request already next-increment-ready -> Ask Matt
- ordinary Adaptive request not next-increment-ready -> Scope Shaper
- status-only request -> current read-only state check / Observatory and hard STOP

Adaptive never makes a broad request next-increment-ready by assertion.

## Leaf delta matrix

### Scope Shaper

Preserve:

- direct current-state and connected-landscape investigation;
- optional Investigation Runner rules, including explicit user-only roster authority;
- Work Package/dependency semantics;
- construction candidate comparison;
- exactly one selected next Increment;
- current templates, unique work-slug rules, immutable revisions, validators, and artifact closure.

Adaptive delta:

- the ordinary single user confirmation of an otherwise complete Scope proposal may be satisfied by standing delegated confirmation when the Mandate resolves the selection and no Return-to-User Boundary is triggered;
- after canonical Scope/Increment closure validates, perform the post-shape Run Contract revalidation below; only after it passes, do not expose the ordinary manual-continuation STOP and return the exact selected `ready-for-matt` Increment to the Adaptive router to continue to Ask Matt in the same planning request;
- when a later leaf finds a construction-stage/foundation/split/merge/order defect, re-enter Scope Shaper directly if reshaping is delegated;
- preserve Required Named Items across Increment selection and reshaping without forcing all obligations into one current Increment;
- treat Candidate Named Items as mutable candidate means under the Mandate and evidence; and
- do not select a next Increment that would make the Run Completion Boundary exceed the Mandate ceiling.

#### Post-shape Run Contract revalidation

After canonical Scope/Increment closure and before Ask Matt handoff, compare the unsatisfied Required Named Items with the selected Increment's Includes/Excludes/Deferred scope, the active Run Completion Boundary, Completion Predicate, and Mandate Continuation Authority ceiling. Repeat the same revalidation whenever a material reshape changes the selected current Increment.

- If the active boundary is a broader named-item or outcome boundary and the Mandate ceiling permits it, continue with exactly one selected Increment while preserving the outer Required Named Items and Completion Predicate.
- If the active boundary is a current-Increment terminal and every unsatisfied Required Named Item is covered by the selected Increment, continue normally.
- If the active boundary is a current-Increment terminal but unsatisfied Required Named Items remain outside the selected Increment, treat that as contract mismatch and do not enter Ask Matt. A broader Mandate ceiling does not silently upgrade the narrow active boundary. Revise the Run Contract from already-clear current user authority or return only the exact boundary decision to the user; do not shrink Required Named Items.
- If the active boundary actually requires continuation beyond the Mandate ceiling, revise/adopt the Mandate only when current user authority grants that continuation; otherwise return the exact authority gap. Never close a smaller boundary merely to avoid the revision.

Keep hard:

- unresolved material evidence;
- missing required exact Runner roster when the user explicitly requested Runners;
- missing/unavailable project root when current Baseline requires it for durable artifacts;
- all validator failures.

### Ask Matt / Behavior / UI

Preserve:

- Scope/Increment admission;
- integrated first-hand investigation before the decision frontier;
- Behavior Design and UI-routing authority ownership;
- verification-feasibility closure;
- existing authority reuse rules;
- product-policy/Behavior/UI decision depth;
- current adversarial-consensus semantics when explicitly activated.

Adaptive delta:

- resolve each current user-owned decision through the Mandate before presenting a question;
- if the delegated-decision test produces one answer, adopt it as `DELEGATED_RECOMMENDATION` and continue the dependency graph without a user round-trip;
- if the frontier is empty after authority/Mandate resolution, continue directly;
- ordinary final approval of completed Behavior/UI authority and integrated shared understanding may use standing delegated confirmation;
- when adversarial consensus is active, keep activation and exact Challenger designation direct-user-only; before the first Challenger invocation apply the pre-consensus delegated Intent Anchor finalization in `02-delegated-decision-policy.md`;
- when that rule determines one faithful current Anchor, the delegated-decision test passes, and no Return-to-User Boundary, authority conflict, separately required disclosure expansion, or explicit current request for direct Anchor review exists, finalize the Anchor as `DELEGATED_RECOMMENDATION` and invoke the exact designated Challenger without a user round-trip; otherwise return only the smallest unresolved Anchor, authority, or disclosure decision;
- after current `ADVERSARIAL CONSENSUS REACHED`, let Ask Matt alone classify the latest reviewed candidate's authority delta as `NONE`, `MATERIAL`, or `UNCERTAIN` using `02-delegated-decision-policy.md`;
- for exact `NONE` with all delegated-finalization eligibility checks passing, approve the applicable completed Behavior/UI authority, finalize the exact integrated shared understanding as `DELEGATED_RECOMMENDATION`, and continue to To Spec without another user round-trip;
- for `MATERIAL` or `UNCERTAIN`, return only the exact unresolved authority decision to the user; if the user's response materially changes the candidate while adversarial activation remains current, require renewed Challenger review before finalization;
- whether finalization is `USER_EXPLICIT` or `DELEGATED_RECOMMENDATION`, treat it as leaf-local and do not revise the Run Contract Goal Outcome, Required Named Items, required/candidate classification, delivery-stage limits, Run Completion Boundary, or Completion Predicate without independent current user authority;
- after completion, continue to current To Spec rather than stopping for a manual leaf request; and
- preserve the Run Contract Goal Outcome, required/candidate classification, delivery-stage limits, and completion predicate without inventing current-Increment product meaning for later obligations.

Return to the user only for the unresolved material frontier that survives the Mandate and closed Run Contract.

Keep hard:

- authority conflict;
- a material decision outside delegation;
- adversarial-consensus activation and exact Challenger binding; an unresolved material Intent Anchor fidelity/authority decision, an explicit current direct-Anchor review request, and any separately required disclosure expansion remain user-return boundaries;
- any current leaf requirement that cannot be satisfied by evidence or valid authority.

### To Spec

Preserve:

- current Source Increment admission/revalidation;
- UI and Behavior authority gates;
- normative source lock;
- exact canonical path, metadata, headings, Verification Expectations schema, and mandatory contract audit;
- current product-contract completeness requirements.

Adaptive delta:

- use the current Baseline To Spec self-review/adoption guard unchanged;
- in explicit Adaptive mode, a current Ask Matt Intent Anchor finalization whose provenance is `USER_EXPLICIT` or `DELEGATED_RECOMMENDATION` satisfies the Baseline `user-confirmed Intent Anchor` admission condition for that exact current candidate; ordinary non-Adaptive To Spec still requires direct user-confirmed Intent Anchor;
- when an active adversarial-consensus gate reaches To Spec, accept only an exact Ask Matt-finalized latest shared understanding whose finalization provenance is `USER_EXPLICIT` or `DELEGATED_RECOMMENDATION`, whose latest complete candidate has current `ADVERSARIAL CONSENSUS REACHED`, whose Challenger final review has no later material candidate change, and whose applicable Behavior/UI authority is approved;
- in explicit Adaptive mode, a valid Ask Matt `DELEGATED_RECOMMENDATION` finalization satisfies the Baseline post-consensus finalization precondition for that exact candidate; ordinary non-Adaptive To Spec still requires the Baseline direct final user approval;
- do not reinterpret the Mandate or Run Contract, reclassify `NONE`/`MATERIAL`/`UNCERTAIN`, or rerun the delegated-decision test inside To Spec; if the finalized authority is missing, stale, conflicting, or appears to require new product meaning, return to Ask Matt rather than creating a second finalization owner;
- carry finalization provenance only in the current invocation context; do not create a receipt, sidecar, gate-state file, or canonical Adaptive metadata for it;
- do not add standing-delegation provenance for a faithful structural projection that Baseline already adopts by self-review;
- continue to current To Tickets without a manual user request; and
- project only the current Increment even when the outer Run Contract spans more Required Named Items or broader outcomes.

If accurate Spec writing requires a new product requirement, boundary, Non-Goal, verification promise, or other material meaning, re-enter Ask Matt or Scope Shaper rather than weakening the guard.

### To Tickets

Preserve:

- exact approved parent Spec admission;
- minimal independently observable Ticket decomposition;
- parent-Spec/Behavior/UI traceability;
- exact Ticket schema and Verification flow fields;
- solution-independence rules;
- blocker semantics;
- adjacent Ticket validator and set validator;
- `Worker:` remaining empty;
- Ready Ticket Set as terminal IIS Planning output.

Adaptive delta:

- use the current Baseline To Tickets whole-Set self-review/readiness guard unchanged;
- do not add standing-delegation provenance for a faithful structural projection that Baseline already readies by self-review; and
- after a complete validated Ready Ticket Set exists, report current-Increment Adaptive **planning phase** complete and return the Set plus the closed Run Contract across the IIS Planning ownership boundary to Outer Main as described in `08-delivery-continuation.md`.

Do not use Adaptive to create preparatory Tickets, implementation sequences, extra verification mechanisms, or Tickets for Required Named Items that do not belong to the current Increment.

## STOP semantics

Adaptive changes only **manual intra-planning continuation stops** for the same current planning unit.

Soft under active Adaptive Mandate:

- confirmed Scope -> manually request Ask Matt
- completed Ask Matt -> manually request To Spec
- approved Spec -> manually request To Tickets

Hard even in Adaptive:

- status-only inspection STOP;
- unresolved Run Contract field STOP before mutation;
- unresolved user decision STOP;
- special explicit-only gate STOP;
- invalid/missing authority or validator failure STOP until the exact defect is resolved;
- complete Ready Ticket Set STOP for IIS Planning ownership;
- boundary between IIS Planning and implementation/verification/delivery ownership. Outer Main applies the closed Implementation and Verification fields rather than assuming both stages from the planning STOP.

An owner STOP is not an invocation STOP. Outer Main compares every exact owner result with the active Run Completion Boundary and Completion Predicate. Blocked, inconclusive, user-return, contract-drift, and no-progress STOPs remain incomplete returns; only an actually satisfied Run Contract is whole-invocation success.

`CURRENT_INCREMENT_IMPLEMENTED` is an implementation-only invocation terminal. It does not create a success re-entry cycle and does not mark Tickets `done`.

A later success re-entry after every current Ticket is actually `done` is a **new Adaptive planning cycle**, not a continuation through the Ready Ticket STOP. It is governed by the active Mandate's Continuation Authority ceiling, the closed Run Contract, and `08-delivery-continuation.md`.

## Re-entry matrix

| Observation | Primary meaning | Route |
| --- | --- | --- |
| current unit bundles foundation/intermediate/mature product states | construction shape defect | Scope Shaper |
| independently acceptable siblings are bundled | split/order defect | Scope Shaper |
| current outcome depends on a missing durable product foundation | construction order defect | Scope Shaper |
| actor/ownership/lifecycle/product-policy meaning is unresolved inside valid INC | product contract incomplete | Ask Matt |
| To Spec needs new product meaning | upstream planning incomplete | Ask Matt or Scope Shaper |
| Spec mis-serializes already approved meaning | projection defect | To Spec |
| Ticket omits/strengthens/weakens parent meaning | projection defect | To Tickets; Ask Matt if parent itself is wrong |
| Ticket cannot form an independently acceptable product unit because current INC shape is wrong | construction shape defect | Scope Shaper |
| Ticket cannot express required Behavior meaning because authority is incomplete | product contract incomplete | Ask Matt |
| current canonical Spec/Ticket projection is complete and valid | normal forward route | continue / planning terminal |
| current Increment is delivered but Required Named Items or an outcome predicate remain unsatisfied | outer run incomplete | fresh actual-state Scope Shaper re-entry when authorized |
| current Increment is implemented with Verification `no` | implementation-only terminal | report exact Run Contract result; no success re-entry |

## Re-entry discipline

Re-entry is not retrying the same answer until a validator passes. Before repeating a leaf, identify a material candidate correction, changed canonical authority, Run Contract revision, or genuinely new evidence that makes the second pass different. If the same artifact/evidence/finding would repeat without such progress, stop at the owning boundary instead of adding retry state.

Within a planning leaf, perform additional investigation only when its possible result can change product/Scope/Behavior/UI/completion meaning, the planning disposition, a Run Contract field, or a Return-to-User boundary. Once current authority determines one complete faithful projection, advance instead of extending the leaf for confidence polishing.

If a validator fails structurally, repair the structural projection without changing product meaning. If the only repair would change product meaning, return upstream.

## Delivery evidence returning to planning

Fresh implementation/runtime/verification evidence may trigger an Adaptive planning re-entry, but it remains evidence rather than product authority.

Examples:

- implementation demonstrates that an assumed existing product acceptance surface does not exist -> reconsider the planning contract/INC as applicable;
- verifier establishes that a Ticket flow is stronger than its exact parent outcome -> projection re-entry;
- current runtime shows the original INC is no longer the actual starting state -> Scope Shaper re-entry against the actual state;
- a delivered current Increment leaves a Required Named Item or broader Completion Predicate unsatisfied -> success re-entry from actual state rather than declaring whole-run completion.

Do not make planning history match an expected implementation. Re-plan from the actual current product state.
