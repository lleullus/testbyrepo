# Ready Ticket Implement Runtime

OMP extension that enforces execution discipline for Ready Ticket implementation and the integrity boundary of Ready Ticket verification without changing product meaning.

## Runtime boundary

The runtime binds the exact Ticket, Parent Spec, applicable Behavior/UI authority, canonical validator, Project Root and Git/worktree identity. A session is armed only by canonical `skill://ready-ticket-implement` or `skill://ready-ticket-verify` invocation; plain filesystem inspection of those skill files is review/maintenance and does not enter Ready execution. Implementation mode preserves the guarded mutation/evidence lifecycle, permits at most one recognized repository-wide DIRECT inventory before the first admitted mutation, and lets an exact native file read run again only when the current file-content identity changed or the Ready mutation revision advanced. Verification mode binds one current Probe handoff and implementation target, blocks generic Project Root mutation, rechecks target identity around guarded observations, fails closed on target drift, and owns only the mechanical guarded `ready -> done` write after the verifier supplies final `VERIFIED`. It does not decide product meaning, run heuristic probing, choose flow/AC verdicts, or create background delivery workers.

`ready_guard cancel_admission` is a same-session recovery action for an accidental canonical invocation that is still `ARMED` and has no execution, assignment, parent, or worker binding. It accepts no Ticket, execution, assignment, or session identifier, disarms only the calling session, and fences any admission that was already waiting on authority work so a later result cannot bind after cancellation or a new arm. It does not release or rewrite active, delegated, uncertain, terminal, or other-session state: active work closes through its existing owner action, and `MUTATION_UNCERTAIN` still requires owner readback and the existing recovery contract.

Canonical `skill://ready-ticket-implement` or `skill://ready-ticket-verify` invocation is therefore reserved for delivery after one actual Ready Ticket has been selected. Planning and documentation investigation reads the skill through its filesystem reference, which does not arm delivery. If a planning session invokes the canonical resource by mistake before binding, it may call `cancel_admission` and continue planning in that same session; it must not use cancellation as a route out of bound or uncertain delivery.

`latest_evidence_revision` is the latest successful **observation** revision. Ordinary reads and inspections count; complete output from a successfully executed `ready_argv mutate` command also binds to its resulting revision. Native file writes alone, failed/timed-out commands, and incomplete output do not provide that observation. Revision equality permits runtime closure but does not prove product obligations or self-check sufficiency; the implementation owner must establish the current result through the authored acceptance path and existing handoff. The persisted field and revision-equality gate are retained.

An `inspect` or verification `execute` request rejected because another guarded operation is active does not reserve an observation. Once that operation finishes, the rejected request remains executable. Actual running duplicates and unchanged successful observations retain their existing restrictions.

Cancelling a structured mutation after admission preserves `MUTATION_UNCERTAIN`: cancellation does not prove that no effect occurred. Current owner readback and the existing recovery contract must resolve the outcome before further mutation or closure.
Structured argv uncertainty resolution currently uses the existing internal lifecycle API after owner readback; it is not an exposed `ready_guard` action.

The inventory quota is an efficiency policy, not the authority/path boundary. Its glob detector currently reads `pattern`; native glob events carrying `path` are not recognized by that branch. Such calls do not prove that the quota was enforced. The policy remains unchanged rather than claiming an unmeasured reduction benefit.

Structured `inspect` and simple native bash inspections share the same argv classification. `sed` inspection is limited to quiet addressed line printing. Known file-output, external-execution, and mutating `git worktree` options are rejected, including attached/clustered short options and long-option forms. `git grep -O` is rejected as an external pager, not treated as a read. `sha256sum` remains outside the inspect allowlist. This is not a process sandbox: ambient executable resolution, Git configuration, and environment remain trust prerequisites. Commands outside inspection still need the existing guarded execute/mutate authority.

Internal tools:

- `ready_probe_binding`: write one current machine-checkable terminal Probe binding outside Project Root
- `ready_guard`: unbound same-session admission cancellation, DIRECT/SUBAGENT lifecycle, verification target binding, checkpoints, terminal verdict close, guarded `ready -> done`
- `ready_argv`: explicit structured inspect/verification-execute/implementation-mutate argv; shell interpreters are rejected
- `ready_service`: execution-owned local service start/stop/status

## Canonical admission inspection

The `iis-workflow` To Tickets locator accepts the existing absolute `SKILL.md` route either bare or enclosed in Markdown backticks.

An armed session with no bound execution may use `ready_argv inspect` with `commands: [["python3", "-B", "<discovered-validate_ticket.py>", "<exact-ticket>"]]` (the `-B` flag is optional). The runtime resolves the script against the current canonical route and executes it with bytecode writes disabled. The response contains the real exit code/stdout/stderr; this does not create an execution, count as product evidence, or authorize product commands. Arbitrary Python, other scripts, batches and mutations still require the existing binding and guards.

During `ACTIVE` verification, the same one-command inspection is allowed only for the bound validator and exact bound Ticket. It uses the existing guarded observation lifecycle, permits a fresh successful revalidation, and checks authority/target currentness before and after execution. Generic `execute` does not gain external-path access. The workflow and To Tickets files join the existing hash-bound protected authority artifacts; exact protected-authority `read` calls may be refreshed, including canonical skill locators and line selectors. Other external paths, mutations, ordinary source rereads and concurrent guarded operations retain their existing restrictions.

The supported isolated evaluation profile exposes native extension tools (`tools.xdev=false`); a fresh-session canonical arm/begin/action/terminal observation is distinct from installed-byte equality. The generic `write xd://...` wrapper remains unsupported for Ready execution: it can be classified as a filesystem mutation before an internal Ready tool receives its call. Native-tool evaluation does not establish wrapper support, and unsupported delivery must not fall back to unguarded execution.

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
