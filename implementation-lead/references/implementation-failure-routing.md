# Implementation failure routing

This reference separates implementation repair from verification-triggered remediation.

## Before the first handoff

Implementation Lead may open another bounded Worker envelope when an actual source or integration
review finds a defect and the ready Ticket already fixes the required behavior. The Lead must preserve
the same planning seal, baseline transaction, selected Worker authority, ownership accounting, and
finite budget.

Do not dispatch a Worker when the finding requires any of these:

- changed or weakened AC meaning;
- expanded Scope or reversed Non-Goal;
- a new product-policy, public/persisted compatibility, migration, UI/UX, deployment, tenant, target,
  credential, or external-effect decision;
- missing safety or mutation authority;
- overwrite or loss of pre-existing work;
- planning or source currentness that cannot be established.

Route the decision to planning or the user. Do not publish a handoff with unresolved implementation
items.

Mandatory implementation check failure keeps the transaction open for a bounded in-Ticket repair when
authorized. Timeout, missing tools, unstable source capture, or environment inability is an
implementation stop; it is not a public VerificationResult.

## After an ImplementationHandoff

The initial Implementation Lead invocation is closed. A later review, test, or runtime finding does not
rewrite or reopen the handoff or initial transaction.

Final semantic outcomes are published only by Verification Lead:

```text
VERIFIED
VERIFICATION_FAILED
INCOMPLETE
BLOCKED
```

Only immutable `VERIFICATION_FAILED` may lead to source mutation. A draft rationale, intermediate
observation, unpublished result, `INCOMPLETE`, or `BLOCKED` does not authorize remediation.

## Verification remediation admission

A fresh Remediation Lead may admit a correction only when:

```text
current tip = exact published VERIFICATION_FAILED
current source = failed handoff final source
at least one exact criterion is CONTRADICTED
desired observable, AC meaning, Scope, and Non-Goals are unchanged
existing authority already decides all material behavior
mutation is necessary for the failed Ticket behavior
safety, authorization, ownership, target, and credential requirements are current
```

Private patch organization may remain delegated. An already-authorized API, schema, migration,
compatibility, or UI correction can therefore remain in-Ticket. A new material decision cannot.

Missing remediation capability or authorization leaves the failed result as the current tip and starts
no Worker. It does not create a replacement `BLOCKED` or `INCOMPLETE` result.

## Remediation closure

Successful remediation requires a non-empty authorized tool-owned delta, a new non-ancestor source
identity, and an atomically linked successor `ImplementationHandoff`. A fresh Assessor then reseals and
re-executes every exact AC without carrying old attempts, mappings, rationale, or provisional smoke.

A no-delta, rejected, or fully reversed Worker call may release its claim only through durable safe
no-successor closure proving exact predecessor identity, complete ownership reconciliation,
preservation, and no unresolved external effect. Otherwise the claim remains active for containment,
restoration, reconciliation, or handoff.

An exact-repeat guard stops another automatic mutation only on mechanical `MATCH` of criterion hash,
sealed obligation/request, stable target, and structured terminal fact. `UNAVAILABLE` never becomes a
free-form similarity classifier.
