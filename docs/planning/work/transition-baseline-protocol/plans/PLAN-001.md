# PLAN-001 — Transition Baseline and Autonomous Continuation Protocol Integration

## 1. Binding and approved outcome

- Project Root: `/home/user01/project/iis-skills`
- Exact Ticket: `docs/planning/work/transition-baseline-protocol/tickets/TICKET-001.md` — `Status: ready`; all five ACs and its one independent Verification flow are in scope.
- Parent Spec: `docs/planning/work/transition-baseline-protocol/SPEC.md` — approved, Requirements 1–5 and Implementation Constraints.
- Scope authority: `docs/planning/scope-shaping/transition-baseline-autonomous-continuation/revisions/SHAPE-001.md` — confirmed; Planning Constraints and INC-001 boundary.
- Behavior authority: `docs/planning/behavior/contexts/transition-protocol.md`, complete Scope/Intent. UI authority: none (`UI: no`).
- Common plans: none. This document is execution method, not ADMIT, implementation permission, or a product verification verdict.

The deliverable is a canonical documentation protocol: explicitly approved Transition Baseline → exactly one Active Block Envelope → fresh Scope selection and ordinary delivery → actual Block Exit assessment → caller/host successor invocation → final transformation authoritative readback. It is not a running scheduler or a demonstration of real infrastructure migration. The Ticket's acceptance boundary is direct canonical file inspection and existing tests.

Only four product paths may change: the new `iis-adaptive-planning/templates/BASELINE-NNN.template.md`, `iis-adaptive-planning/SKILL.md`, `iis-adaptive-planning/references/09-run-contract.md`, and `scope-shaper/SKILL.md`. No external DB, persistent controller, dashboard, agent registry, seven-state Block verdict system, prescribed rollback SQL, checker/schema changes, or installed-skill synchronization is included. Ticket/Spec/Behavior/Scope authority and historical artifacts stay unchanged.

## 2. Code Grounding and controlling entry path

All relative primary-source paths below are rooted at Project Root. Existing observations were made on 2026-09-11 against the working-tree files, not inferred from Git HEAD. Recheck materially changed anchors before relying on them.

### EXISTING

| Claim | Primary definition and consumer | Successful observation and consequence |
| --- | --- | --- |
| Adaptive is explicit opt-in; Outer Main owns invocation closure and completion, leaves own planning/delivery | `iis-adaptive-planning/SKILL.md:23–41,59–72,100–137,247–275` | Direct inspection establishes the current entry and decision path. Transition intake must run after explicit activation and before product-meaning/Run closure, not activate from an old file. |
| Current completion forbids stopping an actionable unfinished invocation | `references/09-run-contract.md:247–268,328–350`; `SKILL.md:260–267` | Goal coverage and same-invocation continuation are explicit. Merely adding a new disposition would contradict these rules; an opt-in, non-success exception must govern both places. |
| There are additional consumers of the same continuation premise | `references/08-delivery-continuation.md:225–280`; `references/07-terminal-report.md:163–183` | Direct read/search finds the existing four dispositions and same-invocation instruction. These are not absent or assumed compatible. The in-scope Skill/09 changes must explicitly state precedence of the narrowly gated transition exception over those ordinary continuation/reporting paths, while preserving them for every other case. |
| Run Contract remains ephemeral; companion provenance already has a location and owner | `SKILL.md:277–288`; `references/05-artifact-contract.md:29–78`; `references/09-run-contract.md:302–350` | Existing artifact rules separate Mandate/Trace from invocation-local contracts. Baseline is an optional approved design artifact, not a saved Run Contract, cursor, completion ledger, or a new required companion for ordinary work. |
| Scope owns exactly one durable current Increment, preserves constraints, and has an atomic exception and re-entry field | `scope-shaper/SKILL.md:275–277,309–358,374–418` | Direct inspection establishes insertion points and downstream canonical fields. Path invariants can inhabit existing Planning Constraints, Preserved Foundations and Re-entry Contract without new schema metadata. Immutable SHAPE history and fresh selection remain intact. |
| Checker tests structure, not transition safety or Goal fidelity | `iis-adaptive-planning/tools/check_run_contract.py:13–42,366–394`; `templates/ADAPTIVE-RUN-CONTRACT.template.md:52–91`; `tests/test_adaptive_run_contract_check.py:23–103,298–335` | Actual CLI invocation with the existing fixture returned exit 0/`STRUCTURE_VALID`; changing only its boundary to delivered with verification disabled returned exit 1/`STRUCTURE_INVALID`. SAFE_INCOMPLETE_HANDOFF therefore belongs to completion routing, never Status or Run Completion Boundary. Existing schema stays unchanged. |
| Target authority is current ready authority; template is genuinely new | Full Ticket/Spec/Behavior/SHAPE inspection; `iis-adaptive-planning/templates/` directory listing | Directory contained only Mandate, Trace and Run Contract templates, not BASELINE. Exact canonical Ticket validation returned `VALID`; read-only `ready_contract inspect_authority` captured ready status and the linked Spec/Behavior. |

Authority capture: Ticket SHA-256 `afd103cb98b94a9e6ae8d121e636e8a9b07b4acb06ec831c951dea6d183b665f`; authority digest `657f44577b4c56fd54d3a6e614f4edefec8ee3a5aef8c124046c01bac685fc78`; pinned bundle `44687d63fead6e4d2389753f837d0f2dffb73ad927a51078ff1c921910627e93`. These observations are navigation for the independent reviewer, not a reusable approval.

The highest-rework premise is how an invocation can stop at a Block boundary without narrowing the assigned transformation Goal. A contrary design would make existing coverage checks meaningless and misreport Block success as full success. Resolve this by preserving the whole delegated Goal and its sufficient Predicate while bounding current construction to the projected Block; a Block Exit permits only an explicitly incomplete handoff. Do not fix this by making the Goal equal to the Block or by introducing a new completion-boundary enum.

### PROPOSED

The following are new designs, not existing implementation facts:

1. An optional approved Baseline artifact identifies overall transformation outcome/readback, immutable path constraints, coarse Blocks and safety predicates. It is supplied by exact path/revision under explicit opt-in; existing presence is not activation.
2. Outer Main projects a compact envelope for one current Block. Scope receives that envelope and applicable source anchors, not the entire map or future Increment details. Coarse Block order constrains authorized transition geography; it is not a preapproved queue of INC/WP/Ticket work.
3. `SAFE_INCOMPLETE_HANDOFF` is a fifth completion-assessment routing disposition, not a seventh-plane Block evaluation system, success label, Ticket verdict, Run status or boundary value. It is an exception to staying in the same invocation, not an exception to truthful completion.
4. Caller/host starts the next explicit authorized invocation from the approved Baseline, current Mandate/source authority and fresh actual state. The successor closes a fresh Run Contract and reprojects one Block. It never resumes a serialized old Run Contract.

Each design is expanded into owned changes and discriminating checks below.

### UNRESOLVED

No cheap repository premise required to write this method remains unresolved. Actual future host transport availability, concrete migration readback and Safe Abort mechanisms depend on the eventual project using this protocol; no running controller or production environment exists in this Ticket's acceptance boundary. This plan does not claim them tested. The protocol must assign those responsibilities and forbid claiming a successor started or an abort completed without actual evidence. A runtime implementation obligation discovered beyond canonical documentation returns to the original Spec/Ticket owner, not a guessed implementation here.

## 3. State, ownership, interfaces and invariants

| State/interface | Key, lifetime and writer | Reader, transition and preservation |
| --- | --- | --- |
| Approved Transition Baseline | Exact project/path plus revision; durable approved map. User approves initial adoption and material changes; Outer Main may prepare it, not silently weaken it. | Outer Main reads applicable slices and source anchors. Progress does not update a cursor in it. Fresh evidence invalidating the map returns to its planning/approval owner. |
| Overall Goal and constraints | Current user delegation and applicable Mandate/approved Baseline; survive individual invocation termination. | Every envelope and newly closed contract preserves relevant obligations and the final readback boundary. An incomplete return never erases remaining work or promotes candidates to required items. |
| Active Block Envelope | Baseline identity + one Block identity; invocation-local projection owned by Outer Main. Created at intake, recomputed at Block transition or material current-state change. | Scope Shaper reads local objective, applicable global/path invariants, verified entry facts, exit/readback, safe continuation/abort conditions and remaining-goal reference. Clear the previous active projection before presenting the next; no two active Block scopes. |
| Run Contract | Current invocation; Outer Main closes and carries it using existing fields. Ends with that invocation; no durable resume record. | Planning and delivery receive only their existing decision-critical fields. Success uses unchanged Goal fidelity; a safe incomplete terminal retains remaining obligations and gives the caller a successor action. |
| Scope/Increment artifacts | Existing immutable SHAPE revision and exact selected INC; Scope owns writes and fresh-state re-entry. | Matt/Spec/Ticket preserve path constraints through existing fields. Exactly one current ready-for-matt Increment. HARD_ATOMIC cannot be divided across independently accepted Increments. |
| Delivery and actual readbacks | Existing implementation/verifier owners; exact stable Ticket target and authoritative evidence. | Outer Main consumes results without issuing another AC verdict. All active effect-owning work must be settled or safely contained before an inter-invocation handoff. No duplicate replay following uncertain external effects. |
| Successor invocation transport | Existing caller/host, not the departing planning leaf or a newly implemented daemon. | Baseline approval includes inter-Block continuation authority within its ceiling. Only actual host invocation evidence supports “started”; unavailable transport is an incomplete capability limit, never success or simulated dispatch. |

Preserve explicit stage stops, `/승인게이트` direct release semantics, current selected execution modes/models, external-effect permissions and no-material-progress rules. Baseline approval is not blanket deployment/destructive-action permission. A successor reapplies the existing invocation-local gate rule; it does not persist an old gate or bypass a newly explicit gate. Ordinary non-transition Adaptive and Baseline IIS remain behaviorally unchanged.

## 4. Concrete implementation steps

### 4.1 Add the Baseline template — AC1

Create `iis-adaptive-planning/templates/BASELINE-NNN.template.md` as a lightweight Markdown design template, following the existing heading/field style rather than creating a parser. Proposed sections:

- Identity and approval: exact Project Root, Baseline identifier/revision, explicit source/approval reference and applicability. Explain that an unapproved template is not activation.
- Transformation Outcome: full Goal, final authoritative readback and completion predicate; required/candidate meaning remains sourced from current authority.
- Global / Path Invariants: constraints that must hold throughout the transition, not only at the endpoint.
- Transition Blocks: repeatable coarse Block entry with identity, intended outcome, dependencies/order constraints, measured Entry Predicate, measured Exit Predicate and readback owner/source. Do not enumerate future ready Increments or implementation tasks.
- Safe Continuation: observable predicate allowing a safe boundary handoff, required carried facts/obligations and successor authority. Absence of danger by assumption is not evidence.
- Safe Abort: triggering condition, authorized safe target state, responsible owner/action boundary and readback proving that state. Keep mechanism project-specific; do not require rollback SQL or promise rollback where unavailable.
- Atomic Boundary: when a Block contains HARD_ATOMIC, its indivisible transition lives within one Increment; internal execution units do not become separate Scope Increments or permit a handoff mid-cutover.

Use existing recommended adaptive provenance location only as a placement suggestion for instantiated `BASELINE-NNN.md`; require the caller's exact supplied identity, not latest-file discovery. The template has no runtime status log, retry ledger or mandatory workflow store.

### 4.2 Integrate intake and completion in Adaptive Skill — AC2

Add a Transition Baseline intake/Active Block Envelope section after Activation and before Run closure. It must:

1. Require explicit Transition Baseline opt-in and one-time approved applicability, including authorized inter-Block auto-continuation. Reconcile the approved map with current Mandate, newer user instructions and actual entry state.
2. Keep the full map out of working planning context: Outer Main locates the current Block from approved source identity and measured state, reads only relevant sections, and projects one envelope. Whole-Goal summary/source anchors plus applicable invariants are retained so context slicing cannot hide an obligation.
3. Enumerate the envelope fields from section 3 and direct Scope to choose one current durable Increment inside the Block; several safe Increments may be needed inside a Block, except HARD_ATOMIC.
4. Keep existing Run fields and coverage invariant. A local Block exit is not permission to weaken full Goal/Predicate or declare `IIS ADAPTIVE RUN COMPLETE`.
5. Add `SAFE_INCOMPLETE_HANDOFF` to Post-delivery completion assessment, guarded by approved transition mode, measured Block Exit and Safe Continuation, settled/contained active work, known remaining obligations and exact successor authority/input. State explicitly that the same-invocation rule here and ordinary `07-terminal-report.md` / `08-delivery-continuation.md` routing are subject only to this narrow exception defined in 09.
6. On a satisfied final transformation predicate use existing `RUN_CONTRACT_SATISFIED`; when Block Exit is not satisfied, continue ordinary corrective/current-Block routing. Missing evidence stays `EVIDENCE_REQUIRED`; material user-owned conflicts stay `USER_DECISION_REQUIRED`. Failure crossing a Safe Abort trigger uses the approved safe-state owner/readback, never a new success disposition.
7. In Artifacts, permit the optional approved Baseline separately from the existing minimal companion provenance and reiterate no durable Run state. Make Terminal boundary distinguish an incomplete caller handoff from planning-phase STOP and Run success.

Do not restyle unrelated sections or move delivery ownership into IIS Planning.

### 4.3 Define the exception and successor reconstruction — AC3

In `references/09-run-contract.md`, update Completion discipline and adjacent Carry-forward/Persistence language only as needed for one coherent rule:

- Retain the unconditional prohibition on whole-run success with unmet Goal. Add SAFE_INCOMPLETE_HANDOFF to incomplete returns.
- Scope the exception to the opt-in approved Baseline case. A valid next action normally remains in the invocation; only measured safe Block-boundary transfer may terminate it incomplete.
- Preserve the overall Goal, Required Named Items, final readback and remaining obligations in upper delegation. Bound current construction to one Block without treating a Block-specific Predicate as whole transformation coverage.
- Define minimal handoff content: exact Baseline/Mandate/source identities, departing Block, actual exit/safety readbacks and limits, remaining Goal obligations, next entry inspection, and caller/host successor action. Use an ordinary terminal handoff and existing material provenance when needed, not a new persistent handoff DB/artifact schema.
- Caller/host autonomously starts the successor under the already-approved continuation authority. Successor re-reads current authority and actual state, resolves the next eligible Block, reprojects one envelope, closes fresh existing-form fields, checks structural consistency and current stage/model/gate applicability, then enters Scope. Do not copy stale statuses or old Run Contract bytes as active authority.
- Unknown/failed handoff safety forbids this disposition; continue authorized evidence/repair, or execute only approved Safe Abort and prove its result. If authority/capability is missing, preserve the actual incomplete limit and required next owner. Do not claim autonomous start from a suggested command.
- Explicitly link this exceptional route from the Skill so ordinary 07/08 report/continuation instructions cannot force false RUN COMPLETE or contradict the safe incomplete terminal. Do not modify those out-of-scope files under this plan. If a reviewer finds the scoped precedence rule insufficient, return the affected method for review and obtain scope authority before editing additional consumers.

No new checker enum, Run field, admission state, scheduler or approval ledger is required.

### 4.4 Carry transition invariants through Scope — AC4

Under `scope-shaper/SKILL.md` Planning Constraints, require applicable approved transition path invariants to carry into each selected Increment's existing constraints/Preserved Foundations and downstream planning. Re-establish them on each re-entry; a different construction order must not silently discard compatibility, authority, safety or atomic boundaries. Preserve only applicable constraints, not the whole future map.

Under Atomic Exception, state HARD_ATOMIC is one Increment with internal execution units only; if the proposed smaller boundary lacks a safe durable readable state, reject the split using the existing exception.

Expand the existing Re-entry Contract paragraph to require the Safe Continuation Predicate, actual state/readback and owner needed before another Increment/Block, plus the approved Safe Abort boundary when continuation cannot be established. This is a planning constraint consumed under current Adaptive authority, not automatic future Increment approval. Ordinary Scope user confirmation, immutable revisions, one selected Increment and the final ordinary Scope STOP remain intact.

## 5. Implementation self-check and verifier handoff — AC1–AC5

The implementation owner first passes current independent plan admission; preparation itself performs no source mutation. After the four-file coherent change, inspect the actual resulting canonical text through the following semantic traces before relying on tests:

| Trace / failure being discriminated | Minimum actual acceptance readback |
| --- | --- |
| Ordinary request or old Baseline file accidentally activates transition mode | Read Activation/intake and confirm no automatic creation/activation, no altered ordinary Scope confirmation or same-invocation continuation. |
| Projection loses Goal/path constraints or expands future work | Read template → Skill envelope → Scope Planning Constraints/Re-entry chain; exactly one Block, whole-goal source/remaining obligations retained, future INC/WP not preapproved. |
| Delivered Tickets falsely close a Block/whole transformation | Trace current completion paragraph → 09 exception with measured exit false, safe predicate false and final Goal false separately. None may yield whole-run success. Existing acceptance owners/readback remain necessary. |
| Successful Block with remaining Goal has no legal successor path | Read guarded incomplete terminal, exact minimal handoff, host ownership and fresh successor closure end-to-end. Confirm no human approval is newly required per Block inside prior authority, no saved Run Contract and no generic 07/08 rule overrides the explicit exception. |
| Interrupted or unsafe transition is labeled safe, or external work gets replayed | Trace pending effect/unknown readback and Safe Abort trigger. Safe handoff requires settled/contained state and proven predicate; only authorized safe-state recovery may run, and unavailable evidence stays incomplete. |
| HARD_ATOMIC split or premature handoff | Read template and Scope Atomic Exception/Re-entry together; two separately accepted Increments and mid-cutover incomplete handoff are prohibited. |
| Valid final transformation is prevented or overstated | Final authoritative readback true uses existing RUN_CONTRACT_SATISFIED; a stage-only/no-verification result cannot claim delivered transformation. |

These are document acceptance inspections, not a claim that a host or production migration has been executed. Use a temporary worked Baseline/envelope/successor contract if needed to expose contradictions; keep it outside product authority, label it a design exercise, and remove it after checks.

Then run the actual checker CLI against fully rendered temporary contracts, never against the unfilled template:

```text
python3 iis-adaptive-planning/tools/check_run_contract.py --file <absolute-rendered-current-contract>
python3 iis-adaptive-planning/tools/check_run_contract.py --file <absolute-rendered-successor-contract>
```

Expect exit 0 and exact `STRUCTURE_VALID` for each valid existing-form contract; use existing supported enum values and selected enabled-stage model rows. Keep SAFE_INCOMPLETE_HANDOFF in routing prose, not the Boundary field. A negative delivered/no-verification contract must return exit 1/`STRUCTURE_INVALID`. Reuse the existing `contract()` fixture shape in `tests/test_adaptive_run_contract_check.py:23–103` only for structure checks; fixture success does not prove Goal fidelity or safe handoff.

For AC5, after all edits settle, the coordinating Main runs once from Project Root:

```text
python3 -m pytest tests/
```

All collected existing tests must pass with no failures; do not substitute an assumed test count or just checker tests. This Planner does not run the project-wide suite during concurrent preparation. A failure is investigated as a concrete regression or pre-existing environmental/contract issue; do not weaken ACs or alter out-of-scope tests/checker just to get green. A required additional product-file/test change returns for scope/method review. Do not add tests pinning prose strings or new parser machinery for this documentation-only protocol.

The final independent verifier receives the exact current ready Ticket, its current parents and stable four-file implementation target, direct file readback, real pytest and checker results with current environment/limits. Any implementation edits after those observations invalidate affected evidence. The separate verifier owns all five ACs and the authored Verification flow; this plan and self-check cannot set Ticket done or issue PASS. Local temporary examples are settled/removed by their creator; no service, credential or external deployment environment is needed for this Ticket.

## 6. Conditional first work and revision triggers

No unresolved implementation-time premise currently requires a conditional ADMIT bundle; conditions may be empty. The first coherent implementation move is to define the bounded non-success handoff and successor semantics in 09 together with their Skill entry/assessment linkage, then derive the Baseline template and Scope carry-forward text from that interface. Do not first write an isolated template whose fields imply incompatible completion semantics.

Permitted local discretion: exact heading names, field wording, example choice and insertion placement that preserve the approved meanings, four-file ownership and existing schema. No runtime controller, new durable progress state or additional approval requirements may be introduced as local detail.

Return affected work to this Planner, Heuristic and independent Plan Review when new source bytes change any load-bearing premise; the envelope/Goal relationship changes; a fifth routing disposition becomes a new Run boundary or success meaning; host ownership, interruption safety, authoritative readback or persistence changes; a concrete counterexample defeats the scoped 07/08 precedence rule; or the required checks cannot establish the same acceptance boundary. Stop dependent mutation until revised method and review are current. Safe unrelated inspection may continue.

Return product-meaning changes, any widening beyond the four scoped product paths, weakening of global/path invariants, or loss of unattended continuation back to the original Scope/Matt/Spec/Ticket authority via Main. Do not silently reduce the deliverable or claim an unsupported host capability. On REVISE, reopen implicated definitions and consumers, bound the same-assumption span, revise the method, recheck the original and repair-induced counterpaths, and obtain affected independent review; new plan bytes alone are not approval.
