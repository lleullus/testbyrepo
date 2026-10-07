# [DKS-C] VCF 기반 Kubernetes 연휴 대비 사전 점검 체계 및 보고서 템플릿
작성자: 미기재  
마지막 업데이트: 미기재  
읽기 시간: 20분

## 1. 개요

이 문서는 DKS-N의 기존 8대 점검 항목인 `Cluster Status`, `Core Node`, `Core Pod`, `Prometheus PVC`, `API Server`, `ETCD`, `Alert`, `ETCD Defrag 추이`를 유지하면서, DKS-C의 실제 장애 경로인 `VCF/VCFA → Supervisor/CCI/CAPI → VKS → CNS/CSI·Storage Policy → NSX VPC/IPAM·Avi LB`와 인증서·토큰·백업 계층을 추가한다.

점검 목적은 현재 화면이 초록색인지 확인하는 데 그치지 않는다. 연휴 종료 시점까지 다음 조건이 유지되는지를 증거로 판정한다.

1. 현재 제어 평면과 데이터 평면이 정상이다.
2. 연휴 중 만료되는 인증서·토큰이 없다.
3. 스토리지·IP·etcd 용량이 예상 증가량과 비상 복구 여유를 포함해 충분하다.
4. 백업 파일이 최근에 생성되었을 뿐 아니라 읽을 수 있고 복구 가능한 상태다.
5. 담당자가 없는 동안 자동 조정·인증서 갱신·백업·알람 전파가 계속 작동한다.
6. 점검 시점에 진행 중인 변경, CAPI reconcile, Argo CD sync, 노드 교체가 없다.

수치 임계치는 두 종류로 구분한다.

- **제품 하드 실패 신호**: 인증서 만료, etcd quorum 상실, `Ready=False`, quota 초과, IP 풀 고갈, 백업 실패처럼 제품 동작상 명확한 실패이다.
- **DKS-C 운영 기준**: D-day, 80%/90% 용량선, 백업 허용 지연처럼 연휴 무인 운영을 위해 적용하는 보수적 기준이다. 실제 증가 속도와 복구 소요시간을 함께 보며, 정적 퍼센트 하나로 최종 판정하지 않는다.

## 2. 확인사항

### 2.1 로컬 DKS-C 자산에서 확인된 운영 기준선

| 영역 | 확인된 기준선 | 점검 시 해석 |
|---|---|---|
| 운영 기반 | VCF 9.0, 운영 WLD01, 3 Zone, Supervisor/VCFA/CCI/VKS | Guest Cluster만 정상이어도 Supervisor·VCFA 장애가 있으면 생성·증설·복구가 중단될 수 있다. |
| 전용 인프라 클러스터 | `prd-dksc-ic01-khm`, `prd-dksg-ic01-khm`, `prd-dksl-ic01-khm`, `prd-dksm-ic01-khm`, `prd-dkso-ic01-khm` | Console, APISIX/Keycloak, OpenSearch, VictoriaMetrics/Grafana, DevOps/Harbor의 장애 도메인이 분리되어 있으므로 5개를 각각 확인해야 한다. |
| 사용자 클러스터 | 최근 일일 보고서 기준 39개 | 기대 수량과 실제 조회 수량을 대조해 누락 자체를 장애 신호로 처리한다. |
| 스토리지 정책 | `vks-pf-storage-policy` 60 TB, `vks-pf-storage-policy-admin` 50 TB, `vks-pf-storage-policy-data` 15 TB | 실제 사용량, provisioned 양, Region/Zone quota, 기저 datastore 여유를 분리해서 본다. |
| 네트워크 소비 모델 | VPC : Supervisor Namespace : VKS Cluster = 1:1:1, 클러스터당 기본 External IP 3개 | IPBlock의 퍼센트뿐 아니라 `available 절대 개수`와 연휴 중 생성·복구 수요를 계산해야 한다. |
| 인증 | Keycloak OIDC, 단기 사용자 토큰, 30~365일 이름의 장기 클라이언트, 별도 `console-token` | 클라이언트 이름이나 설정값이 아니라 실제 발급 JWT의 `exp`, Secret의 만료값, 실제 API 호출 성공을 확인한다. |
| 백업 | `logs-hub`·`metric-hub` 일 1회, `Console-db`·`Keycloak-db`·`Apisix-etcd` 시간당 1회 | 최근 샘플의 `정상`, `Fail Count 0`, snapshot count만으로는 복구 가능성을 증명하지 못한다. 최신 artifact의 age·size·checksum·repository read와 복구 검증이 필요하다. |
| 기본 Addon | cert-manager, Velero, VictoriaMetrics agent, logs/events agent, Kyverno 등 | Addon controller와 대상 CR의 `Ready`, 마지막 성공 시각, 전송 목적지 접근성을 함께 본다. |

다음 로컬 자료 불일치는 보고서 작성 전에 해소해야 한다.

- WLD 식별자가 `kh-prd-ia-wld01`과 `kh-prd-ai-wld01`로 혼재한다. 실제 VCFA/vCenter 조회 결과를 기준으로 하나를 확정한다.
- 같은 일일 보고서 안에서 `vks-pf-storage-policy` provisioned가 87%와 88%, 사용량이 22.75 TB와 23.46 TB로 다르다. 모든 표에 단일 `수집 시각`과 `원천 시스템`을 기록해야 한다.
- 일일 보고서 제목에는 Thanos가 있으나 DKS-C 기술 스택은 VictoriaMetrics를 중앙 메트릭 저장소로 정의하고, 로컬 자산에는 DKS-C Thanos URL이 없다. DKS-N URL을 재사용하지 말고 실제 사용 여부를 확인해 `N/A` 또는 정식 URL로 확정한다.
- 인증서 현황 문서의 일부 `Renewal` 날짜는 이미 지난 기준선이다. 문서 날짜를 복사하지 말고 현재 `Certificate.status.notAfter`, `status.renewalTime`, Secret의 실제 인증서와 서비스가 제공하는 인증서를 다시 수집한다.
- Keycloak 문서는 30/90/120/180 클라이언트의 표기 lifespan과 실제 발급 토큰이 항상 365일이라는 주의사항을 함께 가진다. 실제 JWT `exp`가 유일한 만료 판정 근거다.

### 2.2 DKS-C에 반드시 추가할 점검 항목과 장애 인과

| 추가 항목 | 연휴 전에 확인하지 않을 때의 장애 경로 | 정상/주의/실패 기준 |
|---|---|---|
| Supervisor/VCFA core health | Supervisor etcd·API·VM Operator·VCFA 서비스 장애 → CCI/CAPI reconcile 중단 → 노드 증설·교체·클러스터 복구 불가 | **정상:** Supervisor Config/Host Config `Running`, `v healthy vcfa` 모든 core/http/prom/sftp/dns 항목 `OK`. **실패:** 하나라도 Failed/Degraded, API 불가, reconcile 정체. |
| CAPI Machine·MachineHealthCheck | Guest API가 아직 응답해도 Machine이 `Provisioning/Deleting/Failed`에 고착 → 다음 장애 때 CP/worker 여유 상실 | **정상:** Cluster/ControlPlane/MachineDeployment `Ready=True`, replicas `desired=ready=available`, MHC remediation 0. **주의:** 진행 중 15분 이상. **실패:** CP replica 부족, remediation 불가, failed Machine 존재. |
| 인증서 실제 만료와 갱신 경로 | Supervisor VIP·Webhook·VKS·cert-manager 인증서 만료 → API/webhook 호출 거부 → 생성·수정·스케줄링 경로 차단 | **정상:** `notAfter > 연휴 종료+30일`, issuer/Certificate Ready, 갱신 후 실제 endpoint 인증서 교체 확인. **주의:** 종료+30일 이내 또는 renewal window 진입. **실패:** 종료+7일 이내, 연휴 중 만료, Ready=False, 갱신 Secret과 served cert 불일치. |
| 동시 갱신 cohort | 같은 날 생성된 다수 90일 인증서가 동시에 갱신 → issuer/API 부하 또는 재기동 집중 → HA replica 동시 영향 | 같은 HA 서비스의 2개 이상 인증서가 같은 24시간 갱신 구간이면 **주의**. 과거 성공량을 초과하거나 자동 reload가 입증되지 않으면 연휴 전 분산·선행 갱신한다. |
| `console-token`·OIDC 장기 토큰 | 무인 health check/CI가 401 → 실제 서비스가 정상이어도 감시·배포·복구 자동화 중단 | **정상:** 실제 consumer 호출 성공, `exp > 종료+30일`. **주의:** D-30 이하. **실패:** D-15 이하, 연휴 중 만료, rotation 후 consumer 미반영. 현재 로컬 샘플의 `console-token`은 현재 기준 D-5이므로 즉시 교체·호출 검증 대상이다. |
| Storage Policy·Region/Zone quota 전망 | quota 도달 → PVC·VM 생성 또는 CAPI 노드 교체 거부 → 장애 노드 복구 실패 | **정상:** `예상 종료 사용량+복구 reserve < limit`. **주의:** provisioned/used 80% 이상 또는 종료 전 85% 교차 전망. **실패:** 90% 이상, quota-denied 이벤트, 복구 reserve 부족, 데이터 원천 간 불일치 미해소. |
| CNS/CSI 볼륨 상태 | PVC Bound만 보고 CNS attachment·volume health 장애를 놓침 → 재스케줄 시 mount 불가 | **정상:** Pending PVC 0, VolumeAttachment 오류 0, CNS health green/accessible, CSI controller/node Ready. **실패:** 신규 provisioning/attach 테스트 실패, inaccessible volume, snapshot 고착. |
| NSX VPC/IPBlock/External IP | External IP 고갈 → 새 VPC/SNAT/LB VIP 할당 실패 → 클러스터 생성·서비스 복구 Pending | **정상:** `free >= 승인된 수요 + 비상 클러스터 1개분(기본 3 IP)`. **주의:** 80% 이상 또는 종료 전 reserve 하회 전망. **실패:** available 0, `EXTERNAL-IP Pending`, `FailedRealizeNSXResource`, VPC limit/usage 불일치. |
| NSX Edge/T0/BGP/BFD·Avi LB | 클러스터 내부 정상이나 외부 API/Ingress 경로 단절 | **정상:** T0/Edge/라우팅 세션 Up, Avi Controller/SE 정상, VS Up, pool member health 정상, VIP pool reserve 충족. **실패:** active alarm, BGP/BFD down, VS/pool down, VIP 풀 고갈. |
| etcd quota·fragmentation·성장률 | backend가 quota에 닿아 `NOSPACE` alarm → 쓰기 거부 → 제어 평면 lock 유사 상태 | **정상:** member 3/3 healthy, leader 1, alarm 0, quota 사용 <70%, fsync 지연 이상 없음. **주의:** 70% 이상, fragmentation 30% 이상, 종료 전 80% 교차 전망. **실패:** member down/no leader/NOSPACE 또는 종료 전 quota 도달 전망. Defrag는 백업 후 member별 순차 작업으로 별도 승인한다. |
| Supervisor/vCenter file-based backup | Supervisor CRD·namespace·VKS 정의가 소실되면 Guest workload 백업만으로 제어 평면 복원 불가 | **정상:** vCenter backup에 Supervisor Control Plane 포함, 최신 성공 artifact 접근·목록 확인, 복구 절차와 credential 확인. **실패:** 옵션 미포함, 최신 backup 실패/부재, 저장소 접근 불가. |
| Velero·서비스별 backup 무결성 | `Completed` 또는 파일 생성만 확인하면 partial snapshot·깨진 DB dump·권한 오류를 놓침 | **정상:** BSL Available, required Backup 모두 Completed, artifact non-zero/checksum, 최근 제한된 restore 검증 성공. **실패:** PartiallyFailed/Failed, 일정+grace 초과, repository verify 실패, restore evidence 없음. |
| APISIX etcd snapshot | APISIX route/auth 설정 손상 시 gateway 전체가 영향받지만 snapshot 개수만으로 복구성을 알 수 없음 | **정상:** endpoint/member health 정상, 최신 snapshot age <2시간, snapshot status hash/revision 확인, off-cluster 보관, 최근 restore 검증. |
| OpenSearch·Harbor·VictoriaMetrics | 로그·이미지·감시 계층 장애가 실제 workload 장애 발견과 복구를 차단 | OpenSearch green 및 disk watermark 미도달, snapshot SUCCESS; Harbor `/api/v2.0/health` healthy·push/pull 성공·job queue 정상; VictoriaMetrics ingest/query 성공·alert rule evaluation과 P-DEP 시험 알람 성공. |
| Argo CD·변경 동결 | 연휴 진입 시 sync/upgrade가 진행 중이면 자동 조정과 수동 대응이 충돌 | **정상:** 필수 App `Healthy/Synced`, 진행 operation 0, 실패 sync 0, 승인되지 않은 drift 0. **실패:** Progressing/Degraded/Unknown, pending deletion, 노드 교체/업그레이드 진행 중. |
| DNS/NTP | 시간 오차 → 새 인증서 `not yet valid`, OIDC JWT 거부, etcd peer TLS 실패 | **정상:** Supervisor/ESXi/vCenter/NSX/Guest가 승인 NTP에 동기화되고 유의미한 drift 없음, 핵심 FQDN 정·역방향 해석 성공. **실패:** NTP unsynchronized 또는 인증/OIDC에 영향을 주는 drift. |

### 2.3 현재 자료에서 연휴 전 우선 해소할 사항

1. **`console-token` 교체가 최우선이다.** 최근 보고서의 만료 시각은 현재 기준 D-5로, 기존 내부 기준 `remaining < 15` 경고에 이미 해당한다. 신규 토큰을 Secret에 반영한 뒤 Console API, OpenSearch, VictoriaMetrics를 사용하는 실제 health-check consumer의 2xx 응답까지 확인해야 한다.
2. **Supervisor extension 인증서 5종은 같은 만료 cohort다.** 최근 보고서 기준 만료까지 약 38일이므로 즉시 만료는 아니지만, 연휴 종료+30일 기준에 들어오는지와 cert-manager 자동 갱신·실제 endpoint reload를 확인한다.
3. **`vks-pf-storage-policy`는 provisioned 87~88%로 보고되었다.** 실제 사용량은 약 23 TB/60 TB이므로 즉시 물리 사용량 고갈로 단정할 수 없지만, quota·예약량·실사용량·datastore 여유가 서로 다른 수치다. CAPI 노드 교체 reserve를 포함한 전망으로 판정한다.
4. **External IPBlock은 provisioned 64%로 보고되었다.** 총량이 없어 절대 잔여 수를 알 수 없으므로 `total/allocated/available`을 다시 수집해야 한다. DKS-C는 클러스터당 기본 3 IP를 사용하므로 퍼센트만으로 Go 판정을 내릴 수 없다.
5. **백업 표는 실행 횟수 또는 실패 건수 위주다.** `logs-hub`, `metric-hub`, DB, APISIX etcd 모두 최신 artifact 식별자·age·size·checksum·원격 저장소 read와 최근 restore evidence를 추가해야 한다.
6. **사용자 클러스터 노드 수 급감 기록을 설명해야 한다.** 최근 샘플에서 `ra-server-monitoring`, `rsip-cluster`, `ssafe-platform`, `cdep0` 등이 이전 값보다 감소했고 `amhs-sim-analysis-pr`는 상태 목록과 node 표의 존재가 다르다. 계획된 scale-down인지, `desired=ready`인지 확인 전에는 정상으로 닫지 않는다.

## 3. 조치방안

### 3.1 적용 순서

- **T-7~T-5**: inventory 고정, 인증서·토큰 D-day 계산, quota/IP/etcd 4주 추이 산출, 미확정 URL·클러스터 수량 해소.
- **T-5~T-3**: 만료 자격증명 교체, quota/IP 증설, orphan 정리, backup repository 검증과 제한된 restore 시험. 용량 변경은 실제 설치 버전에서 지원되는 경로와 승인 절차를 확인한 뒤 수행한다.
- **T-2**: 5개 인프라 클러스터와 P1 tenant의 API/etcd/storage/LB end-to-end 확인, 시험 알람 발송, Argo CD/CAPI 변경 완료.
- **T-1**: 변경 동결, 모든 표를 같은 수집 시각으로 다시 작성, 최신 backup 완료 확인, 당직자·접근 권한·복구 credential 확인, Go/No-Go 승인.
- **연휴 중**: 자동 알람에 더해 인증서 D-day, backup age, storage/IP forecast, etcd growth를 최소 일 1회 갱신한다. 실패 기준에 도달하면 승인된 runbook으로만 조치한다.

### 3.2 Go/No-Go 판정

다음 중 하나라도 충족하면 **No-Go 또는 명시적 위험 승인** 없이는 연휴 무인 운영으로 전환하지 않는다.

- Supervisor/VCFA core health에 Fail/Degraded가 있다.
- 인프라 또는 P1 tenant에서 CP/worker desired와 ready가 다르거나 API/etcd quorum이 불안정하다.
- 인증서·토큰이 연휴 중 또는 종료 후 7일 이내 만료되며 갱신·consumer 검증이 끝나지 않았다.
- 예상 종료 사용량과 복구 reserve가 Storage Policy/Zone/IP quota를 넘는다.
- 필수 backup이 일정+grace를 넘었거나 partial/failed이며 읽기·무결성 검증이 없다.
- NSX/Avi 경로, CNS/CSI provisioning/attach, Harbor push/pull, Keycloak OIDC, VictoriaMetrics ingest/query, 시험 알람 중 하나가 실패한다.
- 승인되지 않은 Argo CD sync, CAPI reconcile, upgrade, certificate rotation, node replacement가 진행 중이다.

---

# [DKS-C] `<연휴명>` 클러스터 사전 점검 보고서

## A. 문서 정보 및 최종 판정

| 항목 | 기입 값 |
|---|---|
| 연휴 기간 | `<YYYY-MM-DD HH:mm KST>` ~ `<YYYY-MM-DD HH:mm KST>` |
| 점검 기준 시각 | `<YYYY-MM-DD HH:mm:ss KST>` |
| 데이터 조회 구간 | 최근 4주: `<시작>` ~ `<종료>` |
| 점검자 / 검토자 | `<이름>` / `<이름>` |
| 대상 WLD / Supervisor | `<VCFA/vCenter에서 확인한 정확한 명칭>` / `<endpoint>` |
| 기대 인프라/사용자 클러스터 수 | `5 / 39` |
| 실제 조회 수 | `<n> / <n>` |
| 변경 동결 기간 | `<시작>` ~ `<종료>` |
| 최종 판정 | `[ ] Go  [ ] Conditional Go  [ ] No-Go` |
| 미해소 예외 승인 번호 | `<없음 또는 Change/Risk ID>` |
| 당직/에스컬레이션 연락처 | `<L1> / <L2> / <VMware·Network·Storage 연락처>` |
| 증적 보관 위치 | `<URL 또는 경로>` |

### 판정 기호

| 상태 | 의미 |
|---|---|
| `정상` | 현재 정상이고 연휴 종료+buffer까지 reserve를 충족함 |
| `주의` | 현재 서비스 영향은 없으나 운영 임계치 진입 또는 전망상 위험이 있어 연휴 전 조치/승인이 필요함 |
| `실패` | 현재 장애, 제품 하드 실패 신호, 연휴 중 실패 전망 또는 복구 증거 부재 |
| `N/A` | 소유자가 사유와 대체 통제를 승인한 비대상. 단순 미확인은 N/A가 아님 |

### 계산식

```text
D-day = floor((만료시각 - 점검시각) / 24h)
예상 종료 사용량 = 현재 사용량 + max(P95 일증가량, 최근 7일 평균 증가량, 0) × (연휴 일수 + 2일 buffer)
가용 reserve = limit - 예상 종료 사용량
ETCD quota 사용률 = dbSize / backendQuota × 100
ETCD fragmentation = (dbSize - dbSizeInUse) / dbSize × 100
IP 필요량 = 승인된 신규/재생성 클러스터 수 × 3 + 승인된 신규 LB VIP 수 + 비상 클러스터 1개분 3 IP
```

## B. 점검 URL 및 접근성

> 원칙: URL을 열었다는 사실이 아니라, 실제 인증 후 핵심 조회/API가 성공하고 인증서 D-day가 기준을 충족하는지 기록한다. 비밀번호·토큰 값은 보고서에 붙이지 않는다.

| 서비스 | URL/Endpoint | 점검 동작 | HTTP/기능 결과 | 인증서 D-day | 상태 | 증적 |
|---|---|---|---|---:|---|---|
| DKS Console | `https://console.dks.samsungds.net/` | 로그인, 클러스터 목록 조회 | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Grafana canonical | `https://grafana.dks.samsungds.net/` | 대시보드 및 datasource query | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Grafana OIDC 등록 URL | `https://grafana-dksm.dks.samsungds.net/` | canonical/redirect 관계 확인 | `<값>` | `<값>` | `<상태>` | `<링크>` |
| VictoriaMetrics VMUI | `https://vmui.dks.samsungds.net/select/0/prometheus/graph/` | 최근 metric query | `<값>` | `<값>` | `<상태>` | `<링크>` |
| VMAlert | `https://vmalert.dks.samsungds.net/vmalert/` | rule evaluation error 확인 | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Alertmanager | `https://alert-dksm.dks.samsungds.net/#/alerts` | active/silence/route 확인 | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Monitoring Health | `https://monitoring-health.dks.samsungds.net` | consumer token으로 health call | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Runbook | `https://runbook.dks.samsungds.net` | 핵심 runbook 접근 | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Keycloak | `https://keycloak.dks.samsungds.net` | OIDC discovery/login/token 검증 | `<값>` | `<값>` | `<상태>` | `<링크>` |
| OpenSearch Dashboards | `https://opensearch-dashboard.dks.samsungds.net` | 로그인, 최근 로그 검색 | `<값>` | `<값>` | `<상태>` | `<링크>` |
| OpenSearch API | `https://opensearch.dks.samsungds.net` | cluster health/snapshot query | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Harbor | `https://kh-prd-ia-mgd-harbor.samsungds.net` | health 및 시험 image pull | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Argo CD 관리 | `https://argocd-admin.samsungds.net` | app health/sync/operation | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Argo CD 사용자 | `https://argocd.samsungds.net` | app health/sync/operation | `<값>` | `<값>` | `<상태>` | `<링크>` |
| VCF Operations | `https://kh-prd-vcf01.samsungds.net` | active alarm/health | `<값>` | `<값>` | `<상태>` | `<링크>` |
| VCFA | `https://kh-prd-vcf-vcfa.samsungds.net` | project/cluster/quota 조회 | `<값>` | `<값>` | `<상태>` | `<링크>` |
| vCenter | `https://kh-prd-ia-wld01-vct.samsungds.net` | alarm, cluster/storage health | `<값>` | `<값>` | `<상태>` | `<링크>` |
| NSX Manager | `https://kh-prd-ia-wld01-nsx.samsungds.net` | Edge/T0/BGP/BFD/IPAM | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Avi Controller | `https://kh-prd-ia-wld01-avi.samsungds.net` | VS/pool/SE/VIP pool | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Package Repository | `https://kh-prd-ia-mgd-tkg.samsungds.net` | VKS/addon artifact pull | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Thanos | `<DKS-C 사용 여부/정식 URL 확인>` | DKS-N URL 재사용 금지 | `<값>` | `<값>` | `<N/A 또는 상태>` | `<근거>` |
| Supervisor API | `<context에 등록된 endpoint>` | authenticated API call | `<값>` | `<값>` | `<상태>` | `<링크>` |

## C. DKS-N 기본 8대 항목 계승 점검표

| Cluster Name | Cluster Status | Core Node | Core Pod | Prometheus/VictoriaMetrics PVC | API Server | ETCD | Alert | Note |
|---|---|---|---|---|---|---|---|---|
| `prd-dksc-ic01-khm` | `<값>` | `<ready/desired>` | `<값>` | `<max used/forecast>` | `<latency/error>` | `<3/3, quota, frag>` | `<건수>` | `<값>` |
| `prd-dksg-ic01-khm` | `<값>` | `<ready/desired>` | `<값>` | `<max used/forecast>` | `<latency/error>` | `<3/3, quota, frag>` | `<건수>` | `<값>` |
| `prd-dksl-ic01-khm` | `<값>` | `<ready/desired>` | `<값>` | `<max used/forecast>` | `<latency/error>` | `<3/3, quota, frag>` | `<건수>` | `<값>` |
| `prd-dksm-ic01-khm` | `<값>` | `<ready/desired>` | `<값>` | `<max used/forecast>` | `<latency/error>` | `<3/3, quota, frag>` | `<건수>` | `<값>` |
| `prd-dkso-ic01-khm` | `<값>` | `<ready/desired>` | `<값>` | `<max used/forecast>` | `<latency/error>` | `<3/3, quota, frag>` | `<건수>` | `<값>` |

### 기본 항목 판정 기준

| 항목 | 정상 | 주의 | 실패 |
|---|---|---|---|
| Cluster/Node | desired=ready=available, 모든 Node Ready | 계획된 drain/scale 중이나 종료 시각 명확 | CP 또는 worker ready 부족, NotReady 지속 |
| Core Pod | Pending/Failed/CrashLoop 0, 비계획 restart 증가 없음 | restart 증가 원인 조사 중 | 다중 replica 동시 장애 또는 핵심 controller 불가 |
| PVC | Pending 0, 최대 사용률 <80%, 종료 전망 reserve 충족 | 80~<90% 또는 종료 전 85% 교차 전망 | 90% 이상, Pending/provision/attach 실패, 종료 전 고갈 전망 |
| API Server | burn alert 없음, 5xx 비율 <1%, 기존 latency SLO 내 | 지연/오류 증가하나 SLO burn 미발생 | API 불가 또는 multi-window burn alert |
| ETCD | member 전부 healthy, leader 1, alarm 0, quota <70% | quota 70% 이상, frag 30% 이상, leader change 증가 | member/quorum 상실, NOSPACE, 종료 전 quota 도달 전망 |
| Alert | 미처리 Critical 0, silence 만료일 확인 | 원인·owner·종료시각 있는 경고 | owner 없는 Critical, 과도/무기한 silence, 알람 전파 실패 |

## D. VKS/Guest Cluster 확장 점검표

### D.1 5대 인프라 클러스터

| Cluster | 역할 | CAPI Ready | CP ready/desired | Worker ready/desired | MHC/remediation | CNS/CSI | Storage Policy reserve | API/LB VIP | 최소 cert D-day | Backup | 상태/증적 |
|---|---|---|---|---|---|---|---|---|---:|---|---|
| `prd-dksc-ic01-khm` | Console | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `prd-dksg-ic01-khm` | APISIX/Keycloak | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `prd-dksl-ic01-khm` | OpenSearch/Logging | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `prd-dksm-ic01-khm` | VictoriaMetrics/Grafana | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `prd-dkso-ic01-khm` | DevOps/Harbor | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |

### D.2 P1 주요 Tenant Cluster

| Priority | Cluster | 서비스/Owner | Cluster Ready | CP | Worker | API | ETCD | PVC/CNS | LB/Ingress | Quota reserve | cert D-day | Alert | 상태/증적 |
|---|---|---|---|---|---|---|---|---|---|---|---:|---|---|
| P1 | `bia-prd` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| P1 | `dsportal-prd` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| P1 | `peoplein360-prd` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| P1 | `claude-cowork` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| P1 | `cae-pcloud-prod` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| P1 | `smap-prod-cluster` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| P1 | `trip-prod` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |

### D.3 전체 사용자 클러스터 inventory 대조

> 아래 목록은 최근 로컬 일일 보고서의 39개 기준선이다. 실제 VCFA/CCI 조회 결과와 1:1 대조하고, 신규·삭제·누락 사유를 기록한다.

| 확인 | Cluster | 실제 존재 | Ready | Node desired/ready | 우선순위/Owner | 예외 |
|---|---|---|---|---|---|---|
| `[ ]` | `bia-dev` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `bia-prd` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `biz-cicd` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `biz-dev` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `cae-pcloud-prod` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `canvas` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `cdep0` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `claude-cowork` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `claude-cowork-poc` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `claude-cowork-research` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `dbrgdev01` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `devops-learning` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `dks-magician-ax` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `dsportal-dev` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `dsportal-prd` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `exe-eye-dev` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `genai-platform` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `hynix-analysis` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `iotagent-dev` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `kua-rag-dev` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `nescafe1` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `peoplein360-prd` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `poc-pipeline` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `ra-server-monitoring` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `ragent-system` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `rsip-cluster` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `skt-challenge-prod` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `smap-dev-cluster` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `smap-prod-cluster` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `ssafe-platform` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `ssam` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `test-cluster` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `test-cluster2` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `test-graphrag` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `teleop` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `test-vks1` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `trip-prod` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `workflow-1` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| `[ ]` | `workflow-2` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |

## E. VCFA Supervisor 및 Platform 확장 컴포넌트

### E.1 Supervisor/VCFA health

| Component/검사 | 기대값 | 관측값 | 마지막 정상 시각 | 상태 | 증적/비고 |
|---|---|---|---|---|---|
| Supervisor Config Status | `Running` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| Supervisor Host Config Status | `Running` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-statefulsets-core` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-api-server-core` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-control-plane-core` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-daemonsets-core` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-networking-daemonsets-core` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `vksm-services-prelude-deployments-core` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `vksm-services-prelude-pods-core` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-snapshots-snapshot` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-storage-capacity-prom` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-vmsp-platform-sftp` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-node-disk-utilization-prom` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-opsmgmt-dns` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-etcd-core` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-machines-core` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |
| `platform-vc-serviceaccount-http` | `OK` | `<값>` | `<값>` | `<상태>` | `<링크>` |

### E.2 CCI/CAPI 일관성

| 검사 | 기대값 | 관측값 | 상태 | 증적/조치 |
|---|---|---|---|---|
| Project / ProjectRoleBinding | dangling binding 0 | `<값>` | `<상태>` | `<값>` |
| VPC / Namespace / Cluster 1:1:1 | 불일치 0 | `<값>` | `<상태>` | `<값>` |
| Cluster/ControlPlane/MachineDeployment Conditions | `Ready=True` | `<값>` | `<상태>` | `<값>` |
| Machine Provisioning/Deleting age | 장기 고착 0 | `<값>` | `<상태>` | `<값>` |
| MachineHealthCheck remediation | 진행/실패 0 | `<값>` | `<상태>` | `<값>` |
| `VPCLimitState` vs 실제 소비량 | 차이 0 | `<값>` | `<상태>` | `<값>` |
| `IPBlockUsage` vs 실제 External IP | 차이 0 | `<값>` | `<상태>` | `<값>` |
| `StoragePolicyQuota` vs vCenter 사용량 | 허용 오차 내 일치 | `<값>` | `<상태>` | `<값>` |
| Zone CRD vs 실제 배치 | 누락/쏠림 없음 | `<값>` | `<상태>` | `<값>` |
| Argo CD 관리/사용자 App | `Healthy/Synced`, operation 0 | `<값>` | `<상태>` | `<값>` |

### E.3 VCF/vCenter/NSX/Avi 기반 인프라

| 계층 | 점검 항목 | 기대값 | 관측값 | 상태 | 증적/조치 |
|---|---|---|---|---|---|
| VCF | active alarm / precheck | 미해소 critical 0 | `<값>` | `<상태>` | `<값>` |
| vCenter | service/DB/cluster alarm | healthy, critical 0 | `<값>` | `<상태>` | `<값>` |
| ESXi/Zone | host/HA/DRS/N+1 reserve | 비상 실패 1건 수용 | `<값>` | `<상태>` | `<값>` |
| NSX Manager | cluster health | healthy | `<값>` | `<상태>` | `<값>` |
| NSX Edge/T0 | node, BGP/BFD, uplink | all Up | `<값>` | `<상태>` | `<값>` |
| Avi | Controller/SE health | healthy | `<값>` | `<상태>` | `<값>` |
| Avi | VS/pool member | 필수 VS Up, member healthy | `<값>` | `<상태>` | `<값>` |
| DNS | 핵심 FQDN 정/역방향 | 성공 | `<값>` | `<상태>` | `<값>` |
| NTP | vCenter/ESXi/NSX/Supervisor/Guest | synchronized | `<값>` | `<상태>` | `<값>` |

## F. Storage Policy, Region/Zone Quota 및 CNS/CSI

### F.1 Region/Zone 자원

| Region | Resource | Zone/Policy | Limit | Used | Provisioned | 4주 P95 일증가 | 종료+2일 예상 | 복구 reserve | 판정 | 증적 시각/원천 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| `<확정 WLD01-region01>` | CPU | `kh-prd-ia-wld01-az01` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` | `<값>` |
| `<확정 WLD01-region01>` | CPU | `kh-prd-ia-wld01-az02` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` | `<값>` |
| `<확정 WLD01-region01>` | CPU | `kh-prd-ia-wld01-az03` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` | `<값>` |
| `<확정 WLD01-region01>` | Memory | `kh-prd-ia-wld01-az01` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` | `<값>` |
| `<확정 WLD01-region01>` | Memory | `kh-prd-ia-wld01-az02` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` | `<값>` |
| `<확정 WLD01-region01>` | Memory | `kh-prd-ia-wld01-az03` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` | `<값>` |
| `<확정 WLD01-region01>` | Storage | `vks-pf-storage-policy` | `60 TB` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` | `<값>` |
| `<확정 WLD01-region01>` | Storage | `vks-pf-storage-policy-admin` | `50 TB` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` | `<값>` |
| `<확정 WLD01-region01>` | Storage | `vks-pf-storage-policy-data` | `15 TB` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` | `<값>` |

### F.2 CNS/CSI 기능 점검

| 검사 | 대상/결과 | 정상 기준 | 상태 | 증적/조치 |
|---|---|---|---|---|
| CSI controller replicas | `<값>` | desired=ready | `<상태>` | `<값>` |
| CSI node coverage | `<값>` | schedulable node 전부 Ready | `<상태>` | `<값>` |
| Pending PVC | `<값>` | 0 | `<상태>` | `<값>` |
| VolumeAttachment 오류 | `<값>` | 0 | `<상태>` | `<값>` |
| CNS volume health | `<값>` | inaccessible/degraded 0 | `<상태>` | `<값>` |
| 시험 PVC provision | `<cluster/policy/result>` | 제한 시간 내 Bound | `<상태>` | `<값>` |
| 시험 Pod mount/read/write | `<결과>` | 성공 | `<상태>` | `<값>` |
| 시험 snapshot/restore | `<결과>` | 성공 | `<상태>` | `<값>` |
| orphan/stale volume | `<값>` | 승인되지 않은 orphan 0 | `<상태>` | `<값>` |

### F.3 External IPBlock/VPC/Avi IPAM

| Pool/Block | 용도 | Total | Allocated | Available | 사용률 | 연휴 승인 수요 | 비상 reserve | 종료 예상 Available | 상태/증적 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `<External IPBlock명>` | VPC SNAT/LB | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `>=3` | `<값>` | `<값>` |
| `<Avi VIP Pool명>` | API/Ingress VIP | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<정책값>` | `<값>` | `<값>` |
| `<Namespace/Pod IPBlock>` | Pod/Namespace | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<정책값>` | `<값>` | `<값>` |

## G. 인증서, OIDC 및 API Token D-day

> 모든 날짜는 KST로 통일하고 `문서상의 날짜`, `Kubernetes Secret`, `Certificate status`, `실제 endpoint가 제공한 인증서`를 구분한다. 갱신 성공은 Secret 생성만으로 닫지 않고 실제 TLS/OIDC/API 호출로 확인한다.

| 구분 | 대상 | Namespace/소비자 | Issuer/발급원 | notAfter/exp | D-day | renewalTime | Ready | 실제 served/consumer 검증 | 판정/조치 |
|---|---|---|---|---|---:|---|---|---|---|
| Supervisor extension | `storage-quota-extension-cert` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| Supervisor extension | `storage-quota-serving-cert` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| Supervisor webhook | `storage-quota-webhook-internal-serving-cert` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| Supervisor issuer | `storage-quota-selfsigned-issuer-cert` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| Supervisor runtime | `runtime-extension-serving-cert` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| Supervisor VIP/API | `<443/6443 인증서>` | 외부/내부 API | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| VKS | `<cluster별 최소 D-day 집계>` | 5 infra + 39 tenant | VMware/VKS | `<값>` | `<값>` | `<값>` | `<값>` | API/etcd/kubelet TLS | `<값>` |
| cert-manager | `<Certificate 전체>` | 전체 namespace | `<Issuer>` | `<최소값>` | `<값>` | `<cohort>` | `<값>` | `<값>` | `<값>` |
| Platform | OpenSearch node cert 8개 | `prd-dksl-ic01-khm` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | node transport health | `<값>` |
| Platform | Monitoring/addon agent cert | infra/tenant | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | ingest 성공 | `<값>` |
| Token | `console-token` | Console 연동 | `<발급원>` | `<값>` | `<값>` | N/A | `<값>` | 실제 Console API 2xx | `<값>` |
| OIDC | `dkssol-console-longterm-client` | P-DEP health check | Keycloak | `<JWT exp>` | `<값>` | N/A | `<값>` | Console/OpenSearch/VM call | `<값>` |
| OIDC | `k8s-longterm-client*` | cluster 자동화 | Keycloak | `<JWT exp>` | `<값>` | N/A | `<값>` | 실제 kube API call | `<값>` |
| OIDC | `grafana-oauth` | Grafana | Keycloak | `<설정/세션>` | `<값>` | N/A | `<값>` | browser login | `<값>` |
| OIDC | `opensearch-dashboard-oauth` | OpenSearch Dashboards | Keycloak | `<설정/세션>` | `<값>` | N/A | `<값>` | browser login | `<값>` |
| Registry | Harbor TLS | image pull/push | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | 시험 pull | `<값>` |

### 동시 갱신 cohort

| 24시간 구간 | 인증서 수 | 같은 HA 서비스 replica 수 | Issuer 상태/과거 처리량 | 자동 reload 증거 | 연휴 영향 | 분산/선행 갱신 계획 |
|---|---:|---:|---|---|---|---|
| `<구간>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |

## H. 백업 및 스냅샷

### H.1 백업 실행·무결성·복구성

| 대상 | 기준 주기 | 최신 성공 시각 | Age | 실행 상태 | Artifact/Size/Checksum | 원격 저장소 read | 최근 restore 검증 | RPO/RTO 충족 | 상태/조치 |
|---|---|---|---|---|---|---|---|---|---|
| `logs-hub` OpenSearch snapshot | 1일 | `<값>` | `<값>` | `<SUCCESS>` | `<값>` | `<값>` | `<날짜/결과>` | `<값>` | `<값>` |
| `metric-hub` | 1일 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<날짜/결과>` | `<값>` | `<값>` |
| `Console-db` PostgreSQL | 1시간 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<날짜/결과>` | `<값>` | `<값>` |
| `Keycloak-db` PostgreSQL | 1시간 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<날짜/결과>` | `<값>` | `<값>` |
| `Apisix-etcd` | 1시간 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<날짜/결과>` | `<값>` | `<값>` |
| vCenter file-based backup | `<정책>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<날짜/결과>` | `<값>` | `<값>` |
| Supervisor Control Plane 포함 | vCenter backup 연계 | `<값>` | `<값>` | `<포함 여부>` | `<값>` | `<값>` | `<날짜/결과>` | `<값>` | `<값>` |
| Velero BSL | 지속 | `<값>` | `<값>` | `Available` | `<값>` | `<값>` | `<날짜/결과>` | `<값>` | `<값>` |
| P1 tenant Velero Backup | `<정책>` | `<값>` | `<값>` | `<Completed>` | `<값>` | `<값>` | `<날짜/결과>` | `<값>` | `<값>` |

권장 허용 지연은 시간당 backup `<2시간`, 일일 backup `<26시간`이다. 실제 cron 시각과 예상 소요시간이 더 엄격하면 그 값을 우선한다. `PartiallyFailed`는 성공으로 집계하지 않는다.

### H.2 APISIX/Control Plane etcd snapshot

| 대상 | Endpoint health | Member healthy | Leader | Alarm | Snapshot age | Revision/Hash 검증 | Off-cluster copy | Restore evidence | 상태 |
|---|---|---|---|---|---|---|---|---|---|
| APISIX etcd | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| Supervisor etcd/backup | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |
| VKS critical cluster aggregate | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |

## I. 심층 추이

### I.1 ETCD Defrag/Quota 4주 추이

| Cluster | Member | 주차/시각 | dbSize | dbSizeInUse | Quota | Quota 사용률 | Fragmentation | 일증가량 | 종료 예상 | Alarm/Leader change | 판정 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `<cluster>` | `<member>` | W-4 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |
| `<cluster>` | `<member>` | W-3 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |
| `<cluster>` | `<member>` | W-2 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |
| `<cluster>` | `<member>` | W-1 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |
| `<cluster>` | `<member>` | 현재 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |

- Defrag 후보 조건: fragmentation이 지속적으로 높고 회수 가능 바이트가 유의미하며 snapshot이 검증된 경우.
- Defrag는 단순 퍼센트만으로 자동 실행하지 않는다. 해당 member의 읽기/쓰기를 잠시 막을 수 있으므로 leader/quorum, 트래픽, backup을 확인하고 **한 member씩** 수행하는 별도 작업계획과 승인을 적용한다.

### I.2 Storage Policy 잔여량/소진 속도 4주 추이

| Policy | W-4 Used/Provisioned | W-3 | W-2 | W-1 | 현재 | P95 일증가 | 종료+2일 예상 | Limit까지 남은 일수 | 복구 reserve | 판정 |
|---|---|---|---|---|---|---:|---:|---:|---:|---|
| `vks-pf-storage-policy` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |
| `vks-pf-storage-policy-admin` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |
| `vks-pf-storage-policy-data` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |

### I.3 Token 만료 위험

| Token/Secret | 실제 소비자 | 실제 `exp` | D-day | 연휴 중 호출 빈도 | 교체 가능 창 | 신규 토큰 발급 | dual-run/rollback | 실제 호출 검증 | 폐기 시각 | 판정 |
|---|---|---|---:|---|---|---|---|---|---|---|
| `console-token` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |
| `<long-term token>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<상태>` |

### I.4 External IP 소진 속도

| Block | W-4 Available | W-3 | W-2 | W-1 | 현재 | 승인된 연휴 수요 | 비상 reserve | 종료 예상 | Limit/Usage 일치 | 판정 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `<External IPBlock>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `>=3` | `<값>` | `<값>` | `<상태>` |

## J. 핵심 서비스 기능 점검

| 서비스 | 기능 검사 | 정상 기준 | 관측값 | 상태 | 증적/조치 |
|---|---|---|---|---|---|
| Keycloak | OIDC discovery/login/token refresh | 성공, issuer/clock 일치 | `<값>` | `<상태>` | `<값>` |
| APISIX | 외부 route/auth 및 backend reachability | 2xx/기대 응답, route sync 정상 | `<값>` | `<상태>` | `<값>` |
| OpenSearch | cluster health | green, unassigned primary 0 | `<값>` | `<상태>` | `<값>` |
| OpenSearch | disk watermark | low/high/flood-stage 미도달 | `<값>` | `<상태>` | `<값>` |
| OpenSearch | snapshot repository | verify 성공, 최신 snapshot SUCCESS | `<값>` | `<상태>` | `<값>` |
| VictoriaMetrics | ingest/query/HA replica | 최근 sample 수집·query, HA 정상 | `<값>` | `<상태>` | `<값>` |
| Alert chain | rule → Alertmanager → dispatcher → P-DEP | 시험 알람 수신 및 resolve 확인 | `<값>` | `<상태>` | `<값>` |
| Harbor | `/api/v2.0/health` | healthy | `<값>` | `<상태>` | `<값>` |
| Harbor | image pull/push/job queue/storage | 성공/정체 없음/reserve 충족 | `<값>` | `<상태>` | `<값>` |
| Console DB | connection/replication/space | 정상, 연휴 reserve 충족 | `<값>` | `<상태>` | `<값>` |
| NATS/DevOps | queue/consumer/DinD capacity | backlog 비정상 증가 없음 | `<값>` | `<상태>` | `<값>` |
| Logs/metrics/events agents | tenant coverage/last sample | 기대 39개 전부 최근 수집 | `<값>` | `<상태>` | `<값>` |

## K. Alert, Silence 및 변경 동결

### K.1 Alert/Silence

| Severity | Alert | 대상 | 시작 | 원인 | Owner | 조치/완료 예정 | 연휴 영향 | 상태 |
|---|---|---|---|---|---|---|---|---|
| `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |

| Silence | Matcher/대상 | 사유 | 생성자 | 시작/만료 | 대체 감시 | 승인 | 상태 |
|---|---|---|---|---|---|---|---|
| `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |

### K.2 진행 중 변경

| 변경/Operation | 대상 | 현재 단계 | 시작 | 종료 예정 | Rollback | Owner | 연휴 전 완료 증거 | 상태 |
|---|---|---|---|---|---|---|---|---|
| `<CAPI/Argo/upgrade/rotation>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` |

## L. 발견사항 및 조치 등록부

| ID | 점검 항목 | 관측값 | 기준/영향 | 연휴 전 조치 | Owner | Due | 완료 증적 | 잔여 위험/승인 | 상태 |
|---|---|---|---|---|---|---|---|---|---|
| HC-001 | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<값>` | `<Open/Closed>` |

## M. 최종 승인

### 필수 gate

- [ ] 기대 인프라 5개와 사용자 39개의 inventory 대조가 완료되었다.
- [ ] Supervisor/VCFA core health가 모두 `OK`이다.
- [ ] 모든 CP/worker가 desired=ready이며 진행 중 CAPI remediation이 없다.
- [ ] API, etcd quorum, CNS/CSI 시험, NSX/Avi 외부 경로가 정상이다.
- [ ] 연휴 종료+7일 이내 인증서/토큰 만료가 없고, 종료+30일 이내 대상은 갱신 계획과 owner가 있다.
- [ ] Storage/CPU/Memory/IP의 종료 예상량과 복구 reserve가 limit 안에 있다.
- [ ] 필수 backup이 일정+grace 내 성공했고 artifact read·무결성·최근 restore 증거가 있다.
- [ ] Keycloak, APISIX, OpenSearch, VictoriaMetrics, Harbor, Console 핵심 기능 검사가 성공했다.
- [ ] 시험 알람이 최종 수신자까지 전달되고 resolve되었다.
- [ ] 진행 중인 upgrade/sync/rotation/node replacement가 없으며 변경 동결이 발효되었다.
- [ ] 미해소 `주의/실패` 항목은 영향, 대체 통제, 만료 시각, 승인자가 기록되었다.
- [ ] 당직자가 Bastion/VCF/VCFA/vCenter/NSX/Avi/Supervisor/K8s/backup 저장소에 실제 로그인했다.

| 역할 | 이름 | 판정 | 시각 | 서명/승인 링크 |
|---|---|---|---|---|
| 점검 수행 | `<값>` | `<값>` | `<값>` | `<값>` |
| Kubernetes 운영 | `<값>` | `<값>` | `<값>` | `<값>` |
| VMware/Network/Storage | `<값>` | `<값>` | `<값>` | `<값>` |
| 최종 승인 | `<값>` | `<Go/Conditional Go/No-Go>` | `<값>` | `<값>` |

---

## 기술 근거

### 공식 자료

1. Broadcom, [Master vSphere Supervisor Certificate Guide](https://knowledge.broadcom.com/external/article/323421/master-vsphere-supervisor-certificate-gu.html) — Supervisor API/내부/웹훅 등 인증서 계층을 분리해 점검해야 하는 근거.
2. Broadcom, [Managing TLS Certificates for TKG Service Clusters](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere-supervisor/8-0/using-tkg-service-with-vsphere-supervisor/managing-security-for-tkg-service-clusters/managing-tls-certificates-for-tkg-service-clusters.html) — workload cluster 인증서 inventory와 수명주기 점검 근거.
3. Broadcom KB 387476, [ESXi nodes become NotReady after rotating Supervisor certificates](https://knowledge.broadcom.com/external/article/387476/esxi-nodes-become-notready-after-rotatin.html) — 인증서 회전과 시간 동기화/NotBefore 오류가 Supervisor node readiness에 미치는 영향.
4. cert-manager, [Certificate resource](https://cert-manager.io/docs/usage/certificate/) — `notAfter`, `renewalTime`, Secret 갱신 상태를 확인하는 근거.
5. etcd, [Maintenance](https://etcd.io/docs/v3.5/op-guide/maintenance/) — quota, compaction, defragmentation, snapshot 및 member 단위 defrag 주의사항.
6. Prometheus Operator Runbooks, [etcdInsufficientMembers](https://runbooks.prometheus-operator.dev/runbooks/etcd/etcdinsufficientmembers/), [etcdNoLeader](https://runbooks.prometheus-operator.dev/runbooks/etcd/etcdnoleader/), [KubeAPIErrorBudgetBurn](https://runbooks.prometheus-operator.dev/runbooks/kubernetes/kubeapierrorbudgetburn/) — etcd quorum/leader와 API error-budget 경보 근거.
7. Broadcom KB 391096, [PVC creation might fail with insufficient storage quota](https://knowledge.broadcom.com/external/article/391096/pvc-creation-might-fail-with-error-opera.html) — StoragePolicyQuota 불일치/고갈이 PVC 생성을 거부하는 실패 경로.
8. Broadcom KB 407628, [vSphere Supervisor Workload Cluster Load Balancer Service External IP Pending](https://knowledge.broadcom.com/external/article/407628/vsphere-supervisor-workload-cluster-load.html) — Avi/NSX IP 풀 고갈 시 LB `EXTERNAL-IP Pending`이 되는 근거.
9. Broadcom KB 436645, [VKS guest cluster fails to deploy: NSX IP block exhausted](https://knowledge.broadcom.com/external/article/436645/vks-guest-cluster-fails-to-deploy-nsx-ip.html) — NSX IPBlock 고갈이 cluster realize를 막는 근거.
10. Broadcom, [Backup and Restore the Supervisor Control Plane](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere-supervisor/8-0/backing-up-and-restoring-vsphere-supervisor/backup-and-restore-the-supervisor-control-plane.html) 및 [Considerations](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere-supervisor/8-0/backing-up-and-restoring-vsphere-supervisor/considerations-for-backing-up-and-restoring-vsphere-iaas-control-plane.html) — vCenter file-based backup의 Supervisor 포함 여부와 workload data 별도 백업 필요성.
11. Velero, [BackupStorageLocation](https://velero.io/docs/v1.18/api-types/backupstoragelocation/) — BSL availability와 backup 저장소 접근성 점검 근거.
12. OpenSearch, [Get snapshot status](https://docs.opensearch.org/latest/api-reference/snapshots/get-snapshot-status/) 및 [Take and restore snapshots](https://docs.opensearch.org/latest/tuning-your-cluster/availability-and-recovery/snapshots/snapshot-restore/) — snapshot 상태·repository·restore 검증 근거.
13. Argo CD, [Application Health](https://argo-cd.readthedocs.io/en/stable/operator-manual/health/) 및 [Notifications triggers](https://argo-cd.readthedocs.io/en/stable/operator-manual/notifications/triggers/) — `Healthy/Synced/Progressing/Degraded`와 operation 상태 점검 근거.
14. Cluster API, [MachineHealthCheck](https://cluster-api.sigs.k8s.io/tasks/automated-machine-management/healthchecking) — unhealthy Machine remediation와 control-plane quorum 고려 근거.
15. Keycloak, [Health checks](https://www.keycloak.org/observability/health) — `/health`, `/health/ready`, `/health/live` 기능 검증 근거.
16. Harbor, [Access Metrics](https://goharbor.io/docs/latest/administration/metrics/) — registry component health, storage, job queue 관측 근거.

### 로컬 교차 검증 자료

- `00. DKS-C 아키텍처 전체 이해 가이드.md`
- `DKS-C 운영 현황 요약.md`
- `VCFA CCI CRDs 및 Quota 가이드.md`
- `DKS-C 인증서 갱신 기간 및 현황.md`
- `VCF CLI 및 접근 운영 정보.md`
- `DKS-C SW 아키텍처 및 기술 스택.md`
- `DKS Keycloak 연계 정보.md`
- `모니터링/DKS 일일 모니터링 보고서 샘플.md`
