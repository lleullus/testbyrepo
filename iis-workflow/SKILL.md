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

The router carries only current-conversation intent. It does not create workflow
state, persist a mode, invent Tickets, or reinterpret product authority.

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

An explicit To Spec or To Tickets request routes only to that exact planning
leaf and stops there:

- `/home/user01/project/iis-skills/matt/skills/to-spec/SKILL.md`
- `/home/user01/project/iis-skills/matt/skills/to-tickets/SKILL.md`

Do not infer end-to-end implementation from an explicit planning-only request.

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

### Explicit Whole-Spec Verification

An explicit request to verify whether one exact approved Spec is currently
complete as a whole routes to:

`/home/user01/project/iis-skills/goal-verification-lead/SKILL.md`

This is verification only. It does not remediate, start Implementation Lead, or
enter the Ralph loop unless the user separately requested end-to-end completion.

### End-To-End Goal Fulfillment

A request whose requested completion unit is the actual product Goal — for
example, finish the feature/fix, keep going until the approved outcome works, or
complete an already approved Spec — routes to the Ralph loop:

`/home/user01/project/iis-skills/iis-goal-loop/SKILL.md`

If one exact approved Spec and its validated complete ready Ticket set already
exist, invoke the Ralph loop directly with that Spec and exact Project Root.

If planning is still required, first run the same ordinary Scope Shaper / Ask
Matt / To Spec / To Tickets leaves above. Each planning leaf still stops at its
own normal boundary. When the top-level user request already clearly authorizes
end-to-end product completion, retain only that current-conversation completion
intent while planning executes. After the planning leaves return one exact
approved Spec and a complete ready Ticket set that passes the set validator, the
router may enter the Ralph loop without asking the user to say "continue",
select a Worker, or approve an implementation mechanism again.

If the user requested planning only, do not enter Ralph after Tickets become
ready. If the approved Spec or Ticket breakdown needs a new product/scope decision
or normal Ticket review, obtain that planning decision through the ordinary leaf;
end-to-end intent does not bypass planning approval.

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
