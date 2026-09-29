---
type: conditional-claim
claim_id: CCL-RES-001
claim_kind: rule
domain: resource

decision_question: "DKS Workload의 CPU·Memory Request와 Limit은 어떤 비율 범위로 설정하는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [not-applicable]
purposes: [resource-quota, workload-resource-sizing]
protocols: [not-applicable]

evidence_ids:
  - "2026060509215539969"
  - "2026061614210309995"
  - "2026062614334080181"
evidence_first_seen: 2026-06-05
evidence_last_seen: 2026-06-26

source_fidelity_min: full-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

2026-06에 관측된 DKS Namespace 자원 정책에서는 CPU·Memory Request:Limit 비율을 1:3으로 적용하고, Workload Limit을 Request의 최대 3배 범위로 설정했다.

## 판단 질문

> P-DEP 또는 Manifest에서 CPU·Memory Request와 Limit을 어떤 비율로 설정해야 하는가?

## 적용 조건

- DKS Namespace Quota와 Workload Resource Request·Limit을 산정하는 상황
- 대상 환경이 2026-06 관측 정책과 동일한 자원 정책을 사용하는 경우

## 적용 전 확인할 미지수

- 대상 서비스 모델과 Namespace에 현재 적용된 Quota 정책
- CPU와 Memory에 동일한 비율이 적용되는지
- P-DEP Template이 별도 최소·최대값을 강제하는지
- 예외 승인 또는 특수 Workload 정책이 있는지

## 근거 사슬

1. 2026-06-05 공식 답변은 자원 효율화를 위해 Namespace CPU·Memory Quota를 Request:Limit 1:1에서 1:3으로 변경했다고 명시했다.
2. 같은 답변은 Limit 대비 1/3의 Request 자원으로 증설 신청하도록 안내했다.
3. 2026-06-16 답변은 P-DEP Template에서 Limit을 Request의 최대 3배까지 설정할 수 있다고 재확인했다.
4. 2026-06-26 Quota 초과 답변도 1:3 기준을 적용한다고 재확인했다.
5. 따라서 관측 시점의 정책값으로서 Request:Limit 1:3 Claim이 반복 근거로 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026060509215539969 | full-dialogue | Namespace CPU·Memory Quota에 Request:Limit 1:3을 적용했다. | `VOC/2026-05-31 ~ 2026-06-06 DKS VOC 목록 (9건).md` 63-75행 |
| direct-support | 2026061614210309995 | full-dialogue | P-DEP에서 Limit을 Request의 최대 3배까지 설정할 수 있다. | `VOC/2026-06-14 ~ 2026-06-20 DKS VOC 목록 (10건).md` 147-153행 |
| corroboration | 2026062614334080181 | full-dialogue | CPU Quota 초과 대응에서 Request:Limit 1:3 기준을 재확인했다. | `VOC/2026-06-21 ~ 2026-06-27 DKS VOC 목록 (27건).md` 116-122행 |

## 이 Claim이 말하지 않는 것

- 모든 Workload가 Limit을 반드시 Request의 3배로 설정해야 한다는 뜻이 아니다.
- 1:3이 성능 최적값 또는 비용 최적값이라는 뜻이 아니다.
- Namespace Quota가 실제 Node Capacity를 보장한다는 뜻이 아니다.
- 2026-09-25 현재도 동일 정책임을 보장하지 않는다.

## 반례·경쟁 설명

- Workload 특성에 따라 Request와 Limit을 동일하게 설정해야 안정적인 경우가 있다.
- 서비스 모델·Cluster·망별로 다른 정책을 적용할 가능성이 있다.

## 무효화 조건

- 최신 공식 자원 정책에서 Request:Limit 비율이 변경되거나 비율 강제가 폐지됐다고 확인되면 supersede한다.

## 다음 검증

- 현재 DKS-N·DKS-C별 CPU·Memory Quota 비율과 P-DEP Validation 규칙을 확인한다.

## 하위 문서 사용 조건

- 과거 정책 분석과 산정 예시에는 사용할 수 있다.
- 실제 신청·배포 값은 현재 Console·P-DEP Validation과 최신 정책을 확인해야 한다.
