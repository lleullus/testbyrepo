---
type: conditional-claim
claim_id: CCL-RES-002
claim_kind: rule
domain: resource

decision_question: "`exceeded quota` 오류가 발생하면 왜 Pod가 생성되지 않는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [not-applicable]
purposes: [pod-admission, quota-troubleshooting]
protocols: [not-applicable]

evidence_ids:
  - "2026060809152249821"
  - "2026062614334080181"
  - "2026063015591003237"
evidence_first_seen: 2026-06-08
evidence_last_seen: 2026-06-30

source_fidelity_min: full-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

Pod가 추가하는 CPU·Memory Request 또는 Limit의 합계가 Namespace ResourceQuota를 초과하면 해당 Pod 생성이 거부된다.

## 판단 질문

> `exceeded quota: requests.cpu` 또는 `compute-resources` 오류가 발생한 Pod가 왜 뜨지 않는가?

## 적용 조건

- Pod 생성·배포 시 `exceeded quota` 오류가 관측됨
- 오류가 가리키는 ResourceQuota가 CPU Request, CPU Limit, Memory Request 또는 Memory Limit임

## 적용 전 확인할 미지수

- 오류가 Request Quota인지 Limit Quota인지
- Namespace의 현재 Used·Hard 값
- 새 Pod가 추가하려는 Request·Limit 값
- 이전 ReplicaSet·Job·Jenkins Agent 등 종료되지 않은 리소스가 Quota를 점유하는지

## 근거 사슬

1. 2026-06-08 사례는 Namespace CPU·Memory Request 총합이 Quota를 초과해 Pod가 생성되지 않았다고 확인했다.
2. 2026-06-26 사례는 CPU Limit Quota 합계 초과 때문에 Pod가 실행되지 않았다고 확인했다.
3. 2026-06-30 사례는 기존 Request 사용량 87.55 Core에 신규 4 Core 요청을 더하면 90 Core Quota를 넘기 때문에 생성이 거부됐다고 수치로 설명했다.
4. Request와 Limit은 서로 다른 Quota 차원일 수 있지만, 어느 쪽이든 Hard 한도를 초과하면 새 Pod Admission이 거부된다는 공통 규칙이 반복 확인됐다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026060809152249821 | full-dialogue | CPU·Memory Request 총합이 Quota를 초과해 Pod가 생성되지 않았다. | `VOC/2026-06-07 ~ 2026-06-13 DKS VOC 목록 (16건).md` 327-332행 |
| direct-support | 2026062614334080181 | full-dialogue | CPU Limit Quota 합계 초과로 Pod가 실행되지 않았다. | `VOC/2026-06-21 ~ 2026-06-27 DKS VOC 목록 (27건).md` 116-122행 |
| direct-support | 2026063015591003237 | full-dialogue | 87.55 Core 사용 상태에서 4 Core 요청이 90 Core Request Quota를 넘어 생성이 거부됐다. | `VOC/2026-06-28 ~ 2026-07-04 DKS VOC 목록 (17건).md` 321-325행 |

## 이 Claim이 말하지 않는 것

- Quota 증설이 항상 승인된다는 뜻이 아니다.
- Quota가 남아 있으면 실제 Node Capacity도 충분하다는 뜻이 아니다.
- `Pending`의 모든 원인이 Quota라는 뜻이 아니다.
- Request와 Limit 중 어느 값을 낮춰야 하는지를 자동 결정하지 않는다.

## 반례·경쟁 설명

- `Insufficient cpu`, Taint, Affinity, PVC, Image Pull 문제도 Pod를 Pending 또는 미생성 상태로 만들 수 있다.
- Limit Quota 초과를 Request Quota 초과로 오인하면 잘못된 조정을 할 수 있다.

## 무효화 조건

- DKS가 Quota 초과 Pod를 별도 Queue에 보류하거나 자동 증설하는 정책으로 변경되면 수정한다.

## 다음 검증

- DKS Console에서 Used·Hard를 확인하는 현재 경로와 Quota 증설 승인 기준을 확인한다.

## 하위 문서 사용 조건

- `exceeded quota` 오류의 직접 원인 설명에 사용할 수 있다.
- 조치 전에는 불필요 Workload 정리와 증설 중 어느 방식이 적절한지 실제 사용량을 확인해야 한다.
