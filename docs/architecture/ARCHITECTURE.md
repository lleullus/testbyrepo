# Architecture Context — logtrim 0.4 compression-first evolution

Artifact-Type: architecture-context
Format-Version: 1
Subject: logtrim 0.4 compression-first architecture
Project-Root: /home/user01/project/work/logtrim-v3-extracted
Prepared-At: 2026-09-27
Starting-Point: EVOLUTION
Architecture-Authority: user-directed architecture evolution; implementation authorized for this project, deployment and Git effects not authorized

## 1. Context and Drivers

### Architecture Question and Boundary

Evolve the current v3 single-process log analyzer so that its default/max-compression path does not materially regress from the practical compression behavior of the 0.1 line while retaining v3's stronger streaming, bounded-state, structured parsing and semantic observability. This context covers ingest, normalization, grouping and reporting responsibilities. Packaging, deployment topology and external services are outside the decision.

### Product and Operator Purpose

The primary utility is to turn large operational log captures into a much smaller set of readable patterns and summaries. Compression is therefore a first-class success condition, not a downstream diagnostic. Smarter parsing is valuable only when it preserves or improves that compression objective while keeping diagnostically important variation recoverable.

### Architectural Drivers

- Compression is the primary quality driver. The default path must establish a coarse grouping floor comparable to the aggressive 0.1 behavior before later intelligence is applied.
- Semantic intelligence must not normally increase top-level pattern count. Important differences should remain recoverable as bounded intra-group variants/statistics.
- High-cardinality operational entropy such as PIDs, TIDs, ports, pod suffixes, hashes, long numeric identifiers and dynamic route segments should be normalized before residual similarity logic.
- The analyzer must retain v3's bounded-memory, disk-backed aggregation, exact accepted-event counts and streaming I/O properties.
- Domain-aware reducers may bypass generic event clustering when the input has stronger structure, such as state snapshots.

### Constraints and Supplied Authority

- Python standard-library runtime remains the current implementation constraint.
- One local process is sufficient; no driver currently justifies services, embeddings, a network dependency or a plugin platform.
- Existing resource limits and atomic output behavior are preserved unless a later measured requirement contradicts them.
- A claim of compression non-regression requires differential measurement on the same corpus and logical-record policy.

### Product-Dependent Assumptions

- The normal/default operating mode favors maximum useful reduction over preserving every literal as a separate top-level pattern.
- Diagnostically important categorical variation can be represented inside a coarse group without requiring a separate top-level group in the normal compression mode.

## 2. Architectural Model

### System Context

Raw files/stdin feed one analyzer process. The analyzer emits text/JSON/JSONL/Markdown/HTML summaries. No external runtime service is required.

### Current Architecture

Current v3 performs logical-event assembly, parser-first normalization to a single pattern string, exact lookup, then strict typed-token candidate clustering. The same normalized pattern representation carries both compression identity and semantic detail. Literal mismatches outside recognized slot families commonly block merging.

### Intended / Target Architecture

Target 0.4 separates **coarse compression identity** from **semantic representation**:

```text
raw input
  -> record assembly / family recognition
  -> semantic normalization
  -> coarse compression canonicalization
  -> exact coarse aggregation
  -> bounded semantic-variant observation
  -> adaptive/residual merge that may reduce groups further
  -> report
```

The coarse identity is monotonic: later semantic analysis does not split an already-established coarse group in default max-compression mode.

### Major Subsystems, Responsibilities and Boundaries

| Area | Primary responsibility | Owns | Deliberately does not own | Collaborates through |
| --- | --- | --- | --- | --- |
| Record assembly | Form bounded logical records | multiline/event boundaries | grouping policy | logical record |
| Semantic normalizer | Preserve diagnostically useful structure | parser result, typed values, anchors, captures | final compression identity | semantic normalized event |
| Coarse canonicalizer | Remove high-cardinality entropy aggressively | primary grouping pattern/key | semantic interpretation | coarse pattern + semantic pattern |
| Aggregator | Count coarse identities exactly on disk | clusters, counts, phases, time/slot stats | parsing semantics | SQLite-backed cluster state |
| Variant observer | Preserve bounded semantic differences without splitting | top semantic variants and overflow counts | top-level cluster identity | cluster variant stats |
| Residual merger | Optionally merge compatible coarse groups further | secondary template generalization | baseline coarse splitting | candidate/template relation |
| Reporter | Expose reduction and retained semantics | stage metrics, patterns, variants | grouping decisions | rows/summary |

### Important Relationships and Dependency Direction

- Semantic normalizer -> coarse canonicalizer: semantic parsing happens first so coarse reduction can reuse recognized placeholders while additionally removing unresolved operational entropy.
- Coarse canonicalizer -> aggregator: the coarse pattern is the primary exact identity and therefore the compression floor.
- Semantic normalizer -> variant observer: the richer semantic pattern is retained only as bounded intra-cluster evidence.
- Aggregator -> residual merger: residual merging may reduce top-level clusters further but cannot create more clusters than the coarse exact floor in default mode.

## 3. Decisions and Rationale

### Decision 1 — Separate coarse identity from semantic representation

Standing: ADOPTED
Scope: default/max-compression analysis path
Drivers and constraints: compression must not be sacrificed merely to preserve richer parser detail.
Selected structure: every event carries a coarse pattern for grouping and a richer semantic pattern for bounded readback.
Material alternatives: one normalized string for both purposes; semantic-first cluster splitting.
Rationale: one representation forces a direct tradeoff between entropy removal and semantic detail. Two representations let grouping stay aggressive while retaining diagnostic variation.
Trade-offs and consequences: additional bounded metadata and normalization work per event; clearer compression invariant.
Dependent assumptions: semantic variants can be represented compactly enough for normal diagnostics.
Evidence / authority: PROVIDED user requirement plus OBSERVED v3/0.1 behavior comparison.
Revisit conditions: measured workloads show bounded variants are insufficient to diagnose material failures.

### Decision 2 — Make coarse compression monotonic

Standing: ADOPTED
Scope: normal default mode
Drivers and constraints: 0.4 must not become smarter by substantially lowering compression.
Selected structure: later semantic analysis annotates existing coarse clusters; residual clustering may merge but does not split them.
Material alternatives: permit semantic split whenever a discriminator differs; compensate through later fuzzy merging.
Rationale: free splitting makes compression retention only an expectation. Non-splitting makes the compression floor structural.
Trade-offs and consequences: one coarse pattern can contain semantically distinct variants, so reports must expose bounded variant counts.
Dependent assumptions: users prefer compact primary output with drill-down semantics to an expanded primary pattern list.
Evidence / authority: PROVIDED user priority; self-review found split-after-compression to be the main logical gap.
Revisit conditions: an explicit precision mode or quantified compression budget is introduced.

### Decision 3 — Restore aggressive operational entropy removal before residual clustering

Standing: ADOPTED
Scope: coarse canonicalization
Drivers and constraints: 0.1 practical compression came largely from early normalization; v3 strict similarity cannot recover literals left unnormalized.
Selected structure: normalize pod suffixes, hashes, long numbers, process/thread identifiers, ports and dynamic route segments in the coarse representation while preserving semantic representation separately.
Material alternatives: lower similarity threshold; add broad fuzzy/embedding clustering.
Rationale: removing known entropy before comparison is deterministic, cheap and directly reduces exact signature cardinality.
Trade-offs and consequences: coarse patterns are intentionally less literal; semantic variants provide readback.
Dependent assumptions: selected coarse normalizations represent operational entropy more often than primary event meaning.
Evidence / authority: OBSERVED 0.1 normalizer and current v3 matching behavior.
Revisit conditions: differential corpus testing identifies a normalization class that causes unacceptable loss of useful grouping boundaries.

### Decision 4 — Preserve v3 disk-backed bounded aggregation

Standing: ADOPTED
Scope: runtime/storage architecture
Drivers and constraints: large captures must not require retaining all unique patterns or events in memory.
Selected structure: keep SQLite-backed aggregate state, bounded cache/candidates and streaming input/output.
Material alternatives: rebuild around in-memory adaptive clustering; external database/service.
Rationale: the current mechanism already satisfies the resource/operational simplicity driver and does not cause the observed compression failure.
Trade-offs and consequences: disk I/O remains part of large analyses.
Dependent assumptions: local temporary disk is available.
Evidence / authority: OBSERVED current implementation and passing baseline tests.
Revisit conditions: measured storage or throughput becomes the limiting requirement.

## 4. Evolution and Open Questions

### Preserve

- SQLite-backed exact counts and temporary lifecycle.
- Streaming I/O and atomic report replacement.
- Resource limits and bounded caches.
- Structured parsing, timestamp extraction and numeric slot statistics.
- Custom rule support and secret redaction.

### Change / Strengthen / Retire / Defer

- Change: primary exact identity becomes parser + coarse pattern rather than parser + semantic anchors + semantic pattern.
- Strengthen: aggressive operational entropy canonicalization, including Kubernetes-oriented identifiers and dynamic route values.
- Strengthen: reports expose bounded semantic variants within each coarse cluster.
- Retire from primary policy: literal-mismatch-zero and immutable-leader veto as the main compression mechanism. They may remain only in residual merge logic.
- Defer: automatic high-cardinality learning across arbitrary field positions until the coarse-floor/variant architecture is measured and stable.
- Defer: domain-specific snapshot/describe reducers until the event path establishes the compression invariant.

### Open Architecture Questions

- Exact numeric tolerance for "not materially below 0.1" remains unspecified. Default max-compression mode therefore targets no top-level group-count regression relative to an equivalent coarse canonicalization baseline.
- The first implementation uses bounded top semantic variants. More sophisticated entropy/cardinality learning is a later decision after measurement.

## 5. Basis and Applicability

### Evidence and Authority Anchors

- A1 | PROVIDED | current conversation | compression is the primary objective and 0.4 should not materially regress from 0.1.
- A2 | OBSERVED | logtrim/patterns.py | current semantic normalizer preserves several values/routes that cause high-cardinality exact patterns.
- A3 | OBSERVED | logtrim/similarity.py and logtrim/grouping.py | incompatible literals and strict leader/template constraints bias toward under-merging.
- A4 | OBSERVED | logtrim 0.1 source archive previously inspected | early operational normalization and family-specific reduction were primary compression mechanisms.
- A5 | OBSERVED | current baseline test run | 40 tests passed before 0.4 implementation changes.

### Inferences and Assumptions

- I1 | INFERRED | separating coarse identity from semantic detail removes the direct tradeoff between top-level compression and diagnostic readback | Supported by: A1-A4 | Falsifier: bounded variants prove unusable for important diagnostics.
- I2 | INFERRED | monotonic non-splitting semantics can structurally prevent smarter analysis from reducing the established coarse compression floor | Supported by: A1-A4 | Falsifier: implementation creates alternate top-level identities outside the coarse aggregator.
- S1 | ASSUMED | the selected 0.1-style entropy classes are appropriate coarse variables on target operational logs | Decision affected: Decision 3 | Smallest discriminator: differential corpus benchmark and variant inspection.

### Coverage and Limitations

Inspected / considered:
- v3 normalization, grouping, models, CLI/report boundaries and regression tests.
- previously inspected 0.1 normalization/grouping/family behavior.
- Architecture Companion and claim-completeness self-review conclusions.

Not inspected / not decided:
- representative user production log corpus is not currently available in this workspace.
- final automatic entropy/cardinality inference algorithm is intentionally deferred.
- deployment/package distribution changes are outside this architecture step.

Applicability and change-sensitive conditions:
- Reassess when representative corpus measurements contradict the coarse normalization assumptions.
- Reassess if exact-preservation/forensic mode becomes a primary product requirement rather than an optional mode.
