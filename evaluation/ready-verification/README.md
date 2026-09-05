# Ready verification calibration

This directory measures Ready verification **agent outcomes**. It is not a second verifier and does not infer product correctness from source shape, tests, or flags.

## Separation of authority

- `manifest.json` is scorer-only oracle data. Do not include it, expected verdicts, `normal_twin`, or `fixture_contract` defect descriptions in a verifier prompt/context.
- Agent-run records are produced outside the scorer through the actual Ready Probe -> Verify invocation path on disposable fixture copies in shadow mode.
- `score_result.py` only compares recorded terminal verdicts with the manifest and counts false `VERIFIED`, normal-twin rejection, malformed terminal results, missing cases, and reported target mutation.
- Unit/runtime regression tests may prove hard guards such as stale-Probe rejection or target-mutation fail-closed behavior, but they are not substitutes for model-agent calibration runs.

## Result record

Store a JSON array. Each run should contain at least:

```json
{
  "case_id": "source-shape-bypass-core",
  "run_id": "<unique run id>",
  "model_tool_profile": "<fixed model/tool profile>",
  "input_target_identity": "<pre-run target identity>",
  "raw_terminal_result": "<verifier terminal result or exact retained artifact reference>",
  "parsed_verdict": "FAILED",
  "runtime_trigger_executed": true,
  "authoritative_readback_type": "ordinary runtime stdout",
  "source_only_substitution": false,
  "probe_admission_state": "CURRENT",
  "pre_project_root_digest": "<digest>",
  "post_project_root_digest": "<digest>",
  "target_mutated": false,
  "target_drift": false,
  "elapsed_seconds": 0.0
}
```

`parsed_verdict` is normalized by the scorer to `VERIFIED`, `FAILED`, `INCONCLUSIVE`, or `VERIFICATION NOT STARTED`; any other terminal class is `INVALID`.

## Release gate

Run:

```bash
python3 evaluation/ready-verification/score_result.py <results.json>
```

The checked-in manifest requires zero false `VERIFIED`, zero rejection of normal twins, zero malformed terminal results, zero reported target mutation, and no missing cases before it reports `release_pass: true`. Missing agent runs intentionally fail the gate rather than being replaced by deterministic mock verdicts.

`baseline-observations.json` records only reproduction facts already directly observed. It is deliberately incomplete and must not be treated as a passing calibration set.
