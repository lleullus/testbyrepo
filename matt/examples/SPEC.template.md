# <제목>

Status: draft
Owner: <사용자 또는 지정된 planning owner>

승인은 사용자 또는 명시된 planning owner가 확인하고, 제품 결정이 모두 해소된 뒤에만 `Status: approved`로 바꾼다. 이 파일은 복사해 직접 편집하는 Markdown 문서이며 별도 metadata나 도구가 필요 없다.

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

완료 시 안정적인 제품·시스템 경계에서 무엇이 관찰되어야 하는지
적는다. 내부 테스트 파일, mock, collaborator 또는 test seam은
미리 고정하지 않는다.

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
Prototype, Design Read, style 선택, 생성 concept는 명시적으로 채택되지 않으면
검토 자료일 뿐 authority가 아니다.

## Open Questions

아직 결정되지 않은 제품·Scope·경계 또는 실현 가능성 결정을 적는다.
어떤 내부 구현 방법이 최선인지 모르는 것만으로는 Open Question이 아니다.
`approved`로 바꾸기 전에는 모두 해소하고 `None`으로 정리한다.
