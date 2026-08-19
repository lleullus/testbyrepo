import assert from "node:assert/strict";
import test from "node:test";
import { AuditRuntime } from "../.pi/extensions/iis-ready-audit/runtime.ts";

const spec = (assignment = "slot-1") => ({
  role: "implementation",
  assignment,
  task: "Inspect one exact implementation candidate.",
  cwd: "/tmp",
  model: "opencodex/gpt-5.6-luna",
  thinking: "high",
  oracleBrowser: false,
});

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function eventCollector() {
  const events = [];
  const waiters = [];
  return {
    emit(event) {
      events.push(event);
      for (let index = waiters.length - 1; index >= 0; index -= 1) {
        const waiter = waiters[index];
        if (!waiter.predicate(event)) continue;
        waiters.splice(index, 1);
        waiter.resolve(event);
      }
    },
    wait(predicate) {
      const existing = events.find(predicate);
      if (existing) return Promise.resolve(existing);
      return new Promise((resolve) => waiters.push({ predicate, resolve }));
    },
    events,
  };
}

test("background run hands off, waits for owner reply, and fans in terminal output", async () => {
  const collector = eventCollector();
  let output = "";
  const runtime = new AuditRuntime(
    async (_runId, _spec, _input, handoff) => ({
      async prompt() {
        const reply = await handoff("baseline evidence established");
        assert.equal(reply, "continue to final assessment");
        output = "IIS IMPLEMENTATION AUDITOR RESULT\nTerminal Status: COMPLETED\n";
      },
      async abort() {},
      dispose() {},
      finalText: () => output,
    }),
    collector.emit,
  );

  const started = runtime.start(spec(), null);
  assert.equal(started.status, "STARTING");
  const handoff = await collector.wait((event) => event.type === "HANDOFF");
  assert.equal(handoff.run.status, "WAITING_REPLY");
  assert.throws(() => runtime.fanIn([started.runId]), /fan-in incomplete/);

  const resumed = runtime.reply(started.runId, handoff.sequence, "continue to final assessment");
  assert.equal(resumed.status, "RUNNING");
  const terminal = await collector.wait((event) => event.type === "TERMINAL");
  assert.equal(terminal.run.status, "COMPLETED");
  assert.equal(runtime.fanIn([started.runId])[0].status, "COMPLETED");
  assert.deepEqual(
    collector.events.map((event) => event.type),
    ["STARTING", "RUNNING", "HANDOFF", "RESUMED", "TERMINAL", "FAN_IN_COMPLETE"],
  );
  const fanIn = collector.events.at(-1);
  assert.equal(fanIn.runs.length, 1);
  assert.equal(fanIn.runs[0].runId, started.runId);
});

test("wrong handoff sequence is rejected without releasing the auditor", async () => {
  const collector = eventCollector();
  const runtime = new AuditRuntime(
    async (_runId, _spec, _input, handoff) => ({
      async prompt() {
        await handoff("evidence");
      },
      async abort() {},
      dispose() {},
      finalText: () => "Terminal Status: COMPLETED\n",
    }),
    collector.emit,
  );

  const started = runtime.start(spec(), null);
  const handoff = await collector.wait((event) => event.type === "HANDOFF");
  assert.throws(
    () => runtime.reply(started.runId, handoff.sequence + 1, "continue"),
    /handoff sequence mismatch/,
  );
  await runtime.cancel(started.runId, "test cleanup");
});

test("cancellation rejects a waiting handoff and emits one terminal result", async () => {
  const collector = eventCollector();
  let aborted = false;
  const runtime = new AuditRuntime(
    async (_runId, _spec, _input, handoff) => ({
      async prompt() {
        await handoff("need owner direction");
      },
      async abort() {
        aborted = true;
      },
      dispose() {},
      finalText: () => "",
    }),
    collector.emit,
  );

  const started = runtime.start(spec(), null);
  await collector.wait((event) => event.type === "HANDOFF");
  const cancelled = await runtime.cancel(started.runId, "owner stopped work");
  assert.equal(cancelled.status, "CANCELLED");
  assert.equal(aborted, true);
  assert.equal(runtime.fanIn([started.runId])[0].status, "CANCELLED");
  const terminals = collector.events.filter((event) => event.type === "TERMINAL");
  assert.equal(terminals.length, 1);
});

test("missing terminal status is a failed attributable result", async () => {
  const collector = eventCollector();
  const runtime = new AuditRuntime(
    async () => ({
      async prompt() {},
      async abort() {},
      dispose() {},
      finalText: () => "review text without the terminal contract",
    }),
    collector.emit,
  );

  const started = runtime.start(spec(), null);
  const terminal = await collector.wait((event) => event.type === "TERMINAL");
  assert.equal(terminal.run.status, "FAILED");
  assert.match(terminal.run.error, /no valid terminal status/);
  assert.equal(runtime.fanIn([started.runId])[0].status, "FAILED");
});

test("verification auditor stays role-isolated through handoff and terminal fan-in", async () => {
  const collector = eventCollector();
  let output = "";
  const runtime = new AuditRuntime(
    async (_runId, received, _input, handoff) => ({
      async prompt() {
        assert.equal(received.role, "verification");
        const reply = await handoff("AC-2 initial-state evidence is visible");
        assert.match(reply, /authoritative execution/);
        output = "IIS VERIFICATION AUDITOR RESULT\nTerminal Status: COMPLETED\n";
      },
      async abort() {},
      dispose() {},
      finalText: () => output,
    }),
    collector.emit,
  );

  const started = runtime.start({ ...spec("AC-2"), role: "verification" }, null);
  const handoff = await collector.wait((event) => event.type === "HANDOFF");
  assert.equal(handoff.run.role, "verification");
  runtime.reply(started.runId, handoff.sequence, "continue authoritative execution");
  const terminal = await collector.wait((event) => event.type === "TERMINAL");
  assert.equal(terminal.run.role, "verification");
  assert.equal(runtime.fanIn([started.runId])[0].status, "COMPLETED");
});

test("runs are isolated by unique ids and shutdown contains every active session", async () => {
  const collector = eventCollector();
  const gates = new Map();
  let abortCount = 0;
  const runtime = new AuditRuntime(
    async (runId) => {
      const gate = deferred();
      gates.set(runId, gate);
      return {
        async prompt() {
          await gate.promise;
        },
        async abort() {
          abortCount += 1;
          gate.reject(new Error("aborted"));
        },
        dispose() {},
        finalText: () => "Terminal Status: COMPLETED\n",
      };
    },
    collector.emit,
  );

  const first = runtime.start(spec("slot-a"), null);
  const second = runtime.start(spec("slot-b"), null);
  assert.notEqual(first.runId, second.runId);
  await new Promise((resolve) => setImmediate(resolve));
  await runtime.shutdown();
  assert.equal(abortCount, 2);
  assert.deepEqual(
    runtime.fanIn([first.runId, second.runId]).map((run) => run.status),
    ["CANCELLED", "CANCELLED"],
  );
});
