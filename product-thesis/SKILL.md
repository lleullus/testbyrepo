---
name: product-thesis
description: Use as the conditional product-meaning phase before IIS next-increment admission when a request newly establishes or materially revises why a product capability should exist, its core utility, completion loop, or truth boundary.
---

# Product Thesis Design

Write the result in the user's conversation language.

## Purpose

Establish the product meaning that later IIS planning must preserve. Identify why the product work matters, the durable utility it promises, the complete causal loop needed to deliver that utility, and the claims that must remain truthful. Prevent a feature list, polished surface, surrogate state, or implementation mechanism from substituting for an actual product result.

The current planning owner directly performs this phase in the current conversation context. It has no separate agent, controller, queue, database, persistent state machine, retry ledger, or approval ceremony.

## Conditional Admission

Apply explicit planning-leaf and read-only classifications before broader inference.

Perform Product Thesis Design when the current request newly establishes or materially revises product meaning, including:

- a new product, new feature family, or broad product direction;
- a requested feature bundle whose durable utility is not already established by current authority;
- a material redesign of an existing user or operator flow; or
- fresh actual evidence that invalidates an applicable approved product meaning and requires product-level reconsideration.

Do not perform or reopen this phase for:

- a status-only or planning-state inspection;
- faithful To Spec or To Tickets projection of current approved authority;
- exact existing Ready Ticket planning, implementation, or verification;
- repository snapshot or other non-product planning utility; or
- a request whose applicable current approved product meaning remains sufficient and unchanged.

A projection leaf that discovers a material product-meaning defect returns to its existing product-planning owner. It does not invent a thesis locally.

Use an existing Product Thesis conclusion when it is current, applicable, and recoverable from current conversation authority or the existing confirmed Scope/Matt authority. Do not rerun the phase merely because a new session or later leaf begins.

## Authority Order

Preserve this order:

```text
Current explicit user instruction and constraints
-> applicable approved authority
-> Product Thesis derived meaning
-> Scope / Matt / Spec / Ticket projection
```

Product Thesis is a planning conclusion derived from authority, not a new source of authority. It never demotes an explicit user-required outcome or means, widens an explicit stage or stop boundary, reopens settled product policy without evidence, or promotes a technical mechanism into a product requirement.

## Required Analysis

Use current user authority, applicable approved planning authority, and inspectable current product evidence. Resolve inspectable facts directly. Ask only when materially different user-owned meanings remain after those sources are exhausted.

### Reason to Exist

State the concrete shortfall in the current product, alternative, or workflow that makes this work matter. A competitive market claim is unnecessary. Do not invent differentiation, market strategy, or adjacent product scope.

### Core Utility

State the durable result the user or operator obtains. It must be an observable value, not a list of features, screens, technologies, or activities.

### Core Completion Loop

Trace the promised utility from intent to actionable outcome:

```text
Intent input
-> persistence or accountable ownership when applicable
-> system work
-> domain judgment when applicable
-> observable result
-> user or operator outcome
```

Adapt the loop to the actual product. Do not force background automation, persistence, a domain decision, or a fixed UI structure where the utility does not need it.

### Truth / Causal Invariants

State only the high-level relationships that must be true for the core utility claim to be honest and correctly attributable. Unknown remains unknown. Surrogate, mock, cached, local, refreshed, cross-identity, or agent-reported state cannot stand for a real product result unless current authority explicitly defines that exact state as the result.

This phase defines claim boundaries, not detailed states, transitions, recovery, concurrency, test flows, or a verification verdict.

### Required, Candidate, And Non-Core Meaning

Classify relevant named items as:

- required outcome;
- required means;
- candidate or replaceable means;
- supporting means; or
- proposed removal or deferral.

Preserve every explicit user-required item. Treat subtraction as a consequence of preserving utility with less unrelated surface, never as a target feature count or permission to remove required scope.

### Success Observation

State the future observable condition that would establish the promised utility. This is the product claim boundary, not a test implementation, command, mock, internal helper, or acceptance-flow design.

## Counterexample Gates

The thesis is not calibrated if any answer below is yes:

1. Could every requested feature and screen exist while the durable utility is absent?
2. Could the Core Utility sentence be true on paper while the intent-to-outcome loop is materially broken?
3. Could the product display the claimed result while its identity, cause, persistence, execution, or authoritative readback is false?

When an item contributes to neither Core Utility nor an explicit required constraint, classify it as a candidate for deferral, replacement, or removal rather than assuming that feature presence is valuable.

## Ownership Boundaries

Product Thesis owns the high-level Reason to Exist, Core Utility, completion loop, truth/causal invariants, named-item meaning, non-core candidates, and success claim boundary.

It does not:

- select the next construction Increment, split/merge Work Packages, or decide product-capability order; Scope Shaper owns those decisions;
- define detailed product policy, semantic states/transitions/recovery/order/concurrency, rendered UI, or final completion contracts; Ask Matt and Behavior/UI authorities own them;
- choose files, modules, data structures, APIs, schedulers, architecture, or implementation sequence;
- design exact verification flows, capture evidence, adjudicate Tickets, or progress delivery; or
- make the whole Core Completion Loop current Increment scope. A selected Increment may establish one durable state that materially advances the loop.

If fresh evidence invalidates the Reason to Exist, Core Utility, or an essential identity/ownership premise, return to the product-meaning owner. Ordinary implementation detail, Ticket progress, or leaf-local correction does not trigger recalibration.

## Downstream Preservation

After `CALIBRATED`, run normal next-increment admission. Product Thesis never selects Scope Shaper versus Ask Matt by itself.

Record only the must-preserve product-level subset as one compact `Product Meaning Binding` in the next durable planning artifact. The binding contains exactly: Core Utility, Core Completion Loop, explicitly required Outcomes / Means, Truth / Causal Invariants, and Success Observation. Candidate / Supporting Means, Non-Core / Defer Candidates, detailed Behavior/UI policy, current Increment projection, Ticket decomposition, and implementation method are excluded. Do not add a separate required Product Thesis artifact, revision ledger, registry, conversation ledger, stable obligation ID, or reviewer lifecycle.

For a Scope path, write the binding once in `SCOPE-SHAPING-RESULT.md`; the normal byte-for-byte immutable `revisions/SHAPE-NNN.md` snapshot preserves the same binding. Do not copy the binding into `INC-NNN.md` or Tickets. For a direct Ask Matt path, `SPEC.md` is the first durable artifact and carries the binding once.

Use schema `iis-product-meaning/v1`. After writing the five binding values, run `python3 tools/product_meaning_binding.py fingerprint <artifact>` to calculate the deterministic SHA-256 value, write that exact value to `Fingerprint:`, then run `python3 tools/product_meaning_binding.py validate <artifact>` before a durable artifact is treated as valid. The fingerprint is only equality/accidental-drift evidence; it is not authentication, signing, tamper-proofing, or proof of semantic correctness.

The mechanical guarantee is deliberately narrow: once the planning owner records a binding, downstream validation can detect serialization/copy drift across the existing Scope -> Increment -> immutable Scope revision -> Spec chain. Product Thesis -> first binding semantic fidelity and binding -> actual Scope/Spec contract semantic fidelity remain responsibilities of the existing planning owner, faithful projection, and Mandatory contract audit. Do not add a mandatory LLM semantic reviewer for those responsibilities.

The binding is product-level meaning, not current delivery scope. A downstream owner may narrow delivery to its authorized current Increment but may not contradict or truncate the product-level binding merely because the Increment delivers only part of the loop. Conversely, the full binding never expands the current Increment or Spec obligation. New explicit user authority takes precedence.

## Result

Report the smallest sufficient result:

```text
PRODUCT THESIS

Reason to Exist:
<current shortfall and why the work matters>

Core Utility:
<durable user or operator result>

Core Completion Loop:
<intent -> system responsibility -> domain judgment -> observable result -> user outcome>

Truth / Causal Invariants:
- <claim that must remain truthful and correctly attributable>

Required Outcomes / Means:
- <explicitly required item, or None>

Candidate / Supporting Means:
- <replaceable or supporting means, or None>

Non-Core / Defer Candidates:
- <item unrelated to utility and required constraints, or None>

Success Observation:
<actual observation that establishes the product result>

Open Product Meaning:
None | <smallest unresolved user-owned decision>

Result:
CALIBRATED | USER_INPUT_REQUIRED
```

Use `CALIBRATED` only when the counterexample gates close and no material product meaning remains unresolved. Continue directly to next-increment admission without a separate approval prompt when current authority fully determines the result.

Use `USER_INPUT_REQUIRED` only when the available authority and inspectable evidence leave one material user-owned product meaning genuinely split. Ask only for that smallest decision and stop before planning mutation. Do not use missing implementation detail, preference among replaceable means, or an inspectable fact as a reason to ask.
