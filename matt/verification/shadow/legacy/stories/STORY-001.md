# STORY-001: Missing Config Exit Code

Story-ID: STORY-001
Project-Root: /home/user01/project/matt/verification/shadow
Planning-Root: /home/user01/project/matt/verification/shadow/legacy
UI: no

## Goal

Make a missing configuration file observable as a CLI failure without changing the error text or successful configuration behavior.

## Acceptance Criteria

- From `project`, `go run . --config missing-config.yaml` exits 2 and writes exactly `configuration file not found` to stderr.
- `project/main_test.go` expects exit code 2 for a missing config and `go test ./...` passes from `project`.
- From `project`, `go run . --config go.mod` still exits 0 and writes `configuration loaded` to stdout.

## Scope

- `project/main.go` missing-config branch.
- `project/main_test.go` missing-config expectation.

## Non-Goals

- UI work.
- Changes to the existing configuration success path.
- Changes to unrelated CLI commands or error handling.

## Verification

- Run `go test ./...` from `project`.
- Check the missing-config stderr and exit code.
- Check the existing-config stdout and exit code.

## Contract and Gate Metadata

- `contractRefs`: `[]`
- `ownershipRows`: `[]`
- `prerequisiteStories`: `[]`
- `validDeferrals`: `[]`
- UX: not-applicable because this Story has no UI or interaction obligation.
