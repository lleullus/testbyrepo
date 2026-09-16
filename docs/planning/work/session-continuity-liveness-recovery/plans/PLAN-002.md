# PLAN-002 — BLOCK-001 반단절 소유자 관찰과 제한된 인계

작성: 2026-09-15 / PlannerAstraR2 / GPT-6 Astra Low
상태: 독립 방법 검토 제출용. ADMIT·구현·Acceptance 판정·Coverage·Block Exit가 아니다.
Project Root: `/home/user01/project/webterm/ttyd-1.7.7`

## 1. 결속, 현재성, 변경 경계

다음 원본 전체를 직접 읽고 실제 바이트 SHA-256을 재계산했다. 상대 경로는 위 Project Root 기준이다.

| 원본 | 리비전 / SHA-256 |
|---|---|
| `docs/planning/product-thesis/android-web-terminal/THESIS-001.md` | CALIBRATED 2026-09-15 / `81003a0783df4f7876ad603aafd47c1b96ba768cec03237ed72e543ce9eb642a` |
| `docs/planning/baseline/BASELINE-001.md` | APPROVED r2-2026-09-15 / `f3b389347779f21b4e0fa1cad49ab748d509181763acb13cd39152416baf27e1` |
| `docs/planning/work/session-continuity-liveness-recovery/SCOPE.md` | iis-scope/v1, ready / `fae4c3cdc6cafa01a1898653b65f5a9805609ea2a147ca9e9285c903a12d4751` |
| `docs/planning/work/session-continuity-liveness-recovery/plans/PLAN-001.md` | 이전 방법 / `9e361221c35ca3d31b1b05e05dc6f3a32938edcddd0f337c517fc15eb88297bb` |
| `/home/user01/tmp/iis-implementation-results/webterm-block001-implement.md` | 현재 구현 보고 / `8cc577b84c5962243592b9381091c083e2ec558ea2311609f30cc1f4cf6f9182` |
| `/home/user01/tmp/iis-verification-results/webterm-block001-verification.md` | 이전 독립 검증 INCONCLUSIVE / `e49f853e7ce7c1e36b3c207c02de69ce9c93e10f4eccc112e894d231ca225130` |
| `/home/user01/tmp/iis-verification-results/webterm-block001-evidence/22-android-network-conflict.md` | 실기기 사용자 관찰 및 후보 서버 판독 / `af4ed8eabbe41a280ba0e9fd96e256a45fe75e43ee4de99590ad1266d1675254` |

`python3 /home/user01/project/iis-skills/scope-shaper/tools/validate_scope.py /home/user01/project/webterm/ttyd-1.7.7/docs/planning/work/session-continuity-liveness-recovery/SCOPE.md --json`은 종료 0, `iis-scope/v1`, `ready`, 위 Product/Transition의 정확한 path/hash를 반환했다. 구조적 유효성은 의미 승인이 아니다. 현재 HEAD는 `409879886810d18bf203fe5b8b36c782c867993d`, `git diff --binary HEAD` 해시는 `7f40b04305566664a323043d08acb721899e8ced3e72d5a238ef2f4f3261c409`이다. 현행 수정 작업 트리를 보존한다. 별도 repository-investigation 원본은 제공되지 않았다.

적용 권위: Scope Outcome/Acceptance 전부; Thesis NB1/NB5/NB6/NB10, I1/I4/I5/I6, SC-1/2/4; Baseline BLOCK-001 B1-E1~E6, G1~G3/G5/G8, P1~P7 및 Safe Abort/세션 복귀 HARD_ATOMIC. 기존 drain, 32,400초 grace, foreground resize, 정상 입력·툴바·화면 보존은 유지한다. PLAN-001 §3.2의 ‘active면 즉시 conflict, old close를 기다려 수동 재시도’ 방법을 이 문서로 교체한다. 그 밖의 이미 구현된 BLOCK-001 결과를 되돌리거나 다시 설계하지 않는다. PLAN-001과 그 옛 review는 역사이며 이번 변경을 승인하지 않는다.

이번 작성은 PLAN-002만 생성한다. 제품 소스·런타임·다른 프로젝트 파일·Scope·Thesis·Baseline은 변경하지 않는다. 계획 중 빌드/시험/제품 시나리오/포맷터/린터/브라우저/서비스 조작은 실행하지 않았다. 이 문서 이후에도 운영 7683, 운영 바이너리/번들/런처, 기존 OMP, 인증은 변경 대상이 아니다. BLOCK-002 Takeover UI와 BLOCK-003 tail/결과 보존/회수/운영 cutover는 제외한다.

## 2. EXISTING — 정확한 원인과 반증 경계

### 2.1 관찰된 실패와 원인

사용자는 실제 Android Chrome의 `/terminal-candidate?diagnostics=1`에서 Wi-Fi/이동망 전환 후 `Session is already active in another tab`이 반복되고 오래 재시도해도 복귀하지 못했다고 관찰했다. 이를 재현해서 사실 여부를 재확인하지 않는다. evidence 22의 서버 순서는 session 3 / connection 3 / PID 61570 정상 입력 → 20:00:03~09 신규 연결 반복 종료 → 20:00:31 `validity too old`로 old owner 분리 → 20:00:32 connection 8이 같은 PID에 attach이다. 다음 전환도 20:00:44~52 반복 종료, 20:01:15 old close, 20:01:26 attach였다.

현재 `src/protocol.c:897-914`는 살아 있는 process와 `session->client != NULL`을 실제 왕복 확인 없이 conflict로 판정한다. `prepare_unattached_response:524-533`는 close-after-state를 설정한다. client `xterm/index.ts:1017-1030`은 conflict를 명시 상태로 두고 recovery attempt를 stop한다. 새 연결의 재시도는 old server owner를 변경하지 않는다. `CLOSED:937-947`에서 old owner가 분리되어야 attach 조건 `563-565`가 열린다. 따라서 모바일에서 client의 old socket 폐기와 server의 old transport 종료가 불일치하는 동안 **registry 점유를 live 증거로 잘못 사용**한다. sessionStorage를 더 신뢰하는 것으로는 복제 탭과 구분할 수 없다.

`B1-ANDROID-OK`가 보이고 같은 session/PID로 다시 붙은 것은 세션/출력 연속성의 양성 증거다. 그러나 오래 막힌 구간, input-ready까지의 시간, 작업 재개 가능성을 지우지 않으며 prompt recovery의 증거가 아니다. PID 단독은 화면 복원도 증명하지 않는다.

경쟁 설명은 경로/토큰 실패 또는 실제 살아 있는 복제 owner이다. 이전 로그의 old validity 종료 직후 동일 session attach와 현재 분기는 stale-owner race를 지지한다. 다음 후보에서 실제 old connection의 식별 가능한 왕복이 성공하면 그 owner는 보호해야 하며, ‘동일 탭이니까 가져온다’고 해석하지 않는다. 성공적인 old 왕복 없이 proxy가 대신 응답하거나 관찰이 old connection에 귀속되지 않는다면 아래 방법 전제가 반증된다.

### 2.2 코드와 의존성 근거

| 현재 정의·읽기/쓰기 경로 | 방법상 의미 |
|---|---|
| `src/protocol.c:27-50,74-78,188,245-309` | session이 process/client/expiry/output을 소유한다. `uv_hrtime` 단조 시계와 server loop의 유한 uv_timer 정리 패턴이 있다. pending contender 상태는 현재 없다. |
| `src/server.c:594-599` | lws는 `server->loop`를 foreign loop로 사용한다. owner 판정·libuv timer·PTY callback을 같은 event loop에서 직렬화할 수 있다. |
| `src/protocol.c:704-763,797-860` | writable callback이 실제 송신점이다. input/resize는 input_ready와 session->client 일치를 요구한다. heartbeat/flow/ready는 PTY와 분리된다. |
| `src/protocol.c:415-469,509-582,929-959` | PTY drain, root exit/session release, attach의 grace 취소/resize/replay 준비, close의 detach/grace가 공유 수명 경계다. pending 참조를 이 모두에서 정리해야 한다. |
| `src/server.c:43-55,466-475` | 기존 transport ping와 추가 validity grace 30초가 별도다. 전역 값을 줄이지 않는다. |
| `xterm/index.ts:153-158,634-856,931-1055` | 60초 자동 window, token 10초, attempt 30초, heartbeat cadence 5초/timeout 30초, captured socket/generation, staged replay/ready가 이미 있다. heartbeat request는 visible/input-ready일 때만 JS에서 보낸다. |
| `app.tsx:8-54` | endpoint-scoped `webterm.session.v1:` 저장 및 explicit create/resume이 있다. 저장 namespace/값을 바꾸거나 ownership credential로 승격하지 않는다. |
| `terminal/index.tsx:208-217,246-251`, `xterm/index.ts:368-398,531-565` | pointer 및 toolbar recovery가 로컬로 귀속된다. checking 중에도 같은 입력 차단/gesture 소비를 유지한다. |
| `src/protocol.c:107-161,321-356,601-610`, `src/pty.c:195-229` | 유한 replay/정직한 overflow 한계, ordered state/replay-end, foreground resize는 보존 대상이다. |
| `staging/check_reconnect.py:44-199,486-505` | 현재 blackhole은 server binary heartbeat reply만 버린다. 이후 `disconnect()`가 upstream TCP까지 닫고 reconnect한다. 이것은 old owner를 남긴 새 연결 경쟁을 증명하지 못했다. |
| `staging/check_fresh_session.py:164-179` | 현재 duplicate는 old raw WS를 읽지 않은 채 conflict를 기다린다. native ping 사용 뒤엔 실제 owner receive/pong pump가 필요하다. 읽지 않는 fixture를 healthy owner로 표시하지 않는다. |

native API를 실제 build cache에서 확인했다. `build/CMakeCache.txt:286`의 Libwebsockets_DIR는 `/home/user01/.local/build-cache/stage/x86_64-linux-musl/lib/cmake/libwebsockets`이다. 대응 include의 `libwebsockets/lws-callbacks.h:424-425`는 server `LWS_CALLBACK_RECEIVE_PONG`, `lws-write.h:123-140`은 writable에서만 `LWS_WRITE_PING`과 LWS_PRE, `lws-timeout-timer.h:82-106`은 callback 밖 `LWS_TO_KILL_ASYNC` close를 제공한다. 이 확인은 API 존재/호출 계약이지 Android·Funnel의 실제 응답 증거가 아니다.

## 3. PROPOSED — 선택한 최소 교정

### 3.1 결정: 경쟁 시 한 번의 native WebSocket Ping/Pong

**서버가 현재 owner transport에 nonce를 넣은 WebSocket control Ping을 보내고, 같은 owner/generation의 정확히 일치하는 Pong을 유한 시간 관찰한다.** 정상 owner는 유지하고 contender만 conflict로 끝낸다. 관찰 실패로 old transport를 명시적으로 분리한 뒤에만 기존 attach 경로로 pending contender를 인계한다. 정상 active 경로에 상시 새 heartbeat나 탭 식별 credential을 추가하지 않는다.

애플리케이션 owner-challenge/ack를 선택하지 않는다. 현재 JS heartbeat는 hidden/input-ready gate와 browser scheduling의 영향을 받는다. 복제 탭을 여는 순간 background인 정상 original의 JS 응답 지연을 dead 판정으로 삼으면 보호를 약화한다. native control Pong은 browser transport가 처리하므로 이 불필요한 JS 의존을 피한다. 기존 application heartbeat는 client가 자신의 작업 통신 실패를 발견하는 용도로 그대로 유지한다. native Pong도 ‘사용자 의도’나 ‘셸 input-ready’를 증명하지 않으며 단지 해당 old transport의 현재 왕복을 증명한다.

전역 validity 단축, sessionStorage equality/nonce 선거, 모든 active owner의 강제 인계, Takeover UI, 입력으로 liveness 확인, 새 retry daemon/무한 queue는 금지한다. 관찰 timeout은 절대적인 tab 사망 증명이 아니라 정해진 기간 동안 old transport 왕복이 성립하지 않았다는 판정이다. 다른 탭이라도 old owner가 이 판정으로 분리된 뒤에는 기존 detached resume 규칙만 적용한다. 같은 탭이라는 특권은 만들지 않는다.

### 3.2 상태와 유한 시간

새 영속 session registry나 세션 자격은 만들지 않는다. session당 pending observation **최대 하나**만 추가한다. 필요한 상태는 session의 pending contender 포인터, old/new connection generation, nonce/check sequence, phase(queued/sent), deadline, uv_timer이며 contender에는 별도 pending-session 참조와 검증된 요청 rows/cols를 둔다. contender의 `pss->session`/`process`는 인계 전 NULL을 유지한다. nonce는 단일 server lifetime에서 재사용되지 않는 sequence와 old generation을 고정 길이로 인코딩하고 125-byte control payload 이하로 유지한다. secret/token/resume 원문은 넣지 않는다.

| 시간 | 출처와 의미 |
|---|---|
| Ping 송신 준비 한도 **2,000 ms** | 신규 authenticated create/resume가 occupied session에 도달한 시점부터 `uv_hrtime()/1000000` 기준. writable을 받지 못하거나 timer init/start 실패면 관찰 실패가 아니라 관찰 불능: old 보호, contender `error`, pending 정리. |
| Pong 관찰 한도 **10,000 ms** | old writable callback에서 Ping payload의 full-length write가 수락된 시점부터 단조 시계. 전송 API 성공은 전달 성공이 아니므로 정확한 Pong을 별도 기다린다. |
| client attempt/자동 복구 | 기존 30초 attempt와 60초 window를 연장하지 않는다. checking은 같은 attempt에 포함된다. token/attempt timeout은 남은 60초로 clamp하여 checking 때문에 최종 시도가 window를 넘기지 않게 한다. recovery clock은 `performance.now()`로 일관되게 사용한다. |
| 기존 heartbeat/transport/grace | client 5초/30초, server transport 정책과 32,400초 session grace는 그대로다. |

10초는 경쟁이 실제 발생한 transport만 관찰하는 국소 한도이며 mobile 지연과 30초 attempt 안의 replay 여유를 함께 둔 방법 매개변수다. 실기기에서 정상 owner가 이 기간에 응답하지 못하거나 stale 회복이 여전히 validity에 묶이면 통과로 바꾸지 않고 §6으로 방법 재진입한다. timer는 wall-clock 보장이 아니므로 event-loop stall의 실제 지연을 기록한다. callback에서 단조 deadline을 재검사하고 아직 이르면 남은 기간으로 재예약한다. timeout을 실행했는데도 owner reply를 기다리는 무한 연장은 없다.

### 3.3 사건 순서와 단일 소유권

1. 기존 authentication/intent/ID/process-running/tombstone 판정을 통과한 occupied session만 관찰한다. 기존 detached attach/explicit spawn/error 분기는 그대로다. 첫 contender를 pending으로 등록하고 `checking` state(`accepted=false`, `inputReady=false`, 올바른 diagnostic ID)를 보낸다. 이 때 old owner의 input-ready, input/resize, flow, replay, grace는 바꾸지 않는다. 다른 contender는 queue에 쌓거나 기존 deadline을 재시작하지 않고 기존 `error` 응답으로 종료한다. 미관찰 owner를 live라고 단정한 conflict는 보내지 않는다.
2. old writable에서 close-status 처리 뒤, output/flow pause와 독립적으로 Ping을 우선 한 번 보낸다. 아직 initial messages를 보내는 owner도 관찰을 막지 않는다. 고정 stack `LWS_PRE + payload` buffer를 사용한다. short/failed write는 성공한 probe로 세지 않는다. old transport의 실제 close 경로로 넘기며, close가 관찰되기 전 contender를 attach하지 않는다. 송신 준비 timer는 여기서 종료하고 10초 observation deadline으로 전환한다.
3. `LWS_CALLBACK_RECEIVE_PONG`: pending이 sent이고 수신 pss가 여전히 old owner이며 generation/nonce/길이가 모두 맞고 `now < deadline`일 때만 live로 판정한다. timer/pending 참조를 먼저 해제하고 contender에 최종 conflict를 보낸다. 일반 lws validity Pong, 과거 nonce, contender의 Pong, application heartbeat/일반 입력은 이 challenge의 성공을 대체하지 않는다. 기존 lws validity 처리는 유지한다.
4. `now >= deadline`에는 동일 session/old owner/old generation/pending contender가 여전히 유효한지 검사한다. session process가 종료되었다면 exited 경로이고 attach/spawn은 없다. 유효하면 **먼저** old `input_ready=false`, session->client=NULL, old pss의 session/process/pending 관련 참조를 끊는다. 이 event-loop 순간이 server-observed detach이다. old wsi는 `lws_set_timeout(..., PENDING_TIMEOUT_CLOSE_SEND, LWS_TO_KILL_ASYNC)`로 종료 요청하되 FIN/Pong/전역 validity를 기다려 소유권 분리를 지연시키지 않는다. 이어 살아 있는 pending contender를 같은 process에 기존 `attach_process`로 붙인다. spawn, buffer reset, 입력 재전송은 없다. old close callback은 이제 session을 소유하지 않으므로 새 owner를 detach하거나 grace를 시작하지 못한다.
5. 실제 old CLOSED가 관찰 도중 먼저 오면 그 자체가 분리 근거다. old 참조와 check timer를 제거하고 유효 pending을 기존 attach에 넘긴다. pending도 이미 닫혔거나 attach가 실패하면 기존 detached grace를 분리 시점부터 한 번 시작한다. 인계 성공 중간에 재시도 때문의 grace 연장은 만들지 않는다. expiry가 이미 확정되거나 root가 먼저 끝났으면 그 사실을 뒤집지 않는다.
6. contender가 먼저 CLOSED/attempt cancellation되면 check를 취소하고 pending 역참조를 제거한다. old owner를 죽이거나 expiry를 만들지 않는다. 이미 송신된 Pong의 후속 도착은 무시한다. session release/root exit에서도 timer stop→timer data NULL→uv_close free-callback, 양쪽 역참조 제거를 먼저 수행한다. uv close callback은 해제된 session/pss를 읽지 않고 timer 저장소만 free한다. server shutdown도 이 lifetime을 정리한다.
7. timeout과 Pong/close가 같은 loop turn에 경합하면 처리 시점의 deadline 규칙과 현재 owner/generation 검사로 한 번만 terminal decision을 수행한다. deadline 이후 Pong은 늦었으므로 판정을 되돌리지 않는다. old data/ready/resize/flow/close는 owner interlock에서 차단된다. old에서 **분리 전에 실제 접수된** 입력은 이미 발생한 효과이며 취소/재전송하지 않는다. 새 owner가 다시 분리되면 기존 grace 규칙만 따른다.

## 4. wire·client·파일 cutover

`checking`은 성공도 conflict도 아니다. client는 ‘Checking previous connection…’ 수준의 사실적 표시와 input gate를 유지하고 현재 attempt를 기다린다. `checking`에서 recovery pointer/Enter는 기존 로컬 소비를 유지하되 진행 중 attempt에 합류한다. 클릭마다 window/deadline을 새로 시작하지 않는다. checking의 transport close는 retry 경로여야 하므로 `session-*` stop prefix와 혼동하지 않는 `checking-owner` client state를 쓴다. confirmed conflict만 기존 안내/stop을 사용하며 visibility가 확인된 conflict의 자동 재획득을 시작하지 않게 한다. 수동 Retry는 새로운 관찰을 요청할 수 있으나 live owner를 강제로 가져오지 않는다.

현재 initial writable과 state_update_pending을 그대로 재사용한다. checking이 initial sequence 중 terminal decision으로 바뀌면 최종 state를 initial state slot에서 한 번 보내고, 이미 initialized이면 state_update_pending으로 보낸다. 최종 unattached conflict/error는 **그 state가 실제 송신된 후** close해야 한다. 현재 close_after_state가 initial 경로에만 적용되는 점을 이 전이에 맞게 수정한다. attach 성공 시에는 `attached` state가 output/replay-end보다 먼저 나가고 기존 replay/SESSION_READY/input-ready 순서를 유지한다. checking 중에는 replay-end를 보내지 않는다.

추가 state를 이해하지 않는 bundle이 애매하게 동작하지 않도록 session wire version은 **2로 clean cutover**한다. server constant, client handshake/state/replay-end reader, 모든 raw staging caller를 함께 바꾸고 v1/legacy는 error로 명시 거절한다. storage schema/version과 `webterm.session.v1:` namespace는 wire version과 별개이므로 바꾸지 않는다. 외부/내장 bundle 호환을 추정하지 않고 후보에서는 명시 `-I html/dist/inline.html`만 사용한다.

정확한 변경 대상:
- `src/server.h`: pss pending 참조/보관 geometry/check 송신 상태에 필요한 최소 fields. 별도 application challenge opcode는 추가하지 않는다.
- `src/protocol.c`: version, occupied 판정, session-local timer/nonce, writable Ping, RECEIVE_PONG, pending→final state ordering, attach/close/exit/release 정리. 기존 input/resize/flow/ready owner guards와 출력/PTY 함수를 재사용한다.
- `html/src/components/terminal/xterm/index.ts`: wire version 2, checking state, join/stop 처리, 남은 60초 timeout clamp 및 monotonic recovery timing. 기존 replay/gesture 경계는 유지한다.
- `staging/check_fresh_session.py`: 실제 owner receive/Pong pump와 양 connection 동시 관찰, v2/checking→final 읽기, live duplicate·stale race. 예전처럼 owner를 읽지 않고 healthy로 간주하지 않는다.
- `staging/check_reconnect.py`: old upstream을 살려 둔 connection별 fault mode, 새 연결 정상 통과, timing/PTY/화면 evidence; 기존 blanket disconnect를 새 race 증거에 사용하지 않는다.
- `staging/check_protocol_edges.py`, `staging/check_omp_reconnect.py`, `staging/check_exit_lifecycle.py`, `staging/check_server_hardening.py`: wire version/중간 상태 소비만 필요한 만큼 이동하며 기존 행위 assertions는 보존한다.
- `CUSTOMIZATION.md`: 성공한 구현 smoke 뒤 bounded owner observation, 진짜 live conflict, 호환 v2 후보와 운영 무변경 한계를 국소 갱신한다.

`src/server.c`, `src/pty.c`, `app.tsx`, `terminal/index.tsx`, overlay/style은 원칙적으로 무변경이다. 별도 timer framework, telemetry subsystem, takeover mode, storage migration, replay redesign는 없다. 현재 diagnostics에 check queued/sent/live/timeout/cancel/detach 및 old/new diagnostic generation/deadline만 필요한 만큼 추가한다. credential/원시 resume/실제 사용자 입력은 기록하지 않는다.

## 5. 구현자 self-check 및 독립 검증으로 넘길 실제 판독

새 검증은 하나의 안정된 source/diff/binary/served-inline manifest에 묶는다. 과거 PASS를 새 wire/소유권의 PASS로 합산하지 않는다. 구현자는 독립 Review 후 허용된 후보에서 아래를 실행하고 Main이 통합 formatter/lint/build를 한 번 소유한다. 계획 단계에서는 실행하지 않는다.

### 5.1 먼저 필요한 국소 race 증거

실제 candidate ttyd/PTY, 실제 browser/WebSocket를 쓰고 proxy는 네트워크만 조절한다. 모의 SET_SESSION_STATE, 수동 inputReady 주입, 가짜 Pong, 미리 심은 성공 로그는 금지한다. proxy의 정확한 대상은 **old connection pair만**이다. old TCP/upstream을 닫지 않고 old data/control/close 전달을 양방향 차단하되 새 HTTP/token/WS pair는 정상 통과시킨다. browser의 old socket close가 upstream close로 전파되지 않았다는 readback과 candidate가 old owner를 유지한 상태에서 새 handshake가 도착했다는 timeline이 필수다. native Ping/Pong은 제어 프레임 opcode/nonce equality로 관찰하며 앱 heartbeat reply와 혼동하지 않는다.

- **live original + duplicate:** 실제 Chrome old tab을 visible/hidden 각각 두고 copied session의 두 번째 연결을 연다. old native Ping/Pong이 정확히 왕복하고 contender는 checking→conflict, old session/generation/PID/starttime 불변. contender 입력/resize delta 0, old의 새 fixture 입력/실제 PTY geometry 변경만 적용. 복제 탭 열기로 original이 background가 되는 사례를 포함한다.
- **same-tab half-open:** old pair를 유지·blackhole한 뒤 client의 실제 liveness/재연결 경로로 새 pair를 연다. 새 handshake→queued→sent→10초 실패→old detach→같은 session attach→replay/parser/render→input-ready를 읽는다. local scheduling 여유 1초를 별도 기록하여 check 시작부터 detach는 13초 이내, 그 후 상한 이내 소량 fixture input-ready는 5초 이내를 관찰 목표로 둔다. 이는 영구 제품 SLA가 아니라 선택한 2초+10초 방법의 discriminating check다. old validity timeout 또는 proxy 강제 upstream close가 먼저 race를 해소했다면 이 사례는 증거 불충분이다.
- **Pong/late/cleanup races:** 실제 browser가 생성한 Pong을 proxy가 deadline 직전/직후에 전달한다. 전자는 old 보호, 후자는 이미 분리된 old를 부활시키지 않아야 한다. 무관 nonce와 이전 check의 실제 지연 Pong, old close/data/resize/ready가 새 attach 뒤 도착하는 경우 새 owner/input-ready/grace 불변을 읽는다. close 이전/이후를 실제 socket 경로에서 만들며 source callback 직접 호출로 대체하지 않는다.
- **취소/종료:** pending contender close, old close, root exit, 송신 준비가 불가능한 old transport, concurrent third contender를 각각 실제 후보로 관찰한다. 취소는 old 유지, old close는 정상 인계, root exit는 exited/no-spawn, 미송신은 error/old 유지, third contender는 pending 교체/무한 queue/deadline 연장 없음. pending count 및 timer/FD와 실제 잔여 프로세스를 함께 읽는다.
- **입력 경계:** raw PTY capture를 시작하고 baseline bytes를 먼저 읽는다. checking/재연결 gesture 전체 수신 delta 0, input-ready 뒤 별도 새 payload만 1회. 분리 전 받은 입력과 불명 입력을 재전송하지 않는다. probe/Pong은 절대로 INPUT framing을 쓰지 않는다.

### 5.2 Scope Acceptance와 B1-E 전체 매핑

| Acceptance / Baseline | 현재 harness 및 필수 새 판독 |
|---|---|
| 동일 탭 복귀/명시 신규 — B1-E1, SC-1 | `check_fresh_session.py`, `check_reconnect.py`, `check_omp_reconnect.py`: reload·저장 유지 복원·새 독립 explicit create·storage 차단/소실을 보존. diagnostic session + PID/starttime + 추가 spawn 0 + 이미 보인 marker 및 실제 shell/OMP 화면. 이번 stale handoff에도 같은 조합을 요구한다. |
| 상태 진실성/소유 보호 — B1-E2 | §5.1 live/stale/late/cancel/third contender + fresh harness의 expired/exited/unknown/v1 rejection/create 응답 유실 중복 spawn 방지. checking을 confirmed live conflict로 표시하지 않으며 입력/resize 단일 귀속을 PTY와 geometry에서 확인한다. |
| 화면 복귀/반단절 — B1-E3, SC-4 | reconnect harness의 기존 selective application-heartbeat failure와 20회 복구를 유지하고 새 old-pair-only race를 별도로 실행. 실제 Android 120초 lock/unlock, 앱 전환, Wi-Fi→mobile와 mobile→Wi-Fi 각각을 temporary route에서 관찰한다. 정상 alive socket은 새 generation 0, dead만 교체. |
| 날조 없는 수동 복구 — B1-E4, SC-2 | reconnect manual overlay/toolbar와 retry-open-close: 실제 60초 소진, 빠른 두 탭, pointerdown 뒤 completion, overlay 제거 뒤 click, visibility 복귀와 동시 gesture 모두 PTY delta 0 및 이후 새 입력 정확히 1회. checking 중 rapid gesture가 새 socket/timer/window를 만들지 않는 사례 추가. 과거 visibility+gesture driver 한계는 여전히 독립 관찰 필요다. |
| 복원 진실성/보존 — B1-E5 | protocol edges/OMP/reconnect/server hardening/exit lifecycle: OPEN→checking→attached→replay→render→input-ready 분리, 상한 내 화면/normal·alternate 보존, 불명 입력 재전송 0, no reset/Enter/ESC/Ctrl+L, drain·foreground resize·default 32,400초와 분리/재분리 의미, 일반 toolbar/terminal 입력. overflow·EXITED_RETAINED 미완성을 숨기지 않는다. |
| 통합/출구 — B1-E6 | 같은 v2 target의 manifest/서빙 문서 hash/instance/generation/spawn/PTY readback, 동일 fixture 20회 stale/live 반복 후 pending/timer/socket/FD 비누적, 완전 dispose 뒤 자기 소유 효과 소멸. production 7683 PID/starttime/artifact/route 불변. 실기기·외부 미관찰이면 Exit 불가. |

이전 verification의 01/02/03/06/07/08/11/12/13/15/16/18/19 증거는 보존할 행동의 navigation이다. 이번 변경 뒤 같은 의미를 다시 관찰한다. 특히 03의 heartbeat-only filter는 새 stale-server-owner race를 대신하지 않는다. 20의 CDP lifecycle 실패는 제품 pass가 아니며 실제 동시 visibility+gesture를 가능한 실제 브라우저 조작으로 확보해야 한다. 실패 시 gap을 남긴다.

### 5.3 실제 Android와 외부 효과 경계

Main/운영자가 현재 권한과 대상/rollback을 확인한 뒤에만 이전에 제거한 `/terminal-candidate` 임시 handler를 **새 후보 전용 비운영 포트**로 다시 준비한다. prior authority는 계획 작성자가 지금 Funnel을 변경할 권한이 아니다. Main이 handler의 정확한 pre-state, 대상 binary/inline/base path, 실제 candidate listener PID/starttime과 폐기 가능한 fixture만 기록한다. `/terminal`, `/terminal/token`, `/terminal/ws` 운영 handler/7683은 수정하거나 시험 입력하지 않는다. 후보에서는 대응 `/terminal-candidate`, `/terminal-candidate/token`, `/terminal-candidate/ws`의 실제 정적 응답 및 양방향 WS를 따로 확인한다. localhost 성공은 외부 path 성공이 아니다.

사용자가 실제 Android Chrome에서 marker가 있는 동일 탭을 유지한 채 Wi-Fi↔mobile을 각각 수행한다. 전환 시각, 새 연결 시작, check send/Pong 또는 deadline, old detach, attach, input-ready, 실제 화면/새 안전한 입력 결과까지 연결해서 기록한다. old session/generation/PID/starttime과 새 generation, raw resume 대신 equality를 남긴다. 양 방향 최소 3회씩 및 정상 live duplicate 사례를 같은 후보에서 관찰하여 ‘오래 기다리면 marker가 보임’이 아니라 **validity 대기 없는 유한 복구와 실제 입력 재개**를 확인한다. 네트워크 자체가 복구되지 않은 시간과 새 route가 도달한 후 owner-check 시간을 분리한다. 오래 막힘을 retry 클릭으로 숨기지 않는다.

시험 전 prod 7683 PID 202/starttime와 운영 binary/index/session.sh hash, 실제 route 설정을 읽기 범위에서 기준화한다. prior evidence의 PID 202는 이번 시점의 새 readback 대신 쓰지 않는다. 종료/실패 시 Main은 자신이 추가한 candidate handler만 제거하고 정확한 설정 차이가 사라졌음을 읽는다. browser auto recovery/입력을 중단→candidate browser/proxy 종료→소유한 disposable PTY/root/자식 종료·reap→candidate ttyd 종료→candidate listener/소켓/타이머/프로세스 부재→운영 listener/identity/hash/route 불변을 읽는다. 전체 Funnel reset, 전역 kill, 기존 OMP 종료는 금지한다. forkpty 자식은 parent kill 반환만으로 정리되었다고 하지 않는다. 확인된 시험 소유분에만 TERM 후 5초, 잔여 KILL 후 5초 관찰을 적용하며 소유 불명/잔여는 Main에 반환한다. marker/비민감 evidence는 보존하되 임시 profile/fixture 파일만 정리한다. 이미 전달된 입력의 효과를 자동 취소·재실행하지 않는다.

## 6. UNRESOLVED — 방법 선택이 아닌 실제 경계 검증 조건

### 6.1 native observation의 실제 귀속

- `plan_anchor`: PLAN-002 §3.1~3.3, §5.1.
- `permitted_initial_work`: 새로운 독립 Review 뒤 구현자가 위 최소 Ping/Pong/pending 방법을 격리 후보에 연결하고 실제 Chrome + connection별 proxy의 live/half-open 첫 사례를 실행한다. API 존재는 이미 확인했으므로 다른 방법을 조사하는 사전 단계로 늘리지 않는다.
- `discriminating_observation`: old connection의 exact nonce Pong이 healthy visible/hidden Chrome에서 왕복하고, old pair 차단 시 새 pair는 성공하나 해당 Pong은 없어 timeout 분리 후 같은 PID/화면/input-ready로 돌아오는가. failed send와 sent-but-no-Pong이 구분되는가. late callback/close가 새 owner를 건드리지 않는가.
- `dependent_work_not_yet_permitted`: 이 귀속이 반증되거나 관찰되지 않은 상태에서 외부 candidate 노출, 전역 timeout 단축, JS ack/secret takeover로 임의 대체, Android pass/Exit 선언.
- `response_if_refuted`: affected ownership 구현/노출을 멈추고 증거를 보존해 Main→Planner→새 독립 Review로 반환한다. 제품 소유권 의미를 바꿔야 하면 Scope/Thesis owner로 반환한다. unrelated v2 caller migration은 별도 파일 경계에서 안전한 경우만 계속한다.

### 6.2 실제 기기/route와 정상 링크 보호

- `plan_anchor`: PLAN-002 §5.3.
- `permitted_initial_work`: Main이 현재 Android/Chrome·임시 route 권한과 cleanup 소유자를 확인하고 §6.1이 지지된 같은 candidate bytes만 제공한다. verifier/운영자는 실기기 정상 duplicate와 Wi-Fi 양방향 전환의 실제 readback을 얻는다.
- `discriminating_observation`: 임시 외부 route가 그 후보를 서빙하고 old owner의 native control 왕복을 중간 프록시가 대신 생성하지 않으며, 실제 정상 owner는 보호되고 stale만 유한 인계되는가. UI와 PID/PTY/시간 증거가 같은 session에 귀속되는가.
- `dependent_work_not_yet_permitted`: 미확인 정상 링크를 timeout으로 탈취해도 성공으로 취급, localhost/desktop으로 Android 대체, 운영 7683/인증 변경, Block Exit/Coverage/다음 Block 진행.
- `response_if_refuted`: 실제 실패는 방법 재진입, 환경/권한 부재는 PARTIAL 또는 BLOCKED와 정확한 gap으로 Main에 반환한다. 기기·경로 제공 권한은 Main/운영자 소유이며 Planner가 만들어내지 않는다.

현재 남은 것은 이 새 방법의 런타임·외부·실기기 증거이지 미결정된 구현 대안이 아니다. timer/nonce 소유, state ordering, timeout 값, 늦은 사건 처리와 검증 경로는 위와 같이 선택했다. helper 이름과 동등한 국소 배치는 구현 재량이지만 native→application 관찰 변경, 시간/권한/상태 의미 변경, 새 persistence/replay 방식, 실제 readback 대체는 material method change로 새 계획/독립 검토가 필요하다.

## 7. 현재 source/artifact 바이트 manifest 및 인계

아래는 계획 시 실제 재계산값이다. 행 번호는 §2의 현재 바이트에 대한 navigation이다. binary/hash 일치는 후보가 지금 실행 중이라는 뜻이 아니다. containment는 evidence 22와 사용자 제공 사실이며 이번 계획에서 서비스를 재기동하거나 재확인하지 않았다.

| 경로 | SHA-256 |
|---|---|
| `src/server.h` | `0b5b948aca0e36b8c73fd167ba6bdb126c68e0b8b5b76b3c25d3c193ff3e9cc7` |
| `src/protocol.c` | `3c3f587b5b10f237c51e13213ac350a3bfaaf9c5e1e26f27087522d694b55c91` |
| `src/server.c` | `e4beac7c4dd2037600323585c991ffc5d3a0acb535facbff55a0f996677ae313` |
| `src/pty.c` | `c3591d3282a5d5746f3247d3cbef0911040331c6df945022292f703ce714bd9c` |
| `html/src/components/app.tsx` | `aac3f4c91c1f44dea7bb92d2e6bc1e73babbfe5add6101324af499470ce99eb6` |
| `html/src/components/terminal/index.tsx` | `6475191099b7ab967544229db4570a9da7b7d684ffa43776cd645b9e0b6f71c9` |
| `html/src/components/terminal/xterm/index.ts` | `0ab8de7cb6f96b8fcc80580ca92e1093e8cece1657159ce43ad248738e784d39` |
| `html/src/components/terminal/xterm/addons/overlay.ts` | `a32cf1e90e5f458d152e0a8780694104eda9fabd8ad348d664300023366e7c16` |
| `staging/check_fresh_session.py` | `a3cf731f2c3a1d2fe6ab9ab0c2a5106e420b1949e463a937ed155b128c33319b` |
| `staging/check_reconnect.py` | `3f399f240552c6eae2bfeecbbfa0c465adccf5630d9caa0fe79455a69f143f6b` |
| `staging/check_protocol_edges.py` | `11706b8dcf910d3377a57084307a91f0b83fd3d2ab47f53ca15db29d29f621e2` |
| `staging/check_omp_reconnect.py` | `6d0c44d1a544ff06adfc3fd3c02be5bf8f59495abf4a433c71b1133318f0bf3f` |
| `staging/check_exit_lifecycle.py` | `6b6a08715c3a813c521f3f35288b4c71fa352ab60b021e21401765768f974b21` |
| `staging/check_server_hardening.py` | `3475e7305db5457473e4f4083f32317d93acc958d8f5f002862047522c91bc95` |
| `CUSTOMIZATION.md` | `e445b766a7496c1d95de8528b7401dc630533193690f7fad181f8e965d805fd3` |
| `build/ttyd` | `9ea5a776a8e4eaed675656aa9e61e288e8a361859dfb9fa05d2a58bac6b2db5b` |
| `html/dist/inline.html` | `e0230956dc1f88032d335798d08aadf67b7bea7cd5883c25662f55007e28f2c1` |
| `build/CMakeCache.txt` | `b80c897648d31364bbd9bba77226440b6cb824f67c2b47004360303fabb68205` |

API 근거 루트 `/home/user01/.local/build-cache/stage/x86_64-linux-musl/include/libwebsockets/`:
- `lws-callbacks.h`: `10f9dad2eda7f8a6d466c17947c41ffa8e5dbbe16f9f4fd398cfd379b3a8e6f5`
- `lws-write.h`: `4b0855605e657f625777a39f3365440dbac15c9f255ff76bba8372423723cbb3`
- `lws-timeout-timer.h`: `43202842ba449f5f1e08f33eae141e399a747760eec8d2f22f42ade48cbcc372`

구현자는 최종 v2 diff/binary/served bundle/시험 명령과 case별 실제 evidence hash, old/new session·generation·PID/starttime, spawn/PTY delta, nonce 왕복의 귀속과 단조 timing, 화면/input-ready, cleanup/운영 무변경, 미관찰 항목을 인계한다. Main은 이 PLAN-002의 새 독립 Gemini review 이후 Sol High 구현→Luna Max 의미 검증→별도 Coverage 순서를 소유한다. 필수 실제 관찰이나 효과 정리가 남으면 다음 Block으로 진행하지 않는다. 본 문서는 그 판정들을 선취하지 않는다.
