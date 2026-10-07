---
type: conditional-claim
claim_id: CCL-CON-001
claim_kind: capability
domain: console-and-request

decision_question: "기존 Kubernetes Namespace의 이름을 인플레이스 변경할 수 있는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [not-applicable]
purposes: [namespace-rename]
protocols: [not-applicable]

evidence_ids:
  - "2026031609361135305"
  - "2026052718461692688"
  - "2026052618154083992"
  - "2026051509123132269"
evidence_first_seen: 2026-03-16
evidence_last_seen: 2026-05-28

source_fidelity_min: full-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

기존 Kubernetes Namespace의 이름은 생성 후 인플레이스 변경할 수 없다.

## 판단 질문

> 오타나 조직 변경 때문에 기존 Namespace의 이름만 수정할 수 있는가?

## 적용 조건

- 이미 생성된 Kubernetes Namespace의 `metadata.name`을 변경하려는 상황
- 목적이 표시명·별칭 변경이 아니라 실제 Namespace 이름 변경임

## 적용 전 확인할 미지수

- 사용자가 원하는 것이 Namespace 객체 이름 변경인지, Project 표시명·Label·Annotation 변경인지
- 대상이 실제 Kubernetes Namespace인지 DKS 콘솔의 별도 표시 필드인지

## 근거 사슬

1. 2026-03 공식 답변은 Kubernetes가 기존 Namespace 이름 변경 기능을 제공하지 않는다고 직접 명시했다.
2. 2026-05의 두 독립 사례에서도 오타로 만든 Namespace의 이름 변경이 Kubernetes 사양·기능 제약으로 불가능하다고 반복 확인됐다.
3. 다른 2026-05 사례에서도 동일하게 Namespace 이름 변경 기능 미지원이 재확인됐다.
4. 따라서 적용 조건 안에서 기존 Namespace 이름을 직접 수정할 수 없다는 Claim이 반복 근거로 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026031609361135305 | full-dialogue | Kubernetes는 기존 Namespace 이름 변경 기능을 제공하지 않는다. | `VOC/2026-03-15 ~ 2026-03-21 DKS VOC 목록 (12건).md` 512-528행 |
| direct-support | 2026052718461692688 | full-dialogue | Kubernetes 사양상 Namespace 이름 변경은 불가능하다. | `VOC/2026-05-24 ~ 2026-05-30 DKS VOC 목록 (10건).md` 185-189행 |
| direct-support | 2026052618154083992 | full-dialogue | K8s 기능 제약으로 이름 수정이 불가능하다. | 같은 파일 226-230행 |
| corroboration | 2026051509123132269 | full-dialogue | Kubernetes는 Namespace 이름 변경 기능을 지원하지 않는다. | `VOC/2026-05-10 ~ 2026-05-16 DKS VOC 목록 (20건).md` 77-85행 |

## 이 Claim이 말하지 않는 것

- 신규 Namespace 생성과 기존 Namespace 삭제가 자동으로 수행된다는 뜻이 아니다.
- Workload·Secret·권한·PVC·DNS·방화벽이 자동 이전된다는 뜻이 아니다.
- Project 이름이나 콘솔 표시명을 변경할 수 없다는 뜻이 아니다.

## 반례·경쟁 설명

- 사용자가 말한 “Namespace 이름”이 실제 Kubernetes 객체 이름이 아니라 별도 UI 표시명이라면 이 Claim의 적용 대상이 아니다.
- 향후 DKS가 별도의 복제·이전 자동화 기능을 제공하더라도 원래 Namespace 객체의 인플레이스 Rename과는 구별해야 한다.

## 무효화 조건

- Kubernetes 또는 DKS가 기존 Namespace 객체의 식별자를 유지하면서 이름을 변경하는 공식 기능을 제공한다고 확인되면 수정한다.

## 다음 검증

- 현재 DKS 콘솔에서 Namespace 교체·이전 자동화 기능이 제공되는지 확인한다.

## 하위 문서 사용 조건

- 이름 변경 불가라는 경계 설명에는 사용할 수 있다.
- 실제 이전 절차에는 [[CCL-CON-002 - Namespace 이름 교체는 신규 생성과 워크로드 이전으로 처리한다]]와 최신 운영 가이드를 함께 확인한다.
