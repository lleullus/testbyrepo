# Scope-Level Initialization Admission

## Classification

Apply this reference when current repository inspection establishes:

```text
current Ticket scope lacks required target readiness
AND completing the Ticket requires first product/package/application artifacts
```

Ticket wording such as `greenfield`, `initialize`, or `bootstrap` is not a
trigger. Product-root emptiness is not a trigger. An existing monorepo may have
a scope-local initialization, while an empty documentation-only root is not
product initialization. Matt's earlier source-absence observation is context;
Implementation Lead rechecks current readiness at invocation time.

The exact Ticket `Project-Root` must already be one canonical accessible
directory. Neither planning nor Implementation Lead creates that root before
Baseline Capsule and ownership preflight.

## Planning Authorization Interface

Before Worker dispatch, establish from the ready Ticket and approved parent
Spec:

1. Initialization scope authority: first product artifacts may be created in
   this exact planning scope.
2. Applicable external decisions: every caller-, registry-, deployment-,
   persisted-contract-, or operating-environment-facing identity and every
   intentionally fixed runtime, toolchain, deployment, or operational
   constraint is resolved, including an explicit statement when none applies.
3. Remaining bootstrap decision disposition: every remaining material choice
   is fixed or, when a choice remains, explicitly delegated to Implementation
   Lead/Worker. If every material choice is fixed, no delegation is applicable
   or required.

These facts are contextual clauses in the existing Spec/Ticket sections, not
new `Initialization:`, `Planning-Root:`, or bootstrap-manifest metadata. The
Ticket must trace them to the Spec and cannot invent a technical value or
delegation.

Initialization scope without mutation authority, an unresolved applicable
external decision, or a remaining material choice with neither a fixed value
nor explicit delegation is `BLOCKED` before Worker dispatch. A missing or
noncanonical project root follows ordinary root preflight and is `BLOCKED` for
the user or repository/environment owner.

## Implementation-Owned Mechanics

Apply fixed product/operational constraints and repository-authoritative
conventions first. Within the fixed choices and, only where choices remain, the
approved delegation, select one current initialization task and freeze its exact
allowed/forbidden paths, dependencies, completion condition, and mutation
envelope from current repository state. The ready Ticket does not need an exact
future file list.

Private toolchain, private package/module identity, dependencies, and minimal
source/config/test arrangement are implementation choices only when the Spec
delegates remaining bootstrap choices and no external contract consumes them.
Create only the minimum artifacts required by the approved outcome and
verification. A private identity being unspecified is not a blocker under that
delegation.

Bootstrap delegation does not authorize network access, package publication,
global tool installation, credential use, external resource creation, or Git
HEAD/index/branch/remote mutation. Such effects require their own authority. If
authorized but the required local capability is unavailable, return
`INCOMPLETE`; if not authorized, return `BLOCKED` before the effect.

Before the initialization Worker, create the ordinary pre-mutation Baseline
Capsule and immutable ownership snapshot. Preserve every pre-existing user
file, planning input, pre-existing or concurrent `.scratch/**` path, and Git
control state. Do not globally exclude `.scratch/**` or use planning artifacts
as product mutation inputs.

## Review And Reclassification

After the Worker, inspect every created path, external/public export identity,
lockfile and dependency provenance, caller, Canonical, test, and integration
boundary. Confirm post-initialization target readiness and then join the
ordinary source review, final representative runtime observation, and v3 result
flow.

If source or a manifest appeared after planning, preserve it and classify the
current scope again. Do not enforce a stale emptiness assumption. Continue by
ordinary task selection when current authority remains clear and the outcome is
still safely achievable; return `BLOCKED` when current source and planning
authority conflict in a way the Lead cannot resolve without product policy.

If current target readiness already exists, use the ordinary brownfield flow.
Do not apply this reference merely because the Ticket mentions initialization.

## Admission Decision Matrix

The following language-neutral scenarios fix the branch before any Worker or
external effect. They are pilot fixtures, not claims that a Markdown skill can
mechanically infer product meaning.

| Scenario | Current facts | Disposition |
| --- | --- | --- |
| `all-fixed-no-delegation` | Target readiness is absent; initialization authority and applicable external decisions are resolved; every material bootstrap choice is fixed; no choice remains to delegate. | `ADMIT_INITIALIZATION` |
| `delegated-private-choice` | Target readiness is absent; initialization authority and applicable external decisions are resolved; remaining private choices are explicitly delegated. | `ADMIT_INITIALIZATION` |
| `missing-initialization-authority` | Target readiness is absent and first product artifacts are required, but initialization mutation authority is absent. | `BLOCKED` before Worker dispatch. |
| `unresolved-bootstrap-disposition` | A material bootstrap choice remains neither fixed nor delegated. | `BLOCKED` before Worker dispatch. |
| `unauthorized-external-effect` | Bootstrap would require network access, publication, global installation, credentials, or external resource creation without separate authority. | `BLOCKED` before that effect. |
| `root-not-ready` | The exact `Project-Root` is absent, noncanonical, or inaccessible. | `BLOCKED`; neither planning nor Implementation Lead creates it. |
| `brownfield-ready-scope` | Current target readiness already exists in the Ticket scope. | `ORDINARY_FLOW`; do not apply initialization admission. |
| `documentation-only-empty-root` | The root lacks product artifacts, but Ticket completion creates documentation only. | `ORDINARY_FLOW`; root emptiness is not initialization. |
| `scope-local-initialization` | The repository is nonempty, but the Ticket scope lacks target readiness and requires first package/application artifacts. | Apply the same initialization authority and disposition gates; root non-emptiness does not bypass them. |
