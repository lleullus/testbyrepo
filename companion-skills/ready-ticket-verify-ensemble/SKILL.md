---
name: ready-ticket-verify-ensemble
description: "Explicitly verify one existing IIS Ready Ticket with a weak-agent ensemble. Main remains the sole verifier and directly performs the Ticket-authorized product/runtime actions; four fixed read-only analyst roles independently inspect one stable target in parallel waves, challenge the contract and evidence, and Main adjudicates every authored Verification flow and AC and owns the guarded done transition. Use only when the user explicitly selects ensemble or team verification; never infer this mode from model capability."
---

# Ready Ticket Verify Ensemble

## Purpose and authority

Verify one exact IIS Ready Ticket when the user explicitly chooses a weak-agent ensemble rather than the DIRECT verifier.

The current Main is the sole verifier. It owns canonical admission, target binding, semantic contract judgment, scenario freeze, objection adjudication, every flow result, every AC verdict, Scope/Non-Goals and cross-AC closure, the whole-Ticket verdict and guarded `ready -> done` progression.

The ensemble supplies bounded evidence and challenges; it does not distribute verifier authority:

- `CONTRACT_INTERPRETER`, `ORACLE_CHALLENGER`, `EVIDENCE_ARCHITECT` and `SEMANTIC_MATERIALITY_REVIEWER` are read-only advisory analysts.
- Main itself performs every frozen Ticket-authorized product/runtime action and captures the raw authoritative evidence. No child role executes the product/runtime trigger.
- No child role issues `SATISFIED`, `CONTRADICTED`, AC `PASS`/`FAIL`, whole-Ticket verdict or Ticket status mutation.

Before work, read [references/orchestration.md](references/orchestration.md) and [references/role-contracts.md](references/role-contracts.md) in full. Main must also read:

- the current sibling DIRECT verifier contract at `../ready-ticket-verify/references/verify.md`, applying its canonical admission, semantic contract check, status, target-stability, evidence, disposition, adjudication, Scope/Non-Goals, guarded progression and no-remediation semantics while excluding its DIRECT-only topology; and
- `../purpose-first-review/SKILL.md` for material-objection admission, closure and anti-bloat discipline.

## Explicit activation

This skill is explicit-only.

- Use it only when the current user explicitly selects `$ready-ticket-verify-ensemble`, ensemble verification, team verification or the equivalent for this exact Ticket.
- Do not infer ensemble mode from model quality, cost, availability or task difficulty.
- Do not silently fall back to `ready-ticket-verify` when ensemble capability is unavailable or a role fails.
- Do not silently switch a DIRECT request into ensemble mode.

## Inputs

Required contract-authority input:

- Ticket: `<exact absolute canonical TICKET-NNN.md path>`

Optional navigation inputs:

- Candidate Verification Target: `None | <current source/config/build/artifact/runtime hint>`
- Implementation Report / Evidence: `None | <navigation/reference only>`
- Additional User Instructions: `<instructions>`

Derive `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities and References from the validated Ticket itself. Optional target/report inputs never override the Ticket or fresh current observation.

## Capability gate

Before canonical product/runtime action, confirm the host can provide:

1. at least two independent child contexts, with four concurrent analyst contexts preferred;
2. the same exact Project Root and target snapshot to every used role;
3. parent-directed terminal results containing actual worker identity, actual root and actual target identity;
4. Main itself can directly access the required product/runtime/canonical surfaces and perform the exact authorized frozen actions; and
5. no forced sharing of another role's conclusions before independent reports are returned.

Four analysts may run concurrently. When only two independent analyst contexts are available, run two roles and then the other two as a second read-only batch without disclosing first-batch conclusions. One reusable child context or a shared conversation that retains another role's conclusions is not independent ensemble capability.

If the capability gate fails, return:

```text
ENSEMBLE CAPABILITY UNAVAILABLE
Ticket:
Missing capability:
AC verdicts: Not issued
```

## Fixed execution topology

Use all four analyst roles for every ensemble verification. Do not ask a weak Main to dynamically choose which reasoning protections a Ticket needs.

```text
Wave 0  Main binds exact authority and target snapshot
Wave 1  Four independent read-only analyst preflights
Wave 2  Main admits and closes material objections; freezes one scenario
Wave 3  Main directly executes the frozen actions and captures raw evidence
Wave 4  Four independent analyst post-run evidence reviews
Wave 5  Main applies the canonical flow/AC/Ticket rules and guarded progression
```

Parallelize only read-only work on the same stable snapshot. Serialize target binding, objection adjudication, product/runtime action, cleanup, final verdict and Ticket mutation.

## Core invariants

- All authored Verification flows and conditional boundaries remain the mandatory denominator.
- Analysts inspect the complete integrated Ticket contract; do not split final AC ownership across workers.
- Analysts never execute the product/runtime trigger. Main owns the single authoritative execution path for the invocation.
- Worker agreement is neither required nor sufficient. Do not vote, average confidence or count supporting workers.
- A concrete material objection survives until closed by exact authority or fresh attributable evidence, not by other workers' disagreement.
- Main uses one invocation-local assignment/objection table only; do not create a product file, persistent roster, queue, receipt, evidence ledger or workflow database.
- Every report must state actual root, Ticket and target identity. A report from another root, revision, artifact or runtime checkpoint is not evidence for this verification.
- Implementation reports, tests, logs and source shape remain navigation/support unless the approved Ticket makes that exact surface authoritative.
- Missing evidence is never rewritten as success or failure.

## Verdict and terminal authority

Main alone applies the sibling DIRECT verifier's canonical result meanings:

```text
Flow result: SATISFIED | CONTRADICTED | INCONCLUSIVE
AC verdict: PASS | FAIL | INCONCLUSIVE
Whole Ticket: VERIFIED | FAILED | INCONCLUSIVE
```

- Any required mapped contradiction makes the affected AC `FAIL`.
- An AC is `PASS` only when all mapped obligations are satisfied by decisive current evidence.
- Otherwise the AC is `INCONCLUSIVE`.
- All ACs `PASS` -> `VERIFIED`; any AC `FAIL` -> `FAILED`; otherwise -> `INCONCLUSIVE`.

Only Main may perform the sibling DIRECT verifier's guarded `Status: ready` to `Status: done` transition, and only after final `VERIFIED`, stable current target/authority, complete cleanup/terminal closure, exact current validator `VALID` and the unchanged canonical ready Ticket contract. Workers never edit Ticket status.

## Safety and stop boundary

- Analysts are read-only and never delegate further.
- Main does not edit product source/config/tests or planning authority to manufacture a pass during verification.
- Side-effectful, duplicate-sensitive, irreversible, credential-bearing, shared/production, message, payment or deployment actions require the exact existing Ticket/user authority.
- A transport/network failure during a Main-owned mutation-capable action leaves execution state unknown until Main reads authoritative current state; do not immediately repeat the same action.
- Verification ends with evidence, verdict and any guarded progression result. Do not automatically remediate implementation, invoke planning, create follow-up Tickets or continue to another Increment.
