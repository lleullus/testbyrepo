import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fixture, materializeReadyBundle } from "./helpers.js";

function zodStub() {
  const node = () => ({ optional() { return this; } });
  return { string: node, enum: node, array: node, object: node };
}

function fakePi() {
  return {
    zod: zodStub(),
    pi: {
      resolveReadyVerifierTerminal() { throw new Error("not used"); },
      releaseReadyVerifierTerminal() {},
      releaseReadyVerifierTerminalsForSession() {},
    },
    registerTool() {},
    on() {},
  };
}

test("the loaded immutable release is the only bundle identity source", async t => {
  const f = await fixture(t);
  const loaded = await materializeReadyBundle(f.base);
  const previous = process.env.IIS_READY_BUNDLE_ID;
  process.env.IIS_READY_BUNDLE_ID = "0".repeat(64);
  try {
    const installed = loaded.module.installReadyBoundaryTools(fakePi(), {
      bundleIdentity: "1".repeat(64),
      validatorPath: f.validatorPath,
    });
    assert.equal(installed.bundleIdentity, loaded.bundleId);
  } finally {
    if (previous === undefined) delete process.env.IIS_READY_BUNDLE_ID;
    else process.env.IIS_READY_BUNDLE_ID = previous;
  }
});

test("a missing or invalid manifest fails before registering boundary tools", async t => {
  const missingFixture = await fixture(t);
  const missing = await materializeReadyBundle(missingFixture.base);
  fs.unlinkSync(path.join(missing.release, "bundle.json"));
  assert.throws(
    () => missing.module.installReadyBoundaryTools(fakePi(), { validatorPath: missingFixture.validatorPath }),
    /READY_BUNDLE_INVALID: cannot read bundle\.json/,
  );

  const invalidFixture = await fixture(t);
  const invalid = await materializeReadyBundle(invalidFixture.base);
  const manifestPath = path.join(invalid.release, "bundle.json");
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  manifest.family = "ready-runtime-v2";
  fs.chmodSync(manifestPath, 0o600);
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest)}\n`);
  assert.throws(
    () => invalid.module.installReadyBoundaryTools(fakePi(), { validatorPath: invalidFixture.validatorPath }),
    /READY_BUNDLE_INVALID: unsupported schema, protocol, or family/,
  );
});

test("loaded boundary file drift fails closed even when the module was already imported", async t => {
  const f = await fixture(t);
  const loaded = await materializeReadyBundle(f.base);
  const corePath = path.join(loaded.release, "delivery-tools/ready-ticket/src/core.js");
  fs.chmodSync(corePath, 0o600);
  fs.appendFileSync(corePath, "\n");
  assert.throws(
    () => loaded.module.installReadyBoundaryTools(fakePi(), { validatorPath: f.validatorPath }),
    /READY_BUNDLE_INVALID: boundary file drift: delivery-tools\/ready-ticket\/src\/core\.js/,
  );
});
