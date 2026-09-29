---
title: "2026-08-30 주말 - Member KubeSphere 선행 학습 및 점검"
status: current
doc_type: study-note
scope: "8/31 신규 Member Monitoring·KubeSphere 설치를 위한 선행 학습 및 점검"
created: "2026-08-18"
updated: "2026-08-18"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|Xi'an DKS Member Cluster 구축 및 운영 기술 전수 계획(안)]]"
---

# 2026-08-30 주말 - Member KubeSphere 선행 학습 및 점검

> [!important] 주말 역할
> 정식 기술 전수일이 아니다. 8/31에 진행할 **`5.5.2 Install kubesphere - member cluster`**의 전체 순서와 신규 Member 고유값을 미리 점검하는 준비 노트다.

> [!success] Host 전제
> Host Cluster는 이미 구성 완료되어 있다. 8/31~9/1에는 **신규 Member를 구성하고 기존 Host에 Join**한다.

## 1. 다음 주 흐름

```text
8/31
Member context / StorageClass 확인
→ monitoring Namespace
→ ETCD certificate Secret
→ Grafana PVC
→ Prometheus Operator CRD
→ DKS custom Prometheus stack
→ Monitoring Ingress
→ External ETCD Monitoring
→ Grafana datasource / Dashboard
→ Member KubeSphere 설치·검증

9/1 오전
→ Member 최종 검증
→ 기존 Host Cluster Join
→ Host Console에서 Multi-Cluster 확인
```

## 2. 오늘 사용할 Manual

- [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5.5.2 Install kubesphere - member cluster]]

`5.5.1 Install kubesphere - host cluster`는 이번 출장 수행 범위에서 제외한다.

## 3. Member Monitoring이 먼저인 이유

Member는 DKS custom Monitoring을 먼저 구성한 뒤 KubeSphere를 설치하는 흐름을 따른다.

```text
Monitoring 선행 구성
→ Member의 ETCD·Workload 관측 기반 확보
→ Member KubeSphere
→ Member Role
→ 기존 Host Join
```

Host 설정이나 다른 Member의 설정을 그대로 복사하지 않는다.

## 4. 신규 Member에서 다시 확인할 값

- context / Cluster name
- StorageClass
- Monitoring Namespace
- External ETCD Endpoint
- ETCD certificate Secret key 이름
- Prometheus external labels
- Grafana datasource
- Monitoring Ingress Domain
- VIP-B / Router 관련 값
- Registry / Image
- nodeSelector / toleration
- `multicluster.clusterRole=member`
- 기존 Host Join endpoint·전달 절차

## 5. 복붙 방지 체크

- [ ] Host ETCD 값을 Member ETCD에 넣지 않는다.
- [ ] 다른 Member의 ETCD Endpoint를 복사하지 않는다.
- [ ] 다른 Cluster의 Domain/VIP를 사용하지 않는다.
- [ ] Grafana datasource가 현재 Member의 Monitoring Service를 가리킨다.
- [ ] external label이 현재 Member identity와 일치한다.
- [ ] StorageClass가 현재 Member 기준과 일치한다.
- [ ] Secret 내용은 출력·기록하지 않는다.

## 6. 8/31 진입조건

- [ ] 8/28 Storage가 실제 Mount·Read/Write까지 정상이다.
- [ ] Member context가 명확하다.
- [ ] Monitoring Namespace와 manifest/bundle을 준비했다.
- [ ] ETCD Endpoint와 인증서 전달 절차를 확인했다.
- [ ] Registry·StorageClass·Domain 등 환경 의존값을 확인했다.
- [ ] 기존 Host 접근과 Join 대상이 확인됐다.

## 관련 문서

- [[2026-08-29 주말 - 1주차 학습 정리 및 약점 보완]]
- [[2026-08-31 구축 실습 4일차 - 사전 학습 및 점검]]
- [[60. 이슈 및 결정/장애/dev-apps-pa01-xas Monitoring 복붙 오적용|Monitoring 복붙 오적용 사례]]
