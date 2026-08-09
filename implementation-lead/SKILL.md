---
name: implementation-lead
description: Use for one exact ready local Markdown Ticket with a user-designated Implementation Subagent.
---

# Implementation Lead

## Active Contract

1. Accept one exact ready local Markdown Ticket and one user-designated
   `Implementation Subagent` role. Before any project mutation, revalidate that
   the Ticket remains `ready`, the current project is its exact `Project-Root`,
   the Ticket is under that project's canonical `docs/planning` root, and its
   `Parent-Spec` resolves to an exact readable `Status: approved` Spec. Resolve
   every path-and-scope item in the Ticket's `## Behavior Authorities`; require
   each target to be a readable Markdown `Status: approved` authority whose
   canonical parent is exactly one of the project's
   `docs/planning/behavior/contexts/`, `lifecycles/`, or `invariants/`
   directories, and which the parent Spec also adopts for a scope containing
   the Ticket scope. `behavior/INDEX.md` and files elsewhere in the tree are not
   authorities. If any authority is missing, draft, inapplicable, outside the
   canonical authority directories, conflicting, or leaves observable policy
   undetermined, report
   `Implementation Assignment: BLOCKED` before mutation.
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
   For every materially distinct product route required by an executable AC and
   authorized Scope that must reach a Ticket-owned externally observable
   outcome/readback from an actual product trigger or contract boundary, make a
   concrete post-implementation actual-product handoff-check plan before
   mutation. Directly confirm before mutation each non-Ticket runtime,
   executable or external dependency, credential/environment, authorization, and
   safe external-effect prerequisite that the plan requires to exist
   independently of the Ticket implementation. This confirms only
   implementation handoff-check capability, not verification-only environment or
   scenario readiness. A Ticket-created first executable, startup mode, product
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
   verification-only targets, seams, fixtures, temporary entrypoints, debug IDs,
   or internal-state/readback surfaces.
5. If those conditions hold, report `Implementation Assignment: FEASIBLE` and
   only then invoke the user-designated `Implementation Subagent` through the
   host's `Host Subagent Invocation Mechanism`, authorizing that role to modify the
   current project directly. If they do not hold, do not invoke it for mutation;
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
   coverage. After implementation, for each materially distinct route, trace in
   the resulting project and actual diff from the actual trigger or contract
   boundary through the applicable real caller, registration/export, product
   configuration, executable/dependency/startup wiring, and integration link to
   the Ticket-owned outcome/readback surface. From the minimum set of safe,
   authorized actual-product focused checks for those routes, obtain current
   direct raw product-boundary evidence; an existing supported product-level
   check may be reused, and a Ticket-created executable, startup, or entry may
   be used as ordinary product implementation. Do not create a new verification
   test or surface. One check may traverse several ACs or routes; do not require
   one check per AC. Actual-product gross handoff-liveness requires that the
   actual startup or entry can be exercised without route or startup failure and
   that the Ticket-owned outcome/readback surface is reachable. When a normal
   product boundary already exposes a success/failure class or invocation
   attribution, require the Ticket-required nominal success class; HTTP 500,
   an obvious no-op, or accepted-only output without the required outcome does
   not pass. Do not require stronger causal attribution than normal Ticket-owned
   semantics provide. If noisy asynchronous behavior would require a
   Ticket-unowned debug hook or seam for deterministic attribution, do not add
   that seam or make completion fail; leave residual causal uncertainty for
   Verification while still performing the safe actual-product gross checks.
   A Subagent or Lead may execute an existing or ordinary product-level check,
   but the Lead must review its actual execution context and direct raw
   product-boundary result; narration, a Worker description, a helper/mock, or a
   test assertion alone is insufficient. If route-affecting source or
   configuration changes occur after a check and before handoff, recheck only
   the affected routes. This is implementation-completion evidence, not
   independent AC evidence or a verdict; overlapping observation with a simple
   AC does not elevate its status.
8. Distinguish verification-only uncertainty from known remaining
   implementation work. When review establishes a concrete Ticket-authorized
   source or integration omission, whether a bounded defect in the Subagent's
   work or missed due-now Ticket work, do not defer it to Verification Lead.
   Resume or reinvoke the same user-designated Implementation Subagent with only
   that bounded finding and the authorized Ticket boundary, then re-review the
   actual diff, checks, and affected AC coverage. Continue only while a concrete
   bounded in-scope correction remains.
9. A confirmed missing Ticket-owned route, registration/export, product
   configuration, executable/startup wiring, caller/integration link, or required
   outcome/readback connection is concrete same-Ticket due-now implementation
   work under paragraph 8; classify it neither as verification-only work nor as
   a new feature or Ticket. Do not dispatch mutation when the finding requires a
   new product, scope, Spec, or Behavior-authority decision; is pre-existing and
   out of scope; or is blocked by environment, ownership, dependency, or
   authorization. If paragraph 4's safe authorized actual-product focused check
   cannot be performed because a non-Ticket prerequisite or execution capability
   is missing, stop at that boundary and do not begin independent verification.
   Stop or report that exact boundary and next owner. Begin independent
   verification only after no known correctable in-scope due-now implementation
   work remains and every materially distinct required route has current gross
   actual-product handoff-liveness evidence from paragraph 7. Failure to obtain
   stronger causal attribution because normal product semantics do not provide
   it and a Ticket-unowned seam would be needed does not fail this gate; carry
   residual causal uncertainty to Verification. Broader runtime availability and
   direct behavioral runtime evidence remain Verification responsibility after
   this gate; source-review uncertainty that requires direct runtime evidence
   may still be reported to independent verification.
10. Report the implementation result and remaining verification-only ambiguous
    AC coverage as input to independent verification. In the current-session
    implementation result, include a nominated implementation-route index for
    each materially distinct required route: applicable ACs; the actual or
    Ticket-created startup/execution path; the actual product trigger or
    contract boundary; the Ticket-owned outcome/readback surface; the reviewed
    source/integration path; the focused actual-product check and observed
    gross nominal boundary facts; residual causal uncertainty; or an unresolved
    paragraph 9 blocker and next owner. This index is navigation only, not a
    runtime-readiness claim or independent AC evidence, and it must not
    constrain or reduce the Verification Lead's independent scenario design,
    runtime availability investigation, evidence acquisition, causal or
    behavioral correctness assessment, or verdict.
    The Implementation Lead must not report final `VERIFIED` status.

The feasibility phase, including any research report, must not reapprove or
rewrite the Ticket or parent Spec, strengthen or add ACs, split the Ticket,
preselect or bind an exact future file list, internal design, implementation
sequence, or technical steps, design independent verification scenarios, assess
verification-only environment readiness, or assign an AC or whole-Ticket verdict.
Keep its result in the current session; do not create a separate handoff file,
serialized state, or approval workflow.

Within the user's role and parallel-execution choices, the host controls the
invocation, communication, resumption, retry, and scheduling details for each
designated role. Research invocation does not authorize mutation. The
Implementation Subagent is invoked for project mutation only after the Lead
reports `Implementation Assignment: FEASIBLE`.

The compound direct implementation contract is: Ticket for this increment's
acceptance ownership, parent Spec for outcome/delivery scope/Non-Goals and
non-behavior constraints, and Ticket-declared approved Behavior authorities for
their exact semantic scopes. Do not import duties from the Behavior index or an
authority scope absent from the Ticket. Research findings and Implementation
Subagent narration do not replace this contract, the actual diff, or project
checks.

## Supported Range

The active range covers read-only implementation-assignment feasibility,
authorized implementation in the current project, and Lead review of its real
diff and checks. Independent verification remains the separate responsibility
of Verification Lead.
