---
title: "Harbor VM 스토리지 증설 및 반영 확인 가이드"
created: 2026-08-29
status: draft
tags:
  - harbor
  - storage
  - vm
scope: "Xi'an 전환 운영 가이드"
---

# Harbor VM 스토리지 증설 및 반영 확인 가이드

## 1. 현재 구성

| 항목 | 값 |
|---|---:|
| Block Disk | 165GB |
| / | 115GB |
| /harbordata | 50GB |
| Harbor 데이터 경로 | /harbordata |

## 2. 확인 기준

- /harbordata Filesystem이 실제로 확장되고 Mount 경로가 그대로 유지되면 Harbor 재시작은 필요하지 않다.
- VM Disk 용량만 증설했다고 해서 /harbordata Filesystem까지 자동으로 확장됐다고 판단하지 않는다.

## 3. 증설 후 확인

```bash
lsblk -f
findmnt /harbordata
df -hT /harbordata
pvs
vgs
lvs
```

## 4. 판정

| 확인 결과 | 판정 |
|---|---|
| df -hT /harbordata에서 증설된 용량 확인 | Harbor 재시작 없이 그대로 사용 |
| Disk 크기는 증가했지만 /harbordata 크기는 그대로 | OS의 Disk/Partition/LVM/Filesystem 구성을 확인한 뒤 필요한 확장 작업 수행 |
| /harbordata가 LVM이 아닌 것으로 확인됨 | LVM 확장 절차를 적용하지 않음 |
| Filesystem 종류가 XFS가 아닌 것으로 확인됨 | xfs_growfs를 적용하지 않음 |

## 5. 작업 시 제외

- /harbordata가 LVM이라고 가정하지 않는다.
- growpart, pvresize, lvextend, xfs_growfs를 고정 절차로 사용하지 않는다.
- "VM Disk 증설 시 /harbordata가 항상 자동 확장된다"고 기록하지 않는다.
- /harbordata Filesystem 확장 완료 후 Harbor 재시작 절차를 넣지 않는다.

## 근거

| 사실 주장 | 근거 |
|---|---|
| xadksharbor01은 Block Disk 165GB, / 115GB, /harbordata 50GB로 기록돼 있다. | 10. 기준 및 설계/클러스터 카탈로그/02. prd-harbor-xas.md L24–30 |
| Harbor data_volume은 /harbordata로 설정돼 있다. | 50. 운영/06. Harbor Manual/01. Harbor Installation.md L103–112 |
| 현재 Workspace에는 xadksharbor01의 Partition/LVM/Filesystem 자동 확장 절차 또는 증설 전후 실행 증적이 없다. | Workspace 검색 결과 |
