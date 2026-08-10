# B Tier Adversarial Consensus

## Decision

B2 remains rejected. The former B1 no-change decision is superseded by the
bounded route-navigation cutover described below.

- B1 is **SUPERSEDED: BOUNDED ROUTE PROVENANCE AUTHORIZED** because cross-context
  producer provenance loss was observed and navigation-only session state could
  not preserve whether required implementation-stage checks were recorded.
- B2, relaxation or addition of legacy prose tolerance, is **REJECTED** as a
  runtime parser change. A bounded, one-shot, owner-confirmed migration may be
  proposed only for a named live compatibility population that satisfies the
  evidence gate below.

The S-tier and A-tier decisions remain unchanged and are not reopened by this
decision.

## Review Frame

- Default: preserve the current design.
- B-tier candidates have non-free lifecycle, compatibility, and authority
  costs; convenience alone is insufficient.
- Every Oracle turn received a fresh complete repository ZIP.
- B1 must prove repeated net efficiency after mandatory independent work is
  excluded.
- B2 must prove a live compatibility population and an authority-preserving
  finite migration boundary.

## B1: Superseded By Bounded Route Provenance

### Current Contract

The prior current-session-only contract is no longer active. Its concrete
failure was loss of route provenance across context boundaries, not merely
navigation inefficiency. The replacement is exactly one atomically replaced
`~/.iis/route-navigation/<ticket-key>.json` sidecar with strict filtered views:

- Primary receives only safe navigation fields after independent mapping and
  independently confirms source anchor digests.
- Verification Lead receives only quarantined redacted producer provenance and
  may answer only the past-tense provenance question.
- No AC mapping, readiness, direct evidence, verdict, or causal conclusion may
  cross either filtered view.
- Absence, malformedness, cleanup, staleness, or supersession remains ambiguous
  and never blocks Verification or proves omission.
- Seven-day terminal grace and thirty-day orphan ceiling are cleanup-only; TTL,
  file age, and mtime are never semantic freshness.

The sole writer and filtered readers are the artifact-specific APIs in
`iis_ephemeral_transport.py`. No raw, generic, list, inspect, history, replay,
recovery, latest, or current-head interface is authorized.

### Correct Characterization

The sidecar preserves bounded local transport and implementation-stage
provenance only. It is not verification authority, readiness, evidence, workflow
state, durable history, or a guaranteed producer record. Supersession replaces
the single slot and no prior producer run is retained.

## B2: Legacy Prose

### Final Disposition

Runtime legacy prose tolerance is rejected at both active authority boundaries:

1. Ticket Acceptance Criteria and Verification roots.
2. Scope Shaper results and Work Package structure consumed by Ask Matt.

No producer, parser, test, schema, compatibility branch, or fallback change is
authorized.

### Ticket Boundary

Current Ticket producers require exact top-level `- ` items and only
two-space-indented continuation lines. Ordered, task-list, nested-only,
prose-only, empty, and mixed-marker bodies are prohibited.

The denominator consumer is `verification-lead/coverage_gate.py::_top_level_items`
under the fail-closed Verification Lead contract.

#### Current Continuation Aperture

Producer and consumer grammars are not identical. After `_top_level_items` sees
one valid top-level `- ` item, a later nonblank line that is neither another
top-level item nor a recognized unsupported top-level marker is appended to the
preceding item without enforcing two-space indentation.

For example, current code accepts this as two roots, with the prose appended to
the first:

```markdown
- The CLI exits 2.
Legacy explanatory paragraph.
- Existing configuration succeeds.
```

This is recorded only as current parser behavior. It is:

- not proof of producer/consumer grammar equivalence;
- not a legacy compatibility guarantee;
- not authority for producers to emit mixed prose;
- not evidence supporting broader tolerance; and
- not modified by this B-tier decision.

The active-example contract test proves that the current template and active
examples parse. It does not prove grammar equality.

### Scope Boundary

`scope-shaper/tools/validate_scope_result.py::_items` accepts only exact `None` or
lines beginning with `- `. Mixed prose fails, and the existing scope-result test
directly preserves that rejection.

Ask Matt requires the canonical validator before planning. No named live
repository population has been identified that a current supported consumer
must read through a legacy prose grammar. Historical and archived material do
not create an active runtime compatibility requirement.

### Future Migration Gate

A future migration proposal requires all of the following:

1. Exact live local paths requiring migration.
2. The current supported workflow consumer that must use them.
3. The owner for each authoritative document.
4. One bounded and explicitly described legacy grammar.
5. Exact mapping from legacy items to current item count, order, and binding.
6. Every location where mapping is not syntactically one-to-one.
7. Owner confirmation for every ambiguous location.
8. Converted output that passes the unchanged current parser.
9. A finite population count and explicit zero-population removal point.
10. Confirmation that current producers no longer emit the legacy form.

Only a one-shot converter or manual migration may then be proposed. It must stay
outside the runtime parser, accept only the enumerated paths and grammar, and be
removed when the population reaches zero.

No indefinite runtime parser, fallback reader, dual grammar, unknown-version
tolerance, or current-producer legacy output may be proposed.

### Tradeoffs

Strict failure can impose migration friction. An older human-readable document
may require reformatting and renewed owner confirmation; the owner may be
unavailable; and a large population can make review expensive.

Those costs become actionable only with a named live population and current
consumer need. Owner unavailability does not make ambiguous automatic mapping
safe.

A one-shot migration is also non-free: inventory, ownership discovery, manual
review, population control, and removal can dominate conversion cost. It is not
pre-approved. Its advantage over runtime tolerance is only that population,
interpretation, ownership, and removal can be bounded before the current parser
accepts the result.

## Preserved Invariants

- S-tier receipt-reuse and single-approval decisions remain unchanged.
- The A-tier hierarchy-freshness correction remains unchanged.
- The route sidecar is one atomically replaced cross-context bounded local
  transport/provenance slot whose navigation semantics remain non-authoritative.
- The sidecar is not the Verification working model, a workflow database,
  planning or approval authority, or history.
- Verification independently decomposes the Ticket and confirms current source.
- Runtime Runner owns only raw readiness material; Primary Verifier owns its
  interpretation, adoption, and readiness semantics.
- Index absence, malformedness, staleness, or disagreement remains nonblocking.
- The index does not enter coverage, readiness, evidence, approval, or verdict.
- Ticket denominator roots remain validator-extracted top-level bullets.
- Unsupported or ambiguous authoritative structure remains fail-closed.
- Current producers continue emitting the canonical grammar.
- No runtime legacy fallback, dual reader, or indefinite compatibility parser is
  introduced.
- Static historical preservation does not become runtime compatibility.

## Non-Goals

- Cross-session Verification resumability.
- Persistence of the Verification working model.
- A project-local route-index file or workflow database.
- Source caching or evidence carry-forward.
- Machine-authoritative AC-to-route binding.
- Sentence splitting or semantic prose decomposition.
- Permanent ordered-list, task-list, mixed-prose, or retired-schema support.
- Synthesis of missing headings, metadata, status, or planning authority.
- Modification of the current Ticket continuation aperture in B.
- Reopening S-tier or A-tier decisions.

## Future Abort And Rollback Triggers

Stop and remove any future B1 pilot if:

- navigation data becomes readiness, evidence, coverage authority, approval
  input, or verdict input;
- independent decomposition or source confirmation is reduced;
- sensitive commands, outputs, credentials, endpoints, or environment values
  are retained;
- records survive transfer or expiry;
- stale hints materially misdirect discovery;
- project-local or durable workflow state becomes necessary;
- fallback versions appear;
- the projection expands beyond navigation anchors;
- measured net benefit falls below the approved evidence predicate; or
- the mechanism implies resumption of state that was never persisted.

Stop any future B2 migration if:

- the population cannot be fully enumerated;
- item count, order, or binding is ambiguous without owner confirmation;
- unknown variants are accepted;
- current producers emit the legacy form;
- the converter becomes a runtime dependency or fallback;
- the zero-population removal point disappears; or
- converted material fails the unchanged current parser.

## Evidence And Sessions

- A/B ChatGPT conversation:
  `https://chatgpt.com/c/6a78a6ea-6748-83ee-8762-13187a198385`
- Initial B followup: `slots-followup-iistierb-b6a4d4c6c6`
- Final B followup: `slots-followup-iistierb-f225f6cbe8`
- Same-conversation authoritative readback: verified for both B turns
- Managed browser: slot 1, local CDP `127.0.0.1:19222`
- Reasoning selection: Pro, verified by the browser control
- Model selection: current selected model requested as GPT-5.6 Sol; exact active
  model label was not independently verified by Oracle metadata
- Final attachment: one generated ZIP with 147 files, 1,109,726 selected bytes,
  and SHA-256
  `fe9eccef2398871d59fbc0513be854169b22132944589cf2e59440895fd89bbf`

## Consensus Status

No material B-tier disagreement remains.

B1 is a possible future efficiency feature whose empirical value is unresolved,
not a current defect. B2 runtime tolerance is rejected; only a bounded,
owner-confirmed migration for a named live population may later be proposed. No
B-tier code or test change is justified now.
