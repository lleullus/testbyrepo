# 개요
DKS (DS Cloud Kubernetes Service) 프로젝트의 Keycloak 연계 정보를 정리한 문서.
Keycloak의 기본 구성 요소, JWT Token 구조, Realm 세션/토큰 전역 설정, 그리고 13개 Client의 상세 설정 정보를 정리한다.

## 핵심 내용
**Keycloak 구성 요소**
- **Realm**: 사용자·클라이언트·그룹 등을 격리 관리하는 단위. DKS Realm에서 전체 운영.
- **Client**: Keycloak 연동 대상 애플리케이션/서비스.
- **ID Provider**: Keycloak이 다른 ID 시스템과 연동하여 사용자 신원 확인 시 사용.

**JWT Token Claim 정보** (OIDC 인증 성공 후 RP가 수신)
- **iss**: 발급 기관 (`https://keycloak.dks.samsungds.net/realms/DKS`)
- **sub**: 사용자 고유 ID
- **aud**: 허가된 앱 (Client ID)
- **exp**: 만료 시간
- **preferred_username**: 사용자 이름

**Realm(전역) 세션/토큰 기본 설정**
- SSO Session Idle : 8시간 (활동 없을 때 만료)
- SSO Session Max : 24시간 (절대 최대 시간, 지속 사용 중에도 강제 종료)
- Access Token Lifespan : 10분

**장기 토큰 발급 메커니즘** (No.2, 5~9 공통)
- 사용자 인증 후 발급된 Access Token 기반으로 **Token Exchange**로 장기 토큰 발급.
- Access Token Lifespan + Client Offline Session Idle을 설정 값(예: 365일)으로 맞추면 만료일 365일의 Access Token이 발급됨.
- 세션과 무관하게 **Access Token 만료 여부만 체크**하여 장기 토큰 사용 가능.

## 세부 정보
### Client 목록
| No. | Client명 | 도메인 | 사용 목적 | Access Token Lifespan | Client Offline Session Idle | 별도 설정 사유 |
|---|---|---|---|---|---|---|
| 1 | dkssol-console | https://console.dks.samsungds.net/ | DKS-C Console OIDC 인증 | **30분** | realm 설정 사용 | 잦은 token 재발급 방지를 위해 30분으로 증가 |
| 2 | dkssol-console-longterm-client | (내부) | DKS-C Console 장기 인증 토큰 (P-DEP Web Health Check에서 console API 인증, OpenSearch/VictoriaMetrics 권한 체크) | **365일** | **365일** | 장기 토큰용 |
| 3 | dks-cluster-mgmt | (내부) | console-vcfa → console API 호출 (시스템 계정) | realm 설정 사용 | realm 설정 사용 | — |
| 4 | k8s-client | (내부) | k8s kube-apiserver OIDC 설정 | realm 설정 사용 | realm 설정 사용 | — |
| 5 | k8s-longterm-client | 클러스터 접속 주소 | k8s 클러스터 접속 장기 토큰 | **365일** | **365일** | 장기 토큰용 |
| 6 | k8s-longterm-client-30 | 클러스터 접속 주소 | k8s 클러스터 접속 장기 토큰 | **30일** | **30일** | 장기 토큰용 |
| 7 | k8s-longterm-client-90 | 클러스터 접속 주소 | k8s 클러스터 접속 장기 토큰 | **90일** | **90일** | 장기 토큰용 |
| 8 | k8s-longterm-client-120 | 클러스터 접속 주소 | k8s 클러스터 접속 장기 토큰 | **120일** | **120일** | 장기 토큰용 |
| 9 | k8s-longterm-client-180 | 클러스터 접속 주소 | k8s 클러스터 접속 장기 토큰 | **180일** | **180일** | 장기 토큰용 |
| 10 | kube-login | http://localhost:8000 | kubectl kube-login 플러그인 → OIDC 인증으로 클러스터 접속 | **8시간** | **8시간** | 8시간 사용 목적. dkssol-console과 동일 세션 타임아웃으로 사용 시 설정 변경 필요 |
| 11 | k8s-cluster-admin | (내부) | kyverno 정책으로 관리자도 시스템 수정 불가 상태 방지 → 시스템 계정 사용 | realm 설정 사용 | realm 설정 사용 | — |
| 12 | grafana-oauth | https://grafana-dksm.dks.samsungds.net/ | Grafana OIDC 로그인 | realm 설정 사용 | realm 설정 사용 | — |
| 13 | opensearch-dashboard-oauth | https://opensearch-dashboard.dks.samsungds.net | OpenSearch OIDC 로그인 | realm 설정 사용 | realm 설정 사용 | — |

### Client 세션 설정 공통 값 (realm 사용 시)
- Client Session Idle : realm 설정 사용
- Client Session Max : realm 설정 사용

### Client No.10 (kube-login) 전용 설정
- Client Session Max : **28900초**

## 주의사항 / 예외 / 확인 필요
- **No.1 dkssol-console**: Access Token Lifespan만 30분으로 변경. 세션 설정은 realm 기본값(Idle 8시간, Max 24시간) 사용.
- **No.10 kube-login**: Access Token Lifespan과 세션 설정을 8시간으로 별도 설정. dkssol-console과 동일한 세션 타임아웃으로 사용하면 설정 변경 필요.
- **No.6~9 (k8s-longterm-client-30/90/120/180)**: Client Offline Session Idle을 30/90/120/180일로 설정하되, 발급되는 Access Token의 만료일은 **항상 365일**로 고정됨.
- **No.11 k8s-cluster-admin**: kyverno 정책이 모든 사용자(관리자 포함)에 제약을 걸므로, 관리자 기능을 유지하기 위해 시스템 계정으로 사용.