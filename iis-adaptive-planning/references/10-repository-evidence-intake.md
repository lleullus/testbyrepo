# Repository Investigation Evidence Intake

## Purpose

For a new product-meaning request, use the saved Thesis as the meaning input to subsequent investigation; sufficient pre-existing evidence may be reused. Keep confirmed facts, unresolved premises and contradictions separate from product authority. A core-meaning contradiction returns to the Thesis owner; implementation uncertainty alone does not lower the goal. This intake adds no investigation stage or storage approval. After intake, Outer Main reads the Thesis and evidence together and reconciles an explicitly applicable Baseline, if any, before Run closure.

Allow one exact independently produced `repository-investigation` artifact to improve an explicit Adaptive invocation without turning that artifact, its author, or its planning-relevance hints into IIS product authority.

This is an optional evidence intake path. Adaptive behavior is unchanged when no exact investigation artifact is supplied by the current user/caller context.

## Admission

Apply this intake only when the current invocation identifies one exact repository-investigation artifact path. Do not search `docs/investigation/**` for a newest, likely, matching, or convenient artifact and do not infer that an old investigation should apply merely because it exists.

Before using the artifact:

1. resolve the current installed/discovered `repository-investigation` companion skill as the evidence-contract owner;
2. resolve its adjacent `tools/validate_investigation.py` and require exact `VALID` for the supplied artifact;
3. require the artifact's exact `Project-Root` to match the current Adaptive Project Root;
4. require its `Repository-Root` to be the same current repository root or an exact current containing Git root for that Project Root;
5. read the compact `## Evidence Handoff` first; and
6. inspect detailed findings/anchors only as needed to re-establish decision-critical current facts.

A structurally invalid artifact, wrong-root artifact, or inaccessible exact path is not usable evidence for the current target. Report the exact intake defect; do not substitute another investigation artifact.

## Evidence-only authority boundary

The artifact records repository evidence only. It does not authorize or decide:

- Desired Product Outcome or Decision Priorities;
- Required Named Items, Candidate Named Items, or Required Item Policy;
- Run Completion Boundary or Completion Predicate;
- Planning Boundary, Work Package split/merge, or Selected Increment;
- Planning Constraints or product-capability dependencies merely because the handoff labels them as candidates;
- Behavior/UI decisions;
- Spec/Ticket product meaning;
- implementation design; or
- verification verdicts.

Treat these handoff labels only as navigation candidates:

```text
CURRENT_STATE
PLANNING_CONSTRAINT_CANDIDATE
PRODUCT_DEPENDENCY_CANDIDATE
ACCEPTANCE_SURFACE_CANDIDATE
DELIVERY_CONTEXT
NONE
```

The current Scope Shaper, Ask Matt, Run Contract owner, or later delivery owner retains its existing decision test and authority.

## Currentness assessment

The investigation artifact is historical evidence about one observed repository state. Do not declare the whole artifact stale merely because Git HEAD changed after the investigation. Re-establish currentness at the load-bearing evidence boundary.

Classify the intake invocation-locally as exactly one of:

- `CURRENT` — every load-bearing fact used by this Adaptive invocation remains attributable/current enough for the intended decision.
- `PARTIALLY_STALE` — some findings/anchors changed or cannot be re-established, while other exact findings remain current and independently usable.
- `STALE` — the investigation answer or all decision-critical load-bearing evidence can no longer be attributed to the current repository state.

Do not write this classification back into the immutable investigation artifact.

Apply freshness sensitivity as follows:

### `ANCHOR_LOCAL`

Reopen the specific load-bearing file/symbol/config anchor. If its recorded identity and material content remain applicable, the fact may remain current even when unrelated repository files changed. If it materially changed, re-establish only the affected fact before using it.

### `SEARCH_UNIVERSE`

An absence, bypass, or alternate-path claim remains current only when the bounded search universe is still appropriate and relevant registrations/entrypoints/exports/config surfaces have not materially changed without reinspection. Do not carry a narrow old search into a broader current absence claim.

### `RUNTIME_STATE`

When the current claim depends on mutable runtime/canonical state, obtain fresh current readback. The prior artifact is navigation, not current state proof.

### `EXTERNAL_VERSION`

Confirm the relevant external/document version or current retrieval when the external fact is load-bearing. A retrieval-date record is not permanent authority.

## Use in Run Contract closure

The Run Contract may use re-established current facts from the investigation as `inspectable current facts`. The investigation artifact itself is not a new Source Authority and must not become the Run Contract's product `Authoritative Readback` merely because it summarizes one.

Correct pattern:

```text
Investigation handoff identifies CLI `status` output as the authoritative current readback.
Adaptive rechecks the current CLI/readback surface and may use that fresh fact when closing the Run Contract.
```

Incorrect pattern:

```text
Authoritative Readback: INV-001.md says the capability exists.
```

If a Run Contract field remains user-owned after current evidence is re-established, return to the user under the existing Run Contract/Mandate rules. Evidence does not expand delegation.

## Use in Scope Shaping

A current `COMPLETE` investigation may supply bounded navigation evidence for:

- Current Product State candidates;
- existing observable capabilities and readback surfaces;
- potential external/public/persisted boundaries to test as Planning Constraints;
- potential product-capability dependencies to test under Scope Shaper's product-level counterfactual rules;
- connected Delivery Context; and
- exact material unknowns already shown to be absent within the investigation boundary.

Scope Shaper still performs its own authority classification and directly reopens every investigation anchor that is load-bearing for the selected Planning Boundary, Planning Constraint, product-capability dependency, construction candidate, or Increment selection.

Do not repeat a broad repository investigation solely for confidence when a current COMPLETE artifact already closes the same material evidence questions and the load-bearing anchors revalidate. Investigate only a new material question, changed/stale evidence, or a Scope-owned counterexample that the prior artifact did not cover.

A `PARTIAL` investigation may contribute current individual facts, but its unresolved decision-critical unknowns remain explicit. It cannot be treated as a complete Current Product State baseline when those unknowns can change the shaping decision.

A `BLOCKED` investigation supplies no completeness claim. Use only separately re-established facts that remain directly attributable; otherwise obtain the missing evidence through the current owning leaf.

## Use in Ask Matt and later planning

When the artifact identifies an actual current acceptance/readback surface or a concrete current behavior fact, Ask Matt may use the re-established fact as repository evidence during its existing first-hand investigation and verification-feasibility closure.

Do not let the artifact strengthen a product promise, turn a current implementation into required future design, or bypass Behavior/UI/product decisions. To Spec and To Tickets continue to project only approved planning authority.

Carry the exact evidence navigation through direct Ask Matt work even when no Source-Increment exists. The direct-Matt absence of Scope lineage is not evidence loss and does not justify a duplicate broad investigation. To Spec/To Tickets may pass this evidence as non-normative context, without adding schema fields or authority.

For execution preparation, hand the exact artifact and re-established load-bearing facts to ready-ticket-plan. Planner independently tests method-relevant anchors/search universe/runtime premises, reusing current evidence instead of repeating the entire investigation. Current ADMIT does not prove future source/runtime currentness; the implementation worker checks important premises before dependent work. Material method changes return to affected preparation, product changes to original planning authority. Final verifier uses its own fresh acceptance/readback evidence; an investigation or reviewed plan is navigation, not PASS.

## Artifact immutability and lineage

Adaptive never edits, supersedes, or annotates a repository-investigation artifact. A new independent investigation creates the next `INV-NNN.md` under its investigation slug.

Do not copy routine investigation findings into `ADAPTIVE-PLANNING-TRACE.md`. Record only an existing material Adaptive decision/route event when the current Adaptive trace contract already requires it; an investigation artifact's existence is not itself an Adaptive provenance event.

Do not create:

- `LATEST.md` or a mutable investigation pointer;
- an evidence database or cache;
- an investigation ID field in canonical IIS artifacts;
- a new Run Contract field for investigation status;
- a mandatory Baseline IIS investigation gate; or
- automatic investigation invocation from Adaptive.

## Compact intake report

When an exact artifact is supplied and materially used, keep the caller-facing intake summary compact:

```text
REPOSITORY EVIDENCE INTAKE
Artifact: <exact path>
Artifact Status: complete | partial | blocked
Currentness: CURRENT | PARTIALLY_STALE | STALE
Re-established load-bearing facts: <summary>
Stale/unresolved evidence: None | <summary>
Authority: EVIDENCE ONLY
```

Continue under the existing Adaptive Run Contract and Baseline leaf contracts. This intake does not create another approval or lifecycle stage.
