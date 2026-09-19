# Current IIS verification boundaries

Dated adjacent records are historical. Current IIS separates deterministic helper/packaging checks from actual model behavior and operating activation.

## Source and utility checks

```text
python3 -B -m unittest discover -s tests
PYTHONPATH=observatory/src python3 -B -m unittest discover -s observatory/tests
python3 -B iis-workflow/tools/assurance.py --help
```

No test in these suites invokes a model or subagent. Local subprocesses and disposable loopback services exercise fixture boundaries. Assurance tests bind disposable committed repositories, capture actual native command output and distinguish positive control from failed readback, missing result, stale target/runtime/raw evidence, skipped job, duplicate invocation, unresolved finding and unsettled effects. Packaging tests cover a frozen c856dd7 old-v4 source independently of new constants, retirement, installed/candidate inspection, rollback/remove and preserved user entries. Source-text assertions are not behavioral compliance evidence.

Use prepare/inspect with disposable store; activate/rollback/remove only disposable client roots unless operating changes are explicitly authorized. Observe actual retired link absence, retained user entries and restored previous installation. Current installed inspection is own-manifest integrity; explicit candidate inspection also applies current topology.

## Real evidence and completion

Follow `iis-workflow/references/assurance.md`: actual source/execution identity, native gate status and required jobs, direct observation predicate outcome, independent Production Heuristic Probe action/hypothesis/raw readbacks, every started invocation/effect and authoritative settlement. EVIDENCE_COMPLETE means this declared evidence structure closed, not universal semantic success, model independence or write authority.

Main checks actual host/result attribution, current originals/target/request authority and scope of result before the status-only write/readback. A no-finding cannot replace a required direct result or override a material counterexample. New target completion evidence is reacquired. Unsafe/non-idempotent uncertainty requires the effect owner, never blind replay.

## Behavioral evaluation

`evaluation/ready-verification/assurance-scenarios.md` defines separately authorized same-target assurance and end-to-end comparisons. Actual dispatch bytes/disclosure sequence and causal traces are retained. Python tests cannot establish hypothesis diversity, embargo compliance or better model detection. NOT_RUN remains until a real cohort is performed. Offline score_assurance aggregates frozen fixture oracles and attributed external results; it does not invoke models, authenticate evidence or authorize production completion.

## Operating activation

Source tests/disposable install do not prove operating adoption or existing-session reload. Operating activation needs current permission, affected-work settlement and exact link/readback checks. The installer does not restart clients. Rollback restores install entries, not product/provider effects. Do not describe source-only retirement as deletion from the still-active operating release.

## Local cutover checks — 2026-09-19

- `python3 -B -m unittest discover -s tests`: 105 tests passed. Initial execution had 18 fixture permission errors and one directory-inventory assertion failure; the private fixture root now uses mode 0700 and the incidental inventory test was removed, not re-pinned.
- `PYTHONPATH=observatory/src python3 -B -m unittest discover -s observatory/tests`: 36 tests passed.
- Disposable actual CLI smoke: Baseline validate/bind, native stdout capture, EVIDENCE_COMPLETE, failed direct-readback BLOCKED, and status-only comparison passed; canonical ready Scope was not changed.
- Offline scorer CLI accepted synthetic paired traces and rejected a missing run. This is scorer behavior, not real model performance.
- Disposable installer CLI exercised frozen c856dd7 v4 activation, current candidate prepare/inspect/upgrade, retired role-link removal, rollback and remove. User-owned entry and historical release survived. No operating installation was activated.
- Actual model/subagent behavioral evaluation: NOT_RUN. Operating adoption and session reload: not performed. The disposable smoke script and temporary stores were removed.
