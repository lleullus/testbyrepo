# Planning Input Currentness

## Purpose And Boundary

This reference owns the resolver and currentness mechanics for the `planning-ticket.md` contract. It does not add a planning authority, terminal state, evidence class, ledger, or self-digest. The captured seal is persisted only as historical correlation in a completed immutable ImplementationResult.

`planning-ticket.md` remains authoritative for Ticket, parent Spec, blocker, project-root, UI/reference, Worker, and readiness rules. This reference neither consumes additional planning inputs nor changes those rules.

## Initial Resolution And Seal Capture

Initial resolution is one fail-closed preflight, in this order:

1. Retain the exact supplied Ticket path bytes/value unchanged as invocation scratch for mismatch diagnosis. Resolve that local path to one readable regular file and capture its canonical absolute real path. Resolution never rewrites the supplied spelling.
2. Read the Ticket as raw bytes. Parse those bytes as UTF-8 Markdown under the Ticket contract; malformed UTF-8 or Markdown-contract failure blocks preflight.
3. Resolve the project root under the Ticket `Project-Root` and optional invocation-root rules. It must be the one canonical, accessible product directory required by `planning-ticket.md`. It is not a seal field or a planning-workspace location.
4. Retain the exact authored `Parent-Spec` value as preflight scratch. Resolve it from the Ticket directory when relative, require one readable regular-file target, and capture its canonical absolute real path. Product-root containment is not a parent-Spec readiness condition.
5. Read the parent Spec as raw bytes and parse it as UTF-8 Markdown under the parent-Spec contract. Preflight its exact `approved` status, non-empty owner, and the required scope-authority and unresolved-product-decision checks.
6. Process the Ticket `Blockers` body. The exact one-line `None` produces an empty blocker list. Otherwise, resolve every authored local Markdown path in authored list order from the Ticket directory, require one readable regular-file canonical target, and block duplicate canonical targets or any ambiguous target. Read each blocker as raw bytes and parse its exact top-metadata `Status`; initial readiness accepts only exact `resolved` or `done`.
7. Complete the Ticket-contract UI/reference and project-root readiness preflight, including the required approved UI/UX authority when `UI: yes` and the prohibition on inferred UI authority when `UI: no`. These checks do not add UI, reference, root, Worker, or workspace fields to the seal.
8. Only after every readiness check succeeds, capture the initial seal before dispatch of the first current task. The initial capture is not a currentness recheck point.

The sole seal shape is:

```text
PlanningInputSeal
  ticketPath
  ticketSha256
  specPath
  specSha256
  blockerFiles[]
    path
    sha256
    status
```

Its field semantics are:

- `ticketPath`, `specPath`, and every blocker `path` are canonical absolute real paths captured after safe resolution.
- Every hash is lowercase SHA-256 of that file's exact raw bytes.
- `blockerFiles` preserves the Ticket-authored list order. Exact `None` produces `[]`; duplicate canonical targets block rather than producing duplicate entries.
- A blocker `status` is its exact parsed metadata value. Initial readiness permits only `resolved` or `done`.
- Exact supplied and authored path values remain ordinary invocation/preflight scratch outside the seal, solely for mismatch diagnosis. They do not create seal fields.
- The seal remains immutable invocation state and is copied into the completed ImplementationResult. It is not a resumption token, is never adopted by a later invocation, and is not hashed into itself.

The canonical seal serialization is compact UTF-8 JSON with no insignificant
whitespace and no trailing newline. Outer fields occur in exact order
`ticketPath`, `ticketSha256`, `specPath`, `specSha256`, `blockerFiles`; every
blocker object uses exact order `path`, `sha256`, `status`; blocker array order
is authored order. Strings use JSON escaping without ASCII-only replacement.
`planningSealDigest` is lowercase SHA-256 of those exact serialization bytes.
No alternate capitalization, field order, alias, or repaired input is accepted.

The initial `planningInputSeal` is captured exactly once before the first Worker and is never resealed.
`AcceptanceCoverageRecord`, `MaterialPremiseRecord`, `ImpactScopeRecord`, current task selection, task
Canonicals, and other derived `RunRecord` projections are not planning inputs and do not alter the
seal. They cannot override or absorb changed Ticket, Spec, or blocker bytes.

## `planning_input_current`

`planning_input_current` is evaluated against the initial seal and the same invocation context. It is true only when all of these are true:

1. The same invocation Ticket path resolves safely to the same canonical `ticketPath`; the current Ticket is readable, regular, parseable, and its exact raw-byte hash equals `ticketSha256`.
2. The current Ticket parse resolves `Parent-Spec` safely to the same canonical `specPath` and yields the same authored blocker sequence with the same canonical blocker paths in the same order. The Spec may remain outside the current valid product root.
3. The current parent Spec is readable, regular, parseable, and its exact raw-byte hash equals `specSha256`.
4. Every current blocker is readable, regular, parseable, has the same raw-byte hash and exact parsed `status` as its corresponding seal entry, and its current status remains exact `resolved` or `done`.
5. Project-root identity, UI/reference authority, and core-workspace identity are rechecked by the existing core/current-authority guard. They are not represented by extra seal fields.

Any missing, unreadable, non-regular, retargeted symlink, ambiguous target, duplicate canonical target, parse error, hash mismatch, status mismatch, status no longer `resolved` or `done`, or Ticket/parent-Spec/blocker list, order, or canonical-path change makes the predicate false. Recheck reads are comparisons only: changed content is never adopted as new input, resealed, repaired, or used to continue.

Hash equality establishes byte and resolved-path currentness only. It does not approve the product again or establish correctness anew. The contextual parent-Spec scope and non-goal judgment occurs at initial preflight; unchanged bytes retain that captured judgment, while changed bytes block for the Ticket or Spec owner. Capsule and source identities remain separate from this seal.

## Mandatory Rechecks And Result

Evaluate `planning_input_current` at these gated points:

1. Immediately before every Worker call, including first, later, and bounded implementation remediation.
2. Immediately before marking each task `IMPLEMENTED`.
3. Immediately before entering final source review.
4. Immediately before publishing the ImplementationResult.

If it is false at any point, stop before that action and return exactly:

```text
blocked: planning input changed
next owner: Ticket 또는 Spec owner
```

Do not auto-reread and continue, reseal, repair planning documents, edit documents, dispatch a Worker, mark a task implemented, or complete after this result. A missing or unavailable exact Worker remains the user-owned preflight result defined by `planning-ticket.md`; it is not planning-input change.

## Core Integration Boundary

`SKILL.md` loads this reference before initial seal capture or currentness use and applies all gated
rechecks above. This reference owns only the mechanics above; it does not modify product paths, add a
planning authority, or alter Capsule, ownership, Worker, or terminal semantics.
