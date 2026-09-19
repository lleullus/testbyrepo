# IIS Planning Skills

IIS is a host-independent skill/document workflow: current request → Thesis and ready Scope → grounded Plan plus Assurance Baseline → authorized implementation/self-check → exact source/execution binding → required native gates and direct observations → independent adversarial Prober lanes → structural evidence closure → Main's conditional status-only record.

There is no independent overall Plan approval role, whole-Scope semantic adjudicator or replacement final judge. Product meaning remains in Thesis/Scope; the evidence policy does not prove arbitrary semantic completeness. Ordinary file/command/delegation tools suffice. No patched OMP, execution plugin, controller database or agent runner is required.

## Components

- `product-thesis/`: complete product meaning, behavior/UI, failure/recovery/preservation, authoritative success observations and any grounded construction decision required to make the current product result determinate. Its bounded exploration stays inside the role.
- `scope-shaper/`: Main's Scope authoring instructions, canonical template and validator, not a separate invocation.
- `companion-skills/scope-plan/`: grounded methods, conditional first work and Assurance Baseline.
- `companion-skills/scope-implement/`: authorized implementation, native self-check and correction/execution handoff.
- `companion-skills/production-heuristic-probing/`: independent minimal-counterexample lanes and standalone bounded investigation.
- `iis-workflow/`: latest-request routing, stage/effect authority, fan-in, re-entry and status recording.
- [`iis-workflow/references/assurance.md`](iis-workflow/references/assurance.md) and `iis-workflow/tools/assurance.py`: evidence schema, currentness, native foreground gate capture and structural closure. No agent/model invocation or Scope writer.
- `companion-skills/repository-investigation/` and `purpose-first-review/`: supporting evidence and general review capabilities. General purpose review is not an implementation-admission role.
- `iis-observatory/`, `observatory/`: optional conservative read-only Scope/project state model.
- `repo-snapshot/`: independent Git snapshot utility, not automatic target sealing.
- `evaluation/`: disposable causal fixtures, offline scorers, explicit unexecuted scenarios and historical results. No model runner.

## Product and evidence contracts

Thesis sources normally live at `docs/planning/product-thesis/<meaning-slug>/THESIS-NNN.md`. Preserve referenced revisions. Create a new ordinal when the binding contract changes: product meaning, required means, a downstream-binding adopted construction decision, or a load-bearing factual premise whose refutation requires a different faithful downstream plan. Evidence/rationale-only additions and implementation defects under an unchanged binding decision do not by themselves require a revision. A newer unrelated source does not automatically replace an old bound original. Investigation and a Completion Brief supply evidence/lenses, not product approval.

Scope is `docs/planning/work/<slug>/SCOPE.md`, schema `iis-scope/v1`, with exact project-local Product Authority, Outcome and Acceptance. `draft` means unresolved meaning, `ready` means sufficient meaning/observation to plan, `done` is Main's conditional recorded completion, and `superseded` retains an unconsumed replacement. Structural closure BLOCKED is not a new Scope status. A digest proves bytes, not success or permission.

The optional approved Transition Baseline preserves Block/order/invariant/continuation/abort/atomic boundaries. It is distinct from Assurance Baseline. Main fixes current Scope from originals and actual state without Spec/Ticket/extra Increment layers. Plan owns faithful execution methods and executable preconditions left open by Thesis/Transition; it does not reselect Thesis-bound construction decisions or weaker success criteria.

Assurance Baseline is one `iis-assurance` JSON fence under the Plan's `## Assurance Baseline`; assurance-only can use invocation-local JSON without a fresh implementation Plan. It maps every authored Acceptance paragraph to evidence, records native gate commands and observation predicates, actual attack surfaces/required lanes, budget, isolation and settlement. It is not a mini-spec or approval certificate.

Clean committed Git source is the initial seal format. No automatic commit, push or repo-snapshot occurs. If commit is unauthorized or working bytes are unsealed, return TARGET_NOT_SEALED rather than attributing them to HEAD. Build artifacts/runtime/mechanisms are identified separately. Store evidence/disposable mutable fixture state outside the sealed source root.

Gate success, direct observation and adversarial search are distinct. Direct readback must satisfy its declared predicate; violated/unobservable results block even if gates pass and lanes find nothing. Every required and actually started result/effect participates in closure. New target evidence is reacquired; old traces remain reproduction/navigation only.

Before hypotheses, Probers receive originals, actual target, assigned surface, budget and safety, not implementation narrative/Plan candidate findings/peer conclusions. Reveal needed recipes and predecessor raw evidence afterward. Isolate mutable resources before fan-out; separate worktrees alone are insufficient. Report procedural embargo unless host access controls actually enforce it. No-finding is bounded search evidence, not universal correctness.

## Commands and limits

```text
python3 -B scope-shaper/tools/validate_scope.py /absolute/project/docs/planning/work/example/SCOPE.md --json
python3 -B iis-workflow/tools/assurance.py --help
python3 -B iis-workflow/tools/assurance.py validate /absolute/PLAN.md
```

The assurance reference documents `bind`, `bind-execution`, `run`, `close` and `recording`, including exact data inputs. `close` returns EVIDENCE_COMPLETE or BLOCKED/reasons. Main additionally checks actual host attribution, current request/authority, unchanged originals/target and settled effects before changing only ready→done and reading back the exact delta. The helper neither authenticates arbitrary JSON nor grants mutation authority. One Scope's closure is not the whole request's completion.

Planning-only and implementation-only stop at their boundaries. Standalone Probe can operate without canonical Scope but cannot create done eligibility. Historical done is diagnostic input, not a new completion event. A Thesis-bound factual premise or adopted construction decision change returns to Product-Thesis; approved transition order/intermediate authority/invariant changes return to Transition; Plan-only method/oracle/safety changes return to Plan/Baseline; faithful implementation correction stays with the selected authorized implementing actor.

## Optional skill installation

Read skills directly from source or prepare one immutable payload and link it into a supported client. Source edits do not change installed skills automatically.

```bash
python3 -B scripts/sync_installed_iis.py prepare --source /absolute/source --store /absolute/iis-store
python3 -B scripts/sync_installed_iis.py inspect --store /absolute/iis-store --bundle <reported-sha256>
python3 -B scripts/sync_installed_iis.py activate --store /absolute/iis-store --bundle <reported-sha256> --host omp --confirm-quiescent
```

Packaging remains `iis-bundle/v4`, `iis-install/v4`, protocol `4`, family `iis-skills`; topology changes do not require a packaging-version bump. `inspect --bundle` checks new-candidate topology; `inspect` without a bundle validates the installed release against its own manifest and managed links, including after rollback to an older v4 topology.

`activate` checks the new candidate and the previous installation separately, retires only managed obsolete links and refuses intervening user changes. All hosts sharing current must be in activation scope. `--migrate` snapshots an unmanaged entry only with explicit permission. Old releases/snapshots/user entries are preserved. v3 Scope installations remain retirement sources only; historical v3 usage requires its matching host source.

`rollback --confirm-quiescent` and `remove --confirm-quiescent` restore installation entries, not product effects. Use disposable stores/client roots for tests. Operating activation requires exact current authority and settled affected work; cancellation receipt is not settlement. Installation does not restart clients or prove session reload: loaded_identity remains NOT_CHECKED.

OMP and Codex are optional path adapters; OpenCode is a different client. Model settings, credentials and project planning/evidence are not packaged. `scripts/sync_installed_observatory.py` remains a separate Codex Observatory skill-copy utility, not part of OMP assurance activation.

## Tests and evaluation

```text
python3 -B -m unittest discover -s tests
PYTHONPATH=observatory/src python3 -B -m unittest discover -s observatory/tests
```

These Python suites do not invoke models or subagents. They include local subprocess/disposable service fixtures, source/path validation, actual helper closure and installation lifecycle checks. The frozen v4 fixture is exported from c856dd7257d518b2eba361f289ff6b28a74d731a rather than generated from new topology constants.

Actual model behavior, hypothesis diversity, framing resistance and detection/cost require separately authorized experiments. Scenarios marked NOT_RUN remain unexecuted. Neither unit-test success nor matching labels establishes those outcomes. See [current verification boundaries](docs/engineering/ready-runtime/verification.md) and [evaluation materials](evaluation/ready-verification/README.md).

[Historical host integration](docs/engineering/host-integration-reintroduction.md) is reference material, not a runtime dependency or planned reinstall.
