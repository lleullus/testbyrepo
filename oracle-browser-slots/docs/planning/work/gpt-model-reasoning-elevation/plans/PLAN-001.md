# TICKET-001 실행 계획 — GPT 모델 및 Pro 추론 승격 지원

## Purpose

`TICKET-001.md`의 승인된 결과를 구현하기 위한 실행 방법을 정의한다. 목표는 `oracle-browser-slots`가 `--model`, `-m`으로 요청된 `gpt-5.5`, `gpt-5.6-sol`, `gpt-6`, `gpt-6-pro`와 reasoning intent를 계정 capability에 맞는 슬롯으로 결정론적으로 라우팅하고, Stock Oracle이 `gpt-6-pro`를 `gpt-5.6-sol`로 무음 치환하지 않으며, ChatGPT의 5단계 Radix slider가 만드는 `6 Pro` 승격을 엄격한 검증을 유지한 채 정상 결과로 인정하게 하는 것이다.

완료 조건은 소스 수정만이 아니다. Stock TypeScript 빌드 산출물 `dist/bin/oracle-cli.js`를 갱신하고, 지정된 pytest/vitest 회귀 표면을 통과한 다음, 슬롯 2의 실제 Pro 계정에서 `gpt-6-pro + pro` 요청이 `completed`로 끝나며 해당 실행의 `meta.json`에 `reasoningSelection.resolvedLevel: "pro"`, `verified: true`가 기록되어야 한다.

### Preserved behavior and non-goals

- 관리 슬롯 집합은 비연속 집합 `(1, 2, 3, 4, 5, 10)`으로 유지하고 슬롯 10은 항상 같은 capability 후보군의 마지막에 둔다.
- standard/medium, high/extended, instant/light/low, extra-high/heavy/pro의 기존 상대 우선순위를 보존한다.
- `pro` reasoning 또는 `gpt-6-pro`를 Plus 슬롯 3, 4, 5로 보내지 않는다.
- `--browser-model-strategy current` 정책과 예상하지 못한 모델 변경에 대한 fail-closed 검증을 유지한다. `pro` 요청이라는 이유만으로 모든 fingerprint 불일치를 허용하지 않는다.
- `--models` 다중 모델 API 기능은 추가하지 않는다. wrapper는 값 개수·형식과 무관하게 이 flag provenance를 인식해 browser managed-slot compatibility 단계에서 거절해야 한다.
- `followup.py`, `originating_slot` 스키마, 부모 세션 완전 일치 비교를 변경하지 않는다. 모델/reasoning을 슬롯 영속 상태나 lineage dict에 추가하지 않는다.
- API 모드의 GPT-6 지원, 가격·토큰 한도·provider 모델 등록은 이 Ticket의 범위가 아니다. `gpt-6-pro` 인식은 browser engine 경로에서만 무음 폴백을 제거한다.

## Applicable Contracts & Anchors

### Product authority

- Ticket: `/home/user01/project/oracle/oracle-browser-slots/docs/planning/work/gpt-model-reasoning-elevation/tickets/TICKET-001.md` (`Status: ready`; AC 1–10).
- Parent Spec: `/home/user01/project/oracle/oracle-browser-slots/docs/planning/work/gpt-model-reasoning-elevation/SPEC.md` (`Status: approved`).
- Behavior authority: `/home/user01/project/oracle/oracle-browser-slots/docs/planning/behavior/contexts/oracle-browser-managed-slots.md`, 특히 슬롯 집합과 capability 순서를 규정한 Behavior Model 17–28행.
- Investigation evidence: `/home/user01/project/oracle/oracle-browser-slots/docs/investigation/gpt-model-reasoning-elevation/INV-001.md`, Finding 1–9 및 Inference 1–3.
- 현재 authority inspection: Ticket SHA-256 `991c14e74d1669d97068e6692391da7cdff6db2f44b9734f9b43c47ecb753071`, authority digest `af877cb7bf73081e583eca7a2542c82f4b84e47712c0b425f8f3b4389c1289d4`.

### Current load-bearing code and data flow

1. `/home/user01/project/oracle/oracle-browser-slots/oracle_browser_slots/runner.py`
   - `MODEL_FLAGS`(현재 36행): wrapper가 child argv에서 모델 옵션을 찾는 유일한 flag 집합이다.
   - `JobRunner.compatible_slots()`(176–207행): 모델 허용과 reasoning별 슬롯 후보 순서를 함께 결정하며, `run`, `submit` allocation, `followup` compatibility가 이 판단을 소비한다.
   - `_option_values()`(653–672행): 분리형 및 `--flag=value`의 값만 수집하고 `--` 뒤 child payload는 검사하지 않지만, flag provenance와 missing occurrence를 보존하지 않는 현재 parser 경계다.
2. `/home/user01/project/oracle/src/cli/runOptions.ts`
   - `resolveRunOptionsFromConfig()`(35–146행): 현재 browser engine의 단일 model은 `inferModelFromLabel()`과 `normalizeChatGptModelForBrowser()`를 통해 `gpt-6-pro` canonical id를 보존한다. 반면 non-empty `models`는 `resolveApiModel()` 목록이 되고 `fixedEngine = "api"`를 강제하므로 wrapper가 `--models` provenance를 잃으면 managed-browser 경계를 우회한다.
3. `/home/user01/project/oracle/src/cli/options.ts`
   - `resolveApiModel()`(226–307행)은 browser-only GPT-6 id를 API 지원 모델로 등록하지 않는다. `parseBrowserGpt6Label()`/`inferModelFromLabel()`(318–450행)은 현재 `gpt-6`, `gpt-6-pro`와 동등 표기를 generic Pro fallback보다 먼저 보존한다.
4. `/home/user01/project/oracle/src/cli/browserConfig.ts`
   - `BROWSER_MODEL_LABELS`(26–54행), `normalizeChatGptModelForBrowser()`(101–141행), `resolveBrowserModelLabel()` 소비 경로는 현재 `gpt-6`/`gpt-6-pro` browser canonical id를 허용하고 picker target을 `Latest`로 둔다. 이 existing canonicalization은 HF-1~3에서 변경하지 않는다.
5. `/home/user01/project/oracle/src/browser/actions/thinkingTime.ts`
   - `ensureBrowserReasoning()`(103–178행): prompt 제출 전 최종 evidence와 `verified`를 판정한다.
   - `evaluateBrowserReasoningSelection()` 및 native input driver(181–352행): reasoning control을 열고 `Input.dispatchMouseEvent`로 slider step을 실행하며 fresh outcome을 읽는다.
   - `stableModelFingerprint()`(495–510행): reasoning owner의 checked version-bearing item과 닫힌 version-bearing composer pill에서 단 하나의 active identity를 요구한다.
   - owner/control discovery와 초기 identity gate(530–641행, 736–807행), elevation/readback loop(720–735행, 846–938행): `ping-13`의 null/null `model-mismatch`가 발생한 현재 fail-closed 경계다.
6. `/home/user01/project/oracle/src/browser/actions/modelSelection.ts`
   - `isReasoningOnlyLabel()`(136–149행): `6 Pro` 계열 reasoning pill을 model picker intent로 오인하지 않게 하는 입구 가드다.
7. `/home/user01/project/oracle/src/browser/index.ts`
   - `ensureBrowserReasoning()` 호출부(1556–1569행, 3241–3254행): 두 실행 경로 모두 기존 `Runtime`과 CDP `Input` domain 및 Node-side `originalModelIdentity`를 전달한다.
8. `/home/user01/project/oracle/src/browser/config.ts`, `/home/user01/project/oracle/src/browser/types.ts` 및 wrapper slot environment
   - `resolveBrowserConfig()`/`resolveManagedBrowserSlotCapability()`/`assertManagedBrowserReasoningIntent()`(`config.ts` 78–104, 182–247행): `ORACLE_BROWSER_SLOT_ID`를 capability로 바꾸고 managed guard를 적용하지만 현재 1–5만 열거하여 `10`은 `null`이 되고 guard를 우회한다.
   - `BrowserManagedSlotCapability.slotId`(`types.ts` 24–29행): 현재 union이 `1 | 2 | 3 | 4 | 5`라서 승인된 관리 슬롯 10을 표현하지 못한다.
   - wrapper `SlotService.job_environment()`(`service.py` 733–739행)는 실제 child에 `ORACLE_BROWSER_SLOT_ID`, slot port, remote endpoint를 공급하고, `model.py`의 `SLOT_IDS`와 `Settings.slot()`(15, 206–213행)은 slot 10을 port `19231`/profile `slot-10`으로 계산한다. 이 existing producer/endpoint/profile 경계를 Stock capability consumer와 일치시켜야 한다.
9. 테스트 표면
   - wrapper: `oracle-browser-slots/tests/test_slots.py`, 특히 `JobRunnerTests.test_compatible_slots_use_exact_model_and_reasoning_capabilities`.
   - Stock: `tests/browser/modelSelection.test.ts`, `tests/browser/thinkingTime.test.ts`, `tests/browser/reasoningSelection.test.ts`, browser model canonicalization의 `tests/cli/options.test.ts`·`tests/cli/browserConfig.test.ts`, managed slot capability의 `tests/browser/config.test.ts`.
10. 빌드/실행 표면
   - `/home/user01/project/oracle/package.json`의 `build` script는 TypeScript를 `dist`로 컴파일한다.
   - 설치 CLI `/home/user01/.nvm/versions/node/v24.18.0/bin/oracle`은 `/home/user01/project/oracle/dist/bin/oracle-cli.js`를 실행하므로 build 이후 라이브 smoke를 수행해야 한다.

### Cause hypothesis, competing explanations, decisive observations

- **EXISTING — authoritative failure and preserved boundary.** `ping-13/meta.json` is the exact live run readback: `status: error`, reasoning `status: model-mismatch`, `originalModelIdentity: null`, `observedModelFingerprint: null`, `controlCount: 1`, `matchingControlCount: 0`, `observedKinds: ["slider"]`, `promptSubmitted: false`. Slot 2 remained available with `occupancy: null`. This proves failure before slider interaction/elevation and prompt submission; it does not prove that CDP pointer dispatch or the approved elevation branch is defective. `ping-12` is not substitute acceptance evidence: it is a different still-`running` session whose verified-true identity may include pre-existing/manual UI state. The fake-DOM PASS likewise proves only that the current algorithm succeeds when fixtures supply a checked, version-bearing model node; it does not prove that live DOM supplies that signal.
- **UNRESOLVED — primary cause hypothesis.** The live reasoning owner found by `REASONING_OWNER_SELECTOR` contains the slider but, at the identity-capture instant, contains no version-bearing `[role="menuitem"]`/`[role="menuitemradio"]` with `aria-checked="true"` or `data-state="checked"`; the only closed composer pill may be the reasoning-only `6 Pro` token, which is intentionally excluded. This directly explains both null identities and `matchingControlCount: 0`. Smallest discriminating observation: a prompt-free CDP `Runtime.evaluate` readback, bound to the exact slot-2 target and current dist/source bytes, records the selected-state attributes and bounded semantic text of model/effort rows, closed composer pills, reasoning-owner ancestry, `aria-controls` links, and the same data at closed, model-menu-open, and reasoning-control-open phases.
- **UNRESOLVED — competing hypotheses.** (a) The latest UI moved the active base-model signal to a changed `menuitemradio`/`option` structure or renamed composer-pill token not covered by current selectors/canonicalization. (b) The signal exists, but `openReasoningControlWithNativeClick()` changes/replaces the owner before `stableModelFingerprint()` reads it, so owner/scope timing loses a previously observable identity. (c) A transient/multiple-owner state makes the selected row invisible or out of the chosen owner. The phase-bound probe refutes the primary hypothesis if exactly one stable selected base-model signal exists within the current owner at capture time; it favors structure/token change if a unique selected signal exists only under a new role/attribute or closed base pill; it favors timing/scope if the signal exists before opening and disappears or moves afterward. If no unique live base-model signal exists in any phase, requested model text, catalog hashing, `Latest`, null sentinels, or broad elevation exemption remain forbidden substitutes.
- **PROPOSED — method after discrimination.** Change only the narrow identity producer/owner boundary evidenced by that probe: consume one live, active base-model signal and preserve null on absence/conflict. Then keep exact identity equality as the normal path and permit `6 Pro` elevation only for `TARGET === "pro"`, one slider at Pro/max, exact closed `6 Pro` pill, and non-null before/after base identities. Slider interaction remains native `Input.dispatchMouseEvent` with fresh geometry and post-click DOM readback; RPC success alone is never success.

### Code Grounding and r5 REVISE normalization (R1–R4)

- **R1 — Normalize.** 현재 결합 대상은 Plan SHA `828c297672a8fbfd09b21d28a75f470cdc3e33f73230c482cb07f3152cbcf6e0`에 대한 r5 `REVISE`(review artifact SHA `4bb0ecc0aee2a1a9fe332355108268758ead1ee2ada19f18b45459a763eb9907`)의 단일 조건이다. SHA `42e4c08c…`의 구 `ADMIT`과 r2/r3/r4 `REVISE`는 이 개정 바이트의 admission이 아니다. r5 조건은 initial max 분기에서 합성 lower baseline을 원래 상태로 오인하지 않도록 immutable `preProbeOriginal`, 별도 `temporaryLowerBaseline`, baseline 왕복 및 최종 원상복귀를 하나의 최종상태 계약으로 명시하는 방법 결함이다. closure owner는 Planner → affected Heuristic → independent Plan Reviewer이며 Planner는 ADMIT이나 검증 판정을 발행하지 않는다.
- **R2 — Reinspect.** 이번 개정에서 Ticket·Spec·Behavior·INV-001·SHA `828c2976…` 현 Plan·r5 JSON 전체를 직접 다시 읽고, 특히 Conditional first work의 initial-max 문장과 CDP retry duplicate-effect 문장을 대조했다. 전자는 lower stable snapshot을 `before`로 덮어쓴 뒤 max→before만 복원하고 후자는 lower baseline을 만든 뒤 max로 복원한다고 읽혀 최종 기준이 충돌하며, 어느 쪽도 원래 max 상태를 별도 immutable snapshot으로 보존하고 마지막에 전필드 equality로 판정하지 않는다. load-bearing 1차 증거인 `thinkingTime.ts`의 `approvedElevationFor()`와 slider loop를 재확인했고, 현재 제품 source에는 `preProbeOriginal`/`finalRestored` snapshot owner가 없으며 `approvedElevationFor()`는 `(metrics.now === metrics.max || level === 'pro')`와 exact pill만 보고 owner/control/aria continuity를 판정하지 않는다. 이는 제품 수정이 아니라 조건부 probe 방법을 명확히 해야 하는 근거다.
- **R3 — Bound impact.** 이 repair의 포함 경계는 exact slot-2 target binding → passive phase stability → immutable `preProbeOriginal` → 원래 now가 max인 경우에만 별도 immutable `temporaryLowerBaseline` 생성 → operational `baseline`→Pro/max `after`→`rollbackAfter` baseline equality → `finalRestored`의 `preProbeOriginal` equality → 성공 또는 `ROLLBACK_FAILED/PARTIAL` 및 environment owner의 격리·복원이다. 각 snapshot의 공유 schema는 target tuple(id/URL/WebSocket), numeric(min/max/now), exact closed pill, non-null canonical base identity, owner key, control key, owner↔control `aria-controls` key다. slot-10, HF-1/HF-2, 슬롯 6–9, Plus-slot Pro, API model 등록, followup/originating_slot 및 기존 exact-target/attach/phase failure taxonomy는 이번 delta의 비영향 경계이며 현 방법을 그대로 보존한다.
- **R4 — Revise and self-check.** 아래 두 anchor와 self-check/risk 문구를 같은 final-state contract로 통일했다. `after`는 동일 target에서 max·exact 6 Pro·관찰된 허용 identity 관계·continuity를, `rollbackAfter`는 baseline 전필드 equality를, `finalRestored`는 `preProbeOriginal` 전필드 equality를 각각 독립 readback한다. initial max 반례에서 lower baseline을 original로 덮어쓰지 않고 max→lower→max→lower→original max의 각 기준을 추적했으며, 어느 단계든 mismatch/replacement/flapping/unknown/incomplete이면 `ROLLBACK_FAILED/PARTIAL`, 격리 및 fresh complete restoration 전 재사용 금지로 끝난다. fake-DOM·`ping-12`·force·metadata edit·blind replay는 대체 증거가 아니다. 이는 직접 source/contract inspection과 proposed design self-check이며 실행 PASS, 독립 `ADMIT` 또는 검증 판정이 아니다.

#### Load-bearing status

- **EXISTING — wrapper contradiction.** `MODEL_FLAGS`에는 현재 `--model`, `-m`, `--models`가 있으나 `_option_values()`는 어느 flag가 값을 만들었는지와 값 없는 occurrence를 버리고, separated value를 `startswith("--")`로만 거르므로 다른 단일대시 option을 값으로 오인한다. `compatible_slots()`는 `gpt-6-pro`를 reasoning 유효성 판정보다 먼저 반환한다. 따라서 malformed separated 값은 미지정 default로, invalid reasoning은 early return으로, 단일 `--models`/`--models=`는 정상 단일 모델로 오인될 수 있다. Stock `runOptions.ts`는 non-empty `models`를 API로 강제한다.
- **EXISTING — identity/elevation contradiction.** `stableModelFingerprint()`는 active-only candidate를 단일 hash로 축약하고 null/conflict를 fail closed하지만 `ping-13` live producer는 아직 미확정이다. `approvedElevationFor()`의 `(metrics.now === metrics.max || level === 'pro')`는 Pro text가 numeric max를 무력화하고 임의의 non-null before/after fingerprint를 허용하며 owner/control/`aria-controls` continuity를 판정하지 않는다. 제품 source에는 probe의 `preProbeOriginal`/`temporaryLowerBaseline`/`rollbackAfter`/`finalRestored` snapshot owner가 없고, 기존 Plan의 initial-max 두 anchor도 합성 baseline과 원래 max 최종상태를 분리하지 않아 원상복귀를 오판할 수 있다.
- **EXISTING — slot-10 capability contradiction.** Behavior는 관리 슬롯 `(1,2,3,4,5,10)`과 slot 10의 Pro capability를 승인했고 wrapper는 `ORACLE_BROWSER_SLOT_ID=10`, port 19231, profile `slot-10`을 공급한다. 그러나 Stock `resolveManagedBrowserSlotCapability()`는 1–5만 열거하고 `BrowserManagedSlotCapability.slotId` union도 10을 제외하므로 slot 10은 `managedSlot=null`이 되어 reasoning capability guard를 우회한다. 기존 `tests/browser/config.test.ts`도 1–5만 읽는다.
- **EXISTING — preserved consumers.** `modelSelection.ts`는 `6 Pro`/`6Pro`를 reasoning-only로 거절하고, CLI browser canonicalization은 `gpt-6`/`gpt-6-pro`를 보존하며, 설치 실행은 `dist/bin/oracle-cli.js`를 소비한다. runner tuple은 승인된 상대순서와 slot-10-last를 이미 표현한다.
- **PROPOSED.** Wrapper는 pre-terminator occurrence provenance와 malformed 상태를 한 번 수집해 validation-before-routing을 수행한다. Probe는 exact target binding과 공유 snapshot schema를 사용해 immutable `preProbeOriginal`, 조건부 `temporaryLowerBaseline`, operational `baseline`, Pro/max `after`, baseline-equal `rollbackAfter`, original-equal `finalRestored`를 분리하고 명시적 `PARTIAL` failure taxonomy와 restoration 실패 시 environment-owner 격리를 적용한다. Stock config/types는 slot 10을 slot 1–2와 같은 Pro capability로 표현·resolve하고 기존 managed guard에 넣는다.
- **UNRESOLVED.** live active base-model signal의 role/attribute/token, phase별 owner lifetime/key, 정상 `6 Pro` 승격 전후 identity 관계 및 initial-max를 포함한 baseline/original 복원 표현은 아직 관찰되지 않았다. HF-1/HF-2 negative/no-claim과 slot-10 config readback 역시 구현 전 evidence-needed frontier다. exact-target phase/elevation readback, `rollbackAfter === baseline` 또는 `finalRestored === preProbeOriginal` 전필드 equality가 불충분하면 selector/identity/elevation 변경, 관련 fixture 확정, build 또는 live prompt가 허용되지 않는다.

## Changes by File

### 1. `oracle-browser-slots/oracle_browser_slots/runner.py`

1. `MODEL_FLAGS = ("--model", "-m", "--models")`를 유지하되 `_option_values()`의 값 목록만으로 model 요청을 판정하지 않는다. 첫 standalone `--` 전 argv를 한 번 스캔해 각 occurrence의 원래 flag, separated/equals 형식, raw value, missing/empty 여부를 보존하는 작은 parser 결과를 `compatible_slots()`가 소비하게 한다. 별도 범용 CLI parser 계층은 만들지 않는다.
2. `--model`/`-m`과 reasoning flag가 명시됐는데 separated 다음 토큰이 없거나 `-`로 시작하는 다른 option 또는 standalone `--` terminator이면 missing으로 기록하고 unconditional `()`로 거절한다. `--model=`/reasoning equals-empty도 거절한다. 이 wrapper 계약은 `-m value`만 short-form value syntax로 허용하고 **`-m=value`는 명시적으로 거절**한다. `--model=value`와 reasoning long-form equals는 non-empty일 때만 허용한다.
3. 같은 의미의 alias를 섞은 `-m value --model value`를 포함해 model occurrence가 둘 이상이거나 reasoning occurrence가 둘 이상이면 값 동일 여부와 무관하게 duplicate로 거절한다. provenance가 `--models`이면 단일값, comma 여부, separated/equals, missing/empty 또는 `--model`/`-m`과의 조합과 무관하게 wrapper compatibility 단계에서 unconditional `()`로 거절한다.
4. structural validation 후에만 canonical model/reasoning을 해석한다. 허용 model은 `gpt-5.5`, `gpt-5.6`, `gpt-5.6-sol`, `gpt-6`, `gpt-6-pro`이고, `gpt-6-pro` 제한보다 reasoning 유효성 판정을 먼저 끝낸다.
5. routing 순서는 다음과 같다.
   - 유효한 `gpt-6-pro`이면 reasoning 생략 또는 유효한 standard/high/pro 별칭과 무관하게 `(1, 2, 10)`이다.
   - 유효한 reasoning `pro`이면 허용된 다른 모델도 `(1, 2, 10)`으로 제한한다.
   - `gpt-5.5`의 None/standard/medium은 `(1, 2, 3, 4, 5, 10)`, high/extended는 `(3, 4, 5, 1, 2, 10)`, pro는 `(1, 2, 10)`이다.
   - 기존 instant/light/low 및 heavy/extra-high 별칭은 `(1, 2, 10)`을 유지하고, 일반 gpt-6/gpt-5.6 계열도 같은 reasoning matrix를 재사용한다.

### 2. `oracle-browser-slots/tests/test_slots.py`

1. 기존 capability test를 model × reasoning 정상 행렬과 provenance-aware negative routing 표로 갱신한다.
2. 정상 행렬은 `-m gpt-5.5`와 `--model gpt-5.5`의 동일 결과, gpt-5.5의 None/standard·high·pro 순서, gpt-6의 기존 reasoning matrix, gpt-6-pro의 omitted/standard/high/pro `(1, 2, 10)`, 기존 gpt-5.6 계열 및 reasoning 별칭 순서를 확인한다.
3. 다음 prompt-free negative routing/readback 표를 `compatible_slots()` 결과와 `assert_slot_compatible()` rejection으로 고정하고, run/submit 소비자에서는 어느 managed slot도 claim하지 않는 경계를 확인한다.

   | argv 사례 | 기대 compatibility/readback |
   | --- | --- |
   | `--model gpt-6-pro` | `(1, 2, 10)` |
   | `--model gpt-6-pro --browser-thinking-time nonsense` | `()`; assignment/queue/claim 전 reject |
   | `--model`/`-m` 뒤 EOF, 다른 `--long`, 다른 `-x`, 또는 standalone `--` | `()`; default model로 대체 금지 |
   | `-m gpt-5.5`와 `--model gpt-5.5` | 동일한 정상 tuple |
   | `-m=gpt-5.5` | `()`; 이 wrapper의 unsupported short equals syntax |
   | `--model=` 또는 `--browser-thinking-time=` | `()` |
   | `--browser-thinking-time` 뒤 EOF, 다른 long/short option 또는 standalone `--` | `()`; reasoning absence로 대체 금지 |
   | unknown model/reasoning 또는 동일값·다른값 model/reasoning duplicate | `()` |
   | `-m gpt-5.5 --model gpt-5.5` 등 alias duplicate | `()` |
   | `--models gpt-6-pro`, `--models=gpt-6-pro` | `()`; 단일값이어도 reject |
   | `--models` missing/empty/comma-multi 또는 model flag와 조합 | `()` |

4. 모든 negative row는 `compatible_slots() == ()`, direct-run `assert_slot_compatible()` rejection, submit의 accepted/queued/claimed event 및 slot assignment 부재를 함께 확인한다. child CLI 후행 오류나 Stock API 강제는 wrapper readback을 대신하지 않는다. 첫 standalone `--` 뒤 같은 토큰들은 payload로서 occurrence parser가 보지 않고 앞쪽의 유효 compatibility를 바꾸지 않는 별도 보존 사례로 둔다.

### 3. `src/cli/options.ts`

`parseBrowserGpt6Label()`과 `inferModelFromLabel()`의 현재 **EXISTING** behavior가 canonical `gpt-6`, `gpt-6-pro` 및 동등 표기를 generic `pro -> DEFAULT_MODEL`보다 먼저 보존하는지 focused test로 고정한다. `resolveApiModel()`에 browser-only id를 API 지원 모델처럼 추가하지 않는다. HF-1/HF-2 수정은 이 단일-model browser 경로를 바꾸지 않으며, 구현 중 API model/pricing/provider 등록이 필요해지면 제품 권한으로 반환한다.

### 4. `src/cli/browserConfig.ts`

`normalizeChatGptModelForBrowser()`과 `BROWSER_MODEL_LABELS`의 현재 **EXISTING** `gpt-6`/`gpt-6-pro` 허용 및 `Latest` base picker target을 보존한다. `gpt-6-pro`의 Pro 의미는 model row가 아니라 별도 reasoning intent가 검증한다. `--browser-model-strategy current`에서 resolved model/metadata canonical id가 유지되는지 확인하되, 이 Ticket에서 `select` 전략의 추측 label을 추가하거나 `6 Pro` reasoning pill을 model picker row로 등록하지 않는다.

### 5. `src/browser/actions/modelSelection.ts`

`isReasoningOnlyLabel()`의 현재 **EXISTING** anchored 판정이 `6 Pro`, `6Pro`, `GPT 6 Pro`, `ChatGPT 6 Pro`를 reasoning-only로 거절하고 범용 `pro` substring으로 넓어지지 않는지 보존한다. 기존 GPT-5.x Pro/Pro Extended 및 GPT-5.6 Sol strict resolution도 회귀시키지 않는다. HF-3의 base-identity/elevation 수정은 이 reasoning-only guard를 우회하거나 완화하지 않는다.

### 6. `src/browser/actions/thinkingTime.ts`

#### Conditional first work — exact-target identity and UI-only elevation discrimination

- `plan_anchor`: `Changes by File / 6. thinkingTime.ts / A. Stable model fingerprint`와 `/ B. Approved 6 Pro elevation`.
- `permitted_initial_work`: fresh admitted worker는 `http://127.0.0.1:19223/json/list`의 한 snapshot에서 `type === "page"`이고 URL hostname이 정확히 `chatgpt.com`인 후보가 **정확히 하나**일 때만 그 동일 entry의 `id`/`targetId`와 `webSocketDebuggerUrl`을 원자적으로 고정한다. attach 직후와 각 phase 및 각 UI transition 전후에 target identity와 현재 URL을 재확인하며, 정렬된 첫 후보·기존 탭 추정·별도 snapshot의 id/WebSocket 조합은 금지한다. wrapper run/session을 만들지 않고 그 WebSocket에 직접 attach해 `Runtime.evaluate`와 control open/close용 native CDP `Input.dispatchMouseEvent`만 사용한다. prompt 제출, model picker 선택, metadata/source 수정, `--force`, build/suite는 금지한다.
- `discriminating_observation`: 먼저 closed → model-menu-open → reasoning-control-open 각 phase에서 최대 8회, 250ms 간격으로 읽고 owner count/key, target/ancestry/`aria-controls`, control identity, role, checked/selected/current/data-state, bounded semantic text/testid, closed pill token, numeric slider metrics의 normalized signature가 3회 연속 동일할 때만 stable로 인정한다. 각 raw sample과 transition timestamp를 보존한다. 세 phase가 stable이고 unique active base signal과 owner/control key가 확인된 경우에만 bounded prompt-free UI-only elevation observation으로 이어진다. 조작 전에 `preProbeOriginal = { target tuple(id/URL/WebSocket), numeric(min,max,now), exact closed pill token, non-null canonical base identity, owner key, control key, owner↔control aria-controls key }`를 원자적으로 읽어 immutable하게 보존한다. 원래 `now < max`이면 `baseline = preProbeOriginal`이고, 원래 `now === max`이면 native pointer로 정확히 한 단계 내린 뒤 같은 schema의 stable `temporaryLowerBaseline`을 별도 immutable snapshot으로 읽어 `baseline`으로 삼되 `preProbeOriginal`을 덮어쓰지 않는다. 이후 동일 target에서 `baseline` → Pro/max `after` → `rollbackAfter`의 최소 왕복을 관찰하고 마지막에 반드시 `preProbeOriginal` 상태로 복원해 별도 `finalRestored`를 읽는다. `after`는 integer `now === max`, canonical Pro, exact `6 Pro`/`6Pro`, 관찰로 허용된 baseline→after base-identity 관계와 동일 owner/control/aria continuity를 모두 만족해야 한다. `rollbackAfter`는 baseline과 공유 schema의 모든 필드가 같아야 하고, `finalRestored`는 `preProbeOriginal`과 모든 필드가 같아야 한다. baseline이 original과 같은 비-max 경로에서도 `finalRestored`를 별도 readback하며 어느 경우에도 prompt를 제출하지 않는다.
- `PARTIAL failure readback`: 후보 0개=`TARGET_NONE`, 복수=`TARGET_AMBIGUOUS`, hostname/URL 변경=`TARGET_URL_CHANGED`, target id/WebSocket 교체 또는 소멸=`TARGET_REPLACED`, attach 실패=`ATTACH_FAILED`, evaluate/read 실패=`EVALUATE_FAILED`, phase 시간 소진=`PHASE_TIMEOUT`, 3회 stable 미충족=`PHASE_INCOMPLETE`, signature/owner/control/identity 왕복=`SAMPLE_FLAPPING`, baseline 생성이나 elevation dispatch·무이동·반대이동 또는 `after` predicate 불충족=`ELEVATION_FAILED`, `rollbackAfter` dispatch/readback 실패 또는 baseline 전필드 mismatch, `finalRestored` dispatch/readback 실패 또는 `preProbeOriginal` 전필드 mismatch, 어느 snapshot에서든 replacement·flapping·unknown·incomplete=`ROLLBACK_FAILED`로 기록한다. 모두 즉시 `PARTIAL`이며 failure code, slot/port, bound target tuple, phase, 시각, raw samples/timestamps, source/dist/symlink identity와 현재 최종 snapshot을 남긴다. stable evidence나 mutation authorization으로 승격하지 않고 blind replay하지 않는다. `ROLLBACK_FAILED` 시 probe executor는 슬롯 2와 해당 UI target을 재사용하지 않으며, managed-slot environment owner가 격리·원상복구·fresh complete `finalRestored === preProbeOriginal` readback을 소유한다. 그 전에는 다른 worker, build 뒤 smoke 또는 live prompt에 해당 슬롯/UI를 제공하지 않는다.
- `dependent_work_not_yet_permitted`: exact-target passive phases, `after` predicate, `rollbackAfter === baseline` 및 `finalRestored === preProbeOriginal` 전필드 equality가 모두 완전하고 active-signal producer/lifetime, 허용되는 identity 관계와 owner/control continuity를 판별하기 전에는 selector/owner/canonical-token identity repair, elevation predicate 변경, 관련 fixture 확정, rebuild, wrapper/live prompt 실행을 시작하지 않는다. `ROLLBACK_FAILED` 격리 중인 슬롯/UI에서는 unrelated safe source inspection 외의 dependent work를 진행하지 않는다.
- `response_if_refuted`: 모든 stable passive phase에서 unique active base signal이 없을 때만 `ACTIVE_SIGNAL_ABSENT`로 기록해 Scope/Behavior/Spec/Ticket 제품 권한 owner에게 반환한다. `after`의 identity/owner 관계가 불명하거나 `rollbackAfter`가 baseline, `finalRestored`가 `preProbeOriginal`의 target/numeric/pill/base identity/owner/control/aria 필드 중 하나라도 복원하지 못하면 raw evidence와 `ROLLBACK_FAILED/PARTIAL`로 Planner와 managed-slot environment owner에게 반환한다. environment owner의 fresh complete 원상복귀 readback 뒤 affected Heuristic 및 independent Review가 current하지 않으면 구현으로 재진입하지 않는다. `Latest`, requested model, catalog hash, null sentinel, broad mismatch exemption, fake-DOM, `ping-12`, force, metadata edit 또는 blind replay는 대체 증거가 아니다.

#### A. Stable model fingerprint

1. Treat the current implementation as **EXISTING but contradicted on live identity**: it queries `[role="menuitem"], [role="menuitemradio"]`, accepts checked version-bearing rows plus closed version-bearing composer pills, and requires exactly one canonical signal; `ping-13` nevertheless produced both identities null. Preserve its fail-closed exclusions until the conditional observation identifies the live active-signal producer.
2. After support, revise only the evidenced selector/owner/lifetime boundary. Accept the observed unique selected/current base-model signal, keep `isVisible`, bounded text, canonicalization, sorting/deduplication and conflict-to-null behavior, and exclude reasoning options, slider labels, account/conversation text, `Latest` without independently observed base identity, and `6 Pro`/`6Pro` reasoning pills.
3. Capture identity at a phase where the probe proves the producer exists; if opening the reasoning control destroys or relocates it, capture before that transition and carry the immutable turn-zero evidence through the existing Node-side `originalModelIdentity` owner rather than widening DOM scope later. Re-read a comparable live signal after interaction for equality/elevation. Do not persist a catalog or configuration-derived proxy.
4. Turn-zero establishment, resume/later-turn persisted identity requirement, and prompt-before-reasoning failure order remain unchanged. Absence or conflict stays null and blocks prompt submission.

#### B. Approved `6 Pro` elevation

1. **EXISTING but contradicted:** exact fingerprint equality는 정상 경로이고 `ensureBrowserReasoning().verified`는 success status, resolved intent, `modelUnchanged`, exact identity 또는 `approvedElevation`을 요구한다. 그러나 현재 `approvedElevationFor()`는 `level === "pro"`일 때 numeric max를 사실상 생략하고 임의의 non-null before/after fingerprint 및 교체된 owner/control도 허용할 수 있으므로 기존 predicate를 승인된 경계로 간주하지 않는다.
2. **SELECTED METHOD (r3 option a), PROPOSED after conditional support:** Ticket AC4·AC5·AC10과 Spec Requirements/Verification이 승인한 native slider Pro 선택의 제품 범위 안에서, prompt 제출 없이 같은 조작과 readback을 더 작게 수행하는 위 bounded UI-only elevation/rollback 관찰을 조건부 첫 작업으로 허용한다. exact target에서 immutable `preProbeOriginal`을 먼저 보존하고, initial max이면 별도 `temporaryLowerBaseline`을 만든다. 실제 operational `baseline`→Pro/max `after`→baseline `rollbackAfter` 뒤 original `finalRestored`까지의 readback만 transition premise와 원상복귀를 결정하며 fake-DOM이나 기존 수동 상태는 결정 근거가 아니다. 각 snapshot은 동일한 target/numeric/pill/base identity/owner/control/aria schema를 사용하고 `rollbackAfter === baseline`, `finalRestored === preProbeOriginal` 전필드 equality가 모두 필요하다.
3. 관찰이 baseline→after에서 base identity 불변을 보이면 exact equality만 사용하고 elevation identity 예외를 제거한다. 하나의 canonical 표현 전이가 관찰된 경우에만 그 exact pair를 허용한다. 어느 경우든 elevation `after`는 `TARGET === "pro"`, 유효한 integer `now === max`, canonical `level === "pro"`, exact closed `6 Pro`/`6Pro` pill, non-null baseline/after active base identity, 동일 owner/control object 또는 관찰로 검증된 유일 stable key가 모두 참일 때만 허용한다. 다른 pair·null·conflict는 prompt 전에 fail closed한다. probe success는 별도로 `rollbackAfter`의 baseline 전필드 equality와 `finalRestored`의 `preProbeOriginal` 전필드 equality를 모두 만족해야 하며 일부복원이나 unknown은 `ROLLBACK_FAILED/PARTIAL`이다.
4. initial, 반복, final/retry loop가 같은 predicate/continuity 의미를 사용한다. `now < max`, wrong pill, non-pro intent, reasoning-only signal만 존재, arbitrary fingerprint change, owner/control/`aria-controls` replacement, key flapping, no/reverse movement 또는 dispatch rejection은 `verified: false`와 `model-mismatch`/`model-changed`/`unavailable` 중 정확한 failure로 끝난다. probe rollback 실패는 runtime success로 오역하지 않고 environment owner 격리로 이어진다.
5. resume/later turn은 persisted original identity를 계속 요구하고 각 invocation에서 unique current owner/control continuity를 새로 검증한다. owner key를 turn 사이 영속 identity로 오용하지 않으며, 두 `browser/index.ts` callsite의 producer/carry/failure 순서를 함께 유지한다.

#### C. Trusted Radix slider interaction

1. **EXISTING:** 두 callsite는 CDP `Input`을 전달하며 Node-side driver가 `mouseMoved -> mousePressed -> mouseReleased`를 dispatch한다. 현재 loop는 fresh geometry, numeric slider readback, 목표 방향 이동, final target을 확인하고 synthetic keyboard를 성공 경로로 사용하지 않는다.
2. `ping-13`은 초기 identity gate에서 종료했으므로 CDP interaction 실패 증거가 아니다. Conditional identity premise가 지지될 때까지 pointer 알고리즘을 재설계하거나 wait/retry를 늘리지 않는다.
3. identity repair 후 실행형 fixture와 최종 live path에서 fresh rect/viewport, visible interaction node, hidden readback 분리, 목표 방향 이동 및 Pro/max 정착을 확인한다. dispatch 오류·무이동·반대 이동·owner/control 교체는 계속 `unavailable`이며 prompt를 제출하지 않는다.
4. 내부 `action-required`/좌표 payload는 외부 metadata 계약으로 확장하지 않고 최종 success/failure evidence만 기록한다.

### 7. `src/browser/index.ts`

두 `ensureBrowserReasoning()` 호출 경로는 이미 동일한 CDP `Input`과 Node-side `originalModelIdentity`를 전달한다. Conditional probe가 pre-open capture/owner-lifetime 변경을 요구할 때만 두 callsite의 동일한 producer/carry contract를 함께 갱신한다. retry, disconnect race, turn index, resume identity requirement, prompt-before-reasoning 순서는 보존하며 한 경로만 바꾸지 않는다.

### 8. `src/browser/config.ts` 및 `src/browser/types.ts` — slot-10 capability

1. `BrowserManagedSlotCapability.slotId` union에 비연속 managed ID `10`을 추가한다. 연속 범위나 generic number로 넓혀 슬롯 6–9를 표현 가능하게 만들지 않는다.
2. `resolveManagedBrowserSlotCapability()`가 `ORACLE_BROWSER_SLOT_ID="10"`을 `{ slotId: 10, expectedControl: "slider", maximumReasoning: "pro" }`로 반환하게 한다. slot 1–2의 기존 capability 의미와 slot 3–5의 High-only 의미를 유지하고 malformed/빈 값/6–9/그 밖의 ID는 계속 `null`로 fail closed한다.
3. `resolveBrowserConfig()`의 existing `managedSlot` resolution과 `assertManagedBrowserReasoningIntent()` 호출 순서를 유지해 slot 10도 managed guard를 실제 통과하게 한다. guard 우회를 별도 special-case로 막지 말고 하나의 capability object가 reasoning resolution/readback의 source가 되게 한다.
4. wrapper `service.py`가 공급하는 `ORACLE_BROWSER_SLOT_ID=10`, `ORACLE_BROWSER_SLOT_PORT=19231`, `ORACLE_BROWSER_REMOTE_CHROME=127.0.0.1:19231`과 `model.py`의 slot 10 port/profile 계산은 변경하지 않고 Stock 입력과의 일치 readback으로 확인한다. runner의 모든 candidate tuple은 set/sort 없이 기존 상대순서와 마지막 `10`을 보존한다. Plus 슬롯 3–5의 Pro 허용, 슬롯 6–9, fallback capability는 추가하지 않는다.

### 9. Stock tests

1. `tests/cli/options.test.ts`
   - browser label inference가 `gpt-6`, `gpt-6-pro` canonical ids를 보존하며 `gpt-5.6-sol`로 떨어지지 않는 observable assertion을 추가한다.
   - API mode에 GPT-6 지원을 암시하는 assertion은 추가하지 않는다.
2. `tests/cli/browserConfig.test.ts`
   - `buildBrowserConfig({ model: "gpt-6-pro", browserThinkingTime: "pro", browserModelStrategy: "current" })`가 canonical model/actual base label과 `reasoningIntent: "pro"`를 보존하는지 확인한다.
3. `tests/browser/config.test.ts`
   - `resolveManagedBrowserSlotCapability({ ORACLE_BROWSER_SLOT_ID: "10" })`가 exact `{ slotId: 10, expectedControl: "slider", maximumReasoning: "pro" }`를 반환하는지 확인한다.
   - env `ORACLE_BROWSER_SLOT_ID="10"`에서 `resolveBrowserConfig({ reasoningIntent: "pro" })`의 `managedSlot` readback이 null이 아니고 Pro guard를 통과하는지 확인한다. slot 3–5의 High-only Pro rejection과 malformed/6–9 `null`을 함께 유지한다.
4. `tests/browser/modelSelection.test.ts`
   - exported/public test boundary를 통해 `6 Pro`, `6Pro`가 reasoning-only label로 거절되고 Runtime DOM evaluation이 호출되지 않는 동작을 검증한다.
   - 기존 `GPT-5.6 Sol` 및 GPT-5.x Pro 판정 회귀를 유지한다.
5. `tests/browser/reasoningSelection.test.ts`
   - 기존 checked-row와 null/catalog 사례는 단위 경계로 보존하되 fixture 구조를 live DOM 증거로 간주하지 않는다. conditional probe가 live producer 하나를 지지한 뒤 관찰된 role/attribute/owner phase와 stable key를 재현하고, repair 전 null → repair 후 단일 stable identity 전이를 검증한다.
   - `ping-13`의 null/null active-signal-absent, conflict, catalog/requested model/`Latest`만 있는 경우, reasoning-only `6 Pro` pill만 있는 경우는 모두 독립 fail-closed fixture로 유지한다.
   - 정상 fixture는 `mouseReleased` 뒤에만 expected slider movement와 exact `6 Pro` pill 및 probe가 허용한 base-identity transition을 만들고, `TARGET === "pro"`, numeric `now === max`, non-null before/after, stable owner/control이 함께 있을 때만 `resolvedLevel: "pro"`, `modelUnchanged: true`, `verified: true`가 되게 한다. synthetic keyboard만으로는 실패해야 한다.
   - 서로 독립된 반례로 (a) numeric `now < max`인데 Pro text인 경우, (b) before/after fingerprint가 임의로 바뀐 경우, (c) owner/control 또는 `aria-controls` stable key가 교체된 경우, (d) reasoning-only `6 Pro` signal만 있는 경우를 둔다. 각 반례는 exact pill 등 다른 긍정 조건을 채워도 mismatch/unavailable 및 `verified: false`여야 한다.
   - high intent, wrong pill, null identity, 이동 없음/반대 이동/CDP dispatch rejection도 prompt-safe failure로 유지한다. 두 callsite와 resume/later-turn carry는 동일 predicate를 소비하며 한쪽에서만 예외가 생기지 않음을 observable evidence로 확인한다.
6. `tests/browser/thinkingTime.test.ts`
   - 공유 selector/normalization 또는 legacy thinking helper와 strict reasoning helper 사이에서 `menuitemradio` 및 `6 Pro` label 해석이 퇴행하지 않는 기존 테스트를 갱신한다. strict slider behavior는 중복 source-string assertion 대신 `reasoningSelection.test.ts`의 실행형 fake DOM/CDP 테스트가 소유한다.

### 10. Build artifact

Stock 테스트가 통과한 소스에서 `/home/user01/project/oracle`의 `pnpm run build`를 실행해 `dist/bin/oracle-cli.js`를 갱신한다. 생성된 `dist` 변경은 Ticket 산출물이며 제거하지 않는다. 라이브 smoke는 source runner나 `tsx`가 아니라 지정된 설치 CLI symlink를 사용해 실제 배포 경로를 검증한다.

## Self-Check Verification Sequence

아래 순서는 값싼 결정적 검사에서 외부 상태와 prompt 제출을 수반하는 검사로 진행한다. 실패한 단계의 원인을 해결하지 않은 채 다음 단계로 넘어가지 않는다.

1. **Authority/current-anchor readback**
   - 구현 시작 직전 Ticket이 여전히 `ready`이고 Plan/authority identity가 현재인지 admission 절차로 확인한다.
   - 위에 명시한 source symbols가 이동했으면 이름 기준으로 다시 찾고, 의미가 바뀌었으면 이 Plan을 추측으로 적용하지 말고 Plan Review로 반환한다.

2. **Conditional exact-target identity/elevation probe — prompt-free, before affected source/test/dist mutation**
   - 한 `/json/list` snapshot에서 `type=page`이고 hostname이 정확히 `chatgpt.com`인 후보가 하나일 때만 동일 entry의 target id와 WebSocket을 원자 바인딩한다. attach/각 phase/각 UI transition 전후 target id·URL을 재확인하고, closed/model-menu-open/reasoning-control-open phase를 각각 최대 8회 250ms 간격으로 sample한다. normalized signature 3회 연속 동일만 stable이며 raw sample/timestamp를 모두 보존한다.
   - `TARGET_NONE`, `TARGET_AMBIGUOUS`, `TARGET_URL_CHANGED`, `TARGET_REPLACED`, `ATTACH_FAILED`, `EVALUATE_FAILED`, `PHASE_TIMEOUT`, `PHASE_INCOMPLETE`, `SAMPLE_FLAPPING`은 명시적 `PARTIAL` readback으로 끝내며 임의 target이나 incomplete phase를 사용하지 않는다. 모든 stable phase에 unique active identity가 없을 때만 `ACTIVE_SIGNAL_ABSENT`로 제품 권한 owner에게 반환한다.
   - passive premise가 지지된 뒤에만 같은 target에서 immutable `preProbeOriginal`을 먼저 읽는다. 원래 `now < max`이면 이를 operational `baseline`으로 쓰고, 원래 `now === max`이면 한 단계 아래 stable `temporaryLowerBaseline`을 별도 immutable snapshot으로 만든 뒤에만 이를 `baseline`으로 쓴다. 이어 `baseline` → native pointer Pro/max `after` → baseline `rollbackAfter`를 관찰하고 마지막에 원래 상태로 복원한 `finalRestored`를 별도 읽는다. 모든 snapshot은 target tuple(id/URL/WebSocket), numeric(min/max/now), exact closed pill, non-null canonical base identity, owner key, control key, owner↔control `aria-controls` key를 공유한다. `after`는 max·canonical Pro·exact 6 Pro·관찰된 허용 identity 관계·continuity를 모두 만족하고, `rollbackAfter`는 baseline, `finalRestored`는 `preProbeOriginal`과 각각 전필드 equality여야 한다. 어느 하나라도 mismatch/replacement/flapping/unknown/incomplete이면 `ROLLBACK_FAILED/PARTIAL`이고 managed-slot environment owner가 슬롯/UI를 격리해 fresh complete 원상복귀 readback 전 재사용을 금지한다. fake-DOM PASS나 `ping-12`는 이 관찰 또는 AC10을 대체하지 않는다.
3. **Wrapper negative routing and regression** — cwd `/home/user01/project/oracle/oracle-browser-slots`

   ```bash
   python3 -m pytest tests/test_slots.py tests/test_followup.py tests/test_workspace_mapping.py
   ```
   - 현재 baseline 126개와 추가 사례가 모두 PASS해야 한다. 먼저 위 negative table을 순수 compatibility/`assert_slot_compatible()`/allocation-before-assignment·queue·claim 경계로 확인한다.
   - valid `-m value`/`--model value` 동등성, `-m=value` 명시적 reject, single-dash option/EOF/다음 option/terminator missing, 동일·상이 alias duplicate, gpt-6-pro 및 pro의 Pro-slot 제한, high ordering/slot-10-last를 확인한다. malformed/empty/unknown reasoning과 모든 `--models` provenance/조합은 `compatible_slots() == ()`이며 assignment·queue·claim이 없어야 한다.
   - 첫 standalone `--` 뒤 payload 제외를 별도 보존 사례로 확인하고 followup/workspace suites로 `originating_slot`과 관리 슬롯 계약 불변을 확인한다.

4. **Slot-10 managed capability focused check** — cwd `/home/user01/project/oracle`

   ```bash
   pnpm exec vitest run tests/browser/config.test.ts
   ```

   - `ORACLE_BROWSER_SLOT_ID=10`이 exact `{ slotId: 10, expectedControl: "slider", maximumReasoning: "pro" }`로 resolve되고 `resolveBrowserConfig()`의 managed guard에 실제 전달되어 Pro를 허용해야 한다.
   - slot 3–5는 High-only Pro rejection을 유지하고 malformed/6–9는 capability를 얻지 않아야 한다. wrapper environment의 slot id/port/remote endpoint와 `model.py`의 19231/slot-10 계산을 source readback으로 결합하고 runner의 `(1, 2, 10)` 및 slot-10-last tuple 순서를 보존한다.

5. **Stock targeted behavior tests** — cwd `/home/user01/project/oracle`

   ```bash
   pnpm exec vitest run tests/browser/modelSelection.test.ts tests/browser/thinkingTime.test.ts tests/browser/reasoningSelection.test.ts
   ```

   - 세 파일 모두 PASS해야 한다.
   - identity case는 conditional probe에서 관찰한 active role/attribute/owner phase를 재현해야 하며 checked-row fake DOM만으로 closure하지 않는다. 정상 expected transition 외에 numeric now<max+Pro text, arbitrary fingerprint change, owner/control 교체, reasoning-only-only signal을 각각 독립 fixture로 실행해 모두 `verified: false`인지 확인한다.

6. **Browser model canonicalization focused checks** — cwd `/home/user01/project/oracle`

   ```bash
   pnpm exec vitest run tests/cli/options.test.ts tests/cli/browserConfig.test.ts
   ```

   - `gpt-6`/`gpt-6-pro`가 browser 경로에서 canonical id를 보존하고 `gpt-5.6-sol`로 무음 폴백하지 않아야 한다.

7. **Compile and deployed artifact synchronization** — cwd `/home/user01/project/oracle`

   ```bash
   pnpm run build
   ```

   - exit code 0이어야 하며 TypeScript signature 변경(`Input` 전달 포함)이 두 callsite와 일치해야 한다.
   - build 성공 후 설치 CLI의 resolved target이 `/home/user01/project/oracle/dist/bin/oracle-cli.js`인지 확인한다. source test PASS만으로 dist 동기화를 대신하지 않는다.

8. **Live precondition check**
   - 슬롯 2 endpoint `127.0.0.1:19223`이 준비되어 있고 ChatGPT 로그인과 Pro entitlement가 유지되는지 기존 slot status/CDP readiness 표면으로 확인한다.
   - 로그인 만료, endpoint down, Plus 계정, 이미 점유 상태는 구현 실패로 우회하지 않는다. prompt를 제출하지 말고 환경 owner가 슬롯 2를 복구한 뒤 동일 빌드로 재개한다.

9. **Live smoke on deployed CLI** — cwd `/home/user01/project/oracle/oracle-browser-slots`

   ```bash
   ./bin/oracle-browser-slots run --slot 2 --job-id verify-pro-elevation -- /home/user01/.nvm/versions/node/v24.18.0/bin/oracle --engine browser --browser-model-strategy current --model gpt-6-pro --browser-thinking-time pro -p "ping"
   ```

   - wrapper JSONL에서 rejection 없이 accepted/started 이후 exit code 0의 completed/finished 결과를 확인하고, `ping-13`에서 관찰된 null identity/model-mismatch가 같은 live acceptance path에서 사라졌는지 확인한다.
   - 로그에서 `model-mismatch`, `model-changed`, `selection-unverified`, `verified: false`가 없어야 한다.
   - 실행 결과가 식별한 정확한 session id를 사용해 `~/.oracle/sessions/<session-id>/meta.json`을 읽는다. 단순히 가장 최신 glob을 고르거나 `ping-12`의 verified-true metadata를 새 실행 성공으로 대체 귀속하지 않는다.
   - authoritative readback은 그 exact session이 top-level `completed`, prompt submission/harvest completion을 거쳐 `reasoningSelection.resolvedLevel === "pro"`, `reasoningSelection.verified === true`, non-null original/observed identity를 기록하는 것이다. slider Pro/max와 requested model `gpt-6-pro` 보존도 같은 session evidence에 결합한다.

10. **Final handoff condition**
   - 위 검사들이 동일한 current source/build bytes를 대상으로 모두 성공하고 live session metadata가 정확한 session id와 결합된 경우에만 독립 verifier에게 넘긴다.
   - 구현자가 Ticket status를 `done`으로 바꾸거나 최종 PASS를 발행하지 않는다. 별도 `ready-ticket-verify` authority가 Ticket의 모든 AC와 false-completion path를 독립 검증한다.

## Risk & Edge Case Mitigations

### Routing and CLI parsing
- **flag provenance 손실:** 값 배열만 반환하면 explicit malformed와 option absence, `--model`과 `--models`를 구분할 수 없다. pre-`--` occurrence record를 compatibility의 단일 입력으로 사용하고 missing/empty/duplicate를 routing 전에 거절한다. 첫 standalone `--` 뒤 payload는 기록하지 않는다.
- **`-m` 우회 재발:** `-m value`만 `--model value`와 동일하게 허용한다. `-m=value`, EOF, 다른 long/short option, terminator는 default로 바꾸지 않고 reject하고, `-m`/`--model` 혼합 duplicate도 값 동일 여부와 무관하게 reject한다.
- **`--models` API 우회:** provenance가 `--models`인 순간 값 개수·형식·missing/empty·다른 model flag와의 조합과 무관하게 wrapper에서 `()`로 reject하고 assignment·queue·claim 부재를 읽는다. Stock API 강제나 child parser 후행 실패를 대체 readback으로 삼지 않는다.
- **validation precedence:** model과 reasoning의 structural/canonical validation을 모두 끝낸 뒤 gpt-6-pro/pro slot restriction을 적용한다. invalid reasoning이 gpt-6-pro early return을 통과할 수 없다.
- **ordering/config boundary:** set/sort를 쓰지 않고 승인된 tuple과 slot-10-last를 유지한다. model option 자체가 없을 때의 기존 config/default 경계는 보존하되, 명시됐으나 malformed인 option은 absence로 취급하지 않는다.

### Slot-10 capability
- **managed guard 우회:** `ORACLE_BROWSER_SLOT_ID=10`을 null로 남기면 wrapper가 Pro 요청을 slot 10에 배정하면서 Stock capability guard는 실행되지 않는다. `types.ts`의 exact non-contiguous union과 `config.ts`의 exact mapping을 함께 바꾸고 public `resolveBrowserConfig()` readback으로 guard 소비를 확인한다.
- **관리 집합 확장 오판:** slot 10 추가를 numeric range로 일반화하지 않는다. 6–9와 malformed ID는 계속 capability `null`, slot 3–5는 High-only이며 Pro를 거절한다. slot 10은 slot 1–2와 같은 capability지만 runner tuple의 기존 상대순서 뒤 마지막에만 위치한다.
- **producer/consumer 불일치:** wrapper `service.py`의 environment와 `model.py`의 port/profile 계산을 Stock capability readback에 결합한다. endpoint/profile/state 로직은 변경하지 않고 config/type special case만으로 새로운 fallback이나 Plus entitlement를 만들지 않는다.

### Model identity and elevation
- **target evidence 오귀속:** 한 `/json/list` snapshot의 정확히 하나인 `chatgpt.com` page entry에서 target id와 WebSocket을 함께 고정한다. 0/복수 후보, URL/target 교체, attach/evaluate 실패, phase timeout/incomplete/flapping은 지정 failure code의 `PARTIAL`이며 stable 또는 mutation 허가가 아니다.

- **live identity producer 오인:** checked row/fake DOM과 `ping-12`를 live 증거로 승격하지 않는다. bounded stable phase probe가 입증한 단 하나의 active base-model producer만 사용하고 catalog/requested config/`Latest`/reasoning pill은 identity가 아니다.
- **arbitrary fingerprint 면제와 복원 기준 혼동:** non-null 또는 단순 불일치는 예상된 elevation transition이 아니다. immutable `preProbeOriginal`과 operational `baseline`을 분리한다. same-target `after`에서 base identity 불변이 관찰되면 equality만 허용하고, 표현 전이가 관찰될 때만 exact canonical pair를 제한적으로 허용한다. `rollbackAfter`는 baseline, `finalRestored`는 `preProbeOriginal`과 target/numeric/pill/base identity/owner/control/aria 전필드가 같아야 하며 합성 lower baseline equality를 원래 max 복원으로 오인하지 않는다.
- **owner/control 연속성:** 같은 injected transition의 object identity를 비교하거나 probe가 입증한 유일한 stable key(target/owner/`aria-controls`/control)를 `preProbeOriginal`·`baseline`·`after`·`rollbackAfter`·`finalRestored`에 함께 적용한다. replacement/flapping은 unavailable 또는 `ROLLBACK_FAILED/PARTIAL`이고 resume turn의 persisted model identity와 혼동하지 않는다.
- **reasoning label 오염:** `Pro`, `6 Pro`, effort labels와 slider metadata는 base fingerprint 입력에서 제외한다. reasoning-only signal만으로 `modelUnchanged`/`verified`를 만들지 않는다.
- **resume identity:** persisted original identity를 새 catalog/current token으로 덮지 않는다. later turn도 비교 가능한 current base signal과 invocation-local owner/control continuity를 요구한다.

### CDP interaction

- **좌표 stale/viewport 변화:** 매 click 전에 rect와 metrics를 재측정하고 유한·viewport 내부 좌표만 dispatch한다. scroll/resize로 rect가 바뀌면 새 좌표를 사용한다.
- **hidden readback:** aria-hidden slider rect를 클릭하지 않는다. visible track/interaction node를 클릭하고 hidden node는 `aria-valuenow` readback에만 쓴다.
- **CDP partial failure:** press 후 release 실패를 성공으로 보지 않는다. UI-only probe의 dispatch·무이동·반대이동 또는 `after` 불충족은 `ELEVATION_FAILED`; baseline 생성 뒤 `rollbackAfter === baseline` 또는 `finalRestored === preProbeOriginal` 전필드 equality를 만들지 못한 dispatch/readback과 mismatch·unknown·불완전 상태는 `ROLLBACK_FAILED/PARTIAL`이다. 효과가 불명한 상태에서 blind replay하지 않고 environment owner가 슬롯/UI를 격리해 fresh complete 원상복귀 전 재사용을 금지한다.
- **click 성공 오판:** mouse event RPC 성공이 아니라 유효한 numeric metrics의 목표 방향 변화, `now === max`, canonical Pro/exact pill 및 same-target identity/continuity를 가진 `after`, baseline-equal `rollbackAfter`, original-equal `finalRestored` readback을 함께 성공 기준으로 삼는다.
- **retry duplicate effect와 initial max:** 구현 reasoning 조작은 현재 level을 먼저 읽고 이미 target이면 click 없이 success로 반환한다. probe만 transition 관찰을 위해 initial max에서 정확히 한 단계 아래 `temporaryLowerBaseline`을 별도로 만들 수 있다. 이 경우 immutable `preProbeOriginal` max를 보존한 채 baseline→max→baseline을 관찰하고 다시 original max로 복원한다. 어느 경로도 이전 좌표/step count를 재사용하거나 합성 baseline을 original로 재명명하지 않는다.

### Build and live environment

- **source/dist drift:** 모든 source test 후 `pnpm run build`를 수행하고, live smoke는 설치 symlink가 가리키는 dist binary로만 실행한다.
- **환경 실패 오분류:** endpoint down, 로그인 만료, entitlement 변경, slot 점유는 code fallback으로 숨기지 않고 환경 조건으로 분리한다. Plus 슬롯에서 Pro를 시험해 실패한 결과로 implementation을 판정하지 않는다.
- **외부 효과 경계:** prompt-free conditional probe는 wrapper session/prompt를 만들지 않지만 선택된 r3 (a) 방법에 한해 slider reasoning state를 bounded하게 변경하고 immutable `preProbeOriginal`, operational `baseline`, `after`, `rollbackAfter`, `finalRestored`의 complete readback까지 소유한다. `ROLLBACK_FAILED`이면 probe executor는 즉시 `PARTIAL`로 멈추고 managed-slot environment owner가 슬롯 2/UI target 격리, 원상복구와 fresh complete `finalRestored === preProbeOriginal` readback을 소유한다. 그 확인 전 슬롯/UI 재사용, build 뒤 smoke, live prompt를 금지한다. 최종 `ping` 제출은 별도 Ticket live verification에서 한 번 수행하며, timeout/transport 단절 시 prompt 미제출을 추정해 즉시 재실행하거나 `--force`를 사용하지 말고 exact session/JSONL/meta readback으로 효과 발생 여부를 먼저 판별한다.

## Local Discretion and Return Conditions

- conditional probe에서 target/phase가 stable하지 않거나 current producer/owner/transition premise가 다르면 broad selector나 mismatch 면제를 추가하지 않는다. 구체적 failure code, raw repeated samples, 현재 UI state와 `PARTIAL`을 Planner에 반환하고 affected Heuristic·독립 Review를 새 Plan bytes에 대해 갱신한다. 모든 stable phase에 고유 active base identity가 없거나 제품 의미 없이는 transition을 정할 수 없으면 Scope/Behavior/Spec/Ticket owner로 반환한다. `rollbackAfter`가 baseline 전필드와 다르거나 `finalRestored`가 `preProbeOriginal` 전필드와 다르면 managed-slot environment owner가 슬롯/UI를 격리·복원하고, fresh complete original-equality readback 및 갱신된 review 전에는 재사용하지 않는다.
- 구현 중 GPT-6의 API model/pricing/provider 등록, `originating_slot` 변경, Plus-slot Pro, 슬롯 6–9 capability, `--models` 지원, model-strategy 기본 변경이 필요하면 이 Plan을 확장하지 말고 Scope/Behavior/Spec/Ticket 권한으로 반환한다.
- source repair가 HF-1/HF-2 negative routing/no-claim table, exact-target `PARTIAL` taxonomy, slot-10 exact capability/guard와 tuple 순서, numeric max, 관찰된 equality/expected transition, `rollbackAfter === baseline`, `finalRestored === preProbeOriginal`, owner/control continuity 또는 독립 반례 중 하나라도 닫지 못하면 affected mutation/build/live를 중단하고 Planner → affected Heuristic → independent Review로 되돌린다. child CLI error, fake-DOM 정상 사례, `ping-12`, force, metadata edit, blind replay는 closure가 아니다.
- 이 개정은 r5 `REVISE`의 initial-max 복원모호 조건을 반영한 Planner method일 뿐이며 자가 `ADMIT`이나 검증 판정이 아니다. SHA `42e4c08c…`의 구 ADMIT과 r2/r3/r4 `REVISE`, SHA `828c2976…`에 결합된 r5 `REVISE`를 새 Plan 승인으로 재사용하지 않는다. 다음 owner는 **affected Heuristic**이며, 그 뒤 current Plan bytes에 대한 independent Plan Review가 갱신되기 전 dependent implementation을 시작·재개하지 않는다.
