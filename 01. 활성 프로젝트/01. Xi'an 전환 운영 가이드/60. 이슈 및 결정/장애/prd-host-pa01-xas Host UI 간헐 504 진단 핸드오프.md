---
title: prd-host-pa01-xas Host UI 간헐 504 진단 핸드오프
created: 2026-07-10
updated: 2026-07-10
status: review
case_status: investigating
type: incident-handoff
tags:
  - xi'an
  - prd-host-pa01-xas
  - 504
  - ingress-nginx
  - router
  - host-cluster
  - triage
aliases:
  - Host 간헐 504
  - Xi'an Host 504 진단
  - ingress-nginx 504 핸드오프
parent: "[[60. 이슈 및 결정/이슈 및 결정 안내|이슈 및 결정 안내]]"
related:
  - "[[10. 기준 및 설계/클러스터 카탈로그/01. prd-host-pa01-xas|prd-host-pa01-xas]]"
  - "[[30. 구축 및 전환/Host 클러스터/개요|Host 클러스터]]"
doc_type: guide
scope: "Xi'an 전환 운영 가이드"
---

# prd-host-pa01-xas Host UI 간헐 504 진단 핸드오프

> [!todo] 다음 출근 시 바로 이어서 할 것
> 1. 문제 ingress-controller Pod 이름 / 배치 Router 노드 재확인
> 2. 해당 controller 504 로그에서 `upstream_addr`, `while connecting|reading`, `request_time` 확보
> 3. **정상 Router vs 문제 Router**에서 동일 `upstream_addr`로 `ip route get` + `nc -vz` 비교
> 4. 결과로 아래 판정 표 채우기
> 5. 조치(재시작/route 변경/timeout 튜닝)는 표 채운 뒤에만

---

## 1. 환경

| 항목 | 값 |
|---|---|
| Cluster | `prd-host-pa01-xas` |
| Bastion | `xadksbthm01` |
| Router | `xadksrthm01` / `xadksrthm02` / `xadksrthm03` |
| Router IP | `109.156.22.47` / `109.156.22.48` / `109.156.22.49` |
| Domain base | `*.xaprdpa01.mgmt.dks.samsungds.net` |
| Console | `ks-console.xaprdpa01.mgmt.dks.samsungds.net` |
| Prometheus | `prometheus.xaprdpa01.mgmt.dks.samsungds.net` |
| Alertmanager | `alertmanager.xaprdpa01.mgmt.dks.samsungds.net` |
| Grafana | `grafana.xaprdpa01.mgmt.dks.samsungds.net` (원문 없는 별도 Ingress 가능) |

도메인 확정:

```bash
kubectl get ingress -A
```

문서 루트:

- Host Cluster: `30. 구축 및 전환/Host 클러스터/`
- Bundle: `~/SCS_DKS_Kubernetes_Stack-v1.0/`

---

## 2. 문서·게시 작업 상태 (이 이슈와 별 트랙)

| 항목 | 내용 | 상태 |
|---|---|---|
| 5.1.1.6 RoleBase | SCS host YAML apply + ks-apiserver/ks-controller-manager restart | 문서·게시 완료 |
| 5.1.1.7 Prometheus | retention 30d, externalLabels 클러스터별 | 문서·게시 완료 |
| 5.1.1.8 Custom rules | Sensor 일부만 반영, 풀 원문(~4만자) 미확보 | 미완료 (504와 직접 무관) |
| 5.1.1.10 Alertmanager | Secret 선적용, ns=`kubesphere-monitoring-system` | 문서·게시 완료 |
| 개요 Index | 05.1 Host Cluster 반영 상태 갱신 | 완료 |
| Blogger | RoleBase / Prometheus / Alertmanager / 504 관련 메모 게시 | 완료 |

Blogger 관련 글:

- [Xi’an Host 현황 전체 정리 + 간헐 504 트리아지](https://0310muro.blogspot.com/2026/07/xian-host-504.html)
- [Pod IP 타임아웃은 라우팅 문제 (스킵)](https://0310muro.blogspot.com/2026/07/xian-host-504-pod-ip.html)
- [ingress-nginx가 504를 생성한 경우](https://0310muro.blogspot.com/2026/07/xian-host-504-ingress-nginx-504.html)

---

## 3. 증상

- Console / Prometheus / Grafana / Alertmanager UI가 **됐다가 안 됐다가** 함
- 안 될 때 브라우저/게이트웨이에 **504 Gateway Timeout**
- 완전 다운 아님. 재시도/기다리면 다시 됨
- 앱 네 종이 같이 영향 → 개별 앱보다 **공유 진입 경로** 쪽이 1순위였음

경로:

```text
사용자
  → VIP / LB
  → Router (xadksrthm01~03)
  → ingress-nginx-controller (Router당 1개 배치)
  → SVC → App Pod
```

---

## 4. 지금까지 확인된 사실 (중요)

| # | 사실 | 의미 |
|---|---|---|
| 1 | 네 UI 동시 간헐 504 | 공유 경로 우선 |
| 2 | Pod Running / EP 정상만으로 설명 안 됨 | “살아 있음” ≠ 요청 성공 |
| 3 | bastion → controller **Pod IP** curl = Connection timeout | **장애 아님**. bastion에 Pod CIDR 라우팅 없음. Pod IP 직접 테스트 **스킵** |
| 4 | **ingress-nginx 로그에 504 존재** | 해당 건은 **ingress가 504를 생성**. VIP/LB가 만든 504가 아님 (그 건 기준) |
| 5 | **특정 ingress-controller 하나에서만 504** | 전역 설정/전 클러스터 장애 아님. 그 controller 또는 그 Router 노드 문제 |
| 6 | Router마다 controller **1개씩** 배치 | 배치 불균형/`externalTrafficPolicy` 가설 우선순위 낮음 |
| 7 | 메인 NIC default metric 낮음, Data LIF NIC는 후순위 default + 전용 route | 정상 설계라면 후순위 default 자체는 무죄 쪽 |
| 8 | Router 3번에 과거 **default metric 역전** 이력 있음 (Data default가 우선된 적 있음). `ip route del`로 정리 | 최초 트리거 후보 |
| 9 | 현재 route 확인 시 **삭제한 상태로 정상** | 지금 계속 잘못된 default가 박혀 있는 상태는 아님 |
| 10 | route 완전 꼬였을 때는 Pod가 안 떴음. **지금은 Pod 기동 정상** | 완전 단절 상태는 해소됨. 간헐 경로 문제는 남을 수 있음 |
| 11 | **문제 controller Pod delete 후에도 동일 증상** | controller 프로세스/cache 일회성 문제 **아님**. **노드 데이터플레인** 쪽으로 이동 |

---

## 5. 현재 판단 (미확정 원인, 범위는 좁음)

> [!important] 현재 triage 결론
> **특정 Router 노드(유력: route 이력이 있던 쪽, 3번 재확인 필요)의 host network data plane 문제.**
> 그 노드 위의 ingress-controller만 backend로 갈 때 간헐 timeout → ingress가 504 생성.
> Pod delete로 안 고쳐지므로 원인 위치는 **Pod 밖 = 노드 커널/CNI/conntrack/iptables/NIC 쪽**.

### 가설 순위 (2026-07-10 기준)

1. **문제 Router의 ingress → Backend Pod IP 경로 불량** (CNI route, conntrack, iptables, drop)
2. **과거 default route 역전의 잔재** (route는 정상인데 데이터플레인/상태가 덜 복구됨) — 가능성 있음, 현재 default 오설정 지속은 아님
3. **문제 controller만 잘못된/stale `upstream_addr` 사용** — Pod delete 후에도 동일하면 우선순위 하락, 그래도 로그로 한 번 확인 필요
4. VIP/LB, 전체 KubeSphere, 앱 공통 장애 — **해당 504 건 기준 후순위/제외 쪽**

### 제외하거나 우선순위 낮춘 것

| 가설 | 이유 |
|---|---|
| bastion Pod IP timeout = 장애 | 라우팅 없음 |
| ClusterIP로 controller 분리 | kube-proxy 분산되어 분리 안 됨 |
| 후순위 Data default route (정상 metric) | 구체 route + 낮은 metric main이 우선 |
| 외부 유입 대표 IP 대역 ACL 차이 | 같은 서브넷/대역 개방 전제 |
| controller 일회성 cache (Pod delete로 해결) | delete 후에도 동일 |
| VIP/LB가 해당 504를 만듦 | ingress access/error에 504 확인됨 |

---

## 6. 라우팅 이슈 정리 (Router 3 이력)

정상 의도:

```text
default via MAIN-GW  dev MAIN-NIC  metric 100
default via DATA-GW  dev DATA-NIC  metric 1001
+ Data LIF 대역용 구체 route (DATA-NIC)
```

장애 시 관측(사용자 진술):

- Data default metric `1001`
- Main default metric이 더 높아짐 → **Data default가 사실상 우선**
- `ip route del`로 Data default 제거 후 사용
- 완전 꼬였을 때: Pod 기동 실패
- 현재: route는 정상 쪽, Pod도 뜸, 하지만 **특정 controller만 간헐 504 지속**

해석:

- 과거 route 역전은 **초기 트리거/노드 불안정 이력**으로 남김
- 현재 지속 504의 직접 원인이 “지금 이 순간 잘못된 default”일 가능성은 낮음
- 그래도 문제 노드가 3번이면 **route 이력과 같은 노드**이므로 우연 취급 금지
- NetworkManager 등이 route를 다시 올릴 수 있으니 default 재확인은 유지

---

## 7. 다음 출근 체크리스트 (읽기 전용 우선)

### 7-1. 문제 인스턴스 고정

```bash
kubectl -n ingress-nginx get pod -o wide
```

- 어느 Pod가 문제 controller인지
- 어느 Router 노드인지 (`NODE` 열)
- Router 3번(`xadksrthm03` / `109.156.22.49`)과 일치하는지

### 7-2. 504 로그 한 줄 확보 (가장 중요)

```bash
kubectl logs -n ingress-nginx <문제-controller-pod> --since=1h \
  | grep -C 3 -E ' 504 |upstream timed out|no live upstreams|connect\(\) failed'
```

기록할 필드:

- 시각
- Host / request URI
- `upstream_addr` (Backend Pod IP:PORT)
- `upstream_status`
- `request_time` / `upstream_response_time`
- 문구: `while connecting to upstream` vs `while reading response header from upstream`

| 로그 문구 | 다음 방향 |
|---|---|
| `while connecting to upstream` | 노드 → Backend Pod TCP 경로 |
| `while reading response header from upstream` | 연결 후 응답 경로/지연 |
| `no live upstreams` / Endpoint miss | controller 설정/Endpoint 반영 |
| 여러 UI·여러 upstream_addr가 그 노드에서만 | 노드 공통 데이터플레인 |
| 특정 upstream_addr만 | 그 Backend Pod/노드 경로 |

### 7-3. 정상 Router vs 문제 Router — 동일 upstream 비교 (결정적)

504에 나온 `BACKEND_POD_IP` / `PORT` 사용.

**문제 Router 노드에서:**

```bash
ip route get <BACKEND_POD_IP>
nc -vz -w 3 <BACKEND_POD_IP> <PORT>
ip -4 route show default
ip -4 rule show
conntrack -S 2>/dev/null || cat /proc/net/stat/nf_conntrack
ip -s link
```

**정상 Router 노드에서 동일 명령:**

```bash
ip route get <BACKEND_POD_IP>
nc -vz -w 3 <BACKEND_POD_IP> <PORT>
ip -4 route show default
```

판정:

| 결과 | 의미 |
|---|---|
| 정상 OK, 문제 Router만 timeout | **그 Router 노드 데이터플레인 문제 확정** |
| 둘 다 OK인데 ingress만 504 | 패킷 손실/간헐, 또는 요청 시점 상태 변화 — 반복 측정 |
| 특정 Backend만 문제 Router에서 실패 | 그 Backend 노드로의 경로 |
| `ip route get`이 DATA-GW/DATA-NIC로 감 | 현재도 라우팅 직접 원인 가능 |

### 7-4. (선택) API Server 경로

과거 watch lost와 연관 확인:

```bash
ip route get <API-SERVER-IP>
```

API 경로가 Data NIC로 빠지면 watch 불안정 → Endpoint 반영 이상 가능.  
다만 Pod delete 후에도 동일하면 **단순 watch cache만**은 설명력 약함.

### 7-5. 아직 안 한 것 / 제약

| 항목 | 상태 |
|---|---|
| bastion Pod IP curl | 스킵 (라우팅 없음) |
| NodePort 외부 비교 | 방화벽으로 불가 |
| port-forward 장시간 | 미실행/미보고 (앱 완전 배제용, 현재 우선순위 낮음) |
| VIP 100회 수치 로그 | 체감만 |
| Router 3대 반복 curl 수치 로그 | 부분 확인(한 controller만 504) 수준, 파일 수치 미정리 가능 |

---

## 8. 판정 표 (출근 후 채우기)

| 구간 | 결과 | 판정 |
|---|---|---|
| 문제 controller 노드 이름 | ? | Router N 고정 |
| ingress 로그에 504 | **있음** | ingress 생성 확정 |
| 한 controller만 504 | **있음** | 전역 아님 |
| Pod delete 후 동일 | **동일** | 노드 쪽 |
| 504 `upstream_addr` | ? | |
| connecting vs reading | ? | |
| 정상 Router `nc` 동일 IP | ? | |
| 문제 Router `nc` 동일 IP | ? | |
| 현재 default route (문제 노드) | 정상으로 확인됨 (재확인) | |
| conntrack drop 증가 | ? | |

---

## 9. 조치 후보 (지금은 하지 말 것 / 표 채운 뒤)

> [!warning] 계층 확정 전 금지에 가까운 것
> - 전 구간 timeout annotation 무작정 상향 (증상 가림)
> - 전체 ingress/KubeSphere 재설치
> - 증거 없이 LB idle 변경

표 채운 뒤 후보:

| 조건 | 조치 후보 |
|---|---|
| 문제 Router만 Backend 연결 실패 | 해당 노드 CNI/route/iptables/conntrack 복구, 필요 시 노드 네트워크 재적용·cordon 검토 |
| default가 다시 Data 우선 | NetworkManager/영구 route 설정 교정, metric 고정 |
| conntrack 포화 | nf_conntrack 튜닝 + 원인 트래픽 확인 |
| connecting timeout + 경로 정상 아님 | CNI 재기동/노드 재부팅은 **최후**, 증거 확보 후 |

---

## 10. 같이 붙어 있는 이슈 (부차)

- Grafana “failed to load its application files” — 정적 리소스/Ingress 가능. 504 계층 확정 후 재판단
- 5.1.1.8 풀 custom Prometheus rule — 원문 미확보, 504와 별 트랙
- LDAP — 이 세션 범위 밖

---

## 11. 한 문단 요약 (보고/인수인계용)

prd-host-pa01-xas Host UI(console/prometheus/grafana/alertmanager)가 간헐 504를 낸다. 완전 다운이 아니라 재시도 시 복구된다. bastion에서 controller Pod IP 직접 curl timeout은 장애가 아니라 Pod CIDR 라우팅 부재다. **ingress-nginx 로그에 504가 찍혀 해당 건의 생성 주체는 ingress**이며, **특정 controller 하나에서만** 발생한다. Router마다 controller 1개 배치. Router 3번에 과거 Data/Main default metric 역전 이력이 있고 route는 수동 정리 후 현재 정상처럼 보이며 Pod도 기동된다. **문제 controller Pod를 delete해도 동일**하므로 controller 프로세스 일회성 문제가 아니라 **해당 Router 노드 데이터플레인(CNI/conntrack/iptables/경로)** 가능성이 가장 높다. 다음 작업은 504의 `upstream_addr`를 확보한 뒤 정상 Router와 문제 Router에서 동일 Backend IP:PORT 연결을 비교하는 것이다.

---

## 12. 다음 세션 붙여넣을 최소 출력

출근 후 아래만 확보하면 이어서 판정 가능:

```text
1) kubectl -n ingress-nginx get pod -o wide
2) 문제 pod 이름 / NODE
3) 504 로그 원문 1~3줄 (upstream_addr 포함, 쿠키/토큰 삭제)
4) 문제 Router: ip route get <upstream_ip>
5) 문제 Router: nc -vz -w 3 <upstream_ip> <port>
6) 정상 Router: 동일 nc / ip route get
7) 문제 Router: ip -4 route show default
```

---

## Version History

| 버전 | 날짜 | 변경 내용 |
|---|---|---|
| 0.1 | 2026-07-10 | 당일 진단 대화 전체 핸드오프 초안 작성 (문서 작업 + 504 범위 축소 + 다음 액션) |
