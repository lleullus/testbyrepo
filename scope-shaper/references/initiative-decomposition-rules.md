# Outcome And Construction Decomposition Rules

Use these rules when Scope Shaper must distinguish independently acceptable outcome areas and choose the next durable construction Increment. Outcome decomposition and construction sequencing are separate decisions.

## Two Axes

### Horizontal: Work Packages

A Work Package is an independently plannable and acceptable product outcome area. Create the largest Work Package that remains independently acceptable. It is a durable Scope record, not an Ask Matt handoff and not a construction step.

### Vertical: Construction Increments

A construction Increment is one durable transition from the actual current product state to the next observable product state. Select exactly one ready Increment per confirmed Scope result. Future stages remain provisional until later re-entry against the delivered state.

Do not use Work Packages as a substitute for construction sequencing, and do not split Increments by technical layers.

## Work Package Relationship Decision

Test only candidate relationships that can change a package boundary. Record:

```text
Candidate Relationship:
Decision: MERGE | SPLIT
Independent Acceptance Test:
Counterexample Tested:
Lead Finding:
Supporting Material Claims:
```

Material claim numbers are local references inside the same Scope result.

### Split Test

Choose `SPLIT` when verified evidence establishes an independent product boundary, such as:

- either result remains meaningful when the other is accepted, deferred, or rejected;
- the results complete different user or operator jobs;
- they own different product lifecycles, authorities, failure policies, or deliberate rollout boundaries;
- one is an optional expansion rather than part of the other's core acceptance; or
- one Matt planning unit would otherwise settle unrelated product decisions.

State what remains independently usable and test the strongest reasonable merge interpretation.

### Merge Test

Choose `MERGE` when:

- neither candidate produces a meaningful accepted result alone;
- one is preparation, migration, source recovery, build enablement, refactor, or another delivery condition for the other's outcome;
- they share one acceptance moment and separation creates a package whose result is only “ready for later work”;
- the apparent boundary disappears when implementation details are removed; or
- Matt would immediately need to settle the same product decisions for both.

### Work Package Statement

Prefer:

```text
<actor> can <complete a meaningful job or operate a meaningful lifecycle>
```

Product acceptance defines package identity. Technical layers, repository modules, schemas, interfaces, tests, and anticipated sequence describe delivery rather than independent acceptance.

## Product Dependency

Add `WP-B depends on WP-A` only when A has an observable product result and B cannot be delivered or coherently accepted without that result under any reasonable internal design.

Record the counterfactual in product terms:

> Without A's observable result, B cannot deliver or define this specific observable result.

Convenience order, shared code, shared data, or expected implementation sequence remain outside the dependency graph. A candidate Increment inside a dependent Work Package is selectable only when every dependency outcome is directly verified in Current Product State; otherwise shape the earliest missing dependency outcome first rather than absorbing a sibling Work Package into the Increment.

## Outcome Horizon

Group Work Packages only to explain broad initiative intent and likely outcome ordering. A horizon is not a set of current ready planning units.

Classify packages when useful as:

- `Foundation` — outcome area likely to contain an early durable product foundation;
- `Expansion` — independently valuable later capability;
- `Deferred` — outside the current shaping commitment.

These labels do not make every Foundation package current delivery scope and do not authorize future Increments.

## Construction Candidate Generation

Within the connected outcome area, generate reasonable next product states from the verified Current Product State. Each candidate must state:

```text
Candidate <label>:
Outcome Area: None | WP-NNN
Current Product State:
Target Product State:
Actor Or Operator:
Trigger Or Inspection Target:
Observable Result:
Authoritative Readback:
Durable Foundation:
Future Policy Avoided:
Lead Disposition: SELECT | REJECT
Reason:
```

Do not create a candidate whose only result is a technical scaffold such as a database, adapter, abstraction, service layer, test seam, refactor, or internal API unless that artifact is itself the externally consumed product.

Exactly one candidate is selected. Structural validation may require the fields above, one `SELECT`, and exact closure from that selected candidate into the Selected Next Increment. It must not score candidates, infer product value, or overrule the Lead's substantive Smallest Durable Choice judgment.

## Construction Dependency

A construction dependency exists only when an earlier observable product state must exist for the candidate state to be meaningful or coherently accepted under any reasonable internal design.

Use the counterfactual:

> If the earlier observable product state did not exist, could this candidate still provide the same product result and authoritative readback under a reasonable implementation?

If yes, the relationship is not a construction dependency. Do not encode likely implementation order, shared code, or storage convenience as product sequencing authority.

## Durable Increment Selection

A selected Increment must pass all applicable tests.

### Observable Completeness

A real actor or operator can trigger or inspect the authored product behavior and obtain an observable result with an authoritative readback. “Ready for later work” does not pass.

### Durable Foundation

The product meaning introduced by the candidate can remain when later capability is added. Avoid intentionally disposable miniature semantics that would need to be replaced simply because the product matures.

### Product-Dependency Closure

The candidate contains all earlier observable product results required for its meaning. Internal implementation prerequisites remain inside later Ticket delivery.

### Future-Policy Deferral

The candidate does not settle later sharing, scale, automation, multi-actor, lifecycle, policy, or presentation choices unless they are necessary for this observable result or already unavoidable authority.

### Smallest Durable Choice

Among passing candidates, choose the one that creates the least additional product surface and premature policy while establishing a usable durable foundation and moving toward the Intent Horizon.

This is not “choose the smallest task.” A tiny technical preparation step fails if it has no independent product result.

## Atomic Exception

A broader Increment is valid when a smaller candidate cannot create a safe, meaningful, independently readable product state, or when an unavoidable compatibility, migration, external contract, or atomic lifecycle boundary requires the broader state.

Record:

```text
Smaller Durable Candidate Tested:
Why It Fails:
Required Broader Boundary:
Supporting Evidence:
```

Do not invoke the exception merely because a broader implementation is convenient.

## Anti-Fragmentation Audit

For every Work Package split and Increment candidate, confirm that the boundary is product-observable rather than a technical preparation boundary. A failed audit merges the outcome or rejects the candidate.

## Anti-Blob Audit

For every selected Increment, confirm that it does not:

- combine independently acceptable sibling outcomes without necessity;
- bundle foundation, intermediate, and mature states only because they share one vision;
- pre-decide later product policy that can safely wait for re-entry; or
- require Matt to plan future capability that is not needed for the selected observable state.

A failed audit narrows the Increment or reopens Scope evidence.

## Re-entry Rule

The provisional construction horizon is advisory only. After the selected Increment is delivered, directly inspect the actual resulting product state before choosing another Increment. Never promote a previously predicted next stage to `ready-for-matt` without a new shaping decision. In the same Scope directory, the new selection uses the next unused `INC-NNN` ordinal and every earlier ready Increment becomes `Status: superseded`; this closes old planning admission without asserting delivery completion.
