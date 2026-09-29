# 개요
DKS-C 서비스(모니터링, OpenSearch 등)의 Health Check를 위해 Long-Term Access Token을 발급하는 방법을 기술한다.
사전에 `dkssol-console-longterm-client`가 생성되어 있어야 함. 2026-06-16 생성.

## 핵심 내용
Token 발급은 3단계로 진행:
1. 사용자 인증 **Code** 발급 (Keycloak)
2. Code를 이용해 토큰 소유자의 **Client Access Token** 발급
3. Exchange Client(Long-Term)의 **Long-Term Access Token** 교환

Keycloak Realm: `DKS`
Keycloak 서버: `https://keycloak.dks.samsungds.net`

## 세부 정보
### 1. Code 발급
- 크롬 브라우저 → 개발자 도구 > 네트워크(전체) 활성화
- 아래 URL로 이동 (로그인 필요):
```
https://keycloak.dks.samsungds.net/realms/DKS/protocol/openid-connect/auth?client_id=dkssol-console&response_type=code&scope=openid&redirect_uri=https://console.dks.samsungds.net/
```
- 네트워크 목록에서 `redirect_uri`에 `session_state`와 `code`가 붙은 URL에서 `code` 값 복사

**주의**: 코드는 일회성이며, 호출되거나 1분 경과 시 만료

### 2. Client Access Token 발급 (Code → Token)
```
curl -X POST 'https://keycloak.dks.samsungds.net/realms/DKS/protocol/openid-connect/token' \
-H 'Content-Type: application/x-www-form-urlencoded' \
-d 'grant_type=authorization_code' \
-d 'client_id=dkssol-console' \
-d 'client_secret=[REDACTED_SECRET]' \
-d 'code=[1번에서 복사한 code 값]' \
-d 'redirect_uri=https://console.dks.samsungds.net/'
```
- `client_id`: 토큰 소유자 Client ID
- `client_secret`: 토큰 소유자 Client Secret

### 3. Long-Term Access Token 교환
- Exchange용 Long-Term Client (`dkssol-console-longterm-client`)의 Client ID/Secret 사용
- Long-Term 토큰 만료 시 재인증 필요
- Long-Term 토큰 유효 기간: **1년**

### 검증
```
# 모니터링 서비스
curl 'https://monitoring.dks.samsungds.net/-/healthy' \
-H 'Authorization: Bearer [Long-Term Access Token]'

# OpenSearch
curl 'https://opensearch-api.dks.samsungds.net/' \
-H 'Authorization: Bearer [Long-Term Access Token]'
```

### 토큰 Claims (참고)
Issued JWT 예시:
- iss: `https://keycloak.dks.samsungds.net/realms/DKS`
- aud: `dkssol-console`
- azp: `dkssol-console-longterm-client`
- sub: `4fbc5cb6-3cfc-485b-91c7-bbbf20513fd7`
- preferred_username: `dsgh25520.id`
- groups: `dkssol-console-longterm-client`

## 주의사항 / 예외 / 확인 필요
- Code는 **1회용** + **1분 만료** (재발급 시 Keycloak 로그인 재수행)
- Long-Term 토큰 만료 시 재발급 위해 재인증 필요
- 토큰 발급에 사용된 Client Secret 등 민감 정보는 별도 보관 필수