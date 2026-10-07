---
type: voc-coverage-ledger
period: 2026-05
status: first-pass-complete
voc_count: 44
review_basis: summary-plus-selected-full-dialogue
last_reviewed: 2026-09-25
---

# 2026-05 VOC Coverage Ledger

> 5월 등록 VOC 44건의 1차 처분이다. DKS-C와 기존 공용형 DKS의 차이가 답을 갈라놓기 시작하므로 서비스 모델이 불명확한 사례는 일반화하지 않는다.

| VOC | 날짜 | 도메인 | 처분 | 관련 Claim / 후보군 | 검토 | 핵심 내용 |
|---|---|---|---|---|---|---|
| 2026050814553588576 | 05-08 | AUTH | candidate-source | ingress-tls-ci-cd-order | summary | Ingress TLS 직접 설정 정상화와 CI/CD 반영 선후관계 |
| 2026050809322884471 | 05-08 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | 방화벽용 Worker Node 대역 안내 |
| 2026050717050981257 | 05-07 | RES | candidate-source | low-utilization-reclaim-exception | summary | 회수 이력 확인과 예외 결재 양식 |
| 2026050711103676786 | 05-07 | IMG | supports-claim | CCL-IMG-001 | summary | CronJob에 ImagePullSecret 누락으로 401 |
| 2026050711044676649 | 05-07 | DEP | candidate-source | container-timezone-configuration | summary | Image·Pod YAML에서 Timezone 구성 |
| 2026050408252355683 | 05-04 | IMG | candidate-source | dksc-registry-quota | summary | DKS-C Registry 10GB에서 50GB 증설 조치 |
| 2026051517142637735 | 05-15 | NET | candidate-source | dksc-loadbalancer-tcp-exposure | summary | DKS-C LoadBalancer Service 외부 IP로 DB TCP 접근 |
| 2026051509123132269 | 05-15 | CON | supports-claim | CCL-CON-001, CCL-CON-002, CCL-AUTH-001, CCL-AUTH-002 | summary | Namespace 이름 불변성과 협력사 Project 멤버 절차 |
| 2026051417172629842 | 05-14 | NET | candidate-source | dksc-gateway-tls-and-ingress | summary | DKS-C Gateway TLS Secret과 단독 Ingress IP 방화벽 |
| 2026051414095927533 | 05-14 | CON | case-only | namespace-create-button-bug | summary | 콘솔 목록추가 버튼 오동작 조치 |
| 2026051409462824287 | 05-14 | AUTH | candidate-source | project-and-namespace-membership | summary | 앱배포 파이프라인 메뉴의 DKS 멤버 권한 |
| 2026051317473421401 | 05-13 | PLT | case-only | control-plane-expansion-incident | summary | Control Plane 3중화 작업 뒤 Ingress IP 정상 노출 |
| 2026051313272517851 | 05-13 | PLT | candidate-source | workload-platform-fit | summary | 특정 AI Web 서비스의 VM·GPU 자원 신청 경로 안내 |
| 2026051309014214595 | 05-13 | PLT | out-of-scope | non-dks-firewall-request | summary | DSDN·Assistant 접속 정보와 보안SOS 이관 |
| 2026051216565011625 | 05-12 | AUTH | candidate-source | administrator-delegation | summary | 대표관리자·관리자 역할을 다른 인력에게 위임 |
| 2026051216363611350 | 05-12 | NET | candidate-source | network-profile-node-subnet; dksc-migration | summary | 임시 Node 대역과 DKS-C Beta 대역 차이 |
| 2026051215080609968 | 05-12 | AUTH | case-only | kubeconfig-account-incident | summary | v1.33 API 401과 올바른 계정 확인 |
| 2026051210223006354 | 05-12 | IMG | candidate-source | dksc-registry-image-flow | summary | Base Image를 Harbor에 Push하고 명시적 Tag 사용 |
| 2026051116153401388 | 05-11 | DEP | case-only | application-coredump-incident | summary | Postgres CrashLoop 분석, Storage 이상 없음 |
| 2026051115122000391 | 05-11 | PLT | supports-claim | CCL-PLT-001, CCL-PLT-002 | summary | DKS-N Operator 제약과 비 Operator Helm·DKS-C 대안 |
| 2026051113491299093 | 05-11 | NET | case-only | worker-shutdown-timeout-incident | summary | Proxy Timeout이 아닌 Worker Shutdown 설정 원인 |
| 2026051113313498841 | 05-11 | NET | candidate-source | connectivity-layer-differential-diagnosis | summary | 405는 방화벽이 아니라 Ingress Path 불일치 |
| 2026051110242496547 | 05-11 | STO | case-only | trident-operator-cpu-change | summary | 특정 C-DEP Trident CPU Limit 변경 |
| 2026051110173596440 | 05-11 | PLT | out-of-scope | vm-os-firewall-request | summary | 가상 서버 OS 방화벽 원격지원 |
| 2026051109591596152 | 05-11 | AUTH | supports-claim | CCL-AUTH-001 | summary | DKS Project 사용자 추가 전 One Cloud 멤버 등록 |
| 2026051108533795058 | 05-11 | PLT | supports-claim | CCL-PLT-003 | summary | DKS-N 공용 Node Label 미지원과 DKS-C 권고 |
| 2026052214564372597 | 05-22 | PLT | supports-claim | CCL-PLT-003 | summary | 공용 Node Label 관리 불가와 Deployment 대안 |
| 2026052214212372495 | 05-22 | IMG | case-only | registry-tag-delete-ui-bug | summary | 개별 Tag 삭제 미동작 개선 접수 |
| 2026052115085469281 | 05-21 | STO | candidate-source | pvc-delete-while-mounted | summary | 사용 중인 PVC 삭제 불가, Mount 해제 후 삭제 |
| 2026052016031464310 | 05-20 | NET | bounds-claim | CCL-NET-G001; node-subnet-change-firewall-drift | summary | 신규 Worker Node 대역의 기존 방화벽 누락 |
| 2026052011420961939 | 05-20 | NET | candidate-source | dksc-ingress-lb-ui-discovery | summary | Cluster 관리 UI에서 Ingress·LB IP 확인 |
| 2026051912595354289 | 05-19 | NET | supports-claim | CCL-NET-003 | full | DKS-C 외부 통신은 Egress IP Source |
| 2026051910115652478 | 05-19 | STO | supports-claim | CCL-STO-001 | summary | DKS NAS를 관리 범위 밖 VM에 Mount 불가 |
| 2026051817525049244 | 05-18 | DEP | supports-claim | CCL-DEP-001, CCL-DEP-002 | summary | 재배포 덮어쓰기를 피하려면 Git·CD 설정 수정 |
| 2026052917011208467 | 05-29 | IMG | candidate-source | dksc-bundled-harbor-discovery | summary | DKS-C 번들 Harbor Registry 확인 경로 |
| 2026052916044707931 | 05-29 | PLT | candidate-source | dksc-beta-environment-availability | summary | Beta 기간 개발·Staging 신청 비활성화, 운영 목적 생성 |
| 2026052914471007049 | 05-29 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | 외부 DataLake 접근에도 Worker Node 방화벽 필요 안내 |
| 2026052911180605029 | 05-29 | PLT | candidate-source | namespace-project-transfer-unsupported; service-model-difference | summary | DKS-N Project 변경 불가와 DKS-N/C 차이 |
| 2026052817073800402 | 05-28 | NET | candidate-source | connectivity-layer-differential-diagnosis | summary | TLS Handshake 후 서버 TCP Reset과 방화벽 구분 |
| 2026052811241496588 | 05-28 | CON | case-only | console-outage-incident | summary | DKS Console 접속 장애 조치 |
| 2026052811092596306 | 05-28 | PLT | out-of-scope | security-port-exception | summary | FTP 21 Port 보안 정책과 예외 신청 이관 |
| 2026052718461692688 | 05-27 | CON | supports-claim | CCL-CON-001, CCL-CON-002 | summary | Namespace 이름 변경 불가, 신규 생성 후 이전 |
| 2026052709023485754 | 05-27 | DEP | candidate-source | platform-vs-workload-fault-isolation | summary | Node 이상 없음, Pod CPU 부족·Probe 실패 원인 |
| 2026052618154083992 | 05-26 | CON | supports-claim | CCL-CON-001, CCL-CON-002 | summary | 오타 Namespace 이름 변경 불가, 신규 생성·삭제 |

## 1차 집계

| 처분 | 건수 |
|---|---:|
| supports-claim | 11 |
| bounds-claim | 3 |
| candidate-source | 19 |
| case-only | 8 |
| out-of-scope | 3 |
| **합계** | **44** |

## 우선 비교 후보군

- `namespace-rename-not-supported`: 여러 달 반복되어 원문 비교 후 절차·불변성 Claim으로 승격할 수 있다.
- `shared-node-label-management`: 공용 Node 책임 경계가 독립 사례에서 반복됐다.
- `node-subnet-change-firewall-drift`: Node 증설·변경과 외부 방화벽 Source 목록의 변경 관리 후보군이다.
- `connectivity-layer-differential-diagnosis`: HTTP Status·TLS Handshake 단계로 방화벽과 애플리케이션 원인을 분리하는 Guard 후보군이다.
- `dksc-*`: DKS-C Beta 당시 정책과 현재 정식 서비스 정책을 반드시 구분한다.
