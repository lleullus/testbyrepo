# B Tier Adversarial Consensus

## Decision

B tier authorizes no current implementation, parser, test, schema, storage,
artifact, wording, or workflow change.

- B1, persistence of the Implementation Lead's nominated implementation-route
  index, is **CURRENT NO CHANGE / EVIDENCE-GATED REOPENING**.
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

## B1: Current-Session Route Index

### Current Contract

The nominated implementation-route index is explicitly a current-session
result:

- `implementation-lead/SKILL.md` requires the index in the current-session
  implementation result.
- The same contract says to keep the result in the current session and forbids
  a separate handoff file, serialized state, or approval workflow.
- `verification-lead/SKILL.md` reads the index only if the current session
  contains it.
- Verification independently decomposes the Ticket before reading the index.
- Verification independently confirms route facts from current product source.
- Runtime Runner remains the only runtime-readiness boundary.
- Index absence, incompleteness, malformedness, staleness, or disagreement does
  not block Verification.
- The Verification working model is separately in-memory and session-temporary.

No writer, reader, storage location, serialization schema, expiry operation, or
persisted-index fixture exists.

### Correct Characterization

Cross-session absence is expected current behavior. It is not a current contract
defect, failed handoff, or discarded guaranteed artifact.

Persistence would be a new efficiency feature. It must prove that repeated
attributable navigation savings exceed storage, lifecycle, privacy, stale-state,
compatibility, accidental-authority, and removal costs.

No route-index persistence mechanism or pilot is authorized now.

### Manual Observation Gate

Observe the next 12 consecutive real Implementation Lead to Verification Lead
transitions, or 90 calendar days, whichever ends first.

Do not extend the window or omit unfavorable cases. Include:

- same-session transitions;
- cross-session transitions;
- source-changed transitions;
- incomplete, malformed, or stale indexes;
- blocked Verification starts; and
- cases whose index contains information unsafe to retain.

A reopening decision requires at least five completed cross-session
Verification starts. Fewer than five leaves the evidence gate closed.

### Recording Boundary

For each transition, record manually only:

- same-session or cross-session;
- number of materially distinct implementation routes;
- whether potentially useful route anchors remained current;
- count of repository-navigation actions;
- lower-bound active navigation time, excluding idle time;
- whether useful information was limited to projection-safe navigation fields;
  and
- whether discovery produced an additional route, alternative, conflict, or
  scenario fact.

Do not copy route content, source text, commands, raw outputs, credentials,
environment values, private endpoints, focused-check observations, or the full
route index into the observation record.

A reviewer may compare closed Implementation and Verification transcripts only
after each case completes. The index must not be exposed operationally to
Verification during measurement.

### Attribution Rule

The measurement window begins after Verification independently decomposes the
Ticket and establishes qualifier bindings. It ends when relevant candidate route
anchors have been located and independently source-confirmed.

Count only surplus discovery work. Exclude every action required for:

- current-source confirmation;
- Runtime Runner investigation;
- alternative search;
- scenario design;
- evidence acquisition;
- conflict resolution; or
- verdict work.

An action or interval is attributable to index absence only when all conditions
hold:

1. It locates a startup/execution path, trigger or contract boundary,
   source/integration path, or outcome/readback surface.
2. The exact or sufficiently narrow anchor was already present in the
   Implementation index.
3. The anchor remained current when Verification began.
4. The action was not required to confirm the anchor against current source.
5. The action discovered no other plausible route, required alternative, source
   conflict, scenario condition, readiness fact, or causal fact.
6. Supplying only the navigation anchor would have eliminated the action without
   narrowing independent investigation.

Resolve ambiguous time or actions against attribution. Stale, malformed,
conflicting, or sensitive entries contribute no benefit and remain in the
observation set.

### Reopening Predicate

B1 may be reopened for design review only when all conditions hold:

1. At least five completed cross-session cases were observed.
2. At least three cases, and at least half of all completed cross-session cases,
   each contain at least four attributable navigation actions and at least five
   lower-bound active minutes of attributable rediscovery.
3. Aggregate attributable rediscovery is at least 45 lower-bound active minutes.
4. Every qualifying benefit derives only from startup/execution, trigger or
   contract-boundary, source/integration, and outcome/readback anchors.
5. A zero-code cost model using the observed lower-bound frequency projects
   six-month saved effort at no less than twice the total estimated one-time and
   six-month recurring cost of implementation, tests, privacy review, capture,
   Ticket binding, retrieval, stale handling, expiry, deletion, and removal.

Meeting this predicate authorizes only reconsideration and a separately reviewed
pilot proposal. It does not authorize implementation or a pilot.

### Future Option, Not Approved

The only future design eligible for evaluation is a host-owned,
outside-Project-Root, short-lived, single-consumer navigation projection with
only these anchor classes:

- startup/execution;
- trigger or contract boundary;
- source/integration; and
- outcome/readback.

It must be bound to one exact Ticket, ignored on mismatch or apparent staleness,
deleted after transfer or bounded expiry, and excluded from readiness, evidence,
Coverage Challenge, Scenario approval, and verdict derivation.

This is not an approved minimum design. Ticket-digest binding alone may be
insufficient because product source can change without a Ticket change.

### Tradeoffs

The observation protocol can undercount resumption value:

- known route anchors can reduce cognitive reconstruction even when the same
  files still require independent reading;
- the index may reduce omission risk rather than only search commands;
- rare multi-entrypoint projects can have large value; and
- manual attribution can cost enough to discourage measurement.

These costs do not establish a defect or justify hidden cross-session state.
Omission reduction cannot count as benefit if the index narrows independent
candidate search.

Even a minimal projection creates cross-session identity, expiry, deletion,
privacy, stale-state, versioning, hidden-state, and accidental-authority costs.
After stripping observations, blockers, results, and AC conclusions, little
utility may remain.

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
- The route index remains current-session-only, navigation-only, and
  non-authoritative.
- No handoff file, serialized state, workflow database, or approval workflow is
  introduced.
- Verification independently decomposes the Ticket and confirms current source.
- Runtime Runner retains readiness ownership.
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
