# Phase 8 Removal Preparation

Status: `PREPARED_BLOCKED`

Prepared on 2026-08-05 from Git revision
`e75e81b0c8162c6e22578d09b61f5dc60b8d5688` with enabled production Effect Adapter set `[]`.

## Gate

No removal, caller cutover, freeze, data move, import, archive, or discard is authorized. Phase 8's hard
precondition requires Phase 7 `RUNTIME_VERIFIED` for the exact source and Adapter set. The current Phase 7
verdict is `RUNTIME_VERIFICATION_BLOCKED` because production Source Adoption cannot provide conditional
pathname mutation against arbitrary uncooperative writers. Phase 8 remains `CLOSED`.

This document is a read-only preparation census. It does not satisfy or replace the runtime gate.

## Bounded Removal Manifest

Removal order is outside-in after the gate opens:

1. Active caller and skill cutover.
2. `verification-lead/tools/verification-run/verification_run.py`.
3. `implementation-lead/tools/implementation-result/implementation_result.py` and historical runtime reader.
4. `implementation-lead/tools/implementation-transaction/implementation_transaction.py` and
   `implementation-lead/tools/task-ownership-snapshot/ownership_snapshot.py`.
5. `implementation-lead/tools/workflow-store/workflow_store.py` and `workflow_store_preopen.py`.
6. `baseline-capsule/` public protocol and store mechanism after historical capsule disposition.
7. Mechanism-coupled tests, references, help, package exports, and installed copies in the same category order.

Current repository census contains 13 tracked files under the three legacy tool surfaces and 15 tracked legacy
test files. Neutral primitives may remain only when the deletion revision has a concrete new Module consumer.

## Active Consumers

- Repository `implementation-lead/SKILL.md` and `verification-lead/SKILL.md` still describe the old orchestration.
- Installed `/home/user01/.codex/skills/implementation-lead/SKILL.md` exists and still requires the durable
  implementation transaction, ownership snapshots, Baseline Capsules, and the old handoff contract.
- Installed `/home/user01/.codex/skills/verification-lead/SKILL.md` does not exist.
- The installed Implementation Lead must not be cut over until the Phase 8 gate opens and the replacement
  production entry routing is usable for the admitted work class.

## Runtime Census

- Default legacy workflow root `/home/user01/.local/state/opencode/implementation-workflows` is absent.
- No running process matched `verification_run.py`, `implementation_result.py`,
  `implementation_transaction.py`, `workflow_store.py`, `ownership_snapshot.py`, or `baseline_capsule.py` at
  census time.
- This point-in-time observation is not the Phase 8 quiescence window. A real zero census must be repeated and
  held from freeze through caller cutover and retired-entrypoint unavailability.

## Durable Data

No disposition has been authorized.

| Root | Observation | Required disposition before removal |
| --- | --- | --- |
| `/home/user01/.local/state/opencode/implementation-results` | 19 JSON files, 137041 bytes: 11 `implementation-result-v3`, 8 `implementation-result-v2` | `IMPORT` only for an explicit continuing consumer and fully representable records; otherwise `STATIC_ARCHIVE`. Never infer test data. |
| `/home/user01/.local/state/opencode/baseline-capsules` | 652645635 bytes; 39 capsule directories | Preserve every referenced capsule and recoverable source; classify unreferenced capsules only under explicit retention authority. |

All 19 historical results reference a distinct existing capsule; missing referenced capsules: 0.

Read-only census digests:

```text
implementation result file/digest list: 21f94db49f33ffef04c98a1421877c2b12c9fb846bd581c79bfead99448a0769
sorted unique capsule refs:           43d1593e9004e0788503b9ffb652944ae1f9e0cf42a9c369edc27d39bcdf153b
```

These aggregate digests identify this preparation census only. The execution manifest must record every item,
relative path, size, digest, chosen disposition, and archive/import readback before any mechanism deletion.

## Execution Preconditions

Removal may begin only after all of these are true:

- Phase 7 is `RUNTIME_VERIFIED` for the exact removal base revision and enabled Adapter set.
- Active callers, installed copies, automation, entrypoints, schemas, and state roots are re-censused.
- Legacy owner, active transition, unresolved may-have-run effect, and incomplete cleanup counts are all zero.
- Every one of the 19 historical results and all reachable capsule bytes have an authorized disposition and
  verified readback manifest.
- The one-way caller cutover target and representative production flow are operational without legacy fallback.

Until then, the only valid Phase 8 action is to refresh this read-only census.
