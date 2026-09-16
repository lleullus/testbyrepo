# PLAN-001 — BLOCK-003 백엔드 출력 거버넌스·결과 보존·운영 감독 실행 방법

- 작성: PlanGeminiB3 (Gemini 3.8 Flash), 2026-09-16.
- Project Root: `/home/user01/project/webterm/ttyd-1.7.7` (이하 상대 경로 기준).
- 대상 Scope: `docs/planning/work/output-governance-result-retention-supervision/SCOPE.md` (상태: `ready`, SHA-256 `8ebb4316f5e96f34db8a38d913c3e44016f25db0a15a11ec8b0b15c1f9d1fcbb`).
- 대상 Product Thesis: `docs/planning/product-thesis/android-web-terminal/THESIS-001.md` (CALIBRATED 2026-09-15, SHA-256 `81003a0783df4f7876ad603aafd47c1b96ba768cec03237ed72e543ce9eb642a`).
- 대상 Transition Authority: `docs/planning/baseline/BASELINE-001.md` (APPROVED r2-2026-09-15, SHA-256 `f3b389347779f21b4e0fa1cad49ab748d509181763acb13cd39152416baf27e1`).
- 상태: 독립 Plan Review 대기 (`/home/user01/tmp/iis-plan-reviews/webterm-block003-plan-review.json`). 이 문서는 실행 방법론이며 ADMIT, 구현 완료 또는 검증 판정이 아니다.
- Planner 권한 한계: 본 Plan 파일 생성만 수행. 제품 소스, 설정, 런타임, 프로덕션 포트 7683 데몬, crontab, systemd, Funnel에 대한 일체의 변경을 가하지 않았다.

---

## 1. 정확한 결속과 보존 경계

### 1.1 원본 결속 대조표

| 원본 문서 | 경로 및 식별자 | SHA-256 / 승인 상태 | 핵심 결속 요건 |
|---|---|---|---|
| **Scope** | `docs/planning/work/output-governance-result-retention-supervision/SCOPE.md` | `8ebb4316f5e96f34db8a38d913c3e44016f25db0a15a11ec8b0b15c1f9d1fcbb` (ready) | Outcome 및 B3-E1~B3-E10 Acceptance 전 항목, 14대 반례 차단 |
| **Thesis** | `docs/planning/product-thesis/android-web-terminal/THESIS-001.md` | `81003a0783df4f7876ad603aafd47c1b96ba768cec03237ed72e543ce9eb642a` (CALIBRATED) | NB2, NB3, NB9, NB11, I7, §4, §6(14대 반례), §7(SC-1~SC-8) |
| **Baseline** | `docs/planning/baseline/BASELINE-001.md` | `f3b389347779f21b4e0fa1cad49ab748d509181763acb13cd39152416baf27e1` (APPROVED r2) | BLOCK-003, B3-E1~B3-E10, G1~G8, P1~P7, Safe Abort/Continuation |

Scope 유효성은 canonical 검증 도구(`/home/user01/project/iis-skills/scope-shaper/tools/validate_scope.py`)를 통해 `VALID` (status: `ready`, product authority 및 transition authority 해시 일치)로 확인되었다.

### 1.2 선행 이정표 성립 근거
- `BLOCK-001`: `docs/planning/work/session-continuity-liveness-recovery/SCOPE.md` (`Status: done`, SHA-256 `51de46c8f5cc9df30b8adb07c478c52db4e3112422a2f7ff44db4c62e582f336`).
- `BLOCK-002`: `docs/planning/work/mobile-touch-keyboard-takeover/SCOPE.md` (`Status: done`, SHA-256 `9ccb9acf122579d84e52fd2f3b00867b87646a3d64cb88b1b964d8a6fc99e2ea`).
- 기검증 결과: VerifyGeminiB2R10 VERIFIED, CoverageGeminiB2R10 COMPLETE (no material gap).
- 현재 작업 트리는 dirty 상태로 BLOCK-001/002의 기전달 소스 변경을 포함하고 있으며, 검증된 후보 실행물 빌드(`build/ttyd` SHA-256 `736629a7950e95ff27ff9b98232b5ddd67958bb4e0680af447da9795626bd560`, `html/dist/inline.html` SHA-256 `1185038553a3f7d0160a294a76e292e40a40af4da59dcc178f9114799bcfe950`)가 보존되어 있다.

### 1.3 HARD_ATOMIC 경계 및 보존/배제 사항
- **HARD_ATOMIC 결합**: 순환 8 MiB tail 및 절사 고지, 포그라운드 TUI 레이아웃 동기화, `EXITED_RETAINED` 9시간 보존 및 1시간 재열람, 32,400초 만료 단일 판정, 프로세스 트리 유한 회수(`SIGHUP` → 대기 → `SIGKILL`), 수용 상한 방어, `systemd` 사용자 서비스 unit/`logrotate` 설정, `CUSTOMIZATION.md` 최신화를 동일한 호환 실행물 단위로 통합 전달한다.
- **엄격 보존 사항**:
  1. BLOCK-001/002에서 확립된 wire v3 세션 핸드셰이크, 128-bit `sessionStorage` 탭 결속, 단일 소유자 CAS Takeover, displaced 상태 전이, 0바이트 복구 제스처, 터치/가상키보드 분리, 한글 IME 조합 무결성, 360/390 CSS px 12개 툴바 요소, 단일 기하 수렴(`resizes-content`).
  2. 운영 중인 포트 7683 (PID 202, crontab `@reboot` 기동, live OMP 세션)의 프로세스 및 세션 연속성.
  3. Tailscale Funnel 외부 라우트(`/terminal` -> `127.0.0.1:7683`).
- **명시적 배제 사항 (Non-Goals)**:
  1. 운영 포트 7683 데몬의 강제 종료 또는 교체 (모든 기능 검증은 포트 7695 등 격리된 후보 실행물에서 수행).
  2. crontab에서 systemd 서비스로의 운영 cutover 실행 (호스트 관리자 권한 및 운영자 승인이 갖춰진 독립 유지보수 경계에서만 수행).
  3. Tailscale 외부 경로에 불필요한 신규 인증 장벽 임의 추가.

---

## 2. 코드 접지: 현행 상태 진단 및 변경 소유권

모든 전제는 현재 소스, 프로세스, 파일시스템을 직접 읽어 `EXISTING`, `PROPOSED`, `UNRESOLVED`로 분류하였다.

### 2.1 진단 및 분류 매트릭스

| 대상 영역 | 현재 구현 (EXISTING) | 제안 변경 (PROPOSED) | 분류 |
|---|---|---|---|
| **출력 링버퍼 거버넌스** | `src/protocol.c:136-150` 버퍼 초과 시 `free(output_buf)` 후 `needs_redraw = true`로 설정하여 누적 출력을 전량 폐기함. | 8 MiB 고정 크기(또는 상한 내 순환) 링버퍼로 최신 `8,388,608 bytes` tail을 유지하고 `output_start`를 전진시키며 `truncated = true` 플래그 및 버려진 바이트 수를 기록. | EXISTING / PROPOSED |
| **포그라운드 레이아웃 동기화** | `src/pty.c:216-231` `pty_signal_foreground()`가 `TIOCGPGRP`로 포그라운드 PGID에 SIGWINCH를 발송함. 클라이언트 `xterm/index.ts`는 동일 크기 재연결 시 resize 전송을 건너뜀. | 동일 크기 재접속 시에도 xterm의 normal/alternate 버퍼를 비파괴 보존하고, 포그라운드 TUI가 화면을 재렌더링하도록 갱신 트리거 및 윈도우 크기 동기화 보장 (Full RIS, 날조 키 전면 배제). | EXISTING / PROPOSED |
| **세션 종료 및 결과 보존** | `src/protocol.c:469-493` `process_exit_cb`에서 `tombstone_add()`, `session_release()`를 즉시 호출하여 세션 테이블에서 제거함. 클라이언트 `xterm/index.ts:1810`은 `exited` 수신 시 "Start New Session"으로 처리. | 단절 중 루트 프로세스 종료 시 `session->state = EXITED_RETAINED`로 전이, exit code/signal 및 최종 8 MiB tail을 보존. 재접속 시 결과 출력 및 exit code 표시, 셸 스폰 0회, PTY write 0 byte, 기한 연장 없음. | EXISTING / PROPOSED |
| **32,400초 수명주기 경계** | `src/protocol.c:22,183-191` `SESSION_GRACE_MAX_SECONDS (9 * 60 * 60)` 상수가 정의되어 있으나 만료와 Takeover의 경합 시 단일 원자 판정 보강 필요. | 단절 시점부터 32,400초 타이머 동작, 만료 시 `session->state = PURGED`로 완전 해제. 유효 Takeover와 만료 경합 시 서버 단일 이벤트 루프 내 원자 판정. | EXISTING / PROPOSED |
| **워커 프로세스 트리 회수** | `src/pty.c:207-214` `pty_kill()`은 `uv_kill(-process->pid, sig)`만 호출하여, 새 세션/그룹을 만든 OMP 서브프로세스 트리를 회수하지 못함. | 세션 소유 프로세스 트리 전체(PGID, `/proc` 기반 하위 트리)에 `SIGHUP` 전송 → 유한 대기(예: 3초) → 잔여 시 `SIGKILL` 에스컬레이션. 미완료 시 `TERMINATING` 유지, 완주 후 `PURGED`. | EXISTING / PROPOSED |
| **수용 상한 (Admission Limits)** | `src/protocol.c:887` `server->max_clients`만 존재하며 세션 수/메모리/프로세스 상한 부재. 초과 시 단순 소켓 거절. | 실행 세션 수, detached 세션 수, `EXITED_RETAINED` 세션 수, 메모리/프로세스 자원 계상. 상한 도달 시 HTTP 503 또는 프로토콜 거절 메시지 반환, 기존 세션 침묵 퇴출 금지. | EXISTING / PROPOSED |
| **systemd 사용자 서비스** | 호스트에 `user@1000.service` 구동 중(`systemd 255.4`, `Linger=yes`), 하지만 ttyd는 crontab `@reboot`으로 구동 중이며 user unit 파일 없음. | `/home/user01/.config/systemd/user/webterm.service` unit 파일 정의 (후보 바이너리, 외부 번들, launcher, 수용 설정, Restart 정책). | EXISTING / PROPOSED |
| **logrotate 설정** | 시스템에 `/usr/sbin/logrotate` 3.21.0 가용. ttyd 로그에 대한 사용자 단위 logrotate 정책 부재. | `/home/user01/.config/logrotate/webterm.conf` 및 상태 파일 정의. 유한 크기(예: 10M), 세대 보존(5회), gzip 압축, copytruncate 정책 검증. | EXISTING / PROPOSED |
| **운영 문서 (CUSTOMIZATION.md)** | `CUSTOMIZATION.md`에 BLOCK-001/002 내용만 반영되어 있고 8 MiB 순환 tail, EXITED_RETAINED, 워커 회수, systemd/logrotate 설명 누락. | `CUSTOMIZATION.md`를 실제 구현/설정 값과 1:1 일치하도록 갱신. | EXISTING / PROPOSED |
| **실제 1h/9h 시간 경계 검증** | 1시간/9시간 장기 검증 환경. | 단축/가상 시간(short grace test)과 실제 시간 경과 관찰의 증거를 명확히 분리하여 계획. | UNRESOLVED |

### 2.2 결정적 소스 및 상태 소유자 식별
1. **출력 링버퍼 소유자**: `src/protocol.c` (`struct tty_session` 내 `output_buf`, `output_len`, `output_start`, `output_end`, `output_cap`, `dropped_output_bytes`, `truncated`).
2. **세션 상태 머신 소유자**: `src/protocol.c` (`SESSION_ACTIVE`, `SESSION_DETACHED_GRACE`, `SESSION_EXITED_RETAINED`, `SESSION_TERMINATING`, `SESSION_PURGED`).
3. **프로세스 수명주기 및 회수 소유자**: `src/pty.c` 및 `src/protocol.c` (`pty_kill_tree()`, `process_exit_cb()`, `session_reap()`).
4. **수용 상한 거버넌스 소유자**: `src/protocol.c` 및 `src/http.c` (`session_admission_check()`, `active_sessions_count`, `retained_sessions_count`).
5. **클라이언트 결과 및 절사 표시 소유자**: `html/src/components/terminal/xterm/index.ts` (`SET_SESSION_STATE` 파서, `truncated` 알림, `exited_retained` 읽기 전용 뷰).

---

## 3. PROPOSED — 하위 컴포넌트별 상세 실행 방법론

### 3.1 [B3-E1, SC-6] 유한 비차단 출력 링버퍼 및 절사 고지
1. **링버퍼 구조체 및 버퍼 불변식**:
   - `SESSION_BACKLOG_MAX`는 정확히 `8 * 1024 * 1024` (8,388,608 bytes).
   - 기존의 `free(session->output_buf)` 및 `needs_redraw = true` 전체 폐기 로직을 전면 제거한다.
   - 새 출력 `len`이 도착했을 때, `session->output_len + len > SESSION_BACKLOG_MAX`인 경우:
     - 넘치는 바이트 수 `overflow = (session->output_len + len) - SESSION_BACKLOG_MAX`를 계산한다.
     - 기존 버퍼의 헤드에서 `overflow`만큼 폐기(전진)하고, `session->dropped_output_bytes += overflow` 및 `session->output_start += overflow`로 갱신한다.
     - 메모리 이동은 단일 연속 버퍼 내 `memmove(session->output_buf, session->output_buf + overflow, session->output_len - overflow)` 또는 원형 링버퍼 인덱싱을 적용하되, 소켓 replay 전송의 단순성을 위해 정규화된 선형 tail 8 MiB를 유지한다.
     - `session->truncated = true` 플래그를 설정한다.
   - 메모리 할당량은 최대 8 MiB로 캡핑되며, 이를 초과하는 무한 보조 큐나 누수는 엄격히 배제된다.
2. **비차단 PTY Drain 보장**:
   - 클라이언트 소켓이 닫혀 있거나 느린 렌더링 중에도 `uv_read_start(process->pty)`는 중단되지 않는다.
   - 커널 PTY 버퍼 포화로 인한 프로세스 데드락 없이 10 MiB 대량 출력 fixture가 정상 완주(`exit 0`)함을 보장한다.
3. **절사 정보의 정직한 프로토콜 전송 및 UI 렌더링**:
   - 클라이언트 재연결 시 `SET_SESSION_STATE` 페이로드의 `replay` 필드에 `{ from: output_start, to: output_end, truncated: true, droppedBytes: dropped_output_bytes }`를 포함한다.
   - 클라이언트(`xterm/index.ts`)는 `truncated === true` 수신 시 상단/오버레이에 "이전 출력이 절사됨 (최신 8 MiB 보존)"을 명시적으로 안내한다. 원시 tail의 바이트 무결성은 보존된다.

### 3.2 [B3-E2] 포그라운드 TUI 레이아웃 동기화 및 비파괴 재그리기
1. **`TIOCGPGRP` 기반 포그라운드 시그널 전달**:
   - `pty_signal_foreground(session->process, SIGWINCH)`를 통해 현재 PTY master fd의 실제 포그라운드 프로세스 그룹(PGID)을 확인하고 SIGWINCH를 전달한다.
   - 포그라운드 프로세스가 없는 경우(`pgid <= 1`) 세션 루트 PID로 폴백한다.
2. **비파괴 상태 보존 및 날조 입력 전면 배제 (NB9, NB10)**:
   - 클라이언트 재접속 시 `terminal.reset()`(Full RIS) 호출을 전면 배제한다.
   - xterm의 normal screen 및 alternate screen 버퍼, 커서 모드를 보존한다.
   - TUI 화면 동기화를 위해 임의의 Enter, ESC, Ctrl+L 날조 입력을 PTY로 주입하는 행위를 전면 금지한다 (PTY 누설 0 byte).
3. **재로드 vs 기존 소켓 재연결 분리 검증**:
   - 새 xterm 인스턴스로의 페이지 새로고침과 기존 xterm 인스턴스의 소켓 재연결 시나리오를 각각 독립적으로 검증한다.

### 3.3 [B3-E3, SC-7] 단절 중 종료 결과 보존과 `EXITED_RETAINED` 1시간 재열람
1. **`process_exit_cb` 전이 로직 수정**:
   - 단절 상태(`session->client == NULL`)에서 루트 프로세스가 종료(`exit_code` 또는 `exit_signal`)되면 세션을 즉시 해제(`session_release`)하지 않는다.
   - 상태를 `SESSION_EXITED_RETAINED`로 전이시키고, `session->exit_code`, `session->exit_signal`, `session->exited_at`을 기록한다.
   - 마지막 PTY read에서 남은 버퍼(EOF 직전 출력)를 완전히 드레인하여 최신 8 MiB tail과 끝 표식을 결속 보존한다.
   - 원래의 9시간 만료 타이머(`expiry_timer`)는 계속 유지된다.
2. **결과 재열람 프로토콜**:
   - 사용자가 재접속(`resumeId`) 시 서버는 세션이 종료되었음을 알리는 `SET_SESSION_STATE` (`state: "exited_retained"`, `exitCode`, `exitSignal`, `replay`)를 전송한다.
   - 백로그 출력을 전송한 뒤 `REPLAY_END`를 전송한다.
   - **불변식 준수**:
     - 새 루트 셸 스폰 횟수: **정확히 0회**.
     - 세션으로 전송되는 PTY 입력 바이트: **정확히 0 byte** (읽기 전용 상태로 모든 입력 차단).
     - 원래의 9시간 만료 기한 연장: **연장 없음 (최초 단절 시점의 기한 유지)**.
   - 클라이언트는 화면에 "작업 완료 (종료 코드: N)" 및 최종 출력을 표시하며, 사용자가 명시적으로 [새 세션 시작]을 누를 때만 신규 세션을 생성한다.

### 3.4 [B3-E4] 32,400초 수명주기 경계와 만료 단일 판정
1. **타이머 관리 및 만료 처리**:
   - 클라이언트 단절 시 32,400초(9시간) `uv_timer_t` 가동.
   - 실패한 재연결 시도, 복제 충돌 거절 등은 타이머를 리셋하거나 연장하지 않는다.
2. **원자적 경합 해결**:
   - Takeover 요청 처리와 만료 타이머 콜백이 경합할 때, libuv 단일 이벤트 루프 스레드에서 원자적으로 처리한다.
   - 이미 만료 판정되어 `TERMINATING`으로 들어간 세션은 Takeover 요청을 즉시 거절(`expired`)한다.
   - Takeover가 성공하여 새 소유자가 확정되면 즉시 기존 `expiry_timer`를 중단(`uv_timer_stop`)하고 `expiry_timer = NULL` 처리한다.
3. **만료 후 완전 회수 (`PURGED`)**:
   - 만료 도달 시 세션에 귀속된 보존 자료(출력 버퍼, 프로세스, 소켓 메타데이터)를 완전 해제하고 `PURGED` 상태로 확정한다.

### 3.5 [B3-E5] 소유 프로세스 트리 유한 회수와 수명주기 진실성
1. **소유 프로세스 트리 식별**:
   - 세션 루트 PID뿐만 아니라, 세션 PTY master fd에 귀속된 PGID 및 `/proc` 프로세스 트리를 탐색하여 세션 소유 자식/손자 프로세스 목록을 식별한다.
2. **2단계 유한 에스컬레이션 회수 (`SIGHUP` → 대기 → `SIGKILL`)**:
   - 1단계: 세션 트리 전체 프로세스 그룹에 `SIGHUP` 전송.
   - 2단계: 유한 대기 타이머(예: 3초) 가동.
   - 3단계: 타이머 만료 후 `/proc` 스캔으로 잔여 프로세스가 확인되면 즉시 `SIGKILL` 전송.
   - 4단계: `waitpid`를 통해 좀비 회수(reap), PTY master fd 닫기, 타이머 및 버퍼 메모리 해제.
3. **진실한 상태 추적**:
   - 회수가 완전히 끝나 프로세스 및 FD가 소멸한 경우에만 `PURGED`로 전이.
   - 프로세스가 여전히 남아있는 비정상 상태인 경우 `TERMINATING` 상태를 유지하고 실패 진단 로그를 남기며, 거짓 `PURGED` 처리를 금지한다.
   - 관련 없는 타 사용자 프로세스나 시스템 데몬은 일체 영향을 받지 않는다.

### 3.6 [B3-E6] 자원 계상 및 정직한 수용 상한 방어
1. **자원 카운터 통합 관리**:
   - `active_sessions_count`: 현재 웹소켓 연결이 붙어 있는 활성 세션 수.
   - `detached_sessions_count`: 단절 후 9시간 유예 중인 세션 수.
   - `retained_sessions_count`: `EXITED_RETAINED` 상태로 결과를 보존 중인 세션 수.
   - `total_tracked_memory`: 출력 버퍼 누적 메모리 바이트 수.
2. **설정 가능한 수용 상한 (`Admission Limits`)**:
   - 최대 동시 실행 세션 수 (`MAX_ACTIVE_SESSIONS`, 예: 8).
   - 최대 결과 보존 세션 수 (`MAX_RETAINED_SESSIONS`, 예: 16).
   - 최대 출력 메모리 총합 (`MAX_TOTAL_BUFFER_BYTES`, 예: 64 MiB).
3. **정직한 수용 거절**:
   - 상한 도달 시 신규 세션 생성 요청(`intent: create`)은 즉시 HTTP 503 또는 프로토콜 거절 메시지(`state: "rejected_capacity"`)를 반환한다.
   - 새 셸을 무단 스폰하거나 기존 9시간 보호 세션을 침묵 퇴출(Silent Eviction)하지 않는다.
   - 이미 존재하는 세션에 대한 재접속(`intent: resume`) 및 결과 열람은 신규 슬롯을 소비하지 않으므로 정상 허용한다.

### 3.7 [B3-E7, B3-E8] systemd 사용자 서비스 및 logrotate 운영 감독
1. **systemd 사용자 서비스 설계**:
   - 대상 유닛 파일: `/home/user01/.config/systemd/user/webterm.service`
   - 구성 내용:
     - `ExecStart=/home/user01/.local/bin/ttyd -W -i 127.0.0.1 -p 7683 -I /home/user01/.local/share/webterm/index.html /home/user01/.local/share/webterm/session.sh`
     - 환경 변수: `TTYD_RECONNECT_GRACE=32400`
     - 재시작 정책: `Restart=on-failure`, `RestartSec=2s`
     - 재시작 제한: `StartLimitIntervalSec=60s`, `StartLimitBurst=5`
     - 표준 출력/에러: `/home/user01/.local/state/webterm/ttyd.log`
   - WSL 환경 전제: `loginctl enable-linger user01` 확인 (`Linger=yes` 기확인됨).
2. **서비스 수명주기 및 메모리 비보존 한계 고지**:
   - 서비스 정상 중단(`systemctl --user stop webterm.service`) 시 SIGTERM 전송 후 프로세스 트리 회수.
   - 서비스 재기동 시 인메모리 세션이 초기화되므로, 이전 세션 ID 요청에 대해 신규 셸을 열어 속이지 않고 정직하게 `unknown`/`expired`로 응답함을 검증.
3. **logrotate 구성 및 실제 파일 회전 검증**:
   - 대상 설정 파일: `/home/user01/.config/logrotate/webterm.conf`
   - 회전 정책:
     ```text
     /home/user01/.local/state/webterm/ttyd.log {
         size 10M
         rotate 5
         compress
         missingok
         notifempty
         copytruncate
     }
     ```
   - 검증 방법: 단순 dry-run이 아닌 `logrotate -f -s /home/user01/.local/state/webterm/logrotate.status /home/user01/.config/logrotate/webterm.conf`를 실행하여 실제 `.1.gz` 파일 생성, 권한 유지, 데몬의 후속 로그 쓰기 지속성을 실증한다.

### 3.8 [B3-E9] CUSTOMIZATION.md 최신화
- 설치, 기동/중단, 업데이트, 롤백 절차를 실측 경로와 1:1 일치하도록 갱신한다.
- 8 MiB 순환 tail 및 절사 고지, `EXITED_RETAINED` 결과 보존(1시간 재열람), 워커 회수 에스컬레이션, 수용 상한 거절 동작을 명시한다.
- `systemd` 사용자 서비스 unit 경로, 관리 명령, `logrotate` 대상 경로 및 WSL2 lingering 전제를 기술한다.
- 데몬 재시작 시 인메모리 세션 비보존 한계와 안전 회수 절차를 명문화한다.

### 3.9 [B3-E10] 14대 반례 차단 및 SC-1..SC-8 전구간 회귀 검증
동일한 최종 바이너리 및 인라인 번들에서 Thesis §6의 14대 거짓 성공 반례를 체계적으로 차단하고 SC-1~SC-8 성공 기준을 독립 검증한다.

---

## 4. 변경 구조 및 구체적 소스 영향 경로

### 4.1 소스 파일별 변경 책임

| 소스 파일 | 주요 변경 내용 |
|---|---|
| `src/server.h` | 세션 상태 열거형(`SESSION_ACTIVE`, `SESSION_EXITED_RETAINED` 등), 수용 상한 설정 변수, 프로세스 트리 회수 함수 시그니처 추가 |
| `src/protocol.c` | 1. `session_output_append()`: 8 MiB 링버퍼 오버플로 시 헤드 전진 및 `truncated` 플래그 설정.<br>2. `process_exit_cb()`: 단절 세션에 대해 `EXITED_RETAINED` 전이 및 결과/exit_code 보존.<br>3. `session_reap_tree()`: 하위 프로세스 그룹 SIGHUP → SIGKILL 유한 회수.<br>4. `session_check_admission()`: 동시 세션/메모리 상한 검사 및 거절 응답 생성.<br>5. 만료/Takeover 원자 경합 해결. |
| `src/pty.c` | 1. `pty_kill_tree()`: PTY 마스터에 연결된 모든 포그라운드/백그라운드 자식 프로세스 트리에 대한 단계적 에스컬레이션 구현.<br>2. `pty_signal_foreground()` 유지 및 보강. |
| `html/src/components/terminal/xterm/index.ts` | 1. `SET_SESSION_STATE`: `truncated` 안내 렌더링, `exited_retained` 상태 처리 및 읽기 전용 뷰 렌더링.<br>2. 결과 재열람 모드에서 PTY write 차단(0 byte) 및 셸 스폰 방지. |
| `staging/check_*.py` | BLOCK-003 전용 테스트 하네스 보강: 10 MiB 대량 출력 링버퍼 검증, `EXITED_RETAINED` 결과 열람 검증, 프로세스 트리 회수 검증, 수용 거절 검증. |
| `CUSTOMIZATION.md` | BLOCK-003 백엔드 거버넌스, systemd/logrotate, 1h/9h 보존 수명주기 반영. |

---

## 5. 14대 반례 차단 매핑 및 권위 있는 판독처

| 번호 | 거짓 성공 (Plausible False Success) | 은폐된 결손 (Hidden Failure) | PLAN-001 차단 방법 및 권위 있는 판독처 (Authoritative Readback) |
|---|---|---|---|
| 1 | 새로고침 후 터미널이 깨끗하게 떴다 | 이전 세션이 아닌 새 셸이 열려 이전 작업이 고아로 방치됨 | 동일 세션 ID 유지, `sessionStorage` 확인, 백엔드 `attached to existing process` 로그, 이전 작업 텍스트 일치 확인 |
| 2 | 동일한 PID가 유지되고 있다 | PID만 살아있고 클라이언트 화면 버퍼가 깨지거나 비어있음 | PID 생존 확인과 함께 xterm 화면 버퍼 내 실제 TUI 레이아웃 및 프롬프트 텍스트 복원 검증 |
| 3 | 8 MiB 초과 출력을 뿜고 프로세스가 끝났다 | 버퍼 초과로 전체가 날아가 최종 결과 확인 불가 | 최신 8,388,608 bytes tail 보존 검증, 화면에 "이전 출력이 절사됨" Truncation 고지 렌더링 확인 |
| 4 | WebSocket OPEN 상태가 되었다 | 소켓만 열리고 세션 핸드셰이크가 안 끝나 입력 불가 | 소켓 OPEN과 별개로 `SET_SESSION_STATE` 수신 및 `Input Ready` 표기/입력 가능 상태 확인 |
| 5 | 화면을 켰을 때 visibility 리스너가 돌았다 | 네트워크 반단절(Half-open)로 실제 송수신 불가 | 핑/퐁 Liveness 검증 완료 및 실제 양방향 데이터 패킷 송수신 재개 확인 |
| 6 | 재연결 탭 한 번으로 연결이 복구되었다 | 재연결 터치가 PTY로 흘러들어가 원치 않는 Enter 제출 | 재연결 수행 시 PTY 수신 바이트가 정확히 **0 byte**임을 PTY 스니퍼로 검증 |
| 7 | 동일 세션에 두 번째 탭이 바로 붙었다 | 탭 간 무한 핑퐁 탈취전 발생 | 기존 탭 보호, 복제 탭에 Takeover 모달 노출, 사용자 명시적 승인 전까지 탈취 차단 확인 |
| 8 | 재연결 시 resize 시스템 콜이 성공했다 | 동일 크기 재연결이라 TUI가 화면을 다시 그리지 않아 깨짐 | `TIOCGPGRP` 기반 포그라운드 PGID SIGWINCH 수신 및 TUI 애플리케이션의 실제 재렌더링 화면 판독 |
| 9 | 가상 키보드가 정상적으로 닫혔다 | 키보드가 닫히면서 작성 중이던 한글 조합 텍스트 유실/중복 | 한글 완성 텍스트가 정확히 1회 PTY로 커밋되었음을 바이트 로그로 확인 |
| 10 | CTRL 버튼이 영문 글자와 잘 동작했다 | 붙여넣기/취소 후 CTRL armed가 남아 다음 글자에서 SIGINT 발생 | 붙여넣기 및 ESC 취소 후 일반 영문 입력 시 잔여 모디파이어에 의한 SIGINT 미발생 입증 |
| 11 | 9시간 만료 후 로그에 kill이 찍혔다 | 서브프로세스나 워커들이 수거되지 않고 백그라운드에 남음 | `/proc` 프로세스 테이블 감사를 통해 세션 하위 워커 프로세스 트리의 완전 소멸(`PURGED`) 입증 |
| 12 | 단일 행 툴바가 390px 화면에 딱 맞게 들어갔다 | 360px 또는 노치 Safe Area 환경에서 버튼이 잘려 누를 수 없음 | 360px 뷰포트 및 Safe Area 환경에서 12개 버튼의 온전한 터치 타깃(34~36px) 접근성 입증 |
| 13 | Tailscale HTTPS로 페이지가 잘 열린다 | 정적 페이지만 로드되고 `/terminal/ws` 프록시가 깨져있음 | 정적 페이지 로드와 별개로 `/terminal/token` 발급 및 `/terminal/ws`의 정상 양방향 통신 검증 |
| 14 | 단절 중 에이전트 프로세스가 살아있다 | 에이전트가 작업 중인 것이 아니라 사용자 입력을 기다리며 멈춤 | 프로세스 생존 여부와 에이전트의 실제 작업 진행/대기 상태를 분리 인지 |

---

## 6. 전구간 성공 기준(SC-1..SC-8) 및 Acceptance 검증 매트릭스

| 성공 기준 | 대상 시나리오 및 입력 | 기대되는 관찰 가능한 결과 | 권위 있는 판독처 |
|---|---|---|---|
| **SC-1** (B3-E10) | 작업 중 탭 새로고침 실행 | 신규 셸이 아닌 동일 세션 ID로 100% 복귀, 이전 화면 버퍼 복원 | `sessionStorage`, 서버 진단 로그, 화면 텍스트 일치 |
| **SC-2** (B3-E10) | 수동 재연결 오버레이에서 ↵ 터치 | 셸/에이전트에 Enter 입력 없이 즉시 소켓 재연결 및 Input Ready | PTY 수신 바이트 = 0 byte, 웹소켓 `ACTIVE` |
| **SC-3** (B3-E10) | 툴바 CTRL 터치 후 ESC 취소, 'c' 입력 | SIGINT 없이 일반 문자 'c' 타이핑 | PTY 수신 바이트 `0x63`, 프로세스 계속 실행 |
| **SC-4** (B3-E10) | 화면 끄고 2분 대기 후 켜기 | 수동 조작 없이 포그라운드 복귀 감지만으로 웹소켓 정상 통신 재개 | `visibilitychange`, 핑/퐁 하트비트 수신 로그 |
| **SC-5** (B3-E10) | 가상 키보드 호출 | 뷰포트가 실제 축소되어 프롬프트와 툴바가 키보드 상단에 안착 | `resizes-content` 레이아웃 높이 축소, xterm rows/cols 일치 |
| **SC-6** (B3-E1) | 모바일 단절 중 10 MiB 대량 출력 | 파이프 블로킹 없이 프로세스 완주(`exit 0`), 최신 8 MiB tail 보존, 재접속 시 절사 안내 | 프로세스 exit code 0, 서버 링버퍼 8 MiB 보존, 화면 Truncation 플래그 |
| **SC-7** (B3-E3) | 단절 중 1분 만에 프로세스 완료, 1시간 뒤 재접속 | 세션 유지(`EXITED_RETAINED`), 최종 exit code 및 결과 출력 열람, 추가 셸 스폰 0회, PTY write 0 byte | 세션 상태 `EXITED_RETAINED`, 1시간 후 화면 결과 일치, spawn=0, write=0 |
| **SC-8** (B3-E10) | 동일 세션 ID를 가진 탭 복제 | 기존 탭 유지, 복제 탭에 Takeover 확인 모달 노출 | 복제 탭 Takeover UI, 기존 탭 displaced 상태 전이 |
| **B3-E4** | 32,400초(9시간) 수명주기 경계 | 단절 시점부터 32,400초 카운트다운, 만료 시 `PURGED` 전환, Takeover 경합 시 원자 판정 | 타이머 이벤트 로그, `/proc` 및 메모리 버퍼 해제 |
| **B3-E5** | 명시적 세션 종료 또는 만료 | 세션 워커 트리 전체에 `SIGHUP` → 대기 → `SIGKILL` 적용, 고아 프로세스 소멸 후 `PURGED` | `/proc` 트리 스캔 결과 0, 열린 FD 0, 서버 `PURGED` 로그 |
| **B3-E6** | 수용 상한 도달 시 신규 세션 요청 | 신규 요청 즉시 명시적 거절(503/거절 응답), 기존 9시간 세션 침묵 퇴출 없음, 재접속은 정상 허용 | HTTP/WS 거절 상태 코드, 세션 테이블 카운터 유지 |
| **B3-E7** | systemd 사용자 서비스 기반 리스너 | `webterm.service` unit이 후보 바이너리/번들/런처로 단일 7683 리스너 감독, Android 실기기 통신 | `systemctl --user status`, `/terminal/ws` 통신 확인 |
| **B3-E8** | 서비스 수명주기 및 logrotate | 정상 중단/재기동 시 세션 만료 정직 고지, `logrotate -f` 실제 로그 파일 회전 및 지속 쓰기 | `systemctl --user` 이벤트 로그, `logrotate` 결과 파일 확인 |
| **B3-E9** | CUSTOMIZATION.md 최신화 | 모든 경로, 플래그, 수명주기 의미, 운영 절차가 실제 구현과 1:1 일치 | `CUSTOMIZATION.md` diff 대조 |

---

## 7. UNRESOLVED — 시간 검증 및 실기기 조건부 첫 작업 번들

### 7.1 장시간(1h 및 9h) 관찰과 제어 시험의 분리
- **장기 관찰 요건**: SC-7의 "1시간 뒤 재접속 열람" 및 B3-E4의 "32,400초(9시간) 만료"는 가상 시간(mock timer)만으로 대체할 수 없는 실전 검증 항목이다.
- **분리 원칙**:
  1. 구현자 self-check 및 단위 회귀: `TTYD_RECONNECT_GRACE=10` 등 단축 환경변수를 사용하여 상태 전이 로직의 결함을 1차 배제한다.
  2. 실제 시간 검증: 격리된 후보 실행물(포트 7695 등)에서 실제 1시간 타이머를 가동하고 단절 후 1시간 뒤 재접속하여 결과를 열람하는 실측 시험을 수행하며, 9시간 만료 역시 실측 관찰 로그를 획득한다. 가상 시간 시험 결과를 실제 1시간/9시간 운영 통과로 표기하지 않는다.

### 7.2 조건부 첫 작업 번들 (Conditional First Work)

#### 번들 1: 8 MiB 링버퍼 비차단 완주 관찰
- `plan_anchor`: §3.1 (B3-E1, SC-6).
- `permitted_initial_work`: 10 MiB 대량 출력을 생성하는 격리 fixture 스크립트 작성 및 포트 7695 후보 서버 대상 단절 실행.
- `discriminating_observation`: PTY 총 방출량 > 10 MiB, 자식 프로세스 exit 0 완주, 서버 버퍼 보존량 == 8,388,608 bytes, 재접속 시 `truncated: true` 수신.
- `dependent_work_not_yet_permitted`: `EXITED_RETAINED` 결과 보존 및 수용 상한 구현.
- `response_if_refuted`: 프로세스가 I/O 블록으로 멈추거나 버퍼 크기가 8 MiB를 초과하면 링버퍼 메모리 이동/드레인 로직을 전면 재검토하고 Planner로 반환.

#### 번들 2: 단절 중 종료 및 EXITED_RETAINED 결과 보존 관찰
- `plan_anchor`: §3.3 (B3-E3, SC-7).
- `permitted_initial_work`: 백그라운드 단절 상태에서 1분 내 완료되는 작업 실행 및 `process_exit_cb` 전이 판독.
- `discriminating_observation`: 프로세스 종료 후 세션 테이블에 `EXITED_RETAINED` 유지, exit code 저장 확인, 재접속 시 결과 출력 정상 수신.
- `dependent_work_not_yet_permitted`: 1시간 장기 대기 및 서비스 감독 통합.
- `response_if_refuted`: 세션이 즉시 해제되거나 버퍼가 유실되면 `process_exit_cb` 내 상태 보존 로직을 수정.

#### 번들 3: 워커 프로세스 트리 유한 회수 관찰
- `plan_anchor`: §3.5 (B3-E5).
- `permitted_initial_work`: OMP 하위 작업처럼 별도 PGID를 생성하는 자식 워커 fixture 실행 후 세션 종료 요청.
- `discriminating_observation`: `SIGHUP` 전송 후 3초 뒤 `/proc` 스캔에서 잔여 시 `SIGKILL` 전송 확인, 최종 프로세스 트리 전원 소멸 및 `PURGED` 전이.
- `dependent_work_not_yet_permitted`: systemd 유닛 연동.
- `response_if_refuted`: 고아 프로세스가 잔존하면 프로세스 트리 추적 알고리즘(`/proc` 순회)을 보강.

---

## 8. 구현 순서 및 통합 컷오버 경계

### 8.1 구현자 단계별 실행 순서
1. **1단계: C 백엔드 링버퍼 및 결과 보존 구현 (`src/protocol.c`, `src/pty.c`, `src/server.h`)**
   - 8 MiB 링버퍼 오버플로 전진 및 절사 플래그 구현.
   - `EXITED_RETAINED` 상태 머신 및 종료 코드/신호 보존 구현.
   - 워커 프로세스 트리 SIGHUP → SIGKILL 유한 회수 구현.
   - 수용 상한 카운터 및 503 거절 로직 구현.
2. **2단계: 프론트엔드 결과 재열람 뷰 및 절사 고지 구현 (`html/src/components/terminal/xterm/index.ts`)**
   - `SET_SESSION_STATE`에서 `truncated` 고지 오버레이 및 문구 반영.
   - `exited_retained` 상태에서 결과 표시 및 PTY write 차단(0 byte).
3. **3단계: 테스트 하네스 갱신 및 Scoped Self-Check (`staging/check_*.py`)**
   - 격리 포트(7684, 7695 등)에서 B3-E1~B3-E6에 대한 자동화 회귀 검증 실행.
4. **4단계: systemd 사용자 서비스 및 logrotate 설정 파일 작성**
   - `~/.config/systemd/user/webterm.service` 및 `~/.config/logrotate/webterm.conf` 생성.
   - 격리된 테스트 포트 또는 환경에서 logrotate 실제 회전 검증.
5. **5단계: 운영 문서 최신화 (`CUSTOMIZATION.md`)**
   - 구현된 모든 수치, 경로, 거버넌스 규칙, systemd/logrotate 지침을 실측값과 동기화.
6. **6단계: 통합 빌드 및 검증 인계**
   - `build/ttyd` 및 `html/dist/inline.html`을 최종 빌드하고 해시를 기록.

### 8.2 Safe Abort 및 롤백 경계
- **트리거**: 10 MiB 대량 출력 시 프로세스 데드락 발생, 단절 중 종료 결과 유실, 워커 프로세스 누출, 메모리 상한 초과, 기존 세션 침묵 퇴출 발생 시 즉시 구현 작업을 중단한다.
- **안전 격리**: 모든 작업은 격리 포트(7695 등)에서 수행되며, 운영 포트 7683의 live daemon에는 일체 손을 대지 않는다. 결함 발생 시 후보 프로세스만 안전하게 회수하고 소스 변경을 재검토한다.
- **운영 컷오버 분리**: 포트 7683 데몬 교체 및 crontab 이관은 본 Plan에 따른 독립 검증 및 Coverage가 모두 완료된 후, 별도의 유지보수 승인을 받아 Main이 수행한다.

---

## 9. 산출물 요약 및 인계 지표

- **Plan 경로**: `/home/user01/project/webterm/ttyd-1.7.7/docs/planning/work/output-governance-result-retention-supervision/plans/PLAN-001.md`
- **적용 Scope**: `docs/planning/work/output-governance-result-retention-supervision/SCOPE.md` (ready, unchanged)
- **리뷰 산출물 위치 (고정)**: `/home/user01/tmp/iis-plan-reviews/webterm-block003-plan-review.json`
- **구현 담당 액터**: Gemini 서브에이전트 (사용자 지시: Opus 대신 Gemini 사용)
- **종료 조건 확인**: Scope 상태 `ready` 보존, 프로덕션 포트 7683 보존, 소스코드 변형 없음, Plan 문서 완성.
