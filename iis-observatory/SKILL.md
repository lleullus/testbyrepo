---
name: iis-observatory
description: Use for read-only IIS project/portfolio state, current Scope, remaining required outcomes, source drift, history and next-work inspection. A reported next pointer never authorizes execution.
---

# IIS Observatory

Use `/home/user01/project/iis-skills/observatory/bin/iis-observatory` as the canonical read-only interface for IIS portfolio and repository state inspection.

## Commands

For a cross-repository overview, run:

```bash
/home/user01/project/iis-skills/observatory/bin/iis-observatory overview /home/user01/project
```

For one repository, run:

```bash
/home/user01/project/iis-skills/observatory/bin/iis-observatory scan <repo>
```

For a durable repository-local derived snapshot, run:

```bash
/home/user01/project/iis-skills/observatory/bin/iis-observatory snapshot <repo> --write
/home/user01/project/iis-skills/observatory/bin/iis-observatory snapshot <repo> --check
```

`--write` may refresh only the derived `docs/planning/observatory/PROJECT-OVERVIEW.md` and `project-state.json`, never source authority. Current Scope state and incomplete required outcomes remain distinct from archived Ticket/Increment history; historical ratios do not prove current product completion.

For artifact consistency checks, run:

```bash
/home/user01/project/iis-skills/observatory/bin/iis-observatory doctor <root-or-repo>
```

For Git-backed planning history, run:

```bash
/home/user01/project/iis-skills/observatory/bin/iis-observatory history <repo>
```

Use `--format json` when machine-readable state is more useful than terminal rendering.

## Boundary

Treat Observatory as a read model of existing `docs/planning/**` artifacts. Do not change Thesis, transition contracts, Scope or historical Spec/Ticket/Increment sources. The explicit `snapshot --write` exception writes derived Observatory files only. Do not select a Scope, plan, implement or verify from a next-work suggestion. Legacy incomplete work requires an explicit current transition decision, not automatic execution; an old Mandate or active marker is not a new request.

An explicit continuation request leaves read-only Observatory and enters the same IIS Main under the user's current scope and stop instructions.

If the CLI cannot run, inspect the exact sources read-only and state the CLI limitation. Do not invent current state or invoke a removed planning fallback.
