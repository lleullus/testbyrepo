# PLAN-001: Three Exact Pro Model/Version Choices

## Contracts and current grounding

Applies to `tickets/TICKET-001.md`, its approved `SPEC.md`, `docs/planning/behavior/contexts/pro-model-version-selection.md`, and `docs/planning/behavior/contexts/oracle-browser-managed-slots.md` under canonical Project Root `/home/user01/project/oracle`.

- CURRENT SOURCE — `src/cli/browserConfig.ts` maps `gpt-6-pro` to requested `Latest`, `gpt-5.6-sol` to `GPT-5.6 Sol`, and `gpt-5.5` to `GPT-5.5`; `src/cli/followup.ts` distinguishes explicit resumed model intent from omission.
- CURRENT SOURCE — `src/browser/actions/modelSelection.ts` already emits `requestedChoice`, `selectedRow`, and `selectedModelIdentity` for non-`current` selection, and `src/browser/actions/thinkingTime.ts` already combines selected-row identity continuity with Power=`Pro` while treating the closed display as contradiction-only.
- CURRENT SOURCE — `src/browser/index.ts` selects on initial runs and on resumed runs with `explicitResumeModel=true`; omitted resumed model intent emits non-assertive skipped evidence.
- CURRENT WRAPPER — `oracle-browser-slots/oracle_browser_slots/runner.py` statically requires and injects `--browser-model-strategy current` for every managed request. `modelSelection.ts` intentionally does not click/read an exact row under `current`, so all three canonical managed Pro requests bypass the new exact-row proof.
- FRESH VERIFIER EVIDENCE — `agent://ReverifyProChoices` reproduced successful prompt submission with `modelSelection.verified=false`; GPT-5.6 Sol remained on Latest, GPT-5.5 projected as legacy Thinking 5.5, and explicit changed-choice followup skipped row selection. Slot/origin preservation and explicit 3/4/5 rejection remained correct.
- DEPLOYED ARTIFACT — canonical `oracle` executes this checkout's ignored `dist/bin/oracle-cli.js`; current `dist/` still contains pre-change model/followup behavior. Source correction alone therefore cannot change the acceptance runtime.

The residual defect has two causes, both inside the approved Ticket: the wrapper forces a strategy that cannot satisfy an explicit exact-row request, and the canonical compiled runtime is stale. No product meaning, public choice vocabulary, slot eligibility/order, or followup-origin policy changes.

## Obligations and preserved boundaries

1. For only the canonical exact Pro requests owned by this Ticket—`gpt-6-pro`, or `gpt-5.6-sol`/`gpt-5.5` combined with explicit Pro reasoning—the wrapper must require/inject `--browser-model-strategy select`, allowing Stock Oracle to choose and verify the requested row. Other existing wrapper request families retain their current strategy unless their own contract already supplies a compatible explicit value.
2. Keep wrapper transport conflict handling fail-closed: duplicate strategy values or a caller value conflicting with the strategy derived for that exact request are rejected before claim/child execution. Do not accept `ignore` or silently downgrade an exact Pro request to `current`.
3. Keep Stock's exact-row proof authoritative: the wrapper chooses transport flags but never performs DOM verification. `ensureModelSelection` must continue to require the one checked requested row for explicit canonical requests, and `ensureBrowserReasoning` must require that row identity to survive Power selection before submission.
4. Preserve the current explicit/omitted followup contract. An explicit canonical model followup uses `select` on the original slot/profile/conversation and obtains fresh turn/attempt row+Power evidence; omitted model or Power axes remain non-assertive and do not fabricate a request or verified result.
5. Preserve managed-slot compatibility `(1,2,10)`, auto-order `1→2→10`, original-slot followup, occupancy, and explicit 3/4/5 rejection. Do not add slot migration, change general slot capability, or alter unrelated model/reasoning routes.
6. Rebuild the canonical ignored `dist/` runtime from the final source using the repository's existing package build. The runtime artifact, not source text alone, must contain the corrected exact row mappings, explicit-resume policy, combined row+Power gate, and wrapper-selected strategy behavior used by the canonical executable.

## State, owners, and interfaces

- `JobRunner._validated_oracle_command` owns the canonical wrapper transport strategy. Derive the expected strategy from the already parsed single model and reasoning arguments: use `select` for the exact Ticket-owned Pro combinations and preserve `current` otherwise. Centralize parsing enough that compatibility and strategy derivation cannot disagree about the same request, without creating a model registry or changing the public CLI.
- Wrapper validation continues before claim. The derived expected strategy participates in the existing duplicate/conflict checks and is injected exactly once when omitted.
- Stock CLI remains owner of requested model/version and followup explicitness. Wrapper selection does not rewrite the requested token.
- `ensureModelSelection` remains owner of native picker interaction and checked-row identity. `ensureBrowserReasoning` remains owner of native Power interaction and identity continuity. Wrapper metadata remains owner of slot/origin evidence.
- Source and compiled `dist/` are one delivery target for this Ticket because `/home/user01/.nvm/versions/node/v24.18.0/bin/oracle` resolves into this checkout's compiled CLI.

## Change structure

1. Re-ground and retain the already implemented Stock source changes; do not redo or weaken them.
2. In `oracle-browser-slots/oracle_browser_slots/runner.py`, replace the static model-strategy expectation with a request-derived value: `select` exactly for `gpt-6-pro`, `gpt-5.6-sol + Pro`, and `gpt-5.5 + Pro`; `current` for unaffected requests. Apply that value to both caller conflict validation and missing-flag injection before slot claim.
3. Add focused wrapper behavior checks covering all three canonical Pro combinations, caller omission/injection, matching explicit `select`, conflicting explicit `current`/`ignore`, unchanged non-Ticket requests, `(1,2,10)` ordering, 3/4/5 rejection, and original-slot followup.
4. Run focused Stock checks for exact row mapping/readback, row+Power conjunction, explicit versus omitted resume in both browser branches, and no-submit failure behavior. Fix only Plan-consistent defects in the current implementation.
5. Run the repository package build once after final source changes so the canonical `dist/` runtime is current. Directly compare the compiled modules used by `dist/bin/oracle-cli.js` against the source-owned behaviors: GPT-5.5=`GPT-5.5`, checked-row identity, contradiction-only closed display, explicit resumed selection, omitted non-assertion.
6. Run canonical CLI dry-run/preview for the three model tokens plus Pro and wrapper no-prompt routing checks. Handoff the exact current source, wrapper, and compiled artifact identities to a fresh verifier.

Partial failure remains pre-submit. A failed selection attempt may retry only within existing bounded pre-submit retries. No change may submit before fresh exact-row+Power proof, add wrapper-side DOM inspection, or duplicate a prompt after submission.

## Checks and readback

1. Wrapper argv checks distinguish canonical exact Pro requests from unaffected requests and prove the derived strategy is enforced before claim.
2. Stock model-selection checks prove one exact checked row for Latest/5.6 Sol/5.5 and reject wrong, multiple, absent, or unresolved states.
3. Reasoning checks prove row identity survives Power=`Pro`, all three tracks pass without a literal `6 Pro` positive gate, and contradictions/drift fail before submission.
4. Local and remote browser execution checks prove explicit resume selects before reasoning/submission while omitted axes stay non-assertive.
5. Wrapper preservation checks prove `(1,2,10)`, `1→2→10`, explicit 3/4/5 rejection, original-slot followup, and no cross-slot fallback.
6. Build readback proves canonical `dist/` contains and executes the same corrected policy; source-only test success is insufficient.
7. The fresh verifier reruns real initial combinations and same-origin explicit/omitted followups with unique nonce prompts, inspects current live rows and Stock/Wrapper evidence, verifies controlled mismatch no-submit behavior, and completes slot/process cleanup.

## Local discretion and return conditions

Private helper names and exact parsing reuse are worker discretion. Keep the change direct; do not add a flag registry, generic policy layer, telemetry, workflow state, or wrapper-side browser evidence.

Return to the Plan owner if satisfying the exact Pro combinations requires changing slot eligibility/order, cross-slot followup behavior, public model vocabulary, omitted-axis semantics, or Stock/Wrapper evidence ownership. A different current ChatGPT row identity or inability to select an explicit row on a resumed conversation also requires return. Ordinary implementation-local fixes to the request-derived wrapper strategy, existing Stock gate, tests, or compiled artifact remain inside this plan.
