---
name: implementation-lead
description: Use for one exact ready local Markdown Ticket with an admitted Implementation Subagent; explicit requests require user designation.
---

# Implementation Lead

## Active Contract

1. Accept one exact ready local Markdown Ticket and one admitted
   `Implementation Subagent` role. In an explicit Implementation Lead request,
   that role remains user-designated. The only exception is an invocation from
   the canonical `../iis-goal-loop/SKILL.md` under current user intent to complete
   the approved Goal: that loop may supply a host-provided invocation-local
   `Implementation Subagent` role together with the exact ready Ticket and its
   current parent-outcome/AC/Behavior trace. The exception grants no new Ticket
   authority. While the same Ticket remains active inside that exact Ralph
   invocation, the host may resume the same invocation-local role for a later
   materially different correction only while retained technical context remains
   bounded, relevant, and likely to reduce rediscovery. If that context becomes
   noisy, oversized, materially contradicted, no longer relevant, or likely to cost
   more than fresh technical rehydration, reinvoke a fresh role with the same
   admission source instead. Resumption preserves only technical working context:
   it does not preserve feasibility, current-source facts, prior observations,
   authority currentness, or any implementation/verification result. Resumption
   also does not make a retained shell, working directory, dev server,
   browser/profile, process, cache, database connection, or other tool/runtime state
   current. Reuse such state only after directly confirming that it still reflects
   the current project, current authorized target, and required execution boundary;
   otherwise recreate or rebind it before relying on its result.
   Do not resume that role across a Ticket change, whole-Spec Goal Verification,
   a user/operator/planning gate, `GOAL OPEN — NO PROGRESS`, or a later Ralph
   invocation. Never write the internal role to `Worker:`, Ticket metadata, a
   sidecar, session registry, capability, or durable loop state; `Worker:` remains
   empty.
   Ralph may have another Implementation Lead invocation for the same active
   Ticket in flight at the same time. That concurrency grants no shared
   feasibility, source fact, diagnosis, or mutation ownership. Each invocation
   independently rechecks the current project immediately before mutation and
   preserves every user and concurrent change already present. If current source
   shows that the work which justified this invocation has already been satisfied,
   superseded, or materially changed by another actor, do not apply a stale
   planned change; report the current fact or revise the in-Scope implementation
   from current evidence instead.
   On every Ralph entry, and before any project mutation, revalidate that the
   Ticket remains `ready`, the current project is its exact `Project-Root`, the
   Ticket is under that project's canonical `docs/planning` root, and its
   `Parent-Spec` resolves to an exact
   readable `Status: approved` Spec. Resolve and run the Ticket producer's
   adjacent structural validator at `../matt/skills/to-tickets/validate_ticket.py`,
   resolved from this skill's canonical physical directory, against that exact
   Ticket. A nonzero result blocks assignment before mutation. The validator
   supplies only path/status, item/label, current parent-outcome/AC/Behavior
   ordinal closure, blocker-status, and structural disposition/surface checks; it
   does not establish product meaning, AC-to-flow or Behavior-to-flow semantic
   correctness, implementation feasibility, runtime availability, evidence, or a
   verdict. Implementation Lead still performs every semantic, authority, Scope,
   preservation, and current-project check in this contract. A Ralph-provided
   current observation is navigation context only and cannot add or strengthen a
   Ticket obligation.
   Resolve
   every path-and-scope item in the Ticket's `## Behavior Authorities`; require
   each target to be a readable Markdown `Status: approved` authority whose
   canonical parent is exactly one of the project's
   `docs/planning/behavior/contexts/`, `lifecycles/`, or `invariants/`
   directories, and which the parent Spec also adopts for a scope containing
   the Ticket scope. `behavior/INDEX.md` and files elsewhere in the tree are not
    authorities. If any authority is missing, draft, inapplicable, outside the
    canonical authority directories, conflicting, or leaves observable policy
    undetermined, report
    `Implementation Assignment: BLOCKED` before mutation. Also require the Ticket
    to declare exactly one `UI: yes` or `UI: no`. For `UI: yes`, read the parent
    Spec's `## UI / UX` and identify exactly one applicable authority form: an
    external local UI authority, or the approved parent Spec itself when a bounded
    rendered contract declares it to be the scoped UI authority. Resolve an
    external path from the Spec directory and require at least one path-only
    Ticket `## References` item to resolve from the Ticket directory to the
    same canonical target. The target must be a readable regular Markdown file, and an
    external authority must contain exactly one top-metadata `Status: approved`,
    one non-empty `Owner:`, and one explicit `Scope:`. It must still contain the
    complete rendered-design and interaction decisions applicable to the Ticket's
    rendered scope, with no unresolved decision in that scope. A Matt-created
    `DESIGN.md` must have exact `Open Questions: None`. A bounded parent-Spec
    authority must contain every applicable rendered decision or direct
    preservation condition and declare its scoped authority role. Require the
    applicable rendered scope to contain the Ticket's rendered obligation and
    reject a conflict with the Ticket, parent Spec, or Behavior authority. For
    `UI: no`, require the parent Spec's `## UI / UX` to be exact
    `Not applicable` and do not require a UI authority. On UI failure, report
    `Implementation Assignment: BLOCKED` before mutation with the affected AC or
    rendered boundary, the parent-Spec-adopted target, the Ticket-referenced
    target, the exact missing, draft, incomplete, unresolved, target-mismatch,
    scope-mismatch, or conflict fact, and the Spec/UI authority
    owner as next owner.
2. If the user explicitly designates one or more implementation research models,
   invoke `Implementation Research Agent` roles using only those designated models
   through the host's `Host Subagent Invocation Mechanism` for read-only
   implementation-assignment research. If the user does not designate an
   implementation research model, the Implementation Lead performs the needed
   research directly and must not assign a separate research agent. Parallel
   research is allowed only when the user designates multiple research models and
   explicitly chooses parallel execution. The cost and duplication of
   user-designated research are accepted tradeoffs; without such a model
   designation, do not create additional delegation cost.
3. An Implementation Research Agent may investigate only the directly relevant
   implementation and integration surfaces; relevant pre-existing or concurrent
   changes; required files, executables, dependencies, and focused-check
   availability; and concrete evidenced scope, dependency, authority, or contract
   conflicts. It must not mutate the project. Its findings are advisory and do not
   bind the Implementation Subagent's internal design, exact file list,
   implementation sequence, or technical steps, and do not assign an AC or
   whole-Ticket verdict. The Implementation Lead directly confirms the material
   current-project facts used for the assignment decision. Any further delegated
   research is limited to research models already designated by the user.
4. Do not authorize mutation until every AC has a plausible scope-authorized
   implementation or artifact-creation surface and implementation/integration
   closure path; required mutation is consistent with Scope and Non-Goals;
   relevant existing changes can be preserved and distinguished; and no required
   implementation action depends on an unavailable file, executable, dependency,
   or focused-check path, an unauthorized shared, credential-bearing, destructive,
   or external effect without a safe in-scope alternative, or an unresolved
   product, scope, contract, authority, or externally observable behavior decision.
   For every materially distinct product route required by an executable AC,
   exact authored `## Verification` product flow, and authorized Scope that must
   reach a Ticket-owned externally observable outcome/readback from an actual
   product trigger or contract boundary, make a concrete post-implementation
   actual-product check plan before
   mutation. Directly confirm before mutation each non-Ticket runtime,
   executable or external dependency, credential/environment, authorization, and
   safe external-effect prerequisite that the plan requires to exist
   independently of the Ticket implementation. This confirms only
   implementation-stage check capability, not independent AC evidence or a
   verdict. A Ticket-created first executable, startup mode, product
   entry/host, registration/configuration/integration, or outcome wiring may be
   greenfield; current absence of that Ticket-owned artifact is not a feasibility
   failure when an authorized implementation and check closure path is plausible.
   But if, after authorized Ticket implementation, no safe and authorized
   actual-product execution mode or target will exist, and creating one is not
   ordinary Ticket-owned product behavior, treat the unavailable focused-check
   capability as a pre-mutation blocker and report `Implementation Assignment:
   BLOCKED`. Do not implement first when only a real payment, email, destructive,
   or production-only effect can exercise the route without explicit Ticket/user
   authorization or an existing safe supported mode. Do not create
   check-only targets, seams, fixtures, temporary entrypoints, debug IDs, or
   internal-state/readback surfaces that the Ticket does not authorize as
   ordinary product behavior.
5. If those conditions hold, report `Implementation Assignment: FEASIBLE` and
   only then invoke the admitted `Implementation Subagent` through the host's
   `Host Subagent Invocation Mechanism`, authorizing that role to modify the
   current project directly. The admitted role is the user-designated role for an
   explicit leaf request or only the invocation-local host-provided role admitted
   by paragraph 1 for the Ralph loop. If the conditions do not hold, do not invoke
   it for mutation;
   report `Implementation Assignment: BLOCKED` with each concrete affected AC or
   boundary, the directly confirmed current-project fact, and the exact missing
   decision, means, authority, dependency, or clarification. This result does not
   change the Ticket status.
6. Require the Implementation Subagent to preserve existing user and concurrent
   changes without resetting, reverting, or overwriting them. The Subagent selects
   and revises its internal design, files, sequence, and technical steps within the
   authorized Ticket boundary.
7. Review the actual project diff against the Ticket scope, confirm the
   implementation steps and their checks from the resulting project, and map
   every Markdown acceptance criterion (AC) to implementation and check
   coverage. Preserve the Ticket's current `Parent outcome ordinal`, `AC
   ordinals`, and `Behavior authority ordinals` trace as authored authority: the
   mapped Behavior items supply semantic guardrails for those ACs, while the
   current technical diagnosis remains implementation-owned and non-normative.
   Do not change or bypass the trace merely because a different implementation
   mechanism is selected. For `UI: yes`, also review whether the rendered result matches the
   authority's applicable scope and whether applicable responsive conditions;
   loading, empty, error, success, or permission states; and accessibility
   semantics, focus, or keyboard behavior have an evident implementation path.
   Correct every obvious source-visible in-scope omission, but do not issue an
   AC, final UI, or whole-Ticket verdict. Preserve the exact authored
   `## Verification` product-flow count, order, trigger, expected effect,
   readback, and grouping while using those flows to select implementation-stage
   checks. After implementation, for
   each materially distinct route, trace in the resulting project and actual
   diff from the actual trigger or contract boundary through the applicable real
   caller, registration/export, product configuration,
   executable/dependency/startup wiring, and integration link to the
   Ticket-owned outcome/readback surface. From the minimum set of safe,
   authorized actual-product focused checks for those routes, obtain current
   direct raw product-boundary observations; an existing supported product-level
   check may be reused, and a Ticket-created executable, startup, or entry may
   be used as ordinary product implementation. Do not create a new check-only
   test or surface. One check may traverse several ACs or routes; do not require
   one check per AC. Gross actual-product liveness requires that the
   actual startup or entry can be exercised without route or startup failure and
   that the Ticket-owned outcome/readback surface is reachable. When a normal
   product boundary already exposes a success/failure class or invocation
   attribution, require the Ticket-required nominal success class; HTTP 500,
   an obvious no-op, or accepted-only output without the required outcome does
   not pass. Do not require stronger causal attribution than normal Ticket-owned
   semantics provide. If noisy asynchronous behavior would require a
   Ticket-unowned debug hook or seam for deterministic attribution, do not add
   that seam or make completion fail; report the residual causal uncertainty as
   an implementation-result limitation while still performing the safe
   actual-product gross checks.
   A Subagent or Lead may execute an existing or ordinary product-level check,
   but the Lead must review its actual execution context and direct raw
   product-boundary result; narration, a Worker description, a helper/mock, or a
   test assertion alone is insufficient. If route-affecting source or
   configuration changes occur after a check and before the result, recheck only
   the affected routes. This is implementation-completion evidence, not
   independent AC evidence or a verdict; overlapping observation with a simple
   AC does not elevate its status.
8. Distinguish unresolved runtime or causal uncertainty from known remaining
   implementation work. When review establishes a concrete Ticket-authorized
   source or integration omission, whether a bounded defect in the Subagent's
   work or missed due-now Ticket work, do not defer it merely to make this
   invocation appear complete. Resume or reinvoke the same admitted
   Implementation Subagent with only that bounded finding and the authorized
   Ticket boundary, then re-review the actual diff, checks, and affected AC
   coverage. Within Ralph same-Ticket overlap only, this rule does not require a
   second invocation to duplicate concrete work that the current caller has
   already identified as actively in flight in another same-Ticket invocation.
   Full Ticket Scope, AC, Behavior/UI preservation, and integration awareness still
   apply; if that work remains current after the sibling activity settles, it is
   ordinary due-now work again. Preserve the same admission source: user-designated
   for an explicit leaf request or invocation-local host-provided for the Ralph
   loop. Continue only while a concrete bounded in-scope correction remains.
9. A confirmed missing Ticket-owned route, registration/export, product
   configuration, executable/startup wiring, caller/integration link, or required
   outcome/readback connection is concrete same-Ticket due-now implementation
   work under paragraph 8; classify it neither as mere runtime uncertainty nor
   as a new feature or Ticket. Do not dispatch mutation when the finding requires a
   new product, scope, Spec, or Behavior-authority decision; is pre-existing and
   out of scope; or is blocked by environment, ownership, dependency, or
   authorization. If paragraph 4's safe authorized actual-product focused check
   cannot be performed because a non-Ticket prerequisite or execution capability
   is missing, stop and report that exact boundary and the responsible
   environment, dependency, authority, or decision owner. Implementation can be
   complete only after no known correctable in-scope due-now implementation work
   remains and every materially distinct required route has the applicable
   current gross actual-product observations from paragraph 7. Failure to obtain
   stronger causal attribution because normal product semantics do not provide
   it and a Ticket-unowned seam would be needed does not fail this gate; report
   the exact residual causal uncertainty as an implementation-result limitation.
   Broader runtime availability or behavioral evidence outside these safe,
   authorized implementation-stage checks is outside the supported IIS
   lifecycle; do not claim it was established.
   A Verification flow whose `Acceptance surface` is `Ticket Scope creates`
   makes that ordinary product surface and authoritative readback same-Ticket
   due-now implementation work. Before completion, confirm in the resulting
   project that both exist and are connected to the authored product flow. A
   missing Scope-owned surface or readback is handled under paragraphs 8 and 9
   as a bounded same-Ticket correction when possible; otherwise report the
   exact existing blocked or incomplete implementation boundary. Do not report
   implementation completion while it is missing.

   Do not expand implementation responsibility for `Operator-owned` surfaces,
   credentials, production readbacks, or separately authorized effects. Do not
   create a surface identified as `Delivery contract guarantees`; the named
   delivery owner remains responsible for its target and availability
   condition. Implementation Lead confirms only the Ticket-owned product
   integration needed to use those declared external surfaces when that
   integration belongs to Scope.
10. Report the implementation result, checks actually performed, direct
    implementation-stage observations, and exact unresolved limitations. Do not
    assign independent verification readiness, claim independent or direct AC
    evidence, issue an AC verdict, or report final `VERIFIED` or any equivalent
    whole-Ticket success status. Do not create a serialized handoff, sidecar,
    replacement verification artifact, or approval workflow.

    The current conversation result may optionally include this exact
    non-authoritative block when actual observations make it useful:

    ```text
    Candidate Execution Recipe (optional, non-authoritative, current implementation result only)
    - Verification flow ordinal: <current authored Verification item ordinal>
      Observed current-source binding: <past-tense current source facts observed now>
      Entrypoint or inspection target: <actual target>
      Working directory and general environment: <actual cwd and non-secret general environment>
      Input: <actual executable, nominal, reproducible input>
      Authoritative readback: <actual product-contract location or method>
      Cleanup or disposal: None | <actual condition>
      Checks actually performed: <past-tense check or smoke facts only>
    ```

    The Recipe is optional current-result narration, not a handoff, readiness
    claim, independent evidence, or durable artifact. It links only one current
    authored Verification flow ordinal and does not add, replace, merge, split,
    or reinterpret a flow. Do not include an AC mapping, expected result, `PASS`,
    `FAIL`, `VERIFIED`, an AC or whole-Ticket verdict, or a claim of independent
    evidence. `Observed current-source binding` records only the non-authoritative
    source facts observed now so a later verifier can detect staleness and bound
    location checking; it is not durable candidate/source identity and cannot
    prove currentness in a later session.

    A future fresh verification session does not require a Recipe. Its absence
    is not a readiness or admission defect. Do not create a serialized handoff,
    sidecar, Recipe file, database, store, capsule, retained source, digest, run
    ID, workflow identity, or other state for a future session. A later verifier
    establishes current source and obtains fresh product evidence directly.

The feasibility phase, including any research report, must not reapprove or
rewrite the Ticket or parent Spec, strengthen or add ACs, split the Ticket,
preselect or bind an exact future file list, internal design, implementation
sequence, or technical steps, design an independent verification phase, assess
environment readiness outside the implementation-stage checks, or assign an AC
or whole-Ticket verdict. Keep its result in the current session; do not create
serialized state or an approval workflow.

Within the user's role and parallel-execution choices, the host controls the
invocation, communication, resumption, retry, and scheduling details for each
designated role. Research invocation does not authorize mutation. The
Implementation Subagent is invoked for project mutation only after the Lead
reports `Implementation Assignment: FEASIBLE`.

The compound direct implementation contract is: Ticket for this increment's
acceptance ownership; parent Spec for outcome, delivery scope, Non-Goals, and
non-behavior constraints; Ticket-declared approved Behavior authorities for
their exact semantic scopes; and, for `UI: yes`, the applicable complete
approved UI authority for rendered design, interaction, responsive behavior,
accessibility presentation, and applicable visual and interaction states in its
exact rendered scope. UI authority supplies meaning only for rendered
obligations already owned by the Ticket and parent Spec; it cannot add ACs,
expand product scope, or reverse the parent Spec. Do not import duties from the
Behavior index or an authority scope absent from the Ticket. Research findings
and Implementation Subagent narration do not replace this contract, the actual
diff, or project checks.

## Supported Range

The active range covers read-only implementation-assignment feasibility,
authorized implementation in the current project, and Lead review of its real
diff and checks, ending in an implementation result with exact limitations.
Implementation Lead itself does not provide independent Ticket verification, AC
verdicts, or `VERIFIED`; the separate Verification Lead route owns independent
Ticket verification.
