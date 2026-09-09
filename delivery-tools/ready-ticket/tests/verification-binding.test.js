import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { captureVerification, checkVerificationCurrentness } from "../src/core.js";
import { fixture } from "./helpers.js";

test("verification binding snapshots stable targets outside the Project Root and permits declared effect mutation", async t => {
  const f = await fixture(t);
  const bindingPath = path.join(f.base, "bindings", "verify.json");
  const captured = await captureVerification({
    projectRoot: f.root,
    ticketPath: f.ticket,
    stableTargetPaths: [f.stable],
    scenarioEffectPaths: [f.effect],
    planReviewPath: f.review,
    bindingPath,
    validatorPath: f.validatorPath,
  });
  assert.equal(captured.binding_path, bindingPath);
  assert.equal(fs.statSync(bindingPath).mode & 0o777, 0o600);
  assert.equal(captured.binding.stable_target_paths[0], f.stable);
  assert.equal(captured.binding.scenario_effect_paths[0], f.effect);
  fs.writeFileSync(f.effect, "{\"published\":true}\n");
  assert.equal((await checkVerificationCurrentness(captured.binding)).current, true);
  fs.writeFileSync(f.stable, "console.log('drift');\n");
  const drift = await checkVerificationCurrentness(captured.binding);
  assert.equal(drift.current, false);
  assert.deepEqual(drift.stable_target_changed, ["cli.js"]);
});

test("stable/effect overlap and protected Plan effect paths are rejected", async t => {
  const f = await fixture(t);
  await assert.rejects(captureVerification({
    projectRoot: f.root,
    ticketPath: f.ticket,
    stableTargetPaths: [f.stable],
    scenarioEffectPaths: [f.stable],
    bindingPath: path.join(f.base, "overlap.json"),
    validatorPath: f.validatorPath,
  }), /overlaps scenario effect/);
  await assert.rejects(captureVerification({
    projectRoot: f.root,
    ticketPath: f.ticket,
    stableTargetPaths: [f.stable],
    scenarioEffectPaths: [f.plan],
    planReviewPath: f.review,
    bindingPath: path.join(f.base, "plan-effect.json"),
    validatorPath: f.validatorPath,
  }), /protected authority\/method/);
});

test("binding paths are immutable and cannot be inside the Project Root", async t => {
  const f = await fixture(t);
  const outside = path.join(f.base, "binding.json");
  await captureVerification({ projectRoot: f.root, ticketPath: f.ticket, stableTargetPaths: [f.stable], bindingPath: outside, validatorPath: f.validatorPath });
  await assert.rejects(captureVerification({ projectRoot: f.root, ticketPath: f.ticket, stableTargetPaths: [f.stable], bindingPath: outside, validatorPath: f.validatorPath }), /already exists/);
  await assert.rejects(captureVerification({ projectRoot: f.root, ticketPath: f.ticket, stableTargetPaths: [f.stable], bindingPath: path.join(f.root, "binding.json"), validatorPath: f.validatorPath }), /outside Project Root/);
});
