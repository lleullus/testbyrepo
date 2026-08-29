# Ready Runtime Verification

## Scope result

The implementation keeps `ready-ticket-implement` caller-facing inputs, DIRECT/SUBAGENT selection, PRE_ACTION/MATERIAL_TURN semantics, terminal `IMPLEMENT RESULT`, and Ticket `ready` status ownership unchanged. Heuristic probing, final verification, Adaptive Run Contract semantics, and Ticket validator semantics remain separate.

## Runtime verification

- Ready runtime Node suite: 19/19 passed.
- Repository Ready runtime contract: 4/4 passed.
- Existing delivery/subagent contract: 14/14 passed.
- Adaptive planning contract: 18/18 passed.
- Adaptive run contract: 12/12 passed.
- Full repository suite after Zero-Mock implementation: 228 tests run, 227 passed, 1 failed.
- The single full-suite failure is the same worktree-local baseline failure captured before implementation: `test_global_cli_link_targets_canonical_observatory`. The global observatory CLI still resolves to `/home/user01/project/iis-skills/observatory/bin/iis-observatory`, while a test executed from this worktree expects the worktree-local path. No Ready runtime change touches that installation.

Runtime tests cover DIRECT and SUBAGENT binding, PRE_ACTION and MATERIAL_TURN gating, parent mutation exclusion, exact tool-result attribution, authority binding/currentness, protected authority writes, Project Root confinement, duplicate observation blocking, mutation revision/current evidence, broad inventory blocking, bounded read retry, deterministic mutation repeat blocking, mutation uncertainty, interrupted-operation recovery, structured argv, managed local-service ownership/cleanup, Zero-Mock mutation blocking, renamed-wrapper taint propagation, mock-mode environment blocking, unknown MCP fail-closed behavior, actual SQLite persistence, unavailable readback disposition, verifier read-only enforcement, exact ready-to-done progression, and current direct-inspection provenance.

## Async boundary

A source-scoped search found no queue, polling loop, scheduler, or interval-based delivery runtime. The only `detached` occurrence is `detached: false` on the managed local service child process.

## Click provenance

The inspected Click source identifies version `0.17.0`; no local `v0.20*` tag was present. This runtime therefore records Click v0.17.0 as the actual provenance point and uses behavior-level reimplementation only. Click approval contracts, modes, Fix/review/planning UX, and verification budgets were not imported.

## Installation / rollback state

The runtime install script supports:

- `--preflight`: read-only Ready Skill/source compatibility check.
- normal sync: installs only the OMP runtime extension after preflight compatibility.
- `--check`: byte-level source/runtime drift check.
- `--remove`: removes the runtime extension without deleting runtime data.

Current live preflight result: `SKILL_DRIFT`.

The live `ready-ticket-implement` and `ready-ticket-verify` payloads still resolve from `/home/user01/project/iis-skills`, while this implementation lives in `/home/user01/project/iis-skills-wt-ready-click-runtime`. The current payloads differ. The runtime extension is therefore intentionally not installed live yet; installing it alone would arm old delivery/verifier instructions without the required runtime procedures. Once both matching Ready Skill payloads are live, `--preflight` must return `READY` before runtime sync.

## Zero-Mock Delivery extension

A later runtime delta adds Zero-Mock Delivery as an implementation and verification invariant. Python and JS/TS mock/patch/interception APIs are statically taint-checked with project-local import-closure propagation, acceptance runners are structured and provenance-recorded, unknown custom/MCP runners fail closed, and candidate COMPLETE/VERIFIED cannot consume mock-tainted or unavailable-readback evidence. Actual temporary SQLite persistence is covered as an allowed real-dependency fixture.
