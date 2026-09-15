# Scope: Studio Shell & Vue 3 Frontend

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-001.md sha256:74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-001.md sha256:5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c

## Outcome

`BLOCK-01`과 `BLOCK-02`는 단일 SQLite 트랜잭션 권위, exactly-five cut identity, monotonic intent/currentness, 통합 generation queue/runner와 실제 process-tree STOP을 완료 검증했다. `BLOCK-03`은 정확히 다섯 Current realization과 authoritative composition에서 하나의 immutable Canonical Review Artifact를 생성·등록·재조회하는 PIL compositor를 완료 검증했으며, 독립 검증은 `VERIFIED`, Coverage는 `COMPLETE / Findings: None`이다. 따라서 `BASELINE-001` Safe Continuation 조건 아래 현재 선택된 결과는 `BLOCK-04 — Studio Shell & Vue 3 Frontend` 하나이다.

현재 실제 제품에는 FastAPI 서버도, `comic-new serve` 명령도, `frontend/` 소스도, 생성된 `src/comic_new/static/` 패키지 자산도 없다. `pyproject.toml`의 runtime dependency는 Pillow뿐이고 package data는 schema/migrations뿐이다. 현재 사용자 표면은 CLI이며, canonical authority는 이미 존재하는 `TransactionalStore.snapshot`과 그 CAS mutation들, `GenerationService`/`GenerationRunner`, `CompositionService`이다. 웹 계층이나 클라이언트가 이들과 경쟁하는 snapshot, queue, currency, artifact 또는 approval truth를 새로 소유해서는 안 된다.

완료 후 창작자는 실제 프로젝트 SQLite를 권위로 사용하는 하나의 프로덕션 Web Studio에서 정확히 다섯 컷의 intent/realization revision과 Current/STALE 상태를 보고, intent와 composition을 수정·저장하고, 생성 queue를 관찰·취소하며, 즉시 STOP하고, 서버가 실체화한 immutable review artifact를 검토할 수 있다. Vue 3 Composition API, `<script setup>`, strict TypeScript, Vite, Pinia의 정확히 하나인 domain store `useStudioStore`, native `fetch`/`EventSource`, DOM/SVG와 native `PointerEvent`, plain CSS Grid/Flex가 이 단일 표면을 이룬다. 프로덕션 빌드 결과는 `src/comic_new/static/`에 포함되고, FastAPI와 generated studio는 별도 frontend daemon 없이 오직 `comic-new serve` 한 Python process에서 같은 origin으로 제공된다.

같은 process boundary의 API/SSE는 브라우저가 기존 canonical services를 직접적이고 정직하게 조작·관찰하는 데 필요한 최소 경계를 제공한다. 여기에는 authoritative studio snapshot, 명시적 Structural Baseline/Re-baseline 수용, CAS 기반 intent/composition save, generation enqueue 및 개별/global stop, immutable review artifact materialization/readback, artifact bytes, 그리고 monotonic identity가 있는 authoritative event stream이 포함된다. 응답과 event는 SQLite 및 기존 service readback을 투영하며 별도 mutable authority를 만들지 않는다.

클라이언트의 domain truth는 `server`(마지막 authoritative readback), `drafts`(아직 수용되지 않은 local projection), `saves`(pending/failed/conflict 시도 상태)의 세 계층으로 분리된다. composition save는 base composition revision 또는 동등한 CAS identity와 mutation identity를 사용하여 직렬화된다. 실패·충돌·더 최신 local edit는 draft를 잃지 않으며, SSE는 server 계층만 갱신한다. 실행 상태, cut currency, release authorization, delivery outcome은 서로 대신하지 않는 별도 차원으로 표시된다.

데스크톱은 permanent Header, 정확히 다섯 컷의 Left Rail, permanent Center Composition Canvas, permanent non-modal Right Inspector의 3열 작업면이다. 좁은 viewport에서도 Center는 영구 유지되고 좌우 rail/inspector만 독립적인 non-modal edge panel이 된다. QueuePopover는 header에 anchor된 non-modal 표면이며 queued/running job, 대상 cut/revision, progress와 개별 STOP을 보인다. STALE와 저장 실패/충돌/미저장 표시는 toast가 사라진 뒤에도 해당 cut/object/field 및 작업면에 지속된다.

Composition Canvas는 브라우저 viewport나 개별 cut image가 아니라 canonical composition surface 기준 `x_pct`, `y_pct`, `w_pct`, `h_pct`를 사용한다. pointer capture, pointer cancellation과 keyboard 조작은 같은 normalized model을 사용한다. 제품 의미의 최종 수치인 arrow nudge `0.5%`, Shift+arrow `2.0%`를 적용한다. 이는 파생 architecture 문서에 남은 `0.25%`/`1%`보다 `THESIS-001 §6.5`를 우선한 결정이다. pointerup이나 키 입력은 local draft를 만들 뿐 server acceptance 전에는 저장 성공으로 보이지 않는다.

ReviewModal은 유일한 일상 작업 차단 focus-trap modal이다. 브라우저가 말풍선이나 텍스트를 재조판하지 않고 실제 server-materialized artifact bytes를 그대로 표시하며, 화면에 표시된 정확한 `artifact_id`와 content hash가 승인 요청 입력이 된다. 이 Scope는 그 요청이 동일 identity/hash를 전달하는 frontend/API handoff까지만 보장한다. durable Release Authorization의 생성·재시작 보존·receiver-visible mutation과 동시인 revocation closure, 실제 PNG export, Blogger delivery, destination readback, success/failure/unknown의 외부 판정은 모두 `BLOCK-05` 소유이며 여기서 완료로 주장하지 않는다.

포함: production FastAPI/static single-serving shell, Vue/Vite build and package boundary, same-origin snapshot/baseline/intent/composition/generation/STOP/review APIs, monotonic SSE와 gap recovery, explicit Structural Baseline/Re-baseline과 source-brief boundary, one-store server/draft/save isolation, exactly-five currency UI, serialized CAS save 및 실패/충돌 보존, desktop/responsive studio surfaces, native normalized pointer/keyboard editing, queue popover, immediate STOP UX, immutable artifact review와 exact displayed identity/hash approval-request handoff.

제외: durable release authorization/revocation의 end-to-end 완료 판정, export payload 또는 PNG 생성, Blogger 요청·발행·재조회, destination evidence, 외부 전달 성공 선언, 임의 N-cut, SSR/별도 frontend production server, WebSocket/GraphQL, 범용 canvas·DnD·component suite, 과거 `comic` 호환 또는 새 mutable authority.

## Acceptance

아래 시나리오는 generated production build, 실제 `comic-new serve`, 실제 브라우저, 실제 FastAPI 요청/SSE, 실제 disposable project SQLite와 해당 SQLite를 다시 여는 authoritative readback을 사용한다. mock snapshot, stubbed store/service, Vite dev server, unit/component test, source inspection 또는 screenshot만으로는 어떤 시나리오도 충족할 수 없다.

### A. 한 process의 실제 production studio (Baseline Exit 1-6)

1. production frontend build를 실행하면 generated index와 content-hashed JavaScript/CSS asset이 Python package static 경계에 생성된다.
2. 실제 초기화된 project를 대상으로 `comic-new serve` 하나만 실행하고 브라우저로 `/`을 열면 generated studio가 로드되며, network readback에서 index와 그 index가 참조한 hashed JS/CSS가 모두 성공한다.
3. 같은 origin의 `/api` snapshot을 브라우저가 읽고 SQLite를 별도 connection/process에서 다시 연 결과와 동일한 authority revision, exactly-five cuts, composition, jobs 및 artifact identities를 본다.
4. production 동작 중 별도 Node/Bun/Vite/SSR/frontend server process가 존재하지 않는다. Node/Bun은 build-time에만 관찰될 수 있다.
5. generated index가 없는 동일 production 실행을 시도하면 `serve`는 non-zero startup failure와 원인을 드러내며, 빈 HTML이나 성공한 empty shell을 제공하지 않는다.

### B. Exactly-five truth와 분리된 상태 차원 (Baseline Exit 7-10)

1. SQLite에 stable `cut_id` 1..5만 있는 프로젝트를 열면 CutRail에 같은 순서의 다섯 slot만 보이고 각 slot에서 desired/realized revision과 Current 또는 STALE를 읽을 수 있다. add/delete/reindex UI는 없다.
2. 다섯 개의 유효한 이전 pixel asset이 있어도 cut 하나를 새 desired revision으로 수용하여 `desired_revision != realized_revision`으로 만들면, 새 snapshot/SSE 뒤 해당 이전 pixel은 보존되어 보이되 명백한 persistent STALE 표시가 함께 보인다.
3. 그 상태에서 Header의 realization truth는 `Complete`가 아니라 `UNRESOLVED`이며 review materialization은 비활성화된다. job status가 succeeded이거나 queue가 비어 있어도 이 판정은 달라지지 않는다.
4. Header에서 execution, realization currency, release authorization, delivery outcome은 별도 표시로 읽히며 하나의 generic success/published 상태로 합쳐지지 않는다.

### C. 단일 store와 save 격리 (Baseline Exit 11-20)

1. production bundle/runtime에서 domain mutable Pinia store가 `useStudioStore` 하나뿐임을 확인하고, CutRail·Canvas·Inspector·Header가 동일한 server/draft/save 상태 전이를 반영한다. component-local pointer gesture 외의 복제 domain store나 query cache가 별도 truth를 주장하지 않는다.
2. Inspector에서 bubble text를 바꾸거나 Canvas에서 geometry를 commit하면 화면은 즉시 local draft를 투영하지만, save acceptance 전의 API snapshot과 별도 SQLite readback은 그대로이고 UI에는 미저장임이 지속 표시된다.
3. save 요청에는 관찰한 base composition revision 또는 동등한 concurrency identity와 해당 local mutation identity가 실린다. 첫 요청의 응답을 지연한 동안 두 번째 edit를 만들면 동시에 둘 이상의 composition save가 비행하지 않고, 첫 acceptance가 와도 두 번째 draft는 지워지거나 과거 값으로 역전되지 않은 채 다음 순서로 저장된다.
4. 브라우저와 server 사이의 save network를 실제로 끊어 실패시키면 draft와 입력 내용은 남고 `저장 실패 — 변경 내용은 이 브라우저에만 남아 있습니다.` 성격의 alert toast가 보인다. toast가 사라진 뒤에도 영향받은 object/field와 canvas 상태에 persistent `저장 안 됨` 표시가 남고 review materialization은 비활성화된다.
5. 두 browser client가 같은 base revision을 편집하여 한쪽을 먼저 실제 SQLite에 수용한 뒤 다른 쪽이 저장하면 후자는 실제 HTTP 409와 최신 server readback을 받는다. 충돌한 local draft는 삭제되지 않고 `서버 값 보기`와 `최신본에 다시 적용`에 해당하는 명시적 비교/재적용 경계를 제공하며 review는 계속 비활성화된다.
6. dirty draft가 있는 동안 다른 client의 accepted change와 SSE가 도착하면 server 계층과 authoritative revision은 갱신되지만 local draft는 그대로 유지되고 `base changed`/conflict 성격을 드러낸다. local projection이 새 server snapshot으로 조용히 덮이거나 반대로 server truth로 위장되지 않는다.
7. retry 또는 reconcile이 실제로 수용되면 그 응답이 식별한 mutation만 cleared되고, fresh API snapshot과 별도 SQLite readback의 composition revision/state가 화면의 saved 표시와 일치한다.

### D. SSE monotonicity와 gap recovery (Baseline Exit 21-27)

1. studio snapshot load 후 browser는 같은 FastAPI process의 native EventSource에 연결하고, stream의 event ID/domain revision과 연결 상태를 관찰할 수 있다.
2. 실제 API로 연속 mutation/job transition을 발생시켜 newer event를 적용한 뒤 duplicate 또는 older entity revision이 전달되어도 browser의 server layer, cut revision과 job truth가 역행하지 않는다. local draft는 어느 event에도 삭제되지 않는다.
3. durable job이 `completed`/`succeeded`로 전환되는 event만 전달된 상태에서는 해당 cut의 realized revision이나 Current가 바뀌지 않는다. 현재 desired revision에 대해 canonical realization이 수용된 authoritative payload와 새 SQLite snapshot을 받은 경우에만 realized revision이 갱신된다.
4. superseded/cancelled/late-success event 뒤에도 이전 pixel은 보존될 수 있으나 `desired_revision != realized_revision`이면 STALE이고, late result가 canonical asset/currency를 덮지 않는다.
5. stream 연결을 끊은 사이 실제 SQLite authority를 둘 이상 전진시켜 replay 범위를 벗어난 gap 또는 `snapshot-required`를 만든 후 재연결하면 browser는 authoritative studio snapshot을 한 번 다시 읽어 server 계층만 교체하고 최신 SQLite readback으로 수렴한다.
6. EventSource 연결 장애 중 Header는 persistent reconnecting 상태를 보이되, running job을 interrupted/failed로 만들거나 queue를 비우거나 cut을 Current로 만드는 domain truth를 임의 생성하지 않는다.

### E. 즉시 STOP과 queue truth (Baseline Exit 28-33)

1. 실제 long-running generation subprocess를 가진 durable running job과 queued job을 만든다. Header는 현재 선택·scroll·QueuePopover 개폐와 무관하게 active/stoppable count와 enabled global STOP을 보이며, QueuePopover는 queued/running job 각각의 target cut, target desired revision, progress/status와 per-job STOP을 보인다.
2. global STOP 또는 per-job STOP을 누르면 confirmation dialog 없이 즉시 same-origin API 요청이 나가고 browser는 우선 `stopRequested`만 표시한다. 실제 SQLite/SSE terminal readback 전에는 running job을 interrupted/cancelled/succeeded로 위장하지 않는다.
3. server가 실제 process tree를 종료하고 SQLite에 terminal execution truth를 기록한 뒤 SSE/snapshot으로 그 상태를 읽었을 때만 terminal UI가 된다. 별도 process observation에서 대상 subprocess가 더 이상 살아 있지 않다.
4. fresh SQLite connection과 browser readback에서 accepted desired intent는 STOP 전과 동일하고, 미완성 revision의 기존 pixel은 남아 있으면서 cut은 STALE, 전체는 UNRESOLVED이다. STOP은 release/delivery truth를 승격하지 않는다.

### F. Canonical percentage interaction (Baseline Exit 34-39)

1. 실제 composition surface에서 bubble을 pointer로 이동·resize해 저장한 뒤 desktop 폭, narrow 폭, browser resize와 visual zoom을 바꾼다. fresh SQLite의 `x_pct`, `y_pct`, `w_pct`, `h_pct`가 동일하며 surface 대비 상대 geometry도 같은 canonical 의미를 유지한다.
2. primary pointerdown 뒤 element가 pointer capture를 보유하고, 실제 drag의 transient frames는 authoritative snapshot/SQLite를 변경하지 않는다. pointercancel을 발생시키면 transient gesture만 마지막 local draft 위치로 되돌아가고 save 요청이나 composition revision 증가가 없다.
3. pointerup은 normalized local draft 하나와 save 시도 하나를 만들지만 acceptance 전까지 saved로 표시하지 않는다. acceptance 후 fresh SQLite state와 화면 geometry가 일치한다.
4. focused bubble/resize handle을 arrow key로 움직이면 canonical percentage가 정확히 `0.5%`, Shift+arrow이면 `2.0%` 변한다. pointer와 keyboard 모두 같은 clamp/normalized model을 사용하고, viewport pixel delta를 authoritative geometry로 저장하지 않는다.

### G. Non-modal shell과 responsive 보존 (Baseline Exit 43-44)

1. desktop viewport에서 Header, Left Rail, Center Canvas, Right Inspector가 동시에 보이고 각 panel의 독립 scroll/selection 중에도 Canvas와 Header STOP에 접근할 수 있다. Inspector의 ordinary text/style/geometry edit는 focus trap이나 modal overlay를 만들지 않는다.
2. 1100px 미만의 narrow viewport에서 Center Canvas는 영구 유지되고 Left/Right는 독립 toggle의 viewport-edge non-modal panel이 된다. 열린 edge panel은 focus를 가두지 않으며 닫은 뒤 편집 draft와 selection을 보존한다.
3. QueuePopover는 Header trigger에 anchor되고 non-modal이며 Canvas 편집을 차단하지 않고, 닫힐 때 focus가 trigger로 돌아간다. ordinary selection, queue inspection, save feedback과 STALE/unsaved 표시에는 focus-trap modal이 없다.

### H. Server artifact 그대로의 검토와 exact approval input (Baseline Exit 40-42)

1. 실제 SQLite project를 exactly five Current이고 unsaved/failed/conflict가 없는 상태로 만든 뒤 browser에서 review materialization을 요청한다. FastAPI가 기존 canonical composition service로 생성·등록한 artifact의 `artifact_id`, content hash, composition revision, ordered five desired/realized/asset closure를 응답하고, 별도 SQLite readback과 artifact file hash가 모두 일치한다.
2. ReviewModal은 그 same-origin artifact URL의 실제 immutable PNG bytes를 `<img>` 계열 pixel surface로 표시하고 contain/zoom만 제공한다. modal 내부에 browser-rendered bubble text/geometry layer나 current editor DOM capture가 최종 승인 이미지로 존재하지 않는다. displayed bytes의 SHA-256이 화면에 표시된 hash 및 SQLite artifact identity와 일치한다.
3. ReviewModal만 focus trap을 사용한다. 열려 있는 동안 Esc/닫기는 승인 없이 종료하고 Canvas를 변경하지 않으며, 다시 열어도 선택한 immutable artifact bytes와 identity가 일치한다.
4. 승인 조작 시 browser가 실제 FastAPI approval handoff에 보낸 request를 관찰하면 payload의 artifact ID와 full content hash가 바로 그 순간 modal에 표시된 값과 byte readback의 값에 정확히 일치한다. modal을 연 뒤 composition/cut identity가 authoritative하게 바뀌거나 다른 artifact를 선택하면 오래된 displayed identity를 current approval로 제출할 수 없다.
5. 이 시나리오의 성공은 approval request identity handoff까지이다. authorization row의 생성·재시작 보존, 이후 accepted change와 동시인 revocation, export/Blogger 가능 여부나 delivery 성공은 이 Scope의 성공 판정으로 사용하지 않는다.

### I. 실제 readback과 false-success 차단의 종합 경계

1. A-H를 하나의 disposable project에서 잇는 production run에서 browser에 표시된 saved/current/job/artifact 값은 매 단계 새 HTTP snapshot과 별도 process의 SQLite readback으로 교차 확인한다. browser cache, SSE payload 단독, in-memory flag 또는 screenshot은 authoritative evidence가 아니다.
2. old pixels가 있는 STALE cut, save network failure, 409 conflict, duplicate/older/gapped SSE, late superseded job, STOP-before-terminal-readback, artifact bytes/identity mismatch 중 하나라도 주입되면 관련 success control과 review가 차단되고 사용자 입력·기존 valid pixels·authoritative SQLite truth가 각 규칙에 맞게 보존된다.
3. production server restart 후 accepted intent/composition/job terminal truth와 registered artifact identity는 fresh snapshot으로 다시 표시되고, local browser draft는 server authority로 복구된 척하지 않는다. 재시작만으로 fake running, Complete, authorized, delivered 또는 published 상태가 생기지 않는다.
4. UI가 release authorization이나 delivery history를 snapshot에서 표시하는 경우 exact artifact-bound authorization과 `unknown`/`confirmed_failure`/`confirmed_success`를 분리하여 그대로 투영한다. 승인 버튼 성공, artifact 존재 또는 local request 완료를 external delivery success로 표시하지 않는다.

### J. Source Brief에서 baseline·intent·generation으로 이어지는 실제 진입

1. 새로 `comic-new init`한 실제 프로젝트를 Studio에서 열면 baseline이 없다는 상태를 정직하게 표시하고, Source Brief와 정확히 다섯 컷의 구조·초기 intent를 입력해 명시적인 1차 승인을 수행할 수 있다. 승인 전에는 generation/review를 가능한 척 표시하지 않는다.
2. 1차 승인 후 fresh API snapshot과 별도 SQLite readback에서 하나의 current Structural Baseline, stable cut `1..5`, 각 컷의 exactly one effective desired intent와 단조 증가 revision이 동일하게 보인다. 브라우저 draft나 Source Brief 텍스트는 별도 authority가 아니다.
3. 한 컷 내부의 대사·시각 prompt를 저장하면 기존 baseline을 유지한 채 그 컷의 `desired_revision`만 증가하고 이전 pixel은 STALE로 보인다. 컷 역할·순서·상호의존성을 바꾸는 수정은 일반 저장으로 우회할 수 없고 명시적 Re-baseline 확인을 거쳐 새 baseline과 정확히 다섯 intent를 원자적으로 수용한다.
4. 승인된 baseline 뒤 Source Brief 참고 텍스트만 고쳐도 current cut intents, realization, composition 또는 release truth가 암묵적으로 바뀌지 않는다. 이를 작품에 반영하려면 Re-baseline 조작을 사용해야 한다.
5. 사용자가 전체 생성 또는 한 컷 재생성을 요청하면 같은 durable generation queue/API에 정확히 다섯 job 또는 해당 한 job이 현재 desired revision으로 등록된다. UI가 보이는 target cut/revision과 fresh SQLite job readback이 일치하며, 별도 full-run 실행 체계나 client-only queue는 없다.

## External Conditions

검증 환경에는 production frontend build를 수행할 Bun 또는 지원되는 Node toolchain, FastAPI를 포함한 설치된 Python runtime, 실제 Chromium 계열 browser, SQLite, Pillow와 BLOCK-03 canonical renderer가 사용할 유효한 font가 필요하다. Node/Bun은 production serving dependency가 아니다. 외부 Blogger 자격 증명이나 network side effect는 이 Scope에 필요하지 않으며 사용해서도 BLOCK-04 완료 증거가 되지 않는다.

`BLOCK-04` 완료 기록과 `BLOCK-05` 진입은 A-I 전부의 fresh runtime evidence, SQLite authoritative readback, 적용되는 INV-1~INV-8 및 모든 Path Invariant 위반 없음, unresolved proof 없음이 확인된 뒤에만 가능하다. 특히 approval request handoff는 release authorization 또는 delivery 성공을 대신하지 않는다.

## Open Decisions

None
