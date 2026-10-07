---
type: conditional-claim
claim_id: CCL-AUTH-002
claim_kind: boundary
domain: authentication-and-authorization

decision_question: "One Cloud Project 멤버가 되면 DKS Namespace 권한도 자동으로 부여되는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [not-applicable]
purposes: [namespace-authorization]
protocols: [not-applicable]

evidence_ids:
  - "2026041416130946649"
  - "2026051509123132269"
evidence_first_seen: 2026-04-14
evidence_last_seen: 2026-05-15

source_fidelity_min: full-dialogue
depends_on: [CCL-AUTH-001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

One Cloud Project 멤버 승인과 DKS Namespace 멤버 권한 부여는 별도 단계이며, Project 멤버가 된 뒤 DKS 관리자에게 Namespace 권한을 별도로 받아야 한다.

## 판단 질문

> One Cloud Project에 사용자를 추가했는데 왜 Namespace를 사용할 수 없는가?

## 적용 조건

- 사용자가 One Cloud Project 멤버로 이미 승인됨
- 특정 DKS Namespace의 조회·배포·관리 권한을 부여하려는 상황

## 적용 전 확인할 미지수

- One Cloud Project 멤버 정보가 DKS에 동기화됐는지
- 대상 사용자가 DKS 사용자 목록에 표시되는지
- 필요한 Namespace 역할이 무엇인지
- 권한을 부여할 DKS 관리자 또는 대표관리자가 누구인지

## 근거 사슬

1. 2026-04 공식 답변은 One Cloud Project 멤버 승인 후 DKS Project 멤버로 동기화된다고 설명했다.
2. 같은 답변은 그 이후 DKS 관리자에게 Namespace 멤버 권한을 별도로 요청하도록 했다.
3. 2026-05 답변도 One Cloud Project 멤버 추가가 선행돼야 DKS에서 Namespace 권한을 할당할 수 있다고 했다.
4. 따라서 Project 멤버 상태와 Namespace 권한은 같은 상태가 아니라 선후관계를 가진 별도 권한 단계다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026041416130946649 | full-dialogue | Project 멤버 동기화 후 DKS 관리자에게 Namespace 멤버 권한을 요청한다. | `VOC/2026-04-12 ~ 2026-04-18 DKS VOC 목록 (8건).md` 179-184행 |
| corroboration | 2026051509123132269 | full-dialogue | One Cloud Project 멤버 추가 후 DKS에서 Namespace 권한을 할당할 수 있다. | `VOC/2026-05-10 ~ 2026-05-16 DKS VOC 목록 (20건).md` 77-85행 |

## 이 Claim이 말하지 않는 것

- 모든 Namespace에 같은 역할이 부여된다는 뜻이 아니다.
- Project 대표관리자가 자동으로 모든 Namespace 권한을 갖는다는 뜻이 아니다.
- Harbor 권한이 Namespace 권한과 완전히 동일하다는 뜻이 아니다.

## 반례·경쟁 설명

- 일부 자동 프로비저닝 흐름에서는 Project 생성 시 특정 기본 Namespace 권한이 함께 부여될 수 있다.
- 이미 권한이 있는 사용자는 별도 요청이 필요하지 않을 수 있다.

## 무효화 조건

- 최신 공식 자료에서 One Cloud Project Membership이 DKS Namespace Role을 자동으로 포함한다고 확인되면 수정한다.

## 다음 검증

- 현재 Namespace 역할 종류와 기본 부여 규칙을 확인한다.
- DKS-N·DKS-C에서 관리자 권한 부여 흐름이 동일한지 확인한다.

## 하위 문서 사용 조건

- 권한 미노출의 1차 점검 순서에는 사용할 수 있다.
- 실제 Role 선택과 승인 주체는 최신 권한 가이드에서 확인한다.
