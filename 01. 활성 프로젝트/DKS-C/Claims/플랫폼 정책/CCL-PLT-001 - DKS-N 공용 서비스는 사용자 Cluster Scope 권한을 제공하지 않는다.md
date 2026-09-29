---
type: conditional-claim
claim_id: CCL-PLT-001
claim_kind: prohibition
domain: platform-policy

decision_question: "DKS-N 공용 Namespace 사용자가 ClusterRole·CRD 등 Cluster Scope 리소스를 생성할 수 있는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-N, unknown]
network_profiles: [shared-namespace]
directions: [not-applicable]
purposes: [cluster-scope-authorization]
protocols: [not-applicable]

evidence_ids:
  - "2026011717453599328"
  - "2026012311122738890"
  - "2026041316005436587"
  - "2026051115122000391"
evidence_first_seen: 2026-01-17
evidence_last_seen: 2026-05-11

source_fidelity_min: full-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

DKS-N 공용 Namespace 서비스에서는 사용자에게 Namespace Scope 권한만 제공하며 ClusterRole·CRD 등 Cluster Scope 리소스 권한을 제공하지 않는다.

## 판단 질문

> 공용 DKS Namespace 안에서 Cluster Scope 리소스 생성 권한을 받을 수 있는가?

## 적용 조건

- 서비스가 DKS-N 또는 공용 Namespace형 DKS임
- 사용자가 ClusterRole, ClusterRoleBinding, CRD 또는 Cluster Scope Operator 리소스를 생성하려는 상황

## 적용 전 확인할 미지수

- 대상 서비스가 실제 DKS-N 공용형인지 DKS-C 독립형인지
- 요청 리소스가 Namespace Scope인지 Cluster Scope인지
- DKS가 해당 기능을 표준 Managed Component로 제공하는지

## 근거 사슬

1. 2026-01 CloudNativePG 사례에서 운영팀은 사용자에게 Namespace Scope 권한만 제공하고 Cluster 권한은 지원하지 않는다고 답했다.
2. 같은 달 Kong CRD 사례에서도 안정성과 보안을 이유로 Namespace Scope만 제공하고 Cluster Scope를 지원하지 않는다고 답했다.
3. 2026-04 Argo CD 사례는 공용 DKS의 타 과제 영향 방지를 이유로 Cluster Scope 권한 미지원을 재확인했다.
4. 2026-05 답변은 기존 DKS-N 공용 Namespace 서비스가 Cluster Scope 권한이 필요한 Operator를 지원하지 않는다고 명시했다.
5. 따라서 적용 조건 안에서 사용자 Cluster Scope 권한 미제공 Claim이 반복 근거로 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026011717453599328 | full-dialogue | 사용자에게 Namespace Scope 권한만 제공하고 Cluster 권한은 지원하지 않는다. | `VOC/2026-01-11 ~ 2026-01-17 DKS VOC 목록 (17건).md` 45-56행 |
| direct-support | 2026012311122738890 | full-dialogue | 안정성과 보안을 위해 Namespace Scope만 제공하고 Cluster Scope를 지원하지 않는다. | `VOC/2026-01-18 ~ 2026-01-24 DKS VOC 목록 (12건).md` 40-54행 |
| direct-support | 2026041316005436587 | full-dialogue | 공용 DKS는 Namespace Scope 서비스이며 Cluster Scope 권한을 지원하지 않는다. | `VOC/2026-04-12 ~ 2026-04-18 DKS VOC 목록 (8건).md` 200-205행 |
| direct-support | 2026051115122000391 | full-dialogue | 기존 DKS-N은 Cluster Scope Operator 생성을 지원하지 않는다. | `VOC/2026-05-10 ~ 2026-05-16 DKS VOC 목록 (20건).md` 344-348행 |

## 이 Claim이 말하지 않는 것

- DKS-C 독립 클러스터에서도 Cluster Scope 권한을 제공하지 않는다는 뜻이 아니다.
- DKS 운영팀이 관리하는 표준 Cluster Scope Component가 존재하지 않는다는 뜻이 아니다.
- Namespace Scope 리소스까지 생성할 수 없다는 뜻이 아니다.

## 반례·경쟁 설명

- DKS가 표준 관리형 Operator를 플랫폼 Component로 제공하는 경우 사용자가 직접 Cluster Scope 권한을 갖지 않아도 기능을 사용할 수 있다.
- DKS-C와 같이 독립 Cluster 권한 모델은 별도 검증이 필요하다.

## 무효화 조건

- 최신 공식 정책에서 DKS-N 사용자에게 제한된 Cluster Scope Self-Service 권한을 제공한다고 확인되면 수정한다.

## 다음 검증

- 현재 DKS-N 허용 리소스 목록과 표준 관리형 Operator 목록을 확인한다.
- DKS-C 사용자 Cluster Scope 권한 범위를 별도 Claim으로 검증한다.

## 하위 문서 사용 조건

- 공용 DKS에서 배포 가능성을 검토할 때의 권한 경계로 사용할 수 있다.
- 구체적인 Operator 가능 여부는 [[CCL-PLT-002 - Cluster Scope Operator는 DKS-N 공용 서비스에 직접 설치할 수 없다]]와 현재 지원 목록을 함께 확인한다.
