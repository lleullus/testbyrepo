# Integrated Implementation Skills

This repository snapshots the local workflow from initiative shaping through
planning, implementation handoff, independent verification, and bounded
verification-triggered remediation.

## Components

- `project-shaper/`: copied from `/home/user01/project/project-shaper`
- `matt/`: exported from `/home/user01/project/matt` at
  `f96d17367b6eecc425ede0c5a96f2e837aac80a9`
- `implementation-lead/`: one exact ready local Markdown Ticket through the
  Implementation Verification Module with the fixed Terra Worker designation.
- `verification-lead/`: independent verification of a Candidate through the
  Implementation Verification Module with the fixed fresh Luna verifier.
- `implementation-verification/`: the Module contract — `implement`, `verify`,
  and `inspect` — with Terra/Luna worker routing and a fail-closed production
  scope (authenticated reads and production effects unsupported).
- `repo-snapshot/`: independent Git working-tree snapshot skill; its credential
  remains outside this repository at `/home/user01/.config/repo-snapshot/token`

The component directories are plain tracked directories. They do not contain
nested Git repositories; versioning is owned by this repository root.
