# Click provenance

This runtime is a behavior-level reimplementation of selected execution-control ideas inspected in the local Click reference checkout at `/home/user01/project/click-upstream`.

- inspected plugin metadata version: `0.17.0`
- reference license: MIT
- copied Click source files: none
- selected meanings: observation anti-loop, repository-wide rescan guard, mutation revision/currentness, structured argv without a shell, atomic state/lock discipline
- deliberately excluded: Click execution contract, approval flow, Always ON/Manual modes, Fix, review mode, planning UX, verification budgets/meters, and global software-mutation guarding

The original implementation plan referred to a v0.20 line, but the available checkout and plugin metadata identify v0.17.0 and contain no local `v0.20*` tag. Provenance records the version actually inspected.

See `docs/engineering/ready-runtime/click-feature-selection.md` in the repository for the feature selection rationale.
