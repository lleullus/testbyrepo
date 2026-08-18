# OMP port contract

## Upstream baseline

- Repository: `annyeong844/lumin-repo-lens`
- Commit: `f7a9cee61d49e06a8350cd125a6b0641a64a59c0`
- Upstream package version: `0.9.0-beta.93`
- OMP port version: `0.9.0-omp.93`

The machine-evidence engine, producer graph, canonical rules, templates,
references, and CLI wrappers are copied unchanged except for host-facing
documentation and plugin-root placeholders.

## Host lifecycle mapping

| Upstream Claude hook | OMP-native equivalent | Behavior |
| --- | --- | --- |
| `UserPromptSubmit` | `before_agent_start` | Drains due evidence reminders into this turn's system prompt |
| `PreToolUse` | `tool_execution_start` | Captures preimages after OMP input revision and immediately before execution |
| `PostToolBatch` | `tool_result` | Runs the same post-write-lite comparison and appends due reminders to the tool result |
| `Stop` | `session_stop` | Observes `AUDIT_ACK` lines in the final assistant message |

OMP's mutation tools are `write` and `edit`. The adapter converts their actual
execution inputs into the existing engine's `Write`/`Edit` hook payload shape.
It supports direct paths, multi-path inputs, nested edit operation arrays, and
`apply_patch` file headers.

Every adapter handler is advisory: failures are logged and never block OMP's
tool execution or session lifecycle.

## Discovery mapping

- `.omp-plugin/marketplace.json` is the preferred OMP catalog.
- Root `package.json#omp.extensions` loads
  `extensions/lumin-repo-lens.ts`.
- `commands/*.md` remain plugin commands, so OMP exposes them as
  `/lumin-repo-lens:<command>`.
- `skills/*/SKILL.md` remain the three original skill surfaces.
- Host-facing command paths use `${OMP_PLUGIN_ROOT}`.

## Dependency behavior

The extension uses light event-store modules without parser setup. On the first
write/edit operation it invokes the upstream dependency guard, which installs
the generated skill package dependencies with the same guarded first-run
behavior as the CLI. Set `LUMIN_REPO_LENS_NO_AUTO_INSTALL=1` to disable this.

## Validation

- `npm run verify`: OMP manifest, extension, commands, skills, and host-specific
  invariant checks
- `npm test`: adapter path extraction and payload mapping
- `npm run smoke`: upstream end-to-end quick audit against a temporary TS repo
- `bun test tests/omp-extension.test.ts`: extension registration surface
- `bun build extensions/lumin-repo-lens.ts`: OMP TypeScript loadability
