---
title: "NetApp iSCSI Block Storage 추가 검토 가이드"
created: 2026-08-30
status: draft
tags:
  - netapp
  - trident
  - iscsi
  - block-storage
scope: "Xi'an 전환 운영 가이드"
---

# NetApp iSCSI Block Storage 추가 검토 가이드

## 1. 대상 Cluster·Node 확인

NetApp iSCSI Block Storage를 추가할 대상 Cluster와 실제 Block PVC가 배치될 Node를 확인한다.

## 2. ONTAP iSCSI 정보 확인

Storage 담당자에게 다음 정보를 확인한다.

- SVM
- iSCSI Data LIF
- Aggregate
- igroup
- Management LIF
- CHAP 사용 여부
- QoS 및 용량 정책

## 3. Node iSCSI·Multipath 구성

Block PVC가 배치될 Node에 다음 구성 여부를 확인하고 필요한 경우 적용한다.

- iscsi-initiator-utils
- device-mapper-multipath
- lsscsi
- sg3_utils
- iscsid
- multipathd

## 4. Node IQN 및 TCP 3260 확인

각 대상 Node의 iSCSI Initiator IQN을 확인하고 ONTAP iSCSI Data LIF의 TCP 3260 연결 여부를 확인한다.

## 5. Trident ontap-san Backend 추가

기존 NetApp NFS Backend와 Trident 설치를 유지한 상태에서 iSCSI Block Storage용 ontap-san Backend를 추가한다.

기존 NFS Backend를 삭제하거나 Trident를 재설치하지 않는다.

## 6. iSCSI StorageClass 추가

csi.trident.netapp.io Provisioner를 사용하는 별도 iSCSI StorageClass를 생성한다.

기존 NetApp NFS StorageClass는 유지한다.

## 7. Block PVC 연결 검증

다음 순서로 확인한다.

```text
PVC
→ PV
→ LUN
→ VolumeAttachment
→ iSCSI Session
→ Multipath Device
→ Filesystem Mount
```

## 8. Pod 기능 검증

- Pod Mount 성공
- Container Write/Read 성공
- 준비된 다른 Node로 재배치 시 Detach/Attach 성공
- PVC 삭제 후 LUN 정리 확인

## 9. 기존 Storage 영향 확인

NetApp iSCSI 추가 전후 다음 기존 Storage 경로가 정상인지 확인한다.

- NetApp NFS PVC
- 기존 PowerFlex 구성요소가 존재하는 Cluster의 PowerFlex PVC 및 CSI 상태

## 완료 기준

- 대상 Node에서 ONTAP iSCSI Data LIF 접근이 가능하다.
- Trident ontap-san Backend가 online이다.
- iSCSI StorageClass로 생성한 PVC가 Bound된다.
- VolumeAttachment, iSCSI Session, Multipath Device가 정상이다.
- Pod에서 Mount 및 Write/Read가 성공한다.
- 기존 NetApp NFS 및 PowerFlex 경로에 영향이 없다.

## 현재 Xi'an 기준

- Kubernetes: 1.22.10
- OS: RHEL 8.10
- Runtime: containerd 1.6.4
- Trident 기준 패키지: 22.07.0
- 현재 NetApp 주 경로: ontap-nas-economy 기반 NFS
- 추가 Protocol: iSCSI
- 추가 Trident Driver: ontap-san
