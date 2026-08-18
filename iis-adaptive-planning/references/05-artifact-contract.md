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

## Approval status meaning remains user-authorized planning authority

Adaptive does not invent statuses such as `auto-approved`, `adaptive-approved`, or `superseded` for artifact types whose current Baseline schema does not provide them.

When standing delegated confirmation validly satisfies an ordinary planning approval:

- write the same canonical status Baseline would write after direct approval (`confirmed`, `approved`, `ready`, etc. as currently defined);
- treat that status as user-authorized through the explicitly adopted Adaptive Mandate;
- record the different provenance in the Adaptive companion trace;
- never add a fake direct-user approval quote or unsupported metadata field.

This preserves downstream Baseline compatibility: canonical consumers continue to see the same complete planning authority, while the Adaptive trace explains how the confirmation was obtained.

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

It records current user-authorized decision criteria. It is Adaptive authority, not product source code, implementation authority, or a replacement for Scope/Behavior/Spec.

### `ADAPTIVE-PLANNING-TRACE.md`

Create it only when there is a material Adaptive event worth preserving. Use [../templates/ADAPTIVE-PLANNING-TRACE.template.md](../templates/ADAPTIVE-PLANNING-TRACE.template.md).

Material events:

- a `DELEGATED_RECOMMENDATION` that materially affects observable product meaning;
- standing delegated confirmation that advances a canonical artifact to a confirmed/approved/ready state;
- INC split/merge/reorder/replace/defer/drop/foundation insertion/supersession;
- verification triage that changes the owning route;
- success re-entry that selects `NEXT_INCREMENT_REQUIRED` or establishes `MANDATE_SATISFIED`;
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

When current Baseline allows unrooted greenfield shaping, keep Mandate/provenance in the current conversation until one exact intended project root exists. Do not create an external fallback planning directory.

When the root appears, write the companion artifacts and recheck actual evidence before treating prior provisional planning as durable.
