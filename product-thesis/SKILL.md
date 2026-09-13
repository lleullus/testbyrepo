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

### Core Behavior Concretization

Make the Core Utility and Core Completion Loop concrete enough to explain which user input or situation requires the system to judge, transform, or preserve what; what result the user must obtain or observe; and why omitting that behavior would make the requested outcome impossible or false. Identify plausible-looking results that would still fail that behavior. Use the relevant current product evidence and existing question path, not a separate investigation stage or a fixed-count checklist.

For example, when the promise is to make a comic from a revised story, saving the conversation is insufficient if the next plan still uses the original story. Identify the required link between the current confirmed revision, the plan the user approves, and the generation input. Whether a story revision must also recompose existing panels is a product decision, not an automatic inference. Input fidelity alone does not establish fidelity of the generated pictures.

Distinguish explicit requirements, behavior necessarily derived from the promised outcome, and unresolved user-owned choices. Explain the causal necessity of derived behavior; current implementation, common practice, or agent preference alone cannot make it required. Do not record an inference as explicit user approval. Apply existing authority and delegation before asking for a material unresolved product choice. Concretize core behavior and success meaning here; leave detailed states, interaction policy, UI, and implementation methods to their existing downstream owners.

### Core Clarification

When core meaning remains unclear, use a provisional Core Utility and Core Completion Loop to clarify it with the user. This is a conversation method within existing conditional Thesis admission, not a separate phase, questionnaire, artifact, or approval gate. Reuse sufficient current meaning; do not require dialogue for an already clear request.

Before asking, identify how different answers would materially change the user result or the input-to-outcome loop. Apply current instructions, adopted authority, delegation, and directly inspectable facts first. In greenfield work, use the brief, fixed constraints, and concrete use situations without inventing implementation facts; inspect external facts only when they materially affect the meaning. Leave detailed UI, recovery policy, and implementation choices downstream unless their product-level meaning changes the core result or loop. This focus does not restrict questions needed to resolve other Thesis obligations under the existing `USER_INPUT_REQUIRED` rule.

Briefly show the current understanding in ordinary language, labeling assumptions as provisional. Explain the specific alternative behaviors and their consequences rather than asking for generally more detailed requirements. Offer a recommendation when the user's goal and constraints support it; otherwise ask without inventing a preference. Allow an open answer when fixed choices would misrepresent the decision. Never recommend a weaker overall product goal merely because it is easier to implement or makes the first Increment smaller; product meaning and construction order are different decisions.

After an answer, briefly reflect the changed Core Utility or Core Completion Loop and update directly affected core behaviors, causal relationships, and success observations. Preserve the distinction between user decisions and derived meaning. Revisit only conclusions materially affected by the answer, inspect newly relevant facts as needed, and honor a user stop or scope change. Do not restart the whole Thesis, repeat settled questions, or select the next Scope here.

Ask only still-unresolved or newly revealed core choices needed for the current understanding. Independent choices may be asked together when easy to answer; sequence choices whose meaning or necessity depends on an earlier answer. Require neither a complete upfront question list nor a separate dependency graph, and set no question or round quota. Do not assume an unresolved answer to finish: use `USER_INPUT_REQUIRED` and resume the relevant analysis when the user replies. Do not present a completed Thesis followed only by a generic request for feedback while core meaning remains open.

For example, “make and revise a comic through conversation” may mean revising the story before generation or editing selected generated panels while preserving the others. Ask about that product difference, not button placement or model choice. If the user chooses selective panel editing, preserve that loop rather than substituting full regeneration for implementation convenience. If the request already explicitly defines the result and revision boundary, do not ask it again.

End this focused dialogue when the user result and core flow are concrete and no material user-owned choice about them remains. This is not yet `CALIBRATED`: complete the truth/causal, named-item, success-observation and counterexample checks. Preserve the actual core behaviors and causal explanations in the source document below, not just feature names. Unknown feasibility remains unknown. There is no additional clarification approval gate.

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

Persist the actual Thesis conclusion before subsequent investigation, Run Contract closure and Scope/Matt consumption. Thesis-source writing is authorized on entry to this phase, including before model selection and `/승인게이트` release; do not ask for separate storage permission or defer storage behind those conditions. This permission covers the Thesis source only, not Scope/Spec mutation, implementation or external effects. Save unresolved meaning honestly and retain `USER_INPUT_REQUIRED`; persistence is neither calibration nor product approval nor permission to continue.

Use [PRODUCT-THESIS.template.md](templates/PRODUCT-THESIS.template.md) as a content guide, in the user's language. Preserve Reason to Exist, concrete core behaviors and why they are necessary, plausible false successes, source authority/provenance, required/candidate/supporting/deferred meaning and unresolved decisions. Do not compress the conclusion into a five-value projection or copy private reasoning/transcripts. The existing five values can express causal meaning; source recoverability, not field count, is the reason for this change.

Use an exact canonical file under `<Project-Root>/docs/planning/product-thesis/<meaning-slug>/THESIS-NNN.md`, choosing the next unused ordinal. Preserve referenced revisions unchanged; changed meaning gets a new file, never an overwritten historical source. Reuse a sufficient existing recoverable source instead of recreating it. For unrooted greenfield use one exact `/tmp/iis-product-thesis-<unique>/THESIS-NNN.md` location and report it; this is not a Project Root and does not authorize Scope/Matt artifact writes. Before durable downstream binding, preserve the same bytes at a durable project source location and bind that exact path. Do not delete a source still referenced by an artifact.

New Scope results and direct Matt Specs use this source reference rather than copying the five values:

```text
## Product Meaning Binding

Schema: iis-product-meaning/v2
Source: /absolute/canonical/path/THESIS-NNN.md
Fingerprint: sha256:<64 lowercase hex>
```

The fingerprint is SHA-256 of the full source UTF-8 bytes. Compute it with `python3 tools/product_meaning_binding.py fingerprint <binding-artifact>` and validate with `validate <binding-artifact>`. A source must remain readable and match its fingerprint. The immutable Scope revision preserves the same reference; Increment remains the existing reference hop, and Scope-shaped Spec preserves that exact binding. Direct Matt has no invented Scope hop. Do not copy Thesis or its binding into Tickets.

Existing v1 bindings and sufficient legacy approved meaning remain usable without bulk migration or recalibration. A new direct artifact uses v2 when a source is available; faithful continuation of an existing v1 Scope keeps its exact binding and original authority. Broken v2 references must fail, never fall back to remembered or legacy meaning.

The planning owner reads the actual source and applies its behavior/causal meaning to the current contract. Source hashing and exact Scope lineage establish recoverability and accidental-drift detection, not semantic fidelity or current user approval. Read the historical source actually bound to the artifact; if newer authority changes applicable meaning, expose and resolve the difference rather than silently substituting a latest file. The full source never expands the authorized current Increment. After `CALIBRATED`, continue normal next-increment admission; no new reviewer, registry or approval ceremony is added.


## Result

Report the smallest sufficient result:

```text
PRODUCT THESIS

Source: <exact saved Thesis path>

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

Use `USER_INPUT_REQUIRED` only for a material user-owned product meaning still split after available authority and evidence. Save the conclusion and exact unresolved choice, ask for that choice, and stop before downstream planning mutation. Do not delay Thesis storage or ask about inspectable facts and replaceable implementation details.
