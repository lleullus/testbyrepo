---
type: voc-coverage-ledger
period: 2026-04
status: first-pass-complete
voc_count: 48
review_basis: summary-only
last_reviewed: 2026-09-25
---

# 2026-04 VOC Coverage Ledger

> 4월 등록 VOC 48건의 1차 처분이다. `2026-03-29 ~ 2026-04-04`와 `2026-04-26 ~ 2026-05-02`의 4월 등록 건을 포함한다.

| VOC | 날짜 | 도메인 | 처분 | 관련 Claim / 후보군 | 검토 | 핵심 내용 |
|---|---|---|---|---|---|---|
| 2026040315450674172 | 04-03 | AUTH | supports-claim | CCL-AUTH-003 | summary | AD 권한 미보유 계정은 DKS 콘솔 1회 로그인 후 연동 |
| 2026040313295272156 | 04-03 | AUTH | candidate-source | project-and-namespace-membership | summary | 협력사 사용자의 기존 Project 권한 확인 |
| 2026040313023671809 | 04-03 | IMG | candidate-source | harbor-bundle-quota-limit; registry-trust | summary | 번들 Harbor 확장 불가와 사내 Registry 활용 |
| 2026040213575563496 | 04-02 | AUTH | candidate-source | tls-secret-registration; dksctl-session-ephemeral | summary | 세션 휘발성과 콘솔 TLS Secret 등록 |
| 2026040209003859682 | 04-02 | PLT | candidate-source | service-population-and-region-scope | summary | HQ 대상 서비스 원칙과 해외 Region 별도 담당 |
| 2026040208180859193 | 04-02 | IMG | supports-claim | CCL-IMG-002 | summary | AD 비밀번호 변경 뒤 ImagePullSecret 갱신 |
| 2026040119202958138 | 04-01 | AUTH | supports-claim | CCL-AUTH-001 | summary | One Cloud Project 권한 선행 후 Namespace·Harbor 권한 |
| 2026040118055057695 | 04-01 | AUTH | out-of-scope | duplicate-voc | summary | 상세 보완 VOC로 연계 종결 |
| 2026040110075950942 | 04-01 | NET | supports-claim | CCL-NET-002 | summary | DNS용 Cluster VIP 조회와 URL Filtering |
| 2026041017020825226 | 04-10 | CON | case-only | namespace-quota-apply-bug | summary | Memory Quota 증설 미반영 버그 조치 |
| 2026041008295318366 | 04-10 | DEP | candidate-source | scheduling-insufficient-capacity | summary | Insufficient CPU Pending과 전용 노드 자원 이관 |
| 2026040913484912883 | 04-09 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | Knox API Source에 Worker Node 대역 등록 |
| 2026040908233608510 | 04-09 | STO | supports-claim | CCL-STO-001, CCL-STO-002 | summary | PVC의 VM 직접 공유 불가, VM NFS 대안 |
| 2026040809041099408 | 04-08 | CON | case-only | browser-cache-deployment-status | summary | 브라우저 Cache로 배포 상태 오표시 |
| 2026040714322493791 | 04-07 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | NAS ACL Source에 Worker Node 대역 안내 |
| 2026040713420393093 | 04-07 | NET | case-only | external-vm-lb-target-change | summary | 사외망 VM 연결을 IT Cloud LB Target으로 변경 |
| 2026040708550889644 | 04-07 | IMG | candidate-source | dksctl-tool-support-boundary | summary | DKSctl Docker 미지원과 Crane 대안 |
| 2026040618370987743 | 04-06 | AUTH | candidate-source | repository-ca-trust | summary | 신규 Repository 신뢰 CA의 노드 적용 계획 |
| 2026040614581984960 | 04-06 | DEP | candidate-source | rollout-new-pod-readiness | summary | 외부 DB 방화벽 미오픈으로 신규 Pod 미기동·Rollout 중단 |
| 2026040613000283076 | 04-06 | DEP | candidate-source | kms-agent-bundle-deployment | summary | 번들 Harbor와 Gateway Pod 연계 KMS Agent 구성 |
| 2026040609362480409 | 04-06 | NET | supports-claim | CCL-NET-002 | summary | Cluster VIP 조회와 GSAMS URL Filtering |
| 2026041714554273484 | 04-17 | OBS | candidate-source | namespace-monitoring-boundary | summary | Namespace 전체 모니터링 한계와 전용형 Beta 안내 |
| 2026041710055069966 | 04-17 | DEP | candidate-source | pdep-custom-helm-unsupported | summary | P-DEP 정의 Template 외 Custom Helm 직접 설치 미지원 |
| 2026041619461767506 | 04-16 | DEP | supports-claim | CCL-DEP-001, CCL-DEP-002 | summary | 재배포 시 Ingress Backend Service 이름 치환 제약 |
| 2026041615483665529 | 04-16 | NET | supports-claim | CCL-NET-002 | summary | DNS 등록용 Cluster Domain 조회 VIP |
| 2026041511425952809 | 04-15 | NET | supports-claim | CCL-NET-001, CCL-NET-002 | summary | 내부 Ingress IP가 아닌 Cluster VIP 등록 |
| 2026041510122851361 | 04-15 | PLT | candidate-source | shared-cluster-availability-topology | summary | DKS 3AZ 기흥·화성 가용성 구조 설명 |
| 2026041416130946649 | 04-14 | AUTH | supports-claim | CCL-AUTH-001, CCL-AUTH-002 | summary | One Cloud Project 멤버 추가 후 Namespace 권한 |
| 2026041316005436587 | 04-13 | PLT | supports-claim | CCL-PLT-001, CCL-PLT-002 | summary | 공용 환경 ClusterRole·CRD 미제공, 전용형 안내 |
| 2026042316415008079 | 04-23 | DEP | candidate-source | container-image-tool-responsibility | summary | vi 부재는 Image 구성 문제, kubectl cp 대안 |
| 2026042211051800439 | 04-22 | IMG | candidate-source | harbor-project-namespace-coupling | summary | Namespace 기반 자동 Harbor Project와 Pull Secret |
| 2026042119491296949 | 04-21 | DEP | candidate-source | git-to-cluster-one-way-sync | summary | Git Config Repository에서 DKS로 단방향 반영 |
| 2026042116145395245 | 04-21 | AUTH | candidate-source | ingress-certificate-responsibility | summary | DKS 인증서 미제공, IAM 발급 후 TLS Secret 등록 |
| 2026042113280492909 | 04-21 | CON | candidate-source | console-cli-capability-boundary | summary | UI 제약 시 DKSctl로 ConfigMap·Secret 등록 |
| 2026042109092689660 | 04-21 | STO | candidate-source | volume-permission-runtime-identity | summary | NAS UID 불일치와 runAsUser·fsGroup 조정 |
| 2026042108444889230 | 04-21 | NET | candidate-source | ingress-annotation-support-boundary | summary | Nginx Snippet 문법과 지원 범위 |
| 2026042018564587681 | 04-20 | DEP | candidate-source | workload-name-kubernetes-default | summary | DKS 강제 Pod 명명 규칙 없이 Kubernetes 규칙 적용 |
| 2026042014360484563 | 04-20 | PLT | candidate-source | managed-core-component-visibility | summary | 공용 Core Pod 직접 조회 권한 미제공 |
| 2026042013113883288 | 04-20 | CON | candidate-source | console-cli-capability-boundary | summary | UI 제약이 있는 ExternalName Service를 CLI로 생성 |
| 2026043015572249189 | 04-30 | AUTH | candidate-source | ingress-certificate-responsibility | summary | DKS 직접 인증서 발급 미지원, IAM·TLS Secret 절차 |
| 2026043014263448079 | 04-30 | AUTH | candidate-source | repository-ca-trust | summary | Repository Issuing CA 사전 등록으로 별도 작업 불필요 |
| 2026042912491137550 | 04-29 | AUTH | case-only | serviceaccount-permission-incident | summary | 사용자 권한 누락으로 SA 생성 불가, 권한 부여 |
| 2026042910405836126 | 04-29 | DEP | candidate-source | container-file-transfer-boundary | summary | 로컬 직접 Download 미지원, Repository 업로드·kubectl cp |
| 2026042814533029433 | 04-28 | CON | case-only | project-aa-change-request | summary | 임시 AA Project의 정식 AA 재신청 |
| 2026042814164028971 | 04-28 | IMG | candidate-source | harbor-project-namespace-coupling; harbor-bundle-quota-limit | summary | Harbor는 Namespace 번들, 공용 Project·Quota 증설 미제공 |
| 2026042810465626401 | 04-28 | STO | supports-claim | CCL-STO-001, CCL-STO-002 | summary | DKS NAS의 VM 직접 Mount 불가, NFS·rsync 대안 |
| 2026042719112022992 | 04-27 | NET | case-only | ingress-controller-capacity-change | summary | 특정 C-DEP Ingress Controller Node Spec 증설 |
| 2026042715332920559 | 04-27 | IMG | case-only | legacy-harbor-project-manual-create | summary | 구형 Namespace Harbor Project 수동 생성 |

## 1차 집계

| 처분 | 건수 |
|---|---:|
| supports-claim | 12 |
| bounds-claim | 2 |
| candidate-source | 26 |
| case-only | 7 |
| out-of-scope | 1 |
| **합계** | **48** |

## 우선 비교 후보군

- `project-and-namespace-membership`: One Cloud Project, Namespace, Harbor 권한의 선후관계 후보군이다.
- `harbor-project-namespace-coupling`, `harbor-bundle-quota-limit`: Project 생성과 저장공간 정책을 분리한다.
- `console-cli-capability-boundary`: UI 미지원과 플랫폼 미지원은 구별해야 한다.
- `dks-volume-vm-sharing-boundary`: DKS 관리 Volume과 VM 파일공유 경계가 복수 사례에서 반복됐다.
- `ingress-certificate-responsibility`: 인증서 발급 주체와 Kubernetes TLS Secret 등록 주체를 분리한다.
