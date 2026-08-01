# Work Package Decomposition Rules

Use these rules to decide whether candidate product outcomes belong in one Matt planning unit or several.

## The central rule

Create the **largest package that Matt can still plan independently**.

A package is not “large” because it contains many files or components. It is large because it owns a coherent product outcome. A package is not “independent” because it can be coded in isolation. It is independent because its product contract can be clarified and accepted without deciding a sibling package's contract.

## Split test

Split candidate A from candidate B only when at least one of these materially changes the planning result:

1. **Independent acceptance** — A can be accepted, used, released, or deliberately omitted while B remains unresolved.
2. **Different user job** — A and B complete meaningfully different jobs, even if they share an interface or data.
3. **Different lifecycle or authority** — A owns a materially different operating lifecycle, permission boundary, external authority, or failure policy.
4. **Optional expansion** — one is a useful expansion rather than necessary to complete the other's core result.
5. **Different rollout boundary** — the user deliberately needs one outcome available or migrated separately.
6. **Unrelated Matt decisions** — planning A would otherwise force Matt to settle material product decisions that do not affect A's acceptance.

A split is invalid when its only justification is code ownership, module layout, architecture, implementation sequence, testing convenience, or expected reuse.

## Merge test

Merge candidate A and B when any of these is true:

1. Neither produces a meaningful accepted result without the other.
2. One is only a technical prerequisite, abstraction, adapter, migration mechanism, refactor, or test surface for the other.
3. They share one acceptance moment and separating them would create a package whose outcome is “ready for later work.”
4. The supposed boundary disappears when implementation details are removed.
5. Matt cannot clarify one without immediately defining the same product decisions for the other.

## Package statement test

A good package title and Outcome can be stated without implementation nouns:

```text
Good: A user can preview exactly what context will be sent.
Good: A user can send one prepared consultation to one supported model and receive a result.
Good: An operator can inspect and recover previous runs.

Bad: Build the provider abstraction.
Bad: Add the session database.
Bad: Implement the browser adapter.
Bad: Create the CLI foundation.
```

A product surface such as “CLI,” “browser use,” or “agent integration” may appear when the surface itself materially changes who can use the product or what job can be completed. It must not be used merely as a proxy for technical layers.

## Dependency test

Add `B depends on A` only when all are true:

1. A has an observable product result.
2. B's observable result cannot be delivered or coherently accepted without A's result.
3. The dependency remains true under a completely different internal design.
4. The dependency is not merely “we expect to implement A first.”

Write the edge reason as a user- or operator-visible counterfactual. Remove edges justified only by shared code, shared data, an abstraction, a schema, or staffing order.

## MVP test

A package is in the MVP only when removing it prevents a real target user from completing the initiative's core end-to-end job.

Do not include a package in MVP solely because it:

- improves breadth, scale, reliability beyond the first accepted operating level, polish, or convenience;
- exists in the reference product;
- creates a reusable base for later packages; or
- is likely to be implemented early internally.

## Anti-fragmentation audit

Before presenting the map, inspect every adjacent pair of packages:

- Could one Spec reasonably own both without introducing unrelated product decisions?
- Does either package have no independently meaningful outcome?
- Is one package only “preparation complete”?

If yes, merge them unless the user approved a real rollout or authority boundary.

## Anti-blob audit

For every package, ask:

- Does it contain two outcomes that can be accepted or deferred independently?
- Does it mix the core job with an optional operating mode or distribution surface?
- Would Matt need to conduct two mostly unrelated requirements interviews?

If yes, split it at the product boundary.

## Reference-product audit

For every capability observed in a reference, classify it before it enters the map:

```text
Adopted core outcome
Adopted later expansion
Useful evidence only
Explicitly excluded
Unknown pending one shaping decision
```

“Present in the reference” is never sufficient authority by itself.
