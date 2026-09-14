import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { checkPlanAdmission, inspectAuthority, hashBytes } from "../src/core.js";
import { fixture } from "./helpers.js";

test("authority inspection and plan admission are stateless current-byte checks", async t => {
  const f = await fixture(t);
  const authority = await inspectAuthority({ projectRoot: f.root, ticketPath: f.ticket, validatorPath: f.validatorPath });
  assert.equal(authority.ticket_status_at_capture, "ready");
  assert.equal(authority.authority_digest, f.authority.authority_digest);
  const admission = await checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath });
  assert.equal(admission.schema, "iis-implementation-admission/v1");
  assert.equal(admission.decision, "ADMIT");
  assert.equal(admission.start_scope, "cli.js");
  assert.equal(typeof admission.admission_digest, "string");
  assert.equal(fs.existsSync(`${f.base}/state`), false);
});

test("legacy extra heuristic data is ignored while reviewer origin remains required", async t => {
  const f = await fixture(t);
  f.reviewData.heuristic = { evidence_reference: "legacy-only", disposition_summary: "ignored" };
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  const admission = await checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath });
  assert.equal(admission.schema, "iis-implementation-admission/v1");
  assert.equal(admission.decision, "ADMIT");
  delete f.reviewData.review_origin.reviewer;
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath }), /PLAN_REVIEW_STALE/);
});

test("missing reviewer evidence reference is stale", async t => {
  const f = await fixture(t);
  delete f.reviewData.review_origin.evidence_reference;
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath }), /PLAN_REVIEW_STALE/);
});

test("EVIDENCE_NEEDED is not admitted", async t => {
  const f = await fixture(t);
  f.reviewData.decisions[0].decision = "EVIDENCE_NEEDED";
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath }), /PLAN_NOT_ADMITTED/);
});

test("Ticket authority byte changes make the review stale", async t => {
  const f = await fixture(t);
  fs.appendFileSync(f.ticket, "\n");
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath }), /PLAN_REVIEW_STALE/);
});

test("missing, stale, and non-admitted reviews fail before implementation admission", async t => {
  const f = await fixture(t);
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, validatorPath: f.validatorPath }), /PLAN_REVIEW_REQUIRED/);
  f.reviewData.decisions[0].decision = "REVISE";
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath }), /PLAN_NOT_ADMITTED/);
  f.reviewData.decisions[0].decision = "ADMIT";
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  fs.appendFileSync(f.plan, "\nmethod changed\n");
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath }), /PLAN_REVIEW_STALE/);
});

test("ordinary implementation source changes do not make a reviewed Plan stale", async t => {
  const f = await fixture(t);
  fs.writeFileSync(f.stable, "console.log('fixed after a local test failure');\n");
  const admission = await checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath });
  assert.equal(admission.decision, "ADMIT");
});

test("ADMIT cannot erase an explicit projection gap or unresolved contract finding", async t => {
  const f = await fixture(t);
  const input = { projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath };
  const decision = f.reviewData.decisions[0];
  decision.projection = { status: "gap", basis: "Parent event subscription has no current Ticket owner." };
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(checkPlanAdmission(input), /PLAN_NOT_ADMITTED/);
  decision.projection.status = "preserved";
  decision.findings = [{ kind: "contract_gap", anchor: "Spec outcome 1", observation: "Subscription omitted", material: false, disposition: "unresolved", basis: "No current sibling owns subscription", next_owner: "To Tickets" }];
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(checkPlanAdmission(input), /PLAN_NOT_ADMITTED/);
});

test("non-material advisory remains admissible but a material unresolved method does not", async t => {
  const f = await fixture(t);
  const input = { projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath };
  const finding = { kind: "method", anchor: "Plan", observation: "Optional diagnostic is absent", material: false, disposition: "unresolved", basis: "Direct CLI output already decides the approved outcome", next_owner: "None" };
  f.reviewData.decisions[0].findings = [finding];
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  assert.equal((await checkPlanAdmission(input)).decision, "ADMIT");
  finding.material = true;
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(checkPlanAdmission(input), /PLAN_NOT_ADMITTED/);
});

test("a resolved finding cannot rely on changed or missing relative evidence", async t => {
  const f = await fixture(t);
  const input = { projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath };
  const evidence = `${f.base}/observation.txt`;
  fs.writeFileSync(evidence, "actual CLI output: expected product output\n");
  f.reviewData.decisions[0].findings = [{ kind: "evidence_limit", anchor: "Plan readback", observation: "Output observed", material: true, disposition: "resolved", basis: "Current CLI readback", next_owner: "None", evidence_refs: [{ path: "observation.txt", sha256: hashBytes(fs.readFileSync(evidence)), locator: "line 1" }] }];
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  assert.equal((await checkPlanAdmission(input)).decision, "ADMIT");
  fs.appendFileSync(evidence, "different run\n");
  await assert.rejects(checkPlanAdmission(input), /PLAN_REVIEW_STALE/);
  fs.unlinkSync(evidence);
  await assert.rejects(checkPlanAdmission(input), /PLAN_REVIEW_STALE/);
});

test("another Ticket's review cannot admit this Ticket", async t => {
  const f = await fixture(t);
  const other = await fixture(t);
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: other.review, validatorPath: f.validatorPath }), /PLAN_REVIEW_STALE/);
  other.reviewData.project_root = f.root;
  other.reviewData.plans = f.reviewData.plans;
  fs.writeFileSync(other.review, JSON.stringify(other.reviewData));
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: other.review, validatorPath: f.validatorPath }), /PLAN_REVIEW_STALE: exact Ticket pairing/);
});

test("historical v1 approval is not automatically migrated into current admission", async t => {
  const f = await fixture(t);
  f.reviewData.schema = "iis-plan-review/v1";
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(checkPlanAdmission({ projectRoot: f.root, ticketPath: f.ticket, planReviewPath: f.review, validatorPath: f.validatorPath }), /PLAN_REVIEW_STALE: schema\/root mismatch/);
});
