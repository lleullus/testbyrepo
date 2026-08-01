# TICKET-001: Missing Config Exit Code

Status: ready
Parent-Spec: SPEC.md
Project-Root: /home/user01/project/matt/verification/shadow
Worker:
UI: no

## Goal

Make a missing configuration file observable as a CLI failure without changing the error text or successful configuration behavior.

## Acceptance Criteria

- From `project`, after `tmpdir=$(mktemp -d)` and `go build -o "$tmpdir/matt" .`, `"$tmpdir/matt" --config missing-config.yaml` exits 2 and writes exactly `configuration file not found` to stderr.
- `project/main_test.go` expects exit code 2 for a missing config and `go test ./...` passes from `project`.
- From `project`, the CLI built at `"$tmpdir/matt"` still exits 0 and writes `configuration loaded` to stdout when run as `"$tmpdir/matt" --config go.mod`.

## Scope

- `project/main.go` missing-config branch.
- `project/main_test.go` missing-config expectation.

## Non-Goals

- UI work.
- Changes to the existing configuration success path.
- Changes to unrelated CLI commands or error handling.

## Blockers

None

## Verification

- Run `go test ./...` from `project`.
- Set `tmpdir=$(mktemp -d)` and run `go build -o "$tmpdir/matt" .` from `project`.
- Check the built CLI's missing-config stderr and exit code.
- Check the built CLI's existing-config stdout and exit code.

## References

- SPEC.md
- ../project/main.go
- ../project/main_test.go
