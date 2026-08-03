# Integrated Implementation Skills

This repository snapshots the local workflow from initiative shaping through
planning, implementation handoff, independent verification, and bounded
verification-triggered remediation.

## Components

- `project-shaper/`: copied from `/home/user01/project/project-shaper`
- `matt/`: exported from `/home/user01/project/matt` at
  `f96d17367b6eecc425ede0c5a96f2e837aac80a9`
- `implementation-lead/`: exported from `/home/user01/project/implement_lead`
  at `63892defd5e8f2bc0a03077ef3daf5ba0112481a`
- `verification-lead/`: owner-controlled sealed verification runs,
  `verification-result-v1`, linear workflow continuation, and remediation
  coordination. Its PROCESS executor v3 binds executable identity and uses a closed environment as the current conformance MVP.
- `baseline-capsule/`: required Implementation Lead support module, exported
  from `/home/user01/project/baseline-capsule` at
  `ffb6ff36df9788cb777aae06ccf847d03f29fe5f`
- `repo-snapshot/`: independent Git working-tree snapshot skill; its credential
  remains outside this repository at `/home/user01/.config/repo-snapshot/token`

The component directories are plain tracked directories. They do not contain
nested Git repositories; versioning is owned by this repository root.
