---
title: "KubeSphere SECDS T2 CA 번들 ConfigMap Mount"
created: "2026-06-19"
tags:
  - kubesphere
  - configmap
  - certificate
  - ca
  - harbor
  - x509
  - t2
parent: "[[50. 운영/01. Operations Overview/운영 안내|운영 안내]]"
doc_type: guide
status: draft
scope: "Xi'an 전환 운영 가이드"
updated: "2026-09-08"
---

> [!summary] 요약
> Harbor 이미지 레지스트리 Secret 생성 시 'x509: certificate signed by unknown authority' 오류가 발생하면, 각 Member Cluster에 SECDS T2 CA 번들(SECDS-T2IssuingCA + SECDS-T2ROOTCA)을 ConfigMap으로 등록하고 ks-apiserver에 마운트해야 한다.

---

## 1. 문제 현상

CA cert 미적용 시 Harbor 이미지 레지스트리 Secret 생성 또는 KubeSphere에서 Harbor 이미지 조회 시 다음 오류 발생:

> 'x509: certificate signed by unknown authority'

참고: 인증/권한 문제인 'unauthorized'와 구분해야 하며, 이 오류는 서버 인증서의 CA 신뢰 체인이 완성되지 않았음을 의미한다.

---

## 2. 해결 절차

### 절차

1. **ConfigMap 생성 (T2 CA 번들 등록)**

   KubeSphere 메뉴 > **Platform** > **Cluster Management** > 각 **Member Cluster** (Host 클러스터는 제외)

   **Configuration** > **Configmaps** > **Create**

   - **Name**: secds-t2-ca (기존 secds-rootca는 유지하고 신규 생성)
   - **Project**: kubesphere-system

   **Next** > **Add Data** > **Key & Value** 삽입

   - **Key**: ca.crt
   - **Value**: SECDS-T2IssuingCA.crt 및 SECDS-T2ROOTCA.crt 합본 내용 붙여넣기 (중간 CA가 위, 루트 CA가 아래)

   **Create** 클릭

2. **ks-apiserver에 ConfigMap 마운트**

   KubeSphere 메뉴 > **Platform** > **Cluster Management** > 각 **Member Cluster**

   **Application Workloads** > **Workloads** > ks-apiserver

   **More** > **Edit Settings**

   **Volumes** > **Mount Configmap or Secret**

   ConfigMap 선택 (secds-t2-ca) → **OK**

   ks-apiserver 자동 재시작으로 CA cert 적용 (Pod Ready 상태 확인 후 Harbor Secret 생성 및 이미지 연동 재검증)

---

## 관련 노트

- [[50. 운영/04. Kubesphere Operation/06. Enable users using kubectl CLI|Enable users using kubectl CLI]]
- [[50. 운영/07. DKS User Guide/02. Harbor User Guide|Harbor User Guide]]
- [[35. 작업 관리/2026-08-19 DEV PRD Member ks-apiserver SECDS T2 CA Bundle 적용 작업계획서|DEV PRD Member ks-apiserver SECDS T2 CA Bundle 적용 작업계획서]]
