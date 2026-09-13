# PLAN-001: Three Exact Pro Model/Version Choices

## Contracts and current grounding

Applies to `tickets/TICKET-001.md`, its approved `SPEC.md`, `docs/planning/behavior/contexts/pro-model-version-selection.md`, and `docs/planning/behavior/contexts/oracle-browser-managed-slots.md`.

- EXISTING — `bin/oracle-cli.ts:1928-1970,2084-2147` resolves browser model input, restores parent browser config for followup, and currently applies only an explicit reasoning override. This is the public entry and the resume-policy owner.
- EXISTING — `src/cli/options.ts:338-460` distinguishes current GPT-6, GPT-5.6 Sol, and GPT-5.5 browser families; `src/cli/browserConfig.ts:26-54,101-140,166-204,258-270,328-349` maps canonical models to picker labels and separates `desiredModel` from `reasoningIntent`.
- EXISTING — `src/browser/index.ts:1508-1608,1625-1638,3202-3292` selects a model only for an initial conversation, runs reasoning immediately before every submission, and currently skips model selection for resumed conversations in both local and remote paths.
- EXISTING — `src/browser/actions/modelSelection.ts:34-125,127-217,223-1244` selects and verifies a requested model row but returns evidence without a reusable selected-row identity.
- EXISTING — `src/browser/actions/thinkingTime.ts:105-182,185-295,345-403,460-1109` separately selects Power and verifies model continuity. Its final Pro approval currently requires only the closed `6 Pro` pill, so explicit 5.6/5.5 Pro combinations cannot close truthfully.
- EXISTING — `src/sessionManager.ts:34-103`, `src/cli/sessionRunner.ts:129-199`, and browser runtime hints persist browser config plus model/reasoning evidence. Wrapper `oracle_browser_slots/runner.py:176-252` owns exact compatible slots and already yields `(1,2,10)` for Pro reasoning while preserving other relative orders.
- EXISTING — current read-only status at preparation time reports slots 1, 2, and 10 authenticated, unoccupied, and CDP-responsive. Live row availability remains runtime-sensitive and must be reread at final acceptance.
- PROPOSED — use the existing canonical model values as the public choice vocabulary: `gpt-6-pro` means requested choice `Latest` with observed resolution kept separate; `gpt-5.6-sol` means `GPT-5.6 Sol`; `gpt-5.5` means `GPT-5.5`. All three combine with `--browser-thinking-time pro`. No new public flag is needed.

No unresolved premise blocks source implementation. Exact live closed composer wording for explicit 5.6/5.5 is intentionally not assumed; checked row plus Power semantics are primary and the closed display is contradiction-only evidence.

## Obligations and preserved boundaries

Implement one coherent selection transaction without inventing a new picker or wrapper authority:

1. Normalize the three canonical model requests to exact current row labels while retaining requested choice separately from resolved display.
2. Capture a redacted model identity that represents the exact selected row (`Latest`, `GPT-5.6 Sol`, or `GPT-5.5`) and can be compared before/after Power selection. Keep dynamic `Latest` intent distinct from its current resolved model.
3. Make Pro approval depend on exact requested-row identity continuity plus `resolvedLevel=pro`; remove the `6 Pro`-only positive gate. A closed/equivalent composer signal may contradict a choice but may not replace row+Power proof.
4. For explicit browser followup model input, rebuild the resumed config with the requested row and select/verify it before that followup's submission. For omitted model input, keep current conversation selection but do not manufacture new requested/verified model evidence. Explicit reasoning follows the same existing override semantics.
5. Preserve managed-slot compatibility `(1,2,10)`, auto-order, original-slot followup, occupancy, and rejection behavior. Do not add slot migration or change slot 3/4/5 general capabilities.
6. Persist each attempt's model and reasoning evidence with turn/attempt attribution sufficient to distinguish explicit selection, omission, mismatch, and retry. Do not copy an earlier turn's success into the current turn.

## State, owners, and interfaces

- CLI owns requested canonical model plus whether model/reasoning were explicitly supplied on a followup. Extend `applyBrowserFollowupReasoning` or replace it with one narrow followup-selection policy that applies both explicit axes; omitted axes remove active selection intent rather than claiming it.
- `BrowserSessionConfig` carries selection intent into browser execution. Add only the minimum marker needed to distinguish an explicit resumed model request from inherited config; do not infer explicitness from `desiredModel` alone because parent config also contains it.
- `ensureModelSelection` owns requested-row selection/readback. Its evidence should carry the normalized exact requested choice and observed selected-row identity needed by the immediately following reasoning check. Extend existing `BrowserModelIdentityEvidence` rather than introducing a parallel evidence object if it can preserve redaction and compatibility.
- `ensureBrowserReasoning` owns Power selection and conjunction verification. Feed it the current turn's requested/observed row identity; compare the exact identity before/after slider action. Replace `closeReasoningControlAndReadProPill` with a semantic consistency readback that accepts all three valid tracks and rejects contradictory version/Power signals without relying on one literal.
- Browser local and remote execution branches are duplicate consumers of this policy and must change together. The submission gate remains immediately before `submitPrompt` for initial prompt and each in-run browser followup.
- Session runner remains persistence owner. Preserve ordered histories and the latest evidence while ensuring current-turn model evidence is not stale on resume or retry.

## Change structure

1. Correct canonical row mapping and exact matchers: map GPT-5.5 to current `GPT-5.5`, retain GPT-5.6 Sol and Latest mappings, and remove legacy Pro-as-model matching from these three canonical requests.
2. Enrich selected-row identity/evidence at `ensureModelSelection`; expose the same bounded row-read helper to reasoning verification so both use one semantic identity vocabulary.
3. Change Pro reasoning verification to require exact requested/current row identity and Power maximum, with closed display used only for contradiction detection. Fail `unavailable`, `ambiguous`, `model-changed`, or `model-mismatch` before submission.
4. Apply explicit resumed model selection in both browser execution branches and bind evidence to the current submission turn. Omitted followup model intent must not rerun selection or claim a requested choice.
5. Update CLI followup assembly so a CLI-provided model is not overwritten by the parent model before browser config creation, while default/omitted model remains inherited current state without asserted selection.
6. Keep wrapper routing code unchanged unless focused checks expose a canonical-token mismatch; its existing Pro matrix is the preserved boundary.

Partial failure remains pre-submit. A failed selection attempt may retry within existing bounded retry counts; dependent prompt submission and attachment side effects remain forbidden until the current attempt verifies. After a prompt has been submitted, do not add a model-selection retry that can duplicate it.

## Checks and readback

Run focused checks in this order:

1. CLI/config checks prove the three canonical values project to exact rows plus independent Pro intent, and followup explicit-vs-omitted model policy is preserved.
2. Model-selection checks prove exact single-row matching for Latest/5.6 Sol/5.5, reject wrong/multiple/absent checked states, and emit distinguishable requested/resolved identity.
3. Reasoning-selection checks prove each selected row survives Power change, all three can verify Pro without a `6 Pro` literal, contradictory row/display or identity drift fails, and turn/attempt evidence remains attributable.
4. Browser execution checks cover both local and remote initial/resume branches: explicit resumed model selection occurs before reasoning and submission; omitted model does not fabricate selection; a failed conjunction prevents `submitPrompt`.
5. Wrapper focused checks preserve `(1,2,10)`, `1→2→10`, explicit 3/4/5 rejection and same-origin followup.
6. Run the actual built CLI dry-run/preview for each canonical model plus Pro to inspect projected control intent without submitting a prompt.
7. Final verifier uses fresh authenticated slot state. Exercise at least one eligible managed slot per real live combination where external availability permits, inspect current rows on all slots 1/2/10, and run a same-origin explicit changed-choice followup. Use unique nonce prompts, capture session paths/evidence, and verify failed controlled mismatches leave no submitted user turn. The verifier, not implementation, owns final live verdict and cleanup/readback.

## Local discretion and return conditions

Names of private helpers and exact evidence field layout are worker discretion if existing stored metadata remains readable and the Ticket observations are preserved. Do not add telemetry, a new model registry, a workflow layer, or wrapper-side DOM verification.

Return to this Plan owner before dependent implementation if current UI exposes a different row identity model than `Latest | GPT-5.6 Sol | GPT-5.5`, if exact row identity cannot be read independently of the closed pill, if explicit model changes are disallowed by ChatGPT on resumed conversations, or if satisfying the contract requires changing wrapper slot policy. Return to Behavior/Spec authority if the observable meaning of omitted followup choice or dynamic Latest would need to change.
