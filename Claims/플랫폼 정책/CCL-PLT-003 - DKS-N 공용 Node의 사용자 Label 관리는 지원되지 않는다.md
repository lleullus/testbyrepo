---
type: conditional-claim
claim_id: CCL-PLT-003
claim_kind: prohibition
domain: platform-policy

decision_question: "DKS-N 사용자가 공용 Worker Node에 임의 Label을 추가·관리할 수 있는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-N]
network_profiles: [shared-worker]
directions: [not-applicable]
purposes: [node-label-management, workload-placement]
protocols: [not-applicable]

evidence_ids:
  - "2026051108533795058"
  - "2026052214564372597"
evidence_first_seen: 2026-05-11
evidence_last_seen: 2026-05-22

source_fidelity_min: full-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

DKS-N 공용 Worker Node는 여러 사용자가 공유하는 플랫폼 자원이므로 사용자가 임의 Node Label을 추가·관리하는 기능을 지원하지 않는다.

## 판단 질문

> 특정 Node에만 Workload를 배치하기 위해 DKS-N 공용 Node에 사용자 Label을 붙일 수 있는가?

## 적용 조건

- 서비스 모델이 DKS-N 공용형임
- 대상 Node가 사용자 전용 Node가 아니라 공용 Worker임
- 사용자가 NodeSelector·Affinity용 사용자 정의 Label을 요청함

## 적용 전 확인할 미지수

- 대상 Cluster·Node Pool이 공용인지 전용인지
- 플랫폼이 제공하는 기존 표준 Label을 조회·사용할 수 있는지
- 요구 목적이 Node 고정인지 단순 Replica 수 제한인지
- DKS-C 또는 전용 Node Pool 대안이 있는지

## 근거 사슬

1. 2026-05-11 사례에서 운영팀은 공용 DKS-N Node가 공유 자원이므로 사용자 Label 관리를 지원하지 않는다고 직접 답했다.
2. 2026-05-22 DaemonSet 사례에서도 공용 Node Label 관리를 사용자에게 지원하지 않는다고 재확인했다.
3. 서로 다른 배치 목적에서 동일한 플랫폼 경계가 반복됐으므로 Claim이 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026051108533795058 | full-dialogue | 공용 DKS-N Node는 공유 자원이라 사용자 Label 관리를 지원하지 않는다. | `VOC/2026-05-10 ~ 2026-05-16 DKS VOC 목록 (20건).md` 464-468행 |
| direct-support | 2026052214564372597 | full-dialogue | 공용 Node Label 관리는 사용자에게 지원되지 않는다. | `VOC/2026-05-17 ~ 2026-05-23 DKS VOC 목록 (8건).md` 36-40행 |

## 이 Claim이 말하지 않는 것

- 플랫폼 표준 Label을 NodeSelector로 사용할 수 없다는 뜻이 아니다.
- DKS-C 또는 전용 Node Pool에서도 사용자 Label 관리가 불가능하다는 뜻이 아니다.
- Workload 배치 제어 자체가 불가능하다는 뜻이 아니다.

## 반례·경쟁 설명

- 전용 Node Pool·DKS-C에서는 다른 권한 모델이 적용될 수 있다.
- 특정 기간 운영팀이 임시 Node를 지정한 사례는 사용자 Label Self-Service를 의미하지 않는다.

## 무효화 조건

- 최신 정책에서 DKS-N 사용자 정의 Node Label 또는 승인형 Label 요청을 지원하면 해당 범위를 분리한다.

## 다음 검증

- 현재 DKS-N의 표준 Node Label 목록과 사용자 Workload Scheduling에 허용된 Selector·Affinity 범위를 확인한다.

## 하위 문서 사용 조건

- Workload 적합성 검토에서 Node Label 요구를 사전에 식별하는 데 사용할 수 있다.
- 대안은 요구 목적에 따라 Deployment 전환, 표준 Label 사용, 전용형 전환을 별도로 검토한다.
