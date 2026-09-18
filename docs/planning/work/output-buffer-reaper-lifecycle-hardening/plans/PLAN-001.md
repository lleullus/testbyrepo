# PLAN-001 — BLOCK-005 출력 버퍼·Reaper·세션 수명 안전성 실행 방법

- Project Root: `/home/user01/project/webterm/ttyd-1.7.7` (이하 경로는 이 루트 기준).
- 대상 Scope: `docs/planning/work/output-buffer-reaper-lifecycle-hardening/SCOPE.md`, SHA-256 `0505e7837cc5546cb9616492a5f2dc63f289088805514edf026e8f22508298fd`, `Schema: iis-scope/v1`, `Status: ready`.
- Product Authority: `docs/planning/product-thesis/android-web-terminal/THESIS-002.md`, SHA-256 `3ac3c25dd0e520e0af1269dd5de32b100400b86872e76ec2704d9d9b22a0e067`.
- Transition Authority: `docs/planning/baseline/BASELINE-002.md`, SHA-256 `285004a80d06ef8ac794513c10af08056d1ed94f992bbe7d2f2041523e9039f5`; 이 Plan은 Scope가 선택한 `BLOCK-005`와 B5-E1~B5-E6만 적용한다. Baseline의 `DRAFT` 표기와 해시는 그 자체로 실행·배포 승인이 아니다.
- 조사 원본: `/tmp/oracle-findings-and-investigation.md`, SHA-256 `d09035efe52fe103720832295e1ae5065096e953748c7e33029e8106540d68bd`.
- 작성 상태: 독립 Plan Review 대기. 이 문서는 구현 방법이며 ADMIT, 구현 완료, 검증 성공, Scope 완료 또는 운영 배포 판정이 아니다.
- 권한 한계: 이 단계에서는 이 Plan만 작성한다. 제품 소스·빌드 산출물·격리/운영 프로세스·포트 7683·Funnel·사용자 세션을 변경하지 않는다.

## 1. 결속 결과와 증거 경계

정확한 Scope는 canonical validator `scope-shaper/tools/validate_scope.py --json <absolute SCOPE.md>`에서 `status: ready`, 위 Product/Transition Authority 경로와 해시 일치로 `VALID` 판독되었다. 세 원본 해시는 현재 바이트 식별일 뿐 제품 동작, Baseline 실행 승인 또는 BLOCK-006 계속 권한을 증명하지 않는다.

BLOCK-005의 결과는 같은 안정 후보의 서버와 클라이언트에서 다음 여섯 경계를 함께 닫는 것이다.

1. 실제 8,388,608-byte bounded chunk ring이 sliding `memmove`를 대체하고, 단절·slow·PAUSE 중에도 PTY read를 멈추지 않으며 최신 tail을 보존한다.
2. 송신 cursor가 보존 시작점보다 뒤처지면 정상 종료나 빈 출력으로 취급하지 않고 정확한 `BUFFER_OVERRUN` 범위를 고지하여 옛 barrier를 폐기하고 새 rebase/barrier로 수렴한다.
3. root child의 wait 결과는 한 경로만 소유하며, session/process/viewer/timer/reaper의 마지막 비동기 참조 전에는 어떤 allocation도 해제하지 않는다.
4. retained 상한 N은 N개를 허용하고, 초과 상태에서도 exit callback·viewer·9시간 보호 결과를 dangling pointer로 제거하지 않는다.
5. write 실패, fragmented message, recovery admission, timer 실패와 control-frame 이후 pending work가 모두 유한하고 정직한 상태로 정착한다.
6. EOF, root status, final PTY bytes, descendant tree와 모든 handle/ref 종료를 각각 판독하고 실제 회수 완료 전에는 `PURGED`를 선언하지 않는다.

검증은 실제 격리 ttyd 바이너리, 실제 libwebsockets 연결, 실제 PTY child, 실제 서빙 bundle과 xterm parser callback, 실제 `/proc` PID/starttime 및 libuv close를 통과해야 한다. source 문자열 검색, ACK mock, seeded ready 상태, kill 반환값, session 목록 삭제, HTTP 200, WebSocket OPEN, exit 0 하나 또는 sanitizer 정상 종료 한 번은 Exit 증거가 아니다. TCP proxy는 실제 연결의 RST/blackhole/frame 순서를 만드는 보조 fault injector이며 서버·PTY·parser를 대체하지 않는다. test-only timer failpoint는 오류 반환 뒤의 상태 보존 분기만 판독하고 실제 libuv 성공 경로·process 회수 증거를 대체하지 않는다.

## 2. Scope 경계와 보존 조건

### 2.1 포함

- THESIS-002 NB2, NB9, NB11, NB15, NB16, NB18, NB19와 I3~I5, I7, I9~I11 중 BLOCK-005에 귀속된 output, GAP, lifecycle, retention, admission 경계.
- BASELINE-002 R3, R5, R6, R7, R8와 B5-E1~B5-E6, ST4, ST5, ST7, ST8, ST10, ST14, ST15, ST16.
- `src/protocol.c`의 output storage/send, session state/ref, expiry/reaper/pruning/admission/reassembly와 `src/pty.c`의 wait/EOF/final close 순서.
- `html/src/components/terminal/xterm/index.ts`의 GAP/rebase, degraded UI, barrier와 input gate.
- 같은 최종 후보를 대상으로 하는 `staging/check_block005.py`와 B4 회귀 판독.

### 2.2 반드시 보존할 동작

- v4 `SESSION_ACCEPTED → OUTPUT → REPLAY_END → REPLAY_APPLIED → READY_ACK`와 session/lease epoch fencing을 유지한다.
- 연속적인 동일 세션 resume은 terminal을 reset하지 않는다. GAP은 화면 완전 복원을 주장하지 않고 degraded 상태를 유지한다.
- gap/recovery/[불완전한 화면에서 계속] 동작은 PTY에 0 bytes를 보낸다. blocked key를 저장했다가 ACK 뒤 전송하지 않는다.
- detached root exit는 기존 disconnect deadline을 유지하고, attached root exit는 종료 관찰 시점부터 기본 32,400초 보존을 시작한다. retained 열람은 deadline을 연장하지 않는다.
- 기존 모바일 focus/IME/toolbar 의미와 B4 token/lease/ready/NACK 계약을 회귀시키지 않는다.
- 모든 crash/race/대량 출력 시험은 임의 free port, temporary HOME/profile, 자기 소유 process tree에서만 수행한다. 운영 7683 및 기존 세션은 건드리지 않는다.

### 2.3 제외

- 실제 Android 기기·Tailscale Funnel·systemd/logrotate·운영 7683 cutover, 전체 ST1~ST17 최종 인수와 `CUSTOMIZATION.md` 최종화(BLOCK-006).
- durable detached-session discovery, terminal snapshot, 서비스 재시작 간 session 영속성, 외부 인증 추가.
- Windows process-tree 의미 확대. 이번 wait/reaper 판독은 Thesis가 결속한 Linux/WSL2 경계다.
- 8 MiB 이전 출력의 복원. 손실은 고지하고 최신 tail로 재동기화할 뿐 복원했다고 표시하지 않는다.

BLOCK-005는 `HARD_ATOMIC`이다. ring만 바꾸고 GAP consumer를 미완성으로 남기거나, `free` 한 곳만 지우고 process/viewer/timer 참조를 옛 모델에 남기거나, `>=`만 `>`로 바꾸고 보호 자격을 생략한 상태는 개발 중간점일 뿐 완료/배포 경계가 아니다.

## 3. 현재 코드 접지

Plan 작성 시 읽은 load-bearing 원본의 바이트와 관찰은 다음과 같다. 작업 트리에는 선행 BLOCK-004 관련 사용자 변경이 존재하므로 출발 commit으로 되돌리거나 옛 v3 구현을 기준으로 재작성하지 않는다.

| 파일 | SHA-256 | EXISTING 관찰 |
|---|---|---|
| `src/protocol.c` | `df40cb95639bc2e3dd63466964a65889ab57bcc0182e8781fc4839e4df772332` | `tty_session`은 단일 `char *output_buf`, `output_len/cap/start/end`를 가진다(`:38-81`). full buffer에 작은 append가 오면 `memmove(output_len-overflow)` 후 copy한다(`:142-188`). |
| `src/protocol.c` | 위와 같음 | `session_output_pending()`은 `send_position < output_start`를 false로 반환한다(`:136-140`). writable path에 부분적인 `SYNC_REQUIRED/BUFFER_OVERRUN` NACK가 있으나 정확한 누락 범위, rebase 승인, 새 barrier와 degraded continue 계약은 없다(`:1293-1313`). |
| `src/protocol.c` | 위와 같음 | v4 OUTPUT은 64 KiB 단위 frame을 만들고 `lws_write`가 전체 frame 길이와 같을 때만 `send_position`을 증가시키는 부분 교정이 있다(`:1015-1035`). 이 동작을 ring reader와 fault/reconnect 판독까지 결속해야 한다. |
| `src/protocol.c` | 위와 같음 | `session_release()`는 timer close 완료·process/viewer 참조와 무관하게 output/session을 즉시 free한다(`:273-292`). session refcount가 없다. |
| `src/protocol.c` | 위와 같음 | `session_reaper`는 embedded `uv_timer_t`를 갖지만 close callback에서 `free(handle)`하고 timer callback은 `uv_close()` 직후 `free(reaper)`한다. 같은 callback에서 `waitpid(-1)`도 실행한다(`:315-375`). |
| `src/protocol.c` | 위와 같음 | timer init 실패를 곧바로 `PURGED`+release로 바꾸고 `uv_timer_start` 반환은 검사하지 않는다(`:377-419`, `:437-451`). 이는 살아 있는 tree의 회수 완료 증거가 아니다. |
| `src/protocol.c` | 위와 같음 | retained pruning은 `while (retained >= max_retained)`이고 current exit callback/viewer/deadline 자격을 제외하지 않은 채 `session_release(oldest)`를 호출한다(`:654-675`). process exit handler는 그 뒤 같은 session을 계속 사용한다(`:679-738`). |
| `src/protocol.c` | 위와 같음 | admission은 active client와 `output_len`만 중심으로 계상하여 detached/retained/terminating session, allocated chunks, fragmented receive memory를 온전히 반영하지 않는다(`:609-652`). filter 단계 `--max-clients`는 HELLO 전에 신규 socket을 거절한다(`:1153-1162`). |
| `src/protocol.c` | 위와 같음 | fragmented receive는 매 fragment마다 `xrealloc(pss->len + len)`하며 누적 총량/overflow 검사가 없다(`:1318-1346`). writable/control branches의 후속 schedule 규칙도 각 분기에 흩어져 있다(`:1231-1316`). |
| `src/pty.c` | `4d3ff3392548efe3a228ce153a1359c6751ce6df94657fbb1d7e208974722c08` | Linux wait thread는 `waitpid(process->pid, &stat, 0)` 실패 여부를 확정하지 않은 채 `WIFEXITED/WIFSIGNALED(stat)`를 읽고 async callback을 보낸다(`:833-852`). |
| `src/pty.c` | 위와 같음 | async callback은 protocol exit callback 직후 pipe/PTY close를 시작하고 process를 free한다(`:854-860`). root status와 PTY EOF/final drain을 별도 완료로 조정하는 상태가 없다. |
| `src/pty.h` | `a190fcce919a88148fc1640eabcf7d7328f4360eb410e6f2d2a8cabd30c155a5` | `pty_process`에는 wait 성공/errno, EOF, callback/close 단계 필드가 없고 `ctx`는 비소유 raw pointer다(`:29-55`). |
| `src/server.h` | `87a22226766085152f8d02289ce23561b0085bafef2d292a675537a840a62f34` | v4 pss에는 cursor/barrier/pending message와 `char *buffer,size_t len`은 있으나 GAP generation/rebase, fragment rejection, recovery-only slot, session ref 보유 표식이 없다(`:7-35`, `:69-121`). |
| `html/src/components/terminal/xterm/index.ts` | `4ef32e5be983c9d1b12aed2a1ef1eab8c63aaf00b582530084e054b4cd87060b` | OUTPUT range 중복 제거와 local gap 감지는 존재하지만 gap에서 old barrier를 폐기하고 Retry만 표시한다. server range를 합의하여 rebase하거나 불완전 계속 후 새 ACK로 input을 여는 경로가 없다(`:1831-1922`, `:2118-2136`). |
| `html/src/components/terminal/xterm/addons/overlay.ts` | `f615ea66663f49dfd8c3d3376a4f2db3bb6fe072e23a4e20bd0022ecb9593f18` | `showAction`과 `showChoices`가 이미 있어 GAP용 새 UI framework는 필요하지 않다. 기존 선택 UI를 재사용한다(`:83-117`). |
| `src/utils.h` | `97f5179cc7c33dc5e83fc5a28e083b86414a405af700a9b0ad56f2afc9641bd1` | embedded handle에서 parent를 구할 `container_of`가 이미 있다(`:4-8`). 새 macro를 중복 정의하지 않는다. |
| `staging/check_block004.py` | `84affe23f48848bcefdcf09803076d478a5d8eca90156a775c6025cae5c8bb05` | 실제 격리 ttyd/WebSocket/PTY/Chromium fixture와 v4 raw client 패턴이 있다. B5 harness는 이 wire 의미와 cleanup 방식을 재사용하되 B5 결함을 피해 간 옛 결과를 B5 증거로 쓰지 않는다. |

### 3.1 분류

- **EXISTING:** 위 sliding buffer, false pending 판정, reaper double/interior free, competing wait, eager session free, pruning off-by-one/UAF, unbounded fragment와 partial B4 write/NACK/client barrier 구현.
- **PROPOSED:** §4~§8의 fixed 64 KiB chunk ring, GAP/rebase wire와 degraded consent, event-loop-owned session refs, single root waiter, EOF/status finalization, safe reaper close, deletion eligibility, recovery reserve, cumulative message cap, timer-failure state, B5 harness.
- **UNRESOLVED:** 현재 source와 `staging/evidence-block004/result.json`의 binary/bundle이 동일 최종 B5 candidate인지 입증되지 않았다. 실제 B5-E1~E6 runtime evidence와 sanitizer/heap checker 결과도 아직 없다. ASan 가능한 native dependency 환경이 없으면 메모리 안전 PASS로 추정하지 않고 E3/E4의 해당 evidence gap을 남긴다. Android/운영 성공은 B6 경계다.

## 4. 출력 저장소와 GAP/rebase 계약

### 4.1 8 MiB fixed chunk ring

`src/protocol.c`의 `output_buf/output_len/output_cap`을 다음 의미의 `struct output_ring` 하나로 clean cutover한다.

- `OUTPUT_CAPACITY = 8,388,608`, `OUTPUT_CHUNK_SIZE = 65,536`, `OUTPUT_CHUNK_COUNT = 128`을 compile-time assertion으로 결속한다.
- ring은 128개 chunk pointer의 고정 metadata 배열을 갖고 각 64 KiB chunk는 처음 쓰일 때 한 번 할당한다. 최대 payload allocation은 정확히 8 MiB이고 pointer metadata만 별도 유한 비용이다. session final destructor에서 할당된 chunk만 해제한다.
- absolute PTY byte position `p`의 물리 주소는 `p % OUTPUT_CAPACITY`, chunk index와 chunk offset으로 계산한다. wrap된 chunk에는 새 prefix와 아직 보존되는 옛 suffix가 공존할 수 있으나 읽기는 반드시 `[output_start, output_end)` 범위만 허용하므로 generation pinning이 필요 없다.
- append는 먼저 `new_end = output_end + len` overflow를 검사한다. 입력이 cap보다 크면 선두를 버리고 마지막 cap bytes만 복사한다. `new_start = max(old_start, new_end - OUTPUT_CAPACITY)`이고 `dropped_output_bytes += new_start - old_start`다. chunk boundary마다 `memcpy`할 뿐 기존 payload를 이동하지 않는다.
- `output_ring_copy(position, dst, max)`는 유효 범위와 wrap을 확인하고 최대 `SESSION_REPLAY_CHUNK=64 KiB`만 현재 LWS frame payload로 복사한다. raw pointer나 chunk ref를 callback 밖에 보존하지 않으므로 producer가 overwrite를 위해 reader를 기다리지 않는다.
- `session_output_append()`는 파일/소켓 wait, `pty_pause`, viewer flow-control wait를 호출하지 않는다. libuv PTY callback에서 입력 bytes를 bounded ring에 복사하고 원 `pty_buf`를 해제한 뒤 writable만 schedule한다. PAUSE는 WebSocket send만 멈추며 PTY drain은 계속한다.
- `output_start`, `output_end`, `dropped_output_bytes`는 monotonic uint64이며 wrap 전에 해당 session을 명시 오류/종결한다. byte count는 문자/UTF-16 길이가 아니다.

`session_output_pending()`의 bool 의미를 없애고 `OUTPUT_SEND_NONE`, `OUTPUT_SEND_DATA`, `OUTPUT_SEND_GAP`의 판정으로 바꾼다. `send_position < output_start`는 언제나 GAP이며 `REPLAY_END` 조건에 들어갈 수 없다. `send_position == replay_target`이고 target이 현재 보존 범위에서 도달 가능할 때만 replay 종료다.

### 4.2 wire 확장과 정확한 손실 범위

B4 opcode를 호환 유지하면서 다음 두 방향을 추가한다.

| 방향 | opcode | 의미 |
|---|---:|---|
| S→C | `8` | `REPLAY_GAP`: `{version,sessionId,leaseEpoch,syncId,reason:'BUFFER_OVERRUN',lost:{start,end},retained:{start,end},target}` |
| C→S | `7` | `REBASE_ACK`: `{sessionId,leaseEpoch,syncId,rebasePosition}` |

- server가 cursor 추월을 발견한 순간 `lost=[old send_position,current output_start)`, `retained=[output_start,output_end)`, `target=output_end`를 한 event-loop turn에서 snapshot한다. `syncId`를 증가시키고 `input_ready=false`, `replay_end_sent=false`, `gap_pending=true`로 만든 뒤 GAP을 full write한다. 누적 `dropped_output_bytes`는 별도 diagnostics이며 이번 `lost` 범위를 대신하지 않는다.
- GAP full write 전후에 `send_position`을 조용히 `output_start`로 올리지 않는다. client의 정확한 `REBASE_ACK`가 와야 `send_position=rebasePosition`, `replay_target=현재 보존 end snapshot`, 새 replay generation이 시작된다.
- ACK가 stale session/epoch/syncId이거나 rebasePosition이 제안된 retained start와 다르면 명시 NACK하고 cursor를 바꾸지 않는다.
- rebase replay 중 생산자가 다시 추월하면 이전 syncId/target을 폐기하고 더 최신 GAP을 보낸다. 이전 target의 `REPLAY_END`는 금지한다. 반복 overrun은 새 GAP와 “출력이 계속 손실되고 있음” 상태, Retry/Start New Session 선택으로 정착하며 spinner만 남기지 않는다.
- `lws_write`가 frame 전체 길이를 반환한 경우에만 OUTPUT payload 길이만큼 `send_position`을 전진한다. 0/음수/short write에서는 cursor와 barrier를 그대로 두고 connection failure로 정착시킨다. successor는 마지막 parser-applied/rebase position에서 다시 요청하므로 미송신 bytes를 잃지 않는다.
- `REPLAY_END.target`은 해당 sync generation에서 실제 full-write된 OUTPUT의 마지막 위치와 같아야 한다. GAP pending 또는 `send_position < output_start`에서는 전송하지 않는다.

### 4.3 클라이언트 rebase와 degraded input gate

`xterm/index.ts`는 현재 `appliedPosition` 하나에 손실과 parser 적용을 섞지 않도록 current sync generation과 gap record를 추가한다.

1. `REPLAY_GAP`의 version/session/epoch/range/syncId를 검증한다. current barrier를 abort하고 `inputReady=false`, `flowPausedGeneration`과 old replay target을 폐기한다. stale GAP은 current attempt를 변경하지 않는다.
2. `lost.end == retained.start`, `lost.start <= lost.end`, `retained.start <= retained.end`, target 범위가 맞을 때만 explicit rebase를 수행한다. `replayPosition`을 retained.start에 놓되 `degradedGap={lost,retained,syncId}`를 반드시 보존하고 diagnostics에 `explicit-rebase`로 기록한다. 이를 parser가 lost bytes를 적용한 것으로 기록하지 않는다.
3. 정확한 `REBASE_ACK`를 즉시 보내 최신 tail replay를 허용한다. terminal은 같은 session이므로 reset하지 않으며, 과거 parser callback은 captured sync generation이 다르면 새 barrier/cursor를 전진시키지 않는다.
4. 새 OUTPUT은 `[start,end)` 연속/overlap/full duplicate 규칙을 그대로 적용한다. 새 `REPLAY_END` 뒤 parser callback이 target에 도달해도 degraded gap이 있으면 곧바로 `REPLAY_APPLIED`를 보내지 않고 persistent 손실 고지와 `[불완전한 화면에서 계속]`, `Retry`, `Start New Session` 선택을 표시한다.
5. 사용자가 `[불완전한 화면에서 계속]`을 선택하면 복구 gesture를 소비하고 PTY bytes는 보내지 않는다. parser가 아직 target 전이면 consent만 기록하고 callback을 기다린다. target 적용 뒤 `REPLAY_APPLIED`에 `syncId`와 `acceptIncomplete:true`를 포함한다.
6. server는 current syncId/target과 consent를 검증한 뒤에만 `READY_ACK(degraded:true,gap:{start,end})`를 보내며, client는 그 새 ACK 수신 후에만 input을 연다. 이 ACK는 화면 완전 복원이 아니라 불완전 상태에서의 제한적 입력 권한이다. 손실 표시는 session이 끝나거나 명시적 새 session이 승인될 때까지 유지한다.
7. Retry는 current attempt를 선점해 보존 범위를 다시 조회하고, Start New Session은 B4의 별도 emulator 경계를 따른다. 둘 모두 blocked key를 나중에 재생하지 않는다.

## 5. 단일 reap 권한과 비동기 수명 모델

### 5.1 root wait의 단일 소유자

Linux root child의 wait 결과 소유자는 `src/pty.c`의 per-process `wait_cb` 하나로 고정한다.

- `session_reaper_timer_cb()`의 `waitpid(-1, WNOHANG)`를 삭제한다. reaper는 저장된 `proc_ident_t(pid,pgrp,starttime)`로 descendant 생존을 판독하고 signal/recheck만 수행한다.
- `wait_cb`는 `int stat = 0`, `wait_result`, `wait_errno`를 분리한다. `waitpid`가 exact root PID를 반환한 때만 `WIFEXITED/WIFSIGNALED`를 해석한다. `-1/ECHILD` 또는 다른 결과는 `exit_status_known=false`, `exit_code=-1`, `wait_error`로 전달하며 exit 0으로 만들지 않는다.
- startup error cleanup에서 해당 code path가 생성한 exact PID만 동기 wait한다. 일반 reaper와 다른 session child에는 `waitpid(-1)`를 사용하지 않는다.
- `pty_process`에 `wait_complete`, `wait_succeeded`, `wait_error`, `pty_eof_observed`, `exit_callback_delivered`, `close_started`를 둔다. wait async와 PTY EOF가 모두 event loop에 관찰된 뒤에만 process pipes/PTY/async close를 시작한다.

### 5.2 final output과 root status의 분리

- `process_exit_cb()`는 root status를 기록하지만 즉시 `session->process=NULL`, viewer close 또는 session free를 하지 않는다.
- `process_read_cb(..., eof=true)`는 최종 read가 모두 append된 뒤 `pty_eof_observed=true`를 기록한다. EOF가 먼저 와도 exit code를 0으로 추정하지 않는다.
- `session_maybe_finalize_exit()` 하나가 `root_exit_observed && pty_eof_observed`를 확인해 EXITED_RETAINED read-only 결과를 publish한다. status가 unknown이면 JSON/UI에 `exitStatusKnown:false`를 보내고 “종료 코드 0”으로 표시하지 않는다.
- root가 attached 상태에서 종료되면 root exit 관찰 시점에 32,400초 result deadline을 고정한다. detached였다면 기존 `expiry_deadline_ms`를 유지한다. EOF/finalization이나 viewer 열람은 deadline을 다시 시작하지 않는다.
- descendant가 slave PTY를 잡고 있어 EOF가 늦어지는 동안에도 read drain은 계속되고 session/process ref는 유지된다. expiry가 먼저 오면 TERMINATING/reaper가 tree를 회수하며, EOF와 root status가 모인 뒤 final ref를 정리한다.

### 5.3 session refcount와 소유 참조

`tty_session` refcount는 libuv event loop thread에서만 증감한다. wait thread는 session을 만지지 않고 `pty_process`와 `uv_async_send`만 사용하므로 atomic refcount를 추가하지 않는다.

- `session_create()`는 registry/list ownership 1 ref로 시작한다.
- `pss->session`을 설치할 때 viewer ref를 acquire하고, fence/close에서 양방향 pointer를 먼저 끊은 뒤 정확히 한 번 unref한다. `session->client` raw back-reference는 별도 ref가 아니다.
- `process->ctx=session` 설치는 process-lifecycle ref를 acquire한다. root status와 PTY EOF가 모두 처리되어 ctx를 NULL로 바꿀 때 unref한다.
- expiry/ready timer context는 각각 session ref와 captured lease/deadline을 소유한다. cancel은 handle을 close할 뿐 ref는 close callback에서 놓는다.
- `session_reaper`는 session ref 하나를 소유하며 reaper close callback에서 놓는다.
- registry unlink는 state를 TERMINATING/PURGED로 옮기고 registry ref를 놓는 연산이다. 실제 `output_ring`과 session allocation destructor는 refcount 0이며 모든 handle context가 닫힌 마지막 시점에만 실행한다.
- 현재 `session_release()` 이름은 `session_unref()`/`session_destroy_final()`로 분리하고 모든 caller를 이행한다. eager-free 호환 alias를 남기지 않는다.
- diagnostics에는 ref total과 registry/process/viewer/expiry/ready/reaper ownership bit를 비밀 없이 기록하여 마지막 해제의 원인을 판독한다.

### 5.4 `session_reaper` close와 실패 의미

- `session_reaper_timer_cb()`에서는 `free(reaper)`를 호출하지 않는다. 완료/실패 후 `uv_timer_stop`과 `uv_close(&reaper->timer, session_reaper_close_cb)`만 정확히 한 번 수행한다.
- close callback은 `container_of((uv_timer_t *)handle, struct session_reaper, timer)`로 allocation 시작 주소를 복원한다. 여기서 idents를 해제하고 session ref를 unref한 뒤 parent reaper를 한 번만 free한다. `free(handle)`은 금지한다.
- reaper timer init 실패는 handle이 초기화되지 않았으므로 parent/id list와 reaper-owned ref만 정상 반환하되 session을 `TERMINATING`+`reap_failed`로 유지한다. timer start 실패는 initialized handle을 close callback으로 닫고 같은 실패 상태를 남긴다. 두 경우 모두 `PURGED`/registry 삭제를 하지 않는다.
- 정상 흐름은 SIGHUP → configured finite grace → 살아 있는 saved identity에 SIGKILL → finite recheck다. PID 숫자만 보지 않고 `/proc/<pid>/stat` starttime까지 일치하는 `proc_ident_t`만 signal한다.
- `PURGED`는 tree identities 부재, root wait 결과 관찰(성공 또는 명시 unknown), PTY/FD close, process ctx release, expiry/ready/reaper handle close, viewer ref 0이 모두 충족된 뒤에만 기록한다. 미확인 항목이 하나라도 있으면 `TERMINATING/reap_failed`다.

## 6. Retained pruning, admission과 유한 자원

### 6.1 deletion eligibility와 정확한 N

`prune_retained_sessions(max_retained, protected_session)`는 다음 순서를 따른다.

1. EXITED_RETAINED 수를 센 뒤 `while (retained > max_retained)`만 실행한다. 0/1/N 바로 아래와 정확히 N은 삭제하지 않는다.
2. candidate는 oldest-first이되 `s != protected_session`, `!s->process_exit_active`, `s->client == NULL`, viewer ref 0, expiry/ready/reaper callback ref 없음, 삭제 자격(`expiry_deadline` 경과 또는 명시적 종료)이 모두 참이어야 한다.
3. 초과 상태 자체는 삭제 자격이 아니다. 9시간 보호 중인 결과나 현재 callback/viewer밖에 없으면 pruning을 멈추고 over-capacity를 명시 계상한다. 후속 create는 `rejected_capacity`로 거절하되 기존 결과를 지우지 않는다.
4. 만료로 viewer를 분리해야 하면 먼저 `input_ready=false`, current lease fence와 `expired/terminating` state를 full write/schedule하고 `pss->session/process`를 끊는다. LWS close callback이 viewer ref를 반환한 뒤에만 session final free가 가능하다.
5. process exit callback은 진입 시 `process_exit_active=true`, 모든 state/deadline/prune 판단이 끝난 단일 exit path에서 false로 바꾼다. refcount가 memory를 지키고 eligibility flag가 같은 callback 대상의 semantic 삭제를 막는다.

### 6.2 session/transport admission

- `TTYD_MAX_SESSIONS`는 active viewer 수가 아니라 ACTIVE, DETACHED_GRACE, EXITED_RETAINED, TERMINATING을 포함한 live session allocation 수에 적용한다. 정상 capacity 압박은 create 거절이며 기존 session expiry 단축이 아니다.
- `TTYD_MAX_TOTAL_BUFFER_BYTES`는 ring의 실제 allocated chunks, 모든 pss receive reassembly bytes와 bounded pending frame bytes를 계상한다. output payload logical length만 세지 않는다.
- `TTYD_MAX_RETAINED_SESSIONS` default 16은 정확히 16개를 허용한다. running session이 나중에 동시에 exit하여 일시 초과할 수 있으나 보호 결과를 조기 삭제하지 않고 신규 create를 거절한다.
- `--max-clients`에 도달한 half-open owner가 valid successor HELLO 자체를 막지 않도록 recovery-only reserve를 정확히 1 slot 둔다. 총 transport는 `max_clients + 1`을 넘지 않는다.
- reserve pss는 5,000 ms 안에 authenticated v4 HELLO를 보내야 하며 `intent=resume`, existing session, same logical client, valid current successor credential인 경우만 grant한다. create/unknown/invalid contender는 명시 `rejected_capacity` 후 close한다. 성공 successor가 old pss를 fence해 regular slot을 반환한다. reserve를 일반 client 증가나 무제한 queue로 쓰지 않는다.

### 6.3 fragmented message cap

- `CLIENT_MESSAGE_MAX = 1,048,576 bytes`를 `server.h`에 정의한다. 기존 64 KiB paste를 충분히 수용하면서 한 connection이 무한히 재조립하지 못하게 하는 fixed default다.
- 매 fragment append 전에 `len > MAX` 또는 `pss->len > MAX - len`을 검사한다. 검사 전에는 `xrealloc`하지 않는다.
- 초과 시 buffer를 해제하고 `fragment_rejected=true`, current accepted session이면 `SESSION_NACK(code='MESSAGE_TOO_LARGE',retryable:false)`, pre-HELLO면 WebSocket close code 1009를 보낸 뒤 close한다. 해당 connection의 later fragment를 parse하지 않는다.
- final fragment에서만 command parser를 호출하고 처리 후 `buffer=NULL,len=0`으로 한 번 정리한다. 정상 64 KiB binary paste와 작은 JSON control은 실제 PTY/wire로 보존한다.

### 6.4 timer/control-frame/write 후속 scheduling

- 모든 `uv_timer_init/start` 반환을 검사한다. expiry 실패는 TERMINATING/reap_failed 추적, ready deadline 실패는 provisional grant 실패/fence, reaper 실패는 살아 있는 tree 추적 유지로 귀결한다. 요청 로그나 timer pointer 존재만 성공이 아니다.
- writable callback 끝에 `pss_has_pending_work()`를 한 번 호출하여 heartbeat reply, NACK, READY_ACK, state update, eligible output 중 하나라도 남으면 다음 writable을 schedule한다. 각 branch에서 우연히 재-schedule하는 규칙을 중복하지 않는다.
- `LWS_CALLBACK_RECEIVE_PONG` 및 사용 중인 Ping/Pong/control callback 뒤에도 같은 helper를 호출한다. control frame 우선 처리 뒤 heartbeat reply/state/output이 다른 입력을 기다리지 않는다.
- exact full write가 아닌 command/state/ACK도 성공 state를 commit하지 않는다. READY_ACK write 실패는 token/phase/input gate를 열지 않고, GAP/state write 실패는 cursor/rebase를 commit하지 않는다.

## 7. 파일별 구현 명세

### 7.1 `src/server.h`

1. output capacity/chunk/message cap/recovery reserve와 GAP/REBASE opcode를 방향별로 정의한다.
2. `pss_tty`에 `sync_id`, `gap_pending`, offered lost/retained ranges, rebase generation, degraded consent/barrier state, fragment rejected, recovery-only slot 보유, session viewer-ref 보유 표식을 추가한다.
3. `tty_session` forward pointer를 계속 사용하되 pss와 session의 ref 소유 규칙을 주석으로 명확히 한다.
4. v4 old opcode alias나 silent fallback을 추가하지 않는다.

### 7.2 `src/protocol.c`

1. single sliding buffer를 §4.1 ring helper로 교체하고 append/send/diagnostics/admission/release caller를 모두 이행한다. obsolete `output_buf/output_cap` path를 삭제한다.
2. output disposition enum과 GAP snapshot/send/rebase validate helper를 추가한다. writable 우선순위는 close → protocol reply/state → GAP → OUTPUT → reachable REPLAY_END이고, 각 full write 뒤 pending work를 재-schedule한다.
3. GAP payload range와 syncId를 session/lease에 귀속한다. ACK 전 cursor jump, GAP 중 END, old sync ACK, cumulative dropped를 current gap으로 재사용하는 경로를 금지한다.
4. `session_ref/session_unref/session_destroy_final`, viewer/process/timer/reaper ownership helpers와 diagnostics를 구현한다. 모든 raw `session_release()` caller를 제거한다.
5. expiry/ready timer를 session-ref-owning context로 바꾸고 init/start/close 반환과 captured generation을 처리한다.
6. reaper에서 `waitpid(-1)`, timer callback free, close callback interior free를 제거하고 existing `container_of`를 사용한다.
7. lifecycle flags와 `session_maybe_finalize_exit/purge`를 한 곳에 두어 EOF/status/final bytes/tree/refs를 조합한다. exit code unknown을 별도 상태로 serialize한다.
8. pruning eligibility와 protected current session을 구현하고 admission 계상을 전체 live states/allocated memory로 바꾼다.
9. filter/established/HELLO/close에서 recovery reserve 1 slot과 5초 deadline을 정확히 반환한다.
10. fragment 누적 overflow/cap을 allocation 전에 거절하고 close/NACK를 명시한다.
11. diagnostics에는 output start/end/chunk count/allocated bytes, current GAP range/syncId, root wait known/error, EOF, tree count, refs/handle ownership, retained/admission counts를 기록하되 token·사용자 input bytes는 기록하지 않는다.

### 7.3 `src/pty.h`, `src/pty.c`

1. wait result와 EOF/close state 필드를 추가하고 root wait 성공 때만 status를 해석한다.
2. wait thread는 session pointer를 읽거나 release하지 않는다. exact root PID 하나만 기다린 뒤 status/error를 process에 기록하고 async를 보낸다.
3. async exit callback과 PTY read EOF callback을 별도 사실로 protocol에 전달한다. 둘이 모두 관찰되기 전에 process/PTY output handle을 free하지 않는다.
4. process close는 한 helper에서 한 번만 시작하고, uv pipe/async close callback이 모두 끝난 뒤 process allocation을 해제한다. session ctx는 protocol이 두 lifecycle 사건을 처리한 뒤 NULL로 만든다.
5. spawn failure cleanup의 exact child kill/wait와 정상 runtime reaper를 구분한다.

### 7.4 `html/src/components/terminal/xterm/index.ts`

1. `Command.REPLAY_GAP`, `Command.REBASE_ACK`, `GapRecord`/sync generation/degraded consent를 추가한다.
2. server GAP와 local OUTPUT `start > applied`를 같은 sync-required entry로 수렴시킨다. local gap도 server에 상태를 요청하고 old barrier/input을 폐기하며 조용히 cursor를 올리지 않는다.
3. exact GAP에서 rebase ACK, new range dedupe/parser callback, persistent loss UI, explicit continue, consent-bearing REPLAY_APPLIED, degraded READY_ACK 순서를 구현한다.
4. old parser callback/GAP/END/ACK는 session+lease+terminal epoch+sync generation이 current일 때만 cursor/barrier/input을 바꾼다.
5. `[불완전한 화면에서 계속]`은 focus를 열거나 PTY input을 만들지 않는다. ACK 전 `sendData()`는 계속 false이고 blocked input queue는 만들지 않는다.
6. 같은 session GAP에서는 terminal reset을 호출하지 않는다. 화면 완전성 표시는 새 session 승인 또는 별도 입증 없이 지우지 않는다.

`overlay.ts`는 기존 `showChoices()`가 필요한 UI를 제공하므로 새 abstraction을 만들지 않는다. 실제 접근성/label 표현에 필요한 최소 변경만 허용한다.

### 7.5 `staging/check_block005.py`

새 standalone script를 작성하되 `check_block004.py`의 실제 fixture/wire/Chromium/cleanup pattern을 재사용한다. 제품 코드를 import하거나 canned protocol server를 만들지 않는다.

- 입력: `TTYD_BIN`(기본 `build/ttyd`), `WEBTERM_TEST_INDEX`(기본 `html/dist/inline.html`), 선택 `TTYD_ASAN_BIN`, `WEBTERM_EVIDENCE_DIR`.
- 각 `test_b5_e1`~`test_b5_e6`은 fresh free port, temporary HOME/profile, fresh session IDs, 자기 소유 ttyd/process tree를 사용한다.
- `WireClientV4`는 real HELLO/OUTPUT/GAP/REBASE/END/APPLIED/ACK/NACK를 기록하고 payload bytes를 원 fixture와 비교한다.
- `TcpFaultProxy`는 실제 socket RST/blackhole/control frame을 만들고 frame을 관찰할 뿐 성공 frame을 생성하지 않는다.
- `ChromeCdp`는 실제 served bundle에서 overlay label, xterm parser callback, current state와 input gate를 읽는다.
- child fixture는 deterministic 10 MiB bytes, completion file, PID/starttime, stdin capture, exit status와 descendant behavior를 제공한다.
- 결과 `staging/evidence-block005/result.json`은 schema `block005-self-check/v1`, source/binary/bundle hashes, candidate command/env/free ports, sanitizer capability, B5-E1~E6 evidence, OS identity/readback, cleanup와 명시 limits를 기록한다. raw token과 사용자 input payload는 기록하지 않는다.

## 8. `staging/check_block005.py` 여섯 시나리오

### 8.1 B5-E1 — 10 MiB drain, exact tail, ring bound, replay/live overrun

1. 실제 PTY child가 CR/LF 변환 영향을 피한 deterministic binary pattern 10 MiB+final marker를 `os.write`로 내고 owned completion file을 만든다.
2. viewer를 PAUSE하거나 disconnect한 채 child completion file이 유한 시간 안에 생기고 server `pty_output_bytes`가 전체 입력에 도달하는지 확인한다. client flow-control 때문에 PTY가 paused되면 실패다.
3. diagnostics에서 logical payload `output_end-output_start == 8,388,608`, allocated chunks ≤128, allocated payload ≤8 MiB, dropped bytes와 start/end가 원 fixture 계산과 같은지 확인한다.
4. reconnect/rebase 뒤 받은 payload를 fixture의 마지막 8,388,608 bytes와 byte-for-byte 비교하고 final marker를 확인한다. exit 0이나 marker 하나만으로 tail 보존을 대신하지 않는다.
5. replay 중 overrun과 READY→PAUSE→RESUME overrun을 각각 만들어 GAP 뒤 최신 출력이 다시 진척되는지 확인한다. producer는 두 경우 모두 완주해야 한다.
6. source/binary identity와 ring diagnostics를 결합하여 full-buffer append마다 8 MiB payload 이동이 없음을 판독한다. 이름만 ring이거나 runtime이 sliding storage를 사용하면 실패다.

### 8.2 B5-E2 — GAP range, reachable barrier, degraded UI, write truth

1. raw client가 오래된 position을 가진 채 10 MiB 출력 뒤 resume하여 `lost=[requested,output_start)`, retained start/end, target이 정확한 GAP을 받는지 확인한다. old syncId의 `REPLAY_END`가 GAP 전후에 없음을 wire 순서로 확인한다.
2. REBASE_ACK 뒤 OUTPUT ranges가 retained start부터 연속이고 새 END target이 실제 마지막 full-write 위치인지 확인한다. 중복 full frame, overlapping prefix, 완전 중복을 전달해 client가 suffix만 한 번 적용/완전 중복 무시하는지 본다.
3. 실제 browser를 proxy로 disconnect한 동안 같은 PTY에 10 MiB를 발생시키고 복귀시켜 loss 고지와 `[불완전한 화면에서 계속]`을 확인한다. 선택 전 실제 key event의 PTY capture는 0 byte다.
4. tail parser callback 완료와 button 선택 중 어느 것이 먼저 와도 consent-bearing APPLIED가 한 번만 전송되고 새 ACK 뒤의 명시 입력만 PTY에 한 번 도착하는지 확인한다. button 자체는 PTY 0 bytes다.
5. 실제 transport를 RST/close하여 OUTPUT write 실패를 만들고 successor가 마지막 parser-applied position에서 같은 byte stream을 복구하는지 확인한다. server cursor가 실패 frame 끝으로 앞서면 실패다.
6. short-write 분기는 exact-length commit invariant를 targeted instrumentation으로 판독하되 이것만으로 실제 transport failure 회복을 대체하지 않는다. 환경에서 실제 short write를 만들 수 없으면 그 한계를 evidence에 남기고 RST real path와 source invariant를 구분한다.
7. UTF-8/escape 중간에서 retained start가 시작되는 fixture는 화면 불완전 표시를 유지하고 완전 복원을 주장하지 않는다.

### 8.3 B5-E3 — single wait owner, reaper/exit/uv-close race, ref lifetime

1. ASan/UBSan 가능한 별도 native candidate 또는 동등한 heap checker에서 short grace/reap grace로 실제 root exit, expiry, delayed PTY EOF, reaper timer와 viewer close를 반복 경합시킨다.
2. root는 명시 exit code 23 또는 signal로 끝나고 descendant는 잠시 PTY를 보유한다. logs/state에서 root PID의 wait owner가 하나, `waitpid(-1)` event가 0, ECHILD/실패가 exit 0으로 변하지 않는지 확인한다.
3. timer close 전에 reaper parent가 free되지 않고 close callback에서 parent allocation이 한 번만 해제되는 ref/close event sequence를 확인한다.
4. process callback, PTY EOF, viewer close, expiry/ready/reaper handle이 서로 다른 순서로 끝나는 변형에서 session final free가 마지막 ref 뒤 한 번만 발생하는지 확인한다.
5. unrelated live session을 같은 server에 두고 race 뒤에도 PID/PTY/input/output이 유지되는지 확인한다. broad reap이나 crash가 다른 child를 수거하면 실패다.
6. 실제 descendant PID/starttime과 PTY/FD 소멸을 확인하고, 남아 있으면 `TERMINATING/reap_failed`여야 한다. sanitizer clean 한 번만으로 tree 회수를 대신하지 않는다.

### 8.4 B5-E4 — retained 1/N, protected callback/viewer, fenced release

1. `TTYD_MAX_RETAINED_SESSIONS=1`에서 0, 정확히 1, 2로 증가하는 실제 exit를 만든다. 1에서 pruning이 없고 result/viewer가 그대로 읽히는지 확인한다.
2. session B의 process exit callback이 진행되는 동안 A retained viewer를 연결한 채 count 2를 만든다. current B와 viewer A 어느 쪽도 free/dangling되지 않고 양쪽 state/output을 계속 판독해야 한다.
3. 두 결과가 모두 9시간 보호 자격이면 over-capacity를 기록하고 새 create를 `rejected_capacity`로 거절해야 하며 임의 결과 삭제로 count를 맞추면 실패다.
4. short test deadline의 별도 fixture에서 A가 실제 expiry 자격을 얻고 viewer에 expired/terminating 통지와 fence가 도착한 뒤 socket/session ref가 끝나는 순서를 확인한다. 그 후에만 A allocation/tree가 해제되고 retained count가 1로 수렴한다.
5. N>1 variant에서도 below/equal/above와 oldest eligible 선택을 반복하고, diagnostics allocated buffer/session/refs가 실제 process/viewer와 일치하는지 본다.

### 8.5 B5-E5 — bounded successor admission, fragment/timer/control scheduling

1. `--max-clients=1` owner를 proxy에서 half-open으로 만든 뒤 recovery reserve를 통해 valid successor HELLO를 보낸다. 총 transport가 2를 넘지 않고 same PTY/new epoch로 유한 시간 안에 인계되며 old socket Pong을 기다리지 않는지 확인한다.
2. reserve에서 create/unknown/invalid token을 보내면 `rejected_capacity` 후 close되고 process spawn count가 늘지 않는다. reserve timeout 뒤 slot이 반환되는지도 확인한다.
3. 실제 fragmented WebSocket으로 정상 64 KiB INPUT/paste를 여러 frame에 나누어 보내 PTY에 정확히 한 번 도착시킨다. 별도 connection에서 총 1 MiB를 1 byte 초과하여 NACK 또는 close 1009를 받고, parser/PTY 전달 0, receive allocation high-water ≤ cap인지 확인한다.
4. test-only timer failpoint로 expiry init/start와 reaper start 오류를 각각 발생시켜 handler가 `TERMINATING/reap_failed`, identity/ref 보존, no PURGED를 기록하는지 확인한다. 이 결과는 libuv 오류 처리 분기 증거이며 정상 실제 timer/reaper run도 같은 scenario에서 별도로 실행한다.
5. pending heartbeat reply/state/output이 있는 상태에서 실제 Ping/Pong control frame을 처리하고 추가 application input 없이 다음 writable에서 pending work가 유한 시간에 전송되는지 wire로 확인한다.

### 8.6 B5-E6 — EOF/status/final/tree ordering, deadlines와 실제 PURGED

1. **root-first variant:** root가 marker와 exit 23을 남긴 뒤 descendant가 PTY slave를 보유하고 늦은 final marker를 출력한다. root status가 먼저 도착해도 두 marker와 exact code가 retained 결과에 있고 EOF 전 조기 close/PURGED가 없어야 한다.
2. **EOF-first/unknown variant:** root가 stdio를 닫고 잠시 뒤 종료하거나 wait failure를 식별 가능한 조건으로 만들어 EOF와 status 순서를 뒤집는다. status 미확인은 `exitStatusKnown:false`이며 0으로 표시하지 않는다.
3. detached session은 disconnect 때 기록된 deadline이 root exit/retained view로 바뀌지 않고, attached exit는 exit 시점+32,400초 default를 기록한다. 실제 expiry behavior는 short isolated grace로 판독하며 이를 실제 9시간 경과 관찰로 주장하지 않는다.
4. expiry/resume를 같은 경계에 경쟁시켜 captured timer generation이 새 owner를 죽이지 않고 하나의 ACTIVE 또는 TERMINATING 결과로 수렴하는지 확인한다.
5. SIGHUP→finite wait→SIGKILL 뒤 descendant/root PID+starttime 부재, PTY/FD close, wait status, uv handle close, ref zero를 모두 읽은 뒤에만 PURGED가 나타나는지 확인한다. signal/kill 반환이나 tombstone만으로 통과하지 않는다.
6. 같은 binary/bundle hash로 `check_block004.py` B4-E1~E6을 다시 실행하여 token/ready/retained/manual recovery 의미가 B5 수명 변경 뒤 보존되는지 확인한다.

## 9. 단계별 구현 순서와 gate

아래 단계는 하나의 HARD_ATOMIC Scope 안의 작업 순서이며 중간 배포/완료 경계가 아니다.

### 단계 0 — current target과 harness identity 고정

- Scope/Thesis/Baseline 해시, B4 source와 현재 작업 트리, candidate binary/bundle 출처를 다시 읽는다.
- `staging/check_block005.py` fixture/evidence schema와 자기 소유 cleanup을 먼저 만든다. 없는 성공 frame/state를 canned data로 채우지 않는다.
- Gate 0: 운영 7683/외부 URL을 사용하지 않고 free port/temp HOME/profile만 쓰며, teardown이 recorded PID/starttime만 정리하는지 확인한다. 기능 PASS는 아직 주장하지 않는다.

### 단계 1 — fixed chunk ring과 write disposition

- ring helper, exact cap/append/read/free, output disposition enum을 구현하고 모든 buffer caller를 이행한다.
- Gate 1: E1 deterministic 10 MiB에서 producer completion, exact 8 MiB tail, ≤128 chunks, no PTY pause를 실제 판독한다. GAP client가 아직 없으므로 일반 운영 노출은 금지한다.

### 단계 2 — GAP/rebase/server-client barrier

- GAP/REBASE opcode, server snapshot/state, client sync generation/degraded UI/consent, reachable END와 ACK gate를 함께 구현한다.
- Gate 2: E2 raw wire exact range/no-old-END, browser loss UI, button PTY 0 bytes, new ACK 뒤 input, repeated overrun을 통과한다. server만 또는 client만 바뀐 후보는 version/protocol mismatch 외 성공으로 노출하지 않는다.

### 단계 3 — root wait/EOF/process/session ref model

- `pty_process` wait/EOF/close states, single root waiter, session ref owners와 finalization coordinator를 구현한다.
- eager `session_release` caller를 전부 제거한다.
- Gate 3: E3 root/expiry/EOF/viewer order 변형에서 exact status/unknown, final bytes, ref/handle close와 unrelated session 생존을 확인한다. sanitizer capability 부재는 PASS가 아니다.

### 단계 4 — reaper/timer/pruning

- reaper container close, init/start failure state, process identity recheck, retained eligibility/`>`와 viewer fencing을 구현한다.
- Gate 4: E3 reaper race와 E4 1/N/over-cap/expiry viewer를 실제 OS identity와 메모리 checker로 통과한다. `free` 한 줄 삭제나 `>=` 변경만으로 gate를 넘지 않는다.

### 단계 5 — admission/fragment/control scheduling

- total live/resource accounting, one recovery reserve, 1 MiB cumulative cap, centralized pending scheduling과 timer failure handling을 구현한다.
- Gate 5: E5 half-open valid successor, invalid reserve refusal, normal fragmented paste, oversize rejection, timer failure state, control-frame 후 pending progress를 통과한다.

### 단계 6 — lifecycle completion과 전체 self-check

- deadline/retained publication, root/EOF/final/tree/PURGED coordinator를 완결하고 diagnostics를 정리한다.
- 같은 최종 source에서 C binary와 inline bundle을 새로 만들고 exact hashes로 `check_block005.py` E1~E6과 `check_block004.py`를 실행한다.
- final Gate: B5-E1~E6 각각에 actual server/PTY/wire/parser/process/ref 증거가 있고 candidate process/profile/ports가 정리되며 운영 7683/기존 session 비영향이 확인되어야 한다. 구현자는 Scope를 `ready`로 유지하고 VERIFIED/done을 기록하지 않는다.

어느 gate에서든 UAF/interior free/double free, broad reap, 보호 result 삭제, unbounded receive/output, PTY drain 정지, unreachable END, false applied/Ready/PURGED가 나타나면 해당 격리 candidate의 신규 연결·입력·시험을 중단하고 자기 fixture의 identity/effect를 보존한다. 운영 daemon을 restart/kill하여 통과시키지 않는다.

## 10. 실패·중단·재개 처리

- **partial wire cutover:** server GAP과 client consumer는 함께 활성화한다. old client/server 조합은 명시 version/protocol mismatch이며 silent cursor jump나 old END fallback을 두지 않는다.
- **write unknown:** exact full-write가 아니면 logical cursor/state를 commit하지 않는다. reconnect readback 전 동일 input/CAS를 blind retry하지 않는다.
- **late callback:** timer/reaper/process/viewer/parser callback은 captured session/lease/sync generation과 자신의 ref만 놓는다. 새 owner의 pointer/deadline/barrier를 정리하지 않는다.
- **timer failure:** timer scheduling 실패를 즉시 PURGED나 expiry 완료로 만들지 않는다. registry/identity/ref를 유지한 TERMINATING failure가 안전 target이다.
- **over-capacity:** 보호 result를 삭제하지 않고 create/recovery 종류에 맞는 명시 거절을 반환한다. valid successor용 reserve는 create capacity 우회가 아니다.
- **cleanup:** test teardown은 owned PID/starttime, socket, browser profile만 정리한다. kill 반환이 아니라 process/port/file descriptor 부재를 읽는다. 남은 process는 evidence와 owner를 기록하고 무관 process를 broad kill하지 않는다.

## 11. Conditional First Work와 방법 변경 경계

### 11.1 B4 predecessor/current candidate 결속

- `plan_anchor`: §3.1, §8.6, §9 단계 0/6.
- `permitted_initial_work`: 현재 source에서 binary와 bundle을 새로 만들고 exact hashes로 `staging/check_block004.py`를 격리 free port에서 실행한다.
- `discriminating_observation`: B4-E1~E6이 같은 source/binary/bundle identity에서 실제 PTY/wire/parser로 성립하고 결과가 B5 결함을 회피했다는 limit를 유지한다.
- `dependent_work_not_yet_permitted`: 과거 `evidence-block004/result.json`만으로 current candidate Entry를 확정하거나 B5 수정 뒤 B4 보존을 자동 가정하는 일.
- `response_if_refuted`: B4 의미가 깨졌으면 B5 dependent cutover를 멈추고 B4 구현 소유자/Main에게 exact failing scenario와 identity를 반환한다. B5 Plan에서 token/lease 제품 의미를 새로 정하지 않는다.

### 11.2 sanitizer/heap-check capability

- `plan_anchor`: §8.3, §8.4, §9 단계 3/4.
- `permitted_initial_work`: 제품 원본과 운영을 건드리지 않는 별도 native build dir에서 ASan/UBSan 또는 사용 가능한 동등 heap checker의 compile/runtime capability를 확인하고 self-owned smoke child를 실행한다.
- `discriminating_observation`: instrumented ttyd가 실제 libuv/lws/PTY fixture를 실행하고 sanitizer report가 evidence에 귀속되거나, runtime/dependency 부재가 정확히 식별된다.
- `dependent_work_not_yet_permitted`: sanitizer가 없는 cross toolchain의 정상 종료를 UAF/double-free 부재로 주장하는 일.
- `response_if_refuted`: real race/OS identity/wire evidence는 계속 수집하되 memory-safety 판독은 `EVIDENCE_NEEDED`로 verifier/Main에 반환한다. assertion 제거나 fixture 축소로 PASS를 만들지 않는다.

### 11.3 short write와 timer failure injection의 증거 한계

- `plan_anchor`: §6.4, §8.2, §8.5.
- `permitted_initial_work`: real RST/blackhole로 actual `lws_write` failure/reconnect를 만들고, 별도 test-only build에서 exact short-return/timer-start negative branch를 주입한다.
- `discriminating_observation`: real transport failure에서는 cursor/bytes가 복구되고, injected branch에서는 commit 전 state가 보존되며 live resource가 PURGED로 사라지지 않는다.
- `dependent_work_not_yet_permitted`: injected return만으로 실제 network recovery 또는 실제 libuv lifecycle 전체를 통과했다고 주장하는 일.
- `response_if_refuted`: real boundary가 재현되지 않으면 해당 실제-effect claim을 evidence gap으로 남긴다. 제품에 silent retry/fake success를 추가하지 않는다.

### 11.4 방법 변경 소유권

다음은 implementer 재량이다: private helper 이름, ring struct의 동일 의미 field 배치, diagnostic event 이름, test utility 내부 구성, 64 KiB frame을 채우는 copy loop의 국소 최적화.

다음은 Plan 재작성과 새 독립 Review가 필요한 material method 변경이다: chunk size/count/cap, rebase wire/opcode 또는 consent 시점, cursor/applied 의미, root wait owner, session ref owner 집합, PURGED predicate, retained deletion eligibility, recovery reserve 수/timeout, fragment cap, deadline 출처, authoritative readback 방법.

제품 의미·Scope Acceptance·BLOCK-004→005→006 순서, 9시간/8 MiB/불완전 화면 정책을 바꾸려면 Plan이 아니라 Main의 Thesis/Baseline/Scope 정합화로 돌아간다.

## 12. Acceptance 추적과 구현자 handoff

| Exit | 구현 anchor | 최소 실제 판독 |
|---|---|---|
| B5-E1 | §4.1, §7.2, §8.1 | 10 MiB producer completion, PTY no-pause drain, exact latest 8,388,608 bytes, ≤128 chunks, replay/live GAP 후 진척, bounded memory |
| B5-E2 | §4.2~4.3, §7.2/7.4, §8.2 | exact lost/retained ranges, old END 부재, rebase/new target, range dedupe, real write failure cursor 보존, loss UI, continue gesture 0 bytes, new ACK 뒤 input |
| B5-E3 | §5, §7.2~7.3, §8.3 | one root waiter, status unknown honesty, parent close once, last-ref free, delayed EOF/callback race, no UAF/interior/double free, unrelated session 보존 |
| B5-E4 | §6.1~6.2, §7.2, §8.4 | `retained > max`, below/equal/above, protected callback/viewer/result, explicit fence/ref end, over-cap create refusal, actual accounting |
| B5-E5 | §6.2~6.4, §7.1~7.2, §8.5 | bounded recovery reserve, valid successor/invalid create 구분, 1 MiB cumulative fragment cap, normal paste, timer failure tracked, control-frame 후 pending progress |
| B5-E6 | §5.2~5.4, §7.2~7.3, §8.6 | EOF/status/final/tree separate readback, exact code/signal/unknown, deadline preservation, timer-generation race, actual PID/FD/handle/ref cleanup 뒤 PURGED, B4 보존 |

구현자 self-check handoff에는 exact Scope/Plan/source/binary/bundle hashes, isolated command/env/free ports, 각 B5 scenario의 session/PTY/process identity와 wire/parser/ref evidence, sanitizer capability, shortened-time evidence의 한계, cleanup 결과, 기존 운영 비영향을 포함한다. mock/failpoint가 대체한 경계와 실제로 관찰한 경계를 분리한다. Scope는 `ready`로 유지하며 구현자가 `done`, `VERIFIED`, BLOCK-006 진입 또는 운영 배포를 선언하지 않는다. 독립 verifier가 stable current candidate에서 B5-E1~E6을 판정하고, 성공 뒤 Main 소유 Production Heuristic Probe와 별도 BLOCK-006 권한이 이어진다.
