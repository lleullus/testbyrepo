from __future__ import annotations

import re
import unittest
from pathlib import Path


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]
SKILL = (IMPLEMENTATION_ROOT / "SKILL.md").read_text(encoding="utf-8")
FAILURE_ROUTING = (IMPLEMENTATION_ROOT / "references/implementation-failure-routing.md").read_text(
    encoding="utf-8"
)
TASK_OWNERSHIP = (IMPLEMENTATION_ROOT / "references/task-ownership.md").read_text(encoding="utf-8")
PLANNING_CURRENTNESS = (
    IMPLEMENTATION_ROOT / "references/planning-input-currentness.md"
).read_text(encoding="utf-8")
PLANNING_TICKET = (IMPLEMENTATION_ROOT / "references/planning-ticket.md").read_text(encoding="utf-8")
UI_TICKET = (IMPLEMENTATION_ROOT / "references/ui-ticket.md").read_text(encoding="utf-8")
COMPLETION_RECORD = (IMPLEMENTATION_ROOT / "references/completion-record-v3.md").read_text(encoding="utf-8")
TO_TICKETS = (IMPLEMENTATION_ROOT.parent / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8")
MATT_SKILLS = [
    (IMPLEMENTATION_ROOT.parent / f"matt/skills/{name}/SKILL.md").read_text(encoding="utf-8")
    for name in ("setup-matt-pocock-skills", "to-spec", "to-tickets", "wayfinder", "handoff", "research", "prototype")
]
PROJECT_SHAPER = (
    IMPLEMENTATION_ROOT.parent / "project-shaper/skills/project-shaper/SKILL.md"
).read_text(encoding="utf-8")
PROJECT_MAP_CONTRACT = (
    IMPLEMENTATION_ROOT.parent
    / "project-shaper/skills/project-shaper/references/project-map-contract.md"
).read_text(encoding="utf-8")
MATT_HANDOFF_CONTRACT = (
    IMPLEMENTATION_ROOT.parent
    / "project-shaper/skills/project-shaper/references/matt-handoff-contract.md"
).read_text(encoding="utf-8")
FROM_PROJECT_SHAPER = (
    IMPLEMENTATION_ROOT.parent / "project-shaper/skills/from-project-shaper/SKILL.md"
).read_text(encoding="utf-8")
GREENFIELD = (IMPLEMENTATION_ROOT / "references/greenfield-implementation.md").read_text(encoding="utf-8")
ASK_MATT = (IMPLEMENTATION_ROOT.parent / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8")
GRILL_WITH_DOCS = (
    IMPLEMENTATION_ROOT.parent / "matt/skills/grill-with-docs/SKILL.md"
).read_text(encoding="utf-8")
GRILL_ME = (IMPLEMENTATION_ROOT.parent / "matt/skills/grill-me/SKILL.md").read_text(encoding="utf-8")
TO_SPEC = (IMPLEMENTATION_ROOT.parent / "matt/skills/to-spec/SKILL.md").read_text(encoding="utf-8")
BASELINE_README = (IMPLEMENTATION_ROOT.parent / "baseline-capsule/README.md").read_text(encoding="utf-8")
BASELINE_SOURCE = (IMPLEMENTATION_ROOT.parent / "baseline-capsule/baseline_capsule.py").read_text(
    encoding="utf-8"
)
PLANNING_WORKSPACE_README = (IMPLEMENTATION_ROOT.parent / "planning-workspace/README.md").read_text(
    encoding="utf-8"
)


class ImplementationSkillContractTests(unittest.TestCase):
    def test_greenfield_classification_uses_current_scope_readiness(self) -> None:
        self.assertIn("current Ticket scope lacks required target readiness", GREENFIELD)
        self.assertIn("Ticket wording such as `greenfield`, `initialize`, or `bootstrap` is not a\ntrigger", GREENFIELD)
        self.assertIn("Product-root emptiness is not a trigger", GREENFIELD)
        self.assertIn("existing monorepo may have\na scope-local initialization", GREENFIELD)
        self.assertIn("empty documentation-only root is not\nproduct initialization", GREENFIELD)
        self.assertIn("Classify current target readiness for the Ticket scope", SKILL)

    def test_greenfield_planning_interface_stays_declarative(self) -> None:
        for fact in (
            "Initialization scope authority",
            "Applicable external decisions",
            "Remaining bootstrap decision disposition",
        ):
            self.assertIn(fact, GREENFIELD)
        self.assertIn("scope in which initialization mutation is authorized", TO_SPEC)
        self.assertIn("applicable external decisions", TO_TICKETS)
        self.assertIn("remaining bootstrap choice fixed/delegated disposition", TO_TICKETS)
        self.assertIn("Do not add `Initialization:`, `Planning-Root:`, a bootstrap manifest", TO_TICKETS)
        self.assertIn("private package/module identity", TO_TICKETS)

    def test_matt_routes_and_asks_only_authorization_decisions(self) -> None:
        self.assertIn("remains codebase-backed even when", ASK_MATT)
        self.assertIn("route it to `grill-with-docs`", ASK_MATT)
        self.assertIn("Target-readiness absence is a\nrepository fact, not a user question", GRILL_WITH_DOCS)
        self.assertIn("The exact product `Project-Root` must\nexist", GRILL_ME)
        self.assertIn("do\nnot duplicate a Project Shaper-specific greenfield checklist", FROM_PROJECT_SHAPER)

    def test_initialization_mechanics_and_external_effects_remain_implementation_owned(self) -> None:
        self.assertIn("select one current initialization task", GREENFIELD)
        self.assertIn("freeze its exact\nallowed/forbidden paths", GREENFIELD)
        self.assertIn("Private toolchain, private package/module identity, dependencies", GREENFIELD)
        self.assertIn("Bootstrap delegation does not authorize network access", GREENFIELD)
        self.assertIn("Preserve every pre-existing user\nfile", GREENFIELD)
        self.assertIn("Do not globally exclude `.scratch/**`", GREENFIELD)
        self.assertIn("If current target readiness already exists, use the ordinary brownfield flow", GREENFIELD)

    def test_greenfield_admission_matrix_covers_language_neutral_branches(self) -> None:
        rows = {}
        for line in GREENFIELD.splitlines():
            if line.startswith("| `"):
                scenario, _, disposition = (cell.strip() for cell in line.strip("|").split("|"))
                rows[scenario.strip("`")] = disposition
        self.assertEqual(
            {
                "all-fixed-no-delegation": "`ADMIT_INITIALIZATION`",
                "delegated-private-choice": "`ADMIT_INITIALIZATION`",
                "missing-initialization-authority": "`BLOCKED` before Worker dispatch.",
                "unresolved-bootstrap-disposition": "`BLOCKED` before Worker dispatch.",
                "unauthorized-external-effect": "`BLOCKED` before that effect.",
                "root-not-ready": "`BLOCKED`; neither planning nor Implementation Lead creates it.",
                "brownfield-ready-scope": "`ORDINARY_FLOW`; do not apply initialization admission.",
                "documentation-only-empty-root": "`ORDINARY_FLOW`; root emptiness is not initialization.",
                "scope-local-initialization": (
                    "Apply the same initialization authority and disposition gates; "
                    "root non-emptiness does not bypass them."
                ),
            },
            rows,
        )
        self.assertIn("If every material choice is fixed, no delegation is applicable\n   or required", GREENFIELD)

    def test_external_planning_workspace_is_shared_by_active_generators(self) -> None:
        active = MATT_SKILLS + [
            PROJECT_SHAPER,
            PROJECT_MAP_CONTRACT,
            MATT_HANDOFF_CONTRACT,
            FROM_PROJECT_SHAPER,
            PLANNING_WORKSPACE_README,
        ]
        self.assertTrue(all("<project-root>/.scratch" not in text for text in active))
        self.assertTrue(all("/tmp" + "/opencode/planning" not in text for text in active))
        for text in MATT_SKILLS:
            self.assertIn("planning-workspace/planning_workspace.py", text)
        self.assertIn("~/opencode/planning/<task-owned-id>/<work-slug>/", MATT_SKILLS[0])
        self.assertIn("<planning-workspace>/SPEC.md", MATT_SKILLS[1])
        self.assertIn("<planning-workspace>/tickets/TICKET-NNN.md", TO_TICKETS)
        self.assertIn("<initiative-planning-workspace>/PROJECT-MAP.md", PROJECT_SHAPER)
        self.assertIn("<initiative-planning-workspace>/matt-briefs/WP-NNN.md", MATT_HANDOFF_CONTRACT)
        self.assertRegex(FROM_PROJECT_SHAPER, r"independent default\s+package planning workspace")
        self.assertRegex(FROM_PROJECT_SHAPER, r"do not nest the\s+package workspace.*initiative workspace")
        self.assertRegex(PLANNING_WORKSPACE_README, r"Implementation Lead uses the exact Ticket and Spec paths directly")
        self.assertRegex(PLANNING_WORKSPACE_README, r"never moved or copied into the product project")

    def test_rootless_spec_workspace_must_be_strictly_revalidated_for_ready_ticket(self) -> None:
        self.assertIn("--future-project-root", PLANNING_WORKSPACE_README)
        self.assertIn("does not create the future root", PLANNING_WORKSPACE_README)
        self.assertIn("same\n`planningWorkspace`", PLANNING_WORKSPACE_README)
        self.assertIn("strict `--project-root`", TO_TICKETS)
        self.assertIn("Ticket\ndrafting may reuse a workspace", TO_TICKETS)
        self.assertIn("Do not manually\ncreate, repair, or adopt a workspace", TO_SPEC)
        self.assertIn("Do not manually create,\nrepair, or adopt a workspace", TO_TICKETS)

    def test_external_parent_spec_preserves_exact_path_currentness(self) -> None:
        self.assertIn("may be inside or outside the product project root", PLANNING_TICKET)
        self.assertIn("Product-root containment is not a parent-Spec readiness condition", PLANNING_CURRENTNESS)
        self.assertIn("same canonical `specPath`", PLANNING_CURRENTNESS)
        self.assertIn("exact raw-byte hash equals `specSha256`", PLANNING_CURRENTNESS)
        self.assertIn("Relative blocker paths resolve from the Ticket directory", PLANNING_TICKET)
        self.assertIn("approved document is a UI/UX authority", PLANNING_TICKET)

    def test_adapter_native_mechanics_are_absent(self) -> None:
        forbidden = [
            r"\bNode\b",
            r"\bPython\b",
            r"\bGo\b",
            r"nativeReport",
            r"contextDigest",
            r"adapterVersion",
            r"references/adapters",
            r"adapters/node",
            r"adapters/python",
            r"adapters/go",
            r"per-task Fast",
            r"Full entry",
        ]
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, SKILL), pattern)

    def test_run_state_is_implementation_only(self) -> None:
        for state in (
            "PREFLIGHT",
            "IMPLEMENTING",
            "RECONCILING",
            "FINAL_REVIEW",
            "IMPLEMENTATION_COMPLETE",
            "INCOMPLETE",
            "BLOCKED",
            "PENDING",
            "WORKER_RUNNING",
            "REVIEWING",
            "IMPLEMENTED",
        ):
            self.assertIn(state, SKILL)
        for removed in (
            "READY_FOR_VERIFICATION",
            "verificationSessionId",
            "verificationResultId",
            "verificationVerdict",
            "currentnessResult",
            "checkpointHistoryRefs",
            "ImplementationHandoff",
            "assertCurrent",
            "RUNTIME_EXERCISE",
            "runtimeExercise",
        ):
            self.assertNotIn(removed, SKILL)

    def test_attribution_and_scope_states_are_not_conflated(self) -> None:
        self.assertIn("`attributionState` is `UNASSESSED`, `RECONCILING`, `CLEAR`, or `BLOCKED`", SKILL)
        self.assertIn("A scope comparison never sets\nit directly", SKILL)
        self.assertIn("`scopeComparisonState` is the tool-reported", SKILL)
        self.assertIn("it does not\nclaim that the actor of every disjoint external path is known", SKILL)

    def test_first_worker_requires_baseline_capsule(self) -> None:
        self.assertIn("../baseline-capsule/baseline_capsule.py create", SKILL)
        self.assertIn("canonical physical directory containing this `SKILL.md`", SKILL)
        self.assertIn("Never search for or substitute another same-named Baseline Capsule copy", SKILL)
        self.assertIn("Immediately before dispatching the first\nWorker", SKILL)
        self.assertIn("require exact equality with\n`baselineSourceIdentity`", SKILL)
        self.assertIn("immutable source-baseline support module", SKILL)

    def test_capsule_failure_prevents_worker_dispatch(self) -> None:
        self.assertIn("no Worker may run after a terminal result", SKILL)
        self.assertIn("missing or expired Capsules are never silently replaced", SKILL)
        self.assertIn("For a genuine zero-source-mutation Ticket path, create the Capsule", SKILL)

    def test_zero_source_mutation_runtime_coverage_has_an_executable_path(self) -> None:
        self.assertIn("For a genuine zero-source-mutation Ticket path, create the Capsule", SKILL)
        self.assertIn("proceed directly to\n`FINAL_REVIEW` when every source requirement is `ESTABLISHED`", SKILL)
        self.assertIn("Runtime coverage remains `PARTIAL` until that final exercise succeeds", SKILL)
        self.assertIn("A zero-source-mutation path freezes no Worker envelope and creates no task", SKILL)

    def test_zero_source_evidence_is_durable_without_artificial_task(self) -> None:
        self.assertIn("create no TaskState, task record, or task fields", SKILL)
        self.assertIn("Final source or runtime evidence is recorded at run level in\n`completionRecord`", SKILL)
        self.assertIn("do not create an artificial task merely to hold evidence", SKILL)

    def test_implemented_is_source_review_not_verification(self) -> None:
        self.assertIn("task_implementation_review_complete", SKILL)
        self.assertIn("does not claim a separate", SKILL)
        self.assertIn("technical verification verdict", SKILL)
        self.assertIn("Implementation completion and Acceptance Criterion coverage", SKILL)

    def test_runtime_dependent_coverage_requires_direct_product_evidence(self) -> None:
        self.assertIn("requirement remains `PARTIAL` after source integration", SKILL)
        self.assertIn("Implementation Lead directly performs a representative runtime exercise", SKILL)
        self.assertIn("obtains the required authoritative product readback", SKILL)
        self.assertIn("internal-helper call alone\nis not that evidence", SKILL)
        self.assertIn("source artifact, static schema,\ndocument, or structural constraint", SKILL)

    def test_runtime_exercise_is_lead_owned_after_source_closure(self) -> None:
        self.assertIn("Worker runtime checks are provisional focused feedback", SKILL)
        self.assertIn("never become a Representative Runtime\nObservation", SKILL)
        self.assertIn("When all source gaps are closed, proceed to\n`FINAL_REVIEW`", SKILL)
        self.assertIn("Implementation Lead directly performs the smallest set", SKILL)
        self.assertIn("One exercise may support multiple requirements", SKILL)

    def test_runtime_observation_is_not_carried_across_source_change(self) -> None:
        self.assertIn("Worker observations remain provisional and are never carried", SKILL)
        self.assertIn("Lead-owned observations are created only after dependency closure", SKILL)
        self.assertIn("any subsequent source change discards them", SKILL)

    def test_runtime_failures_distinguish_product_environment_and_authority(self) -> None:
        self.assertIn("expected effect that is absent", FAILURE_ROUTING)
        self.assertIn("Ticket-authorized defect attributable to the task", FAILURE_ROUTING)
        self.assertIn("Without an authoritative readback, the runtime-dependent Acceptance Criterion remains `PARTIAL`", FAILURE_ROUTING)
        self.assertIn("reliable target-to-source binding is\n  `INCOMPLETE`", FAILURE_ROUTING)
        self.assertIn("Unclear target authority, an unapproved external effect", FAILURE_ROUTING)
        self.assertIn("A project delta during the Lead-owned final exercise invalidates the observation", FAILURE_ROUTING)

    def test_runtime_safety_and_ticket_observability_are_explicit(self) -> None:
        self.assertIn("Use the current checkout only when the repository-authoritative command cannot create", SKILL)
        self.assertIn("source materialization outside the project root", SKILL)
        self.assertIn("Use `INDEPENDENT_READBACK`", SKILL)
        self.assertIn("Do not automatically use production, real money, real messages, user data", SKILL)
        self.assertIn("explicit user authorization for this invocation", SKILL)
        self.assertIn("observable product flow, expected effect, and readback", TO_TICKETS)
        self.assertIn("Implementation Lead\ndirectly performs any final representative runtime exercise", TO_TICKETS)
        self.assertIn("but does not itself add a\npositive completion condition", PLANNING_TICKET)

    def test_final_review_binds_two_equal_source_identities(self) -> None:
        self.assertIn("finalReviewStartIdentity", SKILL)
        self.assertIn("finalSourceIdentity", SKILL)
        self.assertIn("source identity before and after equals `finalSourceIdentity`", SKILL)
        self.assertIn("finalReviewStartIdentity == finalSourceIdentity", SKILL)

    def test_final_review_discards_observation_on_identity_drift(self) -> None:
        self.assertIn("discard all observations and restart the complete final review once", SKILL)
        self.assertIn("second disjoint identity drift is\n    `INCOMPLETE`", SKILL)
        self.assertIn("overlapping or authority change is `BLOCKED`", SKILL)

    def test_unexpected_delta_is_reconciled_before_terminal_routing(self) -> None:
        self.assertIn("change is evidence to reconcile", SKILL)
        self.assertIn("Continue automatically when the unexpected delta is external or remains unattributed", SKILL)
        self.assertIn("Record `CONTINUE` only when", SKILL)
        self.assertIn("Record `REMEDIATE` only for", SKILL)

    def test_blocked_is_reserved_for_authority_overlap_or_preservation_loss(self) -> None:
        self.assertIn("Return `BLOCKED` only when planning authority changed", SKILL)
        self.assertIn("pre-existing work was overwritten", SKILL)

    def test_other_scratch_work_is_not_automatically_blocking(self) -> None:
        self.assertIn("Another `.scratch/<work-slug>/**` tree is not automatically safe or unsafe", SKILL)
        self.assertIn("Do not globally exclude `.scratch/**`", SKILL)

    def test_reconciled_external_changes_are_auditable_and_not_completion_evidence(self) -> None:
        self.assertIn("Each reconciled external-change record contains", SKILL)
        self.assertIn("preservationBeforeIdentity, preservationAfterIdentity", SKILL)
        self.assertIn("excludedFromCoverage = true", SKILL)
        self.assertIn("must not infer an actor from path spelling", SKILL)

    def test_scope_remediation_cannot_launder_an_out_of_envelope_delta(self) -> None:
        self.assertIn("does not retroactively\nmake the original out-of-envelope delta valid task evidence", SKILL)
        self.assertIn("Never use remediation to retain\nan unplanned path", SKILL)

    def test_operational_failures_do_not_become_ownership_blockers(self) -> None:
        self.assertIn("Ownership compare exit `10`: enter `RECONCILING`", FAILURE_ROUTING)
        self.assertIn("retry the same bounded call once", FAILURE_ROUTING)
        self.assertIn("A second\n  no-delta runtime failure is `INCOMPLETE`", FAILURE_ROUTING)
        self.assertIn("never re-seal", FAILURE_ROUTING)
        self.assertIn("ImplementationResult `PLANNING_INPUT_CHANGED`: `BLOCKED`", FAILURE_ROUTING)

    def test_reconciliation_scenario_matrix_is_closed(self) -> None:
        self.assertIn("Preserved external change, disjoint from planning authority and task impact", FAILURE_ROUTING)
        self.assertIn("Worker-attributable scope violation", FAILURE_ROUTING)
        self.assertIn("Overlapping product path with unclear actor", FAILURE_ROUTING)
        self.assertIn("overwritten pre-existing work", FAILURE_ROUTING)
        self.assertIn("A path inside the envelope can still be externally edited", FAILURE_ROUTING)
        self.assertIn("`WITHIN_ENVELOPE` means only", TASK_OWNERSHIP)
        self.assertIn("blocked: planning input changed", PLANNING_CURRENTNESS)

    def test_final_review_has_one_disjoint_restart(self) -> None:
        self.assertIn("restart the complete final review once", SKILL)
        self.assertIn("second disjoint identity drift is\n    `INCOMPLETE`", SKILL)

    def test_completion_publishes_independent_result(self) -> None:
        self.assertIn("implementation-result-v3", SKILL)
        self.assertIn("implementation_result.py publish", SKILL)
        self.assertIn("the caller does not submit\n`implementationStatus`", SKILL)
        self.assertIn("publisher validates and writes immutable implementation-result-v3", SKILL)
        self.assertIn("It does not mean `VERIFIED`", SKILL)
        self.assertIn("supplementalLocalAuthorityBindings", COMPLETION_RECORD)
        self.assertIn("projectDeltaBinding", COMPLETION_RECORD)
        self.assertIn("unknown properties are rejected", COMPLETION_RECORD)

    def test_ui_dispatch_evidence_is_not_an_acceptance_criterion_type(self) -> None:
        self.assertIn("every ESTABLISHED coverage that depends on implementation or renderer evidence from a", SKILL)
        self.assertIn("`UI_IMPLEMENTATION` dispatch has applicable approved UI authority", SKILL)
        self.assertIn("`UI_IMPLEMENTATION` dispatch has applicable approved UI authority", SKILL)
        self.assertIn("Implementation Lead uses the actual intended\nrenderer", SKILL)
        self.assertNotIn("every UI_IMPLEMENTATION Acceptance Criterion", SKILL)

    def test_later_finding_cannot_reopen_implementation(self) -> None:
        self.assertIn("later user bug report or review finding requires new", SKILL)
        self.assertIn("it never reopens this one", SKILL)
        self.assertIn("cannot\nretroactively alter this invocation's immutable result", SKILL)

    def test_removed_named_actor_is_absent_from_active_contracts(self) -> None:
        removed_actor = "Verification" + " Lead"
        active = [
            SKILL,
            FAILURE_ROUTING,
            TASK_OWNERSHIP,
            PLANNING_CURRENTNESS,
            PLANNING_TICKET,
            UI_TICKET,
            GREENFIELD,
            TO_TICKETS,
            BASELINE_README,
            BASELINE_SOURCE,
        ]
        self.assertTrue(all(removed_actor not in text for text in active))
        self.assertIn("Ticket's Acceptance Criteria can be observed", TO_TICKETS)
        self.assertIn("Verification Expectations", TO_SPEC)
        self.assertIn("independent certification", COMPLETION_RECORD)
        self.assertIn("independent general technical\ncertification", SKILL)

    def test_frontend_mode_is_exactly_a_dispatch_classification_not_a_lifecycle(self) -> None:
        mode_block = re.search(
            r"`frontendMode` is a current-dispatch classification.*?```text\n(.*?)```",
            SKILL,
            re.DOTALL,
        )
        self.assertIsNotNone(mode_block)
        assert mode_block is not None
        self.assertEqual(
            {"NONE", "ENGINEERING_ONLY", "UI_IMPLEMENTATION"},
            set(mode_block.group(1).split()),
        )
        self.assertIn("not a RunState, TaskState, task record, manifest,\nor result protocol", SKILL)
        self.assertIn("not Worker selection", SKILL)
        self.assertIn("no Addon,\ndedicated frontend Worker, or separate manifest", SKILL)
        self.assertNotIn("FRONTEND_REVIEW", SKILL)
        self.assertNotIn("FRONTEND_IMPLEMENTING", SKILL)

    def test_frontend_classification_uses_actual_consumer_and_rendered_contract(self) -> None:
        self.assertIn("actual current runtime consumer and observable completion condition", SKILL)
        self.assertIn("never a file\nextension, directory name, task title, or guessed stack", SKILL)
        self.assertIn("browser or\n  native UI runtime consumer", SKILL)
        self.assertIn("accessibility semantics, focus or keyboard behavior", SKILL)
        self.assertIn("Shared source is frontend-bearing only", SKILL)
        self.assertIn("even when its expected pixels and UX\nare preservation rather than change", SKILL)

    def test_ui_authority_modes_preserve_no_ui_contract(self) -> None:
        self.assertIn("`UI_IMPLEMENTATION` with Ticket `UI: no` is `BLOCKED` before Worker dispatch", SKILL)
        self.assertIn("`ENGINEERING_ONLY` is permitted for Ticket `UI: no`", SKILL)
        self.assertIn("must not infer a UI authority,\nrequirement, or reference", SKILL)
        self.assertIn("a backend-only task is `NONE`", SKILL)
        self.assertIn("A Ticket with `UI: no` never loads this reference", UI_TICKET)

    def test_every_frontend_dispatch_passes_active_guidance_for_direct_read(self) -> None:
        self.assertIn("including frontend remediation\ndispatches", SKILL)
        self.assertIn("stable identifier `ima2-front`", SKILL)
        self.assertIn("canonical physical absolute `SKILL.md` path", SKILL)
        self.assertIn("pass both values afresh on every Worker call", SKILL)
        self.assertIn("Before any product-file mutation, the Worker reads the passed absolute", SKILL)
        self.assertIn("does not assume that the OpenCode `skill` tool is available", SKILL)
        self.assertIn("task-relevant references that the\n   `SKILL.md` routing directs", SKILL)
        self.assertIn("following symlinks to their real paths", SKILL)

    def test_frontend_worker_authority_and_guardrails_are_explicit(self) -> None:
        self.assertIn("ready Ticket and approved parent Spec", SKILL)
        self.assertIn("> approved UI reference and task locator when UI: yes", SKILL)
        self.assertIn("> repository design system, commands, and conventions", SKILL)
        self.assertIn("> ima2-front objective implementation guidance", SKILL)
        self.assertIn("> ima2-front style samples", SKILL)
        self.assertIn("does not invoke `ima2-uiux`", SKILL)
        self.assertIn("The Lead never invokes `ima2-uiux` as a fallback", SKILL)
        self.assertIn("create a new Design Read", SKILL)
        self.assertIn("does not install or set up `ima2`, log in, or change global defaults", SKILL)
        self.assertIn("Concept mockup generation is forbidden", SKILL)
        self.assertIn("preserves the rendered and UX result exactly", SKILL)

    def test_frontend_routing_rendered_evidence_and_currentness_are_explicit(self) -> None:
        self.assertIn("return `INCOMPLETE` before product mutation", SKILL)
        self.assertIn("returns `GUIDANCE_UNAVAILABLE`; the Lead routes this to `INCOMPLETE`", SKILL)
        self.assertIn("returns `AUTHORITY_GAP`; the Lead routes this to `BLOCKED`", SKILL)
        self.assertIn("Static source inspection cannot establish `UI_IMPLEMENTATION`", UI_TICKET)
        self.assertIn("expected rendered effect and authoritative product readback", SKILL)
        self.assertIn("Do not apply the no-delta generic Worker-call retry", FAILURE_ROUTING)
        self.assertIn("shared CSS/design tokens", UI_TICKET)
        self.assertIn("Final rendered observations are created only after source dependency closure", UI_TICKET)
        self.assertIn("any later\nsource change discards them", UI_TICKET)
        self.assertIn("create no TaskState, task record, or task fields", SKILL)
        self.assertIn("Lead-owned final\nrepresentative runtime exercise", SKILL)


if __name__ == "__main__":
    unittest.main()
