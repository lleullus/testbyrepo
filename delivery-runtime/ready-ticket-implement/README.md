# Ready Ticket Implement Runtime

OMP extension that enforces execution discipline for `ready-ticket-implement` without changing its caller-facing Ready contract.

## Runtime boundary

The runtime binds the exact ready Ticket, Parent Spec, applicable Behavior/UI authority, canonical validator, Project Root and Git/worktree identity. It guards native read/search/mutation calls, structured argv, joined SUBAGENT checkpoints, mutation revision/current evidence, and an execution-owned local service. It does not decide product meaning, run heuristic probing, adjudicate final verification, change Ticket status, or create background delivery workers.

Internal tools:

- `ready_guard`: DIRECT/SUBAGENT lifecycle, checkpoints, status, terminal close, mutation-uncertainty resolution
- `ready_argv`: explicit structured inspect/mutate argv; shell interpreters are rejected
- `ready_service`: execution-owned local service start/stop/status

## Test

```text
node --test tests/*.test.js
```

The repository-level `tests/test_ready_ticket_runtime_contract.py` runs the same runtime test suite from `run_tests.py`.

## Install / check

Use the repository script after the matching Ready Skill source is ready to be installed:

```text
python3 scripts/sync_installed_ready_runtime.py --preflight
python3 scripts/sync_installed_ready_runtime.py
python3 scripts/sync_installed_ready_runtime.py --check
```

`--preflight` requires the live Ready Skill payload to match this source tree before the runtime can be installed. The sync installs this package as one OMP extension directory under `~/.omp/agent/extensions/ready-ticket-implement-runtime`; it does not install or rewrite the Ready Skill itself.

## Rollback

Remove or rename `~/.omp/agent/extensions/ready-ticket-implement-runtime` and restore the prior Ready Skill content through its normal skill synchronization path. Runtime data under `~/.omp/agent/data/iis-ready-runtime` is not deleted by rollback; it becomes inactive historical state.
