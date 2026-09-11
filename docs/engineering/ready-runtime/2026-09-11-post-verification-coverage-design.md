# IIS — Verifier 이후 Coverage

작성일: 2026-09-11
상태: 소스 반영 및 로컬 기본 검증 완료 — 설치 활성화·모델 효과 검증 미수행
대상: `/home/user01/project/iis-skills`
확인 기준: `f8d6731 — refactor: remove separate heuristic preparation stage`

사용자가 제공한 DESIGN DRAFT를 검토하고, 상세 TODO와 직접 구현을 요청한 결정을 반영한다. 이전 초안의 CodexPro transport 실패는 당시 관측이다. 이번에는 로컬 소스에서 같은 HEAD와 변경 없는 작업 트리를 확인했다. 설치 상태나 실제 탐지 효과를 소스 확인으로 대신하지 않는다.

## 목적과 순서

누적·다중 엔티티 상태와 provider 실패 후 상태 고착이 기존 검증에서 누락됐다는 사용자 보고를 출발점으로 삼는다. 당시 원계약과 실행 기록 전체를 조사한 것은 아니므로 특정 프롬프트나 격리 정책을 원인으로 확정하지 않는다.

```text
Ready Ticket → Grounded Plan → Independent Plan Review → Implement
  → Verifier
    → VERIFIED: read-only Coverage
      → COMPLETE + 중요한 미해결 공백 없음: 기존 ready_finalize
      → 중요한 finding / PARTIAL / BLOCKED: 성공 반영 보류, 기존 소유자 반환
    → FAILED / INCONCLUSIVE: Coverage 없이 기존 비진행 finalization과 triage
```

직접 verification-only 요청에도 성공 경로는 동일하다. 구현을 새로 수행하거나 Plan ADMIT을 추가로 요구하지 않는다. 이미 done인 Ticket의 명시적 진단은 기존 비진행 경계를 유지하며, 추가 진단은 사용자 범위에 따른다.

Verifier의 semantic verdict는 불변이다. PROVISIONAL_VERIFIED를 만들지 않으며 done을 먼저 쓴 뒤 되돌리지 않는다. Coverage는 성공 handle 제출 전의 실제 추가 절차다. 별도 제품 승인권, 합의 투표, 승인 DB, controller를 만들지 않는다.

## 책임

- Planner / Plan Reviewer: grounding, 사전 전제, 착수 충분성, 조건부 첫 작업, material revision. 구현 전에 확인할 중요한 전제를 Coverage로 미루지 않는다.
- Verifier: semantic preflight, 모든 authored Flow/AC, 시나리오의 판별력, binding, 실행·readback·cleanup, cross-AC 및 Scope/Non-Goals, semantic verdict. 각 flow의 Nearest nonconforming state, Discriminating observation, Sensitivity activation은 유지한다. 실행 중 발견하거나 전달받은 중요한 반례를 무시하지 않는다.
- Coverage: Verifier가 실제 관찰한 조건·증거와 구현을 대조하여 놓친 중요한 구현 경로, 관찰 공백, 계약 투영 공백을 읽기 전용으로 조사한다. 기존 별도 Bounded post-implementation frontier의 주 책임을 맡는다. 제품/runtime 실행, 실험, 수정, AC verdict, Ticket 변경, finalizer 호출을 하지 않는다.
- Caller: exact terminal 연결, Coverage 단일 호출과 결과 회수, 성공 반영 보류/진행, 기존 소유자로 반환. 두 번째 AC 판정이나 finding 임의 삭제를 하지 않는다.

Coverage 질문: 실제 검증의 모든 관찰이 맞더라도 같은 승인 결과를 깨뜨리는 현실적인 구현 경로가 그 관찰을 통과할 수 있는가?

## Coverage invocation

한 개의 독립 read-only worker가 자기 조사를 직접 끝낸다. Verifier와 병렬 실행하거나 Verifier를 pause/resume하지 않는다. 재위임하지 않는다. 모델/effort는 기존 사용자 선택 정책을 따른다. 포괄적으로 적용되는 선택을 재사용하며, 별도 모델·고성능 모델·서로 다른 모델을 강제하지 않는다. 실제로 필요한 선택만 기존 경로로 해결한다.

입력은 exact Ticket, Parent Spec, 적용 Behavior/UI와 사용자 지시, exact verification report와 primary evidence 위치, 기존 target/binding 식별 근거다. Plan과 구현 보고서는 navigation이다. 다른 run의 latest 보고서를 자동 선택하지 않는다. opaque handle은 caller만 보유하며 Coverage 입력이나 보고에 넣지 않는다.

원계약과 실제 구현을 직접 읽고 초기조건, trigger, readback, 관찰 창을 실제 증거와 대조한다. Verifier의 결론에 동의하는 것으로 끝내지 않는다. 범위는 승인 결과를 결정하는 entrypoint, writer/reader, state/effect, authoritative readback과 중요한 단서가 가리키는 의존 경계다. repository 전체 감사나 고정 장애 checklist는 아니다.

중요한 finding에는 다음 인과 연결을 담는다.

1. 승인 의무와 exact Ticket/parent anchor.
2. 실제 구현 경로와 깨질 수 있는 가정. 관찰과 추론을 구분.
3. 도달 가능한 조건에서 발생하는 중요한 잘못된 결과.
4. 기존 검증의 어느 조건·관찰이 실패를 구별하지 못하는지.
5. 가장 좁은 다음 관찰 또는 그 관찰에 필요한 정확한 권한·환경 제한.

관찰이 당장 불가능하다고 중요한 증거 공백을 버리지 않는다. 일반 위험, 범위 밖 기능, 도달 불가능하거나 충분히 판별된 후보를 blocking finding으로 만들지 않는다. finding 개수 목표가 없다.

승인 범위의 실제 단서에서 도출한 중요한 후보가 증거 있는 기각, 구체적인 finding 또는 정확한 증거 제한으로 정리되면 종료한다. 무발견을 채우기 위해 더 파거나 새 중요한 근거 없는 반복 탐색을 하지 않는다.

결과는 기존 host terminal/artifact 전달로 회수하는 한 개의 읽기 전용 검토 결과다. 다음은 읽을 내용이지 새 machine schema나 prose-string validator가 아니다.

```text
COVERAGE REVIEW RESULT
Ticket: <exact Ticket>
Reviewed verification: <exact report / primary-evidence references>
Target and authority: <기존 식별 근거와 현재성 제한>
Completion: COMPLETE | PARTIAL | BLOCKED
Findings: None | <인과 연결>
Limitations: None | <정확한 조사·근거·권한 제한>
```

COMPLETE는 조사 완료이며 finding과 양립한다. COMPLETE + None은 모든 버그가 없다는 증명이 아니다. 무응답, 도구 실패, PARTIAL을 무발견으로 취급하지 않는다. 별도 registry, fingerprint, lifecycle DB를 만들지 않는다.

## 반환과 재검증

- 완료 및 중요한 미해결 공백 없음: 현재 target/authority 조건에서 해당 원래 handle을 기존 finalizer에 제출.
- 승인 의무를 깨뜨릴 수 있는 미검증 경로: 성공 보류, finding을 기존 검증/교정 소유자에게 전달. 가설 자체를 product FAILED나 수정 완료로 바꾸지 않는다.
- Parent 의미의 Ticket 투영 공백: 원래 계약 소유자에게 반환. 새 AC를 Coverage나 Verifier가 승인하지 않는다.
- 범위 밖 기능: 현재 Ticket 완료 차단 근거가 아니다.
- 근거 부재·조사 실패·대상 귀속 불가: 정확한 PARTIAL/BLOCKED 및 다음 소유자를 보고. product FAILED로 변환하지 않는다.

종료된 Verifier의 결과/binding을 수정하거나 재개하지 않는다. 보충 실행·재판정은 fresh verifier invocation과 새 binding·terminal로 수행한다. source/config 또는 effect 범위가 달라졌으면 이전 PASS를 이월하지 않는다. 새 verifier는 모든 적용 의무를 판정하며, 관찰 재사용은 기존 freshness·attribution·flow 규칙에 따른다.

수정은 기존 Implement/Plan Review 경로다. finding 기각은 새 verifier의 current primary evidence로 입증한다. 합의만으로 닫지 않는다. 새 성공에 대한 Coverage는 이전 finding 해소와 수정·새 증거의 영향 범위를 중심으로 하며 무관한 영역을 반복하지 않는다. target·의무·초기조건이 바뀌면 과거 검토를 자동 재사용하지 않는다. 동일 finding과 동일 증거만 반복되는 자동 loop는 만들지 않는다.

## 사례와 경계

다중 프로젝트가 승인 범위이면 global key와 프로젝트별 식별 경로를 읽는다. 한 프로젝트·고유 key 검증만 했다면 서로 다른 결과를 가진 두 프로젝트의 같은 local key 조회가 좁은 다음 관찰일 수 있다. 단일 프로젝트 전용 계약에 다중 프로젝트 지원을 발명하지 않는다. 운영 DB 복제나 무단 쓰기는 필요조건이 아니다.

fresh evidence는 empty state가 아니다. 격리된 환경에서도 누적·다중 엔티티 상태를 준비할 수 있지만 검증 대상인 이력·전이 자체를 seeded 상태로 대체하면 안 된다. cleanup 이후에는 당시 primary evidence를 읽고, 기록되지 않은 조건은 제한으로 남긴다. 현재 빈 DB에서 과거 초기조건을 추정하지 않는다.

provider 실패 후 비고착 의미가 승인되어 있으면 실제 writer와 성공·실패 반환 경로를 읽는다. 통제된 실패 응답으로 애플리케이션 경계를 관찰하는 것과 provider 외부 동작을 검증하는 것은 구분한다. 쿼터 소진, 새 retry/fallback 요구는 하지 않는다. 실패 semantics가 결정되지 않았다면 계획 소유자에게 반환한다. 이 사례는 모든 Ticket의 의무 테스트 목록이 아니다.

## 구현 경계

- 신규 `companion-skills/ready-ticket-coverage/SKILL.md`와 기본 프롬프트.
- `ready-ticket-verify` SKILL/reference/default prompt의 별도 frontier 책임 이동과 caller 성공 순서.
- Adaptive `08-delivery-continuation.md`, triage, terminal report, Run Contract, template, SKILL/default prompt 연결.
- `iis-workflow/SKILL.md`, root README, 평가의 실제 verify prompt 및 terminal 연결 관측.
- installer companion discovery로 충분하면 installer는 변경하지 않음.

finalize를 소유한 caller 한 곳만 Coverage를 dispatch한다. Adaptive Outer Main이 caller이면 별도 verify wrapper를 더 만들지 않는다. opaque handle, verifier terminal machine schema, binding stable/effect/불변성, finalizer 입력 및 guarded status write는 그대로다. Coverage 이행은 caller 프로토콜이며 finalizer가 기계적으로 강제하지 않는다.

Heuristic 복원, preparation 고정 revision, 새 stage switch, 승인 ledger, 기본 risk checklist, 설치 .pyc drift 수정은 범위 밖이다.

## 비용과 검증

총비용 = Coverage 호출·읽기 + 필요한 재검증 − Verifier에서 제거한 별도 탐색. 성공마다 독립 호출이 늘어난다. 오탐 지연, Verifier 서술에 대한 anchoring, 같은 반례 누락 가능성은 남는다. 탐지율 향상과 시간 절감은 미측정이다.

기존 실행/관측 수단으로 성공 handle 순서와 정확한 연결, Coverage 보류에서 미완료 유지, fresh verifier terminal 연결, 비진행 verdict와 상태 보호를 확인한다. 문서 프로토콜은 소유권·원문·호출 경로를 대조하고, 테스트를 위해 caller engine이나 prose validator를 만들지 않는다. 모델별 semantic evaluation은 별도 요청 없이는 구현 완료 조건이 아니다. bundle prepare/check는 기존 경계를 사용하고 설치 활성화는 별도 권한이다.

근거: `ready-ticket-verify/references/verify.md`의 semantic check/scenario/evidence/terminal, `delivery-tools/ready-ticket/src/finalization.js`, `iis-adaptive-planning/references/08-delivery-continuation.md`, `evaluation/ready-verification/{calibrate,run_agent,completion,goal,inspect_run}.py`, `scripts/sync_installed_iis.py`.

## 반영 및 기본 검증 기록

사용자의 후속 지시에 따라 직접 반영, 정합성 확인과 로컬 기본 검증까지만 수행했다. 별도 에이전트 소환, 새 OMP 실행, 모델 기반 semantic evaluation, 운영 설치 활성화는 하지 않았다.

- Coverage SKILL/default prompt 추가. Verifier의 별도 frontier 탐색 책임을 이동하고 flow 판별력·known finding 처리·terminal schema는 유지.
- 단일 caller의 post-success Coverage, Adaptive event/triage/report, Run Contract·template·default prompt, 일반 workflow와 README 연결.
- 평가 관측은 최신의 단 한 번 전달된 host handle과 일치하는 finalizer만 현재 verdict/binding/progression에 연결. 이전 성공 결과는 새 보류 결과를 완료시키지 못하며, 복수의 서로 다른 순차 terminal은 전체 개수만으로 거절하지 않음. 모든 기존 raw history와 총 전달 횟수는 보존.
- `inspect_run.py`는 task dispatch와 raw async owner return의 event ordinal을 표시. Coverage prose 판정기나 새 caller engine은 추가하지 않음.
- Python 로컬 회귀 70개 통과: agent capture, verification calibration, completion calibration, goal calibration, Run Contract checker. Goal의 추가 순차 terminal/보류 회귀 반영 후 해당 13개 재실행 통과.
- Node finalization/verification-binding 회귀 15개 통과. 성공 status write, FAILED/INCONCLUSIVE 비변경, drift 거절, rollback, diagnostic 경계 확인. 실제 사용자 Ticket은 변경하지 않음.
- 기존 dependency scan PASS: 87개 text file, retired-runtime finding 없음.
- 변경 Python 문법, YAML/default prompt 및 Markdown 상대 링크 확인.
- 임시 store에서 기존 bundle prepare/check 통과: 81개 payload file, 신규 Coverage 두 파일과 host-link discovery 포함. installer 소스 수정 불필요. `installed: false`, `loaded_identity: NOT_CHECKED`; 임시 bundle 제거.
- synthetic local event 입력으로 기존 observation viewer CLI를 실행하여 Coverage dispatch/return 순서, BLOCKED 원문과 finalize 미호출 표시를 확인. 이것은 관측 코드의 기본 검증이며 실제 agent 동작의 증거가 아님. 임시 입력 제거.

opaque handle, verifier terminal machine schema, verification binding 및 finalizer 구현은 변경하지 않았다. Coverage 탐지 효과와 실제 OMP 내 protocol 준수는 이번 검증의 주장 범위 밖이다.
