# Integrated Initiative Decomposition Rules

Use these rules only when Scope Shaper has verified several connected candidate
outcome areas. They add product decomposition decisions to the same Scope
result; they do not repeat landscape discovery.

## Central Rule

Create the largest Work Package that remains independently plannable and
acceptable.

A package is large because it owns a coherent observable product or operating
outcome. It is independent when its product contract can be clarified and
accepted without defining a sibling package's contract.

## Relationship Decision

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

## Split Test

Choose `SPLIT` when verified evidence establishes an independent product
boundary, such as:

- either result remains meaningful when the other is accepted, deferred, or
  rejected;
- the results complete different user or operator jobs;
- they own different product lifecycles, authorities, failure policies, or
  deliberate rollout boundaries;
- one is an optional expansion rather than part of the other's core acceptance;
  or
- one Matt planning unit would otherwise settle unrelated product decisions.

State what remains independently usable and test the strongest reasonable merge
interpretation.

## Merge Test

Choose `MERGE` when:

- neither candidate produces a meaningful accepted result alone;
- one is preparation, migration, source recovery, build enablement, refactor, or
  another delivery condition for the other's outcome;
- they share one acceptance moment and separation creates a package whose result
  is only “ready for later work”;
- the apparent boundary disappears when implementation details are removed; or
- Matt would immediately need to settle the same product decisions for both.

## Package Statement

Prefer:

```text
<actor> can <complete a meaningful job or operate a meaningful lifecycle>
```

Product acceptance defines package identity. Technical layers, repository
modules, schemas, interfaces, tests, and anticipated sequence describe delivery
rather than independent acceptance.

## Product Dependency

Add `WP-B depends on WP-A` when A has an observable product result and B cannot
be delivered or coherently accepted without that result under any reasonable
internal design.

Record the counterfactual in product terms:

> Without A's observable result, B cannot deliver or define this specific
> observable result.

Convenience order, shared code, shared data, or expected implementation sequence
remain outside the dependency graph.

## Release Cut

`MVP` is the smallest dependency-closed set that enables the initiative's core
end-to-end job for a real user or operator.

Classify every package once:

- `MVP` — required for the first usable end-to-end result;
- `Next` — independently valuable near-term expansion;
- `Deferred` — outside the current shaping commitment.

## Anti-Fragmentation Audit

For every split, confirm that both sides have meaningful outcomes, neither side
is merely preparation, one Spec cannot reasonably own both without unrelated
product decisions, and the independent-acceptance counterfactual holds.

A failed audit changes the relationship to `MERGE` or reopens the affected
Scope evidence.

## Anti-Blob Audit

For every package, confirm that it does not contain two outcomes that can be
accepted or deferred independently, does not combine the core job with an
optional expansion, and would not require two mostly unrelated Matt planning
interviews.

A failed audit creates a supported split or reopens the affected Scope evidence.
