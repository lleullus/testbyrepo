# TICKET-001: 설정 파일 부재 CLI 종료 코드 수정

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/matt/verification/smoke-workspaces/flow-1
Worker:
UI: no

## Goal

설정 파일이 없는 CLI 실행을 실패로 식별할 수 있게 종료 코드 2를 반환한다.

## Acceptance Criteria

- `go run . --config missing-config.yaml`이 stderr `configuration file not found`를 유지한 채 exit code 2를 반환한다.
- `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli/main_test.go`의 missing config baseline test가 exit code 2를 기대하도록 갱신되고 `go test ./...`가 통과한다.
- `go run . --config go.mod`이 stdout `configuration loaded`와 exit code 0을 유지한다.

## Scope

- `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli/main.go`의 설정 파일 부재 분기 종료 코드
- `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli/main_test.go`의 해당 baseline expectation

## Non-Goals

- UI 변경
- 설정 파일이 존재하는 경우의 CLI 동작 변경
- 관련 없는 CLI 명령 또는 오류 처리 변경

## Blockers

None

## Verification

- `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli`에서 `go test ./...`를 실행한다.
- `go run . --config missing-config.yaml`로 exit code 2와 오류 문구 보존을 확인한다.
- `go run . --config go.mod`으로 설정 파일 존재 성공 경로를 확인한다.

## References

- ../SPEC.md
- ../../../disposable-cli/main.go
- ../../../disposable-cli/main_test.go
