# Phase 7 Runtime Evidence

Status: `RUNTIME_VERIFICATION_BLOCKED`

Updated on 2026-08-05 in `/home/user01/project/iis-skills-simplify-leads` without committing.

The prior `RUNTIME_VERIFIED` declaration is invalidated. The previous production Source Adoption implementation
used `RENAME_EXCHANGE` followed by a rollback exchange. A competing `os.replace(latest, target)` between those
two exchanges could move the latest user object into the temporary pathname and then delete it. Its mode-only
directory path could exchange a non-empty canonical directory with an empty temporary directory and fail while
removing the old directory, leaving canonical children absent. Linux pathname APIs available in this Adapter do
not provide a linearized compare-and-replace/delete primitive against arbitrary uncooperative writers.

`LinuxSourceAdoptionAdapter` now fails closed before every canonical mutation with `AdoptionConflict`; it does
not claim advisory occupancy as a substitute. This preserves existing regular file/create/delete/symlink/
directory state but leaves production implementation adoption unsupported. `create_production_module` accepts no
caller-supplied implementation review callback. Its Module-owned bounded implementation review/check Adapter runs
exact configured processes against a bounded projection and read-only source namespace, and fails closed for
timeout, missing tool, unsafe effect requirement, or unreadable result. Source mutation still stops at Source
Adoption, so the 24 deterministic public flows cannot establish production runtime verification. Authenticated READ is also
disabled because no external authoritative grant/provenance exists. Phase 8 remains closed.

## Tested Source Identity

Base Git revision: `7912f190943a922b1abc67614cf3a57790a921ba`

The tested source is the base revision plus this exact dirty-worktree manifest. The evidence report itself was
written after the final run and is not an executable input. The command output in this report is authoritative
for the dirty worktree identified here.

```text
d36c7bdeac28b7455b25082ebd8821f9ddd1745517a196045a8d775d2d185625  PHASE-7-INTEGRATION-RUNTIME-VERIFICATION-CONTRACT.md
0ab1dfbd216c28891f424a5f80476d5c14f4999889dadde83150ed1864d4301d  IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
f3ff51eb3eaab31968d86bf25f91eff6aa61c6899ba53ef6d314a218e2bf871a  implementation-verification/implementation_execution.py
d1d40d5bb3d4656d8ca43e691a29fb648363ab2f2d6594491d61a3c6c585a26a  implementation-verification/production_adapters.py
3386f53441ae5e8af07b7254be3eb5ec85b363e8ad299d40b0031699203ae066  implementation-verification/production_entrypoint.py
cf97499477bd0513bc7c7cf398947cb71ef16d92e9c3d140e800287606690ff8  implementation-verification/production_smoke.py
8d3ae7ee3df452bc54eeb5f8811fa1fce1d632c6309e20641b1bb977be497a84  implementation-verification/verification_execution.py
3899d77d5a60bcfeff5a525a4703e8c8c24ab96268f2e0420ddc55c04903d9a8  implementation-verification/tests/test_phase6_effect_observation.py
38b88012b88e3250313198a5de7619e5484bfc7a2337364bedd946bcd9cea978  implementation-verification/tests/test_phase7_public_contract.py
d8aa7a58142dbc12883eb475cd88c76ec4675e7172b3bd35430e8a1d1dce7fce  implementation-verification/tests/test_phase7_fault_boundaries.py
dcded1cd2a25ceaf90ace0e2cb887190e96726d9b72b06d4630c0fb62d332e11  implementation-verification/tests/test_phase7_legacy_negative.py
fac9b69a597bc13ca721084adce705f08c2806c35d2365d025b3c9726bdeb584  implementation-verification/tests/test_production_conformance.py
bd7c56e19252bcb90f96975f0d0ca23dc9ed7a29c7c6f1395807b19f96191452  implementation-verification/tests/test_verification_execution.py
```

Runtime: Linux `6.6.87.2-microsoft-standard-WSL2`, Python `3.12.3`, bubblewrap `0.9.0`.

## Production Composition

`production_entrypoint.create_production_module` assembles:

```text
DurableWorkStore
ImplementationExecution
VerificationExecution
ModuleExecution
DurableBackend
ImplementationVerificationModule
```

The caller surface remains `implement(work, worker)`, `verify(candidate)`, and `inspect(work)`. No caller-owned
actor, capability, claim, authorization, run, flow, step, artifact, or replay value is accepted.

## Production Adapter Scope

| Seam | Production implementation | Variant/mode | Physical target and covered branches |
| --- | --- | --- | --- |
| Implementation review/check | `LinuxImplementationReviewAdapter` | `bubblewrap-module-owned-implementation-review-v1` | exact configured review/check processes; bounded request/output; read-only source; assignment bounds; timeout, missing tool, dangerous check without effect authority and unreadable result stop Candidate publication |
| Worker | `LinuxWorkerAdapter` | `bubblewrap-private-workspace-v1` | private candidate workspace writable; canonical source, planning authority and durable state host paths absent; allowed write and three forbidden-write branches |
| Fresh Verifier | `LinuxFreshVerifierAdapter` | `bubblewrap-fresh-projection-v1` | minimal namespace with exact projected Candidate/planning/full AC, read-only `/candidate`; prior verdict/plan/raw-artifact/implementation-check canaries absent; Candidate/canonical writes rejected |
| Evidence Runner | `LinuxEvidenceRunnerAdapter` | `bubblewrap-runner-owned-evidence-v1` | read-only Candidate, runner-only scratch, fixed SOURCE/LOCAL requests; authenticated READ is disabled because no external authoritative grant/provenance exists |
| Source Adoption | `LinuxSourceAdoptionAdapter` | `unsupported-uncooperative-writer-fail-closed-v1` | rejects regular file/create/delete/symlink/directory canonical mutation before write; no conditional-mutation conformance claim |

Enabled production Effect Adapter set: `[]`.

No concrete production message, payment, deployment, or other dangerous-effect consumer/target exists in this
repository, so no fake provider was enabled. `TestConformanceEffectAdapter` is labeled test/conformance-only and
covers exact authority, pre-dispatch marker, action, authoritative readback, ambiguity, non-reexecution,
implementation safety projection, cleanup and final-disposition semantics. It is not a verified or enabled
production provider. Unsupported production dangerous effects remain nonconclusive with zero dispatch.

## Physical Conformance

Command:

```text
python3 -m unittest -v tests.test_production_conformance
```

Result: `Ran 16 tests ... OK`.

- Worker: `/workspace` mutation succeeded. Canonical/planning/state writes failed physically. Protected bytes,
  inode and mode remained unchanged.
- Fresh Verifier: all four prior semantic canaries were invisible. Exact Candidate/full AC projection was visible.
  Retained Candidate and canonical source writes failed physically and bytes remained unchanged.
- Evidence Runner: fixed source/local requests ran through the production bubblewrap launcher, Candidate writes
  failed, scratch writes succeeded, and the Adapter produced the evidence artifact.
- Source Adoption: direct regressions preserve latest user bytes/inode after the former mismatch window and
  preserve a non-empty directory child and mode. Existing file/create/directory/symlink adoption all stop before
  canonical mutation.
- Authenticated READ: a caller-supplied root cannot self-grant current/outside-writable/credential/redaction
  authority; production READ is unsupported and nonconclusive.
- Multi-request SOURCE/LOCAL: each request has its own preserved artifact and matching artifact identity.
- Production composition: `create_production_module` accepts no caller implementation-review callback. Module-owned
  review/check closes a zero-mutation Candidate and, for a bounded Worker change, runs before the production flow
  stops at unsupported Source Adoption with canonical source unchanged.
- Enabled Effect Adapter conformance: not applicable because the enabled production set is empty.

## Public Flow Coverage

Command:

```text
python3 -m unittest -v tests.test_phase7_public_contract
```

Result: `Ran 24 tests ... OK` through a deterministic test-only adoption
adapter. It is not production conformance while production adoption is fail-closed.

| Flow | Executable evidence |
| --- | --- |
| 1 | `test_flow_01_dirty_source_success` |
| 2 | `test_flow_02_same_path_overlap_stop` |
| 3 | `test_flow_03_same_final_value_non_attribution` |
| 4 | `test_flow_04_zero_mutation_candidate` |
| 5 | `test_flow_05_known_gap_or_check_failure` |
| 6 | `test_flow_06_fresh_full_ac_positive` |
| 7 | `test_flow_07_disconnected_missing_observation` |
| 8 | `test_flow_08_direct_contradiction` |
| 9 | `test_flow_09_tool_evidence_failure` |
| 10 | `test_flow_10_source_non_mutation` |
| 11 | `test_flow_11_fresh_namespace` plus production canary conformance |
| 12 | `test_flow_12_candidate_commit_response_loss`, Candidate readback and a later overlapping adoption; it does not prove the full contract sequence because the adoption uses the deterministic test-only Adapter |
| 13 | `test_flow_13_verification_result_commit_response_loss`, including Candidate recovery and one fresh legal transition after `UNDETERMINED` |
| 14 | `test_flow_14_retained_candidate_plus_canonical_drift`, retained A evidence and stable live B `NOT_CURRENT` |
| 15 | `test_flow_15_no_complete_result`, active transition readback only; corrupt binding and unreadable-head variants are not exercised |
| 16 | `test_flow_16_no_actual_authority_no_dispatch` |
| 17 | `test_flow_17_authenticated_read_without_production_authority_is_undetermined`; production authenticated READ has no enabled grant path |
| 18 | `test_flow_18_timeout_plus_authoritative_readback` (test/conformance effect target) |
| 19 | `test_flow_19_ambiguous_non_reexecution`, same and new Candidate dispatch count remains one |
| 20 | `test_flow_20_completed_implementation_occurrence`, implementation action once then fresh readback-only verification |
| 21 | `test_flow_21_cleanup_final_disposition`, final absence and cleanup-timeout duplicate suppression |
| 22 | `test_flow_22_contradiction_drift_containment`, post-action drift, cleanup and no current positive result |
| 23 | `test_flow_23_failed_result_to_new_candidate` |
| 24 | `test_flow_24_authority_delta_stop` |

## Fault Boundary Coverage

Command:

```text
python3 -m unittest -v tests.test_phase7_fault_boundaries.Phase7FaultBoundaryTests.test_fault_01_concurrent_work_has_one_external_owner tests.test_phase7_fault_boundaries.Phase7FaultBoundaryTests.test_fault_02_overlapping_mutation_domain_has_one_winner tests.test_phase7_fault_boundaries.Phase7FaultBoundaryTests.test_fault_03_user_write_after_occupancy_recheck_stops tests.test_phase7_fault_boundaries.Phase7FaultBoundaryTests.test_fault_04_expected_state_competing_write_preserved tests.test_phase7_fault_boundaries.Phase7FaultBoundaryTests.test_fault_05_worker_may_have_run_response_loss_no_redispatch tests.test_phase7_fault_boundaries.Phase7FaultBoundaryTests.test_fault_06_source_adoption_fails_closed_before_mutation tests.test_phase7_fault_boundaries.Phase7FaultBoundaryTests.test_fault_07_atomic_publication_boundaries tests.test_phase7_fault_boundaries.Phase7FaultBoundaryTests.test_fault_08_effect_marker_dispatch_boundaries tests.test_phase7_fault_boundaries.Phase7FaultBoundaryTests.test_fault_09_live_owner_not_reclassified_by_competing_publication
```

Result: `Ran 9 tests ... OK`. The source-adoption runtime claim is superseded
by the fail-closed production adapter.

| Fault | Executable evidence |
| --- | --- |
| 1 | concurrent same-work owner, physical Worker dispatch count one and one public result |
| 2 | overlapping work mutation domain, one deterministic test-only Adapter Candidate winner; production Source Adoption is fail-closed, so the full production winner/loser sequence is not exercised |
| 3 | user write after occupancy observation/before recapture, exact user bytes preserved and `ImplementationStopped` |
| 4 | expected-state/mutation competing write, intended bytes absent and exact latest user bytes preserved |
| 5 | Worker may-have-run response loss, workspace reconciliation and physical dispatch count one |
| 6 | Source Adoption is unavailable before canonical mutation; custom Adapter is never called and source remains unchanged |
| 7 | result precommit failure exposes no partial result; the full postcommit response-loss liveness sequence is not established by this fault test |
| 8 | marker-before-dispatch and ambiguous recovery, action count one |
| 9 | live Runner owner remains live while competitor waits; one result identity and no competing publication |

## Legacy Independence

Command:

```text
python3 -m unittest -v tests.test_phase7_legacy_negative.Phase7LegacyNegativeTests.test_legacy_unavailable_production_fail_closed_flow
```

Result: `Ran 1 test ... OK`.

The environment blocks imports of `implementation_result`, `verification_run`, `workflow_store`, and
`baseline_capsule`; creates valid-looking poisoned result files below the actual
`IMPLEMENTATION_WORKFLOW_STORE`, `IMPLEMENTATION_RESULT_STORE`, and `BASELINE_CAPSULE_STORE` roots; marks all
three roots mode `000`; and installs a direct root-read sentinel. The Module-owned review/check Adapter closes a
zero-mutation production Candidate, and `inspect` recovers that exact Candidate without any legacy read. This is
not a successful mutation-bearing `implement -> verify -> inspect` proof because production Source Adoption remains
unsupported. Legacy sentinel calls are `0`; caller ceremony values are `0`.

## Complete Verification

```text
cd implementation-verification && python3 run_tests.py
```

Result: `Ran 121 tests ... OK`.

Breakdown: 71 existing Phase 1-6 component tests, 16 production physical conformance tests, 24 Phase 7 public
flows, 9 fault-boundary flows, and 1 legacy-negative flow. No tests were skipped. The deterministic public flows
are retained behavior evidence only; production mutation remains blocked.

```text
cd implementation-verification && python3 production_smoke.py
```

Prior smoke readback is invalidated. Current smoke verifies production fail-closed behavior:

```json
{"canonicalSource":"baseline","reason":"conditional source adoption is unavailable","status":"IMPLEMENTATION_STOPPED"}
```

```text
git diff --check
```

Result: success with no output.

```text
python3 -m py_compile *.py tests/*.py
```

Result: success with no output.
