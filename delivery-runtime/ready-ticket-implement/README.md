# Ready Ticket Implement Runtime

OMP extension that enforces execution discipline for `ready-ticket-implement` without changing its caller-facing Ready contract.

## Runtime boundary

The runtime binds the exact ready Ticket, Parent Spec, applicable Behavior/UI authority, canonical validator, Project Root and Git/worktree identity. It guards native read/search/mutation calls, structured argv, joined SUBAGENT checkpoints, mutation revision/current evidence, Zero-Mock implementation/verification evidence, and an execution-owned local service. It does not decide product meaning, run heuristic probing, issue AC/Whole-Ticket verification verdicts, or create background delivery workers; verifier status progression remains owned by `ready-ticket-verify` after runtime admission.

Internal tools:

- `ready_guard`: DIRECT/SUBAGENT implementation lifecycle, checkpoints, status, terminal close, mutation-uncertainty resolution
- `ready_argv`: structured inspect/mutate plus Zero-Mock `acceptance`; every acceptance call requires `provenance_kind` exactly `LOCAL_PATH`, `LOCAL_SQLITE`, or `EXTERNAL_HTTP_PROVIDER`
- `ready_verify_guard`: verifier Zero-Mock begin/admission/post-progression validation; revalidates current evidence fingerprints before admission without taking verdict authority
- `ready_service`: execution-owned local service start/stop/status

Clean local PASS provenance binds the resolved runner's exact canonical selected test-root set to the exact canonical `evidence_paths` set and fingerprints the production and evidence import closures, dependency/config files, authoritative readback, runner configuration, and mutation revision; ambiguous or unsupported selectors fail closed. Package runners additionally fingerprint the original and resolved argv plus `package.json`, and fail closed before execution when the exact adjacent `pre<name>` or `post<name>` lifecycle hook is configured. JS/TS taint analysis follows mock authority through globals, static members, destructuring, and aliases. Implementation `COMPLETE` requires a non-empty acceptance-provenance denominator whose every entry is clean and current; ordinary read-only observation is not a substitute. The fingerprint is recomputed at implementation completion or verifier admission, where `VERIFIED` requires the same binding and current fingerprint while preserving the authored direct-canonical-inspection exception. Basename/text mention alone is not provenance. The current runtime cannot correlate `EXTERNAL_HTTP_PROVIDER` execution with readback, so it runs neither command nor readback argv and records acceptance as `INCONCLUSIVE`; implementation is `BLOCKED`, affected verifier flows/ACs remain `INCONCLUSIVE`, and the evidence cannot admit `VERIFIED`.

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

`--preflight` requires both live `ready-ticket-implement` and `ready-ticket-verify` payloads to match this source tree before the runtime can be installed. The sync installs this package as one OMP extension directory under `~/.omp/agent/extensions/ready-ticket-implement-runtime`; it does not install or rewrite the Ready Skill itself.

## Rollback

Remove or rename `~/.omp/agent/extensions/ready-ticket-implement-runtime` and restore the prior Ready Skill content through its normal skill synchronization path. Runtime data under `~/.omp/agent/data/iis-ready-runtime` is not deleted by rollback; it becomes inactive historical state.
