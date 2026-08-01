# Gate 1 수동 대화형 Smoke 기록

최초 문서 계약 smoke 실행 시각: 2026-07-28T11:05:58+09:00

Task 1-4 보완 재실행 시각: 2026-07-28T11:28:47+09:00

재실행 시작 기준 commit: `34a3cf46348ee27e9d8404b13a2baedc0219aba6`; 시작 worktree는 clean이었다. 재실행 변경은 기준 commit 이후 별도 Task로 보존되며 독립 검증 뒤 Task 단위 커밋 대상이다.

## 실행 경계

- 수행 흐름: 정확히 4개
- 재실행 대상: 기존 Flow 1과 Flow 3만. Flow 2와 Flow 4의 결과와 산출물은 변경하지 않았다.
- 산출물 언어: 한국어. 최소 문서 계약상 고정된 Markdown key와 heading은 원문을 유지했다.
- Implementation Lead, Worker, `/implement`, `/tdd`, `/code-review`, 제품 코드 구현 호출: 0건
- 제품 코드 변경: 0건
- Flow 1 disposable CLI는 smoke 전용 비제품 코드로 유지한다. Flow 3 throwaway prototype은 독립 검증 뒤 삭제됐으며 Ticket 구현은 0건이다.
- 새 validator, 검사기, schema, fixture framework, evidence chain, Decision Ledger: 0개. Flow 3 browser 검증은 설치된 Playwright의 일회성 inline command만 사용했다.
- Flow 4용 프로젝트 root, Spec, Ticket, Wayfinder, 프로토타입 파일: 0개
- 이전 Flow 1과 Flow 3은 문서 계약과 권위 분리를 smoke했지만, 실제 codebase-backed `grill-with-docs`와 실제 runnable `prototype`의 skill fidelity가 약했다. 아래 재실행은 그 결함만 보완한다.
- Flow 3 prototype은 독립 Lead browser 검증 통과 뒤 cleanup을 완료했다. 채택된 B 결정만 권위 문서에 남는다.

## Flow 1: 일반 non-UI

테스트 운영자 입력: "CLI 설정 파일이 없으면 성공 코드 0 대신 종료 코드 2를 반환한다. 기존 오류 문구는 유지한다. UI 작업은 아니다. 관련 없는 CLI 동작은 바꾸지 않는다. 기존 CLI 테스트로 검증한다."

### 재실행 결함과 경계

- 이전 기록은 테스트 운영자가 제공한 CLI 및 test 사실을 문서에 옮겼을 뿐, source/test를 읽거나 실제 CLI와 `go test`를 실행하지 않았다. 따라서 `grill-with-docs`가 요구하는 codebase fact 확인이 약했다.
- 이번 재실행은 기존 project root `/home/user01/project/matt/verification/smoke-workspaces/flow-1`를 그대로 사용했다. `.scratch/` 밖의 `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli`만 disposable smoke CLI다.
- Ticket은 구현하지 않았다. 이 source와 test는 사용자가 요구한 변경 전 baseline을 고정하는 smoke 대상이며 제품 코드가 아니다.

### 직접 확인한 codebase facts

- CLI entry와 함수: `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli/main.go`의 `main`이 `run(os.Args[1:], os.Stdout, os.Stderr)`를 호출한다.
- 현재 missing config 분기: `run`은 `--config <path>` 또는 기본 `config.yaml`을 `os.Stat`하고, 없으면 exact stderr `configuration file not found`를 출력한 뒤 `0`을 반환한다.
- 확인한 existing test: `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli/main_test.go`의 `TestRun`; missing config의 현재 exit code 0과 exact stderr, config 존재 성공 경로를 고정한다.
- 실제 실행 작업 directory: `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli`.
- `go version && go test ./...` 결과: `go version go1.21.13 linux/amd64`, `ok   example.com/matt-flow-1-cli  0.003s`.
- `go run . --config missing-config.yaml` 결과: process exit code 0, exact stderr `configuration file not found`.
- `go run . --config go.mod` 결과: process exit code 0, stdout `configuration loaded`.

이 codebase facts는 운영자에게 질문하지 않고 source/test를 읽고 명령을 실행해 확인했다. 제품 결정과 독립이다.

### 제품 결정 및 승인 순서

1. 테스트 사용자가 이미 확정한 제품 결정은 missing config의 exit code만 2로 바꾸고, 오류 문구를 유지하며, UI와 관련 없는 CLI 동작을 제외하는 것이다.
2. 이 재실행에서는 위 제품 결정을 다시 묻지 않았다. 직접 확인 가능한 code fact는 질문 대상이 아니며, 결정은 기존 테스트 사용자 입력을 그대로 사용했다.
3. 실제 baseline facts를 반영한 `SPEC.md` draft의 범위는 위 제품 결정을 넘지 않으며, 기존 테스트 사용자 Spec 승인 순서를 다시 기록해 `Status: approved`를 유지했다.
4. 실제 source/test path와 post-change verification을 반영한 `TICKET-001.md` draft는 하나의 종료 코드 변경으로 한정했고, 기존 테스트 사용자 Ticket breakdown 승인 순서를 다시 기록해 `Status: ready`를 유지했다.
5. Worker는 선택하지 않았고, Implementation Lead, Worker, 또는 제품 구현을 호출하지 않았다.

사용한 스킬:

- `grill-with-docs`: 코드베이스 기반 CLI 변경의 범위와 기존 검증 조건을 한 질문씩 확인하기 위해 사용했다.
- `grilling`: 직접 확인한 code fact는 질문하지 않고, 기존 테스트 사용자 제품 결정과 승인 순서를 분리해 기록하기 위해 사용했다.
- `to-spec`: 실제 source/test baseline을 포함하되 승인된 제품 범위를 확대하지 않는 Spec을 유지하기 위해 사용했다.
- `to-tickets`: 실제 변경 대상과 verification command를 가진 관찰 가능한 단일 Ticket을 유지하기 위해 사용했다.

생략한 선택 스킬:

- `wayfinder`: 작업 경로가 짧고 단일 계획 세션에서 보이므로 큰 작업 조건이 아니다.
- `prototype`: UI 작업이나 대화만으로 해결 불가능한 설계 불확실성이 없다.
- `domain-modeling`, `research`, `handoff`: 용어·아키텍처 결정, 외부 조사, 전달 문서가 이 범위에 필요하지 않다.

생성 경로:

- Project root: `/home/user01/project/matt/verification/smoke-workspaces/flow-1`
- Disposable CLI source: `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli/main.go`
- Disposable CLI test: `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli/main_test.go`
- Spec: `/home/user01/project/matt/verification/smoke-workspaces/flow-1/.scratch/cli-config-exit-code/SPEC.md`
- Ticket: `/home/user01/project/matt/verification/smoke-workspaces/flow-1/.scratch/cli-config-exit-code/tickets/TICKET-001.md`

## Flow 2: 큰 작업

테스트 운영자 입력: "여러 서비스에 흩어진 계정 내보내기 기능을 장기적으로 통합하고 싶다. 첫 구현 범위는 기존 단일 서비스의 JSON 내보내기 한 경로만 유지한 채 새 공통 요청 형식으로 연결하는 것이다. 다른 서비스, CSV, UI, 데이터 삭제는 제외한다. 기존 통합 테스트로 이전/새 요청의 동일 결과를 검증한다."

대화 및 승인 순서:

1. 질문: 장기 목적과 첫 구현 범위를 분리할지 확인했다. 추천: 다중 서비스라는 장기 목적은 Wayfinder에 남기고 첫 구현은 단일 서비스 JSON 경로 하나로 제한한다.
2. 명시적 답변: 테스트 사용자는 후보 A, 즉 단일 서비스 JSON 경로 하나를 새 공통 요청에 연결하는 범위만 채택했다. 다른 서비스, CSV, UI, 데이터 삭제는 제외로 확정했다.
3. `WAYFINDER.md`에 후보 A/B/C, 채택된 후보 A, 알려진 의존성, 명시적 제외를 기록했다. 이 문서는 `기획 보조 (비권위)`로 남겼다.
4. `SPEC.md`를 `draft`로 작성했다. 질문: 이전 요청을 유지하면서 기존 통합 테스트로 이전/새 요청의 동일 결과를 확인하는 범위를 반영할지 확인했다. 추천: 이 검증을 첫 구현의 완료 조건으로 유지한다.
5. 명시적 승인: 테스트 사용자가 위 첫 구현 범위의 draft Spec을 승인했다. 미해결 제품 결정이 없음을 확인한 뒤 `Status: approved`로 전환했다.
6. `TICKET-001.md`를 `draft`로 작성했다. 추천: 새 공통 요청 연결과 기존 통합 테스트의 동등 결과 확인은 분리할 수 없는 한 구현 변경으로 둔다.
7. 명시적 승인: 테스트 사용자가 blocker 없는 TICKET-001을 승인했다. parent Spec 승인, 관찰 가능한 AC, 유일한 project root, `Blockers: None`을 확인한 뒤 `Status: ready`로 전환했다.

사용한 스킬:

- `grilling`: 큰 작업의 목적과 첫 구현 범위를 한 결정씩 분리하기 위해 사용했다.
- `wayfinder`: 여러 서비스에 걸친 장기 목적의 첫 경로를 비권위 Markdown map으로 한정하기 위해 사용했다.
- `to-spec`: 채택된 첫 구현 범위만 승인 가능한 Spec으로 옮기기 위해 사용했다.
- `to-tickets`: 승인된 첫 구현 범위에서 단일 구현 Ticket을 만들기 위해 사용했다.

생략한 선택 스킬:

- `prototype`: UI 또는 대화로 해결할 수 없는 설계 질문이 없다.
- `research`, `domain-modeling`: 테스트 운영자가 제공한 범위 밖의 외부 사실이나 추가 도메인 결정을 만들 필요가 없다.
- `handoff`: 구현으로 넘기지 않는 Gate 1 smoke이므로 필요하지 않다.

생성 경로:

- Project root: `/home/user01/project/matt/verification/smoke-workspaces/flow-2`
- Wayfinder: `/home/user01/project/matt/verification/smoke-workspaces/flow-2/.scratch/account-export-common-request/WAYFINDER.md`
- Spec: `/home/user01/project/matt/verification/smoke-workspaces/flow-2/.scratch/account-export-common-request/SPEC.md`
- Ticket: `/home/user01/project/matt/verification/smoke-workspaces/flow-2/.scratch/account-export-common-request/tickets/TICKET-001.md`

## Flow 3: UI 프로토타입 선택 사용

테스트 운영자 입력: "설정이 비어 있는 화면에서 안내문과 주요 설정 버튼 중 무엇을 먼저 보여줄지 확인하고 싶다. 좁은/넓은 화면 모두 대상이며 다른 화면은 바꾸지 않는다."

### 재실행 결함과 prototype 경계

- 이전 기록은 테스트 운영자가 제공한 A/B 결과를 planning Markdown에만 기록했고 실제 runnable UI route, static server, browser render가 없었다. 이는 `prototype/UI.md`의 single-route variant switcher fidelity가 약한 결함이다.
- 이 재실행은 기존 project root `/home/user01/project/matt/verification/smoke-workspaces/flow-3`를 그대로 사용했다. `.scratch/` 밖의 `prototype-empty-settings-hierarchy/index.html`은 zero-dependency single HTML/CSS/JS throwaway surface였으며, 독립 검증 통과 뒤 삭제됐다.
- 이 smoke workspace에는 가까운 기존 UI route가 없으므로 throwaway 신규 page 경로를 사용했다. prototype source, variants, switcher, screenshot은 제품 구현이나 권위가 아니며 cleanup에서 삭제했다.

### 실제 variants와 사용자 채택

- A (`A - 설정 버튼 우선`): 큰 제목 다음 action panel에서 주요 `작업 공간 설정` 버튼을 상세 안내보다 우선한다.
- B (`B - 안내 우선`): 제목과 설명으로 이루어진 전체 안내 영역을 먼저 제시한 뒤 단일 `설정 열기` 버튼을 둔다. 테스트 사용자는 실제 렌더링 관찰 후 이 후보를 채택했다.
- C (`C - 단계 안내`): `01 준비`, `02 설정`, `03 검토` 단계와 `단계별 설정 시작`을 둔 구조적으로 다른 비교 후보다. 채택하거나 권위 문서에 반영하지 않았다.
- `PROTOTYPE-NOTE.md`는 A/B/C 비교와 실행 기록만 가진 비권위 문서다. 승인된 `UX-REFERENCE.md`, `SPEC.md`, `TICKET-001.md`에는 채택된 B의 안내문 우선 및 단일 주요 버튼만 남겼다.

### 실제 server 및 browser render

작업 directory는 `/home/user01/project/matt/verification/smoke-workspaces/flow-3/prototype-empty-settings-hierarchy`이며, 다음 실제 static server command로 port 4173을 사용했다.

```bash
(node -e 'const http=require("http"); const fs=require("fs"); http.createServer((req,res)=>{res.writeHead(200,{"Content-Type":"text/html; charset=utf-8"}); res.end(fs.readFileSync("index.html"))}).listen(4173,"127.0.0.1");' >/dev/null 2>&1 & jobs -p)
```

`/usr/bin/google-chrome` executable을 사용하는 설치된 Playwright로 다음 실제 render/interaction command를 실행했다. 이 command는 수행 기록으로만 유지하며, cleanup 후 source가 삭제되어 현재 재실행 대상이 아니다.

```bash
python3 -c $'from playwright.sync_api import sync_playwright\nbase = "http://127.0.0.1:4173/"\nlabels = {"A": "A - 설정 버튼 우선", "B": "B - 안내 우선", "C": "C - 단계 안내"}\nrows = []\nwith sync_playwright() as p:\n    browser = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)\n    for width, height in ((390, 844), (1440, 1000)):\n        page = browser.new_page(viewport={"width": width, "height": height})\n        for key in ("A", "B", "C"):\n            page.goto(f"{base}?variant={key}", wait_until="networkidle")\n            action = page.locator(".primary-action")\n            action_box = action.bounding_box()\n            switcher_box = page.locator(".prototype-switcher").bounding_box()\n            overlap = action_box["x"] < switcher_box["x"] + switcher_box["width"] and switcher_box["x"] < action_box["x"] + action_box["width"] and action_box["y"] < switcher_box["y"] + switcher_box["height"] and switcher_box["y"] < action_box["y"] + action_box["height"]\n            assert page.locator("html").get_attribute("lang") == "ko"\n            assert page.locator(".prototype-notice").inner_text() == "프로토타입 전용. 제품 화면이 아닙니다."\n            assert page.locator("#variant-label").inner_text() == labels[key]\n            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth || document.documentElement.scrollHeight > innerHeight")\n            assert not overlap and page.locator(".prototype-switcher").is_visible()\n            if key == "A":\n                panel, guide = page.locator(".action-panel").bounding_box(), page.locator(".guide").bounding_box()\n                assert panel["y"] < guide["y"] and action.inner_text() == "작업 공간 설정"\n                result = "action panel before detailed guidance"\n            elif key == "B":\n                guidance = page.locator(".explanation").bounding_box()\n                main = page.locator("main").inner_text()\n                last_line = page.locator(".explanation > p:not(.eyebrow)").evaluate("""element => { const node = element.firstChild, lines = new Map(); for (let index = 0; index < node.length; index++) { const range = document.createRange(); range.setStart(node, index); range.setEnd(node, index + 1); const rect = range.getBoundingClientRect(); if (rect.width) { const y = Math.round(rect.y); lines.set(y, `${lines.get(y) || ""}${node.textContent[index]}`); } } return [...lines.values()].map(line => line.trim()).filter(Boolean).at(-1); }""")\n                assert guidance["y"] < action_box["y"] and main.index("차분하게 기준부터 정하세요.") < main.index("설정 열기")\n                assert action.inner_text() == "설정 열기" and last_line not in ("다.", "니다.", "습니다.", "있습니다.")\n                result = f"guidance block before single action; last Korean line: {last_line}"\n            else:\n                assert page.locator(".variant-c nav").is_visible() and page.locator(".variant-c li").all_inner_texts() == ["01 준비", "02 설정", "03 검토"]\n                assert action.inner_text() == "단계별 설정 시작"\n                result = "guided-step structure"\n            page.screenshot(path=f"/tmp/opencode/matt-gate1-flow3/variant-{key}-{width}x{height}.png")\n            rows.append(f"{key}@{width}x{height}: {labels[key]}, {result}, no clipping/overlap, switcher")\n        page.close()\n    page = browser.new_page(viewport={"width": 390, "height": 844})\n    page.goto(base + "?variant=A", wait_until="networkidle")\n    page.get_by_role("button", name="다음 후보").click()\n    assert page.url.endswith("?variant=B") and page.locator("#variant-label").inner_text() == labels["B"]\n    page.keyboard.press("ArrowRight")\n    assert page.url.endswith("?variant=C") and page.locator("#variant-label").inner_text() == labels["C"]\n    page.goto(base + "?variant=B", wait_until="networkidle")\n    page.locator("#next").focus()\n    assert page.locator("#next").evaluate("element => getComputedStyle(element).outlineWidth") == "3px"\n    page.keyboard.press("ArrowLeft")\n    assert page.url.endswith("?variant=A") and page.locator("#variant-label").inner_text() == labels["A"]\n    page.keyboard.press("ArrowRight")\n    assert page.url.endswith("?variant=B") and page.locator("#variant-label").inner_text() == labels["B"]\n    browser.close()\nprint("\\n".join(rows))\nprint("button A->B, keyboard B->C and B->A->B, 3px focus outline: pass")'
```

- URLs: `http://127.0.0.1:4173/?variant=A`, `http://127.0.0.1:4173/?variant=B`, `http://127.0.0.1:4173/?variant=C`.
- 390x844와 1440x1000에서 A/B/C 각각의 current variant label, 안내문/버튼 순서, fixed switcher를 확인했다. 여섯 render 모두 overflow/clipping과 주요 action/switcher overlap이 없었다.
- 실제 버튼은 A -> B로 URL과 label을 갱신했고, 실제 right arrow keyboard는 B -> C로 갱신했다. 별도 left/right keyboard 확인은 B -> A -> B였고 focused switcher button의 visible outline은 3px이었다.
- 진단용 screenshots만 `/tmp/opencode/matt-gate1-flow3/variant-{A,B,C}-{390x844,1440x1000}.png`에 저장했다. 저장소에는 image evidence를 만들지 않았다.
- server PID는 각 검증 직후 종료했고, 최종 `ss -ltn 'sport = :4173'`은 LISTEN socket이 없음을 보였다.

### 독립 Lead 결함 보완 재검증

- 독립 Lead는 wide B의 큰 guidance block이 왼쪽에서 먼저 읽히므로 채택 방향은 유효하다고 확인했다. paragraph 단독 top과 button을 비교한 assertion은 B의 실제 정보 계층을 충분히 표현하지 못하므로 layout을 재설계하지 않았다.
- 실제 artifact 결함: 테스트 사용자 언어가 한국어인데 `/home/user01/project/matt/verification/smoke-workspaces/flow-3/prototype-empty-settings-hierarchy/index.html`이 `<html lang="en">` 및 영어 UI copy/variant label을 사용했다. 이는 `prototype/SKILL.md`의 사용자 대화 언어 규칙을 위반한다.
- 최소 수정: `<html lang="ko">`, notice, aria label, A/B/C label, heading, 설명, button, 단계 label을 한국어로 교체했다. A/B/C 구조, same route `?variant=`, fixed switcher, URL 갱신, keyboard, focus, responsive layout은 유지했다.
- 같은 static server와 `/usr/bin/google-chrome` Playwright render로 A/B/C를 390x844와 1440x1000에서 다시 확인했다. `A - 설정 버튼 우선`, `B - 안내 우선`, `C - 단계 안내` 및 한국어 copy가 모두 표시됐다.
- A는 action panel이 상세 안내보다 먼저, B는 `.explanation` 전체 guidance block의 top과 읽기 순서가 단일 `설정 열기` button보다 먼저, C는 `01 준비`/`02 설정`/`03 검토` 단계형 구조임을 확인했다. B에는 paragraph 단독 y-coordinate assertion을 사용하지 않았다.
- 여섯 render 모두 clipping/overflow 및 action/switcher overlap이 없었다. `다음 후보` button A -> B, right keyboard B -> C, left/right keyboard B -> A -> B, 3px focus outline을 확인했고 screenshots를 `/tmp/opencode/matt-gate1-flow3/`에 한국어 render로 덮어썼다.
- 독립 Lead 최종 browser 검증 통과 뒤 source, variants, switcher와 빈 경로를 삭제했다. server PID는 종료했고 `ss -ltn 'sport = :4173'`에 LISTEN socket이 없다.
- 독립 Lead는 390x844 B 본문의 마지막 `다.` orphan과 위 초기 영어 Playwright command의 stale aria label/단순 DOM order assertion도 발견했다. B copy를 같은 의미의 더 짧은 문장으로 교체하고 `word-break: keep-all`을 적용했으며, 위 inline command를 한국어 labels/aria, actual A/B/C layout, Korean last-line, overflow/overlap, URL 전환, 3px focus를 확인하도록 교체했다.

### 독립 Lead 최종 검증

- Flow 1: `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli`에서 `go test ./...`가 통과했고, missing config actual exit code 0과 exact stderr `configuration file not found`, existing config success path를 다시 확인했다.
- Flow 3: 한국어 A/B/C를 390x844와 1440x1000에서 직접 렌더링했다. hierarchy, horizontal overflow, action/switcher overlap, B 모바일 orphan이 모두 통과했고 `다음 후보` A -> B, keyboard B -> C -> B, focus outline 3px도 통과했다.
- port 4173 cleanup을 확인했다. 이 최종 검증 뒤 prototype을 삭제했으므로 browser 재검증을 다시 요구하지 않는다.

### 승인 순서

1. 테스트 사용자는 기존의 좁은 UI 질문과 비교 범위를 유지했다.
2. 실제 A/B/C render를 관찰한 뒤 B를 채택했다. A/C는 비채택이다.
3. 기존 테스트 사용자 UX reference 승인 순서를 다시 기록해 B만 든 `UX-REFERENCE.md`의 `Status: approved`를 유지했다.
4. B만 반영한 `SPEC.md`의 기존 승인 순서와 `TICKET-001.md`의 기존 Ticket 승인 순서를 다시 기록해 각각 `approved`와 `ready`를 유지했다.
5. Worker는 선택하지 않았고, Implementation Lead, Worker, 또는 제품 구현을 호출하지 않았다.

사용한 스킬:

- `prototype`: 대화만으로 확정하지 않은 빈 설정 화면 정보 계층 질문을 후보 비교로 분리하고, 사용자의 채택 전에는 비권위로 유지하기 위해 사용했다.
- `to-spec`: 실제 browser render 뒤 테스트 사용자가 채택한 B만 승인된 UI/UX 참조와 Spec에 반영하기 위해 사용했다.
- `to-tickets`: 승인된 B UI/UX 참조를 가리키는 UI Ticket을 유지하기 위해 사용했다.

생략한 선택 스킬:

- `grilling`: 테스트 운영자가 비교 질문, 후보 결과, 채택 결정을 모두 명시해 추가 인터뷰가 필요하지 않다.
- `wayfinder`: 단일 화면의 정보 계층 문제로 여러 세션의 큰 작업이 아니다.
- `research`, `domain-modeling`, `handoff`: 외부 조사·도메인 모델·구현 전달이 이 승인 범위에 필요하지 않다.

생성 경로:

- Project root: `/home/user01/project/matt/verification/smoke-workspaces/flow-3`
- Deleted throwaway prototype source: `/home/user01/project/matt/verification/smoke-workspaces/flow-3/prototype-empty-settings-hierarchy/index.html`
- Prototype note: `/home/user01/project/matt/verification/smoke-workspaces/flow-3/.scratch/empty-settings-hierarchy/PROTOTYPE-NOTE.md`
- 승인된 UI/UX 참조: `/home/user01/project/matt/verification/smoke-workspaces/flow-3/.scratch/empty-settings-hierarchy/UX-REFERENCE.md`
- Spec: `/home/user01/project/matt/verification/smoke-workspaces/flow-3/.scratch/empty-settings-hierarchy/SPEC.md`
- Ticket: `/home/user01/project/matt/verification/smoke-workspaces/flow-3/.scratch/empty-settings-hierarchy/tickets/TICKET-001.md`

## Flow 4: 프로젝트 밖 아이디어

테스트 운영자 입력: "매주 토요일 90분 동안 기술 글 한 편을 읽고 5문장 요약을 남기는 개인 학습 습관"

대화 및 정리:

1. 질문: 이 습관의 첫 목표가 무엇인지 확인했다. 추천: 기능이나 도구를 추가하지 않고 4주 연속 실행 여부로 목표를 관찰한다.
2. 명시적 답변: 테스트 사용자는 4주 연속 실행 여부를 확인하는 것을 목표로 정했다.
3. 질문: 앱, 자동화, 알림, 구현 Ticket을 만들지 않을지 확인했다. 추천: 개인 습관 정리에만 머물고 기획 산출물이나 구현 안내로 넘기지 않는다.
4. 명시적 답변: 앱·자동화·알림·구현 Ticket을 만들지 않기로 확정했다.

정리된 설명: 매주 토요일에 90분을 확보해 기술 글 한 편을 읽고 5문장 요약을 남긴다. 목표는 이 행동을 4주 연속 실행했는지 확인하는 것이다. 이 흐름은 개인 학습 습관 정리이며 앱, 자동화, 알림, 구현 Ticket, 자동 구현 안내를 만들지 않는다.

사용한 스킬:

- `grill-me`: 코드베이스 밖 개인 습관을 한 질문씩 명확히 하기 위해 사용했다.
- `grilling`: 추천과 명시적 답변을 한 결정씩 기록하기 위해 사용했다.

생략한 선택 스킬:

- `to-spec`, `to-tickets`: 테스트 사용자가 Spec과 구현 Ticket을 만들지 않기로 명시했다.
- `wayfinder`, `prototype`, `research`, `domain-modeling`, `handoff`: 여러 세션의 프로젝트 경로, 불확실한 UI/로직, 외부 조사, 도메인 모델, 구현 전달이 없다.

생성 경로: 없음. 이 보고서 외 프로젝트 root, `.scratch/`, Spec, Ticket, Wayfinder, 프로토타입 파일을 만들지 않았다.

## 사람 기준 계약 검토

상태 전환 시점:

- Flow 1 Spec은 기존 테스트 사용자 Spec 승인 뒤에만 `draft`에서 `approved`로 전환했고, Ticket은 기존 테스트 사용자 breakdown 승인 뒤에만 `draft`에서 `ready`로 전환했다. 재실행은 직접 확인한 code fact만 보완했고 새 제품 결정을 만들지 않았다.
- Flow 2 Spec은 채택된 후보 A의 명시적 승인 뒤에만 `approved`로 전환했고, Ticket은 명시적 blocker 없는 breakdown 승인 뒤에만 `ready`로 전환했다.
- Flow 3 UI/UX 참조는 실제 browser render 뒤 테스트 사용자가 후보 B를 명시적으로 채택하고 승인한 뒤에만 `approved`로 전환했다. Spec은 그 참조와 draft Spec의 기존 승인 뒤에만 `approved`로 전환했고, UI Ticket은 그 뒤 기존 Ticket 승인 뒤에만 `ready`로 전환했다.
- 세 흐름 모두 `## Open Questions`는 `None`이고 Ticket `## Blockers`는 `None`이다.

필수 heading 및 key 검토:

- Flow 1~3의 모든 `SPEC.md`는 제목, `Status`, `Owner`, `Problem`, `Desired Outcome`, `Requirements`, `Non-Goals`, `Implementation Constraints`, `Verification Expectations`, `UI / UX`, `Open Questions`를 포함한다.
- Flow 1~3의 모든 `TICKET-001.md`는 제목, `Status`, `Parent-Spec`, 절대 `Project-Root`, 빈 `Worker`, `UI`, `Goal`, `Acceptance Criteria`, `Scope`, `Non-Goals`, `Blockers`, `Verification`, `References`를 포함한다.
- 세 Ticket의 `Parent-Spec: ../SPEC.md`는 각각 같은 work slug의 approved Spec으로 해소된다. 세 `Project-Root`는 flow별 실제 절대 root와 일치한다.
- Flow 3의 `UI: yes` Ticket `References`는 승인된 `../UX-REFERENCE.md`를 가리킨다. `PROTOTYPE-NOTE.md`는 비권위임을 명시한다.

AC 및 범위 검토:

- Flow 1 AC는 실제 `main.go`와 `main_test.go` path, 설정 파일 부재 시 종료 코드 2, 오류 문구 보존, `go test ./...`, config 존재 성공 경로로 관찰 가능하다. 현재 source는 의도적으로 변경 전 exit code 0 baseline을 유지한다.
- Flow 2 AC는 새 공통 요청 연결, 이전/새 요청의 기존 통합 테스트 동일 결과, 이전 요청 유지로 관찰 가능하다.
- Flow 3 AC는 실제 B render의 390x844/1440x1000 빈 상태에서 안내문 우선과 단일 버튼으로 관찰 가능하다.
- 세 Ticket 모두 `Scope`, `Non-Goals`, `Blockers`, `Verification`을 포함하며 parent Spec의 범위를 확대하지 않는다.

UI 권위 및 자동 실행 검토:

- 후보 B는 테스트 사용자의 명시적 채택과 승인된 `UX-REFERENCE.md`를 통해서만 Spec/Ticket에 반영됐다.
- 후보 A/C와 `PROTOTYPE-NOTE.md`는 구현 권위가 아니다. prototype source와 switcher는 독립 Lead 최종 검증 뒤 삭제됐고 B의 채택 결정만 권위 문서에 남는다.
- 네 흐름에서 자동 구현 호출은 0건이다. exact Ticket 경로와 exact Worker를 제공한 구현 요청도 없었고, Implementation Lead 또는 Worker를 호출하지 않았다.

## 발견 결함과 보완

- 이전 Flow 1/3 결함: 문서 계약과 authority 분리는 확인했지만, 실제 codebase-backed `grill-with-docs`와 runnable `prototype` 검증이 약했다.
- 보완: Flow 1은 disposable Go source/test와 실제 baseline command를 추가해 code fact와 제품 결정을 분리했다. Flow 3은 격리된 actual UI prototype, static server, Chrome/Playwright render와 interaction을 추가했다.
- 독립 Lead 발견 Flow 3 artifact 결함: prototype source가 테스트 사용자 언어 규칙을 따르지 않고 `<html lang="en">` 및 영어 UI copy를 렌더링했다. source의 language/copy만 한국어로 최소 수정하고 A/B/C layout과 interaction을 재검증했다.
- 독립 Lead 최종 검증 통과 뒤 `prototype/SKILL.md` cleanup 계약에 따라 prototype source와 switcher를 삭제했다.
- 당시 로컬 `skills/`의 명확한 문구 결함이 없다는 판정은 아래 2026-07-30 후속 계약 감사에서 폐기됐다.
- 당시 `skills/` 수정: 0개.
- Flow 2/4 결과와 산출물 변경: 0개.
- 과투자 중단 신호: 없음. 네 개를 초과하는 smoke, 새 schema, validator, 반복 evidence 파일, 원격 tracker 일반화, Phase 2 작업을 시작하지 않았다.

## Gate 1 기준 판정

| 기준 | 판정 | 근거 |
| --- | --- | --- |
| 일반 non-UI에서 approved Spec과 ready Ticket을 만들 수 있음 | pass | 독립 Lead가 Flow 1의 `go test ./...`, missing config baseline, existing config success path와 approved Spec/ready Ticket을 재확인 |
| Ticket AC, Scope, Non-Goals, Blockers, Verification이 구현 입력으로 충분함 | pass | 독립 Lead가 Flow 1 실제 CLI/test와 Flow 3 승인 B 결정 및 390x844/1440x1000 browser 결과를 재확인 |
| 큰 작업만 Wayfinder를 사용함 | pass | Flow 2만 `WAYFINDER.md`를 생성했고 Flow 1과 3은 생성하지 않음 |
| 프로토타입 결과가 사용자 채택 없이 authority가 되지 않음 | pass | 독립 Lead가 B 채택만 권위 문서에 남고 A/C와 prototype code가 비권위이며 cleanup으로 삭제된 것을 확인 |
| planning skill이 구현을 자동 호출하지 않음 | pass | 자동 구현 호출 0건 |
| 사용 경험이 기존 BMAD보다 가벼움 | 사용자 판단 필요 | 테스트 수행자가 확정할 수 없는 사용자 경험 판단 |
| validator, evidence chain, Decision Ledger가 생기지 않음 | pass | 새 도구·schema·반복 evidence·ledger 0개 |

독립 Lead의 Flow 1/3 최종 기술 검증과 Flow 3 cleanup은 완료됐다. Gate 1 최종 승인과 Phase 2 진행은 선언하지 않는다. 반드시 남겨야 할 판단은 "사용 경험이 기존 BMAD보다 가볍다"는 사용자 판단이며, 이를 포함한 Gate 1 최종 승인도 사용자에게 남겨 둔다.

## 2026-07-30 Ticket 계약 정합성 후속 감사

이 후속 감사는 위 대화형 smoke의 제품 결정을 다시 승인하거나 Gate 1 최종 승인을 선언하지 않는다. Matt Ticket 생산 계약과 Implementation Lead 입력 계약의 직렬화 및 권위 정합성만 재검토했다.

### 확인된 결함

- UI reference: `to-tickets`는 승인된 UI/UX 경로를 요구했지만 exact item 문법을 정하지 않았고, Flow 3과 UI example은 레이블 또는 backtick 설명을 경로와 섞었다. Implementation Lead는 standalone local Markdown path를 요구하므로 생산자와 소비자 계약이 달랐다.
- Goal authority: `to-tickets`는 Goal의 normative statement를 추적성 감사 대상으로 삼았지만 Implementation Lead는 Goal을 실행 입력에서 제외했다. Goal-only 의무가 조용히 누락될 수 있었다.
- Blockers: `to-tickets`는 blocker의 의미만 규정했고, Implementation Lead는 exact one-line `None` 또는 local Markdown path-only list와 대상 `Status: resolved|done`을 요구했다. 현재 ready fixture는 모두 `None`이라 실제 fixture 실패는 없었지만 생산 가능한 형식 범위가 달랐다.
- 이 저장소에는 Ticket resolver 또는 parser 구현이 없다. `planning-ticket.md`도 자신을 resolver code가 아닌 reference contract로 한정하므로 위 결함은 실행 코드 재현이 아니라 문서 기반 fail-closed 인터페이스 결함으로 판정했다.

### 적용한 정렬

- Goal을 비규범적 요약으로 고정했다. Goal의 결과·제약·불변조건·제외·검증 의무는 Acceptance Criteria, Scope, Non-Goals, Blockers, Verification에 완전히 표현돼야 한다.
- Implementation Lead는 Goal을 task-decomposition 또는 completion authority로 사용하지 않되, Goal-only 의무나 실행 권위 섹션과의 충돌을 contextual preflight에서 차단한다.
- Blockers를 exact one-line `None` 또는 item 전체가 local Markdown path인 목록으로 고정했다. referenced blocker는 readable regular Markdown이고 top metadata의 유일한 `Status:`가 `resolved` 또는 `done`이어야 한다.
- `UI: yes` authority는 item 전체가 local Markdown path인 목록 항목으로 고정했다. 레이블, backtick, colon prefix, status, parenthetical explanation, URL이 섞인 항목은 UI authority가 아니다.
- `skills/implementation-lead`와 `staging/implementation-lead`의 runtime reference를 동일하게 유지하고, 실제 활성 `/home/user01/.codex/skills/implementation-lead` 사본도 같은 내용으로 동기화했다. 활성 `to-tickets`는 `/home/user01/project/matt/skills/to-tickets`를 가리키는 기존 symbolic link다.
- Ticket template, examples 3개, verification ready Ticket 4개의 References를 path-only 항목으로 정렬했다. 제품 요구사항과 ready 상태는 바꾸지 않았다.

### 검증 결과

- 양성 UI: 두 `UI: yes` Ticket은 각각 `../UI-UX.md`, `../UX-REFERENCE.md` path-only 항목을 가지며, 두 target은 readable regular file이고 top metadata가 `Status: approved`다.
- 양성 Blockers: ready Ticket 7개 모두 exact `## Blockers` body `None`을 사용한다. template도 같은 기본 형식을 시연한다.
- 양성 Goal: ready Ticket 7개의 Goal을 Acceptance Criteria, Scope, Non-Goals, Verification과 대조했고 Goal-only 구현 의무 또는 충돌은 0개였다.
- 음성 UI: label, backtick, colon prefix, parenthetical explanation, URL, unreadable target, non-approved target, `UI: yes`의 authority 부재는 소비자 계약에서 명시적으로 차단된다.
- 음성 Blockers: prose, mixed path/explanation, URL, unreadable target, duplicate 또는 malformed `Status:`, `open`을 포함한 `resolved|done` 외 상태는 명시적으로 차단된다.
- 음성 Goal: Goal-only obligation, 실행 권위 섹션과의 충돌, 관계를 확정할 수 없는 경우는 Ticket/Spec owner 대상으로 blocked다.
- `cmp -s skills/implementation-lead/references/planning-ticket.md staging/implementation-lead/references/planning-ticket.md`: pass.
- `cmp -s skills/implementation-lead/references/planning-ticket.md /home/user01/.codex/skills/implementation-lead/references/planning-ticket.md`: pass.
- `git diff --check`: pass.
- `verification/smoke-workspaces/flow-1/disposable-cli`의 `go test ./...`: pass.
- `verification/shadow/project`의 `go test ./...`: pass.
- Flow 1 baseline `go run . --config missing-config.yaml`: exact stderr `configuration file not found`, exit code 0 유지.
- Flow 1 baseline `go run . --config go.mod`: stdout `configuration loaded`, exit code 0 유지.

후속 감사 결과: producer가 만들 수 있는 ready Ticket 문법과 consumer의 fail-closed 입력 문법이 Goal, UI reference, Blockers에 대해 동일하다. 새 validator, schema, parser, fixture framework, Worker 호출, 제품 구현은 추가하지 않았다.
