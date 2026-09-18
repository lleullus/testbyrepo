# Scope: v4 Protocol, Successor Token Takeover, and rAF-free Recovery Core

Schema: iis-scope/v1
Project-Root: /home/user01/project/webterm/ttyd-1.7.7
Status: done

## Product Authority

- /home/user01/project/webterm/ttyd-1.7.7/docs/planning/product-thesis/android-web-terminal/THESIS-002.md sha256:3ac3c25dd0e520e0af1269dd5de32b100400b86872e76ec2704d9d9b22a0e067

## Transition Authority

- /home/user01/project/webterm/ttyd-1.7.7/docs/planning/baseline/BASELINE-002.md sha256:285004a80d06ef8ac794513c10af08056d1ed94f992bbe7d2f2041523e9039f5

## Outcome

현재 코드는 WebSocket 단절 후 재연결 시 이전 반단절(half-closed) 소켓의 생존 여부를 2초/10초 핑퐁(Owner Check)으로 판별하여, 2초 내 쓰기 지연 시 허위 프로토콜 에러(`session-error`)를 내고 복구를 영구 중단하거나 10~12초의 긴 프리징을 유발한다. 또한 브라우저 백그라운드/절전 시 중단되는 `requestAnimationFrame(rAF)`을 기하구조 획득(`waitForGeometry`)과 리플레이 완료(`settleReplay`)의 필수 조건으로 삼아 백그라운드 복구를 교착시키며, `SESSION_READY` 위치 불일치 시 침묵 무응답(`break`)으로 키 입력을 영구 폐기하고, 종료된 세션(`exited_retained`) 화면을 본 클라이언트가 플래그를 고착시켜 새 세션 생성 및 입력을 차단한다.

이 Scope는 승인된 Transition Baseline `BASELINE-002`의 `BLOCK-004`를 하나의 `HARD_ATOMIC` 제품 경계로 구현하여 확립한다. 클라이언트와 서버 간 v4 프로토콜을 도입하여 일회성 `successorToken`과 단조 증가하는 `connectSequence`, `leaseEpoch`를 통해 이전 죽은 소켓의 핑퐁 대기 없이 0 추가 Owner Check RTT로 세션을 원자적으로 인계하고 이전 epoch를 즉시 격리(fencing)한다. 프로토콜 게이트에서 rAF와 16ms 폴링을 전면 제거하여 80×24 Fallback Geometry와 파서 완료 콜백(`terminal.write`) 배리어로 백그라운드 핸드셰이크를 완결하며, `REPLAY_APPLIED`에 대한 서버 `READY_ACK` 및 위치 불일치 시 명시적 `SYNC_REQUIRED`/`POSITION_MISMATCH` NACK를 도입하여 데드락을 차단한다. `exited_retained` 상태는 읽기 전용으로 정착시키고 수동 복구 및 새 세션 시작 시 이전 대기를 즉시 선점(preemption)하며 에뮬레이터 상태를 완전 분리한다.

포함 범위는 `THESIS-002`의 NB1, NB3, NB5, NB6, NB9, NB10, NB11, NB12, NB13, NB14, NB15, NB17 및 `BASELINE-002`의 R1, R2, R4, R7, B4-E1~B4-E6, ST1, ST2, ST3, ST6, ST9, ST11, ST12, ST13이다. BLOCK-005에 속하는 8 MiB 순환 청크 버퍼 구조체 교체(`memmove` 제거), `session_reaper` libuv/waitpid 메모리 수명 교정(P0-3), Retained Pruning 조건 수정(P0-4) 및 BLOCK-006의 실제 운영 7683 서비스 cutover는 이번 Scope에서 제외하되, B4의 신규 프로토콜 경로가 해당 결함을 은폐하거나 새로운 UAF를 유발하지 않도록 격리된 실제 ttyd 인스턴스에서 검증한다.

## Acceptance

### v4 핸드셰이크 식별과 침묵 단절 0 RTT 무지연 인계

격리된 실제 ttyd 서버와 클라이언트 간에 정상 세션이 수립되어 첫 `READY_ACK`와 함께 일회성 `successorToken`을 발급받은 후, 클라이언트의 네트워크 단절(TCP FIN/RST 누락 모의)을 발생시키고 동일 세션 식별자와 새 `connectSequence`, 유효한 `successorToken`을 담은 v4 `HELLO`로 재접속하면, 서버는 이전 소켓에 대한 2초/10초 핑퐁 대기 없이 이전 소켓(`old leaseEpoch`)을 즉시 격리(fencing)하고 새 `leaseEpoch`로 인계한다. 이전 소켓에서 유입되는 지연 입력·리사이즈·하트비트는 모두 거절되며, 클라이언트는 허위 프로토콜 에러(`session-error`)나 10초 대기 없이 즉시 세션 리플레이 및 준비 단계로 진입한다. 권위 판독은 서버 로그 및 wire 상에서 기존 소켓 대상 핑퐁 왕복 부재, 새 epoch 확정, 및 동일 PTY 프로세스 유지로 확인한다.

### READY 소유권 경합 즉시 차단 및 CAS 기반 명시적 Takeover

서로 다른 논리 클라이언트 식별자(`clientInstanceId`)를 가진 두 번째 연결이 활성 `READY` 상태의 세션에 접근하면, 서버는 10초 대기 없이 즉시 `CONFLICT` 응답을 반환하고 기존 소유자의 입력 및 리사이즈 권한을 유지한다. 두 번째 클라이언트가 사용자가 확인한 `leaseEpoch`를 포함하여 명시적 Takeover를 요청하면, 서버는 observed epoch에 대한 CAS(Compare-And-Swap)로 원자적 인계를 수행하여 새 lease를 발급하고 이전 소유자를 `displaced` 상태로 전이시킨다. 그 사이 epoch가 변경되었으면 `STALE`을 반환하며, `displaced`된 클라이언트는 자동 탈환을 시도하지 않는다. 동일 클라이언트의 중복 시도는 이전 대기를 `SUPERSEDED`로 종료한다.

### rAF 없는 백그라운드 복구 및 Fallback Geometry

브라우저 탭이 백그라운드(`document.visibilityState === 'hidden'`)에 있거나 기하구조가 아직 계산되지 않은 cold-start 상태에서 재연결을 개시하더라도, `requestAnimationFrame`을 기다리지 않고 마지막 유효 크기 또는 80×24 Fallback Geometry로 즉시 v4 `HELLO`를 전송한다. 백로그 수신 후에도 rAF 2회 대기 없이 xterm의 `terminal.write()` 파서 콜백(`appliedPosition >= target`)만으로 리플레이 배리어를 해제하고 서버에 `REPLAY_APPLIED`를 전송하여 `READY_ACK`를 수신한다. 탭이 포그라운드로 복귀하면 실제 뷰포트 크기를 측정하여 `RESIZE_TERMINAL`로 정상 보정한다. 백그라운드 경과 시간은 60초 전면 자동 복구 예산을 소진시키지 않는다.

### 명시적 ACK/NACK 응답 및 Silent Deadlock 차단

클라이언트가 전송한 `REPLAY_APPLIED`의 `position`이 서버의 `replay_target`과 일치하고 epoch가 유효한 경우, 서버는 즉시 `READY_ACK`를 반환하고 양방향 키 입력을 활성화한다. 위치가 불일치하거나 손상된 페이로드, 이미 만료/종료된 세션인 경우 침묵 `break` 대신 원인에 맞는 `POSITION_MISMATCH` / `SYNC_REQUIRED` NACK를 반환하여 클라이언트가 대기 교착에 빠지지 않고 정직하게 저하(degraded) 상태 또는 재동기화 루틴으로 진입하도록 보장한다. 서버 측 ready deadline(유한 타이머)이 작동하여 응답 없는 클라이언트가 provisional owner 상태를 무기한 점유하지 못하게 차단한다.

### 종료 결과 보존과 새 세션의 완전한 에뮬레이터 분리

루트 프로세스가 종료된 `exited_retained` 세션에 접속한 경우, 최종 출력 리플레이가 파서에 적용되면 attempt를 읽기 전용 완료로 즉시 정착시키고 `READY_ACK` 대기로 남겨두지 않는다. 사용자가 "Start New Session"을 선택하면 진행 중인 대기를 즉시 선점(preemption)하고, 새 세션 승인 시 첫 출력이 적용되기 전에 이전 xterm 에뮬레이터의 버퍼, 모드, 커서 및 `isExitedRetained` 플래그를 완전히 초기화하여 새 셸에서 정상적으로 `SESSION_READY` 전송 및 양방향 키 입력이 가능하도록 보장한다. 반면 동일 세션의 정상 재개에서는 alternate screen 및 마우스 모드를 파괴하는 강제 리셋을 수행하지 않는다.

### 수동 복구 선점권 및 날조 입력 배제

재연결 시도, 토큰 조회, 지연 백오프 또는 리플레이 배리어 대기 중에 사용자가 화면의 Reconnect 또는 Start New Session 버튼, 툴바 Enter를 누르면, 이전 비동기 대기(`AbortController`/세대 취소)를 즉시 중단하고 최신 사용자 의도로 선점한다. 이전 시도의 지연된 콜백이나 소켓 닫힘이 새 연결의 상태를 훼손하지 않는다. 빠른 연속 탭, 화면 탭, 복구 버튼 클릭을 포함하여 복구 동작에 귀속되는 PTY 입력 바이트는 정확히 0 byte이며, 입력 차단 상태에서 누른 키는 버퍼링 후 자동 제출되지 않고 오직 입력 준비 완료 후 입력된 키만 정확히 1회 전달된다.
