# Assurance: evidence execution and closure

This is one evidence contract, not product authority, independent admission or a semantic verdict. Thesis/Scope and any approved Transition remain authoritative. No final judge, review artifact, agent runner, database or host authentication is introduced.

## Baseline

Use exactly one `iis-assurance` fenced JSON block in `## Assurance Baseline` of the Plan. Assurance-only may supply the same JSON as an invocation-local file without creating an implementation Plan. `tools/assurance.py validate BASELINE` validates the actual block bytes and the canonical ready Scope. It calls the existing Scope validator rather than implementing another source authority parser.

The `iis-assurance/v1` baseline contains:

- `scope`: `{path, sha256}` of the exact ready Scope; all Scope-bound originals are read directly.
- `obligations`: `{anchor, evidence}` rows. `anchor` is the exact text of one nonempty blank-line-separated paragraph in Scope Acceptance; `evidence` is a nonempty list of gate/observation IDs. Every paragraph must be covered, with no foreign or duplicate anchors. This checks authored coverage, not completeness of natural-language meaning.
- `gates`: `{id, argv, cwd, timeout, mechanisms, jobs, jobs_path}` rows. Use an argv array, absolute cwd, positive timeout and nonempty `{path,sha256}` mechanism references. `jobs` lists required native jobs; use an absolute `jobs_path` when nonempty, otherwise null. The native job export must contain this run's `run_id`, `gate_id` and `jobs` map with every required job `SUCCESS`; skipped/unknown/absent is not success. `IIS_ASSURANCE_RUN_ID` and `IIS_ASSURANCE_GATE_ID` are supplied to the native command. Never import stale CI status as a fresh run.
- `observations`: `{id, initial_state, trigger, readback, predicate}` rows. Each string identifies the actual procedure/boundary. At least one required observation is necessary, including for artifact-only work. Observation results distinguish `SATISFIED`, `VIOLATED`, `UNOBSERVABLE`; existence of output is not satisfaction.
- `surfaces`: `{id, boundary}` rows naming actual attack boundaries, not expected bugs.
- `lanes`: `{id, surfaces, required, min_actions, budget, safety}` rows. Surfaces are IDs; required is boolean; min_actions is positive; budget and safety are nonempty strings. Every required surface has a required lane. An empty surface/lane set is allowed only with a nonempty `no_probe_reason` for a genuinely non-behavioral artifact. Skill documents change behavior and are not exempt because their extension is `.md`.
- `no_probe_reason`: null for an ordinary behavioral target, otherwise the exact grounded artifact-only reason.

All IDs are unique across gates, observations and lanes. Baseline authorship belongs to the planning owner, or Main's assurance-only preparation. Implementer/Prober do not edit it. A legitimate revision preserves previous attempts and reasons and starts new evidence acquisition; do not remove a failed requirement after seeing results.

## Binding

`bind BASELINE --root ROOT --base FULL_SHA --execution EXECUTION.json --output BINDING.json` seals a clean committed Git working tree and full result SHA. It records base→result diff digest, exact tracked file bytes/modes, canonical Scope/original digests and exact Baseline block digest. No automatic commit or repo-snapshot occurs. Without an authorized clean committed target, return `TARGET_NOT_SEALED`; implementation self-check is still useful but cannot establish normal closure. Evidence outputs and mutable disposable fixtures must be outside the source root. A submodule or symlink must not hide mutable executable bytes; the initial helper rejects those tracked target forms.

Execution identity input is `{artifacts: [file refs], runtime: [file refs], mechanisms: [file refs], note: string}`. Mechanisms must be nonempty. Runtime/artifacts may be empty for a native source/artifact target; note explains the actual execution boundary. Runtime references are native launcher/config/provider identity readbacks, not a claimed source SHA. Build first when needed, then bind the produced artifact. A build gate may create an artifact after source sealing: `bind-execution BINDING EXECUTION --output NEW_BINDING` produces the final binding; reacquire evidence against that final binding, never rewrite earlier results to a new identity. Native builds can instead be completed as implementation self-check before binding.

All references are absolute regular files with actual SHA-256; executable target modes are also sealed. Currentness rereads actual bytes, tracked/untracked status, HEAD, source set, originals, Baseline and execution files. A new target, mechanism, runtime/config or authority invalidates completion evidence. Old raw evidence remains navigation/reproduction only. Hashes do not prove deployed identity, independent judgment or authenticity.

## Native gate capture

`run BASELINE BINDING GATE_ID --output NEW_DIRECTORY` executes exactly the declared foreground command and stores stdout/stderr bytes, exit status, job export, elapsed time and binding identity in `result.json`. The output directory must not exist and must be outside the source root. Use existing project launchers; services belong to native host lifecycle facilities, not this helper. Effects require current authority and the activity/settlement record below. Timeout/failed launch is blocked, never silently retried; surviving effects require their owner's containment/readback. stdout and exit zero alone do not establish product observations.

Self-check results may be reused only if they were actually captured for this same sealed binding/mechanism. Intermediate-tree success is not final evidence.

## Results and activity

Every gate, observation and probe result has:

`schema: iis-assurance-result/v1`, `kind: gate|observation|probe`, `id`, actual `invocation`, `binding` (SHA-256 of canonical binding JSON), `completion: COMPLETE|PARTIAL|BLOCKED`, nonempty `evidence` file references and `effects` (effect IDs, or an explicit empty array).

Observation adds `outcome`, `initial_state`, `trigger`, `readback`, and `predicate` matching its declared boundary. The observation producer executes/reads the real boundary and preserves raw evidence; human judgment uses the existing requirement's human confirmation, not a new LLM approver. The helper checks recorded outcome and attribution, not whether arbitrary natural language or raw output actually proves it.

Probe adds `outcome: COUNTEREXAMPLE_FOUND|NO_COUNTEREXAMPLE_WITHIN_BUDGET|UNOBSERVABLE`, `hypotheses` (file references recorded before narrative disclosure), `actions` and `findings`. Each action records assigned `surface`, `hypothesis`, `initial_state`, `trigger`, `readback`, and nonempty `evidence`. Each finding records `anchor`, `materiality: MATERIAL|OUT_OF_SCOPE|UNKNOWN`, `disposition: OPEN|DISMISSED`, and nonempty evidence. A material unresolved candidate or required unobservable boundary cannot be no-finding. A reproducible finding also preserves runnable content, conditions, wrong authoritative readback and directly evidenced sibling scope in the ordinary result; an expiring pathname alone is insufficient. `COUNTEREXAMPLE_FOUND` must have an attributable material open finding. A foreign-scope finding is reported without inventing a current obligation.

Main supplies one ordinary activity export, not a persistent registry:

```json
{"run_id":"the binding run_id","evidence":[{"path":"/absolute/host-actions.log","sha256":"actual digest"}],"started":[{"kind":"probe","id":"targeted","invocation":"actual-host-invocation"}],"effects":[{"id":"fixture-reset","owner":"actual-owner","state":"SETTLED","evidence":[{"path":"/absolute/readback.json","sha256":"actual digest"}]}]}
```

Record every started invocation, including optional/failed/cancelled work, and every started effect. Each result's effect IDs must exist in this export. Main checks the export against actual native host action/result delivery; the helper cannot discover an invocation or effect deliberately omitted by its caller. `SETTLED` requires authoritative raw readback, not the boolean alone. Unknown/unfinished effects block. Safety facts are never embargoed.

`close BASELINE BINDING --activity ACTIVITY.json RESULT.json ...` compares the predeclared denominator and every started invocation, not just returned workers. It accepts only exact started/result identity pairs, completed required gates/observations/lanes, sufficient actual assigned-surface attempts, current raw refs, and settled effects. Optional lanes that started also need attributable terminal results; their material findings/effects cannot be ignored. Several no-findings never offset one unresolved material finding.

Output is `EVIDENCE_COMPLETE` or `BLOCKED` with reason codes. Neither is a semantic verdict or write authorization. Malformed input, missing fields, failed observations and unknown identity/effects do not default to success. Native gate records can be checked structurally but are not signed credentials; Main retains actual execution provenance. New automation must not claim to authenticate LLM-authored JSON.

## Independent search and completion

Before hypothesis capture give a lane the exact originals, actual target, assigned surface, budget and safety/isolation/settlement constraints. Do not give implementation success narrative, Plan candidate findings, full Baseline rationale or peer conclusions. After hypotheses, reveal needed recipes/raw predecessor evidence. A scout explores from originals and target rather than Planner candidates. Preserve actual dispatch bytes and disclosure sequence in host evidence. When access control is unavailable, explicitly report procedural embargo; do not claim enforced isolation or statistical independence.

Separate DB/cache/queue/tenant/session/cleanup resources before fan-out. Serialize only the shared mutable boundary that cannot be isolated. Hypothesis diversity is assessed in offline behavioral evaluation, not by role names or unit tests.

Main waits for actual terminal delivery and settlement before correction. It checks current authority, scope of request, exact identities, accessible unchanged results and whole-request coverage; it does not issue a second whole-Scope semantic judgment. A concrete counterexample routes to the currently authorized implementation actor; a method/oracle gap to its planning/tooling owner; meaning and transition changes to their original owners. A finding label alone does not authorize repair. Urgent containment may interrupt search, preserving partial evidence and unknowns.

After current closure and authority checks, Main alone edits only `Status: ready` to `Status: done` and reads back the exact status-only delta. `recording READY_COPY DONE_FILE` checks that delta without writing either file. Keep ready preimage, closure, source target and actual write/readback separately. Recording is not product drift and does not relabel old evidence as execution on a later commit. A concurrent product/Acceptance change is not a status-only exception. Historical done and one Scope's closure never prove whole-request completion.
