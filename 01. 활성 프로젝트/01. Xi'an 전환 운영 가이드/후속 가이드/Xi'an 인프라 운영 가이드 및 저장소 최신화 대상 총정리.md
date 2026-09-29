---
title: "Xi'an 인프라 운영 가이드 및 저장소 최신화 대상 총정리"
date: 2026-09-08
tags:
  - xian
  - kubernetes
  - kubesphere
  - harbor
  - modernization
  - blog
parent: "[[후속 가이드/04. 기존 운영 가이드 국문 번역 및 저장소 최신화 가이드|기존 운영 가이드 국문 번역 및 저장소 최신화 가이드]]"
---

# Xi'an 인프라 운영 가이드 및 저장소 최신화 대상 총정리

해외 사업장(Xi'an) 클러스터 구축 및 운영 전환 과정에서 과거 임시 경로, 레거시 테스트 저장소, 타 사이트(Taylor) 기준 설정값들이 혼재되어 있던 문제를 해결하기 위해 정리된 **'운영 정보 및 저장소 최신화(현행화)' 핵심 대상과 세부 변경 사항**을 정리한 글입니다.

---

## 1. 최신화가 왜 필요했는가?

초기 인프라 구축 단계에서는 프로비저닝 속도를 위해 임시 Nexus 저장소나 범용 테스트 네임스페이스를 사용하는 경우가 많습니다. 또한 기존에 구축되었던 타 사업장(Taylor 등)의 매뉴얼과 영문·중문 문서 초안을 기반으로 작업하다 보니 현장에서 다음과 같은 문제가 발생했습니다.

1. **임시 저장소 폐기 리스크**: 구축 초기에 쓰이던 사내 Nexus 도메인이 폐기되어 신규 노드 증설 시 패키지 다운로드 실패 발생.
2. **레지스트리 네임스페이스 혼선**: 운영 컨테이너 이미지와 테스트 네임스페이스(`dspaas-testrepo`) 혼재.
3. **타 사이트 레퍼런스 잔존**: 과거 문서에 타 사이트 전용 도메인, IP, StorageClass 예시가 그대로 남아 있어 현장 운영자 혼란 유발.

이를 해소하고 **현지 운영자가 즉시 신뢰하고 실행할 수 있는 표준 국문 가이드와 최신 환경값**으로 전면 최신화를 단행했습니다.

---

## 2. 핵심 최신화 대상 및 변경 전·후 비교

최신화 작업은 크게 **① 인프라/저장소 엔드포인트**, **② 배포 디렉터리 및 인벤토리**, **③ 운영 매뉴얼 및 환경 파라미터**의 3대 영역으로 구분됩니다.

### 📌 변경 전(과거) vs 변경 후(최신 표준) 매핑

| 분류 | 과거 임시 / 레거시 표기 | 최신화(현행화) 표준값 | 최신화 목적 및 조치 내용 |
| :--- | :--- | :--- | :--- |
| **사내 YUM 저장소** | `nexus.adpaas.cloud.samsungds.net` (임시 Nexus) | `http://repo.dks.samsungds.net/repository/...` (Xi'an 전용 사내 미러) | 폐기된 임시 Nexus 제거, `dks-base`, `dks-docker`, `dks-kubernetes` 패키지 다운로드 안정화 |
| **Harbor 네임스페이스** | `dspaas-testrepo`, `dks-test`, `harbor.adpaas.cloud` | `xa.dcr.dks.samsungds.net/dspaas-v1.22.10-a/...`<br>`xa.dcr.dks.samsungds.net/kubesphere/...` | 공식 운영 레지스트리 FQDN 및 버전별 표준 프로젝트로 통합 |
| **기본 테스트 이미지** | `.../dspaas-testrepo/nginx:latest` | `xa.dcr.dks.samsungds.net/dspaas-v1.22.10-a/nginx:1.14.2` | 태그 불명확(`latest`) 제거 및 검증된 고정 버전 명시 |
| **배포 패키지 디렉터리** | `/app/dspaas/paas-admin-k8s-v1.22.10-a` | `/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0` | Bastion 내 공식 표준 배포 패키지 구조로 디렉터리 단일화 |
| **Kubespray 인벤토리** | 이전 클러스터 인벤토리 | `20.kubespray-release-2.19/inventory/dks/` (`hosts.yaml`, `dks_vars.yml`) | 신규 Worker 노드 증설 및 유지보수용 공식 인벤토리 확정 |
| **오프라인 바이너리 경로** | 외부 인터넷 또는 임시 다운로드 링크 | `http://repo.dks.samsungds.net/repository/files/...` | 폐쇄망 환경에서 `docker-compose`, Harbor 설치 파일 등 200 OK 다운로드 보장 |
| **운영 매뉴얼 기준값** | Taylor 사이트 도메인/IP/클러스터명 | Xi'an Host Dashboard, PRD/DEV Ingress, 실제 VIP/CA 경로 | 현장 운영자가 화면과 스크립트 대조 시 불일치 제거, 전면 국문화 |

---

## 3. 부문별 상세 최신화 내용

### (1) 사내 YUM 저장소(Artifactory) 설정 최신화
Bastion(`xadksbtmp01`)과 Master/Worker 노드의 `/etc/yum.repos.d/` 내 설정 파일들을 공식 사내 미러 저장소로 교체했습니다.

- **적용 대상 파일**:
  - `/etc/yum.repos.d/dks-base.repo` (Base YUM Repo)
  - `/etc/yum.repos.d/dks-docker.repo` (Docker CE Repo)
  - `/etc/yum.repos.d/dks-kubernetes.repo` (Kubernetes Repo)
- **설정 내용**:
  ```ini
  [dks-base]
  name=DKS Base Repository
  baseurl=http://repo.dks.samsungds.net/repository/centos-7-base/
  enabled=1
  gpgcheck=0
  ```
- **검증**: `sudo yum clean all && sudo yum repolist` 수행 시 총 11,000여 개 이상의 정상 패키지 인덱싱 확인.

---

### (2) Harbor 이미지 레지스트리 경로 현행화
검증되지 않은 외부 레지스트리 직접 참조나 테스트 네임스페이스를 완전히 배제하고, 공식 Harbor 경로로 전환했습니다.

- **Calico CNI 이미지**: `calico/cni:v3.21.4` → `xa.dcr.dks.samsungds.net/calico/cni:v3.21.4`
- **KubeSphere 인스톨러 이미지**: `harbor.adpaas.cloud/...` → `xa.dcr.dks.samsungds.net/kubesphere/ks-installer:v3.3.0`
- **표준 테스트 컨테이너**: `xa.dcr.dks.samsungds.net/dspaas-v1.22.10-a/nginx:1.14.2`

---

### (3) Bastion 배포 패키지 및 Kubespray 인벤토리 현행화
Bastion 호스트의 표준 작업 디렉터리를 확정하여 형상 관리를 일원화했습니다.

- **공식 표준 경로**: `/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0`
  - `20.kubespray-release-2.19`: Kubespray 및 배포 플레이북
  - `30.storage-netapp`: NetApp Trident 스토리지 프로비저닝
  - `40.monitoring`: Prometheus / Grafana 모니터링 스택
  - `50.kubesphere`: KubeSphere Member 설치 스크립트
  - `SECDS-T2IssuingCA.crt` / `SECDS-T2ROOTCA.crt`: 사내 공통 CA 인증서
- **공식 인벤토리 위치**: `20.kubespray-release-2.19/inventory/dks/hosts.yaml`

---

### (4) 폐쇄망 오프라인 바이너리 캐시 검증
외부 인터넷 연결이 불가능한 폐쇄망 특성상 필요한 바이너리를 내부 파일 저장소에서 HTTP curl로 직접 호출할 수 있도록 최신화했습니다.

```bash
# Docker Compose 바이너리 응답 확인
curl -sk -o /dev/null -w "%{http_code}\n" http://repo.dks.samsungds.net/repository/files/docker-compose
# 출력: 200

# Harbor 오프라인 설치본 응답 확인
curl -sk -o /dev/null -w "%{http_code}\n" http://repo.dks.samsungds.net/repository/files/harbor-offline-installer-v2.2.2.tgz
# 출력: 200
```

---

### (5) Worker 노드 증설 절차 최신화
Ansible Playbook을 활용해 신규 노드(`xadkswkmp03` 등) 추가 시 최신 저장소 설정 파일을 자동 배포하고, 즉시 패키지를 내려받아 노드를 확장할 수 있도록 실습 검증 절차를 현행화했습니다.

---

## 4. 함께 반영된 현장 추가 요청 사항 (8대 후속 가이드)

단순 저장소 교체 외에도 현장 구축 및 운영 전환 시 발생하는 특수 이슈를 해결하기 위해 8대 추가 가이드가 작성·반영되었습니다.

1. **인증서 갱신 시 사용자 kubeconfig 처리**:
   - Kubernetes CA가 유지되고 사용자 Client Certificate가 유효하면 사용자용 kubeconfig는 재발급하지 않아도 됨을 명확히 규정.
2. **본사 T2 CA 만료기간 확인**:
   - Bastion 내 CA 번들 및 Harbor FQDN(`xa.dcr.dks.samsungds.net:443`) 인증서 만료일/체인 점검 스크립트 제공.
3. **NetApp iSCSI Block Storage 추가 검토**:
   - SVM, LIF, igroup, Node Multipath/iscsid 패키지 점검 및 Trident `ontap-san` 드라이버 도입 가이드.
4. **Native API Ingress Source CIDR 통제 검토**:
   - PRD Native API와 일반 Ingress의 VIP-B(:443) 공유 구조 및 ssl-passthrough 환경에서의 L4 CIDR 통제 한계점/대응방안 검토.
5. **Kubernetes Dashboard Skip 로그인 활성화·비활성화**:
   - `--enable-skip-login`, `--disable-settings-authorizer` 인자 설정 및 보안 롤백 절차.
6. **KubeSphere·Harbor LDAP 보안그룹 추가·제거**:
   - KubeSphere `userSearchFilter`의 LDAP 보안그룹 OR 조건(`SG1599`, `SG1600` 등) 확장 및 Harbor Project 멤버 매핑.
7. **Harbor 서버 인증서 갱신 및 CA 변경 대응 계획**:
   - 단순 서버 인증서 갱신(클라이언트 무중단) vs Root CA 변경(Worker/API 서버 Trust 배포 필요)의 작업 분리.
8. **Harbor VM 스토리지 증설 및 반영 확인**:
   - VM 디스크 용량 증설 후 `/harbordata` (XFS/LVM) 파일시스템 확장 확인 및 무중단 적용 기준 수립.

---

## 5. 결론 및 기대 효과

이번 최신화 작업을 통해 **"문서에 기재된 명령어를 그대로 실행했을 때 오류 없이 즉시 동작하는 환경"**을 확보했습니다.

* **인프라 안정성**: 폐기된 레거시 Nexus URL 참조로 인한 노드 배포 실패 리스크 원천 차단.
* **운영 명확성**: 영문/중문 혼재 및 타 사이트(Taylor) 예시 혼선을 제거하고 국문 표준 절차서 확립.
* **유지보수 표준화**: Bastion 내 단일 표준 스택 디렉터리를 중심으로 형상 관리 일원화.
