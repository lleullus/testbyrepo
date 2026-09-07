import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

import { buildProbeBinding, validateProbeHandoff } from "../src/probe-handoff.js";
import { captureVerificationTarget } from "../src/verification-target.js";

function sha(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function initGit(project) {
  for (const args of [
    ["init", "-q"],
    ["add", "."],
    ["-c", "user.name=Ready Test", "-c", "user.email=ready@example.invalid", "commit", "-qm", "fixture"],
  ]) {
    const result = spawnSync("git", ["-C", project, ...args], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
  }
}

function writeTicket(ticket, project, extra = "") {
  fs.writeFileSync(ticket, [
    "# TICKET-001: probe binding fixture",
    "",
    "Status: ready",
    `Project-Root: ${project}`,
    "",
    "## Verification",
    "",
    "- Parent outcome ordinal: 1",
    "  AC ordinals: 1",
    "  Trigger or inspection target: ordinary runtime",
    "  Authoritative readback: stdout",
    extra,
    "",
  ].filter(line => line !== undefined).join("\n"));
}

function fakeAuthority(project, ticket, spec) {
  return {
    project_root: fs.realpathSync(project),
    ticket_path: fs.realpathSync(ticket),
    ticket_sha256: sha(ticket),
    ticket_status_at_start: "ready",
    parent_spec_path: fs.realpathSync(spec),
    parent_spec_sha256: sha(spec),
    behavior_authorities: [],
    ui_authority: null,
  };
}

async function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "iis-probe-binding-"));
  const project = path.join(root, "project");
  fs.mkdirSync(project, { recursive: true });
  const ticket = path.join(project, "TICKET.md");
  const spec = path.join(project, "SPEC.md");
  const product = path.join(project, "product.js");
  fs.writeFileSync(spec, "Status: approved\n");
  fs.writeFileSync(product, "console.log('ok');\n");
  writeTicket(ticket, project);
  initGit(project);
  const bindAuthorityFn = async () => fakeAuthority(project, ticket, spec);
  const binding = await buildProbeBinding({
    projectRoot: project,
    ticketPath: ticket,
    targetPaths: [product],
    admittedLanes: ["flow-1"],
    laneTerminals: [{ lane: "flow-1", status: "NO_FINDING" }],
    bindAuthorityFn,
    captureTargetFn: captureVerificationTarget,
  });
  const handoff = path.join(root, "probe-binding.json");
  fs.writeFileSync(handoff, JSON.stringify(binding, null, 2) + "\n");
  return { root, project, ticket, spec, product, handoff, bindAuthorityFn };
}

test("current Probe machine binding accepts a harmless parent claim", async t => {
  const data = await fixture();
  t.after(() => fs.rmSync(data.root, { recursive: true, force: true }));
  const binding = JSON.parse(fs.readFileSync(data.handoff, "utf8"));
  binding.parent_claim = "Parent says this complete Probe remains current.";
  fs.writeFileSync(data.handoff, JSON.stringify(binding, null, 2) + "\n");
  const result = await validateProbeHandoff({
    probeBindingPath: data.handoff,
    projectRoot: data.project,
    ticketPath: data.ticket,
    targetPaths: [data.product],
    bindAuthorityFn: data.bindAuthorityFn,
    captureTargetFn: captureVerificationTarget,
  });
  assert.equal(result.valid, true);
  assert.equal(result.binding.probe_completion, "COMPLETE");
});

test("Probe machine binding rejects malformed JSON bytes", async t => {
  const data = await fixture();
  t.after(() => fs.rmSync(data.root, { recursive: true, force: true }));
  const validBytes = fs.readFileSync(data.handoff, "utf8");
  fs.writeFileSync(data.handoff, `${validBytes.trimEnd()},\n`);
  await assert.rejects(
    validateProbeHandoff({
      probeBindingPath: data.handoff,
      projectRoot: data.project,
      ticketPath: data.ticket,
      targetPaths: [data.product],
      bindAuthorityFn: data.bindAuthorityFn,
      captureTargetFn: captureVerificationTarget,
    }),
    SyntaxError,
  );
});

test("Probe machine binding rejects verifier-owned verdict contamination", async t => {
  const data = await fixture();
  t.after(() => fs.rmSync(data.root, { recursive: true, force: true }));
  const binding = JSON.parse(fs.readFileSync(data.handoff, "utf8"));
  binding.evaluation = "PASS";
  fs.writeFileSync(data.handoff, JSON.stringify(binding, null, 2) + "\n");
  await assert.rejects(
    validateProbeHandoff({
      probeBindingPath: data.handoff,
      projectRoot: data.project,
      ticketPath: data.ticket,
      targetPaths: [data.product],
      bindAuthorityFn: data.bindAuthorityFn,
      captureTargetFn: captureVerificationTarget,
    }),
    /verifier-owned value/,
  );
});

test("Probe machine binding rejects incomplete or noncanonical lane closure", async t => {
  const data = await fixture();
  t.after(() => fs.rmSync(data.root, { recursive: true, force: true }));
  const binding = JSON.parse(fs.readFileSync(data.handoff, "utf8"));
  binding.lane_terminals = [];
  fs.writeFileSync(data.handoff, JSON.stringify(binding, null, 2) + "\n");
  await assert.rejects(
    validateProbeHandoff({
      probeBindingPath: data.handoff,
      projectRoot: data.project,
      ticketPath: data.ticket,
      targetPaths: [data.product],
      bindAuthorityFn: data.bindAuthorityFn,
      captureTargetFn: captureVerificationTarget,
    }),
    /lane denominator/,
  );
});

test("parent claim cannot refresh a stale Probe identity", async t => {
  const data = await fixture();
  t.after(() => fs.rmSync(data.root, { recursive: true, force: true }));
  const binding = JSON.parse(fs.readFileSync(data.handoff, "utf8"));
  binding.parent_claim = "Parent says this Probe is rebound to the current Ticket";
  fs.writeFileSync(data.handoff, JSON.stringify(binding, null, 2) + "\n");
  writeTicket(data.ticket, data.project, "  Decision boundary: materially changed current flow");
  await assert.rejects(
    validateProbeHandoff({
      probeBindingPath: data.handoff,
      projectRoot: data.project,
      ticketPath: data.ticket,
      targetPaths: [data.product],
      bindAuthorityFn: data.bindAuthorityFn,
      captureTargetFn: captureVerificationTarget,
    }),
    /STALE (ticket|verification_flow_denominator|implementation_target)/,
  );
});
