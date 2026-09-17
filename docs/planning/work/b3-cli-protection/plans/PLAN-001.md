# PLAN-001 — B3 CLI Protection 실행 방법

Plan 역할: 이 문서는 `B3-CLI-PROTECTION` Scope의 구현 순서와 구현자 자체 점검 방법이다. 제품 의미나 Acceptance를 새로 정의하지 않으며, 구현·검증 판정·배포·다음 Block 시작을 승인하지 않는다.

## 1. 결합된 권위, 현재성, 실행 경계

- Product Thesis: `/home/user01/project/oracle/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md`, SHA-256 `b532ad84c1e8529e8169f68e6673d279b6f3a6cf8018f7d0fd64b761cb9c69c6`.
  - 목적과 완전한 제품 루프: 일반 사용자·agent·scheduler가 별도 운영 지식을 주입하지 않아도 설치/사전 검증/점유/제출/현재 턴 결과 확정/저장/해제 또는 격리/결과 회수까지 같은 보호를 받아야 한다.
  - false-success 경계: child exit 0이나 브라우저 응답 존재만으로 성공이 아니다. 성공은 B2가 보장하는 `same conversation ∧ uniquely identified current user turn ∧ assistant owned by that turn ∧ completed response`를 우회하지 않아야 한다.
  - 실패/복구 의미: 제출 전 조건 불충족은 remote effect 전에 fail-closed로 거절한다. 제출 가능성이 생긴 뒤의 불확실성은 자동 재제출하지 않으며, 이미 귀속 확정된 결과와 후처리 실패를 분리한다.
  - authoritative success readback: 생성된 실제 child argv, session metadata/result, 원격 current-turn 관찰, slot 종료 상태를 함께 읽는다. command normalization 단위 테스트나 CI green 하나만으로 전체 제품 성공을 주장하지 않는다.
- Scope: `/home/user01/project/oracle/docs/planning/work/b3-cli-protection/SCOPE.md`, SHA-256 `1ce86cf5628595adc9f0c49a36754f091c0f83b05c7608cf660f10d60981b7bf`, `Schema: iis-scope/v1`, `Status: ready`.
  - canonical `validate_scope.py --json` 결과는 `status: ready`였고 Product/Transition Authority 경로와 digest가 Scope 기록과 일치했다.
- Transition Authority: `/home/user01/project/oracle/docs/planning/adaptive/maintainable-operational-runtime/BASELINE-001.md`, SHA-256 `6e4d81d83c18d21ec8f1d3e60f671bd2d3db07e0a8699507009e91e953b5d1a9`.
  - 적용되는 전이 제약은 Block `B3-CLI-PROTECTION`, 모든 Global Invariant 중 특히 `GI-03`~`GI-08`, `GI-11`, Path Invariant `PI-08`~`PI-13`, 그리고 `HA-07 Production default safety semantics`다.
  - 기본 `2h`, mandatory pre-submit validation, unsupported-runtime fail-closed는 public execution path에 함께 존재하는 한 runnable cut이어야 한다. CI 연결만 또는 agent 지침만 먼저 존재하는 상태를 B3 완료로 발표하지 않는다.
  - 원문 자체는 `Status: DRAFT`, `Approved by: Pending`, `Approval scope: None`, `Inter-Block auto-continuation authorized: no`다. Scope가 결합한 제약은 보존하지만 이 Plan은 product edit, release promotion, 외부 Browser 실행 또는 B4 시작 권한을 만들지 않는다.
- Repository investigation artifact: supplied artifact 없음. 아래 소스와 테스트를 직접 읽어 method grounding으로 사용했다.
- 현재 Scope의 Non-Goal: Block 4의 clean isolated environment live E2E는 수행하지 않는다. B1 runtime provenance와 B2 result attribution 의미를 재설계하지 않는다.

## 2. 달성할 관찰과 보존 조건

1. public `run`, `submit`, `followup`이 browser child command를 정규화할 때 caller가 `--browser-timeout`을 생략했으면 정확히 한 번 `--browser-timeout 2h`를 넣는다.
2. caller가 유효한 `--browser-timeout 30m` 또는 `--browser-timeout=30m`를 한 번 지정하면 값과 표기 의미를 덮어쓰지 않는다. missing/empty/duplicate timeout은 child/claim 이전에 exit code 2로 거절한다. 값 자체의 duration validity는 실제 stock Oracle parser가 최종 결정하되, wrapper가 명백한 구조 오류를 통과시키지 않는다.
3. timeout 삽입은 `--` terminator 앞에 일어난다. terminator 뒤 prompt/child payload에 같은 문자열이 있어도 option으로 오인하지 않는다.
4. runtime compatibility, argument/routing validation, attachment ZIP preparation은 기존 순서를 유지하고 remote submission 전에 끝난다. slot claim 뒤에는 각 public execution path가 실제 child `Popen` 전에 현재 slot의 CDP 및 login을 `pre_submit_check()`로 다시 읽는다.
5. guard 실패 시 `Popen`은 0회이고 exit code는 2다. 현재 claim은 owner-checked `finish_job`으로 해제하거나, 해제를 증명하지 못하면 격리/운영자 조치가 드러난다. prepared ZIP은 기존 ownership 규칙으로 정리하고 remote submission 가능성으로 표시하지 않는다.
6. `submit`은 첫 candidate의 guard 실패가 안전하게 해제된 경우에만 기존 compatible-slot 순서로 다음 slot을 시도한다. `followup`은 원 slot에서 실패하고 다른 slot/conversation으로 이동하지 않는다. `run`은 지정 slot에서 실패한다.
7. `.github/workflows/ci.yml`의 독립 Linux Python job이 `tests/test_slots.py`와 `tests/test_followup.py`를 실행하고, 실패를 무시하는 조건 없이 workflow success를 차단한다.
8. queue wait, attachment preparation, cleanup, caller/scheduler process ceiling은 browser response timeout `2h`와 합치거나 이름을 바꾸지 않는다. 이 Scope는 외부 scheduler timeout을 자동 연장하지 않는다.

## 3. Code Grounding

### EXISTING

1. **공통 command normalization 경계가 이미 있다.**
   - `oracle-browser-slots/oracle_browser_slots/runner.py:626-752`의 `_validated_oracle_command()`가 runtime identity, forbidden transport flags, required `--engine browser`, model strategy, slot별 `--remote-chrome`, workspace URL을 검사/주입한다.
   - explicit `run`은 `runner.py:61-75`, `submit`은 `allocator.py:101-124`의 `validate_auto_command()`, `followup`은 `followup.py:1012-1017`의 동일 호출을 거친다. slot 선택 후 `claim_for_auto()`가 slot-dependent normalization을 다시 적용한다.
   - 현재 values/required-values table에는 `--browser-timeout`이 없으므로 생략 시 stock Oracle의 짧은 기본값이 유지된다.
2. **현재 `run`에는 live pre-submit guard가 빠져 있다.**
   - `runner.py:133-165`는 claim 성공 후 바로 `execute_claimed()`를 호출한다.
   - `runner.py:375-405`의 `pre_submit_check()`는 `service.cdp.check_login(slot)`로 CDP reachability와 login validity를 읽고 typed reason/operator action을 반환하지만 `run()`은 호출하지 않는다.
3. **`submit`과 `followup`에는 이미 orchestration-level guard가 있다.**
   - `allocator.py:525-648`은 claim 후 `pre_submit_check()`를 실행하고 실패한 slot claim을 finish한 뒤, release가 확정된 경우에만 다음 compatible slot을 고려한다. 성공하면 `_execute_assignment()`가 `execute_claimed()`로 간다.
   - `followup.py:1177-1270`은 originating slot claim 후 `pre_submit_check()`를 실행하고 실패하면 finish 후 child 없이 반환한다. 다른 slot fallback은 없다.
   - followup의 archived-conversation restore는 guard 뒤, child 앞에서 별도 fail-closed readback을 수행한다(`followup.py:1272-1316`). 이를 CDP/login guard로 대체하거나 순서를 뒤집지 않는다.
4. **실제 child process boundary는 한 곳이다.**
   - `runner.py:407-624`의 `execute_claimed()`가 runtime entry를 재확인하고 `runner.py:445`에서 `popen_factory`를 호출한다. `run`, `submit`, `followup`의 정상 child path는 모두 이 메서드로 수렴한다.
   - 이 메서드는 child 시작 여부를 기준으로 submission 가능성, attachment cleanup/manifest, finish/release를 기록한다. guard failure를 spawn error나 post-submit failure로 오분류하지 않아야 한다.
5. **public CLI dispatch는 세 경로를 명확히 나눈다.**
   - `cli.py:85-102`는 `followup`을 `FollowupRunner.run()`에 전달하고, `cli.py:129-136`은 `submit`을 `AutoAllocator.submit()`, explicit `run`을 `JobRunner.run()`에 전달한다.
   - `prepare`와 `status`는 child를 만들지 않으므로 timeout/submit guard 대상이 아니다. `--dry-run`/`--preview`는 child Oracle 내부의 non-submitting operation이며 별도 선행 요구가 아니다.
6. **attachment validation은 이미 timeout option의 value requirement를 안다.**
   - `attachments.py:47-92`의 `REQUIRED_VALUE_OPTIONS`에 `--browser-timeout`이 있어 file parsing 시 분리형 option의 값 누락을 감지할 수 있다. 하지만 file-free command의 wrapper normalization을 대신하지 않는다.
7. **stock duration 의미는 실제 Node parser가 소유한다.**
   - `src/cli/options.ts:202-214`의 `parseDurationOption()`은 non-empty positive duration을 요구하고 `30m`, `10s`, `500ms`, `2h`를 지원한다. `src/duration.ts:1-31`은 `ms/s/m/h` 및 복합 duration을 해석한다.
   - wrapper는 이 parser의 별도 Python 복제본을 만들지 않는다. default `2h`를 주입하고 structural duplicate/missing만 조기에 거절하며, explicit value의 canonical duration 판정은 동일 release의 stock CLI가 담당한다.
8. **기존 tests가 재사용할 경계를 갖는다.**
   - `tests/test_slots.py:1359-1957`은 normalization/claim/Popen/release를, `tests/test_slots.py:2101-2961`은 allocation, duplicate, pre-submit reassignment를 다룬다.
   - `tests/test_followup.py:497-1203`은 원 slot 고정, child argv, archived restore, no-fallback을 다룬다. fake `popen_factory`는 “guard 실패 시 spawn 0회”와 normalized argv 관찰에 적합하다.
9. **CI에는 Python gate가 없다.**
   - `.github/workflows/ci.yml`은 OS matrix Node lint/docs/test/build/packed-cli와 Linux CDP proof만 실행한다. `actions/setup-python`, package install, pytest invocation이 없다.
   - `oracle-browser-slots/pyproject.toml`은 Python `>=3.11`과 setuptools package를 선언하지만 pytest dependency는 선언하지 않는다.
10. 현재성 fingerprint:
    - `runner.py` `10add9924914b5b1fa062a38a9a9b140e9e0ce4ee2ef904f07e5e9935f6dba1f`
    - `allocator.py` `7de092f25fa9dd8f50028d0af44b6fd2c1f074ceace997db6abdf569ed24bbee`
    - `followup.py` `5bd6f02bb82a47159b4ace743555d82b36cf905d74f87b349aa163901eb9e0c5`
    - `cli.py` `5f4034100cd2b9ed5daea196ca686255648167e674e9ddde67c847bb2367c8c5`
    - `.github/workflows/ci.yml` `ae4099fb57d38d35fc69cda3bee324929d2088e7ef558a93f1db8ec23d965b90`
    - `tests/test_slots.py` `cd1977f94b103b96105114de8e82659c26111e00a73777f7db8704d3c8a85fcc`
    - `tests/test_followup.py` `b3d1408ea79af5719c1533d5e6cc348572dde3f41e01a4953c09263bc574ad8c`

### PROPOSED

1. `runner.py`에 `BROWSER_TIMEOUT_FLAG = "--browser-timeout"`와 `DEFAULT_BROWSER_TIMEOUT = "2h"`를 둔다. `_validated_oracle_command()`의 기존 option scanner를 확장하여 분리형과 equals형 occurrence를 terminator 전까지만 한 번 계산한다.
2. occurrence가 없으면 기존 `_insert_before_terminator()`로 `(BROWSER_TIMEOUT_FLAG, DEFAULT_BROWSER_TIMEOUT)`을 주입한다. occurrence가 정확히 하나이면 원래 token/value를 그대로 둔다. missing/empty/duplicate는 `OracleTransportError`로 거절한다. timeout을 required-values equality table에 넣어 explicit override를 `2h`와 비교하지 않는다.
3. default/override 모두 이후 slot-dependent 재정규화를 통과해도 occurrence가 정확히 하나여야 한다. `validate_auto_command(None)`이 먼저 `2h`를 넣고 `claim_for_auto(slot)`가 remote endpoint를 넣을 때 timeout을 다시 추가하지 않는 idempotence를 테스트한다.
4. `JobRunner.run()`에 claim 직후/`execute_claimed()` 직전 `pre_submit_check(slot_id)`를 추가한다. 실패 시 prepared attachment cleanup, owner-checked `finish_job(..., outcome="pre_submit_failed", exit_code=2, ...)`, `child_started=False`를 반환하고 Popen으로 내려가지 않는다.
5. allocator/followup의 기존 guard는 보존한다. 세 public callsite의 guard 결과/exit semantics를 공통 private helper로 정리하는 것은 허용하지만, submit의 safe reassignment와 followup의 no-fallback 의미를 하나의 generic retry helper로 합치지 않는다.
6. 모든 live guard failure를 exit code 2로 통일한다. claim release가 실패하면 exit 2보다 더 중요한 격리 readback(`released=false`, state/operator action)을 보존하되 성공이나 fallback으로 바꾸지 않는다. `accepted`는 claim 사실을 나타낼 수 있으므로 `child_started=False`, outcome/event, exit code가 remote submission 여부를 명확히 한다.
7. `execute_claimed()`가 유일 Popen boundary라는 구조는 유지한다. public callers가 guard를 생략하지 못하는지 behavioral tests로 고정하고, 새 child-producing entrypoint가 생기면 같은 guard matrix에 추가하도록 구현 주석이 아니라 call graph와 테스트 ownership으로 보장한다.
8. `.github/workflows/ci.yml`에 독립 `python-wrapper-tests` job을 추가한다. `ubuntu-latest`, repository checkout, supported Python(최소 계약인 3.11), `actions/setup-python`, `working-directory: oracle-browser-slots`에서 `python -m pip install -e . pytest`, `python -m pytest tests/test_slots.py tests/test_followup.py`를 실행한다. `continue-on-error`, failure-swallowing shell, path filter, matrix exclusion을 두지 않는다.
9. Node build job과 Python job은 동일 workflow event/commit checkout을 사용한다. Python job을 Node OS matrix에 반복해 넣지 않는다. Scope가 요구한 Linux/WSL2 wrapper gate를 하나의 필수 job으로 명확히 둔다.

### UNRESOLVED

1. **Transition approval authority**: bound `BASELINE-001.md`는 DRAFT/Pending/None이며 실행 권한을 부여하지 않는다. 이 Plan 작성과 read-only review는 가능하지만 product/test/CI edit 및 release candidate 실행은 owning transition authority가 승인 상태를 해소하기 전 허용되지 않는다. 최소 판별 관찰은 B3를 포함하는 exact approved baseline/revision의 approval scope 직접 readback이다. Next owner: preparation lead / transition authority owner.
2. **B1/B2 handoff evidence**: 이 assignment에는 B1 exact release candidate identity나 B2 admitted result-attribution handoff가 공급되지 않았다. source-level 구현과 focused tests는 계획할 수 있지만 B3 Exit, packed-runtime consistency 또는 B4 continuation을 주장할 수 없다. 최소 관찰은 동일 candidate에 대한 B1 provenance와 B2 attribution gate/readback이다.
3. **실제 session timeout readback**: current read-only planning에서는 live Browser child를 실행하지 않았다. generated argv는 wrapper 결정의 primary readback이지만 stock session이 `2h`를 실제 적용한 최종 readback은 승인된 implementation/verifier 환경에서 exact child/session metadata로 확인해야 한다.

## 4. Entry/read paths, owners, 수명

### Entry 및 결정 경로

1. `cli.main()`이 child argv에서 wrapper terminator 하나를 제거하고 `run`, `submit`, `followup`으로 dispatch한다.
2. 세 경로 모두 `_validated_oracle_command()`에서 runtime/transport/model/timeout의 transport-independent normalization을 받는다.
3. `run`은 지정 slot으로 재정규화하고 claim한다. `submit`은 compatible slot을 계산한 뒤 선택 slot마다 재정규화/claim한다. `followup`은 parent의 originating slot으로만 재정규화/claim한다.
4. file-bearing request만 기존 `prepare_file_request()`가 exact selected set을 one ZIP으로 만든다. timeout default는 file 유무와 독립적이며 no-file request에 ZIP을 만들지 않는다.
5. claim 뒤 volatile CDP/login reader인 `pre_submit_check()`가 현재 slot을 읽는다. 성공한 경로만 `execute_claimed()`의 Popen boundary에 도달한다.
6. stock Oracle가 normalized `--browser-timeout`을 session option으로 해석하고, B2의 current-turn result gate가 최종 success를 결정한다.

### Writer/reader와 상태 의미

- timeout writer: `_validated_oracle_command()`가 in-memory argv만 쓴다. 별도 config/persistent default를 만들지 않는다.
- explicit override reader: same scanner가 terminator 전 occurrence를 읽는다. caller의 유효 값이 authoritative하며 wrapper default보다 우선한다.
- live readiness reader: `service.cdp.check_login(slot)`가 현재 CDP/login을 판정한다. 과거 `prepare`/dry-run 성공은 이 readback을 대신하지 않는다.
- slot state writer: `claim_job`과 `finish_job`만 occupancy를 변경한다. guard 자체가 slot JSON을 직접 수정하지 않는다.
- external effect owner: `execute_claimed()`가 시작한 stock Oracle child만 remote prompt submission 가능성을 만든다. guard 실패에서 `popen_factory`가 호출되지 않으면 remote submission은 발생하지 않은 것으로 분류할 수 있다.
- CI writer: workflow는 product state를 쓰지 않고 exact checkout에서 test result를 만든다. job success/failure가 merge/release gate의 readback이다.

### interruption/partial failure

| 경계 | 처리 |
| --- | --- |
| normalization/timeout 구조 오류 | claim/ZIP/Popen 전 exit 2; remote effect 없음. |
| ZIP 준비 실패 | 기존 cleanup/diagnostic 계약으로 exit 2; claim/Popen 없음. |
| claim 후 CDP/login 실패 | Popen 0회, owner-checked finish, exit 2; release 미확정이면 slot 격리 지시. |
| submit 첫 slot guard 실패 | finish/readback이 안전할 때만 다음 compatible slot; 실패한 slot evidence를 reassignment record에 보존. |
| followup guard 실패 | originating slot에서 종료; 다른 slot/conversation fallback 없음. |
| guard 성공 후 child nonzero/interrupt | 기존 post-start 의미 유지; 자동 재시도 없음. |
| CI install/test 실패 | `python-wrapper-tests` job red; Node green으로 상쇄하지 않음. |

## 5. 구현 순서 — HA-07 atomic cut

1. **timeout scanner를 기존 normalization에 결합한다.** 새 parser/설정 계층을 만들지 말고 기존 terminator-aware occurrence scanner와 insertion helper를 재사용한다. missing/empty/duplicate case와 separated/equals explicit case를 먼저 unit-level로 고정한다.
2. **default injection을 idempotent하게 연결한다.** transport-independent `validate_auto_command()`와 slot-specific `_validated_oracle_command()`의 두 번 normalization 뒤에도 exact one timeout이 남도록 한다. required `engine/model-strategy/remote-chrome` 순서 변화는 의미가 없지만 tests는 exact value/cardinality와 terminator 위치를 관찰한다.
3. **explicit `run` guard gap을 닫는다.** claim 성공 직후 live check를 호출하고, failure terminal record/cleanup/finish를 구현한다. `execute_claimed()`를 호출하지 않는 negative path를 유지한다.
4. **submit/followup guard 계약을 정렬한다.** 기존 placement와 submit reassignment/followup no-fallback은 보존한다. guard failure exit code와 `child_started=False` readback을 Scope 계약에 맞춘다. archived followup restore는 live login check 이후, child 이전에 남긴다.
5. **entrypoint matrix tests를 추가한다.** `test_slots.py`에 normalization 및 explicit run/submit guard cases, `test_followup.py`에 followup guard cases를 추가한다. fake CDP가 unready/exception을 반환하고 `popen_factory`가 호출되면 test 자체가 실패하도록 한다.
6. **positive execution regressions를 갱신한다.** 기존 exact argv assertions에 default `--browser-timeout 2h`를 반영한다. explicit override가 preserved되는 run/submit/followup 한 사례씩과 double-normalization cardinality를 확인한다. broad duplicate parameter rows는 만들지 않는다.
7. **CI job을 연결한다.** setup-python/install/두 지정 파일 pytest를 별도 required-by-failure job으로 추가한다. test command는 repository root가 아니라 package root를 명시하여 import path가 우연한 caller cwd에 의존하지 않게 한다.
8. **하나의 runnable source cut으로 self-check한다.** timeout만 또는 tests/CI만 별도 완료로 선언하지 않는다. runtime semantics, entrypoint guards, focused pytest, workflow gate가 함께 verifier handoff 대상이다.

## 6. 테스트와 구현자 자체 점검

Project-wide formatter/lint/build/test는 integration owner가 한 번 수행한다. 구현자는 아래 좁은 경계만 실행하고 결과를 보존한다.

### 6.1 Focused normalization/readback

```bash
cd /home/user01/project/oracle/oracle-browser-slots
python3 -m pytest tests/test_slots.py -k 'browser_timeout or missing_oracle_flags or equals_flags'
```

필수 관찰:

- omitted timeout → generated child argv에 exact one `--browser-timeout 2h`;
- `--browser-timeout 30m` 및 `--browser-timeout=30m` → exact one caller value, `2h` 없음;
- missing/empty/duplicate → claim/Popen 전 exit 2;
- terminator 뒤 `--browser-timeout` text는 option occurrence가 아님;
- submit의 pre-slot/selected-slot double normalization 후에도 exact one timeout.

### 6.2 Public entrypoint guard matrix

```bash
cd /home/user01/project/oracle/oracle-browser-slots
python3 -m pytest tests/test_slots.py -k 'pre_submit or public_run or submit'
python3 -m pytest tests/test_followup.py -k 'pre_submit or followup'
```

최소 matrix:

| entrypoint | guard observation | required readback |
| --- | --- | --- |
| `run` | CDP error, login invalid | exit 2, `child_started=False`, Popen 0, own claim finish/release 또는 quarantine readback |
| `submit` | candidate 1 invalid, candidate 2 ready | candidate 1 Popen 0/released, candidate 2 exact one Popen; attempted/reassignment evidence 보존 |
| `submit` | 모든 compatible slot invalid | exit 2, Popen 0, false success/queue residue 없음 |
| `followup` | originating slot invalid | exit 2, Popen 0, 다른 slot attempt 없음, parent lineage 불변 |
| `followup` archived | login ready, restore failure | Popen 0, origin claim finish, no fallback |

Tests는 FakeCDP/fake Popen으로 ordering을 증명하지만 실제 CDP/login 또는 remote submission 성공 증거라고 주장하지 않는다.

### 6.3 Exact required Python suite

```bash
cd /home/user01/project/oracle/oracle-browser-slots
python3 -m pytest tests/test_slots.py tests/test_followup.py
```

두 파일 모두 green이어야 하며 timeout/guard 변경 때문에 기존 slot ownership, FIFO, followup lineage, one-ZIP cleanup 의미가 깨지지 않아야 한다.

### 6.4 CI structural and execution readback

- `.github/workflows/ci.yml`에서 `python-wrapper-tests`가 `ubuntu-latest`, setup-python, package install, exact two-file pytest command를 갖는지 직접 읽는다.
- `continue-on-error` 또는 `|| true`가 없어 pytest nonzero가 job/workflow failure인지 확인한다.
- 가능한 CI 또는 equivalent isolated runner에서 job command를 그대로 실행하고 checkout commit SHA와 pytest summary를 보존한다. 로컬 pytest green만으로 CI gate 존재를 대체하지 않는다.

### 6.5 Minimum real acceptance path와 verifier handoff

승인된 runtime/login/외부 effect 권한이 있고 C0~C2가 충족된 뒤 verifier가 수행한다.

1. exact candidate로 no-file `run` 또는 `submit`을 caller timeout 없이 한 번 실행하고 actual child argv/session option에서 `2h`를 읽는다.
2. 별도 request에 `--browser-timeout 30m`을 주고 child argv/session option에서 `30m` 보존을 읽는다.
3. login/CDP를 의도적으로 unavailable하게 만든 non-submitting precondition case에서 child PID/Popen과 remote prompt count가 증가하지 않고 exit 2인지 읽는다.
4. B2 authoritative current-turn result gate와 session result를 대조한다. wrapper exit 0만으로 성공을 선언하지 않는다.
5. handoff에는 exact Scope/Thesis/Transition hashes, source/candidate identity, default/override argv 및 session readback, entrypoint guard matrix, pytest/CI result, slot cleanup/quarantine 상태를 포함한다.

Block 4의 clean-environment 전체 E2E는 이 Scope에서 수행하거나 대체하지 않는다.

## 7. Conditional first-work bundles

### C0 — Transition authority gate

- `plan_anchor`: §1 Transition Authority, §3 UNRESOLVED 1.
- `permitted_initial_work`: exact bound baseline 및 caller가 공급한 superseding approval의 read-only inspection; Plan 작성/독립 review.
- `discriminating_observation`: exact approved transition source가 B3 implementation 범위와 continuation ceiling을 명시하거나 owning authority가 ready Scope와 DRAFT binding 충돌을 명시적으로 해소함.
- `dependent_work_not_yet_permitted`: product/test/CI edits, Browser/slot effect, release candidate promotion.
- `response_if_refuted`: 구현을 시작하지 않고 authority conflict를 preparation lead/transition authority owner에게 반환한다. Thesis/Scope/Baseline bytes를 임의 수정하지 않는다.

### C1 — B1/B2 handoff currentness

- `plan_anchor`: §3 UNRESOLVED 2, §6.5.
- `permitted_initial_work`: supplied B1/B2 handoff의 exact candidate/source/guard readback을 비제출 방식으로 읽기.
- `discriminating_observation`: B1 runtime provenance가 현재 wrapper/stock artifact와 연결되고, B2 result-attribution gate가 같은 candidate에서 present/current하며 unresolved remote request가 격리됨.
- `dependent_work_not_yet_permitted`: B3 Exit/Block 4 continuation 주장, packed candidate success 합성.
- `response_if_refuted`: promotion과 external execution을 중단하고 해당 predecessor owner 및 Plan owner에게 반환한다. B3 source tests를 predecessor evidence로 재분류하지 않는다.

### C2 — Timeout normalization and guard cut

- `plan_anchor`: §5 steps 1-6.
- `permitted_initial_work`: C0 충족 및 independent Plan ADMIT 뒤 runner/allocator/followup/tests의 local reversible edit와 focused fake-based tests.
- `discriminating_observation`: three entrypoints generate exact one default/override timeout; every unready CDP/login case records Popen 0 and exit 2; submit-only safe reassignment 및 followup no-fallback가 유지됨.
- `dependent_work_not_yet_permitted`: release promotion, live Browser submission, Scope PASS/B3 Exit 주장.
- `response_if_refuted`: affected runnable candidate 사용을 중단하고 claim/slot evidence를 보존한다. public path ownership, retry policy 또는 guard boundary가 달라져야 하면 Plan revision과 fresh review로 반환한다.

### C3 — CI gate execution

- `plan_anchor`: §5 steps 7-8, §6.3-6.4.
- `permitted_initial_work`: exact checkout에서 Python job dependency install과 지정 두 pytest 파일 실행.
- `discriminating_observation`: job은 same commit에서 두 파일을 수집/실행하고 test failure가 workflow failure로 전파됨.
- `dependent_work_not_yet_permitted`: CI gate green 주장, release candidate handoff, B3 Exit.
- `response_if_refuted`: optional/ignored gate를 만들지 않고 workflow handoff를 중단한다. dependency/install 문제를 product test skip으로 우회하지 않는다.

### C4 — Actual default/override and no-submit readback

- `plan_anchor`: §6.5.
- `permitted_initial_work`: 별도 외부-effect 권한과 current candidate가 명시된 뒤 isolated request 하나씩으로 default/override를 관찰하고, 별도 unready precondition case를 실행.
- `discriminating_observation`: actual child/session option이 각각 `2h`/caller override이며, unready case는 child/remote prompt 증가 없이 exit 2; B2 current-turn gate가 그대로 적용됨.
- `dependent_work_not_yet_permitted`: clean-environment matrix, B4, transformation completion, deployment/publish.
- `response_if_refuted`: 신규 submission을 중단하고 request/session/conversation/slot evidence를 보존한다. timeout/guard defect는 Plan/implementer로, product meaning 변경 필요는 Scope/Thesis owner로 반환한다.

## 8. 구현 재량과 재검토 경계

- implementer 재량: private constant/helper 이름, equivalent option-occurrence helper 재사용, diagnostic 문구, test helper 구성, Python 3.11 이상의 exact CI patch version.
- 새 duration parser, generic validation framework, telemetry, persistent config, retry service, timeout abstraction, 새 recovery entrypoint는 추가하지 않는다.
- 다음은 material method 변경이므로 affected work를 멈추고 Plan 개정 및 fresh independent review가 필요하다: timeout ownership/precedence, accepted override syntax, public entrypoint set, guard/Popen ordering, submit reassignment 또는 followup fallback policy, slot finish/quarantine 의미, CI acceptance surface, B1/B2 provenance/readback 연결.
- current Outcome/Acceptance/Non-Goals를 바꾸려면 Scope owner로, caller-independent protection/false-success/timeout 제품 의미를 바꾸려면 Thesis owner로 반환한다.
- independent Plan Reviewer가 `ADMIT/REVISE/EVIDENCE_NEEDED`를 소유한다. 이 Plan의 존재나 digest는 구현 admission, Scope verification, B3 Exit, B4 시작 또는 제품 completion을 뜻하지 않는다.
