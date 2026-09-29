---
title: "oracle-plan-review - 요구사항 구조화와 Dryforge Bridge Packet 스킬 사례"
status: draft
date: 2026-06-17
source: "/home/user01/.config/opencode/skills/oracle_plan_review"
---

## Oracle 분석 요약

`oracle-plan-review`는 큰 요구사항을 바로 구현 계획이나 작업 목록으로 바꾸는 스킬이 아니다. 이 프로젝트의 현재 source of truth 기준 역할은 요구사항을 사용자-visible 성공 흐름으로 재구성하고, 그 흐름을 `Integrated Acceptance Scenario`와 `AS step map`으로 분해한 뒤, 각 step을 `Minimum Reviewable Value Slice` 기준의 MVP로 나누는 것이다. 최종 산출물은 `{project-root}/.oracle/plan-review.md`에 저장되는 요구사항 구조화 문서이며, downstream `oneshot`이 dryforge 3-doc을 만들기 전에 참조할 수 있는 입력 계약을 제공한다.

핵심은 "무엇을 구현할 것인가"가 아니라 "어떤 사용자-visible 흐름이 성공으로 간주되는가", "그 흐름 중 지금 검토 가능한 최소 가치 조각은 무엇인가", "다음 실행 스킬이 이 범위를 어떻게 오해하지 않게 할 것인가"를 문서 계약으로 고정하는 데 있다. 따라서 이 프로젝트는 브레인스토밍 도구라기보다, 큰 요구사항을 downstream 실행으로 넘기기 전의 handoff protocol에 가깝다.

## 1. 프로젝트가 실제로 하는 일

이 스킬은 large requirement를 구현 task 목록으로 직접 바꾸지 않고, 먼저 reviewable planning artifact로 변환한다. 사용자의 원래 의도를 `Reconstructed Intent`로 재구성하고, 전체 성공 흐름을 `Integrated Acceptance Scenario`로 잡은 다음, 각 흐름을 `AS-1.1`, `AS-1.2` 같은 하위 step으로 나눈다. 이 step들은 단순 기능 목록이 아니라, 사용자가 실제로 관찰할 수 있는 결과와 evidence를 보존하는 단위다.

`Integrated Acceptance Scenario`는 프로젝트의 north star 역할을 한다. 여기에는 user-visible goal, entry point, preconditions, trigger, ordered flow, expected result, observable acceptance evidence, failure / edge paths, non-goals, unknowns가 포함된다. 이 구조는 "MVP-1용 AS", "MVP-2용 AS"처럼 MVP마다 별도 시나리오를 만드는 방식을 피하고, 먼저 전체 사용자 성공 흐름을 세운 뒤 그 흐름의 step들을 MVP coverage로 나누는 방향을 강제한다.

`AS step map`은 Integrated AS를 MVP split과 Bridge Packet으로 연결하는 중간 표다. 각 AS step이 무엇을 의미하는지, 사용자가 무엇을 보거나 확인하는지, 어떤 source anchor에서 왔는지, 어떤 notes가 필요한지를 유지한다. validator도 `AS Step`, `Description`, `Evidence / Observable Result`, `Source anchor`, `Notes`가 비어 있거나 의미 없는 placeholder일 때 실패시키도록 되어 있다.

MVP split에서 말하는 MVP는 `Minimum Viable Product`가 아니라 `Minimum Reviewable Value Slice`다. 즉 "제품으로 쓸 수 있는 최소 기능"이 아니라 "사용자-visible 진전이 있고, 경계가 검토 가능하며, 다음 MVP와 섞이지 않는 최소 가치 조각"이다. MVP row는 stable ID, local label, 덮는 AS step, user-visible outcome, boundary, deferred/excluded, unknowns, status를 가진다.

`stable MVP identity`는 downstream drift를 막기 위한 핵심 장치다. `MVP-1` 같은 bare label은 local display label일 뿐이고, downstream scope나 Dryforge Bridge Packet의 선택 후보로 쓰면 안 된다. 현재 규칙은 `Plan Review ID: PR-YYYYMMDD-HHMMSS`, `Stable MVP ID: <Plan Review ID>:MVP-<n>` 형식이다. deterministic timestamp가 없으면 `PR-<short-slug>-<sequence>`를 쓸 수 있지만, downstream-facing MVP scope는 반드시 plan review ID로 namespace를 가져야 한다.

`Dryforge Bridge Packet`은 선택된 MVP를 downstream dryforge-native `oneshot`으로 넘기기 위한 bridge다. 여기에는 `Selected MVP Candidate`, `Source-to-AS Trace`, `Scope Guard for Downstream Dryforge`, `Behavior Contract Seeds`, `Risk Signals for Downstream Planning`, `Sparse Oracle Hints`가 들어간다. 이 packet은 `.dryforge/spec.md`, `.dryforge/plan.md`, `.dryforge/handoff.md` 자체가 아니라, downstream이 그 문서들을 만들 때 확장하지 말아야 할 경계와 보존해야 할 evidence를 전달하는 입력 묶음이다.

이 스킬이 의도적으로 하지 않는 일도 중요하다. `oracle-plan-review`는 구현 task 목록, 파일별 구현 계획, DTO/interface/test shape, RED/GREEN/TDD 절차, dryforge Execution Graph, `.dryforge/spec.md`/`plan.md`/`handoff.md`, G1/G2/G3/G4 레거시 게이트, Oracle 실행 프롬프트를 만들지 않는다. 탐색 힌트나 evidence type hint는 가능하지만, 특정 파일을 수정하라거나 특정 verification command를 확정하는 것은 over-specification으로 본다.

## 2. 아키텍처

### 핵심 워크플로우

현재 `SKILL.md`의 워크플로우는 다음 순서다.

1. `Intake`에서 goal, user-visible outcome, constraints, dislikes, attachments, requested output form, non-goals, unknowns를 수집한다.
2. `Plan Review Identity`를 먼저 부여한다.
3. 전체 요구사항을 하나 이상의 `Integrated Acceptance Scenario`로 만든다.
4. 각 scenario를 reviewable `AS step`으로 분해한다.
5. AS step을 `Minimum Reviewable Value Slice` 기준으로 MVP에 배치한다.
6. 각 MVP에 대해 `MVP-by-MVP AS Notes`를 쓴다.
7. 선택 MVP를 downstream으로 넘길 `Dryforge Bridge Packet`을 만든다.
8. `Minimal Self-Check`로 문서가 pass 상태인지 확인한다.
9. `.oracle/plan-review.md`를 `python scripts/validate_plan_review.py .oracle/plan-review.md`로 검사한다.

이 흐름에서 가장 중요한 순서는 "AS 먼저, MVP 나중"이다. MVP는 source intent를 쪼개는 출발점이 아니라, Integrated AS의 step coverage를 나누는 결과물이다. 이 순서가 무너지면 MVP가 구현 편의나 파일 구조 기준으로 잘릴 수 있고, 그러면 downstream dryforge가 사용자-visible 성공 기준 대신 내부 작업 경계로 drift할 가능성이 커진다.

### 주요 문서 계약

현재 validator와 fixture가 실제로 강하게 확인하는 산출물 구조는 `# AS/MVP Decomposition` 아래의 다음 섹션들이다.

- `## 0. Plan Review Identity`
- `## 1. Reconstructed Intent`
- `## 2. Integrated Acceptance Scenario`
- `## 3. AS Step Map`
- `## 4. MVP Split`
- `## 5. MVP-by-MVP AS Notes`
- `## 6. Recommended First MVP`
- `## 7. Dryforge Bridge Packet`
- `## 8. Minimal Self-Check`

validator의 required section 목록에는 `0`, `2`, `3`, `4`, `5`, `7`, `8`이 들어간다. `6. Recommended First MVP`는 존재 자체를 required로 강제하지는 않지만, 있으면 `Selected MVP Candidate`와 stable MVP ID가 일치하는지 검사한다. 따라서 문서 계약상으로는 `SKILL.md`의 Required Output 전체를 따르는 것이 맞고, validator는 그중 구조적으로 중요한 부분을 자동 검증하는 안전망에 가깝다.

`Dryforge Bridge Packet`의 scope guard는 downstream 연결에서 특히 중요하다. `In scope`, `Out of scope`, `Deferred`, `Explicit exclusions`, `Unknown / needs authority`를 분리해서, 다음 단계 스킬이 선택 MVP를 전체 프로젝트 구현으로 확장하지 못하게 한다. 이 항목은 "이번 실행의 범위"뿐 아니라 "이번 실행이 아니라고 명시된 것"까지 downstream 계약으로 넘긴다.

### validator / fixture / agent 설정 구조

`validate_plan_review.py`는 `.oracle/plan-review.md`의 구조와 over-specification을 검사하는 validator다. 주요 검증 범위는 다음과 같다.

- `Plan Review ID`와 stable ID scheme 존재 여부
- `Integrated Acceptance Scenario` 안의 `AS-<n>.<m>` step 존재 여부
- `AS Step Map`이 모든 AS step을 매핑하는지
- `MVP Split`이 모든 AS step을 MVP, deferred, excluded, unknown / needs authority 중 하나로 처리하는지
- `Stable MVP ID`가 `PR-...:MVP-<n>` 형식을 따르고 Plan Review ID prefix와 일치하는지
- `MVP-by-MVP AS Notes`가 MVP split과 같은 step coverage를 유지하는지
- `Recommended First MVP`와 `Dryforge Bridge Packet / Selected MVP Candidate`가 같은 stable MVP를 가리키는지
- `Source-to-AS Trace`가 selected AS step을 빠뜨리지 않는지
- `Behavior Contract Seeds`가 unknown AS anchor를 참조하지 않는지
- `Minimal Self-Check`가 모두 `yes`인지
- Task heading, Execution Graph, DTO, test shape, verification command, RED->GREEN, 파일 수정 지시, class/function 정의 지시 같은 구현 선결정 표현이 새는지

fixture는 이 validator의 의도를 보여준다. `tests/fixtures/valid/minimal_plan_review.md`는 통과해야 하는 최소 구조를 제공하고, invalid fixture들은 missing Integrated AS, missing AS step map, unmapped AS step, missing bridge scope guard, missing MVP split, missing MVP notes, self-check `no`, selected/recommended MVP mismatch, header-only trace, empty scope guard, file-level instruction, implementation-over-spec 등을 실패 케이스로 둔다. 제공된 테스트는 39개 케이스를 포함하며, valid fixture와 주요 invalid 변형을 통해 validator의 계약을 고정한다.

`agents/openai.yaml`은 인터페이스 표시명과 기본 prompt를 제공하지만, 현재 `SKILL.md` 및 validator와 완전히 같은 표면을 갖지는 않는다. agent prompt는 `AS/MVP Prompt Bundle`, `Boundary Check Prompt`, `Verify Prompt`, `MVP-level Oracle Review Prompt`를 말하지만, 현재 validator와 valid fixture의 중심은 `.oracle/plan-review.md`의 `AS/MVP Decomposition` 및 `Dryforge Bridge Packet`이다. 따라서 실제 source of truth를 잡을 때는 `SKILL.md`와 validator/fixture를 우선하고, agent prompt는 현재 운영 표면과 일부 불일치가 남아 있는 보조 설정으로 보는 편이 안전하다.

## 3. 저장소와 운영 방식

중심 파일은 `SKILL.md`, `scripts/validate_plan_review.py`, `tests/fixtures/valid/minimal_plan_review.md`, `tests/test_validate_plan_review.py`다. `SKILL.md`는 의도와 출력 계약을 설명하고, validator script는 문서가 최소 계약을 지키는지 검사한다. valid fixture는 실제 pass 가능한 최소 문서의 예시이며, invalid fixtures와 tests는 어떤 누락과 drift를 실패로 볼지 명문화한다.

`SKILL.md`는 사람이 읽는 계약이다. 여기에는 이 스킬이 무엇을 만들고 무엇을 만들지 않는지, `Integrated Acceptance Scenario`, `AS step map`, `Minimum Reviewable Value Slice`, `stable MVP identity`, `Dryforge Bridge Packet`, `Minimal Self-Check`의 의미가 정리되어 있다. 특히 "이 스킬은 구현 스킬이 아니다"라는 boundary가 반복해서 나온다.

`references` 디렉터리는 역사적 맥락과 과거 설계를 담지만, 현재 모두 같은 무게로 취급하면 안 된다. `mvp-slice-boundary-patch.md`, `oracle-prompt-templates.md`, `oracle-review.md`, `sot-review-surface.md`, `workflow-contract.md`에는 명시적인 `DEPRECATED` 배너가 있다. 이들은 과거의 Task-shaped implementation-plan workflow, one Task per Oracle turn, Task-by-Task Oracle review, Execution Contract, Flow-to-Task-to-Test Matrix 같은 모델을 설명하며, 현재 `oracle-plan-review` 스킬의 직접 source of truth가 아니라고 적혀 있다.

`packet-schema.md`는 명시적 DEPRECATED 배너는 없지만, 내용상 "one numbered Task for Oracle", `task_id`, files/modules, functions/classes/interfaces, implementation steps, layered test commands 등을 다룬다. 이는 현재 `SKILL.md`가 금지하는 Task-shaped 구현 계획과 충돌한다. 그러므로 이 파일은 현재 validator가 보장하는 `.oracle/plan-review.md` 계약으로 그대로 가져오면 안 되고, 최소한 legacy packet schema 또는 재정렬이 필요한 보조 문서로 분리해서 봐야 한다.

이 프로젝트는 단순 브레인스토밍이 아니다. 산출물은 downstream `oneshot`으로 넘어가기 전의 handoff protocol이며, validator는 그 protocol이 최소한의 구조를 갖췄는지 검사한다. 특히 `Dryforge Bridge Packet`은 "다음 단계가 알아서 잘 해석하겠지"라는 느슨한 전달이 아니라, 선택 MVP의 stable identity, AS coverage, observable evidence, in/out/deferred/excluded/unknown 경계를 함께 넘기는 계약이다.

운영 방식도 이 점을 반영한다. `.oracle/plan-review.md`를 처음 작성한 직후, AS 구조나 MVP split이나 Bridge Packet이나 Minimal Self-Check를 수정한 직후, downstream `oneshot`에 전달하기 전에 validator를 실행한다. 일반 출력은 `python scripts/validate_plan_review.py .oracle/plan-review.md`, machine-readable 출력은 `python scripts/validate_plan_review.py .oracle/plan-review.md --json`이다.

단, validator의 한계도 문서화되어 있다. 이 검사는 user intent 해석이 맞는지, MVP split이 최선의 product decision인지, downstream dryforge execution이 성공할지, source fidelity와 product judgment가 충분한지를 증명하지 않는다. validator는 구조적 누락과 과도한 구현 선결정을 줄이는 장치이지, 최종 판단자나 Oracle review의 대체물이 아니다.

## 4. 프로젝트 99에 가져올 인사이트

### 4.1 큰 요구사항을 먼저 실행이 아닌 reviewable slice로 구조화한다

프로젝트 99에서 가져올 첫 번째 원칙은 "큰 요구사항을 받았을 때 바로 구현 계획을 만들지 않는다"는 점이다. `oracle-plan-review`는 large requirement를 먼저 `Integrated Acceptance Scenario`와 `AS step map`으로 바꾸고, 그 다음에 `Minimum Reviewable Value Slice`로 나눈다. 이 구조는 LLM이 큰 요구사항을 받자마자 파일 목록, 함수 설계, task graph로 뛰어드는 문제를 줄인다.

프로젝트 99의 코드베이스 관리 문맥에서는 이것을 "실행 전 reviewable slice 만들기" 원칙으로 해석할 수 있다. 즉, 복잡한 기능 요청이 들어오면 먼저 사용자가 확인할 수 있는 성공 흐름과 evidence를 정의하고, 그 흐름 중 이번 턴에서 닫을 수 있는 최소 조각을 선택한다. 실행은 그 이후의 별도 계약으로 넘긴다.

### 4.2 구현 계획보다 acceptance scenario와 observable evidence를 우선한다

이 프로젝트의 강점은 acceptance를 문서 맨 앞쪽으로 끌어올린다는 점이다. `Integrated Acceptance Scenario`는 entry point, trigger, ordered flow, expected result, observable acceptance evidence를 포함한다. `AS step map`은 각 step마다 evidence와 source anchor를 요구한다. 이는 내부 구현이 아니라 사용자가 관찰할 수 있는 결과를 기준으로 계획을 고정하는 방식이다.

프로젝트 99에서는 이 원칙을 "코드베이스 이해와 실행 계약의 공통 기준은 observable evidence"라고 정리할 수 있다. 내부 구조를 아무리 잘 설계해도, 사용자-visible 결과나 검토 가능한 evidence가 없으면 slice가 닫힌 것이 아니다. 이 관점은 `Understand Anything`류의 지식 그래프 사례와도 연결된다. 지식 그래프가 코드베이스의 구조적 이해를 돕는다면, `oracle-plan-review`는 그 이해를 실행 전 acceptance evidence로 바꾸는 중간 관문을 제공한다.

### 4.3 stable MVP identity와 scope guard로 downstream drift를 막는다

`stable MVP identity`는 작은 장치처럼 보이지만 downstream drift 방지에 중요하다. bare `MVP-1`은 매 plan-review run마다 다시 등장할 수 있으므로, downstream 실행 단위로 쓰면 충돌 가능성이 있다. 이 프로젝트는 `Plan Review ID`를 먼저 만들고, `PR-...:MVP-1`처럼 namespace가 붙은 stable ID를 downstream scope로 사용하게 한다.

프로젝트 99에서 이 원칙은 "실행 단위에는 로컬 이름이 아니라 stable identity를 부여한다"로 가져올 수 있다. `scope guard`는 그 stable identity가 가리키는 범위를 다시 좁힌다. `In scope`, `Out of scope`, `Deferred`, `Explicit exclusions`, `Unknown / needs authority`를 나누면, 다음 스킬이나 다음 세션이 "선택 MVP"를 전체 기능 구현으로 확장하는 것을 막을 수 있다.

### 4.4 Dryforge Bridge Packet으로 다음 단계 스킬과 계약을 연결한다

`Dryforge Bridge Packet`은 이 프로젝트의 가장 직접적인 handoff 장치다. 이 packet은 downstream `oneshot`이 `.dryforge/spec.md`, `.dryforge/plan.md`, `.dryforge/handoff.md`를 만들 때 참고할 selected MVP의 입력 묶음이다. 중요한 점은 Bridge Packet이 plan 자체가 아니라 bridge라는 것이다. 즉, task id, work target, dependency graph, verification command, test-first 여부, 파일별 구현 지시를 포함하지 않는다.

프로젝트 99에서는 이것을 "스킬 간 연결은 출력 문서 전체가 아니라 다음 스킬이 필요한 최소 계약 묶음으로 한다"는 원칙으로 가져올 수 있다. 앞 단계가 너무 많은 구현 결정을 넘기면 downstream은 유연성을 잃고, 너무 적게 넘기면 drift한다. Bridge Packet은 그 중간 지점에서 source-to-AS trace, scope guard, behavior seed, risk signal, Sparse Oracle hint를 제공한다.

### 4.5 validator로 과도한 명세화와 누락을 동시에 막는다

이 validator의 특징은 단순히 필수 섹션이 있는지만 보지 않는다는 점이다. AS step이 실제로 map에 들어갔는지, MVP split이 모든 AS step을 덮는지, MVP notes와 split의 coverage가 일치하는지, selected MVP와 recommended MVP가 일치하는지, Source-to-AS Trace가 selected step을 커버하는지까지 확인한다. 동시에 Task heading, file-level instruction, class/function 정의, literal verification command, Execution Graph, DTO, RED->GREEN 같은 over-specification도 잡는다.

프로젝트 99에서는 validator를 "누락 방지"뿐 아니라 "과잉 실행화 방지" 도구로 보는 것이 중요하다. 많은 문서 validator는 비어 있는 항목을 채우게만 하지만, 이 프로젝트의 validator는 아직 정하면 안 되는 것을 정하지 못하게 한다. 이 접근은 LLM 기반 코드베이스 관리에서 특히 유용하다. LLM은 빈칸을 싫어하고 구체화를 과하게 하는 경향이 있으므로, validator가 일부 구체화를 실패 조건으로 만들어야 한다.

### 4.6 self-check는 완료 선언이 아니라 pass 조건이다

`Minimal Self-Check`는 형식적 체크리스트가 아니다. validator는 required self-check 항목이 빠지거나, 값이 `yes/no`가 아니거나, 하나라도 `no`이면 실패시킨다. "One integrated AS exists", "Every AS step is mapped", "Source observable evidence is preserved", "Bridge Packet contains no implementation tasks, file plans, DTOs, test shapes, or graph" 같은 항목은 문서가 downstream으로 넘어갈 수 있는지 판단하는 최소 조건이다.

프로젝트 99에서는 self-check를 "모델의 자신감 표현"이 아니라 "다음 단계로 넘겨도 되는 계약 상태"로 다뤄야 한다. 특히 self-check가 `no`인 문서를 pass처럼 제시하지 않는 규칙은, 실행 계약과 guarded execution을 다루는 문서들과 잘 연결된다.

## 5. 프로젝트 99에 적용할 때의 해석

이 구조를 그대로 복제하면 안 되는 이유가 있다. `oracle-plan-review`는 특정 목적, 즉 큰 요구사항을 dryforge-native `oneshot` 이전의 AS/MVP decomposition으로 바꾸는 데 맞춰져 있다. 프로젝트 99의 모든 문서나 모든 LLM workflow가 `Integrated Acceptance Scenario`, `MVP Split`, `Dryforge Bridge Packet`을 그대로 가져야 하는 것은 아니다. 작은 수정 요청, 단순 코드 읽기, 이미 scope가 명확한 bugfix에는 이 구조가 과할 수 있다.

또한 현재 저장소 내부에는 source of truth의 층위가 완전히 깨끗하게 정리되어 있지는 않다. `SKILL.md`와 validator/fixture는 `.oracle/plan-review.md` 중심의 현재 구조를 잘 보여주지만, 일부 deprecated references는 `AS/MVP Prompt Bundle`, `Active MVP Prompt Bundle`, old Task review surface를 언급한다. `agents/openai.yaml`도 현재 validator가 요구하지 않는 prompt bundle 섹션을 기본 prompt에서 말한다. 따라서 프로젝트 99에서는 이 저장소를 "완성된 범용 표준"이 아니라 "handoff protocol을 validator로 고정하려는 사례"로 읽는 것이 안전하다.

프로젝트 99의 본문 문서와 연결할 때는 다음처럼 해석할 수 있다.

- `00`에는 큰 요구사항을 바로 실행하지 않고 사용자-visible 성공 흐름으로 재구성하는 원칙을 연결한다.
- `01`에는 코드베이스 이해나 지식 그래프가 만들어낸 구조적 이해를 `AS step map`과 evidence anchor로 변환하는 관점을 연결한다.
- `02`에는 `stable MVP identity`, `scope guard`, `Dryforge Bridge Packet`을 실행 계약 이전의 handoff contract로 연결한다.
- `03`에는 validator와 fixture를 통해 누락, scope drift, over-specification을 자동으로 차단하는 운영 원칙을 연결한다.

외부 레퍼런스로서의 가치는 "LLM에게 더 자세히 생각하라"가 아니라 "어떤 문서 구조와 validator가 LLM의 drift를 줄이는가"를 보여준다는 데 있다. 특히 이 프로젝트는 acceptance-first, slice-first, stable identity, scope guard, bridge packet, validator를 하나의 체인으로 묶는다. 반면 한계는 validator가 의미적 품질을 증명하지 못하고, references 일부가 deprecated 상태이며, agent 설정과 현재 문서 계약 사이에 불일치가 남아 있다는 점이다.

## 6. 배치 원칙

- 지금 위치: `아카이브/LLM 바이브 코딩 코드베이스 관리/외부 레퍼런스/`
- 문서 역할: `oracle-plan-review`를 외부 레퍼런스로 분석해, 프로젝트 99에 가져올 수 있는 acceptance-first planning, reviewable slice, stable MVP identity, Dryforge Bridge Packet, validator 기반 guard 원칙을 정리하는 노트
- 연결할 문서:
  - `Understand Anything - 코드베이스 지식 그래프 사례.md`
  - `oneshot - 실행 계약과 Guarded Execution Pack 스킬 사례.md`
  - 프로젝트 99의 본문 문서 `00`
  - 프로젝트 99의 본문 문서 `01`
  - 프로젝트 99의 본문 문서 `02`
  - 프로젝트 99의 본문 문서 `03`

이 노트는 `Understand Anything` 사례와 `oneshot` 사례 사이에 놓기 좋다. `Understand Anything`이 코드베이스 이해를 구조화하는 사례라면, `oracle-plan-review`는 요구사항을 실행 전 reviewable AS/MVP 계약으로 바꾸는 사례다. `oneshot`이 실제 실행 계약과 guarded execution에 가까운 사례라면, `oracle-plan-review`는 그 전에 선택 MVP의 scope와 evidence를 고정하는 upstream handoff protocol이다.

## 7. 최종 판단

- `oracle-plan-review`의 현재 핵심은 구현 계획 생성이 아니라, large requirement를 `Integrated Acceptance Scenario`, `AS step map`, `Minimum Reviewable Value Slice`, `Dryforge Bridge Packet`으로 바꾸는 요구사항 구조화 계약이다.
- 프로젝트 99에 가장 가치 있는 부분은 acceptance-first 사고, stable MVP identity, scope guard, downstream bridge packet, validator 기반 over-spec 방지다.
- deprecated references는 과거 Task-shaped Oracle review 모델을 보여주는 역사적 자료로만 다뤄야 하며, 현재 source of truth는 `SKILL.md`와 validator/fixture 조합으로 보는 것이 안전하다.
- validator는 구조적 누락과 과도한 구현 선결정을 잘 잡지만, user intent 해석의 정확성이나 MVP split의 제품적 최선 여부까지 보장하지는 않는다.
- 이 사례는 프로젝트 99에서 "실행 전에 먼저 reviewable handoff contract를 만든다"는 원칙을 설명하는 외부 레퍼런스로 적합하다.
