import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { checkPlanAdmission, inspectAuthority } from "../src/core.js";
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
