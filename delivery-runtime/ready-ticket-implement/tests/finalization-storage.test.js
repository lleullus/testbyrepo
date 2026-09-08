import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { fixture } from "./helpers.js";
import { finalizeVerification } from "../src/core.js";

async function prepare(f) {
  const state = await f.lifecycle.beginDirect({ sessionId: "verifier", projectRoot: f.root, ticketPath: f.ticket, purpose: "verify" });
  f.lifecycle.checkpoint(state.execution_id, "verifier", "PRE_PROGRESSION", "current full closure");
  await f.lifecycle.releaseCheckpoint(state.execution_id, "verifier", "CONTINUE");
  return state;
}

test("terminal state write failure does not manufacture completed from done bytes", async t => {
  const f = await fixture(t), state = await prepare(f), before = fs.readFileSync(f.ticket);
  const write = f.store.writeExecution.bind(f.store);
  let injected = false;
  f.store.writeExecution = value => {
    if (!injected && value.phase === "COMPLETE") { injected = true; throw new Error("injected durable terminal failure"); }
    return write(value);
  };
  const result = await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED");
  assert.equal(injected, true); assert.equal(result.ticket_progression, "FAILED");
  assert.deepEqual(fs.readFileSync(f.ticket), before);
  assert.ok(f.store.readActiveTicket(f.root, f.ticket));
  assert.equal((await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED")).ticket_progression, "COMPLETED");
});

test("durable terminal plus interrupted index cleanup preserves exclusion until exact recovery", async t => {
  const f = await fixture(t), state = await prepare(f);
  const clear = f.store.clearActiveTicket.bind(f.store);
  let injected = false;
  f.store.clearActiveTicket = (...args) => {
    if (!injected) { injected = true; throw new Error("injected index cleanup interruption"); }
    return clear(...args);
  };
  const result = await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED");
  assert.equal(result.ticket_progression, "FAILED"); assert.equal(result.ticket_status_after, "done");
  assert.ok(f.store.readActiveTicket(f.root, f.ticket));
  const recovered = await finalizeVerification(f.lifecycle, state.execution_id, "verifier", "VERIFIED");
  assert.equal(recovered.ticket_progression, "COMPLETED");
  assert.equal(f.store.readActiveTicket(f.root, f.ticket), null);
});
