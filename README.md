# Integrated Implementation Skills

This repository snapshots the local workflow from initiative shaping through
planning, implementation result, and optional independent verification.

## Components

- `scope-shaper/`: connected planning-landscape investigation and conditional
  initiative decomposition in one Lead context and one user approval.
- `scope-investigation-runner/`: internal read-only investigation contract used
  only by Scope Shaper with the exact user-designated Runner roster.
- `matt/`: exported from `/home/user01/project/matt` at
  `f96d17367b6eecc425ede0c5a96f2e837aac80a9`
- `implementation-lead/`: implementation of one exact ready local Markdown
  Ticket by a user-designated Implementation Subagent, followed by Lead review
  of the real project diff, implementation checks, and exact unresolved
  limitations. The result is not an independent AC verdict or final `VERIFIED`
  status.
- `verification-lead/`: optional independent verification of one exact ready
  `Independent` Ticket from fresh direct product or canonical-target evidence.
  It does not modify the product or restore a verification runtime, transport,
  store, ledger, or persistent result state.
- `repo-snapshot/`: independent Git working-tree snapshot skill; its credential
  remains outside this repository at `/home/user01/.config/repo-snapshot/token`

The component directories are plain tracked directories. They do not contain
nested Git repositories; versioning is owned by this repository root.
