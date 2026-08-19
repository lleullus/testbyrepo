import { randomUUID } from "node:crypto";

export type AuditRole = "implementation" | "verification";
export type AuditRunStatus =
  | "STARTING"
  | "RUNNING"
  | "WAITING_REPLY"
  | "COMPLETED"
  | "BLOCKED"
  | "FAILED"
  | "CANCELLED";

export interface AuditRunSpec {
  role: AuditRole;
  assignment: string;
  task: string;
  cwd: string;
  model: string;
  thinking: string;
  oracleBrowser: boolean;
}

export interface AuditSession {
  prompt(task: string): Promise<void>;
  abort(): Promise<void>;
  dispose(): void;
  finalText(): string;
}

export interface AuditRunSnapshot {
  runId: string;
  role: AuditRole;
  assignment: string;
  status: AuditRunStatus;
  model: string;
  thinking: string;
  cwd: string;
  handoffSequence: number;
  finalOutput?: string;
  error?: string;
}

export type AuditRuntimeEvent =
  | { type: "HANDOFF"; run: AuditRunSnapshot; sequence: number; body: string }
  | { type: "TERMINAL"; run: AuditRunSnapshot };

export interface AuditSessionFactory<TSessionInput> {
  (
    runId: string,
    spec: AuditRunSpec,
    input: TSessionInput,
    handoff: (body: string) => Promise<string>,
  ): Promise<AuditSession>;
}

interface DeferredReply {
  sequence: number;
  resolve: (body: string) => void;
  reject: (error: Error) => void;
}

interface AuditRunRecord<TSessionInput> {
  runId: string;
  spec: AuditRunSpec;
  input: TSessionInput;
  status: AuditRunStatus;
  handoffSequence: number;
  pendingReply?: DeferredReply;
  session?: AuditSession;
  finalOutput?: string;
  error?: string;
  terminalEmitted: boolean;
}

const TERMINAL_STATES = new Set<AuditRunStatus>([
  "COMPLETED",
  "BLOCKED",
  "FAILED",
  "CANCELLED",
]);

function terminalStatusFromOutput(output: string): AuditRunStatus {
  const match = output.match(
    /(?:^|\n)Terminal Status:\s*(COMPLETED|BLOCKED|FAILED|CANCELLED)\s*(?:\n|$)/i,
  );
  if (!match) return "FAILED";
  return match[1].toUpperCase() as AuditRunStatus;
}

export class AuditRuntime<TSessionInput> {
  private readonly runs = new Map<string, AuditRunRecord<TSessionInput>>();
  private readonly createSession: AuditSessionFactory<TSessionInput>;
  private readonly emit: (event: AuditRuntimeEvent) => void;

  constructor(
    createSession: AuditSessionFactory<TSessionInput>,
    emit: (event: AuditRuntimeEvent) => void,
  ) {
    this.createSession = createSession;
    this.emit = emit;
  }

  start(spec: AuditRunSpec, input: TSessionInput): AuditRunSnapshot {
    if (!spec.assignment.trim()) throw new Error("assignment is required");
    if (!spec.task.trim()) throw new Error("task is required");
    if (!spec.cwd.trim()) throw new Error("cwd is required");
    if (!spec.model.trim()) throw new Error("model is required");
    if (!spec.thinking.trim()) throw new Error("thinking is required");

    const runId = `iis-audit-${randomUUID()}`;
    const record: AuditRunRecord<TSessionInput> = {
      runId,
      spec,
      input,
      status: "STARTING",
      handoffSequence: 0,
      terminalEmitted: false,
    };
    this.runs.set(runId, record);
    void this.execute(record);
    return this.snapshot(record);
  }

  reply(runId: string, sequence: number, body: string): AuditRunSnapshot {
    const record = this.requireRun(runId);
    if (record.status !== "WAITING_REPLY" || !record.pendingReply) {
      throw new Error(`run ${runId} is not waiting for a reply`);
    }
    if (record.pendingReply.sequence !== sequence) {
      throw new Error(
        `handoff sequence mismatch for ${runId}: expected ${record.pendingReply.sequence}, got ${sequence}`,
      );
    }
    if (!body.trim()) throw new Error("reply body is required");

    const pending = record.pendingReply;
    record.pendingReply = undefined;
    record.status = "RUNNING";
    pending.resolve(body);
    return this.snapshot(record);
  }

  async cancel(runId: string, reason: string): Promise<AuditRunSnapshot> {
    const record = this.requireRun(runId);
    if (TERMINAL_STATES.has(record.status)) return this.snapshot(record);

    record.status = "CANCELLED";
    record.error = reason.trim() || "cancelled by owner";
    if (record.pendingReply) {
      record.pendingReply.reject(new Error(record.error));
      record.pendingReply = undefined;
    }
    if (record.session) await record.session.abort();
    this.emitTerminal(record);
    return this.snapshot(record);
  }

  fanIn(runIds: string[]): AuditRunSnapshot[] {
    if (runIds.length === 0) throw new Error("at least one run id is required");
    const records = [...new Set(runIds)].map((runId) => this.requireRun(runId));
    const unfinished = records.filter((record) => !TERMINAL_STATES.has(record.status));
    if (unfinished.length > 0) {
      throw new Error(
        `fan-in incomplete: ${unfinished.map((record) => `${record.runId}:${record.status}`).join(", ")}`,
      );
    }
    return records.map((record) => this.snapshot(record));
  }

  async shutdown(reason = "owner session shutdown"): Promise<void> {
    const active = [...this.runs.values()].filter((record) => !TERMINAL_STATES.has(record.status));
    await Promise.all(active.map((record) => this.cancel(record.runId, reason)));
  }

  private async execute(record: AuditRunRecord<TSessionInput>): Promise<void> {
    try {
      const session = await this.createSession(
        record.runId,
        record.spec,
        record.input,
        (body) => this.openHandoff(record.runId, body),
      );
      record.session = session;
      if (record.status === "CANCELLED") {
        await session.abort();
        return;
      }

      record.status = "RUNNING";
      await session.prompt(record.spec.task);
      if ((record.status as AuditRunStatus) === "CANCELLED") return;

      record.finalOutput = session.finalText().trim();
      record.status = terminalStatusFromOutput(record.finalOutput);
      if (record.status === "FAILED" && !record.finalOutput.match(/Terminal Status:/i)) {
        record.error = "auditor returned no valid terminal status";
      }
      this.emitTerminal(record);
    } catch (error) {
      if (record.status !== "CANCELLED") {
        record.status = "FAILED";
        record.error = error instanceof Error ? error.message : String(error);
        this.emitTerminal(record);
      }
    } finally {
      record.session?.dispose();
    }
  }

  private openHandoff(runId: string, body: string): Promise<string> {
    const record = this.requireRun(runId);
    if (record.status !== "RUNNING") {
      throw new Error(`run ${runId} cannot open a handoff from ${record.status}`);
    }
    if (!body.trim()) throw new Error("handoff body is required");

    record.handoffSequence += 1;
    record.status = "WAITING_REPLY";
    const sequence = record.handoffSequence;
    const reply = new Promise<string>((resolve, reject) => {
      record.pendingReply = { sequence, resolve, reject };
    });
    this.emit({ type: "HANDOFF", run: this.snapshot(record), sequence, body });
    return reply;
  }

  private emitTerminal(record: AuditRunRecord<TSessionInput>): void {
    if (record.terminalEmitted) return;
    record.terminalEmitted = true;
    this.emit({ type: "TERMINAL", run: this.snapshot(record) });
  }

  private requireRun(runId: string): AuditRunRecord<TSessionInput> {
    const record = this.runs.get(runId);
    if (!record) throw new Error(`unknown audit run: ${runId}`);
    return record;
  }

  private snapshot(record: AuditRunRecord<TSessionInput>): AuditRunSnapshot {
    return {
      runId: record.runId,
      role: record.spec.role,
      assignment: record.spec.assignment,
      status: record.status,
      model: record.spec.model,
      thinking: record.spec.thinking,
      cwd: record.spec.cwd,
      handoffSequence: record.handoffSequence,
      ...(record.finalOutput ? { finalOutput: record.finalOutput } : {}),
      ...(record.error ? { error: record.error } : {}),
    };
  }
}
