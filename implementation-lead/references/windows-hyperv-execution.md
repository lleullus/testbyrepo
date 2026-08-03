# Conditional Windows / Hyper-V implementation execution

This reference adds bounded platform mechanics only. It creates no Windows lifecycle, dedicated
Worker, public artifact, Completion Record field, verification status, or final verdict.

## Trigger

Load it only after Lead-first Ticket, source, caller, and repository-command inspection proves that the
actual current consumer or required check needs Windows. File extension, directory name, title, or a
guessed stack is not evidence.

Resolve this exact reference from the canonical physical directory containing Implementation Lead's
`SKILL.md`. If it cannot be resolved or read, stop before VM use; do not approximate a same-named copy.

## Authority

The Ticket, approved Spec, applicable UI authority, and repository commands still decide behavior.
This reference authorizes no VM creation, image choice, credential use, network access, external
resource, deployment, or product mutation.

Use only an already-authorized bounded supervisor. Host commands, direct Hyper-V mutation, arbitrary
PowerShell, interactive desktop work, or a second ad-hoc transport are prohibited unless separately
authorized by repository policy.

## Worker and ownership boundary

The same selected Worker owns product mutation through its frozen envelope. The VM is an execution
target, not another Worker or source owner. Product edits made inside a VM are prohibited unless they
are the exact selected Worker call and are captured by the ordinary project ownership transaction.

Planning files stay in their canonical external workspace. Do not copy Ticket/Spec/UI authority into a
VM project materialization or treat a copy as current authority.

## Source binding

Before a Windows implementation check, bind the target to the exact handoff candidate source through
one of the repository-authorized mechanisms:

```text
CURRENT_PROJECT_ROOT
SOURCE_BOUND_MATERIALIZATION
REVISION_BOUND_TARGET
```

A source-bound materialization is owner-only, outside the project root, derived from the exact physical
source projection, and disposable. Record its digest/revision and require equality with the current
implementation transaction identity. Remove only runner-owned materialization after bounded readback.

Never infer source identity from Git HEAD, a branch, timestamp, VM name, or copied path spelling.

## Bounded implementation checks

Seal the exact repository-authoritative executable, arguments, target, environment-delta digests,
expected provisional effect, readback, timeout, and cleanup before execution. Record all attempts and
outputs through the implementation transaction tool. No shell substitution, fallback target, manual
retry, or hidden recovery action is allowed.

Windows checks can close build, packaging, platform integration, installer, or source compatibility
responsibilities. Rendered WPF, WinForms, or WinUI work also follows the approved UI reference and
frontend guidance.

## AgentBridge window-mode contract

Every newly submitted bounded AgentBridge job JSON must contain exactly one explicit `windowMode`:

```text
hiddenConsole
interactiveGui
```

Use `hiddenConsole` for PowerShell, `cmd.exe`, compilers, test runners, CLIs, and other console work. The
interactive Worker starts that process with a hidden window while preserving stdout/stderr redirection,
the process handle, exact exit code, timeout, and process-tree termination. A `hiddenConsole` job with
non-empty UI Automation `actions` is a contract error and must fail before process start.

Use `interactiveGui` for WPF, WinForms, WinUI, and any process whose actual runtime consumer requires a
visible user window, foreground interaction, or UI Automation. Its visible GUI execution path remains
unchanged.

Choose the mode from the actual runtime consumer. Never infer it from a file name, extension, path, job
name, `waitForExit`, `captureScreenshot`, screenshot presence, or the mere existence of an `actions`
field. A screenshot request alone does not make a job interactive. A missing or unsupported
`windowMode` must produce a clear failure result without starting the process. `windowMode` is bounded
bridge job input only; it creates no Implementation Lead RunState, Worker type, task-record field,
Completion Record field, or public contract field.

The bounded `status` action must provide readback for the `InteractiveWorker` action count, Execute,
Arguments, WorkingDirectory, principal LogonType, RunLevel, task state, `Settings.Hidden`, interactive
AgentAdmin session, Worker process session, queue counts, and deployed bridge/Worker hashes.
`Settings.Hidden` controls Task Scheduler listing behavior; it does not hide a PowerShell process
window.

Ordinary Implementation Lead execution must never call `configure-worker-window` or use
`-ApplyWindowHideStaging`. Those capabilities are restricted to an explicitly authorized AgentBridge
maintenance operation; they are not product execution, a fallback transport, or an arbitrary-command
escape hatch.

These observations are provisional implementation facts. They are not final runtime evidence and may
not be copied into `VerificationResult`. The later Verification Assessor independently seals the final
Windows product flow, target/revision binding, expected effect, readback, and cleanup.

## Safety and privacy

- Do not use production/user data, real payment/message targets, or credentials without explicit
  current authorization.
- Store only bounded redacted output projections and secret references/digests.
- Do not inline screenshots, raw user data, secrets, VM credentials, or message/payment content in a
  handoff.
- Cleanup is concrete and single-attempt; do not retry a failed cleanup automatically.
- Preserve the product target when the Ticket requires it; cleanup of runner-owned materialization is
  distinct from product-resource cleanup.

## Failure routing

An unavailable VM, supervisor, materialization, credential, or repository command stops the current
implementation check. Missing authority returns to the authority owner; missing execution capability is
an implementation environment stop. Neither condition creates `INCOMPLETE` or `BLOCKED` as a public
VerificationResult.

A source mismatch or drift invalidates the check and prevents handoff preparation. Re-establish
implementation accounting at the current source; never auto-adopt another identity.

After an ImplementationHandoff, any Windows product contradiction belongs to Verification Lead. Source
mutation then requires an immutable `VERIFICATION_FAILED`, fresh remediation admission, a selected
Worker, ownership controls, a successor handoff, and a fresh full-AC VerificationRun.
