---
type: voc-coverage-ledger
period: 2026-07
status: first-pass-complete
voc_count: 38
review_basis: summary-plus-selected-full-dialogue
last_reviewed: 2026-09-25
---

# 2026-07 VOC Coverage Ledger

> 7월 1일부터 7월 18일까지 등록된 VOC 38건의 1차 처분이다. 현재 VOC 폴더에서 확인되는 마지막 등록 기간이다.

| VOC | 날짜 | 도메인 | 처분 | 관련 Claim / 후보군 | 검토 | 핵심 내용 |
|---|---|---|---|---|---|---|
| 2026070315304232707 | 07-03 | NET | candidate-source | node-subnet-not-individual-ip | summary | Auto Scaling Node는 개별 IP가 아닌 Subnet 단위 관리 |
| 2026070313103230545 | 07-03 | PLT | candidate-source | user-helm-under-policy-guardrails | summary | Kyverno·PSS 준수 조건의 사용자 Helm 설치 |
| 2026070311513629933 | 07-03 | AUTH | candidate-source | certificate-san-validation | summary | 인증서 검증은 CN보다 SAN을 우선 |
| 2026070215422022832 | 07-02 | AUTH | candidate-source | namespace-tls-secret-responsibility | summary | 사용자 TLS 인증서·Key는 Namespace Secret에서 관리 |
| 2026070211275719321 | 07-02 | PLT | supports-claim | CCL-NET-006, CCL-NET-007 | summary | Nginx Ingress와 Contour·Envoy Gateway API 차이 |
| 2026070210463918590 | 07-02 | AUTH | candidate-source | dksn-role-creation-boundary | summary | DKS-N 사용자 Role 생성 제한과 RoleBinding Mapping |
| 2026070114095511072 | 07-01 | DEP | candidate-source | cpu-throttling-timeout | summary | CPU Limit 초과·Throttling과 HPA·Limit 조정 |
| 2026070111201509120 | 07-01 | NET | candidate-source | dksc-vpc-tenant-isolation | summary | VPC 기반 1:1:1 Tenant 격리 구조 |
| 2026070109152207551 | 07-01 | RES | candidate-source | resource-quota-ui-observation | summary | Workload UI에서 Namespace Quota Used·Limit 확인 |
| 2026070108041106080 | 07-01 | PLT | candidate-source | pss-hostpath-hostport-prohibition | summary | Kyverno PSS로 HostPort·HostPath 차단 |
| 2026071014035082777 | 07-10 | CON | out-of-scope | catalog-feature-request | summary | Catalog Ingress Custom Values 개선 검토 |
| 2026071010500280606 | 07-10 | DEP | candidate-source | ingress-backend-readiness | summary | 502의 실제 원인은 Container Port Connection Refused |
| 2026071009220779103 | 07-10 | PLT | out-of-scope | regional-access-policy | summary | 해외 연구소 IP의 규정·법적 접근 제한 |
| 2026070915201074247 | 07-09 | IMG | case-only | registry-quota-project-change | summary | 특정 Harbor Registry 10GiB에서 150GiB 증설 |
| 2026070914260173368 | 07-09 | STO | candidate-source | statefulset-volumeclaimtemplate-immutable | summary | StatefulSet VolumeClaimTemplate 수정 불가, 재생성 |
| 2026070914154173172 | 07-09 | PLT | candidate-source | dksn-dksc-local-cli-access | summary | DKS-N 외부 Endpoint 미제공, DKS-C Local kubectl 지원 |
| 2026070913140772220 | 07-09 | CON | out-of-scope | edm-attachment-error | summary | 결재 첨부파일 오류를 EDM Helpdesk로 이관 |
| 2026070910454370421 | 07-09 | PLT | candidate-source | cae-environment-availability | summary | CAE Infra 미확보와 향후 DevOps망 계획 |
| 2026070910420970348 | 07-09 | IMG | candidate-source | cae-harbor-secret-and-firewall | summary | CAE 전용 Harbor·ImagePullSecret·VWP 방화벽 |
| 2026070909551569635 | 07-09 | NET | candidate-source | runbook-network-access-boundary | summary | PC 위치·건물별 Network 정책으로 Runbook URL 차단 |
| 2026070810412560478 | 07-08 | NET | case-only | production-development-subnet-distinction | summary | 운영·개발 Cluster Subnet 구분 확인 |
| 2026070711202251404 | 07-07 | AUTH | candidate-source | cicd-serviceaccount-vs-oidc-token | summary | DKS-C 외부 API·P-DEP에는 OIDC 장기 Token 안내 |
| 2026070707335247998 | 07-07 | IMG | candidate-source | harbor-registry-trust | summary | Docker Unknown Authority와 Root CA·Insecure Registry |
| 2026070619392047178 | 07-06 | AUTH | candidate-source | serviceaccount-token-secret-lifecycle | summary | ServiceAccount 연결 전 Token Secret 소멸·자동 발급 |
| 2026070616480645617 | 07-06 | AUTH | supports-claim | CCL-AUTH-003 | summary | One Cloud 멤버 등록 후 DKS-C 최초 Login 필요 |
| 2026070613235842138 | 07-06 | DEP | candidate-source | platform-vs-workload-fault-isolation | summary | UI 정지 원인이 Platform이 아닌 App 부하·호출 Pattern |
| 2026071617520129033 | 07-16 | NET | supports-claim | CCL-NET-001, CCL-NET-002 | full | DKS-N 내부 Cluster IP와 DNS용 VIP 구분 |
| 2026071615341227017 | 07-16 | NET | bounds-claim | CCL-NET-G001; cae-outbound-node-subnet | full | CAE DKS Worker 대역과 Harbor Secret 안내 |
| 2026071614024125668 | 07-16 | PLT | candidate-source | service-model-difference | full | DKS-N Namespace형과 DKS-C 독립 Cluster형 비교 |
| 2026071516232517757 | 07-15 | AUTH | candidate-source | dksc-rootca-trust; inter-vpc-firewall; longterm-token-validity | full | Node Root CA Trust·IaaS 통신·장기 Token 1년 |
| 2026071511402714205 | 07-15 | CON | case-only | namespace-change-default-ui-bug | full | Namespace 변경 화면 기본값 재선택 Bug |
| 2026071511054113740 | 07-15 | PLT | out-of-scope | overseas-investment-process | full | 해외 법인 자체 수요·투자 Process |
| 2026071318535899180 | 07-13 | NET | candidate-source | connectivity-layer-differential-diagnosis | full | Envoy 정상 인입 후 사용자망 URL·Payload 정책 차단 |
| 2026071317114898244 | 07-13 | NET | supports-claim | CCL-NET-004, CCL-NET-005 | full | DKS-C NodePort 직접 접근 불가와 LB VIP Backend |
| 2026071315201096512 | 07-13 | NET | candidate-source | dksc-gateway-healthcheck-route | redacted | Gateway Route의 Health Check Path Mapping |
| 2026071314102295411 | 07-13 | IMG | candidate-source | image-download-performance | redacted | 대용량 Image Download 지연·Runtime 처리 점검 |
| 2026071311053093214 | 07-13 | NET | supports-claim | CCL-NET-003 | redacted | DKS-C 고정 Egress SNAT IP로 외부 DB 방화벽 연동 |
| 2026071216401589123 | 07-12 | IMG | candidate-source | harbor-vulnerability-scan-policy | redacted | Harbor Trivy Scan 결과와 배포 차단 기준 |

## 1차 집계

| 처분 | 건수 |
|---|---:|
| supports-claim | 5 |
| bounds-claim | 1 |
| candidate-source | 25 |
| case-only | 3 |
| out-of-scope | 4 |
| **합계** | **38** |

## 우선 비교 후보군

- `dksn-dksc-*`: Ingress, CLI 접속, Tenant 구조를 하나의 차이표로 합치기 전에 각각 별도 Claim으로 검증한다.
- `certificate-san-validation`, `namespace-tls-secret-responsibility`, `dksc-rootca-trust`: Server 인증서, Workload Trust, Node Trust를 혼합하지 않는다.
- `cicd-serviceaccount-vs-oidc-token`, `serviceaccount-token-secret-lifecycle`: Token 목적과 Kubernetes 버전 동작을 분리한다.
- `pss-hostpath-hostport-prohibition`, `user-helm-under-policy-guardrails`: 설치 자유와 Security Guardrail의 관계를 검증한다.
- `connectivity-layer-differential-diagnosis`: Envoy까지 정상인 경우 상위 보안정책·Application을 다음 후보로 보는 Guard Claim을 검토한다.
