---
type: conditional-claim
claim_id: CCL-CON-002
claim_kind: procedure
domain: console-and-request

decision_question: "이름을 바꿀 수 없는 Namespace를 다른 이름으로 교체하려면 어떤 패턴을 사용하는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [not-applicable]
purposes: [namespace-replacement]
protocols: [not-applicable]

evidence_ids:
  - "2026031609361135305"
  - "2026052718461692688"
  - "2026052618154083992"
  - "2026051509123132269"
evidence_first_seen: 2026-03-16
evidence_last_seen: 2026-05-28

source_fidelity_min: full-dialogue
depends_on: [CCL-CON-001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

관측된 DKS Namespace 이름 교체 절차에서는 원하는 이름의 신규 Namespace를 생성하고 Workload를 이전한 뒤 기존 Namespace를 삭제했다.

## 판단 질문

> 기존 Namespace 이름을 바꿀 수 없다면 어떤 방식으로 새 이름으로 전환하는가?

## 적용 조건

- [[CCL-CON-001 - Namespace 이름은 생성 후 변경할 수 없다]]가 적용됨
- 사용자가 기존 Namespace를 다른 이름의 Namespace로 실제 교체하려는 상황
- 단순 표시명 변경이 아님

## 적용 전 확인할 미지수

- 이전해야 할 Workload·ConfigMap·Secret·ServiceAccount·RoleBinding 목록
- PVC·PV와 데이터의 이전 또는 재연결 가능 여부
- DNS·Ingress·Gateway·방화벽·CI/CD 대상 이름 변경 영향
- 신규 Namespace 생성 승인과 기존 Namespace 삭제 조건
- 전환 중 중단 허용 여부와 Rollback 방법

## 근거 사슬

1. Namespace 자체는 이름을 인플레이스 변경할 수 없다.
2. 2026-03 답변은 현재 Namespace 삭제 후 원하는 이름의 새 Namespace를 신청하도록 했다.
3. 2026-05의 복수 답변은 신규 Namespace 생성 후 Workload를 이전하고 기존 Namespace를 삭제하도록 했다.
4. 따라서 관측된 교체 패턴은 “신규 생성 → 이전 → 기존 삭제”다.
5. 다만 원문은 전체 리소스·데이터 이전 절차를 제공하지 않으므로 이 Claim은 상위 패턴까지만 정당화한다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026031609361135305 | full-dialogue | 기존 Namespace 삭제 후 새 이름으로 신규 신청하도록 안내했다. | `VOC/2026-03-15 ~ 2026-03-21 DKS VOC 목록 (12건).md` 523-528행 |
| direct-support | 2026052718461692688 | full-dialogue | 신규 Namespace 생성 후 Workload 이전과 기존 Namespace 삭제를 안내했다. | `VOC/2026-05-24 ~ 2026-05-30 DKS VOC 목록 (10건).md` 185-189행 |
| direct-support | 2026052618154083992 | full-dialogue | 신규 신청과 기존 Namespace 삭제를 안내했다. | 같은 파일 226-230행 |
| corroboration | 2026051509123132269 | full-dialogue | 신규 Namespace 생성 후 Workload 이전을 안내했다. | `VOC/2026-05-10 ~ 2026-05-16 DKS VOC 목록 (20건).md` 77-85행 |

## 이 Claim이 말하지 않는 것

- Namespace의 모든 리소스가 자동 복제된다는 뜻이 아니다.
- PVC·데이터·외부 연동을 무중단으로 이전할 수 있다는 뜻이 아니다.
- 기존 Namespace를 먼저 삭제해야 한다는 뜻이 아니다. 안전한 순서와 동시 존재 가능성은 별도 검증이 필요하다.
- 삭제 전 Backup·Rollback 절차가 불필요하다는 뜻이 아니다.

## 반례·경쟁 설명

- 단순 오타라도 Workload·데이터가 많으면 새 Namespace로의 이전 비용이 이름 유지 비용보다 클 수 있다.
- DKS가 향후 Namespace 복제·Migration 자동화를 제공하면 세부 절차는 달라질 수 있다.

## 무효화 조건

- 공식 Rename 기능 또는 기존 Namespace를 보존한 자동 Migration 기능이 제공되면 절차를 갱신한다.

## 다음 검증

- DKS의 현재 Namespace 신규 신청·삭제 순서와 Project 내 동시 Namespace 생성 제한을 확인한다.
- PVC·Secret·권한·DNS·CI/CD를 포함한 별도 Migration Runbook이 존재하는지 확인한다.

## 하위 문서 사용 조건

- 이 Claim은 상위 전환 패턴만 제공한다.
- 실제 작업계획서는 영향 리소스 목록, 데이터 이전, 검증, Rollback을 별도로 작성해야 한다.
