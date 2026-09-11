# PTY Continuous Drain Invariants

Status: approved
Owner: user01
Scope: non-blocking PTY read and flow control decoupling invariants

## Research

- `src/protocol.c` & `src/pty.c`: libuv PTY stream에서 `uv_read_stop()`을 정상 데이터 경로에서 호출하지 않음으로써 PTY read를 상시 가동함.
- `CUSTOMIZATION.md`: 모바일 터미널 환경에서 브라우저 전송 지연이 호스트 빌드/테스트 프로세스를 차단해서는 안 됨.

## Behavior Model

### Causal Invariants
1. **[PTY 상시 배출(Continuous Drain) 불변성]**:
   - 클라이언트의 WebSocket 전송 속도, 모바일 슬립, LWS 전송 버퍼 지연, `PAUSE` 수신 여부와 완전히 무관하게, 호스트의 자식 프로세스 PTY 출력은 항상 끊임없이 읽혀 세션의 8MB bounded output queue로 흡수된다.
   - PTY read를 임의로 `uv_read_stop()`하는 것은 허용되지 않는다.
2. **[PAUSE의 단일 의미 불변성]**:
   - 프론트엔드가 전송하는 `Command.PAUSE`는 "해당 클라이언트로의 WebSocket 패킷 발송만 일시 보류"하는 단일 게이트 역할만 수행하며, 서버 PTY 프로세스의 read를 중단시키지 않는다.
3. **[버퍼 한도 초과 시 처리 불변성]**:
   - 세션 큐가 8MB를 초과하면 기존 버퍼는 즉시 폐기되고 `needs_redraw = true`로 설정된다.
   - 이후 발생하는 PTY 출력은 계속 drain되되 클라이언트 소비가 재개될 때까지 폐기(discard)되어 호스트 작업의 진행을 절대 막지 않는다.
4. **[진단 루프 격리 불변성]**:
   - `?diagnostics=1` URL 쿼리가 없는 일반 운영 환경에서는 `requestAnimationFrame` 모니터링 루프가 동작하지 않아 모바일 배터리를 낭비하지 않는다.

## Counterexample Stress Test

- **경계 조건 1: 대량 출력(100MB 빌드 로그) 중 모바일 화면 끔**
  - 해결: 8MB까지는 큐에 보관되고, 이후 초과분은 즉시 폐기되며 PTY read가 계속 돌아 빌드 프로세스는 stdout 블로킹 없이 100% 정상 종료됨. 재접속 시 최신 화면이 foreground SIGWINCH로 재동기화됨.
- **경계 조건 2: PAUSE 수신 후 클라이언트가 복귀하지 않고 영구 단절**
  - 해결: PTY는 정상 작업 종료 시까지 계속 drain되며, 단절 9시간 경과 시 유예 타이머에 의해 정상 회수됨.

## Product Decision Return

None

## Conclusion

브라우저 및 네트워크 상태는 결코 호스트의 실행 흐름을 지연시키거나 정지시킬 수 없으며, 터미널 세션은 항상 자식 프로세스의 무단절 실행을 최우선으로 보장한다.
