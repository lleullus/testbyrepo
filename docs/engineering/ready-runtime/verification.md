# Ready Runtime Verification

## Scope result

The implementation keeps `ready-ticket-implement` caller-facing inputs, DIRECT/SUBAGENT selection, PRE_ACTION/MATERIAL_TURN semantics, terminal `IMPLEMENT RESULT`, and Ticket `ready` status ownership unchanged. Heuristic probing, final verification, Adaptive Run Contract semantics, and Ticket validator semantics remain separate.

## Runtime verification

- Ready runtime Node suite: 11/11 passed.
- Repository Ready runtime contract: 3/3 passed.
- Existing delivery/subagent contract: 14/14 passed.
- Adaptive planning contract: 18/18 passed.
- Adaptive run contract: 12/12 passed.
- Full repository suite after implementation: 227 tests run, 226 passed, 1 failed.
- The single full-suite failure is the same worktree-local baseline failure captured before implementation: `test_global_cli_link_targets_canonical_observatory`. The global observatory CLI still resolves to `/home/user01/project/iis-skills/observatory/bin/iis-observatory`, while a test executed from this worktree expects the worktree-local path. No Ready runtime change touches that installation.

Runtime tests cover DIRECT and SUBAGENT binding, PRE_ACTION and MATERIAL_TURN gating, parent mutation exclusion, exact tool-result attribution, authority binding/currentness, protected authority writes, Project Root confinement, duplicate observation blocking, mutation revision/current evidence, broad inventory blocking, bounded read retry, deterministic mutation repeat blocking, mutation uncertainty, interrupted-operation recovery, structured argv, and managed local-service ownership/cleanup.

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

The live Ready Skill is a symlink resolving to `/home/user01/project/iis-skills/companion-skills/ready-ticket-implement`, while this implementation lives in `/home/user01/project/iis-skills-wt-ready-click-runtime`. Their current Skill payloads differ. The runtime extension is therefore intentionally not installed live yet; installing it alone would arm the old Skill without the required runtime begin procedure. Once the matching Ready Skill source is live, `--preflight` must return `READY` before runtime sync.
