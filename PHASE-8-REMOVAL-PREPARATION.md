# Phase 8 Removal Preparation

Status: `REMOVAL_WORKTREE_VERIFIED_PENDING_DELETION_REVISION`

Prepared on 2026-08-05. The removal worktree head is `c48ab0fdc52aee77bb2b686370c4e6630578474b`; the
preparation census was taken at revision `e75e81b0c8162c6e22578d09b61f5dc60b8d5688` with enabled production
Effect Adapter set `[]`.

## Gate

The exact source and Adapter set pass Phase 7 `ACCEPTED_SUPPORTED_RANGE_VERIFIED`, as mechanically checked by
`phase8_supported_range_gate.py`. This label is not mutation-capable `RUNTIME_VERIFIED`: production Source
Adoption remains `UNSUPPORTED_PRE_MUTATION_FAIL_CLOSED`, so no mutation-bearing production flow is claimed.
Enabled production Effect Adapter set remains `[]` and authenticated READ remains unsupported.

The removal worktree completed `DURABLE_DATA_DISPOSITION` and `ACTIVE_CALLER_CUTOVER`. Repeated point-in-time
zero censuses and retired-entrypoint absence were observed, but the bounded `CONTINUOUS_LEGACY_WRITE_QUIESCENCE`
window remains a deletion-revision prerequisite. Historical data remains in the verified `STATIC_ARCHIVE`; the
active legacy mechanism and its coupled tests are absent from this dirty worktree.

The deletion worktree was rechecked by the runtime gate and the bounded removal census.

## Completed Deletion Evidence

### Removal Manifest — executed

The removal order below is complete; retired source, bytecode, and empty legacy directories are gone from the
actual filesystem:

1. Active caller and skill cutover — installed `/home/user01/.codex/skills/implementation-lead` and
   `/home/user01/.codex/skills/verification-lead` are repository symlinks whose `SKILL.md` is the Terra/Luna
   Module contract (canonical target, SKILL.md SHA-256, and retired-term absence verified by the census).
2. `verification-lead/tools/verification-run/verification_run.py` and `executable_identity.py`.
3. `implementation-lead/tools/implementation-result/implementation_result.py` and historical runtime reader.
4. `implementation-lead/tools/implementation-transaction/implementation_transaction.py` and
   `implementation-lead/tools/task-ownership-snapshot/ownership_snapshot.py`.
5. `implementation-lead/tools/workflow-store/workflow_store.py` and `workflow_store_preopen.py`.
6. `baseline-capsule/` public protocol and store mechanism after historical capsule disposition.
7. Mechanism-coupled tests, references, help, package exports, and installed copies in the same category order.

Deletion worktree census (current head, uncommitted): 0 tracked legacy source files, 0 tracked legacy test
files, 0 filesystem legacy files, 0 residue files, 0 empty legacy directories. Removed retired bytecode
(`baseline_capsule.cpython-312.pyc`, `verification_run.cpython-312.pyc`, `executable_identity.cpython-312.pyc`,
`implementation_result.cpython-312.pyc`, `implementation_transaction.cpython-312.pyc`,
`ownership_snapshot.cpython-312.pyc`, `workflow_store.cpython-312.pyc`, `workflow_store_preopen.cpython-312.pyc`,
`test_baseline_capsule.cpython-312.pyc`, and the retired test suite bytecode) and empty legacy directories
(`implementation-lead/tools/*`, `verification-lead/tools/`, the retired test directories, and
`baseline-capsule/`). None of these remain under the installed symlink surface.

### Active Consumers

- Installed `/home/user01/.codex/skills/implementation-lead` and `/home/user01/.codex/skills/verification-lead`
  are symlinks to this repository's `implementation-lead/` and `verification-lead/`, both describing the
  Terra/Luna Implementation Verification Module contract; no retired mechanism term remains in either
  `SKILL.md`.
- The production entry routing in `implementation-verification/` is the admitted replacement and the only
  supported route for the admitted work class.

### Runtime Census

- Default legacy workflow root `/home/user01/.local/state/opencode/implementation-workflows` is absent.
- No running process matched `verification_run(.py|.pyc)`, `implementation_result(.py|.pyc)`,
  `implementation_transaction(.py|.pyc)`, `workflow_store(.py|.pyc)`, `ownership_snapshot(.py|.pyc)`, or
  `baseline_capsule(.py|.pyc)` at census time.
- This point-in-time observation is not the Phase 8 quiescence window. A real zero census must be repeated and
  held from freeze through caller cutover and retired-entrypoint unavailability.

### Durable Data — `STATIC_ARCHIVE` disposition executed

Historical user data was preserved read-only; nothing was deleted or inferred as test data.

| Root | Observation (preparation census at `e75e81b`) | Disposition |
| --- | --- | --- |
| `/home/user01/.local/state/opencode/implementation-results` | 19 JSON files, 137041 bytes: 11 `implementation-result-v3`, 8 `implementation-result-v2` | `STATIC_ARCHIVE` — every item read back in manifest `2080a8fc83d2d4604a3278f197f3ad3b884acfdac3ab4d6b28a071b18d9a7405` |
| `/home/user01/.local/state/opencode/baseline-capsules` | 652645635 bytes; 39 capsule directories | `STATIC_ARCHIVE` — preserve every referenced capsule; unreferenced capsules only under explicit retention authority |

All 19 historical results reference a distinct existing capsule; missing referenced capsules: 0. Archive
verify on the deletion worktree: 10,804 files, 648,217,529 bytes, 19/19 items, via
`python3 phase8_static_archive.py verify --archive-path /home/user01/.local/share/opencode-phase8-static-archives/phase8-static-archive-v1-2080a8fc83d2d4604a3278f197f3ad3b884acfdac3ab4d6b28a071b18d9a7405`.

Read-only census digests (deletion worktree, current head):

```text
implementation result file/digest list: 21f94db49f33ffef04c98a1421877c2b12c9fb846bd581c79bfead99448a0769
sorted unique capsule refs:           43d1593e9004e0788503b9ffb652944ae1f9e0cf42a9c369edc27d39bcdf153b
```

These aggregate digests are unchanged from the preparation census because the historical result and capsule
surface was only read, never written. The execution manifest records every archived item, relative path, size,
digest, chosen disposition, and archive readback.

## Historical Preparation (superseded)

The preparation census at `e75e81b` (2026-08-05) recorded, before any deletion, 13 tracked legacy source files
under the three legacy tool surfaces plus `baseline-capsule/`, and 15 tracked legacy test files, with active
consumers still describing the old orchestration, no authorized data disposition, and pending destructive
prerequisites. Every item in that preparation state was resolved as follows:

- 13 legacy source files and 15 legacy test files: deleted (tracked deletions in the worktree) and removed
  from the filesystem including ignored bytecode and empty directories.
- Active consumer cutover: installed skills switched to the Module contract and verified by target, content,
  and retired-term absence.
- `DURABLE_DATA_DISPOSITION`: `STATIC_ARCHIVE` manifest `2080a8...` with 19/19 readback.
- Repeated point-in-time runtime censuses were zero at each recheck; bounded
  `CONTINUOUS_LEGACY_WRITE_QUIESCENCE` start/end evidence remains pending.

## Execution Preconditions — completed

- Phase 7 is `ACCEPTED_SUPPORTED_RANGE_VERIFIED` for the removal base revision and enabled Adapter set `[]`;
  this does not assert mutation-capable `RUNTIME_VERIFIED`.
- Active callers, installed copies, automation, entrypoints, schemas, and state roots were re-censused; the
  installed cutover is verified by canonical target, SKILL.md SHA-256, and retired-term absence.
- Legacy owner, active transition, unresolved may-have-run effect, and incomplete cleanup counts were zero at
  repeated point-in-time censuses; the bounded quiescence window is not yet evidenced.
- Every one of the 19 historical results and all reachable capsule bytes have an authorized disposition
  (`STATIC_ARCHIVE`) and verified readback manifest.
- The one-way caller cutover target and representative production flow are operational without legacy fallback.

## Deletion Revision Prerequisite

All evidence above was produced on the current dirty worktree (head `c48ab0fdc52aee77bb2b686370c4e6630578474b`),
which is **not yet committed**. `LEGACY_MECHANISM_REMOVED` closes only after the deletion revision is committed,
the bounded quiescence window is evidenced, and the same gate, census, smoke, archive-verify, and installed-surface
checks are re-run and pass on that exact committed revision. The existing gate output's HEAD, tracked diff hash,
and untracked-file identity bind the current dirty-worktree run; no permanent ledger is required. Until then this
document must not be read as a committed deletion revision.
