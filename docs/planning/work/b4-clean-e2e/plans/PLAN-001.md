# PLAN-001 — B4 Clean E2E 실행 방법

Plan 역할: 이 문서는 exact `B4-CLEAN-E2E` Scope를 구현하고 구현자 자체 점검으로 넘기기 위한 실행 방법이다. 제품 의미나 Acceptance를 새로 정의하지 않으며, 실제 외부 prompt 제출, 배포, registry publish 또는 Transformation Completion 판정을 승인하지 않는다.

## 1. 결합된 권위와 현재성

- Product Thesis: `/home/user01/project/oracle/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md`, SHA-256 `b532ad84c1e8529e8169f68e6673d279b6f3a6cf8018f7d0fd64b761cb9c69c6`.
  - 목적과 완전한 제품 루프: 지원 Linux/WSL2 환경에서 설치·사전 검증·점유·실행·현재 요청 결과 확정·저장·해제 또는 격리·결과 회수가 개인 HOME/NVM과 숙련자 지침 없이 닫혀야 한다.
  - false-success 경계: package 생성, child exit 0, 마지막 답변 또는 dry-run 한 번은 제품 성공의 대체 증거가 아니다. 실제 제출 성공에는 `same conversation ∧ uniquely identified current user turn ∧ assistant owned by that turn ∧ completed response`가 필요하다.
  - 실패/복구 의미: 제출 전 조건 불충족은 remote effect 전에 거절한다. 제출 가능성이 생긴 뒤에는 자동 재제출하지 않고, 이미 확정된 결과와 cleanup/slot 실패를 분리한다.
  - authoritative readback: 실제 설치된 artifact의 executable/selector identity, CLI 종료 상태, session/result와 slot state를 같은 candidate에서 읽는다. 이번 Scope의 non-submitting 경로는 remote response 증거를 만들지 않으므로 그것을 주장하지 않는다.
- Scope: `/home/user01/project/oracle/docs/planning/work/b4-clean-e2e/SCOPE.md`, SHA-256 `f4c539bd3f45a1a99732197176e9f91f0cb9afecbcf19b9fa8199569abd66a58`, `Schema: iis-scope/v1`, `Status: ready`.
  - canonical `/home/user01/project/iis-skills/scope-shaper/tools/validate_scope.py --json`은 `status: ready`와 위 Product/Transition Authority 경로 및 digest를 반환했다.
  - Scope의 세 Acceptance는 (1) clean prefix에서 설치/provenance와 `status`/`prepare`/`run --dry-run` 성공, (2) file-bearing exact one ZIP과 normalized member paths 및 file-free zero ZIP, (3) unready slot 또는 invalid args가 child submission 전에 exit code 2로 닫히고 slot을 오염시키지 않는 것이다.
- Transition Authority: `/home/user01/project/oracle/docs/planning/adaptive/maintainable-operational-runtime/BASELINE-001.md`, SHA-256 `6e4d81d83c18d21ec8f1d3e60f671bd2d3db07e0a8699507009e91e953b5d1a9`.
  - 적용 경계는 Block `B4-CLEAN-E2E`, 특히 `GI-05`~`GI-07`, `GI-09`, `GI-11`, `PI-01`~`PI-04`, `PI-08`~`PI-15`, Safe Abort의 evidence preservation이다.
  - 원문은 `Status: DRAFT`, `Approved by: Pending`, `Approval scope: None`, `Inter-Block auto-continuation authorized: no`다. exact Scope가 요구한 read-only Plan 작성 외에 이 Baseline은 external Browser run, promotion 또는 Completion approval 권한을 만들지 않는다.
- Repository investigation artifact: supplied artifact 없음. 아래 current source와 packaging contract를 직접 읽었다.
- Non-Goals: npm publish, production rollout, Windows/macOS installer, B1~B3 의미 재설계, 실제 prompt submission, recovery/concurrency/adversarial matrix 확장은 이 exact Scope 밖이다.

## 2. 달성할 관찰과 보존 조건

1. `/tmp/oracle-b4-clean-e2e-*` 아래에 clean `HOME`, npm prefix, Python venv, state/profile/temp/fixture/evidence directories를 만든다.
2. clean build environment에서 `pnpm pack`으로 npm tarball을 만들고 `pip wheel`로 Python wrapper wheel을 만든다. tarball은 temp npm prefix에, wheel은 temp venv에 설치한다. editable install, source import, `pnpm link`, 개인 global package는 사용하지 않는다.
3. consumer `PATH`는 `<work>/venv/bin:<work>/npm/node_modules/.bin`과 승인된 system directories만 포함한다. `HOME`, `PATH`, resolved `node`, `oracle`, wrapper, Python module path 어디에도 `/home/user01`, 개인 NVM, source checkout이 없어야 한다.
4. installed `oracle --version`, file-selection capability JSON, installed wrapper resolver가 `@steipete/oracle` `0.16.1`, `oracle-file-selection/v1`, 동일 installed entry SHA를 가리켜야 한다.
5. installed wrapper의 `status`, `prepare --slot N`, no-file `run --dry-run`이 순서대로 exit 0이어야 한다. `prepare`가 manual login을 요구하면 환경 전제가 충족되지 않은 것이므로 evidence를 보존하고 `EVIDENCE_NEEDED`로 중단한다.
6. file-bearing `run --dry-run`은 실제 wrapper 경로에서 정확히 한 compressed ZIP을 만들고 child argv에는 원본 파일들 대신 그 ZIP 하나만 전달한다. ZIP member는 fixture cwd 기준 `a.txt`, `nested/b.txt`여야 하며 완료 뒤 ZIP은 정리된다. file-free dry-run은 ZIP을 전혀 만들지 않는다.
7. caller가 `--browser-timeout`을 주지 않은 dry-run의 actual child argv에는 exact one `--browser-timeout 2h`가 있어야 한다. harness가 이 flag를 대신 주입하지 않는다.
8. clean, unprepared slot의 valid `run --dry-run`과 prepared slot의 structurally invalid command는 exit 2여야 한다. 둘 다 stock Oracle child process를 만들지 않고, before/after state에서 occupancy가 생기거나 기존 prepared slot이 변하지 않아야 한다.
9. 모든 command, env, artifact digest, stdout/stderr, process/file trace, lifecycle JSON과 slot before/after를 evidence bundle에 남긴다. 실패 시 evidence를 읽기 전에 `/tmp` tree를 삭제하지 않는다.

## 3. Code Grounding

### EXISTING

1. **npm packed artifact 경계**
   - `package.json:2-3,16-27,35-36,51,56,109-112`는 `@steipete/oracle` `0.16.1`, `oracle -> dist/bin/oracle-cli.js`, 배포 대상 `dist/**/*`, `prepare -> pnpm run build`, Node `>=24`를 선언한다.
   - `scripts/packed-cli-smoke.mjs:17-55`는 이미 temp directory에 `pnpm pack`, npm install, packed CLI help를 실행하지만 alternate HOME/PATH, Python wheel, wrapper lifecycle, ZIP member와 fail-closed state를 관찰하지 않는다.
2. **Python wheel/console entry 경계**
   - `oracle-browser-slots/pyproject.toml:1-15`는 setuptools wheel, Python `>=3.11`, `oracle-browser-slots = oracle_browser_slots.cli:main`을 선언한다.
3. **runtime provenance reader**
   - `oracle-browser-slots/oracle_browser_slots/runtime.py:16-18,25-49`는 package name/version, selector schema와 entry SHA identity를 표현한다.
   - `runtime.py:52-153`은 clean PATH에서 Node `>=24`와 `oracle`을 찾고, owning `package.json`, declared bin, CLI `--version`, `runtime file-selection --capability --json`을 대조한다. 불일치하면 child submission 전에 `OracleRuntimeError`로 닫는다.
4. **wrapper public entry와 exit 의미**
   - `oracle_browser_slots/cli.py:18-51,54-184`는 `prepare`, `status`, `run`, `submit`, `followup`을 노출한다. `prepare`는 slot이 AVAILABLE일 때 0, `status`는 0, run/submit/followup은 runner의 exit code를 반환하고 lifecycle JSON을 stderr에 flush한다.
5. **normalization, timeout, pre-submit 경계**
   - `runner.py:88-215`는 runtime/argv validation → attachment preparation → atomic claim → live pre-submit check → child 순서로 `run`을 수행한다. validation/attachment/claim failure는 exit 2이고 child가 시작되지 않는다.
   - `runner.py:676-807`은 logical `oracle`을 proven installed entry로 치환하고 required browser flags와 omitted default `--browser-timeout 2h`를 terminator 앞에 넣는다. duplicate/empty/invalid timeout과 forbidden transport args는 `OracleTransportError`로 거절한다.
6. **single-ZIP와 normalized member ownership**
   - `attachments.py:357-460`은 file args가 없으면 `None`, 있으면 proven runtime selector로 selected set을 얻어 temp `oracle-attachments.zip` 하나를 만든다.
   - `attachments.py:592-672`는 cwd-relative path를 `/` 구분자로 normalize하고 `.`/`..` segment를 제거하며 collision을 거절한 뒤 ZIP_DEFLATED member로 기록한다.
   - `attachments.py:675-739`는 원본 file args를 제거하고 exact one ZIP `--file`과 attachment policy를 child command에 삽입한다.
   - `attachments.py:279-305`는 request-owned ZIP/temp directory cleanup readback을 반환한다.
7. **fail-closed slot ownership**
   - `service.py:346-367`의 pre-claim rejection은 occupancy를 바꾸지 않는다.
   - `service.py:369-571`은 lock 안에서 slot state와 owner PID/starttime을 확인한다. missing/unprepared/unavailable/occupied slot은 승인하지 않고, owner loss는 `requires_reprepare=True`로 격리하며, 성공 claim만 occupancy를 기록한다.
   - `service.py:573-627`은 finish 시 현재 process identity와 owner를 대조하지 못하면 임의 해제하지 않는다.
8. **현재 harness 자산과 drift**
   - `oracle-browser-slots/scripts/clean_e2e.py`가 이미 clean toolchain, pack/wheel install, provenance, file/no-file dry-run 및 evidence bundle의 대부분을 구현한다.
   - current script의 `scenario3a()`/`scenario3b()`는 이전의 더 넓은 concurrency/duplicate/recovery 계획을 구현한다. exact Scope Scenario 3은 unready slot 또는 invalid args의 exit 2와 no-pollution이므로 이 추가 실행은 현재 acceptance에 필요하지 않다.
   - current file-bearing ZIP capture는 process가 실행되는 동안 5ms polling으로 transient ZIP을 복사한다(`clean_e2e.py:539-613`). scheduler timing에 따라 실제 ZIP이 생성됐어도 관찰을 놓칠 수 있으므로 decisive E2E readback으로는 불안정하다.
9. 계획 시 current fingerprint:
   - `oracle-browser-slots/scripts/clean_e2e.py` `7d854e9e955728162ab94607cd5ec17ce341c2b6a478f2055e327570eaa3b219`
   - `runtime.py` `2236b649bd21d95edfddb6c5057dba57ad541bb6095867268624eb801f49dc1f`
   - `runner.py` `7a147d001eb116882f3250a8c4247d210954e91ed3bbc9eb85ad4a58ad749711`
   - `attachments.py` `8bf6153a4df416d519f0f53f0a10821ffee19a3929726bad5c0819b180babb24`
   - `service.py` `6634bd022eac26cb82853184905c0decdaf4e5e03f1156ec7be76cbc90772157`
   - `cli.py` `5f4034100cd2b9ed5daea196ca686255648167e674e9ddde67c847bb2367c8c5`
   - `package.json` `9fdd86af8557bca025be71011aa8f5440b6c7e8b181c3570da978a2fc4f4ec44`

### PROPOSED

1. `oracle-browser-slots/scripts/clean_e2e.py`를 exact Scope의 하나의 stdlib-only harness로 유지한다. product module을 source checkout에서 import하지 않고 packed/wheel-installed entry만 subprocess로 실행한다.
2. existing preflight/staging/provenance/evidence code를 재사용하고 scenario flow를 다음으로 좁힌다.
   - Scenario 1: clean install → installed identity → `status` → `prepare` → no-file `run --dry-run`.
   - Scenario 2: no-file zero ZIP + file-bearing exact one compressed ZIP/member normalization/cleanup.
   - Scenario 3: unready slot valid command + prepared slot invalid args, 둘 다 exit 2/no child/no state pollution.
3. obsolete `scenario3a` concurrency/duplicate orchestration과 `scenario3b` recovery-seed mutation/CLI options를 이 harness에서 제거한다. 해당 제품 기능을 없애는 것이 아니라 이 exact Scope 실행기에서 out-of-scope remote/state complexity를 제거하는 clean cutover다.
4. transient ZIP은 timing polling 대신 실제 wrapper lifecycle을 이용해 잡는다.
   - file-bearing wrapper를 separate process group으로 시작한다.
   - stderr의 flushed `attachment_prepared` JSON을 관찰하면 process group에 `SIGSTOP`을 보낸다.
   - `<TMPDIR>/oracle-browser-slots-zip-*/oracle-attachments.zip`이 정확히 하나인지 확인하고 evidence dir로 복사해 `zipfile`로 member/compression/SHA를 읽는다.
   - `SIGCONT` 후 same wrapper를 정상 settle하고 cleanup record와 ZIP 부재를 확인한다.
   - `attachment_prepared` 전에 process가 끝나거나 bounded wait 안에 record가 없으면 member proof를 추정하지 않고 실패/EVIDENCE_NEEDED로 닫는다.
5. child invocation은 existing `strace` process trace에서 installed `oracle-cli.js`의 `execve` argv를 읽는다. no-file/file-bearing 각각 child 하나, exact one intrinsic `--browser-timeout 2h`, file-bearing exact one generated ZIP `--file`을 요구한다.
6. Scenario 3은 dedicated unready slot을 사용한다. chosen prepared slot과 다른 slot을 고르며, 실행 전후 `status --slot` JSON과 state file existence/content를 기록한다.
   - unready case: valid no-file dry-run; expected exit 2, `event=rejected`, child `execve` 0, occupancy 없음.
   - invalid case: prepared slot에서 duplicate `--browser-timeout 1h --browser-timeout 2h`; expected exit 2, pre-claim rejection, child `execve` 0, prepared slot state bytes unchanged.
7. evidence bundle은 현재 `summary.json`, `commands.jsonl`, `artifacts.json`, `env.json`, `logs/`, `traces/`, `state-before/`, `state-after/` 구조를 유지한다. 새 report framework나 database를 추가하지 않는다.

### UNRESOLVED

1. **clean system toolchain**: approved system PATH에서 Node >=24, Python >=3.11, npm/pnpm, `strace`, Chrome가 모두 `/home/user01`/NVM 밖에 존재하는지는 이 read-only planning에서 실행하지 않았다. 최소 판별 관찰은 harness preflight의 resolved realpaths와 versions다. 없으면 개인 binary를 복사/symlink하지 않고 `EVIDENCE_NEEDED`로 종료한다. Owner: execution environment owner.
2. **isolated Chrome/login readiness**: clean profile로 `prepare --slot N`이 AVAILABLE까지 갈 수 있는지는 volatile external environment 사실이다. 최소 판별 관찰은 installed wrapper `prepare` exit 0과 `status`의 `status=사용 가능`, `occupancy=null`, `requires_reprepare!=true`다. manual login이 필요하면 work root를 보존하고 operator 환경으로 반환한다. Owner: authorized operator/environment owner.
3. **B3 release candidate correlation**: supplied assignment에는 B3 CI가 검증한 exact candidate digest/handoff가 없다. pack/wheel bytes와 installed provenance는 새 evidence를 만들지만 B3 CI와 같은 candidate라는 최종 correlation은 predecessor handoff 없이는 주장할 수 없다. Owner: preparation lead/B3 handoff owner.
4. **Transition approval**: bound Baseline은 DRAFT/Pending/None이다. Plan 작성은 가능하지만 external Browser effect, promotion 또는 B4 Exit 권한으로 확장하지 않는다. Owner: transition authority owner.

## 4. Harness layout, entry/read paths와 상태 수명

### 4.1 `/tmp` layout와 environment

```text
/tmp/oracle-b4-clean-e2e-*/
  build-home/
  artifacts/npm/*.tgz
  artifacts/python/*.whl
  npm/node_modules/.bin/oracle
  venv/bin/oracle-browser-slots
  home/.oracle/
  slot-state/
  profiles/
  tmp/
  run/{a.txt,nested/b.txt}   # consumer cwd and file-selection fixture root
  evidence/{summary.json,commands.jsonl,artifacts.json,env.json,logs,traces,state-before,state-after}/
```

Build environment는 clean `HOME`, approved system `PATH`, local empty npmrc, `<work>/tmp`만 전달한다. Consumer environment는 다음만 명시한다.

```text
HOME=<work>/home
ORACLE_HOME_DIR=<work>/home/.oracle
ORACLE_BROWSER_SLOTS_STATE_ROOT=<work>/slot-state
ORACLE_BROWSER_SLOTS_PROFILE_ROOT=<work>/profiles
ORACLE_BROWSER_SLOTS_CHROME_PATH=<approved system Chrome>
ORACLE_BROWSER_SLOTS_PORT_BASE=<isolated port base>
TMPDIR=<work>/tmp
PATH=<work>/venv/bin:<work>/npm/node_modules/.bin:<approved system PATH>
LANG=C.UTF-8
LC_ALL=C.UTF-8
```

`NVM_DIR`, `NODE_PATH`, `PYTHONPATH`, user npm config와 caller HOME는 전달하지 않는다. build cwd만 source checkout이며 모든 consumer command cwd는 `<work>/run`이다.

### 4.2 writers/readers와 lifetime

- artifact writers: `pnpm pack`, `python -m pip wheel`; harness는 tarball/wheel SHA-256을 설치 전에 기록하고 bytes를 수정하지 않는다.
- installers: npm temp prefix와 Python venv만 쓴다. installed `oracle`/wrapper paths와 Python module path가 authoritative consumer entry다.
- provenance readers: `oracle --version`, capability JSON, installed venv Python의 `resolve_oracle_runtime()` 결과와 direct entry SHA.
- slot writers: installed `prepare`, `claim_job`, `finish_job`; harness는 slot JSON을 직접 성공 상태로 만들거나 수정하지 않는다.
- ZIP writer: installed wrapper의 `FileAttachmentPolicy`; lifecycle `attachment_prepared`, paused live ZIP, actual child argv, cleanup record가 서로 다른 readback이다.
- failure reader: wrapper exit code, lifecycle JSON, child `execve` count, state file before/after. stdout 문구 하나만으로 no-submission/no-pollution을 주장하지 않는다.
- creation/reset: work root는 한 run에 한 번 새로 생성한다. prior files가 없는 initial snapshot을 먼저 남겨 post-run absence와 구분한다.
- completion: all three scenarios settle, child processes exit, slot occupancy is null or unchanged as expected, evidence files are flushed before cleanup eligibility를 판단한다.

## 5. 구현 순서

1. **current harness를 exact Scope에 맞춘다.** 기존 environment/staging/provenance/evidence helpers를 보존하고 concurrency/duplicate/recovery 전용 code/options를 제거한다.
2. **preflight와 immutable staging을 유지한다.** approved system tools의 realpath/version을 확인한 후 다음 exact commands를 실행한다.

```bash
pnpm pack --pack-destination <work>/artifacts/npm
python3 -m pip wheel --no-deps --wheel-dir <work>/artifacts/python <project>/oracle-browser-slots
python3 -m venv <work>/venv
<work>/venv/bin/python -m pip install --no-index --no-deps <wheel>
npm install --prefix <work>/npm --ignore-scripts --no-audit --no-fund <tgz>
```

3. **Scenario 1 identity와 public commands를 결합한다.** installed entry 존재, version/capability/resolver SHA를 확인하고 `status` exit 0을 기록한다. isolated slot을 `prepare`하고 AVAILABLE readback 뒤 Scenario 2의 no-file dry-run exit 0을 Scenario 1의 마지막 관찰로 공유한다.
4. **Scenario 2 ZIP 관찰을 deterministic lifecycle pause로 바꾼다.** no-file부터 실행해 zero ZIP baseline을 만들고, file-bearing request에서 `attachment_prepared` 직후 pause/copy/inspect/resume/cleanup을 한 process lifetime 안에서 수행한다.
5. **Scenario 3 negative matrix를 추가한다.** unready slot과 prepared-slot invalid args를 각각 한 번 실행하고 exit 2, zero child, state unchanged/no occupancy를 대조한다.
6. **aggregation과 cleanup boundary를 닫는다.** scenario마다 artifact identity, command/exit, child argv, slot/ZIP state를 `summary.json`에 연결한다. PASS일 때도 evidence dir을 먼저 확정하고, FAIL/EVIDENCE_NEEDED이면 work root를 보존한다.

## 6. Exact scenarios와 decisive checks

### 6.1 Scenario 1 — clean installation and provenance

Consumer cwd `<work>/run`, clean env에서 실행한다.

```bash
oracle --version
oracle runtime file-selection --capability --json
oracle-browser-slots status
<venv-python> -c '<installed module path와 resolve_oracle_runtime 결과를 JSON 출력>'
oracle-browser-slots prepare --slot <N>
oracle-browser-slots status --slot <N>
```

그 다음 §6.2 no-file command를 실행한다.

필수 판정:

- npm tarball/wheel이 각각 exact one이고 SHA-256이 기록됨.
- version exact `0.16.1`; capability `ok=true`, `schema=oracle-file-selection/v1`, package name/version 일치.
- installed Python module은 venv 아래, `oracle_entry`/`package_root`는 npm prefix 아래, resolved Node는 approved system Node다.
- resolver/capability/direct file SHA가 같은 installed entry를 가리킴.
- `status`, `prepare`, prepared `status`, no-file dry-run 모두 exit 0.
- trace/env/resolved paths에 `/home/user01`, NVM, source checkout 접근이 없음.

### 6.2 Scenario 2 — file-free zero ZIP and file-bearing single ZIP

No-file:

```bash
oracle-browser-slots run --slot <N> --job-id b4-nofile-<nonce> -- \
  oracle --engine browser --browser-model-strategy current \
  --dry-run summary -p 'B4 clean no-file <nonce>'
```

File-bearing:

```bash
oracle-browser-slots run --slot <N> --job-id b4-files-<nonce> -- \
  oracle --engine browser --browser-model-strategy current \
  --dry-run summary --files-report -p 'B4 clean files <nonce>' \
  --file a.txt \
  --file nested
```

Consumer cwd가 `<work>/run`이므로 installed selector가 반환하는 cwd-relative paths와 ZIP members는 exact `a.txt`, `nested/b.txt`다. Harness는 이 실제 ZIP member list를 읽으며 source helper의 예상값으로 대체하지 않는다.

필수 판정:

- both exit 0, both actual installed child `execve` exactly one.
- both child argv에 caller injection 없이 exact one `--browser-timeout 2h`.
- no-file: `attachment_prepared` 0회, initial/final temp tree와 trace에 ZIP 생성 0회.
- file-bearing: `attachment_prepared` 정확히 1회, paused temp tree에 `oracle-attachments.zip` 정확히 1개, valid ZIP_DEFLATED, member exactly `a.txt`, `nested/b.txt`, duplicate/absolute/`..` member 없음.
- child argv에는 original multiple `--file` 대신 generated ZIP `--file` exactly one.
- resume/settle 뒤 `generated_zip_cleanup.removed=true`, request-owned ZIP/temp directory 없음, slot occupancy null.

### 6.3 Scenario 3 — unready/invalid fail-closed without pollution

Unready case는 prepared `<N>`과 다른 `<U>`를 사용한다.

```bash
oracle-browser-slots status --slot <U>
oracle-browser-slots run --slot <U> --job-id b4-unready-<nonce> -- \
  oracle --engine browser --browser-model-strategy current \
  --dry-run summary -p 'B4 unready <nonce>'
oracle-browser-slots status --slot <U>
```

Invalid case는 prepared `<N>`에서 실행한다.

```bash
oracle-browser-slots status --slot <N>
oracle-browser-slots run --slot <N> --job-id b4-invalid-<nonce> -- \
  oracle --engine browser --browser-model-strategy current \
  --browser-timeout 1h --browser-timeout 2h \
  --dry-run summary -p 'B4 invalid <nonce>'
oracle-browser-slots status --slot <N>
```

필수 판정:

- both run exit code exactly 2 and lifecycle `event=rejected`.
- unready reason/state가 prepared 성공으로 변하지 않고 before/after occupancy 없음.
- invalid case는 pre-claim rejection이며 prepared slot state bytes/status/occupancy가 unchanged.
- both traces에서 installed `oracle-cli.js` child `execve` 0회; remote prompt/session artifact 증가 없음.
- harness 자체 exit는 scenario failure를 0으로 덮지 않는다.

## 7. Partial failure, interruption, resumption과 cleanup

| 경계 | 판별 readback | 처리 |
| --- | --- | --- |
| clean tool missing/personal path | tool realpath/version/env | pack 전에 `EVIDENCE_NEEDED`; copy/symlink/global fallback 금지. |
| pack/wheel/install failure | command logs, partial artifact SHA | downstream command 금지; source를 harness에서 patch하지 않음. |
| installed provenance mismatch | package metadata, capability, resolver/entry SHA | slot preparation 전 FAIL; same-version 추정 금지. |
| login/CDP unavailable | prepare/status JSON, profile/state paths | `EVIDENCE_NEEDED`; manual login은 environment owner, 기존 personal profile mount 금지. |
| ZIP lifecycle pause 실패 | stderr records, process state, temp tree | member proof를 추정하지 않고 process를 안전하게 settle/terminate한 뒤 evidence 보존. |
| ZIP/member mismatch | live ZIP copy, lifecycle selected set, child argv | FAIL; alternate source helper 결과로 대체하지 않음. |
| unready/invalid child spawn | trace execve, slot before/after | FAIL 및 신규 scenario 중단; slot/session evidence 보존. |
| operator interrupt | live PIDs, slot state, artifacts | child/process group을 bounded terminate하고 evidence/state를 보존; 자동 rerun 금지. |
| cleanup/release 불명 | terminal lifecycle, temp tree, slot status | 정상 완료로 발표하지 않고 work root 보존; owner 불명 slot을 수동 삭제하지 않음. |

Resume가 필요하면 existing `--resume <work-root>`는 tarball/wheel/installed entry SHA와 state를 다시 읽고 같을 때만 이어간다. artifact가 바뀌었으면 새 run이며 이전 scenario evidence와 합성하지 않는다.

## 8. 구현자 자체 점검과 verifier handoff

### 8.1 좁은 smoke

Project-wide formatter/lint/test는 integration owner가 한 번 수행한다. 구현자는 실제 harness를 단계별로 실행한다.

```bash
python3 oracle-browser-slots/scripts/clean_e2e.py --preflight-only
python3 oracle-browser-slots/scripts/clean_e2e.py --stage-only
python3 oracle-browser-slots/scripts/clean_e2e.py --work-root /tmp/oracle-b4-clean-e2e-<nonce>
```

- `--preflight-only`: personal/NVM path가 system PATH에 들어오면 pack 전에 nonzero.
- `--stage-only`: exact tarball/wheel, isolated install, installed provenance까지 완료.
- full run: three Scope scenarios only; no prompt submission, no recovery seed requirement, no concurrency holder.

### 8.2 Minimum acceptance/readback

Verifier handoff에는 다음 current evidence를 포함한다.

- exact Thesis/Scope/Transition hashes와 Plan hash.
- npm tgz/wheel SHA, installed package metadata와 actual entry SHA.
- clean HOME/PATH/tool/module/executable readback 및 zero denied-path trace.
- `status`/`prepare`/no-file dry-run exit 0와 prepared slot state.
- no-file zero ZIP; file-bearing one ZIP, selected files, actual member list/compression/SHA, normalized child argv, cleanup.
- unready/invalid exit 2, lifecycle rejection, zero child exec, before/after state.
- final process settlement, slot occupancy와 preserved evidence path.

Harness PASS는 이 exact Scope의 verifier 입력이지 B4 Exit 또는 Transformation Completion 판정이 아니다. 실제 prompt/response, recovery, concurrency 등 Baseline 전체 completion matrix는 이 narrower Scope Acceptance를 넘어서는 별도 authorized evidence로 남는다.

## 9. Conditional first-work bundles

### C0 — transition/candidate admission

- `plan_anchor`: §1 Transition Authority, §3 UNRESOLVED 3/4.
- `permitted_initial_work`: Plan/independent review, B3 candidate handoff 및 transition approval의 read-only inspection, local harness edit.
- `discriminating_observation`: owning authority가 이 Scope 실행 범위를 허용하고 B3 handoff가 pack할 exact source/candidate identity를 제공함.
- `dependent_work_not_yet_permitted`: Chrome/profile interaction, release promotion, B4 Exit/Completion 주장.
- `response_if_refuted`: execution을 시작하지 않고 preparation lead/B3 handoff owner/transition authority owner에게 반환한다.

### C1 — clean toolchain and staging

- `plan_anchor`: §3 UNRESOLVED 1, §4.1, §5 steps 2-3.
- `permitted_initial_work`: `/tmp` work root 생성, clean PATH preflight, pack/wheel/install, installed provenance readback.
- `discriminating_observation`: approved tool realpaths가 denylist 밖이고 Node/Python versions 충족; installed module/entries가 temp prefix/venv 아래이며 identity/SHA가 일치함.
- `dependent_work_not_yet_permitted`: `prepare`, run dry-run, Scenario PASS 주장.
- `response_if_refuted`: staging 중단; personal tool copy/symlink/global fallback 없이 environment owner 및 Plan owner에게 반환한다.

### C2 — isolated prepared slot

- `plan_anchor`: §3 UNRESOLVED 2, §5 step 3, §6.1.
- `permitted_initial_work`: exact staged artifact와 isolated state/profile로 `status`, `prepare`, prepared `status` 실행.
- `discriminating_observation`: prepare exit 0; selected slot AVAILABLE, occupancy null, `requires_reprepare!=true`; paths 모두 work root 아래.
- `dependent_work_not_yet_permitted`: no-file/file-bearing dry-run과 negative scenario.
- `response_if_refuted`: work root/evidence 보존 후 `EVIDENCE_NEEDED`; 인증 우회, personal profile mount, slot JSON 수동 수정 금지.

### C3 — installed dry-run and ZIP boundary

- `plan_anchor`: §5 step 4, §6.2.
- `permitted_initial_work`: prepared slot에서 no-file와 file-bearing non-submitting dry-run, lifecycle pause/copy/inspect/resume.
- `discriminating_observation`: both exit 0/intrinsic 2h; file-free zero ZIP; file-bearing exact one compressed ZIP with expected normalized members, one child `--file`, cleanup true.
- `dependent_work_not_yet_permitted`: Scenario 2 PASS aggregation, negative lifecycle scenario, cleanup deletion.
- `response_if_refuted`: 신규 run 중단, process/slot/ZIP/trace evidence 보존; ZIP observation method나 runtime ownership 변경이 필요하면 Plan revision/fresh review로 반환한다.

### C4 — fail-closed negative lifecycle

- `plan_anchor`: §5 step 5, §6.3.
- `permitted_initial_work`: dedicated unready slot valid dry-run과 prepared slot duplicate-timeout invalid dry-run.
- `discriminating_observation`: both exit 2/rejected, zero Oracle child, unready occupancy absent, prepared state unchanged.
- `dependent_work_not_yet_permitted`: full PASS, temp cleanup, B4 Exit/Completion 주장.
- `response_if_refuted`: 신규 run 중단, state/process/session traces 보존; guard/slot ownership defect는 implementer/Plan owner로, Acceptance 의미 변경 필요는 Scope/Thesis owner로 반환한다.

## 10. 구현 재량과 재검토 경계

- implementer 재량: private helper 이름, nonce 형식, bounded polling interval, evidence JSON key ordering, prepared/unready slot pair 선택, equivalent process-group settle mechanics.
- 새 telemetry, database, container abstraction, test-only product hook, retry daemon, personal path fallback, synthetic success fixture를 추가하지 않는다.
- material method 변경: packed/wheel artifact 대신 source/editable 실행, clean PATH policy, provenance identity 방식, live ZIP readback을 source helper assertion으로 대체, negative case/exit semantics, state pollution readback, failure cleanup policy. 해당 work를 멈추고 Plan 개정과 fresh independent review가 필요하다.
- promised meaning/Acceptance나 transition geography 변경은 Main과 owning Scope/Thesis/Transition authority로 반환한다.
- independent Plan Reviewer가 `ADMIT/REVISE/EVIDENCE_NEEDED`를 소유한다. Plan 파일/hash는 admission, 구현 완료, verification verdict 또는 B4 Exit를 뜻하지 않는다.
