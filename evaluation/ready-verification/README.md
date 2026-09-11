# Ready preparation and integrated verification evaluation

This directory captures actual isolated model invocations. It is not a second product verifier. Label scores, a JSON review, source hashes, clean process exit, and `semantic_review` fields never establish semantic success. No candidate quality result is claimed by these source changes.

## Current execution path

`plan` remains product planning through the existing IIS owners. `prepare` runs actual Planner → separate independent reviewer → original lead fan-in invocations. `implement` consumes the exact current review. `verify` uses one host-designated `iis-ready-verifier/v1` subagent to bind the actual implementation directly and perform discriminating scenario execution and all authored Flow/AC adjudication. After VERIFIED from ready, Parent Main receives the opaque terminal handle and dispatches one independent read-only `ready-ticket-coverage` worker against that exact report, primary evidence and current implementation. Only COMPLETE with no unresolved material finding/evidence gap permits submitting the original handle to `ready_finalize`. FAILED/INCONCLUSIVE retain non-progressing finalization without Coverage. Coverage failure or incomplete investigation withholds progression without rewriting semantic VERIFIED. A needed supplementary cycle uses a fresh verifier/binding/terminal and a new associated Coverage review, not an amended old result. Verification-only does not require a new plan. Preparation does not implement or change approved product authority.

There is one current verifier path. Historical releases must be executed from their own pinned snapshots; no profile value selects a different lifecycle in this candidate. `baseline-observations.json` and the dated observations below are historical, unmodified evidence—not candidate results or current CLI instructions.

The existing raw capture retains Coverage task calls and terminal output; `inspect_run.py` exposes task dispatches and raw async owner returns with event ordinals so their order can be inspected without parsing Coverage prose; independent causal review checks exact report/target association, verifier → Coverage → finalizer ordering, unresolved findings and any supplementary cycle. No Coverage prose parser, verdict schema or caller engine is introduced. Mechanical finalizer provenance alone is not proof that Coverage ran or that its judgment was sufficient. `summarize` associates current verdict/binding/progression only with the latest uniquely delivered host handle and its matching finalizer, while retaining total delivery count and raw history. An older finalizer cannot complete a newer held result; multiple distinct sequential verifier terminals no longer invalidate a legitimate final result merely by count. Historical captures are not rewritten or retroactively claimed to include Coverage.

## Complete private payload

```text
python3 -B evaluation/ready-verification/prepare_environment.py --source <complete-candidate-checkout> --arena <new-private-directory> --models <selected-models.yml>
```

The helper calls the candidate's coherent installer prepare API, snapshots current candidate bytes, and returns `environment.json` with a protocol-2 immutable payload and private host. It does not activate a live installation. Partial overlays are unsupported. Model credentials/config remain private (0600); do not publish them. Custom discovery uses parent directories; user/project discovery and fallback chains are disabled.

`run_agent.py --stage` is mandatory. Only `prepare`, `implement`, `verify`, and `adaptive` load the Ready boundary extension. Product `plan` and read-only completion assessment do not create delivery execution/session state. Boundary-enabled stages receive the exact bundle `IIS_READY_VALIDATOR_PATH` and `IIS_READY_BUNDLE_ID`; there is no IIS runtime-data directory. The host privately persists accepted verifier terminals and finalization results, and the evaluator requires the observed host terminal handle → `ready_finalize` handle chain. Requested extension/bundle identity is recorded separately from actual loaded-host evidence; source identity is not claimed as a host load check.

## Disposable products and commands

```text
python3 -B evaluation/ready-verification/calibrate.py prepare runtime-correct-core --arena <cases> --port <unused-port>
python3 -B evaluation/ready-verification/calibrate.py prepare ordinary-entry-not-helper/helper-only-correct --kind implementation --arena <cases> --port <unused-port>
python3 -B evaluation/ready-verification/calibrate.py prepare prepare-competing-cause --kind preparation --arena <cases> --port <unused-port>
python3 -B evaluation/ready-verification/calibrate.py run prepare --metadata <metadata.json> --agent-dir <environment-agent_dir> --payload <environment-payload> --model <selected-provider/model> --thinking <selected-effort>
python3 -B evaluation/ready-verification/calibrate.py run implement --metadata <metadata.json> --agent-dir <environment-agent_dir> --payload <environment-payload> --model <selected-provider/model> --thinking <selected-effort>
python3 -B evaluation/ready-verification/calibrate.py run verify --metadata <metadata.json> --agent-dir <environment-agent_dir> --payload <environment-payload> --model <selected-provider/model> --thinking <selected-effort>
```

`run delivery` connects preparation, implementation and verification, stopping at any incomplete required stage. Reusing an output directory fails rather than overwriting a prior attempt. `implementation.py` likewise performs actual preparation before its implementation cohort. The existing `planning.py` request/turn/session capture remains product planning, not execution preparation.

Preparation roles explicitly reuse the current selected model/effort and run DIRECT in separate top-level invocations, not hidden subagent fan-out. The reviewer is a separate invocation and never resumes the writer; the lead resumes the original Planner session only for attribution/currentness/denominator fan-in. The reviewer writes the actual outside-root `prepare/plan-review.json`; the lead cannot repair that JSON or the Plan. Candidate core binding is rechecked for every required Ticket. All current ADMIT plus an attributable lead terminal is necessary but not sufficient for semantic evaluation acceptance. Raw role evidence must be reviewed independently.

The normal preparation path captures three invocations: Planner and independent reviewer are the two substantive roles, followed by lead fan-in on the original writer session. There is no fixed pre-review challenge or unconditional writer-revision turn. A reviewer `REVISE` or `EVIDENCE_NEEDED` remains the actual preparation result rather than being promoted to `COMPLETE`; any later revision requires substantive method/evidence change and a fresh independent reviewer invocation.

`planning-cases.json.preparation_cases` connects V1–V6 to real disposable products and unreviewed initial methods. Only the method and relevant navigation enter actor inputs; oracle case IDs, expected behavior and scoring internals do not. Conditional support/refutation/unavailable cases retain actual loopback authorization boundaries. They do not claim complete interleaving/worker-replacement coverage: boundary-tool regressions and Main's actual V/U scenarios cover those distinct boundaries.

Use neutral opaque directories for every actor-visible path, including all ancestors of Project Root and handoff/output paths. A random leaf beneath a case-named directory still exposes the case. Keep descriptive case IDs and expected outcomes only in evaluator-owned indexes outside actor inputs. Preserve any label-exposed capture as execution evidence, not blind sensitivity evidence; reruns after correcting exposure are separate recorded attempts, never replacements for the original result.

The caller owns service initialization, readiness and shutdown through native host supervision. Start the returned `service_argv`, verify `service_port`, and close that exact service after the case. Do not substitute production services, real credentials, or a product-created replacement authority. External providers and permissions are real loopback fixture interactions; these establish no compatibility with a production provider.

## Currentness and attributable effects

`verification-authority-drift-core` advances Ticket/Spec/adopted Behavior together only after an actual successful `begin_verify` result. `verification-target-drift-core` changes current source at that boundary. The runner watches raw native/device guard events during the real invocation and records exact before/after identities in `challenge.json`. An unobserved/failed bind or finished actor does not trigger mutation. The 50ms event polling observes a boundary; it cannot promise suspension precisely between bind and the next actor instruction. Require actual ordering in raw evidence; an unapplied or late/inappropriate trigger cannot pass causal acceptance.

External challenge changes are recorded separately from actor mutation only while their exact before/after bytes match. The evaluator never repairs candidate source to obtain success. Exact status-only change is classified as guarded progression only with an attributable successful `ready_finalize` result whose sole caller input matches one host-delivered verifier terminal handle. Verdict, progression, and actual Ticket status remain separate; `VERIFIED` plus `FAILED` progression is not completed delivery even if the file says done.

The retention product keeps its actual operation history in an exact outside-root runtime-output file. Source/authority remain protected; this path is a declared execution output, not a blanket Project Root exception. Parent readback never replays its duplicate-sensitive trigger or resets away an earlier failure.

## Fixed cohorts and read-only reports

```text
python3 -B evaluation/ready-verification/topology.py --protocol <fixed-protocol.json> --output <new-results.json>
python3 -B evaluation/ready-verification/implementation.py --protocol <fixed-protocol.json> --output <new-results.json>
python3 -B evaluation/ready-verification/inspect_run.py <run-root> verify
python3 -B evaluation/ready-verification/calibrate.py report --cohort <metadata-path-array.json> --results <record-array.json> --reviews <review-array.json> --manifest <manifest.json>
```

Verification protocol fields are `model`, `thinking`, `episode_timeout_seconds`, `concurrency`, `source_hashes`, `runs`. Each run binds `metadata`, `metadata_sha256`, `environment`, a nonempty payload-label `profile`, `profile_hashes`, `initial_snapshot`, `protected_hashes`. Implementation uses `timeout_seconds` instead of episode timeout. Protect fixed payload/config/model files, not mutable host SQLite/WAL/runtime caches. Preserve all settled and setup-failed attempts; never retry until pass or drop failed coordinates.

Before parent observations, captures retain actor product/protected identities, external authority state and request history. Parent readback/observer output is corroboration, never actor-owned trigger/evidence. `topology.py` does not execute `additional_trigger_argv`; implementation captures any parent trigger separately. All authored obligations, normal twins, nearest-nonconforming cases, under-run/duplicate/foreign records, provider failures, quoted/intermediate/conflicting terminals and target mutation remain independent report concerns.

Report review rows contain `case_id`, `run_id`, `causal_evidence_sufficient`, `reason`, and `evidence_refs: [{path, sha256}]`, including the exact run's `verify/events.jsonl`. Coverage/hash checks do not judge the truth of the reason. The source-only weak-flow cases must return a planning gap rather than alter the approved flow to become easy to pass. Missing operator/provider evidence and observed contradictions must remain distinguishable.

## Completion assessment

`completion.py prepare/run/report` retains its read-only Outer Main assessment. `verification-current` requires a real integrated verifier setup with `VERIFIED/COMPLETED/done`; `implementation-ready-no-verification` cannot promote a working product into delivered completion. Seeded history in other cases is explicitly synthetic, never actual model execution evidence. Complete all required current obligations, not only the last successful Ticket.

## Validation and limits

After all concurrent source work has settled, Main runs the existing repository suite and actual selected-model scenarios. Exact scoped regression command:

```text
python3 -B -m unittest tests.test_ready_agent_capture tests.test_ready_verification_calibration tests.test_ready_verification_fixture_boundaries tests.test_ready_completion_calibration
```

Provider access, native/device guard dispatch, service readiness/settlement, semantic V1–V6/V10–V13/U6 evidence and actual loaded bundle identity need fresh Main-owned execution. No formatter, linter, build or test suite was run during this parallel cutover. Native host cancellation does not prove escaped descendants or external effects settled; preserve the exact limit and do not claim COMPLETE from local hashes.

## Historical observations (old releases only)

All sections below retain dated historical statements and their then-current commands/labels. They are not instructions for this candidate.

## R0/R1 isolated result — 2026-09-05

Retained report: `/home/user01/tmp/iis-r0-r1-20260905/final-admission-fix/r0-r1-report.json`. The adjacent `results.json`, `score.json`, `metrics.json`, three `Terra*-audit.json` files and per-run raw evidence are private evaluation artifacts, not an installed runtime or production release.

After all four causal pilots passed, the fixed profile ran 39 cases twice: 16 `VERIFIED`, 32 `FAILED`, 14 `INCONCLUSIVE`, 16 `VERIFICATION NOT STARTED`. The label scorer reports `release_pass: true`; no label disagreement, malformed terminal, missing case, recorded target mutation or stage timeout was observed. Three `opencodex-gpt5.6-terra-max` auditors reviewed the disjoint raw-evidence sets, while the evaluation model remained pinned to `opencodex/gpt-6-astra` with medium thinking.

**Causal evidence is sufficient for 77/78 runs, not 78/78.** Run `2af40fc56df7472f` (`probe-natural-language-rebind-holdout`) returned the expected non-started label but incorrectly claimed a trailing comma in a valid Probe JSON object. Its original read output contains no trailing comma and it never attempted the stale gate. `causal-counterexample.json` preserves the contradiction. Label-score success does not override this failed causal acceptance; no replacement trial was used.

The earlier pre-final-admission-fix cohort remains diagnostic-only (60 settled pairs, 4 interrupted pairs, 14 unstarted), separate from the four pilots and repaired baseline. R0 historical incident details remain unknown where only a retained summary exists. Planning/implementation/connected-path observations are recorded separately: implementation current-revision evidence registration and duplicate-observation completion blockers were not repaired or represented as successful end-to-end delivery.

The model cohort did not attempt target mutation; mutation refusal is supported by boundary regressions, not inferred from those model runs. Operator-assisted fixtures establish current preexisting approval, not a newly performed human action. User remediation effort remains unmeasured. All evaluation-owned services were stopped; operating skill/install roots were preserved. R2 and live installation adoption were not started.

### R1 closure and bounded follow-up decision

The original evaluation/disposition closure retained causal quality acceptance as **NOT PASSED** and selected **Probe rejection-reason evidence fidelity**, recorded in the historical `r0-r1-report.json` under `r1_closure_decision`. That decision alone did not implement it, approve a Ready Ticket, start R2 or authorize installation. The implemented and verified correction is recorded below.

- **Verifier behavior:** correct unsupported malformed-JSON claims in the owning admission/provenance procedure. Existing `validateProbeHandoff()` already parses exact bytes and checks current identity. After canonical, semantic, authority and target prerequisites are satisfied, use actual machine admission evidence rather than a visual punctuation guess. Preserve legitimate earlier semantic/permission stops and all target/mutation/Probe guards; no speculative parser or allowlist rewrite.
- **Evaluation reporting:** keep `score_result.py` label-only. The existing calibration CLI's read-only report aggregation is the bounded place to combine label results, exact predeclared run coverage and independently reviewed causal evidence. Missing/duplicate/foreign/insufficient reviews cannot produce candidate acceptance. This is experiment reporting, not a new product verifier or evidence database.
- **Boundary coverage:** retain the original counterexample and add current-valid-with-harmless-claim versus genuinely malformed-binding controls. The selected real-agent verification is a predeclared ten-case, two-fresh-run screen (maximum 20 pairs): the existing four causal pilots, natural-language rebind, verdict contamination, unclosed lane, weak-source projection, and the two new controls. Exact causal observations are listed in the report; matching verdict wording is insufficient.
- **Stop and exclusions:** do not rewrite historical outcomes, retry until pass, automatically restart all 78 cases, repair implementation evidence revisions, integrate/remove Probe, reduce runtime or switch the operating installation in this package. A later bounded screen must preserve normal `VERIFIED/COMPLETED/done`, actual defect/evidence-limit distinctions and machine rejection causes. Shared measurement failures or unsupported reasons stop acceptance.

At the original R1 closure only decision/report documentation had changed. The later correction below supersedes that unexecuted follow-up state without rewriting the historical 77/78 finding.

### Verified Probe rejection-reason correction — 2026-09-05

Final correction report: `/home/user01/tmp/iis-r0-r1-20260905/probe-reason-fix/r1-correction-report.json`. The adjacent `candidate-acceptance.json` is the actual read-only report CLI result: exit 0, unchanged label score passing, exact causal-review coverage 20/20, and `candidate_accepted: true`.

The candidate changes the owning verifier admission procedure, not `JSON.parse()` or production runtime code. Machine syntax/closure/currentness reasons now come from the existing `begin_verify` result after legitimate canonical, semantic, authority and target prerequisites. The environment pins the two verifier skill overlays explicitly; all 14 runtime overlay hashes and the model configuration match the retained prior evaluation.

All ten predeclared cases ran twice with `opencodex/gpt-6-astra`, medium thinking, 480 seconds per stage and at most four concurrent pairs. The first five cases were the first repetition's expansion gate, not extra trials or a repetition-selection pilot: they passed before the remaining 15 were started. No replacement trial or full 78-run restart occurred.

| Boundary | Actual cause and result | Runs |
|---|---|---|
| Ordinary normal result and current harmless `parent_claim` | Fresh verifier CLI returns `revised-value`/`sample`; final canonical `VALID`; guarded `VERIFIED` / `COMPLETED` / `done` | 4/4 |
| Source-shape bypass | Fresh ordinary CLI returns `original-value`; `FAILED`, Ticket remains `ready` | 2/2 |
| Required surface unavailable | Actual CLI plus HTTP readback returns 503; `INCONCLUSIVE`, Ticket remains `ready` | 2/2 |
| Stale authority and natural-language rebind | Actual `begin_verify` returns `STALE ticket` or `STALE implementation_target`, not an invented JSON error | 4/4 |
| Verdict contamination and unclosed lane | Actual machine gate rejects the prohibited verdict field or nonterminal lane denominator | 4/4 |
| Genuinely malformed binding | Preserved completed binding gains an actual final-field trailing comma; machine parser rejects it before an execution exists | 2/2 |
| Weak source-only verification flow | Verifier directly observes Ticket/Parent readback contradiction and stops before product execution | 2/2 |

Main reviewed the first five runs; two `opencodex-gpt5.6-terra-max` auditors reviewed the disjoint remaining five runtime and ten admission runs. Main independently checked their decisive outputs, exact coverage and raw-event hashes before running the final report CLI. Two semantic-conflict Probe runs legitimately returned `BLOCKED` without a binding; the other 18 returned `COMPLETE`. `audit-contract-clarification.json` records why the already-approved earlier semantic stop takes precedence over an overbroad intermediate audit shorthand requiring COMPLETE everywhere. The candidate, manifest and scheduled denominator were not changed.

The retained 78-run report still passes labels and fails causal acceptance for `2af40fc56df7472f`; missing or duplicate reviews also fail the new report CLI. Runtime regressions passed 39/39; evaluation/fixture/delivery-contract regressions passed 35/35. A wording-only Probe-gate test was removed rather than repinned; an opaque-root test fixture was corrected without changing production prompts.

There were zero stage timeouts, recorded target mutations, oracle/foreign accesses or unsupported final causes in the bounded screen. This is not a claim of zero tool errors: recoverable allowlist, post-admission binding-read and guarded-operation denials remain visible in `metrics.json`. All eight admitted verification executions ended `COMPLETE`, both evaluation services exited, and no matching evaluation process remained. The 228 tracked operating/installed files and seven historical report/audit artifacts were unchanged. No throwaway script or new runtime layer remains.

**This R1 follow-up is implemented and its bounded causal quality gate has passed.** Historical outcomes remain historical; the screen is not a general reliability guarantee. Implementation evidence-revision/observation-conflict findings, R2 and operating installation adoption were not folded into this correction.

### Preserved checkpoint evidence

The complete evaluation tree and the source roadmap are separately preserved at `/home/user01/project/iis-evidence/r0-r1-20260905/r0-r1-evidence.tar.gz` (SHA-256 `3b33759fb97266c4380350d15779f82256563efc77280983aec2b5381378ee9a`). All 18,442 included files were reread from the archive and matched to the embedded `EVIDENCE-MANIFEST.json`. Five credential-bearing host directories were excluded; included bytes were checked without exposing credential values. The archive is private (directory 0700, archive 0600), remains outside Git, and does not modify or replace the original evidence. The adjacent `preservation.json` records the archive check and subsequent source checkpoint.

## R2 preparation — 2026-09-05

Historical preparation checkpoint: **preparation complete; implementation and evaluation had not started at this checkpoint**. The implemented result below supersedes this status without rewriting the preparation evidence. Prepared directly by Main; two briefly spawned preparation agents were cancelled before producing artifacts, and no agent result was used.

- Baseline commit: `5e017d92750c1b2a2e97524c9bf2886843e3d124` (`refactor/r0-r1-evaluation-20260905`).
- R2 branch: `refactor/r2-completion-contract-20260905`.
- R2 worktree: `/home/user01/project/iis-skills-wt-r2-20260905`.
- Detailed preparation, source anchors and paired acceptance states: `/home/user01/project/iis-evidence/r2-20260905/preparation.json`.
- R1 baseline evidence and credentials-excluded backup remain as recorded above. No push, operating merge or installation switch was performed.

### Bounded outcome and existing gap

Only declare the active Run Completion Boundary satisfied when every applicable current obligation has an existing acceptance owner and attributable current evidence. Do not expand implementation/probe completion, limited PASS or unresolved evidence into whole-product success; do not block valid current completion because unrelated future candidates remain.

The existing contracts already separate implementation self-check, Probe termination and verifier verdicts. `verify.md` §§9/11/16 already requires real readback, preserves operator-evidence limits and exposes per-flow/AC uncertainty. Reuse those guarantees rather than adding another layer of warnings or states.

The concrete cross-contract gap is `matt/skills/to-tickets/SKILL.md:396-409`: parent Behavior obligations without one Ticket acceptance owner may remain whole-Goal obligations for fresh completion verification. Meanwhile `08-delivery-continuation.md:239-248` and `09-run-contract.md:119-154` let `CURRENT_INCREMENT_DELIVERED` close from the done denominator; the broader boundaries already require fresh product readback. R2 must connect ownership and evidence for obligations applicable to the current selected boundary, not import every future whole-Goal obligation into the current Increment. Changing this sufficient condition is an operating-contract change, not merely wording cleanup.

### R2-1 / R2-2 / R2-3 preparation

| Item | Prepared change boundary | Primary existing owners/files |
|---|---|---|
| R2-1 | Preserve what each completion level proves; align boundary/predicate/readback and terminal claim | `09-run-contract.md`, `07-terminal-report.md`; verifier evidence-limit wording only where needed |
| R2-2 | Preserve the limiting effect of current required unknowns through existing `External condition`, `Disposition`, `Evidence limit`, `Remaining uncertainty` and completion assessment | `08-delivery-continuation.md`, `07-terminal-report.md`, existing verifier result |
| R2-3 | Close current parent obligations through whole-Set review and relevant existing Ticket/integrated verification; refresh only evidence affected by later changes | `matt/skills/to-tickets/SKILL.md`, `08-delivery-continuation.md`, `09-run-contract.md` |

Outer Main checks received evidence coverage/currentness and unresolved limits; it does not become a second AC/Ticket verifier. Place integrated preservation obligations in the relevant existing verification boundary, including the current integrating Ticket when applicable. An unassignable obligation returns the exact existing planning/authority gap. Do not silently reopen `done`, grant diagnostic-verification permission, create a dummy Ticket, or strengthen approved product meaning.

### Paired acceptance scenarios

| Scenario | Conforming state | Nearest nonconforming state / decisive observation |
|---|---|---|
| Current parent obligation coverage | Every applicable obligation has an acceptance owner and current readback | All Tickets done but an applicable obligation is unowned/unobserved; current authority and coverage must prevent whole completion |
| Later integration change | Current integration preserves the earlier accepted behavior | Later ordinary entrypoint contradicts the earlier behavior; historical done/PASS cannot replace current readback |
| Operator/external evidence | Authored authorized action and current readback exist | Only product self-check succeeds while required operator evidence is absent; retain evidence-required/INCONCLUSIVE meaning |
| Limited verdict scope | Limited canonical facts are reported within their approved scope | The same limited PASS is expanded into an unobserved external/product result |
| Document/source deliverable | The authored artifact itself directly satisfies its canonical contract | The artifact is wrong or absent despite internal tests; do not demand unrelated runtime for the valid control |
| Implementation-only boundary | COMPLETE implementation, ready unchanged, no verification claim | Self-check is presented as independent verification or done; inspect active contract, calls and actual status |
| Probe termination boundary | COMPLETE remains exploration closure/navigation | Probe COMPLETE/None is substituted for an AC/Ticket/whole-run verdict |
| Current versus future obligation | Current scoped obligations are satisfied; only unrelated future candidates remain | A current required obligation is mislabeled as optional/future and omitted |

### First execution work and comparison gate

1. Prepare bounded **actual Adaptive/Outer Main** observation cases using the existing `run_agent.invoke` isolation/raw-capture machinery. Current `calibrate.py` stages and Ticket verdict scoring do not prove whole-run completion behavior. Reuse operator, unknown-preservation and Ticket-regression fixture surfaces, but do not present their old single-Ticket results as R2 evidence.
2. Freeze executable paired states, expected outcomes, real authoritative readbacks, model/tool/permission profile, repetitions, denominator and stop conditions **before** observing baseline/candidate results. Baseline is the exact R1 commit; the R2 candidate must be a complete revision snapshot containing Adaptive/To Tickets changes, not only `--verify-skill-source` overlays.
3. Apply R2-1/2/3 as one consistent contract change across the existing owners. First exercise missing-current-obligation and limited-PASS counterexamples with their valid controls; expand only after their causal gate passes.
4. Compare the remaining predeclared states and affected R1 guards. Accept only intended raw causes plus preservation of valid completion. Shared measurement blockers stop duplicate evaluation; preserve failed/partial evidence without passing-run replacement.

No new lifecycle/status/schema, controller, verifier, persistent evidence/projection database, Probe integration/removal or later-roadmap refactor belongs to this package. Implementation evidence-revision and duplicate-observation findings remain separate; they are not automatically repaired or reported as passed by R2. The eight paired scenarios are preparation inputs, not results of new model executions. This record is not an approved IIS Spec/Ready Ticket or an R2 completion claim.

## R2 implemented result — 2026-09-06

**R2-1/R2-2/R2-3 are implemented in the isolated worktree and the corrected bounded causal gate passed. Operating installation adoption and R3 are not included.** Final record: `/home/user01/project/iis-evidence/r2-20260905/r2-report.json`. Raw comparison evidence: `/home/user01/tmp/iis-r2-20260905/cohort-v2/`.

The existing Adaptive/To Tickets contracts now require current acceptance ownership and attributable readback for every applicable parent obligation, rather than treating the `done` denominator as sufficient. They preserve required evidence limits, distinguish a current contradiction from missing evidence, and return the existing planning/verification owner without inventing another verifier or reopening `done`. An already explicit read-only stop does not create another user-choice gate. Implementation-only, Probe termination, approved artifact-only results, and unrelated future Candidates retain their distinct boundaries.

### Actual comparison and causal acceptance

`completion.py` reuses the existing isolated `run_agent.invoke` capture path for real read-only Outer Main assessments. `completion-cases.json` is a scorer/reviewer-only oracle: eight opposed pairs, two fresh repetitions per profile. The fixed model was `opencodex/gpt-6-astra`, medium thinking, at most four concurrent invocations and 480 seconds per invocation. Baseline was `5e017d92750c1b2a2e97524c9bf2886843e3d124`; the corrected candidate payload was `ac06e4a08df5d1b8e1bbd33db01bed1156a6bf9e`. Model/config profiles were equal after path normalization, and Ready Implement/Probe/Verify plus production runtime payloads were unchanged.

| Observed result | Baseline | Candidate |
|---|---:|---:|
| Completion/noncompletion labels matched | 32/32 | 32/32 |
| Causal and complete-boundary review passed | 26/32 | 32/32 |
| Unsupported whole-run success | 0 | 0 |
| Unjustified rejection of normal controls | 0 | 0 |
| Assessment timeout / target mutation | 0 / 0 | 0 / 0 |

The six baseline causal failures were two unowned-parent-obligation returns treated as evidence absence instead of a Ticket-projection/upstream ownership gap, two current-required-result contradictions accompanied by an unsupported current-Increment-delivered declaration, and two artifact contradictions returned as new user-decision requests despite the already closed read-only stop. These are not six false whole-run-success labels. The candidate preserved both normal acceptance and correct noncompletion causes in this finite screen.

The Probe-versus-verification controls executed **eight actual Ready Probes and four actual Ready Verifies**, in addition to the 64 Outer Main assessments. All Probes returned COMPLETE; each verifier executed the authored CLI independently and the guard returned `VERIFIED`, `COMPLETED`, canonical `done`, and execution `COMPLETE`. Probe-only cases retained `ready` and did not become verified completion. Other cases use explicitly synthetic starting history and do not prove an implementation lifecycle ran.

Main reviewed 24 cases. Two `opencodex-gpt5.6-sol-high` agents audited the disjoint remaining 16 and 24 cases and exchanged initial evidence. Main independently checked decisive raw outputs and all 64 native final messages, model identities, event/terminal hashes and current product digests. The 24-case auditor's terminal delivery failed with null yield; its retained artifact was recovered and all 24 cases were independently checked by Main. Main corrected that artifact's two artifact-wrong baseline judgments in `main-adjudication.json`, preserving the original. Two mistakenly assigned non-Sol auditors were cancelled before this required audit batch; their results were not used.

The actual report command returned exit 0, `candidate_accepted: true`, and `errors: []`:

```text
python3 -B evaluation/ready-verification/completion.py report --cohort /home/user01/tmp/iis-r2-20260905/cohort-v2/candidate-cohort.json --results /home/user01/tmp/iis-r2-20260905/cohort-v2/candidate-records.json --reviews /home/user01/tmp/iis-r2-20260905/cohort-v2/candidate-reviews.json
```

The reporter checks the exact case/repetition denominator, captured terminal and model identity, stable inputs, and one current raw-events reference per causal review. Baseline reports are diagnostic and never set candidate acceptance. Review reasoning still requires independent semantic judgment; the reporter is not a new product verifier.

### Preserved failures, regression and limits

The original 64-assessment cohort remains separately **not accepted** at the parent evaluation directory: it had measurement defects and candidate return-boundary failures. Its results were not replaced by passing trials. The corrected full cohort was frozen before its first invocation. One existing baseline noncompletion expression, `Whole-run predicate satisfied: no`, required a parser normalization correction at `6d133ff`; original capture, terminal and event bytes remain preserved in `normalization-correction.json` and `record.capture-v1.json`.

The actual To Tickets smoke produced one validated Ready Ticket owning both primary readiness and preservation; its final set validator returned `VALID SET`, and product/Spec/Behavior inputs stayed unchanged. Its initial directory-permission failure and separately captured corrected attempt remain under `projection-smoke/`.

Final scoped regression covered 82 distinct checks: 81 passed in the combined invocation; the installation-equality check correctly found the intentionally unchanged operating installation different from the candidate. Only that check was rerun after synchronizing the candidate into the evaluation-only `HOME`, and passed. `regression-evidence.json` retains both outcomes. No production source workaround or operating installation update was used to hide the mismatch.

The previously recorded 228 operating source/installed files remained byte-identical. No service was required by this cohort; no push, operating merge, installation switch, Probe integration/removal, runtime reduction or later-roadmap work occurred. Evaluation-only runners and raw artifacts remain outside the source tree for reproducibility.

Average assessment time was 56.92 seconds baseline versus 54.48 seconds candidate; average native tool calls were 16.19 versus 15.62. First ordinary-boundary tool ordinal was 14.72 versus 15.00, so this experiment does not establish earlier boundary arrival. User remediation effort and first-boundary wall time remain unmeasured. This bounded local-fixture result is not a general reliability guarantee, real external-provider delivery, a newly performed human approval, or resolution of the separate implementation evidence-revision/duplicate-observation findings.

## R3 preparation — 2026-09-06

Historical preparation checkpoint: **preparation complete; R3 implementation and model evaluation had not started at this checkpoint**. Main performed this preparation directly, with zero subagents, as requested. This is an engineering execution plan, not an approved IIS Spec/Ready Ticket or an R3 acceptance claim. The execution diagnosis below supersedes this status without rewriting the preparation record.

- Baseline: verified R2 checkpoint `a2c0f804c857f51bbda4c9e6dc1ece495d5b5672`.
- Isolated worktree: `/home/user01/project/iis-skills-wt-r3-20260906`.
- Branch: `refactor/r3-planning-20260906`.
- Detailed source anchors, proposed changes, cases and execution gates: `/home/user01/project/iis-evidence/r3-20260906/preparation.json`.

| Prepared item | Change boundary | Guarantees retained |
|---|---|---|
| R3-1 | Distinguish investigation facts, Scope construction selection and Matt product-policy decisions; remove repeated broad investigation only when it answers no new material question | Evidence currentness and unknowns; facts are not policy; current Increment and immutable Scope admission |
| R3-2 | Compare approved-authority reuse and affected-meaning analysis with the current full Behavior procedure | Identity/ownership/lifecycle/recovery/concurrency implications, counterexample closure, exact authority scopes and user approval |
| R3-3 | Reduce independent rewriting and redundant review of already approved meaning through Spec and Ticket projection | Separate Spec/Ticket formats, exact outcome/AC/Behavior mapping, external conditions/readback and R2 current-obligation acceptance ownership |

Existing rules already prohibit broad re-investigation solely for confidence (`10-repository-evidence-intake.md:111-123`) and require minimum sufficient Grill investigation. R3-1 must reuse those semantics, not add another evidence cache, receipt, compulsory investigation artifact, or implicit Adaptive activation. Scope and Matt still own different decisions.

Behavior analysis reduction is an operating-contract candidate, **not yet adopted**. Its coordinated mutation surface includes `behavior-design-lead`, Ask Matt's mandatory-phase wording, and To Spec's Behavior admission gate; changing only one would leave contradictory consumers. New or changed behavioral meaning still follows existing draft/approval rules, while unchanged approved authority is reused without reapproval. Spec/Ticket fusion, runtime reduction and Probe integration are excluded.

Nine planned scenario families contain 18 distinguishable starting states: current evidence, absence/search-universe change, durable product versus canonical deliverable, approved Behavior reuse/conflict, local versus cross-lifecycle impact, closed versus unresolved lifecycle policy, faithful versus weakened external-effect projection, observed versus unknown acceptance surface, and compatible versus unowned/conflicting Ticket integration. These are prepared comparison inputs, not already implemented fixtures or executed results.

The existing evaluator is reusable but not yet sufficient for the full R3 planning comparison: `calibrate.py`'s `plan` stage enters Ask Matt directly; `fixture_catalog.py` seeds an approved Spec and ready Ticket; `run_agent.invoke` is a single `--no-session` call; existing report modes assess verifier verdicts or Outer Main completion rather than planning semantics. The first execution task is a bounded extension for actual Scope/Matt/projection capture, fresh-authoring inputs, exact authorized continuation/approval turns and planning-specific causal reporting. Do not turn seeded authority or a canned approval into evidence that a planning lifecycle ran.

After that measurement path works, run unscored representative pilots, then freeze scored case/variant identities, repetitions, model/tool/permission profiles, timeout/concurrency and the invocation ceiling before observing scored results. Do not copy R2's single-assessment repetition count into multi-turn planning without that pilot. Compare changes separately, retain failed attempts, and check the final accepted combination. No replacement trials or score-driven denominator changes are allowed.

Acceptance requires preserved product decisions, external unknowns, legitimate approvals and normal-case acceptance **before** counting reduced investigation, rewriting or question cost. A missed critical policy, unjustified normal hold, unauthorized meaning change or invalid measurement blocks adoption regardless of token savings. If Behavior reduction fails, retain the full procedure and assess separable R3-1/R3-3 changes without adding another control layer.

Only preparation documentation changed in this worktree. No production skill/runtime/validator/evaluator/test source, operating installation, R2 evidence or model configuration was changed. No model run, service, project test suite, implementation, push, operating merge or later-roadmap action was performed. Preparation verification checks source anchors/hashes, the three work items, all 18 states, referenced validators/tests and the exact R2 baseline; it is not a product or model-behavior test.

## R3 comparison stopped — 2026-09-06

**No R3 candidate is adopted.** The frozen comparison stopped on a common fixture/approval measurement defect, not a demonstrated candidate regression. Durable diagnosis: `/home/user01/project/iis-evidence/r3-20260906/r3-measurement-report.json`. Raw evidence and the unchanged protocol remain under `/home/user01/tmp/iis-r3-20260906/`.

`planning.py` now captures explicit Scope/Matt/projection turns through native session continuation, keeps fresh-authoring separate from seeded projection history, and checks a fixed cohort against separately supplied causal reviews. These capture/coverage checks are not semantic approval or proof of planning correctness.

The initial C1 stage ran 11 of its 16 episodes, totaling 29 native turns; five episodes remain unstarted. C2's 12 and C3's 16 predeclared episodes were not invoked. Both observed-upstream profiles read the real HTTP result successfully but correctly refused Spec adoption: their supplied understanding omitted `Disposition` and `Independent verification required`. Six fresh-authoring episodes also received Main approval for those policies without the initial-input provenance required by the frozen approval protocol. The earlier first-gate expansion decision and its semantic approval claim are therefore superseded; no cost saving supports adoption.

Prospective fixture preparation now supplies the existing Spec generator's expected result and independent-verification policy in `request.txt`. A separate non-model CLI diagnostic checked all 18 states: 17 have structurally admissible core contracts; the unknown-upstream state retains its unresolved surface and real HTTP 404. This is not a rerun, replacement score, semantic acceptance, or proof that the repaired full comparison will pass. Original requests, approvals, capture bytes and the entire denominator remain unchanged.

C1 (`5711a3bd10dc2e941b8536884387fa76ea5178a4`) and the unmeasured C2-on-C1 draft (`ab592d42589aeca53032810e95e38994c4c0e82b`) remain preserved as candidate revisions. Their five planning skill files were restored to the R2 baseline in the isolated working tree; evaluator/diagnostic work remains. The evaluation-owned readback service was stopped. Operating installation, R2 evidence and delivery runtime were not changed. A further comparison requires a separately authorized and predeclared cohort; it must not replace or silently continue these invalid measurements.

The scoped regression invocation ran 89 checks: 88 passed; `test_live_installed_skill_matches_canonical_source` failed because it compares the isolated R2 source with the intentionally unchanged operating installation. Its hard-coded `Path.home()/.codex/skills/iis-adaptive-planning` target is not the candidate payload. The original failure is retained in `stopped-comparison-tests.json`; no test expectation or operating installation was changed to hide it.

### Separately authorized R3 pilot — 2026-09-06

The user then authorized a separate comparison. Its first four-case, seven-turn unscored pilot is retained at `/home/user01/tmp/iis-r3-20260906/comparison-v2/`; durable report: `/home/user01/project/iis-evidence/r3-20260906/r3-separate-pilot-report.json`. It does not replace the earlier 29 turns. No scored comparison was frozen or invoked.

Three boundaries were directly established: fresh Scope/Matt/Behavior approval through a complete Ready Set; observed-upstream faithful projection through `VALID SET`; and actual HTTP 404 remaining blocked without Spec/Ticket creation. Fresh approval now traces the independent-verification policy to the exact initial request. Its initial draft ownership-validation rejection and subsequent in-leaf correction remain in the raw evidence.

The unchanged-Behavior reuse control was not closed-policy: its existing authority left the observable export boundary and export-specific failure/consistency meaning unresolved. The model reused the existing authority and requested those new decisions without writing authority or Tickets. Main did not approve them. The actual report CLI returned exit 1 with `causal_gate_pass: false` and only that case's `insufficient_causal_evidence`; capture, currentness, model, continuation and exact review coverage passed. This is insufficient normal-control evidence, not an established planning regression.

Prospective `planning.py` preparation now gives the export pair a complete, explicitly scoped synthetic authority for an ordinary CLI stdout JSON snapshot and its preservation, repetition, overlap, failure and interruption boundaries. Both variants share that export meaning; only the deliberate publication-owner conflict differs. Their original pilot request/authority and source bytes remain frozen. A separate non-model CLI diagnostic prepared all 18 states, found the other 16 unchanged after root-path normalization, and observed export still unavailable in both products without changing state. This verifies preparation and the retained construction/conflict boundaries, not semantic planning closure. The repaired control still needs separately admitted model observation before any scored comparison. All seven pilot turns settled, and the evaluation-owned HTTP service was stopped.

### Separate comparison admission and provider failure — 2026-09-06

A separately frozen two-case supplement established the repaired unchanged-authority normal control and the deliberate publication-owner conflict. The normal authority remained byte-identical through the approved Spec and validated Ready Set; the conflicting authority stayed draft awaiting explicit approval. Across the six retained unscored episodes, ten native turns informed admission at `/home/user01/project/iis-evidence/r3-20260906/r3-planning-admission-v2.json`. The original four-case pilot remains unpassed; it was not overwritten by the supplement.

The v2 comparison then froze its own protocol and C1's 16-episode denominator. Four episodes ran, totaling six turns. Both normal Scope confirmation turns ended with `stopReason: error` and `Error Code unknown: The usage limit has been reached`, although OMP exited zero and emitted `agent_end`. Neither produced a final response or Scope artifact. The other two episodes completed the expanded-registry no-construction observation; twelve C1 episodes and all C2/C3 episodes remain unstarted. Comparison expansion stopped without another model call or candidate adoption. Current diagnosis: `/home/user01/project/iis-evidence/r3-20260906/r3-provider-failure-report.json`.

`run_agent.py` now separates the observed `agent_ended` event from successful model completion. A clean invocation requires exit zero, no timeout, the requested model, and a nonempty final assistant response with `stopReason: stop` and no model error. Error, abort, truncation, empty output and an unfinished tool-call turn cannot provide a verdict or reuse an earlier success response. Raw terminal text and error details remain evidence, not substituted error prose.

Planning, completion and Probe/Verify invocation exits consume this clean result. Their reports independently inspect native completion, so an old clean flag or positive review cannot override a provider failure. Planning also checks the previous raw turn before resuming; paired Probe/Verify execution does not advance after a transport failure. Existing domain-level `FAILED` or `INCONCLUSIVE` decisions remain valid normal model endings, not transport errors.

Scoped verification passed 33 tests. Replay of 16 retained native turns preserved 14 normal endings and rejected the two provider errors. The actual report CLI rejected the full C1 denominator and still accepted the separately reviewed two-case control. No old metadata, request, approval, raw event or terminal file was rewritten; no operating installation, model configuration, runtime or candidate planning skill was changed by this correction. No provider retry was attempted. Further comparison requires restored provider access and a fresh admission decision under the retained no-replacement protocol.

### Third comparison and stale-generator stop — 2026-09-06

The separately authorized v3 comparison completed C1's 16 episodes and 44 native turns. Direct review and the actual report CLI passed capture/currentness checks for all 16. C1 reduced repeated unchanged investigation in the first paired gate and remains a candidate for final-combination validation, not an installed or finally adopted operating contract. The canonical-artifact baseline also exposed a retained normal rejection: Matt declared no applicable Behavior authority, while the canonical Ticket validator rejects `Behavior Authorities: None`. The candidate used a reviewed canonical artifact authority and reached Ready. This does not establish that C1 fixes that validator limitation.

C2 stopped on a Main-owned measurement error: fixture preparation called a stale `planning` module retained in a persistent Python kernel, rather than the current frozen generator in a fresh process. All 12 prepared C2 inputs differ from the declared source; four actual one-turn observations are invalid measurements and eight remain unstarted. No C2 quality or efficiency conclusion is available. C3's 16 episodes and the conditional 18-state planning / 16-state R2 final-combination checks were not started. No failed input or result was replaced, repaired in place, or retried.

A separate non-model fresh-process comparison checked every C1 and C2 initial snapshot after root-path normalization. All 16 C1 inputs match the declared frozen generator; all 12 C2 inputs differ. C1 evidence therefore remains usable for its bounded stage conclusion. The C2 report CLI rejects the full denominator. Durable stop report: `/home/user01/project/iis-evidence/r3-20260906/r3-generator-drift-report.json`; original v3 evidence: `/home/user01/tmp/iis-r3-20260906/comparison-v3/`.

Prospective preparation now records `fixture_source_sha256` captured when the generator module is loaded. Preparation and execution reject a source file changed since import; execution also rejects missing or mismatched preparation provenance before invoking the model. Use the actual `planning.py prepare` CLI in a fresh process, not a retained notebook module. Existing unbound metadata remains readable for historical reporting but cannot be silently promoted into new execution by adding the field. Changed source requires separately prepared inputs and a newly frozen protocol.

Two new regression tests failed before this correction; all eight capture tests pass afterward. The actual run CLI also rejected one retained unstarted invalid input without a native turn or metadata change, and fresh CLI preparation produced source-bound metadata. No model was invoked for these diagnostics. Unmeasured projection skill edits were restored while their patch and hashes remain preserved; operating installation and delivery runtime were not changed. No final combination is adopted.

### Fourth comparison and final-combination result — 2026-09-06

The user explicitly authorized resuming from C2 with fresh source-bound inputs. The v4 protocol and all prior failed cohorts remain separate. Durable report: `/home/user01/project/iis-evidence/r3-20260906/r3-comparison-v4-report.json`; raw evidence: `/home/user01/tmp/iis-r3-20260906/comparison-v4/`.

C2 was rejected at its first paired gate: four episodes/six native turns preserved the observed semantic boundaries but did not establish reduced redundant Behavior work. Both profiles already reused unchanged approved authority without reapproval. Eight predeclared C2 episodes remain unstarted after rejection; no replacement trial was run. The full Behavior procedure remains unchanged.

C3 completed all 16 episodes/26 native turns on C1. Both initial paired executions consumed 996 fewer bytes of duplicated To Spec/To Tickets instructions (57708 to 56712); the normal and weakened external-effect contracts retained their canonical owning-leaf guards. This bounded instruction reduction is not a general timing, artifact-size, or user-remediation improvement. C1 and C3 advanced only to final-combination validation at immutable revision `1f4ab8c5e1a08450dd025f497f44d0f0fdf844d5`.

The exact C1+C3 profile completed all 18 planning states in 34 native turns. Main reviewed every full terminal and material authority/Spec/Ticket artifact. The actual planning reporter rejected adoption with one `insufficient_causal_evidence` finding for `lifecycle-counterexamples--closed-policy`; capture, model, continuation, hashes, current artifacts and protected product boundaries had no reported errors. The nominal closed-policy input preserves either allowed confirmation/expiry race winner but does not close expiry eligibility/trigger, attribution and complete retry/interruption semantics. Its reservation rules are also appended under a publication/legacy Scope. The model returned unapproved product proposals rather than a normal Ready projection. Main did not invent approval, rewrite the input/oracle, or rerun the case. This is insufficient normal-control evidence, not an established candidate regression.

The separate final R2 regression passed all 16 completion states: eight valid completions and eight correct noncompletions, with `errors: []`. Two actual Ready Probes returned COMPLETE; one separate verifier executed the authored CLI through the then-current legacy verification lifecycle and produced `VERIFIED`, `COMPLETED`, canonical `done` and execution `COMPLETE`. The Probe-only control stayed `ready` and did not satisfy delivered completion. All 16 Outer Main assessments inspected current readback and left their targets unchanged. This paragraph is historical evidence only and does not define the current boundary-tool protocol. The predeclared one-repetition R3 oracle was supplied only to the report process; the original two-repetition R2 oracle was not modified.

Focused regression passed 173 checks in the isolated evaluator/source tree. A separate historical candidate-payload invocation passed 164 checks but had one loader error because `tests.test_ready_agent_capture` is not present in that payload; those evaluator-source tests passed in the source-tree invocation. Both command results are retained without calling the errored command a passing suite.

**The final combination is not adopted.** Passing R2 and reduced duplicate instructions do not override the missing closed-policy normal control. All six isolated planning skill files already match the R2 baseline and were left untouched; candidate revisions, the immutable evaluation payload, and the unadopted patch remain available. The 228 protected operating source/installed files are unchanged, and the evaluation-owned readback service was stopped. No operating merge, installation switch, push, runtime reduction, Probe removal or later-roadmap work occurred. A new model comparison requires separately fixed policy-complete inputs and explicit authorization; none of these results may be replaced.

## R3 completed — 2026-09-06

**C1 and C3 are adopted and applied in the isolated R3 worktree; C2 is rejected. R3 is complete within that engineering scope, not an operating installation switch.** Durable completion report: `/home/user01/project/iis-evidence/r3-20260906/r3-completion-report.json`. This decision follows the user's explicit instruction to continue R3 through completion and supersedes the adoption hold, not the historical v4 measurement result.

The reservation normal-control preparation now states its complete local authorization, explicit-expiry trigger, terminal retry/rejection, response-loss, interruption/restart, readback and publication-interaction rules under an exact combined authority scope. It preserves both allowed confirmation/expiry race winners and introduces no deterministic scheduler. A fresh-process comparison of all 18 generated states showed that only this normal state's request, authority and index changed; the other 17 states and the normal product source/state stayed unchanged after root-path normalization.

The separately frozen `final-closure-v5` cohort contains four episodes: policy-complete normal and unchanged open-policy controls on C1 and on the exact C1+C3 profile. All four passed direct semantic review and the actual capture/currentness reporter, with `errors: []`. Six native model turns were executed, without replacement trials. Both normal episodes reused the existing approved authority byte-identically and reached an approved Spec plus a complete Ready Ticket Set after one explicit integrated-understanding approval. Their real validators returned `VALID` and `VALID SET`. Both open controls exposed unresolved product decisions without adopting authority or writing Spec/Tickets. No product state was mutated.

This supplemental paired evidence closes the previously missing normal-control criterion. The combined adoption also retains the 17 sufficient v4 planning-state observations, the earlier C1/C3 stage evidence, and the exact-profile 16/16 R2 completion regression. The old failed v4 report remains unchanged; there is no claim that v4 became an 18/18 passing cohort or that all R2 states were rerun for this closure.

Applied source files match the already evaluated revision `1f4ab8c5e1a08450dd025f497f44d0f0fdf844d5` byte-for-byte:
- `scope-shaper/SKILL.md`, `matt/skills/ask-matt/SKILL.md`, and `matt/skills/grill-with-docs/SKILL.md`: reuse attributable current first-hand facts and investigate missing/changed boundaries without repeating broad research solely because the planning leaf changed.
- `matt/skills/to-spec/SKILL.md` and `matt/skills/to-tickets/SKILL.md`: remove duplicate explanations while retaining canonical provenance, replaceability, self-review, current-obligation ownership and preservation rules.

`behavior-design-lead/SKILL.md` remains unchanged: no incremental benefit justified C2's Behavior-procedure reduction. Spec/Ticket separation, actual product boundaries, unknown external conditions and R2 completion protections remain intact.

The applied source passed all 173 focused planning, validator, R2-completion and capture regression checks. The 228 protected operating source/installed files and all 20 indexed historical v4 evidence files remained unchanged. No operating merge, installation update, push, runtime reduction, Probe removal, new service or R4+ work was performed. Candidate efficiency claims remain bounded to the observed redundant-investigation and duplicate-instruction reductions, not statistical reliability, generalized timing or measured user-remediation savings.

## R4 isolated implementation comparison — 2026-09-06

Completion report: `/home/user01/project/iis-evidence/r4-20260906/r4-completion-report.json`. The isolated R4 worktree adopts C1+C3; C2's additional completion prose showed no incremental benefit and is excluded. The evaluated production source is pinned at `76c85b1`: earlier decisive preconditions in the existing implementation preflight, successful complete command-output observation binding, and reservation ordering that leaves a rejected overlapping observation executable after release. Persisted fields and the distinction between runtime currentness and product sufficiency remain intact.

The fixed model was `opencodex/gpt-6-astra`, medium thinking, one repetition per state, with no replacement runs. Three pilot runs were excluded from scoring; candidate screens used 6+12+6 runs, followed by a fresh 21-state baseline/candidate comparison of 42 runs. All final native captures settled cleanly. Main reviewed actual actor commands, final product observations, protected identity and external state before parent readback, with disjoint Sol High reviews of the retained evidence.

| Final paired boundary | Baseline | C1+C3 |
|---|---:|---:|
| Normal or owned-repairable states completed | 11/15 | 15/15 |
| Normal product observed but runtime blocks completion | 4 | 0 |
| External-limited states kept non-complete | 6/6 | 6/6 |
| Unsupported product `COMPLETE` | 0 | 0 |

One baseline result omitted the ordinary completion field: its raw parsed value remains `null`, while its explicit terminal decision and runtime state are `BLOCKED`. This observed formatting defect is retained, not reparsed into a passing result or replaced. Baseline credential-unavailable/rejected runs also left the independent engine change undone; the candidate made that bounded change without claiming external success.

All 21 pairs matched after declared root/port normalization, not literal byte equality. Initial authority equality is supported by the fixed successful initializer and separate deterministic reconstruction, not a retained original state snapshot. The 42 final and 24 screen products had no source/protected drift after parent observations; final external state was already established by actor requests and did not change during parent readback. The 92 relevant runtime/delivery/capture regressions passed. Two reviewer jobs suffered terminal-delivery failure; their retained evidence was independently verified by Main rather than counted as successful audit jobs.

The 259 protected operating/historical/configuration files and the R3 source snapshot remained unchanged; all evaluation-owned services were stopped. No operating installation, merge, push, R5/R6 work, new verifier, or persisted evidence schema was introduced. These are bounded single-repetition observations using disposable loopback authorities, not general reliability, real-provider/human-approval, timing significance, or measured user-remediation savings claims.

## R5 isolated execution — integration not admitted — 2026-09-06

Execution report: `/home/user01/project/iis-evidence/r5-20260906/r5-execution-report.json`. Production remains the R4 separate Probe→Verify contract. An actual runtime-handler counterexample showed that removing the Probe predecessor's target/output agreement admits a source exclusion that A rejects, while both permit the existing tracked runtime-state output. B was stopped before model comparison; its draft skill diff is retained outside the worktree. This is evidence against the selected minimal cutover, not proof that every integrated design is impossible or that A independently validates all output semantics.

The unchanged A payload ran 15 unscored episodes / 30 model invocations. Seven initial causal pilots matched their expected runtime/admission causes. The first new-input pilot also retained four pre-model rejections caused by incorrectly pinning mutable host databases. Only the four previously uninvoked retention/report-bias cases ran later under a corrected configuration-only profile binding; no completed case was replaced. Those four preserved current counterexamples and ordinary-entrypoint evidence, with no parent-created operations.

One intended-normal minimal-input episode returned `FAILED` for a combined two-edge input after Probe explicitly left its contractual applicability uncertain; the holdout accepted the three single-edge cases. The authored equivalence wording did not explicitly resolve the combined-edge interpretation. Preserve that disagreement: the minimal-input family is not an admitted clean scored denominator, and no production guidance or fixture was rewritten to make it pass. There is no scored A/B cost or quality result and no new 16-state R2 comparison.

Final isolated regression passed 302 tests. The original 307-test run and its three failures remain recorded. Five tests requiring the live user's installed payload/global links to equal whichever checkout ran the unit suite were removed, including two that happened to pass; no operating installation was changed. This test cleanup does not establish installed-host compatibility. Evaluation capture and regression changes remain isolated; R5 integration adoption, operating transition and R6 were not performed.
