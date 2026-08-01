# Phase 2 Baseline

## Scope And Observation

- Task: `2-1. Implementation Lead 기준선 재확인` only. No Task 2-2 or later work was started.
- Observation time: `2026-07-28T13:21:50+09:00`.
- Active repository: `/home/user01/project/implement_lead`.
- Planning repository: `/home/user01/project/matt` was `main` at `5a17bac13f47f2038da2c2b0f8a392e49693596b` and clean immediately before this report was written.

## Active Implementation Lead State

- Branch: `main`.
- HEAD: `6ab0186ef24a63f91a1374366b09cea7cbfc08ea`.
- Most recent commit: `6ab0186 Refactor implementation lead context loading`.
- Git status:

```text
 M SKILL.md
?? .ai-bridge/
```

- `SKILL.md` raw-byte SHA-256 before and after this task: `d6615f6048cf8612bb28e0678c7871edf525f59e942600197aa15ec742c641e9`.
- This task did not modify, restore, stage, delete, commit, or otherwise mutate the active repository. `.ai-bridge/` remains untracked and was not read or copied.

### Phase 0 Comparison

`verification/phase-0-baseline.md` records the same active `SKILL.md` SHA-256 and the same two status entries (` M SKILL.md`, `?? .ai-bridge/`). Phase 0 did not record the active repository HEAD or recent commit, so no historical HEAD comparison is asserted. This record establishes only the observable state at its observation time.

### Pre-existing SKILL.md Diff And Ownership Boundary

The active `SKILL.md` has a pre-existing uncommitted diff against its current HEAD. Read-only inspection shows it changes Planning Admission authority and its revalidation gates, including `planningAdmissionIdentity`, `planning_admission_current`, `external_claims_current`, `X13`, and `X14`.

This diff is user-owned baseline state. It is preserved byte-for-byte in the rollback copy below and must not be edited, restored, staged, committed, or absorbed into a later Ticket-input change. Directly changing the active dirty `SKILL.md` would mix the existing Planning Admission delta with Phase 2 work, preventing reliable ownership and actual-delta attribution.

## Preserved Core Invariants

| Invariant | Source location |
| --- | --- |
| Only the user-selected Worker may modify product source, tests, configuration, generated files, or other project paths. The Lead must not directly edit product paths. | `SKILL.md` `Implementation Lead` lines 87-103; `Worker` lines 114-118 |
| Worker calls are synchronous and sequential: one bounded call at a time. | `SKILL.md` `Worker` lines 116-118; `Sequential implementation loop` lines 1102-1123 |
| Each bounded task has a frozen mutation envelope; actual delta is independently inspected, cannot widen that envelope, and must preserve pre-existing changes. | `SKILL.md` `Phase completion projections` lines 197-216; `Sequential implementation loop` lines 1089-1121 |
| Canonicals are exact current code references with path, symbol/entry point, responsibility, relationship (`reuse`, `extend`, or `replace`), and supported before digest. | `SKILL.md` `Decompose the Story` lines 1021-1024; Worker instruction requirements lines 122-132 |
| Every applicable Acceptance Criterion and Story task maps to a bounded task or explicit no-mutation review item; an unexplained gap blocks dispatch. | `SKILL.md` `Decompose the Story` lines 993-1009 and 1032-1045 |
| Adapter-native schema, status, exit code, evidence category, and report fields retain their native meaning; no common Adapter result is invented. | `SKILL.md` `Adapter authority boundary` lines 289-310; `In-session state projection` lines 369-384; `Adapter contexts and invocation` lines 1239-1303 |
| Evidence lifetime is an overlay only: `CURRENT` supports judgment, `STALE` requires revalidation, `INVALID` cannot support acceptance, and `SUPERSEDED` is history/diagnosis only. | `SKILL.md` `In-session state projection` lines 349-378; `Mandatory RunRecord update points` lines 1065-1073 |
| Full requires accepted due-now tasks or a recorded zero-mutation path, no pending/validating/revalidating task, no required stale/invalid evidence, clear ownership, and one sealed final state. | `SKILL.md` `Full integration gate` lines 1305-1367 |
| Terminal results remain `complete`, `blocked`, and `incomplete`; their required conditions and failure boundaries must not be weakened or expanded. | `SKILL.md` `An implementation-stage complete result requires` lines 1441-1468; `Stop and return boundaries` lines 1470-1508 |

## Documented Adapter Commands

No Adapter command was executed in Task 2-1. The following are existing documented commands only; no command has been inferred or invented.

### Node

- Package identity and scripts: `/home/user01/project/implement_lead/adapters/node/package.json` lines 1-20.
- Native contract and development verification: `/home/user01/project/implement_lead/adapters/node/README.md` lines 12-26 and 521-555.
- Lead integration invocation: `/home/user01/project/implement_lead/references/adapters/node.md` lines 57-65 and 112-128.

```bash
npm run prepare:typescript-integration
npm test
npm run lint
npm run typecheck
npm run build
node /home/user01/project/implement_lead/adapters/node/src/cli.js probe --project /absolute/project --context /absolute/context.json
node /home/user01/project/implement_lead/adapters/node/src/cli.js fast --project /absolute/project --context /absolute/context.json
node /home/user01/project/implement_lead/adapters/node/src/cli.js full --project /absolute/project --context /absolute/context.json
```

### Python

- Package and tool configuration: `/home/user01/project/implement_lead/adapters/python/pyproject.toml` lines 1-47.
- Native contract and development verification: `/home/user01/project/implement_lead/adapters/python/README.md` lines 8-31 and 307-315.
- Lead integration invocation: `/home/user01/project/implement_lead/references/adapters/python.md` lines 58-64 and 91-101.

From `/home/user01/project/implement_lead/adapters/python`:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src
SOURCE_DATE_EPOCH=0 .venv/bin/python -m build --wheel --no-isolation
.venv/bin/python -m python_adapter fast --project /absolute/project --context /absolute/context.json
.venv/bin/python -m python_adapter full --project /absolute/project --context /absolute/context.json
```

### Go

- Module configuration: `/home/user01/project/implement_lead/adapters/go/go.mod` lines 1-3.
- Native schemas: `/home/user01/project/implement_lead/adapters/go/schemas/context-v1.0.schema.json` lines 1-79 and `/home/user01/project/implement_lead/adapters/go/schemas/report-v1.0.schema.json` lines 1-74.
- Native contract and verification: `/home/user01/project/implement_lead/adapters/go/README.md` lines 16-43 and 93-135.
- Lead integration invocation: `/home/user01/project/implement_lead/references/adapters/go.md` lines 64-77 and 84-127.

From `/home/user01/project/implement_lead/adapters/go`:

```bash
go test ./...
go test -race ./...
go vet ./...
go build ./cmd/go-adapter
./bin/go-adapter manifest --project /absolute/snapshot-root
./bin/go-adapter fast --project /absolute/project --context /absolute/context.json
./bin/go-adapter full --project /absolute/project --context /absolute/context.json
```

## Immutable Pre-Phase 2 Copy

- Exact path: `/home/user01/project/implement_lead.pre-phase2-20260728`.
- Pre-create check: `/home/user01/project` existed and the exact target path did not exist. The target was created once and was not overwritten.
- Copied scope only: active `SKILL.md` and the complete active `references/` tree, retaining their original relative paths and permissions with `cp -a`.
- Excluded: `.git/`, `.ai-bridge/`, `adapters/`, all other active-repository files, and files outside the active repository. No manifest was created in the backup.
- File count: 7 regular files. Source and backup each contain the same six `references/` files and one `SKILL.md`.
- Raw bytes, SHA-256 values, and mode values were compared after copy. Recursive byte comparison was empty, all listed source/backup SHA-256 values matched, regular files are mode `0644`, and `references/` plus `references/adapters/` are mode `0755`.

| Relative path | SHA-256 |
| --- | --- |
| `SKILL.md` | `d6615f6048cf8612bb28e0678c7871edf525f59e942600197aa15ec742c641e9` |
| `references/failure-and-retry.md` | `5ff4e34c352ab02975527b00ba28e8294ec3547acec13bcb6c7e952e4e76a388` |
| `references/greenfield.md` | `9a0e8ad9ea87df5aac7a2c7f4a9d33f470f01a399146afe29e58d60ecf360c7d` |
| `references/ui-story.md` | `f0249a109acbf529c5d554a11abeddc2d12abe3466f090fd0f84e006d62c1749` |
| `references/adapters/go.md` | `6ec818a6b0e5cfccac0ae3ba283e5070c102a9b88f48bb1e4eda5dc966ad5df1` |
| `references/adapters/node.md` | `64c32ae11d70fe8cbb5cdff1012557d059ba9ee830c3eb48f381ab8e28e56b0f` |
| `references/adapters/python.md` | `078623eed47ff0a542b5284843c8fce0859718719fa9a078f96f837ca44d3add` |

The backup is an immutable rollback baseline. Do not modify it during later staging or cutover work.

## Phase 2 Safety Boundary And Limit

Do not directly edit or commit the active dirty `/home/user01/project/implement_lead/SKILL.md` during Phase 2. A later change must be prepared and verified in a separate staging candidate, then cut over only after preserving and reconciling the pre-existing user-owned diff. The active repository's current dirty state and this rollback copy are the comparison boundary.

This report makes no unsupported historical claim about changes before the Phase 0 or Phase 2 observations. It proves only the recorded raw-byte state, command documentation, copy scope, and absence of mutations performed by this Task 2-1 work. No global skill was modified by this task.
