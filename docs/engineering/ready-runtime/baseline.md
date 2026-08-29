# Ready Runtime Baseline

## Worktree

- Source repository: `/home/user01/project/iis-skills`
- Source HEAD: `3795dcc75201c7851830d3d00ae2cb5c21ad49de`
- Branch: `refactor/ready-implement-click-runtime`
- Worktree: `/home/user01/project/iis-skills-wt-ready-click-runtime`
- Source worktree status before implementation: clean

## Baseline tests

Command:

```text
python3 run_tests.py
```

Result before source changes:

- Tests run: 224
- Passed: 223
- Failed: 1
- Existing worktree-local failure: `test_global_cli_link_targets_canonical_observatory`
- Failure boundary: the globally installed `iis-observatory` CLI resolves to `/home/user01/project/iis-skills/observatory/bin/iis-observatory`, while the test executed from this new worktree expects the worktree-local canonical path. No Ready runtime source had been changed when this baseline was captured.

This failure is retained as baseline evidence and is not treated as a Ready runtime regression unless its behavior changes because of this branch.
