# PLAN-001 — BLOCK-002 모바일 입력·명시적 인계 실행 방법

- 작성: PlannerAstraB2R2, GPT-6 Astra Low, 2026-09-16.
- Project Root: `/home/user01/project/webterm/ttyd-1.7.7` (이하 모든 상대 경로의 기준).
- 상태: 독립 Plan Review 대기. 이 문서는 방법이며 ADMIT, 구현 완료 또는 의미 검증 판정이 아니다.
- 현재 작성 권한: 이 파일만 생성. 제품/시험/설정/Scope 수정, 빌드, 시험, 브라우저, 서비스, 외부 경로 실행을 하지 않았다.

## 1. 정확한 결속과 보존 경계

| 원본 | 바이트 SHA-256 / 적용 |
|---|---|
| `docs/planning/work/mobile-touch-keyboard-takeover/SCOPE.md` | `f89d736c553b96b848872832f41f479f0d891e98c5223f662bd878a31e0df20b`, `iis-scope/v1`, ready; Outcome와 Acceptance 전부 |
| `docs/planning/product-thesis/android-web-terminal/THESIS-001.md` | `81003a0783df4f7876ad603aafd47c1b96ba768cec03237ed72e543ce9eb642a`, CALIBRATED 2026-09-15; NB4/7/8/10, I3/5/6, §4.1~4.4, SC-3/5/8 및 선행 보존 |
| `docs/planning/baseline/BASELINE-001.md` | `f3b389347779f21b4e0fa1cad49ab748d509181763acb13cd39152416baf27e1`, APPROVED r2-2026-09-15; BLOCK-002 B2-E1~E7, G1~G3/G5/G6/G8, P1~P7, Safe Abort/Continuation, Atomic Boundary |

세 원본을 직접 읽고 실제 바이트 해시를 대조했다. `/home/user01/project/iis-skills/scope-shaper/tools/validate_scope.py <정확한 Scope 경로> --json`은 exit 0, ready와 위 두 authority path/digest를 반환했다. 별도 repository investigation은 제공되지 않았다.

선행 근거: `/home/user01/tmp/iis-verification-results/webterm-block001-verification-r3.md` SHA-256 `db2dc60b48817f911136e3b80ddca860fd667883fc2c2cc14d396f9b01497a63`, VerifyLunaR3 VERIFIED; `/home/user01/tmp/iis-coverage-results/webterm-block001-coverage-r3.md` SHA-256 `56ab0af483f2a8df8ce9aec2c8b298bd30610b45cc676ede5a0c6b47455021fc`, CoverageLunaR3 COMPLETE/no material gap. 직접 읽고 해시를 확인했다. Main이 기록한 BLOCK-001 done 및 후보 효과 정리를 전제로 삼으며, 보고서 당시 후보 PID/route가 현재 살아 있다고 간주하지 않는다. 과거 Android 복구 관찰은 이번 IME/Takeover 통과 증거가 아니다.

**HARD_ATOMIC:** 입력 의도·포커스·IME·paste·modifier·복구 ↵·geometry와 Takeover UI·서버 전환·displaced 억제를 같은 호환 후보에서 활성화한다. 내부 단계 완료를 독립 제품 완료로 넘기지 않는다. 기존 create/resume, endpoint storage v1, bounded owner check, replay/parser/render/input-ready, 복구 0 byte, 9시간 grace, 비차단 drain, foreground resize와 정상 입력을 유지한다. BLOCK-003의 tail 절사 완결/종료 결과 보존/워커 회수/상한/systemd/logrotate/운영 cutover/전체 TUI 동일 크기 복원은 구현하지 않는다.

## 2. 현행 근거와 변경 소유권

아래는 작성 시 직접 읽은 **EXISTING 소스 사실**이다. 실행물/실기기 동작의 새 증명은 아니다.

| 대상과 범위 | 현재 경로, 결정적 의미 | 변경 |
|---|---|---|
| `html/src/components/app.tsx:8-54,97-108` | origin+path의 `webterm.session.v1:`; explicit create만 ID 발급; request intent create/resume | namespace/저장 schema 유지. Takeover는 저장된 create/resume intent가 아니라 일회성 연결 요청으로 전달 |
| `html/src/components/terminal/index.tsx:12-52,187-307` | UI Shift와 Xterm CTRL 이중 소유; toolbar blur/hide; body CTRL 해제; font 10..30 | UI는 입력 owner snapshot 표시와 intent dispatch만. blur/hide 제거, font/fullscreen 실제 상태 반영 |
| `html/src/components/terminal/xterm/index.ts:163-244,326-398,412-569,594-633` | Xterm이 실제 textarea/onData/onBinary/sendData·복구 click 소유; 여러 fit 호출 | 같은 Xterm 안 단일 입력 owner 및 단일 fit scheduler. 별도 전역 bus/새 store 없음 |
| 같은 파일 `635-874,910-1074` | 단일 복구 flight, 세대 검증, 60초/30초 attempt, 5초 heartbeat/30초 timeout, replay ack; conflict Retry | 보존하면서 terminal displaced와 explicit takeover 연결을 결속; 모든 복구 진입점 차단 |
| 같은 파일 `1083-1170` | server/query preference가 font를 다시 쓰고 addon sender가 sendData를 사용 | font의 모든 writer 정규화; addon/binary도 최종 readiness/generation gate 통과 |
| `template.html:6`, `style/index.scss:1-102` | resizes-content 없음; root 100dvh; row/button 30px, nonshrinking min width | viewport meta 및 layout viewport 기반 flex; 35px hit height, 좁은 폭 shrink |
| `src/server.h:7-22,46-87` | v2 명령 및 pss generation/session/readiness | v3 명령·Takeover 상태 필드 동시 이행 |
| `src/protocol.c:30-61,342-358,531-788,913-980,1017-1185` | session->client 단일 owner; pending owner check; conflict는 close_after_state; close는 pointer identity 확인 | 기존 check 유지, conflict offer와 명시적 CAS handoff 추가; old pss 분리 후 displaced 전송 |
| `xterm/addons/overlay.ts:31-117` | wrapper pointerdown이 action 실행; detail=0 click 경로; persistent overlay | 복구와 Takeover action 구분. Takeover는 버튼 확정에서만 실행; 배경 터치가 인계하지 않음 |
| `staging/check_reconnect.py:19-24,455-495,533-574,733-789` | 지정 binary/index, 실제 ttyd/PTy/Chrome/proxy, 원시 PTY capture와 20회 복구 | v3와 conflict 선택 의미로 이행; 실제 fixture/counters 재사용 |
| `staging/check_touch_resize.py:186-309`, `check_staging.py:293-342` | 에뮬레이션·term.input 직접 주입; 30px/blur 기대 및 구 초기 ready 가정 | 기대 계약 갱신. 이 결과를 Android IME/키보드의 대체 증거로 사용 금지 |

현행 핵심 해시: app `aac3f4c91c1f44dea7bb92d2e6bc1e73babbfe5add6101324af499470ce99eb6`; terminal UI `6475191099b7ab967544229db4570a9da7b7d684ffa43776cd645b9e0b6f71c9`; Xterm `26e50b6f129ec255a97364067666bccb7f796eb9b83a9a757ce7809cdcccfd9d`; template `abfbab70a8181255343e1bbc11bdda1222ead5a944459161cadee7d5aaa1e465`; stylesheet `53d1cd993b5e0359e006edce5df190ce225f42df6ed06b5a648624090329a917`; protocol `0f8dc3e9d4f268d8f3ffca4468e1142980e731db04583cbe1e90d5993b9d2638`; server.h `94b29ed39fb5dcd270310800a90486b7d77a0aedb33f04a75b7f4da2fc438c87`. 마지막 세 파일은 선행 검증의 해당 소스 해시와 같다. 작업 트리를 과거 커밋으로 되돌리지 않으며, 구현자는 변경된 load-bearing 파일만 재결속한다.

**EXISTING 의존성 근거:** 설치된 `html/node_modules/@xterm/xterm/src/browser/input/CompositionHelper.ts:61-206`은 compositionend 뒤 timer로 textarea 범위를 전송하고, 비조합 keydown에 조합을 즉시 확정한다. `CoreBrowserTerminal.ts:342-385,1021-1033`에는 textarea/element paste와 key/input/composition 처리기가 존재한다. 따라서 onData에 별도 compositionend sender를 덧붙이거나 이벤트 문자열을 시간 기준으로 dedup하는 방법은 선택하지 않는다. 같은 한글을 두 번 입력하는 정상 행위를 지우거나 Enter 제출을 누설할 수 있다.

## 3. PROPOSED — 입력 의도 소유자와 순서

Xterm 내부 한 owner가 `{modifier: none|shift|ctrl, focusIntent: inactive|typing, compositionTransaction, inputEpoch}`를 가진다. 기존 connectionGeneration/serverConnectionGeneration/inputReady를 읽고 복제하지 않는다. UI callback은 snapshot일 뿐 writer가 아니다. 이벤트 listener와 지연 callback은 disposable로 이 owner 수명에 귀속한다. 미확정 입력은 저장소/복구 큐에 보관하지 않는다.

### 3.1 분류와 포커스

1. capture 단계에서 복구/인계/일반 입력을 먼저 분류한다. non-ready recovery pointerdown은 기존 click 소비 latch를 유지하고 modifier/조합을 무효화한 후 local recovery만 요청한다. 연결이 click 전에 ready가 되어도 그 click은 끝까지 local이다. displaced에서는 복구 자체를 요청하지 않고 소비만 한다.
2. 본체 직접 탭 후보를 pointerdown에서 기록하되 아직 focus하지 않는다. scroll 이동, pointercancel, 선택/long press, link/overlay/file control 대상이면 취소한다. 유효 pointerup/click의 사용자 activation 안에서만 textarea focus; Shift 해제, CTRL 유지. xterm 기본 mouse/touch focus가 이 분류를 앞서지 않도록 본체 이벤트의 focus 경로를 통제하되 기존 scroll/selection/link 동작은 살린다. 읽기 조작을 막는 전체 preventDefault는 사용하지 않는다.
3. toolbar pointerdown은 버튼으로의 기본 focus 이동만 막는다. 이미 typing이면 textarea focus를 그대로 두고 blur/refocus/VirtualKeyboard.hide를 호출하지 않는다. inactive이면 focus 호출을 하지 않는다. click은 단 한 번 intent dispatch. native keyboard 실제 열림 여부를 focusIntent boolean으로 주장하지 않는다.
4. 페이지 초기/자동 reconnect/input-ready 완료는 자동 focus하지 않는다. hide, disconnect, owner loss, dispose에서 modifier를 중립으로, 조합 transaction을 invalid로, focusIntent를 inactive로 만든다. show/online/pageshow는 fit/liveness만 수행하며 typing을 복원하지 않는다. 사용자 직접 새 탭 입력은 새 intent다.

### 3.2 모디파이어 및 PTY 의미

| intent | owner 전이와 ready 세대에서의 PTY 효과 |
|---|---|
| Shift / CTRL | 동일 토글은 해제, 반대는 교체; 둘 동시 true 불가; PTY 0 |
| 본체 입력 탭 | Shift만 해제, CTRL 유지; 탭 자체 PTY 0 |
| TAB | modifier 먼저 소비: Shift이면 `ESC [ Z`, 아니면 `09`; CTRL 해제 |
| 방향키 | Shift이면 `ESC [ 1 ; 2 D/A/B/C`; 일반은 현재 `applicationCursorKeysMode`에 따라 `ESC O` 또는 `ESC [` + D/A/B/C; CTRL 해제 |
| 일반 단일 영문 | CTRL이면 A..Z를 01..1A로 1회 변환 후 중립. paste/IME provenance는 절대 이 분기를 타지 않음 |
| 다른 일반 입력 | 원문 정상 경로, pending modifier 중립; 비영문을 Ctrl 바이트로 바꾸지 않음 |
| Enter, 조합 아님 | 양 modifier 해제 후 `0D` 정확히 한 번; recovery이면 위 local 경로만 |
| ESC, 조합 아님 | 양 modifier 먼저 해제 후 `1B` 한 번. 이후 c는 `63`, `03`/SIGINT 없음 |
| font/fullscreen | local-only, pending modifier 해제, focus 보존, fit 요청; PTY input 0 |
| paste/compositionstart/hide/disconnect/인계 | 양 modifier 해제; 아래 transaction 규칙 |

모든 sendData/onBinary/addon sender는 동일 current socket + local generation + 서버 owner/inputReady gate를 통과한다. not-ready의 특수키/일반 입력은 보관하거나 다음 세대로 재전송하지 않는다. toolbar action의 modifier 결정은 비동기 Preact setState가 아니라 owner의 동기 snapshot을 읽는다.

### 3.3 조합·paste transaction

**선택 방법:** 제품이 textarea의 composition/paste/text-input transaction을 소유하고, 해당 DOM 사건의 xterm 기본 전송을 capture에서 차단한다. xterm은 터미널 렌더링과 비텍스트 키 시퀀스·모드 처리를 유지한다. private `_compositionHelper`를 monkey-patch하거나 node_modules를 수정하지 않는다. text transaction의 listener는 textarea의 조상 capture에 놓아 이미 등록된 xterm textarea capture보다 먼저 분류한다. 단순 onData 문자열을 조합/paste로 추정하지 않는다. 모바일 229 및 beforeinput/input도 동일 provenance로 처리하여 xterm의 delayed textarea diff 송신과 제품 송신이 공존하지 않게 한다. 일반 하드웨어 키/터미널 응답을 무작정 끊지 말고, 실제 DOM text transaction으로 소유한 입력만 기본 경로에서 제외한다.

- transaction key는 inputEpoch + connectionGeneration + server owner generation + 증가하는 local transaction sequence. compositionstart가 생성, update/beforeinput/input이 draft/range를 갱신한다. 중간 조합 문자는 PTY 0. textarea 값과 replacement 범위를 판독하며 compositionend.data 하나만 진실로 삼지 않는다.
- compositionend와 뒤따르는 final input은 같은 transaction을 settle한다. 현재 transaction/세대이며 취소되지 않은 경우에만 확정 UTF-8를 한 번 보내고 consumed로 만든다. 다음 정상 transaction의 같은 문자열은 별개 입력이다. 다음 조합 시작 전에 이전 확정 경계를 정리하여 한국어 종성 이동을 중복/누락하지 않는다.
- 조합 중 native Enter는 native IME 확정 효과를 허용하되 원격 CR/LF 송신을 차단한다. toolbar ↵ 역시 local commit-only intent이며 확정 문자열만 한 번 보낸다. native commit의 실제 방법과 사건 순서는 §7의 실기기 첫 관찰에 결속한다. synthetic key dispatch를 IME 확정 수단/증거로 쓰지 않는다. 확정 뒤 별도의 다음 Enter만 CR를 보낸다.
- 조합 ESC는 transaction을 **먼저 invalid**로 만들고 modifier를 해제한 다음 로컬 draft/textarea 조합을 취소한다. 원격 ESC/DEL/CR/LF 0. 이어지는 늦은 compositionend/input은 invalid transaction으로 버린다. textarea clearing/selection 변화가 실제 IME를 취소하는지는 §7에서 관찰하며 blur로 키보드를 닫아 성공으로 간주하지 않는다.
- paste는 길이와 관계없이 modifier를 먼저 해제하고 현재 draft를 정리한 후 clipboard 원문을 한 번 전송한다. 한글/여러 줄/한 글자 모두 Ctrl 변환 없음. xterm bracketed paste mode가 켜져 있으면 기존 mode semantics의 wrapper만 한 번 적용하고 payload를 중복 정규화하지 않는다. native paste와 이에 딸린 beforeinput/input은 한 transaction이다. clipboard 데이터가 제공되지 않는 IME paste는 실제 inputType/range 경로로 판정하고 미확인 시 성공을 만들지 않는다.
- toolbar TAB/방향키 접촉은 focus와 진행 조합을 유지하며 확정되지 않은 draft를 원격으로 강제 flush하지 않는다. 조합과 별개 특수키 intent의 바이트는 위 표대로 한 번만 보낸다. font/회전은 geometry만 갱신하고 draft를 재전송하지 않는다. hide/disconnect/Takeover/새 연결/소유권 상실은 inputEpoch를 올리고 pending commit을 폐기한다. 늦은 callback은 세대 비교 후 무효; 자동 재전송 없음.
- 보류 transaction은 완료/취소 후 해제하고 timer/listener는 dispose한다. 범용 이벤트 로그/입력 persistence는 추가하지 않는다. 시험 전용 관찰은 승인된 무해 문자열만 수집한다.

## 4. PROPOSED — 단일 viewport/geometry 경로

`template.html` viewport에 `interactive-widget=resizes-content`를 추가한다. layout viewport에 root가 맞도록 html/body/root의 높이를 한 계열로 연결하고 flex terminal이 toolbar를 제외한 실제 나머지 content box를 차지하게 한다. keyboard 높이 또는 visualViewport와 layoutViewport 차이를 다시 빼지 않는다. Safe Area 좌우/하단은 CSS 한 곳에서 적용하며 버튼 hit height와 별도로 계상한다.

Xterm의 공개 `fit()`는 coalesced requestAnimationFrame scheduler의 요청 함수가 된다. open, window resize, visualViewport resize/scroll(측정 트리거만), container ResizeObserver, fullscreenchange, font 변경, visibility 복귀, `window.term.fit` 및 applyPreferences font writer 전부 이 함수로 이행한다. 직접 fitAddon.fit 두 번 호출/미등록 RAF 경로를 없앤다.

scheduler 순서: visible + 양수 container content box 확인 → FitAddon으로 현재 cell metric에 맞는 cols/rows 계산·적용 → 양수 정수 결과만 `lastValidGeometry` 갱신 → 현재 owner ready이면 `(serverGeneration,cols,rows)` 중복 제거하여 resize 전송. 숨김/0 크기는 terminal resize/lastValid overwrite/서버 송신 모두 금지. layout이 변하지 않는데 fit이 observer를 다시 자극하면 동일 측정값을 건너뛴다. 무한 RAF 재예약 루프를 만들지 않는다.

handshake는 마지막 유효 geometry만 사용한다. 아직 유효 측정이 없으면 0을 송신하지 않고 첫 유효 측정까지 해당 attach를 기다린다(기존 attempt deadline 안). handshake에 실린 크기와 이후 ready 사이의 최신값이 같으면 재전송하지 않고, 달라졌으면 서버 input-ready 직후 최신값 한 번만 전송한다. 단절 중 geometry는 최신 하나만 보관한다. takeover의 신규 owner도 같은 규칙이며 서버 resize writer는 기존 current owner check/pty_resize 경로를 유지한다.

font는 기존 storage key를 유지하고 초기 props/storage/server prefs/query/toolbar writer 모두 동일 8..32 clamp를 거친다. owner/UI 실제 font를 동기화하여 저장값·label만 바뀌지 않게 한다. 8에서 A−, 32에서 A+는 값·fit·resize 변화 없음. fullscreen aria는 요청 성공 가정이 아닌 fullscreenchange/document.fullscreenElement에서만 갱신한다.

toolbar 순서와 기준 폭: TAB 33, Shift 30, 네 방향 각 29, Enter 32, ESC 33, CTRL 40, A−/A+ 각 29, fullscreen 29 CSS px; 합 371px. 390에서는 11개의 1px gap과 양끝 기본 3px padding을 포함해 388px. 높이 35px로 34..36 안에 둔다. 360/Safe Area에서는 flex-basis를 위 비율로 두되 shrink 가능, min-width:0, padding 우선 축소, label font는 읽을 수 있게 유지하여 같은 단일 행 전체가 들어가게 한다. 버튼 숨김/다중 행/가로 스크롤로 우회하지 않는다. 확대 텍스트의 실제 hit/label 충돌은 §7/§8 실기기에서 판정; 더 좁은 조건이 요구 의미를 바꾸면 Main/Thesis owner로 반환한다.

## 5. PROPOSED — wire v3와 서버 원자적 Takeover

v2 conflict의 자동 close를 억지로 재사용하지 않고 v3에서 명시적 요청을 추가한다. create/resume 의미와 기존 bounded owner check(prepare 2초, exact native Pong 10초)는 보존한다. storage version은 변경하지 않는다. wire v3는 client handshake, SET_SESSION_STATE, REPLAY_END 모두에 적용하고 v2/legacy는 spawn/입력 없는 명시적 mismatch로 거절한다. 운영 v2 실행물에는 v3 번들을 덮지 않는다.

- 서버 conflict 응답에는 실제 session diagnostic identity와 `ownerGeneration`을 포함한다. requester는 여전히 non-owner/non-ready. 응답의 connectionGeneration은 requester의 generation이지 owner generation과 혼동하지 않는다.
- 실제 충돌 connection을 사용자 선택용으로 유지한다. pss에 offer 대상 session identity와 관찰 ownerGeneration만 둔다. 세션 raw pointer를 오래 보관하지 않고 요청 시 현재 registry에서 다시 찾는다. conflict 관찰 자체는 소유권/geometry/grace를 변경하지 않는다. check timer는 기존대로 정리된다.
- client 명령 `TAKEOVER = '6'`: conflict connection에서 `{ownerGeneration, columns, rows}`를 한 번 전송한다. 이는 INPUT과 완전히 별개다. client는 전송 즉시 선택을 pending으로 바꾸며 중복 click/pointer를 소비한다. 일반 overlay 배경/toolbar ↵/retry/자동 복귀는 이 명령을 만들 수 없다.
- 서버 receive에서 인증·handshake 완료·conflict offer·현재 살아 있는 같은 session·offer ownerGeneration == 현재 session->client->connection_generation을 확인한다. 현재 owner가 없어졌거나 세대가 달라졌으면 **자동 takeover/resume/spawn하지 않는다**. 현재 사실의 conflict/unknown/expired/exited 또는 명시적 재확인 상태를 반환한다. 바뀐 owner에 대한 재확정은 새 사용자 선택이 필요하다.
- 성공의 linearization은 같은 event-loop callback 안에서: 경쟁 owner check를 정리하고 해당 대기 contender를 non-owner로 settle → old input_ready/session_accepted=false → old session/process 연결을 null로 분리 → session->client 비움 → 기존 attach_process로 requester를 같은 process에 붙임. old에는 `displaced` state를 queue하고 state가 전송된 뒤 old transport만 close한다. requester는 attached/replay → parser/render → SESSION_READY → input-ready 순서이며 그 전 입력 차단.
- old의 close/Pong/message/resize/SESSION_READY는 pointer+generation이 더 이상 현재 owner가 아니므로 효과 없음. callback이 새 client를 닫거나 expiry를 시작하지 않도록 기존 identity guards를 유지한다. 프로세스가 종료/세션이 사라졌으면 exited/unknown 경로만, spawn 금지. old notice 전송 실패는 인계를 rollback하지 않는다; 서버 단일 owner가 진실이며 old browser가 끊겨 notice를 못 받는 한계는 숨기지 않는다.
- 동일 offer의 동시 요청은 첫 valid CAS만 성공한다. 나머지는 stale conflict이고 사용자의 새 확인 없이 최신 owner를 가져오지 못한다. 동일 pss에서 중복 TAKEOVER는 이미 accepted/pending으로 no-op하며 attach/replay를 재시작하지 않는다. 새 third contender는 기존 pending owner-check 정책에 따라 non-ready로 settle되고 기존 owner를 바꾸지 않는다. third의 새 확인도 그때 받은 ownerGeneration에만 적용된다.
- 취소 버튼/뒤로가기/복제 탭 닫기는 offer connection/지역 timer만 닫으며 세션·원본·grace·spawn을 바꾸지 않는다. TAKEOVER 전송 뒤 취소/close는 이미 선형화된 인계를 되돌리는 약속이 아니다. 서버 readback으로 미전송 취소와 인계 후 단절을 구분하고, 후자는 신규 owner의 detach/grace이지 원본 자동 복권이 아니다.
- client `session-displaced`는 terminal state. 수신 즉시 inputEpoch 무효, modifier 중립, inputReady=false, fetch abort, heartbeat/retry/attempt 정리, local generation invalidation 및 socket listener 정리. 문구는 `세션이 다른 탭으로 이동되었습니다`. requestRecovery/beginRecovery/runRecovery/handleVisibilityReturn/sendHeartbeat/handleSocketClose/toolbar/overlay 전부 이 상태에서 새 contender를 만들지 않는다. 뒤늦은 promise finally나 replay callback이 상태를 덮지 못한다. 새로고침은 새 페이지의 명시적 충돌 판단이지 displaced 탭 내부 자동 재획득 루프가 아니다.

충돌 UI는 `세션이 이미 다른 탭에서 사용 중입니다`와 버튼 `이 화면으로 가져오기 (Take Over)`, 취소를 표시한다. OverlayAddon에 필요한 최소 다중 action/persistent message 지원만 추가한다. 복구 action의 기존 pointerdown 즉시 소비는 보존하되 takeover는 정확한 버튼 활성화에만 결속한다.

## 6. 변경 순서와 전체 cutover

1. 독립 Review/ADMIT 뒤 §7의 실제 Android 입력 사건 관찰만 먼저 수행한다. 무해 fixture, Main 승인 후보 route/서비스가 준비되어야 한다. 실제 IME가 방법을 반박하면 해당 입력 변경을 시작하지 않는다. 서버/CSS의 독립 소스 준비는 가능하나 불완전 조합을 노출하지 않는다.
2. `server.h`, `protocol.c`의 v3/offer/CAS/displaced를 구현하고 raw real-PTY ownership self-check. input gate/owner-check/replay 기존 함수를 재사용한다. 별도 session manager/새 process lifetime 계층 금지.
3. Xterm의 입력 owner·조합 provenance·single fit·Takeover/recovery terminal gate를 구현하고 terminal UI를 intent dispatch/snapshot 방식으로 동시 이행. app은 storage 의미 보존; 필요 일회성 요청 타입만 연결한다. overlay actions와 template/style/font writer를 함께 이행.
4. **모든 wire caller:** `staging/check_fresh_session.py`, `check_reconnect.py`, `check_protocol_edges.py`, `check_omp_reconnect.py`, `check_exit_lifecycle.py`, `check_server_hardening.py`의 v2 handshake/응답/replay 기대를 v3로 변경. legacy rejection 시나리오는 의도된 구 버전 입력으로 남기고 명시적으로 구별한다. conflict close/Retry 가정과 reload 후 old-close 재시도는 explicit offer/취소/안전 resume 의미에 맞춘다. wire helper 추상화를 새로 만들 이유는 없다.
5. **UI callers:** `check_staging.py`, `check_touch_resize.py`, `check_xterm6_compat.py`와 실제 `window.term.input/fit` 사용부를 점검하여 explicit create/input-ready 진입을 사용한다. 30px/blur 기대는 폐기하고 실제 hit height/focus 유지/8..32 검사로 교체한다. term.input 직접 주입은 키 시퀀스/PTY 보조 검사에만 남기고 IME 검증으로 표기하지 않는다. 최소 모바일 입력/Takeover 시나리오는 기존 staging 파일에 붙인다.
6. Main이 최종 한 번의 필요한 빌드/통합 validation을 관리한다. 구현자 scoped self-check는 실제 후보 binary + 실제 served bundle + 기존 launcher에서 수행한다. 내장 `src/html.h`, `staging/index.html`, `html/dist/inline.html`을 혼동하지 말고 실제 선택된 `-I` 파일/응답 hash를 기록한다. generated artifact는 기존 빌드 경로로 생성하고 손편집하지 않는다.
7. self-check가 성립한 뒤 `CUSTOMIZATION.md`의 wire v2, blur, font/toolbar/Takeover 설명과 후보 실행/실기기 한계를 현행화한다. stale alias/이중 modifier writer/직접 fit listener/중복 text sender를 제거하고 disposable을 연결한다. 이 Plan 작성에서는 이들 파일을 수정하지 않는다.

## 7. UNRESOLVED — 실기기에만 의존하는 조건부 첫 작업

**plan_anchor:** `PLAN-001.md §7` 및 §3.1/§3.3.

**permitted_initial_work:** 독립 ADMIT와 Main의 실제 후보 실행/임시 외부 경로 권한 확인 뒤, 구현자가 사용자 실제 Android Chrome/사용 한글 IME 버전·모델·CSS 폭/DPR/배율/Safe Area를 기록한다. 생산과 격리된 ttyd/PTy capture 화면에서 실제 한글 조립/종성 이동/후보/Backspace/Enter/ESC/한 글자 paste 및 toolbar 접촉의 native beforeinput/input/composition/key 사건 순서·textarea 범위·키보드 실가시 상태를 승인된 무해 텍스트로 한 번 판독한다. 현행 결손을 재확인하기 위한 재시험이 아니라 새 transaction 분류/commit/cancel 방식의 판별이다.

**discriminating_observation:** (a) native Enter가 commit을 끝내는 순서와 final textarea 범위, (b) toolbar commit-only 및 local cancel이 키보드 강제 닫힘 없이 동작하는 실제 수단, (c) 늦은 final input을 transaction에 귀속시키는 사건 경계, (d) scroll/selection을 훼손하지 않는 직접 탭 activation. 키보드와 후보창 화면 + 사건 순서 + PTY 최종 bytes를 함께 남긴다. xterm delayed sender가 우회하여 중복 송신되지 않아야 한다.

**dependent_work_not_yet_permitted:** 위 관찰 전에는 §3.3의 IME interception/commit/cancel 구현을 확정·활성화하거나 실기기 지원을 선언하지 않는다. 합성 composition/desktop emulation으로 이 gate를 닫지 않는다. 서버/CSS의 비활성 준비는 독립적으로 가능하다.

**response_if_refuted:** IME가 textarea/capture 기반 commit/cancel 또는 provenance 구분을 제공하지 않으면 관련 입력 구현 중단, 관찰을 Main/Planner에게 PARTIAL/BLOCKED로 반환하고 영향 방법을 재계획·독립 재검토한다. 키보드를 닫기/문자 누락 허용 같은 제품 의미 변경은 Thesis owner, 지원 폭·핵심 OMP 조작 부족은 Scope/Thesis owner로 반환한다. 프레임워크 교체나 IME별 추측 fallback은 자동 승인되지 않는다.

OMP는 사용자 제공 현재 버전 `18.2.0`을 전제로 한다. 실제 keymap과 장치 inventory는 검증 입력이며 이 문서에서 추정하지 않는다. 사용자 선택이 제공 조작으로 가능한지 실제 OMP 화면/설정에서 확인하고, 불가능하면 임의 단축키를 보내지 않고 의미 결손으로 반환한다. 아직 실행하지 않은 외부 후보 URL/포트/프로세스는 존재한다고 기록하지 않는다.

## 8. 실제 경계 증거 매핑 및 좁은 self-check

모든 행은 같은 최종 소스/binary/served bundle/launcher 해시와 실제 서버 instance에 귀속한다. raw PTY recorder는 fixture의 실제 slave 입력을 읽고, 셸/OMP 관찰은 실제 프로그램 화면/실행 결과를 읽는다. terminal onData 횟수나 client input-sent만으로 PTY 전달을 증명하지 않는다. raw capture와 OMP는 같은 후보의 별도 승인 fixture 세션을 사용할 수 있으나 session identity를 각각 기록한다. ancillary network proxy는 실제 전달 경로만 제어하며 서버/PTY 결과를 대체하지 않는다.

관찰 기본 한도: 일반 입력/IME commit 뒤 5초, geometry는 마지막 실제 전이 뒤 5초 안에 최종값 도달하고 추가 2초 안정(지속 resize 없음), attach/replay는 기존 30초 attempt, 자동 recovery는 실제 60초, owner check는 실제 2초 prepare + 10초 Pong, displaced 관찰은 최소 65초와 사건 반복. 이는 시험의 유한 관찰 한도이며 새 제품 SLA가 아니다. 초과는 timeout/미관찰로 남기고 성공을 추정하지 않는다.

| Scope Acceptance / Exit | Initial | Action | Authoritative readback | Window |
|---|---|---|---|---|
| 입력 포커스와 가상 키보드 / B2-E1 | 실제 Android 최초 진입 또는 auto reconnect; keyboard closed. 별도 typing+keyboard open, scrollback/선택/link 준비 | 직접 본체 탭, scroll/selection/link; open/closed 각각 TAB·네 방향 실제 touch; hide/show; manual overlay/↵ pointerdown~click 사이 ready 및 빠른 연속 tap | 실제 키보드/후보창 영상·focus·viewport·후속 한글 입력; scroll/selection/link 결과; recovery 전 capture armed/0 byte 확인, 후속 별개 문자열 1회 | 각 조작 5초, 실제 60초 소진 후 복구+후속 5초 |
| 모디파이어와 특수 키 / B2-E2, SC-3 | raw PTY fixture, ordinary/application cursor mode 각각; UI 중립/Shift/CTRL 각각 | 재토글·상호 전환; Shift TAB/네 방향; CTRL→body→영문; CTRL→ESC→c; Enter/ESC/font/fullscreen/hide/disconnect/takeover; not-ready 동일 keys | 위 §3.2 exact hex, UI aria snapshot 일치, c=63 및 03/SIGINT 없음; not-ready 0; application mode 화면과 bytes | 각 transition 전후 5초; mode별 분리 |
| 한글 IME·paste / B2-E3 | 실제 식별 IME, raw recorder armed 및 별도 실제 shell/OMP draft | 음절 조립/중간 수정/후보/Backspace/한영 전환; 한/여러 글자 paste; composing Enter와 ESC; toolbar/rotation/hide/disconnect/recover/takeover 교차; 늦은 실제 end/input | 최종 UTF-8와 의도 확정 문자열 1회; Enter commit에서 CR/LF·제출 0; ESC cancel 원격 ESC/제어 0; late event 중복 0, 후속 독립 입력 가능; 실제 shell/OMP 화면 대조 | native settle 후 5초; 단절은 recovery 전체+후속 5초 |
| 단일 기하 수렴 / B2-E4, SC-5 | 실제 served meta 확인, keyboard/candidate closed, 유효 geometry 기록 | keyboard/candidate open/close, 주소창 높이, 세로/가로, fullscreen in/out, 8/32 font, hidden/0, 단절 중 크기 변경 후 reconnect | layout/visual viewport와 container pixel, last-valid, xterm rows/cols, 실제 PTY TIOCGWINSZ/stty size 및 서버 적용 횟수/값; prompt/12 toolbar/OMP 화면; 0 전송 없음, ready 후 최신 한 번 | 마지막 사건 후 5초 수렴+2초 안정; ready 직후 비교 |
| 360/390 접근성 / B2-E5 | 실제 390/360 조건 각각; Safe Area/확대 텍스트/DPR 기록 | 12 버튼 각각 실제 touch; font 양끝 추가 click; fullscreen success/failure | bounding boxes height 34..36, scrollWidth<=clientWidth, elementFromPoint의 각 intended button, 겹침/잘림 없음, single row; label/aria와 실제 font/fullscreen 일치 | 각 layout 안정 후 5초 및 모든 hit 수행 |
| 명시적 Takeover/displaced / B2-E6, SC-8 | 실제 original ready+marker, root PID/starttime/diagnostic/gen/geometry/spawn 기준값; 같은 endpoint storage의 실제 duplicate | 먼저 cancel/back/close 각각. 새 duplicate에서 Takeover 1회/중복; 두 contenders 동시 확인; old close/Pong/message 지연 및 third; old visibility/online/pageshow/heartbeat/retry/toolbar 반복 | 확인 전 original input/resize 지속, contender input/spawn delta 0; 후 같은 root PID+starttime/marker/diagnostic, 새 owner만 input/resize, old terminal displaced; 서버 CAS/attach count와 양 탭 UI; stale offer가 최신 owner를 뒤집지 않음 | check 12초 이내+attach 30초; 성공 후 65초와 반복 사건, 별개 new-owner 입력 1회 |
| 실제 OMP 모바일 루프 / B2-E7 | 동일 후보/launcher의 실제 OMP 18.2.0, 현재 keymap 직접 판독; 하드웨어 키보드 없음 | body tap→한글/영문 편집→여러 줄 줄바꿈/제출 구분→TAB/방향 선택→의도 ESC/CTRL 취소→이전 출력 scroll/selection→font/rotation/fullscreen→duplicate takeover→다음 작업 | 실제 OMP 편집 내용·선택·제출 횟수·의도 취소·무해 실제 도구 실행과 그 결과; 이전/새 탭 소유권; 정적 startup 화면/프로세스 생존만으로 통과 금지 | 각 입력 5초; 실제 도구는 시작 전 승인된 유한 실행 한도 기록, 결과/대기/실패 분리 |
| 통합 보존 / B2-E7 및 Scope 마지막 문단 | final stable artifact, production 7683 기준 상태, 별도 fixture | BLOCK-001 SC-1~SC-4, 20회 recovery, replay/parser/input-ready, grace/drain/foreground 정상 입력; SC-3/5/8은 위 행 통합 | 같은 root PID/starttime·marker/no spawn, storage namespace, 0-byte recovery, 20회 generations/active listener·timer·socket 수; 실제 2분 Android lock와 network 전환; 생산 변경 없음/cleanup | 실제 2분 lock, 60초 manual, 각 30초 attempt, 20회 종료 뒤 정리 판독 |

Takeover raw race self-check는 자기 소유의 격리 candidate만 사용한다. late/duplicate ordering 보조 검사와 실제 Chrome 두 탭 확인을 구분한다. 원본 actual sessionStorage를 복제한 browser duplicate와 storage 없는 독립 새 탭을 모두 구별한다. unsupported 좁은 실기기 조건/IME 미지원/OMP 조작 불가는 미관찰 또는 의미 결손이지 자동 통과가 아니다.

증거 필수 필드: 관찰 시각/소유자, source/build/served/launcher hash, 장치 모델·Android/Chrome/IME 버전, CSS 폭·DPR·배율·Safe Area·방향·keyboard/candidate/fullscreen, OMP version/keymap, 비밀 아닌 session diagnostic ID, local/server connection generation, 실제 session-root PID와 `/proc/<pid>/stat` field 22 starttime, PTY 입력/resize 값과 화면. 원시 resumeId/token/실제 사용자 명령을 공개 보고서에 복제하지 않는다. server diagnostic에는 필요한 state/resize counter만 기존 opt-in 경로로 추가할 수 있고 상시 payload telemetry는 금지한다.

검증자는 성공한 self-check와 별개로 현재 안정된 후보를 직접 판독한다. 빌드/source가 바뀌면 영향 행을 같은 최종 대상으로 다시 귀속한다. missing Android는 desktop screenshot/synthetic composition/seeded state로 대체하지 않는다. 이 계획 작성은 어떤 행의 실행 성공도 주장하지 않는다.

## 9. 중단·정리·인계

IME 중복/누락/제출 누설, ESC 뒤 제어문자, 무단 인계/핑퐁, old event의 새 owner 변경, prompt/필수 버튼 가림, resize 진동/파괴, artifact/wire mismatch가 나타나면 해당 후보 입력/인계 시험을 중단한다. 실제 PTY/OMP 효과·현재 owner·last-valid geometry·미확정 입력을 먼저 기록하고 임의 재입력/자동 rollback하지 않는다. 방법 변경은 Planner와 독립 Review, 제품 의미는 Thesis owner, Scope 변경은 Main/Scope shaper에게 반환한다.

Main이 현재 권한 확인 후만 비7683 임시 loopback 포트와 필요 임시 외부 후보 route를 준비한다. 생산 `/home/user01/.local/bin/ttyd`, `/home/user01/.local/share/webterm/index.html`, 기존 `session.sh`, 7683 daemon 및 `/terminal` Funnel은 교체/재시작/입력하지 않는다. 후보의 외부 문서 hash·token·WS 양방향과 실제 device 연결을 별도로 판독한다. 이전 후보 route가 정리되었다는 사실은 새 route 생성 권한/준비 증거가 아니다.

구현자/검증자는 자신이 만든 Chrome tab/profile, websocket, proxy, RAF/timer/listener/observer, recorder 파일, 시험 PTY/자식 프로세스를 소유 목록과 함께 정리한다. Main만 자신이 만든 shared candidate service/route를 정리한다. 정리 전 존재와 PID/starttime/port/route를 기록하고 정리 후 실제 absence 또는 승인된 감독 상태를 확인한다. kill 반환만으로 회수 완료를 주장하지 않는다. 불명 소유 프로세스/실제 사용자 세션은 건드리지 않는다. 보존할 증거를 먼저 외부 evidence path에 저장·해시한 뒤 throwaway 파일만 제거한다.

최종 인계: 정확한 Plan/Review/Scope/source/build hash, §8 전체 결과와 미관찰 한계, 변경된 caller 목록, 실제 후보 identity/잔여 효과/책임자, 생산 보존 readback. 독립 Review ADMIT 전에는 구현 시작을 승인하지 않는다. 독립 Verification/Coverage와 Main의 종료 기록 전에는 Scope done 또는 BLOCK-003 계속을 선언하지 않는다.
