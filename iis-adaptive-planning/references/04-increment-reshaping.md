# Increment Reshaping Contract

## Core principle

> An Increment is the current best planning hypothesis for the next durable observable product change. It is not a promise that must survive better evidence.

Keep the user's Intent/Mandate comparatively stable while allowing the construction shape to change.

Future construction horizon remains provisional exactly as current Scope Shaper defines it. Do not pre-create future `ready-for-matt` Increment files merely because Adaptive can reason about likely later work.

## When reshaping is normal

Treat reshaping as an ordinary planning operation when fresh evidence shows that the current shape is materially worse under current IIS/Mandate authority.

Typical triggers:

- Ask Matt discovers that one INC bundles independently acceptable outcomes;
- Behavior/UI planning reveals a missing durable product foundation or incompatible lifecycle boundary;
- To Spec cannot serialize the current shared understanding without importing deferred capability;
- To Tickets cannot form minimal independently acceptable Tickets without changing the product promise;
- verification evidence shows that the approved outcome is ordered after a missing product capability;
- a prior delivery changed actual current product state so the provisional horizon is no longer the best next shape;
- a Mandate revision changes product priorities or constraints.

Do not reshape merely because an implementation path looks inconvenient or a test is hard.

## Permitted operations under delegated reshaping

When the Mandate authorizes general Adaptive reshaping and no Return-to-User Boundary is triggered, Scope Shaper may:

- **split** one current candidate/INC into smaller durable observable product outcomes;
- **merge** candidate outcomes when separate delivery would not produce safe/meaningful independently readable states;
- **reorder** provisional outcome areas based on actual product-capability dependencies;
- **replace** the selected next INC with a better current-to-next product state;
- **shrink** an INC by deferring later maturity/policy not needed for the first durable result;
- **insert foundation** when a missing earlier observable product capability must exist first;
- **defer** a legitimate later capability to `Deferred Until Re-entry` / provisional horizon;
- **drop** speculative future capability that current intent/evidence does not support;
- **supersede** a no-longer-current ready planning handoff under current Scope lineage rules.

Use product meaning and counterfactual dependency, not technical layers, to decide these operations.

## Evidence before reshape

Before changing the current selected INC:

1. inspect the actual current product state relevant to the decision;
2. identify the exact new material fact, authority change, or contradiction;
3. compare the current shape with at least one plausible replacement shape;
4. apply current Scope Shaper durable-Increment tests and Mandate priorities;
5. determine whether the result is fully delegated or crosses a Return-to-User Boundary.

Do not create a generic scoring engine. Preserve Scope Shaper's substantive judgment model.

## Lineage

Use the current Scope Shaper's own artifact/history rules.

For a replacement shaping pass:

- create the next immutable `SHAPE-NNN` revision;
- use the next unused `INC-NNN` ordinal;
- assign a new project-wide unique Suggested Work Slug when current Scope rules require uniqueness;
- make prior `ready-for-matt` Increment(s) exact `Status: superseded` as current Scope rules require;
- never rewrite an earlier immutable Scope revision;
- keep each historical Increment bound to its original immutable source revision.

Adaptive trace records **why** the reshape happened and the old/new Increment paths. It does not replace canonical Scope lineage.

## Downstream planning invalidation

A material reshape invalidates downstream planning only to the extent its adopted meaning changed.

Apply current Baseline rules first. In addition:

- do not carry a shared understanding from a superseded INC into the replacement INC merely because it is similar;
- unchanged approved Behavior/UI authorities may be re-adopted when their exact scopes still apply;
- a replacement INC receives its own work slug/Spec under current Scope rules;
- old work artifacts remain historical evidence and do not become authority for the replacement merely by similarity;
- unfinished Ticket projection affected by a changed parent meaning must not remain current delivery authority.

If current Baseline rules already provide a valid way to return affected unfinished Tickets to `draft`, use it. Do not invent a new `superseded` Ticket status.

## Delivery-consumption boundary

Do not rewrite delivered history.

Exact `Status: done` Tickets remain terminal historical markers. If the desired direction changes after delivery:

1. inspect the actual resulting product state;
2. shape a new current Increment from that reality;
3. preserve the prior Scope/INC/Spec/Ticket history unchanged.

For a `ready` Ticket that may already have been implementation-consumed but is not `done`, do not pretend the old product state still exists. Use direct current repository/runtime evidence and available delivery evidence to establish the actual baseline. If whether work was consumed materially changes historical interpretation and cannot be established, return that exact fact boundary rather than silently rewriting it.

Adaptive does not create an implementation-consumption ledger to solve this ambiguity.

## Defer versus drop

Use **defer** when:

- the capability is still consistent with the Desired Product Outcome;
- it is not required for the current durable outcome;
- later need/order depends on future actual product state or policy.

Use **drop** when:

- the capability is not supported by the current Mandate/approved intent;
- it came from speculative implementation/test thinking rather than product authority;
- retaining it in the horizon would incorrectly imply intended future scope.

Do not create a future INC merely to preserve every discarded idea.

## Foundation insertion

Insert an earlier foundation only when the foundation is itself an observable durable product state or product capability required for the later outcome to be meaningful under any reasonable implementation.

Do not insert technical preparation such as:

- database setup only for later work;
- adapter/service abstraction;
- test seam;
- refactor for convenience;
- internal queue/controller;
- placeholder UI;
- temporary mock product state.

Those remain implementation-owned unless they independently satisfy current product authority.

## User-return examples

Return to the user when reshaping exposes a material product trade-off not resolved by the Mandate, for example:

- ship a limited but durable user mode now versus delay for a stronger atomic ownership model when both satisfy stated priorities equally;
- preserve a legacy compatibility promise versus intentionally break it to simplify the future domain model when no priority resolves the conflict;
- choose which of two independent user outcome areas should be pursued first when neither has a product dependency or priority advantage.

Do **not** return merely to ask permission for the mechanical act of split/merge/reorder when the better product shape is already determined by authority.
