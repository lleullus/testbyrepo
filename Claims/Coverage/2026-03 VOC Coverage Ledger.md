---
type: voc-coverage-ledger
period: 2026-03
status: first-pass-complete
voc_count: 36
review_basis: summary-plus-selected-full-dialogue
last_reviewed: 2026-09-25
---

# 2026-03 VOC Coverage Ledger

> 3월 등록 VOC 36건의 1차 처분이다. `2026-03-29 ~ 2026-04-04` 파일 중 3월 30·31일 2건도 포함한다.

| VOC | 날짜 | 도메인 | 처분 | 관련 Claim / 후보군 | 검토 | 핵심 내용 |
|---|---|---|---|---|---|---|
| 2026030612551576849 | 03-06 | NET | supports-claim | CCL-NET-002 | full | 대표 도메인 `nslookup` 기반 DNS VIP 확인 |
| 2026030314251049562 | 03-03 | RES | candidate-source | unplanned-minimum-resource | summary | 계획 외 최소 자원 후 실사용 기반 증설 |
| 2026030314180949387 | 03-03 | DEP | candidate-source | jvm-container-memory-sizing | summary | JVM 기본 Heap 비율과 MaxRAMPercentage·Replica 조정 |
| 2026031310191224424 | 03-13 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | FTP 아웃바운드 Source 대역 안내 |
| 2026031307400622363 | 03-13 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | 외부 DB 접근용 Source IP 대역 안내 |
| 2026031213192417165 | 03-12 | PLT | candidate-source | platform-os-kubernetes-version | summary | RHEL 8.6·Kubernetes 1.26 표준 정책 |
| 2026031118270611712 | 03-11 | DEP | candidate-source | ingress-backend-readiness | summary | Bad Gateway의 실제 원인이 Liveness Probe 실패 |
| 2026031118241311694 | 03-11 | DEP | candidate-source | ingress-backend-response-boundary | summary | Ingress 이후 Backend Pod가 404·Redirect 응답 |
| 2026031112004206492 | 03-11 | CON | case-only | web-console-permission-bug | summary | 웹콘솔 권한 버그와 임시 UI 대체 |
| 2026031109544604758 | 03-11 | NET | candidate-source | ingress-rate-limit | summary | Nginx Annotation Rate Limit 구성 |
| 2026031017454401399 | 03-10 | NET | out-of-scope | duplicate-voc | summary | 상세 누락으로 재등록된 VOC |
| 2026031009431094950 | 03-10 | DEP | candidate-source | container-data-user-responsibility | summary | 컨테이너 Dump는 사용자 관리 영역, 외부 업로드 안내 |
| 2026030917570492036 | 03-09 | PLT | candidate-source | platform-migration-difference | summary | PaaS와 DKS Kubernetes 환경 차이·전환 가이드 |
| 2026030909451185227 | 03-09 | CON | candidate-source | onecloud-project-membership; legacy-outbound-node-subnet | summary | Project 멤버 기반 Namespace 권한과 아웃바운드 안내 |
| 2026032015455775887 | 03-20 | NET | candidate-source | tcp-nodeport-limit | summary | Worker Node NodePort 외부 접근과 방화벽 |
| 2026032015044075665 | 03-20 | IMG | supports-claim | CCL-IMG-001, CCL-IMG-002 | summary | 403 인증 만료와 ImagePullSecret 갱신 |
| 2026032014335075503 | 03-20 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | Knox API Source에 Worker Node 대역 안내 |
| 2026032013191774953 | 03-20 | IMG | candidate-source | harbor-insecure-registry | summary | Harbor Push 인증 오류와 insecure-registries 설정 |
| 2026031916294570686 | 03-19 | CON | case-only | resource-change-ui-incident | summary | 자원 변경신청 중단 현상 개별 확인 |
| 2026031814565059775 | 03-18 | NET | candidate-source | ingress-port-boundary | summary | 11443 인입을 443으로 Redirect하는 구성 미지원 |
| 2026031811314757475 | 03-18 | NET | supports-claim | CCL-NET-002 | summary | 해외법인 인바운드 Cluster VIP·URL Filtering |
| 2026031713412948754 | 03-17 | RES | candidate-source | low-utilization-reclaim-criteria | summary | 일 평균·기간 최고치 기반 저활용 판정 |
| 2026031706472243959 | 03-17 | CON | case-only | resource-change-pvc-deletion-incident | summary | PVC 삭제 미반영으로 변경신청 중단·재신청 |
| 2026031618060242650 | 03-16 | NET | supports-claim | CCL-NET-001, CCL-NET-002 | summary | 콘솔 내부 IP가 아닌 조회된 Cluster VIP로 DNS 등록 |
| 2026031615022639988 | 03-16 | STO | candidate-source | storage-decrease-not-supported; storage-change-request | summary | StorageClass 감설 불가와 근거 첨부 증설 |
| 2026031609361135305 | 03-16 | CON | supports-claim | CCL-CON-001, CCL-CON-002 | summary | Namespace 이름 변경 불가, 삭제·신규 생성 |
| 2026032716324325872 | 03-27 | STO | candidate-source | shared-nas-qos-bottleneck | summary | NAS QoS 상향 상태와 Pod I/O 조정 검토 |
| 2026032615112215546 | 03-26 | DEP | candidate-source | pod-kernel-node-dependency | summary | Pod 커널은 Worker Node에 종속, nodeName 고정 위험 |
| 2026032610455211989 | 03-26 | CON | case-only | project-default-data-bug | summary | 기본 Cluster·Namespace 정보 누락 DB 조치 |
| 2026032415282595862 | 03-24 | PLT | out-of-scope | server-access-request | summary | Hiware 서버 접근 신청 이관 |
| 2026032413593794648 | 03-24 | AUTH | candidate-source | namespace-admin-role | summary | 운영 Namespace Admin 권한 부여 |
| 2026032409352691074 | 03-24 | RES | candidate-source | demand-dashboard-semantics | summary | 연간 수요 잔여량·전체량 표기 규칙 |
| 2026032311350183044 | 03-23 | PLT | supports-claim | CCL-PLT-001, CCL-PLT-002 | summary | 공용 클러스터 Operator 미제공, Namespace Scope 권장 |
| 2026032308151579788 | 03-23 | AUTH | candidate-source | secret-bulk-registration | summary | DKSctl·YAML Secret 일괄 등록과 EndpointSlice 지원 |
| 2026033113293844007 | 03-31 | AUTH | candidate-source | project-and-namespace-membership | summary | Project 권한 외 Namespace 멤버 권한 필요 |
| 2026033017280338061 | 03-30 | RES | candidate-source | demand-dashboard-semantics | summary | 수요조사 자원·최소자원과 Dashboard 0 의미 |

## 1차 집계

| 처분 | 건수 |
|---|---:|
| supports-claim | 6 |
| bounds-claim | 3 |
| candidate-source | 21 |
| case-only | 4 |
| out-of-scope | 2 |
| **합계** | **36** |

## 우선 비교 후보군

- `ingress-backend-*`: Ingress 자체 장애와 Backend 애플리케이션·Probe 실패를 분리하는 Guard Claim 후보다.
- `low-utilization-reclaim-criteria`, `resource-usage-evidence-for-reduction`: 저활용 판단 기준과 자료 제공을 구분한다.
- `namespace-rename-not-supported`, `namespace-project-transfer-unsupported`: Kubernetes 객체 불변성과 DKS 신청 프로세스를 구분해 검토한다.
- `cluster-scoped-crd-prohibited`, `cluster-scoped-operator-unavailable`: 공용 클러스터 Scope 경계 후보군이다.
