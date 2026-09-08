import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fixture } from "./helpers.js";
import { bindPlanReview } from "../src/plan-binding.js";

test("missing, wrong-ticket, REVISE and stale review cannot create implementation assignment", async t => {
  const f = await fixture(t);
  await assert.rejects(f.lifecycle.assignSubagent({ parentSessionId: "parent", projectRoot: f.root, ticketPath: f.ticket }), /PLAN_REVIEW_REQUIRED/);
  const wrong = structuredClone(f.reviewData); wrong.contracts[0].ticket_path += ".other";
  fs.writeFileSync(f.review, JSON.stringify(wrong));
  await assert.rejects(f.lifecycle.assignSubagent({ parentSessionId: "parent", ...f.input }), /PLAN_REVIEW_STALE/);
  f.reviewData.decisions[0].decision = "REVISE";
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(f.lifecycle.beginDirect({ sessionId: "worker", ...f.input }), /PLAN_NOT_ADMITTED/);
  assert.equal(f.store.readActiveTicket(f.root, f.ticket), null);
  f.reviewData.decisions[0].decision = "ADMIT";
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  fs.appendFileSync(f.plan, "method changed");
  await assert.rejects(f.lifecycle.beginDirect({ sessionId: "worker", ...f.input }), /PLAN_REVIEW_STALE/);
});

test("review must be exact outside root and hash actual bytes, not caller declaration", async t => {
  const f = await fixture(t);
  const inside = path.join(f.root, "review.json"); fs.copyFileSync(f.review, inside);
  assert.throws(() => bindPlanReview({ planReviewPath: inside, authority: f.authority }), /outside Project Root/);
  f.reviewData.plans[0].sha256 = "invented";
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  assert.throws(() => bindPlanReview({ planReviewPath: f.review, authority: f.authority }), /PLAN_REVIEW_STALE/);
});

test("delegated consumption rechecks review after assignment issuance", async t => {
  const f = await fixture(t);
  const assignment = await f.lifecycle.assignSubagent({ parentSessionId: "parent", ...f.input });
  f.reviewData.decisions[0].start_scope = "different permitted scope";
  fs.writeFileSync(f.review, JSON.stringify(f.reviewData));
  await assert.rejects(f.lifecycle.beginDelegated({ childSessionId: "child", assignmentId: assignment.assignment_id }), /PLAN_REVIEW_STALE/);
  assert.equal(f.store.readAssignment(assignment.assignment_id).status, "issued");
});
