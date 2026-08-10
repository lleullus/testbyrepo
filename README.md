# Integrated Implementation Skills

This repository snapshots the local workflow from initiative shaping through
planning, implementation, and independent verification.

## Components

- `scope-shaper/`: connected planning-landscape investigation and conditional
  initiative decomposition in one Lead context and one user approval.
- `scope-investigation-runner/`: internal read-only investigation contract used
  only by Scope Shaper with the exact user-designated Runner roster.
- `matt/`: exported from `/home/user01/project/matt` at
  `f96d17367b6eecc425ede0c5a96f2e837aac80a9`
- `implementation-lead/`: implementation of one exact ready local Markdown
  Ticket by a user-designated Implementation Subagent, followed by Lead review
  of the real project diff, implementation checks, and a bounded filtered route
  sidecar for independent verification navigation.
- `verification-lead/`: user-facing verification workflow authority for gate,
  approval, structural validation, bounded remediation authorization, and final
  publication without product-verification semantic fallback.
- `primary-verifier/`: internal sole product-verification semantic owner for AC
  mapping, readiness, Scenarios, direct evidence, verdicts, and affected-AC
  re-verification.
- `repo-snapshot/`: independent Git working-tree snapshot skill; its credential
  remains outside this repository at `/home/user01/.config/repo-snapshot/token`

The component directories are plain tracked directories. They do not contain
nested Git repositories; versioning is owned by this repository root.
