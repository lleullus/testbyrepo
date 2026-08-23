# Baseline Coexistence and Adaptive Delta

## Baseline remains complete and default

Baseline IIS remains independently complete. Adaptive installation must not alter the behavior of ordinary IIS requests.

```text
Baseline IIS
- current iis-workflow activation and routing
- current per-leaf self-review/approval/STOP behavior
- current canonical artifacts and validators

IIS Adaptive Planning
- explicit opt-in only
- same product-planning semantics and canonical artifacts
- invocation-local Run Contract closure
- exact process delta for delegated confirmations and planning re-entry
```

There is no separate Adaptive Run skill. Outer Main is the main agent for the current explicit Adaptive invocation; it carries the Run Contract and routes exact owner results without taking over Baseline planning, implementation, heuristic-exploration, or verification authority.

Do not edit `iis-workflow`, Scope Shaper, Ask Matt, To Spec, To Tickets, Behavior/UI authority skills, their templates, or validators merely to make Adaptive work.

## What remains authoritative from Baseline

Always preserve the current Baseline definitions for:

- what belongs to Scope Shaper, Ask Matt, Behavior Design, UI planning, To Spec, and To Tickets;
- next-Increment admission;
- product authority and evidence hierarchy;
- current product-state inspection requirements;
- canonical artifact paths, metadata, headings, status vocabulary, and lineage;
- Spec/Ticket projection semantics;
- verification expectations and Ready Ticket flow structure;
- structural validators and semantic review obligations;
- the terminal product of IIS Planning: one approved Spec plus its validated complete Ready Ticket Set;
- the boundary that implementation and verification are separate delivery lifecycles.

Repository/runtime facts remain evidence unless the current Baseline already treats the fact as an unavoidable external or deliberately preserved product boundary.

## Exact Adaptive Delta

When and only when Adaptive is explicitly active, the user's adopted Mandate and closed invocation-local Run Contract change **how eligible planning confirmation, intra-planning continuation, and outer whole-run completion are satisfied**. They do not change the product authority being confirmed.

The delta is limited to:

1. **Run Contract closure and terminal discipline** — before the first planning mutation, normalize current authority into one compact invocation-local contract that separates Required Named Items from Candidate Named Items, fixes the Required Item Policy, records Implementation and Verification independently, and closes the Run Completion Boundary, Completion Predicate, Authoritative Readback, and Run Contract Approval Gate. Ask only for a material unresolved field. The gate defaults to `not_required`; only an affirmative `/승인게이트` modifier on the current explicitly active Adaptive invocation sets it to `required`, renders the exact `CLOSED` contract, and STOPs before the first mutation until direct user approval. The modifier is Run Contract-only: it neither activates Adaptive nor adds Scope, Ask Matt, Spec, Ticket, implementation, or verification approval gates. A Baseline leaf STOP or Ready Ticket terminal remains exactly what Baseline says; it becomes whole-run completion only when the outer Run Contract predicate is satisfied.
2. **Standing delegated planning confirmation** — a Baseline leaf's ordinary user-owned planning decision may be satisfied by the active Mandate when the candidate is fully within delegated authority and the delegated-decision test passes. Baseline To Spec/To Tickets self-review adoption is not reclassified as delegated confirmation merely because Adaptive is active.
3. **Pre-consensus delegated Intent Anchor finalization** — when adversarial consensus was explicitly activated and the user designated the exact Challenger, Ask Matt may satisfy the Baseline Intent Anchor confirmation through standing delegation when current user authority, the adopted Mandate, closed Run Contract, applicable canonical authority, and direct facts determine one faithful current Anchor, the delegated-decision test passes, and no Return-to-User Boundary, authority conflict, separately required disclosure expansion, or explicit current request for direct Anchor review exists. Correct any determinable omission or mismatch from current authority before finalization; if a material interpretation remains unresolved, return only that decision. A valid delegated Anchor is finalized as `DELEGATED_RECOMMENDATION` and the exact designated Challenger may be invoked without a user round-trip. This changes only how the Intent Anchor confirmation is satisfied in explicit Adaptive mode; ordinary Baseline adversarial consensus still requires direct user confirmation.
4. **Post-consensus delegated finalization** — when adversarial consensus was explicitly activated with an exact user-designated Challenger and a current finalized Intent Anchor whose provenance is `USER_EXPLICIT` or `DELEGATED_RECOMMENDATION`, Ask Matt may satisfy the Baseline post-consensus final integrated approval through standing delegation only after current `ADVERSARIAL CONSENSUS REACHED`, an authority-delta result of `NONE`, a still-passing delegated-decision test, no Return-to-User Boundary or authority conflict, and no material candidate change after the Challenger's final review. This changes only how that finalization approval is satisfied in explicit Adaptive mode; it does not make Challenger consensus itself product authority or change ordinary Baseline finalization.
5. **Intra-planning continuation** — an ordinary leaf STOP that exists to wait for the user to manually request the next IIS planning leaf becomes a return to the Adaptive router for the same current planning unit.
6. **Planning re-entry/reshaping** — fresh evidence may send the current unit back to an earlier existing IIS planning leaf without requiring a new user prompt when the Mandate already authorizes that decision. Required Named Items and the active Completion Predicate remain preserved across that reshape; Candidate Named Items remain mutable under current authority.
7. **Verification-result triage** — a separate verifier result may be classified and fed back into the appropriate existing planning leaf as evidence.

Everything else remains current Baseline authority.

The Run Contract is not a Baseline artifact, new product-authority layer, or durable workflow state. It constrains the outer Adaptive invocation: which user-named items remain obligations, which remain candidate means, which delivery stages are authorized, and which observable condition permits whole-run success. It never causes one current Spec or Ticket to absorb multi-Increment scope.

The Ready Ticket Set remains the terminal **IIS Planning** product. Under explicit Adaptive activation, that ownership STOP returns the Set and closed Run Contract to Outer Main, which applies the independently closed Implementation and Verification fields. When Verification is enabled, the current delivery contract requires heuristic probing before final verification; this does not create a third Run Contract field or extend IIS Planning authority into delivery, and the owner STOP is not an invocation STOP.

A broader `NAMED_REQUIRED_ITEMS_DELIVERED`, `BOUNDED_OUTCOME_SATISFIED`, or `MANDATE_OUTCOME_SATISFIED` Run Completion Boundary also does not turn one IIS planning cycle into a multi-Increment workflow. After a current Increment is fully delivered, Adaptive performs a fresh success re-entry; only when the active predicate is still unsatisfied and the Mandate ceiling permits it does it start a new planning cycle and return to Scope Shaper for one new current Increment from actual state.

`CURRENT_INCREMENT_IMPLEMENTED` is an implementation-only outer terminal. It does not mark Tickets `done`, claim independent verification, or authorize success re-entry into another Increment.

## Standing delegation is user authority, not inferred approval

The user explicitly selects Adaptive and adopts the Mandate. That act gives standing authority for a bounded class of later planning decisions.

When a canonical planning state is actually reached through a valid Adaptive delegated decision, preserve that distinct provenance:

- direct user-owned decision: `USER_EXPLICIT`
- mandate-resolved decision: `DELEGATED_RECOMMENDATION`

Never report a delegated decision as though the user uttered a direct approval for that artifact. Baseline To Spec/To Tickets self-review adoption remains `STRUCTURAL_PROJECTION`/Baseline behavior and does not create a delegated-confirmation trace merely because Adaptive is active.

Store Adaptive decision provenance in the companion trace. Do not add Adaptive-only metadata to canonical artifacts unless the current Baseline schema independently permits/owns that field.

A fully derived `CLOSED` Run Contract is likewise not a user approval event. It is a normalization of current authority. It proceeds without another approval prompt when `Run Contract Approval Gate: not_required`; when the exact invocation-local gate is `required`, only direct user approval of the rendered current Run Contract releases mutation. That release does not become approval of any downstream leaf or delivery stage. Ask only when a material field is genuinely unresolved.

## Hard Baseline boundaries that Adaptive does not soften

The following remain hard even in Adaptive mode:

- a status-only/current-state request is read-only and stops after reporting;
- adversarial planning consensus remains explicit-only and Adaptive never chooses/activates a Challenger;
- adversarial planning consensus activation and exact Challenger binding remain direct-user-only; ordinary Baseline Intent Anchor confirmation remains direct-user-only, while explicit Adaptive mode may satisfy only that Anchor confirmation through the exact faithful-Anchor standing-delegation rule above; ordinary Baseline post-consensus final approval also remains direct-user-owned by default, while explicit Adaptive mode may satisfy only that finalization event through the exact no-authority-delta standing-delegation rule above;
- a missing project root, invalid canonical path, unresolved authority conflict, failed validator, or unavailable required evidence is not cured by delegation;
- the complete Ready Ticket Set is the terminal IIS Planning output for the current Increment;
- implementation, heuristic probing, and verification are outside IIS Planning;
- planning completion never authorizes deployment, credentials, production/external effects, or destructive operations;
- a Run Contract cannot weaken or bypass any of these boundaries;
- an unsatisfied Run Contract cannot be reported as successful merely because an owning leaf stopped.

## Current Baseline drift

At every Adaptive run, read the current Baseline instead of assuming this package's design notes are current.

If a future Baseline change makes the exact Adaptive Delta ambiguous or impossible without modifying product/artifact meaning:

```text
IIS ADAPTIVE PLANNING: CONTRACT DRIFT
Baseline change: <exact current rule>
Adaptive delta affected: <run closure | confirmation | continuation | reshaping | triage>
Why it cannot be applied without changing IIS meaning: <reason>
STOP
```

Do not silently rewrite Baseline semantics to preserve Adaptive convenience.

## Installation non-interference

The canonical Adaptive source and live install must be side-by-side additions only:

```text
/home/user01/project/iis-skills/iis-adaptive-planning/
/home/user01/.codex/skills/iis-adaptive-planning/
```

Synchronizing or removing Adaptive must never write inside another skill directory or existing project `docs/planning/**` tree.
