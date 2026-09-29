---
type: conditional-claim
claim_id: CCL-DEP-001
claim_kind: boundary
domain: deployment

decision_question: "DKS 콘솔에서 직접 수정한 Deployment·Ingress 값이 P-DEP 재배포 후 왜 원래대로 돌아가는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [not-applicable]
purposes: [pdep-reconciliation, deployment-configuration]
protocols: [not-applicable]

evidence_ids:
  - "2026012612104247173"
  - "2026041619461767506"
  - "2026051817525049244"
evidence_first_seen: 2026-01-26
evidence_last_seen: 2026-05-19

source_fidelity_min: full-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

P-DEP가 배포 시 생성·치환하는 Deployment·Ingress 필드를 DKS 콘솔에서 직접 수정하면, 다음 P-DEP 재배포 때 Product·Git·CD 설정을 기준으로 다시 렌더링되어 직접 수정값이 덮어써질 수 있다.

## 판단 질문

> DKS 콘솔에서 수정한 Ingress Service 또는 Deployment 환경변수가 P-DEP 재배포 뒤 초기화되는 이유는 무엇인가?

## 적용 조건

- Workload가 P-DEP 파이프라인으로 배포·관리됨
- 수정한 필드가 P-DEP Template, Product 정보, Git Manifest 또는 CD 설정에서 생성되는 필드임
- 콘솔·kubectl에서 Live Resource만 직접 수정함

## 적용 전 확인할 미지수

- 해당 Resource의 선언 원본이 Git, P-DEP Template, CD 설정 중 어디에 있는지
- 어떤 필드가 P-DEP 치환 대상인지
- 수동 수정 이후 P-DEP가 다시 배포됐는지
- 별도 GitOps Controller가 동시에 Reconcile하는지

## 근거 사슬

1. 2026-01 사례에서 P-DEP는 Product 기준으로 Ingress Service 이름을 치환해 배포한다고 설명했다.
2. 2026-04 사례에서도 여러 Path에 수동 지정한 Service가 재배포 때 하나의 Product Service로 일괄 치환됐다.
3. 2026-05 사례에서는 DKS 콘솔에서 수정한 Deployment 환경변수가 P-DEP 재배포 후 원래 값으로 돌아갔다.
4. 서로 다른 Resource와 필드에서 동일한 “배포 원본 기준 재렌더링” 현상이 반복됐으므로 Live Resource 직접 수정은 지속 상태가 아니라는 Claim이 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026012612104247173 | full-dialogue | P-DEP가 Product 기준으로 Ingress Service 이름을 치환한다. | `VOC/2026-01-25 ~ 2026-01-31 DKS VOC 목록 (13건).md` 585-609행 |
| direct-support | 2026041619461767506 | full-dialogue | 재배포 시 Path별 Service가 단일 Product Service명으로 일괄 치환된다. | `VOC/2026-04-12 ~ 2026-04-18 DKS VOC 목록 (8건).md` 91-96행 |
| direct-support | 2026051817525049244 | full-dialogue | DKS 콘솔의 Deployment env 수정이 P-DEP 재배포 뒤 초기화됐다. | `VOC/2026-05-17 ~ 2026-05-23 DKS VOC 목록 (8건).md` 177-181행 |

## 이 Claim이 말하지 않는 것

- DKS 콘솔 직접 수정이 기술적으로 항상 차단된다는 뜻이 아니다.
- 모든 필드가 P-DEP에 의해 덮어써진다는 뜻이 아니다.
- P-DEP 외 배포 방식에도 동일한 동작이 있다는 뜻이 아니다.
- Drift가 발생하면 즉시 자동 복구된다는 뜻이 아니다. 관측된 Trigger는 재배포였다.

## 반례·경쟁 설명

- P-DEP가 관리하지 않는 Resource·필드는 직접 수정이 유지될 수 있다.
- 다른 GitOps Controller나 Admission Policy가 값을 되돌리는 경우 P-DEP가 원인이 아닐 수 있다.

## 무효화 조건

- P-DEP가 Live Resource의 수동 변경을 원본으로 역동기화하거나 특정 필드를 관리 대상에서 제외하는 정책으로 변경되면 범위를 수정한다.

## 다음 검증

- 현재 P-DEP의 Field Ownership·치환 목록과 Drift 처리 방식을 확인한다.

## 하위 문서 사용 조건

- 재배포 후 설정 초기화의 원인 분기에는 사용할 수 있다.
- 지속 변경 방법은 [[CCL-DEP-002 - P-DEP 지속 설정은 Git 또는 CD 정의에 반영한다]]를 함께 적용한다.
