# 오라클 브라우저 슬롯별 워크스페이스 통합 — 상세 설계

버전: v0.1 (검토 요청용 초안)  
대상 저장소: `/home/user01/project/oracle` (stock Oracle `@steipete/oracle` 0.16.1 + 커스텀 래퍼 `oracle-browser-slots`)  
상태: 설계 검토 대기 (구현 전)

---

## 1. 배경과 목표

### 1.1 사용자 요구

> "특정 슬롯에서 GPT를 사용할 때, 특정 ChatGPT 워크스페이스(프로젝트 폴더) 주소로 자동 이동해서 프롬프트를 입력하게 하고 싶다."

- 슬롯마다 다른 워크스페이스가 기본값으로 연결되어야 한다.
- 일부 슬롯만 매핑할 수 있어야 하며, 매핑되지 않은 슬롯은 기존 동작을 유지해야 한다.
- 실행 시 호출자가 `--chatgpt-url`을 명시하면 그 값이 우선해야 한다.

### 1.2 계층 구조 (왜 이 설계가 필요한가)

현재 시스템은 두 계층으로 나뉜다.

| 계층                 | 역할                                             | 슬롯 개념      | 워크스페이스 처리               |
| -------------------- | ------------------------------------------------ | -------------- | ------------------------------- |
| stock Oracle CLI     | ChatGPT 브라우저 자동화(네비게이션·입력·수집)    | 없음           | 실행 단위당 `--chatgpt-url` 1개 |
| oracle-browser-slots | 슬롯 1..5, 고정 포트, 프로필, 점유/큐, argv 검증 | 있음(1차 개념) | 전역 env 1개만 존재             |

stock Oracle에는 "슬롯"이라는 개념이 없고, `--browser-port`는 단지 Chrome DevTools 포트일 뿐이다.  
슬롯·포트·프로필·점유는 전부 커스텀 래퍼(`oracle-browser-slots`)의 설계이므로, "슬롯별 워크스페이스" 정책도 래퍼가 소유해야 한다. **stock Oracle은 무수정을 원칙으로 한다.**

### 1.3 키(key) 선택: 포트가 아니라 슬롯

- 포트는 `Settings.slot(slot_id)`에서 `port_base + slot_id - 1`로 파생된다 (`oracle_browser_slots/model.py:117-124`).
- `ORACLE_BROWSER_SLOTS_PORT_BASE`가 바뀌면 포트가 모두 이동한다. 포트를 키로 삼으면 설정이 깨진다.
- 슬롯에는 프로필(`slot-1`..`slot-5`)과 계정이 묶여 있어, "슬롯 = 계정 = 워크스페이스"가 의미상 일관된다.
- **결정: 매핑 키는 슬롯 ID(`1|2|3|4|5`)로 한다.**

---

## 2. 현재 동작 요약 (설계 근거)

### 2.1 stock Oracle (무수정 대상)

| 항목                                    | 위치                                      | 내용                                                        |
| --------------------------------------- | ----------------------------------------- | ----------------------------------------------------------- |
| `--chatgpt-url` 옵션 선언               | `bin/oracle-cli.ts:635`                   | 워크스페이스/폴더 URL 지정                                  |
| `--browser-url` 은닉 alias              | `bin/oracle-cli.ts:642`                   | `--chatgpt-url`과 동일 의미                                 |
| `--browser-port`/`--browser-debug-port` | `bin/oracle-cli.ts:719,724`               | Chrome DevTools 포트 고정                                   |
| URL 해석                                | `src/cli/browserConfig.ts:190-191`        | `options.chatgptUrl ?? options.browserUrl` → 정규화         |
| 포트 해석                               | `src/cli/browserConfig.ts:207,300-307`    | `browserPort ?? browserDebugPort`, 1..65535 검증            |
| 실행 설정 병합                          | `src/browser/config.ts:75-79,111-113`     | env `ORACLE_BROWSER_PORT`도 `debugPort`로 수용              |
| Chrome 실행                             | `src/browser/chromeLifecycle.ts:18,43-49` | `debugPort`를 chrome-launcher `port`로 전달                 |
| 로컬 모드 네비게이션                    | `src/browser/index.ts:1356-1393`          | base URL → 로그인 → `config.url`(워크스페이스)로 이동       |
| 원격 Chrome 모드 네비게이션             | `src/browser/index.ts:3060-3067`          | `config.resumeConversationUrl` 없으면 `config.url`로 이동   |
| 입력/전송                               | `src/browser/index.ts:3218-3224`          | 같은 탭에서 `runProviderSubmissionFlow(chatgptDomProvider)` |

핵심: 원격 Chrome 모드(`--remote-chrome`)에서도 `config.url`이 곧 이동·입력 대상이다. 즉 **래퍼가 `--chatgpt-url`을 argv에 주입하면 stock은 그 워크스페이스로 이동해서 입력한다.**

### 2.2 oracle-browser-slots (변경 대상)

| 항목                     | 위치                                                                         | 내용                                                                                |
| ------------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 슬롯 정의                | `oracle_browser_slots/model.py:13,117-124`                                   | `SLOT_IDS=(1,2,3,4,5)`, 포트 파생, 프로필 경로                                      |
| 설정                     | `oracle_browser_slots/model.py:44-115`                                       | `Settings.from_env()`, 전부 env 기반                                                |
| 전역 워크스페이스 env    | `oracle_browser_slots/model.py:52,111`                                       | `ORACLE_BROWSER_SLOTS_CHATGPT_URL` (기본 `https://chatgpt.com/`)                    |
| Chrome 시작 명령         | `oracle_browser_slots/launcher.py:101-113`                                   | `--remote-debugging-port=<slot.port>` + 초기 탭 `settings.chatgpt_url`              |
| run 경로                 | `oracle_browser_slots/runner.py:58-146`                                      | 슬롯 명시, 검증 → 파일 준비 → 점유 → 실행                                           |
| submit 경로              | `oracle_browser_slots/runner.py:168-192` (`claim_for_auto`) + `allocator.py` | 첫 가용 슬롯 자동 배정                                                              |
| argv 검증/주입 공통 지점 | `oracle_browser_slots/runner.py:428-509`                                     | `_validated_oracle_command(slot_id, argv)`                                          |
| 필수 플래그              | `oracle_browser_slots/runner.py:23-26`                                       | `--engine browser`, `--browser-model-strategy current` (누락 시 주입, 충돌 시 거부) |
| 금지 transport 플래그    | `oracle_browser_slots/runner.py:27-33`                                       | manual-login/chrome-path/keep-browser/remote-host/bridge                            |
| CLI 진입                 | `oracle_browser_slots/cli.py:17-178`                                         | prepare/status/run/submit/followup, `Settings.from_env()` 실패 시 exit 2            |
| followup                 | `oracle_browser_slots/cli.py:93-101`, `followup.py`                          | 원본 슬롯 고정, 대화 URL 재개                                                       |
| 테스트                   | `tests/test_slots.py` 등                                                     | unittest 스타일, FakeLauncher/FakeCDP 패턴                                          |

`run`(runner.py:71)과 `submit`(runner.py:175) 모두 `_validated_oracle_command`를 통과하므로, **슬롯별 `--chatgpt-url` 주입은 이 한 지점만 고치면 두 경로에 모두 적용된다.**

---

## 3. 요구사항

### 3.1 기능

- R1. 슬롯별 기본 워크스페이스 URL을 설정할 수 있다 (부분 매핑 허용).
- R2. `run --slot N`과 `submit`(자동 배정) 모두에서, 해당 슬롯이 매핑을 가지면 `--chatgpt-url`이 자동 주입된다.
- R3. 호출자가 `--chatgpt-url` 또는 `--browser-url`을 명시하면 그 값이 우선하고 주입하지 않는다.
- R4. 매핑이 없는 슬롯은 argv가 변경되지 않는다 (기존 동작 100% 유지).
- R5. `prepare --slot N` 직후 Chrome 초기 탭도 해당 슬롯의 워크스페이스여야 한다.
- R6. `followup`은 기존 대화 URL(`resumeConversationUrl`)을 재개하므로 슬롯 매핑을 적용하지 않는다 (stock 동작에 위임).

### 3.2 비기능

- N1. stock Oracle 소스 무수정.
- N2. 설정 오류(JSON 파싱 실패, 잘못된 키/URL)는 기존 패턴대로 `Settings.from_env()`에서 `ValueError` → CLI exit 2.
- N3. 주입되는 값은 반드시 URL이어야 하며, `--`로 시작하는 등 argv 플래그로 해석될 수 있는 값은 거부.
- N4. env 미설정 환경은 동작 불변.

---

## 4. 설계 결정 (ADR 요약)

### D1. 매핑 키는 슬롯 ID

- 포트 파생(`port_base + slot_id - 1`)에 내성이 있어야 하므로 슬롯 ID를 키로 쓴다.
- 설정 키는 문자열 `"1"`, `"2"`, `"3"`, `"4"`, `"5"`만 허용한다 (JSON 객체 키 특성상 문자열).

### D2. 설정 형식: env JSON 맵 (설정 파일 도입 없음)

- 기존 `Settings`가 전부 env 기반이므로 일관성을 유지한다.
- 신규 env: `ORACLE_BROWSER_SLOTS_CHATGPT_URLS` — JSON 객체 `{"1": "...", "2": "..."}`.
- 우선순위: 슬롯 매핑 > 기존 전역 `ORACLE_BROWSER_SLOTS_CHATGPT_URL` > 기본 `https://chatgpt.com/`.
- 설정 파일 도입은 이후 필요가 생기면 별도 설계로 확장한다.

### D3. 주입 지점: `JobRunner._validated_oracle_command`

- `run`(runner.py:71)과 `submit`→`claim_for_auto`(runner.py:175)가 공통으로 통과하는 유일한 argv 검증 지점이다.
- 파일 첨부 준비(`prepare_file_request`)보다 앞이므로, ZIP 번들이 만들어지는 요청에도 동일하게 적용된다.
- `validate_auto_command(slot_id=None)` 경로(러너 선검증)는 슬롯이 아직 정해지지 않았으므로 주입하지 않는다.

### D4. 우선순위

```
호출자 명시 --chatgpt-url / --browser-url  (있으면 주입 생략)
  > 슬롯 매핑 ORACLE_BROWSER_SLOTS_CHATGPT_URLS[slot_id]
  > 전역 ORACLE_BROWSER_SLOTS_CHATGPT_URL
  > 기본 https://chatgpt.com/                  (기본값과 같으면 주입 생략)
```

- transport 플래그(예: `--remote-chrome`)는 래퍼가 강제·충돌 거부하지만, URL은 workflow 옵션이므로 호출자 명시를 우선한다. 이는 "가끔 다른 워크스페이스에서 실행하고 싶다"는 합법적 사용을 막지 않는다.
- 기본값과 동일한 URL은 주입하지 않아 argv 변경을 최소화한다.

### D5. 중복/alias 처리

- `--chatgpt-url`과 `--browser-url`은 stock에서 동일 의미(`browserConfig.ts:190`)이므로, 둘 중 하나라도 명시되면 호출자 명시로 간주한다.
- 같은 플래그의 중복 지정(예: `--chatgpt-url A --chatgpt-url B`)은 기존 `REQUIRED_ORACLE_FLAGS` 처리 방식(runner.py:482-497)과 동일하게 거부한다.

### D6. launcher 초기 탭도 슬롯 URL

- `launcher.py:_command`의 마지막 인자를 `settings.slot_chatgpt_url(slot.slot_id)`로 변경한다.
- 단, 초기 탭은 stock 실행 시 `config.url`로 다시 이동하므로, 실제 워크스페이스 보장은 D3의 argv 주입이 담당한다. launcher 변경은 `prepare` 직후 운영자 화면 일관성을 위한 것이다.

### D7. followup은 매핑을 적용하지 않는다

- stock은 `resumeConversationUrl`이 있으면 그 URL로 이동한다(`index.ts:3061`).
- 래퍼 `followup`(cli.py:93-101)은 원본 대화의 정확한 URL을 재개하는 것이 목적이므로 슬롯 매핑을 덮어쓰면 안 된다. **변경 없음.**

### D8. 검증 규칙

| 대상        | 규칙                               | 실패 시               |
| ----------- | ---------------------------------- | --------------------- |
| JSON 문법   | `json.loads` 성공                  | `ValueError` → exit 2 |
| 키          | 숫자 문자열 `1`부터 `5`만 허용     | `ValueError` → exit 2 |
| URL 스킴    | `http:` 또는 `https:`              | `ValueError` → exit 2 |
| URL 호스트  | 비어있지 않은 hostname             | `ValueError` → exit 2 |
| argv 안전성 | 값이 `-` 또는 `--`로 시작하면 거부 | `ValueError` → exit 2 |

호스트 제한(`chatgpt.com`/`chat.openai.com` 강제)은 두지 않는다. 래퍼는 운영자 본인의 env를 신뢰하되, "플래그로 오인될 값"만 차단한다. (검토 질문 Q4 참고)

---

## 5. 파일별 변경 계획

### 5.1 `oracle_browser_slots/model.py`

1. 상수 추가: `DEFAULT_CHATGPT_URL = "https://chatgpt.com/"`.
2. `Settings`에 필드 추가:
   ```python
   slot_chatgpt_urls: dict[int, str] = field(default_factory=dict)
   ```
3. `from_env`:
   - 기존 `chatgpt_url` 기본값을 `DEFAULT_CHATGPT_URL`로 통일.
   - `ORACLE_BROWSER_SLOTS_CHATGPT_URLS`를 `json.loads` 후 검증(키·URL·argv 안전성), `dict[int, str]`로 변환.
   - 파싱/검증 실패는 기존 `ValueError` 패턴 유지 (cli.py:57-60에서 exit 2).
4. 헬퍼 추가:
   ```python
   def slot_chatgpt_url(self, slot_id: int) -> str:
       return self.slot_chatgpt_urls.get(slot_id, self.chatgpt_url)
   ```

### 5.2 `oracle_browser_slots/runner.py`

1. `_validated_oracle_command`의 `values`에 추적 대상 추가:
   ```python
   values["--chatgpt-url"] = []
   values["--browser-url"] = []
   ```
   (기존 파싱 루프 runner.py:457-480은 `values`의 모든 플래그를 자동으로 인식하므로 파싱은 그대로 동작)
2. 주입 로직 (`normalized` 구성부, runner.py:505-509 근처):
   ```python
   slot_url: str | None = None
   if slot_id is not None:
       slot_url = self.service.settings.slot_chatgpt_url(slot_id)
   user_explicit = bool(values["--chatgpt-url"] or values["--browser-url"])
   if (
       slot_id is not None
       and not user_explicit
       and slot_url != DEFAULT_CHATGPT_URL
   ):
       normalized.extend(("--chatgpt-url", slot_url))
   ```
3. 중복 거부: `--chatgpt-url`이 2회 이상이면 기존 방식과 동일한 `OracleTransportError`(중복 지정)를 발생시킨다. `--browser-url`도 동일하게 추적하되 주입 대상은 아니다.

### 5.3 `oracle_browser_slots/launcher.py`

1. `_command(slot)`에서 `self.settings.chatgpt_url` → `self.settings.slot_chatgpt_url(slot.slot_id)`로 교체.

### 5.4 `README.md`

1. env 표에 `ORACLE_BROWSER_SLOTS_CHATGPT_URLS` 추가 (형식·우선순위·예시).
2. `run`/`submit` 섹션에 "슬롯별 `--chatgpt-url` 자동 주입" 동작과 호출자 명시 우선 규칙 문서화.
3. `prepare` 섹션에 초기 탭이 슬롯 워크스페이스가 됨을 문서화.

### 5.5 테스트

신규 파일 `tests/test_workspace_mapping.py` (기존 unittest 스타일):

| 테스트                                | 검증 내용                                         |
| ------------------------------------- | ------------------------------------------------- |
| `test_from_env_default`               | env 없이 `slot_chatgpt_url`이 기본값              |
| `test_from_env_global_only`           | 전역만 설정 시 모든 슬롯이 전역 값                |
| `test_from_env_slot_map`              | 슬롯 매핑이 전역보다 우선                         |
| `test_from_env_partial_map`           | 일부 슬롯만 매핑, 나머지는 전역/기본              |
| `test_from_env_invalid_json`          | 잘못된 JSON → `ValueError`                        |
| `test_from_env_invalid_key`           | `"4"`/`"x"` 키 → `ValueError`                     |
| `test_from_env_invalid_url`           | 비-http(s), 호스트 없음, `--` 시작 → `ValueError` |
| `test_run_injects_slot_url`           | `run` 경로에서 매핑 URL 주입                      |
| `test_submit_injects_slot_url`        | `claim_for_auto` 경로에서 매핑 URL 주입           |
| `test_explicit_url_wins`              | 호출자 `--chatgpt-url` 명시 시 미주입             |
| `test_browser_url_alias_wins`         | `--browser-url` 명시 시 미주입                    |
| `test_duplicate_chatgpt_url_rejected` | 중복 지정 거부                                    |
| `test_no_mapping_no_injection`        | 매핑 없는 슬롯 argv 불변                          |
| `test_validate_auto_no_injection`     | `slot_id=None` 경로에서는 미주입                  |
| `test_launcher_uses_slot_url`         | `_command`가 슬롯 URL을 초기 탭으로 사용          |

---

## 6. 데이터 흐름 예시

설정:

```bash
export ORACLE_BROWSER_SLOTS_CHATGPT_URLS='{"2":"https://chatgpt.com/g/g-p-xxxx/project-b"}'
```

| 시나리오            | 명령                                                | 결과 argv (변경분)                                            |
| ------------------- | --------------------------------------------------- | ------------------------------------------------------------- |
| A. 슬롯 2 자동 배정 | `submit ... -- <oracle> --engine browser -p "..."`  | `--chatgpt-url https://chatgpt.com/g/g-p-xxxx/project-b` 주입 |
| B. 매핑 없는 슬롯 1 | `run --slot 1 ...`                                  | 주입 없음, 기존 동작                                          |
| C. 호출자 명시      | `run --slot 2 ... --chatgpt-url https://.../custom` | 호출자 값 유지                                                |
| D. prepare          | `prepare --slot 2`                                  | Chrome 초기 탭 = 슬롯 2 워크스페이스                          |
| E. followup         | `followup ...`                                      | 매핑 미적용, 대화 URL 재개                                    |

---

## 7. 영향·리스크

| 리스크                     | 설명                                                                                                                              | 대응                                                                                                     |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Cloudflare/로그인          | stock의 이중 이동(base → target)이 그대로 적용됨. 워크스페이스 접근은 슬롯 계정 권한에 의존                                       | 매핑 URL은 해당 슬롯 계정이 접근 가능한 워크스페이스여야 함. 기존 대응(수동 clearance, cookie sync) 동일 |
| 기존 동작 회귀             | env 미설정 시 주입 없음 → argv 불변                                                                                               | N4 테스트로 보장                                                                                         |
| argv 오염                  | 슬롯 URL이 플래그로 해석될 가능성                                                                                                 | D8 검증(`-`/`--` 시작 거부)                                                                              |
| `--browser-url` alias 혼동 | stock에서 동일 의미인데 래퍼가 한쪽만 인식하면 사용자 혼란                                                                        | 둘 다 추적, 둘 중 하나라도 있으면 명시로 간주                                                            |
| 전역 env 의미 변화         | 기존 `ORACLE_BROWSER_SLOTS_CHATGPT_URL`은 launcher 초기 탭에만 반영됐는데, 이 설계는 run/submit argv에도 반영(기본값과 다를 경우) | 의도된 승격이며 README에 명시 (검토 질문 Q2)                                                             |
| followup과의 상호작용      | 슬롯 매핑이 대화 재개를 방해하면 안 됨                                                                                            | D7: followup 경로는 변경하지 않음                                                                        |

---

## 8. 검증 계획

1. 단위 테스트: 5.5 표 전체.
2. 기존 회귀: `python -m pytest tests/` 전체 통과.
3. dry-run 스모크 (Chrome 비사용):
   ```bash
   ORACLE_BROWSER_SLOTS_CHATGPT_URLS='{"2":"https://chatgpt.com/g/g-p-xxxx/project-b"}' \
   ./bin/oracle-browser-slots run --slot 2 --job-id smoke-001 -- \
     /home/user01/.nvm/versions/node/v24.18.0/bin/oracle \
     --engine browser --browser-model-strategy current \
     --dry-run summary -p "smoke"
   ```
   argv 주입 자체는 단위 테스트로 확인 (dry-run 출력에는 argv가 노출되지 않음).
4. (선택) 슬롯 2 라이브 1회: 매핑된 워크스페이스에서 실제 입력·응답 확인.

---

## 9. 오픈 질문 (검토 요청 대상)

- Q1. 설정 형식: env JSON이 현재 패턴과 일치하지만, 슬롯별 설정 파일(예: `~/.oracle/browser-slots/settings.json`)이 더 적절한가?
- Q2. 기존 전역 `ORACLE_BROWSER_SLOTS_CHATGPT_URL`을 run/submit argv 주입으로 승격하는 것이 맞는가? (기존에는 launcher 초기 탭에만 반영)
- Q3. 주입 정책: "기본값과 다를 때만 주입"이 최소 변경인가, 아니면 항상 주입이 더 예측 가능한가?
- Q4. URL 검증 수준: `http/https` + hostname + `-`/`--` 시작 거부로 충분한가, 아니면 `chatgpt.com`/`chat.openai.com` 호스트만 허용해야 하나?
- Q5. 테스트는 신규 파일(`tests/test_workspace_mapping.py`) 분리가 맞는가, 기존 `tests/test_slots.py`에 합치는 것이 맞는가?
