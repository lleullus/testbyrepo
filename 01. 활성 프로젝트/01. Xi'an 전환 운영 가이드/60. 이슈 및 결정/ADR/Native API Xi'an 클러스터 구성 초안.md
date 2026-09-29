---
title: Native API Xi'an 클러스터 구성 설명 훈련
created: 2026-07-12
status: draft
type: judgment-apprenticeship
tags:
  - xi-an
  - native-api
  - p-dep
  - ingress
  - rbac
  - explanation
parent: "[[60. 이슈 및 결정/이슈 및 결정 안내|이슈 및 결정 안내]]"
aliases:
  - Native API Xi'an 클러스터 구성 초안
doc_type: guide
scope: "Xi'an 전환 운영 가이드"
updated: "2026-07-19"
---

# Native API Xi'an 클러스터 구성 설명 훈련

## 이 문서의 목적

이 문서는 Xi'an 클러스터의 Native API 구성안을 **다른 운영자, 고객, P-DEP 담당자에게 정확히 설명할 수 있게 되는 것**이 목적이다. YAML 적용 순서를 암기하는 문서가 아니다.

설명할 때 반드시 지켜야 할 경계는 하나다.

> [!summary] 핵심 메시지
> Native API 구성은 P-DEP용 비즈니스 API를 새로 만드는 일이 아니다. 인프라가 `kube-apiserver까지의 접근 경로`, `호출 주체 제한`, `합의된 권한 기반`을 제공하는 일이다. 그 위에서 Access Token 발급과 같은 업무 로직은 P-DEP가 구현한다.

이 문서의 범위는 인프라 제공자의 구성과 검증이다. P-DEP의 래퍼, EPID 검증, Namespace Label 검증, DKS-N 대체 로직의 구현은 포함하지 않는다.

## 판단 도제 아크

### assumption

당신은 운영 변경 승인자나 고객에게 10분 안에 다음을 설명해야 한다.

- 왜 kube-apiserver를 외부에서 접근할 수 있게 만드는가
- 경로 개방과 Kubernetes 권한이 왜 별개인가
- 현재 RBAC이 최종 권한이 아니라 초기 베이스라인인 이유
- 무엇이 확인되어야 적용 완료라고 말할 수 있는가

### domain read

- class: E, 운영 클러스터와 권한을 다루는 고위험 전문 영역
- risk: high, kube-apiserver 노출 또는 과도한 RBAC은 클러스터 접근 범위를 넓힌다
- prerequisite burden: medium, Kubernetes Service, Ingress, ServiceAccount, RBAC의 역할을 구분할 수 있어야 한다
- feedback availability: medium, 실제 클러스터 검증은 강하지만 이 문서의 학습은 구성값 확정 전에는 사례 검토에 의존한다
- calibration: 이 아크는 구성안을 설명하고 경계를 지키는 능력을 검증한다. 실제 운영 적용 권한을 부여하지 않는다

### thin orientation map

첫 아크의 병목은 YAML 문법이 아니라, 다음 세 층을 섞지 않고 설명하는 것이다.

1. **경로:** 외부 요청이 kube-apiserver까지 도달하는가
2. **접근 제어:** 정해진 P-DEP 출발지와 ServiceAccount만 통과하는가
3. **업무 권한:** 통과한 주체가 합의한 Kubernetes 작업만 할 수 있는가

이 아크를 통과한 뒤의 다음 판단은 RBAC 최종화, TokenRequest 전환 설계, 운영 변경 절차와 장애 회귀 계획이다.

## 전문가 벤치 장면

고객이 다음처럼 묻는다.

> “P-DEP가 Access Token을 발급해야 한다면 P-DEP 전용 API 서버를 만드는 것인가요? 그리고 현재 RBAC YAML을 적용하면 DKS-N 대체가 끝난 것인가요?”

전문가는 YAML부터 보여주지 않는다. 먼저 다음처럼 상황을 분해한다.

| 층 | 인프라가 제공하는 것 | 이 구성안이 보장하지 않는 것 |
|---|---|---|
| 경로 | `nativeapi.{domain}`에서 kube-apiserver로 이어지는 HTTPS 경로 | P-DEP 업무 API 또는 업무 로직 |
| 네트워크 제한 | 검증된 Ingress 또는 상위 네트워크의 source IP 제한 | P-DEP 내부 호출의 정당성 |
| 인증과 권한 | ServiceAccount와 RBAC 기반의 Kubernetes API 권한 | DKS-N 대체 기능 전체의 완전성 |
| 검증 | 경로, 인증, 허용/거부 권한의 관찰 결과 | 미확정 CIDR, DNS, K8s 버전 문제의 자동 해결 |

### 구성 대상

| 환경 | 클러스터 | Native API FQDN | kube-apiserver master IP | Ingress router IP | 상태 |
|---|---|---|---|---|---|
| 운영 Host | `prd-host-pa01-xas` | `nativeapi.xaprdpa01.mgmt.dks.samsungds.net` | `109.156.22.44~46` | `109.156.22.47~49` | 구성 대상 |
| 운영 Apps | `prd-apps-pa01-xas` | `nativeapi.xaprdpa01.apps.dks.samsungds.net` | `109.156.22.58~60` | `109.156.22.61~63` | 구성 대상 |
| 개발 Apps | `dev-apps-pa01-xas` | `nativeapi.xadevpa01.apps.dks.samsungds.net` | `109.156.22.73~75` | `109.156.22.76~78` | 구성 대상 |

```mermaid
flowchart LR
    P[P-DEP: 허용된 출발지 IP] --> I[Ingress: nativeapi.{domain}]
    I --> S[Service: kube-system/kube-apiserver]
    S --> A[kube-apiserver static Pods]
    P -. Bearer Token .-> A
    A --> R[ServiceAccount + RBAC]
```

### 판단 루프

1. **Notice:** 질문이 경로, 네트워크 제한, 인증, RBAC, P-DEP 업무 로직 중 어느 층에 관한 것인지 먼저 분류한다.
2. **Compare:** 각 구성물의 책임을 대조한다. `Service/Ingress`는 경로, 검증된 source IP 제한은 출발지 제한, `ServiceAccount/RBAC`은 API 인증·인가다.
3. **Ignore for now:** 특정 Endpoint 몇 개만 보고 최종 최소 권한을 확정하거나, P-DEP의 내부 업무 로직을 인프라 완료 범위에 포함하지 않는다.
4. **Decide:** 전체 DKS-N 대체 범위를 확인하기 전에는 현재 Access Token 흐름용 권한을 초기 베이스라인으로만 설명한다.
5. **Check:** Service Endpoint, Ingress Address, 무인증 요청의 거부, Token 요청의 허용 범위와 거부 범위를 각각 확인한다.

## 첫 작은 산출물

다음 네 문장으로 구성안을 설명하는 1분 설명 카드를 작성한다.

1. **무엇을 연다:** `nativeapi.{domain}`에서 kube-apiserver까지의 경로를 연다.
2. **어떻게 제한한다:** P-DEP CIDR allowlist와 ServiceAccount Bearer Token으로 호출 주체를 제한한다.
3. **무엇을 허용한다:** 현재 확인된 Access Token 발급 흐름에 필요한 Kubernetes 리소스 동작만 초기 RBAC에 둔다.
4. **무엇을 아직 말할 수 없는가:** 전체 DKS-N 대체 범위, 최종 least privilege, Token 방식은 미결 조건을 확인해야 확정할 수 있다.

Constraints:

- “P-DEP API 서버를 새로 만든다”라는 표현을 쓰지 않는다.
- 경로 개방과 RBAC을 한 문장으로 합치지 않는다.
- 적용 완료 조건을 최소 세 개의 관찰 가능한 결과로 말한다.
- Token 값, CIDR 값, Namespace 값이 미확정이면 확정된 것처럼 말하지 않는다.

## 초보자 함정

약한 설명은 다음과 같다.

> “Ingress와 RBAC을 만들고 Token을 전달하면 Native API 전환이 완료됩니다.”

이 설명은 두 가지를 숨긴다. Ingress는 요청이 도달할 길을 열 뿐 API 권한을 부여하지 않으며, 현재 RBAC은 분석된 Access Token 흐름만 커버하는 초기안이라 P-DEP의 모든 DKS-N 의존 기능을 대체했다는 증거가 아니다.

이를 다음 설명으로 교체한다.

> “먼저 P-DEP가 kube-apiserver에 도달할 길과 호출 주체 제한을 제공합니다. 그다음 전체 대체 범위를 확인한 뒤 필요한 Kubernetes 권한을 산정하고 least privilege로 좁힙니다. 현재 RBAC은 그 과정의 초기 베이스라인입니다.”

## 충돌 시험

설명 카드와 구두 설명은 다음을 모두 만족하면 통과다.

1. `Service -> Ingress -> kube-apiserver` 경로와 `ServiceAccount -> RBAC` 권한 경로를 분리해 설명한다.
2. allowlist가 “누가 Ingress까지 들어올 수 있는가”를 제한하고 RBAC이 “도달 후 무엇을 할 수 있는가”를 제한한다고 설명한다.
3. 현재 RBAC의 범위가 `namespaces`, `serviceaccounts`, `secrets`, `roles`, `rolebindings`의 현재 분석 흐름용 베이스라인이며 최종안이 아니라고 말한다.
4. 완료 검증을 Endpoint, Ingress Address, 무인증 거부, Token 요청의 허용/거부 권한으로 나눠 제시한다.
5. K8s 버전에 따라 ServiceAccount Token 취급이 달라질 수 있으며 1.24+에서는 TokenRequest API 검토가 필요하다고 말한다.

다음 중 하나면 실패다.

1. `403`만 나오면 모든 구성이 정상이라고 단정한다. 무인증 응답은 apiserver의 anonymous-auth 설정에 따라 `401` 또는 `403`일 수 있으므로, 핵심은 인증되지 않은 요청이 허용되지 않는 것과 이후 Token 권한 검증을 분리하는 데 있다.
2. 현재 권한 YAML만으로 P-DEP의 전체 DKS-N 대체가 완료된다고 말한다.

Feedback source:

- 실제 변경 전에는 구성안 검토자 또는 인프라 담당자와의 설명 리허설
- 실제 적용 시에는 `kubectl` 상태와 curl 응답을 이용한 객관적 검증
- feedback strength: qualified review + objective test
- confidence: medium before scope confirmation, high for applied path checks

## 뒤늦은 개념 패치

첫 설명을 만든 뒤 아래 실패가 보일 때만 읽는다.

1. **Concept: Service와 Ingress의 역할 분리**
   - Repairs: Ingress가 kube-apiserver를 직접 찾는다고 설명하거나 경로와 권한을 혼동하는 문제
   - Use it when: 외부 요청이 어디로 흘러가는지 설명할 때
   - Re-enter when: 충돌 시험 1을 통과하지 못했을 때

2. **Concept: 인증, 인가, 출발지 제한의 서로 다른 책임**
   - Repairs: CIDR allowlist만으로 Kubernetes 권한까지 제한된다고 설명하는 문제
   - Use it when: “왜 allowlist와 RBAC이 모두 필요한가”에 답할 때
   - Re-enter when: 충돌 시험 2를 통과하지 못했을 때

3. **Concept: RBAC 베이스라인과 최종 least privilege의 차이**
   - Repairs: 현재 4개 Endpoint 기준 권한을 최종 권한으로 선언하는 문제
   - Use it when: 권한 검토 범위와 남은 의사결정을 설명할 때
   - Re-enter when: 충돌 시험 3 또는 실패 조건 2에 해당할 때

4. **Concept: ServiceAccount Token 방식의 버전 의존성**
   - Repairs: `.secrets[0]` 방식이 모든 Kubernetes 버전에서 동작한다고 전제하는 문제
   - Use it when: Token 전달 방법과 운영 갱신 방식을 설명할 때
   - Re-enter when: 충돌 시험 5를 통과하지 못했거나 K8s 버전이 1.24+로 확인됐을 때

## 사실 카드: 구성과 검증

### 사전 확인

- `kubectl get po -n kube-system -l component=kube-apiserver`로 static Pod label을 확인한다. 예시 selector는 `component=kube-apiserver`, `tier=control-plane`이다.
- 같은 이름의 `Service` 또는 `Ingress`가 이미 있는지 확인한다.
- P-DEP ServiceAccount namespace를 확정한다. `oprsvc-prd`는 운영 선례의 예시일 뿐 Xi'an 확정값이 아니다.
- NGINX Ingress Controller의 SSL passthrough 활성화 여부와, 이 모드에서 source IP allowlist annotation이 실제 차단을 강제하는지 확인한다. SSL passthrough는 일반 HTTP 요청 처리 경로를 우회할 수 있으므로 annotation 존재만으로는 충분하지 않다.
- P-DEP Host/Apps의 최종 CIDR, 세 FQDN의 DNS, 각 클러스터 Kubernetes 버전을 확인한다.

### 경로 구성

1. `kube-system/kube-apiserver` Service가 static kube-apiserver Pod의 `6443`을 가리키게 한다.
2. `nativeapi.{domain}` Ingress가 해당 Service의 `443`으로 TLS passthrough 되게 한다.
3. source IP 제한은 SSL passthrough 환경에서 실제 차단이 확인된 제어 지점에 둔다. Ingress annotation 기반 allowlist가 유효한지 먼저 검증하고, 유효하지 않으면 Load Balancer나 방화벽 등 상위 네트워크 제어로 각 P-DEP CIDR을 제한한다.

설명용 최소 Service 예시는 다음과 같다. 실제 Pod label을 확인한 뒤 selector를 맞춘다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kube-apiserver
  namespace: kube-system
spec:
  type: ClusterIP
  selector:
    component: kube-apiserver
    tier: control-plane
  ports:
    - port: 443
      targetPort: 6443
      protocol: TCP
```

Ingress의 설명 포인트는 host와 source IP 제한의 **검증 상태**다. 아래 CIDR은 placeholder이며 실제 적용값이 아니다. SSL passthrough에서 이 annotation만으로 제한이 강제된다고 가정하지 않는다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kube-apiserver-ingress
  namespace: kube-system
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/whitelist-source-range: "<P-DEP-CIDR>"
spec:
  rules:
    - host: nativeapi.xaprdpa01.apps.dks.samsungds.net
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: kube-apiserver
                port:
                  number: 443
```

### 권한 베이스라인

현재 분석된 Access Token 발급 흐름을 기준으로 하는 초기 권한은 아래와 같다. 이것은 최종 권한 명세가 아니다.

| 목적 | 리소스 | 초기 동사 | 설명 시 붙일 경계 |
|---|---|---|---|
| 대상 확인 | `namespaces` | `get`, `list` | Namespace 존재와 속성 확인 |
| SA 재사용·생성·보정 | `serviceaccounts` | `get`, `list`, `create`, `update`, `patch` | 실제 변경 흐름 재확인 필요 |
| Role 재사용·생성·보정 | `roles` | `get`, `list`, `create`, `update`, `patch` | Namespace 범위 권한 |
| RoleBinding 재사용·생성·보정 | `rolebindings` | `get`, `list`, `create`, `update`, `patch` | SA와 Role 연결 |
| Token 관련 조회·처리 | `secrets` | `get`, `list`, `create`, `update`, `patch` | 1.22 계열 가정이 포함됨 |

아직 포함하지 않은 항목도 명시한다.

| 미포함 항목 | 이유 | 추가 전 확인 |
|---|---|---|
| `delete` | 재발급·정리 흐름의 실제 필요가 확인되지 않음 | P-DEP의 삭제 기반 운영 흐름 |
| `serviceaccounts/token` create | TokenRequest 전환 여부가 미확정 | 각 클러스터 Kubernetes 버전과 Token 정책 |
| P-DEP의 추가 DKS-N 기능 권한 | 현재 분석 범위 밖 | 전체 대체 기능 목록 |

### 완료 검증

검증은 한 번의 curl 결과가 아니라 아래 네 층을 확인하는 일이다.

| 검증 층 | 확인 명령 또는 관찰 | 기대 결과 |
|---|---|---|
| Service | `kubectl describe svc -n kube-system kube-apiserver` | master 3개 Endpoint와 `:6443` |
| Ingress | `kubectl describe ing -n kube-system kube-apiserver-ingress` | 해당 클러스터 router IP 3개 |
| 출발지 제한 | 허용되지 않은 검증용 출발지에서 동일 FQDN 접근 시도 | TCP/TLS 또는 HTTP 단계에서 거부됨. SSL passthrough 시 실제 강제 지점을 함께 기록 |
| 무인증 요청 | `curl -k https://$NATIVE_API_HOST/api/v1/namespaces` | 인증되지 않은 요청은 거부됨. 환경에 따라 `401` 또는 `403` 가능 |
| Token 요청 | Bearer Token으로 허용 리소스와 비허용 리소스를 각각 호출 | 허용 API는 정상 응답, 예를 들어 `pods`처럼 부여하지 않은 권한은 거부 |

> [!warning] 운영 경계
> `curl -k`는 인증서 검증을 생략하므로 임시 진단 외의 운영 검증 기준으로 삼지 않는다. Token은 문서, shell history, 채팅에 남기지 않고 승인된 비밀 전달 경로로만 취급한다. 실제 적용은 격리된 검증 또는 승인된 변경 절차와 자격 있는 검토를 전제로 한다.

## Practice & Calibration Runbook

### Start Packet

#### First move

15분 안에 고객 질문에 답하는 1분 설명 카드를 작성한다.

- Artifact: `무엇을 연다 / 어떻게 제한한다 / 무엇을 허용한다 / 무엇이 미결인가`의 네 문장
- Key constraints: 경로와 RBAC 분리, 현재 RBAC을 최종안으로 단정하지 않기, 완료 검증 세 가지 이상 포함
- Done when: 동료에게 읽어 주었을 때 `P-DEP API를 새로 만드는 것인가`라는 오해를 바로잡을 수 있다

#### You need

- 이 문서의 `전문가 벤치 장면`, `충돌 시험`, `사실 카드`만 열어 둔다.
- 실제 클러스터, 실 Token, 실 CIDR은 첫 설명 시도에 필요하지 않다.
- 실제 적용 여부를 판단하는 단계에서는 승인된 sandbox 또는 운영 변경 절차, 인프라 담당자 검토, P-DEP의 전체 대체 범위 확인이 필요하다.
- Feedback strength for this attempt: qualified review

#### Read only if blocked

- **구성 요소가 섞임:** `전문가 벤치 장면`의 표와 `판단 루프`를 읽고 First move로 돌아간다.
- **왜 두 가지 제한이 필요한지 막힘:** `뒤늦은 개념 패치`의 인증·인가·출발지 제한 항목만 읽는다.
- **K8s 1.24+ Token 질문에 막힘:** `사실 카드: 구성과 검증`의 권한 베이스라인과 Token 관련 미포함 항목만 읽는다.
- **설명을 이미 했고 틀렸음:** `Collision Response`로 바로 간다.
- **그 외:** First move를 바로 수행한다.

#### Local terms

1. **TLS passthrough:** Ingress가 TLS를 종료하지 않고 kube-apiserver까지 전달하는 방식이다. API 서버의 TLS 통신 경로를 설명할 때 필요하다.
2. **source IP allowlist:** Ingress 진입 전에 허용할 출발지 CIDR 목록이다. Kubernetes API 권한 자체는 부여하지 않는다.
3. **ServiceAccount:** Kubernetes API 요청의 주체가 되는 identity다. Bearer Token과 RBAC을 연결하는 기준점이다.
4. **least privilege:** 필요한 업무 범위가 확인된 뒤 그 동작에 필요한 최소 권한만 남기는 원칙이다. 현재 초기 RBAC을 최종안으로 부르지 않는 이유다.

### Rep Ladder

#### Rep 0 - 네 문장으로 경계 세우기
- **Judgment focus:** Notice - 고객 질문을 경로, 접근 제한, RBAC, 업무 로직으로 분류한다.
- **Controlled variation:** clean case - P-DEP가 Native API로 Access Token 발급 흐름을 대체해야 하는 기본 상황이다.
- **Learner output:** 네 문장 설명 카드와 구성도 한 장.
- **Collision gate:** 충돌 시험 1 - 경로와 권한 경로를 분리한다.
- **AI role:** Learner submits first: 설명 카드. AI may: 제출 뒤 누락된 층을 지적한다. AI must not: 설명문을 먼저 작성하거나 층 분류를 대신한다.

#### Rep 1 - “Ingress가 있는데 RBAC이 왜 필요한가?”
- **Judgment focus:** Compare - allowlist와 RBAC이 제한하는 대상을 대조한다.
- **Controlled variation:** misleading cue - 고객이 allowlist가 있으면 Kubernetes 권한도 안전하다고 주장한다.
- **Learner output:** allowlist와 RBAC의 차이를 각각 한 문장으로 설명하고, 둘 중 하나만 있을 때의 빈틈을 한 가지씩 적는다.
- **Collision gate:** 충돌 시험 2 - 진입 가능 주체와 API 동작 가능 범위를 분리한다.
- **AI role:** Learner submits first: 두 문장과 빈틈. AI may: 제출 뒤 “누가 들어오는가, 들어온 뒤 무엇을 하는가”라는 힌트 하나만 준다. AI must not: 정답 문장을 제공한다.

#### Rep 2 - “이 RBAC으로 전환 완료인가?”
- **Judgment focus:** Decide - 초기 베이스라인과 최종 권한 확정 사이의 결정을 말한다.
- **Controlled variation:** missing information - 현재 분석된 4개 Endpoint 외의 P-DEP DKS-N 의존 기능 목록이 주어지지 않는다.
- **Learner output:** 완료 선언을 보류하는 이유, 먼저 확인할 정보, 현재 적용 가능한 제한적 결론을 각각 한 문장으로 적는다.
- **Collision gate:** 충돌 시험 3 - 현재 RBAC이 최종안이 아니라고 명확히 말한다.
- **AI role:** Learner submits first: 세 문장. AI may: “어떤 기능 목록이 없어서 권한을 확정할 수 없는가?”라는 질문 하나만 한다. AI must not: 추가 권한을 추정해 제시한다.

#### Rep 3 - 적용 완료 설명 검증
- **Judgment focus:** Check - 경로, 인증, 권한의 검증 신호를 순서대로 제시한다.
- **Controlled variation:** transfer - 운영 Host 클러스터의 FQDN과 router/master 주소로 사례 표면을 바꾼다.
- **Learner output:** `prd-host-pa01-xas`를 대상으로 한 검증 순서와 각 단계의 기대 관찰 결과.
- **Collision gate:** 충돌 시험 4와 5 - Endpoint, Ingress Address, 무인증 거부, 허용/비허용 Token 권한, 버전 경계를 말한다.
- **AI role:** Learner submits first: 검증 순서. AI may: 충돌 시험 기준만 적용한다. AI must not: 명령 순서나 예상 응답을 미리 작성한다.

### Collision Response

#### Pass
- **Criterion used:** 해당 Rep의 충돌 시험 기준
- **Judgment held:** 구성 요소의 책임과 미결 조건을 섞지 않고 설명했다.
- **Next:** 다음 Rep의 controlled variation으로 진행한다.
- **AI support:** 다음 Rep의 AI role에 따라 설명 모델링에서 제출 후 검토로 지원을 줄인다.

#### Partial pass
- **Criterion used:** 충돌 시험 1, 2, 3, 4 또는 5 중 부분 충족 항목
- **Missed cue:** 경로 개방과 인가를 한 덩어리로 말했거나, 초기 RBAC의 확정 범위를 과장했다.
- **Concept patch:** `Service와 Ingress의 역할 분리`, `인증, 인가, 출발지 제한의 서로 다른 책임`, 또는 `RBAC 베이스라인과 최종 least privilege의 차이`
- **Re-enter when:** 해당 충돌 시험 기준을 한 문장으로 다시 충족시킬 수 있을 때
- **Closest retry:** 원래 설명에서 문제가 된 한 문장만 `누가 들어오는가`와 `들어온 뒤 무엇을 할 수 있는가`로 나눠 고쳐 말한다.
- **Activate drill if:** 같은 기준 또는 같은 누락 신호가 이전 시도에서도 반복되면 Targeted Drill을 활성화한다.

#### Fail
- **Criterion used:** 실패 조건 1 또는 2
- **Missed cue:** 무인증 응답 상태 코드 하나만으로 경로·권한이 모두 정상이라고 판단했거나, 현재 권한을 최종 대체 범위로 선언했다.
- **Concept patch:** `인증, 인가, 출발지 제한의 서로 다른 책임` 또는 `RBAC 베이스라인과 최종 least privilege의 차이`
- **Re-enter when:** 무인증 거부와 Token 권한 검증을 분리하고, 전체 기능 범위 확인 전에는 완료 선언을 보류할 수 있을 때
- **Closest retry:** Rep 2 또는 Rep 3에서 “현재 확인된 범위”와 “추가 확인이 필요한 범위”를 각각 한 문장으로 다시 작성한다.
- **Activate drill if:** 같은 실패 기준이 두 번 발생하거나 같은 누락 신호를 두 번 보이면 Targeted Drill을 활성화한다.

#### Blocked
- **Criterion used:** 충돌 시험 4 또는 5를 실제 근거로 확인할 수 없음
- **Missing enabler:** P-DEP 전체 DKS-N 대체 기능 목록, 최종 CIDR, 실제 ServiceAccount namespace, Kubernetes 버전, DNS 가능 여부 중 하나
- **Secure before retry:** 해당 책임자에게 미결 사항 표를 기준으로 값을 확인하고, 값이 확정되기 전에는 placeholder와 미결 상태를 유지한다.
- **Re-enter when:** 확인된 값을 설명 카드의 조건 또는 검증 계획에 반영했을 때
- **Do not:** 미확정 값을 사실처럼 말하거나 다음 Rep을 통과 처리한다.

#### Unsafe or unverifiable
- **Criterion used:** 실제 운영 cluster에 대한 적용·Token 추출·권한 호출이 승인 절차나 자격 있는 검토 없이 요구됨
- **Stop:** 실 Token 발급·전달과 운영 Ingress 적용을 중단한다.
- **Route to:** 격리된 검증 환경 또는 승인된 변경 절차에서 인프라 담당자와 P-DEP 담당자의 공동 검토로 전환한다.
- **Do not:** 문서상의 예시 명령을 운영 실행 승인으로 해석하거나, Token을 채팅·문서·shell history에 남긴다.

### Progression Record

#### Attempt log

| case | first-ranked cue | decision | collision result | patch used | next change | AI support level |
|---|---|---|---|---|---|---|
| Rep 0 - 네 문장으로 경계 세우기 | 경로와 권한은 별도 층 | 네 문장 설명 카드 작성 | 미시도 | - | 고객 질문에 1분으로 설명 | 제출 후 누락 층 검토 |

#### Done condition

다음을 모두 만족하면 이 아크를 마친다.

- **Transfer case:** `prd-host-pa01-xas` 사례에서 FQDN, 경로, 제한, RBAC, 검증을 설명하고 충돌 시험 4와 5를 통과한다.
- **AI support:** 마지막 Rep에서 사전 힌트 없이 설명을 먼저 제출하고 사후 기준 검토만 받는다.
- **Collision threshold:** 독립된 두 질문에서 충돌 시험 1~4를 모두 충족하고 실패 조건 1~2가 없다.
- **Consistency:** 두 번 연속으로 “현재 RBAC은 초기 베이스라인”이라는 경계와 그 이유를 먼저 말한다.

#### Next action

`첫 작은 산출물`의 네 문장으로 1분 설명 카드를 작성한 뒤, “P-DEP API를 새로 만드는 것인가?”라는 질문에 소리 내어 답한다.
