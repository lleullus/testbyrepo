# Changelog

## Unreleased

- Move direct Scope observation to `iis-scope/v2` fixed source refs; Observatory displays them but leaves Product Thesis closure and role admission to the trusted host.
- Replace source fingerprints and Markdown checksums with direct stored-original comparison for snapshot freshness and exact JSON→Markdown projection comparison.
- Bump live scan schema to `3.0` and durable snapshot schema to `2.0`.
- Include displayed Scope and legacy history in snapshot freshness so additions, edits and removals refresh stored projections without promoting history into current authority. Unrelated product-code changes still leave snapshots unchanged.

## 0.3.0

- Read canonical `docs/planning/work/<slug>/SCOPE.md` artifacts using `iis-scope/v1` and bound Thesis SHA-256 sources.
- Display direct Scope `draft`, `ready`, `done`, and `superseded` state, required outcomes, optional Transition Authority, and exact read-only next pointers.
- Preserve legacy Scope Shaping/Increment/Spec/Ticket artifacts as history; report unfinished legacy work as `transition required` without automatic migration or old Matt/Ticket routing.
- Detect stale bound sources and duplicate active Scopes as consistency errors in `scan` and `doctor`.

## 0.2.1

- Add deterministic progress-bar rendering for exact-ratio snapshot measurements while always preserving the exact numerator, denominator, and percentage beside the bar.
- Use fractional Unicode blocks for small non-zero ratios so a value such as 1.2% is not visually exaggerated into a full 10% cell.
- Keep progress visualization presentation-only: it does not affect IIS health, next-work routing, or planning authority.

## 0.2.0

- Add durable read-only project snapshots under `docs/planning/observatory/PROJECT-OVERVIEW.md` and `project-state.json`.
- Add `snapshot --write` and `snapshot --check` with CURRENT, STALE, MISSING, and INCONSISTENT freshness states.
- Base snapshot freshness on a deterministic content fingerprint of current canonical planning inputs and displayed Adaptive provenance, excluding Observatory outputs themselves.
- Refuse snapshot writes when canonical planning state is inconsistent, validate the Markdown/JSON pair with a recorded checksum, and make unchanged writes a true no-op.
- Record Adaptive companion artifacts only as provenance and never infer current Adaptive Planning activation from their presence or recorded status.
- Separate canonical planning, Adaptive provenance, and Observatory projection entries in Git-backed history output.

## 0.1.7

- Show portfolio `Unit` as a stable planning identifier plus its authored title, for example `INC-003 · <Increment heading>`.
- Use the authored Spec heading for direct-work units as `work · <Spec heading>` instead of exposing an unexplained work slug.
- Strip only repeated identifier prefixes from headings; Observatory does not generate or paraphrase unit summaries.
- Give the Unit column more room on wider terminals while preserving the full follow-up `Next` pointer in narrow 80-column output.

## 0.1.6

- Redesign the portfolio table around `Unit`, compact Ticket progress, derived `State`, and a wider `Next` planning pointer.
- Preserve authored follow-up candidates in narrow 80-column terminals, for example `Scope Shaper [WP-002, WP-003]`.
- Use `—` for complete units with no authored next work and shorten the terminal summary so it does not crowd the portfolio rows.
- Keep Markdown overview columns aligned with the terminal overview semantics.

## 0.1.5

- Separate authored planning artifact statuses from Observatory-derived delivery state in detailed `scan` output.
- Show `Derived Delivery State` only when a current Ticket-backed delivery state is `READY`, `BLOCKED`, or `COMPLETE`.
- Keep planning-only states uncluttered so `ready-for-matt`, `scoped`, and `approved` remain visibly distinct from delivery completion.

## 0.1.4

- Read explicit `Outcome Horizon` Expansion and Deferred Work Packages from the current confirmed Scope.
- When the current Increment's Tickets are all done, keep the current unit `COMPLETE` while pointing to `Scope Shaper` if authored Expansion candidates remain.
- Preserve authored Expansion order, never infer priority from WP numbering, and never promote Deferred Work Packages into next-work candidates.
- Expose follow-up candidates in text and JSON output with `Next Increment: not yet shaped`.

## 0.1.3

- Treat a non-Git discovery root as a portfolio container even if it has a stray `docs/planning` directory.
- Keep an explicitly scanned Git repository eligible when the discovery root itself is the repository.
- Make `doctor <root>` follow the same container-vs-repository rule as `overview <root>`.

## 0.1.2

- Scope `ready-for-matt` uniqueness and Increment lookup to the currently selected Scope lineage instead of the whole repository.
- Prevent repeated `INC-NNN` identifiers in sibling or historical Scope lineages from cross-associating Specs and Tickets by also honoring the current work slug.
- Preserve `IIS102` for multiple `ready-for-matt` Increments inside the same current Scope lineage.

## 0.1.1

- Exclude linked Git worktrees from multi-repository discovery by default.
- Added `--include-worktrees` to `overview` and `doctor` for explicit worktree visibility.
- Explicit `scan <worktree-path>` and `doctor <worktree-path>` remain supported.

## 0.1.0

- Added read-only discovery of repositories containing `docs/planning`.
- Added deterministic Scope → Work Package → Increment → Spec → Ticket projection.
- Added `overview`, `scan`, `doctor`, and Git-backed `history` commands.
- Added text, Markdown, and JSON output.
- Added consistency checks for missing selected Increments, duplicate/missing Ticket states, and broken local planning links.
- Added dependency-free installer and unit/integration tests.
