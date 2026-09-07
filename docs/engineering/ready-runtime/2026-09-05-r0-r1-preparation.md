> 과거 기록: 2026-09-05의 R0~R1 수행 준비 문서다. 아래 상태·제약·다음 작업은 작성 당시 기준이며, 현재 진행 상태나 운영 지침이 아니다.

# IIS R0-R1 실행 준비

## 대상과 목적
- Workspace: `/home/user01/project/iis-skills`
- 현재 확인 브랜치: `improve/ready-verification-reliability-direct`
- 이번 요청의 범위는 로드맵 R0(기준선·사건·격리)와 R1(행동 평가 기반)의 수행 준비다. 이 문서는 실행 계획이며, R0/R1 실행 완료나 승인된 Ready Ticket Set을 뜻하지 않는다.
- R2 이후 계약·스킬·runtime 구조 변경은 시작하지 않는다.
- 목표는 운영본을 오염시키지 않고 실제 사건과 현재 조합을 분리해 기준선을 고정한 뒤, 문구가 아니라 실제 작업자 행동을 비교할 평가 기반을 실행 가능하게 만드는 것이다.

## 이번 준비에서 직접 확인한 상태
- 기준 revision: `6fb4c92113cc9c12aabaad734329c95dfb613ae0`.
- `git status --short --branch --untracked-files=normal`: tracked 변경 표시는 없고 `.ai-bridge/`, `Tmp/`는 untracked다. 전체 작업 트리가 clean이라고 표현하거나 이 사용자 파일들을 정리하지 않는다.
- Ready Implement / Heuristic Probe / Verify의 `~/.codex/skills/` 항목은 실제 symlink이며 각각 현재 저장소의 `companion-skills/<name>`을 가리킨다. runtime 설치 항목 `~/.omp/agent/extensions/ready-ticket-implement-runtime`은 일반 디렉터리다.
- `omp --help`: `omp v18.1.10`; `--profile`, `--config`, `--no-extensions`, 명시적 `--extension`을 제공한다. 도움말 확인은 새 평가 세션 실행이 아니다.
- 현재 작업 디렉터리에서 `omp config list --json`으로 확인한 값: `skills.enableCodexUser=false`, `skills.customDirectories=[]`, `extensions=[]`. 따라서 Codex symlink의 존재만으로 OMP가 Ready Skill을 발견·로드했다고 주장할 수 없다. 자동 extension 탐색 여부도 `extensions=[]`만으로 판단하지 않는다.
- 현재 평가 manifest는 10개 family, 24개 사례다: `VERIFIED` 4, `FAILED` 10, `INCONCLUSIVE` 2, `VERIFICATION NOT STARTED` 8. 보존된 baseline은 한 건의 요약 기록이며 완전한 현행 기준선이 아니다.
- 이번 준비에서는 소스 변경, 설치 동기화, worktree 생성, 테스트 재실행, 실제 에이전트 평가를 하지 않는다. 변경 대상은 이 기존 준비 문서뿐이다.

## 이전 준비 기록 — 이번에 재실행하지 않음
- 이 문서에 이미 기록되어 있던 결과: 설치 `--check`는 `SYNCED`, `--preflight`는 `READY`, calibration unittest는 `6 tests, OK`.
- 기존 baseline 채점 기록: release gate 실패, `false_verified=1`, `target_mutation_runs=1`.
- 위 결과는 이전 기록으로 보존한다. 이번 세션의 새 검증 결과나 사건 당시 runtime 적용 증거로 확대하지 않는다.

현재 평가 입력의 SHA-256(`evaluation/ready-verification/` 기준):
- `score_result.py`: `687b3dea0c31ebc0312451ab46858031a1f44de6094d18aaca0f52303ae400d6`
- `manifest.json`: `9b17fbc8f16959bf6f356d5377bb767b4b07729046a4f06e3c0a936e355836e8`
- `baseline-observations.json`: `4e285c92cf447265887f8290e29d40b80f7faba4dcc76b107bac652acfc2cfca`

## 공통 안전 제약
1. 현재 canonical checkout에서 브랜치 전환이나 source 편집을 하지 않는다. Companion skill live entry가 원본 디렉터리의 direct symlink일 수 있으므로, source 변경 전에 반드시 별도 worktree 또는 동등한 격리 복제본을 만든다.
2. 격리 작업본의 root, branch/revision, skill 탐색 경로, runtime 설치/실행 경로, 평가 fixture 경로를 명시적으로 기록한다. 기존 세션이 새 skill/runtime 조합을 암묵적으로 재로딩했다고 가정하지 않는다.
3. `SYNCED`/`READY`는 파일 일치/설치 준비 증거다. canonical skill invocation으로 runtime이 실제 활성화됐다는 증거로 확대하지 않는다.
4. 과거 사건 원인은 로그나 retained artifact가 없으면 `미확인`으로 유지한다. 현재 파일을 읽고 사건 당시와 동일했다고 추론하지 않는다.
5. 실제 에이전트 평가에서 scorer-only oracle(`manifest.json`의 expected/fixture_contract/normal_twin 등)을 작업자 프롬프트나 verifier context에 노출하지 않는다.
6. R0/R1 중 운영본 설치 전환, runtime 삭제/감량, Probe 삭제/통합, Behavior 절차 감량은 하지 않는다.

# R0 — 기준선·사건·격리

## R0-1 현재 환경과 사건 당시 환경 분리
- 현재 source revision/branch/working tree를 고정 기록한다.
- live skill symlink 대상, installed runtime 위치/일치 상태, 실제 지원 host와 canonical invocation 경로를 read-only로 확인한다.
- 설치됨 / 세션에 로드됨 / 보호 경로로 실행됨을 서로 다른 상태로 기록한다.
- 사건 당시 동일 정보는 retained log/artifact가 있을 때만 연결한다.
- 원인 분류는 다음 네 축으로만 시작한다: 장치 미적용 / 적용됐지만 보호 범위 밖 / 계약 자체 약함 / 충분한 계약의 수행 오류. 증거 없이 하나로 확정하지 않는다.

## R0-2 대표 사건 연결
- 저장소에 남아 있는 `evaluation/ready-verification/baseline-observations.json`의 `verifier-target-mutation-core`를 우선 조사할 사건 앵커로 사용한다. 사용자 불만의 전체 원사건과 동일하다고 단정하지 않는다.
- 이 JSON은 Probe의 `wrong` 관찰 → 검증 중 파일이 `adjusted`로 변경 → verifier의 `VERIFIED` 반환 및 사후 변경 확인을 서술한다. 이번에 직접 확인한 것은 이 요약의 존재다. 원시 로그를 독립적으로 확인한 사건 재현으로 격상하지 않는다.
- 요구→사전조사→Scope/Spec/Ticket→구현→Probe→Verify→최종 보고의 retained artifact가 실제로 존재하면 연결한다. 없는 단계는 추측으로 채우지 않는다.
- `최초 증거 부족`, `최초 근거 없는 성공 판정`, `상위 보고에서의 확대`를 분리해 기록한다.
- 과거 전체 사건 재현 자료가 없으면 구조적 반례와 과거 사건을 명확히 구분한다.

| 증거 연결 | 현재 확보 범위 | 실행 시 닫을 조건 |
|---|---|---|
| 사용자 요구·사전조사·Scope/Spec/Ticket·구현 | 해당 baseline JSON에 원자료 경로 없음 | 사건 소유자가 보존한 정확한 자료가 연결될 때만 귀속 |
| Probe·Verify·변경 확인 | `baseline-2026-09-04-1` 요약과 verdict 한 줄 | 원시 도구 출력·대상 경로·변경 전후 내용이 있으면 연결 |
| 당시 revision·모델·runtime 적용 | 구체 revision/모델 없음; machine digest 미보존 명시 | 현재 조합으로 과거 공백을 채우지 않음 |
| 상위 최종 보고의 성공 확대 | 해당 원문 미확보 | 최초 부당 판정과 상위 확대를 별개로 기록 |

- 조사 범위는 현재 저장소의 관련 evaluation/engineering 자료 및 여기서 직접 연결되는 원자료로 제한한다. 이번 범위에서는 원시 실행 transcript나 정확한 사건 제품 root를 찾지 못했다. 무관한 저장소·다른 세션을 넓게 검색하지 않는다.
- 새 원자료가 없으면 역사적 원인 탐색을 닫고 요약 기반 구조적 반례로 전환한다. 이는 R1 사례 작성의 차단 사유가 아니며, 과거 사건 재현 성공으로 보고하지 않는다.
- `evidence_limit`에 과거 OMP 반복 실행 중단 요청이 남아 있다. 이번 수행 준비를 반복 실행 재개 권한으로 해석하지 않는다.

## R0-3 실험본 격리
- 제안 작업본: `/home/user01/project/iis-skills-wt-r0-r1-20260905`, 기준 revision은 위 SHA로 고정한다. 제안 실험 저장소: `/home/user01/tmp/iis-r0-r1-20260905`. 두 경로는 이번 확인 시 존재하지 않았으며 아직 생성하지 않았다. 기존 다른 worktree는 재사용하거나 변경하지 않는다.
- 실행 착수 후 별도 worktree를 만든다. baseline의 스킬·runtime payload는 기준 revision으로 고정하고 평가용 변경은 실험본에서만 한다. baseline과 후속 후보에 동일한 보완 scorer·case oracle을 적용해 측정 도구 변경과 제품 지침 변경을 혼동하지 않는다.
- 제품 fixture root, oracle, raw results, runtime data를 서로 분리한다. 작업자에게는 승인된 제품 계약과 초기 fixture만 제공한다. oracle·변형 매핑·정답 설명은 fixture root, 파일명, 작업자 prompt와 history에 들어가지 않게 한다.
- 새 OMP 평가 profile/config에 실험용 skill 탐색 경로를 명시하고 live/home/project의 중복 탐색을 차단한다. 별도 profile만 만들었다고 완전 격리로 간주하지 않는다. `--no-skills`는 canonical 진입도 막으므로 격리 대책으로 사용하지 않는다.
- runtime은 `--no-extensions`와 명시적 실험본 `--extension` 경로를 사용하는 실행안을 우선한다. 준비 단계에서는 이 조합을 실행·검증했다고 주장하지 않는다.
- `IIS_READY_RUNTIME_DATA`를 실험 데이터 경로로 반드시 고정한다. `src/state-store.js:21-23`의 기본값은 profile과 무관하게 `~/.omp/agent/data/iis-ready-runtime`을 사용한다.
- `IIS_READY_IIS_WORKFLOW_SKILL`도 실험 payload로 고정한다. `src/authority-binding.js:141-166`은 workflow 안의 절대 To Tickets 경로에서 validator를 결정한다. 원본 `iis-workflow/SKILL.md`의 절대경로가 live checkout을 가리키므로, 실험용 사본의 배치 경로를 정합화하고 최종 To Tickets/validator realpath까지 실험본 내부인지 확인해야 한다. live 문서는 고치지 않는다.
- 설치 스크립트를 사용한다면 `IIS_READY_SKILL_INSTALL_DIR`, `IIS_READY_VERIFY_SKILL_INSTALL_DIR`, `IIS_READY_PROBE_SKILL_INSTALL_DIR`, `IIS_READY_RUNTIME_INSTALL_DIR` 네 경로를 모두 실험 위치로 지정한다. 기본값을 둔 sync는 실행하지 않는다.
- 새 세션에서 skill 발견 → canonical 진입 → guard binding → 실제 도구 실행의 root/revision/path를 관찰해야 격리 통과다. 이번에 oracle을 읽은 준비 세션은 blind 평가 작업자로 재사용하지 않는다. 실제 실행은 DIRECT 기준이며 별도 사용자 선택 없이 SUBAGENT 비교를 추가하지 않는다.
- canonical checkout의 기존 사용자 파일과 live link/payload를 보존한다. 파일 일치, 세션 로드, 보호 경로 실행은 각각 별도 증거로 기록한다.

## R0 통과 조건
- 어떤 사건을 관찰하는지, 현재/과거 무엇이 확인됐는지, 어떤 조합을 비교하는지, 실험 변경이 live instruction에 흘러들지 않는지가 명확해야 한다.
- 기록 없는 역사적 원인은 미확인으로 남긴다.

# R1 — 행동 평가 기반

## R1-1 기존 평가 틀 재사용
- `evaluation/ready-verification/`을 기본 평가 골격으로 유지한다. 새 평가 프레임워크를 만들지 않는다.
- 실제 Probe→Verify agent 결과와 단위/runtime 테스트의 증거 역할을 분리한다.
- Ready verification 외에 기획/구현/E2E 행동 평가가 필요한 범위를 먼저 inventory하고, 기존 evaluator에 최소 확장 가능한지 확인한 뒤에만 새 fixture/runner를 추가한다.

현재 `evaluation/ready-verification/`에는 README, manifest, scorer, baseline 요약만 있다. 24개 서술형 case가 곧 실행 fixture 24개라는 뜻은 아니다. 관련 파일명·engineering 자료 조사에서도 이 세트의 재사용 가능한 실행 runner는 확인되지 않았다.

| 평가 영역 | 작업자에게 제공할 입력 | 결과를 판단할 관찰 |
|---|---|---|
| 기획 | 요구·현 상태·중요 미확인 | 생성된 권위가 실제 외부 효과와 미확인을 보존하는지; 허용 범위를 내부 응답으로 약화하지 않는지 |
| 구현 | 승인된 계약과 disposable 제품 시작 상태 | 실제 사용자 진입점의 결과, 권위 있는 readback, 구현 handoff의 주장 범위 |
| 검수 | Ready authority·구현 대상·현재 Probe handoff | 실제 Probe → Verify 결과, 원시 관찰, 대상 무결성 |
| 연결 평가 | 동일 요구와 초기 상태 | 기획→구현→검수→최종 보고에서 미확인·회귀·전체 완료 주장이 어떻게 전달되는지 |

- 네 영역은 같은 fixture·실행 기록 형식을 재사용한다. 기획/구현 결과를 verifier 전용 verdict로 억지 변환하지 않는다. 기존 scorer는 검수 verdict를 채점하고, 다른 영역은 case별 관찰과 주장 대응으로 비교한다.
- 실행 진입 경로, 초기화 방법, 외부 상태 readback이 있는 fixture와 소규모 공통 실행 도구만 보충한다. 별도 플랫폼·총괄 검증자·영구 evidence DB는 만들지 않는다.

## R1-2 scorer 판별 한계 보완
- 현재 `score_result.py`의 release gate가 false VERIFIED, normal-twin rejection, malformed verdict, target mutation, missing case는 잡지만 defect 사례에서 `FAILED`와 `INCONCLUSIVE`의 오분류를 직접 실패시키지 않는다는 한계를 테스트로 먼저 고정한다.
- 최소 회귀 테스트를 추가해 `expected=FAILED`인 결함 사례를 전부 `INCONCLUSIVE`로 반환해도 통과할 수 있는 현재 약점을 재현한다.
- 그 다음 case별 허용 verdict 범위와 필요한 관찰을 표현하는 가장 작은 scorer/manifest 변경을 설계한다. 명확한 결함 관찰과 단순 증거 부족을 구분하고, 권한 부족만으로 제품 결함을 확정하지 않는다.
- 모호한 사례가 실제로 존재할 때만 허용 verdict 집합을 도입한다. 단일 문자열 exact match를 기계적으로 확대하지 않는다.
- raw tool/result provenance가 필요한 표본을 확인하되 모든 제품에 영구 evidence ledger를 새로 도입하지 않는다.
- 명확한 결함의 `FAILED → INCONCLUSIVE`, 증거 부족의 `INCONCLUSIVE → FAILED`, admission 실패의 `VERIFICATION NOT STARTED → INCONCLUSIVE`를 서로 다른 오분류로 집계하고 허용 범위 밖 verdict는 gate 실패로 연결한다. 기존 `class_confusion`은 보고만 하고 gate가 사용하지 않는다는 점이 수정 대상이다.
- 허용 verdict는 실행 전에 case oracle로 고정한다. 관찰에 따라 여러 verdict가 정당한 사례에는 각 verdict의 전제 관찰을 함께 둔다. 단순한 허용 문자열 목록으로 판정 근거를 면제하지 않는다.
- 회귀 증거는 정상 통과 유지, 결함을 일괄 보류하는 전략 거절, 권한/표면 부족을 제품 결함으로 단정하는 전략 거절, 대상 변경 거절을 각각 구분한다. 테스트 개수·문구·필드 전달 자체를 품질 증거로 삼지 않는다.
- 기록의 `run_id`, 실제 모델/도구 profile, 대상 identity, 원시 결과 참조, 초기화·반복 횟수는 평가 입력 적격성에서 확인한다. 현재 scorer가 이런 필드를 검증한다고 가정하지 않는다. 중복 run이나 불완전 기록으로 예정된 평가 수를 채우지 않는다.
- scorer의 verdict 비교는 제품 현실을 재판정하지 않는다. `runtime_trigger_executed: true`만 믿지 말고, 핵심 사례와 표본에서 실제 명령·출력·readback을 검토한다. 기록 누락은 평가 증거 부족이지 제품 `FAILED`의 근거가 아니다.

## R1-3 사용자 불만 판별 사례 보강
- 현재 manifest가 이미 다루는 source-shape bypass, wrong entry, normal twin, missing surface, stale Probe, target mutation은 재사용한다.

| 로드맵 사례 | 현재 재사용점 / 부족한 부분 | 추가 fixture와 판별 관찰 |
|---|---|---|
| Mock 정상·실제 인증 거절 | 직접 대응 부족 | 같은 제품 진입점으로 인증 성공/거절 쌍. 유효한 승인 자격으로도 계약을 위반하는 경우와 자격 자체가 없는 경우를 구분 |
| 성공 응답·외부 상태 미변경 | 직접 대응 부족 | 응답은 같되 권위 있는 상태가 변하는/변하지 않는 쌍. 비동기 작업이면 계약상 완료 시점까지 관찰 |
| helper를 진입점이 우회 | `source-shape-bypass`, `wrong-entry` | 서술만 재사용하지 말고 실제 CLI/API로 정상/우회 경로를 실행 |
| 사전조사 미확인 소실 | `weak-authored-flow`가 일부 관련 | 미확인이 남은 요구를 기획부터 전달하고 생성 권위·최종 주장에 제한이 유지되는지 관찰 |
| 후속 Ticket이 이전 동작 회귀 | 직접 대응 부족 | A 완료 후 B 변경으로 A가 깨지는 제품 상태를 만들고 현재 통합 경로를 관찰. 과거 done 합계는 readback 아님 |
| 정상 제품·경계 사용 가능 | `runtime-correct` 및 정상 twin | 실제 경계를 사용할 수 있는 정상 쌍을 유지. 불필요한 중단·보류도 회귀로 집계 |
| 운영자 권한 필요 | `missing-surface`는 부재만 다룸 | 승인된 운영자 증거 제공/미제공 쌍. 도움으로 닫힌 경우 진행하고 미제공은 제한. 우회나 Mock 대체는 실패 행동 |
| 검증 중 소스 수정 유혹 | `target-mutation` | 수정 전 실제 모순과 원래 대상 판정을 보존. 변경 시도 차단과 실제 파일 변경을 구분하고 고친 대상을 원래 대상의 성공으로 인정하지 않음 |

- 정상·결함·증거 부족을 관찰로 구분할 수 있는 최소 사례를 각 행에 둔다. core와 이름/구조가 다른 blind 변형을 준비하며 불필요한 같은 경로의 중복 사례는 만들지 않는다.
- 제어된 평가 서비스의 성공은 에이전트 판단 시험 결과다. 실제 대상 서비스의 연동 성공으로 보고하지 않는다. 실제 외부 효과를 약속한 후보는 승인된 실제 테스트 환경에서 같은 제품 경로로 별도 확인해야 한다.

## R1-4 기준선 비교 프로토콜 고정
- baseline과 후보를 같은 모델, 도구, 권한, 초기 fixture 상태로 비교한다.
- 각 run 전에 disposable 상태를 초기화하고 oracle 정보를 작업자 문맥에서 제거한다.
- core + holdout/이름·구조 변형을 유지한다.
- 채택 비교에 사용하지 않을 pilot으로 비용·변동성을 먼저 측정한다. 그 뒤 본 기준선/후보 결과를 보기 전에 반복 수, case 목록, 허용 편차, 중단/재시도 처리, 표본 감사 범위를 고정한다. 지금 근거 없는 반복 수를 발명하거나 본 결과를 본 뒤 기준을 조정하지 않는다.
- 1차 지표: 근거 없는 전체 완료(false VERIFIED), 정상 결과 부당 보류, 결함 vs 증거 부족 구분, 핵심 현실 경계에 처음 도달하는 시점, 사용자 재검수/재작업.
- 2차 비용 지표: 토큰, 도구 호출, 문서량/시간.
- 비교 profile에는 실제 provider/model ID·reasoning 설정·도구·권한·host·skill/runtime revision을 남긴다. 기본 모델 alias나 설명형 profile만으로 동일 조건을 주장하지 않는다.
- `핵심 경계 첫 도달`은 실행 시작에서 첫 실제 경계 호출까지의 시간/도구 순번이며, 경계 성공 여부는 따로 기록한다. 미도달도 누락하지 않는다. `사용자 재검수·재작업`은 추가 사용자 개입과 수정 재진입을 기록하며 관찰이 없으면 0이 아니라 미측정이다.
- 분모는 사전 고정된 case×반복이다. 실패·중단·접근 불가도 보존한다. 정상 case 부당 보류와 결함/증거 부족 오분류를 함께 보고하고, 토큰 절감으로 이를 상쇄하지 않는다.
- R0/R1은 평가 기반과 현행 행동 기준선을 만드는 범위다. R2 이후의 스킬/runtime 후보를 지금 만들어 비교하지 않는다. 후속 후보도 여기서 고정한 측정 기준으로 비교한다.

## R1 통과 조건
- scorer test 통과만이 아니라 실제 작업자 행동 비교가 가능해야 한다.
- 알려진 핵심 회귀에서 근거 없는 완료를 허용하지 않는다.
- 모든 defect를 `INCONCLUSIVE`로 돌려 false VERIFIED만 낮추는 후보는 통과시키지 않는다.
- 정상 제품의 완료율/부당 보류가 기준선보다 악화되면 채택하지 않는다.
- 유한 평가 통과를 일반적 무오류 보장으로 해석하지 않는다.

# 실행 순서 및 체크포인트
1. 위 현재 조합을 출발점으로 R0-1 환경 기록을 고정한다. 기록된 실패·설치 결과를 확인하려고 불필요하게 재실행하지 않는다.
2. R0-2 요약 사건과 원자료의 차이를 기록하고, 확보 범위를 닫는다. 새 근거 없는 역사적 원인 추론을 중단한다.
3. R0-3 worktree·skill 탐색·extension·runtime data·workflow/validator·fixture/oracle 격리를 만든다. 이 경계가 닫히기 전 평가 소스 수정과 agent run은 시작하지 않는다.
4. R1-1 네 평가 영역과 기존 24개 case를 실행 가능한 fixture/관찰에 매핑한다. 기획·구현·연결 평가를 검수 테스트로 대체하지 않는다.
5. R1-2 판정 오분류를 거절하는 최소 scorer/manifest 변경과 행동 회귀 검사를 실험본에서 수행한다. 기존 정상 통과와 무결성 gate를 보존한다.
6. R1-3 여덟 사례의 누락 fixture·raw-result 수집·상태 초기화를 보완한다. 작업자 문맥의 oracle 유출을 점검한다.
7. 변경이 모인 뒤 관련 calibration/runtime 검사를 한 번 수행한다. 이 결과는 모델 행동 평가나 실제 외부 연동 성공과 구분한다.
8. 실제 평가 실행을 요청받은 뒤 격리된 새 세션에서 pilot을 수행한다. 과거 반복 실행 중단 기록을 무시하고 이번 준비 요청만으로 재개하지 않는다.
9. pilot 제외 조건과 본 평가 반복 수/허용 편차를 고정한 다음 현행 조합의 blind 기준선 평가를 수집한다. 불완전한 과거 한 건을 현행 baseline으로 대체하지 않는다.
10. R0/R1 산출물·통과/미달·미확인을 보고하고 STOP. R2는 시작하지 않는다.

## 수행 시 필요한 산출물과 종료 기준
| 범위 | 산출물 | 통과 증거 |
|---|---|---|
| R0-1 | 현재 조합과 역사적 미확인 구분 | revision·실제 경로·host와 근거 귀속이 명시됨 |
| R0-2 | 사건 claim/evidence 연결 | 원시 증거·요약·추론을 구분하고 조사 범위가 닫힘 |
| R0-3 | 격리된 실행 조합 | 새 세션의 skill/guard/validator/data/제품 root가 실험본에 귀속됨 |
| R1-1 | 네 평가 영역의 실행 입력·관찰 대응 | 서술형 case뿐 아니라 실제 실행 경로가 있음 |
| R1-2 | scorer/manifest 변경과 회귀 결과 | 정상 통과를 유지하며 결함/증거 부족 오분류를 gate가 거절함 |
| R1-3 | 여덟 사례의 fixture·정상 쌍·변형 | 원시 관찰로 정상·결함·접근 불가를 구분함 |
| R1-4 | 사전 고정 프로토콜과 현행 행동 기준선 | blind 실제 실행의 충분한 기록과 지표 분모가 있음 |

- 이번 상태: 수행 준비 문서 보완. 위 실행 산출물, 격리 통과, R0/R1 완료는 아직 선언하지 않는다.
- 다음 착수점: 고정 revision에서 실험 worktree를 만들고, profile뿐 아니라 runtime data와 절대 validator 경로까지 격리한다.

## 실행 시 예상 변경면 — 실험본에만 적용
- `evaluation/ready-verification/score_result.py`: 허용 verdict 밖 오분류 집계와 release gate 연결. 제품 의미를 판정하는 두 번째 verifier로 확장하지 않는다.
- `evaluation/ready-verification/manifest.json`: 관찰 전제·정당한 verdict 범위·여덟 사례의 대응을 필요한 만큼 보완한다. baseline 사건 요약은 새 결과로 덮어쓰지 않는다.
- `tests/test_ready_verification_calibration.py`: 정상 통과/일괄 보류/근거 없는 결함 확정/무결성 위반의 소비자 관점 회귀를 검증한다.
- `evaluation/ready-verification/README.md`: 실제로 구현한 실행·초기화·blind 입력 분리·결과 채점 방법에 맞춘다. fixture/공통 실행 도구는 이 평가 영역 안에서 기존 패턴을 우선한다.
- 운영 skill, delivery runtime, planning authority, 기존 done Ticket은 R0/R1의 제품 의미 변경 대상이 아니다. 격리용 skill 사본의 경로 정합화와 후속 R2 계약 변경을 구분한다.

# 최종 보고 형식
## 확인된 상태
- 실제 workspace/root/branch/revision, clean 여부, 설치/skill/runtime 확인 결과, 격리 경로.

## 실패 경계
- transport/protocol/tool/domain 오류를 구분한다. 실패한 읽기 호출은 대상 상태의 증거로 사용하지 않는다.

## 확정된 사실
- retained artifact와 성공한 tool 결과만 사용한다.

## 미확인 사항
- 과거 세션의 runtime 적용 여부, 없는 incident artifact, 실제 외부 경계 성공 여부 등.

## 다음 안전한 동작
- R2 이전에 남은 R0/R1 통과 조건만 제시한다.
