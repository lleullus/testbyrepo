# Changelog

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
