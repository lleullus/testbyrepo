# Integrated Implementation Skills

This repository snapshots the local IIS workflow from initiative shaping through
product planning, Ticket implementation/verification, and Ralph-style end-to-end
Goal fulfillment.

## Components

- `scope-shaper/`: connected planning-landscape investigation and conditional
  initiative decomposition in one Lead context and one user approval.
- `scope-investigation-runner/`: internal read-only investigation contract used
  only by Scope Shaper with the exact user-designated Runner roster.
- `matt/`: product/Behavior/UI planning, approved Spec creation, and complete
  ready Ticket decomposition. Ticket Verification flows use current positional
  `Parent outcome ordinal`, `AC ordinals`, and `Behavior authority ordinals` so
  observable AC work remains traceable to its parent outcome and applicable
  semantic Behavior guardrails without persistent IDs or a trace database.
  Project-relative Behavior paths resolve from the exact `Project-Root`. Global
  or preserved Spec Behavior may remain whole-Goal obligations instead of being
  copied into an unrelated Ticket merely for set coverage.
- `implementation-lead/`: implementation of one exact ready local Markdown
  Ticket followed by Lead review of the real project diff, implementation checks,
  and exact unresolved limitations. Explicit leaf requests use a user-designated
  Implementation Subagent. Current-conversation user role bindings, reservations,
  ordering, and consumption timing remain authoritative in Ralph; host-provided
  roles fill only unspecified slots. Related fresh findings feed an existing
  active implementation invocation first when communication is available instead
  of consuming another reserved role. This is invocation-local continuity, not
  defect/AC/file ownership. Implementation result is not an independent AC verdict
  or final `VERIFIED` status.
- `verification-runner/`: fresh bounded product/canonical observation subordinate
  to Verification Lead or Goal Verification Lead. It reports raw current evidence
  or an exact evidence limit and never owns verdicts, remediation, progression, or
  another role merely because the same model is available. User-designated Runner
  bindings and consumption conditions are preserved; IIS defines no fixed
  AC/flow/outcome/defect/file-per-Runner split.
- `verification-lead/`: independent Ticket-verdict authority for one exact ready
  `Independent` Ticket. Fresh Verification Runner invocations perform actual
  observation; the Lead owns evidence admission, AC verdicts, and aggregate. An
  early concrete Runner finding may be forwarded to Ralph before remaining
  observation finishes, but Lead and Runner never remediate product code.
- `iis-goal-loop/`: Ralph-style orchestration for exactly one bounded approved
  Spec. It rejects an outcome with no approved completion evidence path before
  mutation, acts on current in-Scope evidence inside the active Ticket, may overlap
  same-Ticket implementation when useful and safe, uses current readbacks without
  duplicating unsafe effects, and requires settled fresh Ticket/whole-Spec
  verification before completion. It never promotes one Work Package to parent
  initiative completion and is not a Controller runtime or durable workflow
  engine.
- `goal-verification-lead/`: fresh whole-Spec verification of every approved
  outcome plus remaining global Requirements, Non-Goals, constraints,
  Behavior/UI obligations, and preserved invariants. Only an all-PASS result may
  return `GOAL VERIFIED`.
- `iis-workflow/`: canonical entry router. Explicit planning, implementation,
  Ticket-verification, and whole-Spec-verification requests stay on their exact
  leaf boundaries; only an end-to-end product-completion request enters the Ralph
  loop after ordinary planning has produced a validated complete ready Ticket
  set.
- `repo-snapshot/`: independent Git working-tree snapshot skill; its credential
  remains outside this repository at `/home/user01/.config/repo-snapshot/token`.

The component directories are plain tracked directories. They do not contain
nested Git repositories; versioning is owned by this repository root. IIS does
not use a controller database, persistent Goal state, attempt ledger, event/replay
engine, or generic workflow DSL for Ralph fulfillment.
