# IIS Planning Skills

IIS is a host-independent skill/document workflow: Main reconciles current state and Thesis into a fixed Scope → Plan → implementation → independent verification → read-only Coverage → Main's completion record. It requires ordinary file, command and independent-invocation facilities, not a patched OMP, a delivery plugin or a dedicated execution CLI. Product and acceptance meaning belongs to Thesis, the current outcome and observable acceptance contract to Scope, methods to Plan, and the semantic verdict to the independent verifier.

## Components

- `product-thesis/`: product meaning, Behavior/UI, failure/recovery and success observations.
- `scope-shaper/`: Main's current Scope contract instructions, template and validator; no separate Shaper stage or invocation.
- `companion-skills/scope-plan/`: method preparation and independent Plan Review.
- `companion-skills/scope-implement/`, `scope-verify/`, `scope-coverage/`: implementation, independent semantic verification and read-only post-success review.
- `iis-workflow/`: current-request routing, continuation and completion responsibility.
- `iis-observatory/`, `observatory/bin/`, `observatory/src/`: optional read-only project state inspection.
- `repo-snapshot/`: independent Git working-tree snapshot utility.
- `companion-skills/repository-investigation/` and `purpose-first-review/`: supporting investigation and review skills.
- `scope-shaper/tools/validate_scope.py` and `iis_path_contract.py`: standalone Python structure/path/source-reference checks, not semantic acceptance or completion authorization.
- `evaluation/`: retained case descriptions, disposable fixture preparation, historical observations and offline scoring. The host-specific delivery runner is retired; see its existing README for the remaining commands and their limits.

## Optional skill installation

Skills can be read directly from this source tree. The existing installer packages one immutable snapshot and optionally links it into a supported client's skill directory; it does not execute IIS work.

```bash
python3 scripts/sync_installed_iis.py prepare --source /absolute/source --store /absolute/iis-store
python3 scripts/sync_installed_iis.py inspect --store /absolute/iis-store --bundle <reported-sha256>
python3 scripts/sync_installed_iis.py activate --store /absolute/iis-store --bundle <reported-sha256> --host omp --confirm-quiescent
```

Use `--host codex` for that optional path adapter, or include both installed hosts when they share `current`. Neither adapter is a workflow requirement. The payload uses `iis-bundle/v4`, installation metadata uses `iis-install/v4`, and family is `iis-skills`. Protocol `4` versions packaging only; there is no host profile, boundary-tool protocol or host terminal schema.

`prepare` does not change installation links. `inspect` checks release bytes and required skill files. `activate` requires affected IIS work and effects to be settled, not shutdown of unrelated services. A cancellation receipt alone is not settlement. Previously managed v3 Scope installs are accepted only as a migration source: their managed Scope extension link is removed, while unrelated user skills/extensions, private historical state, releases and snapshots are preserved. `--migrate` is needed for an unmanaged entry and preserves a recovery snapshot.

`rollback --confirm-quiescent` and `remove --confirm-quiescent` preserve history and refuse intervening user changes. They change installation entries, not product effects or OMP source. Restoring a historical v3 installation would also require its matching host source; it is not an alternate current operating mode. Installation does not restart clients or prove existing sessions reloaded the skills; `loaded_identity: NOT_CHECKED` remains explicit.

Model configuration, credentials and product planning/evidence are not bundled. IIS preserves explicit user-selected model policy rather than supplying model presets. Observatory's independent data installer remains `python3 scripts/sync_installed_observatory.py`.

## Product and planning contracts

Thesis source storage is authorized before model/approval closure but does not approve product meaning or implementation. Sources normally live at `docs/planning/product-thesis/<meaning-slug>/THESIS-NNN.md`; preserve referenced revisions. Optional Transition Baseline remains a transition map, not a replacement Thesis or a second operating mode. Main reuses fixed construction boundaries and chooses a current durable outcome only where the originals leave that choice open. Existing Block predicates suffice unless an actual independent handoff or prescribed order needs a finer boundary; no universal boundary catalog is required.

Scope lives at `docs/planning/work/<kebab-case-slug>/SCOPE.md`, using `Schema: iis-scope/v1`, `Project-Root`, `Status`, `## Product Authority`, `## Outcome`, `## Acceptance`, and optional `## Open Decisions`/`## Transition Authority`. `draft` preserves unresolved meaning, `ready` admits reviewed work, `done` records completed verification/Coverage and Main's confirmed status change, and `superseded` marks an unconsumed replaced contract. The standalone validator checks structure and exact bound sources; it does not decide semantic completeness.

Main fixes the current Scope before method writing; Plan chooses implementation methods without redefining Outcome or Acceptance. The same independent Plan Review checks fidelity to bound originals and method sufficiency, recording exact reviewed files and actual-byte hashes with `iis-scope-plan-review/v2`; no extra review stage or host-generated authority digest is required. Re-entry follows the changed decision: Thesis meaning, Baseline geography, Main's Scope application, or Plan method. Missing required delegated-role selections are resolved by the user or returned as `MODEL_SELECTION_REQUIRED`, never by a hidden default.

## Verification and completion

```text
Current user intent + actual product state
  → Thesis when meaning needs definition or revision
  → Main reconciles applicable Baseline/current state and fixes Scope
  → Plan and independent Plan Review
  → Implementation → independent Verification
  → independent read-only Coverage after VERIFIED
  → Main records ready → done with ordinary file tools and readback
```

The verifier records every authored Acceptance result, actual observations and evidence, exact original/target identities, declared scenario effects, currentness and settlement. Main preserves the original verdict; it does not issue a second semantic verdict. Completion requires attributable completed independent verification, complete Coverage with no unresolved material gap, current authority/target, settled effects and current user permission. Main then edits only the Scope status and reads back the actual result. Failed, inconclusive, missing or stale evidence cannot become completion.

These are procedural responsibilities, not host-enforced authentication or locks. Hashes, report fields and process exits do not by themselves prove independent judgment or success. No replacement runtime, opaque credential store or execution CLI is introduced. Scope completion is not automatically completion of the user's whole request.

Read-only and stage-only requests stop at their requested boundary. Historical planning revisions and completed evidence are not rewritten to claim a new completion. IIS has no controller database, persistent Goal state, execution roster, attempt ledger, evidence cache, event/replay engine or generic workflow DSL.

## Optional future host integration

See the [host integration reintroduction guide](docs/engineering/host-integration-reintroduction.md) for the archived Scope tools and separate OMP source references, selective reintroduction steps, and current contract boundaries. This is reference material, not a planned or required runtime dependency.
