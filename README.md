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
  observable AC work remains traceable to its parent outcome and semantic
  Behavior guardrails without persistent IDs or a trace database.
- `implementation-lead/`: implementation of one exact ready local Markdown
  Ticket followed by Lead review of the real project diff, implementation checks,
  and exact unresolved limitations. Explicit leaf requests use a user-designated
  Implementation Subagent. The Ralph loop alone may provide an invocation-local
  host role without persisting it. Implementation result is not an independent AC
  verdict or final `VERIFIED` status.
- `verification-lead/`: optional independent verification of one exact ready
  `Independent` Ticket from fresh direct product or canonical-target evidence.
  It does not modify the product or restore a verification runtime, transport,
  store, ledger, or persistent result state.
- `iis-goal-loop/`: Ralph-style orchestration for an already approved product
  Goal. It repeatedly selects current unmet Ticket ACs, reuses the same Ticket
  across materially different in-Scope corrections, reobserves current behavior,
  and keeps the Goal open until fresh whole-Spec verification succeeds. It is not
  a Controller runtime or durable workflow engine.
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
