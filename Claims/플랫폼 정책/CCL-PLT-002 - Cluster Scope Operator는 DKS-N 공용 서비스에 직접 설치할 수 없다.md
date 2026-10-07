---
type: conditional-claim
claim_id: CCL-PLT-002
claim_kind: capability
domain: platform-policy

decision_question: "CRD·ClusterRole을 요구하는 Operator를 DKS-N 공용 Namespace에 직접 설치할 수 있는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-N, unknown]
network_profiles: [shared-namespace]
directions: [not-applicable]
purposes: [operator-installation]
protocols: [not-applicable]

evidence_ids:
  - "2026011717453599328"
  - "2026012311122738890"
  - "2026032311350183044"
  - "2026041316005436587"
  - "2026051115122000391"
evidence_first_seen: 2026-01-17
evidence_last_seen: 2026-05-11

source_fidelity_min: full-dialogue
depends_on: [CCL-PLT-001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

CRD·ClusterRole 등 Cluster Scope 권한을 필수로 요구하는 Operator는 DKS-N 공용 Namespace 서비스에 사용자가 직접 설치할 수 없다.

## 판단 질문

> Helm Chart가 Operator와 CRD를 포함할 때 공용 DKS Namespace에 그대로 배포할 수 있는가?

## 적용 조건

- 서비스가 DKS-N 또는 공용 Namespace형 DKS임
- Chart·Manifest가 CRD, ClusterRole, ClusterRoleBinding, Admission Webhook 등 Cluster Scope 리소스를 필수로 생성함
- 사용자가 직접 설치하려는 구성임

## 적용 전 확인할 미지수

- Cluster Scope 리소스가 선택 기능인지 필수 기능인지
- Operator 없이 Namespace Scope 리소스만으로 배포 가능한 Chart가 있는지
- DKS가 동일 기능을 표준 Managed Component로 제공하는지
- 독립 Cluster인 DKS-C로 전환 가능한지

## 근거 사슬

1. DKS-N 공용형은 사용자에게 Cluster Scope 권한을 제공하지 않는다.
2. CloudNativePG·Kong·Argo CD·MinIO 사례에서 설치 요구사항으로 CRD·ClusterRole·Operator가 확인됐다.
3. 운영팀은 공용 DKS에서 해당 Cluster Scope 설치를 지원하지 않으며 CRD 없는 구성, 표준 리소스, 비 Operator Chart 또는 독립 Cluster를 검토하도록 답했다.
4. 따라서 Cluster Scope Operator의 사용자 직접 설치는 공용 DKS에서 지원되지 않는다는 Claim이 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026011717453599328 | full-dialogue | CloudNativePG Operator의 Cluster 권한을 지원하지 않는다. | `VOC/2026-01-11 ~ 2026-01-17 DKS VOC 목록 (17건).md` 45-56행 |
| direct-support | 2026012311122738890 | full-dialogue | Kong CRD 권한을 제공하지 않고 CRD 없는 구성 또는 표준 Ingress를 권장했다. | `VOC/2026-01-18 ~ 2026-01-24 DKS VOC 목록 (12건).md` 40-54행 |
| corroboration | 2026032311350183044 | full-dialogue | 공용 Cluster에서 PostgreSQL Operator 대신 Namespace Scope 구성을 안내했다. | `VOC/2026-03-22 ~ 2026-03-28 DKS VOC 목록 (8건).md` 246-261행 |
| direct-support | 2026041316005436587 | full-dialogue | Argo CD 설치용 ClusterRole·CRD 권한을 공용 DKS에서 지원하지 않는다. | `VOC/2026-04-12 ~ 2026-04-18 DKS VOC 목록 (8건).md` 200-205행 |
| direct-support | 2026051115122000391 | full-dialogue | MinIO Operator 대신 비 Operator Helm 또는 DKS-C를 검토하도록 했다. | `VOC/2026-05-10 ~ 2026-05-16 DKS VOC 목록 (20건).md` 344-348행 |

## 이 Claim이 말하지 않는 것

- 해당 제품 자체를 DKS에서 전혀 사용할 수 없다는 뜻이 아니다.
- Namespace Scope 대체 Chart나 외부 Managed Service가 없다는 뜻이 아니다.
- DKS-C에서도 Operator 설치가 항상 허용된다는 뜻이 아니다.

## 반례·경쟁 설명

- Chart에 포함된 CRD가 선택적이며 사전 제거 가능한 경우 Namespace Scope 일부 기능은 사용할 수 있다.
- DKS 운영팀이 Operator를 플랫폼 관리형으로 설치하면 사용자 직접 설치가 아니므로 별도 판단이다.

## 무효화 조건

- 최신 DKS-N 정책에서 특정 CRD·Operator의 Self-Service 또는 승인형 설치를 지원한다고 확인되면 해당 범위를 분리한다.

## 다음 검증

- 현재 DKS-N 표준 Catalog·Managed Operator 목록을 확인한다.
- DKS-C의 Cluster Scope 권한과 PSS·Kyverno 제한을 별도로 확인한다.

## 하위 문서 사용 조건

- 신규 Workload 적합성 검토에서 “Operator 필수 여부”를 조기에 판단하는 데 사용할 수 있다.
- 대체 배포안은 해당 제품의 Namespace Scope 지원과 최신 DKS Catalog를 확인해 작성한다.
