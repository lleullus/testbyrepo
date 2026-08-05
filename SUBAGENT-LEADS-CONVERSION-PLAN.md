# Implementation / Verification Lead 전환 계획

상태: `CONVERSION-SKELETON`

이 문서는 현재 Python `implementation-verification/` Module/OpenCode JSON
assignment 구조에 의존하는 두 Lead를 호스트 중립적인 서브에이전트 호출 구조로
전환하기 위한 실행 골격이다. 구현 자체의 변경 목록이 아니라, 전환 착수 전에
권한·보존·삭제·검증 순서를 고정하는 문서다.

## 목표와 보존할 가치

전환 후 정상 흐름은 다음과 같다.

```text
Matt ready Ticket
  -> Implementation Lead
  -> 지정된 Implementation Subagent가 실제 프로젝트를 구현
  -> Lead가 diff, 구현 단계, Ticket Markdown AC별 구현/검사 coverage 확인
  -> 현재 프로젝트의 구현 결과와 실제 변경을 독립 검증 대상으로 남김 (최종 VERIFIED 아님)
  -> Verification Lead
  -> 동일 exact Ticket과 현재 프로젝트에서 검증 시작
  -> 지정된 Fresh Verification Subagent가 fresh 관점에서 검증
  -> 각 Ticket Markdown AC를 직접 증거로 독립 판정
```

여기서 `Implementation Subagent`와 `Fresh Verification Subagent`는 각각
사용자가 각각 지정한 구현 역할과 fresh 검증 역할이다. 각 Lead는 사용자가
지정한 해당 역할을 호출하지만, 호출 횟수·재개·실패 복구·background/foreground
여부·중간 통신은 Lead 계약으로 고정하지 않는다.

구체적인 호출·통신 방식은 전적으로 `Host Subagent Invocation Mechanism`과
호스트 전역 지침이 소유한다. 이 문서는 특정 `Task`, `functions.task`,
`message`, background 방식, 또는 특정 호스트의 JSON assignment 형식을
계약에 결합하지 않는다. Lead는 호스트가 제공한 결과를 아래의 산출물 의미와
검증 gate에만 대조한다.

전환으로 보존해야 할 핵심 가치는 다음 네 가지다.

- 실제 프로젝트에 대한 정확한 구현
- 구현 전후 사용자 변경과 작업 대상의 보존
- 구현 Lead와 분리된 fresh 검증
- Ticket, AC, 구현 결과, 직접 증거 사이의 추적 가능성

기존 Module의 capability, claim, authorization, audit, replay 의식을
호스트 중립 용어로 이름만 바꿔 재도입하지 않는다.

## 역할 경계

### Implementation Lead

입력은 하나의 정확한 Matt ready Ticket과 사용자가 지정한
`Implementation Subagent` 역할이다. Lead는 서브에이전트가 실제 프로젝트
작업을 수행하도록 한다. Implementation Subagent는 현재 프로젝트를 직접
수정하되, 기존 사용자 변경이나 동시 변경을 reset/revert/overwrite하지
않는다. Lead는 실제 변경과 작업 결과를 다음 기준으로 검사한다.

- 실제 프로젝트 diff가 Ticket의 범위와 일치하는가
- 구현 단계와 결과가 실제 변경에 의해 확인되는가
- Ticket Markdown에 적힌 각 AC가 어떤 구현과 검사에 대응하는가
- 아직 독립 검증되지 않은 사실을 `VERIFIED`로 승격하지 않는가

Lead의 결과는 현재 프로젝트의 구현 결과와 실제 변경에 대한 구현 검토 및
AC coverage 확인이다. 이는 독립 검증을 시작할 수 있다는 뜻이지 최종
`VERIFIED` 판정이 아니다.

### Verification Lead

입력은 동일 exact Ticket과 현재 프로젝트의 구현 결과 및 실제 변경이다. 새
구조에는 Candidate 전달물이 없다. Lead는 이전 구현 설명이나 이전 결론을
독립 증거로 취급하지 않고, 제품 파일을 수정하지 않는 read-only 역할인
fresh context의 `Fresh Verification Subagent`가 실제 프로젝트와 허용된
검증 표면을 관찰하게 한다. 구현 Lead와 Implementation Subagent의 서술과
결론은 Fresh Verification Subagent에 direct evidence로 전달하지 않는다.

검증 기준은 별도 AC schema나 hash가 아니라 Ticket Markdown의 AC 자체다.
Verification Lead는 Ticket의 모든 AC에 대해 최종 AC 결과 행을 정확히 하나씩
만들고, 각 행을 다음 중 하나로 판정하며 직접 증거를 붙인다. 여기서
`정확히 하나씩`은 서브에이전트 호출 횟수가 아니라 최종 AC 결과 행의
cardinality를 뜻한다.

| 판정 | 의미 |
| --- | --- |
| `SATISFIED` | 필요한 관찰이 완료되었고 AC가 요구하는 결과를 직접 증거가 보임 |
| `NOT_SATISFIED` | 완전한 직접 증거가 AC의 요구 결과와 모순됨 |
| `UNDETERMINED` | 증거 누락·관찰 실패·권한/환경/현재성 불명 등으로 결론을 낼 수 없음 |

구현 Lead의 diff/검사 coverage는 검증리드가 검증할 범위와 누락을 찾는
입력이지, Verification Lead의 직접 증거를 대체하지 않는다. 모든 AC가
독립 증거로 판정되지 않으면 최종 성공으로 집계하지 않는다.

## AC 기준과 산출물 경계

- 권위 있는 AC 목록은 해당 Ticket Markdown의 AC다.
- AC를 복제한 별도 schema, hash, state machine을 만들지 않는다.
- Implementation Lead는 각 AC에 대응하는 구현과 구현 단계 검사를 확인한다.
- Verification Lead는 각 AC별 상태와 직접 증거를 기록·판정한다.
- Lead 산출물은 일반적인 Ticket/구현 diff/검사 결과/검증 증거로 충분해야
  하며, 별도 handoff 파일을 새로 만들지 않는다.
- Candidate를 별도 serialization 규격으로 만들거나, 상태 전이를 관리하는
  새 저장 모델을 도입하지 않는다.
- 구현·검증 결과를 호스트의 호출 반환값과 Ticket/프로젝트 증거에서
  해석할 수 있어야 하며, caller가 내부 workflow를 조립하지 않는다.

## 전환 대상의 disposition

### 현재 dirty diff: 선행 gate

전환 착수 시점의 worktree에는 다음 20개 파일에 dirty diff가 있다.

- `README.md`
- `implementation-lead/SKILL.md` 및 해당 contract test
- `verification-lead/SKILL.md`
- `implementation-verification/`의 durable backend, execution,
  production adapter/entrypoint/smoke 및 관련 tests

이 변경은 앞서 잘못 해석한 OpenCode agent 고정 해제/routing 변경이다. 현재
문서 작업에서는 어떤 파일도 revert하거나 수정하지 않는다. 다만 전환 구현은
이 diff를 기준으로 진행하지 않으며, 착수 전 다음 disposition gate를
통과해야 한다.

1. 각 변경을 기존 의도와 실제 source/runtime 근거에 대조한다.
2. 전환 요구에 독립적으로 필요한 변경인지, 잘못 해석한 routing 변경인지
   구분한다.
3. 근거가 있는 부분만 `SALVAGE`하고 나머지는 `DISCARD`한다.
4. disposition이 끝나기 전에는 dirty diff를 전환의 권위 있는 baseline,
   보존 증거, 또는 검증 통과 근거로 사용하지 않는다.

이 문서의 작성은 위 disposition을 대신하지 않으며, disposition 과정에서
기존 변경을 자동으로 되돌리지 않는다.

### `implementation-verification/` 후보

Python `implementation-verification/` 전체를 남길지, 일부 보조 검사만
남길지는 전환 단계의 실제 consumer census와 gate 대조 뒤 결정한다.

보존 후보는 다음 세 조건을 모두 만족해야 한다.

- 새 Implementation Lead 또는 Verification Lead가 실제로 소비한다.
- 호스트 중립 흐름의 직접 완료 gate에 꼭 필요하다.
- 상태·호출·assignment·handoff 프로토콜을 재도입하지 않고 독립적인
  source/diff/직접 관찰 검사로 남길 수 있다.

이 조건을 입증하지 못하는 Python Module, durable 저장소, production
adapter, orchestration, protocol-coupled test는 삭제 후보로 분류한다.
보조 검사를 남길 경우에도 Ticket Markdown AC와 실제 프로젝트 증거를
검사하는 최소 표면만 보존하고, 기존 Module을 유지하기 위한 새
`begin`/`complete` 상태 API는 만들지 않는다.

다음 항목은 새로 만들지 않는다.

- 별도 SQLite 저장소
- Candidate serialization 포맷
- transition state machine
- assignment envelope
- actor/capability/claim 모델
- 별도 handoff 파일
- 위 항목을 대신하는 호스트 종속 상태·통신 계층

## 실행 순서

각 단계의 결과는 다음 단계의 gate를 만족할 때만 사용한다. 기존 dirty
변경은 이 순서를 우회하지 않는다.

### 1. Baseline과 disposition 고정

- 현재 두 Lead, Matt ready Ticket 형식, 실제 호출 소비자, 검증 표면을
  read-only로 census한다.
- 위 dirty diff 20개 파일을 파일별로 `DISCARD` 또는 `SALVAGE` 후보로
  분류하고 근거를 남긴다.
- disposition 결과를 확정한 뒤에만 깨끗한 전환 baseline을 정한다.

**Gate:** dirty diff의 최종 disposition이 있고, 잘못 해석한 OpenCode
routing 변경이 전환 근거로 암묵적으로 채택되지 않는다.

### 2. 두 Lead의 호스트 중립 계약으로 축소

- Implementation Lead의 입력, 실제 구현, diff/단계/AC coverage 검사를
  문서화한다.
- Verification Lead의 fresh 검증, 전체 Ticket AC 판정, 직접 증거 요구를
  문서화한다.
- 호출·통신·재개 정책은 `Host Subagent Invocation Mechanism`의 입력과
  반환 의미만 참조하고 Lead 문서에 복제하지 않는다.
- 정상 흐름에서 구현 역할과 fresh 검증 역할이 각각 하나의 지정된
  서브에이전트 역할로 연결되는지 확인하되, 호출 횟수나 복구 호출을
  계약으로 고정하지 않는다.

**Gate:** 두 Lead가 특정 Task/API/JSON assignment/background/message
구현 없이 동일한 역할·입출력 의미를 설명하고, Verification Lead의
판정이 Implementation Lead 결과를 재사용하지 않는다.

### 3. 실제 consumer와 보조 검사 판별

- `implementation-verification/`의 각 모듈·adapter·test가 현재 새 Lead
  흐름에서 직접 소비되는지 확인한다.
- 직접 consumer가 없는 durable/state/protocol surface는 삭제 후보로
  표시한다.
- 보존 후보는 Ticket AC와 실제 diff/직접 관찰을 검사하는지 확인하고,
  단순히 기존 Module의 상태·assignment·handoff를 유지하는 이유만으로
  남기지 않는다.

**Gate:** 각 보존 파일에는 실제 consumer와 직접 완료 gate가 있고, 각
삭제 후보에는 대체되는 Ticket/diff/evidence 검증 근거가 있다. 근거 없는
후보는 보존하지 않는다.

### 4. 최소 경로 구현

- disposition된 baseline에서 두 Lead의 호스트 중립 경계를 구현한다.
- Implementation Subagent가 실제 프로젝트를 변경하고, Lead가 diff와
  단계별 검사 및 AC coverage를 확인하는 경로를 연결한다.
- Verification Lead가 Fresh Verification Subagent의 독립 관찰을 통해
  Ticket의 모든 AC를 세 상태와 직접 증거로 판정하는 경로를 연결한다.
- 새 SQLite, Candidate serialization, state machine, envelope, actor/
  capability/claim, handoff 파일 또는 begin/complete API를 추가하지 않는다.

**Gate:** 대표 ready Ticket이 실제 프로젝트 구현까지 도달하고, 구현
검토 결과가 final `VERIFIED`가 아닌 상태로 Verification Lead에 전달된다.

### 5. 구 Module과 보조 코드 정리

- 3단계 census와 4단계 경로를 기준으로 삭제 후보를 제거한다.
- 보존한 보조 검사는 새 Lead가 직접 호출하고, Ticket Markdown AC 또는
  실제 diff/직접 증거의 완료 gate를 검사해야 한다.
- old Module을 새 Lead의 facade로 남기거나 compatibility/dual-run/fallback
  경로로 보존하지 않는다.

**Gate:** repository와 설치된 Lead 표면에서 삭제 후보의 import/call이
  남지 않고, 보존 코드가 호스트 호출 프로토콜이나 숨은 상태 저장을
  재도입하지 않는다.

### 6. 독립 검증과 legacy absence 확인

- Implementation Lead와 다른 fresh 관점에서 동일 Ticket의 모든 AC를
  직접 관찰한다.
- 각 AC의 `SATISFIED`/`NOT_SATISFIED`/`UNDETERMINED`와 직접 증거가
  Ticket AC에 일대일로 대응하는지 확인한다.
- 구현 Lead의 diff/검사 coverage만으로 `SATISFIED`를 만들지 않는다.
- 삭제한 Module·protocol·state surface가 다시 호출되지 않고, 의도하지
  않은 fallback이 없음을 확인한다.

**Gate:** 모든 AC가 독립 증거로 판정되고, 검증 결과가 구현 Lead의
  서술·검사 결과·이전 verdict를 증거로 carry-forward하지 않는다.

### 7. 전환 완료 판정

다음 evidence를 함께 확인할 때만 전환 완료로 판정한다.

- disposition된 dirty diff와 최종 전환 baseline
- 실제 ready Ticket에서의 구현 diff와 Lead coverage 확인
- 같은 Ticket에 대한 fresh 검증의 AC별 세 상태와 직접 증거
- 보존/삭제 파일의 consumer 및 완료 gate 판정
- old Module, assignment/state/handoff surface와 fallback 부재 확인
- 호출/통신 상세가 Lead 계약이 아니라 `Host Subagent Invocation
  Mechanism`과 호스트 전역 지침에 남아 있다는 확인

하나라도 빠지면 전환을 완료로 보고하지 않고 해당 gate에서 중단한다.

## 검증 기준

전환 구현 후 검증은 기존 Python Module의 통과 여부가 아니라 실제 Lead
경로를 우선한다.

1. Matt ready Ticket을 입력으로 사용한다.
2. 사용자가 지정한 Implementation Subagent 역할이 실제 프로젝트를
   변경하는지 확인한다.
3. 구현 Lead가 실제 diff, 구현 단계, Ticket AC별 coverage를 확인하는지
   확인한다.
4. Verification Lead가 이전 구현 context와 분리된 Fresh Verification
   Subagent 역할로 모든 AC를 다시 관찰하는지 확인한다.
5. 각 AC의 세 상태와 직접 증거를 authoritative Ticket과 대조한다.
6. 보존된 보조 검사와 삭제된 legacy surface가 위 flow를 우회하지 않는지
   확인한다.

호스트가 재개·실패 복구를 위해 내부적으로 추가 호출을 하더라도, 이는 이
문서의 Lead 계약이나 AC 의미를 바꾸지 않는다. 반대로 호스트 호출이
성공했다는 사실만으로 실제 프로젝트 구현, 직접 증거, AC 판정을 대신할 수
없다.

## 열린 결정과 중단 조건

다음은 전환 구현 전에 실제 판단이 필요한 항목이다.

- 현재 dirty diff 각 변경의 `DISCARD`/`SALVAGE` disposition. 기본 방향은
  잘못 해석한 OpenCode routing 변경을 전환 기반으로 채택하지 않는 것이다.
- census에서 기존 외부 consumer 또는 보존해야 할 실제 기록이 발견될 때의
  처리 범위. 근거 없는 compatibility facade나 자동 변환은 선택하지 않는다.
- 보존 후보가 새 Lead의 직접 완료 gate인지 증명되지 않을 때 해당 후보를
  삭제할지 여부. 증명되지 않은 코드는 기본적으로 삭제 후보로 둔다.

다음 사실이 발생하면 해당 단계에서 중단한다.

- dirty diff disposition 없이 전환 baseline을 정해야 하는 경우
- 실제 consumer가 남아 있는데 legacy Module을 제거해야 하는 경우
- Ticket Markdown AC와 직접 연결되지 않은 별도 AC 모델을 만들게 되는 경우
- Implementation Lead의 coverage나 서술을 독립 검증의 직접 증거로
  대체해야 하는 경우
- 호출·통신 세부를 Lead 계약에 넣거나 특정 호스트 API에 결합해야 하는
  경우
- 삭제를 위해 새 SQLite, serialization, state machine, envelope,
  actor/capability/claim, handoff 파일 또는 begin/complete API가 필요하다고
  판단되는 경우

이 문서에 없는 호출 구현·통신 규칙·상태 보존 정책은
`Host Subagent Invocation Mechanism`과 호스트 전역 지침의 결정 사항이다.
