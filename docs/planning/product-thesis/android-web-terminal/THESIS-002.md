# THESIS-002: 단절과 경합에도 작업·출력·입력 의도를 보존하는 안드로이드 웹 터미널

- **Status**: CALIBRATED
- **Date**: 2026-09-18
- **Author**: IIS Astra High Agent
- **Target Path**: `docs/planning/product-thesis/android-web-terminal/THESIS-002.md`
- **Baseline Target**: `webterm / ttyd-1.7.7`
- **Branch**: `custom/android-mobile-toolbar`
- **Commit**: `9246173` (`9246173177686762bcf7c2f6a4e6b864185fc38c`)
- **Snapshot Commit**: `e2cd5a1314215ad40cf8f5bb4aead00bdaf8fb4f` (`snapshot/ttyd`)
- **Previous Thesis**: [THESIS-001.md](THESIS-001.md), 불변 보존
- **Previous Thesis SHA-256**: `81003a0783df4f7876ad603aafd47c1b96ba768cec03237ed72e543ce9eb642a`

`CALIBRATED`는 아래 제품 의미와 반례에 대한 정책을 확정했다는 뜻이다. v4 구현, 버그 수정, 실제 Android 검증 또는 운영 배포가 완료되었다는 뜻이 아니다. 본 문서는 기존 모바일 가치 전체를 계승하면서 복구의 성공 의미, 소유권, 출력 손실, 종료 결과와 회수 경계를 개정한다. 기존 Scope의 원본 바인딩이나 과거 검증 결과를 자동으로 교체하지 않는다.

## 근거와 개정 이유

이번 정의의 중심 질문은 **“소켓을 다시 여는 것뿐 아니라, 같은 작업을 올바른 소유자에게 돌려주고 실제 적용된 출력 뒤에서만 입력을 재개하며, 복구가 불가능한 부분은 정직하게 알릴 수 있는가?”**이다.

근거는 `/tmp/oracle-findings-and-investigation.md`의 1차 조사와 그 안에 수록된 **오라클 브라우저 1번 슬롯(GPT-5.6 Sol Pro) 검토 전문**, THESIS-001, 그리고 아래 로컬 소스의 읽기 전용 확인이다. 브리핑 SHA-256은 `d09035efe52fe103720832295e1ae5065096e953748c7e33029e8106540d68bd`이다. 브리핑은 임시 경로이므로 장기 보존이 보장되지 않는다. 스냅샷은 [해당 커밋](https://github.com/lleullus/testbyrepo/commit/e2cd5a1314215ad40cf8f5bb4aead00bdaf8fb4f)으로 식별한다.

오라클의 근거 수준은 정적 코드 추적과 기존 스테이징 테스트 검토이며, 실제 Android 패킷 캡처나 프로세스 discard 실험이 아니다. 이 문서를 작성하면서도 런타임 실험을 수행하지 않았다. 따라서 아래 결함 경로는 소스 관찰과 그로부터 도출한 실패 조건이며, 모든 사용자 환경에서 측정된 발생률·지연 수치로 일반화하지 않는다.

| 근거 구분 | 확인된 경로와 필요한 보정 | 제품 의미 반영 |
| --- | --- | --- |
| **A: Owner Check** | `src/protocol.c:972–990`에서 Ping 미전송 2초 만료를 `error`로 분류한다. Ping이 전송되면 10초 Pong 대기를 거치며 전송 준비 지연을 합치면 약 12초가 될 수 있다. 모든 half-closed 연결이 2초 오류를 일으키는 것은 아니다. native Pong은 JS/xterm의 준비 상태 증명이 아니다. | NB6, NB12, NB13: 연속성 자격에 따른 즉시 인계, 애플리케이션 lease, 명시적 경합 결과 |
| **B: rAF·복구 예산** | `xterm/index.ts:1149–1158, 1506–1626, 1804–1846`의 rAF await는 콜백이 오지 않으면 deadline 검사도 재개되지 않는다. 60초 wall-clock 예산과 기존 `connectPromise`가 복귀·수동 복구를 가로막는다. | NB5, NB6, NB14: paint와 프로토콜 분리, fallback geometry, 취소·선점 |
| **C: 준비 응답 누락** | `protocol.c:1363–1380`의 잘못된 `SESSION_READY`는 silent break다. visible에서는 30초 attempt timeout이 작동할 수 있으므로 모든 경우 영구 대기라고 표현하지 않는다. frozen에서는 그 타이머도 멈출 수 있다. | NB15: REPLAY_APPLIED/READY_ACK와 명시적 NACK, 서버 ready deadline |
| **D: 복구 식별 소실** | `app.tsx:16–47`은 endpoint별 `sessionStorage`에 ID만 저장하고, create 승인 전부터 이를 기록한다. discard가 반드시 storage 소실을 뜻하지는 않는다. 실제 키는 `webterm.session.v1:${endpoint}`이며 초안의 키 이름은 구현과 다르다. | NB1, NB17: 승인된 binding과 임시 create의 구분, 소실 고지, 장래 discovery 경계 |
| **E: TUI 정합성** | `protocol.c:868–882`는 attach마다 resize와 foreground SIGWINCH를 요청한다. 이것이 화면·모드 복원을 증명하지 않는다. `prepare_session_response()`의 누적 `replay_lost`는 현재 구간 손실과 과거 손실을 섞는다. 새 세션 전환은 실제 emulator reset 없이 진행된다. | NB3, NB9, NB16: 연속 재개·새 세션·gap을 분리 |
| **P0-1: exited_retained 고착** | `xterm/index.ts:1838–1842, 1924–1979`는 종료 플래그를 설정한 뒤 retained replay 시 attempt를 settle하지 않고, created/attached에서도 플래그를 해제하지 않는다. `requestRecovery()`는 pending promise가 있으면 새 세션 요청을 무시한다. | NB5, NB9, NB11: 읽기 전용 완료와 새 세션의 완전한 상태 분리 |
| **P0-2: 8 MiB cursor 추월** | `protocol.c:132–135, 1257–1273`에서 `send_position < output_start`를 “출력 없음”으로 취급한다. replay는 도달 불가능한 REPLAY_END를 만들고, READY 후 PAUSE/RESUME도 영구 출력 정지로 이어질 수 있다. `159–170`은 실제 ring이 아니라 대규모 memmove다. | NB2, NB16: 명시적 gap, rebase, 실제 순환/청크 버퍼 |
| **P0-3: reaper 수명 위반** | `protocol.c:311–370`은 embedded timer의 `uv_close()` 직후 parent를 free하고 close callback에서 interior pointer를 free한다. `waitpid(-1)`은 `pty.c:833–859`의 root waiter와 경쟁하며, 실패한 wait 결과의 `stat` 해석 및 뒤늦은 exit callback의 session UAF 가능성이 있다. | NB18: 단일 reap 권한, 비동기 참조 수명, 회수 진실성 |
| **P0-4: retained pruning** | `protocol.c:637–695`는 전환된 현재 세션을 센 후 `retained >= max_retained`로 제거한다. 상한 1이면 현재 callback의 세션을 바로 free하고 계속 참조할 수 있으며 연결된 viewer도 제외하지 않는다. | NB11, NB18, NB19: 정확한 상한과 보호 중인 결과·참조 보존 |
| **P1: 전송·자원·종료 경계** | `protocol.c:1077–1091, 1271–1272`는 write 실패에도 cursor를 전진시킨다. `1129–1136`은 HELLO 전 client 수로 연결을 차단한다. `1288–1308`은 fragmented message 누적 크기를 제한하지 않는다. `433–446`은 expiry timer start 결과를 확인하지 않는다. PTY EOF와 root exit 처리는 별개다. | NB15–NB19: 전송 진실성, 복구 수용 경로, 유한 입력 버퍼, 만료·종료의 명시적 실패 |

P0 번호는 브리핑의 **“누락된 중대 실패 경로” 절의 네 결함 번호**를 따른다. 뒤의 “적용 우선순위” 목록은 다른 순서로 재번호화되어 있으므로 동일 식별자로 혼용하지 않는다. 이하 의무는 오라클 권고를 이번 위임 범위에서 채택한 제품 결정이다. 오라클이 직접 사용자 승인을 부여했거나 현재 코드에 이미 구현되어 있다는 뜻이 아니다.

## 1. Product Promise (제품 약속)

### 1.1 구체적 결손

사용자는 Android 브라우저에서 원격 Linux 개발 셸과 OMP를 운영한다. 화면 잠금, 앱 전환, Wi-Fi/LTE 변경은 정상 사용의 일부인데, 기존 복구 경로는 이때 다음과 같이 작업을 이용할 수 없게 만든다.

- FIN/RST가 도달하지 않은 **half-closed/half-open 연결**을 기존 소유자로 보아, 2초 뒤 false protocol error로 자동 복구를 멈추거나 약 10–12초의 Owner Check 대기를 요구한다. 세 번째 시도도 generic error가 될 수 있다.
- 백그라운드에서 중단되는 **requestAnimationFrame(rAF)**을 geometry와 replay 완료의 필수 조건으로 삼아, 소켓을 열기 전 또는 출력 수신 후에 멈춘다. 대기 중인 Promise가 사용자의 Reconnect까지 막는다.
- **최신 8 MiB 보존 창이 송신 cursor를 추월**하면 이미 사라진 바이트를 기다리거나 이후 출력까지 영원히 전송하지 않는다. 버퍼가 있어도 사용자가 결과를 읽을 수 없는 상태다.
- **exited_retained 결과를 본 뒤 새 세션을 시작해도** 이전 종료 상태가 남아 새 셸의 준비 응답과 입력이 차단된다.
- **reaper·pruning의 UAF, 잘못된 free, reap 경쟁**은 개별 탭 복구를 넘어 서버와 다른 세션의 존속을 위협한다.
- 승인되지 않은 create ID 저장, 복구 권한 소실, 새 셸과 이전 xterm 상태 혼합은 “연결됨” 화면을 보여도 사용자가 요청한 작업을 복원하지 못한다.

이와 함께 THESIS-001의 결손, 즉 가상 키보드 가림·자동 팝업, 모바일 특수 키 부재, IME 중복 입력, 재연결 터치의 Enter 누설, 단절 중 PTY 출력 블로킹과 고아 프로세스 누적을 계속 해결해야 한다.

### 1.2 Durable Utility (불변의 가치)

> **호스트와 터미널 서비스가 계속 가동되고 승인된 세션의 복구 자격이 남아 있는 동안, Android 사용자는 화면 잠금과 통신 전환 뒤에도 9시간 유예 안에서 같은 원격 작업으로 돌아온다. 서버는 연결·렌더링 속도와 무관하게 출력을 배출하고 최신 8 MiB를 보존한다. 유효한 연속성 자격으로는 이전 죽은 소켓의 응답을 기다리지 않고 인계하며, 실제 적용된 출력과 서버의 준비 확인 뒤에만 입력을 연다. 잃은 출력·권한·종료 결과를 숨기거나 새 셸로 대체하지 않는다. 사용자는 키보드 가림 없는 단일 행 툴바와 한 번의 명시적 복구 동작으로 작업을 계속한다.**

- **작업 보존**: 브라우저의 수면이나 느린 viewer가 PTY drain을 멈추게 하지 않는다. 입력을 기다리는 프로그램까지 자동으로 완료시킨다는 약속은 아니다.
- **정직한 연속성**: 동일한 작업, 출력 범위, 소유권 epoch, 종료 상태를 구분한다. 과거 escape sequence가 유실된 TUI의 완전 복원을 가장하지 않는다.
- **복구 가능성**: 사용자의 복구 의도가 오래된 attempt·timer·paint 대기보다 우선한다. 단, 다른 정상 소유자의 권한을 몰래 빼앗는 권한은 아니다.
- **모바일 완결성**: 자동 키보드 팝업 없이 프롬프트와 툴바가 보이고, 특수 키·한글 조합·붙여넣기가 의도대로 한 번만 전달된다.
- **안전한 종료 결과**: 루트 종료를 새 입력 가능 상태로 위장하지 않으며, 유예 안에 최종 결과를 읽을 수 있고 실제 자원 회수로 수명주기를 끝낸다.

## 2. Core Completion Loop (v4 핵심 인과 루프)

### 2.1 단계와 성공 경계

```text
접속 / visible 복귀 / 명시적 복구
  → 이전 attempt 선점·fence, 승인된 binding 선택, 유효 geometry 또는 fallback 확보
  → HELLO(version=4, resumeId, intent, clientInstanceId,
          connectSequence, successorToken, replayPosition, columns, rows)
  → 권한·lease 판정: 즉시 successor 인계 / CONFLICT / 명시적 실패
  → SESSION_ACCEPTED(session identity, leaseEpoch, replay 범위, 새 연속성 자격)
  → OUTPUT(start, end, bytes) 연속 적용
       ├─ gap → REPLAY_GAP / SYNC_REQUIRED(BUFFER_OVERRUN)
       │         → 손실 고지·명시적 rebase → 새 replay barrier
       └─ REPLAY_END(target)
  → xterm parser write callback으로 해당 barrier 적용 완료 확인
  → REPLAY_APPLIED(session, epoch, target)
  → READY_ACK → 현재 소유자만 입력 가능
  → 단절 / 화면 잠금: 서버 drain·최신 8 MiB 보존·유예 유지
  → 복귀: 같은 루프 / 종료 결과 읽기 / 명시적 새 세션 / 만료·회수
```

1. **진입과 식별**: endpoint별 승인된 세션 binding을 읽는다. 신규 생성과 resume 의도를 분리하고, 복구 자격이 없으면 이를 숨기지 않는다. geometry 때문에 HELLO가 paint를 기다리지는 않는다.
2. **소유권 인계**: 서버는 유효한 일회성 Successor Token과 증가한 connectSequence를 같은 논리적 클라이언트의 연속성으로 검증한다. 새 leaseEpoch를 확정하고 이전 연결을 먼저 fence한다. 이것이 기존 소켓에 대한 Owner Check 추가 왕복이 없는 **0 RTT 인계**다. TCP/TLS/WebSocket 연결, 인증, HELLO 응답, replay의 실제 네트워크 지연까지 0이라는 뜻은 아니다.
3. **출력 복원**: SESSION_ACCEPTED는 입력 준비가 아니다. 클라이언트는 epoch와 byte range가 맞는 OUTPUT만 적용하고, 중복은 재적용하지 않으며, gap은 숨기지 않는다. 서버는 실제 전송 가능한 구간에 대해서만 REPLAY_END를 보낸다.
4. **Replay Barrier**: paint 대신 parser 완료로 적용 위치를 확정한다. REPLAY_APPLIED의 대상·epoch·position을 서버가 확인하고 READY_ACK를 반환한 뒤 입력을 연다. 렌더링과 실제 TUI 판독 가능성은 별도 성공 조건이다.
5. **상호작용**: 현재 입력 가능한 세션에만 의도한 키를 전송한다. 복구 제스처, IME 조합, UI 설정은 PTY 명령과 섞이지 않는다.
6. **단절과 복귀**: 서버는 bounded buffer에 계속 drain한다. 복귀·online·수동 재시도는 해당 논리 세션을 재개하며, 과거 attempt가 최신 연결을 덮거나 닫지 못한다.
7. **결과와 종료**: EXITED_RETAINED는 읽기 전용 replay 완료로 정착한다. 사용자가 Start New Session을 선택하면 이전 복구를 취소하고 새 세션을 별도 emulator 상태에서 시작한다. 만료·명시적 종료는 실제 프로세스 및 참조 회수로 끝난다.

### 2.2 v4 계약의 필수 의미

요청된 v4, Successor Token, Lease Epoch, parser barrier와 buffer overrun 처리의 의미는 본 Thesis의 필수 수단이다. opcode 배치, 직렬화 형식, 자료구조 구현, timer 수치·조율은 Plan의 책임이다.

- HELLO는 `version: 4`, `resumeId`, `intent`, `clientInstanceId`, `connectSequence`, resume 시 `successorToken`, `replayPosition`, `columns`, `rows`를 구분한다. create에는 기존 token이 없으며 create 승인이 binding의 출발점이다.
- 서버는 `leaseEpoch`, `ownerClientInstanceId`, `successorTokenHash`, `ownerPhase = ATTACHING | REPLAYING | READY`, `lastApplicationHeartbeat`, `lastProgressAt`에 대응하는 권위 상태를 유지한다.
- 모든 입력 권한, replay barrier, takeover와 지연 응답은 대상 세션 및 leaseEpoch에 귀속된다. 이전 epoch의 INPUT·RESIZE·ACK·heartbeat가 새 소유자를 조작하지 못한다.
- 오류는 원인·재시도 가능 여부를 구분한다. position 문제는 `POSITION_MISMATCH` 또는 `SYNC_REQUIRED`, cursor 추월은 `BUFFER_OVERRUN`을 포함한 명시적 GAP, 경합은 `CONFLICT`, 뒤처진 시도는 `SUPERSEDED`/`STALE`, 일시적인 경합 처리 포화는 `OWNER_CHECK_BUSY`와 `retryable: true`, `retryAfterMs`로 표현한다. 정상 복구 상황을 generic protocol error로 끝내지 않는다.
- v3와 v4를 묵시적으로 섞지 않는다. 호환되지 않는 클라이언트·서버 조합은 명시적 version mismatch이며, 새 셸 생성이나 성공 UI로 대체하지 않는다.

## 3. Necessary Behaviors (필수 동작)

### NB1. 승인된 세션 binding과 복구 의도 보존

THESIS-001의 탭 단위 연속성을 계승하되, `resumeId`만으로 동일 클라이언트라고 판단하지 않는다. endpoint, 서버가 승인한 세션, 논리 클라이언트, 연속성 자격의 결합을 보존한다. create 응답 전 ID는 **pending creation**이지 복구 가능한 세션이 아니다. 응답 소실이나 재시도로 같은 생성 의도가 중복 PTY를 만들지 않아야 한다. 거절된 create의 로컬 기록을 다음 reload에서 승인된 resume으로 오인하지 않는다.

storage 접근 거부·소실 시 복구 보장 저하를 알린다. unknown/expired/exited에 침묵하는 자동 create를 하지 않는다. 같은 browsing context의 reload/restore에서 복구 자격과 필요한 terminal 상태가 보존된 경우 같은 세션으로 돌아간다. 자격이 남아 있어도 emulator 상태가 없는 재로드는 NB9의 재구성 한계를 따른다.

### NB2. 최신 8 MiB 비차단 보존과 overrun 처리

세션당 출력 보존 payload의 상한은 **8 MiB = 8,388,608 bytes**다. detached뿐 아니라 slow/paused/hidden viewer가 붙은 동안에도 PTY drain을 지속한다. 오래된 출력은 버리고 최신 출력을 유지한다. 이 한도는 세션 객체·WS 버퍼 등 전체 프로세스 메모리가 정확히 8 MiB라는 뜻이 아니며, 별도 전송·메타데이터 메모리도 유한해야 한다.

sliding memmove로 새 출력마다 거의 8 MiB를 복사하는 구조를 없애고 실제 circular buffer 또는 bounded chunk deque를 사용한다. reader가 보는 bytes를 덮어쓴 후 정상 출력으로 보내지 않는다. 청크 참조 보존을 택해도 무제한 pinning으로 보존 상한을 우회하거나 생산자를 막지 않고, 한계에서는 명시적 gap으로 전환한다.

`send_position < output_start`는 **데이터가 없다는 뜻이 아니라 필요한 데이터가 사라졌다는 뜻**이다. replay와 READY 이후 live stream 모두 NB16의 gap/rebase를 실행한다. 최신 출력 생성이 계속되더라도 cursor가 영구 정지하지 않으며, 소비 속도가 계속 부족하면 반복 손실을 정직하게 표시한다.

### NB3. 실제 geometry와 foreground TUI 동기화

visible에서 가능한 유효 geometry를 계산하고, hidden에서는 마지막 유효 geometry, 없으면 **80×24 Fallback Geometry**로 연결을 진행한다. visible 복귀·ResizeObserver 후 실제 크기를 `RESIZE_TERMINAL`로 보정한다. 현재 소유권 확인 전의 stale resize가 새 소유자의 크기를 덮지 않는다.

Linux에서 `TIOCGPGRP` 기반 foreground process group에 SIGWINCH를 전달하는 의미를 유지하며, 동일 크기 재접속에서도 redraw 요청 경로가 있어야 한다. 요청·시그널 성공은 실제 redraw 성공이 아니다. 무시하는 프로그램이나 손실된 mode sequence에는 NB9/NB16의 degraded 정책을 적용한다.

### NB4. 가상 키보드와 포커스 분리

페이지 진입·자동 복구로 가상 키보드를 열지 않는다. 입력 가능한 터미널 본체를 사용자가 직접 터치했을 때만 typing focus를 얻는다. 타이핑 중 툴바 터치는 키보드를 유지하고, 비입력 상태의 툴바 조작은 키보드를 새로 열지 않는다. 복구 오버레이를 누른 행위는 포커스 획득이나 PTY 입력으로 재해석하지 않는다.

### NB5. 수동 복구의 선점과 유한 정착

Reconnect, 툴바 Enter의 복구 동작, Start New Session은 현재 attempt가 있어도 무시되지 않는다. 명시적 동작은 오래된 fetch·backoff·geometry 대기·parser barrier·takeover 대기를 취소하고 최신 의도로 선점한다. AbortSignal 또는 동등한 generation 취소는 실제 await를 깨워야 하며, 단순 플래그 증가만으로 끝내지 않는다.

동시에 유효한 복구는 하나다. 이전 attempt의 `finally`, timeout, socket close, parser callback이 새 attempt의 참조·cursor·입력 권한을 지우지 않는다. 최신 사용자 동작으로 최종 의도가 수렴한다. 이는 로컬 복구 선점이며 다른 READY owner의 lease를 우회하는 권한이 아니다.

### NB6. 애플리케이션 liveness와 장기 복귀

WebSocket `OPEN`이나 native Ping/Pong을 입력 가능한 소유자의 증거로 삼지 않는다. READY_ACK와 현재 epoch에 귀속된 JS application heartbeat로 lease를 판단한다. 정지한 parser·준비 미완료가 heartbeat만으로 영구 소유권을 유지하지 못하도록 ready deadline과 필요한 진행 상태를 구분한다. 출력이 없는 정상 idle 셸은 그 자체로 실패가 아니다.

hidden 동안의 시간은 60초 **전면 자동 복구 예산**을 소진시키지 않는다. 기존 60초는 visible 상태에서 실제 재시도한 적극적 복구 구간으로 한정하며, 소진 뒤에는 수동 복구를 계속 제공하고 서버 유예 안에서 낮은 빈도의 backoff 복구를 유지한다. `visibilitychange:visible` 또는 `online`은 만료·displaced 등 명시적 종결 상태가 아닌 한 즉시 한 번의 복구/유효성 확인을 유발한다. 사용자 취소나 정상 다른 소유자와의 conflict를 자동 takeover로 바꾸지 않는다.

### NB7. 원샷 모디파이어의 결정적 정리

Shift와 CTRL은 상호 배타적인 1회 토글이다. Shift는 TAB/방향키 조합에 적용한다. 소비한 입력, ESC 취소, paste, compositionstart, 복구·소유권 전환에서 필요한 pending 상태를 해제하여 나중의 일반 문자가 Ctrl+C 등으로 변하지 않게 한다. 조합 중 ESC는 IME 취소이며 별도 터미널 ESC를 날조하지 않는다.

### NB8. 모바일 viewport와 단일 행 툴바

Android Chrome 108+에서 `interactive-widget=resizes-content`로 키보드 출현 시 실제 layout viewport와 xterm 줄 수를 보정한다. 프롬프트와 하단 툴바는 키보드 위에 노출된다. 390 CSS px에서 12개 요소를 가로 스크롤 없는 단일 행에 제공하며, 360px 이하·Safe Area에서도 조작이 잘리지 않는다. 기존 배열과 규격은 §4.5를 따른다.

### NB9. 동일 세션·새 세션·불연속 emulator의 분리

기존의 무조건적인 `terminal.reset()` 금지는 **동일 세션의 연속적인 재개**에 한정한다. 이때 alternate screen, 커서, DEC mode, mouse tracking 등 기존 emulator 상태를 보존한다.

명시적 새 PTY가 승인되면 **첫 출력 적용 전에** terminal reset 또는 Terminal 재생성으로 이전 세션의 화면·모드·parser·cursor·종료 플래그를 분리한다. create가 거절되었는데 이전 결과 화면부터 지우지 않는다. `isExitedRetained` 등 이전 상태는 신규 attempt/승인된 created·attached 상태를 오염시키지 않는다.

gap 또는 reload로 emulator 상태가 사라진 경우, byte position만 남았다고 화면 복원이 완료된 것은 아니다. 재구성 가능한 출력을 replay하고 필요시 redraw를 요청하되, 상태를 입증할 수 없으면 degraded를 유지한다. 최신 tail이 escape sequence나 UTF-8 문자 중간에서 시작할 수 있다는 사실도 이 경계에 포함된다. snapshot은 향후 선택 가능한 수단이지 현재 존재한다고 가정하는 성공 근거가 아니다.

### NB10. 날조 입력 금지와 입력 준비의 분리

모든 사용자 액션은 UI 제어, 복구 제스처, IME 조합, PTY 명령 입력으로 구분한다. 복구를 위한 탭·Enter·visibility 이벤트는 PTY에 **0 bytes**를 보낸다. 전송 여부가 불확실한 과거 입력을 자동 재전송하지 않는다.

READY_ACK 전, retained viewer, conflict, displaced, sync 중에는 키보드를 PTY로 보내지 않으며 “입력 대기/불가” 상태를 보인다. 이 상태에서 누른 키를 성공한 입력처럼 표시하거나 ACK 뒤 자동 제출하지 않는다. 정상 입력도 전송 요청, PTY 전달, 프로그램의 실행 결과를 혼동하지 않는다.

### NB11. 종료 결과 읽기와 새 세션의 독립성

루트 종료 코드/신호와 최종 보존 출력을 EXITED_RETAINED로 제공한다. retained replay 완료는 해당 attempt의 **읽기 전용 완료**이며, 입력을 위한 READY_ACK를 기다리는 미완료 연결이 아니다. Start New Session은 replay 중에도 NB5에 따라 선점할 수 있다. 새 세션은 `isExitedRetained = false`에 해당하는 독립 상태에서 정상 준비·입력 루프를 수행한다.

PTY EOF, root exit, 마지막 bytes drain, 하위 프로세스 잔존은 서로 다른 사실이다. 먼저 도착한 EOF나 exit callback 하나로 완료 결과를 조기 확정하거나 남은 출력을 폐기하지 않는다. exit code를 확보하지 못한 경우 0으로 간주하지 않고 미확인 상태를 나타낸다. 종료 결과 열람과 전체 프로세스 트리 회수는 별도 완료 경계다.

### NB12. Successor Token + Lease Epoch의 원자적 연속성

서버 발행의 일회성 `successorToken`, 단조 증가한 `connectSequence`, 해당 `clientInstanceId`가 현재 세션 자격과 일치하면, 이전 소켓의 writable/Pong을 기다리지 않고 이전 연결을 fence하고 새 leaseEpoch로 인계한다. raw token을 진단 로그나 화면에 노출하지 않으며, session ID나 IP/User-Agent만으로 대체하지 않는다.

소비된 token과 오래된 sequence는 새로운 인계 권한이 아니다. token 회전 승인 응답이 소실되어도 정상 사용자가 자격을 영구히 잃거나 중복 소유자가 생기지 않아야 한다. **동일 승인 시도의 재조회·중복 전달은 새 인계로 세지 않고 동일 결과로 수렴**해야 하며, 이미 다른 epoch가 확정되었다면 그 사실을 반환한다. 구체적 회전·확인 방식은 Plan에서 이 손실 응답 반례를 닫는다.

### NB13. 경합·takeover·pending contender 정책

다른 논리 클라이언트가 유효한 READY application lease를 가진 owner에게 접근하면 즉시 CONFLICT를 반환한다. 10초 native Ping 대기는 없다. lease가 만료되었거나 owner가 없어도 다른 클라이언트는 명시적 Take Over 선택을 거쳐 인계한다. 동일 논리 클라이언트의 유효 successor는 이 확인이 필요 없다.

Takeover는 사용자가 본 `leaseEpoch`를 포함한 CAS다. 그 사이 다른 인계가 있었다면 STALE과 최신 상태를 알리고 새 확인을 요구한다. 단지 기존 소켓이 닫혔고 epoch가 그대로라면 연결 부재를 이유로 stale 처리하지 않고 명시적 인계를 진행한다. 응답 소실은 유한 timeout 후 결과 재확인/재시도가 가능해야 한다.

ATTACHING/REPLAYING owner는 영구 소유권이 아니다. 서버 ready deadline을 넘기면 provisional 연결을 해제하여 다음 자격 있는 복구가 진행할 수 있게 한다. 같은 논리 클라이언트의 더 최신 유효 contender는 이전 pending 시도를 SUPERSEDED로 끝낸다. 다른 클라이언트의 추가 contender는 READY conflict 또는 일시적 OWNER_CHECK_BUSY이지 generic error가 아니다. displaced/superseded된 클라이언트는 자동 탈환을 중단한다.

### NB14. rAF 없는 준비와 취소 가능한 Replay Barrier

geometry 획득과 REPLAY_APPLIED 전송의 필수 경로에서 `requestAnimationFrame` 및 16ms polling을 제거한다. parser 적용 완료는 `terminal.write(data, callback)`의 callback과 해당 attempt/barrier로 직접 판정한다. rAF는 화면 갱신에 사용할 수 있지만 네트워크 프로토콜의 진행을 막을 수 없다.

브라우저가 **hidden이지만 JS가 실행되는 상태**에서는 paint 없이 handshake를 진행할 수 있어야 한다. **frozen 상태**에서는 timer·Promise·JS 자체가 실행되지 않을 수 있으므로 그 동안 클라이언트 진척을 약속하지 않는다. 대신 서버의 drain·유예·ready deadline이 독립적으로 작동하고, thaw 뒤 오래된 대기를 정리하여 즉시 복구한다. rAF를 setTimeout으로 이름만 바꾸는 것은 이 의무를 충족하지 않는다.

### NB15. 명시적 ACK/NACK와 전송 위치 진실성

REPLAY_END는 해당 barrier의 bytes를 실제 송신한 결과이며, REPLAY_APPLIED는 parser가 실제 적용한 결과다. READY_ACK는 그 둘과 세션/epoch가 일치할 때만 입력을 허용한다. mismatch, 잘못된 JSON/position, 잘못된 phase·owner, 종료된 세션은 원인에 맞는 NACK/상태 또는 명시적 연결 종료로 정착한다. silent break로 양측이 서로를 기다리게 하지 않는다.

OUTPUT write 실패/short write에서는 성공하지 않은 bytes만큼 logical cursor를 전진시키지 않는다. 연결 복구 시 마지막 **적용 확인 위치**에서 중복을 제거하며 복원한다. 제어 프레임(Ping 포함) 처리 뒤 pending heartbeat reply·state update·output이 다른 우연한 이벤트를 기다리며 방치되지 않는다. ACK/NACK·takeover·ready 대기는 유한하며, 클라이언트가 frozen이어도 서버가 provisional owner를 무기한 유지하지 않는다.

### NB16. 출력 연속성, gap과 degraded 복구

출력 위치는 문자열 문자 수가 아니라 원본 PTY **byte offset**이다. 같은 세션/epoch의 OUTPUT 구간 `[start, end)`와 현재 적용 위치 `applied`를 비교한다.

- `start == applied`: bytes를 순서대로 한 번 적용한다.
- `start < applied < end`: 적용한 prefix를 제외하고 새 suffix만 적용한다.
- `end <= applied`: 완전히 중복된 구간을 다시 적용하지 않는다.
- `start > applied`: gap이다. 정상 연속 적용·정상 READY를 중단하고 SYNC_REQUIRED로 전환한다.

서버에서 cursor 추월을 먼저 발견하면 `REPLAY_GAP` 또는 `SYNC_REQUIRED`에 `BUFFER_OVERRUN`, 누락 구간, 현재 보존 시작점/끝점을 알린다. 양측은 옛 target을 폐기하고 명시적인 rebase와 새 barrier로 합의한다. 사라진 byte 위치까지 `appliedPosition`을 조용히 올려 parser 적용을 날조하지 않는다.

손실 이후 최신 출력을 읽을 수 있게 하고 redraw를 요청하되, 완전한 emulator 상태를 입증하지 못하면 **“출력 일부 손실 / 화면 상태 불완전”**을 유지한다. 이 경우 기본 입력은 차단하고 **[불완전한 화면에서 계속]**이라는 명시적 선택을 제공한다. 그 선택도 입력 바이트를 만들지 않으며, 새 동기화 구간의 ACK 이후에만 제한된 의미의 입력 준비를 허용한다. 이는 손실을 복원했다는 승인이 아니다. 반복 overrun으로 재동기화가 계속 실패하면 원인을 표시하고 재시도·새 세션 선택을 열어두며 영구 spinner에 두지 않는다.

누적 `dropped_output_bytes`와 이번 resume에서 필요한 구간의 손실은 구분한다. 과거 한 번 overflow했다는 이유만으로 연속적인 이번 resume를 새로운 gap으로 표시하지 않는다. 반대로 이미 입증된 emulator 손실은 현재 byte 범위가 맞는다는 이유만으로 해소되었다고 하지 않는다.

### NB17. 복구 자격 소실과 저장 실패의 정직성

`sessionStorage`는 일반적으로 같은 page session의 reload/restore 동안 유지되지만 탭 close, 새 browsing context, 접근 거부, 사용자 데이터 삭제 등으로 사라질 수 있고, opener/탭 복제로 복사될 수도 있다. 이 한계를 사용자에게 숨기지 않는다. session ID 하나의 로컬 저장 성공은 서버 세션 생성이나 향후 모든 재진입 복구의 증거가 아니다.

복구 자격이 없으면 “기존 세션을 확인할 수 없음”과 명시적 신규 생성 선택을 제공한다. 원래 세션은 정해진 유예와 회수 정책을 따른다. 인증된 사용자별 detached-session discovery와 durable recovery credential 관리는 향후 확장으로 남기며, 현재 서버에 목록 API가 있다고 주장하지 않는다.

### NB18. 회수 권한과 비동기 객체 수명의 일치

root child의 reap 결과를 결정하는 권한은 하나다. root waiter와 경쟁하는 무차별 `waitpid(-1)`로 다른 경로의 child를 가로채지 않으며, wait 실패/`ECHILD`를 유효한 exit status로 읽지 않는다.

session, process, viewer, libuv handle을 참조하는 callback이 남아 있는 동안 그 객체를 free하지 않는다. embedded timer는 `uv_close` 완료 전 parent를 해제하지 않고, close callback에서 allocation의 소유 parent를 정확히 한 번 해제한다. interior-pointer free, 늦은 process exit callback의 UAF, viewer의 dangling `pss->session`은 금지다. 구체적 refcount 또는 소유권 구조는 Plan에서 선택하되 이 수명 경계를 보장한다.

SIGHUP → 유한 대기 → SIGKILL의 회수 의도를 유지하되, signal 전송을 PURGED의 증거로 삼지 않는다. 만료/reaper timer 초기화·시작 실패에서도 살아 있는 트리를 “회수 완료”로 표시하거나 추적에서 지우지 않는다. 실패는 추적 가능한 TERMINATING/회수 실패로 남고, 실제 확인 뒤 해제한다. PID 재사용으로 무관한 프로세스를 회수 대상에 넣지 않는다.

### NB19. 보존 약속을 깨지 않는 수용 상한과 pruning

세션 수 상한은 attached만 세어서는 안 된다. detached 실행 프로세스, retained 결과, 회수 중 리소스와 실제 할당 buffer/전송 메모리를 포함하여 수용 가능성을 판단한다. `TTYD_MAX_SESSIONS`가 현재 detached를 직접 센다는 초안 설명은 채택하지 않는다.

승인한 세션의 9시간 유예·결과 보존을 먼저 지키며, 정상 용량 압박은 신규 create의 명시적 거절로 처리한다. 보존 약속 안의 결과를 알리지 않고 pruning하여 용량을 맞추지 않는다. retained 상한 N은 N개를 허용하며, 단순 수 계산상 pruning 필요 조건은 **`retained > max_retained`**이지 `>=`가 아니다. 실제 삭제는 만료·명시적 종료 등 삭제 자격과 참조 안전성을 함께 만족해야 한다. 현재 exit callback의 세션이나 연결된 viewer를 즉시 free하지 않는다. 만료 등으로 viewer를 분리할 때도 상태 통지·fencing 후 참조가 끝난 뒤 해제한다.

half-open transport가 `--max-clients`를 차지해 successor HELLO 자체를 영구 차단하지 않도록, 자격 있는 기존 세션 교체를 판정할 수 있는 **유한한 복구 수용 경로**가 있어야 한다. 이는 무제한 연결 허용이 아니다. fragmented client message는 재조립 전체 크기에 유한 한도를 적용하고 초과를 명시적으로 거절한다. 정상 paste와 제어 메시지의 지원 범위, 정확한 자원 상한은 Plan에서 정하되 조각별 한도만으로 전체 한도를 대신하지 않는다.

## 4. Behavior and UI Policy (상태·소유권·상호작용)

### 4.1 서버 세션 수명과 연결 상태는 별개다

| 서버 상태 | 의미와 허용 동작 | 다음 경계 |
| --- | --- | --- |
| ACTIVE | 살아 있는 작업이 연결 소유자를 갖는다. 소유자의 ATTACHING/REPLAYING과 입력 가능한 READY는 구분한다. | 소유권 상실/단절 → DETACHED_GRACE, 루트 종료 → 결과 수집 후 EXITED_RETAINED |
| DETACHED_GRACE | 입력 owner 없이 작업·PTY drain을 유지한다. 마지막 유효 lease 상실/단절을 서버가 확인한 시점부터 9시간(32,400초) 유예다. | 유효 재개 → ACTIVE, 루트 종료 → EXITED_RETAINED, 만료 → TERMINATING |
| EXITED_RETAINED | exit code/signal과 최종 보존 출력을 읽는다. live 셸이나 입력 READY로 돌아가지 않는다. | 만료·명시적 종료 → TERMINATING/회수, 새 세션 선택 → 별도 세션 생성 |
| TERMINATING | 신규 입력·소유권 인계를 막고 실제 트리 및 참조 회수를 진행한다. | 회수 확인과 callback/handle 종료 → PURGED |
| PURGED | 해당 자원이 실제로 해제되었다. 재접속에는 expired/종료 이유를 알린다. | 기존 ID를 자동으로 새 PTY에 재사용하지 않는다. |

살아 있는 세션의 유효한 재개는 detach 유예를 취소한다. provisional attempt의 반복만으로 무기한 자원을 점유하지 않게 ready deadline을 적용한다. 이미 detached 상태에서 루트가 종료되면 기존 유예 deadline을 유지하고, attached 상태에서 종료되면 종료 시점부터 9시간 결과 보존을 시작한다. retained 결과를 열람하거나 재접속하는 것만으로 보존 deadline을 계속 연장하지 않는다. 명시적 새 세션 시작은 기존 결과/실행 작업의 명시적 종료와 다르며, 기존 세션의 보존·회수 정책을 조용히 무효화하지 않는다.

### 4.2 클라이언트 연결 상태와 화면 의미

| 상태 | 표시·허용 입력 | 복구·전이 |
| --- | --- | --- |
| Disconnected / Recovering | 연결 중 또는 재시도 중. PTY 입력 불가, 복구 제어는 사용 가능 | HELLO 시도, backoff, 사용자의 선점 |
| Connected / Attaching | 소켓 연결과 세션 자격 확인 중. “입력 준비 완료” 표시 금지 | SESSION_ACCEPTED 또는 명시적 실패/CONFLICT |
| Replaying | 백로그 적용 중. paint 대기가 아닌 parser barrier 진행 | REPLAY_APPLIED → READY_ACK 또는 SYNC_REQUIRED |
| Ready | 현재 epoch의 입력 권한 확인. visible에서 화면·geometry도 확인 | 사용자 입력, heartbeat, 단절 시 권한 차단 |
| Sync Required / Degraded | 손실 구간·화면 불완전 표시. 기본 입력 차단 | 명시적 rebase/재시도, 불완전 상태 수용 후 ACK, 새 세션 |
| Exited Retained | 종료 코드/신호와 읽기 전용 결과. 입력 불가 | replay 완료로 attempt 정착, 언제든 Start New Session |
| Conflict | “세션이 이미 다른 탭에서 사용 중입니다” | Take Over, 취소, 재확인. 자동 steal 금지 |
| Taking Over | CAS 인계 요청 중. 키 입력 불가 | 결과/STALE/유한 timeout, 수동 취소·선점 가능 |
| Displaced / Superseded | “세션이 다른 연결로 이동되었습니다” 또는 이전 시도 대체 | 자동 탈환 중단. 새 세션이나 별도의 명시적 재확인만 허용 |
| Expired / Unknown / Rejected Capacity / Protocol Error | 원인을 구분하고 새 셸 미생성을 명시 | 해당 의미의 Retry 또는 명시적 Start New Session |

`Connected ≠ Accepted ≠ Replay Applied ≠ Ready ≠ 화면 완전 복원 ≠ 작업 성공`이다. hidden에서 Ready가 되어도 화면이 실제로 표시되었다고 주장하지 않는다. 자동 복구가 잠시 쉬는 상태와 서버 세션이 만료된 상태도 구분한다.

### 4.3 논리적 클라이언트와 탭 복제의 한계

`resumeId`는 세션 locator, `clientInstanceId`는 논리 클라이언트 표식, Successor Token은 연속성 자격, leaseEpoch는 서버가 확정한 소유권 세대다. 어느 하나를 물리적 탭의 완전한 증명으로 취급하지 않는다.

서로 다른 자격/논리 클라이언트가 같은 세션을 요청하면 기존 READY owner를 보호하고 CAS takeover를 요구한다. 그러나 탭 복제 등으로 **동일한 모든 자격 bytes가 복제된 경우 서버가 물리적 탭을 구별할 수 있다는 약속은 하지 않는다.** 이 경우 일회성 token 소비와 epoch/sequence로 하나만 승자로 만들고, 패자는 자동으로 sequence를 올려 탈환하지 않는다. 이 한계는 THESIS-001의 “동일 resumeId만으로 같은 탭과 복제 탭을 완전히 구별”하는 해석을 대체한다. 정상 복구의 저지연과 구별 불가능한 credential clone의 완전 식별을 동시에 주장하지 않는다.

### 4.4 수동 복구·인계·종료 선택

- 일반 Reconnect는 기존 승인 세션의 resume이다. 자동 create나 자동 다른 owner takeover가 아니다.
- Start New Session은 명시적 create 의도이며 현재 로컬 recovery를 선점한다. 현재 retained 표시·terminal 모드·cursor는 새 승인 세션과 분리한다.
- Take Over만 다른 owner의 세션 인계 의도를 나타내며 observed leaseEpoch에 대한 CAS로 처리한다.
- 복구/인계/새 세션 버튼의 pointerdown, click, Enter가 중복 전송·개행으로 변하지 않게 로컬에서 소비한다. 연속 탭으로 이전 비행을 기다리지 않되 최신 의도 하나로 수렴한다.
- 다른 소유자에게 displaced된 화면의 일반 복귀 이벤트는 자동 탈환을 시작하지 않는다. 명시적 재확인은 최신 소유권 상태를 조회하는 것이지 과거 token을 재사용하는 우회가 아니다.
- 세션 종료는 작업과 보존 결과를 끝내는 명시적 선택이다. 탭 닫기, 화면 잠금, 새 세션 생성과 혼동하지 않는다.

### 4.5 계승하는 모바일 UI·IME 계약

390 CSS px의 단일 행 배열은 `TAB(33px)`, `Shift(30px)`, 네 방향키(각 29px), `Enter(32px)`, `ESC(33px)`, `CTRL(40px)`, `A-/A+(각 29px)`, `전체화면(29px)`의 12요소다. 높이는 34–36px, `touch-action: manipulation`, 폰트 조절 범위는 8–32px다. 360px 이하와 Safe Area에서는 필요한 padding/flex 축소를 적용하여 양 끝 조작을 보존한다. 방향키는 xterm application cursor mode를 반영하고 Shift+Tab은 `\x1b[Z`다.

| 동작 | 포커스·키보드 | 입력 의미 |
| --- | --- | --- |
| 페이지 진입·자동 복구 | blur, 키보드 닫힘 | 입력 생성 없음, modifier 중립 |
| Ready 터미널 본체 탭 | typing focus, 키보드 열림 | Shift 해제, CTRL은 다음 의도한 입력까지 유지 |
| 타이핑 중 툴바 터치 | typing focus와 열린 키보드 유지 | 해당 특수 키만 전송, 1회 modifier 정리 |
| 비입력 상태 툴바 터치 | 키보드 닫힘 유지 | UI/특수 키/복구 의도를 상태에 따라 분리 |
| 복구 오버레이·Enter | blur, 키보드 열지 않음 | 복구만 실행, modifier 모두 해제, PTY 0 bytes |
| 한글 composition | 조합 수명 추적 | 완료 텍스트를 정확히 한 번 전달 |
| composition 중 Enter / ESC | 조합 확정 / 로컬 취소 | Enter를 별도 명령 제출로, ESC를 별도 PTY 키로 누설하지 않음 |
| Paste | 기존 입력 흐름 유지 | 1글자라도 순수 paste로 처리, armed modifier 먼저 해제 |

## 5. Truth & Causal Invariants (진실 및 인과 불변식)

1. **I1 — 작업 정체성**: resume 성공의 대상은 승인된 동일 세션/작업이다. 로컬 ID, 열린 소켓, 새 셸 프롬프트만으로 증명하지 않는다. 새 PTY는 명시적 create로만 생긴다.
2. **I2 — 단일 입력 권위**: 한 세션에는 현재 leaseEpoch의 입력 owner가 최대 하나다. fence 이후 이전 연결의 입력·resize·늦은 callback은 효력이 없다. native Pong은 애플리케이션 lease를 대신하지 않는다.
3. **I3 — 적용 위치 진실성**: bytes 수신, socket write 성공, parser 적용, 화면 paint는 서로 다르다. appliedPosition은 현재 세션의 실제 parser 적용 bytes 또는 명시적으로 선언된 rebase에 의해서만 변하며, rebase를 적용 성공으로 기록하지 않는다.
4. **I4 — 도달 가능한 barrier**: REPLAY_END target은 해당 동기화 구간에서 도달 가능해야 한다. ring overrun으로 구간이 사라지면 정상 END/READY 대신 gap과 새 barrier로 전환한다. 실패한 write는 cursor를 전진시키지 않는다.
5. **I5 — 비차단·유한 보존**: transport/renderer flow control이 PTY drain을 멈추지 않는다. 보존 payload는 최대 8 MiB, 나머지 버퍼·pending 메시지도 유한하다. 보존 초과는 최신 bytes 유지와 명시적 손실이지 무한 메모리나 침묵 정지가 아니다.
6. **I6 — 날조 없는 의도**: 복구·인계·UI 동작은 PTY 0 bytes이며, 불확실한 입력의 자동 재전송은 없다. modifier·composition·paste가 뒤의 입력으로 누설되지 않는다.
7. **I7 — 준비와 화면의 정직성**: READY_ACK는 입력 권한과 parser barrier의 성립이지 실제 paint·완전한 TUI 상태·프로그램 성공의 증명이 아니다. degraded 상태를 성공 문자열이나 reset으로 지우지 않는다.
8. **I8 — 복구의 최신성**: 취소된 attempt는 최신 attempt의 자원과 state를 정리할 권한이 없다. hidden/frozen 시간이 수동 복구 가능성을 소멸시키지 않는다. 브라우저가 멈춘 동안의 진척을 날조하지 않는다.
9. **I9 — 종료의 분리**: EOF, root exit, final output, descendant reap은 별도 사실이다. EXITED_RETAINED는 read-only 완료이며 이후 새 세션의 준비 가능성을 막지 않는다.
10. **I10 — 참조 수명과 회수 진실성**: callback/handle/viewer가 참조하는 객체를 먼저 free하지 않는다. reap 결과의 소유자는 하나이고 kill 로그나 timer 실패는 PURGED가 아니다. 상한 N에 정확히 N개 있는 상태는 초과가 아니다.
11. **I11 — 보장 경계**: 9시간은 가동 중인 서버가 승인한 세션의 유예·보존 정책이다. storage가 사라진 상태의 자동 재발견, 서비스 재시작을 가로지르는 영속성, arbitrary TUI의 유실된 모든 mode 재구성까지 입증한 것처럼 넓히지 않는다.

## 6. Counterexample Stress Tests (경계 스트레스와 거짓 성공 반증)

아래는 **향후 수락 검증이 닫아야 할 반례**이지 이번 문서 작업에서 실행한 테스트 목록이 아니다. 같은 서버 세션·epoch·출력 범위·PTY 결과를 결합하여 관찰해야 하며, 단일 로그 문자열이나 mock의 ACK만으로 통과시키지 않는다.

| 반례 상황 | 실패로 판정할 모습 | 요구 결과와 판독 |
| --- | --- | --- |
| **ST1 — 침묵 단절 후 동일 client 재연결**: FIN/RST와 기존 Pong을 차단하고 유효 successor로 HELLO | 2초 protocol error 또는 10초 owner-check 대기, 새 PTY 생성 | 같은 세션으로 0 **추가 Owner Check RTT** 인계. 이전 epoch 즉시 fence, 새 ACK 후 입출력. 서버 소유권·PTY 식별과 wire 순서로 확인 |
| **ST2 — 다른 탭·기기의 READY owner 충돌/CAS**: conflict를 본 뒤 다른 인계 또는 기존 소켓 close 발생 | silent steal, stale epoch로 인계, 소켓만 닫혔는데 무조건 stale | 정상 READY owner 유지와 즉시 CONFLICT. epoch 변경이면 STALE, 동일 epoch의 명시적 takeover는 owner close 후에도 성공. 이전 탭 자동 탈환 없음 |
| **ST3 — hidden rAF 정지와 frozen 복귀**: geometry 없는 hidden 시작, 또는 replay 직후 rAF를 중단; 이후 JS 전체 freeze/thaw | 80×24도 없이 rAF await, parser 적용 후 READY 미전송, thaw 후 60초 예산 소진만으로 영구 중단 | JS 실행 가능한 hidden에서는 fallback과 parser callback으로 handshake. frozen 동안 서버 drain·ready deadline 유지, thaw 후 최신 attempt 복구. 실제 paint는 visible 복귀 후 별도 확인 |
| **ST4 — replay 중 8 MiB overrun**: 느린 consumer보다 빠르게 출력하여 output_start가 send_position/옛 target을 추월 | 도달 불가능한 REPLAY_END, target까지 무한 대기 | BUFFER_OVERRUN/GAP과 정확한 누락 범위, 새 barrier/rebase, 최신 출력 판독. 누락 bytes를 applied로 속이지 않음 |
| **ST5 — READY 후 PAUSE 동안 8 MiB 초과**: RESUME 후 추가 출력 | 이후 모든 출력이 침묵, 서버는 정상 READY라고 주장 | live stream도 gap 감지·재동기화, 새 출력 진척 또는 반복 overrun의 명시적 상태. PTY 생산자는 완주 |
| **ST6 — exited_retained에서 Start New Session**: retained replay 진행 중·완료 후 각각 선택 | pending promise 때문에 클릭 무시, 새 세션에도 종료 플래그, 옛 alternate screen 잔류 | 이전 attempt 선점, retained 읽기 완료의 정착, 승인된 새 세션 첫 bytes 전에 emulator 분리, 새 READY_ACK와 실제 입력 성공 |
| **ST7 — reaper와 exit callback 경합**: root 종료 직후 expiry/reaper, 지연된 async callback과 uv close | UAF, interior free, ECHILD를 exit 0처럼 해석, 다른 child 수거 | 단일 reap 권한, callback/close 완료까지 수명 보장. 메모리 오류 없음과 실제 트리 회수, 미회수 시 TERMINATING 유지 |
| **ST8 — retained 상한 1/N 및 viewer**: 현재 세션이 exit되고 다른 retained viewer가 열린 상태 | N개인데 N−1로 감소, 현재 callback/viewer dangling pointer | N개 허용, 보호 중 참조 유지, 삭제 자격 없는 결과 보존. 추가 자원 필요는 신규 admission에서 명시적 거절 |
| **ST9 — 잘못된 REPLAY_APPLIED**: wrong position, malformed payload, old epoch, retained 상태 | silent break 후 입력 불가 spinner | 원인별 NACK/종결 상태, 서버 ready deadline, stale ACK가 새 owner를 Ready로 만들지 않음 |
| **ST10 — 출력 write 실패/중복**: transport write 실패 직후 재개, 겹치는 OUTPUT 재전달 | cursor만 전진하여 실제 bytes 소실 또는 화면에 중복 적용 | 미송신 위치는 전진하지 않고 적용 위치로 복원. prefix 중복 제거와 최종 bytes/화면 일치 |
| **ST11 — successor 승인 응답 소실/동시 contender**: token 소비 직후 응답 drop, 같은 token의 경쟁 요청 | 자격 영구 소실, 둘 다 owner, SUPERSEDED 클라이언트의 자동 탈환 | 동일 승인 시도는 같은 결과로 수렴, 하나의 epoch owner만 존재. 최신 유효 시도/명시적 STALE·BUSY로 정착 |
| **ST12 — 수동 preemption의 늦은 callback**: parser 또는 fetch 대기 중 연속 Reconnect/Start New Session 후 오래된 finally 실행 | 새 socket이 닫히거나 새 connectPromise가 제거됨, 잘못된 세션에 입력 | 최신 사용자 의도 하나만 유효. 옛 callback은 새 상태에 영향 없음. 복구 제스처 PTY 0 bytes |
| **ST13 — storage/create 경계**: storage 접근 거부·소실, create capacity 거절 후 reload, 승인 응답 유실 | nonexistent ID를 확정 binding으로 표시, 자동 중복 셸 또는 기존 작업 복구 주장 | pending/승인 구분과 정직한 오류. 동일 생성 의도 중복 방지. 자격 소실 시 명시적 새 세션 선택 |
| **ST14 — TUI 모드 gap과 동일 크기 redraw**: alternate screen/mouse mode 중 gap, SIGWINCH 무시 프로그램 | reset으로 연속 화면 파괴 또는 SIGWINCH 성공만으로 완전 복원 판정 | 연속 resume는 상태 보존. 새 PTY만 초기화. gap은 손실·불완전 표시와 명시적 계속 선택, 실제 TUI readback으로만 복원 판정 |
| **ST15 — max-clients·fragment·timer 실패**: half-open으로 transport 한도 소진, 과대 fragmented message, expiry timer start 실패 | HELLO조차 영구 차단, 무제한 메모리, 추적 없는 세션 유출 또는 거짓 PURGED | 유한한 successor 판정 경로, 총 메시지 크기 거절, timer 실패 상태 및 실재 자원 추적. 정상 기존 세션 보존 |
| **ST16 — EOF/exit 순서 뒤집힘**: 종료 직전 마지막 출력과 늦은 root status, 하위 프로세스 잔존 | 마지막 결과 누락, 미확인 exitCode=0, root exit만으로 전체 회수 완료 | 최종 출력/종료 상태/하위 트리를 따로 판독하고 결과 보존. 수거 완료는 실제 프로세스 관찰로 확인 |
| **ST17 — Android 실제 입력·viewport 회귀**: 390/360px, Safe Area, IME Enter/ESC, paste, CTRL→ESC→c | 키보드 가림, 버튼 잘림, 중복 한글, 의도하지 않은 submit/SIGINT | 실제 viewport·툴바·프롬프트 판독, 정확한 PTY bytes와 한 번의 조합 전달, 일반 c 보존 |

## 7. Decision Priorities & Boundary (결정 우선순위와 경계)

### 7.1 충돌 시 우선순위

1. **프로세스·메모리 수명과 입력 의도**가 연결 속도나 매끈한 성공 UI보다 우선한다. UAF·잘못된 reap·날조 입력을 “복구 성공률”로 상쇄하지 않는다.
2. **승인된 작업·결과 보존과 단일 소유권**이 신규 세션 수용보다 우선한다. capacity 부족은 기존 유예 단축이나 silent steal의 허가가 아니다.
3. **실제 적용·손실의 진실성**이 무조건 Ready 표시에 우선한다. gap을 고지하고 degraded로 계속할 수는 있어도 완전 복원으로 명명하지 않는다.
4. **유효 successor의 즉시 인계와 사용자의 수동 선점**이 이전 dead transport의 Pong 대기보다 우선한다. 단 다른 논리 클라이언트의 유효 owner 권한은 별도의 명시적 takeover 없이 침해하지 않는다.
5. **비차단 생산과 유한 메모리**가 무제한 출력 이력 보존보다 우선한다. 8 MiB 밖의 출력은 잃을 수 있으나 최신 출력 진척과 손실 고지는 잃지 않는다.
6. **프로토콜 진척**은 paint보다 우선한다. 화면 완전성과 사용자 판독은 별도 증거를 요구하며, frozen JS가 실행된다는 가정은 하지 않는다.
7. **기존 모바일 조작의 완결성**을 유지한다. 프로토콜 개선을 이유로 포커스·IME·툴바의 의미를 축소하지 않는다.

이는 구현 순서나 현재 Scope 선택이 아니다. P0 네 결함, A–E 보정과 P1 실패 경로를 포함한 전체 약속은 여기서 보존하며, 이후 Main이 실제 적용 범위와 방법을 결정한다.

### 7.2 범위와 의도적 비약속

- 대상은 Android 브라우저와 Linux 호스트의 webterm/ttyd다. 기존 운영 경계인 `/home/user01/.local/bin/ttyd`(port 7683), `/home/user01/.local/share/webterm/index.html`, `session.sh`, Tailscale Funnel의 `/terminal` → `127.0.0.1:7683`를 계승한다. 이번 작업에서 해당 실행물이나 경로의 현재 가동·버전 일치를 검증하지 않았다.
- 서버/호스트 재시작, 디스크 영속 세션 저장, 항상 남는 브라우저 storage, 8 MiB 이전 출력의 완전 복원은 현재 약속이 아니다. 서버의 정상 용량 부족을 보존 약속을 깨는 예외로 사용하지 않는다.
- durable session discovery 및 terminal snapshot은 오라클의 P2 확장이다. 이번 정의는 그 부재를 숨기지 않고 올바른 unknown/degraded 행동을 요구한다. 계정별 목록 권한이나 snapshot 형식은 이를 실제로 채택할 Scope 전에 정해야 하며, 지금 구현 의무로 끼워 넣지 않는다.
- 동일 credential이 완전히 복제된 물리적 탭을 확실히 식별한다는 보장은 없다. 외부 접속 인증을 Successor Token으로 대체하지 않는다.
- Windows 분기는 `pty_signal_foreground()`가 false를 반환하는 등 Linux와 의미가 다르다(`src/pty.c:230–252`). 이 문서의 Linux foreground signal·프로세스 트리 보장을 Windows에서 이미 충족한다고 주장하지 않으며, Windows 지원 확대는 별도 요청 범위다.
- 방법 선택으로 남기는 것은 token 회전의 정확한 wire encoding, 취소/refcount 구조, ring 대 deque 선택, heartbeat·ready deadline의 구체적 수치, bounded admission/fragment 크기다. 그 선택은 위 반례를 닫아야 하며 제품 의미를 약화할 수 없다.
- THESIS-001에서 참조한 완료 이력은 불변이다. 연결·소유권·종료·buffer·입력·모바일 회귀를 다루는 후속 Scope/Plan의 의미 적합성 재검토는 Main의 책임이며, 여기서 Scope 생성·구현·배포·검증 판정을 시작하지 않는다.

## 8. Authoritative Readback (권위 있는 성공 판독)

제품이 완성되었다는 판정은 아래 실제 경계의 증거를 결합해야 한다. 이 문서의 존재, 소스 diff, 단위 mock, “attached” 로그 하나는 대체 증거가 아니다.

| 주장 | 권위 있는 판독 | 대체할 수 없는 증거 |
| --- | --- | --- |
| 같은 작업으로 복귀했다 | 실제 서버 세션 identity, 생존 작업의 프로세스 identity, 이전 작업 결과/화면, 승인된 client binding의 일치 | 같은 resumeId 문자열, 새 셸 프롬프트만으로 판정 금지 |
| owner 인계가 완료되었다 | 서버 leaseEpoch·ownerPhase와 실제 old-epoch INPUT 거절, 새 client의 READY_ACK | native Pong, client의 로컬 ready boolean만으로 판정 금지 |
| 0 RTT successor 인계다 | HELLO 처리부터 인계까지 기존 owner Ping/Pong 왕복이 없는 사건 순서와 동일 작업 유지 | 모든 네트워크 지연이 0ms라고 주장 금지 |
| replay가 적용되었다 | 서버 OUTPUT 범위/전송 결과, client parser callback의 적용 범위, 동일 target·epoch의 REPLAY_APPLIED/READY_ACK | frame 수신, pendingBytes 표시, paint 이벤트 하나만으로 판정 금지 |
| output gap을 복구했다 | 실제 output_start/end·누락 구간, GAP/rebase, 새 barrier, 최신 출력과 degraded 고지의 일치 | cursor를 임의 증가시키거나 누적 truncated flag만 확인하는 것으로 판정 금지 |
| UI가 작업 가능한 상태다 | 실제 Android visible 화면의 TUI/프롬프트/geometry/키보드/툴바와 의도한 입력 결과 | resize syscall·SIGWINCH 성공만으로 판정 금지 |
| 복구 입력을 날조하지 않았다 | 복구/인계 제스처에 귀속된 실제 PTY 수신 bytes가 0, 이후 명시적 입력만 전달됨 | 버튼 handler 호출 수, client send mock만으로 판정 금지 |
| detached 작업이 완료되었다 | 실제 프로그램의 진행/종료 코드와 최종 출력, retained readback | PID가 살아 있음 또는 root exit 단독으로 전체 결과·트리 완료 판정 금지 |
| 자원이 회수되었다 | OS 프로세스 identity/트리 소멸, wait 결과, callback·uv close 완료와 session/viewer 참조 해제 | kill 로그, session table에서 삭제됨, timer 예약 성공만으로 판정 금지 |
| 운영 경로가 복구된다 | 실제 배포 binary·bundle·설정 식별, 외부 `/terminal/ws` 양방향 경로에서 위 루프 실행 | 저장소 commit 일치나 정적 페이지 로드만으로 판정 금지 |

### 최종 권위 문장

**이 제품에서 재연결 성공은 “다시 열린 소켓”이 아니라, 승인된 동일 작업에 대해 현재 논리 소유자가 확정되고, 보존 가능한 출력이 올바른 emulator 문맥에 실제 적용되며, 손실·종료·권한 변화가 명시되고, 그 사실과 일치하는 입력 권한이 서버에 의해 확인된 상태다. 종료된 작업은 읽기 전용 결과로 완결되고, 새 세션은 명시적 의도와 독립 상태로 시작한다. 브라우저가 잠들거나 출력이 8 MiB를 넘었다는 이유로 생산자·복구·최신 출력이 영구 정지해서는 안 되며, 그 보장을 위한 서버 회수 경로 자체가 다른 세션을 파괴해서도 안 된다.**
