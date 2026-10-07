---
type: conditional-claim
claim_id: CCL-IMG-002
claim_kind: procedure
domain: image-and-registry

decision_question: "AD 비밀번호·Registry Token 변경 후 기존 Workload의 Image Pull이 실패하면 무엇을 갱신해야 하는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [outbound]
purposes: [registry-credential-rotation]
protocols: [https]

evidence_ids:
  - "2026032015044075665"
  - "2026040208180859193"
  - "2026010508063503895"
evidence_first_seen: 2026-01-05
evidence_last_seen: 2026-04-02

source_fidelity_min: summary-only
depends_on: [CCL-IMG-001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

AD 비밀번호나 Registry Token처럼 Pull Secret에 저장된 Credential이 변경되면 기존 Secret은 자동 갱신되지 않을 수 있으므로 최신 Credential로 Secret을 재발급·갱신해야 한다.

## 판단 질문

> 이전까지 정상 Pull되던 Workload가 계정 비밀번호·Token 변경 뒤 401·403으로 실패하는 이유는 무엇인가?

## 적용 조건

- Private Registry Pull이 이전에는 정상 동작함
- Registry 계정 비밀번호·Token·Key가 변경되거나 만료됨
- Workload가 변경 전 Credential을 저장한 Pull Secret을 계속 참조함

## 적용 전 확인할 미지수

- Secret에 어떤 계정·Token이 저장돼 있는지
- Credential 변경 시점과 Image Pull 실패 시작 시점
- 여러 Namespace·ServiceAccount에 동일 Credential이 복제돼 있는지
- Robot Account 또는 장기 Token으로 전환 가능한지

## 근거 사슬

1. 2026-04 사례에서 AD 비밀번호 변경 뒤 Harbor Pull이 401로 실패했고 운영팀은 Pull Secret 갱신을 직접 요구했다.
2. 2026-03 사례에서도 403이 계속되자 Credential 변경·정책 변경으로 Secret 데이터가 달라졌을 가능성을 제시하고 최신 Credential로 재발급·갱신하도록 했다.
3. 2026-01 요약 사례도 AD 비밀번호 만료 후 Secret 재생성으로 분류됐다.
4. 따라서 Pull Secret은 외부 Credential 변경을 자동 추종하지 않을 수 있으며 회전 시 갱신이 필요하다는 Claim이 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026040208180859193 | full-dialogue | AD 비밀번호 변경으로 401이 발생해 Pull Secret 갱신이 필요했다. | `VOC/2026-03-29 ~ 2026-04-04 DKS VOC 목록 (11건).md` 220-240행 |
| direct-support | 2026032015044075665 | full-dialogue | 403 발생 시 최신 Credential로 Secret 재발급·갱신을 안내했다. | `VOC/2026-03-15 ~ 2026-03-21 DKS VOC 목록 (12건).md` 155-162행 |
| corroboration | 2026010508063503895 | summary-only | AD 비밀번호 만료와 Secret 재생성이 요약됐다. | `VOC/2026-01-04 ~ 2026-01-10 DKS VOC 목록 (16건).md` 28행 |

## 이 Claim이 말하지 않는 것

- Credential 변경이 모든 401·403의 원인이라는 뜻이 아니다.
- Secret을 갱신하면 Running Pod의 Image가 자동 재Pull된다는 뜻이 아니다.
- 개인 AD 계정을 장기 자동화 Credential로 사용하라는 뜻이 아니다.

## 반례·경쟁 설명

- Registry 권한 회수, Repository 경로 변경, Tag 삭제, Network·TLS 문제도 같은 오류를 낼 수 있다.
- Robot Account·Workload Identity처럼 비밀번호 회전과 분리된 Credential은 다른 수명주기를 가진다.

## 무효화 조건

- Registry와 DKS가 Credential 자동 Rotation·Secret 동기화를 공식 제공하면 수동 갱신 범위를 수정한다.

## 다음 검증

- 현재 Harbor에서 Workload용 Robot Account·Token을 발급하는 권장 절차와 만료 정책을 확인한다.
- 여러 Namespace의 Secret Rotation 자동화 방법을 확인한다.

## 하위 문서 사용 조건

- Credential Rotation Runbook의 Trigger로 사용할 수 있다.
- Secret 갱신 후 신규 Pod 생성 또는 Rollout 필요 여부는 배포 방식에 따라 별도 확인한다.
