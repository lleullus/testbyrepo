---
type: conditional-claim
claim_id: CCL-AUTH-001
claim_kind: procedure
domain: authentication-and-authorization

decision_question: "신규 사용자에게 DKS Namespace 또는 Harbor 권한을 부여하기 전에 어떤 Project 권한이 필요한가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [not-applicable]
purposes: [project-membership, namespace-authorization, harbor-authorization]
protocols: [not-applicable]

evidence_ids:
  - "2026040119202958138"
  - "2026041416130946649"
  - "2026051509123132269"
  - "2026051109591596152"
evidence_first_seen: 2026-04-01
evidence_last_seen: 2026-05-15

source_fidelity_min: full-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

관측된 DKS 권한 부여 흐름에서는 대상 사용자가 One Cloud에서 해당 Project 멤버로 신청·승인된 뒤에 DKS Project·Namespace·Harbor 권한을 할당할 수 있었다.

## 판단 질문

> 사용자가 DKS Namespace 또는 Harbor 멤버 목록에 없을 때 먼저 무엇을 확인해야 하는가?

## 적용 조건

- 기존 One Cloud Project와 연결된 DKS Project·Namespace·Harbor에 사용자를 추가하려는 상황
- 사용자가 아직 해당 One Cloud Project 멤버로 승인됐는지 불명확함

## 적용 전 확인할 미지수

- 대상 사용자 계정이 One Cloud Project 멤버로 승인됐는지
- 인사정보·권한 동기화가 완료됐는지
- DKS 콘솔 최초 로그인 조건이 추가로 필요한지
- 협력사·비실명 계정에 별도 절차가 있는지

## 근거 사슬

1. 2026-04 협력사 계정 사례에서 운영팀은 DKS·Harbor 권한 부여 전에 One Cloud Project 권한 신청과 승인을 요구했다.
2. 다른 2026-04 사례에서는 One Cloud Project 멤버 승인 후 인사정보가 동기화되어 DKS Project 멤버가 된다고 설명했다.
3. 2026-05 사례도 Namespace 멤버 권한을 할당하기 전에 One Cloud Project 멤버로 먼저 추가하도록 답했다.
4. 따라서 관측된 흐름에서 One Cloud Project 멤버 승인은 DKS 하위 권한 할당의 선행조건이었다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026040119202958138 | full-dialogue | One Cloud Project 권한 승인 후 DKS·Harbor 권한 부여가 가능하다. | `VOC/2026-03-29 ~ 2026-04-04 DKS VOC 목록 (11건).md` 275-281행 |
| direct-support | 2026041416130946649 | full-dialogue | One Cloud Project 멤버 승인 후 동기화되어 DKS Project 멤버로 추가된다. | `VOC/2026-04-12 ~ 2026-04-18 DKS VOC 목록 (8건).md` 179-184행 |
| direct-support | 2026051509123132269 | full-dialogue | Namespace 권한 전에 One Cloud Project 멤버 추가가 필요하다. | `VOC/2026-05-10 ~ 2026-05-16 DKS VOC 목록 (20건).md` 77-85행 |
| corroboration | 2026051109591596152 | full-dialogue | DKS Project 사용자 추가 전 One Cloud Project 멤버 등록을 안내했다. | `VOC/2026-05-10 ~ 2026-05-16 DKS VOC 목록 (20건).md` 444-448행 |

## 이 Claim이 말하지 않는 것

- One Cloud Project 멤버 승인이 곧바로 모든 Namespace·Harbor 권한을 부여한다는 뜻이 아니다.
- 동기화가 즉시 완료된다는 뜻이 아니다.
- Project 대표관리자·관리자·일반 멤버 역할이 동일하다는 뜻이 아니다.

## 반례·경쟁 설명

- 기존에 동기화된 사용자나 플랫폼 운영 계정은 다른 흐름을 사용할 수 있다.
- DKS-C Tenant 또는 별도 망 환경에서 권한 시스템이 바뀌었을 가능성이 있다.

## 무효화 조건

- 최신 공식 자료에서 DKS 권한이 One Cloud Project Membership과 독립적으로 관리된다고 확인되면 수정한다.

## 다음 검증

- 현재 One Cloud → DKS 사용자 동기화 주기와 실패 확인 방법을 검증한다.
- DKS-N과 DKS-C의 권한 소스가 동일한지 확인한다.

## 하위 문서 사용 조건

- 사용자 추가의 선행조건 점검에는 사용할 수 있다.
- 실제 역할 부여는 [[CCL-AUTH-002 - Project 멤버와 Namespace 멤버 권한은 별도 단계다]]와 현재 권한 가이드를 함께 확인한다.
