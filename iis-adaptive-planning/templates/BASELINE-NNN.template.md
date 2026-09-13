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
- `<exact user instruction, Mandate revision, Spec/Scope authority, or other approved source>`

Approval:
- Approved by: `<authority owner>`
- Approved at / reference: `<date or exact approval record>`
- Approval scope: `<Goal, invariants, Blocks, and continuation ceiling covered by this approval>`
- Inter-Block auto-continuation authorized: `yes | no`

Activation is explicit and opt-in. Supplying, discovering, or having an old Baseline file does not activate Transition Baseline mode. The caller must provide this exact Baseline identity/revision and an explicit approval/applicability decision for the current invocation. This artifact is a design authority map, not a Run Contract, cursor, status log, retry ledger, or workflow store.

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

These constraints apply throughout the transition path, including Block boundaries and re-entry. Carry only the applicable slice into the Active Block Envelope and each selected Increment; do not silently drop or weaken an invariant because construction order changes.

- `<path invariant>`
- `<path invariant>`

## Transition Blocks

Define only coarse transition milestones and their measured predicates. Do not pre-authorize future Work Packages, Increments, Tickets, or implementation tasks.

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

`HARD_ATOMIC` applies only to one selected Scope Increment. The indivisible cutover may contain internal execution units, but those units are not separate Increments and do not permit a Block handoff or `SAFE_INCOMPLETE_HANDOFF` in the middle of the cutover. If a smaller boundary cannot produce a safe, durable, independently readable state, keep the work inside the single Increment under the existing atomic exception.

## Placement and Use

Instantiate this template only at an exact caller-supplied path/revision, preferably beside the project's Adaptive planning provenance. Never select the latest matching file by discovery. The Baseline remains optional for ordinary Adaptive work and does not create durable Run Contract state or a controller/scheduler.
