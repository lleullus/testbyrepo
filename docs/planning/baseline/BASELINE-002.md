# Transition Baseline `BASELINE-002`

Status: DRAFT
Project-Root: `/home/user01/project/webterm/ttyd-1.7.7`
Baseline-ID: `BASELINE-002`
Revision: `r1-2026-09-18`
Applicability: `webterm / ttyd-1.7.7`의 기존 `custom/android-mobile-toolbar`, 출발 커밋 `9246173` (`9246173177686762bcf7c2f6a4e6b864185fc38c`), 스냅샷 커밋 `e2cd5a1314215ad40cf8f5bb4aead00bdaf8fb4f`에서 `THESIS-002`의 견고한 세션 연속성·생존성과 v4 프로토콜 제품 결과로 이행하기 위한 조건부 전환 계약 초안. 이 정확한 리비전의 실행 범위가 승인되면 승인된 조건부 전환 계약으로 적용한다. 현재 권한은 문서 작성까지이며 구현·배포·Block 간 자동 계속을 승인한 상태가 아니다.

## Identity & Approval

Source Authority:
- Product meaning: `/home/user01/project/webterm/ttyd-1.7.7/docs/planning/product-thesis/android-web-terminal/THESIS-002.md`, `CALIBRATED`, `2026-09-18`, SHA-256 `3ac3c25dd0e520e0af1269dd5de32b100400b86872e76ec2704d9d9b22a0e067`. §1~5의 제품 약속·NB1~NB19·I1~I11, §6의 ST1~ST17, §7의 우선순위·비약속, §8의 권위 판독을 온전히 결속한다.
- Investigation: `/tmp/oracle-findings-and-investigation.md`, SHA-256 `d09035efe52fe103720832295e1ae5065096e953748c7e33029e8106540d68bd`. 1차 조사와 오라클 브라우저 1번 슬롯 GPT-5.6 Sol Pro 검토 전문이다. 스냅샷에 대한 정적 코드 추적·기존 스테이징 테스트 검토이며 실제 Android 패킷 캡처·discard 실험은 아니다. 임시 경로의 지속 보존을 보장하지 않으므로 실행 인계 시 해당 바이트의 가용성을 확인한다.
- Template: `/home/user01/project/iis-skills/iis-workflow/templates/BASELINE-NNN.template.md`, SHA-256 `834c90e0504a75d06e051c5bc5229ba0b1f1230b49f31fd8acbe42b481b0487c`. 절 순서와 필수 필드의 구조 권위이다.
- Previous Baseline: `/home/user01/project/webterm/ttyd-1.7.7/docs/planning/baseline/BASELINE-001.md`, `APPROVED`, `r2-2026-09-15`, SHA-256 `f3b389347779f21b4e0fa1cad49ab748d509181763acb13cd39152416baf27e1`. 원본을 불변 보존한다. BLOCK-001~BLOCK-003의 세션 복귀·모바일 조작·출력/결과/운영 경계를 계승하되 과거 승인, 완료 주장 또는 테스트 PASS를 새 의미의 현재 증거로 전용하지 않는다.
- Current instruction: `2026-09-18` 사용자 요청, 오라클 검토 결과 기반 테시스 확정 및 `BASELINE-002.md` 작성. 이번 직접 위임은 이 문서 생성과 문서 정합성 확인이며 코드 수정·빌드·린트·테스트 스위트 실행은 제외한다. BLOCK-004~BLOCK-006의 순서와 각 6개 Exit를 실행 가능한 계약으로 구체화한다.

Approval:
- Approved by: 문서 작성은 현재 사용자의 명시적 위임에 따른다. 전환 실행의 승인 소유자는 사용자이며 이 DRAFT의 실행 승인은 기록되지 않았다.
- Approved at / reference: `2026-09-18` 현재 문서 작성 요청. 이후 실행 승인이 있다면 이 정확한 원본 리비전과 승인 범위를 결속해야 하며 현재 요청을 그 승인으로 가장하지 않는다.
- Approval scope: 지금 허용된 결과는 Goal, R1~R9, G1~G8, P1~P7, BLOCK-004~BLOCK-006, 계속·중단·원자 경계가 채워진 초안이다. 실제 Scope 수립 이후의 계획·구현·독립 검증·운영 변경은 해당 단계의 현재 권한을 별도로 확인한다. 이 문서 자체는 미래 Scope를 ready로 만들지 않는다.
- Inter-Block auto-continuation authorized: `no`

적용에는 이 정확한 원본 리비전과 현재 권한이 모두 필요하다. 과거 파일 발견, THESIS-002의 CALIBRATED 또는 선행 Baseline의 APPROVED만으로 새 전환은 시작되지 않는다. 이 문서는 조건부 전환 계약이지 운영 모드, 요청서, 실행 커서, 상태 로그 또는 워크플로 저장소가 아니다. Main은 위임 범위에서 계약을 준비·정합화하되 범위 밖 선택은 승인 소유자에게 돌려보낸다. 결속된 과거 원본을 보존하며 불필요한 별도 승인 의식을 추가하지 않는다.

원본 해시는 이번 작성에서 실제 파일 바이트로 계산하여 대조했다. 운영 바이너리·브라우저·서버의 현재 상태나 결함 수정 여부를 이번 문서 작성에서 실측한 것은 아니다. 오라클 P0 번호는 브리핑의 **“누락된 중대 실패 경로”** 절에 고정한다: P0-1 retained 고착, P0-2 cursor 추월, P0-3 reaper 수명, P0-4 pruning. 브리핑 뒤쪽 적용 우선순위의 재번호와 혼용하지 않는다. storage discard가 항상 자격 소실이라는 주장, 모든 half-open이 2초 오류라는 주장, 모든 malformed ready가 visible에서도 영구 대기라는 주장은 채택하지 않는다.

## Transformation Outcome

Goal:
- THESIS-002 §1~8 전체 약속을 현행 브라운필드에서 실현한다. 유효 successor의 침묵 단절 **0 추가 Owner Check RTT 인계**, paint와 분리된 복구, 최신 8 MiB 비차단 출력과 명시적 GAP, P0 네 결함 및 P1 전송·수용·종료 경계의 해소, 기존 Android 모바일 조작을 같은 제품 루프로 성립시킨다. 정상 복구를 2초 generic error나 기존 소켓의 10초 Pong 대기로 끝내지 않는다.
- 호스트와 서비스가 가동 중이고 승인된 복구 자격이 남아 있는 동안 9시간 유예 내 동일 작업 또는 종료 결과로 돌아가며, parser 적용과 서버 준비 확인 뒤에만 입력을 연다. 손실·권한 변화·종료·회수 미완료를 새 셸이나 성공 UI로 감추지 않는다. “결함 없음”의 판정 범위는 결속된 의무와 ST1~ST17이며 모든 미래 장애가 없다는 무제한 보장은 아니다.
- 운영 대상은 Linux/WSL2, `/home/user01/.local/bin/ttyd`, `/home/user01/.local/share/webterm/index.html`, `/home/user01/.local/share/webterm/session.sh`, 포트 `7683`, Tailscale Funnel `/terminal`이다. 서비스/호스트 재시작을 넘는 메모리 세션 영속성, durable discovery, terminal snapshot, Windows 지원 확대나 외부 인증 신규 도입은 이 전환에 넣지 않는다. Successor Token은 외부 접속 인증의 대체물이 아니다.

Required Named Items:
- **R1 — v4 단일 소유권과 0 RTT successor 인계:** v4 HELLO의 `resumeId`, `intent`, `clientInstanceId`, `connectSequence`, `successorToken`, `replayPosition`, `columns`, `rows`; 서버의 `leaseEpoch`, `ownerClientInstanceId`, `successorTokenHash`, `ownerPhase`, `lastApplicationHeartbeat`, `lastProgressAt` 의미를 함께 구현한다. 승인된 binding/pending create를 분리하고 생성 응답 소실에도 중복 PTY를 만들지 않는다. 일회성 token 회전·재조회, epoch fencing, READY application lease, 즉시 CONFLICT, observed epoch CAS takeover, STALE/SUPERSEDED/재시도 가능한 BUSY와 유한 복구 admission을 포함한다. v3/v4 mismatch는 명시적으로 거절한다. NB1·NB6·NB12·NB13·NB17·NB19 → B4-E1·E2·E6, B5-E5, B6-E1·E4.
- **R2 — rAF 없는 복구 코어:** geometry·parser barrier·REPLAY_APPLIED의 필수 경로에서 rAF와 16ms polling을 완전히 제거한다. visible 유효 geometry, hidden 마지막 유효 geometry 또는 `80×24` fallback으로 진행하고 visible/ResizeObserver에서 보정한다. parser callback에 직접 결속한 취소 가능한 barrier, 실제 await를 깨우는 수동 선점, hidden 시간 제외 60초 전면 예산과 유예 내 저빈도 backoff, thaw/online 즉시 확인을 성립시킨다. 화면 갱신 전용 rAF까지 금지하는 뜻은 아니다. NB3·NB5·NB6·NB14 → B4-E3·E4, B6-E2·E3.
- **R3 — 8 MiB 순환 청크 버퍼와 GAP/rebase:** payload `8,388,608 bytes` 상한, 실제 circular/chunk 구조, 새 작은 출력마다 거의 8 MiB를 복사하는 sliding `memmove` 제거, PTY 연속 drain과 유한 reader/전송 메모리, replay 및 READY/PAUSE 이후 cursor 추월의 명시적 BUFFER_OVERRUN/GAP을 구현한다. 도달 불가능한 REPLAY_END, 미송신 cursor 전진과 조용한 applied 조작을 금지하며 새 barrier·중복 제거·degraded 선택을 결합한다. NB2·NB9·NB15·NB16 → B4-E4, B5-E1·E2·E6, B6-E1·E3.
- **R4 — 종료 결과와 새 emulator의 완전 분리:** P0-1을 닫는다. EXITED_RETAINED는 read-only replay 완료로 attempt를 정착시키고 언제든 Start New Session이 선점한다. 새 승인 세션 첫 출력 전에 화면·모드·parser·cursor·종료 플래그를 초기화하되 create 거절 시 기존 결과를 먼저 지우지 않는다. 연속적인 동일 세션 resume는 emulator 상태를 보존한다. NB5·NB9·NB11 → B4-E5, B5-E6, B6-E1·E3.
- **R5 — 단일 reap 권한과 비동기 참조 수명:** P0-3을 닫는다. `session_reaper` 중심의 단일 reap 결과 소유 경계를 확립하고 root waiter와 경쟁하는 `waitpid(-1)`를 없앤다. 실제 wait 수행 위치는 Plan이 정하되 동일 child를 두 경로가 수거하지 않으며 결과를 단일 소유 경계에 전달한다. session/process/viewer/libuv handle의 refcount 또는 동등한 소유권으로 마지막 callback/close까지 allocation을 보존한다. interior-pointer free, ECHILD/실패 status 해석, 늦은 exit callback UAF, 거짓 PURGED를 금지한다. NB11·NB18 → B5-E3·E6, B6-E1·E4.
- **R6 — 보존·pruning·수용 상한:** P0-4를 닫는다. N개를 허용하고 단순 초과 조건은 `retained > max_retained`다. 초과만으로 삭제 권한이 생기지 않으며 9시간 보호·삭제 자격·참조 안전성을 함께 만족해야 한다. 현재 exit callback과 viewer 연결 세션을 즉시 free하지 않고, 만료에 따른 분리도 통지/fencing·참조 종료 후 해제한다. detached·retained·회수 중 자원까지 계상하며 압박은 신규 create 거절로 다룬다. NB18·NB19 → B5-E4·E5·E6, B6-E4.
- **R7 — 준비 ACK/NACK와 전송 진실성:** 기존 `SESSION_READY`의 무응답 경로를 v4 `REPLAY_APPLIED → READY_ACK`와 원인별 NACK/종결 상태로 교체한다. position·JSON·phase·session·epoch·retained 상태 불일치가 silent deadlock을 만들지 않는다. server ready deadline은 frozen client와 독립적이고, OUTPUT write 실패/short write·제어 프레임 이후 미처리 작업에도 cursor·진행 사실을 정직하게 유지한다. NB13·NB15·NB16 → B4-E2·E4, B5-E2·E5, B6-E1.
- **R8 — Android 가치와 작업 생존 회귀 방지:** 키보드 viewport 압축, 390/360 CSS px·Safe Area의 단일 행 12요소, 의도적 본체 focus, 원샷 modifier, 한글 IME·paste 정확히 한 번 전달, 복구 제스처 PTY 0 bytes, foreground TUI 실제 redraw, 9시간 유예·결과와 비차단 drain을 보존한다. NB3~NB11, §4.5 → B4-E3·E5, B5-E1·E6, B6-E2·E3·E4.
- **R9 — 운영 감독과 동일 실행물 종단 판독:** 실제 Tailscale Funnel `/terminal`·`/terminal/token`·`/terminal/ws`, 단일 리스너, systemd 사용자 서비스·런처·환경, 실제 logrotate 대상/트리거/회전 후 기록을 대조한다. `CUSTOMIZATION.md`를 실제 설치·실행·기한·손실·재시작/중단 한계와 일치시키고 최종 같은 대상에서 ST1~ST17 및 전 의무를 판독한다. Thesis §7.2·§8, 선행 운영 경계 → B6-E1·E5·E6.

Candidate Named Items:
- 고정 크기 청크 배열의 ring index, bounded chunk deque 또는 동등한 실제 circular buffer는 R3의 세부 수단 후보이다. 실제 유한 순환 구조와 sliding memmove 제거는 필수이며 후보로 격하하지 않는다. 참조 청크 pinning에는 유한 상한과 GAP 전환이 필요하다.
- 일회성 토큰 해시 저장소와 승인 시도별 유한 결과 재조회 기록은 token 회전 응답 소실을 닫는 후보이다. 저장 위치·encoding·만료 방식은 Plan이 선택하되 raw token 로그 금지·동일 시도 수렴·하나의 owner는 필수다.
- attempt/session/epoch/target을 보유한 parser callback 배리어 구조체, AbortController 또는 동등하게 실제 대기를 깨우는 취소 primitive는 후보이다. 단순 generation 플래그 변경이나 rAF의 setTimeout 치환만으로 요구를 충족하지 않는다.
- refcount, 명시적 callback 소유권, embedded handle에서 parent를 찾는 해제 방식은 수명 보장 수단 후보이다. 실제 단일 reap·마지막 비동기 참조 뒤 해제는 선택 사항이 아니다. 시험 fixture의 fault injection 방식과 진단 카운터는 필요한 판독을 얻는 범위에서 Plan이 선정한다.

Completion Predicate:
- **동일하게 식별된 최종 소스·바이너리·실제 서빙 번들·런처·설정에서 B4-E1~B4-E6, B5-E1~B5-E6, B6-E1~B6-E6이 모두 관찰되고, R1~R9와 NB1~NB19·I1~I11·ST1~ST17이 빠짐없이 성립하며, G1~G8/P1~P7 위반과 필수 미관찰·미확정 효과가 없는 상태에서 실제 Android 외부 진입 → 동일 작업 → 단절/절전 → 정직한 출력·소유권 복구 → 의도한 입력 또는 종료 결과 열람 → 명시적 신규 세션/만료 회수의 전체 루프가 권위 판독으로 연결된다.** 서로 다른 빌드의 과거 PASS를 합산하거나 문서 작성 완료를 이 명제의 성립으로 기록하지 않는다.

Final Authoritative Readback:
- Surface / owner: 권한 있는 운영자가 실제 Linux 프로세스·세션·systemd·Funnel·로그를, 독립 검증자가 동일 안정 대상의 프로토콜·PTY·parser 및 Android Chrome/실제 IME/OMP 화면을 판독한다. 정상 실행 절차의 독립 Production Heuristic Probe는 검증 이후 같은 대상에서 관찰 공백과 비정상 경로를 조사한다. Main은 실제 귀속된 결과와 현재 권한을 종합하고 검증자의 의미 판정을 대신하지 않는다.
- Source / method:
  - source commit과 미커밋 차이, 실제 실행 바이너리·서빙 HTML/번들·런처·설정 해시, 서버 인스턴스와 관찰 시각을 결속한다. 외부 `https://desktop-balmtav-1.tail42cd28.ts.net/terminal` 및 그 token/ws 경로는 선행 운영 주소이며 B6 Entry에서 현재 라우트를 확인한다. localhost 정적 문서만으로 외부 성공을 대체하지 않는다.
  - 비밀값을 제거한 세션 진단 identity, process PID와 시작 시각, 소유 트리·PTY·foreground PGID, epoch/phase, OUTPUT byte range와 전송 결과, parser callback·barrier·ACK/NACK를 같은 사건 순서로 대조한다. HELLO 뒤 old-owner Ping/Pong 왕복이 없는 것이 0 추가 Owner Check RTT의 증거이다.
  - 통제된 출력 fixture의 원 bytes·최신 tail·최종 표식·종료 결과, GAP 누락 범위·rebase·새 target, 각 복구/인계/불완전 계속 제스처의 실제 PTY 0 bytes와 별도 명시 입력을 대조한다. bytes 수신·적용·paint를 분리한다. 실패 write와 중복 OUTPUT, reaper 지연 callback·uv close·pruning 상한의 실제 경계를 관찰한다.
  - 실제 Android의 버전·Chrome·IME·폭·Safe Area·화면 잠금/네트워크 조건을 기록한다. 9시간은 운영 `32,400초` 설정과 격리 기한 전/경계/후 관찰을 결합하고 실시간 9시간 대기 여부를 별도 명시한다. 단축/가상 시간 결과를 실제 9시간 장기 관찰로 바꾸지 않는다.
  - `systemctl --user cat/show/status`의 unit/주 PID/명령/환경/재시작 제한, 실제 7683 리스너, 회전 대상·권한·트리거·회전 후 새 기록·보존 상한을 `CUSTOMIZATION.md`와 대조한다. 기록은 실제 생성된 증거 경로·해시·관찰자·시각을 가지며 예정된 증거를 존재하는 것으로 참조하지 않는다.
- Claim limits: 소스 해시·빌드 성공·WS OPEN·native Pong·READY_ACK·SIGWINCH/kill 호출·systemd active·logrotate dry-run은 각각 전체 제품 성공의 단독 증거가 아니다. 0 RTT는 연결/인증/replay 지연 0ms가 아니며 8 MiB는 전체 프로세스 메모리 크기가 아니다. frozen JS의 진척, 동일 credential clone의 물리 탭 구별, 임의 TUI 유실 mode 복원, 자격 소실 뒤 자동 discovery, 서비스 재시작 간 영속성과 실측하지 않은 모든 기기·장기 무장애는 주장하지 않는다. 현재 문서는 위 판독을 요구할 뿐 수행했다고 선언하지 않는다.

## Global Invariants

- **G1 — 의미·승인·근거 경계:** THESIS-002와 현재 권한이 제품 의미·실행 한도를 결정한다. 과거 NB 번호를 새 Thesis에 기계적으로 적용하지 않는다. DRAFT, Block Exit, 배포, 독립 검증과 완료 기록은 별개다. 기존 사실과 목표를 분리하고 미실측·미승인·미존재 증거를 만들지 않는다. 우선순위는 Thesis §7.1을 따른다.
- **G2 — 세션 단일 귀속과 Successor Token 0 RTT 인계:** 승인된 같은 작업은 같은 세션/실행 개체로 돌아오며 임의 새 PTY로 대체하지 않는다. 유효 successor·증가 sequence의 원자적 소비, old epoch fencing, 새 epoch 확정으로 입력/resize 권위는 최대 하나다. application READY lease를 native Pong으로 대체하지 않는다. 다른 client는 명시적 CAS takeover를 거치며 credential clone도 승자는 하나이고 패자는 자동 탈환하지 않는다. pending create와 승인 binding·소실 자격을 구분한다.
- **G3 — 날조·중복 입력 배제 및 PTY 0 bytes:** 복구 탭·Enter·takeover·visibility·degraded 계속 선택은 PTY 0 bytes다. READY_ACK 전, retained/conflict/displaced/sync 상태는 입력을 큐에 쌓았다가 자동 제출하지 않는다. 미확정 과거 입력도 재전송하지 않는다. 입력 전송 요청, 실제 PTY 전달, 프로그램 실행 결과를 구분한다.
- **G4 — 유한 비차단 출력과 GAP 진실성:** disconnected/slow/paused/hidden viewer가 PTY drain을 막지 않는다. payload는 최대 8,388,608 bytes이며 참조·전송·재조립·진단 큐도 유한하다. cursor 추월은 명시적 GAP이지 출력 없음이 아니다. 실패/short write는 미송신 bytes의 cursor를 전진시키지 않으며 REPLAY_END는 도달 가능한 target만 선언한다. 실제 적용과 명시 rebase를 구분하고 누적 폐기량을 이번 resume 손실로 오인하지 않는다.
- **G5 — 복원 계층 진실성과 rAF 독립성:** Connected, Accepted, Replay Applied, Ready, 화면 완전 복원과 작업 성공을 구별한다. 프로토콜 gate에는 rAF/16ms polling이 없고 hidden JS는 fallback과 callback으로 진행한다. frozen 동안 서버 보존/ready deadline은 유지하되 클라이언트 실행을 약속하지 않는다. 연속 resume의 emulator는 보존하고 승인된 새 PTY는 첫 bytes 전에 분리한다. gap/reload로 mode가 불명하면 degraded·기본 입력 차단을 유지하며 명시적 불완전 계속 선택과 새 ACK도 완전 복원 선언이 아니다.
- **G6 — 모바일 입력·조작 결정성:** 자동 진입/복구는 키보드를 열지 않고, 입력 가능한 본체의 직접 탭만 typing focus를 얻는다. 타이핑 중 툴바는 키보드를 유지한다. Shift/CTRL은 배타적 원샷이며 ESC·paste·compositionstart·복구/인계의 정리 정책을 지킨다. IME Enter는 조합 확정, IME ESC는 로컬 취소이고 PTY submit/ESC를 날조하지 않는다. 프롬프트·12요소는 지원 폭·Safe Area·키보드 상태에서 보이며 실제 조작 가능해야 한다.
- **G7 — 기한·결과·자원 수명과 회수 권한 단일화:** 서버가 마지막 유효 lease 상실/단절을 확인한 때부터 32,400초 grace다. 살아 있는 유효 resume는 detach 기한을 취소하나 provisional 반복은 ready deadline으로 제한한다. detached root exit는 기존 기한, attached root exit는 종료 시점부터 9시간 결과 보존이며 열람은 연장하지 않는다. EOF/root exit/final drain/descendant reap은 별개다. 단일 reap 소유, wait 성공 여부, 마지막 callback/viewer/uv close 뒤 free를 지키며 신호 발송·timer 실패만으로 PURGED를 선언하지 않는다. N개 retained는 초과가 아니고 보호된 결과는 압박으로 퇴출하지 않는다.
- **G8 — 운영 일관성과 기존 세션 보호:** 바이너리·실제 번들·런처·설정·프로토콜·라우트가 같은 검증 대상이다. 혼합 v3/v4를 묵시적으로 운영하지 않는다. 후보 시험·감독/로그 변경은 기존 작업을 임의 종료하거나 결과/파일을 지우지 않는다. 재시작으로 메모리 세션이 사라질 수 있는 교체는 실제 영향과 권한을 먼저 확정한다. raw successor token·민감 입력·복구 credential을 운영 진단에 기록하지 않는다.

## Path Invariants

아래 제약은 재진입과 Block 경계를 포함한다. 브라운필드에 이미 알려진 결함이 있다는 사실은 출발 상태이지 불변식 충족 선언이 아니다. 새 활성 경로는 적용 불변식을 만족해야 하고, 미수정 기존 결함은 노출·영향을 명시하여 격리한다. 미수정 메모리 안전 결함이 있는 중간 후보를 일반 운영으로 승격하지 않는다.

- **P1 — 현행 원본 및 브라운필드 재측정:** 각 Entry에서 정확한 Baseline 리비전/권한·Thesis/조사 지문·현재 소스와 작업 트리·실행물 출처를 읽는다. `9246173`이나 스냅샷은 출발 근거이지 현재 작업 트리/운영 실행물의 동일성 증거가 아니다. 기존 변경을 보존하고 출발 커밋으로 강제 되돌리지 않는다. 조사 이후 달라진 load-bearing 경로만 재측정한다.
- **P2 — 순차 블록 경계와 교차 계층 책임:** BLOCK-004 → BLOCK-005 → BLOCK-006의 측정된 Exit 순서를 유지한다. 각 Block은 하나의 HARD_ATOMIC 완료 단위이며 미래 ready Scope/자동 작업 큐가 아니다. B4는 v4 wire 의미·GAP/NACK 소비·부당 READY 거절까지 책임지고 B5는 실제 버퍼/송신/수명 경계를 완결한다. “다음 Block 소관”을 이유로 현재 새 경로에 거짓 ACK나 UAF를 허용하지 않는다. B4/B5 중간 후보는 격리 검증/개발 인계이며 최종 운영 노출은 B6의 승인된 cutover에서만 한다. B4의 안전한 제한 실행조차 기존 결함 때문에 불가능하면 Exit를 주장하지 말고 승인된 순서/원자 경계 정합화로 돌아간다.
- **P3 — 연결 세대와 비동기 효과 격리:** fetch·backoff·geometry·parser·takeover 실제 대기를 취소하고 최신 로컬 의도 하나로 수렴한다. old epoch INPUT/RESIZE/ACK/heartbeat와 old attempt finally/close/callback은 새 owner·promise·cursor를 변경하지 못한다. 복구 pointerdown~click을 소비하고 overlay 제거 후에도 PTY로 관통하지 않게 한다. 사용자의 취소/conflict/displaced를 자동 탈환으로 바꾸지 않는다.
- **P4 — 기존 세션 보존과 시험 격리:** 기존 세션/결과/작업/기한은 권한 있는 운영자가 판독한다. 대량 출력·half-open·timer/write 실패·시간 단축·pruning·kill/reap·메모리 안전 시험은 승인된 별도 인스턴스·세션·포트/한도에서 한다. 생산 OMP에 임의 입력하거나 전역 kill·storage 삭제·작업 트리 초기화로 통과시키지 않는다. 시험이 크래시해도 기존 운영에 전파되지 않는 범위와 정리 주체가 필요하다.
- **P5 — 실행물과 상태 전환 결합:** v4 server/client·binding·token/epoch·barrier·입력 gate를 함께 활성화한다. 실제 서빙이 외부 HTML인지 내장 번들인지 읽고 디스크 교체와 실행 프로세스를 구별한다. buffer/GAP/rebase/degraded, exit/reaper/viewer/accounting도 맞물린 소비자를 함께 변경한다. 미완성 프로토콜이나 수명 모델을 파편 배포하지 않는다.
- **P6 — 결과와 미확정 효과 인계:** Block Exit별 실제 증거 경로/지문·환경·대상·관찰 시각, owner/epoch·출력/적용/rebase·기한·결과·회수 상태를 인계한다. 미확정 입력, token 승인, kill/reap, 재시작/배포를 완료로 바꾸지 않는다. 뒤 Block 변경이 앞 Block 의미에 영향을 주면 독립 검증자가 필요한 현재 증거를 판정하며 과거 PASS를 자동 유지하지 않는다.
- **P7 — 매개변수와 운영 전제의 출처:** v4, 80×24 fallback, 8,388,608 bytes, 32,400초, hidden 제외 visible 적극 복구 60초, 390/360 CSS px, 34~36px 높이, 8~32px 폰트는 결속값이다. heartbeat/lease/ready deadline·ACK/takeover timeout·backoff·회수 유한 대기·token 재조회 유지·세션/총메모리/fragment/admission 상한·로그 회전 수치는 Plan에서 실제 유한 값과 출처·반례 경계를 확정한다. “적절한 값”으로 Exit를 선언하지 않는다. 사용자 관리자/로그아웃/WSL/linger/로그 트리거 전제는 운영 판독 대상이며 권한 상승은 자동 허용되지 않는다.

## Transition Blocks

아래는 전환 이정표와 측정 명제이지 구현 체크리스트나 미래 Scope 승인 목록이 아니다. 현재 Main은 실제 상태와 권한에 맞는 Block을 재측정하여 원본 Entry/Exit/불변식/계속 경계를 현재 Scope에 결속한다. 선행 BLOCK-001~003 원본과 완료 이력은 바꾸지 않으며 그 제품 가치의 현재 보존 여부는 이 전환에서 다시 증명한다.

### Block `BLOCK-004` — v4 프로토콜·Successor Token 인계 및 rAF 제거 복구 코어

- **ID:** `BLOCK-004`
- **Name:** 단일 소유권·취소 가능한 parser 준비·종료 결과 분리를 갖춘 v4 복구 코어
- **Meaning Contribution:** A/B/C, P0-1 및 D의 binding 정직성, E의 새 세션 상태 혼합을 닫는다. R1·R2·R4·R7의 복구 계약과 R3의 GAP/barrier wire 의미를 실제 클라이언트·서버에 결합한다.
- **Order / Dependencies:** 이번 전환의 첫 Block이다. 기존 모바일·운영 성과를 보존하면서 v3 성공 기대값을 v4 의미로 전환한다. BLOCK-005에서 닫을 P0-2~P0-4 및 P1의 미해결 범위를 기록하고 후보는 격리 인스턴스에서만 판독한다. token/ACK UI만 바꾸고 서버 소유권을 옛 Ping 경로에 남기는 분할 완료는 없다.
- **Entry:** Main/현재 Scope 책임자가 원본 지문과 현재 protocol/xterm/app의 HELLO·binding·owner check·ready·recovery·retained 경로를 읽고 변경분과 알려진 결함을 구분한다. 구현/검증 소유자는 승인된 격리 서버·PTY 관찰·wire/파서 관찰 수단, 안전한 정상 종료/정리 경계, P7의 유한 lease/ready/attempt/재조회 값을 확인한다. 운영 변경 권한이 없는 경우 후보 경계만 다룬다. A/B/C·P0-1 및 ST1~ST3/ST6/ST9/ST11~ST13의 discriminating 관찰이 가능해야 한다.
- **Exit:** 같은 안정 후보에서 독립 검증자가 다음 여섯 명제를 서버·PTY·wire·parser/UI 증거로 판독한다. 메모리/overrun 미해결 경로를 피한 검증은 그 제한을 명시하며 전체 제품 또는 운영 안전의 증거로 사용하지 않는다.
  - **B4-E1:** HELLO v4로 승인된 binding과 pending create가 구별된다. create capacity 거절/reload/storage 거부·소실·승인 응답 drop에서 nonexistent binding 확정, 자동 기존 작업 복구 주장, 동일 생성 의도 중복 PTY가 없다. 유효 successor는 같은 세션/작업을 old socket writable/Pong 대기 없이 새 epoch로 인계하고 old epoch INPUT/RESIZE/ACK/heartbeat를 거절한다. 원문 token 비기록, 명시적 version mismatch를 함께 확인한다. ST1·ST13.
  - **B4-E2:** 다른 client의 유효 READY lease에는 즉시 CONFLICT, 명시적 takeover에는 observed epoch CAS를 적용한다. epoch 변경은 STALE, epoch가 같고 old socket만 close된 경우는 takeover 가능이다. token 소비 직후 승인 응답 소실/동시 contender는 같은 승인 시도 재조회에서 동일 결과 또는 이미 확정된 최신 epoch로 수렴하고 owner는 하나다. 최신 유효 동일-client contender는 이전 pending을 SUPERSEDED로, 다른 contender 포화는 retryable OWNER_CHECK_BUSY/retryAfterMs로 정착시킨다. displaced/superseded는 자동 탈환하지 않으며 ATTACHING/REPLAYING과 takeover/응답 대기는 유한하다. idle 무출력 셸은 그 사실만으로 실패하지 않는다. ST2·ST11.
  - **B4-E3:** geometry 없는 hidden-but-JS-running 시작에서 80×24, 있으면 마지막 유효 크기로 HELLO를 보낸다. rAF를 호출하지 않는 조건에서도 parser callback 후 REPLAY_APPLIED/READY_ACK까지 진행하고 visible/ResizeObserver에서 실제 geometry로 보정한다. frozen 동안 서버 drain·ready deadline이 독립 작동하고 thaw/visible/online 뒤 오래된 대기를 정리하여 즉시 확인한다. hidden 시간은 60초 전면 예산을 소진하지 않고 visible 예산 소진 뒤에도 수동 복구와 유예 내 저빈도 backoff가 살아 있다. ST3.
  - **B4-E4:** SESSION_ACCEPTED→OUTPUT→REPLAY_END→parser callback→REPLAY_APPLIED→READY_ACK 순서, session/epoch/target 일치와 ACK 전 입력 차단을 실제 bytes로 확인한다. callback barrier는 취소 가능하고 rAF/16ms polling에 의존하지 않는다. wrong position/JSON/owner/phase/old epoch/retained ready는 NACK·SYNC_REQUIRED/POSITION_MISMATCH·종결 상태로 유한 정착하며 silent break가 없다. 도달하지 못한 target을 applied로 날조하거나 정상 READY를 보내지 않고 GAP 수신은 옛 barrier/입력 권한을 폐기한다. full overrun/rebase의 완결은 B5-E1·E2에서 판독한다. ST9.
  - **B4-E5:** retained replay 진행 중과 완료 후 Start New Session이 실제 대기를 선점하고 retained read-only 완료는 READY_ACK 대기로 남지 않는다. 승인된 새 PTY 첫 bytes 전에 emulator·cursor·parser·종료 플래그가 분리되어 새 ACK 후 실제 입력이 성공한다. create 거절은 이전 결과 화면을 보존하고, 연속 resume는 alternate/mouse/DEC mode를 함부로 reset하지 않는다. 새 세션 선택이 기존 작업의 명시적 종료나 유예 단축으로 변하지 않는다. ST6.
  - **B4-E6:** parser/fetch/backoff/takeover 중 Reconnect·Start New Session 연속 선택이 최신 의도 하나로 수렴하고 실제 await가 풀린다. 옛 finally/timeout/socket close/callback이 새 promise/socket/cursor/권한을 지우지 않는다. 복구·인계 제스처의 실제 PTY 수신은 0 bytes이고 입력 불가 때 누른 키와 미확정 과거 입력은 나중에 제출되지 않는다. 서버·클라이언트 리비전, v4 사건, 생성/owner/PTY 관찰이 같은 후보에 귀속되고 미해결 B5 의무와 격리 효과가 명확하다. ST12.
- **Invariants:** G1~G3·G5·G6·G8, P1~P7을 직접 충족하고 G4·G7의 보존 의미를 회귀시키지 않는다. 알려진 버퍼/수명 결함은 해결된 것으로 표시하지 않으며 B4의 새 경로에서 노출되면 안전한 Exit가 아니다.
- **Continuation:** B4-E1~E6, 프로토콜/오류/epoch/barrier 의미, binding/token 재조회 정책과 비밀 제거 근거, 미확정 효과 부재, B5 대상 결함과 제한 노출을 인계한다. 후보 효과가 정착하고 Safe Continuation·B5 Entry 및 새 실행 권한이 성립해야 다음 Block을 시작한다. 이 DRAFT로 자동 계속하지 않는다.
- **Abort:** 중복 PTY/owner, 정상 successor의 Ping 대기·generic error, stale callback 오염, PTY 입력 누설, 부당 READY, retained 고착, 관찰 중 UAF/미상 자원 수명이 나타나면 변경 소유자가 후보의 신규 입력/인계/시험을 중단한다. 안전 목표는 기존 운영에 영향을 주지 않는 격리·진단 보존이다. 서버 owner/epoch·PTY/작업·pending 승인/입력·callback/프로세스 판독 없이 재시도/재시작으로 성공을 만들지 않는다. 실제 운영 containment는 권한 있는 운영자 경계다.
- **Insufficient for Exit:** v4 상수나 token 필드만 존재, 0ms 시계값, native Pong, mock ACK, rAF를 setTimeout으로 치환, hidden desktop 화면만으로 frozen 복귀 주장, retained flag 한 줄 변경, await를 깨우지 않는 generation, 새 프롬프트만 확인, 서버 결과 없는 로컬 ready boolean.

### Block `BLOCK-005` — 8 MiB 순환 청크 버퍼·GAP 동기화 및 라이프사이클/리퍼 메모리 안전성 확립

- **ID:** `BLOCK-005`
- **Name:** 비차단 출력의 진실성과 결과·참조·회수 수명을 함께 닫는 서버/클라이언트 경계
- **Meaning Contribution:** P0-2·P0-3·P0-4와 P1 write/admission/fragment/timer/EOF 경계를 닫아 R3·R5·R6, R7의 전송 진실성과 R8의 유예/생존을 완결한다. E의 TUI 손실 한계를 정상 READY와 구분한다.
- **Order / Dependencies:** B4-E1~E6과 격리된 v4 후보가 선행한다. wire GAP·NACK·degraded 소비자를 그대로 결속하여 실제 buffer/lifetime 효과를 완성한다. 메모리 안전 우선순위를 지키고 정상 운영 승격 전에 모든 P0/P1 의무를 닫는다. reaper/root wait·pruning/viewer·출력 참조 변경을 독립 완료로 쪼개지 않는다.
- **Entry:** Main/검증자가 B4 증거와 현재 target을 대조하고 구현자는 output append/send/PAUSE·RESUME, `lws_write` 결과, root waiter/`session_reaper`, uv close·process ctx·viewer 참조, expiry·pruning·수용·재조립 전체 경로를 판독한다. 격리 crash/fault 시험과 메모리 오류 관찰 수단, 원 출력과 tail을 대조할 fixture, session별 소유 트리·실제 수거 경계를 확보한다. P7의 buffer 외 메모리/fragment/admission/회수 한도와 삭제 자격을 실제 값/정책으로 결속한다.
- **Exit:** 독립 검증자가 같은 안정 후보의 실제 OUTPUT/PTY·프로세스/참조·오류 결과를 결합하여 다음 여섯 명제를 확인한다.
  - **B5-E1:** 실제 circular/chunk buffer가 8,388,608 bytes 이하 최신 payload를 보존하고 sliding 8 MiB memmove를 제거한다. 단절·slow·hidden·PAUSE에서도 알려진 10 MiB 이상 fixture의 생산자는 계속 drain되어 끝 표식/정한 결과에 도달한다. reader가 덮인 bytes를 정상 출력으로 내보내거나 pinning/전송 큐로 메모리를 무한 유지하지 않는다. replay와 READY 이후 양쪽에서 cursor 추월 시 BUFFER_OVERRUN·누락 범위·현재 보존 범위를 보내고 옛 target을 버려 rebase/new barrier로 최신 출력 진척을 회복한다. 반복 과부하는 명시적 상태/재시도/새 세션 선택으로 정착하며 영구 spinner가 아니다. ST4·ST5.
  - **B5-E2:** OUTPUT `[start,end)`는 원 PTY byte offset이다. 연속 적용, 겹친 prefix 제거, 완전 중복 무시, 앞선 start의 GAP을 각각 확인한다. write 실패/short write에서 미송신 bytes만큼 cursor가 앞서지 않고 실제 적용 확인 위치로 복구한다. REPLAY_END는 해당 sync 구간에서 실제 송신된 도달 가능한 target만 갖는다. 손실 bytes를 applied로 조용히 올리지 않고 rebase로 표시하며 누적 dropped bytes와 이번 손실을 구분한다. gap/reload의 UTF-8/escape/mode 불완전은 고지·기본 입력 차단을 유지하고 [불완전한 화면에서 계속]도 PTY 0 bytes 및 새 ACK 뒤 제한적 입력만 허용한다. ST4·ST5·ST10·ST14.
  - **B5-E3:** root exit와 expiry/reaper·지연 async exit·uv close가 경합해도 child별 wait/reap 결과 소유자가 하나다. `waitpid(-1)`가 root waiter 결과를 가로채지 않고 실패/ECHILD를 유효 exit status로 해석하지 않는다. embedded timer parent는 close 완료 전에 free되지 않고 close에서 정확한 allocation을 한 번만 해제한다. process ctx/session/viewer/청크 등 모든 비동기 참조 종료까지 refcount 또는 동등 수명 증거가 있으며 실제 경합 관찰에서 UAF/interior free/double free가 없다. 실제 소유 트리 회수와 무관 세션 보존도 함께 확인한다. ST7.
  - **B5-E4:** retained 상한 1과 N의 바로 아래/동일/초과에서 정확히 N개는 허용하고 조건은 `retained > max_retained`다. 초과는 즉시 삭제 명령이 아니라 삭제 자격 검토이며 보호된 결과/현재 exit callback/연결 viewer를 free하지 않는다. 삭제 자격 없는 기존 결과는 보존하고 추가 자원은 create admission에서 거절한다. 만료 viewer는 명시 상태·fencing·참조 종료 후 해제하여 `pss->session` dangling이 없고 계상이 실제 buffer/process/retained 자원과 일치한다. ST8.
  - **B5-E5:** half-open으로 `--max-clients`를 채워도 유한한 추가 판정 경로가 유효 successor HELLO를 받아 기존 세션 교체를 판단하며 무제한 신규 연결을 허용하지 않는다. fragmented message의 재조립 총량을 제한하고 초과를 명시 거절하면서 선정한 정상 paste/control 범위는 보존한다. expiry/reaper timer 초기화·시작 실패는 진단·추적 가능한 실패/TERMINATING 상태이고 살아 있는 트리를 registry에서 지우지 않는다. Ping 등 control frame 뒤 pending heartbeat reply/state/output은 다시 진행되어 우연한 외부 이벤트를 기다리지 않는다. ST15 및 NB15.
  - **B5-E6:** EOF·root status·마지막 PTY read 순서를 뒤집어도 최종 tail/종료 코드 또는 신호/미확인 상태/하위 프로세스를 따로 판독한다. detached exit는 기존 deadline, attached exit는 종료부터 32,400초를 유지하고 retained 열람·실패 재시도는 연장하지 않는다. 만료와 resume 경합은 단일 상태 판정이고 취소된 옛 timer가 새 owner를 죽이지 않는다. SIGHUP→유한 대기→SIGKILL 후 실제 트리·reap·PTY/FD·handle/callback·참조가 정리된 경우만 PURGED이며 미확인은 TERMINATING/회수 실패로 남는다. B4의 token/ready/retained/수동 복구 의미가 같은 후보에서 보존된다. ST7·ST8·ST16.
- **Invariants:** G1~G8, P1~P7 전부. 최신 출력·손실 고지·실제 수거·참조 해제·보존 기한은 한 상태 모델이며 한쪽 성공으로 다른 실패를 상쇄하지 않는다. 값이 유한하다는 주장에는 실제 계상 경계가 필요하다.
- **Continuation:** B5-E1~E6, 영향받은 B4 현재 검증 근거, buffer/wire/메모리 상한, 단일 reap/참조 수명/삭제 자격/기한, 시험 효과 정착과 기존 운영 비영향을 인계한다. B6 실기기/운영 권한·유지보수 경계와 Safe Continuation을 확인한 뒤에만 운영 cutover를 준비한다. 기록된 후보 안전성은 운영 배포 권한이 아니다.
- **Abort:** UAF·interior free·잘못된 reap·보호 결과 삭제·미추적 worker·unbounded 메모리·PTY drain 정지·불가능한 END·거짓 PURGED가 관찰되면 격리 시험/후보 노출을 중단하고 해당 소유자는 참조/결과/프로세스 근거를 보존한다. 안전 목표는 위험 후보의 추가 효과 억제와 기존 서비스 보존이며, 아직 살아 있는 트리를 성공으로 지우지 않는다. 정리 신호는 승인된 시험 소유 범위만 대상으로 한다. OS identity/참조/출력/기한/계상 판독이 없으면 Safe Abort 미완료다.
- **Insufficient for Exit:** ring이라는 이름의 sliding buffer, 상수 8 MiB, exit 0만 나온 대량 출력, `>=`를 `>`로만 바꿈, free 한 곳 삭제, refcount 필드만 추가, sanitizer 정상 종료 한 번만으로 실제 경합/수거 생략, kill 반환값, 목록에서 session 삭제, ACK mock, fragment 한 조각의 크기 검사, timer start 요청 로그.

### Block `BLOCK-006` — 안드로이드 실기기 통합 검증·ST1~ST17 및 운영 문서/감독 cutover

- **ID:** `BLOCK-006`
- **Name:** Android 실제 사용자 루프와 호환 운영 실행물을 결합한 최종 인수 경계
- **Meaning Contribution:** R8·R9를 완결하고 최종 실행물에서 R1~R7 및 모든 NB/I/ST를 재결속하여 전체 Completion Predicate를 판정한다. 기존 BLOCK-001~003의 모바일·결과·운영 가치는 현행 증거로 보존한다.
- **Order / Dependencies:** B4/B5 Exit 및 안전 인계가 선행한다. 실제 운영 교체·서비스 제어·Funnel/로그 설정 변경은 권한 있는 운영자의 구체적 승인과 기존 작업 영향 판독 후에만 실행한다. 실기기나 운영 권한 부재는 필수 Exit 미관찰이지 desktop/mock 대체 승인 사유가 아니다.
- **Entry:** Main/검증자/운영자가 최종 후보 identity와 선행 증거, 실제 Android·Chrome 108+·한글 IME·OMP/keymap·지원 폭/Safe Area·잠금/망전환 수단을 확보한다. 실제 binary/HTML/런처/7683/Funnel route/unit/logrotate와 운영 중 세션·결과·기한을 판독한다. 교체 시 메모리 세션을 유지할 수 없다면 작업 종료/결과 인수 또는 명시적 영향 수용 등 승인된 유지보수 경계 전에는 재시작하지 않는다. 로그·재시작 정책의 유한 값과 운영자 readback 경로를 결속한다.
- **Exit:** 같은 최종 배포 대상에서 독립 검증자와 권한 있는 운영자가 다음 여섯 명제를 판독한다. 운영에서 파괴적 fault를 직접 주입하지 않아도 동일 산출물의 격리 경계 증거와 실제 운영 통합 판독을 구분·연결해야 한다.
  - **B6-E1:** 아래 ST1~ST17 대응표의 모든 반례에 판정·실제 근거·환경·대상 identity가 있고 미해결 실패/필수 미관찰이 없다. NB1~NB19·I1~I11·R1~R9와 B4/B5 Exit를 같은 최종 target에 추적한다. 단순 PASS 목록이 아니라 서버 권위·PTY·parser·기기/프로세스 판독이 각 주장에 연결된다. 정상 IIS 실행 경로에서는 독립 검증의 VERIFIED와 이어진 독립 Probe COMPLETE/미해결 Scope-material finding 없음이 실제 기록되어야 하며 Main이 이를 문서 존재로 대체하지 않는다.
  - **B6-E2:** 실제 Android에서 자동 진입/복구는 키보드를 열지 않고 Ready 본체 탭만 typing focus를 얻으며 타이핑 중 툴바는 키보드를 유지한다. `interactive-widget=resizes-content`와 xterm rows/cols가 키보드·후보창·회전·주소창·전체화면·8~32px 폰트 변화에 수렴한다. 390 CSS px의 단일 행 12요소와 34~36px hit 높이, 360px 이하·Safe Area의 양끝 조작, 가로 스크롤 없는 노출을 실제 화면/터치로 확인한다. 한글 조립·수정·확정·Enter/ESC·한 글자 paste, CTRL→ESC→c에서 중복 문자/submit/SIGINT가 없고 의도한 PTY bytes만 한 번 전달된다. ST17 및 NB4·NB7·NB8·§4.5.
  - **B6-E3:** 실제 화면 잠금·앱 전환·절전 복귀·Wi-Fi/LTE 전환과 통제된 FIN/RST 없는 단절에서 같은 작업·epoch·출력/ACK 루프를 확인한다. hidden JS 진행과 frozen 서버 보존/thaw 복구를 구분하고 수동 Enter/Reconnect는 PTY 0 bytes다. 실제 OMP/지원 TUI의 동일 크기 재접속·foreground `TIOCGPGRP`/SIGWINCH·normal/alternate/mouse/application cursor mode를 읽는다. SIGWINCH 무시·gap/reload 상태는 불완전을 유지하고 명시적 계속 선택을 검증하며, 신호 발송만으로 복원 성공을 판정하지 않는다. ST1·ST3·ST6·ST12·ST14.
  - **B6-E4:** 운영 32,400초 구성과 격리 기한 전/경계/후·재접속/만료 경합을 연결한다. detached 작업의 연속 drain·실제 진행/종료·최종 결과, retained read-only 열람과 무단 새 PTY 0회, 열람 비연장, 새 세션 독립성·참조/트리 회수를 확인한다. capacity는 detached/retained/회수 중 자원까지 계상하고 신규 create 거절이 기존 보호 작업에 영향을 주지 않는다. 실제 장시간 관찰과 가상/단축 시간 증거의 범위를 명시한다. ST7·ST8·ST13·ST15·ST16.
  - **B6-E5:** 실제 운영 binary·서빙 bundle·런처·환경이 검증된 v4 조합이고 systemd 사용자 서비스가 단일 7683 리스너를 감독한다. 외부 `/terminal`, `/terminal/token`, `/terminal/ws`에서 실제 Android 양방향 복구/입력 루프를 완료한다. 승인된 안전 경계에서 정상 시작/중단·예기치 않은 종료 후 재시작 제한과 메모리 세션 비보장, WSL/로그아웃 전제를 판독한다. logrotate는 실제 생성 로그·실행 주체/스케줄·권한·회전 후 새 기록·유한 보존을 갖고, 관계없는 빈 파일/dry-run으로 대체하지 않는다. 별도 인증/외부 노출 범위를 임의 변경하지 않는다.
  - **B6-E6:** `CUSTOMIZATION.md`의 설치·기동·업데이트/중단·가능한 되돌림, 실제 경로/설정, v4/version mismatch, successor/lease/자격 소실, GAP/degraded, read-only retained/새 세션, 9시간·capacity·reap 실패·운영 감독/logrotate 진단이 실제 실행물과 일치한다. raw token을 기록하지 않는 운영자 인수 근거와 미확정 효과 부재를 확인한다. Final Authoritative Readback과 Completion Predicate가 같은 target으로 닫히며 남은 필수 항목을 향후 작업으로 넘기지 않는다.
- **Invariants:** G1~G8, P1~P7 전부. 실기기 없는 UI 통과, 실제 route 없는 종단 통과, 서비스 재시작으로 사라진 세션의 복구 성공 선언은 금지다. 제품 검증과 운영 효과 승인·정착을 구분한다.
- **Continuation:** 후속 구현 Block은 정의하지 않는다. 전체 Predicate·독립 검증/Probe·효과 정착·현재 권한을 확인한 Main이 인수/완료를 기록한다. 목표가 남으면 정확한 의무와 원본·현재 target·재진입 경계를 남기고 완료라고 하지 않는다. 이 계약은 무기한 자율 운영이나 다음 기능을 승인하지 않는다.
- **Abort:** 실제 입력/IME 누설, 소유권/출력/결과 거짓 표시, 기한 위반·타 세션 손상, 혼합 배포·route 오접속·중복 리스너·무제한 restart/log, 기존 작업 영향 불명이면 운영자와 변경 소유자가 승인된 범위의 후보 활성화/시험/cutover를 중단한다. 안전한 기존 감독 유지 또는 승인된 유지보수 상태가 목표이며 무조건 restart/rollback하지 않는다. 실제 세션·결과·트리·unit/PID/binary/bundle·로그·Funnel 판독으로 정착을 입증한다.
- **Insufficient for Exit:** desktop viewport 에뮬레이션, 한글 완성 문자열 paste만의 IME 증명, static `/terminal` 200, localhost WS만 성공, unit active·회전 설정 파일만 존재, 과거 ST PASS 합산, 새 빌드에 이전 검증 자동 적용, 운영 문서만 변경, 단축 시간으로 실제 9시간 지속 주장, 권한/기기 부재를 통과로 표시.

ST1~ST17 의무의 1차 해결 경계와 최종 판독 연결:

| Thesis 반례 | 1차 해결 Exit | B6에서 보존해야 할 구별 증거 |
| --- | --- | --- |
| ST1 침묵 단절 successor | B4-E1 | 동일 작업·새 epoch·old fence, old-owner 왕복 없음 |
| ST2 다른 owner/CAS | B4-E2 | CONFLICT, epoch 변경 STALE, 동일 epoch/owner close 후 명시 인계 |
| ST3 hidden/frozen | B4-E3·E4 | rAF 없는 fallback/parser ACK, frozen 서버 deadline, thaw 복귀 |
| ST4 replay overrun | B5-E1·E2 | 정확한 누락 범위·옛 target 폐기·rebase/new barrier |
| ST5 READY PAUSE overrun | B5-E1·E2 | 생산자 계속 실행·RESUME 이후 최신 출력 또는 명시 반복 손실 |
| ST6 retained/new | B4-E5 | read-only settle·수동 선점·첫 bytes 전 reset·새 실제 입력 |
| ST7 reaper/exit/close | B5-E3·E6 | 단일 wait 결과·참조 생존·메모리 오류 부재·실제 트리 회수 |
| ST8 retained N/viewer | B5-E4 | N 허용·보호 결과 유지·viewer/callback dangling 없음 |
| ST9 invalid applied | B4-E4 | 원인별 응답/종결·server deadline·old epoch ACK 무효 |
| ST10 write/duplicate | B5-E2 | 미송신 cursor 보존·prefix/완전 중복 제거·bytes 일치 |
| ST11 token 응답 소실/경쟁 | B4-E2 | 같은 승인 수렴·단일 owner·STALE/BUSY·자동 탈환 없음 |
| ST12 preemption/callback | B4-E6 | 실제 await 취소·최신 의도·old finally 무효·PTY 0 bytes |
| ST13 storage/create | B4-E1 | pending/승인 구분·중복 스폰 없음·자격 소실 명시 |
| ST14 mode gap/redraw | B4-E5, B5-E2 | 연속 mode 보존·새 PTY 분리·degraded 선택·실제 TUI |
| ST15 admission/fragment/timer | B5-E5 | 유한 successor 경로·총량 거절·실패 자원 추적 |
| ST16 EOF/exit/final/tree | B5-E6 | final bytes·진실한 status·하위 트리·결과와 회수 분리 |
| ST17 Android/IME/viewport | B6-E2 | 실제 화면/hit 영역·한 번의 한글·정확한 PTY bytes |

## Safe Continuation

Safe Continuation Predicate:
- 현재 Block의 모든 Exit가 동일 안정 대상에서 관찰되고 적용 불변식 위반이 없으며, 후보/시험/입력/인계/회수/배포 효과가 종료되었거나 실제 소유자·유한 상태·기한을 가진 감독 아래 있고, unknown 비멱등 효과와 파편 cutover가 없으며 다음 Entry에 필요한 원본과 현재 증거가 가용한 상태만 인계 가능하다. 기존 운영 세션을 인계를 위해 종료할 필요는 없지만 identity·owner·deadline·출력/결과·감독자는 확인되어야 한다. B4의 알려진 B5 결함은 격리 후보의 미해결 의무로 인계하며 운영 안전/전체 완료로 이름을 바꾸지 않는다.

Required handoff facts and readbacks:
- 실제 Block/Scope와 Exit별 판독, 적용 계획/독립 검증 및 수행된 Probe의 실제 기록 경로·지문·한계, source commit/작업 트리·binary/bundle/런처/설정·환경/기기/IME/OMP와 관찰 시각을 전달한다. 아직 수행되지 않은 역할/판독은 수행됨으로 쓰지 않는다.
- 서버 인스턴스·비밀 제거 session identity·client/epoch/phase·sequence/승인 시도 상태, PID/시작 시각·소유 트리/PTY/PGID, output_start/end·send/applied·GAP/rebase/target, retained/exit/기한·reap/ref/uv close 상태를 필요한 범위에서 전달한다. raw credential·사용자 명령을 복제하지 않는다.
- 진행 중 입력·승인 응답·취소 callback·timer·재시작/배포·kill/reap·시험 프로세스의 정착 또는 안전 감독 증거를 전달한다. 불확실한 입력/소유권 효과를 blind retry하지 않는다. 다른 세션과 기존 결과가 보존되었는지 실제 판독을 포함한다.
- 남은 R1~R9/NB/I/ST와 G/P 제약, Block별 후보/운영 노출 범위·미관찰 시간/기기 경계, 다음 Entry의 현행 재측정 항목·증거 가용성·필요 권한을 넘긴다. 앞 Block PASS 유지 여부는 바뀐 대상에 대해 검증 소유자가 결정한다.

Successor authority:
- 현재 문서 작성 요청의 계속 한도는 이 DRAFT 저장까지다. `Inter-Block auto-continuation authorized: no`이므로 Exit나 안전 상태만으로 후속 실행을 시작하지 않는다. 이후 적용 가능한 명시적 지시가 있으면 그 단계·중단·외부 효과 한도와 실제 host capability 안에서만 계속한다.
- 후속 소유자는 이 파일의 `r1-2026-09-18` 원본, Identity & Approval의 정확한 THESIS-002·템플릿·조사/이전 Baseline 지문, 현재 사용자 권한, 실제 target/효과/handoff 근거를 받아야 한다. 존재하는 현재 Scope/Plan도 정확한 원본으로 전달한다. 과거 Baseline 승인이나 권고된 실행 명령을 successor 시작 증거로 쓰지 않는다.

관찰된 위험이 없다는 사실은 Safe Continuation 증명이 아니다. predicate 또는 필수 readback이 미상이면 자동 인계하지 않는다. 안전 경계가 성립해도 현재 `no`는 계속 허가로 변하지 않는다.

## Safe Abort

Trigger:
- 무단 인계·중복 PTY·다중 owner·PTY 날조/중복 입력, 불가능한 REPLAY_END·숨긴 GAP·거짓 ACK/복원/종료, PTY drain 정지·무한 메모리, UAF/interior free·잘못된 reap·보호 retained 퇴출·기한 위반·미추적 자원이 관찰된다.
- 혼합 실행물/프로토콜·route/리스너 불일치, 승인되지 않은 운영 변경, 소유 범위 불명 kill/reap·입력/승인/재시작 효과 불명, 원본 충돌 또는 필수 readback 부재 때문에 안전한 다음 조치를 선택할 수 없다.
- 정상 통신 단절·정직한 GAP/degraded·capacity 거절·입력을 기다리는 OMP·아직 돌아오지 않은 grace 세션은 그 자체로 서비스 전체 종료 사유가 아니다. 원래 보호/감독을 유지하고 미완료 Exit와 구분한다.

Authorized safe target state:
- 후보의 신규 위험 입력/인계/배포/파괴적 시험이 억제되고 기존 정상 서비스·사용자 작업·출력/결과·기한이 확인된 감독 아래 유지되는 상태. 시험은 승인된 자기 소유 범위만 유한하게 정리하며 미회수는 추적한다. 자원 위험으로 그대로 유지할 수 없으면 운영자 승인 범위의 신규 수용 억제/유지보수 상태로 제한한다.
- 호환 실행물·설정이 보존되고 현재 세션과 호환됨을 판독한 범위에서만 되돌림을 선택한다. token 소비/epoch 변경, 이미 입력된 명령, 유실 출력, 종료 프로세스와 메모리 세션은 파일 복사나 restart로 자동 복구되지 않는다. 무손실 rollback을 약속하지 않고 현재 영향과 미확정 효과를 보존한다.

Owner and action boundary:
- 구현/시험 소유자는 자신의 허용 후보 경로와 격리 fixture만 중단·정리한다. 실제 daemon·Funnel·systemd·계정/권한·운영 세션의 종료/교체는 현재 Main 또는 운영자의 구체적 권한이 필요하다. 이 계약의 Abort가 새로운 외부/파괴적 권한을 만들지 않는다.
- 전체 sessionStorage·결과/작업 파일 삭제, 무관 프로세스 종료, 무단 권한 상승, 인증 추가, 다음 Block 시작을 중단 조치로 포장하지 않는다. 의미 변경은 Thesis 소유 경계, 전환 순서/원자 경계 변경은 Baseline 권한, 기술 방법 변경은 현재 Plan/독립 검토, Scope 의미 누락은 Main의 정합화 경계로 돌린다.
- 누설 입력·신호·승인 응답 소실 이후 추가 재시도는 실제 효과 판독 전 안전하다고 간주하지 않는다. 현재 문서 작성 단계에서는 운영 containment를 직접 실행하지 않는다.

Authoritative readback:
- 실제 unit/주 PID/리스너/binary/bundle/route, 세션 owner/epoch·output/applied/GAP·retained/exit/deadline, 소유 트리/PID 시작 시각·wait 결과·PTY/FD/uv close·callback/viewer 참조·자원 계상을 읽어 안전 목표와 대조한다. stop/kill 명령 반환과 테이블 삭제는 실제 종료 증거가 아니다.
- 입력/인계 사고는 승인된 범위의 실제 PTY·셸/OMP 결과·서버 승인 상태로 확인한다. 모르는 제출/실행 여부는 미확정으로 남기며 재실행하지 않는다. 진단·원본·사용자 파일과 기존 결과 보존, 추가 위험 효과 억제를 함께 확인한다.
- 전체 안전 목표를 입증할 수 없으면 `Safe Abort 미완료`로 남기고 정확한 잔존 효과·책임자·마지막 관찰 시각·읽지 못한 경계를 보고한다. 미관찰을 자원 없음이나 안전함으로 치환하지 않는다.

## Atomic Boundary

`HARD_ATOMIC`은 분할 불가능한 cutover를 하나의 Scope 안에 유지한다. 내부 기술 단위는 독립 완료 제품 Scope가 아니며 중간 상태의 제품 인계를 허용하지 않는다. 안전하고 지속 가능한 독립 경계가 새로 관찰되면 기존 계약/권한을 정합화한 뒤에만 분리를 선택한다.

- **BLOCK-004 — HARD_ATOMIC:** v4 HELLO·승인 binding·token 회전/재조회·lease epoch/old fence·application lease·CAS/contender 결과, fallback geometry·실제 취소·parser barrier/ACK/NACK·input gate·retained/new emulator 분리를 하나의 호환 코어로 완결한다. 새 client만 노출하고 서버 대응을 다음 Scope로 넘기거나 ACK보다 먼저 입력을 활성화하지 않는다.
- **BLOCK-005 — HARD_ATOMIC:** 실제 8 MiB ring/chunk·send 결과/cursor·GAP/rebase/new barrier·degraded 정책·PTY drain, root/EOF/final 결과·단일 reap·refcount/uv close·viewer pruning·admission/fragment/timer failure를 호환 상태로 함께 완결한다. buffer 교체만 완료로 넘기거나 free와 callback 소비자, retained 계상과 보존 의미를 분리 배포하지 않는다.
- **BLOCK-006 — HARD_ATOMIC:** 동일 binary/bundle/런처/unit/환경/로그·7683/Funnel 경로, 실제 Android/ST 판독과 `CUSTOMIZATION.md`, 기존 세션 영향·승인된 유지보수·효과 정착을 하나의 운영 인수 경계로 결속한다. 디스크만 새 파일이고 프로세스/브라우저는 구버전인 상태, route 미확인, 파괴 효과 미확정을 중간 배포 완료로 넘기지 않는다.
- 세 Block 전체가 하나의 분산 트랜잭션이라는 뜻은 아니다. B4/B5의 독립적으로 확인된 격리 Exit는 개발 인계 경계이고 B6 이전의 일반 운영 배포 허가는 아니다. 내부 컴파일/fixture 준비·일시 중단은 제품 완료나 후속 Block 진입으로 세지 않는다. 분할되지 않은 cutover 도중 실패는 Safe Abort로 실제 효과를 정착시키며 자동 rollback을 가정하지 않는다. 현재 안전성이 순서 변경을 요구하면 사용자 지정 BLOCK-004→005→006을 조용히 바꾸지 말고 승인된 전환 경계를 먼저 정합화한다.

## Placement and Use

원본 저장 위치는 `/home/user01/project/webterm/ttyd-1.7.7/docs/planning/baseline/BASELINE-002.md`, 프로젝트 상대 경로는 `docs/planning/baseline/BASELINE-002.md`, 리비전은 `r1-2026-09-18`이다. 현재 상태는 DRAFT이며 문서 작성 위임만 결속되어 있다. 전환 실행에 채택할 때 현재 Scope의 Transition Authority에서 정확한 원본/리비전/적용 권한을 참조하고, 결속된 과거 Baseline·Thesis·완료 이력은 수정하지 않는다.

이 문서에 실행 커서·진행 로그·미래 Scope 큐를 쌓지 않는다. 필요한 Scope/Plan/검증 기록은 실제 생성된 원본에서 이 계약을 참조한다. Baseline은 일반 IIS 작업의 필수 모드가 아니며 배포·외부 효과·후속 실행 권한을 현재 지시와 실제 host capability 이상으로 확대하지 않는다. 이번 산출물의 완료는 완전한 전환 계약 파일의 저장과 문서 정합성 확인이며, 여기서 정의한 제품 전환의 완료·실기기 검증·운영 cutover 수행을 뜻하지 않는다.
