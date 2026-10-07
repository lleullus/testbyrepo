---
type: conditional-claim
claim_id: CCL-DEP-002
claim_kind: procedure
domain: deployment

decision_question: "P-DEP 재배포 후에도 유지돼야 하는 설정은 어디에 반영해야 하는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [not-applicable]
purposes: [pdep-configuration-source]
protocols: [not-applicable]

evidence_ids:
  - "2026012612104247173"
  - "2026041619461767506"
  - "2026051817525049244"
evidence_first_seen: 2026-01-26
evidence_last_seen: 2026-05-19

source_fidelity_min: full-dialogue
depends_on: [CCL-DEP-001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

P-DEP 재배포 후에도 유지돼야 하는 설정은 Live Resource만 수정하지 말고 Git Manifest, P-DEP CD 설정 또는 필요한 경우 Custom CD의 선언 원본에 반영한다.

## 판단 질문

> 환경변수·Secret·Ingress Backend 같은 설정을 재배포 후에도 유지하려면 어디를 수정해야 하는가?

## 적용 조건

- [[CCL-DEP-001 - P-DEP 관리 필드의 콘솔 직접 수정은 재배포 시 덮어써질 수 있다]]가 적용됨
- 변경값을 다음 P-DEP 배포에도 지속해야 함
- 해당 설정을 표현할 수 있는 Git·CD·Custom CD 원본이 존재함

## 적용 전 확인할 미지수

- 설정의 Source of Truth가 Git Manifest인지 P-DEP CD UI인지
- 기본 CD Template가 표현할 수 있는 필드인지
- Custom CD 전환 시 CI+CD 자동화·Artifact Tag 처리에 어떤 제약이 생기는지
- Secret 값을 Git에 평문으로 둘 수 없는 보안 요구

## 근거 사슬

1. P-DEP 관리 필드의 Live 수정은 재배포 때 덮어써질 수 있다.
2. 2026-05 환경변수 사례에서 운영팀은 Git의 `deployments.yaml` 또는 P-DEP CD 설정 탭에 값을 등록하도록 했다.
3. 2026-01·04 Ingress 다중 Backend 사례에서는 기본 Product 치환으로 표현할 수 없어 Custom CD를 사용하도록 했다.
4. 따라서 지속 설정은 배포 원본에 반영하며, 기본 모델이 표현하지 못하는 구성만 Custom CD로 분기한다는 절차가 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026051817525049244 | full-dialogue | 환경변수는 Git `deployments.yaml` 또는 P-DEP CD 설정에서 등록한다. | `VOC/2026-05-17 ~ 2026-05-23 DKS VOC 목록 (8건).md` 177-181행 |
| direct-support | 2026012612104247173 | full-dialogue | 기본 치환으로 표현할 수 없는 Ingress는 Custom CD가 필요하며 수동 CD 제약이 있다. | `VOC/2026-01-25 ~ 2026-01-31 DKS VOC 목록 (13건).md` 598-609행 |
| corroboration | 2026041619461767506 | full-dialogue | Path별 다중 Service 구성이 필요하면 Custom CD와 수동 처리 제약을 안내했다. | `VOC/2026-04-12 ~ 2026-04-18 DKS VOC 목록 (8건).md` 91-96행 |

## 이 Claim이 말하지 않는 것

- 모든 설정을 Git에 평문으로 저장하라는 뜻이 아니다.
- Custom CD가 기본 선택이라는 뜻이 아니다.
- Git 수정만 하면 즉시 Cluster에 반영된다는 뜻이 아니다.
- P-DEP 외 GitOps 도구의 Source of Truth 위치를 규정하지 않는다.

## 반례·경쟁 설명

- 일회성 진단용 변경이나 P-DEP 비관리 필드는 Live 수정만으로 충분할 수 있다.
- Secret은 External Secret, Vault, P-DEP Secret 기능 등 별도 보안 원본이 필요할 수 있다.

## 무효화 조건

- P-DEP가 Live 변경의 역동기화 또는 Field별 관리 제외 기능을 제공하면 원본 반영 경로를 수정한다.

## 다음 검증

- 현재 P-DEP CD 설정이 지원하는 Field 목록과 Custom CD의 자동화 제약을 확인한다.

## 하위 문서 사용 조건

- 설정 지속성 원칙에는 사용할 수 있다.
- 구체적인 파일·UI 경로와 Secret 처리 방식은 현재 P-DEP 가이드에서 확인한다.
