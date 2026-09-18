# Scope: Output Buffer, Reaper, and Lifecycle Hardening

Schema: iis-scope/v1
Project-Root: /home/user01/project/webterm/ttyd-1.7.7
Status: done

## Product Authority

- /home/user01/project/webterm/ttyd-1.7.7/docs/planning/product-thesis/android-web-terminal/THESIS-002.md sha256:3ac3c25dd0e520e0af1269dd5de32b100400b86872e76ec2704d9d9b22a0e067

## Transition Authority

- /home/user01/project/webterm/ttyd-1.7.7/docs/planning/baseline/BASELINE-002.md sha256:285004a80d06ef8ac794513c10af08056d1ed94f992bbe7d2f2041523e9039f5

## Outcome

현재 코드는 8 MiB 버퍼가 가득 찼을 때 새 출력마다 8 MiB 전체를 복사하는 `memmove`를 반복하여 이벤트 루프를 지연시키고, 클라이언트의 송신 위치가 버퍼 시작점보다 뒤처질 경우(`send_position < output_start`) 이를 출력 없음으로 오판하여 도달 불가능한 `REPLAY_END`를 보내거나 출력을 영구 침묵 정지(Silent Freeze)시킨다. 또한 `session_reaper`에서 `uv_close` 완료 전 구조체를 free하고 콜백에서 내부 타이머 주소를 해제하는 interior pointer free 결함(P0-3), 전용 스레드의 `waitpid`와 reaper의 `waitpid(-1)` 경합, 그리고 `retained >= max_retained`로 방금 종료된 세션이나 뷰어가 붙은 세션을 즉시 해제하여 dangling pointer를 만드는 pruning UAF/off-by-one 결함(P0-4)이 존재한다.

이 Scope는 승인된 Transition Baseline `BASELINE-002`의 `BLOCK-005`를 하나의 `HARD_ATOMIC` 제품 경계로 구현하여 확립한다. 8 MiB 슬라이딩 `memmove` 버퍼를 실제 circular/chunk buffer 구조로 전면 교체하여 대량 출력 중에도 PTY 연속 drain을 보장하고, 송신 커서 추월 시 `BUFFER_OVERRUN`과 누락 구간을 명시적으로 알리는 `REPLAY_GAP`/`SYNC_REQUIRED` rebase 동기화를 구축한다. `session_reaper`의 프로세스 수거 권한을 단일화하고 libuv 타이머 비동기 수명 및 세션/프로세스/뷰어 비동기 참조 카운팅(refcount)을 완결하여 UAF 및 double free를 원천 차단한다. Retained 세션 pruning을 `retained > max_retained` 초과 조건으로 수정하고 뷰어가 연결된 세션 및 exit 처리 세션을 보호하며, write 실패 시 커서 전진 금지, fragmented 메시지 총량 제한, expiry 타이머 실패 추적을 확립한다.

포함 범위는 `THESIS-002`의 NB2, NB9, NB11, NB15, NB16, NB18, NB19 및 `BASELINE-002`의 R3, R5, R6, R7, R8, B5-E1~B5-E6, ST4, ST5, ST7, ST8, ST10, ST14, ST15, ST16이다. BLOCK-006의 실기기 종합 검증 및 실제 운영 포트 7683 cutover는 제외하되, B5의 버퍼/수명 교정 결과가 BLOCK-004의 v4 프로토콜과 완벽히 결합하여 동작하도록 격리된 실제 ttyd 인스턴스에서 검증한다.

## Acceptance

### 8 MiB 순환 청크 버퍼와 비차단 PTY 연속 드레인

격리된 실제 ttyd 서버와 PTY에서 10 MiB 이상의 대량 출력을 연속 발생시키는 동안, 서버는 8 MiB 전체 메모리 복사(`memmove`) 없이 유한한 circular/chunk buffer 구조로 PTY 출력을 비차단 연속 드레인하여 프로세스가 I/O 블록 없이 완주하도록 보장한다. 클라이언트가 단절되어 있거나 PAUSE 상태인 동안 출력이 8 MiB를 초과하더라도, 최신 8,388,608 bytes의 tail 출력이 온전히 보존되고 오래된 헤드만 유한하게 폐기된다.

### 커서 추월 시 명시적 GAP 및 Rebase 재동기화

클라이언트가 단절 또는 지연된 상태에서 버퍼 시작점(`output_start`)이 클라이언트의 `send_position`을 추월했을 때, 서버는 이를 정상 종료나 출력 없음으로 오인하지 않고 도달 불가능한 `REPLAY_END` 전송을 엄격히 차단한다. 대신 `BUFFER_OVERRUN`과 정확한 누락 바이트 범위를 포함한 `REPLAY_GAP` 또는 `SYNC_REQUIRED`를 전송하여 클라이언트가 손실을 인지하고 최신 보존 범위로 rebase하도록 합의한다. 클라이언트는 손실 사실을 고지하고 기본 입력을 차단하며, 사용자의 명시적 [불완전한 화면에서 계속] 선택 시 새 ACK 수신 후 입력을 재개한다. 누락된 바이트를 적용된 것으로 날조하지 않는다.

### 프로세스 Reap 권한 단일화 및 libuv 메모리 수명 완전 일치

프로세스 수거(reap)를 단일 경로로 일원화하여 `waitpid(-1)`가 root waiter의 결과를 가로채거나 ECHILD를 유효한 종료 상태로 오인하지 않도록 보장한다. `session_reaper`의 libuv 타이머는 `uv_close` 완료 콜백에서만 소유 parent 구조체 전체를 정확히 1회 해제하여 interior-pointer free를 근절한다. 세션 객체는 프로세스 exit callback, 비동기 libuv 핸들 닫힘, 연결된 뷰어 참조가 모두 종료될 때까지 refcount로 수명을 안전하게 유지하며, 프로세스 종료와 타이머 만료가 경합하더라도 UAF, double free, 거짓 PURGED가 발생하지 않는다.

### Retained 세션 Pruning의 엄밀한 상한 및 뷰어 연결 세션 보존

보존된 종료 세션(`EXITED_RETAINED`) 수가 설정치 N 이하인 경우 임의 삭제를 실행하지 않으며, 오직 `retained > max_retained` 초과 조건에서만 가장 오래된 자격 있는 세션을 pruning 대상으로 선정한다. 현재 process exit 처리 중인 세션이나 뷰어가 활성 연결된 retained 세션을 dangling pointer로 즉시 해제하는 것을 엄격히 금지하며, 만료 등으로 뷰어를 분리할 때도 명시적 통지 및 펜싱 후 참조가 끝난 뒤 안전하게 메모리를 해제한다.

### 전송 진실성 및 자원 한도 보호

WebSocket `lws_write` 실패 또는 부분 쓰기(short write) 발생 시 미전송된 바이트만큼 논리 송신 커서를 앞당기지 않고 실제 전송된 위치를 보존한다. 수신되는 fragmented 클라이언트 메시지는 누적 총량 한도를 두어 과도한 메모리 할당 시 명시적 거절을 반환하고, control frame(Ping/Pong) 처리 후 보류된 heartbeat reply나 state update가 이벤트 루프에서 영구 방치되지 않고 즉시 후속 스케줄링되도록 보장한다.

### 종료 수명주기 상태 진실성 및 자원 회수 완료

루트 프로세스 종료 시 최종 출력 드레인, exit code/signal 수집, 하위 프로세스 트리 회수를 정직하게 분리하여 추적한다. 단절 중 루트가 종료되어도 32,400초의 원래 유예 기한을 온전히 유지하며, 세션 회수 시 SIGHUP $\rightarrow$ 유한 대기 $\rightarrow$ SIGKILL을 거쳐 실제 프로세스 트리와 파일 디스크립터, 세션 참조가 모두 소멸한 것이 확인된 경우에만 `PURGED` 상태로 완결한다.
