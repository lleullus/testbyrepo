# Adaptive Artifact and Provenance Contract

## Canonical IIS artifacts remain canonical

Adaptive Planning creates and updates the **same canonical IIS artifacts** that the current Baseline would create for the same approved product meaning.

Examples include, as applicable:

- `SCOPE-SHAPING-RESULT.md`
- immutable Scope revisions
- Work Package records
- selected/superseded Increment records
- project-local Behavior authorities
- applicable UI/UX authority
- `SPEC.md`
- `TICKET-NNN.md` files
- current canonical validator outputs/results

The exact paths, metadata, headings, statuses, and validation requirements belong to current Baseline IIS. Do not redefine them here.

## Canonical status meaning remains Baseline-owned

Adaptive does not invent statuses such as `auto-approved`, `adaptive-approved`, or `superseded` for artifact types whose current Baseline schema does not provide them.

When standing delegated confirmation validly resolves a genuinely user-owned planning decision, write only the canonical Baseline status that decision normally permits, record the delegated provenance in the Adaptive companion trace, and never add a fake direct-user approval quote or unsupported metadata field.

When current Baseline To Spec/To Tickets self-review adopts a faithful structural projection as `approved` or `ready`, preserve that Baseline meaning without manufacturing `DELEGATED_RECOMMENDATION` provenance merely because Adaptive is active. This keeps canonical consumers compatible and keeps the Adaptive trace limited to material Adaptive decisions.

## Invocation-local Run Contract

The compact form in [../templates/ADAPTIVE-RUN-CONTRACT.template.md](../templates/ADAPTIVE-RUN-CONTRACT.template.md) closes one invocation's Goal Outcome, Required Named Items, Candidate Named Items, Required Item Policy, independent Implementation/Verification fields, Delivery Model Selection, Run Completion Boundary, Completion Predicate, and Authoritative Readback.

It is invocation-local authority, not a canonical IIS artifact and not a required third durable companion artifact. Do not add the form to canonical IIS artifacts, create a project-local workflow-state file for it, or use it as an attempt ledger.

Carry the closed form and relevant Source Authority anchors in the current request/context; pass only decision-critical fields and applicable actual user constraints across ownership boundaries under `09-run-contract.md`. Do not propagate only a derived Goal summary or copy the entire conversation into every Ticket. Trace only a material closure/revision or Goal/contract recovery and its source basis when later interpretation needs it, not routine transitions, progress, or every rendering.

Delivery model/effort selections and their user-confirmation basis stay in that invocation-local form and the relevant delivery assignments. The replaceable model guide is an operational recommendation reference, not a canonical product artifact, planning Source Authority, persistent worker roster, or permission to change models. Do not duplicate its ranking tables or encode selected models in Spec/Ticket metadata.

Execution plans are derived method artifacts, normally under the work slug's `plans/PLAN-NNN.md`, not canonical product authority or Adaptive state. Current `iis-plan-review/v2` is the independent reviewer's exact outside-Project-Root handoff, preserving rationale, projection, findings, evidence limits, conditional scope and current plan/Ticket/authority identities. Carry the original result/path and digest unchanged as `plan_review_path`; do not synthesize approval, search for latest reviews, rewrite findings from a summary or migrate historical v1 approval automatically. File currentness and declared consistency do not authenticate the reviewer or establish semantic sufficiency.

Implementation material-method terminal reports, verifier terminal semantic results, and caller finalization results are invocation-local delivery messages. They are not canonical IIS artifacts, Adaptive companion artifacts, trace events by default, progress heartbeats, worker/session IDs, or workflow state. Preserve only the exact handoff evidence needed by the current invocation. If such a result exposes a material authority fact that changes routing, record the resulting route after the exact owner/finalizer result exists; do not persist delivery control state as new provenance machinery.

## Companion provenance artifacts

Use companion artifacts only to preserve Adaptive-specific authority/provenance that does not belong in canonical IIS schema.

Recommended location once one exact project root exists:

```text
<Project-Root>/docs/planning/adaptive/<planning-slug>/
├── ADAPTIVE-PLANNING-MANDATE.md
└── ADAPTIVE-PLANNING-TRACE.md
```

Choose `<planning-slug>` from the bounded Adaptive initiative/work context. Prefer the current Scope slug when one already exists. Do not reuse the directory as a workflow database or attempt ledger.

If the project already has an established equivalent planning-provenance location, use it only when that convention is clearly applicable and does not alter canonical IIS paths.

### `ADAPTIVE-PLANNING-MANDATE.md`

Use [../templates/ADAPTIVE-PLANNING-MANDATE.template.md](../templates/ADAPTIVE-PLANNING-MANDATE.template.md).

It records current user-authorized decision criteria and the maximum Continuation Authority ceiling. It is Adaptive authority, not product source code, implementation authority, an invocation terminal, or a replacement for Scope/Behavior/Spec.

### `ADAPTIVE-PLANNING-TRACE.md`

Create it only when there is a material Adaptive event worth preserving. Use [../templates/ADAPTIVE-PLANNING-TRACE.template.md](../templates/ADAPTIVE-PLANNING-TRACE.template.md).

Material events:

- a `DELEGATED_RECOMMENDATION` that materially affects observable product meaning;
- a material standing-delegated user-owned planning decision whose provenance affects later interpretation;
- a material Run Contract closure/revision whose Goal fidelity, required/candidate classification, delivery stages, or completion semantics affect later interpretation, including recovery of an omission or weak Predicate from actual source authority;
- INC split/merge/reorder/replace/defer/drop/foundation insertion/supersession;
- verification triage that changes the owning route;
- success re-entry that selects `NEXT_INCREMENT_REQUIRED`, returns `EVIDENCE_REQUIRED`, or establishes `RUN_CONTRACT_SATISFIED`;
- a Return-to-User decision and its later resolution;
- a material Mandate revision.

Do not record:

- private chain-of-thought;
- every tool call/search/read;
- routine validator reruns;
- retry counters;
- agent/model roster state;
- implementation task lists;
- speculative future source paths;
- progress/status heartbeat entries.

## Trace entry minimum

A material trace entry should be small and auditable:

```text
### <sequence> — <short decision>
Provenance: USER_EXPLICIT | DELEGATED_RECOMMENDATION | INHERITED_AUTHORITY | STRUCTURAL_PROJECTION
Authority: <Mandate revision + exact canonical parent authority as applicable>
Evidence: <short primary evidence anchors or None>
Decision: <what planning meaning changed or was confirmed>
Reason: <why current authority selected it>
Affected canonical artifacts: <paths or None>
Re-entry / next leaf: <Scope Shaper | Ask Matt | To Spec | To Tickets | terminal | user>
```

Do not add persistent decision IDs to canonical Scope/Spec/Ticket documents.

## Lineage separation

Canonical IIS lineage remains authoritative for planning history:

- immutable Scope revisions show shaping history;
- Increment `Source-Scope-Revision` shows the authority that selected it;
- `Source-Increment` links Spec to the current shaped Increment;
- Parent Spec and positional verification mappings link Tickets.

Adaptive trace explains **why Adaptive changed/confirmed the planning shape**. It must not duplicate or replace those canonical relationships.

## Reshape artifact handling

When reshaping:

1. use current Scope Shaper to produce the next canonical revision/Increment relationship;
2. preserve immutable prior revisions;
3. preserve prior work artifacts as historical evidence;
4. invalidate/re-draft only affected unfinished downstream artifacts when current Baseline rules provide that transition;
5. never invent a new status solely for Adaptive lineage;
6. record old/new canonical paths in Adaptive trace.

If the replacement current INC has a new required unique work slug, create its new canonical work artifact workspace. Do not overwrite the old work slug to make history look continuous.

## Verification-result lineage

Keep verifier evidence/verdict separate from planning correction.

If a verification failure triggers planning correction:

```text
Old verifier result: remains exactly what it was
Old planning artifact: preserved under its current/historical canonical meaning
Adaptive triage: recorded in companion trace
New/changed planning artifact: validated fresh
Future verification: fresh evidence required
```

Never edit an old failure into PASS because the contract was later reshaped.

## No project root

When current Baseline allows unrooted greenfield shaping, keep Mandate/provenance in the current conversation until one exact intended project root exists. Do not create an external fallback Scope/Matt/Adaptive workspace. The independently authorized Thesis source alone uses the exact temporary location defined by product-thesis; it is not a Project Root and does not release downstream gates.

When the root appears, write the companion artifacts and recheck actual evidence before treating prior provisional planning as durable.
