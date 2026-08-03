# Freeze 22 implementation evidence

Authoritative design: `/tmp/opencode/implementation-verification-lead-final-design-20260802.md`

This register is the implementation/verification closure checklist for the design's section 33.
`[x]` means that the condition has a concrete fail-closed mechanism and direct executable evidence;
documentation-only assertions are not sufficient.

## Freeze checklist

| # | Status | Frozen condition | Enforcing implementation | Direct evidence |
| ---: | :---: | --- | --- | --- |
| 1 | [x] | Caller-authored outcome alone cannot publish a result. | `VerificationService.publish_result` accepts exact semantic assessments only, reads the sealed run and complete owner ledger itself, and rejects conclusive verdicts without obligations. | `test_forged_satisfied_assessment_without_execution_is_rejected` |
| 2 | [x] | Failed, missed, timed-out, interrupted, and polling attempts cannot be omitted or silently treated as conclusive. | Runner appends each attempt; result closure fills every unstarted/started-without-record step, and publisher computes unresolved uncertainty by step role. READBACK needs an exact exited observation, CLEANUP errors remain incomplete, and an ambiguous ACTION needs a later sealed readback. | `test_action_timeout_without_later_readback_is_incomplete`, `test_action_timeout_can_be_satisfied_by_sealed_authoritative_readback`, `test_cleanup_tool_error_is_incomplete`, `test_cleanup_timeout_is_incomplete`, `test_retain_terminal_readback_timeout_is_incomplete`, `test_retain_terminal_readback_tool_error_is_incomplete` |
| 3 | [x] | AC-to-obligation mapping cannot change after execution. | Exact bidirectional mapping is normalized before the durable plan seal; execution and publication read only the stored sealed plan digest. | `test_invalid_bidirectional_mapping_releases_only_unstarted_claim`, `test_post_hoc_or_disconnected_mapping_cannot_supply_missing_required_flow`, `test_step_cardinality_and_sealed_request_are_not_caller_replaceable` |
| 4 | [x] | Separate component successes cannot be composed after the fact. | Every exact criterion requires every presealed mapped flow/review; unmapped or unexecuted required flows remain incomplete. | `test_post_hoc_or_disconnected_mapping_cannot_supply_missing_required_flow`, pilot `test_disconnected_flow_negative` |
| 5 | [x] | Executor cannot run an operation other than the sealed request. | PROCESS v2 request includes executor/environment policy in its digest, starts from an empty child environment plus exact sealed delta, and executes by `(runRef, flowId, stepId)` with no replacement request or shell. Ambient-overlay plans are retired rather than reinterpreted. | `test_step_cardinality_and_sealed_request_are_not_caller_replaceable`, `test_process_execution_ignores_environment_added_after_seal`, `test_legacy_ambient_environment_plan_cannot_execute_under_process_v2` |
| 6 | [x] | ACTION and CLEANUP execute at most once per run. | Durable `verification_step_executions` primary key is inserted before subprocess start; every second call fails `STEP_CARDINALITY_EXCEEDED`. | `test_step_cardinality_and_sealed_request_are_not_caller_replaceable`, `test_retain_without_executed_terminal_readback_cannot_be_verified` |
| 7 | [x] | A real direct-result flow reaches `VERIFIED`. | Fixed PROCESS runner captures the actual stdout artifact and publisher derives `VERIFIED` from complete exact evidence. | `test_direct_result_process_is_verified_and_artifact_is_runner_owned`, pilot `test_direct_result_positive` |
| 8 | [x] | A real delayed readback reaches `VERIFIED` through bounded identical polling. | READBACK seals `1..10` attempts and one request digest; every miss/error is retained, while a later exact-source exited poll may resolve an earlier timeout. | `test_readback_polling_preserves_every_attempt_and_one_request_digest`, `test_readback_timeout_can_be_resolved_by_later_identical_poll`, pilot `test_delayed_readback_positive` |
| 9 | [x] | RETAIN requires a conclusive terminal readback after cleanup. | Publisher requires the final sealed/executed step of every RETAIN flow to be READBACK, later than all CLEANUP steps, and to contain at least one exact-source exited artifact. | `test_retain_without_executed_terminal_readback_cannot_be_verified`, `test_retain_terminal_readback_timeout_is_incomplete`, `test_retain_terminal_readback_tool_error_is_incomplete` |
| 10 | [x] | Source start mismatch and execution/publication drift fail closed. | Physical source identity is captured at preflight, before/after every attempt, and before publication; no new identity is auto-adopted. | `test_start_identity_mismatch_publishes_preflight_incomplete_with_zero_actions`, `test_identity_drift_stops_execution_and_forbids_verified` |
| 11 | [x] | Every new v3 publication is blocked. | Handoff publisher checks `implementation-result-v3` before request-shape validation and returns `PROTOCOL_RETIRED`; historical reads have no adapter. | `test_all_new_v3_publications_are_retired_before_shape_validation`, `test_historical_v3_is_read_only_and_never_adapted`, pilot `test_caller_authored_runtime_v3_cannot_be_published` |
| 12 | [x] | Coordinator, Assessor, Remediator, and Worker capabilities cannot cross role or actor boundaries. | Tokens are stored only by digest and checked against role, invocation, exact claim/transaction/selected Worker, and raw artifacts require the exact run-owning Assessor actor rather than any Assessor in the invocation. | `test_role_capabilities_cannot_cross_claim_or_publication_boundaries`, `test_role_capabilities_are_not_interchangeable`, `test_only_the_exact_owning_assessor_can_read_raw_artifacts`, `test_capture_requires_selected_worker_dispatch_and_dispatch_is_single_use` |
| 13 | [x] | Product remediation cannot begin before immutable failure publication. | `open_remediation` accepts only the exact current `VERIFICATION_FAILED` node; draft contradiction and noncurrent refs have no mutation authority. | `test_remediation_cannot_open_before_failed_result_is_published` |
| 14 | [x] | Only admitted remediation under selected-Worker ownership controls may mutate. | Fresh Remediator admission predicates, contradicted criterion subset, exclusive claim, frozen path envelope, selected Worker capability, snapshots, and reconciliation are mandatory. | `test_remediation_requires_admission_and_non_empty_delta`, `test_remediation_delta_is_bound_to_failed_source_and_selected_worker`, pilot `test_authority_delta_negative` |
| 15 | [x] | Every successful remediation continuation has a non-empty authorized delta, new non-ancestor identity, and atomic successor handoff. | Preparation distinguishes retained Worker-attributable paths from preserved external paths; external-only/no-delta and ancestor identity fail while publication atomically closes transaction/claim/budget and adds one edge. | `test_external_only_delta_cannot_satisfy_remediation_progress`, `test_remediation_cannot_reuse_an_ancestor_source_identity`, `test_remediation_handoff_closes_transaction_and_advances_failed_tip_atomically`, pilot `test_in_ticket_remediation_positive` |
| 16 | [x] | Fresh Assessor reseals every exact AC; old evidence cannot carry forward. | Every successor verification issues a new Assessor and run, validates the new handoff source, creates a new full mapping/ledger, and cannot read an ancestor run's raw artifact with its new capability. | `test_failure_publication_remediation_handoff_and_fresh_full_ac_verification`, `test_only_the_exact_owning_assessor_can_read_raw_artifacts` |
| 17 | [x] | Exclusive current-tip claim exists before effect/Worker dispatch and survives partial work. | Store has one active claim per root/tip; a run or transaction with durable facts cannot use unstarted release; unsafe/unreconciled remediation retains the claim. | `test_claim_blocks_competing_execution_before_publication`, `test_concurrent_claim_race_has_exactly_one_winner`, `test_invalid_bidirectional_mapping_releases_only_unstarted_claim`, `test_retained_delta_or_unreconciled_envelope_keeps_remediation_claim` |
| 18 | [x] | Continuation is atomic, immutable, linear, and has one derived current tip. | SQLite owner transaction publishes node, unique edge, claim/budget closure, and run/transaction closure together; immutable triggers and unique indexes reject mutation/forks. | `test_owner_only_store_and_immutable_initial_node_round_trip`, `test_matching_claim_atomically_publishes_one_successor_and_advances_tip`, `test_concurrent_claim_race_has_exactly_one_winner` |
| 19 | [x] | Fresh authority-delta admission separates in-Ticket repair from replanning. | Exact boolean admission predicates plus authority-delta digest and contradicted-criterion subset reject changed AC/scope/material decisions without changing the failed tip. | `test_remediation_requires_admission_and_non_empty_delta`, pilot `test_authority_delta_negative` |
| 20 | [x] | Ancestor identity always fails; exact repeat stops only on `MATCH`; `UNAVAILABLE` creates no classifier. | Lineage source lookup rejects ancestor identity before preparation and again at atomic publication; structured three-valued comparator gates only exact `MATCH`. | `test_remediation_cannot_reuse_an_ancestor_source_identity`, `test_exact_structured_repeat_stops_second_automatic_remediation_only_on_match`, `test_remediation_requires_admission_and_non_empty_delta` (`UNAVAILABLE`) |
| 21 | [x] | Every outer invocation has finite elapsed/resource budget and reserved closure; exhaustion cannot rewrite public status/planning. | Positive deadline and complete finite vector are mandatory; new transaction/Worker/ACTION spend checks deadline; claim-bound idempotent closure remains usable and tip is unchanged on exhaustion. | `test_budget_exhaustion_blocks_new_units_without_changing_public_tip`, `test_publication_requires_reserved_closure_work`, `test_remediation_worker_dispatch_consumes_reserved_worker_call_budget`, `test_result_publication_retry_preserves_assessments_and_closure_budget` |
| 22 | [x] | Ambiguous prior effects cannot replay across runs without mechanical safety. | Preflight scans every same-handoff ancestor ACTION/CLEANUP attempt and requires exact-idempotency or unique-correlation authorization before another effectful request; absent authority publishes `BLOCKED`. | `test_ambiguous_cross_run_effect_is_blocked_until_exact_idempotency_authority` |

## Delivery checklist

- [x] `implementation-result-v3` new-publication retirement and byte-preserving historical read.
- [x] `implementation-handoff-v1` transaction-derived initial/remediation publisher.
- [x] Owner-only schema v7, v6 migration, actors, capabilities, budgets, claims, immutable nodes/edges, and exact-once step guards.
- [x] Durable `INITIAL_IMPLEMENTATION` and `VERIFICATION_REMEDIATION` ownership transactions.
- [x] Handoff-only Implementation Lead instructions and provisional UI/Windows/greenfield routing.
- [x] Verification Lead package, preflight, sealed plan, PROCESS v2 closed-environment runner, role-aware uncertainty, exact-owner raw artifacts, redacted argv projection, complete ledger, and four-status result publisher.
- [x] Publication-before-remediation, authority-delta admission, safe no-successor closure, exact-repeat guard, and fresh full-AC cycle.
- [x] Five process-level verification pilots: direct positive, disconnected negative, delayed readback positive, in-Ticket remediation positive, authority-delta negative.
- [x] Static contract checks, unit/behavior suites, process pilots, Python compilation, Ruff, Mypy, and diff whitespace checks.

## Verification record

Verified at `2026-08-03T08:55:00+09:00`.

```text
git diff --check
python3 -m compileall -q implementation-lead verification-lead matt/skills/to-tickets
ruff check implementation-lead verification-lead --exclude __pycache__
mypy --ignore-missing-imports <four production modules>
python3 implementation-lead/run_tests.py
```

Result: **128 tests passed** across contract, ownership, owner-store, implementation transaction,
handoff publication, planning-workspace, implementation pilot, verification behavior, and PROCESS
pilot suites. Ruff and Mypy reported no issues; compilation and whitespace validation passed.
