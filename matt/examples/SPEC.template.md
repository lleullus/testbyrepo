# <제목>

Status: draft
Owner: <사용자 또는 지정된 planning owner>
Source-Increment: None | <project-relative Scope Increment path>

승인은 사용자 또는 명시된 planning owner가 확인하고, 제품 결정이 모두 해소된 뒤에만 `Status: approved`로 바꾼다. Scope Shaper에서 온 작업이면 `Source-Increment`에 해당 Increment의 project-relative canonical path를 적고, 직접 Ask Matt 작업이면 정확히 `None`을 적는다. 이 trace는 미래 Scope를 가져오는 authority가 아니다.

## Problem

해결할 문제와 영향을 받는 대상을 간결하게 적는다. 해결 방법을 먼저 결정하지 않는다.

## Desired Outcome

완료 시 관찰할 수 있는 결과를 적는다.

## Requirements

완료 시 관찰되어야 할 동작, 보존할 기존 동작과 승인된 제품 결정을
적는다. 예상 원인이나 구현 방법은 적지 않는다.

## Non-Goals

이번 범위에서 명시적으로 하지 않을 일을 적는다.

## Implementation Constraints

사용자가 의도적으로 고정한 제품·운영 경계, 외부 호환 계약,
보안·배포 invariant와 변경 허용 범위를 적는다. 예상 파일, 모듈,
endpoint, abstraction, 구현 순서와 test seam은 그 자체가 승인된
요구사항이 아닌 한 적지 않는다.

## Verification Expectations

- Outcome: <observable claim>
  Acceptance boundary: <product or canonical inspection boundary>
  Trigger or inspection target: <product input/trigger or canonical target>
  Expected observable result: <expected result>
  Authoritative readback: <product or canonical readback>
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | <directly established surface>
  External condition: None

각 independently acceptable outcome을 top-level item 하나로 적고 위 core
label을 정확히 한 번 사용한다. Scope가 ordinary product acceptance surface를
만들 책임이 있으면 `Acceptance surface: Ticket Scope creates | <surface>`로
적는다. Confirmed delivery contract가 disposable target과 availability
condition을 실제로 보장할 때만 `Acceptance surface: Delivery contract
guarantees | <disposable target and availability condition>`를 쓴다. 이 값으로
존재하지 않는 sandbox를 추정하거나 사용자 승인을 current-surface evidence로
바꾸지 않는다. Operator-owned path 또는 독립 경계가 없는 확정 outcome은 각각
`Operator-assisted`, `Not independently verifiable`로 적고 실제 external
condition 또는 부재 이유를 보존한다. 독립 검증이 필수이면 두 non-independent
disposition을 사용할 수 없다. Absence, ordering, persistence/lifecycle,
interruption, external effect, UI rendered/interaction 경계는 적용되는
outcome에만 To Spec 계약의 exact conditional label로 추가한다. 미결정 값은
placeholder로 숨기지 않고 Spec을 draft로 유지한다. 내부 테스트 파일, mock,
collaborator, private helper 또는 test seam은 normative boundary/readback으로
고정하지 않는다. Source·artifact·document·structure claim에는 current canonical
target direct inspection을 쓰며 runtime command를 강제하지 않는다.

## Behavior Authorities

- <project-relative local path> | Scope: <exact applicable scope>

승인된 canonical Behavior authority의 경로와 적용 scope만 적는다. Behavior
규칙 자체를 Spec에 복사하지 않는다.

## UI / UX

UI 작업이 아니면 본문 전체를 정확히 `Not applicable`으로 적는다. 새롭거나
material한 UI라면 최신 shared understanding이 명시적으로 채택한, 완전하고
승인된 로컬 UI/UX authority의 exact local path와 적용 rendered scope를 적는다.
상대 경로는 Spec 디렉터리에서 해석한다. Bounded rendered contract에 별도
authority가 없다면 채택된 rendered 결정 또는 직접 보존 조건을 모두 적고,
승인된 이 Spec 자체가 해당 범위의 scoped UI authority임을 명시한다. 어느
authority도 이 Spec의 제품 범위를 확대하거나 뒤집지 않는다.
Prototype, visual reference, style 선택, 생성 concept는 명시적으로 채택되지
않으면 검토 자료일 뿐 authority가 아니다.

## Open Questions

아직 결정되지 않은 제품·Scope·경계 또는 실현 가능성 결정을 적는다.
어떤 내부 구현 방법이 최선인지 모르는 것만으로는 Open Question이 아니다.
`approved`로 바꾸기 전에는 모두 해소하고 `None`으로 정리한다.
