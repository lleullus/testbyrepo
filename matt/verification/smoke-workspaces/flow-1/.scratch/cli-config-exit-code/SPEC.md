# CLI 설정 파일 부재 시 종료 코드

Status: approved
Owner: 테스트 사용자

## Problem

확인된 disposable CLI의 `main.go`에서 설정 파일이 없을 때 오류가 발생해도 종료 코드 0이 반환되어 호출자가 성공으로 해석할 수 있다.

## Desired Outcome

CLI 설정 파일이 없는 경우 호출자는 기존 오류 문구와 함께 종료 코드 2를 관찰한다.

## Requirements

- CLI 설정 파일이 없으면 종료 코드 2를 반환한다.
- 기존 오류 문구는 변경하지 않는다.
- 관련 없는 CLI 동작은 변경하지 않는다.

## Non-Goals

- UI 변경
- 설정 파일이 존재하는 경우의 CLI 동작 변경
- 관련 없는 CLI 명령 또는 오류 처리 변경

## Implementation Constraints

- 변경은 설정 파일 부재 시의 CLI 결과로 한정한다.
- 확인한 CLI entry와 변경 대상 함수는 `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli/main.go`의 `main`과 `run`이다.
- 확인한 현재 CLI 입력은 `--config <path>`이며, 설정 파일이 없을 때 `run`은 stderr `configuration file not found`를 출력하고 0을 반환한다.
- 확인한 기존 baseline test는 `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli/main_test.go`다.
- 이 문서는 현재 baseline을 수정하지 않으며, Ticket 구현에서 missing config 결과만 2로 변경한다.

## Verification Expectations

- `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli`에서 `go test ./...`를 실행한다.
- 구현 전 baseline 명령 `go run . --config missing-config.yaml`은 stderr `configuration file not found`와 exit code 0을 보인다. 구현 후 같은 명령은 오류 문구를 유지하며 exit code 2를 보여야 한다.
- `go run . --config go.mod`의 설정 파일 존재 성공 경로는 stdout `configuration loaded`와 exit code 0을 유지해야 한다.

## UI / UX

Not applicable

## Open Questions

None
