# Windows Hyper-V Execution

## Purpose And Conditional Trigger

This reference is conditional Implementation Lead runtime-adapter mechanics. It adds no RunState,
TaskState, Windows lifecycle, Addon, dedicated Worker, manifest, task-record field, Completion Record
field, planning authority, or completion verdict.

The Lead decides whether to load this reference only after directly reading the canonical Ticket and
Spec, inspecting current repository wiring, selecting the current task, and resolving the actual runtime
consumer and repository-authoritative command requirement. Load it only when that actual intended
consumer or command requires Windows build, test, run, install, or GUI execution in the configured
environment. A file extension, directory name, Ticket title, framework name, or guessed platform is not
a trigger. An available Windows environment is not itself a requirement.

The configured profile is fixed for this invocation:

```text
WSL product source and Git: canonical product Project-Root only
Hyper-V host: DESKTOP-BALMTAV
VM: Windows
Guest computer: DESKTOP-IRUC588
Interactive GUI worker: DESKTOP-IRUC588\AgentAdmin
Guest work root: C:\AgentBridge\work
Transport: PowerShell Direct only
Bounded supervisor: C:\AgentBridgeHost\Invoke-AgentVmBounded.ps1
```

SSH, external ports, and host-Windows product application, installer, build, test, or GUI execution are
forbidden. Windows build, test, run, install, and GUI activity happens in the guest VM only. The raw
bridge `C:\AgentBridgeHost\Invoke-AgentVm.ps1` is never called directly by the Lead or Worker; every VM
action uses only `C:\AgentBridgeHost\Invoke-AgentVmBounded.ps1`.

## Planning And Source Boundaries

The Lead directly reads the exact canonical Ticket and Spec paths in WSL, captures and rechecks the
existing `PlanningInputSeal`, and records the canonical path of this reference plus Windows task facts
in the existing task fields. Ticket, Spec, blockers, and approved UI authority may live in an external
planning workspace such as `~/opencode/planning/<task-owned-id>/<work-slug>/`.

An external planning-workspace Ticket, Spec, blocker, or approved UI authority is never separately
copied into a product materialization or synced to the VM. `wslpath` and VM sync apply only to a product
source materialization. If current planning authority is already inside product-root legacy
`.scratch/**`, `source-evidence-v1` includes it as ordinary projected source bytes and those bytes can
reach the guest incidentally in the source materialization. That guest copy is never planning authority:
the canonical WSL path and `PlanningInputSeal` remain the only authority and currentness binding.
Planning-workspace identity never mixes with product `Project-Root`, Baseline Capsule, materialization,
or source identity. A VM success does not make planning current: any changed planning bytes or canonical
planning path still returns the existing result:

```text
blocked: planning input changed
next owner: Ticket 또는 Spec owner
```

The shared `source-evidence-v1` projection remains controlling. Do not exclude product-root legacy
`.scratch/**` from a Baseline or final source projection merely because it can resemble planning; the
existing projection and planning-currentness contracts decide its treatment.

## Roles And Dispatch

The Lead is first: it decides the conditional trigger, reads this reference, selects the safe target,
and records the canonical reference path, actual consumer/command basis, runtime commands, expected
effects, and authoritative readbacks in the existing `integrationObligations` and
`focusedWorkerChecks`. Windows facts are task-specific and are orthogonal to `frontendMode`.

The Lead resolves this reference from the canonical physical `implementation-lead/SKILL.md` directory,
following symlinks, and reads the exact canonical regular file before recording or dispatching Windows
facts. It never searches for or substitutes a same-named copy. Failure to resolve or read that exact file
is `INCOMPLETE` before Worker dispatch or VM use; no fallback or approximation is permitted.

The user-selected Worker remains the only Worker. There is no Windows Worker. For every Windows-bearing
dispatch, the Lead passes that same selected Worker the canonical absolute path of this reference and
the exact provisional commands, expected effects, and readbacks. Before using the VM, the Worker reads
the passed reference directly, but it does not decide whether Windows is needed, select a target, alter
the profile, or claim final Acceptance evidence.

Worker Windows observations are bounded provisional focused checks and implementation feedback only.
They may guide the existing source-review/remediation loop but never become a Representative Runtime
Observation. After source dependency closure, the Lead itself performs the final representative exercise
through the bounded supervisor and independently reads the result, effect, and readback. Do not promote
a Worker result.

WPF, WinForms, and WinUI rendered-contract work remains subject to existing approved UI authority and
`ima2-front` routing. GUI automation uses stable `AutomationId` first; coordinate-based automation is
forbidden.

## Source-Bound Materialization

Only the selected Worker mutates the WSL product source under the canonical `Project-Root`. Neither the
host nor the guest mutates that product source. A Windows check uses a disposable copy, never the WSL
checkout through a mounted or shared path.

For the final representative exercise, the Lead creates one owner-only source materialization outside
the project root and verifies that its `source-evidence-v1` projection identity exactly equals
`finalSourceIdentity`. This is the only path passed through `wslpath`; sync it to a unique guest path
under `C:\AgentBridge\work\<run-id>`. Do not separately pass an external planning workspace, Ticket,
Spec, blocker, approved UI Markdown, Capsule store, or a host product path to sync. A legacy planning
file already included by the product source projection is not separately selected or used as authority.

Use a new unguessable run ID and unique job IDs for every attempt. A failed sync abandons that guest run
directory. A failed guest run directory is never reused, even for retry. Before and after VM execution,
capture the existing project source identity and ownership snapshots and require the expected final
identity and no project delta. Clean up the WSL materialization and guest run path after observation,
then read back their absence. Record cleanup/readback as existing runtime-observation facts; never add a
Windows-specific record.

## Bounded Supervisor Flow

Use this ordered flow for each bounded VM operation:

```text
status -> sync -> submit -> wait -> collect -> cleanup/readback
```

`status` establishes the configured VM and interactive worker health before source sync. Its output is a
formatted PowerShell object, not JSON: require wrapper exit `0` and directly inspect `computer`,
`session`, `workerTask` state/user/run level, `queuedJobs`, `inboxUploads`, `processingJobs`,
`resultUploads`, `results`, `workerHash`, and `bridgeHash`. Establish the current nonzero interactive
AgentAdmin session ID from `session`; the scheduled-task principal may be rendered as `AgentAdmin`
rather than a domain-qualified name. `sync` receives only the converted owner-only source
materialization and copies that source directory beneath `GuestPath`, so the actual guest source path is
`<GuestPath>\<source-basename>`. `submit` receives a task-specific bridge job with a unique job ID. Only
`wait` emits the selected job's result JSON; `wait` and `collect` are always bound to that ID or a
run-unique prefix. The bridge job file is a bounded supervisor input, not a new Implementation Lead
manifest or Completion Record field.

The following WSL bash commands are the only permitted VM invocation path. Run them directly as the WSL
agent's ordinary user, without `sudo`, UAC, RunAs, or a nested PowerShell host. Substitute only
Lead-frozen task values; read each command's emitted result rather than treating its process exit alone
as evidence.

```bash
BOUNDED='C:\AgentBridgeHost\Invoke-AgentVmBounded.ps1'
VM_NAME='Windows'
RUN_ID="implementation-lead-$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM"
JOB_ID="${RUN_ID}-final"
MATERIALIZATION='/owner-only/source-materialization'
GUEST_RUN="C:\\AgentBridge\\work\\${RUN_ID}"
MATERIALIZATION_NAME="$(basename "$MATERIALIZATION")"
GUEST_SOURCE="${GUEST_RUN}\\${MATERIALIZATION_NAME}"
RESULT_DIRECTORY="C:\\AgentBridgeHost\\results\\${RUN_ID}"

STATUS_OUTPUT="$(powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass \
  -File "$BOUNDED" -VMName "$VM_NAME" -Action status)"
STATUS_EXIT=$?
printf '%s\n' "$STATUS_OUTPUT"
# Require STATUS_EXIT=0 and directly inspect formatted fields: computer=DESKTOP-IRUC588;
# a nonzero interactive AgentAdmin session; InteractiveWorker State=Running, User=AgentAdmin,
# RunLevel=Highest; queuedJobs/inboxUploads/processingJobs/resultUploads/results and
# workerHash/bridgeHash are expected for this run.

# The WSL owner-only materialization, not the product root, is the only wslpath input.
WINDOWS_MATERIALIZATION="$(wslpath -w "$MATERIALIZATION")"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass \
  -File "$BOUNDED" -VMName "$VM_NAME" -Action sync \
  -LocalPath "$WINDOWS_MATERIALIZATION" -GuestPath "$GUEST_RUN"
# Job workingDirectory and executable paths use GUEST_SOURCE, because sync places the source directory
# at GUEST_RUN\MATERIALIZATION_NAME rather than directly at GUEST_RUN.

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass \
  -File "$BOUNDED" -VMName "$VM_NAME" -Action submit \
  -JobFile "C:\\AgentBridgeHost\\${JOB_ID}.job.json"
WAIT_OUTPUT="$(powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass \
  -File "$BOUNDED" -VMName "$VM_NAME" -Action wait -JobId "$JOB_ID" \
  -TimeoutSeconds <bounded-seconds>)"
WAIT_EXIT=$?
# Only WAIT_OUTPUT is result JSON. Validate its JobId/result fields and compare WAIT_EXIT before collect.
printf '%s\n' "$WAIT_OUTPUT"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass \
  -File "$BOUNDED" -VMName "$VM_NAME" -Action collect -JobId "$JOB_ID" \
  -ResultDirectory "$RESULT_DIRECTORY"
```

For a small related set of jobs from this one run, `collect -JobPrefix $runId` is permitted. Ordinary
runs never use `-CollectAll`; it is permitted only for explicit bridge diagnostics, which are not
product runtime evidence. The Lead directly reads the selected collected JSON and any required readback.
A cleanup job, when needed, receives its own unique job ID and follows the same `submit -> wait ->
collect` sequence. The Lead then confirms the guest path and WSL materialization are absent without
including their raw contents in the Completion Record.

## Result And GUI Evidence

For every accepted job, the Lead requires the selected result JSON to name the expected unique ID and
establish:

- `timedOut` is false;
- stderr is examined for the task's expected clean/error condition;
- `user` exactly equals `DESKTOP-IRUC588\AgentAdmin`, `sessionId` is nonzero, and it equals the exact
  interactive session established by the status/readback for this run;
- the expected exit, effect, and authoritative readback all match the Ticket requirement.

For a `waitForExit=true` job, require an integer `exitCode` equal to the task-expected value and the
Worker contract relation `success == (exitCode == 0)`. An ordinary successful build or test therefore
requires `success=true` and `exitCode=0`. When the Ticket requires an intended rejection or other
negative result, its expected nonzero exit requires `success=false` and the exact nonzero result
`exitCode` and host `wait` exit code to match each other and the expected effect and readback. An
expected nonzero exit is not an automatic failure of the Ticket requirement.

For an intentional interactive GUI job with `waitForExit=false`, `exitCode=null` is expected and does
not fail the job. Require `success=true`, the completed task-specific UI actions, a screenshot locator,
the selected collected screenshot, and actual Lead PNG readback before accepting the requested effect
and authoritative readback. Do not apply the waited-process exit-code relation to this GUI shape.

A non-GUI result does not need a screenshot. A GUI screenshot is supporting observation, not a substitute
for the Ticket-required effect and authoritative product readback. Completion Record
`runtimeObservations` and `SOURCE_BOUND_MATERIALIZATION` retain only existing redacted summaries,
digests, and locators: never raw stdout, stderr, PNG bytes, credentials, passwords, or user data.

The guest Worker runs in the AgentAdmin interactive session at Highest. Its result is evidence of that
administrator-level interactive execution only; it is not evidence of standard-user behavior. A Ticket
requiring standard-user behavior remains `INCOMPLETE` under this profile unless a separate authorized
safe standard-user target and readback are available.

## Timeouts, Errors, And Recovery

Do not blindly replay an ambiguous action:

- After a submit timeout, inspect/read back the same JobId result through the bounded flow before any
  resubmit. Do not create a second job merely because submit's caller timed out.
- A wait timeout may repeat `wait` for the same JobId; it must not submit a replacement job.
- A sync failure abandons the unique run path and requires a new run ID and guest path.
- A collect failure is not success. Retain the failed observation as incomplete until selected result and
  readback can be collected or a new safe final exercise is performed.

`AgentBridgeLockTimeout` occurs before guest-session creation or a guest effect. Retry the identical
bounded call exactly once; a second lock timeout is `INCOMPLETE`. `AgentBridgeCredentialMissing`,
exhausted PowerShell Direct retry, and unavailable configured VM/worker channel are existing
`INCOMPLETE` environment/capability outcomes. After `AgentBridgeWallClockTimeout`, first perform
action-specific safe readback of the current state; do not blindly replay the action. If that readback
cannot establish a safe current state, return `INCOMPLETE`.

Route worker timeout exit `124` and worker execution failure exit `125` as unsuccessful
provisional/final runtime attempts, never as success. Route an application or test nonzero exit as task
feedback only after Lead source review unless it is the Ticket-authorized expected nonzero result above;
then require its exact result/host exit, effect, and readback. Use the existing bounded remediation,
new-initial-task, `BLOCKED`, or `INCOMPLETE` semantics as its actual cause requires.

Do not request a guest password, credential, UAC prompt, RunAs, host administrator approval, VM/user/
credential/Autologon/scheduled-task reconfiguration, SSH access, or external ports. Do not call
`activate` in ordinary work. Only after bounded retry and demonstrated actual PowerShell Direct or
interactive-worker channel recovery need, with reboot validation required, may the Lead use the bounded
supervisor's health-first `activate` action. A successful `activate` performs its own validation and
creates its validation checkpoint. The ordinary `checkpoint` action is forbidden unless the Ticket
explicitly requires it. If the configured recovery path cannot run without an unauthorized prompt or
approval, return `INCOMPLETE` rather than asking for it.

Installer, service, or other persistent effects require Ticket authority, a safe task-owned target,
independent authoritative readback, and product-supported cleanup with cleanup readback. Never make such
an effect merely to prove the environment.

## Completion Boundary

The final Windows observation is accepted only under the existing final-review gates: current planning
seal, source materialization identity exactly equal to `finalSourceIdentity`, equal pre/post source
identities, clear equal ownership snapshots with zero project delta, selected result JSON, requested
effect/readback, and cleanup/readback. Record it only in the existing
`completionRecord.runtimeObservations` with `executionTargetBinding.mode =
SOURCE_BOUND_MATERIALIZATION`; do not add raw bridge output or Windows-only schema.

This reference preserves the existing `BLOCKED`, `INCOMPLETE`, task-feedback, planning-currentness,
external-planning-workspace, Baseline Capsule, and Completion Record contracts with no Windows-only
schema.
