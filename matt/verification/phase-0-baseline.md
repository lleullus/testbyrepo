# Phase 0 Baseline

## Scope

Task 0-1 only. This record captures the observable state before subsequent Matt work. No Task 0-2 upstream checkout, copy, or other later task was started.

## Observation

- Observation time: `2026-07-28T10:38:20+09:00`
- `matt` parent check: `ls -ld "/home/user01/project/matt"` confirmed that `/home/user01/project/matt` existed before `verification/` was created.
- Pre-write Matt root listing: exactly `matt-skills-lean-planning-implementation-lead-workplan.md`.
- Pre-write artifact check: no paths matched `verification` or `**/{validator*,*validator*,fixture*,*fixture*,evidence*,*evidence*,contract*,*contract*,dist,build,out,target}` under `/home/user01/project/matt`.
- Therefore, the observed start state contained no prior validator, evidence, fixture, contract, or build artifact. The only file was the workplan.

## Implementation Lead

Read-only command executed in `/home/user01/project/implement_lead`:

```text
date --iso-8601=seconds && sha256sum SKILL.md && git status --short --branch
```

- `SKILL.md` raw-byte SHA-256: `d6615f6048cf8612bb28e0678c7871edf525f59e942600197aa15ec742c641e9`
- Exact Git status summary:

```text
## main
 M SKILL.md
?? .ai-bridge/
```

The pre-existing modified `SKILL.md` and untracked `.ai-bridge/` directory were not changed, restored, staged, or deleted.

## Global Skill Inventory

The current OpenCode configuration at `/home/user01/.config/opencode/opencode.json` declares these `skills.paths`: `/home/user01/skills/obsidian`, `/home/user01/.codex/skills/bmad`, and `/home/user01/.codex/skills`.

- `/home/user01/.codex/skills`: `.system`, `000-codexpro-global-stress-1784986796335`, `bloger`, `bmad`, `bmad-story-closure-audit`, `codexpro-launcher`, `expert-apprenticeship-coach`, `gws`, `ima2`, `ima2-front`, `ima2-prompt`, `ima2-uiux`, `implementation-lead`, `judgment-apprenticeship-designer`, `naver-cafe-scraper`, `oracle-browser`, `repo-snapshot`, `spine`, `superloopy-clone`, `superloopy-frontend`, `tax-usage`, `triage`.
- `/home/user01/.codex/skills/bmad`: `bmad-architecture`, `bmad-brainstorming`, `bmad-check-implementation-readiness`, `bmad-correct-course`, `bmad-create-epics-and-stories`, `bmad-create-story`, `bmad-help`, `bmad-planning-admission`, `bmad-prd`, `bmad-product-brief`, `bmad-project-init`, `bmad-technical-research`, `bmad-ux-bridge`.
- `/home/user01/.agents/skills`: `dks-n`; `dks-tech-review-writer` is an empty directory at observation time.
- `/home/user01/skills/obsidian`: `json-canvas`, `obsidian-bases`, `obsidian-markdown`, `obsidian-orphan-folder-guide`, `obsidian-project-prose-governor`, `obsidian-vault-humanizer`, `obsidian-wiki-governor`.
- `/home/user01/.config/opencode/skills`: `ttageo`.

No global skill was installed, deleted, or modified during this task.

## Verification Boundary

The observations above establish only the current filesystem state at the stated time and the absence of mutations by this Task 0-1 work. They do not prove the historical claim that the prior deletion operation never changed `/home/user01/project/implement_lead` or any global skill: no before-delete snapshot, audit trail, or repository history for every observed skill path was examined, and no deleted artifacts were searched for or recovered. A future comparison can use this file's `SKILL.md` hash, exact Git status, and inventory as its baseline.
