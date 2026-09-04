# Ready Ticket Implement Runtime

OMP extension that enforces execution discipline for Ready Ticket implementation and the integrity boundary of Ready Ticket verification without changing product meaning.

## Runtime boundary

The runtime binds the exact Ticket, Parent Spec, applicable Behavior/UI authority, canonical validator, Project Root and Git/worktree identity. Implementation mode preserves the guarded mutation/evidence lifecycle, permits at most one repository-wide DIRECT inventory before the first admitted mutation, and lets an exact native file read run again only when the current file-content identity changed or the Ready mutation revision advanced. Verification mode binds one current Probe handoff and implementation target, blocks generic Project Root mutation, rechecks target identity around guarded observations, fails closed on target drift, and owns only the mechanical guarded `ready -> done` write after the verifier supplies final `VERIFIED`. It does not decide product meaning, run heuristic probing, choose flow/AC verdicts, or create background delivery workers.

Internal tools:

- `ready_probe_binding`: write one current machine-checkable terminal Probe binding outside Project Root
- `ready_guard`: DIRECT/SUBAGENT lifecycle, verification target binding, checkpoints, terminal verdict close, guarded `ready -> done`, mutation-uncertainty resolution
- `ready_argv`: explicit structured inspect/verification-execute/implementation-mutate argv; shell interpreters are rejected
- `ready_service`: execution-owned local service start/stop/status

## Test

```text
node --test tests/*.test.js
```

The repository-level `tests/test_ready_ticket_runtime_contract.py` runs the same runtime test suite from `run_tests.py`.

## Install / check

Use the repository script after the matching Ready Implement, Heuristic Probe, and Verify Skill sources are ready to be installed together:

```text
python3 scripts/sync_installed_ready_runtime.py --preflight
python3 scripts/sync_installed_ready_runtime.py
python3 scripts/sync_installed_ready_runtime.py --check
```

`--preflight` requires the live Ready Skill payload to match this source tree before the runtime can be installed. The sync installs this package as one OMP extension directory under `~/.omp/agent/extensions/ready-ticket-implement-runtime`; it does not install or rewrite the Ready Skill itself.

## Rollback

Remove or rename `~/.omp/agent/extensions/ready-ticket-implement-runtime` and restore the prior Ready Skill content through its normal skill synchronization path. Runtime data under `~/.omp/agent/data/iis-ready-runtime` is not deleted by rollback; it becomes inactive historical state.
