# Phase 2 Shadow Comparison

## Observation

- Observation time: `2026-07-28T14:04:08+09:00`.
- Matt HEAD: `7210f48adfe9cb0fc804e499b1f55c64d4a51340` (`Connect Ticket planning to execution core`), clean before shadow materialization.
- Legacy baseline contract: `/home/user01/project/implement_lead.pre-phase2-20260728/SKILL.md`, SHA-256 `d6615f6048cf8612bb28e0678c7871edf525f59e942600197aa15ec742c641e9`.
- Staged candidate: `/home/user01/project/matt/staging/implementation-lead/` at the same Matt HEAD; `SKILL.md` SHA-256 `cac3f5704adbf3eaebec7797c355dc49112845c5950a099f4e6412e1ef39dde4`.
- Both paths use Project-Root `/home/user01/project/matt/verification/shadow`; the shared Go module root is `/home/user01/project/matt/verification/shadow/project`.
- Selected test operator Worker: `openai-gpt5.6-terra-xhigh`. It is named only for this shadow comparison, is available in the current agent catalog, and was not called.

## Fixture Paths And Commands

- Baseline module: `verification/shadow/project/go.mod`, `verification/shadow/project/main.go`, and `verification/shadow/project/main_test.go`.
- Legacy input: `verification/shadow/legacy/stories/STORY-001.md` and `verification/shadow/legacy/planning-admission/by-story/sha256/487b23e65bb7785137d25bbad5feab594db4ecd79a93a70e0ad84da043265374.md`.
- New input: `verification/shadow/ticket/SPEC.md` and `verification/shadow/ticket/TICKET-001.md`.
- Shared baseline command, run from `verification/shadow/project`:

```bash
go test ./...
go run . --config missing-config.yaml
go run . --config go.mod
```

`go test ./...` passed. The first CLI command exited 0 and wrote exact stderr `configuration file not found`; the second exited 0 and wrote `configuration loaded`. The requested exit-code change is not implemented.

- Legacy target key command:

```bash
printf '%s' 'STORY-001' | sha256sum
```

Result: `487b23e65bb7785137d25bbad5feab594db4ecd79a93a70e0ad84da043265374`.

- Legacy identity commands, run from the Matt root with `root=verification/shadow`:

```bash
{ for path in legacy/ARCHITECTURE-SPINE.md legacy/CAPABILITY-MATRIX.md legacy/PRD.md legacy/SCHEMA-MIGRATION-REGISTRY.md legacy/STATE-TRANSITION-MATRIX.md legacy/epics.md legacy/story-dependency-ownership-matrix.md legacy/stories/STORY-001.md; do printf '%s\0%s\n' "$path" "$(sha256sum "$root/$path" | cut -d ' ' -f1)"; done; } | sha256sum
printf 'STORY-001\0legacy/stories/STORY-001.md\0%s\n' "$(sha256sum "$root/legacy/stories/STORY-001.md" | cut -d ' ' -f1)" | sha256sum
```

- Ticket seal command, run from the Matt root:

```bash
sha256sum verification/shadow/ticket/TICKET-001.md verification/shadow/ticket/SPEC.md
```

## Legacy Admission Preflight

The legacy Planning-Root locator is not specified by the backup `SKILL.md`. The fixture therefore uses explicit local Story metadata `Planning-Root: /home/user01/project/matt/verification/shadow/legacy`. This is a disclosed local interpretation, not an inferred legacy syntax. It resolves the canonical report path exactly as required by the backup preflight.

| Predicate | Result |
| --- | --- |
| Exact Story identity and target path | Pass. `STORY-001` has no NUL/LF; its SHA-256 target key is the canonical report filename. |
| Schema and target result | Pass. The canonical report has `artifact: planning-admission`, schema version 2, target `STORY-001`, `closure.algorithm: exact-slice-worklist-v1`, `closure.result: ready`, and `admission.result: pass`. |
| Detailed Story closure | Pass. `assessedDetailedStoryIds` is the sorted, duplicate-free one-item sequence `[STORY-001]`; the materialization matrix resolves it once to `legacy/stories/STORY-001.md`. No support Story is present. |
| Boundary closure | Pass. `assessedBoundaryObligationIds: []`; the ownership matrix declares no shared obligation or prerequisite. |
| Project and planning roots | Pass. The report values equal the current resolved real paths for the shadow root and `legacy/` planning root. |
| Source map and source bundle | Pass. Eight safe, unique regular files are project-relative and their current raw SHA-256 values equal the report map. Recomputed `source-bundle-v1` is `3c3bbf02978ffd151aec6a10f32f7d9cf92621b4c36a8a76d2c89be73d5a9933`. |
| Story set | Pass. Recomputed `story-set-v1` is `dfd7f09c2d9293d406771b099eab1113d6b7645fe15a99decade4b56b0b2eaef`. |
| UX and external claims | Pass. The Story is non-UI; report UX is `not-applicable` with rationale. `externalClaims: []` is valid and creates no external recheck. |
| Sealed report identity | Pass. Canonical report raw SHA-256 is `062a9d2fbda9e25f8b9dc59c9c0dc39f8208110e31814c05f9d1f4132a19c42a`. |

The legacy fixture contains the minimum one-target authority set: PRD, Architecture Spine with Contract Freeze Index, state/schema/capability registries, epics, ownership matrix, one materialized Story, and one target report. The source authority is mutually consistent on AC, scope, non-goals, verification, non-UI status, and the shared Go module root.

Limitation: this is a direct human comparison against the backup preflight predicates and raw-byte algorithms. No legacy Planning Admission producer or Worker was invoked, and no new parser or validator was created.

## New Ticket Preflight

`TICKET-001.md` has exact `Status: ready`, `Parent-Spec: SPEC.md`, non-empty observable AC, a canonical Project-Root containing its parent Spec, blank planning-only `Worker:`, `UI: no`, and exact one-line `Blockers` body `None`. `SPEC.md` has exact `Status: approved`, a non-empty Owner, all eight required sections, and `Open Questions` body `None`.

The Ticket preserves the approved Spec's change, scope, non-goals, and verification. It adds no UI authority and no new product decision. The same invocation Worker is the sole Worker authority; the blank Ticket Worker value was not consumed.

PlanningInputSeal captured after readiness preflight:

```text
ticketPath: /home/user01/project/matt/verification/shadow/ticket/TICKET-001.md
ticketSHA256: 3493e0b37db0aad59c4d28a94245f4ddae86d68d8ed14fd5accc0d657c73d414
specPath: /home/user01/project/matt/verification/shadow/ticket/SPEC.md
specSHA256: 497dbea5d291b4afa66d5a8b8541ae511c16f1a5b330c951933b7281a46b060b
blockerFiles: []
```

The first-Worker `planning_input_current` comparison was manually repeated against the same invocation paths, raw bytes, parent-Spec resolution, and empty blocker list. It is true. The values above are report content only, not a separate seal artifact or evidence class.

## Go Adapter Preflight And Native Baseline

The active Adapter source was read-only at `/home/user01/project/implement_lead/adapters/go`. All generated artifacts are under `/tmp/opencode/implementation-lead/phase2-shadow/`; no binary, manifest, context, or Adapter report was written to Matt or the shadow project.

Commands run:

```bash
go version
bwrap --version
GOTOOLCHAIN=local go -C /home/user01/project/implement_lead/adapters/go build -trimpath -o /tmp/opencode/implementation-lead/phase2-shadow/go-adapter ./cmd/go-adapter
go version -m /tmp/opencode/implementation-lead/phase2-shadow/go-adapter
sha256sum /tmp/opencode/implementation-lead/phase2-shadow/go-adapter
git -C /home/user01/project/implement_lead/adapters/go rev-parse HEAD
git -C /home/user01/project/implement_lead/adapters/go status --porcelain=v2 --untracked-files=all
git -C /home/user01/project/implement_lead/adapters/go diff --binary -- . | sha256sum
/tmp/opencode/implementation-lead/phase2-shadow/go-adapter manifest --project /home/user01/project/matt/verification/shadow/project > /tmp/opencode/implementation-lead/phase2-shadow/legacy-root-manifest.json
/tmp/opencode/implementation-lead/phase2-shadow/go-adapter manifest --project /home/user01/project/matt/verification/shadow/project > /tmp/opencode/implementation-lead/phase2-shadow/ticket-root-manifest.json
```

- Runtime availability: `go version go1.21.13 linux/amd64`; `bubblewrap 0.9.0`.
- Binary identity: `/tmp/opencode/implementation-lead/phase2-shadow/go-adapter`, SHA-256 `765a14413fb39e8d661dcd5cbd932245b9cccbb45eaa97d1177eda079c6229c6`. `go version -m` records Go `go1.21.13`, `-trimpath=true`, `linux/amd64`, VCS revision `6ab0186ef24a63f91a1374366b09cea7cbfc08ea`, and `vcs.modified=true`.
- Adapter source identity: Git HEAD `6ab0186ef24a63f91a1374366b09cea7cbfc08ea`; adapter-scoped `git diff --binary -- .` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. The source identity captured the pre-existing repository-level modified `SKILL.md` and untracked `.ai-bridge/blogger-post.html`; neither was changed.
- Target module ownership: `project/go.mod` declares `go 1.21`, contains no `toolchain` or `replace`, and has no `go.work`, `go.sum`, or `vendor` path. `GOTOOLCHAIN=local go -C /home/user01/project/matt/verification/shadow/project env GOTOOLCHAIN GOVERSION GOMOD GOWORK` returned `local`, `go1.21.13`, the exact project `go.mod`, and an empty workspace. The target has no dependency, build-constraint, or CGO/native prerequisite beyond the standard-library CLI source. `GOTOOLCHAIN=local` was used for the build and target environment probe, so no implicit toolchain download was permitted.
- Legacy manifest: `/tmp/opencode/implementation-lead/phase2-shadow/legacy-root-manifest.json` returned root `/home/user01/project/matt/verification/shadow/project` and digest `240c40f7d4eb914ceebcffcfb1f9fed65c5a8ff285a3eeae4bcb56e94aa3dffd`.
- Ticket manifest: `/tmp/opencode/implementation-lead/phase2-shadow/ticket-root-manifest.json` returned the same root and digest `240c40f7d4eb914ceebcffcfb1f9fed65c5a8ff285a3eeae4bcb56e94aa3dffd`. The two JSON outputs have the same raw SHA-256 `01434f5de5829ff40b5a6fa97c1eaffc49e30369cc5f1977bdb3c1ab857d6a62`.
- Product-mutation check: before and after SHA-256 values match for `project/go.mod` (`2dddfe668902daaef8a957fc932f8155ec8f430f74f220332a4071b22351fc6c`), `project/main.go` (`3002f86cd32473075736a2c0457cf7ea2a570b74be3b06eb34c7e67e274c86f3`), and `project/main_test.go` (`71a14cb5ae45c586f196a186c7c6cdb95d3dab0bc5fe1833034bafbc9cd9ff20`).

The two manifest outputs and build metadata are run-scoped diagnostic preflight artifacts, not implementation evidence or a new evidence class. No context JSON was created; Go Fast and Full were not invoked.

## Preflight And Decomposition Comparison

| Aspect | Legacy Story path | New Ticket path | Comparison |
| --- | --- | --- | --- |
| Implementation scope | Change the missing-config return in `project/main.go`; update its expectation in `project/main_test.go`. | Same. | Equal. |
| AC coverage | One bounded task covers AC 1 missing-config exit/text, AC 2 test update and `go test`, and AC 3 existing-config success preservation. | Same one bounded task and same mapping. | Equal. |
| Proposed task | Update only the missing-config branch from return 0 to return 2 and the matching test expectation; preserve all other behavior. Canonicals: `project/main.go` `run` and `project/main_test.go` `TestRun`, both `extend`. | Same. | Equal. |
| Mutation envelope | Allowed: `project/main.go`, `project/main_test.go`. Forbidden: every other path, including planning and Adapter paths. | Same. | Equal. |
| Dependencies and blockers | No dependency/support Story or boundary obligation; no planning blocker. | `Blockers: None`; no parent-Spec open question. | Equal outcome; the source of the decision changes with the input contract. |
| UI | Non-UI, UX contract not-applicable. | `UI: no`; no UI reference consumed. | Equal. |
| Applicable Adapter and native state | Go only. The verified temp binary built with local Go and `bwrap` available; legacy manifest digest is `240c40f7d4eb914ceebcffcfb1f9fed65c5a8ff285a3eeae4bcb56e94aa3dffd`. | Go only. The same verified binary and availability condition produced ticket manifest digest `240c40f7d4eb914ceebcffcfb1f9fed65c5a8ff285a3eeae4bcb56e94aa3dffd`. | Equal. The root-state outputs are byte-identical and match the unchanged common project. `go test ./...` remains baseline validation, not Adapter Fast evidence. |
| Worker | Invocation-selected `openai-gpt5.6-terra-xhigh`; same availability condition and no fallback. | Same. | Equal. |
| Input-currentness gate | `planning_admission_current` would compare the sealed canonical report, source bundle, and story set. All are current at this shadow stop. | `planning_input_current` compares the captured Ticket/Spec bytes and paths. It is true at this shadow stop. | Explained replacement of input-currentness contract. |
| Dispatch judgment immediately before Worker | `planning_admission_current`, AC mapping, frozen two-path envelope, clear ownership, exact Worker availability, and native root identity are satisfied. Initial dispatch is authorized. | `planning_input_current`, AC mapping, frozen two-path envelope, clear ownership, exact Worker availability, and native root identity are satisfied. Initial dispatch is authorized. | Equal. Each task remains `PENDING` and stops immediately before the Worker call by this shadow boundary; Worker calls are 0. |

## Preserved Execution Rules

| Rule | Result |
| --- | --- |
| Selected Worker is sole product mutator; Lead does not edit product paths | Preserved. Both paths leave the task `PENDING`; no Worker call and no implementation mutation occurred. |
| Ownership, frozen envelope, actual-delta review, and Canonical obligations | Preserved. The identical two-path envelope and Canonicals are recorded before the intentional stop; no envelope was widened. |
| Adapter-native evidence and evidence lifetime | Preserved. Go `manifest` ran twice as native preflight; no context, Fast, or Full evidence was created or claimed. |
| Full gate | Preserved. No task was accepted, so Full entry is prohibited; no Full evidence or exception was created. |

## Runtime Lookup And Fixture Reuse Observation

- Candidate runtime term search: `rg -n -i '\b(bmad|story|admission)\b' staging/implementation-lead --glob '*.md'` produced zero matches. The staged candidate contains only Markdown runtime-contract files and performs no BMAD, Story, or Admission lookup.
- Current reusable-fixture observation: `/home/user01/project/implement_lead` and `/home/user01/.codex/skills/implementation-lead` contain no reusable Planning Admission fixture; their broad filename matches were only the `references/ui-story.md` reference. `/home/user01/.codex/skills/bmad` contains Planning Admission and ownership templates, not a materialized reusable fixture. No existing fixture was copied or reused.
- Active `/home/user01/project/implement_lead/SKILL.md` and backup `/home/user01/project/implement_lead.pre-phase2-20260728/SKILL.md` both remain SHA-256 `d6615f6048cf8612bb28e0678c7871edf525f59e942600197aa15ec742c641e9`.

## Result

Pass. The semantic decomposition and native baseline identity are identical. Every observed difference is solely the authorized input-contract replacement: legacy Story plus target-specific Planning Admission versus ready Ticket plus approved parent Spec and PlanningInputSeal. Unexplained differences: 0.

Product implementation mutations: 0. The disposable Go files are the intentionally unchanged shadow baseline; the requested return-code change was not applied. Worker calls: 0. Go Adapter manifest preflight invocations: 2. Go Fast invocations: 0. Go Full invocations: 0. Pilot, cutover, active/backup changes, global-skill changes, remote tracking, fallback, and dual-read: 0.

No over-investment stop condition was reached: this is one disposable Go baseline with two allowed input paths, one schema-v2 legacy report required by the comparison, and no validator, generator, reusable fixture framework, daemon, ledger, or extra evidence file. Task 2-5 is complete. This pass does not start Task 2-6; any pilot entry remains subject to its separate authorization and preconditions.
