---
type: conditional-claim
claim_id: CCL-STO-001
claim_kind: boundary
domain: storage

decision_question: "DKS StorageClass로 생성한 PVC·PV를 DKS 외부 일반 VM에 직접 마운트할 수 있는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [managed-worker-storage-acl]
directions: [not-applicable]
purposes: [cross-platform-file-sharing, external-vm-mount]
protocols: [nfs]

evidence_ids:
  - "2026040908233608510"
  - "2026042810465626401"
  - "2026051910115652478"
evidence_first_seen: 2026-04-09
evidence_last_seen: 2026-05-19

source_fidelity_min: full-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

DKS StorageClass로 프로비저닝된 PVC·NAS 볼륨은 DKS 관리 Worker Node에만 스토리지 ACL이 허용되어 있어 DKS 외부의 일반 사용자 VM에 직접 마운트할 수 없다.

## 판단 질문

> DKS Pod가 쓰는 PVC를 로그 분석이나 파일 공유 목적으로 외부 VM에서도 직접 마운트할 수 있는가?

## 적용 조건

- 볼륨이 DKS StorageClass를 통해 프로비저닝됨
- 마운트 주체가 DKS 관리 Worker Node가 아닌 일반 사용자 VM임
- 목적이 동일 PV·PVC를 직접 공유하는 것임

## 적용 전 확인할 미지수

- 대상 볼륨의 StorageClass와 Backend 종류
- 접근할 VM이 실제로 DKS 관리 범위 밖인지
- 별도 승인형 ACL 확장 또는 전용 공유 서비스가 있는지
- 읽기 전용·복제본 접근이 지원되는지

## 근거 사슬

1. 2026-04-09 사례에서 운영팀은 DKS PVC의 VM 직접 공유가 불가능하다고 답했다.
2. 2026-04-28 사례는 NetApp NAS가 ACL·보안 정책상 DKS 관리 Worker VM에서만 마운트 가능하다고 구체화했다.
3. 2026-05-19 사례도 DKS PVC 볼륨은 DKS 관리 노드에만 ACL이 허용되어 외부 일반 VM 마운트가 불가능하다고 재확인했다.
4. 따라서 적용 조건 안에서 DKS PVC의 외부 VM 직접 마운트 불가 Claim이 반복 근거로 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026040908233608510 | full-dialogue | DKS PVC의 VM 직접 공유는 불가하다. | `VOC/2026-04-05 ~ 2026-04-11 DKS VOC 목록 (12건).md` 129-139행 |
| direct-support | 2026042810465626401 | full-dialogue | DKS NetApp NAS는 DKS 관리 Worker VM에서만 마운트 가능하다. | `VOC/2026-04-26 ~ 2026-05-02 DKS VOC 목록 (9건).md` 159-164행 |
| direct-support | 2026051910115652478 | full-dialogue | DKS PVC는 DKS 관리 노드에만 ACL이 허용되어 외부 일반 VM 마운트가 불가하다. | `VOC/2026-05-17 ~ 2026-05-23 DKS VOC 목록 (8건).md` 157-161행 |

## 이 Claim이 말하지 않는 것

- Pod와 VM 사이의 모든 파일 교환이 불가능하다는 뜻이 아니다.
- VM이 제공하는 NFS를 Pod가 마운트할 수 없다는 뜻이 아니다.
- DKS-C 전용 Storage나 별도 Storage Service에도 동일한 ACL이 적용된다는 뜻이 아니다.
- 백업·복제·Object Storage를 이용할 수 없다는 뜻이 아니다.

## 반례·경쟁 설명

- DKS 관리 범위에 포함된 전용 VM 또는 승인된 Storage Client는 별도 정책을 적용받을 수 있다.
- Storage Backend·Service Model이 변경되면 ACL 경계도 달라질 수 있다.

## 무효화 조건

- 최신 공식 정책에서 사용자 VM의 DKS PVC 직접 Mount 또는 승인형 ACL 등록을 지원한다고 확인되면 수정한다.

## 다음 검증

- 현재 DKS-N·DKS-C StorageClass별 Client ACL과 외부 공유 지원 여부를 확인한다.

## 하위 문서 사용 조건

- 직접 Mount 가능성 판단에는 사용할 수 있다.
- 대체 파일 공유 방식은 [[CCL-STO-002 - 외부 VM과의 파일 공유는 별도 NFS 또는 동기화 경로를 사용한다]]와 보안·성능 요구를 함께 검토한다.
