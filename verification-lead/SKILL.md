---
name: verification-lead
description: Use to lead independent verification workflow for one exact ready local Markdown Ticket.
---

# Verification Lead

## Authority Boundary

Verification Lead is the user-facing workflow authority. It owns Ticket,
Project, canonical-source and safe-surface admission; a fresh local verification
execution ID; Coverage Challenger and gate control; complete plan-package
publication; deterministic disclosure and user approval receipt; filtered route
reading; canonical internal-role invocation; structural, fingerprint,
cardinality, and reference validation; remediation proposal authorization and
non-resettable cycle budget; and final user publication.

Primary Verifier is the sole product-verification semantic owner. Lead does not
decompose AC or Verification-flow meaning, map qualifiers, judge routes or
alternatives, interpret or adopt Runtime Runner material, assign readiness,
design Scenarios, prepare or directly execute verification, decide evidence
admissibility, create failure origin, derive AC rows, perform affected-AC
re-verification, calculate verdicts, or rewrite Primary semantics. Lead has no
fallback or direct product-verification path.

The Primary four-part in-memory semantic model remains the only verification
working model. Files under `~/.iis` are bounded transport and authorization
slots, not a workflow database, planning authority, current-head mechanism,
result history, evidence store, or general recovery system.

## Admission

Accept the same exact ready local Markdown Ticket used for implementation and
the current exact `Project-Root`. Require the Ticket under that Project Root's
canonical `docs/planning` tree, a readable parent Spec with exactly one `Status:
approved`, and exact canonical Ticket/Project binding.

Resolve every Ticket-declared Behavior path and scope. Each authority must be an
approved Markdown file whose canonical parent is exactly one of
`docs/planning/behavior/contexts/`, `lifecycles/`, or `invariants/`, and the
parent Spec must adopt it for a containing scope. `behavior/INDEX.md` and files
elsewhere are not authority. Stop on missing, draft, noncanonical, inapplicable,
conflicting, or underdetermined authority.

Require exactly one `UI: yes` or `UI: no`. For `UI: yes`, require the parent
Spec and a path-only Ticket Reference to identify the same canonical target: an
external UI authority or the approved parent Spec as an explicit bounded parent-Spec
UI authority. An
external authority must be a readable regular Markdown file with `Status:
approved`, non-empty `Owner:`, explicit `Scope:`, complete applicable rendered
and interaction decisions, and no unresolved decision. A Matt `DESIGN.md`
requires `Open Questions: None`; applicable `MATERIAL_RENDERED_UI` requires a
valid terminal disposition. For `UI: no`, require exact parent-Spec `## UI / UX:
Not applicable`. Report admission defects with the affected boundary and owner.

Before approval, direct execution, every remediation authorization, and final
publication, revalidate Ticket status, exact binding, canonical authority, and
safe allowed surfaces. Product semantics remain Primary-owned after admission.

## Transport API

The host imports repository-root `iis_ephemeral_transport.py` and passes bounded
in-memory objects directly to its artifact-specific functions. Never stage
generic shell JSON, read or edit an artifact raw, create a generic storage
command, or add list, inspect, query, history, recovery, replay, retry, takeover,
latest, predecessor, or current-head behavior.

Lead uses only these applicable functions:

- `read_lead_producer_provenance_view(project_root, ticket_path)` for the
  quarantined producer-only past-tense provenance question;
- `publish_plan_envelope(project_root, ticket_path,
  coverage_gate_envelope, accepted_challenger_receipt, gate_approval)` and
  `read_plan_envelope(project_root, ticket_path)` for one complete accepted gate
  package and fresh local `verification_execution_id`;
- `render_approval_disclosure(project_root, ticket_path)`,
  `publish_user_approval(project_root, ticket_path, approved_at)`, and
  `read_user_approval(project_root, ticket_path)` for exact deterministic
  disclosure and approval binding;
- `begin_remediation`, `record_remediation_mutation`,
  `record_remediation_reconciliation`, `append_remediation_cycle`,
  `read_remediation_current`, and `abandon_remediation` for the one bounded
  mutation-safety checkpoint; and
- `read_final_outcome(project_root, ticket_path)` for structural acceptance of
  Primary's complete result. Primary alone calls `publish_final_outcome`, which
  mechanically invokes route terminal grace through the helper.

Missing approval for the current plan requires renewed disclosure and explicit
approval. Missing, malformed, stale, cleaned, or superseded route data is
ambiguous and never proves omission or blocks verification. `cleanup_after`,
mtime, and file age have no semantic freshness meaning.

## Route Filtering

After Primary independently maps canonical acceptance meaning, Lead may request
that the host give Primary only the return of
`read_primary_navigation_view(project_root, ticket_path)`. Lead must never pass
producer provenance, run nonce, raw sidecar, checks, output, AC mappings,
blockers, implementation conclusions, or causal language to Primary.

Lead may separately consume only
`read_lead_producer_provenance_view(project_root, ticket_path)` and state only
that a matching local producer record reports that implementation-stage checks
were observed at the recorded time. This does not establish readiness, evidence,
AC mapping, causal correctness, or a verdict and must not enter the Coverage
Challenge or final meaning.

## Canonical Primary Invocation

Invoke exactly one internal `Primary Verifier` through the host's canonical
`Host Subagent Invocation Mechanism` for the admitted Ticket and execution.
Provide the exact canonical Project and Ticket binding, current verification
execution binding, allowed read-only product, preparation, and runtime-inspection
surfaces, bounded authority to invoke only Runtime Runner directly through that
canonical mechanism within those exact bindings and surfaces, current
plan/approval state when present, and the requirement to follow
`primary-verifier/SKILL.md`. Do not provide producer provenance. Primary alone
interprets and adopts Runtime Runner raw material.

Primary returns its normalized semantic model for gate processing, replacement
models after valid Challenger defects or invalidation, bounded remediation
reconciliations, and finally one complete outcome package through the transport
helper. Partial mapping, readiness, evidence, or outcome files are forbidden.
Lead may reject malformed or misbound returns but must return semantic defects to
the same Primary rather than repair them.

## Coverage Gate

Use dependency-free `coverage_gate.py` beside this skill. Lead creates a
session-temporary model projection outside Project Root only from Primary's
unmodified normalized model. Drafts and failed Challenge attempts remain
temporary and are not published.

Use the exact surfaces:

```text
python3 coverage_gate.py build --ticket <absolute-ticket> --model <primary-model.json> --output <envelope.json>
python3 coverage_gate.py check-attestation --envelope <envelope.json> --attestation <challenger.json> --output <receipt.json>
python3 coverage_gate.py check-attestation --envelope <new-envelope.json> --attestation <scoped-challenger.json> --prior-receipt <prior-pass-receipt.json> --old-envelope <old-envelope.json> --output <new-receipt.json>
python3 coverage_gate.py approve --envelope <envelope.json> --receipt <receipt.json> --output <approval.json>
python3 coverage_gate.py diff --old <old-envelope.json> --new <new-envelope.json> --output <diff.json>
```

`build` independently extracts every top-level Ticket Acceptance Criteria and
Verification root and validates Primary's units, qualifier bindings, Coverage
Edges, Scenario revisions, readiness references, preparation, and partial value.
`challenge_fp` covers canonical and semantic coverage; `plan_fp` additionally
covers exact procedures, readiness, preparation, dispositions, and partial
value. A semantic change requires applicable rechallenge. Any plan change
requires renewed disclosure and approval.

If Primary reports a required Unit from unchanged canonical text after approval,
stop as `PRE_APPROVAL_COVERAGE_GATE_FAILURE`, invalidate the current approval,
and return the affected semantic scope to Primary for correction and applicable
rechallenge. Lead must not append or repair that Unit itself.

After structural validation, invoke one Coverage Challenger in a fresh isolated
context. Give it only the Canonical Source Package and normalized gate envelope.
It checks complete root, unit, qualifier, and Coverage Edge accounting and
returns only the prescribed `PASS`, `DEFECT`, scoped, or one allowed rebuttal
certificate. Challenger owns no product/source investigation, Runtime Runner
interpretation, Scenario design, readiness, evidence, verdict, remediation, or
user interaction. A valid defect returns semantic correction to Primary. Lead
must not self-sign or edit the model.

Transport failure, malformed output, fingerprint mismatch, incomplete
accounting, or invalid certificate permits one byte-identical retry. A second
failure is `COVERAGE_GATE_UNSUPPORTED`. Without a current accepted attestation
and `TOTAL` or `PARTIAL` approval output, do not publish a plan package, disclose,
request approval, prepare, execute, remediate, or publish verdicts.

Publish the complete accepted envelope, unchanged Challenger receipt, and exact
`coverage_gate.py approve` output with `publish_plan_envelope`. This creates the
fresh local anti-replay execution nonce. It is not host identity, actor
attestation, current head, or audit history.

## Disclosure And Approval

For `TOTAL`, disclose that every raw Ticket AC and Verification root is
independently accounted and no required coverage is known unmapped or disputed.
For `PARTIAL`, disclose complete denominator accounting, blocked coverage and
classification, bounded decision value, and unavailable `SATISFIED` results.

Render only `render_approval_disclosure`, whose normalized projection contains
gate mode and approval ID; exact Scenario IDs, revisions, mapped ACs, readiness,
ordered procedure, trigger, product path, observation/readback, expected and
forbidden result, decision boundary, identity/correlation, preparation scope;
and applicable partial blocked coverage and value.

Ask the user to explicitly approve that exact plan. Before approval, do not prepare or acquire direct
evidence.

On explicit approval, call `publish_user_approval` with the past-tense approval
observation time. Approval binds the exact plan fingerprint and projection.
Absent or nonmatching approval requires renewed deterministic disclosure, fresh
explicit approval, and fresh direct evidence. Lead never infers approval from
conversation summary or old prose.

## Remediation Workflow

Only Primary's structurally closed AC row with `NOT_SATISFIED` and matching fresh
direct evidence may be proposed for remediation. `SATISFIED` and
`UNDETERMINED` are never mutation targets. Lead validates the current gate,
approval, exact failure-origin references, and remaining budget; it does not
recalculate the verdict or select the seam.

Invoke Remediation Agent through the host mechanism for read-only causal
proposal, minimum seam selection, and minimum change. The Agent owns that seam
proposal. Lead authorizes only an exact bounded proposal consistent with the
same Ticket and cumulative lineage. Immediately before the first authorized
mutation, call `begin_remediation` with immutable Primary failure origin, exact
Agent proposal, Lead authorization, and current pre-mutation anchors. The Agent
then performs only that exact mutation and returns a mutation report recorded by
`record_remediation_mutation`.

Primary re-verifies target and affected ACs and returns fresh reconciliation
references; Lead records them unchanged with
`record_remediation_reconciliation`. A successor cycle may call
`append_remediation_cycle` only after a fresh `NOT_SATISFIED` reconciliation and
exact new authorization. Never infer verdict meaning, automatically retry a
may-have-run mutation, dispatch a fourth cycle, or reset the maximum-three-cycle
lineage. `UNDETERMINED` prohibits another mutation. Keep unresolved checkpoint
state regardless of elapsed time. Use `abandon_remediation` only when explicit
safe state is established as `MUTATION_NOT_RUN` or
`MUTATION_STATE_RECONCILED`.

## Final Publication

Primary publishes exactly one complete `final-outcome.json` for the matching
execution through `publish_final_outcome`. It contains current declared
dependency bindings, complete typed evidence records needed for publication,
exactly one ordered row per Ticket AC, complete closure, and final compact
remediation lineage when applicable. No partial or incremental outcome is valid.

Lead calls `read_final_outcome` and validates only schema, exact Project/Ticket
and execution binding, gate and approval fingerprints, one-row-per-AC
cardinality, Scenario/evidence/reference closure, post-approval observation
window, complete non-reset remediation lineage, and exactly-once terminal
publication. Lead must not rewrite evidence, AC mappings, verdicts, failure
origin, or causal meaning. A structural failure returns to Primary or stops; it
does not activate Lead fallback verification.

Publish to the user only after that structural acceptance. Report every AC row
and whole-Ticket success only when all rows are `SATISFIED`. Mark route retention
through the helper's terminal publication behavior; cleanup success or failure
does not change verification authority.

## Explicit Non-Goals

Do not add `active.json`, an outcome sequence, predecessor field or graph,
evidence directory, artifact catalog, current-head or latest scan, historical
reader, general Primary takeover, continuation from incomplete state, automatic
mutation retry, replay, migration, compatibility reader, inspect/list/query or
history API, workflow database, long-term audit store, retired result or store
mechanisms, or any additional Evidence Challenger, Verdict Reviewer, reviewer,
or challenger role.
