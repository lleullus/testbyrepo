# Ready Ticket Implement Runtime

OMP extension that enforces execution discipline for Ready Ticket implementation and the integrity boundary of Ready Ticket verification without changing product meaning.

## Runtime boundary

The runtime binds the exact Ticket, Parent Spec, applicable Behavior/UI authority, canonical validator, Project Root and Git/worktree identity. Skill reads never arm execution. Only explicit begin/assignment requests admit work, and authority plus required Probe/target validation precede execution commit. Implementation preserves the guarded mutation/evidence lifecycle and bounded observation policy. Verification keeps the target immutable, fails closed on drift, and owns only the mechanical guarded `ready -> done` write after the verifier supplies `VERIFIED`. Product meaning, heuristic findings and flow/AC verdicts remain with their existing owners.

`ready_guard cancel_admission` fences an in-flight unbound admission in the current session. Failed unbound admission automatically disarms. Cancellation cannot erase execution, assignment, parent, worker or uncertain state; those bindings close through owner recovery/terminal actions.

Same-worker continuation preserves its binding. Replacement requires the old worker to stop owned activity and call `suspend_worker`, then Parent to confirm inactivity and call `replace_worker`. The replacement consumes a one-use assignment, rechecks authority and suspended working-tree identity, retains prior execution/checkpoint provenance, and waits for a fresh Parent release. Old worker calls remain fenced. This runtime fence is not proof that a harness job exited; Parent still owns actual job containment.

`latest_evidence_revision` is the latest successful **observation** revision. Ordinary reads and inspections count; complete output from a successfully executed `ready_argv mutate` command also binds to its resulting revision. Native file writes alone, failed/timed-out commands, and incomplete output do not provide that observation. Revision equality permits runtime closure but does not prove product obligations or self-check sufficiency; the implementation owner must establish the current result through the authored acceptance path and existing handoff. The persisted field and revision-equality gate are retained.

An `inspect` or verification `execute` request rejected because another guarded operation is active does not reserve an observation. Once that operation finishes, the rejected request remains executable. Actual running duplicates and unchanged successful observations retain their existing restrictions.

Mutation snapshots cover every declared target, including directory contents. Partial failure with attributable changes advances `mutation_revision` without producing successful evidence. Interruption invalidates evidence and preserves `MUTATION_UNCERTAIN`; only owner exact target readback or `ready_guard resolve_mutation` can compare saved before identities against current targets. Missing/unattributable readback stays uncertain. No caller-supplied outcome is accepted. Structured commands join termination before recovery; services stop before terminal closure. Parent session refresh never recovers the child's active operation, and same-process live operations survive session refresh.

The inventory quota is an efficiency policy, not the authority/path boundary. Its glob detector currently reads `pattern`; native glob events carrying `path` are not recognized by that branch. Such calls do not prove that the quota was enforced. The policy remains unchanged rather than claiming an unmeasured reduction benefit.

Structured `inspect` and simple native bash inspections share the same argv classification. `sed` inspection is limited to quiet addressed line printing. Known file-output, external-execution, and mutating `git worktree` options are rejected, including attached/clustered short options and long-option forms. `git grep -O` is rejected as an external pager, not treated as a read. `sha256sum` remains outside the inspect allowlist. This is not a process sandbox: ambient executable resolution, Git configuration, and environment remain trust prerequisites. Commands outside inspection still need the existing guarded execute/mutate authority.

Internal tools:

- `ready_probe_binding`: write one current machine-checkable terminal Probe binding outside Project Root
- `ready_guard`: explicit admission, bounded cancellation/recovery, DIRECT/SUBAGENT continuation/checkpoints, terminal verdict close and guarded `ready -> done`
- `ready_argv`: explicit structured inspect/verification-execute/implementation-mutate argv; shell interpreters are rejected
- `ready_service`: execution-owned local service start/stop/status

## Canonical admission inspection

The `iis-workflow` To Tickets locator accepts the existing absolute `SKILL.md` route either bare or enclosed in Markdown backticks.

An unbound session may use `ready_argv inspect` with `commands: [["python3", "-B", "<discovered-validate_ticket.py>", "<exact-ticket>"]]` (`-B` optional). The runtime checks the canonical route and disables bytecode writes. Actual exit code/stdout/stderr are returned; this creates no execution and grants no arbitrary Python or product-command authority.

During `ACTIVE` verification, the same one-command inspection is allowed only for the bound validator and exact bound Ticket. It uses the existing guarded observation lifecycle, permits a fresh successful revalidation, and checks authority/target currentness before and after execution. Generic `execute` does not gain external-path access. The workflow and To Tickets files join the existing hash-bound protected authority artifacts; exact protected-authority `read` calls may be refreshed, including canonical skill locators and line selectors. Other external paths, mutations, ordinary source rereads and concurrent guarded operations retain their existing restrictions.

OMP Ready tools are `loadMode: essential`, available natively even with default `tools.xdev=true`. Exact `write xd://ready_guard|ready_argv|ready_probe_binding|ready_service` envelopes defer to the inner registered tool's schema and lifecycle checks; other device writes are not exempt. Native and device routes require separate live smoke evidence. No global xdev setting change or unguarded fallback is needed.

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

`--preflight` reports installability, not live readiness. Sync installs the runtime under `~/.omp/agent/extensions/ready-ticket-implement-runtime` and links missing Ready Implement/Probe/Verify skills under OMP's own `~/.omp/agent/skills`; existing differing skill content is never overwritten. `--check` proves installed byte equality only. Both outputs explicitly say `LIVE_SESSION_NOT_CHECKED`. Verify discovery and begin/action/terminal in a fresh top-level OMP session with the actual configured transport. Existing parent/child skill and module snapshots are not refreshed by disk installation or worker replacement.

## Rollback

Remove or rename `~/.omp/agent/extensions/ready-ticket-implement-runtime` and restore the prior Ready Skill content through its normal skill synchronization path. Runtime data under `~/.omp/agent/data/iis-ready-runtime` is not deleted by rollback; it becomes inactive historical state.
