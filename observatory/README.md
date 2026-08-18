# IIS Observatory

IIS Observatory는 여러 저장소의 IIS planning 아티팩트를 읽어 현재 위치, Ticket 진행 상태, 다음 작업, 정합성 문제를 한 화면에 보여주는 **읽기 전용 관측 도구**입니다.

```text
IIS PROJECT OVERVIEW
────────────────────────────────────────────────────────────────────────────────────────────
Repository         Unit                                  Tkts   State      Next
────────────────────────────────────────────────────────────────────────────────────────────
tax                INC-004 · VAT authoritative readback  3/5    READY      TKT-005 구현
ima2               INC-012 · Job inspection              —      PLANNING   Ask Matt
oracle             WP-003 · Browser slot expansion       —      NEEDS SCOPE Scope Shaper
legacy-api         work · Legacy cleanup                 4/4    COMPLETE   —
dc-ai-tier         INC-004 · CN bounded batch 평가       1/1    COMPLETE   Scope Shaper [WP-002, WP-003]
────────────────────────────────────────────────────────────────────────────────────────────
Ready 1   Blocked 0   Planning 2   Inconsistent 0   Complete 2
```

`Unit`은 별도 요약을 생성하지 않습니다. Increment가 있으면 `INC-NNN · <Increment authored heading>`, Work Package만 있으면 `WP-NNN · <Work Package authored heading>`, direct-work이면 `work · <Spec authored heading>`을 사용하고 터미널 폭에서만 잘라냅니다.

## 설계 원칙

- 상태의 원본은 각 저장소의 `docs/planning/**` Markdown 파일입니다.
- Observatory는 상태 DB나 workflow ledger를 만들지 않습니다.
- 파일을 변경하지 않고 매 실행마다 현재 상태를 다시 계산합니다.
- 에이전트용 JSON과 사람용 Overview가 동일한 판정 로직을 사용합니다.
- `delivery outside IIS`는 다음 포인터일 뿐, 구현이나 검증을 실행하지 않습니다.

## 요구 사항

- Linux 또는 WSL
- Python 3.11 이상
- Git은 `history` 명령에 필요하며, snapshot에서는 생성 시점 참고 metadata로만 선택적으로 사용합니다.
- 외부 Python 패키지 없음

## 설치

ZIP을 원하는 위치에서 푼 뒤 실행합니다.

```bash
cd observatory
./install.sh
```

기본 설치 결과:

```text
소스: /home/user01/project/iis-skills/observatory
명령: ~/.local/bin/iis-observatory
```

`~/.local/bin`이 `PATH`에 없다면 셸 설정에 한 번 추가합니다.

```bash
export PATH="$HOME/.local/bin:$PATH"
```

기존 설치를 백업하고 교체하려면:

```bash
./install.sh --force
```

다른 경로에 설치하려면:

```bash
./install.sh --target ~/tools/iis-observatory
```

설치하지 않고 ZIP 안에서 바로 실행할 수도 있습니다.

```bash
./bin/iis-observatory overview ~/project
```

## 빠른 사용법

### 여러 저장소 Overview

```bash
iis-observatory overview ~/project
```

`overview`는 기본 명령이므로 다음도 같습니다.

```bash
iis-observatory ~/project
```

중첩된 저장소 탐색 깊이는 기본 4단계입니다.

```bash
iis-observatory overview ~/project --max-depth 6
```

검색 루트 자체가 Git 저장소가 아니라 단순 프로젝트 모음 폴더라면, 그 루트에 우연히 `docs/planning`이 있어도 포트폴리오 항목으로 포함하지 않습니다. 반대로 검색 루트 자체가 Git 저장소라면 정상적인 하나의 IIS 프로젝트로 포함합니다.

연결된 Git worktree는 포트폴리오 화면의 중복/노이즈를 줄이기 위해 기본적으로 제외합니다. 필요할 때만 포함합니다.

```bash
iis-observatory overview ~/project --include-worktrees
iis-observatory doctor ~/project --include-worktrees
```

특정 worktree 경로를 명시한 상세 조회는 기본 설정과 관계없이 그대로 가능합니다.

```bash
iis-observatory scan ~/project/x.com/worktrees/feature
```

### 한 저장소 상세 상태

```bash
iis-observatory scan ~/project/tax
```

출력은 IIS의 read-only Current Planning State Check와 같은 성격을 갖습니다.

```text
IIS CURRENT PLANNING STATE
Repository: tax
Current Scope: ...
Current Work Package: WP-002 / scoped [...]
Current Increment: INC-004 / ready-for-matt [...]
Current Spec: SPEC.md / approved [...]
Derived Delivery State: READY
Completed: TKT-001, TKT-002, TKT-003
Remaining: TKT-004 (ready), TKT-005 (ready)
Next Work: TKT-004 구현
Next leaf: delivery outside IIS
Health: READY
...
STOP
```

### Durable 프로젝트 상태판

현재 상태를 Git에 보관할 수 있는 **파생 read model**로 기록하려면:

```bash
iis-observatory snapshot ~/project/tax --write
```

다음 두 파일만 갱신합니다.

```text
docs/planning/observatory/
├── PROJECT-OVERVIEW.md
└── project-state.json
```

이 파일들은 canonical IIS authority가 아닙니다. Scope, Work Package, Increment, Spec, Ticket을 변경하거나 다음 leaf를 실행하지 않습니다. 동일한 source fingerprint라면 `Action: UNCHANGED`로 끝나며 파일/mtime도 바꾸지 않습니다.

사람용 `PROJECT-OVERVIEW.md`에는 현재 Ticket denominator가 있을 때 정확한 비율과 함께 진행 막대가 표시됩니다.

```text
Delivery Progress
  Current Ticket delivery: ██████░░░░ 3 / 5 (60.0%) — exact ratio
```

작은 비율도 과장하지 않도록 fractional block을 사용합니다. 예를 들어 `1.2%`는 `▏░░░░░░░░░`처럼 표시되며 정확한 분자/분모/퍼센트가 항상 옆에 남습니다. 막대는 presentation-only이고 `Health`나 `Next Work` 판정에 영향을 주지 않습니다.

저장된 상태판이 아직 최신인지 확인하려면:

```bash
iis-observatory snapshot ~/project/tax --check
```

결과는 `CURRENT`, `STALE`, `MISSING`, `INCONSISTENT` 중 하나입니다. Freshness는 Git HEAD가 아니라 canonical planning 입력과 표시되는 Adaptive provenance의 content fingerprint로 판정하며 `docs/planning/observatory/**` 자체는 fingerprint에서 제외합니다.

Adaptive Mandate/Trace가 존재하면 provenance로만 표시합니다. 파일에 `Status: active`가 기록돼 있어도 현재 요청의 Adaptive 활성화를 추론하지 않습니다. 세부 계약은 [`docs/SNAPSHOT-CONTRACT.md`](docs/SNAPSHOT-CONTRACT.md), JSON 계약은 [`docs/PROJECT-STATE-SCHEMA.md`](docs/PROJECT-STATE-SCHEMA.md)를 참고합니다.

### JSON 출력

```bash
iis-observatory overview ~/project --format json
iis-observatory scan ~/project/tax --format json
```

Web UI나 다른 에이전트는 텍스트를 다시 파싱하지 말고 JSON을 소비해야 합니다.

### Markdown 리포트

```bash
iis-observatory overview ~/project --format markdown --output overview.md
```

### 정합성 검사

```bash
iis-observatory doctor ~/project
```

다음 문제를 탐지합니다.

- Scope가 선택한 Increment 파일이 없음
- `ready-for-matt` Increment가 둘 이상임
- 현재 Ticket의 ID나 `Status`가 없음
- 현재 Ticket ID가 중복됨
- 알 수 없는 Ticket 상태
- 현재 Spec의 `Source-Increment` 불일치
- 존재하지 않는 로컬 planning Markdown 링크

CI나 자동화에서 오류 상태를 exit code로 받고 싶다면:

```bash
iis-observatory overview ~/project --fail-on-inconsistent
iis-observatory scan ~/project/tax --fail-on-inconsistent
```

### Git 기반 planning 이력

```bash
iis-observatory history ~/project/tax --limit 20
```

`docs/planning`을 건드린 최근 커밋과 `Status:` 줄 전환을 보여줍니다. Canonical planning, Adaptive provenance, Observatory projection은 별도 범주로 표시하며, 이 명령도 Git을 읽기만 합니다.

## 명령 목록

```text
iis-observatory overview [ROOT]
iis-observatory scan [REPOSITORY]
iis-observatory snapshot [REPOSITORY] [--check|--write]
iis-observatory doctor [ROOT]
iis-observatory history [REPOSITORY]
iis-observatory version
```

전체 옵션은 각 명령의 `--help`에서 확인합니다.

```bash
iis-observatory overview --help
```

## 판정 개요

현재 단위는 다음 순서로 찾습니다.

1. 최신 canonical `SCOPE-SHAPING-RESULT.md`
2. 명시된 `Selected-Increment` 또는 `Current-Increment`
3. Scope가 유일하게 참조하는 Increment
4. 유일한 `ready-for-matt` Increment
5. 유일한 Spec `Source-Increment`
6. direct work인 경우 `Suggested-Work-Slug` 또는 유일한 work slug

다음 작업은 정합성 오류 → blocked Ticket → ready Ticket → draft Ticket → 현재 delivery unit 완료 후 authored Scope horizon → Spec → Increment → Scope 순서로 판정합니다. 현재 Ticket이 모두 `done`이어도 `Outcome Horizon > Expansion` 후보가 있으면 현재 unit의 `COMPLETE`는 유지하면서 후보를 그대로 표시하고 `Scope Shaper`를 다음 leaf로 가리킵니다. `Deferred`는 표시만 하고 자동 승격하지 않습니다. 세부 계약은 [`docs/STATE-CONTRACT.md`](docs/STATE-CONTRACT.md)에 있습니다.

`scoped`, `ready-for-matt`, `approved` 같은 값은 원본 planning artifact의 authored status입니다. 상세 `scan`에서 Ticket 기반 delivery 상태가 성립하면 `Derived Delivery State: READY|BLOCKED|COMPLETE`를 별도 줄로 표시해 authored planning status와 Observatory의 계산 결과를 구분합니다.

## 인식하는 기본 구조

```text
<repository>/
└── docs/
    └── planning/
        ├── scope-shaping/
        │   ├── .../SCOPE-SHAPING-RESULT.md
        │   ├── .../WORK-PACKAGE-001.md
        │   └── .../INCREMENT-001.md
        └── work/
            └── <work-slug>/
                ├── SPEC.md
                └── tickets/
                    ├── TICKET-001.md
                    └── TICKET-002.md
```

다음과 같은 metadata 표기 방식을 모두 읽습니다.

```markdown
---
status: ready
source_increment: INC-004
---
```

```markdown
Status: ready
Source-Increment: INC-004
```

```markdown
| Status | ready |
| Source-Increment | INC-004 |
```

`TICKET-005`는 내부적으로 `TKT-005`로 정규화됩니다.

## 상태 의미

| Health | 의미 |
|---|---|
| `READY` | 구현 가능한 Ready Ticket이 있음. Delivery는 IIS 외부임. |
| `BLOCKED` | 현재 Ticket에 blocker가 있음. |
| `PLANNING` | Ask Matt, To Spec, To Tickets 또는 Ticket readiness 작업이 남음. |
| `NEEDS SCOPE` | Scope Shaper가 다음 Increment를 만들어야 함. |
| `INCONSISTENT` | 아티팩트가 서로 모순되거나 필수 상태가 빠짐. |
| `COMPLETE` | 현재 선택된 delivery unit의 연관 Ticket이 모두 done임. 후속 Scope 후보가 존재해도 현재 unit은 COMPLETE일 수 있음. |
| `STALE` | 현재로 식별되는 계보가 superseded 상태임. |

## 테스트

```bash
make test
```

또는:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

샘플 프로젝트를 생성하고 Overview를 직접 확인하려면:

```bash
make demo
```

## 제거

명령 링크만 제거하고 소스는 보존합니다.

```bash
/home/user01/project/iis-skills/observatory/uninstall.sh
```

소스까지 제거하려면:

```bash
/home/user01/project/iis-skills/observatory/uninstall.sh --purge-source
```

## 현재 범위

0.1.0은 Markdown 아티팩트 기반의 포트폴리오 Overview, 상세 상태, 정합성 검사, Git planning history를 완결된 CLI로 제공합니다. 그래프형 Web UI는 이 패키지의 JSON을 소비하는 별도 read-only 화면으로 후속 추가할 수 있습니다. 상태 판정 로직을 Web UI에서 재구현하지 않는 것이 핵심입니다.
