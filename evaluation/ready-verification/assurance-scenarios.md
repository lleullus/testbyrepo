# Assurance causal evaluation

Status: NOT_RUN

This describes separately authorized real-invocation experiments, not executed model tests. Python suites and score_assurance.py never invoke models/subagents. Case catalog and expected outcomes are evaluator-only; keep them out of actor inputs. Frozen old sources are comparison conditions, never active completion roles or fallback.

## Comparison design

A: same implementation/source/artifact/runtime/tools/authority/initial state, compare historical assurance with candidate machine observations plus adversarial lanes/closure. B: same request/Scope/base state, compare complete historical construction path with candidate planning/implementation/assurance. Reviewer removal can change the implementation itself; do not merge A and B causally.

Preserve these ablations: machine-only versus one Prober; one versus targeted+scout; full narrative versus initial embargo; full Baseline versus lane projection; same versus different models; equal total versus equal per-lane budget; correction evidence reacquisition cost. A user-approved smaller experiment reports omitted comparisons, not an implied full evaluation.

Freeze experiment ID, exact case/repetition/variant denominator, model/effort/tools/budget conditions, candidate and input bytes, safe stop/settlement rules and numeric thresholds before results. No hidden default models or retry-to-pass. Keep failed/BLOCKED/cancelled/timeout/skipped runs with reasons and all costs. No result-selected removal of required cases or weak normal controls.

## Causal cases

`assurance-cases.json` identifies wrong actual entry, weak oracle, omitted mapping, framing, duplicate lanes, same-instance state, source/runtime/mechanism drift, shared cleanup contamination, uncertain non-idempotent effect, correction, false block, always-incomplete and behavioral-document cases.

The existing fixture catalog supplies actual CLI/service boundaries. Its weak-oracle defective/normal pair both pass a weak assertion while returning different actual values. Its parallel-contamination shared/isolated pair exercises the actual file-backed write lane-a → reset lane-b → read lane-a interleaving. The latter is a deterministic schedule of a shared-resource conflict, not a measurement of scheduler probabilities. The caller owns service startup/readiness/settlement. Never use production credentials or replay dangerous effects merely to obtain a red case.

Helper/schema fixtures prove contract handling, not model detection. Framing/disclosure and behavioral-document cases require actual independent host invocation logs, hypothesis capture, raw actions/readbacks and exact loaded source. Shared workspace without access controls gives procedural embargo only. Unit tests cannot prove independent reasoning.

## Offline scorer input

Run `python3 -B evaluation/ready-verification/score_assurance.py EXPERIMENT.json RECORDS.json`. It reads existing files only and returns offline evaluation_pass, never production completion permission or authenticated evidence.

Experiment schema `iis-assurance-experiment/v1`:

- experiment_id; positive repetitions; variants keyed by variant name, each with nonempty candidate and conditions file refs.
- cases with unique id, expected DEFECT/NORMAL/LIMIT, defect_id for DEFECT, exact inputs refs and evaluator oracle `{path: [JSON keys/indices], equals: expected readback}`. Include at least one defect and normal control.
- limits: min_detection in [0,1], max_false_completion, max_false_block, max_incomplete. Declare actual chosen values before running; no defaults silently select policy.

Current Assurance refs are executor-owned `{snapshot,path}` values. Conditions preserve selected models/effort/budgets, fixture/tool source and observation boundaries. Immutable native exports must remain accessible. A copied ref/JSON field alone does not prove a new invocation or evidence provenance; the experiment owner checks actual acquisition. Arbitrary natural-language causal judgments require offline analysis, not automatic interpretation by this finite JSON oracle.

Each record has experiment_id, variant, case_id, repetition, unique run_id; exact candidate/conditions/inputs refs; events refs; state COMPLETE/BLOCKED/FAILED/CANCELLED/TIMEOUT/SKIPPED; and nonnegative cost tokens/tool_calls/wall_seconds/correction_seconds. Non-complete records include reason, cannot claim EVIDENCE_COMPLETE, remain in the denominator and retain cost.

Complete records additionally have target `{source,artifact,runtime,mechanism}` identities; observation trace ref; mutation ref containing run_id and actual target_mutated boolean; settlement ref containing run_id and SETTLED/UNKNOWN; closure EVIDENCE_COMPLETE/BLOCKED; findings array `{defect_id,lane,trace}`. Each trace contains exact run_id/target, initial_state, trigger and structured authoritative readback. The fixed evaluator oracle must match actual readback. An actor-supplied expected field cannot override it. Missing identity/mutation/settlement/raw fields do not default successful.

## Measurements and interpretation

Count actual causal defect detection by scheduled defect run, false completion including wrong identity/unknown effects, normal false block, incomplete outcomes, all costs, duplicated exact causal traces, per-lane unique contribution and per-run detection vectors. Count one causal defect only once even if several lanes report it. Detection vectors permit offline correlation analysis; paraphrased semantic duplication still requires evidence analysis.

The scorer sums recorded wall_seconds/correction_seconds; the exporter must measure actual run critical path, not sum parallel lane durations and call that wall time. Native dispatch bytes, hypothesis disclosure events, actions, effect readbacks and cost source remain available for inspection. A missing run is not zero-cost success. All-BLOCKED is not a quality win.

Structural negative cases must not close and normal controls must succeed. Detection/cost adoption uses the predeclared numeric criteria and observed limitations, not small-sample generalization. Failed candidate evaluation stops rollout; it does not automatically restore deleted approval roles as a fallback or install a new Result Reviewer.
