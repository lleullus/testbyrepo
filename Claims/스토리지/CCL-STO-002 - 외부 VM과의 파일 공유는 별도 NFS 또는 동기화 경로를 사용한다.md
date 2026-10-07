---
type: conditional-claim
claim_id: CCL-STO-002
claim_kind: procedure
domain: storage

decision_question: "DKS PVC를 외부 VM에 직접 마운트할 수 없을 때 Pod와 VM이 파일을 어떻게 교환하는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [managed-worker-storage-acl]
directions: [not-applicable]
purposes: [cross-platform-file-sharing]
protocols: [nfs, rsync]

evidence_ids:
  - "2026040908233608510"
  - "2026042810465626401"
evidence_first_seen: 2026-04-09
evidence_last_seen: 2026-04-28

source_fidelity_min: full-dialogue
depends_on: [CCL-STO-001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

관측된 대안에서는 외부 VM에 별도 NFS Server를 구성해 Pod가 그 NFS를 마운트하거나, 해당 공유 경로를 통해 `rsync` 등으로 데이터를 동기화했다.

## 판단 질문

> DKS PVC를 VM에 직접 마운트할 수 없을 때 VM과 Pod가 데이터를 공유하는 대체 방식은 무엇인가?

## 적용 조건

- [[CCL-STO-001 - DKS PVC는 외부 일반 VM에 직접 마운트할 수 없다]]가 적용됨
- VM과 Pod 사이에 파일 단위 공유 또는 복제가 필요함
- VM이 NFS Server를 운영할 수 있고 Pod에서 해당 Server로 네트워크 접근할 수 있음

## 적용 전 확인할 미지수

- NFS Server의 운영·백업·가용성 책임 주체
- NFS Port와 방화벽·ACL
- 파일 일관성 요구와 동시 쓰기 여부
- 성능·용량·보안 요구
- `rsync` 주기와 실패 복구 방식

## 근거 사슬

1. DKS PVC를 외부 VM에 직접 마운트할 수 없다는 경계가 확인됐다.
2. 2026-04-09 답변은 VM에서 NFS Server를 만들고 Pod가 그 NFS Volume을 마운트하는 대안을 제시했다.
3. 2026-04-28 답변은 같은 방향에 `rsync` 동기화를 결합한 대안을 제시했다.
4. 따라서 관측된 대체 패턴은 DKS 관리 PVC의 ACL을 확장하는 것이 아니라 별도 공유 지점을 만들고 Pod가 Client로 접근하는 방식이다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026040908233608510 | full-dialogue | VM에 NFS Server를 구성하고 Pod에서 NFS Volume으로 Mount하도록 권장했다. | `VOC/2026-04-05 ~ 2026-04-11 DKS VOC 목록 (12건).md` 129-150행 |
| direct-support | 2026042810465626401 | full-dialogue | VM NFS를 Pod에서 Mount한 뒤 rsync로 동기화하는 방식을 권장했다. | `VOC/2026-04-26 ~ 2026-05-02 DKS VOC 목록 (9건).md` 159-164행 |

## 이 Claim이 말하지 않는 것

- VM NFS가 DKS의 관리형·표준 서비스라는 뜻이 아니다.
- 동시 쓰기 데이터베이스나 강한 일관성이 필요한 데이터에 적합하다는 뜻이 아니다.
- 보안 검토·방화벽·백업 없이 사용할 수 있다는 뜻이 아니다.
- Object Storage, SFTP, API 등 다른 대안이 부적절하다는 뜻이 아니다.

## 반례·경쟁 설명

- 대용량·고성능·다중 Writer 요구에는 VM NFS가 병목이나 단일 장애점이 될 수 있다.
- 단방향 Log Export라면 Object Storage, Log Pipeline 또는 API 방식이 더 적합할 수 있다.

## 무효화 조건

- DKS가 외부 VM과의 승인형 Shared Storage 또는 Managed Data Exchange 기능을 제공하면 대안 우선순위를 갱신한다.

## 다음 검증

- 현재 허용되는 외부 NFS Endpoint·Protocol·StorageClass 사용 조건을 확인한다.
- 데이터 성격별 권장 교환 방식이 공식 문서에 있는지 확인한다.

## 하위 문서 사용 조건

- 아키텍처 대안 후보로만 사용한다.
- 실제 설계는 보안·성능·가용성·데이터 일관성 요구를 별도로 검토해야 한다.
