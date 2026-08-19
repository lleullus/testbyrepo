---
name: ready-ticket-implement
description: "Dispatch one exact IIS Ready Ticket to the dedicated Implement Pi appliance by default, or run the preserved Main-owned lifecycle only when the caller explicitly requests DIRECT mode."
---

# Ready Ticket Implement Dispatcher

## Public contract

This is the public Ready Ticket implementation entrypoint. Its default and normal mode is `PI`: collect the exact invocation, start the companion-owned Implement runner, validate its terminal envelope, independently confirm decision-critical state, and report. Do not execute the implementation lifecycle in Session Main and do not read the lifecycle references in `PI` mode.

`DIRECT` is a preserved compatibility mode only when the caller explicitly requests `DIRECT`, `Main direct`, or an equivalent unambiguous phrase. Never choose it as fallback when Pi admission, startup, execution, or result validation fails.

Neither mode performs verification, writes Ticket `done`, or starts planning.

## Input closure

Resolve before dispatch:

- exact absolute canonical Ticket path;
- exact absolute Project Root;
- current bounded target identity;
- additional user instructions, or `None`;
- optional exact owner-model and owner-thinking overrides;
- complete implementation auditor configuration.

When no audit was requested and no count was supplied, use `auditors: []`. If audit was requested but count, role, slot, or assignment is incomplete, return the existing exact audit-configuration problem. Implement permits 0-3 uniquely named slots. An omitted per-slot model or thinking value resolves to the runner's pinned auditor default instead of becoming a configuration gap.

Owner model precedence is exact invocation `ownerModel`, then `IIS_READY_IMPLEMENT_MODEL`, then the runner's pinned owner default. Owner thinking precedence is exact invocation `ownerThinking`, then the pinned `max` default. Auditor binding precedence is each explicit per-slot value, then `opencodex/gpt-5.6-luna` for model and `xhigh` for thinking. Explicit values are never replaced. The runner's Pi model/provider configuration lives under the user-local `~/.pi/agent/iis-ready-ticket/`; never copy credentials into the companion repository.

Each active slot contains:

```text
slot
assignment
model: optional exact provider/model; default opencodex/gpt-5.6-luna
thinking: optional off | minimal | low | medium | high | xhigh | max; default xhigh
oracleBrowser: false unless explicitly authorized
```

## PI mode — default

1. Resolve this installed skill's real directory and require executable `pi/iis-ready-implement-runner.mjs`. Do not use a generic Pi parent or natural-language agent selection.
2. Create one private mode-`0600` temporary invocation JSON with schema `iis.pi.ready-ticket-implement/v1`; never pass invocation content on the command line or log it:

```json
{
  "schema": "iis.pi.ready-ticket-implement/v1",
  "runId": "<unique OMP lifecycle run ID>",
  "ticket": "<absolute Ticket>",
  "projectRoot": "<absolute Project Root>",
  "targetIdentity": "<current bounded identity>",
  "additionalInstructions": "<instructions or None>",
  "auditors": []
}
```

Add `ownerModel` and/or `ownerThinking` only for exact overrides; omitted owner values resolve to Luna Max. Populate `auditors` from the resolved caller-owned selection, roles, and assignments. Omit an auditor model/thinking value only to select the pinned Luna XHigh default.

3. Start that exact executable as an OMP managed process with `--input <invocation.json>`. Use the companion repository root as `cwd`; do not background it through shell. Wait through the process manager without polling.
4. Treat stderr as progress only. Require exactly one final stdout object with schema `iis.pi.ready-ticket-run/v1`, matching run ID, mode `IMPLEMENT`, agent `iis-ready-implement`, and session `none`.
5. A nonzero process exit, `processStatus` other than `COMPLETED`, missing canonical output, mismatched identity, or malformed workflow is a failed Pi run. Do not silently continue in `DIRECT` mode.
6. Independently re-read the exact Ticket and decision-critical product state named by the envelope. Require implementation never changed Ticket `Status: ready` to `done`; classify evidence limits exactly.
7. Remove the temporary invocation on every completion, failure, and cancellation path. Report the terminal envelope's implementation outcome, self-check/runtime evidence, auditor fan-in, changed scope, remaining uncertainty, and unchanged Ticket status. Do not re-run the implementation in Main.

## DIRECT mode — explicit compatibility only

Only for an explicit `DIRECT` request:

1. Read `references/lifecycle.md` and `references/implement.md` in full.
2. For nonzero auditor count, also read `references/concurrent-auditors.md` in full.
3. Execute that preserved Main-owned lifecycle exactly, including its authority, audit, self-check, fan-in, output, and Ticket-status boundaries.

The files under `references/` are the canonical lifecycle authority for both this explicit compatibility path and the dedicated Pi owner. The dispatcher contains no duplicate lifecycle policy.
