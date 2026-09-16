# Scope: Mobile Touch, Keyboard, and Takeover Interaction

Schema: iis-scope/v1
Project-Root: /home/user01/project/webterm/ttyd-1.7.7
Status: done

## Product Authority

- /home/user01/project/webterm/ttyd-1.7.7/docs/planning/product-thesis/android-web-terminal/THESIS-001.md sha256:81003a0783df4f7876ad603aafd47c1b96ba768cec03237ed72e543ce9eb642a

## Transition Authority

- /home/user01/project/webterm/ttyd-1.7.7/docs/planning/baseline/BASELINE-001.md sha256:f3b389347779f21b4e0fa1cad49ab748d509181763acb13cd39152416baf27e1

## Outcome

`BLOCK-001`은 동일 소스 대상에서 독립 검증 `VerifyLunaR3`의 `VERIFIED`, 독립 Coverage `CoverageLunaR3`의 `COMPLETE`·material finding 없음, 후보 효과 정리와 `Status: done` 기록까지 완료했다. 현재 서버와 클라이언트에는 명시적 create/resume, 살아 있는 소유자 보호, bounded owner check, 세대별 단일 복구, replay/render/input-ready 단계와 복구 제스처 PTY 차단이 존재한다. 이 호환 계약과 운영 7683의 기존 세션은 보존 대상이다.

현재 모바일 입력 표면은 12개 툴바 요소를 갖지만 모든 툴바 pointerdown과 대부분의 버튼 동작이 터미널을 blur하고 가상 키보드 hide를 시도한다. 터미널 본체 pointerdown은 Shift뿐 아니라 CTRL도 해제하며, 조합·붙여넣기·지연된 composition 사건을 이 제품의 입력 상태와 연결해 판정하는 단일 소유 경로가 없다. 실제 문서의 viewport meta에는 `interactive-widget=resizes-content`가 없고, 폰트 범위는 10~30px, 툴바 높이는 30px여서 결속된 8~32px·34~36px 정책과 다르다. `BLOCK-001`의 충돌 화면은 살아 있는 원본을 보호하지만 명시적 Takeover와 이전 탭 displaced 종결 상태는 아직 없다.

이 Scope는 승인된 Transition Baseline `r2-2026-09-15`의 `BLOCK-002` 전체를 `HARD_ATOMIC` 모바일 입력·인계 활성화 경계로 전달한다. 실제 사용자가 터미널 본체를 직접 탭할 때만 입력 포커스와 Android 가상 키보드를 획득하고, 타이핑 중 툴바 조작은 키보드를 닫거나 재호출하지 않으며, 비입력 상태의 툴바·자동 복귀는 키보드를 열지 않는다. Shift/CTRL 원샷, ESC, paste와 실제 한글 IME 조합을 하나의 입력 의도 상태로 결속한다. 실제 레이아웃 viewport와 xterm geometry는 키보드·후보창·회전·전체화면·폰트 변화에 수렴하고, 390/360 CSS px 및 Safe Area에서 12개 조작 접점이 보이고 눌린다. 복제 탭은 서버 소유권과 결합된 명시적 Takeover만 허용하며 이전 탭은 displaced 뒤 자동 재획득하지 않는다. 실제 OMP `18.2.0`의 현재 keymap과 실제 Android Chrome·사용 IME 환경에서 하드웨어 키보드 없이 핵심 조작 루프가 성립해야 한다.

포함 범위는 Thesis NB4·NB7·NB8, I3, §4.1~4.4, SC-3·SC-5·SC-8과 Baseline B2-E1~B2-E7, 적용 G1~G3·G5·G6·G8 및 P1~P7이다. BLOCK-001의 NB10 입력 누설 금지, 단일 소유권, 세대 격리, replay/input-ready와 기존 9시간 grace·비차단 drain·foreground resize·정상 입력을 회귀시키지 않는다.

BLOCK-003의 최신 8 MiB tail 절사 고지, 종료 결과 보존, 소유 워커 회수, 수용 상한, systemd/logrotate와 운영 cutover는 제외한다. NB3의 전체 TUI 동일 크기·오버플로 후 화면 복원 완결도 BLOCK-003에 남기되, 이번 Scope의 현재 viewport rows/cols 전달과 실제 OMP 화면 조작은 관찰한다. 운영 바이너리·번들·7683 daemon·Funnel 교체는 이 Scope의 기본 실행 수단이 아니며 먼저 격리된 호환 후보와 명시적으로 승인된 임시 외부 후보 경로에서 검증한다.

## Acceptance

### 입력 포커스와 가상 키보드 소유권

실제 Android Chrome의 식별된 기기·버전·사용 IME에서 후보 페이지 최초 진입과 자동 재연결은 터미널 textarea에 포커스를 주거나 가상 키보드를 열지 않는다. 입력 준비 상태에서 사용자가 터미널 본체의 입력 의도 영역을 직접 탭하면 포커스와 키보드가 열리고, 스크롤·선택·링크 조작은 입력 탭으로 오인되지 않는다. 키보드가 열린 채 TAB과 네 방향키를 실제 터치하면 포커스·조합 가능 상태와 키보드가 닫힘/재열림 없이 유지된다. 키보드가 닫힌 상태의 툴바 조작, 화면 복귀와 재연결은 키보드를 열지 않는다. 수동 복구 오버레이/툴바 ↵의 pointerdown부터 click까지는 여전히 로컬 복구로만 소비되어 PTY delta가 정확히 0이다. 포커스 DOM 상태만이 아니라 Android 키보드의 실제 가시 상태, viewport 변화, PTY 바이트와 후속 입력 가능 상태를 함께 판독한다.

### 모디파이어와 특수 키의 결정적 전이

Shift와 CTRL은 동시에 활성화될 수 없고 UI 표시와 입력 라우터의 상태가 항상 일치한다. Shift는 TAB 또는 방향키 한 번에만 적용되고, CTRL은 다음 유효한 단일 영문 입력에 제어 바이트를 한 번만 적용한 뒤 중립으로 돌아간다. CTRL을 켠 뒤 터미널 본체를 탭해도 CTRL은 유지되지만 paste·compositionstart·연결 단절·소유권 인계에서는 해제된다. ESC는 조합 중이 아닐 때 원격 `\x1b`를 정확히 한 번 보내면서 Shift와 CTRL을 모두 해제한다. 따라서 CTRL → ESC → `c`는 `0x03`이나 SIGINT가 아니라 일반 `c`가 된다. Shift+TAB, Shift+네 방향키, xterm application cursor mode의 일반 방향키, 재토글, Enter, ESC, A−/A+, 전체화면, page hide/show, 단절/복구 전이를 실제 PTY 바이트·모드·UI 상태로 구분하며, 입력 준비 전에는 어떤 특수 키도 PTY로 관통하지 않는다.

### 한글 IME 조합·붙여넣기 무결성

실제 Android Chrome과 사용 중인 한글 IME에서 음절 조립, 중간 수정, 후보 선택, 조합 중 Backspace, 한/영 전환 및 한 글자·여러 글자 붙여넣기의 최종 확정 문자열이 실제 PTY와 셸/OMP 입력 화면에 정확히 한 번 나타난다. 조합 중 Enter는 IME 확정만 수행하고 CR·LF나 셸/OMP 제출을 만들지 않는다. 조합 중 ESC는 Shift/CTRL과 로컬 미확정 조합을 취소하며 원격 Escape를 보내지 않는다. paste는 길이가 한 글자여도 CTRL 대상이 아니고 무장된 모디파이어를 먼저 해제한 뒤 원문 텍스트를 한 번 보낸다. 조합 도중 툴바 접촉, 화면 회전, visibility 변화, 연결 단절/복구 또는 Takeover가 끼면 아직 확정되지 않은 텍스트를 자동 재전송하거나 이전 연결 세대에 보내지 않는다. 늦은 `compositionend`/`input`도 중복 문자·명령·제출을 만들지 않는다. DOM 이벤트 횟수만이 아니라 최종 PTY UTF-8 바이트, 화면 문자열, CR/LF·ESC·제어문자 수와 제출 횟수를 대조한다.

### 키보드·회전·전체화면의 단일 기하 수렴

실제 서빙 문서의 viewport meta에 `interactive-widget=resizes-content`가 적용된다. 실제 Android에서 키보드와 한글 후보창을 열면 레이아웃 viewport, 터미널 컨테이너, xterm rows/cols와 서버에 적용된 최신 유효 크기가 유한 시간 안에 한 경로로 수렴하여 현재 프롬프트와 12개 툴바가 키보드 위에 보인다. 키보드 닫기, 주소창 높이 변화, 세로/가로 회전, 전체화면 진입/해제와 폰트 8~32px 경계에서 viewport를 이중 차감하거나 빈 영역·무한 resize 진동을 만들지 않는다. 숨김 또는 0 크기는 마지막 정상 크기를 덮어쓰거나 서버로 전송되지 않고, 단절 중 계산된 최신 유효 크기는 재연결 후 현재 소유자에게 한 번 적용된다. CSS 선언이나 resize 호출 성공만이 아니라 실제 viewport/container 픽셀, xterm rows/cols, resize 횟수·최종값, 현재 프롬프트/툴바 가시성과 실제 OMP 화면을 판독한다.

### 360/390 CSS px 툴바 접근성

390 CSS px 세로 화면에서 Thesis §4.1 순서의 12개 요소 `TAB / Shift / ← / ↑ / ↓ / → / ↵ / ESC / CTRL / A− / A+ / ⛶`가 가로 스크롤 없이 한 행으로 모두 보이고, 각 실제 hit 영역 높이는 34~36 CSS px이다. 360 CSS px, 실제 Safe Area inset, 확대된 시스템/브라우저 텍스트 조건에서도 양 끝 요소를 포함한 버튼이 잘리거나 겹치지 않고 각각의 intended hit target만 작동한다. 폰트는 8px와 32px를 포함한 경계에서 더 이상 감소/증가하지 않으며 전체화면 상태와 aria 상태가 실제 화면과 일치한다. bounding box·elementFromPoint·scrollWidth/clientWidth와 실제 Android 터치를 함께 확인한다. 지원 범위를 넘는 더 좁은 실제 조건이 나오면 기능을 몰래 숨기거나 다중 행으로 의미를 바꾸지 않고 한계를 명시하여 재진입한다.

### 명시적 Takeover와 displaced 종결

살아 있는 원본 탭과 같은 endpoint-scoped storage를 가진 실제 복제 탭을 연다. 원본 연결·입력·resize와 세션 루트 PID/starttime은 유지되고 복제 탭은 서버가 확정한 충돌 상태와 명시적 `이 화면으로 가져오기 (Take Over)` 선택을 표시하며 Takeover 전 PTY 입력과 spawn delta는 0이다. 취소·뒤로가기·복제 탭 닫기는 세션을 종료·생성·이전하지 않고 원본을 계속 입력 가능하게 둔다.

사용자가 복제 탭에서 Takeover를 한 번 확정하면 서버가 현재 소유권 세대에 결속하여 정확히 한 번 인계한다. 새 탭만 입력·resize 소유자가 되고 동일 세션 진단 ID, 루트 PID/starttime, 화면 표식과 최신 유효 geometry를 유지한다. 이전 탭은 `세션이 다른 탭으로 이동되었습니다`라는 terminal state를 표시하고 입력 준비가 아니며, visibility/online/pageshow/heartbeat/retry/toolbar 사건이 반복되어도 자동 재획득하거나 새 contender를 만들지 않는다. 지연된 old close/Pong/message, 중복 Takeover click, 두 탭의 동시 Takeover와 새 third contender도 최종 단일 소유자를 뒤집거나 새 연결을 닫지 않는다. 양 탭의 서버 연결 세대·소유자, PTY 입력/resize, spawn 수와 사용자 화면을 함께 판독하며 팝업 문구만으로 통과하지 않는다.

### 실제 OMP 모바일 작업 루프와 통합 보존

동일한 후보 서버·번들·런처와 실제 OMP `18.2.0`/확인된 keymap에서 하드웨어 키보드 없이 터미널 본체 탭, 한글/영문 프롬프트 편집, 여러 줄 입력의 줄바꿈과 제출 구분, TAB·방향키로 필요한 선택지 탐색, 의도한 ESC/CTRL 취소, 이전 출력 스크롤/선택, 폰트/회전/전체화면과 복제 탭 Takeover를 수행한다. 임의 단축키를 추정하거나 실제 도구 실행·결과 대신 정적 화면을 성공으로 쓰지 않는다. 제공된 조작으로 필수 작업이 불가능하면 의미 결손으로 남긴다.

모든 B2-E1~B2-E7 관찰은 같은 안정된 소스에서 빌드한 호환 서버·서빙 번들과 식별된 실제 Android Chrome/IME 환경에 귀속한다. 기기 모델, Android/Chrome/IME 버전, CSS 폭·devicePixelRatio·배율·Safe Area·방향·키보드/후보창/전체화면 상태, OMP 버전/keymap, session diagnostic ID, connection generation, 루트 PID/starttime, PTY 입력·resize 및 화면 readback을 비밀 session ID 없이 남긴다. BLOCK-001의 SC-1~SC-4와 단일 소유권·복구 제스처 0 byte·20회 복구·replay/input-ready를 같은 최종 실행물에서 회귀 확인한다. 시험 브라우저·연결·타이머·listener·프로세스는 정리되고 운영 7683과 기존 OMP 세션은 변경되지 않아야 한다. 실제 Android/IME 경계를 수행할 수 없으면 데스크톱 에뮬레이션이나 합성 composition 이벤트로 대체 통과하지 않고 정확한 환경 한계를 남긴다.
