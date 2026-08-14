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
  ready Ticket decomposition. An adversarial-consensus gate is available only
  when the user explicitly requests it for the current planning unit and
  explicitly designates the exact Adversarial Planning Challenger; Matt confirms
  the Intent Anchor first, remains the defending/counterattacking planning
  authority throughout the debate, and still requires final user approval after
  consensus. An explicit To Spec request does not bypass an active gate. Ordinary
  Matt planning does not suggest or auto-enable this gate, and follow-up rounds
  carry only material deltas instead of restating closed context.
  Ticket Verification flows use current positional
  `Parent outcome ordinal`, `AC ordinals`, and `Behavior authority ordinals` so
  observable AC work remains traceable to its parent outcome and applicable
  semantic Behavior guardrails without persistent IDs or a trace database.
  Project-relative Behavior paths resolve from the exact `Project-Root`. Global
  or preserved Spec Behavior may remain whole-Goal obligations instead of being
  copied into an unrelated Ticket merely for set coverage.
- `implementation-lead/`: implementation of one exact ready local Markdown
  Ticket followed by Lead review of the real project diff, implementation checks,
  and exact unresolved limitations. Explicit leaf requests use a user-designated
  Implementation Subagent. One Lead invocation consumes at most one admitted
  Subagent. Current-conversation user role bindings, reservations, ordering, and
  consumption timing remain authoritative in Ralph; ordered bindings are reusable
  precedence unless the user explicitly makes them one-shot/usage-limited/rotational,
  and host-provided roles fill only unspecified bindings. Related fresh findings feed an existing
  active implementation invocation first when communication is available instead
  of consuming another reserved role. This is invocation-local continuity, not
  defect/AC/file ownership. Implementation-stage product checks stay focused on
  changed/integration-affected gross liveness; they do not pre-run the complete
  independent browser/viewport/state/lifecycle/AC matrix. Implementation result is
  not an independent AC verdict or final `VERIFIED` status.
- `verification-runner/`: fresh bounded product/canonical observation subordinate
  to Verification Lead or Goal Verification Lead. It reports attributable raw
  current readback or an exact evidence limit before disposable cleanup and never
  owns verdicts, remediation, progression, or another role merely because the same
  model is available. User-designated Runner bindings and consumption conditions
  are preserved; IIS defines no fixed AC/flow/outcome/defect/file-per-Runner split.
- `verification-lead/`: independent Ticket-verdict authority for one exact ready
  `Independent` Ticket. Fresh Verification Runner invocations perform actual
  observation; the Lead owns evidence admission, AC verdicts, and aggregate. Runner
  labels are never votes or consensus. An early concrete Runner finding may be
  forwarded to Ralph before remaining observation finishes, but Lead and Runner
  never remediate product code.
- `iis-goal-loop/`: Ralph-style orchestration for exactly one bounded approved
  Spec. It acts on current in-Scope evidence inside the active Ticket. Unless a
  newer explicit user direction changes the initial schedule, each active Ticket
  starts implementation with one Lead/one Subagent. When timing is left to Ralph,
  later overlap waits for that first work to settle and uses the materially distinct
  useful-work tradeoff. An exact user instruction to overlap now overrides that
  Lead-owned wait/efficiency choice without changing Ticket or product authority.
  Eligible role count and maximum concurrency are capacity, not mandatory
  consumption. Scheduling repair is prospective: product-authorized mutation from
  an otherwise eligible but misordered/mistimed implementation binding is reobserved,
  not replayed merely to reconstruct preferred history. An observed scheduling
  change is sent once, delta-only, to affected active roles; exact immediate-overlap
  conflicts are reported instead of silently serialized. After mutation quiescence,
  an all-Independent Ticket does not pay a redundant Ralph full-AC scan before its
  verifier: Ralph performs a lightweight integration/authority preflight. Earlier
  Independent Tickets run Ticket Verification before Ralph leaves them; a last/only
  Independent Ticket goes directly to fresh Goal Verification unless the user asked
  for a separate Ticket verdict. Mutation-invalidated verification does not spawn
  new Runner work merely to finish stale old coverage; already-active observation
  continues only for distinct correction value or exact user-requested continuation.
  `GOAL INCONCLUSIVE` ends only its verifier invocation, and `NO PROGRESS` requires
  bounded closure of all currently known contract-admitted evidence/correction
  paths. One failed endpoint or
  representation is not dependency-wide unavailability. The loop never promotes
  one Work Package to parent initiative completion and is not a Controller runtime
  or durable workflow engine.
- `goal-verification-lead/`: fresh whole-Spec verification of every approved
  outcome plus remaining global Requirements, Non-Goals, constraints,
  Behavior/UI obligations, and preserved invariants. It uses new fresh Runner
  invocations after quiescence as a final non-streaming barrier; only an all-PASS
  result may return `GOAL VERIFIED`.
- `iis-workflow/`: canonical entry router. Explicit planning, implementation,
  Ticket-verification, and whole-Spec-verification requests stay on their exact
  leaf boundaries; only an end-to-end product-completion request enters the Ralph
  loop after ordinary planning has produced a validated complete ready Ticket
  set. Orchestration is live but event-driven rather than frozen or repeatedly
  rechecked: when an actual new user/canonical scheduling delta appears, the owning
  role applies only that delta to affected future work. With no new delta there is
  no extra full-conversation reread or freshness-agent call. Product-meaning deltas
  still return to planning instead of being smuggled through scheduling.
- `repo-snapshot/`: independent Git working-tree snapshot skill; its credential
  remains outside this repository at `/home/user01/.config/repo-snapshot/token`.

The component directories are plain tracked directories. They do not contain
nested Git repositories; versioning is owned by this repository root. IIS does
not use a controller database, persistent Goal state, attempt ledger, event/replay
engine, or generic workflow DSL for Ralph fulfillment.
