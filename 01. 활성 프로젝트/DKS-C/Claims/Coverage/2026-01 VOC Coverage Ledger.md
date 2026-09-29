---
type: voc-coverage-ledger
period: 2026-01
status: first-pass-complete
voc_count: 58
review_basis: summary-plus-selected-full-dialogue
last_reviewed: 2026-09-25
---

# 2026-01 VOC Coverage Ledger

> 이 Ledger는 모든 1월 VOC의 1차 처분을 기록한다. `summary` 행은 요약 목록 기준 분류이며 Claim 승격 전에 원문 공식 답변 확인이 필요하다.

| VOC | 날짜 | 도메인 | 처분 | 관련 Claim / 후보군 | 검토 | 핵심 내용 |
|---|---|---|---|---|---|---|
| 2026010916101249367 | 01-09 | PLT | out-of-scope | service-inventory-contact | summary | DKS 사용 시스템 담당자 연결 요청 |
| 2026010914555348401 | 01-09 | AUTH | candidate-source | managed-serviceaccount-protection | full | 관리 SA 삭제로 credentials 오류 발생 |
| 2026010913485647506 | 01-09 | STO | candidate-source | storage-attach-delay | summary | Trident NAS 상태로 Job·Pod 지연 |
| 2026010911155846127 | 01-09 | RES | candidate-source | demand-allocation-approval | summary | 수요 반영과 가용자원 초과 결재 |
| 2026010911103946029 | 01-09 | DEP | case-only | rollingupdate-failure-event | summary | P-DEP 배포 실패와 Pod Event 확인 |
| 2026010910513745690 | 01-09 | NET | supports-claim | CCL-NET-002 | summary | 방화벽 신청용 Cluster VIP 안내 |
| 2026010816305640901 | 01-08 | RES | candidate-source | low-utilization-reclaim | summary | 저활용 자원 회수로 P-DEP 자원 미노출 |
| 2026010813561138614 | 01-08 | PLT | candidate-source | linux-node-only | summary | Windows Node 미지원, Linux Node Pool 지원 |
| 2026010812130237380 | 01-08 | OBS | candidate-source | user-prometheus-boundary | summary | 사용자 모니터링용 Prometheus·CRD 안내 |
| 2026010717065431667 | 01-07 | NET | candidate-source | shared-ingress-capacity | summary | LB·Ingress 공유 구조와 대역폭 설명 |
| 2026010709123624893 | 01-07 | NET | candidate-source | client-ip-preservation-limit | summary | LB SNAT·TLS Termination으로 Client IP 제약 |
| 2026010606534413494 | 01-06 | STO | case-only | failed-volume-publish-node | summary | PV 미게시 상태와 노드 재부팅 조치 |
| 2026010513415208585 | 01-05 | CON | candidate-source | demand-resource-reassignment | summary | 수요 자원을 기존 Namespace에 할당하는 절차 |
| 2026010511310007305 | 01-05 | RES | candidate-source | unplanned-minimum-resource | summary | 수요조사 미참여 시 최소 자원 신청 |
| 2026010510485106580 | 01-05 | PLT | candidate-source | service-model-difference | summary | 클러스터형과 Namespace형 접근 차이 |
| 2026010508063503895 | 01-05 | IMG | supports-claim | CCL-IMG-002 | summary | AD 비밀번호 만료 후 Pull Secret 재생성 |
| 2026011717453599328 | 01-17 | PLT | supports-claim | CCL-PLT-001, CCL-PLT-002 | summary | Namespace Scope 정책으로 Cluster CRD 등록 불가 |
| 2026011611070993107 | 01-16 | AUTH | candidate-source | ingress-certificate-algorithm-limit | summary | rsassaPss 인증서의 Ingress 미지원·예외 |
| 2026011610005492048 | 01-16 | NET | supports-claim | CCL-NET-001, CCL-NET-002 | full | 내부 Ingress IP와 외부 Cluster LB VIP 구분 |
| 2026011609404091710 | 01-16 | CON | candidate-source | namespace-quota-change-request | summary | 콘솔 변경신청으로 CPU·Memory 할당 변경 |
| 2026011514522786752 | 01-15 | CON | out-of-scope | console-improvement-request | summary | 콘솔 세션·자동 로그인 개선 요청 |
| 2026011510483584284 | 01-15 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | full | 서비스 모델 미확인 환경의 Worker Node Source 안내 |
| 2026011509574983551 | 01-15 | NET | case-only | dns-nameserver-misconfiguration | summary | NetworkPolicy 문의였으나 실제 원인은 DNS 설정 |
| 2026011418102280855 | 01-14 | AUTH | candidate-source | ingress-tls-secret-update | summary | TLS Secret과 Ingress tls.hosts 매핑 |
| 2026011413285077108 | 01-14 | OBS | candidate-source | user-prometheus-boundary | summary | 기본 메트릭 범위와 P-DEP 연계 |
| 2026011408400273401 | 01-14 | DEP | candidate-source | pod-terminal-access | summary | 콘솔 터미널과 kubectl exec 사용 |
| 2026011321063572188 | 01-13 | NET | supports-claim | CCL-NET-002 | summary | Cluster VIP 기반 DNS 등록·IAM 신청 |
| 2026011315580469873 | 01-13 | AUTH | candidate-source | ingress-tls-secret-configuration | summary | TLS Secret 생성과 Ingress TLS 적용 |
| 2026011309562065024 | 01-13 | IMG | candidate-source | harbor-bundle-quota-limit | summary | Harbor 번들 저장공간 증설 제한 |
| 2026011217581062134 | 01-12 | IMG | candidate-source | harbor-repository-auto-create | summary | Image Push 시 repository 자동 생성 |
| 2026011217432161976 | 01-12 | NET | candidate-source | tcp-nodeport-limit | summary | RabbitMQ NodePort, HA 미보장·포트 충돌 주의 |
| 2026011216255560900 | 01-12 | STO | candidate-source | storageclass-availability-by-cluster | summary | 클러스터별 가용 StorageClass 확인 |
| 2026011213472358287 | 01-12 | DEP | candidate-source | hpa-metric-support-boundary | summary | CPU·Memory HPA 지원, Custom Metric 미지원 |
| 2026012311122738890 | 01-23 | PLT | supports-claim | CCL-PLT-001, CCL-PLT-002 | summary | 공용 클러스터에서 Cluster CRD 등록 불가 |
| 2026012216201735215 | 01-22 | STO | case-only | netapp-load-qos-incident | summary | NetApp CPU 부하와 QoS 조치로 PVC 지연 복구 |
| 2026012215325634545 | 01-22 | STO | case-only | failed-attach-volume-incident | summary | 스토리지 부하로 다수 Pod Pending |
| 2026012209151929769 | 01-22 | AUTH | case-only | ad-cluster-login-incident | summary | AD 로그인 후 클러스터 인증 오류 조치 |
| 2026012115103825084 | 01-21 | CON | case-only | onecloud-aa-mapping-incident | summary | Namespace 신청 AA 정보 수동 Push |
| 2026012013095714286 | 01-20 | NET | supports-claim | CCL-NET-002 | summary | 외부 서버 인바운드 Cluster VIP·URL Filtering |
| 2026012013023114191 | 01-20 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | 외부 DB 연결 시 Worker Node 대역을 Source로 안내 |
| 2026012009215611314 | 01-20 | NET | supports-claim | CCL-NET-002 | summary | 외부 DNS에서 Ingress 접근 시 Cluster VIP 매핑 |
| 2026011918023708884 | 01-19 | NET | candidate-source | client-ip-preservation-limit | summary | L4 LB SNAT로 Client IP 수집 제약, XFF 미지원 |
| 2026011915464907158 | 01-19 | DEP | candidate-source | hpa-existing-deployment | summary | 기존 Deployment에 HPA 생성·적용 |
| 2026011914543806415 | 01-19 | CON | candidate-source | demand-resource-reassignment | summary | 수요 할당 자원의 Namespace 분할·변경 신청 |
| 2026011913275505190 | 01-19 | AUTH | case-only | tls-secret-key-order-error | summary | tls.crt·tls.key 반대 작성 오류 수정 |
| 2026013019094789917 | 01-30 | RES | candidate-source | quota-change-capacity-approval | summary | 가용자원 초과 경고와 승인 절차 |
| 2026013017520489751 | 01-30 | DEP | candidate-source | ephemeral-storage-eviction | summary | 노드 임시디스크 고갈로 Pod 축출, emptyDir 주의 |
| 2026012920064282502 | 01-29 | DEP | candidate-source | workload-probe-edit | summary | 기존 Deployment Probe 수정 방법 |
| 2026012914434779096 | 01-29 | NET | supports-claim | CCL-NET-002 | summary | Cluster LB VIP 조회와 hosts 등록 |
| 2026012815144969461 | 01-28 | NET | supports-claim | CCL-NET-002 | summary | Cluster VIP 조회와 URL Filtering |
| 2026012813042467375 | 01-28 | PLT | candidate-source | outbound-internet-direct-access-limit | summary | 서버망에서 사외 GitHub 직접 접근 제한 |
| 2026012807213563086 | 01-28 | OBS | candidate-source | pdep-grafana-access | summary | 공용 Grafana 환경과 메트릭 링크 |
| 2026012711445556789 | 01-27 | NET | candidate-source | ingress-port-boundary | summary | LB VIP 80·443 구조에서 URL 기반 NodePort 접근 불가 |
| 2026012710402655651 | 01-27 | AUTH | candidate-source | workload-truststore-image | summary | Dockerfile keytool import로 Pod 신뢰 인증서 추가 |
| 2026012617375251357 | 01-26 | PLT | candidate-source | shared-namespace-stateful-l4-limit | summary | Kafka·MongoDB 등 Stateful L4 서비스 제약 |
| 2026012613064647652 | 01-26 | IMG | candidate-source | harbor-network-access | summary | 준사내 Harbor 웹콘솔 GSAMS 방화벽 필요 |
| 2026012612104247173 | 01-26 | DEP | supports-claim | CCL-DEP-001, CCL-DEP-002 | summary | P-DEP 치환으로 Ingress 설정 초기화, Custom CD 대안 |
| 2026012611473446983 | 01-26 | NET | supports-claim | CCL-NET-002 | summary | DNS 신청용 Cluster VIP 조회 |

## 1차 집계

| 처분 | 건수 |
|---|---:|
| supports-claim | 12 |
| bounds-claim | 2 |
| candidate-source | 34 |
| case-only | 8 |
| out-of-scope | 2 |
| **합계** | **58** |

## 다음 단계

- 반복 후보군은 2월 이후 자료와 합쳐 원문 상세 대화를 확인한다.
- `managed-serviceaccount-protection`, `cluster-scoped-crd-prohibited`, `hpa-metric-support-boundary`, `user-prometheus-boundary`, `ingress-tls-secret-*`, `harbor-*`, `demand-*` 후보군을 우선 비교한다.
