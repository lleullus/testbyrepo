# PLAN-001 — BLOCK-001 세션 연속성·liveness 복구 실행 방법

작성: 2026-09-15 / PlannerAstra (GPT-6 Astra Low)
상태: 독립 검토에 제출할 방법. ADMIT, 구현 완료, 검증 판정 또는 Block Exit가 아니다.

## 1. 정확한 결속과 실행 경계

Project Root: `/home/user01/project/webterm/ttyd-1.7.7`

| 원본 | 현재 리비전 / SHA-256 |
|---|---|
| `/home/user01/project/webterm/ttyd-1.7.7/docs/planning/product-thesis/android-web-terminal/THESIS-001.md` | CALIBRATED 2026-09-15 / `81003a0783df4f7876ad603aafd47c1b96ba768cec03237ed72e543ce9eb642a` |
| `/home/user01/project/webterm/ttyd-1.7.7/docs/planning/baseline/BASELINE-001.md` | APPROVED r2-2026-09-15 / `f3b389347779f21b4e0fa1cad49ab748d509181763acb13cd39152416baf27e1` |
| `/home/user01/project/webterm/ttyd-1.7.7/docs/planning/work/session-continuity-liveness-recovery/SCOPE.md` | iis-scope/v1, ready / `fae4c3cdc6cafa01a1898653b65f5a9805609ea2a147ca9e9285c903a12d4751` |

세 원본 전체를 직접 읽고 `sha256sum`으로 지정값과 일치 확인했다. `python3 /home/user01/project/iis-skills/scope-shaper/tools/validate_scope.py <위 Scope 절대 경로> --json`은 종료 0, schema/status `iis-scope/v1`/`ready`, 위 Product Authority와 Transition Authority의 동일 path/hash를 반환했다. 최초 `python` 호출은 명령 부재로 실행되지 않았고 python3로 해결했다. 구조 검사는 의미 판정이 아니다.

직접 적용: Scope Outcome·Acceptance 전부, Thesis NB1/NB5/NB6/NB10, I1/I4/I5/I6, SC-1/2/4, NB9 보존, Baseline BLOCK-001 B1-E1~E6, G1~G3/G5/G8, P1~P7, Safe Abort/Continuation, Atomic Boundary의 세션 복귀 HARD_ATOMIC. 원본이 제품 의미이며 이 Plan은 추가 수락 계약이 아니다.

계획 시 관찰한 Git HEAD는 `409879886810d18bf203fe5b8b36c782c867993d`, branch `custom/android-mobile-toolbar`. `git status --short --branch`에는 baseline/product-thesis/이 Scope의 planning 디렉터리만 untracked로 나왔다. 조사 artifact는 제공되지 않았다. 아래 근거는 현 작업 트리 소스의 정적 판독이지 운영 실행 증거가 아니다. 계획 단계에서 제품 시나리오, 빌드, 린터, 포맷터, 서비스 조작을 실행하지 않았다.

이 Scope는 한 Sol High 구현자가 서버·클라이언트·해당 staging 호출자를 함께 변경한다. 운영 `/home/user01/.local/bin/ttyd`, `/home/user01/.local/share/webterm/index.html`, `session.sh`, 7683, Funnel과 기존 OMP는 변경하지 않는다. BLOCK-002 Takeover 완결 UI/IME/포커스/뷰포트/수정자 재설계와 BLOCK-003 최신-tail/EXITED_RETAINED/회수·수용 상한/운영 감독은 제외한다. 새 UI는 기존 overlay/toolbar에 필요한 상태와 로컬 복구·신규 선택만 붙인다.

## 2. EXISTING — 방법을 바꾸는 현재 소스 증거

경로는 Project Root 상대 경로이며 행은 계획 시점 기준이다.

| 실제 정의와 사용 | 관찰 / 방법상 의미 |
|---|---|
| `html/src/components/app.tsx:8-16,59-70` | 모듈 평가마다 crypto 16 bytes를 hex ID로 만들고 URL의 resume을 덮어쓴다. token/ws 경로는 trailing slash 제거한 pathname에 붙인다. 탭 저장·신규 의도 구분이 없다. endpoint namespace와 명시적 생성이 함께 필요하다. |
| `html/src/components/terminal/index.tsx:48-65,74-77,124-130,175-180,240-246` | mount에서 token await 후 open/connect, unmount에서 dispose. toolbar pointerdown은 blur, Enter click은 바로 CR 전송. 비동기 mount 폐기와 pointerdown~click 양쪽을 묶어야 한다. 일반 포커스 정책 전체 교체는 B2다. |
| `html/src/components/terminal/xterm/index.ts:111-174,293-303,510-605` | 60초/최대 5초 재시도는 존재. connect는 매번 socket/listener 생성, callbacks는 현재 this.socket을 참조; token 결과에 세대/abort가 없다. open에서 listeners를 설치하고 close가 전체 dispose한다. 수동 복구는 terminal.onKey Enter만 구독하며 해당 disposable은 registry 밖이다. visibility/앱 heartbeat가 없다. 숫자 generation은 있으나 소유권 차단이 아니다. |
| 같은 파일 `224-236,389-411,434-485,663-688,697-787` | input은 OPEN만 확인, resize는 상태 확인 없이 send. write callback은 현재 세대를 사용한다. fresh에 terminal.reset(), resumed/unknown에서 준비 완료를 추정하며 parser와 실제 복원을 혼동한다. addon/preferences 재적용도 connection마다 발생한다. 모든 입력 송신자(onData/onBinary/toolbar/zmodem sender)를 하나의 준비 interlock 아래 둔다. |
| `.../xterm/addons/overlay.ts:11-30,37-72` | mousedown 차단만 있고 action은 없다. dispose가 비어 있으며 제거 타이머가 남는다. 복구 action과 영속 상태를 resize/font의 잠깐 overlay가 덮지 않도록 한다. |
| `src/server.h:7-18,42-65`; `src/protocol.c:24-83,156-215,445-498,700-735` | pss generation/세션 diagnostic ID와 카운터는 이미 있다. resume 조회 실패는 spawn, attach는 활성 old 연결을 무조건 떼며 expiry를 먼저 취소한다. 인증 후 신규/재개 판정 및 단일 입력·resize 소유자가 실제 서버에서 확정되어야 한다. |
| `src/protocol.c:217-245,353-405,748-771` | close는 현재 client일 때만 detach하고 grace 시작. exit는 세션을 즉시 release; expiry는 unlink 후 kill. 확정 expired/exited 사실도 잊는다. 종료 결과 보존은 없으므로 작은 종료 사유 기록과 결과 보존은 구별해야 한다. |
| `src/protocol.c:89-144,599-637` | 현재 버퍼는 미전송 큐이며 전송 완료 후 free한다. 8 MiB 초과 시 전체 폐기하고 이후 출력도 버린 뒤 SIGWINCH로 redraw를 요청한다. **새 페이지에는 이미 전송한 화면을 재생할 자료가 없다.** 저장 ID만 고쳐서는 E1/E5를 만족할 수 없다. 상한 이내 재생 자료/위치 보존을 이번 Scope에서 최소 추가해야 한다. 최신-tail 정책 완결은 B3에 남긴다. |
| `src/pty.c:195-229`; `src/server.c:50-55,473-474`; `src/http.c:115-163` | resize는 TIOCSWINSZ, 별도 foreground 함수는 TIOCGPGRP→SIGWINCH. 서버 validity ping/추가 grace 기존 경로와 외부 -I/내장 html 서빙 분기가 있다. 앱 heartbeat는 PTY 입력과 분리하고 기존 서버 ping 정책을 단축하지 않는다. |
| `staging/check_reconnect.py:16-20,40-173,259-425` | 임시 포트·TCP proxy·실제 ttyd/bash·임시 Chrome profile/CDP·60초 실시간 시험이 있다. proxy는 현재 close/drop만 지원해 OPEN blackhole은 추가 필요. 성공 기다리며 같은 shell 명령을 재전송하는 372-382행은 새 입력 불확실성 시험의 증거로 재사용할 수 없다. process-group 종료만으로 forkpty 셸 정리를 증명할 수도 없다. |
| `staging/check_fresh_session.py:41-50,146-230`; `staging/check_omp_reconnect.py:44-67,116-205` | raw WS 호출자는 구 handshake/문자열 상태에 묶여 있다. fresh 시험은 자동 takeover와 만료 후 fresh를 성공으로 요구하므로 그 기대를 교체한다. OMP 시험은 실제 유료 provider/tool 실행까지 요청할 수 있는 prompt/auto-approve가 있어 무심코 실행하지 않는다. 실제 OMP 화면 시험은 별도 안전한 scratch 작업에서 수행한다. |
| `html/package.json:12-18,20-22,55-72`; `CMakeLists.txt:30-85`; `CUSTOMIZATION.md:59-109` | Yarn 4.18/Node 24.20 계열, inline은 html/dist/inline.html, CMake 서버는 libuv/json-c/lws/zlib. 문서의 staging 명령은 운영 바이너리·런처를 재사용하므로 이번 증거에 그대로 쓰지 않는다. 문서의 frontend-only copy/restart와 fresh-shell 표현은 원자 cutover에 맞춰 수정해야 한다. |

## 3. PROPOSED — 한 원자 경계의 변경 구조

### 3.1 탭 식별과 요청 의도

`app.tsx`에서 endpoint=`origin + 정규화 pathname`에 귀속된 versioned sessionStorage 키 하나(예: `webterm.session.v1:<endpoint>`)를 사용한다. 128-bit random ID, 요청의 생성 확정 여부만 보관하고 token/화면/키 입력은 저장하지 않는다. query의 resume은 더 이상 임의 사용하지 않는다. 탭 저장은 복제될 수 있으므로 소유권 증거로 사용하지 않는다.

처음 저장값이 없거나 손상/접근 차단이면 “보존된 탭 세션 없음/연속성 불가”와 **새 세션 시작** 선택을 보인다. 값 부재만으로 최초 방문인지 값 소실인지 알 수 있다고 주장하지 않는다. 사용자 선택에서만 ID와 create 의도를 만들고, 연결 재시도는 같은 ID의 idempotent create/조회로 이어져 중복 스폰하지 않는다. 생성 사실 응답 이후 resume 의도로 바꾼다. create 응답 유실 때 같은 ID가 이미 존재하면 서버가 해당 사실을 알려주고 신규 스폰하지 않는다. 저장 쓰기 실패 시 ephemeral 세션임을 계속 표시하며 reload 연속성 약속을 하지 않는다. 만료/종료/unknown 이후 신규 선택은 새 ID로 한다; 기존 ID를 자동 회전하지 않는다.

### 3.2 서버 판정·소유권·상태 계약

`server.h`, `protocol.c`, xterm의 Command/handshake/state reader를 한 번에 변경한다. 기존 JSON_DATA 인증 초기 메시지에 protocol version, intent(create/resume), 화면 인스턴스의 replay 위치를 포함한다. `resume` query와 ID validation은 조회 키로 유지하되 **intent 없는 구 클라이언트는 spawn/attach하지 않고 protocol 불일치로 종료**한다. 구 `fresh/resumed` 문자열 fallback도 삭제한다. 인증 자체·token endpoint·URL args는 재설계하지 않는다.

서버의 기존 event loop가 유일한 판정자다. 응답은 versioned `SET_SESSION_STATE` JSON으로 최소 `created/attached/conflict/expired/exited/unknown/error`, 비밀이 아닌 diagnostic session ID, server connection generation, replay 범위/한계, 입력 준비 상태를 제공한다. WS OPEN과 session accepted는 별개다. 미지원 version/오류/unknown state는 입력 닫힌 상태로 남는다.

- create: 유효한 명시적 요청이며 ID가 없을 때만 spawn. 같은 ID가 이미 있으면 두 번째 spawn 금지; detached면 적격 attach, active면 conflict, 종료 사유가 있으면 해당 상태. spawn 실패를 ready로 보내지 않는다.
- resume: live detached 세션만 attach. active owner가 있으면 기존 owner의 input/resize를 보존한 conflict. 이 Block에서는 자동 takeover/탭 nonce 추정/브라우저 선거를 넣지 않는다. 정상 reload는 구 socket close를 서버가 관찰한 뒤 attach한다. close 전달이 늦은 첫 conflict는 안내 후 사용자가 복구를 재시도할 수 있으며 강제 인계하지 않는다.
- `attach_process`는 소유 가능성을 확인한 **뒤**에만 expiry 취소/owner 할당. 실패·충돌은 기존 grace를 연장하지 않는다. CLOSED/INPUT/RESIZE/PAUSE/RESUME/새 control 모두 `session->client == pss` 및 generation/phase 확인을 공유한다. old close는 새 session/owner를 변경하지 않는다.
- expiry/exit 시 확정 사유를 세션 삭제 전에 기록한다. 작은 in-memory tombstone으로 ID, diagnostic ID, reason, 관찰 시각만 보관한다(출력/프로세스 유지 아님). 제안 상한 256건·최대 32,400초, 초과/기간 종료 시 오래된 사유부터 버리고 이후 조회는 **unknown**. 서버 재시작도 unknown이다. 이 보관 한도는 연속성/종료 결과 보존 약속이 아니라 “확정 가능한 사실만 말함”을 위한 유한 진단 저장이다. B3의 EXITED_RETAINED로 승계할 수 있도록 원래 detach deadline과 종료 사유를 혼동하지 않는다.
- B2에 넘기는 interface는 conflict 및 소유권 검사다. Takeover 버튼/권한 전환 프로토콜을 미리 활성화하지 않는다. B3에 넘기는 interface는 replay 한계/종료 사유/원래 deadline이다. exited를 결과 열람 성공으로 표시하지 않는다.

### 3.3 상한 이내 화면 재생과 준비 interlock

이번 Scope에서 복귀 후 깨끗한 새 셸을 성공으로 숨길 수 없다. 서버 미전송 큐와 별도 무제한 history를 만들지 말고 **기존 8 MiB payload 저장을 전송 위치와 분리하여 상한 이내 출력의 재생 자료로 유지**한다. 전송 후 즉시 free하는 경로를 바꾸고 session 종료/정리 때 반환한다. 저장 길이와 connection별 send cursor, absolute output 위치를 명시적으로 분리한다. 전송 chunk는 기존 64 KiB를 재사용한다. 브라우저는 frame 위치를 받고 parser callback에서 실제 적용 위치를 갱신한다.

새 페이지 xterm은 처음 위치부터 상한 이내 전체 스트림을 재생한다. 기존 xterm reconnect는 마지막 실제 적용 위치 다음부터만 재생한다. old socket에서 이미 큐에 들어간 terminal.write는 순서대로 끝내고 그 applied 위치가 확정되기 전 새 replay를 시작하지 않는다. late parser callback이 새 flow-control/readiness를 해제하지 않도록 terminal instance와 연결 세대를 함께 검사한다. input 재전송 큐는 만들지 않는다.

attach 시 재생 끝 위치를 snapshot하고 해당 위치까지 output 뒤에 ordered replay-end control을 보낸다. client는 그 위치까지 parser callback 완료, 유효 geometry 적용, 다음 화면 render/frame 관찰을 구분한 다음 ready-ack를 보내며 server가 현재 owner/위치에 대해 input-ready를 응답한다. 무출력 세션도 replay-end가 존재해야 한다. 준비 전의 사용자 입력은 보관/나중 전송하지 않고 현재 입력 불가를 표시한다. resize는 소유권 확정 후 최신 유효 rows/cols를 적용하고 숨김 0 크기를 보내지 않는다.

재접속은 `pty_resize`에 더해 기존 `pty_signal_foreground(SIGWINCH)`를 사용하여 동일 크기 OMP도 비파괴 redraw 기회를 갖는다. 신호 성공은 화면 복원의 증거가 아니다. normal/alternate/커서/모드의 화면 판독은 §5에서 따로 한다. 지원 셸/OMP의 상한 이내 replay가 깨진다면 단순 경고를 Exit 대신 쓰지 않고 §6.1로 돌아간다.

8 MiB를 넘어선 기존 전체 폐기 결손은 최신-tail 구현으로 확대하지 않는다. replay 불연속/overflow를 server state에 유지해서 client가 “출력 유실·완전 복원 확인 불가”로 표시한다. 폐기 직후 `redraw-complete`만으로 손실 표식을 지우지 않는다. 새로운 페이지의 시작 위치가 보존 범위 밖이면 정상 복원/ready로 위장하지 않는다. 기존 live 입력을 불필요하게 파괴하지 않는 저하 상태와 복원 실패 상태를 구별한다. B3가 tail/파서 경계/완전 재동기화를 완결한다. 이는 overflow 사례로 E1의 **상한 이내** 화면 증거를 대체할 허가가 아니다.

`terminal.reset()` 복구 경로와 unknown→application-ready, resumed 즉시 Reconnected 표시를 제거한다. 명시적 신규 세션은 별개의 terminal 인스턴스 수명으로 시작할 수 있지만 복구 도중 기존 normal/alternate buffer를 초기화하지 않는다. 입력/resize/파일 sender/terminal binary 모두 같은 owner+ready 검사를 통과한다.

### 3.4 하나의 연결 세대와 liveness

Xterm 인스턴스 수명 listener/addon과 socket 세대별 listener/timer를 분리한다. lifetime listeners는 open에서 한 번 설치; close는 socket 세대만 폐기, component unmount는 전체 dispose(활성 socket close, fetch abort, retry/heartbeat/overlay/rAF 제거). 초기 mount token await도 이 coordinator 안으로 이동하여 unmount 뒤 connect를 막는다.

연결 세대는 token fetch 시작 전에 증가한다. callbacks는 captured socket+generation을 검사하고 current this.socket으로 늦게 도착한 old open을 처리하지 않는다. token fetch AbortController와 유한 deadline, socket opening/session handshake/replay 단계 deadline을 같은 60초 recovery window 안에서 관리한다. proposed 값: token/open/handshake 각 최대 10초, replay settlement 최대 30초, retry 기존 1/2/4/5초 cap, 총 자동 시도 60초. 이 deadline은 성공 추정이 아니라 실패를 명시하기 위한 한도다. 전체 60초는 OPEN이 아닌 session/input-ready 성립 전까지 리셋하지 않는다.

앱 control heartbeat는 INPUT과 별도 opcode로 request nonce/response를 교환한다. visible 상태 5초 cadence, 응답 제한 30초를 사용하여 기존 서버 validity 정책을 단축하지 않는다. 정상 응답은 socket liveness만 증명한다. visibility→visible/pageshow/online은 기존 OPEN에 즉시 probe(이미 probe 진행 중이면 합류); 살아 있으면 새 socket 없음. 응답 deadline 초과만 해당 세대를 invalidate/close하고 복구 coordinator로 들어간다. 서버 transport ping도 유지한다. hidden 때 timer 지연을 새 OPEN 성공으로 해석하지 않고 복귀 직후 실제 왕복을 판독한다. 한 번에 유효 token/connect/probe 흐름 하나, terminal owner 하나. conflict/expired/exited/unknown/protocol mismatch는 자동 스폰/무한 재획득 없이 명시 상태로 멈춘다.

### 3.5 전체 복구 제스처의 로컬 소비

overlay action과 toolbar Enter는 `requestRecovery` 하나로 수렴한다. Enter의 input route와 recovery route를 click 순간 상태만으로 선택하지 않는다. 안정적으로 남는 terminal root/toolbar capture에서 pointerdown 당시 복구 gesture를 귀속하고 pointerup/cancel 및 후속 click까지 소비한다. overlay 제거로 click target이 바뀌어도 같은 gesture는 새 input-ready 세션으로 통과하지 않는다. gesture가 끝난 후 새로 시작한 조작만 입력 가능하다. 단순 300ms 전체 입력 차단 같은 시간 추정 대신 pointer sequence를 사용하고 keyboard Enter activation도 별도 로컬 소비한다. 빠른 반복/visibility 동시 action은 진행 중 coordinator에 합류한다.

복구 pointerdown은 preventDefault/propagation 차단, modifier 정리, blur를 수행하되 PTY 바이트를 만들지 않는다. Shift UI와 Xterm CTRL 소유자는 기존 callback을 통해 함께 정리한다. 일반 연결 상태 toolbar/IME 정책은 B2로 남기고 이 Scope에서 광범위하게 바꾸지 않는다. resize·복사 overlay는 영속 session/recovery 상태를 덮지 않는다. overlay dispose는 실제 timer/listener/node를 정리한다.

## 4. 정확한 통합 순서와 소유 파일

1. **입장/격리 준비:** 구현자는 원본 hash·작업 트리 차이를 확인하고 변경된 load-bearing source만 재판독한다. 아래 §6 조건부 첫 작업으로 지원 화면/환경 한계를 먼저 판독한다. 개인 운영 세션에 입력하지 않는다.
2. **서버 비활성 준비:** `src/server.h`, `src/protocol.c`에 versioned intent/state, 소유 interlock, 종료 사유, replay 위치/end, heartbeat/ready controls를 함께 작성. 기존 PTY read/drain·grace 함수·인증/HTTP는 재사용한다. `src/pty.c`, `src/server.c`, `src/http.c`는 기본적으로 변경하지 않는다. 필요 변경이 실제 계약을 바꾸면 재검토한다.
3. **클라이언트 결합:** `app.tsx`, `terminal/index.tsx`, `xterm/index.ts`, `xterm/addons/overlay.ts`를 같은 계약으로 변경. session storage, connect coordinator, stage 상태 표시, pointer 소비, 모든 send interlock, replay parser 위치를 연결한다. 기존 스타일이 상태/action 표시를 못할 경우에만 `html/src/style/index.scss`의 국소 규칙을 추가하고 레이아웃 재설계는 하지 않는다.
4. **모든 구 호출자 cutover:** `staging`의 resume/JSON_DATA/`fresh`/`resumed` 소비자를 검색하여 `check_fresh_session.py`, `check_reconnect.py`, `check_protocol_edges.py`, `check_omp_reconnect.py`와 실제로 동일 계약을 쓰는 나머지 harness를 새 protocol로 이동한다. 자동 takeover/만료 후 fresh/복구 reset을 기대하는 assertion은 새 계약에 맞게 교체한다. 의미 없는 소스 문자열 pin은 없앤다. 신구 handshake fallback/구 스폰 분기/중복 listener 설치 경로는 남기지 않는다.
5. **동일 target 빌드:** Main과 조정하여 통합 후 한 번 formatter/lint/build를 수행한다. 기존 Yarn inline 경로와 CMake out-of-tree target(예: build-block001/ttyd)을 사용한다. 시스템 설치/운영 바이너리 덮어쓰기 금지. 명시 TTYD_BIN과 새 inline 파일로만 실행; 기존 staging 파일 재사용 시 새 html/dist/inline.html과 hash 일치 확인. 내장 html 사용 여부는 분리 표기하고 이 시험은 `-I` 외부 bundle로 고정한다. 내장 artifact를 배포 호환 완료로 주장하지 않는다.
6. **실제 isolated smoke/회귀:** §5를 같은 final bytes에 실행. build 변경 뒤 영향 시나리오를 재실행하며 옛 server와 새 bundle 성공을 합치지 않는다. 서버만 또는 저장 ID만 먼저 운영 노출하는 중간 완료는 없다.
7. **검증 인계/cleanup:** 성공한 smoke 뒤 기존 `CUSTOMIZATION.md`의 fresh-shell/자동 신규/프런트 단독 배포 설명을 이번 계약과 격리 실행 한계로 갱신한다. 별도 일반 문서는 만들지 않는다. 영구 시험은 실제 plausible regression(중복 스폰, late generation, pointer 누설, replay 유실)을 방어하는 기존 harness 확장만 유지; 임시 계측/fixture는 evidence 보존 후 제거한다. Scope status는 구현자가 ready에서 바꾸지 않는다.

## 5. 실제 증거 방법 — Acceptance 전 항목 대응

### 공통 실행 경계 / 원시 판독

한 final source/build manifest에 full HEAD+미커밋 diff hash, authority/Plan hash, binary/inline/시험 launcher hash, command/env, 실제 listener PID와 `/proc/<pid>/exe`, `/proc/<root>/stat` starttime, PTY/foreground PGID, 시각·Chrome/OMP 버전·storage namespace를 묶는다. 응답으로 받은 정적 문서 hash를 inline 파일에 대조하고 `/terminal` base-path 옵션으로 index/token/ws도 별도로 관찰한다. 실제 production 경로 통과 여부는 별도 열이다.

기존 Python/websocket/CDP staging 도구를 재사용하되 명시적인 임시 포트(7683 제외), 임시 profile/cwd, 직접 빌드한 ttyd, fixture launcher로 실행한다. fixture shell은 bootstrap에서 root PID/starttime·작업 marker를 파일에 기록하고, raw PTY reader 모드에서는 받은 bytes를 자기 scratch 파일에 기록한다. fixture는 **실제 ttyd가 생성한 PTY의 실제 수신자**이며 모의 서버/가짜 응답이 아니다. OMP는 실제 OMP 화면으로 별도 확인한다. `TTYD_DIAGNOSTICS=1` 기존 세션/connection/counter를 보강하되 raw resume/token/운영 입력은 로그에 넣지 않는다. WS input counter는 송신/접수 보조 근거일 뿐 PTY 수신 바이트는 fixture의 파일/PTY 끝에서 읽는다. 시험 counter의 시작값을 먼저 캡처한다.

서버 stdout/stderr는 파일로 지속 배출해 pipe 포화가 시험을 막지 않게 한다. 브라우저 screenshot, xterm buffer/모드/rows-cols, 실제 diagnostic snapshot, WS control timeline, fixture raw bytes, process identity와 spawn events를 저장한다. DOM 상태 주입·가짜 `SET_SESSION_STATE`·WebSocket 대체 객체는 제품 성공 근거로 쓰지 않는다. ancillary fault injection은 네트워크만 지연/차단하며 실제 backend/PTY/render 경계는 유지한다.

| Scope Acceptance / Baseline | 실제 조작과 결정적 readback |
|---|---|
| **동일 탭 복귀와 명시적 신규 생성 — B1-E1, SC-1** | 최초 새 세션 선택→fixture marker 생성→같은 탭 reload와 storage 유지한 탭 복원 각각 실행. ID는 원문 대신 equality/진단 ID로 증거화. root PID+starttime, server attach, marker, 전후 spawn 수(추가 0), 실제 전후 shell/OMP 화면을 함께 읽는다. reload 전에 이미 화면에 전달된 출력도 복원되는지 필수 확인. 기존 xterm 단절 재연결과 새 xterm reload를 별도 사례로 둔다. 새 독립 탭은 별도 신규 선택 뒤에만 1 spawn. 저장소 거부/값 삭제/손상은 scratch profile에만 적용; continuity 불가 표시와 선택 전 0 spawn/0 bytes, 선택 후 ephemeral 경고를 확인. |
| **상태 진실성과 소유권 보호 — B1-E2** | 짧은 `TTYD_RECONNECT_GRACE=2` 실행으로 실제 expiry, fixture root 실제 exit, 그 인스턴스만 재시작한 unknown ID를 각각 관찰. expired/exited/unknown을 구별하고 신규 선택 전 spawn/input delta 0. default 32400 구성 판독은 별도로 보존하고 단축 시험을 실제 9시간으로 쓰지 않는다. 같은 storage 복제 탭 또는 같은 ID의 실제 두 번째 WS에서 conflict를 읽고 기존 탭의 새 시험 입력/resize만 통과하는지 확인. 구 연결 close 관찰 뒤 재시도는 같은 root로 attach. 지연된 old close/control은 현재 owner/새 socket/expiry를 바꾸지 않는다. create 응답 유실 후 같은 ID 재시도도 spawn 1회. |
| **화면 복귀와 반단절 liveness — B1-E3, SC-4** | 실제 브라우저에서 다른 탭/창 전환 등으로 visibility hidden을 확인하고 120초 후 visible로 복귀; 정상 살아 있는 socket은 generation/spawn 증가 0, 실제 nonce 왕복. proxy에는 TCP를 닫지 않고 양방향 bytes를 버리는 blackhole mode를 추가해 browser OPEN 유지 상태를 먼저 캡처한 뒤 앱 probe deadline과 한 번의 교체를 읽는다. 이어 network disconnect/recover, 앱 전환, 실제 Android lock 2분/복귀 및 Wi-Fi↔이동망은 가능한 환경에서 각각 시행. token 응답/upgrade를 proxy에서 지연해 visibility+timer+manual을 겹치고 실제 session/input-ready까지 유효 시도/owner 최대 1인지 확인. 정상 pong만으로 복원 성공이라고 하지 않는다. |
| **날조 입력 없는 수동 복구 — B1-E4, SC-2** | 실제 60초 자동 window 소진(OPEN 직후 반복 close도 포함) 뒤 overlay tap과 toolbar Enter를 각각 실제 pointer events로 실행. fixture raw-byte baseline→복구 settlement까지 정확히 delta 0. 빠른 두 번 탭, pointerdown 뒤 연결 완료, overlay 제거 뒤 click, visibility와 동시 tap을 별도 기록. 그 뒤 새 pointer/key gesture로 보낸 고유 payload 1개가 정확히 1회 수신되는지 확인. CDP `window.term.input`만으로 touch action 성공을 대체하지 않는다. |
| **복원 진실성과 보존 — B1-E5 및 모든 보존 조건** | 끊기기 직전 보낸 고유 입력, 접수 여부 불명 입력, server root가 먼저 종료된 입력을 각각 실제 proxy/fixture로 발생시켜 복구 후 자동 재전송 0을 판독. 사용자 명령을 성공할 때까지 반복 보내는 기존 loop는 제거. WS-open→session accepted→replay-end→parser settled→render 관찰→input-ready를 시간순으로 읽고 어느 단계가 멈춰도 상위 성공 표시가 없는지 확인. shell과 실제 OMP의 normal/alternate 화면·커서·mode·marker를 재진입 전후 비교. Enter/ESC/Ctrl+L/RIS 주입 없이 resize/foreground 신호와 실제 화면을 확인. overflow는 기존 유실 한계를 정직하게 표시하며 tail/종료 결과 보존 성공을 주장하지 않는다. 분리 중 출력 fixture가 계속 전진하는 파일 marker/실제 output, grace default와 취소/재분리, 일반 toolbar Enter/TAB/arrows/terminal input을 재검사. |
| **통합 대상과 Block 출구 — B1-E6** | 위 사례를 하나의 final build manifest/격리 campaign에 귀속(각 case별 새 fixture 인스턴스와 instance ID를 명시); expiry용 env 차이도 기록. 동일 active fixture에서 복구 20회 반복, 처음 안정 상태/마지막 안정 상태/완전 dispose 후의 listener/socket/timer/FD/PTY 및 browser generation을 비교. 이벤트당 처리 1회, outstanding fetch/socket/retry/heartbeat 유효 수와 서버 owner 수를 읽어 monotonic 누적이 없는지 확인. screenshot/readback/evidence 파일의 실제 hash·시각·소유자와 cleanup 결과를 남긴다. 운영 완료 또는 모든 Android 조합 지원으로 확대하지 않는다. |

기존 `check_protocol_edges.py`의 64 KiB 실제 paste/fragment/flow-control 회귀는 새 handshake/ready 이후로 갱신하여 정상 입력 경계를 보존한다. 필요 raw control 경합 시험은 실제 server에만 수행하고 무작위 외부 target을 사용하지 않는다. 브라우저 내부 카운터는 진단이며 독립 verifier는 actual WS/PTY와 화면을 교차 확인한다.

### 실패 영향 범위와 가장 싼 판독

- 잘못된 intent/ID 분기: 먼저 isolated raw WS로 spawn/owner delta를 판독; 같은 서버의 모든 create/resume 경로가 영향 범위. 실패하면 브라우저 신규 입력 시험을 중단한다.
- 세대/heartbeat 오류: 실제 proxy+browser 한 fixture로 old result/current owner를 판독; token/open/close/flow/parser/resize가 같은 가정의 영향 범위. helper callback 테스트만으로 통과하지 않는다.
- gesture 누설: raw PTY delta가 하나라도 생기면 해당 fixture의 실제 효과를 보존하고 추가 명령을 멈춘다. 모든 복구 activation 접점에 수정·재판독한다.
- replay/readiness 오류: 원시 출력 위치 대조와 실제 shell/OMP 화면이 최소 경계. buffer 숫자/renderer callback만으로 대체하지 않는다. 화면 전략 변경은 재검토한다.
- resource 정리 실패: 시험 소유 PID/starttime/PTY/소켓을 다시 읽고 residual을 명시한다. 운영 daemon kill로 정리하지 않는다.

## 6. UNRESOLVED — 증거에 따라 방법이 달라질 수 있는 조건부 첫 작업

### 6.1 지원 화면 재생 검증

- `plan_anchor`: PLAN-001 §3.3, §6.1.
- `permitted_initial_work`: 독립 ADMIT 뒤 구현자가 승인된 scratch ttyd/PTY/browser에서 기존 셸과 실제 OMP의 출력 상한 이내 startup/normal/alternate stream을 수집하고, §3.3의 bounded replay/위치 처리 최소 연결을 그 격리 대상에서만 확인한다. 실제 OMP는 새 scratch cwd의 입력 대기 화면과 비민감 로컬 작업을 사용; 기존 OMP 연결/실행을 건드리지 않는다.
- `discriminating_observation`: reload 전 이미 전달된 화면과 reload 후 실제 screenshot/buffer/mode/cursor/작업 marker, root identity가 일치하는가; 유지 xterm의 queued parser와 resume 위치에서 누락/중복 제어 효과가 없는가. SIGWINCH 후 실제 OMP redraw까지 판독한다.
- `dependent_work_not_yet_permitted`: 이 최소 replay가 반증된 상태에서 application-ready/화면 복원 성공을 활성화하거나 “한계 안내”만으로 E1/E5 완료 처리, snapshot/별도 terminal emulator/무제한 history로 확장하는 일.
- `response_if_refuted`: affected replay/readiness 구현을 멈추고 Planner/독립 Plan Reviewer에 방법 재진입. 지원 화면 의미를 바꿔야 하면 Main→Scope/Thesis owner. 관련 없는 서버 intent/소유 interlock 작업은 파일 경계가 분리되면 계속할 수 있다.

### 6.2 실제 Android·외부 경로·OMP 환경

- `plan_anchor`: PLAN-001 §5 B1-E3/E6, §6.2.
- `permitted_initial_work`: Main/운영자가 이용 가능한 실제 Android Chrome/remote-debug 접근과 같은 후보 build를 기기에 제공할 승인된 경로, 실제 OMP 실행 가능 여부를 확인한다. verifier가 기기/Chrome/네트워크 조건과 전달받은 artifact ID를 읽는다. 격리 localhost `/terminal` 경로 검사는 바로 가능하지만 운영 Funnel 변경은 하지 않는다.
- `discriminating_observation`: 후보 build 식별자가 같은 실기기에서 실제 2분 lock/복귀와 network 전이를 관찰할 수 있는가; 외부 `/terminal/token`·`/terminal/ws`가 **그 후보**를 통과하는가. 단순 기존 운영 페이지 로드는 후보 증거가 아니다.
- `dependent_work_not_yet_permitted`: 데스크톱 viewport/CDP visibility를 실제 Android 화면 잠금으로 기록, localhost를 외부 route 통과로 기록, 운영 7683 교체/인증 변경/권한 상승/기존 OMP 종료.
- `response_if_refuted`: 로컬 격리 구현/증거는 보존해 PARTIAL로 Main에 인계하고 missing device/route/OMP 권한·환경을 명시한다. 필수 B1 관찰이 남으면 Block Exit/Safe Continuation을 주장하지 않으며 다음 Block으로 자동 진행하지 않는다. Main이 정확한 추가 환경/권한을 마련한 뒤 해당 원본에 재진입한다. 외부 공개나 provider 호출은 이 조건만으로 승인되지 않는다.

빌드 도구/라이브러리의 가용성은 계획에서 실행 확인하지 않았다. 구현 입장에서 기존 .build-deps/native 구성을 읽고 명시 out-of-tree target을 빌드하되 시스템 설치가 필요하면 Main에 반환한다. 이것은 제품 방법을 바꾸는 기본 분기가 아니므로 불필요한 별도 실험 단계로 늘리지 않는다.

## 7. 실패·중단·정리와 독립 검증 인계

운영 무변경의 사전 기준은 운영자가 읽은 7683 listener PID/starttime·실행물 hash/감독자와 기존 작업 상태다. 시험자는 읽기 권한 범위에서 전후 identity를 비교하며 운영 명령을 입력하지 않는다. 파일이 그대로라는 사실만으로 프로세스/세션 무영향을 증명하지 않는다.

시험 시작 전에 각 ttyd/proxy/browser 및 fixture root/자식의 PID+starttime·소유 관계를 기록한다. 종료 시 신규 시험 입력/재연결을 중단→browser dispose→proxy 닫기→시험 소유 session/root/child만 유한 종료·reap→ttyd/browser 종료→port/FD/PTY/자식 부재 판독 순서다. forkpty는 별도 세션/그룹을 만들 수 있으므로 ttyd parent killpg 반환만으로 끝내지 않는다. 실제 소유 fixture에 TERM 후 5초, 남은 확인된 fixture에 KILL 후 5초 관찰을 사용할 수 있으나 실패/소유 불명은 추가 무차별 kill 없이 Main에 residual 목록을 반환한다. 이 cleanup은 B3 제품 거버넌스 구현이 아니다.

프로토콜 불일치·중복 스폰·무단 인계·PTY 누설·old close가 새 연결 종료·기존 작업 영향 불명이면 후보 신규 시나리오/입력 활성화를 중지한다. 이미 전달된 입력을 자동 취소/재실행하지 않는다. 로그·raw bytes·현 owner·spawn된 시험 root·deadline을 보존한다. 호환하지 않는 frontend-only rollback이나 운영 restart는 금지한다. scratch profile/fixture 파일은 근거를 필요한 비민감 형태로 보존한 뒤 자기 소유분만 제거한다.

구현자는 최종 diff/manifest, 실제 build 결과, §5 행별 raw evidence 경로와 hash, default/단축 grace 구분, PTY/스폰 delta, 미확정 입력, lifecycle cleanup과 운영 무영향, §6 미관찰을 인계한다. 독립 verifier는 같은 stable target에서 Scope Acceptance를 판정하고 Main이 별도 Coverage와 Safe Continuation을 소유한다. Plan 파일 존재나 구현자 smoke는 ADMIT/Acceptance/Coverage를 대체하지 않는다.

private helper/명칭/동등한 국소 배치는 구현자 재량이다. intent/state schema의 의미, 소유권 증거, replay/persistence 방식, heartbeat/deadline 효과 전략, authoritative readback 또는 Scope 경계가 달라지면 affected 구현을 멈추고 이 Plan 수정 후 새 독립 검토를 받는다. B1-E1~E6 중 하나라도 필수 실제 관찰이 남거나 cleanup 효과가 불명이면 Exit와 다음 Block 계속을 완료로 기록하지 않는다.
