---
type: voc-coverage-ledger
period: 2026-06
status: first-pass-complete
voc_count: 69
review_basis: summary-plus-selected-full-dialogue
last_reviewed: 2026-09-25
---

# 2026-06 VOC Coverage Ledger

> 6월 등록 VOC 69건의 1차 처분이다. DKS-N·기존 공용형과 DKS-C 전용형의 구조·접속·인증·네트워크 답변을 분리한다. `2026-06-28 ~ 2026-07-04` 파일의 6월 29·30일 7건도 포함한다.

| VOC | 날짜 | 도메인 | 처분 | 관련 Claim / 후보군 | 검토 | 핵심 내용 |
|---|---|---|---|---|---|---|
| 2026060513242242609 | 06-05 | AUTH | candidate-source | dksc-kubeconfig-access | summary | DKS-C Kubeconfig 생성과 CLI 접속 |
| 2026060509215539969 | 06-05 | RES | supports-claim | CCL-RES-001 | summary | Namespace Request:Limit 1:3과 증설 기준 |
| 2026060509004339615 | 06-05 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | FTP 아웃바운드 Source에 Node 대역 안내 |
| 2026060411254332894 | 06-04 | NET | supports-claim | CCL-NET-G001 | full | 인바운드 VIP와 아웃바운드 Node 대역의 방향별 분기 |
| 2026060410480932261 | 06-04 | AUTH | out-of-scope | enterprise-identity-change | summary | OAuth·SAML 인증 변경을 AD 운영팀으로 이관 |
| 2026060217395026968 | 06-02 | PLT | candidate-source | host-os-vs-container-image-os | summary | Node RHEL·Kernel과 Container Image OS 구분 |
| 2026060216190625973 | 06-02 | AUTH | candidate-source | managed-clusterrolebinding-boundary | summary | DKS-C System CRB 수정 불가, 사용자 CR 생성 |
| 2026060213333823953 | 06-02 | DEP | candidate-source | cpu-throttling-timeout | summary | CPU Limit 도달·Throttling으로 504 Timeout |
| 2026060107470611605 | 06-01 | AUTH | case-only | project-permission-reset-incident | summary | 기본 Cluster·Namespace 재설정으로 권한 복구 |
| 2026061214041088514 | 06-12 | PLT | candidate-source | gateway-node-failure-drill | summary | DKS-C Gateway Worker 장애 모의훈련 절차 |
| 2026061211100286820 | 06-12 | AUTH | candidate-source | dksc-console-access-and-sso | summary | 사내망·VDI URL과 SSO 접속 |
| 2026061209355785860 | 06-12 | IMG | candidate-source | harbor-robot-account-pull-secret | summary | DKS-C 개발계 Robot Account Secret과 Pull 권한 |
| 2026061114561081577 | 06-11 | NET | supports-claim | CCL-NET-G001 | summary | Ingress VIP·FQDN을 이용한 ALB/NLB 방화벽 신청 |
| 2026061114402681423 | 06-11 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | Pod 아웃바운드 Worker Node 대역 Source |
| 2026061113540680970 | 06-11 | AUTH | case-only | project-role-mapping-incident | summary | 신규 계정 Project Mapping·Role 복구 |
| 2026061110292879007 | 06-11 | AUTH | candidate-source | access-certificate-renewal | summary | DKS-C Browser·CLI 인증서 갱신 누락과 재발급 |
| 2026061109040878174 | 06-11 | AUTH | candidate-source | kubeconfig-context-setup | summary | Kubeconfig Download와 Context 설정 |
| 2026061017444374341 | 06-10 | DEP | case-only | crashloop-application-config-incident | summary | 환경변수·DB 연결 설정 오류로 CrashLoopBackOff |
| 2026061014164172551 | 06-10 | IMG | candidate-source | dksc-harbor-project-oidc | summary | Harbor Project 생성과 OIDC Login |
| 2026061013493472288 | 06-10 | NET | supports-claim | CCL-NET-002 | summary | Ingress Controller VIP와 Domain 조회 |
| 2026061009180769913 | 06-10 | CON | case-only | keycloak-session-cache-incident | summary | Keycloak Session·Browser Cache 초기화 |
| 2026060915354965177 | 06-09 | OBS | candidate-source | monitoring-dashboard-access | summary | VictoriaMetrics·Grafana URL과 권한 |
| 2026060914101264251 | 06-09 | NET | candidate-source | ingress-host-path-misconfiguration | summary | TLS Host·Path Prefix 오류 수정 |
| 2026060816223155708 | 06-08 | IMG | candidate-source | harbor-ad-group-membership | summary | AD Group 기반 Harbor Project Member 연동 |
| 2026060809152249821 | 06-08 | RES | supports-claim | CCL-RES-002 | summary | Quota 초과와 1:3 기준 증설 |
| 2026061815030129798 | 06-18 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | KMS 아웃바운드 Source에 Worker Node 대역 |
| 2026061715435221577 | 06-17 | CON | candidate-source | namespace-finalizer-deletion | summary | DKS-N Terminating Namespace Finalizer 정리 |
| 2026061715424021547 | 06-17 | IMG | candidate-source | harbor-sso-login-boundary | summary | Local Account와 Knox SSO Session 불일치 |
| 2026061711025218102 | 06-17 | DEP | candidate-source | scheduling-resource-contention | summary | C-DEP Scheduling 지연과 Node Resource 경합, 일부 대화 누락 |
| 2026061616450011234 | 06-16 | NET | supports-claim | CCL-NET-G001 | summary | 외부 DNS에는 Pod IP가 아닌 Ingress LB VIP 사용 |
| 2026061614210309995 | 06-16 | RES | supports-claim | CCL-RES-001 | summary | P-DEP Resource Request:Limit 1:3 반영 |
| 2026061610075207898 | 06-16 | IMG | candidate-source | image-pull-policy-and-tag | summary | Pod 미갱신 시 Always Policy와 Tag 갱신 확인 |
| 2026061609200507157 | 06-16 | PLT | candidate-source | dksn-to-dksc-migration-differences | summary | Gateway API·P-DEP Token·StorageClass 차이 |
| 2026061514125201281 | 06-15 | DEP | candidate-source | scheduling-insufficient-capacity | summary | Worker 가용자원 부족으로 Pod Pending |
| 2026061512515600159 | 06-15 | DEP | candidate-source | dksc-gitops-integration | summary | DKS-C ArgoCD·Flux와 Kubeconfig 연동 |
| 2026062623495782955 | 06-26 | PLT | candidate-source | paas-to-dksc-migration | summary | PaaS 종료에 따른 DKS-C Tenant 신청·이전 |
| 2026062619585582734 | 06-26 | AUTH | candidate-source | multicluster-deployment-token | summary | P-DEP Multi Cluster 배포 Token 등록 |
| 2026062615575881268 | 06-26 | AUTH | candidate-source | administrator-delegation | summary | 대표관리자 변경과 Console 권한 이관 |
| 2026062614334080181 | 06-26 | RES | supports-claim | CCL-RES-001, CCL-RES-002 | summary | CPU Request·Limit Quota 초과로 배포 실패 |
| 2026062612443678844 | 06-26 | OBS | candidate-source | monitoring-stack-deployment | summary | Prometheus·Grafana 기본 Stack과 Metric 수집 |
| 2026062609203976164 | 06-26 | CON | candidate-source | namespace-finalizer-deletion | summary | 잔류 CRD·Finalizer로 Terminating, 강제 정리 |
| 2026062609064275943 | 06-26 | AUTH | case-only | workspace-permission-mapping-incident | summary | Project·Workspace 권한 Mapping 오류 해결 |
| 2026062517291273716 | 06-25 | IMG | case-only | harbor-url-typo-incident | summary | Harbor Domain 오타와 정상 SSO URL 안내 |
| 2026062516184272719 | 06-25 | NET | candidate-source | dksc-vpc-subnet-isolation | summary | DKS-C Tenant별 VPC·Subnet 격리 구조 |
| 2026062516143872668 | 06-25 | PLT | candidate-source | dksc-package-installation | summary | DKS-C Cluster 생성과 Carvel·Helm Package 설치 |
| 2026062513500970612 | 06-25 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | 범용 Cluster DB Source에 Node 대역 안내 |
| 2026062512592269958 | 06-25 | PLT | candidate-source | dksc-environment-availability | summary | DKS-C 운영계 우선 제공과 개발·운영 Pool 계획 |
| 2026062512050169600 | 06-25 | PLT | candidate-source | pdep-cluster-baseline-information | summary | API Server·Cluster Domain·StorageClass 기준 정보 |
| 2026062512011769580 | 06-25 | IMG | candidate-source | cicd-registry-secret | summary | Harbor Secret과 P-DEP Build Manifest 연동 |
| 2026062417471365489 | 06-24 | NET | candidate-source | dksc-gateway-multidomain-routing | summary | Gateway·HTTPRoute 다중 Domain Mapping |
| 2026062413261561765 | 06-24 | STO | candidate-source | dksc-storageclass-selection | summary | DKS-C 전용 StorageClass와 PVC Manifest |
| 2026062316024554609 | 06-23 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | 외부 RabbitMQ Source에 Node 대역 등록 |
| 2026062313431452587 | 06-23 | AUTH | supports-claim | CCL-AUTH-003 | summary | 비실명계정의 최초 Console Session 후 권한 부여 |
| 2026062312395352000 | 06-23 | PLT | supports-claim | CCL-NET-006 | summary | Nginx Ingress와 Contour·Envoy Gateway API 차이 |
| 2026062218271247272 | 06-22 | NET | supports-claim | CCL-NET-G001 | summary | API Server·Ingress VIP·Egress Node 대역을 목적별 분리 |
| 2026062218112847141 | 06-22 | IMG | case-only | dksc-harbor-project-missing | summary | 사용자 Harbor Project 미생성 수동 조치 |
| 2026062217140146565 | 06-22 | AUTH | candidate-source | workload-truststore-ca-mount | summary | 다른 Project SSL 오류와 Pod Trust Store·CA Mount |
| 2026062217021046427 | 06-22 | NET | candidate-source | connection-timeout-layer-analysis | summary | 대용량 Upload 60초 단절의 Timeout 계층 분석 |
| 2026062212215842602 | 06-22 | AUTH | candidate-source | dksc-kubeconfig-and-pdep-token | summary | CLI Kubeconfig와 P-DEP Token의 목적 구분 |
| 2026062210073040603 | 06-22 | DEP | candidate-source | platform-vs-workload-fault-isolation | summary | Node 장애가 아니라 특정 Pod 과부하·OOM Killer |
| 2026062208562139360 | 06-22 | PLT | candidate-source | worker-node-ssh-prohibited | summary | VKS Worker Node 직접 SSH 접근 불가 |
| 2026062208293839035 | 06-22 | NET | bounds-claim | CCL-NET-G001; node-subnet-change-firewall-drift | summary | 신규 Worker 대역이 기존 FTP 방화벽에 미반영 |
| 2026063016540703914 | 06-30 | NET | candidate-source | dksc-contour-tcp-exposure | summary | Contour HTTPProxy TCPProxy·TLS SNI Routing |
| 2026063016483603852 | 06-30 | NET | supports-claim | CCL-NET-003 | full | DKS-C 외부 DB 방화벽 Source는 Egress SNAT IP |
| 2026063015591003237 | 06-30 | RES | supports-claim | CCL-RES-002 | summary | Jenkins Agent가 Namespace CPU Quota 초과 |
| 2026063015301202881 | 06-30 | AUTH | candidate-source | cicd-serviceaccount-vs-oidc-token | summary | CI/CD의 SA Token과 OIDC Long-Term Token |
| 2026063014152001552 | 06-30 | IMG | candidate-source | dksc-registry-management-and-quota | summary | Console Registry 관리와 10GiB 제한 |
| 2026062916425193441 | 06-29 | RES | candidate-source | dksc-unplanned-resource-request | summary | 사전 수요 없는 DKS-C 자원 근거 결재 신청 |
| 2026062914465291704 | 06-29 | IMG | candidate-source | registry-retention-user-managed | summary | 자동 삭제·보관기한 없이 Quota 안에서 사용자 관리 |

## 1차 집계

| 처분 | 건수 |
|---|---:|
| supports-claim | 13 |
| bounds-claim | 6 |
| candidate-source | 42 |
| case-only | 7 |
| out-of-scope | 1 |
| **합계** | **69** |

## 우선 비교 후보군

- `quota-request-limit-ratio`, `quota-exceeded-deployment-failure`: 1:3 정책, Namespace Quota, Scheduling Capacity를 서로 다른 계층으로 분리한다.
- `dksc-kubeconfig-*`, `cicd-serviceaccount-vs-oidc-token`, `multicluster-deployment-token`: 사람의 CLI 접속과 자동화 Token을 구분한다.
- `harbor-*`: OIDC·AD Group·Robot Account·Pull Secret·Project 생성은 서로 독립적인 Claim이 필요하다.
- `namespace-finalizer-deletion`: 일반 삭제 절차와 강제 Finalizer 제거의 위험을 함께 검증해야 한다.
- `dksn-dksc-ingress-difference`: Migration 문서의 핵심 경계 후보군이다.
