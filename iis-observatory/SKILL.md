---
name: iis-observatory
description: Use when the user asks to inspect, summarize, compare, or visualize IIS planning state across one or more repositories, including IIS PROJECT OVERVIEW, repository health, current planning position, remaining Tickets, blockers, inconsistencies, history, or the next planning/delivery pointer. Use the read-only IIS Observatory CLI and never treat status inspection as permission to execute the reported next work.
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

Treat Observatory output as a read-only projection of existing `docs/planning/**` artifacts. Do not modify Scope, Work Package, Increment, Spec, or Ticket artifacts as part of inspection. Do not start Scope Shaper, Ask Matt, To Spec, To Tickets, implementation, or verification merely because Observatory reports that leaf as next.

For an explicit request to continue or execute the reported next work, leave Observatory and route the new request through the appropriate planning or delivery skill.

If the CLI cannot run, fall back to the `iis-workflow` Current Planning State Check contract rather than inventing state.
