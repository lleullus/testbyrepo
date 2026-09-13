# Plan 001: Stock Oracle 경로 복원 및 슬롯 4 라이브 프롬프트 실행 계획

## 1. Product Contract and Baseline Evidence

- Target Ticket: `/home/user01/project/oracle/oracle-browser-slots/docs/planning/work/oracle-browser-slots-stock-restoration/tickets/TICKET-001.md`
- Parent Spec: `/home/user01/project/oracle/oracle-browser-slots/docs/planning/work/oracle-browser-slots-stock-restoration/SPEC.md`
- Behavior Authority: `docs/planning/behavior/contexts/oracle-browser-managed-slots.md`
- Evidence Baseline:
  - `/home/user01/tmp/oracle-browser-slots-rollback-failure-handoff.md` (사용자 승인 증거 기반)
  - Git HEAD `1800689b` (`Wait for browser warmup before slot preparation`)
  - 슬롯 4(포트 19225) 기동 확인 및 WSLg 환경 준수 (`DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-0`, `XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir`)

## 2. Obligations and Scope

- **달성 의무**:
  - 래퍼 수준의 임의 사전 차단(`_prepare_strict_destination`, 강제 탭 고정 등)이 영구 배제된 상태 유지.
  - 슬롯 4의 런타임 CDP 세션에서 불필요한 잔여 에러 탭(`Try again`)을 안전하게 정리하고 단일 정상 ChatGPT 프로젝트 세션 확보.
  - stock Oracle 실행을 통해 고유 nonce 프롬프트를 전송하고 exit code 0으로 응답을 수신.
  - 실행 종료 즉시 슬롯 4가 `status: 사용 가능`, `occupancy: null`로 복귀함을 확인.
- **보존 경로**:
  - `JobRunner`의 argv-preserving child 실행 구조 및 환경변수 전달 경로.
  - 관리 슬롯 1~5, 10의 격리된 프로필 및 생명주기.
- **Non-Goals**:
  - 롤백된 커밋 `6306d498` 및 `d6d548b8`의 대규모 모델/추론 로직 병합.
  - 래퍼 내부에 새로운 웹 차단/재시도 게이트 추가.
  - 가상 단위 테스트 통과만으로 라이브 검증을 대체하는 행위.

## 3. Cause Analysis and Structural Architecture

- **문제 원인 분석**:
  - 과거 커밋 `6ec078be`는 stock Oracle이 child로 실행되기 전에 래퍼가 미리 ChatGPT 프로젝트 페이지의 DOM 요소를 strict하게 점검하려 했음.
  - 네트워크 지연이나 일시적 UI 리로드(`Try again`) 상태에서 래퍼가 예외(`OracleTransportError`)를 던져 stock Oracle의 정상 전송 시도 자체를 원천 차단함.
- **해결 구조**:
  - 현재 HEAD `1800689b`에서는 래퍼가 브라우저 DOM을 사전 검열하지 않으며, 슬롯 할당 및 환경변수(`ORACLE_BROWSER_CDP_PORT=19225`) 주입 후 제어권을 stock Oracle에 온전히 넘김.
  - 슬롯 4 내부에서 이전 시도로 남아 있는 불필요한 복제 탭(`Try again`)을 CDP `/json/close`로 정리하여 stock Oracle이 깨끗한 프로젝트 세션과 통신하도록 유도.

## 4. State Writers, Readers, and Owners

- `SlotService` / `SlotAllocator`: 슬롯 4의 점유 잠금 파일(`/home/user01/.oracle/browser-slots/slot-4.lock`) 및 상태 파일 소유.
- `JobRunner`: stock Oracle child 프로세스를 Popen으로 실행하고 생명주기 관리.
- `stock Oracle` (`/home/user01/.nvm/versions/node/v24.18.0/bin/oracle`): Chrome CDP(포트 19225)에 연결하여 ChatGPT 대화 세션을 주도.
- `Chrome Browser` (포트 19225): 프로필 `/home/user01/.oracle/browser-profiles/slot-4` 소유.

## 5. Implementation and Verification Steps

### Step 1: 베이스라인 정적 검사 (Discriminating Check 1)
- `oracle_browser_slots/runner.py` 및 `cdp.py`에 `_prepare_strict_destination` 및 strict pre-child 게이트가 완전히 부재함을 확인.
- Git 트래킹 작업 트리가 clean HEAD `1800689b`임을 확인.

### Step 2: 슬롯 4 런타임 세션 정리 및 준비 (Discriminating Check 2)
- `http://127.0.0.1:19225/json/list`를 조회하여 현재 열려 있는 4개 탭 중 불필요한 에러 탭을 정리.
- `curl -s http://127.0.0.1:19225/json/close/<targetId>`를 안전하게 호출하여 `ChatGPT - prom` 정상 탭을 제외한 잔여 중복 탭을 정리.
- 대상 탭의 URL이 정상 ChatGPT Project URL(`https://chatgpt.com/g/g-p-6a66d302e9f08191a0f8e569b2fe3f68-prom/project`)임을 확인.

### Step 3: Implementer Self-Check 실행
- 고유한 타임스탬프 기반 nonce(`VERIFY_SMOKE_SELFCHECK_<timestamp>`)를 생성.
- 아래 명령으로 stock Oracle 라이브 프롬프트 실행:
  ```bash
  DISPLAY=:0 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir \
  ./bin/oracle-browser-slots run --slot 4 --job-id selfcheck-<timestamp> -- \
    /home/user01/.nvm/versions/node/v24.18.0/bin/oracle --wait \
    -p "Reply with exactly: VERIFY_SMOKE_SELFCHECK_<timestamp>"
  ```
- 프로세스 exit code가 0이고, 표준 출력에 nonce 응답이 포함됨을 관측.

### Step 4: 자원 점유 해제 확인
- `./bin/oracle-browser-slots status --slot 4` 실행하여 `status: 사용 가능`, `occupancy: null` 확인.

## 6. Verifier Handoff Condition

- 위 Step 1~4의 self-check가 모두 완료되고, TICKET-001의 AC-1부터 AC-5까지 충족됨을 확인한 뒤, Final Verifier(`opencodex-gpt5.6-sol-medium`)에게 새로운 고유 nonce(`VERIFY_SMOKE_FINAL_<timestamp>`)를 통한 독립적인 라이브 검증을 위임한다.
