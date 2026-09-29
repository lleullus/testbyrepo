---
tags:
  - OMP
  - Oh-My-Pi
  - extension
  - omp-ballast
  - 업데이트
  - 운영-런북
status: 적용
created: 2026-08-15
updated: 2026-09-04
---

# OMP 사용자 extension omp-ballast 운영 및 업데이트 유지 런북

## 현재 결론

`omp-ballast` extension 자체는 향후 다른 조건부 지침과 tool guard에 사용할 수 있도록 활성 상태로 유지한다. Subagent·IRC governance는 조건부화하지 않고 원래처럼 `~/.omp/agent/RULES.md`에 전체 내용을 상시 로드한다.

현재 구조:

```text
~/.omp/agent/RULES.md
  └─ 전체 subagent·IRC governance, always-on

~/.omp/agent/extensions/omp-ballast/
  └─ 원본 omp-ballast 0.1.0, 자동 탐색 활성

~/.omp/agent/ballast.rules.json
  └─ rules: [happy-search-research-synthesis]

~/.omp/agent/ballast/happy-search-research.md
  └─ Happy Search 계열 도구에만 조건부 주입하는 조사·종합 지침

~/.omp/agent/ballast/subagent-governance.md
  └─ 과거 조건부화 사본, 현재 어떤 rule에서도 참조하지 않음
```

> [!IMPORTANT]
> 현재 subagent governance는 Ballast가 전달하지 않는다. OMP의 기본 사용자 `RULES.md`가 부모와 자식 세션에 항상 제공한다. Ballast는 Happy Search 조사·종합 규칙을 조건부로 제공한다.

## 2026-09-16 request-first-execution 규칙 제거

- 프롬프트 레벨의 상시 주입 지침이 OMP 베이스 프롬프트(§ Workflow)와의 충돌 및 모델의 예외 조항 자의적 해석(연쇄 조사 합리화)으로 실효성이 없고 혼선을 초래하여, 사용자 요청에 따라 `request-first-execution` 규칙을 완전히 제거했다.
- 제거 후 상태: `ballast.rules.json`의 effective rule은 `happy-search-research-synthesis` 1개로 복원.
- 백업: `~/.omp/agent/manual-backups/request-first-remove-20260916T002238Z/ballast.rules.json`.

## 2026-09-16 request-first-execution 간결·강제형 재작성

- 기존 구술형 한국어 서술이 OMP 베이스의 RFC 2119(`MUST`, `§ Workflow`) 지침과 충돌할 때 후순위로 밀리는 문제를 해결하기 위해 지침을 간결한 영어 OVERRIDE 계약으로 전면 재작성했다.
- 변경 내용: `§ Workflow`, `skill-first`, `research-first`, `todo-init`에 대한 명시적 `supersedes` 선언 추가, `MUST NOT read skills/files, research, plan, or initialize todos first` 행동 금지 명시, 선행 확인 조건 격상(생략 시 실행 차단/결과 변동인 경우만).
- 백업: `~/.omp/agent/manual-backups/request-first-20260916T000234Z/ballast.rules.json`.

## 2026-09-15 요청 수행 우선 규칙 등록

- 사용자 승인으로 `request-first-execution`을 user rules에 등록했다. 짧은 지침은 `instruction`에 보관하며 `RULES.md`는 변경하지 않았다.
- `read`, `grep`, `glob`, `web_search`, `edit`, `write`, `bash`, `eval`, `task`, `hub`, `todo` 중 첫 호출에서 지침을 전달한다. 프롬프트 매칭은 없고, 동일 실행에서는 한 번만 발동하며 `before_agent_start`에서 초기화한다. IIS 전용 제외 조건은 없다.
- 현재 Main 세션에서 실제 `read` 호출이 지침 전달로 중단되고 같은 호출의 재시도가 성공했다. 재시작 없이 설정이 반영됐다.
- 실제 extension 핸들러를 메모리 수신기에 연결해 status의 effective rules 2개, 일반 프롬프트 비매칭, Happy Search 기존 매칭, 독립 인스턴스 두 개의 첫 호출 발동·재시도 통과, 다음 요청 초기화, `ask` 비발동을 확인했다. 실제 서브에이전트 모델 실행 시험은 하지 않았다.
- 백업: `~/.omp/agent/manual-backups/request-first-20260915T093218823924Z/ballast.rules.json`. 롤백은 현재 설정에서 이 규칙만 제거한다. 이후 변경이 없다면 해당 백업으로 복원할 수 있다.

## 2026-09-15 구형 IIS 알림 제거

사용자 요청에 따라 `ready-ticket-verify-triage-reminder` 규칙을 제거했다. 이 규칙은 퇴역한 `iis-ready-verifier/v1`, Adaptive 문서와 호스트 전용 완료 도구를 참조했다. 새 IIS 규칙이나 대체 실행 엔진은 추가하지 않았다. Ballast extension과 기존 `happy-search-research-synthesis` 규칙은 유지한다.

- 변경 전 원본: `/home/user01/tmp/iis-host-independent-20260914T235153Z/ballast.rules.json`.
- 실제 extension의 동일 인스턴스 명령/도구 핸들러로 설정 재로딩을 확인: effective rules 2 → 1, 구형 호출 알림 비활성, Happy Search prompt/tool activation 유지, 일반 요청 미매칭.
- 핸들러 검증은 메모리 보고 수신기를 사용했으며 실제 차단 대상 도구나 모델은 실행하지 않았다. 새 OMP 프로세스의 `/ballast status`는 exit 0이지만 JSON 모드가 custom report 본문을 출력하지 않아 본문 readback으로 주장하지 않는다.
- 기존 OMP 세션이나 Ballast 코드는 재시작·교체하지 않았다. 과거 버전 검증 기록은 아래에 역사로 보존한다.

## 제품 경계와 설치 상태

| 항목 | 현재 값 |
| --- | --- |
| Client | OMP (`omp`) |
| 기준 OMP 버전 | `18.1.8` |
| Extension 경로 | `~/.omp/agent/extensions/omp-ballast/` |
| Ballast 버전 | `0.1.0` |
| 설치 방식 | direct user extension |
| Plugin registry | 미등록 |
| 사용자 rules | `~/.omp/agent/ballast.rules.json` |
| Effective Ballast rules | `2` (`request-first-execution`, `happy-search-research-synthesis`) |
| Always-on governance | `~/.omp/agent/RULES.md` |
| 제품 구분 지침 | `~/.omp/agent/APPEND_SYSTEM.md` |

OpenCode의 `~/.config/opencode/opencode.json`과 OpenCodex의 `ocx`·`127.0.0.1:10100`은 이 설정의 소유자가 아니다.

## 2026-08-16 OMP 17.3.5 업데이트 확인

OMP를 `17.3.4 -> 17.3.5`로 공식 업데이트한 뒤에도 `omp-ballast`는 user extension 경로에 그대로 남았다. 확인 결과 extension package version은 `0.1.0`, `package.json#omp.extensions`는 `./index.js`, `ballast.rules.json`의 effective rule 수는 계속 `0`이다.

따라서 이 extension은 OMP global package 교체로 재패치할 대상이 아니다. OMP 본체 `dist/cli.js`에 직접 들어간 로컬 패치와 달리 `~/.omp/agent/extensions/omp-ballast/`는 별도 사용자 소유 artifact로 유지된다.

`omp plugin list --json`에는 Ballast가 나타나지 않는다. OMP가 사용자 extension 디렉터리의 `package.json#omp.extensions`를 자동 탐색해 `index.js`를 로드한다.

## 2026-08-19 OMP 17.3.8 업데이트 확인

OMP를 `17.3.5 -> 17.3.8`로 공식 업데이트한 뒤에도 Ballast 사용자 artifact와 governance 파일은 그대로 유지됐다. 업데이트 전 백업은 `~/.omp/agent/manual-backups/omp-before-17.3.8-20260819T121758Z/`에 보존했다.

업데이트 후 checksum은 업데이트 전 기준과 모두 일치했다.

| 파일 | SHA-256 |
| --- | --- |
| `extensions/omp-ballast/index.js` | `2969f0905d17fe8a133a7a19c10b5d96278115c7b6980b82075180788ce019f6` |
| `ballast.rules.json` | `8772df49af2416bdf2f4881dd6f70452b3a0a8c31cf93f4aa1d7cb40ba0537a4` |
| `RULES.md` | `13d10f9520681838fee159d74d5ad35682eb984724e554224521222087e071ef` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |

새 `omp/17.3.8` 프로세스를 실제 PTY로 실행해 `/ballast status`를 호출한 결과:

```text
omp-ballast 0.1.0
User rules: /home/user01/.omp/agent/ballast.rules.json
Project rules: (none)
Effective rules: 0
```

추가 검증으로 extension 자체 `node --test tests/*.test.mjs`는 `10 pass, 0 fail`, `bun run check` syntax 검사는 통과했다. 따라서 17.3.8에서도 Ballast는 direct user extension으로 자동 탐색되며 별도 재설치·재패치가 필요하지 않다. 17.3.8 upstream에는 revived subagent가 extension runtime을 초기화하지 못하던 문제의 수정도 포함되어 있어, 현재 Ballast 운영 경계와 충돌하는 새 변경은 확인되지 않았다.

## 2026-08-20 OMP 17.4.0 업데이트 확인

OMP를 `17.3.8 -> 17.4.0`으로 공식 업데이트하고 combined core patch를 재설치한 뒤에도 Ballast는 별도 user extension artifact로 그대로 유지됐다. 업데이트 전 운영 상태는 다음에 보존했다.

```text
~/.omp/agent/manual-backups/omp-before-17.4.0-20260820T175053+0900/
```

17.4 업데이트 후 Ballast와 governance checksum은 업데이트 전 17.3.8 기준과 모두 동일했다.

| 파일 | SHA-256 |
| --- | --- |
| `extensions/omp-ballast/index.js` | `2969f0905d17fe8a133a7a19c10b5d96278115c7b6980b82075180788ce019f6` |
| `ballast.rules.json` | `8772df49af2416bdf2f4881dd6f70452b3a0a8c31cf93f4aa1d7cb40ba0537a4` |
| `RULES.md` | `13d10f9520681838fee159d74d5ad35682eb984724e554224521222087e071ef` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |

Extension 자체 `npm test`는 `10 pass, 0 fail`, `npm run check` syntax 검사는 통과했다. 17.4 extension loader/API 변경도 정적 검토했으며 Ballast가 사용하는 `logger`, `before_agent_start`, `input`, `tool_call`, `registerCommand`, `sendMessage` 계약은 유지됐다. 새 `omp/17.4.0` TUI를 PTY에서 시작했을 때 extension load 오류 없이 기동했다.

이번 PTY 실행에서는 splash 이후 `/ballast status`의 텍스트 결과를 안정적으로 캡처하지 못했으므로 그 출력 자체를 재검증했다고 기록하지 않는다. 다만 extension 파일 보존, API 계약 유지, 자체 테스트/문법 검사, 새 TUI loader 기동까지는 확인됐다. 다음 정상 interactive 세션에서 `/ballast status`를 실행하면 기존 정상 기준인 `omp-ballast 0.1.0`, effective rule `0`을 확인하면 된다.

17.4에서도 일반 `omp update`가 Ballast를 재패치할 이유는 없다. Ballast는 계속 `~/.omp/agent/extensions/omp-ballast/`의 direct user extension으로 관리하고, core patch는 별도 `local-patches` 런북에서 관리한다.

## 2026-08-22 activateOnTools 인자 패턴 매칭 확장 및 IIS 가드레일 등록

에이전트가 특정 스킬(예: `skill://ready-ticket-implement`, `skill://ready-ticket-verify`)을 로드할 때(도구 호출 `read`) 1회 가로채어 메인 에이전트 전용 오케스트레이션 수칙을 동적으로 주입하고 재시도하도록 `activateOnTools`에 인자 매칭(`patterns`, `keywords`) 지원을 추가했다.

1. `src/core.js`: `normalizeToolActivator` 추가 및 `findToolActivation`에 `input` 인자 패턴 매칭 확장.
2. `index.js`: `tool_call` 이벤트 핸들러에서 `event.input`을 `findToolActivation`에 전달, `formatRule`의 activation 표시 지원.
3. `ballast.rules.schema.json`: `toolActivator` 객체 정의 및 `activateOnTools` 스키마 업데이트.
4. `~/.omp/agent/ballast.rules.json`: `iis-ticket-implement-guard`, `iis-ticket-verify-guard` 2개 룰 등록.
5. 테스트: `npm test` 12 pass / 0 fail, `npm run check` syntax 통과.

## 2026-08-22 OMP 17.4.2 업데이트 전 Ballast 기준점 — 미적용

OMP `17.4.2` 업데이트 준비 시점의 Ballast/governance 상태를 새 기준으로 고정한다. 17.4.0 업데이트 기록의 checksum은 당시 역사값이며, 오늘 `activateOnTools` 확장과 2개 IIS guard 등록으로 `index.js`와 `ballast.rules.json`이 의도적으로 변경됐다.

| 파일 | 업데이트 전 SHA-256 |
| --- | --- |
| `extensions/omp-ballast/index.js` | `040667aa8a00c73fe8f9c278389722b49e56a5fa9684b5173250e9423f9a1d70` |
| `ballast.rules.json` | `9682c31994bb4e166ade2908f6a34bbd134aaac48afac0ad40fd099fd73bc76f` |
| `RULES.md` | `13d10f9520681838fee159d74d5ad35682eb984724e554224521222087e071ef` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |

현재 `ballast.rules.json`은 version `1`, effective user rule `2`개이며 ID는 `iis-ticket-implement-guard`, `iis-ticket-verify-guard`다. Extension 자체 `npm test`는 `12 pass / 0 fail`로 다시 통과했다.

OMP `17.4.2` source 사전 검토에서 `before_agent_start` event는 유지되고 extension surface에는 `isProjectTrusted()` 등 capability가 추가됐지만 Ballast가 현재 사용하는 기존 event/API 제거는 확인되지 않았다. 따라서 실제 업데이트 전에는 Ballast 코드를 17.4.2용으로 선제 변경하지 않는다.

실제 `omp update` 직전에는 위 네 파일을 timestamp backup으로 다시 복사하고, 업데이트 후 새 TUI에서 `/ballast status`와 implement/verify guard의 positive/negative activation을 확인한다. checksum이 달라졌다면 자동 복원하지 않고 OMP update가 파일을 바꾼 것인지 사용자 후속 변경인지 먼저 구분한다.

현재 단계는 **17.4.2 호환성 사전 검토 및 기준 checksum 확보 완료, 실제 OMP는 17.4.0 유지**다.

## 2026-08-22 OMP 17.4.2 업데이트 후 Ballast 검증 — 적용 완료

OMP 본체를 실제 `17.4.2`로 업데이트한 뒤 Ballast/governance 사용자 artifact가 그대로 유지됐는지 다시 확인했다. 업데이트 전에는 다음 경로에 전체 기준을 보존했다.

```text
~/.omp/agent/manual-backups/omp-before-17.4.2-20260822T120142+0900/
```

업데이트 후 checksum은 업데이트 직전 기준과 **모두 동일**했다.

| 파일 | 17.4.2 업데이트 후 SHA-256 |
| --- | --- |
| `extensions/omp-ballast/index.js` | `040667aa8a00c73fe8f9c278389722b49e56a5fa9684b5173250e9423f9a1d70` |
| `ballast.rules.json` | `9682c31994bb4e166ade2908f6a34bbd134aaac48afac0ad40fd099fd73bc76f` |
| `RULES.md` | `13d10f9520681838fee159d74d5ad35682eb984724e554224521222087e071ef` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |

현재 user rules는 version `1`, effective rule `2`개이며 `iis-ticket-implement-guard`, `iis-ticket-verify-guard`를 유지한다. Extension 자체 `npm test`를 업데이트 후 다시 실행해 `12 pass / 0 fail`을 확인했다.

새 OMP `17.4.2` process `pid 2311498`의 startup log에도 다음 등록이 확인됐다.

```text
omp-ballast extension registered
version: 0.1.0
agentDir: /home/user01/.omp/agent
```

별도의 17.4.2 전용 Ballast 재설치나 source 수정은 필요하지 않았다. `omp -p --no-session --max-time 30s "/ballast status"`도 exit `0`으로 처리됐으며, print mode에서는 extension의 custom UI message를 stdout으로 노출하지 않으므로 상태 본문을 캡처했다고 기록하지 않는다. loader 등록 여부는 startup log를 권위 있는 readback으로 사용한다.

또한 새 17.4.2 saved smoke turn이 정상 종료되고 그 session을 ompweb 0.3.5가 읽은 것을 확인했으므로 OMP 업데이트가 user extension/session lifecycle을 깨뜨리지는 않았다.

최종 판정: **Ballast는 OMP 17.4.2에서도 direct user extension으로 정상 유지되며, 업데이트 후 별도 재패치가 필요하지 않다. 현재 기준은 effective rule 2개와 위 checksum이다.**

## 왜 단순 구조로 복원했는가

기존 296줄 `RULES.md`는 약 17.9KB지만, 이것이 실제 context overflow, 품질 저하, 유의미한 지연 또는 비용 문제를 일으켰다는 측정은 없었다.

조건부화 과정에서는 다음 운영 복잡도가 추가됐다.

```text
prompt trigger 판정
→ 부모 system prompt 조건부 주입
→ implicit task 첫 차단
→ 부모 재시도
→ 자식 task prompt 보강 local patch
→ 자식 system prompt 재주입
```

절감 효과의 절대 크기를 확인하기 전에 상대적인 95% 파일 축소율을 기준으로 최적화한 것이 문제였다. Subagent governance는 원래 전역 지침으로 잘 동작했으므로 `RULES.md`에 복원했다.

Ballast는 다른 조건부 지침과 실제 tool guard에 여전히 가치가 있으므로 extension은 제거하지 않았다.

## 평상시 사용법

현재 Ballast에는 IIS implement/verify guard 2개와 Happy Search 조사·종합 rule 1개가 활성화되어 있지만 각 스킬·도구·프롬프트 조건에서만 동작하므로, 평상시 OMP 사용에는 별도 수동 조작이 필요 없다.

상태 확인:

```text
/ballast status
```

정상 결과:

```text
omp-ballast 0.1.0
User rules: /home/user01/.omp/agent/ballast.rules.json
Effective rules: 3
```

Subagent governance는 `/ballast status`에 나오지 않는 것이 정상이다. `RULES.md`에서 상시 로드되기 때문이다.

## 향후 다른 조건부 지침 추가

새 지침을 등록하기 전에 `$omp-ballast` skill을 읽고 가장 좁은 범위를 선택한다.

판단 기준:

| 목적 | 저장 위치 |
| --- | --- |
| 현재 대화에서만 필요 | 영구 저장하지 않음 |
| 모든 OMP 요청에 반드시 필요 | `~/.omp/agent/RULES.md` |
| 불변 제품·설정 경계 | `~/.omp/agent/APPEND_SYSTEM.md` |
| 특정 사용자 prompt에서만 필요 | `~/.omp/agent/ballast.rules.json` |
| 특정 프로젝트에서만 필요 | `<project>/.omp/ballast.rules.json` |
| 긴 조건부 지침 | 별도 Markdown + `instructionFile` |
| 실제 tool 실행 차단 | Ballast `toolRules` + OMP approval + sandbox |
| 반복 가능한 사용 절차 | `~/.codex/skills/<name>/SKILL.md` |
| 사람이 읽는 운영 이력 | Obsidian 런북 |

짧은 사용자 rule 예시:

```text
/ballast pin user evidence-check | 조사, 검증 | 수치와 실질적 주장에는 출처와 기준 시점을 표시한다.
```

프로젝트 rule 예시:

```text
/ballast pin project test-policy | 테스트, test | 이 프로젝트에서는 bun test만 사용한다.
```

검증:

```text
/ballast status
/ballast test 조사해줘
/ballast test 이 함수 설명해줘
```

Positive prompt는 예상 rule이 매칭되고 negative prompt는 매칭되지 않아야 한다.

## 운영 원칙

- 의미 추론을 기대하지 않고 좁은 keyword 또는 JavaScript regex를 사용한다.
- 프로젝트 rule은 신뢰된 저장소에서만 허용한다.
- 사용자와 프로젝트에 같은 `id`가 있으면 프로젝트 rule이 이긴다.
- 긴 지침은 JSON에 복제하지 않고 `instructionFile`로 분리한다.
- `promptAction: block`만 실제 보안 경계로 사용하지 않는다.
- 위험 행동은 `toolRules`, OMP approval, sandbox를 함께 사용한다.
- 같은 의미의 지침을 `RULES.md`, Ballast, skill에 중복 등록하지 않는다.
- 변경 전에는 대상 파일을 별도 timestamp 디렉터리에 백업한다.
- `config.yml`의 동시 변경은 자동 복원하지 않고 diff를 먼저 확인한다.

## OMP 업데이트 후 유지

현재 OMP updater는 전역 Bun/npm package 또는 standalone binary를 교체한다. 사용자 상태인 다음 경로는 일반적인 업데이트 후 유지된다.

```text
~/.omp/agent/extensions/omp-ballast/
~/.omp/agent/ballast.rules.json
~/.omp/agent/RULES.md
~/.omp/agent/APPEND_SYSTEM.md
```

파일 유지와 extension API 호환성은 별개다. OMP 업데이트 후 새 세션에서 확인한다.

```text
/ballast status
```

정상 기준:

```text
omp-ballast 0.1.0
Effective rules: 2
```

`omp update --plugins`는 direct user extension인 Ballast를 관리하지 않는다.

## 복원 및 백업 기록

전체 subagent governance 원본:

```text
~/.omp/agent/RULES.md.ballast-backup-2026-08-15T15-08-24-566Z
```

원본과 현재 `RULES.md`의 SHA-256:

```text
13d10f9520681838fee159d74d5ad35682eb984724e554224521222087e071ef
```

`0.1.1-local.1` task prompt propagation 패치는 단순 구조 복원 시 제거했다. 제거 직전 상태는 다음에 보존했다.

```text
~/.omp/agent/manual-backups/omp-ballast-before-simple-rollback-20260815T170855Z/
```

원본 `0.1.0` 복원에 사용한 백업:

```text
~/.omp/agent/manual-backups/omp-ballast-task-propagation-20260815T164524Z/omp-ballast/
```

## 현재 checksum 기준

| 파일 | SHA-256 |
| --- | --- |
| `extensions/omp-ballast/index.js` | `040667aa8a00c73fe8f9c278389722b49e56a5fa9684b5173250e9423f9a1d70` |
| `extensions/omp-ballast/src/core.js` | `8748ce99c89933d44e85eb088ea3173fede8a271bd9b113b94cdd38063540674` |
| `ballast.rules.json` | `5428659d65545a76764eaf35ce98ca19f459a192f5b8e0269d5b9fda1484f734` |
| `RULES.md` | `13d10f9520681838fee159d74d5ad35682eb984724e554224521222087e071ef` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |
## 검증 결과

| 항목 | 결과 |
| --- | --- |
| Ballast package | `0.1.0` 유지, OMP `17.4.0` loader 기동 확인 |
| Ballast tests | 12 pass, 0 fail |
| Syntax check | 통과 |
| `RULES.md` | 원본 SHA-256 일치 |
| Ballast extension 로딩 | 17.4 TUI에서 load 오류 없음; `/ballast status` 텍스트 재캡처는 다음 정상 세션에서 확인 |
| Effective Ballast rules | `2` (`iis-ticket-implement-guard`, `iis-ticket-verify-guard`) |
| Ballast extension 상태 | 활성, IIS 스킬 로드 가드레일 정상 동작 |
| `APPEND_SYSTEM.md` | 변경하지 않음 |

## 최종 운영 계약

1. Subagent·IRC governance는 `RULES.md`에 상시 유지한다.
2. Ballast로 subagent governance를 다시 조건부화하지 않는다.
3. Ballast는 향후 다른 조건부 prompt rule과 tool guard에 사용한다.
4. 새로운 전역·조건부 지침은 `$omp-ballast` skill로 배치 위치를 먼저 판단한다.
5. 측정된 문제가 없으면 단순한 전역 지침을 성급하게 조건부 engine으로 바꾸지 않는다.

## 2026-08-22 OMP 18.0.0 업데이트 후 검증 — 적용 완료

OMP core를 `17.4.2 -> 18.0.0`으로 전환한 뒤 Ballast와 governance 사용자 artifact를 다시 검증했다. 업데이트 직전 전체 기준은 다음 경로에 보존했다.

```text
~/.omp/agent/manual-backups/omp-before-18.0.0-20260822T214610+0900/
```

18.0.0 official updater가 package-manager launcher를 standalone binary로 바꿨지만 `~/.omp/agent/` 사용자 artifact는 건드리지 않았다. 업데이트 전후 SHA-256은 다음과 같이 동일했다.

| 파일 | OMP 18.0.0 전환 후 SHA-256 |
| --- | --- |
| `config.yml` | `b2c11652e4cdffba774729638e024cf8ad11dfac009efa22aa519d6b59707731` |
| `extensions/omp-ballast/index.js` | `040667aa8a00c73fe8f9c278389722b49e56a5fa9684b5173250e9423f9a1d70` |
| `ballast.rules.json` | `9682c31994bb4e166ade2908f6a34bbd134aaac48afac0ad40fd099fd73bc76f` |
| `RULES.md` | `ec3abe1700186801ab7a61170ed8eff6f87145e59da235e888127fcd5fd83965` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |

`RULES.md`는 과거 17.4.0 시점 문서에 기록된 hash와 달랐지만, 18 업데이트 직전 실제 파일이 이미 이 값이었다. 따라서 이를 사용자 후속 변경이 반영된 현재 권위 상태로 취급했고 과거 hash로 복원하지 않았다.

후속 actual external TUI smoke 과정에서 `config.yml`의 theme 두 항목만 일시 변경된 것이 최종 hash 비교에서 확인됐다. 이는 Ballast나 updater가 만든 변경으로 취급하지 않았다. OMP 18의 setup/theme migration 계약을 확인한 뒤 smoke 전 값인 `theme.dark: dark-monokai`만 복원하고 임시 `theme.light: light-one`을 제거했으며, 최종 `config.yml` SHA-256은 다시 업데이트 직전 값 `b2c11652e4cdffba774729638e024cf8ad11dfac009efa22aa519d6b59707731`과 일치한다.

업데이트 후 Ballast 자체 검증:

- `npm test`: `12 pass / 0 fail`
- `npm run check`: PASS
- `omp -p --no-session --max-time 30s "/ballast status"`: exit `0`
- print mode에서는 extension custom UI 본문이 stdout에 나오지 않으므로 status 텍스트를 확인했다고 기록하지 않는다.
- 현재 effective user rule은 계속 `2`개이며 ID는 `iis-ticket-implement-guard`, `iis-ticket-verify-guard`다.

실제 OMP 18 saved model turn `OMP18.0.0 smoke OK`가 정상 종료됐고 그 session을 ompweb `0.3.5`가 읽었다. 따라서 **OMP 18 standalone runtime -> user extension/session lifecycle -> persisted JSONL** 경계까지 정상이다.

최종 판정: **Ballast는 OMP 18.0.0에서도 direct user extension으로 그대로 유지되며 별도 18용 재설치나 source 수정이 필요하지 않았다.** Core local patch와 Ballast lifecycle은 계속 별도 artifact로 관리한다.

## 2026-08-26 Happy Search 조사·종합 규칙 등록 — 적용 완료

일반 웹 검색이 아니라 Happy Search 계열과 `unified_search` 사용 시에만 근거 선별, 재검색, 중복 제거, 과잉 일반화 방지 및 결론 중심 종합 지침을 주입하도록 `happy-search-research-synthesis`를 추가했다.

구성:

- 지침 원본: `~/.omp/agent/ballast/happy-search-research.md`
- 사용자 rule: `~/.omp/agent/ballast.rules.json`
- prompt trigger: `해피서치`, `해피 서치`, `유니파이드서치`, `유니파이드 서치`, `Happy Search`, `Unified Search`
- tool activator: `write` 입력의 `xd://mcp__happy_search_` 경로
- 일반 `web_search`, 임의 파일 `write`, 코드 검색에는 활성화하지 않음

변경 전 사용자 rules는 다음 경로에 보존했다.

```text
~/.omp/agent/manual-backups/ballast-happy-search-20260826T231255+0900/
```

OMP `18.0.6` 실제 TUI와 extension core에서 확인한 결과:

- `/ballast status`: effective rules `3`, 새 rule과 `write(p:xd://mcp__happy_search_)` activator 표시
- positive `/ballast test`: `유니파이드 서치로 최신 반응을 조사해줘`에서 새 rule 매칭
- negative `/ballast test`: `이 함수 설명해줘`에서 매칭 없음
- core matcher: warning 없음, positive 매칭, negative 비매칭, Happy Search `write` 활성화, 일반 파일 `write` 비활성화, instructionFile 정상 해석
- prompt trigger가 없는 실제 Reddit 검색 요청에서도 첫 Happy Search `write`가 새 standing rule로 중단되고 지침 주입 후 재시도되어 검색 결과까지 반환

최종 판정: **Happy Search 조사 규율은 Happy Search MCP 경계에만 조건부 적용되며 일반 웹 검색과 비검색 작업에는 주입되지 않는다.**

## 2026-08-28 OMP 18.0.7 업데이트 후 검증 — 적용 완료

OMP live launcher를 `18.0.6` custom checkout에서 exact tag `v18.0.7` commit `6be4a1bec9c53ed9eef33e65a70a060970f30cce` 기반 checkout으로 전환한 뒤 Ballast를 다시 검증했다. 전환 전 사용자 상태는 `~/.omp/agent/manual-backups/omp-before-18.0.7-20260828T001941+0900/`에 보존했다.

현재 확인 결과:

- `omp --version`: `omp/18.0.7`
- Ballast `npm test`: `12 pass / 0 fail`
- Ballast `npm run check`: PASS
- `omp -p --no-session --max-time 30s "/ballast status"`: exit `0`
- print mode의 custom UI 본문은 stdout에 노출되지 않으므로 status 텍스트를 캡처했다고 기록하지 않는다.
- `ballast.rules.json` readback: enabled rule `3`개 유지
  - `iis-ticket-implement-guard`
  - `iis-ticket-verify-guard`
  - `happy-search-research-synthesis`
- `~/.omp/agent/extensions/`에는 `omp-ballast`만 남아 있고 폐기된 OMPWeb bridge는 없다.

업데이트 전 기준 checksum 중 Ballast/governance 파일은 다음과 같다.

| 파일 | SHA-256 |
| --- | --- |
| `extensions/omp-ballast/index.js` | `040667aa8a00c73fe8f9c278389722b49e56a5fa9684b5173250e9423f9a1d70` |
| `extensions/omp-ballast/src/core.js` | `8748ce99c89933d44e85eb088ea3173fede8a271bd9b113b94cdd38063540674` |
| `ballast.rules.json` | `5fca7df051802176a69c3dccae9378c257b904ccc13e38dab02d26d498849c03` |
| `RULES.md` | `ec3abe1700186801ab7a61170ed8eff6f87145e59da235e888127fcd5fd83965` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |

`config.yml`은 Ballast가 아니라 폐기한 assistant Markdown spacing 설정을 제거하면서 의도적으로 변경됐다. 이를 Ballast 업데이트 변화로 취급하거나 과거 config checksum으로 자동 복원하지 않는다.

최종 판정: **Ballast는 OMP 18.0.7에서도 direct user extension으로 유지하며 별도 source 수정이나 재설치가 필요하지 않다. 현재 effective user rule은 3개다.**

## 2026-08-28 OMP 18.0.9 업데이트 후 검증 — 적용 완료

OMP live launcher를 exact `v18.0.9` commit `cc14e04f075de82c5c0c0ccd2f9dfbce6f03fe9e` 기반 custom checkout으로 전환한 뒤 Ballast를 다시 검증했다. 전환 전 상태는 다음 경로에 보존했다.

```text
~/.omp/agent/manual-backups/omp-before-18.0.9-20260828T183047+0900/
```

검증 결과:

- live `omp --version`: `omp/18.0.9`
- Ballast `npm test`: `12 pass / 0 fail`
- Ballast `npm run check`: PASS
- 18.0.9 source `/ballast status`: exit `0`
- 18.0.9 live `/ballast status`: exit `0`
- effective user rule은 계속 3개다.
  - `iis-ticket-implement-guard`
  - `iis-ticket-verify-guard`
  - `happy-search-research-synthesis`
- 18.0.9의 nested subagent observability 및 concurrent shutdown 변경과 함께 실제 TUI smoke를 수행했고 root process가 정상 생존했다.

업데이트 전 backup과 업데이트 후 사용자 artifact를 byte 단위로 비교한 결과 Ballast/governance 파일은 모두 동일했다.

| 파일 | SHA-256 |
| --- | --- |
| `extensions/omp-ballast/index.js` | `040667aa8a00c73fe8f9c278389722b49e56a5fa9684b5173250e9423f9a1d70` |
| `extensions/omp-ballast/src/core.js` | `8748ce99c89933d44e85eb088ea3173fede8a271bd9b113b94cdd38063540674` |
| `ballast.rules.json` | `5fca7df051802176a69c3dccae9378c257b904ccc13e38dab02d26d498849c03` |
| `RULES.md` | `ec3abe1700186801ab7a61170ed8eff6f87145e59da235e888127fcd5fd83965` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |

`config.yml`은 한 줄만 의도적으로 달라졌다. OMP 18.0.9에서 `extendedContext` 기본값이 `true -> false`로 바뀌므로 기존 GPT-5.6 동작을 보존하기 위해 업데이트 전에 root 설정에 `extendedContext: true`를 명시했다. 이는 Ballast 변경이 아니며 Ballast artifact checksum 복원 대상도 아니다.

최종 판정: **Ballast는 OMP 18.0.9에서도 direct user extension으로 정상 유지되며 별도 재설치·source 수정이 필요하지 않다. 현재 effective user rule은 3개다.**

## 2026-08-30 OMP 18.0.11 업데이트 후 검증 — 적용 완료

OMP live launcher를 exact `v18.0.11` commit `b8ce33a58911c26bed1d84f0db9a5e2e727c49a2` 기반 custom checkout으로 atomic 전환했다. 전환 전 사용자 상태는 다음 경로에 보존했다.

```text
~/.omp/agent/manual-backups/omp-before-18.0.11-20260830T102713+0900/
```

검증 결과:

- live `omp --version`: `omp/18.0.11`
- live `--smoke-test`: `smoke-test: ok`
- live model turn: `OMP18.0.11 LIVE RUNTIME OK`
- Ballast `npm test`: `12 pass / 0 fail`
- Ballast `npm run check`: PASS
- 실제 18.0.11 TUI 로그에서 `omp-ballast extension registered` 확인
- `/ballast status`: `omp-ballast 0.1.0`, effective rule `3`개
  - `iis-ticket-implement-guard`
  - `iis-ticket-verify-guard`
  - `happy-search-research-synthesis`

업데이트 전 backup과 전환 후 사용자 artifact를 byte 단위로 비교한 결과 모두 동일했다.

| 파일 | SHA-256 |
| --- | --- |
| `extensions/omp-ballast/index.js` | `040667aa8a00c73fe8f9c278389722b49e56a5fa9684b5173250e9423f9a1d70` |
| `extensions/omp-ballast/src/core.js` | `8748ce99c89933d44e85eb088ea3173fede8a271bd9b113b94cdd38063540674` |
| `ballast.rules.json` | `5fca7df051802176a69c3dccae9378c257b904ccc13e38dab02d26d498849c03` |
| `RULES.md` | `ec3abe1700186801ab7a61170ed8eff6f87145e59da235e888127fcd5fd83965` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |
| `config.yml` | `d6c6b650368191cba59cda200feaf729c66b2681028f48e2b75b4dcd0b47487a` |

최종 판정: **Ballast는 OMP 18.0.11에서도 direct user extension으로 정상 유지되며 별도 재설치·source 수정이 필요하지 않다. 현재 effective user rule은 3개다.**

## 2026-09-04 OMP 18.1.8 업데이트 후 검증 — 적용 완료

OMP live launcher를 exact `v18.1.8` 기반 custom checkout으로 atomic 전환한 뒤 Ballast와 governance 사용자 artifact를 다시 검증했다. 전환 전 현재 상태는 다음 경로에 보존했다.

```text
~/.omp/agent/manual-backups/omp-upgrade-18.1.4-to-18.1.8-20260904T134442+0900/
```

검증 결과:

- live `omp --version`: `omp/18.1.8`
- live `--smoke-test`: `smoke-test: ok`
- live model turn: `OMP18.1.8 LIVE RUNTIME OK`
- Ballast `npm test`: `12 pass / 0 fail`
- Ballast `npm run check`: PASS
- `omp -p --no-session --max-time 30s "/ballast status"`: exit `0`; print mode의 custom UI 본문은 stdout에 노출되지 않음
- 현재 authoritative `ballast.rules.json` enabled rule은 `happy-search-research-synthesis` 1개다. 18.0.11 이후 사용자 후속 변경이 반영된 현재 상태로 취급하며 과거 3-rule 상태로 자동 복원하지 않는다.
- `config.yml`, `RULES.md`, `APPEND_SYSTEM.md`, `ballast.rules.json`, Ballast `index.js`와 `core.js`는 cutover 전후 checksum이 모두 동일하다.

현재 checksum:

| 파일 | SHA-256 |
| --- | --- |
| `extensions/omp-ballast/index.js` | `040667aa8a00c73fe8f9c278389722b49e56a5fa9684b5173250e9423f9a1d70` |
| `extensions/omp-ballast/src/core.js` | `8748ce99c89933d44e85eb088ea3173fede8a271bd9b113b94cdd38063540674` |
| `ballast.rules.json` | `7774191e2a105e3032a74fb61bd00f1293fc5c3c9d591d59719f16fc1800176d` |
| `RULES.md` | `ec3abe1700186801ab7a61170ed8eff6f87145e59da235e888127fcd5fd83965` |
| `APPEND_SYSTEM.md` | `6cdfbac76c81e6a04eab51bb855f200f7b3d0130abc6db9a1ede5c1c7be901ef` |
| `config.yml` | `d9073eebe9e43a4a74b9ed785e8eca98ee4763d97b5da1220417b64a9f5ed04d` |

최종 판정: **Ballast는 OMP 18.1.8에서도 direct user extension으로 유지되며 재설치나 source 수정이 필요하지 않다. 현재 authoritative effective user rule은 1개다.**
