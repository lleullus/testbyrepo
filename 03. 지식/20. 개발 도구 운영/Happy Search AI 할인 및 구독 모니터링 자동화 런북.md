---
tags:
  - HappySearch
  - MCP
  - 텔레그램
  - 자동화
  - GPT-5.6-Luna
  - 모니터링
  - 런북
status: 운영중
created: 2026-08-18
updated: 2026-08-19
---

# Happy Search 기반 AI 할인 및 구독 모니터링 자동화 런북

## 1. 개요 및 아키텍처

본 시스템은 **`happy-search` MCP의 4개 플랫폼(Reddit, X, V2EX, LINUX DO) 수집 기능**과 **`OpenCodex GPT-5.6 Luna (xhigh)` 심층 평가 모델**을 결합하여, **10분 주기로 최신 AI 도구·구독·API 크레딧 할인 정보를 자동 탐색 및 평가하여 텔레그램으로 브리핑**하는 무인 모니터링 파이프라인이다.

특히 X 등 SNS에서 동일한 프로모션(예: OpenRouter GPT-5.6 Sol 50% 인하)이 여러 계정에 의해 반복 게시되는 현상을 완벽히 방어하기 위해 **최근 24시간 인덱스 이력 주입(`[D1..Dn]`) + Luna 단일 문맥 중복 판정 + 원자적 토픽 추적(Atomic Topic State)** 아키텍처를 적용하고 있다.

```text
[systemd user timer (10분 주기)]
       │
       ▼
[1. 병렬 멀티 플랫폼 수집 (2~3초)]
  ├─ LINUX DO: /latest.json 최신 피드 수집 (익명 검색 429 우회)
  ├─ Reddit: r/LocalLLaMA 등 핵심 Subreddit + <atom:published> 시각 복원
  ├─ X (Twitter): 고급 검색 연산자 + 금융/주식 노이즈 네거티브 필터링
  └─ V2EX: 중국어/영어 AI 딜 키워드 병렬 쿼리 (AI 优惠, 订阅 折扣 등)
       │
       ▼
[2. 1차 Timestamp & URL Guard (0.1초)]
  ├─ 게시 시각 검증 (직전 10분 이내 작성 여부 판별)
  └─ 이미 수집된 URL 중복 제거 (seen_urls.json)
       │
       ▼ (정제된 신규 후보 2~10건 전달)
[3. 최근 24시간 인덱스 이력 로드 (seen_topics.json)]
  └─ [D1] (2시간 전) OpenRouter | GPT-5.6 Sol API 50% 인하
  └─ [D2] (5시간 전) Modelflare | 가입 5 RMB 크레딧 프로모션
       │
       ▼
[4. OpenCodex GPT-5.6 Luna (xhigh) 심층 평가 & 중복 판정 (15~30초)]
  ├─ 진위 및 신뢰도 검증 (공식 프로모션 vs 스팸/피싱/리퍼럴)
  ├─ 실질 가성비 분석 (정가 대비 할인율, 무료 크레딧 규모)
  ├─ 액션 태깅:
  │    ├─ [ACTION: NEW] : 완전히 새로운 신규 딜
  │    ├─ [ACTION: DUPLICATE_OF D#] : 최근 보고된 D#의 단순 재인용/리트윗 (제외)
  │    └─ [ACTION: UPDATE_TO D#: STATUS] : 중대 상태 변화 (EXPIRED, PRICE_CHANGE 등)
  └─ 전문가 Verdict (최종 추천 대상 및 실용성)
       │
       ▼
[5. Python 후처리 & 텔레그램 발송]
  ├─ NEW 딜: 마크다운 브리핑 발송 + seen_topics.json에 [D_new] 등록
  ├─ UPDATE 딜: 4시간 쿨다운 검증(EXPIRED는 즉시) 후 발송 + 이력 갱신
  ├─ DUPLICATE / 0건 시: 알림 생략 (조용한 백그라운드 운영)
  └─ 상태 원자적 저장: seen_urls.json & seen_topics.json (os.replace)
```

---

## 2. 구성 파일 및 경로

| 구분 | 파일 경로 | 설명 |
| :--- | :--- | :--- |
| **실행 스크립트** | `/home/user01/scripts/happy_search_ai_deals.py` | 4개 플랫폼 수집, 인덱스 이력 주입, Luna 평가 및 텔레그램 전송 |
| **봇 설정 파일** | `/home/user01/.config/happy-search/telegram.json` | 텔레그램 Bot Token 및 Chat ID (`7110717577`) |
| **URL 캐시** | `/home/user01/.config/happy-search/seen_urls.json` | 이미 평가/수집된 URL 이력 (최대 1,000건 유지) |
| **토픽 추적 상태** | `/home/user01/.config/happy-search/seen_topics.json` | 최근 24시간 동안 보고된 유효 딜 목록 (중복 방지용 인덱스 이력) |
| **실행 로그** | `/home/user01/.config/happy-search/cron.log` | 스케줄러 실행 및 텔레그램 발송 로그 |
| **systemd 서비스** | `/home/user01/.config/systemd/user/happy-search-ai-deals.service` | Oneshot 실행 서비스 유닛 (`TimeoutStartSec=600`) |
| **systemd 타이머** | `/home/user01/.config/systemd/user/happy-search-ai-deals.timer` | 10분 주기 스케줄러 (`OnCalendar=*:0/10`) |

---

## 3. 플랫폼별 수집 전략

### 1) LINUX DO (`linuxdo_latest`)
- **수집 방식:** `/latest.json` 최신 토픽 스트림(`LinuxdoClient.latest`)을 호출한 뒤, 제목과 본문에서 AI 및 할인/우회/편법 키워드를 교차 매칭하여 수집.
- **타겟 키워드:**
  - AI: `ai`, `gpt`, `claude`, `cursor`, `openai`, `deepseek`, `gemini`, `perplexity`, `windsurf`, `copilot`, `openrouter`, `groq`, `api`, `llm`, `token`, `suno`, `midjourney`, `vllm`, `runpod`
  - 딜/우회: `优惠`, `订阅`, `额度`, `免费`, `福利`, `折`, `活动`, `兑换`, `羊毛`, `白嫖`, `土区`, `尼日利亚`, `埃及`, `阿根廷`, `印度`, `拼车`, `车位`, `倒卖`, `BIN`, `绑卡`, `破限`, `逆向`, `降价`, `低价`, `coupon`, `promo`, `discount`, `deal`, `credit`

### 2) Reddit (`RedditClient`)
- **수집 방식:** 10분 주기마다 단일 통합 메가 쿼리로 1회만 호출하여 429 차단을 방어하고 전체 AI 서비스의 우회/지역가격/트릭/크레딧을 광범위하게 수집.
- **전용 쿼리:**
  ```text
  (ChatGPT OR Claude OR Cursor OR Perplexity OR OpenRouter OR Copilot) 
  ("regional pricing" OR VPN OR Turkey OR Nigeria OR Egypt OR cheaper OR trick OR bypass OR glitch OR BIN OR "promo code" OR voucher OR coupon OR "free credits" OR "startup credits" OR "student discount")
  ```

### 3) X / Twitter (`XClient`)
- **수집 방식:**
  - **공격적 쿼리:**
    ```text
    (ChatGPT OR "ChatGPT Plus" OR Claude OR "Claude Pro" OR Cursor OR "Cursor Pro" OR Perplexity OR "Perplexity Pro" OR OpenAI OR OpenRouter OR "API credits") 
    ("regional pricing" OR "VPN" OR "Turkey" OR "Nigeria" OR "Egypt" OR "India" OR "cheaper" OR "trick" OR "bypass" OR "BIN" OR "promo code" OR "coupon" OR "voucher" OR "discount" OR "free credits" OR "glitch" OR "free trial") 
    -is:retweet -filter:replies
    ```
  - **네거티브 필터:** `discount-rate`, `treasury`, `bonds`, `earnings`, `bofa`, `btc`, `hedge fund`, `selloff` 등이 포함된 금융 노이즈 트윗 자동 제거.

### 4) V2EX (`V2EXClient`)
- **수집 방식:** 중국어 및 영어 주요 키워드(`AI 优惠`, `Claude 优惠`, `Cursor 订阅`, `API 额度`, `AI 土区`, `AI 订阅`, `AI discount`)를 병렬 조회하여 최신 토픽 수집.

---

## 4. 중복 방지 및 심층 평가 메커니즘 (어드버설 컨센서스 반영)

### 1) 인덱스 이력 주입 (`[D1..Dn]`)
- 최근 24시간 내 보고된 딜 목록을 `seen_topics.json`에서 읽어 초경량 1줄 요약 포맷으로 프롬프트에 주입:
  ```text
  <recent_reported_topics>
  [D1] (2시간 전 보고됨) OpenRouter | GPT-5.6 Sol API 50% 인하 | GPT-5.6 Sol 모델 API 단가 50% 인하
  [D2] (5시간 전 보고됨) Modelflare | 5 RMB 가입 크레딧 프로모션 | 신규 가입 5 RMB 지급 및 과금 계수 할인
  </recent_reported_topics>
  ```
- 프롬프트 토큰 오버헤드: 200토큰 미만.

### 2) Luna 단일 문맥 액션 태깅
- **`[ACTION: NEW]`**: 완전히 새로운 프로모션 (텔레그램 브리핑 발송 + `seen_topics.json` 등록)
- **`[ACTION: DUPLICATE_OF D#]`**: 기보고된 D# 딜의 단순 재인용, 리트윗, 실사용 잡담, 동일 프로모션 (알림 생략)
- **`[ACTION: UPDATE_TO D#: STATUS]`**: 기보고된 딜의 중대 상태 변화 (`EXPIRED`, `PRICE_CHANGE`, `NEW_CODE`)
  - `EXPIRED`는 즉시 알림 발송
  - 일반 업데이트는 4시간 쿨다운 적용으로 바이럴 에코 도배 방지

### 3) 구분자 블록 마크다운 파싱 (`=== DEAL ===`)
- JSON 문자열 임베딩 시 발생하는 큰따옴표/줄바꿈 이스케이프 파싱 에러를 원천 제거하기 위해 표준 블록 구분자(`=== DEAL ===`) 직접 파싱.

### 4) 원자적 상태 파일 기록 (Crash Robustness)
- `save_json_atomic()`: 임시 파일 작성 후 `os.replace`로 원자적 교체하여 프로세스 강제 종료 시 0바이트 파일 손상 방지.
- 소켓 타임아웃 300초 적용 및 평가 에러 발생 시에도 `seen_urls`를 안전 커밋하여 에러 무한 루프 방지.

---

## 5. 운영 및 유지보수 명령어

### 1) 타이머 및 서비스 상태 확인
```bash
# 타이머 활성 상태 및 다음 실행 시각 확인
systemctl --user list-timers happy-search-ai-deals.timer

# 서비스 유닛 상태 확인
systemctl --user status happy-search-ai-deals.service
```

### 2) 수동 즉시 실행 테스트
```bash
# 서비스를 즉시 1회 트리거
systemctl --user start happy-search-ai-deals.service

# 또는 직접 파이썬 스크립트 실행
python3 /home/user01/scripts/happy_search_ai_deals.py
```

### 3) 실시간 로그 및 토픽 상태 모니터링
```bash
# 실행 로그 확인
tail -f ~/.config/happy-search/cron.log

# 현재 추적 중인 활성 딜 토픽 확인
cat ~/.config/happy-search/seen_topics.json | jq .
```
