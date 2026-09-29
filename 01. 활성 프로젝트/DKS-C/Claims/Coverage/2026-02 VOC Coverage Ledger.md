---
type: voc-coverage-ledger
period: 2026-02
status: first-pass-complete
voc_count: 41
review_basis: summary-only
last_reviewed: 2026-09-25
---

# 2026-02 VOC Coverage Ledger

> 이 Ledger는 모든 2월 VOC의 1차 처분을 기록한다. 현재 폴더에는 `2026-02-15 ~ 2026-02-21` 주차 파일이 없으므로, 이 Ledger는 존재하는 3개 주차 파일의 41건만 다룬다. Claim 승격 전에는 상세 공식 답변을 다시 확인한다.

| VOC | 날짜 | 도메인 | 처분 | 관련 Claim / 후보군 | 검토 | 핵심 내용 |
|---|---|---|---|---|---|---|
| 2026020616281637308 | 02-06 | STO | candidate-source | pvc-shrink-not-supported | summary | 기존 PVC 분할·축소 불가, 신규 생성·마이그레이션 |
| 2026020613441335043 | 02-06 | NET | candidate-source | ingress-http-port-boundary | summary | Ingress HTTP 80·443 지원, 일반 사용자 NodePort 공개 지양 |
| 2026020611043333480 | 02-06 | NET | candidate-source | ingress-body-size | summary | 기본 Body 1MB와 `proxy-body-size` 조정 |
| 2026020610520033255 | 02-06 | DEP | candidate-source | app-log-rolling-responsibility | summary | 로그 RollingPolicy는 컨테이너 애플리케이션 권한·환경 점검 영역 |
| 2026020518515630035 | 02-05 | RES | candidate-source | unplanned-minimum-resource | summary | 수요 미포함 시 최소 자원 신청 후 변경신청 |
| 2026020516394128813 | 02-05 | CON | case-only | namespace-application-account-incident | summary | 계정 정보 이상으로 결재 취소 후 재신청 |
| 2026020513120725900 | 02-05 | RES | candidate-source | incremental-quota-increase | summary | CPU 피크 근거로 점진적 증설 |
| 2026020415471018662 | 02-04 | NET | bounds-claim | CCL-NET-G001; legacy-outbound-node-subnet | summary | 서비스 모델 미확인 Pod 아웃바운드 Worker Node Source 안내 |
| 2026020415321318476 | 02-04 | CON | candidate-source | namespace-project-transfer-unsupported | summary | Namespace Project 이전 불가, 반납 후 재배포 |
| 2026020411501215974 | 02-04 | STO | case-only | volume-not-published-node | summary | PVC 증설 뒤 특정 노드 Publish 실패, Cordon 조치 |
| 2026020411404115875 | 02-04 | RES | candidate-source | resource-usage-evidence-for-reduction | summary | 감설 판단용 CPU·Memory Max 사용량 제공 |
| 2026020410254114677 | 02-04 | NET | supports-claim | CCL-NET-002 | summary | 해외법인 인바운드 Cluster VIP와 URL Filtering |
| 2026020409585514266 | 02-04 | DEP | candidate-source | ephemeral-storage-eviction | summary | 공용 노드 DiskPressure와 Pod Evict |
| 2026020408583213333 | 02-04 | PLT | candidate-source | shared-platform-boundaries | summary | 외부 kubectl·모니터링·CAE Harbor 제약 종합 안내 |
| 2026020408343213030 | 02-04 | DEP | candidate-source | ephemeral-storage-eviction | summary | 타 Namespace의 ephemeral-storage 고갈이 공용 노드에 전파 |
| 2026020312141806661 | 02-03 | CON | candidate-source | resource-change-request | summary | 최소 스토리지 외 추가 자원 변경신청 |
| 2026020310214405017 | 02-03 | NET | candidate-source | ingress-port-boundary | summary | Ingress 80·443 외 포트와 특정 NodePort 범위 미지원 |
| 2026020309571604649 | 02-03 | CON | case-only | namespace-permission-duplicate-bug | summary | Namespace 권한 중복 적용 버그 조치 |
| 2026020218075901594 | 02-02 | STO | candidate-source | storage-mount-support-boundary | summary | NFS 마운트 지원, Object Storage 마운트 미지원 |
| 2026020212371096980 | 02-02 | NET | candidate-source | cae-repository-firewall | summary | CAE 자체 이미지·Helm 저장소 방화벽 Source 대역 안내 |
| 2026020210355795480 | 02-02 | IMG | supports-claim | CCL-IMG-001 | summary | ImagePullSecret·토큰·전체 Image 경로와 방화벽 구분 |
| 2026020209242794297 | 02-02 | IMG | case-only | image-pull-runtime-restart | summary | 느린 Pull에 kubelet·containerd 재기동 후 모니터링 |
| 2026020207092193033 | 02-02 | STO | candidate-source | shared-nas-qos-bottleneck | summary | Shared PV NAS QoS 제한과 성능 병목 후보 |
| 2026021309112578507 | 02-13 | NET | out-of-scope | duplicate-voc | summary | 고정 IP 문의 중복 접수 |
| 2026021218065176507 | 02-12 | PLT | candidate-source | shared-cluster-istio-unavailable | summary | 공용 Namespace 환경 Istio 미설치·전용형 계획 |
| 2026021217281176273 | 02-12 | OBS | candidate-source | prometheus-pod-churn-cardinality | summary | 타 Namespace Pod 급속 생성·삭제로 TSDB 메트릭 폭증 |
| 2026021208144969603 | 02-12 | STO | candidate-source | nfs-qos-stale-handle | summary | NFS stale handle과 NAS QoS, Block Storage 우회 |
| 2026021114522765888 | 02-11 | STO | candidate-source | storage-type-change-request | summary | RWO·RWX 오신청 후 Block Storage 추가 변경신청 |
| 2026021109410962159 | 02-11 | IMG | candidate-source | image-tag-existence-first-check | summary | Failed Pull 시 Registry 실제 Tag 존재 확인 |
| 2026021016230057995 | 02-10 | NET | candidate-source | tcp-nodeport-limit; ingress-port-boundary | summary | Ingress 80·443, 기타 TCP NodePort와 HA 사용자 책임 |
| 2026021014531656645 | 02-10 | NET | candidate-source | tcp-nodeport-limit | summary | FTP TCP를 Worker Node NodePort로 제공, 노드 가변성 주의 |
| 2026021010545454009 | 02-10 | PLT | out-of-scope | test-voc | summary | 댓글 기능 테스트용 VOC |
| 2026020916335148759 | 02-09 | NET | supports-claim | CCL-NET-002 | summary | 도메인 조회 기반 VIP 확인과 URL Filtering |
| 2026020814014741036 | 02-08 | RES | candidate-source | low-utilization-reclaim; vm-dks-resource-separation | summary | VM·DKS 수요 구분과 저활용 기반 재신청 |
| 2026022613431630513 | 02-26 | PLT | candidate-source | vm-dks-resource-nontransferable | summary | Cloud VM과 DKS는 별도 자원으로 이관 불가 |
| 2026022612410229905 | 02-26 | PLT | candidate-source | outbound-internet-direct-access-limit | summary | 사외 직접 통신 제한, 사내 Repository 경유 |
| 2026022611160529134 | 02-26 | AUTH | candidate-source | serviceaccount-token-secret-manual | summary | Kubernetes 1.24+ SA Secret 자동생성 미지원과 수동 Token |
| 2026022610255828376 | 02-26 | NET | candidate-source | ingress-body-size | summary | `proxy-body-size: "0"`으로 Body 제한 해제 |
| 2026022517064524918 | 02-25 | NET | candidate-source | ingress-header-size | summary | 502의 Header Size 원인과 Ingress Annotation 조정 |
| 2026022411561713187 | 02-24 | OBS | candidate-source | prometheus-pod-churn-cardinality | summary | 단기 Batch Pod 반복으로 Prometheus OOM |
| 2026022311243204451 | 02-23 | RES | candidate-source | resource-usage-evidence-for-reduction | summary | 저활용 회수 대응 CPU·Memory AVG/MAX 통계 정정 |

## 1차 집계

| 처분 | 건수 |
|---|---:|
| supports-claim | 3 |
| bounds-claim | 1 |
| candidate-source | 31 |
| case-only | 4 |
| out-of-scope | 2 |
| **합계** | **41** |

## 우선 비교 후보군

- `ingress-body-size`: 동일 달에 두 사례가 있어 원문 비교 우선순위가 높다.
- `ephemeral-storage-eviction`: 공용 노드 자원 경계 Claim 후보다.
- `prometheus-pod-churn-cardinality`: Pod churn과 TSDB/OOM 인과 Claim 후보다.
- `unplanned-minimum-resource`, `resource-change-request`, `resource-usage-evidence-for-reduction`: 자원 신청·변경·회수 판단을 분리해 검토한다.
- `serviceaccount-token-secret-manual`: Kubernetes 버전 전제와 DKS 정책을 구분해야 한다.
