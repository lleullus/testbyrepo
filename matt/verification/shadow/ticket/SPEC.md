# Missing Config Exit Code

Status: approved
Owner: Shadow verification owner

## Problem

The CLI reports a missing configuration file but exits successfully, so callers can treat the failure as success.

## Desired Outcome

When a configuration file is missing, the CLI exits with code 2 while preserving its exact error text.

## Requirements

- In `project/main.go`, the missing configuration branch returns exit code 2.
- The missing configuration stderr remains exactly `configuration file not found`.
- The existing configuration success path remains unchanged.

## Non-Goals

- UI work.
- Changes to the existing configuration success path.
- Changes to unrelated CLI commands or error handling.

## Implementation Constraints

- The shared Project-Root is `/home/user01/project/matt/verification/shadow`.
- The Go module root is `project`.
- The requested change is not implemented in this baseline.

## Verification Expectations

- Run `go test ./...` from `project`.
- Confirm a missing `--config` path exits 2 with the exact existing stderr after implementation.
- Confirm an existing config exits 0 with stdout `configuration loaded` after implementation.

## UI / UX

Not applicable.

## Open Questions

None
