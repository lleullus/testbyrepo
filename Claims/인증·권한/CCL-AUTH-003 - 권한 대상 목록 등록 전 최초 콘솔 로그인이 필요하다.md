---
type: conditional-claim
claim_id: CCL-AUTH-003
claim_kind: procedure
domain: authentication-and-authorization

decision_question: "One Cloud 멤버인데 DKS 사용자·멤버 목록에 보이지 않을 때 무엇을 확인하는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-C, unknown]
network_profiles: [unknown]
directions: [not-applicable]
purposes: [user-directory-registration, namespace-authorization]
protocols: [not-applicable]

evidence_ids:
  - "2026062313431452587"
  - "2026070616480645617"
  - "2026040315450674172"
evidence_first_seen: 2026-04-03
evidence_last_seen: 2026-07-06

source_fidelity_min: summary-only
depends_on: [CCL-AUTH-001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

관측된 DKS 사용자 등록 흐름에서는 대상 계정이 DKS 콘솔에 최소 1회 로그인해야 플랫폼 사용자 DB와 권한 대상 목록에 나타났다.

## 판단 질문

> One Cloud Project에 추가된 사용자가 DKS 멤버 선택 목록에 보이지 않는 이유는 무엇인가?

## 적용 조건

- One Cloud 또는 상위 권한 시스템에 사용자가 이미 등록됨
- DKS 콘솔의 Project·Namespace 멤버 추가 목록에서 사용자를 찾을 수 없음
- 대상 계정이 DKS 콘솔에 로그인한 적이 있는지 불명확함

## 적용 전 확인할 미지수

- 대상 계정이 실제로 DKS 콘솔 인증에 성공했는지
- 로그인 대상이 올바른 DKS 환경·망인지
- 로그인 후 사용자 DB 동기화 지연이 있는지
- 비실명·협력사 계정에 별도 인증 조건이 있는지

## 근거 사슬

1. 2026-06 비실명계정 사례에서 운영팀은 콘솔 1회 접속 이력이 있어야 사용자 목록에 등록된다고 답했다.
2. 2026-07 DKS-C 사례에서도 One Cloud 멤버 61명 중 12명만 보인 원인을 콘솔 로그인 이력으로 설명했고, 로그인해야 플랫폼 사용자 DB에 등록된다고 명시했다.
3. 서로 다른 계정 유형과 환경에서 같은 선행조건이 반복됐다.
4. 따라서 상위 Membership만으로 목록 노출이 완료되지 않고 최초 콘솔 로그인이 사용자 등록 Trigger로 작동했다는 Claim이 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026062313431452587 | full-dialogue | DKS 콘솔 1회 접속 이력이 있어야 사용자 목록에 등록된다. | `VOC/2026-06-21 ~ 2026-06-27 DKS VOC 목록 (27건).md` 399-405행 |
| direct-support | 2026070616480645617 | full-dialogue | DKS-C 콘솔 로그인 이력이 있어야 플랫폼 사용자 DB에 등록되고 멤버 대상 목록에 나타난다. | `VOC/2026-07-05 ~ 2026-07-11 DKS VOC 목록 (16건).md` 344-348행 |
| corroboration | 2026040315450674172 | summary-only | AD 권한 미보유 계정의 콘솔 1회 로그인 후 연동이 요약됐다. | `VOC/2026-03-29 ~ 2026-04-04 DKS VOC 목록 (11건).md` 요약 목록 |

## 이 Claim이 말하지 않는 것

- 최초 로그인만으로 Project·Namespace 권한이 자동 부여된다는 뜻이 아니다.
- 로그인 성공이 One Cloud Project Membership 승인을 대체한다는 뜻이 아니다.
- 사용자 목록 노출이 즉시 일어난다는 뜻이 아니다.

## 반례·경쟁 설명

- 운영 계정이나 사전 프로비저닝된 계정은 로그인 전에도 등록될 수 있다.
- 사용자 미노출 원인이 Project Membership 누락, 동기화 지연, 잘못된 망·환경일 수도 있다.

## 무효화 조건

- 최신 공식 자료에서 사용자 DB가 로그인과 무관하게 상위 Directory에서 자동 동기화된다고 확인되면 수정한다.

## 다음 검증

- 현재 DKS-N과 DKS-C 각각의 사용자 DB 등록 Trigger와 동기화 시간을 확인한다.
- 첫 로그인 후에도 목록에 없을 때의 점검 경로를 확인한다.

## 하위 문서 사용 조건

- 사용자 미노출 Troubleshooting의 한 분기로 사용할 수 있다.
- 권한 자체는 [[CCL-AUTH-001 - One Cloud Project 멤버 승인이 DKS 권한 할당에 선행한다]]와 [[CCL-AUTH-002 - Project 멤버와 Namespace 멤버 권한은 별도 단계다]]를 함께 적용한다.
