# Adaptive Routing and Planning Re-entry

## Execution model

Adaptive is an alternate execution contract, not an edit to Baseline leaf files.

For each leaf:

1. read the current canonical Baseline leaf;
2. preserve all of its product semantics, evidence requirements, authority ownership, admission checks, canonical artifact rules, validators, and non-approval completion criteria;
3. apply the exact Adaptive confirmation/continuation delta below;
4. if an unlisted conflict appears, treat it as Baseline contract drift rather than inventing another override.

Do not run the Baseline leaf as an independent user-facing workflow and then try to ignore its approval prompt afterward. Perform the leaf under the already active Adaptive Mandate from the start.

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
- after canonical Scope/Increment closure validates, do not expose the ordinary manual-continuation STOP; return the exact selected `ready-for-matt` Increment to the Adaptive router and continue to Ask Matt in the same planning request;
- when a later leaf finds a construction-stage/foundation/split/merge/order defect, re-enter Scope Shaper directly if reshaping is delegated.

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
- after completion, continue to current To Spec rather than stopping for a manual leaf request.

Return to the user only for the unresolved material frontier that survives the Mandate.

Keep hard:

- authority conflict;
- a material decision outside delegation;
- active adversarial-consensus direct-user-only gates preserved by Baseline coexistence;
- any current leaf requirement that cannot be satisfied by evidence or valid authority.

### To Spec

Preserve:

- current Source Increment admission/revalidation;
- UI and Behavior authority gates;
- normative source lock;
- exact canonical path, metadata, headings, Verification Expectations schema, and mandatory contract audit;
- current product-contract completeness requirements.

Adaptive delta:

- draft the same canonical `SPEC.md`;
- when the content is a complete faithful projection and the ordinary approval gate is eligible for delegation, standing delegated confirmation satisfies the planning approval and the canonical Spec may transition to exact `Status: approved`;
- record the confirmation provenance in Adaptive trace, not the Spec schema;
- continue to current To Tickets without a manual user request.

If accurate Spec writing requires a new product requirement, boundary, Non-Goal, verification promise, or other material meaning, do not auto-approve it. Re-enter Ask Matt or Scope Shaper.

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

- when the proposed breakdown is a faithful projection and the delegated-decision test passes, standing delegated confirmation satisfies the ordinary user review requirement;
- canonical Tickets may transition from `draft` to `ready` only after every current readiness requirement is met;
- run the exact current per-Ticket and set validators;
- after a complete validated Ready Ticket Set exists, report current-Increment Adaptive Planning complete and hard STOP.

Do not use Adaptive to create preparatory Tickets, implementation sequences, or extra verification mechanisms.

## STOP semantics

Adaptive changes only **manual intra-planning continuation stops** for the same current planning unit.

Soft under active Adaptive Mandate:

- confirmed Scope -> manually request Ask Matt
- completed Ask Matt -> manually request To Spec
- approved Spec -> manually request To Tickets

Hard even in Adaptive:

- status-only inspection STOP;
- unresolved user decision STOP;
- special explicit-only gate STOP;
- invalid/missing authority or validator failure STOP until the exact defect is resolved;
- complete Ready Ticket Set STOP;
- boundary between IIS Planning and implementation/verification/delivery.

A later success re-entry after every current Ticket is actually `done` is a **new Adaptive planning cycle**, not a continuation through the Ready Ticket STOP. It is governed by the active Mandate's Continuation Authority and `08-delivery-continuation.md`.

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
| current canonical Spec/Ticket projection is complete and valid | normal forward route | continue / terminal |

## Re-entry discipline

Re-entry is not retrying the same answer until a validator passes.

Before repeating a leaf, identify the **new material fact or changed authority** that makes the second pass different.

If there is no new evidence/authority and the same unresolved user-owned branch remains, return to the user.

If a validator fails structurally, repair the structural projection without changing product meaning. If the only repair would change product meaning, return upstream.

## Delivery evidence returning to planning

Fresh implementation/runtime/verification evidence may trigger an Adaptive planning re-entry, but it remains evidence rather than product authority.

Examples:

- implementation demonstrates that an assumed existing product acceptance surface does not exist -> reconsider the planning contract/INC as applicable;
- verifier establishes that a Ticket flow is stronger than its exact parent outcome -> projection re-entry;
- current runtime shows the original INC is no longer the actual starting state -> Scope Shaper re-entry against the actual state.

Do not make planning history match an expected implementation. Re-plan from the actual current product state.
