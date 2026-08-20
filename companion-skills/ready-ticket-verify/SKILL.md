---
name: ready-ticket-verify
description: "Dispatch one exact IIS Ready Ticket to the dedicated Verify Pi acceptance appliance by default, or run the preserved Main-owned lifecycle only when the caller explicitly requests DIRECT mode."
---

# Ready Ticket Verify Dispatcher

## Public contract

This is the public Ready Ticket verification entrypoint. Its default and normal mode is `PI`: collect the exact invocation, start the companion-owned Verify runner, validate its terminal envelope, independently confirm decision-critical state and the guarded Ticket progression, and report. Do not execute the verification lifecycle in Session Main and do not read the lifecycle references in `PI` mode.

`DIRECT` is a preserved compatibility mode only when the caller explicitly requests `DIRECT`, `Main direct`, or an equivalent unambiguous phrase. Never choose it as fallback when Pi admission, startup, execution, mutation guarding, or result validation fails.

Neither mode remediates product source, invokes implementation, or starts planning.

## Input closure

Resolve before dispatch:

- exact absolute canonical Ticket path;
- exact absolute Project Root from the Ticket;
- current bounded stable-target identity;
- optional candidate-target and implementation-report hints, navigation only;
- additional user instructions, or `None`;
- optional exact owner-model and owner-thinking overrides;
- complete AC Runtime Auditor configuration.

When no audit was requested and no count was supplied, use `auditors: []`. If an audit was requested but selection, AC, or linked authored-flow ordinals are incomplete, return the existing exact audit-configuration problem. Each active auditor is bound to one unique current AC and non-empty authored flow ordinals. An omitted per-AC model or thinking value resolves to the runner's pinned auditor default.

Owner model precedence is exact invocation `ownerModel`, then `IIS_READY_VERIFY_MODEL`, then the runner's pinned owner default. Owner thinking precedence is exact invocation `ownerThinking`, then the pinned `max` default. Auditor binding precedence is each explicit per-AC value, then `opencodex/gpt-5.6-luna` for model and `xhigh` for thinking. Explicit values are never replaced. The runner's Pi model/provider configuration lives under the user-local `~/.pi/agent/iis-ready-ticket/`; never copy credentials into the companion repository.

```text
acOrdinal
linkedFlows
model: optional exact provider/model; default opencodex/gpt-5.6-luna
thinking: optional off | minimal | low | medium | high | xhigh | max; default xhigh
oracleBrowser: false unless explicitly authorized
```

## PI mode — default

1. Resolve this installed skill's real directory and require executable `pi/iis-ready-verify-runner.mjs`. Do not use a generic Pi parent or natural-language agent selection.
2. Create one private mode-`0600` temporary invocation JSON with schema `iis.pi.ready-ticket-verify/v1`; never pass invocation content on the command line or log it:

```json
{
  "schema": "iis.pi.ready-ticket-verify/v1",
  "runId": "<unique OMP lifecycle run ID>",
  "ticket": "<absolute Ticket>",
  "projectRoot": "<absolute Project Root>",
  "targetIdentity": "<current bounded stable identity>",
  "candidateTarget": "<hint or None>",
  "implementationReport": "<hint or None>",
  "additionalInstructions": "<instructions or None>",
  "diagnosticReverify": false,
  "auditors": []
}
```

Add `ownerModel` and/or `ownerThinking` only for exact overrides; omitted owner values resolve to Luna Max. Populate `auditors` from the resolved caller-owned AC selection and linked flows. Omit an auditor model/thinking value only to select the pinned Luna XHigh default. Set `diagnosticReverify: true` only when the user explicitly requests diagnostic re-verification of an already-`done` Ticket; never infer it from Ticket status.

3. Start that exact executable as an OMP managed process with `--input <invocation.json>`. Use the companion repository root as `cwd`; do not background it through shell.
4. While the process is live, consume stderr through the process manager's cursor-based log follow. This is event-driven follow, not polling. Do not block on one exit wait before consuming progress. Require every non-empty runner stderr line to be a structured `iis.pi.progress/v1` event for the exact run ID whose first JSON field is the runner-generated safe `summary`. Track the highest accepted progress `sequence` and deduplicate replayed lower or equal sequences from the managed-process log; if a forward sequence gap appears, report the omitted interval without inventing its states. The runner already coalesces tool activity into low-frequency `OWNER_STATUS` transitions and exposes only aggregate `AUDITOR_STATUS`; relay each accepted `summary` as a meaningful lifecycle transition before process exit, and when reporting progress outside the managed log surface do not repeat raw JSON. A process-manager `follow timed out` transport note is not a Pi run failure; continue the same cursor-follow lifecycle. Render `RUN_ALIVE` only as elapsed time since the last observed runtime activity, never as model thinking or provider health. Never expose prompt, arguments, evidence body, reasoning, auditor handoff identity, or raw child stderr.
5. After terminal progress or managed-process exit, require exactly one final stdout object with schema `iis.pi.ready-ticket-run/v1`, matching run ID, mode `VERIFY`, agent `iis-ready-verify`, and session `none`.
6. A nonzero process exit, `processStatus` other than `COMPLETED`, malformed progress event, mutation-guard failure, missing canonical output, mismatched identity, or malformed workflow is a failed Pi run. Do not silently continue in `DIRECT` mode.
7. Independently re-read the exact Ticket, validator result, target identity, and guarded progression evidence. `NOT_STARTED`, `FAILED`, and `INCONCLUSIVE` must not produce `done`. `VERIFIED` is distinct from progression failure.
8. Remove the temporary invocation on every completion, failure, and cancellation path. Report the scenario/flow/AC denominator, evidence limits, auditor fan-in, whole-Ticket verdict, progression, postcondition result, and exact final Ticket status. Do not re-run verification in Main.

## DIRECT mode — explicit compatibility only

Only for an explicit `DIRECT` request:

1. Read `references/lifecycle.md` and `references/verify.md` in full.
2. For nonzero auditor count, also read `references/ac-runtime-auditors.md` in full.
3. Execute that preserved Main-owned lifecycle exactly, including its admission, scenario, audit, evidence, verdict, progression, output, and non-remediation boundaries.

The files under `references/` are the canonical lifecycle authority for both this explicit compatibility path and the dedicated Pi owner. The dispatcher contains no duplicate lifecycle policy.
