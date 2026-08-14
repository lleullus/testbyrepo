---
name: iis-workflow
description: Canonical entry router for IIS planning leaves, explicit implementation/verification leaves, and Ralph-style end-to-end Goal fulfillment.
---

# IIS Workflow Router

## Purpose

Route the user's requested completion unit without changing the meaning or
terminal boundary of any IIS leaf. Planning remains Scope Shaper / Ask Matt / To
Spec / To Tickets. Explicit one-Ticket implementation and verification remain
independent leaves. End-to-end product completion uses the Ralph Goal Fulfillment
Loop only after ordinary planning has produced one exact approved Spec and a
validated complete ready Ticket set.

The router carries only current-conversation intent. This includes any explicit
user designation of an `Adversarial Planning Challenger`, `Implementation
Subagent`, `Implementation Research Agent`, or `Verification Runner` role and
any explicit ordering, reservation, consumption timing, or maximum-concurrency
condition attached to that role. An `Adversarial Planning Challenger` binding is
separate from the user's explicit instruction to run adversarial consensus; one
never implies the other. Preserve those bindings and conditions as authored
instead of reinterpreting a configured model as a different role or consuming a
role at a different phase. Authored ordering is reusable dispatch precedence
unless the user explicitly makes a binding one-shot, usage-limited, rotational,
reserved, withdrawn, or otherwise ineligible; prior invocation alone does not
consume or demote it.
Model identity alone is not a role: using the same configured model/agent for a
different IIS role requires a separate user designation for that role. An owning
Lead may decide only role grouping, count, timing, concurrency, or serial fallback
that the user did not already fix. These are current-conversation routing
constraints only; the router does not create workflow state, persist a mode or
roster, invent Tickets, or reinterpret product authority.

Treat those designations as request-scoped role bindings, not as a general pool
of interchangeable agents. Before every downstream invocation, first resolve the
IIS role required by the current protocol step, then consider only bindings for
that role, apply only the ordering/reservation/consumption/concurrency conditions
the user actually authored, and only then select an eligible assignee. Never
select an assignee first and reinterpret its role. A binding for one role is
ineligible for every other role unless the user separately designated that same
configured model/agent for the other role. Pass each downstream Lead only the
role bindings it may consume; this projection is invocation-local routing, not a
registry, quota, scheduler, or durable roster.

## Live Orchestration Authority

Do not freeze IIS orchestration to the user scheduling conditions or canonical
rules that were current when an invocation began. Live reconciliation is
**event-driven**, not a repeated proof-of-currentness ceremony. When a new user
orchestration instruction or coherent canonical IIS change is actually observed,
the current owning Router/Lead applies only the material scheduling delta from the
next controllable boundary. If no new instruction or contract change is observed,
continue without a new orchestration checkpoint. Do not poll or re-read the full
conversation at every control boundary, and do not invoke another agent merely to
prove that no newer instruction exists.

This live reconciliation changes orchestration, not product meaning. A newly
observed user direction may change role eligibility, ordering, reservation, exact
consumption, maximum concurrency, Challenger activation, or other scheduling
conditions. It does not retroactively erase prior work. Already-produced
source/product changes remain current state to reobserve. If the new direction
changes Outcome, Scope, Non-Goals, Behavior/UI meaning, an acceptance obligation,
or verification meaning itself, return to the owning planning authority instead
of disguising the product-contract change as scheduling.

A scheduling delta is prospective. Apply it to future duties and dispatch rather
than recreating preferred history. If continuing an in-flight invocation would
itself violate an exact current user instruction, stop assigning it new duties and
request stop at the earliest host-controllable boundary; otherwise let its current
bounded action return and apply the delta to the next dispatch. Preserve current
user/concurrent changes either way. Before any progression that depends on affected
mutation, require ordinary quiescence and fresh current observation.

If the host knows a newer direction exists but cannot observe its content, block
only the affected new dispatch, mutation authorization, or progression decision;
do not stall unrelated current work whose authority is unchanged. If a canonical
IIS update is partially applied or internally conflicting, fail closed only on new
dispatch/progression that depends on the conflicting rule until a coherent current
contract can be read; do not choose whichever old or new rule is more convenient.

## Route By Requested Completion Unit

Apply explicit leaf requests before broad IIS inference.

### Scope Shaping

An explicit Scope Shaper request or an initiative-scale IIS request routes to:

`/home/user01/project/iis-skills/scope-shaper/SKILL.md`

Scope Shaper has entry precedence for initiative-scale work. Respect its selected
Work Package and downstream planning boundary. Do not skip initiative shaping in
order to enter implementation or the Ralph loop sooner.

### Ask Matt / Planning

An explicit Ask Matt request, or an ordinary bounded IIS planning request, routes
to:

`/home/user01/project/iis-skills/matt/skills/ask-matt/SKILL.md`

Ask Matt owns product/Behavior/UI/completion-contract planning and invokes its
ordinary To Spec / To Tickets planning leaves under their existing contracts.
Those leaves stop at their own outputs. Planning approval does not itself mutate
the product.

Pass an explicit user instruction to run adversarial consensus for this exact
planning unit to Ask Matt even when its Challenger binding is still missing, so
Ask Matt can preserve the required `CHALLENGER BINDING REQUIRED` finalization
boundary rather than silently dropping the user's requested gate. Separately pass
an exact `Adversarial Planning Challenger` binding only when the user explicitly
designated it. Ask Matt may consume that binding through
`matt/skills/adversarial-consensus/SKILL.md` only when both the activation
instruction and exact binding are current. Do not suggest the gate, infer
activation from a Challenger designation, choose a missing Challenger, or pass the
binding to implementation or verification roles.

An explicit To Spec or To Tickets request routes only to that exact planning
leaf and stops there:

- `/home/user01/project/iis-skills/matt/skills/to-spec/SKILL.md`
- `/home/user01/project/iis-skills/matt/skills/to-tickets/SKILL.md`

An explicit To Spec request does not withdraw, satisfy, or bypass an active adversarial-consensus instruction. When routing, pass the current adversarial-consensus activation or withdrawal fact to To Spec together with any exact current Challenger binding already supplied in this conversation; To Spec owns the direct admission gate and must not infer missing completion. Do not infer end-to-end implementation from an explicit planning-only request.

### Explicit One-Ticket Implementation

An explicit request to implement one exact ready local Markdown Ticket routes to:

`/home/user01/project/iis-skills/implementation-lead/SKILL.md`

Require the exact Ticket and the Implementation Lead's ordinary explicit-leaf
inputs, including its user-designated Implementation Subagent role. Do not
silently convert an explicit one-Ticket implementation request into Ralph Goal
fulfillment. Implementation result is not an AC verdict or whole-Goal completion.

### Explicit Independent Ticket Verification

An explicit request to independently verify one exact ready local Markdown Ticket
routes to:

`/home/user01/project/iis-skills/verification-lead/SKILL.md`

Require the exact `Project-Root`. The Candidate Execution Recipe is optional and
non-authoritative. Do not require an Implementation Lead result, implementation
checks, prior evidence, or a prior verdict to begin a fresh valid verification
session.

This independent route requires fresh independent authority, direct evidence, and
an AC verdict from Verification Lead itself. A Ticket flow with
`Operator-assisted` or `Not independently verifiable` has no independent IIS
verification route. Do not bypass that boundary through Implementation Lead,
another agent, a compatibility command, or implementation checks instead of
selecting a fallback. Return the exact disposition boundary to the user or
calling workflow.

If the user supplied one or more `Verification Runner` roles or conditions for
this verification request, pass those exact current-conversation bindings to
Verification Lead. If the user supplied none, the verification leaf may use its
ordinary host-provided invocation-local Runner mechanism. Do not repurpose a
Verification Runner designation as implementation research or mutation.

### Explicit Whole-Spec Verification

An explicit request to verify whether one exact approved Spec is currently
complete as a whole routes to:

`/home/user01/project/iis-skills/goal-verification-lead/SKILL.md`

This is verification only. It does not remediate, start Implementation Lead, or
enter the Ralph loop unless the user separately requested end-to-end completion.
Pass any user-designated `Verification Runner` bindings and conditions unchanged
to Goal Verification Lead; absence of a user Runner designation does not create
new user ceremony.

### End-To-End Goal Fulfillment

A request whose requested completion unit is the actual product Goal — for
example, finish the feature/fix, keep going until the approved outcome works, or
complete an already approved Spec — routes to the Ralph loop:

`/home/user01/project/iis-skills/iis-goal-loop/SKILL.md`

If one exact approved Spec and its validated complete ready Ticket set already
exist, invoke the Ralph loop directly with that Spec and exact Project Root,
carrying any current-conversation Implementation/Verification role bindings and
their explicit consumption conditions unchanged.

If planning is still required, first run the same ordinary Scope Shaper / Ask
Matt / To Spec / To Tickets leaves above. Each planning leaf still stops at its
own normal boundary. When the top-level user request already clearly authorizes
end-to-end product completion, retain that current-conversation completion intent
and any explicit Adversarial-Planning/Implementation/Verification role bindings,
the separate adversarial-consensus activation instruction when present, and their
authored consumption conditions while planning executes, but do not invoke those
delivery or verification roles during planning merely because they were
designated. Also do not invoke a Challenger unless its separate activation
condition is present. After
the planning leaves return one exact approved Spec and a complete ready Ticket set
that passes the set validator, the router may enter the Ralph loop without asking
the user to say "continue", select a Worker, restate an already supplied role
binding, or approve an implementation mechanism again.

If the user requested planning only, do not enter Ralph after Tickets become
ready. If the approved Spec or Ticket breakdown needs a new product/scope decision
or normal Ticket review, obtain that planning decision through the ordinary leaf;
end-to-end intent does not bypass planning approval.

Ralph's supported completion unit is exactly one bounded approved Spec. For an
initiative-scale request, Scope Shaper still owns decomposition and selection of a
bounded Work Package. Ralph may complete that selected package's Spec, but the
router must not promote that package's `GOAL ACHIEVED` to completion of the parent
initiative, sibling Work Packages, or a multi-Spec release. Report remaining
initiative scope separately. Do not invent fan-in orchestration or silently reduce
an initiative-level completion request to the first bounded package.

## Ralph Completion Boundary

The Ralph loop owns iterative orchestration only. The approved Spec remains Goal
authority; Ticket ACs are observable work units; mapped Behavior authorities are
semantic guardrails. The loop may repeat the same ready Ticket across materially
different in-Scope corrections, but it may not widen Ticket Scope or dynamically
invent a new Ticket.

Only fresh whole-Spec `GOAL VERIFIED` from Goal Verification Lead permits the
router/loop to report `GOAL ACHIEVED`. Ticket readiness, implementation
completion, passing tests, `VERIFIED` for one Ticket, partial improvement, or a
current `NO PROGRESS` result never means Goal completion.

`GOAL OPEN — NO PROGRESS` is not terminal product impossibility. It ends only the
current attempt when no materially different authorized correction, direct
evidence path, operator action, or required product/scope decision remains in the
current invocation.

## User Decision Boundary

During end-to-end fulfillment, ask the user only for a real product, Scope,
completion-contract, or dangerous-authority decision. Do not ask the user which
endpoint, parser, retry/fallback policy, file, algorithm, implementation sequence,
Worker, or next in-Scope correction to use, and do not ask whether IIS should
continue to the next unfinished AC.

An exact approved operator-owned action may produce `OPERATOR ACTION REQUIRED`
with its exact environment/target and authoritative readback. The operator does
not interpret the AC or supply the verdict.

## Safety And Non-Goals

This router does not create a Controller runtime, workflow database, durable Goal
state, attempt ledger, gap registry, event log, replay engine, claim/capability
registry, persistent queue, or generic DSL. It does not turn agent investigation
misses into project-specific IIS core rules. Explicit leaf semantics stay valid
and take precedence over broad end-to-end routing.
