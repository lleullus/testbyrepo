---
title: "Matt 스킬 경량 도입 및 Implementation Lead 직접 연결 작업계획서"
created: "2026-07-28"
updated: "2026-07-28"
status: ready-to-execute
document_type: operation-workplan
version: 1.0
project_root: "/home/user01/project/matt"
implementation_lead_root: "/home/user01/project/implement_lead"
strategy: "기존 과설계 폐기 후 경량 재구축"
---

# Matt 스킬 경량 도입 및 Implementation Lead 직접 연결 작업계획서

> [!important] 현재 시작 상태
> 기존 `/home/user01/project/matt` 내용은 전부 삭제되었고 같은 경로가 빈 디렉터리로 다시 생성됐다. 이 계획은 삭제된 P1, P2-01, Go validator, fixture, evidence, contract, build 산출물을 복구하거나 재사용하지 않는다. `/home/user01/project/implement_lead`와 전역 스킬은 삭제 작업에서 변경하지 않았으며, 이 계획에서도 명시된 단계 전에는 건드리지 않는다.

## 1. 목표

사용자가 원한 구조는 다음과 같다.

```text
Matt의 작은 기획 스킬 묶음
→ 사용자가 승인한 SPEC.md
→ 구현 가능한 Markdown Ticket
→ Implementation Lead가 Ticket을 직접 읽음
→ 기존 Worker / Adapter / Full 검증으로 구현
```

이번 작업의 목적은 Matt를 별도 기획 플랫폼으로 만드는 것이 아니다. 다음 두 가지만 달성한다.

1. Matt의 기획 스킬들을 원래 성격에 가깝게 가볍게 사용한다.
2. Implementation Lead의 BMAD 입력부를 로컬 Markdown Ticket 입력부로 교체한다.

## 2. 핵심 원칙

### 2.1 반드시 지킬 원칙

- Task 0-1부터 선행 조건을 확인하며 번호 순서대로 실행한다.
- upstream은 `v1.1.0`, commit `d574778f94cf620fcc8ce741584093bc650a61d3`으로 고정한다.
- Matt는 독립적으로 조합되는 Markdown 스킬 묶음으로 유지한다.
- 초기 운영 입력은 local Markdown만 지원한다.
- planning skill은 Implementation Lead나 Worker를 자동 호출하지 않는다.
- 사용자가 exact Ticket 경로와 exact Worker를 지정해야 구현을 시작한다.
- pilot 프로젝트, exact Ticket, exact Worker, 전역 설치 여부는 해당 값이 실제로 필요한 Task에 도달하기 전에는 질문하지 않는다.
- Implementation Lead의 기존 Worker, Adapter, evidence, ownership, Full 실행 코어는 유지한다.
- 실제 end-to-end pilot 전에 범용화하지 않는다.
- 기존 `/home/user01/project/matt` 삭제 전 산출물은 권위도 참고 구현도 아니다.
- Gate 1과 Gate 2에서는 검증 결과와 변경 내역을 보고한 뒤 중단하고 사용자 승인을 기다린다. 승인 없이 다음 단계로 자동 진행하지 않는다.

### 2.2 만들지 않을 것

다음은 이번 작업 범위에서 금지한다.

```text
별도 Go 또는 Python 기획 애플리케이션
새 build/overlay 엔진
Decision Ledger
Planning Admission 대체 보고서
증적 lineage 시스템
범용 tracker provider 프레임워크
GitHub/GitLab/Linear 직접 resolver
새 영속 실행 ledger
BMAD 계약의 이름만 바꾼 1:1 재구현
```

### 2.3 과투자 중단 신호

다음 중 하나가 나타나면 현재 Task를 중단하고 범위를 줄인다.

- 실제 Ticket pilot 전에 신규 schema가 두 개를 초과한다.
- resolver 또는 validator가 SKILL 입력 규칙보다 커진다.
- Phase별 evidence 파일을 반복 버전으로 쌓기 시작한다.
- 초기 smoke fixture가 네 개를 초과한다.
- local Markdown 한 건도 실행하지 못했는데 remote tracker 일반화를 시작한다.
- BMAD Admission의 모든 predicate를 새 용어로 복원하려 한다.
- `implement_lead/SKILL.md` 전체 재작성으로 진행된다.

과투자 중단 신호가 발생하면 구현을 확대해 해결하지 않는다. 현재 상태, 발생한 신호, 이미 이루어진 변경을 보고하고 사용자 판단을 기다린다.

## 3. 작업 범위

### 3.1 포함 범위

Matt planning 스킬 후보:

```text
setup-matt-pocock-skills
ask-matt
grill-me
grilling
grill-with-docs
domain-modeling
codebase-design
research
prototype
wayfinder
to-spec
to-tickets
handoff
```

초기 main flow가 안정된 후에만 검토할 선택 항목:

```text
triage
improve-codebase-architecture
```

Implementation Lead 변경 범위:

```text
invocation input
Ticket 및 parent Spec 해석
ready/blocker 확인
입력 파일 변경 감지
Ticket AC 기반 decomposition 입력
BMAD 입력 경로 제거
```

### 3.2 제외 범위

- Worker 재설계
- Adapter 공통 상태 모델 도입
- Node/Python/Go Adapter의 native schema 변경
- remote tracker 직접 읽기
- 다중 저장소 orchestration
- planning artifact 자동 승인
- 제품 정책의 자동 결정
- 기존 전역 BMAD 스킬 즉시 삭제

## 4. 경로와 산출물

새 작업은 기존과 같은 경로를 사용한다.

```text
/home/user01/project/matt/
├── matt-skills-lean-planning-implementation-lead-workplan.md
├── upstream/
├── skills/
├── examples/
└── verification/
```

각 대상 프로젝트에서 Matt가 만드는 기획 산출물은 다음과 같이 단순하게 유지한다.

```text
<project-root>/.scratch/<work-slug>/
├── SPEC.md
├── WAYFINDER.md           # 큰 작업일 때만
├── tickets/
│   ├── TICKET-001.md
│   └── TICKET-002.md
└── HANDOFF.md             # 필요할 때만, 권위 문서 아님
```

## 5. 최소 문서 계약

### 5.1 SPEC.md

필수 항목:

```markdown
# <제목>

Status: draft | approved
Owner: <사용자 또는 지정된 planning owner>

## Problem
## Desired Outcome
## Requirements
## Non-Goals
## Implementation Constraints
## Verification Expectations
## UI / UX
## Open Questions
```

규칙:

- `approved`는 사용자 또는 명시된 planning owner가 확인한 경우에만 사용한다.
- 미해결 제품 결정이 있으면 `approved`로 전환하지 않는다.
- UI가 아니면 `UI / UX`에 `Not applicable`을 명시한다.
- prototype 결과는 자동으로 authority가 되지 않는다. 사용자가 채택한 결정만 Spec에 반영한다.

### 5.2 Ticket Markdown

필수 항목:

```markdown
# TICKET-001: <제목>

Status: draft | ready | blocked | done
Parent-Spec: ../SPEC.md
Project-Root: <절대 경로 또는 Spec 기준 유일한 프로젝트 경로>
Worker: <사용자 선택 시 확인할 후보 또는 비어 있음>
UI: yes | no

## Goal
## Acceptance Criteria
## Scope
## Non-Goals
## Blockers
## Verification
## References
```

규칙:

- 한 파일은 하나의 implementation Ticket만 표현한다.
- `ready`는 parent Spec이 `approved`이고 blocker가 모두 해소된 경우에만 허용한다.
- Goal은 비규범적 요약이며 구현 의무의 유일한 위치가 될 수 없다. Goal을 제거해도 Acceptance Criteria, Scope, Non-Goals, Blockers, Verification이 완전한 구현 계약을 유지해야 한다.
- Acceptance Criteria는 관찰 가능한 완료 조건이어야 한다.
- Scope에는 변경 허용 영역을 적고 Non-Goals에는 명시적 제외를 적는다.
- Blockers는 정확한 한 줄 `None` 또는 항목 전체가 로컬 Markdown 경로인 목록이다. 경로 대상의 상태가 모두 `resolved` 또는 `done`이어야 `ready`가 될 수 있다.
- UI Ticket은 항목 전체가 경로인 승인된 로컬 UI/UX Markdown 문서를 `References`에 포함하며, 대상 상태는 `approved`여야 한다.
- Ticket은 parent Spec의 범위를 확대하거나 뒤집지 않는다.

## 6. 작업 순서 요약

| Task | 내용 | 활성 영향 |
| --- | --- | --- |
| 0-1 | 빈 `matt/` 상태와 보호 대상 기준선 확인 | 없음 |
| 0-2 | upstream 스킬 최소 집합 고정 | 없음 |
| 1-1 | 필요한 Matt 스킬을 로컬 후보로 배치 | 없음 |
| 1-2 | 한국어·자동 구현 금지·Ticket-first 규칙만 추가 | 없음 |
| 1-3 | SPEC/Ticket template 작성 | 없음 |
| 1-4 | 실제 대화형 smoke 4종 이하 실행 | 없음 |
| Gate 1 | Matt가 유효한 Spec/Ticket을 가볍게 만드는지 승인 | 없음 |
| 2-1 | Implementation Lead 기준선 재확인 | 없음 |
| 2-2 | 최소 Ticket 입력 계약 확정 | staging만 |
| 2-3 | Ticket/Spec resolver와 변경 seal 구현 | staging만 |
| 2-4 | 기존 execution core에 Ticket projection 연결 | staging만 |
| 2-5 | BMAD 입력 제거 후 read-only shadow 검증 | staging만 |
| 2-6 | 실제 non-UI Ticket pilot | 제한적 |
| 2-7 | UI 경로 추가 여부 판단 및 선택 pilot | 제한적 |
| 2-8 | 활성 경로 cutover와 rollback 확인 | 있음 |
| Gate 2 | Ticket 기반 Implementation Lead 전환 승인 | 있음 |

# Phase 0. 시작 상태와 보호 경계

## Task 0-1. 새 `matt/` 시작 상태 확인

1. `/home/user01/project/matt`가 존재하고 이 계획 파일 외 기존 산출물이 없는지 확인한다.
2. 삭제된 과거 P1/P2-01 파일을 복원하거나 다른 경로에서 복사하지 않는다.
3. `/home/user01/project/implement_lead/SKILL.md`의 현재 SHA-256과 Git 상태를 기록한다.
4. 전역 스킬 inventory를 기록하되 이 단계에서는 설치·삭제·수정하지 않는다.
5. 삭제 작업으로 `implement_lead`와 전역 스킬이 변경되지 않았는지 확인한다.

검증 기준:

- 새 `matt/`에 과거 validator, evidence, fixture, contract가 없다.
- `implement_lead` 기준선이 기록된다.
- 전역 스킬 변경은 0이다.

## Task 0-2. upstream 최소 집합 고정

1. Matt upstream을 `v1.1.0`, commit `d574778f94cf620fcc8ce741584093bc650a61d3`으로 고정하고 checkout 결과가 정확히 일치하는지 확인한다.
2. 선택된 스킬 원문과 라이선스를 `matt/upstream/`에 보관한다.
3. 사용하지 않는 실행 스킬은 가져오지 않는다.
4. upstream 원문은 직접 수정하지 않는다.
5. 로컬 변경은 `matt/skills/`의 사용자-facing 사본에만 적용한다.

검증 기준:

- 선택된 planning skill 목록과 source commit을 한 문서에서 확인할 수 있다.
- `implement`, `tdd`, `code-review` 등 별도 실행 체인은 포함되지 않는다.
- 라이선스가 보존된다.

# Phase 1. Matt 스킬 묶음 경량 도입

## Task 1-1. planning 스킬 로컬 후보 배치

1. 선택된 Matt 스킬을 `matt/skills/`에 배치한다.
2. 스킬 간 링크와 상대 참조가 깨지지 않도록 한다.
3. `ask-matt`가 planning 흐름만 안내하도록 범위를 확인한다.
4. 큰 작업에서만 `wayfinder`를 사용하고 일반 작업에는 강제하지 않는다.
5. `research`, `prototype`, `handoff`는 필요할 때만 사용한다.

검증 기준:

- 각 스킬이 독립적으로 읽히고 필요한 참조가 존재한다.
- 모든 아이디어가 Wayfinder나 prototype을 강제로 거치지 않는다.

## Task 1-2. 최소 로컬 정책 적용

로컬 변경은 다음 네 가지로 제한한다.

1. 질문과 산출물을 사용자의 언어로 작성한다.
2. planning skill이 Implementation Lead 또는 Worker를 자동 호출하지 않는다.
3. 구현으로 넘어갈 때 exact Ticket 경로와 exact Worker를 사용자에게 요청한다.
4. `to-spec`과 `to-tickets`가 이 계획의 최소 Markdown 계약을 따른다.

`ask-matt`의 최종 안내 예시는 다음과 같다.

```text
기획 산출물이 준비됐습니다.
구현하려면 다음 형식으로 직접 요청하세요.

implementation-lead <exact-ticket-path> <exact-worker>
```

검증 기준:

- 자동 구현 호출 0이다.
- 사용자 확인 전 `approved` 또는 `ready` 전환 0이다.
- 한국어 대화에서 산출물이 불필요하게 영어로 전환되지 않는다.

## Task 1-3. template과 사용 예시 작성

`matt/examples/`에 다음만 만든다.

```text
SPEC.template.md
TICKET.template.md
simple-non-ui/
large-wayfinder/
ui-prototype/
```

예시는 계약 설명용이며 별도 schema나 validator를 만들지 않는다.

검증 기준:

- 사람이 읽고 직접 수정할 수 있다.
- hidden metadata나 전용 생성 프로그램 없이는 사용할 수 없는 구조가 아니다.

## Task 1-4. 실제 smoke 흐름 확인

최대 네 가지 흐름만 확인한다.

1. 일반 non-UI 변경: 대화 → approved Spec → ready Ticket
2. 큰 작업: opening grill → Wayfinder → Spec → Ticket
3. UI 작업: prototype 선택 사용 → 채택된 결정만 Spec/Ticket 반영
4. 프로젝트 밖 아이디어: grill-me → 정리된 설명, 자동 구현 없음

검증 방법:

- 실제 스킬 대화 흐름을 수행한다.
- 생성된 Markdown을 사람이 검토한다.
- 구조 검사기는 만들지 않는다.
- 발견된 결함만 스킬 문구에 최소 수정한다.

### Gate 1. Phase 1 승인 기준

다음이 모두 참이면 Phase 2로 진행한다.

- 일반 non-UI 흐름에서 approved Spec과 ready Ticket을 만들 수 있다.
- Ticket AC, Scope, Non-Goals, Blockers, Verification이 실제 구현 입력으로 충분하다.
- 큰 작업만 Wayfinder를 사용한다.
- prototype 결과가 사용자 채택 없이 authority가 되지 않는다.
- planning skill이 구현을 자동 호출하지 않는다.
- 사용 경험이 기존 BMAD보다 가볍다고 사용자가 판단한다.
- 별도 validator, evidence chain, Decision Ledger가 생기지 않았다.

Gate 1 실패 시 Phase 2를 시작하지 않고 스킬 문구나 template만 좁게 수정한다.

Gate 1 검증이 통과해도 Phase 2로 자동 진행하지 않는다. 검증 결과와 Phase 1 변경 내역을 사용자에게 보고하고 명시적 승인을 기다린다.

# Phase 2. Implementation Lead 최소 입력 전환

## Task 2-1. Implementation Lead 기준선 재확인

1. `/home/user01/project/implement_lead`의 현재 Git 상태와 `SKILL.md` SHA-256을 다시 기록한다.
2. 기존 미커밋 변경을 삭제하거나 `git restore`하지 않는다.
3. 기존 Worker, ownership, mutation envelope, Adapter, evidence lifetime, Full 관련 핵심 규칙을 목록화한다.
4. Node/Python/Go Adapter의 기존 test 명령을 확인한다.
5. Phase 2 변경 전 복원 가능한 사본을 별도 경로에 만든다.

검증 기준:

- Phase 2 변경 전후 비교 기준이 있다.
- 기존 미커밋 작업의 소유권을 임의로 변경하지 않는다.

## Task 2-2. 최소 Ticket 입력 계약 확정

새 invocation 형식:

```text
implementation-lead <exact-ticket-path> <exact-worker> [project-root]
```

Lead가 Ticket과 parent Spec에서 읽는 필드는 다음으로 제한한다.

```text
Ticket path
Ticket status
Parent-Spec path
Project-Root
Goal (preflight coherence validation only)
Acceptance Criteria
Scope
Non-Goals
Blockers
Verification
UI marker
References
```

입력 차단 조건:

- Ticket 파일을 읽을 수 없음
- Ticket status가 `ready`가 아님
- parent Spec이 없거나 `approved`가 아님
- Acceptance Criteria가 비어 있음
- Goal이 실행 권위 섹션과 충돌하거나 Goal에만 구현 의무가 있음
- unresolved blocker가 있음
- Blockers가 정확한 `None` 또는 로컬 Markdown 경로-only 목록이 아님
- UI Ticket에 승인된 로컬 UI/UX 경로-only 참조가 없음
- project root가 유일하게 결정되지 않음
- exact Worker가 제공되지 않음

별도 JSON schema를 만들지 않는다. Markdown heading과 단순 `Key: Value` 규칙을 SKILL/reference에 명시한다.

## Task 2-3. Ticket/Spec 해석과 PlanningInputSeal 구현

필요한 seal은 다음 하나뿐이다.

```text
PlanningInputSeal
  ticketPath
  ticketSHA256
  specPath
  specSHA256
  blockerFiles[]
    path
    SHA256
    status
```

규칙:

- SHA-256은 현재 raw file bytes 기준이다.
- seal은 현재 invocation의 in-session scratch다.
- 영속 ledger나 새로운 evidence 종류가 아니다.
- blocker가 `None`이면 빈 목록을 사용한다.
- blocker path가 없는 단순 텍스트 설명은 `ready`에서 허용하지 않는다.

필수 재검사 시점:

1. 첫 Worker 호출 직전
2. task acceptance 직전
3. Full 진입 직전
4. 최종 완료 직전

변경을 발견하면 다음으로 중단한다.

```text
blocked: planning input changed
next owner: Ticket 또는 Spec owner
```

Lead는 변경된 planning 문서를 자동 반영하거나 수정하지 않는다.

## Task 2-4. 기존 execution core에 Ticket projection 연결

교체 대상:

```text
BMAD Story parsing
Planning Admission lookup
Story identity seal
admission currentness projection
Story AC decomposition input
BMad planning owner 반환
```

보존 대상:

```text
사용자 선택 Worker만 제품 파일 수정
Lead의 제품 파일 직접 수정 금지
Worker 순차 호출
frozen mutation envelope
actual workspace delta 검사
pre-existing 변경 보존
Canonical reuse / extend / replace
AC-to-task coverage
Adapter-native status/exit/evidence
CURRENT / STALE / INVALID / SUPERSEDED
Full integration gate
terminal complete / blocked / incomplete
```

변경 방식:

- 기존 `SKILL.md`에서 입력부 관련 부분만 좁게 수정한다.
- 공통 reference는 최대 두 개만 추가한다.
  - `references/planning-ticket.md`
  - 필요할 경우 `references/planning-input-currentness.md`
- 새 실행 프로그램이나 daemon을 만들지 않는다.

## Task 2-5. read-only shadow 검증

1. 같은 의미를 가진 기존 BMAD fixture와 새 Markdown Ticket 예시를 준비한다.
2. 둘 다 Worker 호출 전 preflight/decomposition까지만 수행한다.
3. 다음 결과를 비교한다.
   - 구현 범위
   - Acceptance Criteria coverage
   - blocker 판단
   - UI 여부
   - 필요한 Adapter
   - Worker dispatch 가능 여부
4. execution core 결과 차이가 입력 계약 교체 때문인지 회귀인지 판정한다.
5. 제품 파일은 수정하지 않는다.

검증 기준:

- selected Worker, mutation ownership, evidence, Full 규칙이 약화되지 않는다.
- 새 경로가 BMAD Story 또는 Planning Admission을 읽지 않는다.
- 설명되지 않는 차이가 0이다.

## Task 2-6. 실제 non-UI pilot

첫 pilot 조건:

```text
local Markdown Ticket
non-UI
외부 prerequisite 없음
blocker 없음 또는 local blocker 파일로 명확히 해소됨
한 프로젝트
한 Worker
한 Adapter 중심
낮은 위험도
```

pilot에서 확인할 것:

1. exact Ticket과 Worker 입력
2. preflight와 PlanningInputSeal
3. Ticket AC 기반 task 분해
4. Worker만 제품 파일 수정
5. frozen envelope와 actual delta 검사
6. 기존 Adapter Fast 검증
7. Full integrated 검증
8. 완료 직전 Ticket/Spec 재검사

중단 조건:

- Lead가 제품 파일을 직접 수정함
- selected Worker 외 mutation 발생
- Ticket/Spec 변경을 놓침
- 기존 Adapter 의미가 변경됨
- 제품 정책을 구현자가 임의로 결정해야 함

## Task 2-7. UI 경로는 non-UI 통과 후 선택적으로 추가

UI 지원이 실제로 필요하면 다음만 추가한다.

- Ticket `UI: yes`
- `References`의 승인된 UX 문서 경로
- 현재 `ima2-front` guidance 로드
- loading, empty, error, success, responsive, accessibility, interaction 검증
- rendered/browser evidence와 Adapter evidence 분리

UI pilot 전에는 UI용 범용 schema나 별도 framework를 만들지 않는다.

## Task 2-8. 활성화와 rollback

활성화 전 조건:

- Gate 1 통과
- read-only shadow 통과
- non-UI 실제 pilot 통과
- Adapter 회귀 테스트 통과
- 변경된 파일 목록과 pre-cutover 사본 확보
- 사용자에게 활성 범위 확인

전역 스킬 정책:

- 기본값은 전역 스킬을 건드리지 않는 것이다.
- 먼저 `/home/user01/project/matt/skills`를 로컬 후보로 검증한다.
- 전역 설치 또는 기존 BMAD 스킬 제거는 사용자의 별도 명시적 승인 후 수행한다.
- 전역 설치를 하더라도 BMAD 스킬 삭제와 Matt 스킬 설치를 같은 무검증 동작으로 묶지 않는다.

Implementation Lead cutover:

1. 새 invocation help가 exact Ticket과 Worker만 안내하는지 확인한다.
2. 활성 경로에서 BMAD Story와 Planning Admission fallback을 제거한다.
3. 새 세션에서 read-only preflight를 실행한다.
4. 실패하면 pre-cutover `implement_lead` 사본을 복원한다.
5. 제품 파일은 rollback 대상에 포함하지 않는다.

### Gate 2. 최종 승인 기준

- local Markdown Ticket으로 실제 구현 하나가 완료됐다.
- Implementation Lead가 BMAD Story와 Planning Admission을 runtime에서 읽지 않는다.
- Worker, Adapter, evidence, Full 불변조건이 유지된다.
- Ticket 또는 Spec 변경이 네 재검사 지점에서 차단된다.
- 새 provider framework나 Admission 대체 체계가 없다.
- 전역 스킬 변경 여부와 범위가 사용자 승인과 일치한다.
- 실패 시 `implement_lead`만 안전하게 복원할 수 있다.

Gate 2 검증 후 결과와 활성 변경 내역을 사용자에게 보고하고 명시적 최종 승인을 기다린다.

# 7. 검증 명령 원칙

실제 명령은 각 저장소 README/package 설정을 먼저 확인한 뒤 사용한다. 임의 명령을 발명하지 않는다.

Implementation Lead Adapter 회귀는 기존 저장소의 명령을 사용한다. 예시 범주는 다음과 같다.

```text
Node: test, lint, typecheck, build
Python: pytest, ruff, mypy, wheel build
Go: go test, race test, vet, build
```

초기 pilot과 관련 없는 Adapter가 실행 환경 부족으로 검증되지 않으면 `pass`가 아니라 `not tested`로 기록한다.

# 8. 완료 체크리스트

## Phase 0

- [ ] 새 `matt/`에 삭제 전 과설계 산출물이 없다.
- [ ] `implement_lead` 기준선과 미커밋 상태를 기록했다.
- [ ] 전역 스킬을 변경하지 않았다.
- [ ] upstream source와 라이선스를 고정했다.

## Phase 1

- [ ] 필요한 Matt planning 스킬만 로컬 후보로 배치했다.
- [ ] 한국어, 자동 구현 금지, Ticket-first 규칙만 적용했다.
- [ ] SPEC/Ticket template을 만들었다.
- [ ] smoke 흐름을 최대 네 개 안에서 확인했다.
- [ ] 별도 validator, ledger, evidence chain을 만들지 않았다.
- [ ] Gate 1을 사용자가 승인했다.

## Phase 2

- [ ] exact Ticket + exact Worker invocation을 구현했다.
- [ ] PlanningInputSeal을 구현했다.
- [ ] 네 재검사 지점에서 stale 입력을 차단한다.
- [ ] 기존 execution core 불변조건을 유지했다.
- [ ] BMAD runtime 입력을 제거했다.
- [ ] read-only shadow를 통과했다.
- [ ] 실제 non-UI pilot을 통과했다.
- [ ] UI는 필요한 경우에만 별도 pilot했다.
- [ ] cutover와 rollback을 검증했다.

# 9. 최종 성공 형태

```text
사용자 아이디어
→ grill-with-docs 또는 필요한 planning skill
→ 사용자가 승인한 SPEC.md
→ ready TICKET-001.md
→ implementation-lead /exact/path/TICKET-001.md <worker>
→ 기존 Worker / Adapter / Full 코어
→ 완료
```

이 구조를 설명하기 위해 필요한 개념은 다음 세 가지를 넘지 않아야 한다.

```text
Matt 스킬 묶음
Spec과 Ticket
Ticket을 소비하는 Implementation Lead
```

그 이상의 플랫폼 용어가 필요해지면 구현을 멈추고 범위를 다시 축소한다.
