# Oracle Browser Skill Tradeoff Review

작성일: 2026-08-09  
상태: 티어별 적대적 합의 및 합의안 적용 완료  
대상: `/home/user01/.codex/skills/oracle-browser/SKILL.md`와 직접 의존하는 `oracle-browser-slots`, stock Oracle 0.16.1  
원칙: 스킬의 취지와 핵심 불변조건을 유지하고, 기대효용 대비 비용·회귀·운영·인지·유지보수 부담이 가장 작은 개선부터 검토한다.

## 1. 검토 실행 증거

| 항목 | 값 |
|---|---|
| 초기 Oracle 세션 | `slots-context-oraclesk-df2063c1d3` |
| 관리 슬롯 | 2 |
| CDP | `127.0.0.1:19223` |
| 추론 요청 | `pro` |
| 추론 선택 증거 | `requestedIntent=pro`, `resolvedLevel=pro`, `verified=true` |
| 모델 전략 | `current` |
| 모델 선택 증거 | `status=already-selected`, `verified=false` |
| 브라우저 제한 | `2h` |
| 결과 상태 | `completed` |
| ChatGPT 대화 | `https://chatgpt.com/c/6a789552-f16c-83ee-9de4-6425ace6c9b4` |
| 첨부 방식 | 생성 ZIP 1개 |
| ZIP 크기 | 337,583 bytes |
| ZIP SHA-256 | `24bb440bbc37dfd713ba1ba67d4e9c21b33ef8b741bd2687a522440777911541` |
| 선택 파일 수 | 54 |
| prompt 제출 | 확인됨 |
| ZIP 정리 | 확인됨 |
| manifest | `/home/user01/.oracle/sessions/slots-context-oraclesk-df2063c1d3/artifacts/oracle-browser-slots-attachments.json` |
| transcript | `/home/user01/.oracle/sessions/slots-context-oraclesk-df2063c1d3/artifacts/transcript.md` |
| 초기 답변 | `/tmp/opencode/oracle-browser-skill-tradeoff-initial-response.md` |
| 초기 프롬프트 | `/tmp/opencode/oracle-browser-skill-tradeoff-initial-prompt.md` |

첨부 범위에는 스킬 본문, 전역 OpenCode 지침, Oracle 저장소 지침, 슬롯 래퍼의 README·설계·구현·전체 테스트, stock Oracle의 직접 관련 CLI·브라우저·reasoning·attachment·reattach·session 구현과 테스트가 포함됐다. 자격증명, 브라우저 프로필, 쿠키, 세션 원본, 토큰, 캐시와 관련 없는 사용자 데이터는 포함하지 않았다.

## 2. 판단 기준

### S

실질적 free lunch 또는 near-free lunch다. 기존 동작과 취지를 바꾸지 않으면서 명확한 이득이 있고, 구현·회귀·운영·인지·유지보수 비용이 무시할 수 있을 정도로 작아야 한다.

### A

높은 순효용이 있지만 실제 비용 또는 경계 변화가 있다. 변경 전 정확한 불변조건, 최소 구현면, 검증과 rollback 조건에 합의해야 한다.

### B

상황 의존적이거나 이득과 비용이 가깝다. 구체적 운영 증거, 사용자 조건 또는 live 검증이 있어야 채택한다.

### C

현재는 보류한다. plausible한 이득은 있지만 근거가 약하거나 작은 대안에 지배되거나, 현재 비용이 편익보다 크다.

### X

기각한다. 취지 또는 핵심 불변조건을 훼손하거나, 보이는 마찰을 줄이는 대신 중복 제출·대화 연속성·증거·복구 보장을 약화하거나, stock/래퍼의 기존 책임을 중복한다.

## 3. 방어할 핵심 현행안

1. canonical stock Oracle을 수정하지 않고 절대 경로로 직접 실행한다.
2. WSL Linux Chrome과 loopback CDP의 관리 슬롯만 사용한다.
3. 슬롯 claim과 queue를 원자적으로 관리하고, 애매한 제출을 자동 재시도하지 않는다.
4. 명시된 reasoning level을 슬롯 사정 때문에 낮추거나 높이거나 생략하지 않는다.
5. `current` 전략으로 현재 선택 모델을 유지하며, 실제 모델은 검증 증거 이상으로 단정하지 않는다.
6. 파일 입력은 stock selector를 재사용해 한 ZIP으로 업로드하고 manifest와 cleanup을 남긴다.
7. managed follow-up은 정확한 원 슬롯, 부모·자식 lineage, 동일 대화, prompt 제출, 완료 결과와 authoritative readback을 요구한다.
8. legacy exact-tab은 managed lineage로 위장하지 않는다.
9. DevSpace mode는 별도 trigger, path allowlist, no-ZIP, 자기 수행·비위임 제약을 유지한다.
10. Deep Research, Bridge, Windows Oracle, remote host와 대체 Oracle을 추가하지 않는다.

## 4. 초기 Oracle 제안과 로컬 재평가

초기 Oracle은 시스템을 “근본적으로 건전하지만 국소적으로 과도하게 제약되고 일부 경계가 불명확한 구조”로 판정했다. 로컬 평가는 이 큰 결론에 동의하지만, Oracle의 초기 티어를 그대로 확정하지 않는다.

### 로컬 검증 교정

- Oracle은 ZIP 추출 환경에서 `114 passed, 2 failed`를 보고했다.
- 실제 관리 저장소 `/home/user01/project/oracle/oracle-browser-slots`에서는 `python -m pytest tests`가 `116 passed`로 통과했다.
- 따라서 초기 `A-03`의 근거인 두 실패는 현재 운영 저장소의 회귀 증거가 아니다.
- `attachments.py`와 `runner.py`의 runtime identity가 분리된 사실은 관찰되지만, 현재 canonical 운영 경로는 일치한다.
- 대체 test executable과 selector까지 하나의 injected runtime으로 묶을지는 별도 테스트 계약 선택이며 free lunch가 아니다.
- stock `dryRun.ts`를 로컬에서 추가 확인했다. wrapper가 원 입력을 ZIP 하나로 치환한 뒤 stock dry-run이 보는 attachment는 생성 ZIP뿐이므로, 원 선택 파일 목록의 wrapper-owned dry-run evidence가 없다는 `A-05`의 핵심은 유지된다.
- 초기 live run 자체에서 Pro 선택은 검증됐지만 모델 label은 `verified=false`였다. 현행의 “실제 모델을 단정하지 않는다”는 규칙을 유지해야 한다.

### 잠정 티어 조정

| 초기 ID | Oracle 티어 | 로컬 잠정 티어 | 현재 상태 | 핵심 이유 |
|---|---:|---:|---|---|
| S-01 route-bound preflight | S | S | 논쟁 예정 | pinned/auto/follow-up route를 먼저 확정하는 것은 동작 변경 없이 오사용을 줄인다. |
| S-02 actual OpenCode ID only | S | B/논쟁 | 강한 이견 | 현재 agent-visible한 durable ID 취득 표면이 확인되지 않았다. 강제 실패는 기존 follow-up 기능을 막을 수 있다. |
| S-03 compatibility before ZIP | S | S | 논쟁 예정 | 불가능한 요청에 ZIP 비용을 지불할 이유가 없다. error precedence만 검토한다. |
| S-04 compatible-only diagnostics | S | S | 논쟁 예정 | admission과 무관한 슬롯의 CDP·state를 건드리는 비용을 제거한다. |
| S-05 version gate over verbose help | S | S | 논쟁 예정 | canonical 0.16.1에서 반복 verbose help보다 정확한 version 확인이 작다. |
| S-06 README allocation order | S | S | 논쟁 예정 | 구현·테스트와 문서의 확인된 불일치다. |
| S-07 stock `low` alias parity | S | S | 논쟁 예정 | canonical stock이 받는 alias를 wrapper만 거절한다. 작은 호환성 복원이다. |
| S-08 describe `current` precisely | S | S | 논쟁 예정 | 전략은 유지하고 사실 설명만 바로잡는다. |
| S-09 explicit-parent adoption docs | S | S | 논쟁 예정 | 테스트된 cross-context adoption을 숨기지 않는다. |
| S-10 superseded design banner | S | S | 논쟁 예정 | stale design trap을 한 배너로 제거한다. |
| S-11 conditional reporting | S | S | 논쟁 예정 | 증거를 줄이지 않고 적용 불가능 필드만 제거한다. |
| A-01 FIFO head-only active probes | A | A | 대기 | polling 증폭은 사실이나 terminal failure 전파 지연이 있다. |
| A-02 claim-based follow-up waiting | A | A | 대기 | CDP mutation을 줄이지만 occupied browser failure 조기 감지를 늦춘다. |
| A-03 unify selector/runtime identity | A | B/C | 강등 | 실제 관리 저장소 테스트는 통과한다. nonproduction injection contract의 비용과 목적을 먼저 정해야 한다. |
| A-04 dual-pin legacy exact URL | A | B | 강등 | 위험 경로는 supported inference이며 live trigger와 `/c/<id>` config 수용을 검증해야 한다. |
| A-05 dry-run attachment plan | A | A | 대기 | wrapper가 이미 가진 원 선택 증거를 sessionless preview에서 드러내는 bounded observability 개선이다. |
| B-01 narrow mandatory dry-run | B | B | 대기 | 단순 명시 파일에는 이득이 있지만 분류 오류 비용이 있다. |
| B-02 deadline-aware timeout | B | B | 대기 | 명시 deadline일 때만 의미가 있다. 기본 2h/5h는 방어한다. |
| B-03 reserve after pure validation | B | B | 대기 | ergonomics와 monotonic idempotency 의미가 충돌한다. |
| B-04 deliberate FIFO use | B | B | 대기 | queue wait, frozen ZIP, 외부 timeout을 함께 봐야 한다. |
| B-05 opt-in no-queue | B | B | 대기 | 명확한 용도는 있지만 API와 retry-loop 위험이 생긴다. |
| B-06 medium uses 3-5 first | B | B | 대기 | account/workspace/profile 등가성과 contention 증거가 필요하다. |
| B-07 instant/light on 3-5 | B | B | 대기 | stock capability만으로 live profile 동작을 단정할 수 없다. |
| B-08 claimless dry-run | B | B/C | 대기 | contention 이득과 readiness 검증 손실을 비교해야 한다. |
| C-01 lazy workspace parsing | C | C | 대기 | fail-closed 설정 계약이 더 단순하다. |
| C-02 wrapper-enforced 2h | C | C | 대기 | transport와 consultation policy 책임을 섞는다. |
| C-03 defer ZIP to queue head | C | C | 대기 | snapshot 결정성과 head-of-line 비용을 악화한다. |
| C-04 remove inactivity unset | C | C | 대기 | 외부 consumer 부재가 아직 완전히 증명되지 않았다. |
| C-05 attachment size cap | C | C | 대기 | 실제 한계 근거 없는 임의 cap은 valid request를 막는다. |
| X-01 patch/fork stock | X | X | 대기 | canonical runtime과 최소 변경 원칙을 훼손한다. |
| X-02 `current` replacement | X | X | 대기 | `ignore`는 증거를, `select`는 현재 모델 유지 취지를 훼손한다. |
| X-03 alter reasoning for capacity | X | X | 대기 | 사용자 요청을 다른 제품 동작으로 바꾼다. |
| X-04 multiple browser attachments | X | X | 대기 | upload action과 partial state를 늘린다. |
| X-05 tab/chat existence as success | X | X | 대기 | durable follow-up 증거를 약화한다. |
| X-06 retry/migrate ambiguous work | X | X | 대기 | 중복 prompt와 분기 대화 위험이 편익보다 크다. |
| X-07 shorter shell with 2h capture | X | X | 대기 | stock의 2회 full capture와 모순된다. |
| X-08 remove status entirely | X | X | 대기 | atomic claim은 login/CDP/operator preflight를 대체하지 않는다. |
| X-09 remove DevSpace guard | X | X | 대기 | 재귀·위임 방지 편익에 비해 token 절감이 작다. |

## 5. 티어별 초기 제안

### S 티어

#### S-01: route-bound preflight

현재 문제: `SKILL.md`는 “하나 이상의 사용 가능 슬롯”을 요구하고 initial live 예시는 `submit`만 보여 준다. 그러나 pinned initial, unpinned initial, managed follow-up, legacy exact-tab은 서로 다른 route다.

최소안: 첫 단계에서 route를 확정한다. pinned initial과 legacy exact-tab은 exact `run --slot N`, unpinned initial은 `submit`, managed continuation은 `followup`을 사용한다. status와 dry-run도 같은 route와 compatibility를 기준으로 해석한다.

현행안 방어: wrapper가 최종 compatibility를 검증하므로 안전 실패는 한다.

잠정 판단: 안전 실패까지 기다리는 것은 ZIP·operator 시간을 낭비하고 pinned 요청을 auto route로 바꿀 수 있다. route binding은 동작 추가가 아니라 기존 의도를 명확히 한다.

#### S-02: actual OpenCode conversation ID only

현재 문제: `SKILL.md`는 unique stable context ID를 “create”하라고 하고 README는 current OpenCode conversation에서 와야 한다고 말한다.

Oracle 최소안: runtime이 노출하는 실제 durable ID만 사용하고 invent/hash/substitute하지 않는다. 표면이 없으면 context-aware route를 실패시킨다.

현행안 방어: wrapper의 실질 계약은 같은 OpenCode 대화에서 같은 namespace를 재사용하는 것이다. 현재 agent-visible runtime surface가 ID를 제공하지 않는다면 대화별 stable generated ID가 사용자 목적을 충족한다. “실제 OpenCode ID”라는 출처 순수성을 위해 기능을 막는 것은 편익보다 크다.

잠정 판단: S가 아니다. 먼저 actual ID 취득 표면이 존재하는지와 wrapper가 왜 그 출처를 요구하는지 합의해야 한다. 대안은 스킬을 막는 대신 README를 “current conversation을 대표하고 그 대화에서만 재사용되는 durable context ID”로 바로잡는 것이다.

#### S-03: compatibility and process identity before ZIP

현재 문제: auto submit은 transport validation 뒤 attachment selection·compression·hash를 하고 나서 process identity와 compatible slot 존재 여부를 검사한다.

최소안: pure deterministic rejection을 ZIP 전에 수행한다. request reservation 의미는 별도 B-03에서 다룬다.

현행안 방어: file error를 먼저 보여 주고 queue 전 파일 snapshot을 빨리 고정한다.

잠정 판단: zero-compatible 요청에는 유효한 실행 snapshot 자체가 없으므로 ZIP 비용과 먼저 나오는 file error는 가치가 없다. process identity 확인도 cheap하다.

#### S-04: compatible-only allocator diagnostics

현재 문제: `_diagnostics(slot_ids)`가 `status_all()`로 5개 슬롯 모두를 검사한 뒤 filter한다. status는 CDP I/O와 state mutation을 포함한다.

최소안: compatible slot subset만 status하고 per-slot exception isolation을 유지한다.

현행안 방어: 전체 dashboard를 한 번에 얻고 다른 슬롯 문제를 일찍 발견한다.

잠정 판단: allocator admission은 dashboard가 아니다. ineligible slot의 상태를 mutate하는 것은 불필요한 결합이다.

#### S-05: exact version gate

현재 문제: 고정된 0.16.1 runtime인데 매 작업 첫 호출마다 verbose help 전체를 출력한다.

최소안: 기본 preflight는 `oracle --version`으로 정확히 0.16.1인지 확인하고, help는 version mismatch, rejected option, 진단 시에만 사용한다.

현행안 방어: 실제 executable과 advanced flag 존재를 동시에 보여 준다.

잠정 판단: canonical path와 exact version gate가 동일 목적을 더 작은 출력과 인지비용으로 달성한다.

#### S-06: README routing truth

현재 문제: README는 submit 순서를 고정 `1,2,3,4,5`로 설명하지만 구현과 테스트는 reasoning별 preference order를 사용한다.

최소안: “request-compatible preference order의 첫 available slot”로 수정하고 routing table을 한 곳에 둔다.

현행안 방어: reasoning 미지정 기본만 단순하게 설명한 것이다.

잠정 판단: 일반 계약처럼 쓰인 문장이 high/Pro에서 틀리므로 수정한다.

#### S-07: `low` alias parity

현재 문제: stock은 `low`를 `light`로 normalize하지만 wrapper는 compatible slot을 0개로 판정한다.

최소안: `low`를 `light`/`instant`와 동일하게 처리하고 skill alias와 routing test를 맞춘다.

현행안 방어: skill은 UI intent name을 선호하고 `low`를 안내하지 않는다.

잠정 판단: wrapper는 canonical stock argv를 감싸므로 stock-supported alias만 거절할 이유가 없다. eligibility를 넓히지 않고 동의어만 복원한다.

#### S-08: precise `current` description

현재 문제: skill은 `current`가 picker automation을 피한다고 단정하지만 stock은 `ensureModelSelection`을 호출한다.

최소안: `current`는 model switch를 요청하지 않고 active model 유지가 목적이지만 inspection/verification은 수행한다고 쓴다.

현행안 방어: “picker automation”은 switch를 의미한 축약이었다.

잠정 판단: 전략을 바꾸지 않고 debugging premise만 바로잡는다.

#### S-09: explicit parent adoption semantics

현재 문제: explicit parent는 `require_context=False`로 foreign/contextless managed parent를 허용하고 새 child는 current context에 귀속되지만 skill이 이 adoption을 설명하지 않는다.

최소안: explicit user-named parent는 deliberate adoption이며 context match가 필수가 아니고, child가 current context에 등록됨을 보고한다. implicit selection은 exact-context-only로 유지한다.

현행안 방어: 명시한 session ID 자체가 충분한 동의다.

잠정 판단: 동의 여부와 ownership transition의 가시성은 다르다. 이후 implicit chain이 달라지므로 보고한다.

#### S-10: superseded design banner

현재 문제: `DESIGN-slot-workspace.md`가 preimplementation v0.1 상태로 남아 있고 현재 HTTPS host allowlist, global launcher-only, slot mapping behavior와 충돌한다.

최소안: 본문을 다시 쓰지 않고 상단에 superseded banner와 현재 authoritative README·implementation·test를 가리킨다.

현행안 방어: v0.1과 review draft 표기가 이미 역사 문서임을 드러낸다.

잠정 판단: 상세 내용이 현재 계약처럼 검색되는 비용이 크고 banner 비용은 거의 없다.

#### S-11: operation-conditional reporting

현재 문제: 모든 성공에 parent/child, manifest, same-conversation, endpoint, transcript를 요구하지만 operation에 따라 존재하지 않는다.

최소안: 항상 필요한 필드, file-bearing 전용, follow-up 전용, troubleshooting/user-request 전용을 나눈다. 적용 불가능한 값을 만들지 않는다.

현행안 방어: verbose evidence가 복구에 유리하다.

잠정 판단: applicability filtering은 증거 약화가 아니다. 실패와 ambiguity는 넓게 보고하되 정상 성공은 실제 operation에 필요한 증거만 낸다.

### A 티어

#### A-01: FIFO head-only active diagnostics

모든 waiter가 0.2초마다 global coordinator lock 안에서 active diagnostics를 하지만 head만 claim할 수 있다. non-head는 queue 존재·position·cancel만 확인하고 head만 status·claim하도록 바꾸는 안이다.

편익: polling work와 CDP mutation, lock hold를 waiter 수 배에서 head 하나로 줄인다.

대가: terminal unavailability를 non-head가 자기 차례 전에는 알지 못하고 실패 전파가 순차적이다.

#### A-02: claim-driven follow-up waiting

follow-up은 occupied origin을 기다리는 동안 0.2초마다 state-mutating status를 하고 다시 claim한다. initial classification 뒤 exact slot의 `claim_for_auto`를 admission authority로 사용하자는 안이다.

편익: TOCTOU와 transient CDP reprepare latch 노출을 줄인다.

대가: live owner가 있는 동안 browser/CDP가 죽은 사실을 waiter가 조기에 발견하지 못할 수 있다.

#### A-03: unified selector/runtime identity

runner test executable injection과 attachment selector의 canonical path가 분리돼 있다. Oracle은 동일 resolved runtime에서 selector와 child를 파생하자고 했다.

로컬 교정: 실제 canonical 저장소의 116 tests는 모두 통과한다. 현재 production split-brain 증거는 없다.

잠정 판단: 대체 executable을 어느 정도 stock-compatible fixture로 취급할지 정하기 전에는 A가 아니다. 테스트 편의 때문에 production canonical selector를 상대화하면 오히려 invariant가 약해질 수 있다.

#### A-04: dual-pin legacy exact conversation

legacy exact-tab에 `--browser-tab <url>`뿐 아니라 `--chatgpt-url <same-url>`도 전달해 stock reset callback이 workspace가 아니라 같은 `/c/<id>`로 돌아가게 하자는 안이다.

편익: 조건부 wrong-chat submission을 예방한다.

대가: reset trigger가 실제로 발생하는지, `/c/<id>`가 config URL로 안전한지 live proof가 없다. 검증 전 mandatory화하면 새로운 failure mode가 생긴다.

#### A-05: wrapper-owned dry-run attachment plan

sessionless dry-run 전에 selected count/bytes, `--files-report`일 때 relative paths/sizes, ZIP hash/size를 lifecycle record로 출력한다.

편익: stock은 wrapper가 치환한 ZIP 하나만 보므로 원 selection을 authoritative하게 확인할 수 있다.

대가: JSONL event와 test가 늘고 relative path도 민감할 수 있어 상세 출력은 opt-in이어야 한다.

### B 티어

#### B-01: uncertainty-bearing requests만 mandatory dry-run

directory, glob, exclusion, ignore-sensitive, large/uncertain, changed route, legacy exact-tab, changed/failed runtime은 mandatory로 유지하고 작은 explicit file list는 optional로 하자는 안이다. 분류 오류가 live path로 넘어가는 비용 때문에 조건부다.

#### B-02: explicit deadline에만 shorter browser timeout

Pro 기본 2h와 shell 5h를 유지한다. 사용자가 hard deadline을 준 경우에만 browser timeout을 줄이고 shell limit은 `2 * browser timeout + overhead` 이상으로 계산한다. measured completion data 없이 일반 default를 줄이지 않는다.

#### B-03: pure rejection 뒤 request ID 예약

transport/context/parent/compatibility의 pure validation 뒤, attachment·queue·claim 전 예약한다. local typo 뒤 같은 ID를 고칠 수 있지만 “첫 시도부터 영구 tombstone”이라는 monotonic idempotency 의미를 바꾼다.

#### B-04: unpinned submit에서 deliberate FIFO 허용

compatible slot이 healthy occupied이고 전체 time budget이 queue+capture를 감당할 때 queue 진입을 허용한다. 무기한 wait, ZIP snapshot 고정, disk와 external timeout 비용이 있다.

#### B-05: opt-in `submit --no-queue`

즉시 claim이 안 되거나 기존 queue가 있으면 enqueue하지 않고 structured diagnostic을 반환한다. deadline-sensitive use case가 있지만 public API, retry loop와 utilization 저하 위험이 있다.

#### B-06: medium은 3-5 우선

Pro-only capacity인 1-2를 아끼기 위해 medium preference를 3-5,1-2로 바꾸는 안이다. 실제 Pro contention과 account/workspace/profile equivalence 증거 없이는 채택하지 않는다.

#### B-07: instant/light를 3-5로 확대

stock capability rank상 가능해 보이지만 account UI와 reasoning selection live evidence가 없다. 슬롯별 controlled live proof 뒤 판단한다.

#### B-08: claimless sessionless dry-run

stock dry-run이 browser automation 전에 종료하므로 wrapper claim/CDP/login 없이 preview하는 안이다. preview contention은 줄지만 live readiness proof를 잃고 execution branch가 하나 늘어난다.

### C 티어

#### C-01: command별 lazy workspace parsing

잘못된 mapping이 status/follow-up도 막는 문제는 있으나 fail-closed 전체 설정 계약이 더 단순하다. 실제 blocked recovery incident 전에는 보류한다.

#### C-02: wrapper가 2h timeout 강제

transport invariant와 consultation policy를 섞고 다른 caller에도 영향을 주므로 보류한다.

#### C-03: queue head에서 ZIP 생성

disk retention은 줄지만 submit-time snapshot 결정성을 잃고 head-of-line에서 compression failure와 지연이 발생하므로 보류한다.

#### C-04: inactivity-timeout unset 제거

supplied stock/wrapper에는 consumer가 보이지 않지만 외부 shell/service consumer 부재가 완전히 증명되지 않았다. 편익도 작으므로 보류한다.

#### C-05: wrapper attachment size cap

실제 downstream failure boundary와 incident 없이 숫자를 정하면 유효한 evidence bundle을 임의로 거절한다. 보류한다.

### X 티어

다음은 초기부터 기각 후보로 분류한다.

| ID | 기각안 | 기각 근거 |
|---|---|---|
| X-01 | stock patch/fork | canonical identity, updateability, 최소 변경을 훼손한다. |
| X-02 | `current`를 `ignore`/`select`로 교체 | active model 유지 또는 evidence를 훼손한다. |
| X-03 | capacity 때문에 explicit reasoning 변경 | 사용자 요청을 조용히 다른 동작으로 바꾼다. |
| X-04 | multiple browser attachments | upload action, partial state, ambiguity를 늘린다. |
| X-05 | tab/chat 존재를 follow-up 성공으로 간주 | durable lineage·submission·result 증거를 잃는다. |
| X-06 | ambiguous submission 자동 retry/migrate | duplicate prompt와 divergent chat 위험이 크다. |
| X-07 | 2h capture를 유지하며 shell만 단축 | stock의 full reload retry를 중간 종료한다. |
| X-08 | status/preparation 완전 제거 | login/CDP/operator recovery를 atomic claim이 대체하지 못한다. |
| X-09 | DevSpace per-turn guard 제거 | recursion/delegation 위험에 비해 token 절감이 작다. |

## 6. 확인된 정합성 문제

1. skill의 context ID “create”와 README의 “actual current OpenCode conversation ID”가 충돌한다. 어느 쪽을 authoritative하게 할지는 S 티어 논쟁 대상이다.
2. README의 fixed submit order는 reasoning-aware implementation과 tests에 어긋난다.
3. wrapper는 stock-supported `low` alias를 거절한다.
4. workspace v0.1 design draft는 현재 URL validation과 injection contract에 어긋난다.
5. skill은 `current`가 picker automation을 피한다고 과장한다. stock은 model inspection/selection routine을 호출한다.
6. explicit parent adoption의 cross-context semantics가 skill에 없다.
7. success reporting은 operation별 적용 가능성을 구분하지 않는다.
8. dry-run은 wrapper가 가진 원 선택 파일 evidence를 노출하지 않고 stock에는 생성 ZIP만 보인다.

## 7. 논쟁 프로토콜

각 티어는 동일 Oracle 대화에서 다음 순서로 진행한다.

1. 로컬 측은 현행안을 최대한 강하게 방어한다.
2. 로컬 측은 Oracle 제안의 hidden cost, behavior drift, maintenance burden과 smaller alternative를 공격한다.
3. Oracle은 제안과 현행안을 공격적으로 재검토한다.
4. 로컬 측은 새 공격을 evidence와 tradeoff로 재방어한다.
5. 합의가 없고 materially 다른 쟁점이 남으면 같은 티어에서 follow-up을 반복한다.
6. 합의는 `ACCEPT`, `ACCEPT_WITH_BOUNDARY`, `DEFER`, `REJECT`, `BOUNDED_DISAGREEMENT` 중 하나로 기록한다.
7. 합의에는 exact wording/behavior, rejected alternative, validation evidence, residual disagreement 또는 reconsideration trigger가 있어야 한다.
8. 이전 티어가 닫히기 전에 다음 티어로 넘어가지 않는다.

## 8. 티어별 합의 기록

### S 티어 합의

상태: 닫힘

Oracle follow-up child: `slots-followup-oraclesk-fb41a27640`

검증된 연속성: parent `slots-context-oraclesk-df2063c1d3`, original slot 2, same ChatGPT conversation, prompt submitted, child completed, stored result available, `verification.ok=true`

#### 합의 결과

| ID | 결론 | 합의된 경계 |
|---|---|---|
| S-01 | `ACCEPT_WITH_BOUNDARY` | route를 status/preview 전 확정한다. auto preview는 sampled compatible slot의 argv·control plan·정규화된 ZIP·표시된 target만 검증하고 eventual slot, login, workspace access, DevSpace MCP를 보장하지 않는다. workspace/account/profile correctness가 중요하면 pinned route다. managed follow-up은 global any-slot availability로 gate하지 않는다. |
| S-02 | `ACCEPT_WITH_BOUNDARY` | runtime-provided current conversation ID가 있으면 사용하되, 없으면 conversation owner가 collision-resistant key를 한 번 생성한다. delegated invocation은 owner key를 받아야 한다. 첫 authoritative registration에서 exact readback을 확인하고 key를 한 번 보고한다. key를 잃으면 prior report 또는 known managed session metadata에서 복구하며 조용히 재생성하지 않는다. README도 provenance가 아닌 enforceable exact-string ownership semantics로 맞춘다. |
| S-03 | `ACCEPT_WITH_BOUNDARY` | request ID 예약과 transport validation 뒤 compatible slots, process identity를 ZIP 전에 확인한다. compatibility를 identity보다 먼저 검사한다. error precedence 변화는 의도된다. reservation과 queue-time ZIP snapshot은 유지한다. |
| S-04 | `ACCEPT_WITH_BOUNDARY` | allocator admission diagnostics는 compatible subset만 probe한다. 출력은 request preference order가 아니라 기존 slot-number order를 유지하고 입력을 deduplicate한다. no-argument diagnostics, all-slot duplicate detection, global `status`는 유지한다. |
| S-05 | `ACCEPT` | 첫 stock invocation 전 canonical `oracle --version`이 정확히 `0.16.1`인지 확인하고 mismatch면 중단한다. verbose help는 rejected option 진단, intentional upgrade 검토, version mismatch 분석에만 쓴다. |
| S-06 | `ACCEPT_WITH_BOUNDARY` | README의 fixed order를 “model/reasoning-compatible preference order”로 수정한다. executable authority와 regression test를 가리키되 README에 두 번째 상세 routing table은 만들지 않는다. skill의 concise routing list는 유지한다. |
| S-07 | `ACCEPT` | stock alias `low`를 `light`/`instant`와 동일하게 받아 exact `(1,2)` eligibility를 유지한다. test와 skill alias만 맞추며 slot 확대는 하지 않는다. |
| S-08 | `ACCEPT_WITH_BOUNDARY` | `current`는 active-model switch를 요청하지 않는다. new non-resumed request에서는 stock model evidence path가 실행되지만 resumed follow-up에서는 selection을 skip한다. `already-selected`와 `verified=false`를 model verified로 해석하지 않는다. |
| S-09 | `ACCEPT_WITH_BOUNDARY` | explicit parent는 사용자가 정확한 managed session 계속을 요청했을 때만 사용한다. context equality는 eligibility 조건이 아니지만 origin·conversation·termination·slot·readback은 우회하지 않는다. child는 current context로 등록된다. parent metadata로 different/missing context가 확인될 때만 confirmed adoption이라고 보고하고, 그렇지 않으면 context relation 미검증으로 보고한다. |
| S-10 | `ACCEPT_WITH_BOUNDARY` | v0.1 design 최상단에 historical, non-authoritative, superseded, do-not-use-as-contract 배너와 current README·implementation·test pointer를 둔다. 역사 본문은 삭제·rewrite·inline correction하지 않는다. |
| S-11 | `ACCEPT_WITH_BOUNDARY` | live 공통, file-bearing, managed follow-up, legacy exact-tab, dry-run, ambiguity/failure별 reporting matrix를 적용한다. clean success에서 endpoint와 transcript path는 optional이지만 ambiguity/failure에서는 duplicate 방지에 필요한 모든 path와 submission evidence를 보고한다. dry-run은 original source-file set을 독립 검증했다고 주장하지 않는다. |

#### 기각된 대안

1. OpenCode runtime ID API가 없다는 이유만으로 context-aware workflow 전체를 실패시킨다.
2. generated context key를 잃은 뒤 같은 대화에서 조용히 새 key를 만든다.
3. auto dry-run이 eventual slot 또는 workspace를 검증했다고 주장한다.
4. managed follow-up을 global any-slot availability로 gate한다.
5. compatible slot이 0개인 요청도 attachment selection·ZIP을 먼저 수행한다.
6. allocator visibility를 이유로 ineligible slot의 stateful status를 probe한다.
7. verbose help를 integrity check로 매번 실행한다.
8. README에 또 하나의 상세 routing table을 만든다.
9. stock의 valid `low` alias를 wrapper에서 거절한다.
10. `current`가 model logic을 항상 수행하거나 항상 skip한다고 단정한다.
11. deliberate explicit-parent continuation을 전면 금지하거나, 모든 explicit parent를 cross-context adoption이라고 부른다.
12. historical workspace design을 삭제하거나 current spec으로 다시 쓴다.
13. clean success에도 endpoint와 artifact path를 항상 강제한다.

#### 검증 조건

- baseline: 실제 관리 저장소 `116 passed`.
- S-03: incompatible request와 missing process identity에서 attachment selector가 호출되지 않고 기존 reservation과 rejection record가 유지되는 focused check.
- S-04: compatible slot만 probe하고 slot-number order와 deduplication을 유지하며 default all-slot duplicate path가 바뀌지 않는 focused check.
- S-07: `low`가 exact `(1,2)`를 반환하고 다른 routing이 바뀌지 않는 focused check.
- 나머지는 cited implementation, existing tests, live model evidence와 exact wording consistency review.

#### 허용된 잔여 한계

- generated context key는 runtime-attested identity가 아니라 caller-scoped ownership key다.
- auto preview는 future atomic assignment를 예측하지 않는다.
- authoritative follow-up readback은 parent context key를 직접 노출하지 않는다.
- historical document의 top banner는 중간 문단만 잘라낸 검색 결과까지 통제하지 못한다.

이 한계는 더 강한 보장으로 오인하지 않도록 명시됐으며 S티어 재논쟁 사유로 남지 않는다.

### A 티어 합의

상태: 닫힘

Oracle follow-up child: `slots-followup-oraclesk-742d3f7084`

검증된 연속성: parent `slots-followup-oraclesk-fb41a27640`, original slot 2, same ChatGPT conversation, prompt submitted, child completed, result available, `verification.ok=true`

#### 합의 결과

| ID | 결론 | 합의된 경계 |
|---|---|---|
| A-01 | `ACCEPT_WITH_BOUNDARY` | 각 queued waiter는 enqueue 직전 또는 첫 wait pass에서 compatible-route viability snapshot을 최대 1회 수행한다. 이미 terminal인 non-head는 자기 entry만 원자적으로 제거하고 ZIP을 정리한다. 그 뒤 반복 diagnostics와 claim은 head만 수행한다. non-head는 queue identity·position·cancel·dead-entry purge만 처리한다. head가 terminal이면 자기 entry만 제거하며 다음 waiter가 다음 poll에서 head가 된다. broadcast와 새 queue state는 없다. |
| A-02 | `ACCEPT_WITH_BOUNDARY` | parent selection·argv compatibility·attachment preparation 뒤 origin `status`를 정확히 1회 수행한다. `AVAILABLE`은 즉시 exact claim, race로 `OCCUPIED`이면 wait, 최초 `OCCUPIED`이면 waiting event 뒤 exact `claim_for_auto(..., apply_workspace_mapping=False)`만 polling한다. 이후 status와 periodic CDP probe는 없다. non-occupied rejection은 terminal이며 다른 slot을 보지 않는다. 기존 post-claim `pre_submit_check`는 유지한다. |
| A-03 | `DEMOTE` | production code는 바꾸지 않는다. test executable override는 child execution seam일 뿐 완전한 stock distribution 계약이 아님을 문서화한다. file-bearing selector parity는 canonical installation을 쓰고 packaging/lifecycle unit test는 기존 `FileAttachmentPolicy(selector=...)` seam을 사용한다. 지원되는 alternate production Oracle이 생기거나 실제 version split이 관찰될 때만 재검토한다. |
| A-04 | `ACCEPT_WITH_BOUNDARY` | user가 exact legacy chat을 요청한 경우 known slot pinned `run`에 동일 canonical `/c/<id>` URL을 `--browser-tab`과 `--chatgpt-url` 모두에 전달한다. live 전 exact tab과 dual-pin control plan을 확인하고, live 직전 다시 확인한다. 후에는 stored/live conversation identity, prompt submission, completion, result를 확인한다. mismatch는 failed/ambiguous이며 자동 retry/fallback하지 않는다. 결과는 verified exact-chat continuity이며 managed lineage가 아니다. |
| A-05 | `ACCEPT_WITH_BOUNDARY` | file-bearing `run`·`submit`·managed `followup` 모두 selection·ZIP write·size/hash 완료 후 queue/claim/wait/child 전 `attachment_prepared` event를 정확히 1회 emit한다. count, aggregate source bytes, ZIP name/bytes/SHA-256, manifest-required 여부를 담는다. explicit `--files-report`가 첫 `--` 전에 있을 때만 relative paths/sizes를 포함한다. absolute temp path·contents는 제외하고 upload/submission 증거로 쓰지 않는다. live manifest와 cleanup evidence는 그대로 authoritative하다. |

#### 핵심 트레이드오프 결정

**A-01:** 완전 head-only는 기각했다. Pro head가 slots 1-2를 기다리는 동안 뒤의 다른 route가 이미 전부 unavailable이면 그 non-head가 ZIP을 무기한 보유할 수 있기 때문이다. 최초 snapshot 1회가 이 회귀를 막고, 이후 steady-state polling 증폭만 제거한다.

**A-02:** current loop는 occupied wait 중 초당 5회 CDP·state write/fsync를 수행하고 transient failure를 reprepare latch로 바꿀 수 있다. waiter의 조기 CDP death 감지는 실제 reclaim을 가능하게 하지 않으므로 반복 mutation보다 가치가 작다고 합의했다. 다만 최초 full status와 free-slot claim 시 login/CDP check, post-claim check는 유지한다.

**A-03:** 초기 extracted ZIP 실패는 production defect 증거에서 철회했다. actual managed `116 passed`가 authoritative baseline이다. fake child를 complete stock installation처럼 만들지 않는다.

**A-04:** dual-pin dry-run은 exact `/c/<id>`가 두 stock URL surface에서 수용되고 exact tab reuse plan이 생성됨을 확인했다. static stock trace는 reset callback이 `config.url`로 이동함을 보여 준다. forced destructive live reset은 검증 비용이 남은 불확실성보다 크므로 요구하지 않는다. exact chat에서 안전 실패하는 것이 다른 destination의 성공보다 낫다.

**A-05:** dry-run-only event는 live manifest failure·claim rejection·queue cancel·follow-up wait cancel의 prepared bundle identity를 잃는다. 기본 event는 작고 path detail은 explicit opt-in이므로 all-route pre-submit 1회가 더 낫다.

#### 기각된 대안

1. 처음부터 pure head-only로 두어 initially terminal non-head도 자기 차례까지 기다리게 한다.
2. 모든 waiter가 매 poll마다 global lock 안에서 stateful diagnostics를 계속한다.
3. follow-up waiter가 초당 5회 `status()`로 CDP와 state를 mutate한다.
4. 임의의 느린 CDP probe cadence와 failure threshold를 새로 만든다.
5. fake child executable마다 stock Node/module layout을 요구한다.
6. legacy exact-tab에 `--browser-tab`만 주고 reset target은 workspace로 남긴다.
7. forced reset을 위해 실제 chat mode를 의도적으로 손상한다.
8. dual-pin 결과를 authoritative wrapper lineage라고 부른다.
9. dry-run에만 attachment event를 만들거나, 모든 path를 기본 출력하거나, prepared event를 upload proof로 사용한다.

#### 검증 조건

**A-01:** non-head diagnostics 최대 1회, initially terminal second waiter self-removal, post-snapshot terminal은 head promotion 뒤 종료, terminal heads 순차 제거, non-head cancellation, FIFO·claim·child order 불변.

**A-02:** multi-poll wait에서 status 정확히 1회, 이후 browser_version/state write 없음, owner release 뒤 exact one claim/child, available-to-occupied race 처리, owner disappearance reprepare, free transition 뒤 CDP/login failure pre-child, cancellation cleanup, initially unavailable exact failure.

**A-03:** production code 추가 test 없음. `116 passed` baseline과 README/source consistency review.

**A-04:** 완료된 dual-pin managed dry-run, static stock navigation trace, wrapper caller-URL injection suppression. command normalization test는 추가할 수 있으나 destructive live reset은 요구하지 않는다.

**A-05:** 세 route에서 exactly one pre-submit event, event order, count/bytes/hash equality, `--files-report` before terminator만 path detail, no absolute temp/content, queue/reassignment no duplicate, emission failure cleanup/no claim, manifest/cleanup semantics 불변.

#### 재검토 트리거

- A-01: mixed-compatibility queue에서 post-snapshot terminal waiter의 process/large ZIP retention이 실제로 감당 불가능한 incident를 만든 경우.
- A-02: owner PID가 live인 채 CDP가 죽고 owner-side evidence도 오지 않아 waiter가 managed owner timeout보다 실질적으로 오래 막혔으며 조기 알림이 실제 복구를 가능하게 했을 경우.
- A-03: alternate Oracle이 supported production config가 되거나 supported child/selector version split이 실제 관찰된 경우.
- A-04: natural dual-pin legacy continuation이 prompt 전 이탈하거나 single-pin이 exact chat에서 안전하게 성공하는 상태를 dual-pin이 일관되게 깨는 경우, 또는 stock version 변경.
- A-05: supported JSONL consumer가 additive event를 실제로 거부하거나 기본 event가 유의미한 output burden을 만드는 경우.

허용된 잔여 비용은 모두 위 trigger로 bounded되며 A티어 재논쟁 사유로 남지 않는다.

### B 티어 합의

상태: 닫힘

Oracle follow-up child: `slots-followup-oraclesk-6f6db9bc22`

검증된 연속성: parent `slots-followup-oraclesk-742d3f7084`, original slot 2, same ChatGPT conversation, prompt submitted, child completed, result available, `verification.ok=true`

#### 합의 결과

| ID | 결론 | 합의된 경계 |
|---|---|---|
| B-01 | `ACCEPT_WITH_BOUNDARY` | dry-run 의무를 구조적 조건으로 명확화한다. directory/glob/exclusion/comma/ignore-sensitive/relative-or-unresolved/alias/unknown membership 또는 size, changed route·slot·model·reasoning·URL·mapping·mode·version·wrapper·profile·env, repaired/failing runtime, legacy exact-tab은 mandatory다. separate absolute canonical regular files를 모두 직접 읽고 size·exact membership을 확인했으며 selection syntax가 없고 route/control tuple이 마지막 관련 변경 이후 검증된 경우만 optional이다. 애매하면 mandatory다. |
| B-02 | `ACCEPT_WITH_BOUNDARY` | default는 browser 2h, shell 최소 5h다. user가 browser timeout `T`를 명시하면 exact `T`를 보존한다. `C(T)=2T+1초`는 stock 두 capture와 reload delay의 capture-only floor, `S(T)=2T+1시간`은 현행 reserve를 일반화한 operational shell budget이며 total bound가 아니다. overall deadline이 `C(T)` 이하이면 full recovery가 불가능함을 명시하고 user가 reduced contract를 선택하지 않으면 숨은 변경을 하지 않는다. queue wait는 공식에 포함되지 않는다. |
| B-03 | `REJECT` | first-contact monotonic request-ID reservation을 유지한다. local rejection도 ID를 소비하며 correction은 새 ID를 쓴다. S-03 cheap validation은 reservation 뒤 ZIP 전에 수행한다. expiry/reuse/pre-validation exception은 없다. |
| B-04 | `REJECT` | skill은 compatible slot이 현재 available일 때만 deliberate unpinned submit을 시작한다. status-to-submit race로 queue 진입한 경우 wrapper FIFO가 안전하게 처리한다. no-expiry queue를 normal 또는 bounded user-driven workflow로 안내하지 않는다. 명시적 user override는 higher-order intent로 가능하지만 full post-claim budget, freshness, deadline을 보장한다고 말하지 않는다. |
| B-05 | `DEFER` | `--no-queue`는 추가하지 않는다. 실제 status-available 뒤 race queue 진입, immediate return 필요, OpenCode shell에서 prompt observation/cancel 불가 또는 material loss, pinned route로 해결 불가가 한 trace에서 입증될 때 재검토한다. no-slot 결과도 accepted B-03에 따라 ID를 소비하는 방향이 기본이다. |
| B-06 | `DEFER` | medium order `(1,2,3,4,5)`를 유지한다. medium이 1/2를 점유해 Pro가 기다렸고 동시에 3-5 중 healthy available slot이 있었던 incident와, preferred 후보 각각에서 medium reasoning verified·model unchanged·submission/result success·profile suitability evidence가 모두 있어야 `(3,4,5,1,2)`만 최소 변경으로 검토한다. |
| B-07 | `DEFER` | instant/light eligibility는 1-2로 유지한다. 실제 capacity incident 뒤에만 3-5 각 candidate에서 exact instant resolved, `verified=true`, model unchanged, prompt submitted, result completed, expected profile behavior의 controlled live proof를 수행한다. stock maximum rank와 dry-run만으로 확대하지 않는다. |
| B-08 | `REJECT` | sessionless dry-run도 normal claim lifecycle을 유지한다. exact slot compatibility, atomic ownership, CDP/login readiness, stock preview, ZIP cleanup, release를 검증한다. file selection·ZIP은 이미 claim 전에 수행되므로 claimless의 실제 capacity 이득은 작고, observed contention도 없다. |

#### 핵심 트레이드오프 결정

**B-01:** `small`·`stable` 같은 주관어와 임의 count/byte threshold를 기각했다. structural selection syntax와 locally inspected exact evidence만 사용한다. ordinary unchanged file-free follow-up은 ritual dry-run을 요구하지 않는다. A-05 event는 live approval checkpoint가 아니므로 dry-run을 대체하지 않는다.

**B-02:** shell formula는 guaranteed total duration이 아니다. ZIP·model/reasoning UI·upload·queue·manifest·cleanup은 capture floor 밖이다. user가 overall deadline만 주고 default 5h보다 짧다면 2h capture 유지+truncated recovery, explicit shorter T, deadline 완화 중 materially different 선택이 남으므로 필요할 때만 확인한다.

**B-03:** typo ID의 작은 tombstone보다 “wrapper가 한 번 본 ID는 다른 attempt를 뜻하지 않는다”는 단순 monotonic contract가 크다.

**B-04:** user consent to wait도 queue duration, ZIP age, shell occupancy, post-claim recovery budget을 bound하지 못한다. one shell timeout이 queue와 capture 전체를 덮으므로 deliberate queue는 정상화하지 않는다.

**B-05:** cancellation이 실제 OpenCode shell에서 queue event를 prompt하게 stream하고 process-control handle을 제공하는지는 증거가 없다. use case는 credible하지만 public API와 request-ID semantics 비용 때문에 incident 전 구현하지 않는다.

**B-06/B-07:** capability scarcity 또는 static maximum rank는 profile/account/live reasoning equivalence가 아니다. curiosity를 위해 여러 live chats를 만들지 않는다.

**B-08:** stock preview 자체는 browser automation 전 끝나지만 wrapper dry-run은 managed route가 현재 사용할 수 있음을 함께 증명한다. A-05가 source selection evidence를 닫았으므로 claimless branch의 남은 편익은 관찰되지 않은 짧은 contention뿐이다.

#### 기각된 대안

1. 정의되지 않은 small file discretion 또는 근거 없는 count/byte threshold.
2. reasoning-level timeout matrix 또는 쉬워 보인다는 이유의 timeout 단축.
3. browser timeout만으로 total runtime을 보장한다고 주장한다.
4. local rejection 뒤 request ID를 재사용한다.
5. user가 wait라고 했다는 이유로 no-expiry FIFO를 bounded workflow라고 부른다.
6. incident 없이 `--no-queue` API를 추가한다.
7. abstract scarcity만으로 medium preference를 바꾼다.
8. stock rank만으로 instant eligibility를 넓힌다.
9. contention 증거 없이 claimless dry-run lifecycle을 추가한다.

#### 검증과 재검토 트리거

- B-01: command matrix consistency review. optional 조건을 모두 만족한 live call에서 dry-run이 구체적으로 잡았을 selection/control error가 발생하면 boundary를 강화한다.
- B-02: stock 두 full waits와 1초 delay static proof, explicit timeout dry-run normalization, default 2h/5h examples. stock retry change 시 formula 재계산.
- B-03: 기존 duplicate/queue/follow-up tests와 `116 passed` baseline 유지. reservation storage 자체가 measured exhaustion을 만들거나 caller가 fresh ID를 만들 수 없는 accepted contract가 생길 때만 재검토.
- B-04: recurring intentional admission need와 queue phase를 독립 bound하면서 claim 뒤 fresh capture budget을 보존하는 기존 caller mechanism이 둘 다 있을 때만 재검토.
- B-05: status available, race queue, immediate return need, actual tool cancel/control failure, pinned 불가가 한 concrete trace에 있어야 재검토.
- B-06: concrete Pro contention + candidate medium live evidence 둘 다 필요.
- B-07: concrete instant capacity need 뒤 candidate별 live evidence 필요.
- B-08: dry-run held interval 자체가 live request를 반복적으로 지연한 lifecycle trace가 있어야 재검토.

B티어의 defer는 구현 backlog가 아니라 명시된 증거가 생기기 전 no-change 결정이다.

### C 티어 합의

상태: 닫힘

Oracle follow-up child: `slots-followup-oraclesk-99bca0fb24`

검증된 연속성: parent `slots-followup-oraclesk-6f6db9bc22`, original slot 2, same ChatGPT conversation, prompt submitted, child completed, result available, `verification.ok=true`

#### 합의 결과

| ID | 결론 | 합의된 경계 |
|---|---|---|
| C-01 | `REJECT` | single fail-closed `Settings.from_env()` validity boundary를 유지한다. malformed workspace config는 prepare/status/run/submit/followup 모두 exit 2다. partial settings, ignore option, fallback empty mapping을 만들지 않는다. |
| C-02 | `REJECT` | wrapper는 2h timeout을 inject/minimum/presence-enforce하지 않는다. timeout은 closed B-02의 skill/user policy다. wrapper는 canonical transport invariants만 소유한다. |
| C-03 | `REJECT` | submit-time file selection·ZIP·hash·A-05 evidence를 유지한다. race queue에서도 exact ZIP snapshot을 보유하고 성공·실패·cancel에 cleanup한다. head-time packaging, later snapshot, new reservation state를 만들지 않는다. |
| C-04 | `PROMOTE` | `SKILL.md`의 모든 `env -u ORACLE_BROWSER_INACTIVITY_TIMEOUT_SECONDS` prefix를 제거한다. global unset, absence requirement, watchdog 설명, wrapper config로 대체하지 않는다. canonical CLI/wrapper를 직접 실행한다. |
| C-05 | `REJECT` | generic individual/aggregate/ZIP cap, warning threshold, free-space reserve/config를 추가하지 않는다. B-01 large/uncertain dry-run과 A-05 size evidence를 유지하고 실제 disk/browser/ChatGPT 경계에서 실패·cleanup한다. |

#### 핵심 트레이드오프 결정

**C-01:** partial status는 actual execution이 거절될 invalid environment를 healthy처럼 보여 S-01 preflight를 약화한다. parse error를 고친 뒤 status를 재실행하는 것이 더 단순하다.

**C-02:** force 2h는 explicit user T와 충돌하고, minimum도 deliberate shorter T를 막으며, omission injection은 stock default와 non-skill callers를 바꾸고, presence-only validation도 skill policy를 wrapper API로 중복한다.

**C-03:** head 전 package는 availability를 놓칠 수 있고, claim 후 package는 scarce slot을 compression 동안 잡고, reservation while packaging은 새 lifecycle을 요구한다. snapshot과 error timing도 나빠진다.

**C-04:** 변수는 active shell, user systemd environment, relevant systemd/user config, wrapper, pinned stock에서 모두 absent이고 known occurrence는 unset examples/history뿐이다. parent watchdog은 child `env -u`로 막지 못하며, future child가 변수를 실제 지원하면 silent stripping이 오히려 user policy를 깨뜨릴 수 있다. exact version gate와 source review가 올바른 변경 감지 수단이다.

**C-05:** individual source, aggregate source, ZIP, compression, free disk, memory, browser upload, ChatGPT limit는 다른 차원이다. 측정된 boundary 없이 하나의 숫자로 합치면 known false rejection을 만든다. free-space precheck도 compressibility와 shared-disk TOCTOU를 해결하지 못한다.

#### 기각된 대안

1. status/followup만 invalid workspace config를 무시한다.
2. wrapper가 exact/minimum/default/presence timeout policy를 소유한다.
3. queue head에서 package하거나 slot을 claim한 뒤 package한다.
4. inactivity unset을 undocumented insurance로 유지하거나 global unset/wrapper config로 옮긴다.
5. generic cap, warning, free-space percentage/fixed reserve, 추정 ChatGPT limit를 추가한다.

#### 검증과 재검토

- C-04 적용 뒤 skill에서 변수 occurrence 0, shell/systemd unset, pinned source consumer 0, version check·status·ordinary dry-run prefix 없이 성공, wrapper `116 passed` baseline 유지.
- C-04 restoration은 supported managed component가 exact variable을 consume하고 child environment를 통해 Oracle work를 B-02와 충돌하게 단축하며 explicit unset이 documented policy라는 focused evidence가 모두 있을 때만 가능하다.
- C-01/C-02/C-03/C-05는 현재 backlog로 유지하지 않는다. 미래 incident는 generic proposal을 부활시키지 않고 actual failing boundary에 대한 새 dimension-specific proposal을 요구한다.

C티어의 residual uncertainty는 invalid config가 diagnostic도 막는 점, non-skill caller의 omitted timeout, race-queued ZIP retention, future variable adoption, very large bundle failure다. 어느 것도 기각안이 현재 최선이라는 증거는 아니다.

### X 티어 합의

상태: 닫힘

Oracle follow-up child: `slots-followup-oraclesk-4edf4e3259`

검증된 연속성: parent `slots-followup-oraclesk-99bca0fb24`, original slot 2, same ChatGPT conversation, prompt submitted, child completed, result available, `verification.ok=true`

#### 합의 결과

| ID | 결론 | 합의된 경계 |
|---|---|---|
| X-01 | `NARROW_REJECTION` | managed canonical installation을 patch/fork/shadow하지 않는다. 별도 source checkout의 upstream contribution과 official version candidate 검토는 허용하지만 live managed call에 쓰거나 current evidence로 가장하지 않는다. accepted official upgrade는 별도 migration decision이지 local fork 예외가 아니다. |
| X-02 | `REJECT` | 모든 managed browser route는 `current`를 유지한다. `ignore`, `select`, omission, picker flakiness 기반 dynamic strategy를 금지한다. 사용자는 invocation 밖에서 active model을 먼저 바꿀 수 있지만 in-skill model switching은 product boundary 밖이다. |
| X-03 | `NARROW_REJECTION` | capacity·latency 때문에 explicit reasoning을 alter/omit/substitute하지 않는다. no compatible slot이면 S-03에 따라 ZIP 전 reject한다. 사용자가 설명을 듣고 다른 level을 명시적으로 새로 선택하면 fresh request ID, route/preflight/dry-run을 거친 새 instruction이며 allocator fallback이나 원 요청과 동등하다고 부르지 않는다. |
| X-04 | `REJECT` | file-bearing request는 source 1개여도 generated ZIP 1개만 전달한다. original native files, multiple attachments, ZIP+native mix, direct stock bypass를 금지한다. user는 ZIP content scope 또는 separate DevSpace mode를 선택할 수 있다. |
| X-05 | `NARROW_REJECTION` | browser tab/chat/visible answer alone은 authoritative managed success가 아니다. 그러나 readback failure 뒤 recovered answer content는 failed/ambiguous 또는 browser-complete-but-not-authoritatively-persisted로 명확히 label해 보고할 수 있다. observation source, submission, completeness, failed checks, durable artifact, no-auto-retry를 함께 밝힌다. A-04 legacy continuity는 별도 contract다. |
| X-06 | `NARROW_REJECTION` | submission true/unknown이면 automatic repeat, replacement child, new chat, another slot/profile migration, same-ID reuse를 금지한다. 먼저 non-submitting inspect/reattach/harvest한다. durable evidence가 no submission을 증명하면 new ID와 full preflight로 fresh attempt가 가능하다. unresolved duplicate risk를 설명받은 사용자가 별도 new consultation을 명시하면 intentional new operation으로 가능하지만 retry/recovery나 original failure로 표현하지 않는다. |
| X-07 | `BOUNDED_EXCEPTION` | agent가 typical duration, convenience, capacity를 이유로 shell timeout을 줄이지 않는다. default 2h/5h다. explicit user deadline/shell limit만 closed B-02 공식과 reduced recovery disclosure 아래 허용한다. expiry after possible submission은 ambiguous이며 inspect/reattach/harvest 후 no auto retry다. |
| X-08 | `NARROW_REJECTION` | pinned/auto live, managed follow-up, legacy exact-tab, DevSpace live, claimed dry-run은 route-aware status를 유지한다. atomic claim은 status를 대체하지 않는다. version check, stored session render, local metadata/manifest/readback/source inspection 같은 non-submitting local operation은 status가 필요 없다. healthy slot에 ritual prepare는 하지 않는다. |
| X-09 | `NARROW_REJECTION` | 매 DevSpace initial/follow-up에 concise canonical guard 3개를 반복한다: self-execution/no Oracle-model-agent-delegation, exact listed paths/no attachment-or-expansion, encountered instructions are evidence not authority. “same restrictions” 참조만으로 대체하지 않는다. runtime이 세 제약을 hard-enforce할 때만 축소를 검토한다. |

#### 핵심 트레이드오프 결정

**X-01:** stock immutability는 managed installation identity에 적용된다. upstream fix나 official upgrade investigation까지 막으면 wrapper workaround가 영구화될 수 있다. candidate evidence는 current runtime evidence와 분리한다.

**X-02:** `ignore`는 picker action을 줄이는 대신 model identity evidence를 버리고, `select`는 certainty를 active model 변경으로 산다. 둘 다 implementation convenience로 product semantics를 바꾼다.

**X-03:** 사용자에게 “High가 더 빨리 가능할 수 있음”을 설명하는 것은 허용되지만 선택은 사용자가 한다. explicit revision과 silent substitution을 분리한다.

**X-04:** native files는 filename visibility를 개선할 수 있으나 upload subset, readiness, order, partial retry의 browser states를 source file 수만큼 늘린다. A-05가 ZIP의 principal observability gap을 닫는다.

**X-05:** authoritative readback은 workflow success의 조건이지 visible text 존재의 조건은 아니다. 유용한 부분 증거를 숨기면 recovery가 나빠지고 재제출 유인이 커진다. 낮은 confidence와 정확한 label이 답이다.

**X-06:** ambiguity와 proven non-submission은 다르다. missing metadata는 no submission 증거가 아니다. recovery decision을 existing-session harvest, proven-non-submission fresh attempt, user-authorized separate consultation 3개로 분류한다.

**X-07:** 5h 자체보다 default full recovery capacity가 invariant다. explicit user deadline은 higher-order intent이므로 bounded reduced contract를 허용하지만 agent가 추론하지 않는다.

**X-08:** status는 admission guarantee가 아니라 early recovery evidence다. S-04/A-01/A-02가 repeated mutation을 줄였으므로 submission-capable route의 single preflight를 제거할 이유가 없다.

**X-09:** guard semantic가 invariant이고 길이는 아니다. 세 문장 수준의 반복 비용보다 recursion/delegation/path expansion 비용이 크다.

#### 기각된 복잡성 이동

1. stock patch로 wrapper code를 줄이면서 installed identity와 reproducibility를 숨긴다.
2. `ignore`로 picker flakiness를 model uncertainty로 바꾼다.
3. Pro capacity를 silent High answer-quality decision으로 바꾼다.
4. ZIP I/O를 multiple partial browser transactions로 바꾼다.
5. visible answer를 success로 부르며 persistence/lineage failure를 숨긴다.
6. stranded request를 duplicate와 conversation fork로 바꾼다.
7. average completion time을 이유로 worst-case ambiguity를 늘린다.
8. claim만 믿고 readiness failure와 operator action을 late failure로 옮긴다.
9. initial DevSpace guard 참조만 남겨 enforcement를 model memory에 넘긴다.

#### 재검토 트리거

- X-01: skill/wrapper로 안전히 해결할 수 없고 wrapper complexity가 disproportional인 concrete stock defect는 upstream contribution/official upgrade를 검토한다. local managed patch는 여전히 금지다.
- X-02: product requirement가 current active model 유지에서 requested model selection으로 명시 변경되거나 official stock이 `current`를 보존할 수 없게 된 경우 새 contract review.
- X-03: silent substitution은 재검토하지 않는다. explicit user revision만 가능하다.
- X-04: all-or-none atomic multi-file readiness, exact selected identities, prompt association, cleanup/retry evidence가 ZIP contract와 동등해진 경우.
- X-05: wrapper가 equally durable alternative verification contract를 도입한 경우. browser appearance만으로는 불가.
- X-06: stock/wrapper가 더 강한 durable submission transaction evidence를 제공할 때 safe-retry boundary만 정교화한다.
- X-07: pinned stock retry behavior 변경 시 capture formula 재계산.
- X-08: single route-aware status가 예방 이득보다 큰 concrete harm을 만들고 claim이 equivalent early recovery evidence를 제공할 수 있음이 증명된 경우.
- X-09: DevSpace runtime이 no delegation/recursion, exact path allowlist, instruction isolation을 hard-enforce할 때만 per-turn guard 축소.

X티어는 blanket prohibition이 아니라 managed intent·exact-once·evidence를 보존하는 정확한 거부 경계로 닫혔다.

## 9. 변경 적용 상태

티어별 합의 기록을 완료했고, 후속 요청에 따라 `SKILL.md`, wrapper 구현,
README, historical design과 기존 focused tests에 합의안을 적용했다. 이
문서는 구현 자체가 아니라 합의와 검증 경계를 보존하는 기록이다.

적용 검증:

- `python -m pytest tests`: `121 passed`.
- `python -m compileall -q oracle_browser_slots`: 통과.
- canonical `oracle --version`: `0.16.1`.
- prefix 없는 `oracle-browser-slots status --slot 2`: `사용 가능`.
- prefix 없는 pinned sessionless dry-run: remote Chrome reuse control plan,
  no files, exit code 0, slot release `사용 가능` 확인.
- `SKILL.md`의 `ORACLE_BROWSER_INACTIVITY_TIMEOUT_SECONDS` occurrence: 0.
