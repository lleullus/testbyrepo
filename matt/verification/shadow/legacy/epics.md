# Epics

Revision: shadow-v1

## Epic: CLI Configuration Result

### STORY-001: Missing Config Exit Code

Materialized Story: `legacy/stories/STORY-001.md`

Acceptance Criteria:

- A missing configuration path exits 2 and writes exactly `configuration file not found` to stderr.
- The missing-config test expects exit code 2 and `go test ./...` passes from `project`.
- An existing configuration path still exits 0 and writes `configuration loaded` to stdout.

Scope: `project/main.go` missing-config branch and `project/main_test.go` missing-config expectation.

Non-Goals: UI work, existing-config behavior changes, and unrelated CLI changes.

Verification: `go test ./...` from `project`, plus missing-config and existing-config CLI observations.

UX: not-applicable because there is no UI or interaction obligation.
