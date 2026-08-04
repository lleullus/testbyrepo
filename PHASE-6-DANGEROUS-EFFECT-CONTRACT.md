# Phase 6 — 위험한 외부효과

상태: `DESIGN_CONVERGED`

## 목적과 단일 결정

Phase 4의 effectful implementation check와 Phase 5의 effect observation이 실제 product 또는 외부
system을 바꿀 수 있을 때, 실제 authority 없는 실행, response loss 뒤 중복 effect, action 응답을
readback으로 가장하는 경로를 막는 최소 내부 Seam을 정한다.

이번 단계의 단일 결정은 다음이다.

> Module은 외부 상태를 바꿀 수 있는 observation을 한 개의 fixed effect observation으로 분류하고,
> 현재 authority가 exact action·target·final disposition을 실제로 허용할 때만 Effect Observation
> Adapter에 맡긴다. Adapter는 action 전에 durable `may-have-run`을 남기고, ambiguous action을 호출
> 재시도만으로 반복하지 않으며, pre-fixed authoritative readback과 필요한 cleanup까지 하나의
> runner-owned evidence bundle로 닫는다.

caller Interface는 Phase 2의 `implement(work, worker)`, `verify(candidate)`, `inspect(work)` 그대로다.
caller가 authorization ref, replay scope, action/readback/cleanup step, correlation token 또는 outcome을
조립하지 않는다.

## 상속한 사용자 가치와 경계

- exact Candidate, planning/전체 AC와 direct evidence 결속을 유지한다.
- 검증은 source를 수정하지 않고, 구현 check는 final verification evidence가 아니다.
- 사용자나 product authority가 허용하지 않은 외부효과를 검증 편의를 위해 실행하지 않는다.
- response loss, timeout 또는 process death가 같은 effect의 자동 재실행 권한이 되지 않는다.
- persistent effect는 action stdout이나 성공 response만으로 완료됐다고 하지 않고 authoritative target
  readback으로 확인한다.
- cleanup이 필요한 effect는 action 시작 전에 cleanup의 target·authority·관찰 방법까지 정해져야 한다.
- evidence나 authority가 부족하면 verification은 `UNDETERMINED`, implementation check는 Candidate를
  만들지 않는 `ImplementationStopped`다. 이것을 AC 불충족으로 바꾸지 않는다.
- Phase 3의 한 active transition과 Phase 5의 unresolved observation lifetime을 그대로 사용한다.

이 Phase는 사용자가 새 public approval protocol을 배우게 하지 않는다. 반대로 exact effect authority가
없는데 ready Ticket 또는 `verify(candidate)` 호출 자체를 묵시적 동의로 간주하지도 않는다.

## 위험한 effect의 최소 분류

다음 중 하나라도 가능한 observation/check는 Phase 6-owned effect다.

- fresh isolated local environment 밖의 persistent state 생성·수정·삭제
- message, payment, job, deployment, queue, account 또는 다른 externally visible operation 발생
- tenant·production·shared environment의 상태나 가용성 변경
- credential, personal/user data 또는 protected target을 사용하면서 외부 consequence도 만드는 operation
- cleanup 없이는 product target이나 외부 resource가 남는 operation
- 실행 여부가 불명확할 때 같은 request 반복이 duplicate consequence를 만들 수 있는 operation

read-only라고 주장해도 request 자체가 notification, job 또는 그 밖의 externally visible consequence를
일으키거나 재호출이 duplicate consequence를 만들 수 있으면 effect로 취급한다. 평범한 authenticated
read와 routine request accounting/rate-limit은 그 사실만으로 dangerous effect가 아니다. 그것들은
opaque credential, current read authority, privacy/redaction과 bounded execution을 만족하는 fixed
read-only Runner/Adapter observation이다. 분류를 안정적으로 할 수 없으면 safe read로 낮추지 않고
effect로 취급하거나 실행하지 않는다.

Candidate에서 만든 disposable local sandbox 안에서만 상태가 생기고, sandbox 밖 write/network/credential
사용이 runtime에서 차단되며 폐기 자체가 외부 product operation이 아닌 경우는 Phase 5 isolated local
execution이다. 단순히 command 이름이 `read`, `test`, `dry-run`이라는 이유로 safe라고 분류하지 않는다.

분류는 caller나 fresh Verifier의 자기 선언이 아니라 Module과 선택된 Adapter가 현재 authority 및 실제
target surface를 읽어 결정한다. 구체 taxonomy, risk score와 generic policy DSL은 만들지 않는다.

## 깊은 Module과 실제 Seam

Implementation Verification Module 안에 **Effect Observation Module**을 둔다. Verification Execution
Module과 Implementation Execution Module은 위험한 effect를 직접 실행하지 않고 이 Module의 내부
Interface만 사용한다.

```text
observe(fixed effect observation, current authority context)
  -> complete EffectEvidenceBundle
  -> unsupported/unsafe/undetermined fact
```

이 이름과 shape는 설명용이며 public 함수나 serialized schema가 아니다. Module은 다음을 한곳에 숨긴다.

- effect classification과 exact target resolution
- authority applicability와 currentness 확인
- action/readback/cleanup request binding
- durable may-have-run ordering과 live execution ownership
- response loss, timeout과 ambiguous prior effect safety
- provider-enforced idempotency 또는 operation correlation이 실제 지원되는 경우의 사용
- authoritative readback, bounded polling, cleanup과 final disposition 확인
- credential 전달과 evidence redaction
- complete effect evidence bundle 생성

실제 Seam에는 effect kind별 **고정 Effect Adapter**가 앉는다. production Adapter는 concrete product
surface를 실행하고 deterministic test Adapter는 같은 authority, may-have-run, readback과 cleanup 의미를
재현한다. 임의 command/plugin이 자신을 안전하다고 선언하는 generic executor registry, repository
discovery 또는 workflow DSL은 허용하지 않는다. 지원되지 않은 effect는 실행하지 않는다.

## fixed effect observation

Phase 5의 immutable observation plan은 첫 evidence 전에 effect observation 전체를 고정한다. 최소 의미는
다음과 같다.

```text
exact Candidate/planning/대상 AC 또는 exact implementation check binding
effect intent와 exact stable target
새 occurrence가 필요한 경우 pre-fixed action request
pre-fixed authoritative readback request와 expected observable
필요한 경우 pre-fixed cleanup request와 cleanup readback
의도한 final target disposition
Adapter가 제공한다고 주장하는 exact safety property
```

final disposition은 특정 enum을 caller에게 노출하지 않는다. plan은 최소한 다음 중 실제 의도를
구분할 수 있어야 한다.

- effect/resulting target을 남기고 그 상태를 확인해야 함
- temporary target을 제거하거나 원래 상태로 복원하고 그 final state를 확인해야 함
- persistent target은 없지만 authoritative terminal receipt가 필요함

action 뒤 새 target, cleanup 또는 alternate readback을 즉석에서 추가해 성공시키지 않는다. 필요한
final disposition을 action 전에 정할 수 없으면 effect를 시작하지 않는다. action/readback/cleanup은
서로 다른 pre-fixed request일 수 있으며 Phase 5의 started-subattempt completeness를 따른다.

fixed effect observation은 **action-bearing observation** 또는 **readback-only observation**일 수 있다.
같은 occurrence의 completed prior effect safety projection이 적용되면 fresh verification은 prior semantic
evidence를 읽지 않고 action을 억제한 채 새 authoritative readback-only observation을 계획할 수 있다.
새 action은 current authority가 별도 occurrence를 허용할 때만 action-bearing observation으로 고정한다.

## 실제 authority와 동의

Effect Observation Module은 action 전에 현재 적용되는 planning, repository/product operational authority와
target authority를 직접 읽는다. authority는 최소한 다음 의미에 exact하게 적용돼야 한다.

```text
무엇을 왜 실행하는가
어느 product/environment/tenant/target인가
허용된 consequence와 final disposition은 무엇인가
cleanup 또는 irreversible outcome까지 허용하는가
현재 Candidate/verification occurrence에 아직 적용되는가
```

ready Ticket, Worker/Verifier 판단, `verify(candidate)` 호출, Coordinator capability, generic role 또는
arbitrary scope digest 발급은 그 자체로 effect 동의가 아니다. 특히 production, tenant, money/message,
credential, user data, irreversible operation은 applicable authority가 exact scope를 명시하지 않으면
실행하지 않는다.

authority가 별도 operator confirmation을 요구하면 Module은 이미 존재하는 authoritative confirmation을
읽을 수 있을 때만 진행한다. Phase 6은 `verify`에 approval argument를 추가하거나 verification 도중
prompt로 동의를 추정하지 않는다. authority가 없거나 stale/ambiguous하면 action·cleanup을 시작하지 않고
verification에는 `UNDETERMINED`, implementation에는 `ImplementationStopped` reason을 돌려준다.

Module은 authority content를 fresh Verifier의 semantic namespace에 넘기지 않는다. Verifier는 현재
observation이 supported/unsafe/undetermined인지와 Runner가 만든 evidence만 읽는다.

effect를 허용하는 granting authority는 Candidate, private Worker workspace, fresh Verifier 또는 해당
effect가 변경할 수 있는 namespace 밖에서 고정·관리되는 authoritative source에서 와야 한다. Candidate
안의 source/config/manifest는 authority를 좁히거나 실행을 금지할 수 있지만 새 effect 권한을 부여하거나
소비된 occurrence를 다시 열 수 없다. Module은 적용한 authority fact에 provenance와 currentness를 함께
확인한다. 이 조건은 caller approval token, generic policy engine 또는 authority digest protocol을
요구하지 않는 Effect Adapter의 내부 gate다.

## 실행 전 gate와 durable ordering

effect action 전에 Module은 한 번의 fail-closed gate에서 다음을 확인한다.

1. exact Candidate/planning 또는 implementation-check source가 current하다.
2. fixed effect observation의 action, target, readback, cleanup과 final disposition이 Adapter에 의해
   concrete하게 지원된다.
3. applicable exact authority가 current하며 cleanup과 irreversible consequence까지 포함한다.
4. 같은 target/action과 충돌할 수 있는 unresolved prior effect가 없다. 있다면 먼저 아래 safety
   resolution만 수행한다.
5. 필요한 credential은 Adapter가 opaque하게 얻을 수 있고 Verifier, caller payload, argv와 evidence에
   secret을 노출하지 않는다.
6. action이 시작된 뒤 필요한 bounded readback/cleanup을 시도할 runtime ability가 있다.

하나라도 확인하지 못하면 action을 시작하지 않는다.

gate가 통과하면 Module은 외부 dispatch 전에 Phase 5 private progress에 exact Candidate/check,
action/target request binding과 `may-have-run`을 durable하게 남긴다. 이 fact가 durable하지 않으면 action을
호출하지 않는다. 한 effect observation에는 한 action execution owner만 존재하며 live owner가 있는 동안
result publication이나 competing execution이 이를 crash로 재분류하지 않는다.

## 비재실행과 prior ambiguous effect

`may-have-run` 뒤 complete action fact를 얻지 못한 것은 action 미발생 증명이 아니다. process death,
timeout, response loss, elapsed time, 새 invocation, 새 fresh Verifier 또는 source bytes 복귀는 같은
action을 반복할 authority가 아니다.

Phase 5의 unresolved observation item은 exact request와 stable target이 겹치는 이후 observation에도
Effect Observation Module의 safety input으로 적용된다. 같은 Candidate의 중간 `UNDETERMINED` result가
이를 지우지 않는다. 새 Candidate라도 같은 work에서 target/action consequence가 겹치면 새 planning이
자동으로 prior effect를 무효화하지 않으며, 현재 authority가 별도 occurrence를 명시적으로 허용하거나
아래 mechanical resolution이 끝나기 전에는 중복 가능한 action을 시작하지 않는다.

prior ambiguous effect는 다음 중 하나가 Adapter evidence로 확인될 때만 resolved된다.

- authoritative readback이 exact target에서 prior effect의 발생 상태와 final disposition을 확정함
- provider가 원 operation identity에 대해 server-enforced exact idempotency를 보장하고 Adapter가 새
  request가 그 exact operation과 target임을 입증함
- pre-fixed unique correlation이 action과 authoritative readback 양쪽에서 확인되어 그 effect instance를
  다른 occurrence와 구별함

문자열 equality, caller assertion, 동일 argv, process cardinality, timeout 뒤 성공 response, source
identity 또는 “대체로 idempotent”라는 문서는 mechanical safety가 아니다. 안전성을 입증하지 못하면
action을 실행하지 않고 unresolved item을 계속 보존한다.

exact idempotency/correlation이 실제 Adapter capability로 존재해도 caller가 replay scope digest,
authorization ref 또는 token substitution을 조립하지 않는다. Adapter가 fixed observation과 authority에
결속해 생성·보존·확인한다. capability가 없는 Adapter에는 해당 경로가 존재하지 않는다.

Implementation check에서 effect가 complete하게 끝나도 그 bundle의 **safety projection**은 Candidate
publication 뒤 사라지지 않는다. projection은 fixed Adapter, canonical target, action
consequence/occurrence, final disposition과 resolution fact만 포함하며 AC 의미·verdict·rationale 또는
implementation evidence payload를 포함하지 않는다. 같은 occurrence와 겹치는 verification action을
억제하고 fresh authoritative readback-only observation을 허용하는 데만 사용한다. representation과
lifetime storage는 숨긴 Implementation이며 새 caller-visible ledger가 아니다.

## authoritative readback과 causal evidence

외부 persistent effect의 action response, stdout, HTTP success status 또는 submitted receipt만으로
최종 product state를 확정하지 않는다. authoritative readback은 다음을 만족해야 한다.

- action 전에 fixed되고 action request와 다른 독립 request일 수 있다.
- action이 겨냥한 exact product/environment/tenant/target을 읽는다.
- effect instance를 구별해야 하면 Adapter-owned correlation/operation identity를 관찰한다.
- bounded identical polling만 수행하고 request·target·expected observable을 중간에 바꾸지 않는다.
- miss, timeout, error와 success를 포함해 시작된 모든 poll이 EffectEvidenceBundle에 순서대로 남는다.
- readback tool failure와 product absence/contradiction을 구별한다.

readback이 effect를 확인하면 ambiguous action response가 있어도 observed product fact를 evidence로 사용할
수 있다. readback이 authoritative하게 effect 부재와 지연 가능성 종료까지 확정하면 prior ambiguity를
resolved-absent로 닫을 수 있다. readback이 단지 찾지 못했거나 authority/target/currentness가 불명확하면
effect 부재로 단정하거나 action을 반복하지 않는다.

direct terminal receipt 자체가 product의 authoritative final observable인 fixed Adapter만 별도 target
readback 없이 complete할 수 있다. 이를 generic process exit나 caller-declared direct result로 넓히지
않는다.

## cleanup과 final disposition

cleanup은 action보다 덜 위험한 bookkeeping이 아니라 별도 외부효과다. action을 시작하려면 필요한
cleanup request, authority, target과 cleanup 뒤 authoritative observation을 미리 확보해야 한다.

- action이 `may-have-run`이면 pre-fixed cleanup은 contradiction, later drift 또는 positive-verdict 불가와
  무관하게 안전한 containment를 위해 시도할 수 있다.
- cleanup도 dispatch 전에 durable `may-have-run`을 남기고 ambiguous cleanup을 자동 반복하지 않는다.
- temporary target을 제거/복원해야 하는데 cleanup이 unsupported 또는 unauthorized라면 처음부터 action을
  시작하지 않는다.
- action 뒤 cleanup 실행이 불가능해졌거나 결과가 ambiguous하면 verification은 `UNDETERMINED`이고
  unresolved cleanup fact를 보존한다. implementation은 Candidate를 publish하지 않는다.
- retained target은 모든 cleanup 뒤 pre-fixed terminal readback으로 intended final state와 usable
  condition을 확인해야 한다.
- remove/restore disposition은 cleanup 뒤 target absence 또는 exact restored state를 authoritative하게
  확인해야 complete다.

cleanup 성공 response만으로 final disposition을 확정하지 않는다. cleanup 자체가 금지되거나 더 큰
위험을 만들면 임의로 실행하지 않고 unresolved state와 필요한 operator action을 reason으로 남긴다.

## EffectEvidenceBundle

Effect Observation Adapter는 Phase 5 Evidence Runner에 한 개의 immutable complete bundle을 반환한다.
최소 의미는 다음과 같다.

```text
exact Candidate/check, planning/AC와 fixed observation binding
실제로 적용된 current authority fact와 exact target
action/readback/cleanup 각각의 pre-fixed request binding
각 외부 dispatch 전 may-have-run durable fact
시작된 모든 subattempt의 순서, tool fact, artifact 또는 artifact 부재
authoritative readback과 operation/correlation 관찰
final target disposition observation
남은 unresolved action 또는 cleanup fact
Candidate/source currentness와 bounded redacted evidence integrity
```

Verifier는 이 bundle의 direct product observations를 AC에 해석하지만 authority를 만들거나 action
outcome을 작성하지 않는다. Module은 conclusive verdict 전에 authority, request/target binding,
started-subattempt completeness, readback과 final disposition을 다시 검사한다. 하나라도 부족하면
`SATISFIED`/`NOT_SATISFIED`를 `UNDETERMINED`로 낮춘다. effect tool failure나 cleanup failure 자체는 AC의
product contradiction이 아니다.

credential, raw user data, payment/message content와 불필요한 remote payload는 evidence에 넣지 않는다.
Adapter는 판정에 필요한 bounded projection만 보존한다. redaction 때문에 required observable을 판정할
수 없으면 보안 정보를 노출해 성공시키지 않고 `UNDETERMINED`다.

## contradiction, drift와 publication

- effect action 직전에 Candidate/planning/current authority를 다시 확인한다.
- complete contradiction이 생기면 아직 시작하지 않은 action은 실행하지 않는다.
- 이미 action이 `may-have-run`이면 필요한 authoritative readback과 pre-authorized cleanup은 계속할 수
  있지만 새 unrelated effect를 시작하지 않는다.
- action 전 drift는 effect 없이 해당 observation을 `UNDETERMINED`로 만든다.
- action 뒤 drift는 exact historical effect evidence와 unresolved safety fact를 버리지 않지만 current
  positive verdict를 허용하지 않는다.
- unresolved action/cleanup, missing final disposition 또는 live owner가 있으면 positive result를
  publish하지 않는다. live owner를 crash로 바꾸어 result를 닫지 않는다.
- live owner가 없고 Phase 5 unresolved item을 보존했으면 `UNDETERMINED` result publication은 허용된다.

Phase 3 atomic VerificationResult publication은 bundle과 unresolved safety binding을 result에 결속한다.
`inspect`는 public verdict와 exact Candidate를 복구하지만 caller에게 raw authority, credential,
idempotency token 또는 internal replay state를 요구하지 않는다.

## implementation check에서의 사용

Phase 4 implementation check가 위험한 effect를 필요로 하면 같은 Effect Observation Module을 사용한다.
exact final source/check와 fixed effect observation, authority, non-reexecution, readback, cleanup 규칙은
verification과 동일하다.

차이는 결과 의미뿐이다.

- complete effect evidence는 implementation closure의 보조 근거일 뿐 AC `SATISFIED` evidence가 아니다.
- authority/effect/readback/cleanup이 incomplete하면 Candidate를 publish하지 않고
  `ImplementationStopped`다.
- verification이 나중에 같은 effect를 요구하면 implementation check의 성공 evidence를 재사용하지
  않는다. 다만 duplicate consequence를 막기 위한 unresolved item과 completed effect safety projection은
  Module이 숨겨 적용하고, fresh verification은 필요한 authoritative readback을 새로 얻는다.

## 허용한 실패·복구 의미

- effect 분류가 불명확하면 safe local operation으로 실행하지 않는다.
- exact current authority가 없으면 action/cleanup을 실행하지 않는다.
- may-have-run을 durable하게 남기지 못하면 외부 dispatch를 시작하지 않는다.
- action response가 유실되면 action을 자동 반복하지 않고 authoritative readback만 시도한다.
- readback miss는 authoritative absence가 아니면 repeat authority가 아니다.
- required cleanup을 action 전에 확보하지 못하면 action을 시작하지 않는다.
- cleanup이 시작됐을 수 있으면 자동 반복하지 않고 unresolved fact를 보존한다.
- exact idempotency/correlation을 Adapter가 mechanically 입증하지 못하면 그 경로를 사용하지 않는다.
- tool/authority/currentness/privacy failure는 verification `UNDETERMINED` 또는
  `ImplementationStopped`이며 AC 불충족이 아니다.
- response loss 뒤 committed result는 `inspect`로 읽고, uncommitted live/unresolved effect는 새 action
  없이 re-enter한다.

## 근거가 있는 최소 시나리오

1. isolated local test는 외부 write/network가 차단돼 Phase 5 Runner에서 실행되고 Phase 6 비용이 없다.
2. production message 전송 AC인데 exact recipient/environment/occurrence authority가 없다. message를
   보내지 않고 `UNDETERMINED`다.
3. authorized effect action이 성공하고 fixed authoritative readback이 exact target state를 확인한다.
   complete bundle만 AC evidence가 된다.
4. action이 timeout됐지만 readback이 correlated effect를 확인한다. action을 반복하지 않고 observed
   state로 effect를 resolved-present 처리한다.
5. action response가 유실되고 readback도 판독 불능이다. unresolved item을 보존하고 다음
   `verify(candidate)`도 action을 반복하지 않는다.
6. 첫 `UNDETERMINED` 뒤 다시 `UNDETERMINED`가 publication돼도 unresolved effect는 authoritative
   resolution 전 사라지지 않는다.
7. remediation이 새 Candidate를 만들었지만 같은 external target/action consequence가 겹친다. 새
   Candidate라는 이유만으로 prior ambiguous effect를 지우거나 반복하지 않는다.
8. disposable resource가 필요한 observation은 action 전에 cleanup과 absence readback이 fixed되고
   authorized된 경우에만 시작한다.
9. action 뒤 contradiction 또는 source drift가 생긴다. 새 action은 중단하지만 already-started effect의
   readback과 safe cleanup을 마치고 positive verdict는 만들지 않는다.
10. cleanup timeout 뒤 success를 추정하지 않는다. unresolved cleanup을 보존하고 result는
    `UNDETERMINED`다.
11. provider가 exact idempotency를 지원하지 않는데 request bytes가 같다는 이유로 retry하지 않는다.
12. effect evidence에 필요한 user data를 안전하게 제한할 수 없다. raw payload를 노출하지 않고
    `UNDETERMINED`다.
13. implementation check에서 effect occurrence가 complete됐다. Candidate 뒤 fresh verification은
    implementation evidence를 재사용하지 않고 action을 억제한 readback-only observation으로 current
    target을 새로 관찰한다.
14. Worker가 Candidate 안의 operational manifest에 production effect 허용을 추가한다. 그 manifest는
    grant provenance가 될 수 없으므로 action을 시작하지 않는다.

## 현재 mechanism에서 삭제·숨길 것

새 Effect Observation Module은 current mechanism의 다음 사용자 가치를 흡수한다.

- effect 전에 applicable authority가 있어야 함
- action/cleanup at-most-once start와 live execution ownership
- bounded identical readback polling과 모든 attempt 보존
- action timeout을 authoritative readback으로만 해소
- action 뒤 required cleanup 시도와 retained target terminal readback
- ambiguous prior effect의 기계적 safety 없는 replay 금지
- correlation/idempotency가 실제 존재할 때의 causal continuity

다음 current mechanism은 정상 caller와 새 public protocol에 남기지 않는다.

- `issue-authorization` command와 invocation-local authorization ref
- caller가 계산·전달하는 arbitrary scope digest와 `authorizationRefs[]`
- `preview-process-step`과 `replay-authorization-scope` command
- caller-visible ACTION/READBACK/CLEANUP step graph와 productTargetRequirement
- caller가 넣는 correlation placeholder/binding ID
- effectfulActions/toolCost budget vector와 reservation ceremony
- PROCESS argv/environment에 secret 또는 authority를 싣는 경로
- cross-run ancestor attempt ledger와 per-run cardinality를 caller가 해석하는 절차

Module 내부에는 fixed effect observation, independent current authority fact, 현재 한 effect의
may-have-run/live owner, complete EffectEvidenceBundle, completed effect safety projection과 unresolved
safety item만 남는다. safety projection은 새 durable state 종류가 아니라 이미 complete bundle에 있는
비semantic projection의 적용 lifetime이다. exact idempotency/correlation이 필요한 Adapter는 그
provider-specific detail을 내부에 숨긴다.

## 명시적 범위 밖

- final function/CLI 이름과 serialized effect/evidence schema
- 구체 product별 effect taxonomy와 production Adapter 목록
- operator approval UI, credential store/secret resolver와 policy engine 구현
- provider별 idempotency key, correlation field, HTTP/MCP/browser/process transport
- timeout/poll interval, rate/resource budget과 performance policy
- concrete live-owner lock, durable storage, network partition과 fault injection
- remediation behavior, migration과 legacy command/schema/test 제거

## Oracle finding 판정 기록

### Initial — `slots-context-phase6in-338da18bbd`

slot 1, DevSpace 무첨부 review가 authoritative readback과 함께 완료됐다. stored model evidence는
`requested=Pro`, `resolved=(unavailable)`, `strategy=current`, `verified=no`이므로 실제 model identity를
확정하지 않는다.

#### F1 — completed implementation effect safety가 Candidate 뒤 사라짐

```text
ORACLE_CLAIM: implementation effect가 complete하면 unresolved item이 아니므로 fresh verification이 같은
  occurrence를 반복하거나, action 없는 fresh readback을 표현하지 못해 영구 UNDETERMINED가 된다.
STRONGEST_COUNTERARGUMENT: complete bundle은 이미 durable하고 fresh verification은 implementation
  evidence를 읽으면 안 되므로 새 action으로 직접 재검증하는 편이 독립적이라고 볼 수 있다. 그러나
  evidence 독립성과 external consequence 반복은 별개이며, action response를 재사용하지 않고 current
  target을 새로 readback하면 둘을 함께 지킬 수 있다.
PURPOSE_INVARIANT_AT_RISK: implementation/verification 독립성, duplicate effect 금지, 조건 해결 뒤 fresh
  verification 가능성.
CONCRETE_EVIDENCE: current action-timeout test는 action 재호출 없이 later readback이 effect를 해소함을
  보인다. 초안은 fixed observation에 action을 필수화하고 verification에는 unresolved fact만 적용했다.
CURRENT_PHASE_OWNERSHIP: prior effect가 새 action을 억제하고 readback-only continuation을 허용하는 의미는
  Effect Observation Seam 소유다.
SMALLEST_CORRECTION: complete bundle의 nonsemantic safety projection만 Candidate 뒤 적용하고, 같은
  occurrence에는 fresh readback-only observation을 허용한다. 별도 occurrence authority가 있어야 새
  action을 시작한다.
COMPLEXITY_DELTA: caller/public state/durable state 종류 +0; effect 경로의 중복 action을 fresh readback으로
  대체하며 replay command와 ancestor ledger는 되살리지 않는다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### F2 — authenticated read를 dangerous effect로 과분류

```text
ORACLE_CLAIM: credential/protected target 또는 routine rate-limit 가능성만으로 ordinary authenticated GET도
  may-have-run/replay/cleanup lifecycle에 들어간다.
STRONGEST_COUNTERARGUMENT: remote read도 rate limit, audit log 또는 비용을 발생시킬 수 있어 보수적으로
  effect로 취급하는 편이 안전하다. 그러나 그 논리면 거의 모든 remote observation이 Phase 6을 거쳐
  Seam이 위험한 consequence를 분리하지 못하고 정상 비용만 늘린다.
PURPOSE_INVARIANT_AT_RISK: fresh direct product observation과 정상 실행 비용 감소.
CONCRETE_EVIDENCE: 초안은 credential 사용 자체와 routine request cost를 effect 조건으로 썼고 fixed
  observation은 action request를 요구했다. current PROCESS의 secret 제한은 delivery 지원 부재이지 모든
  authenticated read의 replay 위험 증명이 아니다.
CURRENT_PHASE_OWNERSHIP: 어떤 operation이 Phase 6 action lifecycle에 드는지는 이 단계의 단일 질문이다.
SMALLEST_CORRECTION: credential/privacy는 fixed read Adapter 조건으로 분리하고, durable/external mutation,
  visible consequence, duplicate consequence 또는 cleanup 필요가 있을 때만 dangerous effect로 분류한다.
COMPLEXITY_DELTA: caller/failure state +0, read-only 정상 경로와 private durable state 감소; 기존 opaque
  credential/redaction 책임 안에서 해결한다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### F3 — Candidate가 effect grant를 자기 승인할 수 있음

```text
ORACLE_CLAIM: exact authority 내용만 요구하고 provenance를 제한하지 않으면 Worker가 Candidate 안의
  operational manifest를 바꿔 자기 production effect를 승인할 수 있다.
STRONGEST_COUNTERARGUMENT: current product/repository authority라는 표현과 Phase 4의 planning/durable-state
  격리는 Candidate-authored grant를 배제한다고 읽을 수 있다. 그러나 repository-owned operational
  config는 Candidate source일 수 있어 conforming Adapter가 이를 grant로 선택하는 경로가 남는다.
PURPOSE_INVARIANT_AT_RISK: 실제 동의, 구현 결과와 실행 권한 분리, unauthorized production/tenant effect
  금지.
CONCRETE_EVIDENCE: current issue_authorization은 Coordinator가 syntactically valid scope digest를 임의
  발급하고 verifier는 invocation/digest 일치만 확인한다. 이를 제거하는 것은 맞지만 grant가 Candidate
  밖에서 온다는 provenance 가치는 명시적으로 남겨야 한다.
CURRENT_PHASE_OWNERSHIP: effect를 허용하는 authority source의 최소 의미는 Phase 6 gate 소유다.
SMALLEST_CORRECTION: granting authority는 Candidate/Verifier/effect writable namespace 밖의 authoritative
  source에서만 오고 Candidate content는 좁히거나 금지만 할 수 있다고 고정한다.
COMPLEXITY_DELTA: caller/durable/failure state/token +0; 기존 authority gate에 provenance/currentness
  확인만 추가하고 generic policy engine을 만들지 않는다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

initial review는 cross-Candidate overlapping effect 차단, provider-backed idempotency/correlation,
cleanup ordering, authoritative terminal receipt의 제한과 privacy fail-closed에는 추가 correction이
필요하지 않다고 판정했다. F1~F3 최소 correction을 같은 conversation follow-up으로 재공격한다.

### Follow-up 1 — `slots-followup-phase6fo-3f6fe9cd52`

같은 conversation URL과 slot 1에서 prompt submission과 completed UI answer를 확인했다. wrapper의 prompt
commit probe timeout 때문에 stock session status와 authoritative readback은 `error`지만, child session의
완성 답변을 harvest했다. 이 delivery 이상은 설계 근거로 사용하지 않는다. stored model evidence는
`requested=Pro`, `resolved=(unavailable)`, `strategy=current`, `verified=no`다.

```text
F1: CLOSED — completed implementation bundle의 safety projection은 semantic evidence를 포함하지 않고
  같은 occurrence의 action 억제와 fresh readback-only 허용에만 쓰인다. 별도 occurrence에는 current
  authority와 새 action-bearing observation이 필요하다.
F2: CLOSED — authenticated pure read는 opaque credential/read authority/privacy/redaction을 지키는
  Phase 5 read-only observation이며, visible/duplicate consequence가 있을 때만 effect lifecycle이다.
F3: CLOSED — positive grant는 Candidate/effect writable namespace 밖에서만 오고 Candidate content는
  external grant를 좁히거나 금지할 수 있어 effective authority가 교집합으로 유지된다.
새 material finding: 없음
사용자 결정: 없음
caller Interface / durable state 종류 / failure state 순증가: 없음
authorization / replay / ledger ceremony 회귀: 없음
```

Oracle closure 선언과 별개로 Phase 1~5 계약과 current source/test에 다시 대조했다.

- F1은 implementation evidence를 final verification에 재사용하지 않으면서 action timeout을 later
  readback으로 해소하는 current 보장을 duplicate-free fresh readback으로 일반화한다.
- F2는 current PROCESS의 secret delivery 제한과 effect replay 위험을 구분해 ordinary read에
  may-have-run state를 만들지 않는다.
- F3은 current arbitrary authorization digest를 제거하되, effect 수행자가 grant를 자기 생성하지
  못한다는 실제 authority 가치만 internal Adapter gate에 남긴다.
- cross-Candidate applicability는 같은 fixed Adapter가 기계적으로 canonicalize한 target와
  action consequence/occurrence에만 한정하며 work-wide semantic matcher를 만들지 않는다.
- provider receipt conformance, marker/dispatch crash ordering과 Adapter classification은 Phase 7 runtime
  검증에 남기며 현재 Interface를 늘리지 않는다.

## 완료 판단

`DESIGN_CONVERGED`다.

- dangerous effect만 fixed Effect Observation Adapter로 분리하고 authenticated pure read의 정상 비용은
  늘리지 않는다.
- exact non-self-grant authority 없이는 action을 시작하지 않으며 Ticket/verify/capability/digest를
  묵시적 동의로 사용하지 않는다.
- 외부 dispatch 전 durable may-have-run, live owner, ambiguous-effect 비재실행과 cross-Candidate
  occurrence safety를 한 Module에 숨긴다.
- persistent effect는 fresh authoritative readback과 필요한 cleanup/final disposition으로만 닫는다.
- implementation check evidence와 fresh verification evidence는 섞지 않으면서 completed safety
  projection으로 duplicate action을 막는다.
- caller-visible authorization ref, replay scope, ACTION/READBACK/CLEANUP graph, correlation placeholder와
  attempt ledger는 재도입하지 않았다.
- 열린 material finding과 사용자 결정은 없다. Phase 7과 제품 구현은 시작하지 않았다.
