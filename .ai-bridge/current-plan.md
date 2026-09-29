# OpenCodex 2.19.0 upgrade

Updated: 2026-08-15T11:56:11.650Z
Workspace: /mnt/d/개발방법론/개발방법론
Target agent: Codex (codex)

## Plan

Goal: Upgrade the local production OpenCodex from the currently documented 2.15.0 + four local runtime patches to exact 2.19.0 while preserving the user's custom behavior and existing config/ledger. This plan is authoritative for execution/review; do not weaken any gate merely to complete the upgrade.

Required patch order (only for patches still required on 2.19.0):
1) post-header stream telemetry
2) translator budget 128MiB (re-evaluate against 2.19.0's explicit 256MiB Bun request-body limit and any upstream translator limit changes; do not blindly preserve a stale 128MiB policy if upstream behavior now supersedes the old fix—preserve the user's original intent: no duplicate charging, bounded overflow, and safe large requests)
3) usage measured-only breakdown
4) Chat Completions service_tier forwarding

Execution gates:
A. Record current version, health/ready/service/routing state, listener, non-secret config fields, disabledModels sorted set/hash, provider count, streamMode/fastMode, usage ledger bytes/rows/hash/summary, production runtime manifest, dependency tree, and current patch hashes. Preserve secrets; config backup mode 0600 and change dir 0700.
B. Verify @bitkyc08/opencodex@2.19.0 metadata (version, integrity, shasum, gitHead, tarball) and official v2.19.0 tag commit. Fetch pristine npm tarball twice (A/B) and official source checkout matching gitHead. Compare common runtime source tarball↔official tag.
C. Inspect 2.19.0 source for each of the four local behaviors before applying anything. Mark each as upstream-included / still-needed / behavior-changed. Specifically inspect new responses_websockets path: determine whether existing streamTelemetry covers WebSocket attempts/fallback/SSE, whether any telemetry patch needs adaptation, and ensure patch does not alter retry/routing semantics. Inspect request-body max (reported 256MiB), translator request_copies accounting and overflow mapping, measured-only usage breakdown, and service_tier forwarding. Do not apply obsolete code.
D. Create target-version v2.19.0 patch artifacts only for still-needed changes. Each artifact needs a fresh recorded SHA-256 even if byte-identical. Apply every required patch on fresh A and B in the fixed order, with git apply --check before apply. Require A/B runtime manifests to match and git diff --check to pass.
E. On official source checkout, apply the exact runtime patches plus test-only fixture adaptations when upstream tests encode superseded vanilla behavior. Run typecheck and focused tests covering translator budget/body size, responses WebSocket/SSE fallback + telemetry/request logging, usage summary/log persistence, Chat completions service tier, tool-call round trips, and service/routing if available. Test-only fixture changes must never enter production runtime.
F. Prepare full rollback package backup including node_modules and config/ledger snapshots. Rehearse an isolated restoration/diff before cutover.
G. Quiesce clients using 127.0.0.1:10100, stop host-proxy only if needed, verify established connections are zero, then ocx stop and confirm process/listener gone. Do not start install if quiescence is uncertain.
H. Install exact `npm install -g @bitkyc08/opencodex@2.19.0`; never use moving `latest` for this cutover. Before service start, verify exact version, pristine runtime manifest, and resolved node_modules against an isolated exact install.
I. Deploy authoritative patched A runtime (package.json/bin/src/gui/dist/assets or the exact runtime areas appropriate to 2.19.0), retaining the exact-install node_modules. Verify production runtime equals authoritative A and dependencies equal isolated install. If direct git apply to production is used instead, every patch must pass --check and final manifest must still equal A.
J. Run `ocx service repair`, then service/status/ready/health and verify protected/reboot-safe/routing/listener/version. Restore host-proxy if it was stopped.
K. Production validation before client traffic resumes: (1) actual Linux ChatGPT Codex request exercises the new WebSocket-preferred path if selectable/observable; verify first-token path/fallback logging without forcing unsupported policy; (2) SSE fallback path remains functional; (3) stream telemetry persists on the actual production path(s) and correlation IDs/outcome/raw timing fields remain meaningful; (4) translator accounting is single-charge and bounded under 2.19.0 semantics; distinguish Bun 256MiB front-door rejection from translator cap; (5) Chat `service_tier` priority/default matrix remains intact; (6) usage full-range keeps requests/unreported counts while breakdown remains measured-only and historyTruncated=false; (7) ledger pre-cutover prefix is byte-for-byte preserved; (8) managementUsageMaxReadBytes, disabledModels canonical set, providers, streamMode/fastMode, accounts/API keys are preserved except source-justified catalog enrichment; (9) representative tool-call/Responses round trip smoke passes.
L. Roll back immediately to the complete 2.15.0-patched package if any required patch cannot be proven compatible, production manifest/dependency verification fails, service/health/ready/routing fails, credentials/config are lost, ledger prefix changes/truncates, or required functional validation fails. Do not blindly overwrite config on code rollback; restore config only if actually damaged after checking current credentials.
M. Update the Obsidian OpenCodex docs with a 2.19.0 plan and an execution record containing exact evidence, deviations, patch disposition (upstream vs local), hashes/manifests, tests, production request IDs, and rollback artifacts. If execution cannot be performed by the local agent environment, record exactly where it stopped and what remains unexecuted; do not claim completion.

## Implementation contract

- Work from this plan in small, reviewable steps.
- Keep edits scoped to the requested task and existing project conventions.
- Run focused verification before handing work back.
- Update .ai-bridge/agent-status.md with files touched, checks run, results, blockers, and review notes.
- Save the final review diff to .ai-bridge/implementation-diff.patch when practical.
- Append notable execution events to .ai-bridge/execution-log.jsonl when the implementation agent supports logging.
