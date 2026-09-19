# IIS Observatory

IIS Observatory는 여러 저장소의 IIS planning 아티팩트를 읽어 현재 위치, Ticket 진행 상태, 다음 작업, 정합성 문제를 한 화면에 보여주는 **읽기 전용 관측 도구**입니다.

```text
IIS PROJECT OVERVIEW
────────────────────────────────────────────────────────────────────────────
Repository         Unit                         State       Next
────────────────────────────────────────────────────────────────────────────
tax                Scope · VAT readback        PLANNING    Plan
ima2               Scope · Job inspection      COMPLETE    Scope Shaper
legacy-api         legacy history              STALE       transition required
oracle              Scope · Browser slot        INCONSISTENT Check consistency
────────────────────────────────────────────────────────────────────────────
Planning 2   Inconsistent 1   Complete 1   Stale 1
```

`Unit`은 별도 요약을 생성하지 않습니다. Increment가 있으면 `INC-NNN · <Increment authored heading>`, Work Package만 있으면 `WP-NNN · <Work Package authored heading>`, direct-work이면 `work · <Spec authored heading>`을 사용하고 터미널 폭에서만 잘라냅니다.

## 설계 원칙

- 현재 권위는 각 저장소의 `docs/planning/work/<slug>/SCOPE.md` (`Schema: iis-scope/v2`)입니다.
- Scope는 executor-owned fixed Thesis ref를 `Product Authority`에 바인딩합니다. 승인된 전환 계약이 현재 Scope에 실제 적용될 때만 선택적인 `Transition Authority`를 같은 방식으로 표시합니다. Observatory는 이 ref의 closure/admission을 인증하지 않습니다.
- Scope 상태는 `draft`, `ready`, `done`, `superseded`입니다. `superseded`는 소비되지 않은 대체 계약의 기록이며 자동 재개하지 않습니다.
- Observatory는 상태 DB나 workflow ledger를 만들지 않고 매 실행마다 Markdown을 다시 계산합니다.
- 기존 Scope Shaping/Increment/Spec/Ticket은 read-only 역사입니다. 직접 Scope가 있으면 현재 권위나 Matt/Ticket 다음 작업으로 재사용하지 않으며, 미완료 항목은 `transition required`로만 표시합니다.
- 에이전트용 JSON과 사람용 Overview는 동일한 판정 로직을 사용합니다. 모든 `Next`/`Next leaf`는 조회 포인터이며 구현·Plan·검증·전환을 실행하거나 허가하지 않습니다.

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
Authority mode: direct Thesis → Scope
Current Scope: VAT readback [docs/planning/work/vat-readback/SCOPE.md]
Scope Status: ready
Bound Thesis refs: snap-...:docs/planning/product-thesis/... (admission not checked)
Required Outcomes — fulfillment not established: <unassessed named requirements>
Next Work: none established
Next leaf: delivery state not established
Health: PLANNING
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

이 파일들은 canonical IIS authority가 아닙니다. Scope, Work Package, Increment, Spec, Ticket을 변경하거나 다음 leaf를 실행하지 않습니다. 저장된 입력 원문과 현재 입력 원문이 같으면 `Action: UNCHANGED`로 끝나며 파일/mtime도 바꾸지 않습니다.

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

결과는 `CURRENT`, `STALE`, `MISSING`, `INCONSISTENT` 중 하나입니다. Freshness는 Git HEAD가 아니라 canonical planning 입력, 표시되는 Scope/legacy 이력 파일과 Adaptive provenance의 저장된 원문을 현재 원문과 직접 비교해 판정합니다. 표시 이력의 추가·수정·삭제도 갱신 대상이며, `docs/planning/observatory/**` 자체와 무관한 제품 코드는 제외합니다. `CURRENT`는 이 파생 상태판의 최신성이지 과거 `done` Scope의 현재 runtime 정상 동작 보장이 아닙니다.

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

- `SCOPE.md`의 Schema/Project-Root/필수 섹션 누락
- Product/Transition source ref 형식이 잘못됐거나 중복됨. 실제 fixed-source currentness와 Product Thesis closure는 admission에서 판정
- `draft|ready` direct Scope가 둘 이상임 (`IIS502`)
- `ready`/`done` Scope의 unresolved Open Decisions
- 존재하지 않는 로컬 planning Markdown 링크
- legacy Scope/Increment/Spec/Ticket 미완료 항목 (`Transition Required`, 자동 이행 없음)

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

현재 Scope는 `docs/planning/work/*/SCOPE.md` 중 다음 규칙으로 찾습니다.

1. `Status: draft|ready`인 active Scope가 하나면 그것을 current로 표시합니다.
2. active Scope가 둘 이상이면 `IIS502`와 `INCONSISTENT`를 표시하며 어느 것도 자동 선택하지 않습니다.
3. active Scope가 없으면 최신 `done` Scope를 read-only current로 표시합니다.
4. `superseded`만 남으면 `STALE`/`transition required`로 표시하고 새 Scope를 자동 생성·승격하지 않습니다.

`draft`는 Scope Shaper를 가리킵니다. `ready`만으로는 Plan 전인지 구현 후 검증 대기인지 알 수 없으므로 정확한 다음 단계는 미확정으로 표시합니다. `done`은 그 Scope의 기록일 뿐입니다. 필수 결과의 충족 여부는 문구 일치로 추측하지 않고 `unassessed`로 남기며 현재 증거와의 대조가 필요함을 표시합니다. 조회는 실행 허가가 아닙니다.

`Product Authority`/`Transition Authority`의 v2 source-ref 구조가 잘못되면 inconsistency로 표시하고, active Scope 중복은 `IIS502`/`INCONSISTENT`입니다. Observatory는 fixed-source currentness나 lifecycle closure를 판정하지 않으며 존재만으로 mandate·baseline 활성화를 추론하지 않습니다.

기존 `SCOPE-SHAPING-RESULT.md`, Work Package, Increment, Spec, Ticket은 `Legacy History`로만 표시합니다. 미완료 legacy 항목에는 `Transition Required`를 붙이고 자동 이행하지 않습니다. 기존 artifact의 `ready-for-matt`, `Ask Matt`, `To Spec`, `To Tickets`, Ticket 구현 pointer는 direct Scope 모드에서 제안하지 않습니다.

## 인식하는 기본 구조

```text
<repository>/
└── docs/planning/
    ├── product-thesis/<meaning-slug>/THESIS-NNN.md
    ├── work/<work-slug>/
    │   ├── SCOPE.md
    │   └── PLAN.md                 # methods only; Observatory does not execute it
    └── ... legacy planning ...     # read-only history during cutover
```

`SCOPE.md`의 최소 canonical 형태는 다음과 같습니다.

````markdown
# <현재 완성할 결과>
Schema: iis-scope/v2
Project-Root: /absolute/project/root
Status: draft | ready | done | superseded

## Product Authority
```iis-sources
[
  {"snapshot":"snap-<executor-id>","path":"docs/planning/product-thesis/example/THESIS-001.md"}
]
```

## Transition Authority       # approved transition contract가 적용될 때만
```iis-sources
[
  {"snapshot":"snap-<executor-id>","path":"docs/planning/transition/BASELINE-001.md"}
]
```

## Outcome
...

## Acceptance
...
````

`Product Authority`는 하나 이상의 executor-owned Thesis ref여야 합니다. `Transition Authority`는 선택적이며 같은 ref 형식을 사용합니다. Observatory는 이 ref의 admission eligibility를 판정하지 않습니다. `Open Decisions`는 `ready`/`done` Scope에서 `None`이어야 합니다.

구 `scope-shaping/**`, `SPEC.md`, `tickets/**`는 새 권위 구조로 자동 변환하지 않습니다. 필요하면 `scan`/`doctor` 결과의 `Transition Required`를 읽고 별도 Scope를 작성합니다.

## 상태 의미

| Health | 의미 |
|---|---|
| `PLANNING` | direct Scope가 draft/ready이거나 done 이후에도 필수 결과 충족 여부가 미확정입니다. ready의 정확한 전달 단계는 별도 현재 증거가 필요합니다. |
| `NEEDS SCOPE` | canonical planning root에는 direct Scope가 없고 새 Scope가 필요합니다. |
| `INCONSISTENT` | Scope schema/source-ref 구조가 깨졌거나 active Scope가 중복됩니다. |
| `COMPLETE` | current Scope가 done이고 명시된 미확정 필수 결과가 관찰되지 않았습니다. 전체 사용자 요청 완료를 뜻하지 않습니다. |
| `STALE` | 현행 Scope가 없는 역사 기록입니다. 미완료 legacy 작업이나 superseded-only 상태는 전환 판단이 필요하지만 완료 역사만으로는 이행을 요구하지 않습니다. |
| `NO_IIS` | 저장소에 `docs/planning`이 없습니다. |

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

0.4.0은 `iis-scope/v2` source-ref projection, direct-input snapshot freshness, 포트폴리오 Overview, 상세 상태, 정합성 검사, Git planning history를 제공합니다. 그래프형 Web UI는 이 패키지의 JSON을 소비하는 별도 read-only 화면으로 후속 추가할 수 있습니다. 상태 판정 로직을 Web UI에서 재구현하지 않는 것이 핵심입니다.
