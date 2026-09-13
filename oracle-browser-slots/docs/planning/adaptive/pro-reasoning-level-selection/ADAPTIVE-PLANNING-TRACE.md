# Adaptive Planning Trace

Project-Root: /home/user01/project/oracle/oracle-browser-slots
Mandate: docs/planning/adaptive/pro-reasoning-level-selection/ADAPTIVE-PLANNING-MANDATE.md
Current Mandate Revision: 1

## Material Events

### 001 — Run Contract closure and delivery role selection
Provenance: USER_EXPLICIT
Authority: Mandate Revision 1; current user instruction; THESIS-003
Evidence: /home/user01/project/oracle/oracle-browser-slots/docs/planning/product-thesis/pro-reasoning-level-selection/THESIS-003.md; /home/user01/project/oracle/oracle-browser-slots/docs/investigation/pro-reasoning-level-selection/INV-003.md
Decision: 세 Pro model/version choice의 전체 bounded outcome을 Required Outcome으로 유지하고, Implementation과 Verification을 활성화한다. Ready Ticket Plan은 Outer Main이 직접 작성하고, Plan Review는 `opencodex-deepseek-v4.1-flash-max`, Implementation Worker는 `opencodex-gpt5.6-luna-max`, Final Verifier와 Coverage는 `opencodex-gpt5.6-luna-max`를 사용한다.
Reason: 사용자가 최신 Thesis를 정확히 따르는 전체 Adaptive 실행과 역할별 모델을 명시했으며, 현재 권위가 Goal, required/candidate 분류, delivery stages 및 bounded completion을 완전히 결정한다.
Affected canonical artifacts: None (Run Contract is invocation-local)
Re-entry / next leaf: Ask Matt


### 002 — Behavior authority and integrated understanding adopted
Provenance: DELEGATED_RECOMMENDATION
Authority: Mandate Revision 1; closed Run Contract; THESIS-003; existing Oracle Browser managed-slot authority
Evidence: docs/planning/behavior/contexts/pro-model-version-selection.md; docs/planning/behavior/contexts/oracle-browser-managed-slots.md; INV-003 Findings 1–7; current initial/resume selection paths
Decision: Pro choice를 exact model/version row와 별도 Power=`Pro`의 conjunction으로 정의하고, initial run 및 explicit same-origin followup에서 fresh pre-submit verification을 요구한다. Followup choice 생략은 current conversation selection을 보존하되 새 requested choice나 Pro 성공을 추정하지 않는다. 이 approved Behavior authority와 bounded rendered contract를 통합 shared understanding으로 채택한다.
Reason: 이 선택만이 Thesis의 exact-choice, dynamic Latest, evidence attribution, fail-closed 요구와 기존 slot/origin authority를 모두 만족하며, 대안들은 observable intent 위조 또는 silent fallback을 허용한다.
Affected canonical artifacts: docs/planning/behavior/contexts/pro-model-version-selection.md; docs/planning/behavior/INDEX.md
Re-entry / next leaf: To Spec

### 003 — Verification target-root correction
Provenance: VERIFIER_OWNER_TERMINAL
Authority: Mandate Revision 1; `ready-ticket-verify`; To Spec/To Tickets canonical Project-Root rules
Evidence: `ready-terminal-119501ef-97ff-46db-aff7-797d68bedc58`; `/home/user01/tmp/pro-reasoning-level-selection-verification-binding.json`; verifier rejection `verification path outside Project Root: /home/user01/project/oracle/src/browser/index.ts`
Decision: 원 verifier verdict `INCONCLUSIVE`와 `Ticket Progression: NOT APPLICABLE`을 보존한다. 제품 의미나 구현 모순이 아니라, Stock Oracle과 wrapper를 함께 소유하는 실제 repository root가 `/home/user01/project/oracle`인데 기존 Ticket이 nested wrapper 디렉터리를 Project-Root로 선언한 planning target-attribution 결함이다. 기존 nested planning history는 변경하지 않고, 동일 승인 의미를 실제 repository root의 canonical Behavior/Spec/Ticket authority로 다시 투영해 validated Ready Ticket Set을 만들었다.
Adaptive classification: INCONCLUSIVE — target-attribution authority gap; product implementation defect not established
Authority comparison: 기존 Ticket의 모든 Flow는 Parent Spec과 일치하지만 Project-Root metadata가 그 Flow가 요구하는 Stock source/deployed CLI를 binding할 수 없었다. 새 rooted Ticket은 동일한 AC/Flow/Behavior/UI 의미를 유지하며 `/home/user01/project/oracle` 전체 acceptance target을 binding할 수 있다.
Disposition: corrected To Spec/To Tickets authority under `/home/user01/project/oracle/docs/planning/`; fresh integrated verification required; implementation rerun not required because product bytes did not change.
Contract changed: authority location and Project-Root only; observable product contract no
Fresh verification required: yes
Re-entry / next leaf: ready-ticket-verify on `/home/user01/project/oracle/docs/planning/work/pro-reasoning-level-selection/tickets/TICKET-001.md`

### 004 — Exact-row readback implementation defect
Provenance: VERIFIER_OWNER_TERMINAL
Authority: corrected rooted TICKET-001; current PLAN-001; `ready-ticket-verify`; Mandate Revision 1
Evidence: `ready-terminal-927b1c22-39d0-40fc-b389-676ca87085d3`; `/home/user01/tmp/oracle-TICKET-001-verification-binding-20260913.json`; fresh managed runs on slots 1, 2, 10 and same-origin followups
Decision: 원 verifier verdict `FAILED`와 `Ticket Progression: NOT APPLICABLE`을 보존한다. Wrapper의 request-derived `select`와 canonical `dist/` 갱신은 확인됐지만, Stock select-mode checked-row reader가 실제 rendered single checked row를 `unavailable`로 반환해 세 positive path가 모두 pre-submit 실패했다. 별도 current-strategy Stock path는 selectedRow=null/verified=false 상태에서도 prompt를 제출했다.
Adaptive classification: IMPLEMENTATION_DEFECT
Authority comparison: 실패 경계는 Parent Spec/Ticket의 exact-row positive gate와 mismatch no-submit 요구를 정확히 투영하며 current Increment에 적합하다. Verifier target·binding·실행·cleanup은 안정적이고 attributable하다.
Primary evidence: managed initial three-choice `promptSubmitted=false` with checked-row unavailable; direct rendered rows present; controlled current-strategy mismatch `promptSubmitted=true` with unverified row; explicit followups fail at the same reader.
Disposition: current reviewed PLAN-001의 Stock exact-row reader/submission gate에 대한 implementation-local correction 후 COMPLETE handoff와 fresh integrated verification
Contract changed: no
Fresh verification required: yes