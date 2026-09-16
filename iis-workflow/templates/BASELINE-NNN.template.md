# Transition Baseline `<BASELINE-NNN>`

Status: DRAFT | APPROVED
Project-Root: `<exact absolute project root>`
Baseline-ID: `<BASELINE-NNN>`
Revision: `<immutable revision or version>`
Applicability: `<project / transition scope and applicable authority>`

## Identity & Approval

Source Authority:
- Product meaning: `<exact saved Thesis source and fingerprint, or sufficient existing approved authority>`
- Investigation: `<exact applicable current-state evidence or None>`
- `<exact user instruction, applicable durable decision, Thesis/Scope original or other approved source>`

Approval:
- Approved by: `<authority owner>`
- Approved at / reference: `<date or exact approval record>`
- Approval scope: `<Goal, invariants, Blocks, and continuation ceiling covered by this approval>`
- Inter-Block auto-continuation authorized: `yes | no`

Applicability requires this exact original revision and current authority. Finding an old file does not authorize the transition. This is a conditional transition contract, not an operating mode, request form, cursor, status log or workflow store. Main prepares or revises it within existing delegated authority; choices outside that authority return to the approval owner above. Preserve bound revisions and obtain approval where the existing authority requires it, not through a new per-revision ceremony.

## Transformation Outcome

Goal:
- `<reference the original product outcome and state only this approved transformation scope; do not rewrite or weaken the Thesis>`

Required Named Items:
- `<required outcome or None required>`

Candidate Named Items:
- `<candidate means/outcome or None named>`

Completion Predicate:
- `<one observable predicate sufficient for the full Goal and every Required Named Item>`

Final Authoritative Readback:
- Surface / owner: `<actual product, canonical, operator, or external readback and responsible owner>`
- Source / method: `<exact source or approved observation path>`
- Claim limits: `<what the readback establishes and what remains unknown>`

## Global Invariants

- `<constraint that must hold for the whole transformation>`
- `<authority, safety, compatibility, truth, or ownership invariant>`

## Path Invariants

These constraints apply throughout the transition path, including Block boundaries and re-entry. Apply the relevant slice to the current measured Block and selected Scope; a different construction order must not silently weaken an invariant.

- `<path invariant>`
- `<path invariant>`

## Transition Blocks

Define transition milestones and measured predicates, not ready future Scopes or a queue of implementation tasks. Reuse a Block's ID, Entry, Exit, Invariants and Continuation when its Exit is the appropriate durable completion unit. Coarse Blocks may leave smaller current outcome selection to Main. Only where independent handoff or a prescribed construction order actually matters, name that internal boundary and its conditions here, reusing the Block's existing predicates and readbacks. State a selection priority only when choosing between eligible boundaries materially matters. Do not require an internal boundary catalog for every Block; even a fixed boundary still needs current evidence and a current Scope before methods.

### Block `<BLOCK-ID>` — `<Name>`

- **ID:** `<stable Block identifier>`
- **Name:** `<human-readable name>`
- **Meaning Contribution:** `<observable contribution toward the full Transformation Outcome>`
- **Order / Dependencies:** `<eligible predecessor, dependency, or transition-geography constraint>`
- **Entry:** `<measured entry predicate, required facts, and authoritative readback owner/source>`
- **Exit:** `<measured exit predicate and authoritative readback owner/source>`
- **Invariants:** `<Global/Path invariants applicable to this Block>`
- **Continuation:** `<conditions for the next eligible Block and facts to carry forward>`
- **Abort:** `<trigger, authorized safe target, owner/action boundary, and required readback>`
- **Insufficient for Exit:** `<evidence or state that must not be mistaken for Block Exit>`

<!-- Repeat the Block heading and fields for each coarse milestone. -->

## Safe Continuation

Safe Continuation Predicate:
- `<observable predicate proving this Block has reached a handoff-safe boundary>`

Required handoff facts and readbacks:
- `<measured Block Exit and safety evidence>`
- `<settled or safely contained active effects; no unknown non-idempotent effect>`
- `<remaining Goal / Required Named Items and preserved invariants>`
- `<next entry inspection and successor source identities>`

Successor authority:
- `<caller/host authority and approved continuation ceiling>`
- `<exact Baseline/Mandate/source inputs the successor must receive>`

Absence of an observed danger is not proof of Safe Continuation. If the predicate or any required readback is unknown, do not perform an automatic handoff.

## Safe Abort

Trigger:
- `<measured failure, unsafe condition, or unknown state that crosses the approved abort boundary>`

Authorized safe target state:
- `<project-specific safe state; do not promise rollback where unavailable>`

Owner and action boundary:
- `<authorized owner and exact action boundary; no new authority is implied>`

Authoritative readback:
- `<evidence proving the safe target state, or the remaining incomplete limit>`

## Atomic Boundary

`HARD_ATOMIC` keeps an indivisible cutover inside one Scope. Internal technical units are not independently completed product Scopes and do not permit handoff in the middle. Split only where a safe, durable, independently observable state exists.

## Placement and Use

Instantiate only for a transition that needs this contract, at the exact project-local approved path/revision. Omit irrelevant fields instead of filling None rows. Bind the original in the applicable Scope's Transition Authority section. It remains optional for ordinary IIS work and does not grant deployment, external-effect or successor-start authority beyond the current instruction and actual host capability.
