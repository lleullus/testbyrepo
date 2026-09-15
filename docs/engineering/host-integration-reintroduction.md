# IIS 실행 도구·OMP 플러그인 재도입 안내

## 목적과 현재 기준

2026-09-15에 IIS의 OMP 본체 종속 기능과 Scope 플러그인을 제거하고, 스킬과 일반 도구로 수행하는 구조로 전환했다. 이 문서는 나중에 그 기능이 다시 필요할 때 참고 코드를 찾고 현재 구조에 맞게 재도입하는 방법을 남긴다. 재도입 승인, 필수 후속 작업, 새 IIS 단계는 아니다.

현재 제품 계약은 **Thesis → Scope → Plan·독립 Review → 구현 → 독립 검증 → Coverage → Main의 완료 기록**이다. 기본 IIS에는 전용 실행 CLI, 호스트 verifier profile, 불투명 terminal handle이 필요하지 않다. 현재 Plan Review는 `iis-scope-plan-review/v2`, 설치는 `iis-bundle/v4`·`iis-install/v4`, 패키징 protocol은 `4`, family는 `iis-skills`다. 이 패키징 버전은 실행 프로토콜이 아니다.

현재 원본: [README](../../README.md), [의존성 지도](ready-runtime/dependency-map.md), [검증 경계](ready-runtime/verification.md), [Plan](../../companion-skills/scope-plan/SKILL.md), [검증](../../companion-skills/scope-verify/SKILL.md), [Coverage](../../companion-skills/scope-coverage/SKILL.md).

## 1. 커밋 통합 뒤에도 참고 코드를 찾는 방법

IIS 저장소에는 아래 annotated tag를 보존한다. main의 세 커밋을 하나로 합쳐도 이 태그가 과거 구현을 계속 참조하므로 reflog나 임시 백업에 의존하지 않는다.

| 구분 | 기준 |
| --- | --- |
| IIS 과거 구현 보존 태그 | `archive/iis-host-integration-v3` |
| 태그가 가리키는 원본 커밋 | `45deb086cde21de664f14895d4eaae4a80f6ff47` |
| 제거 변경의 조사 기준 | `a00a457af769b4c600b48b47aceb4cf29fede850` — 통합 전 이력 식별용이며 지속적인 코드 복구 기준은 위 태그 |
| 별도 OMP 저장소의 기능 추가 | `2300ce22cf2da3a295d7ccbc3202c682631592ed` |
| 별도 OMP 저장소의 해당 패치 되돌림 | `d88612394171bc645261185bad6949a69aef121c` |

IIS 저장소 루트에서 읽기만 하려면:

```bash
git rev-parse 'archive/iis-host-integration-v3^{commit}'
git show archive/iis-host-integration-v3:delivery-tools/scope/README.md
git show archive/iis-host-integration-v3:delivery-tools/scope/omp.js
git show archive/iis-host-integration-v3:delivery-tools/scope/src/finalization.js
```

전체 과거 소스를 별도 디렉터리에서 검토하려면, 대상 디렉터리가 아직 없는 상태에서 다음을 실행한다. 현재 main이나 운영 설치를 바꾸는 명령은 아니다.

```bash
git worktree add --detach ../iis-host-integration-reference archive/iis-host-integration-v3
```

다른 머신이나 저장소 사본으로 옮길 때는 이 태그도 함께 보존한다. main만 옮기거나 태그를 삭제하면 과거 코드의 지속 보존을 보장할 수 없다. 원격 전송은 이 문서 작성·커밋 통합 작업에 포함하지 않는다.

OMP는 독립 저장소다. 당시 로컬 경로는 `/home/user01/project/oh-my-pi-custom-v18.1.21`이며, 그 저장소에서 다음으로 추가·되돌림 내용을 확인한다. IIS 태그에는 OMP 코드가 들어 있지 않으므로 OMP 저장소를 폐기하거나 이력을 별도로 재작성할 때는 이 커밋도 따로 보존해야 한다.

```bash
git show --stat 2300ce22cf2da3a295d7ccbc3202c682631592ed
git show 2300ce22cf2da3a295d7ccbc3202c682631592ed:packages/coding-agent/src/task/authority-profile.ts
git show 2300ce22cf2da3a295d7ccbc3202c682631592ed:packages/coding-agent/src/task/ready-verifier-terminal.ts
```

## 2. 무엇을 제거했고 무엇을 참고하면 되는가

| 영역 | 과거 소스 | 참고할 기능과 현재 주의점 |
| --- | --- | --- |
| Scope 도구 | `delivery-tools/scope/src/core.js`, `authority-binding.js`, `plan-binding.js` | Scope·Thesis 원본 식별과 Plan admission. 과거 Review v1을 현재 v2 계약에 그대로 연결하지 않는다. |
| 검증 binding | `delivery-tools/scope/src/verification-binding.js` | 원본·stable target의 바이트 식별, scenario effect 경로 분리, 검증 전후 현재성 확인. 바이트 일치는 독립 실행이나 의미적 성공의 증명이 아니다. |
| 완료 기록 | `delivery-tools/scope/src/finalization.js` | 정확한 상태 전이, 재시도 결과 복구, 조건부 원상 복구. 과거에는 호스트가 수락한 terminal을 소비했으며 현재의 일반 도구 기반 완료 절차와 권한 모델이 다르다. |
| OMP 연결부 | `delivery-tools/scope/omp.js` | `ready_contract`와 `ready_finalize` 등록, host API 연결. 과거 이름의 `ready`는 Scope 상태이지 Ticket 호환 계층이 아니다. |
| 진단용 CLI | `delivery-tools/scope/cli.js` | 원본 확인·admission·binding capture. 과거 CLI의 `ready_finalize`는 호스트 terminal 권한이 없어 `CAPABILITY_UNAVAILABLE`로 거부했다. 독립 실행 완결 CLI가 아니었다. |
| OMP 본체 | 별도 저장소의 `task/authority-profile.ts`, `task/ready-verifier-terminal.ts`, Task 실행·결과 전달·extension API 연결 | 지정 verifier의 prompt/schema/topology, host-owned terminal과 caller/session 귀속, finalization 결과 재사용. 플러그인 파일만 복사해서는 생기지 않는 기능이다. |
| 설치 | 과거 `scripts/sync_installed_iis.py`, `tests/test_ready_ticket_boundary_tools.py` | v3 immutable bundle, extension 링크와 migration/rollback. 현재 v4는 스킬 중심이며 과거 extension을 제거하는 경로다. |
| 실행 평가기 | 과거 `evaluation/ready-verification/run_agent.py`, `prepare_environment.py`, `planning.py`, `implementation.py`, `goal.py`, `completion.py`, `inspect_run.py`, `topology.py`, `calibrate.py` | 당시 호스트에 종속된 실행·관찰 경로. 플러그인을 추가한다고 이 평가기 전체까지 복원할 필요는 없다. 현재 남은 offline 평가 도구와 구분한다. |

**과거 코드의 정확한 계약은 태그 안의 `delivery-tools/scope/README.md`, 해당 구현과 테스트를 우선한다.** 같은 태그의 `docs/engineering/ready-runtime/dependency-map.md`와 `verification.md`에는 더 오래된 Ticket 경로·스키마 설명이 남아 있다. 이 문서들을 Scope v3의 설치·운영 지침으로 그대로 사용하지 않는다.

과거 OMP 연결부는 `SCOPE_VERIFIER_PROFILE === "iis-scope-verifier/v1"`을 요구했고, `resolveReadyVerifierTerminal`, `readyVerifierVerdictRecordPath`, `resolveReadyVerifierFinalization`, `recordReadyVerifierFinalization`, `releaseReadyVerifierTerminalsForSession` API를 사용했다. terminal schema는 `iis-scope-verifier-terminal/v1`이었다. 현재 호스트가 이 API들을 제공한다고 가정해서는 안 된다.

## 3. 재도입은 필요한 보장부터 선택한다

### 일반적인 자동화·편의 기능을 원하는 경우

현재 main에서 개발하고, 필요한 과거 함수와 동작만 참고한다. 예를 들어 원본 hash 확인이나 현재 Review v2의 구조 검사는 일반 명령/라이브러리로 먼저 해결할 수 있다. 이미 있는 Scope validator나 설치 도구를 재사용하고, OMP에서 호출하기 편해야 할 때만 얇은 플러그인 연결부를 추가한다.

이 경로에서는 독립 verifier 결과와 Coverage를 확인하는 Main의 현재 책임을 유지한다. 보고서 경로를 불투명 문자열로 바꾸거나 UUID를 붙였다는 이유로 host-owned provenance가 생겼다고 주장하지 않는다. 플러그인이 없어도 기본 IIS를 수행할 수 있어야 한다.

### 호스트가 verifier 결과의 귀속과 완료 기록을 강제해야 하는 경우

이 보장이 실제 요구라면 과거 OMP 본체 변경도 검토 대상이다. 당시 구현은 독립 작업자의 최종 결과를 호스트에서 수락하고 caller/session에 묶었으므로, **플러그인만으로 과거와 같은 보장을 복원했다고 주장할 수 없다.**

먼저 현재 OMP의 Task·extension API가 동등한 기능을 제공하는지 확인한다. 충분하면 그 공개 API를 사용한다. 부족하면 필요한 호스트 API와 플러그인 사이의 계약을 정하고, OMP 저장소의 변경을 별도 작업으로 수행한다. 호스트 중립 부분과 OMP 연결부를 구분하되, 실제 두 번째 소비자도 없는데 범용 어댑터 프레임워크부터 만들지는 않는다.

이 경로에서 완료 기록 주체나 권한을 바꾼다면 관련 IIS 역할 원본도 함께 수정해야 한다. 현재 Main의 일반 도구 방식과 과거 `ready_finalize` 전용 방식을 동시에 필수 규칙으로 남기지 않는다. 호스트 강제 보장이 필요 없는 클라이언트의 기본 경로와, 그 보장을 요구하는 요청의 실행 가능 여부도 구분한다.

## 4. 실제 작업 순서

1. **현재 요청과 부족한 동작을 특정한다.** 편의 자동화인지 host-owned 결과 귀속인지 선택하고, 실제 관찰할 성공 조건을 정한다. 과거 구현 전체 복구를 시작점으로 삼지 않는다.
2. **현재 main을 구현 기준으로 삼는다.** 태그는 별도 worktree의 참고 자료로 사용한다. `45deb08` 전체 cherry-pick이나 `a00a457` 전체 revert는 스킬·설치·평가기까지 되돌리므로 선택적 재도입 방법이 아니다.
3. **관련 계약과 구현을 같이 맞춘다.** 현재 Scope·Thesis·Review v2, verifier 결과 수령, Coverage, 완료 기록의 연결을 따른다. 원본 binding과 finalization만 옮기더라도 입력 schema와 실제 결과 전달 경로를 먼저 맞춘다. 필요한 범위의 과거 테스트도 새 계약에 맞춰 가져온다.
4. **설치 경로는 실행 기능과 구분한다.** 단순 편의 플러그인은 기존 extension 설치 방식을 쓸 수 있다. IIS 관리 payload나 metadata 계약을 실제 바꾸는 경우에만 새 packaging/migration을 설계한다. 현행 v4 manifest에 v3 파일을 끼워 넣거나 과거 release를 덮어쓰지 않는다.
5. **격리 환경에서 연결을 검증한다.** 아래 관찰을 필요한 보장에 맞게 확인한 뒤, 운영 반영을 별도 수행한다. 운영 반영 전에는 영향받는 작업과 효과가 정리됐는지 확인하고, 반영 후에는 실제 새 세션의 로드된 도구·스킬·프로토콜을 확인한다. 소스 수정·설치 링크 변경만으로 기존 세션이 갱신됐다고 판단하지 않는다.

과거 스냅샷을 통째로 운영 복원해야 하는 별도 요청이라면 IIS v3와 대응 OMP 본체를 함께 맞춰야 한다. 현재 installer의 rollback은 설치 엔트리를 되돌릴 뿐 OMP 소스, 제품 데이터, 실행 효과를 복구하지 않는다. 따라서 설치 rollback만으로 옛 기능이 살아난다고 안내하지 않는다.

당시 제거한 전역 Ballast 규칙 `ready-ticket-verify-triage-reminder`는 오래된 Ticket 경로를 대상으로 했다. Scope 플러그인 재도입과 별개이며 자동 복원하지 않는다. 현재 Scope 흐름에 지침이 실제 필요할 때 그 목적과 적용 지점을 새로 판단한다.

## 5. 무엇을 관찰하면 재도입이 제대로 된 것인가

- **기본 경로:** 플러그인 없는 클라이언트에서도 현재 스킬 기반 작업이 수행된다. 선택 기능이 기본 실행의 숨은 필수 의존성이 되지 않는다.
- **입력과 현재성:** 현재 Scope·Thesis·Review v2를 사용하고, 중요한 원본·대상 변경이 생기면 오래된 판단으로 완료를 기록하지 않는다. 허용된 scenario effect는 stable target 변경과 구분한다.
- **실제 결과 전달:** host-owned 귀속을 약속한다면 실제 독립 verifier의 완료 결과를 통해 확인한다. fixture terminal이나 복사한 JSON으로 그 보장이 검증됐다고 하지 않는다. FAILED·INCONCLUSIVE·누락 결과가 완료로 진행하지 않아야 한다.
- **완료 기록:** 성공한 독립 검증 뒤 Coverage가 완료되고 중요한 공백이 없을 때만 해당 Scope의 상태를 바꾼다. 재시도·응답 유실 후 실제 기록을 확인하고, 이미 `done`인 파일을 새 완료 성과로 세지 않는다.
- **설치와 제거:** 격리된 client root에서 기존 사용자 파일 보존, 플러그인 설치·제거·rollback을 확인한다. host 전용 보장을 선택한 경로는 필요한 capability가 없으면 분명히 실행 불가로 보고하며 그 보장을 조용히 낮추지 않는다.
- **일반 도구:** 보통의 명령 실패는 오류 결과로 처리하며, 관련 없는 편집·명령 실행을 막는 전역 잠금이나 도구 가로채기를 다시 도입하지 않는다.

태그의 `delivery-tools/scope/package.json`은 Node `>=20`과 `node --test tests/*.test.js`를 사용한다. 과거 테스트는 참고 스냅샷에서 해당 디렉터리를 작업 디렉터리로 실행할 수 있다. 이는 과거 경계 동작의 증거일 뿐, 현재 호스트와 새 구현의 호환성 증거는 아니다. 재도입 완료는 새 구현의 실제 연결·상태 변화로 확인한다.

현재 변경은 이 안내와 과거 소스 참조 보존뿐이다. 플러그인·OMP 본체·실행 평가기를 재설치하거나 운영 세션을 재시작하지 않는다.
