# OpenCodex Google Antigravity 403 (Verify your account) 장애 분석 및 복구 런북

- **작성일자**: 2026-09-25
- **대상 시스템**: OpenCodex (`ocx`), Google Antigravity Provider (`daily-cloudcode-pa.googleapis.com` / `cloudcode-pa.googleapis.com`)
- **영향 계정**: `tubeofmill@gmail.com` (o662ec8), `0310muro@gmail.com` (o29a5fc)

---

## 1. 개요 및 장애 현상

### 1.1 에러 메시지
```text
Error: 403 Provider error 403: Antigravity access denied (PERMISSION_DENIED): Verify your account to continue.
Provider error 403: Antigravity access denied (PERMISSION_DENIED): Verify your account to continue. (type=permission_error param=permission_denied)
```

### 1.2 발생 맥락
- OpenCodex에서 `google-antigravity/gemini-3.8-flash` 모델을 사용하는 요청 중 일부 계정으로 라우팅될 때 위 403 에러가 발생.
- `usage.jsonl` 분석 결과, 총 12개 등록 계정 중 2개 계정에서 403 에러가 누적 발생:
  - `tubeofmill@gmail.com`: 206회 에러
  - `0310muro@gmail.com`: 12회 에러

---

## 2. 시행착오 및 오판 분석 (헤맸던 내용)

### 2.1 잘못된 진단 1: "일반 웹페이지에서 본인 인증을 하면 된다"
- **초기 판단**: 구글 계정 자체가 잠긴 줄 알고 `accounts.google.com`, `antigravity.google`, 구글 클라우드 콘솔, 연령 인증, 결제 설정 페이지 등을 안내함.
- **실제 사실**: 사용자가 해당 페이지들에 접속해도 **어떠한 인증 배너나 메시지도 뜨지 않음**. 구글 계정 자체는 완전히 정상인 상태였음.
- **원인**: 구글의 보안 정책상 일반 웹 로그인 세션과 Antigravity IDE/API 전용 OAuth 세션이 완전히 분리되어 있음. 일반 웹사이트에서는 API 전용 계정 잠금 여부가 표출되지 않음.

### 2.2 잘못된 진단 2: "에러 메시지에 인증 링크가 없다"
- **초기 판단**: OpenCodex 터미널 로그에는 `Verify your account to continue` 단문만 뜨고 링크가 없어서, 링크 자체가 없는 에러인 줄 알았음.
- **실제 사실**: OpenCodex의 `safeGoogleHttpErrorMessage()` 에러 정제 로직이 구글 API 응답 본문(JSON)에 들어있던 `validationUrl`을 잘라내고 짧은 메시지만 남겨서 숨겨진 것이었음.
- **실제 구글 백엔드 응답**:
  ```json
  {
    "ineligibleTiers": [
      {
        "reasonCode": "VALIDATION_REQUIRED",
        "validationErrorMessage": "Verify your account to continue.",
        "validationUrl": "https://accounts.google.com/signin/continue?sarp=1&scc=1&continue=https://developers.google.com/gemini-code-assist/auth/auth_success_gemini&plt=AKgnsbu2...&flowName=GlifWebSignIn&authuser"
      }
    ]
  }
  ```
  구글은 **일회성 보안 토큰(`plt=...`)이 포함된 전용 링크**를 응답하고 있었음.

### 2.3 오판 분석 3: "0310muro 계정의 인증 락 해제 여부 오판"
- **초기 판단**: 두 계정 모두 403이 떴으니 둘 다 구글 SMS 인증 대상인 줄 알았음.
- **중간 오판**: 프로브 테스트 당시 응답 분기(엔드포인트 차이)로 인해 0310muro가 정상인 것처럼 보였으나, 실제로는 구글 백엔드(`daily-cloudcode-pa`)에서 `VALIDATION_REQUIRED`로 차단되어 있었음.
- **실제 사실**:
  - `tubeofmill`: 구글 백엔드에서 `VALIDATION_REQUIRED`로 차단되어 전용 인증 링크(`validationUrl`)를 통한 SMS 본인 인증 완료 후 정상화.
  - `0310muro`: 마찬가지로 `VALIDATION_REQUIRED` 상태였으며, 전용 인증 링크 발급 및 본인 인증 완료 후 새 토큰을 주입하여 정상화.
  - **결론**: 두 계정 모두 구글 Antigravity 백엔드에서 정식 SMS 본인 확인 절차가 필수적이었음.
### 2.4 PKCE 핸드셰이크 타이밍 불일치
- 브라우저 콜백으로 받아온 OAuth `code`를 교환하려 했으나, 최초 인증 URL 생성 시 발행했던 일회성 `code_verifier`를 저장해 두지 않아 첫 시도에서 토큰 교환 실패.
- 해결: 고정된 `verifier`/`challenge` 쌍을 파일(`/tmp/oauth_pkce.json`)로 영구 저장 후 인증 URL을 생성하여 즉시 교환 성공.

---

## 3. 근본 원인 (Root Cause)

1. **Google Antigravity 백엔드의 부정 사용 감지**:
   - `cloudcode-pa.googleapis.com` 및 `daily-cloudcode-pa.googleapis.com`은 프록시/서드파티 도구 트래픽에 대해 간헐적으로 `VALIDATION_REQUIRED` 플래그를 세팅함.
2. **토큰 만료 및 무효화**:
   - 403 에러가 반복되면서 구글 서버에서 기존 OAuth Refresh Token을 세션 파기(`invalid_grant`) 처리함.
3. **OpenCodex 에러 로깅 한계**:
   - 구글이 응답 본문에 내려준 `validationUrl`을 축약하여 사용자에게 표출하지 않아서 사용자가 링크 존재를 알 수 없었음.

---

## 4. 최종 해결 및 복구 절차 (표준 작업 런북)

추후 동일한 `Verify your account to continue` 에러 발생 시 아래 절차로 정확하게 복구한다.

### 1단계: 임시 PKCE 생성 및 인증 링크 발급
파이썬 스크립트로 고정된 PKCE 키 쌍을 저장하고, 대상 계정(`login_hint`)이 포함된 전용 인증 URL을 생성한다:

```python
import json, urllib.parse, secrets, base64, hashlib

verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("utf-8")
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).rstrip(b"=").decode("utf-8")

with open("/tmp/oauth_pkce.json", "w") as f:
    json.dump({"verifier": verifier, "challenge": challenge}, f)

CLIENT_ID = "1071006060591-REDACTED.apps.googleusercontent.com"
SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cclog",
    "https://www.googleapis.com/auth/experimentsandconfigs",
]

params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": "http://localhost:51121/callback",
    "scope": " ".join(SCOPES),
    "code_challenge": challenge,
    "code_challenge_method": "S256",
    "access_type": "offline",
    "prompt": "consent select_account",
    "login_hint": "대상계정@gmail.com",
}
print("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params))
```

### 2단계: 브라우저 승인 후 `code` 회수
1. 사용자가 위 출력된 URL을 브라우저에서 열고 로그인 및 권한을 승인한다.
2. 리디렉션된 주소(`http://localhost:51121/callback?code=...`)에서 `code` 값을 복사한다.

### 3단계: 토큰 교환 및 Antigravity 백엔드 판정 확인
저장해둔 `verifier`로 구글에 요청하여 토큰을 발급받고 `loadCodeAssist`를 조회한다:

```python
import json, urllib.request, urllib.parse

with open("/tmp/oauth_pkce.json") as f:
    pkce = json.load(f)

# 구글 토큰 교환
data = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": "GOCSPX-REDACTED",
    "code": "수신한_CODE",
    "redirect_uri": "http://localhost:51121/callback",
    "code_verifier": pkce["verifier"],
}
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=urllib.parse.urlencode(data).encode("utf-8"), method="POST")
tokens = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))

# loadCodeAssist 조회
req2 = urllib.request.Request(
    "https://daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist",
    data=json.dumps({"metadata": {"ideType": "ANTIGRAVITY"}}).encode("utf-8"),
    headers={"Authorization": f"Bearer {tokens['access_token']}", "Content-Type": "application/json", "User-Agent": "Antigravity/2.0"},
    method="POST"
)
resp = json.loads(urllib.request.urlopen(req2).read().decode("utf-8"))
ineligible = resp.get("ineligibleTiers", [])

if ineligible:
    # SMS 본인 인증 링크가 존재하는 경우
    print("본인 인증 링크:", ineligible[0].get("validationUrl"))
else:
    # 계정이 이미 정상인 경우
    print("계정 정상 승인 완료")
```

### 4단계: (인증 필요 시) 사용자가 `validationUrl` 통과
- `validationUrl`이 출력되면 사용자가 해당 링크를 브라우저에서 열어 구글 본인 인증(SMS 확인)을 완료한다.

### 5단계: OpenCodex `auth.json` 갱신 및 서비스 재기동
새로 발급된 `access_token`과 `refresh_token`을 `~/.opencodex/auth.json`의 해당 계정 데이터에 주입하고 `ocx restart`를 수행한다.

```bash
# auth.json 주입 후
ocx restart
```

### 6단계: 상태 검증
```bash
TOKEN=$(cat ~/.opencodex/admin-api-token)
curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:10100/api/oauth/accounts?provider=google-antigravity&quota=1" | jq '.accounts[] | select(.email | contains("대상계정"))'
```
- `quotaUnavailable: false` 및 `customWindows` 정상 표시 확인.

---

## 5. 결론 및 교훈

1. **에러 원인 분리의 중요성**: 
   동일한 403 에러라도 계정에 따라 '구글 본인 인증 대기'와 '단순 리프레시 토큰 파기'라는 서로 다른 원인이 존재하므로, API 응답 세부 본문(`ineligibleTiers`)을 직접 찔러서 확인해야 함.
2. **단축/정제 에러 메시지의 맹점**:
   프록시 툴이 상위로 에러를 전달할 때 상세 URL(`validationUrl`)을 탈락시키는 경우가 있으므로, 원시 엔드포인트(`daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist`)를 직접 조회하는 것이 가장 정확함.
3. **PKCE 세션 보존**:
   OAuth 플로우를 수동으로 중개할 때는 `verifier`를 휘발시키지 말고 파일로 보관해야 사용자가 전달한 `code`를 즉시 토큰으로 맞교환할 수 있음.
