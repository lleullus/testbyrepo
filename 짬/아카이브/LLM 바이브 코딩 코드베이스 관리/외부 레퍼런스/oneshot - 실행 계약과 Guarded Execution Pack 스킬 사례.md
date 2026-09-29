---
title: "oneshot - 실행 계약과 Guarded Execution Pack 스킬 사례"
status: draft
date: 2026-06-17
source: "/home/user01/.config/opencode/skills/oneshot"
---

## Oracle 분석 요약

`oneshot`은 사용자의 짧고 애매한 요청을 "다른 실행자가 바로 수행할 수 있는 계약"으로 컴파일하는 OpenCode skill 프로젝트다. 기본 산출물은 두 갈래다. 하나는 v1 `prompt-only` 방식으로, `.dryforge`와 `.oracle` 흐름을 전제로 하는 강화된 구현 프롬프트를 만든다. 다른 하나는 v2 `guarded repo` 방식으로, repo-local `.oneshot` 산출물, 정책, evidence, closure, validator, optional hook template를 포함하는 Guarded Execution Pack을 만든다.

이 프로젝트의 핵심은 프롬프트 문장을 잘 쓰는 데 있지 않다. 사용자의 요청을 `spec`, `task`, `test`, `review`, `closure`, `evidence`, `validator`가 서로 검증 가능한 구조로 바꾸고, `PASS_SCOPED` 같은 완료 주장을 validator와 Oracle gate가 허락하기 전까지 차단하는 프로토콜이다. 특히 Oracle Browser는 최종 구현 프롬프트를 생성하는 transport로 쓰이고, O1/O2는 생성 대상이 아니라 lifecycle approval gate로 분리된다.

## 1. 프로젝트가 실제로 하는 일

이 프로젝트는 사용자 요청을 단순한 "실행 지시문"이 아니라 실행 가능한 산출물 계약으로 바꾼다. 입력은 짧고 불완전한 요청일 수 있지만, 출력은 실행자가 따라야 할 lifecycle, source authority, validation command, evidence requirement, stop condition, non-claim을 포함해야 한다. 구현 지향 요청은 최종적으로 `.oracle`, `.dryforge`, 그리고 v2에서는 `.oneshot` 기반의 구조화된 산출물로 연결된다.

v1 `prompt-only`는 repo-local guard pack을 만들지 않는다. 대신 `D0 -> D1 -> D2 -> Trace Matrix -> O1 -> D3 -> D4 -> O2 -> Final Scoped Verdict` 흐름을 포함한 구현 프롬프트를 생성하고, `validate-prompt`, `validate-graph`, `validate-artifacts` 같은 validator로 prompt와 dryforge artifact 계약을 검사한다. v1에서도 O1/O2는 필수 lifecycle gate이며, low-risk라는 이유로 생략하는 흐름은 명시적으로 차단된다.

v2 `guarded repo`는 prompt-only 위에 `.oneshot` 구조를 추가한다. 이 모드에서는 `state.json`, `policy.yaml`, `spec.md`, `architecture.md`, `tasks/<task_id>.md`, `tests.md`, `review.md`, `closure.md`, `events.jsonl`, `logs/`, `approvals/`가 중심 artifact가 된다. `validate-guard-schema`, `derive-context`, `activate-rules`, `validate-closure-v2`, `validate-evidence`, `validate-approvals`, `validate-guard-v2`가 단계별로 실행되며, executor prose나 self-approval은 evidence로 인정되지 않는다.

Oracle Browser는 최종 구현 프롬프트를 ChatGPT가 직접 쓰지 않고 외부 Oracle Browser가 생성하게 할 때 쓰인다. 이때 ChatGPT의 역할은 final implementation prompt 작성이 아니라 source packet, generation prompt, invocation command, output path, validation path를 구성하는 것이다. prompt generation은 `run_oracle_prompt_generation.py` wrapper를 통해 수행되며, 실패 시 sanitized regeneration loop가 작동한다. wrapper는 prompt, source packet, stdout/stderr log, validation result, hash, final status를 남기고, clean generation이 아닌 manual repair를 clean pass로 취급하지 않는다.

최종 실행/검증 흐름은 "생성 -> 구조화 -> evidence 수집 -> closure -> mechanical validation -> semantic approval -> scoped verdict" 순서다. guarded repo에서는 `validate-guard-v2`가 final mechanical eligibility를 결정하지만, 그것만으로 최종 완료가 되지는 않는다. 최종 `PASS_SCOPED`는 같은 현재 상태에 대해 `validate-guard-v2`가 통과하고, 최신 O2/O2-R이 semantic approval을 제공할 때만 가능하다.

## 2. 아키텍처

### 핵심 운영 모드

운영 모드는 두 축으로 나뉜다.

첫 번째 축은 transport다. `direct`는 ChatGPT가 최종 prompt를 직접 작성하는 방식이고, `oracle_browser`는 ChatGPT가 Oracle Browser generation artifact만 만들고 최종 prompt는 Oracle Browser가 생성하게 하는 방식이다.

두 번째 축은 target이다. `normal_prompt`는 v1 prompt-only dryforge/O1/O2 구현 프롬프트를 목표로 한다. `guarded_repo_prompt`는 v1 lifecycle 위에 `.oneshot`, `validate-guard-v2`, `PASS_SCOPED` evidence gate를 추가한 guarded repo 실행 프롬프트를 목표로 한다.

Stable MVP ID가 감지되면 scope-managed run으로 전환된다. 이때 canonical artifact는 `.oracle/scopes/<plan_review_id>/<mvp_id>/...` 아래에 저장되고, `.oracle`, `.dryforge`, `.oneshot`, `compiled-oneshot-prompt.md` 같은 기본 경로는 current projection으로만 취급된다. scope activation 전 current projection에 canonical artifact를 직접 쓰는 것은 차단된다.

### 주요 문서 계약

`SKILL.md`는 control plane이다. 사용자의 요청을 prompt-only, guarded repo, Oracle Browser generation 중 어디로 보낼지 결정하고, 어떤 reference를 읽어야 하는지 지정한다.

`references/prompt-only-mode.md`는 v1 dryforge-native lifecycle과 O1/O2 contract를 정의한다. 여기에는 required v1 prompt contract, Oracle hardening, O1/O2 recheck, lifecycle unlock, canonical evidence, attachment manifest, final verdict 규칙이 포함된다.

`references/guarded-repo-mode.md`는 v2 Guarded Execution Pack의 의미를 정의한다. 여기서 중요한 전환은 "긴 프롬프트가 executor에게 잘하라고 말하는 구조"에서 "state, policy, validator, evidence, closure가 완료 주장을 허용하거나 차단하는 구조"로 바뀌는 점이다.

`references/strict-data-model.md`, `spec-trace-closure.md`, `evidence-and-command-registry.md`, `validator-contract.md`는 artifact의 신뢰 모델을 정의한다. Markdown prose는 보조 설명이고, 주요 validator는 canonical YAML block과 structured record를 신뢰한다. requirement closure, guard rule closure, quality floor closure는 서로 대체할 수 없다.

`references/scoped-workspace.md`는 MVP 범위가 있는 작업에서 canonical archive와 current projection을 분리한다. 이는 여러 MVP 또는 여러 scope의 artifact가 `.oracle`, `.dryforge`, `.oneshot` 경로에서 섞이는 문제를 막기 위한 장치다.

### 주요 런타임 / validator / wrapper 구조

validator는 `oneshot_validator.cli`를 중심으로 노출된다. v1에는 `validate-prompt`, `validate-graph`, `validate-artifacts`가 있고, v2에는 `validate-guard-schema`, `derive-context`, `activate-rules`, `validate-closure-v2`, `validate-evidence`, `validate-approvals`, `validate-guard-v2`, `validate-proposal` 등이 추가된다.

`guard_schema.py`는 `.oneshot` artifact의 필수 구조, allowed/forbidden disposition, command registry, core rule set을 검사한다. `guard_runtime.py`는 changed paths, touched surfaces, risk, task kind, G0 decision, diff hash를 executor claim이 아니라 validator context에서 도출한다. `guard_closure.py`는 requirement, guard rule, quality floor closure가 모두 evidence와 함께 닫혔는지 검사한다. `guard_evidence.py`는 command evidence, event lineage, review, tests, architecture, search evidence, SSOT registry 등 rule-specific evidence source를 검사한다. `guard_final.py`는 이들을 묶어 `validate-guard-v2` mechanical eligibility를 판단한다.

Oracle 관련 wrapper는 prompt generation, O1 contract review, O2 closure review를 직접 `oracle-plus` 호출로 방치하지 않는다. `run_oracle_prompt_generation.py`는 Oracle Browser prompt generation을 provenance와 hash가 남는 반복 시도로 관리한다. `run_oracle_contract_review.py`는 O1/O1-R을 manifest-bound attachment와 recovery loop로 실행한다. `run_oracle_closure_review.py`는 O2 closure review를 attachment manifest와 lifecycle unlock에 묶는다.

## 3. 저장소와 운영 방식

중심 파일은 `SKILL.md`, `references/`, `scripts/`, `src/oneshot_validator/`, `tests/unit/`, `pyproject.toml`이다. `SKILL.md`는 routing과 hard rules를 담고, `references/`는 사람이 읽는 운영 계약을 담는다. `src/oneshot_validator/`는 그 계약 중 기계적으로 검사 가능한 부분을 구현한다. `scripts/`는 validator나 Oracle wrapper를 사람이 매번 손으로 조립하지 않도록 묶는 실행 entrypoint다. `tests/unit/`은 validator가 막아야 할 실패 모드와 허용해야 할 정상 구조를 사례로 고정한다.

문서와 코드는 역할이 분리되어 있다. 문서는 lifecycle, policy, evidence, closure, scope의 의미를 설명한다. validator는 그 설명 중 반드시 지켜야 할 구조를 fail-closed 방식으로 검사한다. wrapper는 Oracle Browser나 O1/O2 실행이 수동 호출, 직접 수정, hash 불일치, attachment 누락으로 흐르지 않도록 provenance를 남긴다. tests는 이 구조가 "좋은 의도"가 아니라 실제 rejection rule로 남아 있는지 확인한다.

첨부본 기준으로 중요한 한계도 확인된다. 코드와 테스트는 `assets/` template 및 `tests/fixtures/` fixture를 참조하지만, 현재 첨부된 파일 세트에는 해당 디렉터리가 포함되어 있지 않다. 따라서 전체 pytest 실행은 `assets/state.json.template`, `tests/fixtures/...` 누락으로 통과하지 않는다. 이는 이 프로젝트의 개념적 구조가 불명확하다는 뜻은 아니지만, 첨부본만으로 generator/template/sample-pack 동작을 완전 재현할 수는 없다는 뜻이다.

이 프로젝트는 단순 프롬프트 모음이 아니다. prompt-only reference가 있더라도 핵심은 prompt 문장 자체가 아니라 prompt가 생성해야 하는 산출물 계약이다. v2에서는 이 성격이 더 분명해진다. `.oneshot` pack은 실행자가 주장한 완료를 그대로 믿지 않고, `policy.yaml`의 rule catalog, runtime-derived active rule, command registry, structured evidence, closure matrix, lifecycle gate를 통해 완료 가능성을 제한한다. 즉, 이 저장소는 "프롬프트 라이브러리"라기보다 "LLM 실행 프로토콜 + 검증기"에 가깝다.

## 4. 프로젝트 99에 가져올 인사이트

### 짧고 애매한 요청을 실행 계약으로 컴파일한다

`oneshot`의 가장 큰 인사이트는 사용자 요청을 곧바로 구현 지시로 보내지 않는다는 점이다. 요청은 먼저 transport, target, lifecycle, artifact, evidence, stop condition으로 분해된다. 사용자가 "해줘"라고 말해도 시스템은 "무엇을 만들고, 어떤 자료를 authority로 삼고, 어떤 검증을 통과해야 하며, 어떤 경우 중단해야 하는가"를 먼저 컴파일한다.

프로젝트 99에 적용하면, 바이브 코딩 요청을 바로 코드 생성으로 넘기기보다 "요청 -> scope -> source authority -> expected artifact -> validation evidence -> closure"로 변환하는 중간 계층이 필요하다. 이 중간 계층은 긴 프롬프트보다 중요하다. LLM이 잘 수행하기를 기대하는 대신, 수행 결과가 어느 계약을 만족해야 하는지를 먼저 고정하기 때문이다.

### 프롬프트보다 산출물 계약을 우선한다

v1에서도 prompt는 자유 문장이 아니라 required contract block, lifecycle token, artifact path, authority order, Oracle gate status, failure class probe를 포함해야 한다. v2에서는 더 나아가 `.oneshot` artifact가 중심이 된다. `spec.md`는 behavior source of truth이고, `tasks/<task_id>.md`는 요구사항과 구현 범위를 task 단위로 묶고, `tests.md`와 `review.md`는 behavior evidence와 review evidence의 위치를 정한다. `closure.md`는 최종 주장이 아니라 evidence와 validator 결과로 닫혀야 하는 상태 파일이다.

프로젝트 99에서 가져올 원칙은 "좋은 프롬프트 템플릿"보다 "좋은 산출물 스키마"가 우선이라는 점이다. LLM에게 설명을 잘 시키는 것보다, LLM이 남겨야 하는 artifact의 이름, 필드, 관계, evidence binding, closure 조건을 먼저 설계해야 한다.

### Oracle을 생성기이자 승인 게이트로 쓰되 역할을 분리한다

이 프로젝트에서 Oracle Browser는 두 역할로 등장하지만, 둘은 섞이지 않는다. 하나는 prompt generation transport다. 이 경우 Oracle Browser는 최종 구현 프롬프트를 생성하고, wrapper는 생성물의 validation, hash, stdout/stderr, regeneration status를 기록한다. 다른 하나는 O1/O2 lifecycle gate다. O1은 구현 전 contract readiness를 검토하고, O2는 evidence closure와 scoped verdict를 semantic하게 검토한다.

프로젝트 99에 중요한 점은 Oracle을 "더 똑똑한 생성기"로만 보지 않는 것이다. Oracle은 생성자이면서 동시에 승인 게이트가 될 수 있지만, 생성한 주체가 자기 산출물을 자기 승인하는 구조는 위험하다. 따라서 prompt generation, O1 contract review, O2 closure review는 별도의 artifact, 별도의 status, 별도의 evidence provenance를 가져야 한다.

### scoped workspace는 MVP 범위를 물리적으로 고정한다

`scoped workspace`는 여러 MVP나 plan review가 같은 `.oracle`, `.dryforge`, `.oneshot` 경로를 공유하면서 artifact가 섞이는 문제를 다룬다. Stable MVP ID가 있으면 canonical artifact는 `.oracle/scopes/<plan_review_id>/<mvp_id>/...`에 저장되고, current projection은 activation된 scope의 작업 공간으로만 쓰인다. projection이 dirty하면 activation을 막고, force는 예외적 overwrite로만 허용된다.

프로젝트 99에서 이 원칙은 매우 중요하다. 코드베이스 관리 문서가 여러 실험, 여러 MVP, 여러 LLM run을 다루게 되면 "현재 보이는 파일"과 "정식 기록"이 쉽게 혼동된다. scoped workspace는 이 혼동을 구조적으로 막는다. MVP 범위는 말로만 "이번엔 여기까지만"이라고 적는 것이 아니라, 저장 위치와 activation/sync 절차로 고정되어야 한다.

### 테스트와 validator로 LLM 산출물을 기계적으로 막는다

`oneshot`은 executor가 "테스트했다", "검토했다", "완료했다"고 말하는 것을 evidence로 보지 않는다. command evidence는 `command_registry`의 `covers` allowlist와 대조되고, produced rule instance가 registry 밖을 주장하면 실패한다. event lineage도 executor-authored record만으로는 ordering-sensitive rule을 닫을 수 없다. review evidence도 hidden coupling, fan-in/fan-out, internal mock boundary 같은 runtime-affecting rule에 대해서는 independent semantic review evidence가 필요하다.

프로젝트 99가 가져와야 할 핵심은 LLM의 산출물을 "나중에 사람이 읽고 판단"하는 수준을 넘어, 기계적으로 reject 가능한 형식으로 만드는 것이다. 특히 evidence freshness, diff hash, changed paths, command exit code, stdout/stderr ref, approval provenance, duplicate closure entry, stale trace matrix 같은 항목은 LLM의 설명력과 무관하게 통과/실패가 결정되어야 한다.

### requirement closure와 guard rule closure를 분리한다

이 프로젝트는 behavior requirement와 engineering discipline rule을 같은 closure로 뭉개지 않는다. requirement closure는 사용자가 요구한 동작이 충족되었는지를 닫고, guard rule closure는 구현 과정에서 지켜야 하는 품질, 검증, 리뷰 규칙이 지켜졌는지를 닫는다. Quality Floor도 별도 closure 축으로 둔다.

프로젝트 99에서는 이 분리가 "코드가 동작한다"와 "코드베이스 관리 원칙을 지켰다"를 구분하는 데 유용하다. 테스트가 통과해도 중복 helper, caller-level defensive patch, 내부 mock 남용, parallel dead path가 있으면 프로젝트 관리 관점에서는 완료가 아니다.

### non-claim을 명시해 과장을 막는다

Oracle Browser generation wrapper는 clean generation이 통과해도 "generated prompt validation PASS"와 "generation provenance verified" 정도만 claim할 수 있게 한다. 동시에 `implementation PASS_SCOPED`, `O1 semantic approval`, `O2 semantic approval`, `validate-guard-v2 runtime PASS`는 not_claimed로 남긴다.

이 패턴은 프로젝트 99에 그대로 가져올 가치가 있다. LLM run 결과는 "무엇을 확인했는가"뿐 아니라 "무엇을 아직 주장하지 않는가"를 함께 남겨야 한다. 특히 외부 레퍼런스, 코드베이스 분석, 리팩터링 제안, 테스트 보강 결과는 완료 claim과 non-claim을 분리해야 과장을 줄일 수 있다.

### 실패 후 재시도는 scope 확장이 아니라 remedy routing이다

O2/O2-R의 `remedy_type`은 CODE_CHANGE, TEST_CHANGE, EVIDENCE_REGEN, CLOSURE_REGEN, PACKET_REBUILD, SCOPE_CLARIFICATION, NON_CLAIM_RECORD, TOOLING_REPAIR로 분리된다. evidence packet 결함이 발견되었다고 해서 product code를 고치는 것은 아니다. closure 결함은 closure를 고쳐야 하고, tooling transport 결함은 tooling을 고쳐야 한다.

프로젝트 99에서 LLM workflow를 설계할 때도 같은 원칙이 필요하다. 실패가 발생하면 "다시 구현"으로 바로 가는 것이 아니라, 실패가 코드 문제인지, 테스트 문제인지, evidence 문제인지, scope 문제인지, 도구 문제인지 먼저 분류해야 한다. 그래야 LLM이 검증 실패를 빌미로 불필요하게 product scope를 확장하지 않는다.

## 5. 프로젝트 99에 적용할 때의 해석

이 프로젝트를 그대로 복제하면 안 된다. `oneshot`은 매우 강한 실행 통제 모델이다. 모든 프로젝트 99 문서나 모든 바이브 코딩 작업에 `.oneshot`, Oracle Browser, O1/O2, full closure matrix를 요구하면 운영 비용이 과해질 수 있다. 특히 개인 지식 관리나 외부 레퍼런스 정리 수준의 작업에는 full guarded repo protocol이 과하다.

프로젝트 99에 가져올 것은 구조의 원리다. "요청을 산출물 계약으로 바꾸기", "scope를 저장소 구조로 고정하기", "LLM claim을 evidence와 분리하기", "semantic approval과 mechanical validation을 분리하기", "PASS보다 non-claim을 먼저 기록하기"가 핵심이다. 반대로 특정 경로, 특정 validator 명령, 특정 Oracle wrapper, 특정 O1/O2 taxonomy를 그대로 복제하는 것은 프로젝트 99의 문서 운영 맥락에 맞지 않을 수 있다.

`00. 홈` 문서와는 전체 철학 차원에서 연결된다. 프로젝트 99가 LLM 바이브 코딩 코드베이스 관리를 다룬다면, `oneshot`은 "프롬프트를 잘 쓰는 법"이 아니라 "LLM 실행을 관리 가능한 protocol로 바꾸는 법"의 사례다. `00`에는 이 외부 레퍼런스를 "코드베이스 관리의 실행 계약화 사례"로 연결하는 것이 적합하다.

`01. 컨텍스트 맵과 도메인 안전 경계` 문서와는 artifact/data model 차원에서 연결된다. `spec`, `task`, `test`, `review`, `closure`, `evidence`를 분리하는 방식은 프로젝트 99의 본문 문서가 코드베이스 지식, 변경 계획, 검증 기록을 나누어 관리하는 데 참고할 수 있다. 특히 Markdown prose와 canonical block을 분리하는 방식은 Obsidian 문서에도 응용 가능하다.

`02. 작업 프로토콜` 문서와는 workflow 차원에서 연결된다. D0/D1/D2/O1/D3/D4/O2/final 같은 lifecycle은 그대로 복제할 필요는 없지만, "구현 전 승인 gate"와 "구현 후 closure gate"를 분리하는 구조는 프로젝트 99의 실행 흐름 설계에 유용하다. 구현 전에 scope와 plan을 잠그고, 구현 후 evidence와 closure를 검토하는 2-gate 구조만 가져와도 효과가 있다.

`03. LLM 친화적 코드베이스 기준` 문서와는 governance/quality gate 차원에서 연결된다. Quality Floor, command registry, evidence provenance, scoped workspace, dirty projection stop은 LLM 산출물의 품질 관리 원칙으로 옮길 수 있다. 특히 "테스트 통과만으로 완료가 아니다"라는 관점은 코드베이스 관리 문서에서 중요하게 다룰 만하다.

외부 레퍼런스로서의 가치는 높다. 이 프로젝트는 LLM 실행을 문서, 스크립트, validator, wrapper, test로 함께 묶어 관리하려는 구체적 사례다. 다만 첨부본 기준으로 `assets/`와 `tests/fixtures/`가 빠져 있어 generator와 sample fixture 기반 테스트를 완전히 재현할 수 없고, validator 자체도 cryptographic producer authenticity, signed command transcript, O2 session isolation까지 증명하지는 않는다. 따라서 프로젝트 99에서는 "완성된 정답"이 아니라 "강한 계약 기반 운영 모델의 참고 사례"로 배치해야 한다.

## 6. 배치 원칙

지금 위치는 적절하다. `아카이브/LLM 바이브 코딩 코드베이스 관리/외부 레퍼런스/`에 두는 것이 맞다. 이 문서는 프로젝트 99의 본문 규칙이 아니라, 외부 구현 사례를 분석해 프로젝트 99로 가져올 원칙과 한계를 추출하는 reference note 역할을 해야 한다.

연결할 문서는 `00`, `01`, `02`, `03`이다. `00`에는 "LLM 실행을 프롬프트가 아니라 protocol로 관리한다"는 큰 방향으로 연결한다. `01`에는 artifact/data model, canonical block, trace/closure 구조로 연결한다. `02`에는 lifecycle gate, Oracle review, retry/remedy routing으로 연결한다. `03`에는 validator, evidence, Quality Floor, scoped workspace, non-claim 원칙으로 연결한다.

문서 역할은 `Understand Anything - 코드베이스 지식 그래프 사례.md`와 비슷하게 잡는 것이 좋다. 즉, 외부 프로젝트를 홍보하거나 단순 요약하는 문서가 아니라, 프로젝트 99의 설계 어휘를 넓히는 사례 분석 노트다. 핵심 질문은 "이 프로젝트가 무엇을 했는가"가 아니라 "프로젝트 99가 여기서 어떤 관리 원칙을 가져오고, 무엇은 가져오지 말아야 하는가"다.

## 7. 최종 판단

- `oneshot`은 프롬프트 모음이 아니라, LLM 구현 작업을 실행 계약, evidence, validator, Oracle gate, closure로 관리하려는 protocol + validator 프로젝트다.
- 프로젝트 99에 가장 중요한 인사이트는 `prompt-only`와 `guarded repo`의 차이다. 전자는 강한 prompt contract이고, 후자는 repo-local artifact와 validator가 완료 주장을 기계적으로 제한하는 구조다.
- Oracle Browser는 최종 prompt 생성 transport로도 쓰이지만, O1/O2 approval gate와 섞이면 안 된다. 생성, 검증, semantic approval은 별도 artifact와 별도 status를 가져야 한다.
- scoped workspace는 MVP 범위를 말이 아니라 저장 구조와 activation/sync 절차로 고정하는 방식이며, 프로젝트 99의 multi-run/multi-scope 관리에 직접적인 참고 가치가 있다.
- 그대로 복제하기보다는 "요청을 산출물 계약으로 컴파일한다", "claim보다 evidence를 우선한다", "closure와 non-claim을 분리한다", "validator로 LLM 산출물을 막는다"는 원칙을 프로젝트 99 문서 체계에 맞게 얇게 적용하는 것이 적합하다.
