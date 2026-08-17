# Baseline Coexistence and Adaptive Delta

## Baseline remains complete and default

Baseline IIS remains independently complete. Adaptive installation must not alter the behavior of ordinary IIS requests.

```text
Baseline IIS
- current iis-workflow activation and routing
- current per-leaf approval/STOP behavior
- current canonical artifacts and validators

IIS Adaptive Planning
- explicit opt-in only
- same product-planning semantics and canonical artifacts
- exact process delta for delegated confirmations and planning re-entry
```

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

When and only when Adaptive is explicitly active, the user's adopted Mandate changes **how eligible planning confirmation and intra-planning continuation are satisfied**. It does not change the product authority being confirmed.

The delta is limited to:

1. **Standing delegated planning confirmation** — a Baseline leaf's ordinary repeated user confirmation/review may be satisfied by the active Mandate when the candidate is fully within delegated authority and the delegated-decision test passes.
2. **Intra-planning continuation** — an ordinary leaf STOP that exists to wait for the user to manually request the next IIS planning leaf becomes a return to the Adaptive router for the same current planning unit.
3. **Planning re-entry/reshaping** — fresh evidence may send the current unit back to an earlier existing IIS planning leaf without requiring a new user prompt when the Mandate already authorizes that decision.
4. **Verification-result triage** — a separate verifier result may be classified and fed back into the appropriate existing planning leaf as evidence.

Everything else remains current Baseline authority.

## Standing delegation is user authority, not inferred approval

The user explicitly selects Adaptive and adopts the Mandate. That act gives standing authority for a bounded class of later planning decisions.

Therefore a canonical `confirmed`, `approved`, or `ready` state reached through a valid Adaptive delegated confirmation still means the planning authority is complete and user-authorized for the active mode. The difference is provenance:

- direct per-artifact response: `USER_EXPLICIT`
- mandate-resolved confirmation: `DELEGATED_RECOMMENDATION`

Never report a delegated confirmation as though the user uttered a direct approval for that artifact.

Store provenance in the Adaptive companion trace. Do not add Adaptive-only metadata to canonical artifacts unless the current Baseline schema independently permits/owns that field.

## Hard Baseline boundaries that Adaptive does not soften

The following remain hard even in Adaptive mode:

- a status-only/current-state request is read-only and stops after reporting;
- adversarial planning consensus remains explicit-only and Adaptive never chooses/activates a Challenger;
- when adversarial consensus is active, its exact direct-user-only binding/Intent Anchor/final-approval requirements remain direct-user-only unless the current Baseline itself changes that contract;
- a missing project root, invalid canonical path, unresolved authority conflict, failed validator, or unavailable required evidence is not cured by delegation;
- the complete Ready Ticket Set is the terminal IIS Planning output for the current Increment;
- implementation and verification are outside IIS Planning;
- planning completion never authorizes deployment, credentials, production/external effects, or destructive operations.

## Current Baseline drift

At every Adaptive run, read the current Baseline instead of assuming this package's design notes are current.

If a future Baseline change makes the exact Adaptive Delta ambiguous or impossible without modifying product/artifact meaning:

```text
IIS ADAPTIVE PLANNING: CONTRACT DRIFT
Baseline change: <exact current rule>
Adaptive delta affected: <confirmation | continuation | reshaping | triage>
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
