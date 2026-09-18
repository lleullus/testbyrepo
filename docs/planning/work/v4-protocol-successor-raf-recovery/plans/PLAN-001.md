# PLAN-001 — BLOCK-004 v4 프로토콜·Successor Token 인계·rAF 제거 복구 코어 실행 방법

- Project Root: `/home/user01/project/webterm/ttyd-1.7.7` (이하 경로는 이 루트 기준).
- 대상 Scope: `docs/planning/work/v4-protocol-successor-raf-recovery/SCOPE.md`, SHA-256 `2ec4035a53d2d0384954aae78d82b97823a41256fb39fd8329a4ce0eafd3f276`, `Schema: iis-scope/v1`, `Status: ready`.
- Product Authority: `docs/planning/product-thesis/android-web-terminal/THESIS-002.md`, SHA-256 `3ac3c25dd0e520e0af1269dd5de32b100400b86872e76ec2704d9d9b22a0e067`.
- Transition Authority: `docs/planning/baseline/BASELINE-002.md`, SHA-256 `285004a80d06ef8ac794513c10af08056d1ed94f992bbe7d2f2041523e9039f5`; 이 Plan은 그 원본 중 Scope가 선택한 `BLOCK-004`와 B4-E1~B4-E6만 적용한다. Baseline의 `DRAFT` 표기나 해시는 그 자체로 실행·배포 승인이 아니다.
- 조사 원본: `/tmp/oracle-findings-and-investigation.md`, SHA-256 `d09035efe52fe103720832295e1ae5065096e953748c7e33029e8106540d68bd`.
- 작성 상태: 독립 Plan Review 대기. 이 문서는 구현 방법이며 ADMIT, 구현 완료, 검증 성공 또는 운영 배포 판정이 아니다.
- 권한 한계: 이 단계에서는 본 Plan만 작성한다. 제품 소스, 빌드 산출물, 격리/운영 프로세스, 포트 7683, Funnel, 사용자 storage를 변경하지 않는다.

## 1. 결속 결과, 증거 경계, 완료 의미

정확한 Scope는 canonical validator `/home/user01/project/iis-skills/scope-shaper/tools/validate_scope.py --json <absolute SCOPE.md>`에서 `status: ready`, 위 Thesis/Transition Authority 경로와 해시 일치로 `VALID` 판독되었다. 해시는 현재 바이트 식별일 뿐 제품 동작이나 전환 승인을 증명하지 않는다.

BLOCK-004의 구현 결과는 서버와 클라이언트가 함께 v4로 전환된 한 후보에서 다음을 동시에 만족하는 것이다.

1. 유효한 동일-client successor는 죽은 이전 소켓의 writable/Ping/Pong을 기다리지 않고 같은 PTY에 즉시 귀속되며 새 소유권만 입력·resize·heartbeat를 수행한다.
2. 다른 client는 자동 탈취하지 못하고 즉시 명시적 경합 결과를 받으며, 사용자가 본 `leaseEpoch`에 대한 CAS Takeover만 소유권을 바꾼다.
3. geometry와 replay 완료는 paint/rAF/16 ms polling 없이 진행하고, xterm parser callback과 서버 `READY_ACK`가 입력 gate를 연다.
4. invalid replay 적용, old epoch, 잘못된 phase는 침묵하지 않고 NACK/종결 상태로 유한 정착한다.
5. `EXITED_RETAINED`는 읽기 전용 replay 완료로 끝나며, 새 PTY가 승인된 뒤 첫 출력 전에 이전 emulator 상태를 분리한다.
6. 수동 Reconnect/Start New Session은 fetch, backoff, parser barrier, takeover를 실제로 abort하며 복구 동작은 PTY에 0 byte를 보낸다.

검증은 실제 격리 ttyd 바이너리, 실제 WebSocket, 실제 PTY child, 실제 서빙 bundle과 실제 xterm parser callback을 통과해야 한다. ACK mock, seeded ready flag, 가짜 PTY readback, source 문자열 검사, HTTP 200, WebSocket OPEN, client local boolean만으로 B4 Exit를 판정하지 않는다. 네트워크 proxy는 FIN/RST 누락·응답 drop·frame 관찰을 만드는 보조 fault injector일 뿐 서버/브라우저/PTY 경계를 대체하지 않는다. Chromium lifecycle 제어도 hidden/frozen 조건을 만드는 fault injection이며, 실제 parser와 실제 wire readback을 그대로 사용한다.

## 2. Scope 경계와 보존 조건

### 2.1 포함

- THESIS-002 NB1, NB3, NB5, NB6, NB9~NB15, NB17 중 BLOCK-004에 귀속된 binding, owner, parser barrier, ACK/NACK, preemption, retained/new-session 경계.
- BASELINE-002 R1, R2, R4, R7과 B4-E1~B4-E6, ST1~ST3, ST6, ST9, ST11~ST13.
- v4 wire의 GAP/NACK 소비 및 입력 차단. 실제 8 MiB buffer 교체와 완전한 rebase는 BLOCK-005에 남긴다.
- v4 cutover로 깨지는 저장소 내부 raw WebSocket 검증 caller를 모두 v4로 이행하고, 옛 Ping Owner Check 기대값을 제거한다.

### 2.2 보존

- 같은 세션의 연속 resume에서는 `terminal.reset()`을 호출하지 않아 alternate screen, DEC mode, mouse tracking, cursor 상태를 보존한다.
- create 거절 전에는 이전 retained 화면을 지우지 않는다.
- `READY_ACK` 전, retained/conflict/displaced/sync 상태에서 input은 전송도 큐잉도 하지 않는다.
- 기존 Android touch/IME/toolbar 의미와 recovery gesture PTY 0-byte 경계를 유지한다.
- 후보는 별도 임의 포트·임시 HOME/profile·자기 소유 child에서만 실행한다. 운영 포트 7683과 기존 세션은 건드리지 않는다.

### 2.3 제외

- `SESSION_BACKLOG_MAX`의 sliding `memmove`를 실제 ring/chunk deque로 바꾸는 작업, full overrun rebase, write/short-write cursor 완결(BLOCK-005).
- `session_reaper`/`waitpid` 수명(P0-3), retained pruning(P0-4), admission/fragment/timer failure 전체 완결(BLOCK-005).
- 실제 Android·Tailscale Funnel·systemd/logrotate·운영 7683 cutover와 `CUSTOMIZATION.md` 최종화(BLOCK-006).
- durable detached-session discovery, terminal snapshot, 외부 인증 추가, 서비스 재시작 간 세션 영속성.

알려진 B5 결함은 해결된 것으로 표시하지 않는다. `staging/check_block004.py`는 output overrun, pruning, reaper 경합을 유발하지 않는 격리 fixture를 쓰고, B4 후보를 일반 운영 안전 증거로 승격하지 않는다.

## 3. 현재 코드 접지

아래 해시는 Plan 작성 시 읽은 load-bearing 원본의 바이트 식별이다.

| 파일 | SHA-256 | EXISTING 관찰 |
|---|---|---|
| `src/server.h` | `abaeb75b034dc73ba5b7e7d966f2b2144654f6495b6aad99a5ed471710cc0220` | client opcode는 `SESSION_READY='5'`, `TAKEOVER='6'`; `pss_tty`에는 epoch/client identity/token/phase가 없고 `input_ready`, `replay_target`, owner generation만 있다(`:7-24`, `:55-99`). |
| `src/protocol.c` | `d2242ed8476a346bb1b6dd276c1393aafd1e120f7209cbb533bd8545c3de74b3` | `SESSION_PROTOCOL_VERSION 3`, 2 s/10 s Owner Check 상수와 nonce/timer 상태(`:21-46`). HELLO는 version/intent/replayPosition만 검증하고 active owner면 `owner_check_begin()`으로 간다(`:1466-1537`). |
| `src/protocol.c` | 위와 같음 | Owner Check는 writable Ping 후 Pong 또는 timeout을 기다리고, Ping 미전송·제3 contender를 generic `error`로 만든다(`:889-1075`). |
| `src/protocol.c` | 위와 같음 | `SESSION_READY`는 retained/owner/position 오류를 `break`로 버리고 valid position이면 곧바로 `input_ready=true`로 만든다(`:1363-1381`). wire ACK/NACK와 server ready deadline이 없다. |
| `src/protocol.c` | 위와 같음 | OUTPUT은 end position만 싣고 write 성공 여부와 무관하게 `send_position`을 전진시킨다(`:1077-1092`, `:1257-1273`). 후자는 B5 대상이지만 v4 frame/epoch 결속은 B4에서 바꾼다. |
| `html/src/components/app.tsx` | `aac3f4c91c1f44dea7bb92d2e6bc1e73babbfe5add6101324af499470ce99eb6` | `webterm.session.v1:${endpoint}`에 create 승인 전 `{version:1,id}`를 저장하고 resume로 바꾼다(`:11-48`). logical client, sequence, token, 승인/in-flight 구분이 없다. |
| `html/src/components/terminal/xterm/index.ts` | `34beafa53bbb2ae147b1a5a2f64e4b98d6117b525ae13de7b1ad27e4730ba947` | `requestRecovery()`는 `connectPromise`가 있으면 수동 동작도 버린다(`:1103-1136`). `waitForGeometry()`가 rAF를 await한다(`:1149-1159`). |
| `html/src/components/terminal/xterm/index.ts` | 위와 같음 | `waitForParserDrain()`과 `settleReplay()`는 16 ms polling을 하고, `settleReplay()`는 추가 rAF 2회를 기다린다(`:1540-1557`, `:1804-1847`). retained는 attempt를 settle하지 않는다. |
| `html/src/components/terminal/xterm/index.ts` | 위와 같음 | `isExitedRetained`는 `exited_retained`에서 true가 되지만 created/attached에서 false가 되지 않는다(`:1924-1978`). 새 session도 같은 terminal을 reset하지 않는다. |
| `html/src/components/terminal/xterm/index.ts` | 위와 같음 | `terminal.write(data, callback)`는 이미 parser completion과 `appliedPosition` 갱신 지점을 제공한다(`:1392-1412`). `ResizeObserver`와 visibility/online listener도 이미 있다(`:1355-1368`, `:1711-1725`). |
| 현재 build dependency | `build/CMakeFiles/ttyd.dir/flags.make`, staged lws headers | 현재 후보 toolchain의 libwebsockets는 `lws_get_random`, `lws_genhash_*`/`LWS_GENHASH_TYPE_SHA256`, `lws_timingsafe_bcmp`를 제공한다. 새 crypto library나 CMake dependency는 필요하지 않다. |

### 3.1 분류

- **EXISTING:** 위 v3 owner-check, silent ready, rAF/polling, storage v1, retained 고착 경로와 lws random/hash API.
- **PROPOSED:** §4~§8의 v4 wire, approval record, epoch fencing, ACK/NACK, ready deadline, storage v2, parser callback barrier, preemption, fresh-session reset, B4 script.
- **UNRESOLVED:** 실제 구현 결과와 B4-E1~E6 runtime 판독은 아직 없다. headless Chromium이 frozen lifecycle을 제공하지 않는 환경에서는 E3 frozen 부분을 통과로 바꾸지 않고 검증 환경 gap으로 남긴다. 실제 Android/운영 경계는 B6이며 B4 script가 대체하지 않는다.

## 4. v4 wire 및 상태 계약

### 4.1 상수와 frame

`SESSION_PROTOCOL_VERSION`은 `src/server.h`의 공유 상수로 옮겨 `4`로 정의한다. v3 client 또는 v3 server와 묵시적으로 섞지 않는다. v3/필수 필드 누락 HELLO에는 process를 spawn/attach하지 않고 `state: "version_mismatch"`, `expectedVersion: 4`, 가능한 경우 `receivedVersion`을 담은 명시 응답을 보낸 뒤 닫는다.

방향별 한 글자 opcode 공간은 유지하되 의미를 v4로 clean cutover한다.

| 방향 | opcode | v4 의미 |
|---|---:|---|
| C→S | `0` | `INPUT`: byte 1~8 big-endian `leaseEpoch`, 뒤가 PTY bytes |
| C→S | `1` | `RESIZE_TERMINAL`: JSON `{leaseEpoch, columns, rows}` |
| C→S | `2`/`3` | `PAUSE`/`RESUME`: JSON `{leaseEpoch}` |
| C→S | `4` | `HEARTBEAT`: JSON `{leaseEpoch, nonce}` |
| C→S | `5` | `REPLAY_APPLIED`: JSON `{sessionId, leaseEpoch, position}` |
| C→S | `6` | `TAKEOVER`: JSON `{observedLeaseEpoch, connectSequence, columns, rows}` |
| S→C | `0` | `OUTPUT`: byte 1~8 `leaseEpoch`, 9~16 `start`, 17~24 `end`, 뒤가 raw PTY bytes. 세 정수는 big-endian uint64 |
| S→C | `3` | `SESSION_STATE`: accepted/conflict/superseded/stale/busy/expired/version mismatch 등 상태 |
| S→C | `4` | `REPLAY_END`: `{version:4, sessionId, leaseEpoch, position, truncated}` |
| S→C | `5` | `HEARTBEAT_REPLY`: `{leaseEpoch, nonce}` |
| S→C | `6` | `READY_ACK`: `{version:4, sessionId, leaseEpoch, position, successorToken}` |
| S→C | `7` | `SESSION_NACK`: `{version:4, sessionId, leaseEpoch, code, retryable, expectedPosition?, receivedPosition?, detail?}` |

`OUTPUT`의 `end - start`는 payload byte length와 같아야 한다. 문자열 길이가 아니라 PTY raw byte offset이다. client는 old epoch frame을 적용하지 않는다. v4 input/resize/pause/resume/heartbeat/replay ACK 모두 현재 session과 epoch 및 `session->client == pss`를 검사한다. 이전 epoch frame은 PTY/geometry/heartbeat 상태를 바꾸지 않고 `STALE_LEASE` 진단/NACK 후 해당 old connection을 닫는다.

### 4.2 HELLO

WebSocket URL의 v3 `?resume=`를 권위 locator로 사용하지 않는다. 첫 JSON HELLO가 다음 필드를 모두 가진다.

```json
{
  "version": 4,
  "resumeId": "32 hex",
  "intent": "create | resume",
  "clientInstanceId": "32 hex",
  "connectSequence": 17,
  "successorToken": "64 lowercase hex; approved resume에서만",
  "replayPosition": 123456,
  "columns": 120,
  "rows": 36,
  "AuthToken": "기존 접속 인증 token"
}
```

- `clientInstanceId`는 browsing-context binding의 128-bit random identity다.
- `connectSequence`는 JSON safe integer 범위 `1..9007199254740991`에서 client binding별 단조 증가한다. socket retry는 같은 논리 attempt의 sequence를 재사용하고, 사용자 preemption은 새 sequence를 할당한다.
- `successorToken`은 서버가 생성한 256-bit random을 lowercase hex로 직렬화한 64자 값이다. create에는 없다.
- 모든 JSON 필드는 json-c type까지 엄격히 확인한다. string을 number로 묵시 변환하거나 음수/overflow/0 geometry를 허용하지 않는다.
- malformed/version mismatch/auth 실패는 create나 resume로 추측하지 않는다.

`SESSION_STATE`의 accepted 상태(`created`, `attached`)에는 최소 `version`, `state`, `sessionId`, `sessionDiagnosticId`, `leaseEpoch`, `ownerPhase`, `replay {from,to,truncated,droppedBytes}`, `inputReady:false`를 싣는다. `CONFLICT`에는 현재 `leaseEpoch`, `ownerPhase`, application heartbeat lease의 fresh 여부를 싣되 token/hash를 싣지 않는다. `OWNER_CHECK_BUSY`는 `retryable:true`, `retryAfterMs:1000`이고 generic error가 아니다.

### 4.3 서버 권위 상태

`struct tty_session`에 다음 권위 상태를 둔다.

- `uint64_t lease_epoch`: 새 create의 첫 grant는 1, 유효 successor 소비 또는 CAS takeover마다 증가한다. 동일 승인 attempt의 response-loss 재조회는 증가시키지 않는다.
- `char owner_client_instance_id[33]`와 `uint64_t owner_connect_sequence`.
- `uint8_t successor_token_hash[32]`, `bool successor_token_valid`. raw token은 session이나 로그에 보존하지 않는다.
- `enum owner_phase { OWNER_ATTACHING, OWNER_REPLAYING, OWNER_READY } owner_phase`; `session->client == NULL`이면 phase는 권위가 없다.
- `uint64_t last_application_heartbeat_ms`, `last_progress_at_ms`, `owner_started_at_ms`.
- 30,000 ms server ready deadline timer. grant 때 시작하고, `READY_ACK` full write 성공 때 중단한다. fixed finite deadline이며 output/heartbeat로 무기한 연장하지 않는다.
- bounded `last_approval` 한 건: approval kind(create/successor/CAS), `clientInstanceId`, `connectSequence`, `leaseEpoch`, 제시된 token hash 유무와 결과. raw token은 보관하지 않는다.

`struct pss_tty`에는 HELLO의 client ID/sequence, 부여받은 `lease_epoch`, 승인 kind, pending ACK/NACK/status, ready-ACK용 일시 token buffer, attempt 결과를 추가한다. fencing 후 stale `pss`가 `tty_session`을 역참조하지 않아도 `resume_id`와 lease로 lookup/거절할 수 있게 하고, dangling session pointer를 만들지 않는다.

### 4.4 token 생성·소비·응답 소실 수렴

1. 발급은 `lws_get_random(context, 32 bytes)`가 정확히 32를 반환한 경우만 성공한다. hex encode 후 raw 32 bytes를 `lws_genhash_*` SHA-256으로 hash하고 session에는 hash만 설치한다. 비교는 `lws_timingsafe_bcmp`를 쓴다. RNG/hash 실패는 입력 권한을 열지 않고 명시적 protocol failure로 정착한다.
2. 유효한 current token, 같은 `ownerClientInstanceId`, 현재보다 큰 sequence가 오면 libuv event-loop callback 안에서 token hash를 먼저 무효화하고 approval record를 기록한 뒤 old pss를 fence하고 `leaseEpoch++` 한다. 기존 socket의 Ping/Pong/writable 결과를 기다리지 않는다.
3. provisional phase에서 같은 client가 같은 consumed token으로 더 높은 sequence를 제시하면 최신 attempt가 같은 approval 결과/epoch를 이어받고 이전 pss는 `SUPERSEDED`가 된다. 더 낮은 sequence는 `SUPERSEDED`; 같은 sequence/같은 approval credential은 response-loss 재조회로 같은 epoch에 재결속한다.
4. `READY` 이후 consumed old token은 정확히 같은 approval tuple의 response-loss 재조회에만 허용한다. 더 높은 새 attempt는 현재 `successorToken`을 제시해야 한다. 이로써 one-time token을 일반 재사용 권한으로 만들지 않는다.
5. valid `REPLAY_APPLIED` 뒤 writable callback에서 새 token을 생성하여 `READY_ACK`를 full write한다. full write 성공 후에만 새 hash를 current token으로 설치하고 owner phase를 `READY`, `input_ready=true`로 바꾼다. raw token buffer는 즉시 지운다. write 실패/short write에서는 ready/token 회전을 성공으로 기록하지 않는다.
6. ACK가 network에서 소실되어 client가 옛 token과 in-flight sequence만 가진 경우, bounded approval record가 exact tuple을 같은 epoch로 다시 붙인다. 재 replay 뒤 새 `READY_ACK` token을 발급한다. 새 PTY나 두 owner를 만들지 않는다.
7. 완전히 복제된 동일 credential/client/sequence를 물리 탭별로 식별한다고 주장하지 않는다. 하나만 `session->client`가 되며 뒤 연결이 앞 연결을 fence한다. `displaced`/`superseded` client는 자동 sequence 증가나 자동 탈환을 하지 않는다.

`EXITED_RETAINED`는 입력 owner takeover가 아니므로 current successor를 소비하거나 `READY_ACK`를 기다리지 않는다. 같은 자격의 read-only viewer만 붙이고 parser callback에서 replay가 끝나면 local attempt를 완료한다. token을 새 입력 권한으로 재발급하지 않으며 모든 input/resize를 계속 거절한다.

### 4.5 경합과 CAS Takeover

- 다른 `clientInstanceId`의 HELLO는 old socket Ping 없이 즉시 `CONFLICT`를 반환한다. READY owner의 input/resize 권위는 그대로다.
- client가 명시적 UI 선택 후 `TAKEOVER(observedLeaseEpoch, connectSequence, geometry)`를 보낸다. 서버는 현재 session `lease_epoch == observedLeaseEpoch`를 단일 event-loop turn에서 비교·교환한다.
- 일치하면 old pss의 input gate를 먼저 닫고 `displaced`를 queue한 뒤 new owner/sequence, `leaseEpoch+1`, ATTACHING, ready deadline을 설정한다. old socket이 이미 닫혀 `session->client == NULL`이어도 epoch가 같으면 성공한다.
- 불일치면 `STALE`과 최신 epoch를 반환하고 자동 재시도하지 않는다. client는 다시 상태를 확인하고 사용자 선택을 요구한다.
- 동일 approval의 CAS response loss는 `last_approval` exact tuple로 같은 epoch 결과를 재조회한다. takeover client는 10,000 ms local timeout 뒤 결과를 재확인할 수 있으나 blind CAS를 반복하지 않는다.
- ATTACHING/REPLAYING owner의 다른-client 추가 contender는 `OWNER_CHECK_BUSY`, `retryable:true`, `retryAfterMs:1000`으로 유한 정착한다. 첫 명시 contender를 server-side pending slot으로 오래 보유하지 않는다.
- 같은-client 최신 provisional contender는 이전 것을 `SUPERSEDED`로 끝낸다. displaced/superseded client는 visibility/online event로 자동 탈환하지 않는다.

### 4.6 replay, ACK/NACK, ready deadline

정상 순서는 다음 하나뿐이다.

```text
HELLO v4
  → SESSION_STATE(created|attached, leaseEpoch, ATTACHING/REPLAYING)
  → OUTPUT(epoch,start,end,bytes)*
  → REPLAY_END(epoch,target)
  → xterm terminal.write(..., callback)에서 target 적용 확인
  → REPLAY_APPLIED(sessionId,epoch,target)
  → READY_ACK(sessionId,epoch,target,new successorToken)
  → client token 저장 시도 후 input gate open
```

- server는 accepted 전 ATTACHING, accepted/replay 송신 시작 시 REPLAYING이다.
- `REPLAY_APPLIED`의 JSON/session/epoch/owner/phase/target을 각각 검사한다.
- current epoch인데 position이 target과 다르면 `POSITION_MISMATCH` NACK에 expected/received를 넣는다.
- malformed payload, OUTPUT gap, 도달할 수 없는 barrier, phase 위반은 `SYNC_REQUIRED`와 구체 `detail`을 보낸다. client는 old barrier를 폐기하고 input을 막은 degraded/sync-required 상태에 머문다. B5 이전에는 손실 byte를 applied로 올리거나 완전 rebase 성공을 주장하지 않는다.
- old epoch는 `STALE_LEASE`, 종료/retained ready 시도는 `SESSION_ENDED` NACK 또는 명시 retained 상태로 끝낸다. 어느 경우도 silent `break`만 하지 않는다.
- ready deadline이 만료되면 해당 pss를 fence하고 `READY_TIMEOUT`을 가능한 경우 보낸 뒤 owner를 비우고 살아 있는 PTY는 `DETACHED_GRACE`로 유지한다. timer callback은 captured/current lease를 대조하여 새 owner를 닫지 않는다.
- native WebSocket Ping/Pong은 transport 진단 외 소유권 판정에 사용하지 않는다. `owner_check_*`, `OWNER_CHECK_PREPARE_MS`, `OWNER_CHECK_PONG_MS`, nonce/timer/pending contender 경로를 삭제한다.
- v4 heartbeat는 READY/current epoch에서만 `last_application_heartbeat_ms`를 갱신한다. 5 s interval/30 s timeout의 현행 client 값을 유지한다. 출력 없는 idle shell은 실패가 아니다. heartbeat가 stale이어도 다른 client가 자동 steal하지 않고 CONFLICT/CAS를 거친다.

## 5. 파일별 구현 명세

### 5.1 `src/server.h`

1. `SESSION_PROTOCOL_VERSION 4`, ID/token/hash 길이, ready deadline(30,000 ms), v4 server opcode `READY_ACK`, `SESSION_NACK`, client opcode의 `REPLAY_APPLIED` 명칭을 정의한다.
2. `enum owner_phase`와 approval/result enum을 추가한다.
3. `pss_tty`에 `client_instance_id`, `connect_sequence`, `lease_epoch`, approval kind, pending ACK/NACK/status, ready token 임시 buffer/length를 둔다. 기존 `offered_owner_generation`/v3 takeover generation 필드는 제거한다.
4. 방향별 동일 숫자 opcode를 주석으로 명확히 구분하고 INPUT/OUTPUT v4 binary header 크기를 상수화한다. magic offsets를 여러 함수에 복제하지 않는다.
5. v3 `SESSION_READY` alias나 owner-generation compatibility shim은 남기지 않는다.

### 5.2 `src/protocol.c`

1. `tty_session`에 §4.3 필드를 추가하고 생성/attach/disconnect/release에서 명시적으로 초기화·중단한다. `lease_epoch` overflow 직전에는 새 grant를 명시 실패시키며 wrap하지 않는다.
2. HELLO parser를 별도 작은 함수로 두어 field type/길이/range/auth를 한 번 검증한다. `resumeId`는 HELLO가 권위이며 v3 query parser 의존을 제거한다.
3. token helper는 lws RNG/SHA-256/timing-safe compare만 감싼다. raw token, token hash, AuthToken을 diagnostics에 넣지 않는다.
4. `last_approval` 판정 함수 하나에서 new successor, exact retry, newer provisional same-client, stale/superseded, other-client conflict를 결정한다. spawn/attach 함수가 별도 규칙을 재구현하지 않게 한다.
5. `fence_owner(session, old, state)`는 먼저 session owner 권위를 제거하고 old `input_ready=false`, old lease 무효, process/session 접근 제거를 수행한 다음 상태 송신/close를 schedule한다. old writable 성공 여부는 새 grant의 선행조건이 아니다.
6. create는 absent session에서만 PTY를 한 번 spawn하고 approval record를 만든다. 동일 `(resumeId, clientInstanceId, connectSequence, create)` 재조회는 기존 PTY/epoch를 재사용한다. capacity 거절이나 spawn 실패는 approved binding/token을 만들지 않는다.
7. `owner_check_begin/clear/finish/send_ping/receive_pong`, 관련 timer와 `checking` state를 삭제한다. lws native control frame 자체를 소유권 증거로 사용하지 않는다.
8. Takeover payload를 `observedLeaseEpoch` CAS로 바꾸고 §4.5 결과를 명시 상태로 보낸다.
9. OUTPUT encoder를 25-byte v4 header로 바꾸고 epoch/start/end를 결속한다. B4에서는 기존 buffer를 유지하되 `send_position < output_start`를 정상 REPLAY_END로 만들지 말고 `SYNC_REQUIRED(detail=BUFFER_OVERRUN)`를 보내 input을 차단한다. 완전 rebase/buffer 교체는 B5에 남긴다.
10. REPLAY_END에 session/epoch를 포함하고, REPLAY_APPLIED handler는 모든 invalid branch에서 NACK/status를 queue한다. ACK/NACK도 writable callback에서 full-write 여부를 확인한다.
11. ready timer는 grant 시 arm, valid READY_ACK full write/owner fence/connection close/session release에서 stop+close한다. timer의 lease 확인 없이 stale callback이 current owner를 정리하지 못하게 한다.
12. INPUT/RESIZE/PAUSE/RESUME/HEARTBEAT를 current owner+epoch+phase READY로 gate한다. rejected old frame은 `pty_write`, `pty_resize`, heartbeat 갱신을 호출하지 않는다.
13. diagnostics는 `leaseEpoch`, phase, connectSequence, approval kind, deadline, replay target/start/end, ACK/NACK code, fence/supersede/CAS 사건을 기록하되 raw token/hash와 사용자 input bytes를 기록하지 않는다.
14. connection close/finally는 `session->client == pss && session->lease_epoch == pss->lease_epoch`일 때만 owner를 detach한다. old close가 new owner의 timer, cursor, phase를 지우지 않는다.

### 5.3 `html/src/components/app.tsx`

endpoint별 storage schema를 `version:2`로 clean cutover한다.

```ts
type StoredBindingV2 = {
    version: 2;
    id: string;
    clientInstanceId: string;
    state: 'pending-create' | 'approved';
    connectSequence: number;              // 마지막 확정 sequence
    successorToken?: string;              // approved에만 존재
    leaseEpoch?: number;
    inFlight?: {intent: 'create' | 'resume'; connectSequence: number};
};
```

1. `clientInstanceId`와 create `resumeId`는 각각 128-bit crypto random hex다.
2. 새 logical attempt를 시작하기 전에 `inFlight.connectSequence`를 storage에 먼저 기록한다. 같은 attempt의 token fetch/socket/backoff/reload retry는 이 값을 재사용한다. 수동 preemption은 더 높은 sequence를 배정한다.
3. create는 `pending-create`로 저장하고 READY_ACK 전에는 approved resume로 승격하지 않는다. create 응답 drop/reload는 같은 ID/client/sequence의 create를 재조회하여 중복 PTY를 만들지 않는다.
4. READY_ACK를 받으면 한 번의 `sessionStorage.setItem`으로 successor token, lease epoch, 확정 sequence, `state:'approved'`, `inFlight` 제거를 기록한다. storage 실패 시 현재 page memory에서는 token을 유지하되 `persisted=false`와 continuity unavailable 안내를 유지한다.
5. v1 record는 v4 credential로 추정하거나 자동 resume하지 않는다. “v4 복구 자격 없음” 상태로 새 세션의 명시적 선택을 제공하며, v1 ID만으로 새 PTY/복구 성공을 만들지 않는다.
6. `SessionBinding` API를 `create`, logical attempt 할당/재사용, `commitReady`로 바꾸고 옛 `markCreated()` 조기 승인 API를 제거한다. 모든 caller를 함께 이행한다.
7. token을 console, diagnostics, DOM, URL에 넣지 않는다.

### 5.4 `html/src/components/terminal/xterm/index.ts`

#### A. v4 state와 wire

- `SessionRequest`에 client ID, sequence, optional successor token/lease, pending/approved 의미를 포함한다.
- server lease와 owner phase, current barrier, current attempt controller/id를 별도 필드로 둔다.
- INPUT frame은 epoch header를 붙이고 resize/flow/heartbeat/replay/takeover payload도 epoch/CAS 계약을 따른다.
- OUTPUT의 epoch/start/end를 검증한다. `end <= applied`는 중복으로 버리고, `start < applied < end`는 적용된 prefix를 잘라 suffix만 write하며, `start > applied`는 gap으로 barrier를 abort하고 `sync-required`/input blocked로 간다. applied position은 parser callback 또는 명시 rebase로만 변한다.
- READY_ACK의 session/epoch/position을 current barrier와 대조하고 `commitReady` 저장 시도 후에만 `inputReady=true`로 바꾼다. stale ACK/NACK는 current attempt를 변경하지 않는다.

#### B. rAF/16 ms polling 제거

- `waitForGeometry()` async loop를 삭제한다. HELLO geometry는 `lastValidGeometry ?? {cols:80, rows:24}`를 동기 선택하므로 rAF를 한 번도 받지 않아도 socket을 연다.
- `ResizeObserver`, `visibilitychange:visible`, visual viewport resize에서 visible layout을 `fitAddon.fit()`으로 측정하고 current READY epoch에 `RESIZE_TERMINAL`을 보낸다. resize batching/diagnostics용 rAF는 남을 수 있지만 connect/replay/ACK의 await 대상이 아니다.
- `waitForParserDrain()`의 16 ms polling과 `settleReplay()`의 polling/rAF 2회를 삭제한다.
- barrier는 `{attemptId, terminalEpoch, sessionId, leaseEpoch, target, signal, sent}`를 가진다. `terminal.write(data, callback)` callback이 pending byte를 줄이고 해당 terminal/session epoch의 `appliedPosition`을 갱신한 직후 `maybeCompleteReplayBarrier()`를 호출한다. 이미 target이면 REPLAY_END 처리 시 즉시 같은 함수를 호출한다. 조건이 충족되면 REPLAY_APPLIED를 정확히 한 번 보낸다.
- AbortSignal listener가 barrier를 즉시 폐기하고 await/deferred를 settle한다. old parser callback은 실제 xterm queue를 마무리할 수 있으나 old attempt barrier, current cursor, input 권위를 변경하지 않는다.
- write callback의 적용 귀속은 connection generation이 아니라 `(sessionId, terminalEpoch)`로 판정한다. 같은 세션 socket 재연결 중 완료된 old callback은 실제 적용 위치로 인정하지만, 새 PTY용 terminal epoch가 바뀐 뒤의 old callback은 새 cursor를 올리지 않는다.

#### C. preemption과 recovery budget

- 하나의 `AbortController`를 logical attempt 전체(fetch, backoff, parser barrier, takeover wait)에 전달한다. manual Reconnect/toolbar recovery/Start New Session은 `connectPromise` 유무와 상관없이 `abortActiveAttempt()`를 먼저 호출하고 새 sequence/intent를 시작한다.
- abort는 fetch abort, backoff deferred resolve, barrier listener settle, attempt timer clear, old socket close를 수행한다. `connectPromise.finally`는 자신이 아직 current promise일 때만 필드를 지워 새 promise를 훼손하지 않는다.
- 모든 socket/message/close/timer/parser callback은 captured `attemptId`, session ID, terminal epoch를 current 값과 비교한다. generation 증가만 하고 pending Promise를 깨우지 않는 방식은 금지한다.
- visible 적극 복구 누적 시간만 60 s budget에 더한다. hidden 구간은 차감하지 않는다. budget 소진 뒤에도 manual action은 항상 가능하고, server grace 동안 30 s 저빈도 retry를 유지한다. `visible`/`online` 복귀는 displaced/expired가 아니면 stale attempt를 abort하고 즉시 한 번 재확인한다.
- recovery UI/toolbar Enter/pointerdown/click은 `preventDefault`/`stopPropagation` 후 local recovery만 시작한다. blocked keystroke를 queue하지 않으며 READY_ACK 뒤 재생하지 않는다.

#### D. retained와 fresh emulator

- retained REPLAY_END target이 parser callback으로 적용되면 `inputReady=false`를 유지하고 attempt를 즉시 `ready`가 아닌 read-only 완료 결과로 settle한다. READY_ACK를 기다리지 않는다.
- Start New Session 시작 시 active attempt를 abort하고 `isExitedRetained=false`, 새 session ID, `appliedPosition=0`, 새 `terminalEpoch`를 준비하지만 이전 화면은 아직 지우지 않는다.
- server가 `state:'created'`로 새 PTY를 승인한 때 `terminal.write(empty, callback)` parser-queue fence를 먼저 넣는다. 그 callback에서 `terminal.reset()`, cursor/barrier/flow/mode 관련 local state를 초기화한다. 이후 수신 OUTPUT write는 xterm queue상 이 reset 뒤에 적용된다. 따라서 첫 새-session byte 전에 분리되며, create 거절이면 reset이 실행되지 않아 이전 결과 화면을 보존한다.
- `attached`(동일 session 연속 resume)에는 reset을 호출하지 않는다. created/attached active 상태에서는 `isExitedRetained=false`를 명시한다.

### 5.5 v4 cutover에 따라 함께 바꿀 staging caller

다음 파일의 raw client가 현재 version 3/old `SESSION_READY`를 직접 생성하므로 v4 HELLO, epoch frame, parser 적용을 대신하는 raw-client의 명시적 REPLAY_APPLIED/READY_ACK token 보관으로 이행해야 한다.

- `staging/check_block003.py`
- `staging/check_exit_lifecycle.py`
- `staging/check_omp_reconnect.py`
- `staging/check_protocol_edges.py`
- `staging/check_server_hardening.py`
- `staging/check_reconnect.py`
- `staging/check_fresh_session.py`

`check_fresh_session.py`/`check_reconnect.py`의 `checking` state, owner Ping/Pong, 2 s/10 s 대기를 정상값으로 고정한 assertion은 새 이름으로 재핀하지 않는다. B4-E1/E2의 no-owner-roundtrip/CONFLICT/CAS/SUPERSEDED로 대체하거나 중복이면 삭제한다. 다른 스크립트가 검증하는 B3/B5-adjacent observable contract는 유지하되 v4 handshake helper만 이행한다. v3 compatibility alias를 test 편의로 제품 코드에 넣지 않는다.

## 6. `staging/check_block004.py` 설계

### 6.1 harness

새 스크립트는 `unittest` 또는 동일한 fail-fast 구조로 정확히 여섯 top-level scenario `test_b4_e1`~`test_b4_e6`을 제공한다. 각 scenario는 fresh free port, temporary HOME/profile/evidence dir, fresh resume IDs, 자기 소유 ttyd process와 PTY fixture를 사용한다.

공통 구성:

- 입력: `TTYD_BIN`(기본 `build/ttyd`), `WEBTERM_TEST_INDEX`(기본 `html/dist/inline.html`), 선택 `WEBTERM_EVIDENCE_DIR`.
- ttyd env: `TTYD_DIAGNOSTICS=1`, 짧은 격리 grace, B4에 필요한 명시 limit. 운영 port 7683 사용 금지.
- `TtydFixture`: process group으로 시작하고 `/token` readiness를 확인하며 stdout/stderr를 캡처한다. teardown은 fixture가 기록한 PID/start identity만 TERM→유한 wait→KILL하고 temp profile/socket을 닫는다.
- `WireClientV4`: 실제 websocket-client로 v4 HELLO/frame parsing, replay bytes 축적, explicit REPLAY_APPLIED, READY_ACK/NACK 수신, token/epoch 갱신을 수행한다.
- `TcpFaultProxy`: WebSocket connection별 frame/control opcode와 monotonic timestamp를 기록하고 선택 connection의 양방향 blackhole, 특정 READY_ACK/HTTP token response drop, delayed frame release를 수행한다. 성공 응답은 생성하지 않는다.
- `ChromeCdp`: 실제 served bundle을 열고 real `window.ttydDiagnostics()`, xterm buffer/modes, sessionStorage record, visibility/lifecycle, ResizeObserver 결과를 읽는다.
- `PtyCaptureFixture`: 실제 child가 PID/session marker를 출력하고 raw stdin bytes를 소유 temp file에 기록한다. 복구 동작 0-byte 및 ACK 후 1회 input을 authoritative readback한다.
- 결과 JSON은 binary/bundle SHA-256, server PID/port, 각 session diagnostic ID와 PTY PID, epoch/phase sequence, wire 사건, PTY byte count, Chromium version/lifecycle capability, 제한을 기록한다. raw AuthToken/successorToken/user input 내용은 기록하지 않는다.

### 6.2 B4-E1 — v4 binding, version gate, silent-disconnect successor

1. real create를 완료하여 READY_ACK token과 epoch, PTY PID를 얻는다. storage record가 `approved`, token/sequence/client ID를 갖고 pending이 제거되었는지 browser에서 읽되 evidence에는 token 값을 쓰지 않는다.
2. old WebSocket을 proxy에서 FIN/RST 없이 blackhole한다. 같은 client, 더 높은 sequence, valid token으로 새 HELLO를 보낸다.
3. `SESSION_ACCEPTED`와 새 epoch가 기존 owner 대상 opcode 9 Ping/Pong 없이 도착하고 같은 PTY PID/진행 중 marker를 읽는지 확인한다. 단순 0 ms가 아니라 wire에 owner roundtrip 부재가 주 증거다.
4. proxy가 보존한 old epoch INPUT/RESIZE/HEARTBEAT를 뒤늦게 전달하고 PTY capture/geometry/heartbeat가 변하지 않는지 확인한다. new epoch input은 정확히 한 번 반영한다.
5. version 3 HELLO는 `version_mismatch(expectedVersion=4)`이고 spawn count가 늘지 않는다. server logs/evidence에 raw token 문자열이 없는지 확인한다.
6. READY_ACK drop 후 같은 in-flight sequence/옛 token으로 reload/retry하여 같은 PTY/epoch approval에 수렴하고 token을 다시 얻는지 확인한다.
7. storage write denial과 capacity-rejected create를 별도 fresh fixture에서 주입하여 approved binding이 생기지 않고 reload가 nonexistent resume/자동 새 PTY로 변하지 않는지 확인한다.

### 6.3 B4-E2 — CONFLICT, CAS, response loss, contender ordering

1. owner A를 READY로 만든 뒤 client B HELLO를 보내 즉시 CONFLICT와 observed epoch를 받고 A의 input이 계속 작동하는지 본다.
2. B가 observed epoch CAS를 선택하면 epoch가 증가하고 A는 displaced, B는 replay→READY가 된다. A의 visibility/online을 발생시켜도 자동 탈환하지 않는지 확인한다.
3. C가 옛 observed epoch로 CAS하면 STALE/latest epoch를 받고 owner가 바뀌지 않는다.
4. 별도 fixture에서 conflict 뒤 old socket만 닫고 epoch가 변하지 않은 상태에서 같은 observed epoch CAS가 성공하는지 확인한다.
5. CAS/READY_ACK 응답 drop 뒤 exact approval tuple을 재조회하여 PTY spawn 1회, owner 1개, 같은 approval epoch로 수렴하는지 확인한다.
6. provisional same-client sequence N/N+1을 경쟁시켜 N은 SUPERSEDED, N+1만 owner인지 확인한다. 다른 client 추가 contender는 retryable OWNER_CHECK_BUSY/retryAfterMs를 받고 generic error가 아니다.
7. ATTACHING/REPLAYING client가 REPLAY_APPLIED를 보내지 않으면 30 s ready deadline 뒤 owner가 해제되고 다음 명시 contender가 진행되는지 확인한다. idle READY shell은 output 부재만으로 해제되지 않는다.

### 6.4 B4-E3 — rAF 없는 hidden/frozen 복구와 geometry

1. fresh Chromium tab에 geometry가 확정되기 전 rAF callback을 실행하지 않도록 fault를 걸고 tab을 background(hidden-but-JS-running)로 둔다.
2. wire에서 HELLO `80×24`, OUTPUT→REPLAY_END→REPLAY_APPLIED→READY_ACK가 실제 parser callback 증가와 함께 완결되는지 확인한다. rAF callback 0회 조건에서도 input-ready가 되어야 한다.
3. 이전 visible geometry가 있는 variant는 fallback이 아니라 마지막 유효 값을 HELLO에 사용한다.
4. tab을 visible로 복귀시키고 container 크기를 변경하여 ResizeObserver가 실제 cols/rows를 계산하고 current epoch RESIZE를 보내 PTY `stty size`가 수렴하는지 확인한다.
5. CDP `Page.setWebLifecycleState('frozen')`가 지원되면 provisional replay 중 freeze하여 client JS가 멈춘 동안 server ready deadline/PTY drain이 진행되는지, thaw 후 stale attempt를 폐기하고 즉시 새 attempt로 복구하는지 확인한다. 지원되지 않으면 E3 frozen 부분을 PASS로 만들지 않고 capability gap을 결과에 남긴다.
6. hidden 경과를 60 s visible budget에서 제외하고 visible budget 소진 뒤에도 manual reconnect와 30 s low-frequency retry가 남는지 diagnostics/wire로 확인한다.

### 6.5 B4-E4 — parser barrier, ACK/NACK, input gate

1. proxy wire와 browser diagnostics를 결합하여 SESSION_ACCEPTED→OUTPUT ranges→REPLAY_END→parser callback/applied target→REPLAY_APPLIED→READY_ACK 순서를 확인한다.
2. READY_ACK 전 terminal key를 발생시켜 PTY capture가 0 byte이고, ACK 후 새 key만 1회 도착하는지 확인한다.
3. raw clients가 wrong position, malformed JSON, old epoch, wrong owner, wrong phase, retained ready를 각각 보내 `POSITION_MISMATCH`, `SYNC_REQUIRED(detail)`, `STALE_LEASE`, `SESSION_ENDED` 등 명시 결과를 유한 시간에 받는지 확인한다. silent timeout은 실패다.
4. proxy에서 실제 서버 OUTPUT 하나를 drop하고 다음 range를 전달하여 client가 start gap을 검출하고 old barrier/input을 폐기하며 SYNC_REQUIRED/degraded가 되는지 확인한다. 누락 bytes까지 appliedPosition을 올리거나 READY를 보내면 실패다. full rebase 성공은 B5로 명시한다.
5. old epoch REPLAY_APPLIED/늦은 READY_ACK를 전달해 current owner/barrier/input gate가 변하지 않는지 확인한다.

### 6.6 B4-E5 — retained read-only settle과 fresh emulator 분리

1. 실제 child가 alternate screen/mouse/DEC mode marker와 final output을 내고 종료하도록 한다. reconnect하여 exited-retained replay가 parser에 적용되면 `connectInFlight=false`, inputReady=false로 즉시 정착하고 READY_ACK를 기다리지 않는지 확인한다.
2. retained replay 진행 중 variant와 완료 후 variant 각각에서 Start New Session을 누른다. old attempt/barrier가 abort되고 create가 진행되어야 한다.
3. 새 `created` 승인 전에는 old result buffer가 남고, 승인 뒤 첫 OUTPUT parser callback 전에 reset fence가 실행되는 사건 순서를 diagnostics로 확인한다. 새 session에는 old marker/mode/cursor와 `isExitedRetained`가 없고 새 PTY PID, READY_ACK, 실제 input 결과가 있어야 한다.
4. create capacity 거절 variant는 old result 화면을 보존한다.
5. 살아 있는 동일 session resume variant는 alternate/mouse/DEC mode를 reset하지 않고 같은 PTY를 유지한다. signal 전송만으로 화면 복원을 판정하지 않고 xterm mode/buffer를 읽는다.
6. 새 세션 선택이 old retained/session grace를 줄이거나 old process를 종료한 것으로 기록되지 않는지 server state를 확인한다.

### 6.7 B4-E6 — manual preemption, late callback isolation, 0-byte gestures

1. token fetch 지연, reconnect backoff, replay parser barrier, takeover wait 네 subcase에서 Reconnect 또는 Start New Session을 연속 선택한다.
2. 각 subcase에서 old AbortSignal이 실제 settle되고 최신 intent의 sequence/socket만 남는지 확인한다. proxy가 old HTTP/socket/frame/callback을 뒤늦게 release해도 new `connectPromise`, socket, cursor, token, inputReady를 지우지 않아야 한다.
3. recovery overlay pointerdown/click, toolbar Enter, rapid double tap, terminal tap을 실제로 발생시키고 PTY capture가 0 byte인지 확인한다.
4. input blocked 중 발생시킨 key가 READY_ACK 후 자동 전달되지 않고, ACK 후 새로 입력한 byte만 정확히 1회 도착하는지 확인한다.
5. evidence의 server/client revision, binary/bundle hash, session/PTY identity, epoch 사건이 같은 fixture에 귀속되는지 확인하고 B5 미해결 제한을 결과에 적는다.

## 7. 단계별 구현 순서와 검증 gate

BLOCK-004는 HARD_ATOMIC이다. 아래 단계는 작업 순서이지 중간 배포/완료 경계가 아니다.

### 단계 0 — 현재 target 고정과 harness 골격

- 위 네 load-bearing source와 v3 staging caller의 현재 bytes를 다시 읽고 사용자 변경을 보존한다.
- `staging/check_block004.py`의 fixture/process cleanup/wire event schema를 먼저 만든다. 아직 없는 v4 성공을 canned response로 채우지 않는다.
- Gate 0: script가 지정되지 않은 binary/bundle, port 7683, 외부 URL을 사용하지 않고, 실패 시 자기 process만 정리하도록 dry discovery에서 확인한다. 기능 PASS는 주장하지 않는다.

### 단계 1 — 공유 v4 wire와 strict version gate

- `server.h` 상수/opcode/pss 구조, `protocol.c` HELLO parser/explicit mismatch, TypeScript enum/frame codec를 함께 바꾼다.
- raw staging caller 전부를 v4 contract로 이행한다. obsolete owner-check expectation은 삭제/대체한다.
- Gate 1: C target compile과 frontend `yarn inline`이 성공하고, real isolated server에서 v3 mismatch가 spawn 0회, v4 create가 accepted까지 진행한다. compile/HTTP만으로 다음 Exit를 주장하지 않는다.

### 단계 2 — server approval/token/epoch/CAS/fencing

- session authority fields, token helper, bounded approval record, create idempotency, successor consume, exact retry, CAS, conflict/superseded/busy를 구현한다.
- old Owner Check code와 fields를 완전히 제거한다.
- Gate 2: B4-E1/E2 raw-wire subset에서 같은 PTY, no old Ping, one owner, old epoch PTY 0 byte, CAS stale/old-close/response-loss를 관찰한다. token 값은 evidence에 남기지 않는다.

### 단계 3 — replay frame, ACK/NACK, ready deadline

- epoch/start/end OUTPUT, REPLAY_END, REPLAY_APPLIED validation, READY_ACK token rotation, NACK, ready timer, epoch-gated input/resize/flow/heartbeat를 구현한다.
- Gate 3: B4-E4 raw/browser subset과 ready timeout을 통과한다. server local `input_ready`만으로 통과하지 않고 parser callback, wire ACK, PTY bytes를 결합한다.

### 단계 4 — approved binding과 client recovery core

- `app.tsx` storage v2/in-flight commit을 구현한다.
- xterm의 callback barrier, synchronous fallback geometry, preemption, visible budget, v4 message handling을 구현한다.
- Gate 4: B4-E1 response-drop/storage cases, B4-E3 hidden path, B4-E6 fetch/backoff/parser/takeover preemption을 실제 bundle에서 통과한다. rAF를 setTimeout으로 바꾼 구현은 실패다.

### 단계 5 — retained/fresh emulator 분리

- read-only settle, create 승인 뒤 parser queue reset fence, active state flag reset, same-session no-reset을 구현한다.
- Gate 5: B4-E5의 replay 중/후 Start New Session, rejection preservation, new PTY input, same-session mode 보존을 통과한다.

### 단계 6 — 전체 B4 self-check와 인계

- 같은 최종 source에서 C binary와 inline bundle을 새로 만들고 그 exact hashes로 `staging/check_block004.py`의 E1~E6을 실행한다.
- v4로 이행한 기존 targeted staging scripts 중 변경된 contract의 실제 경로를 실행한다. project-wide suite는 최종 fan-in 소유자가 한 번 수행한다.
- final Gate: E1~E6 모두 실제 결과가 있고, candidate process/profile/ports가 정리되며, 운영 7683/기존 세션 비영향을 확인한다. B5 미해결 결함, headless/실기기 한계, 실행물 identity를 handoff에 남긴다.

어느 gate에서든 duplicate PTY/owner, old epoch input, generic owner-check error, false READY, input leak, retained 고착, UAF/unknown process effect가 나타나면 해당 candidate의 신규 입력/시험을 중단하고 자기 fixture를 정리한다. 실제 운영 process를 restart/kill하여 통과시키지 않는다.

## 8. 실패·중단·재개 처리

- **partial server/client cutover 금지:** v4 server와 v3 bundle 또는 그 반대를 후보 성공으로 노출하지 않는다. version mismatch가 유일한 혼합 결과다.
- **late effect:** every callback/timer/close는 attempt/session/terminal epoch를 검사한다. old cleanup은 current pointer/epoch가 자신과 같을 때만 공유 state를 해제한다.
- **ACK unknown effect:** token/CAS/READY_ACK response가 소실되면 exact approval tuple readback을 먼저 한다. 새 create/CAS를 blind retry하지 않는다.
- **NACK:** mismatch에서 input gate는 닫힌다. B5 전에는 fake rebase나 applied cursor jump를 만들지 않는다.
- **timer:** ready timer init/start 실패는 grant를 성공시키지 않는다. provisional owner를 fence하고 retryable explicit failure로 돌린다.
- **cleanup:** test teardown은 owned PID/start identity, sockets, browser profile만 정리한다. kill 반환값을 정리 완료로 간주하지 않고 process exit와 port 해제를 판독한다.

## 9. Conditional First Work와 방법 변경 경계

### 9.1 frozen lifecycle 관찰

- `plan_anchor`: §6.4 B4-E3.
- `permitted_initial_work`: 격리 Chromium에서 CDP lifecycle 지원 여부를 읽고 fresh candidate tab을 `frozen`/`active`로 전환한다.
- `discriminating_observation`: frozen 동안 JS diagnostics가 정지하고 server ready deadline/PTY drain은 계속되며 active 복귀 후 새 attempt가 시작된다.
- `dependent_work_not_yet_permitted`: frozen 경계를 hidden/rAF override 결과만으로 PASS 처리하거나 실제 Android 절전 성공으로 확대하는 일.
- `response_if_refuted`: CDP capability가 없으면 hidden-but-JS-running 결과만 보존하고 E3 frozen evidence를 `EVIDENCE_NEEDED`로 verifier/Main에 반환한다. client에 가짜 timer 진척을 넣지 않는다.

### 9.2 known B5 defect 격리

- `plan_anchor`: §2.3, §6.1.
- `permitted_initial_work`: 각 fixture output을 8 MiB 미만, retained count 1 미만의 안전 범위로 제한하고 sanitizer/diagnostic에서 unexpected lifetime fault를 감시한다.
- `discriminating_observation`: B4 사건 중 `send_position < output_start`, retained pruning, reaper 경합/UAF가 발생하지 않고 PTY/process identity가 끝까지 판독된다.
- `dependent_work_not_yet_permitted`: 이 제한 결과를 ring/reaper/pruning 해결이나 일반 운영 안전으로 주장하는 일.
- `response_if_refuted`: 알려진 B5 결함이 B4 path에서 발생하면 B4 Exit를 중단하고 Main이 BLOCK 순서/원자 경계를 재정합화한다. B4 코드에서 임시 숨김이나 무관 lifetime patch를 덧대지 않는다.

다음은 implementer 재량이다: private helper 이름, 동일 wire 계약을 유지하는 local struct 배치, 진단 event 이름, test utility 내부 구성. 다음 변경은 Plan 재검토가 필요하다: token rotation/idempotency 방식, lease/phase owner, storage 승인 시점, parser barrier 적용 소유자, ready deadline 값, CAS/readback 방식, OUTPUT frame layout. 제품 의미·Scope acceptance·Block 순서를 바꾸려면 Plan이 아니라 Main의 Thesis/Baseline/Scope 정합화로 돌아간다.

## 10. Acceptance 추적과 최종 handoff

| Exit | 구현 anchor | 최소 실제 판독 |
|---|---|---|
| B4-E1 | §4.2~4.4, §5.2~5.3, §6.2 | v4 approved/pending binding, same PTY, new epoch, old Ping 없음, old epoch frame 무효, version mismatch, response-drop 수렴, raw token 비기록 |
| B4-E2 | §4.4~4.5, §5.2, §6.3 | immediate CONFLICT, observed epoch CAS, STALE, old-close success, one owner, SUPERSEDED/BUSY, finite provisional deadline |
| B4-E3 | §5.4B/C, §6.4 | no-rAF fallback/last geometry HELLO, real parser ACK, visible ResizeObserver correction, frozen server progress/thaw, hidden-excluded budget |
| B4-E4 | §4.1/4.6, §5.2/5.4A, §6.5 | epoch/range wire order, parser callback target, READY_ACK-before-input, explicit NACK, old epoch rejection, GAP blocks false Ready |
| B4-E5 | §5.4D, §6.6 | retained local settle, preempt during/after replay, approval-before-reset, first-byte ordering, new PTY input, rejection preservation, same-session no-reset |
| B4-E6 | §5.4C, §6.7 | real AbortSignal settlement in four waits, latest intent, late callback no effect, gesture PTY 0 bytes, blocked input no later replay |

구현자 self-check 결과는 exact source/binary/bundle hashes, isolated command/env/port, six scenario result, wire/server/parser/PTY evidence path, cleanup result, 미관찰 경계를 포함한다. Scope는 `ready`로 유지하며 구현자가 `done`/VERIFIED를 쓰지 않는다. 독립 verifier가 같은 stable candidate에서 B4-E1~E6을 판정하고, Main이 별도 Production Heuristic Probe와 후속 권한을 소유한다.
