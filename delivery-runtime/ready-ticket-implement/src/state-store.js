import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const STATE_SCHEMA_VERSION = 1;
const LOCK_STALE_MS = 30_000;

function normalize(value) {
  if (Array.isArray(value)) return value.map(normalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, normalize(value[key])]));
  }
  return value;
}

export function stableDigest(value) {
  return crypto.createHash("sha256").update(JSON.stringify(normalize(value))).digest("hex");
}

function defaultRoot() {
  if (process.env.IIS_READY_RUNTIME_DATA) return path.resolve(process.env.IIS_READY_RUNTIME_DATA);
  return path.join(os.homedir(), ".omp", "agent", "data", "iis-ready-runtime");
}

export class RuntimeStore {
  constructor(root = defaultRoot()) {
    this.root = path.resolve(root);
    this.executions = path.join(this.root, "executions");
    this.assignments = path.join(this.root, "assignments");
    this.locks = path.join(this.root, "locks");
    this.#ensureDirectories();
  }

  #ensureDirectories() {
    for (const directory of [this.root, this.executions, this.assignments, this.locks]) {
      fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
      try { fs.chmodSync(directory, 0o700); } catch {}
    }
  }

  #readJson(file) {
    try {
      const value = JSON.parse(fs.readFileSync(file, "utf8"));
      return value && typeof value === "object" ? value : null;
    } catch (error) {
      if (error?.code === "ENOENT") return null;
      throw error;
    }
  }

  #writeJson(file, payload) {
    this.#ensureDirectories();
    const value = {
      ...payload,
      schema_version: STATE_SCHEMA_VERSION,
      updated_at: payload.updated_at ?? new Date().toISOString(),
    };
    const temporary = path.join(path.dirname(file), `.${path.basename(file)}.${process.pid}.${crypto.randomBytes(6).toString("hex")}.tmp`);
    fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });
    fs.chmodSync(temporary, 0o600);
    fs.renameSync(temporary, file);
    return value;
  }

  #sessionPath(sessionId) {
    return path.join(this.executions, `session-${stableDigest(sessionId)}.json`);
  }

  #executionPath(executionId) {
    return path.join(this.executions, `${executionId}.json`);
  }

  #assignmentPath(assignmentId) {
    return path.join(this.assignments, `${assignmentId}.json`);
  }

  #activeTicketPath(projectRoot, ticketPath) {
    return path.join(this.executions, `active-${stableDigest({ project_root: path.resolve(projectRoot), ticket_path: path.resolve(ticketPath) })}.json`);
  }

  readSession(sessionId) {
    return this.#readJson(this.#sessionPath(sessionId));
  }

  writeSession(sessionId, state) {
    return this.#writeJson(this.#sessionPath(sessionId), { ...state, kind: "session", session_id: sessionId });
  }

  readExecution(executionId) {
    return this.#readJson(this.#executionPath(executionId));
  }

  writeExecution(state) {
    if (!state?.execution_id) throw new Error("Ready execution state requires execution_id");
    return this.#writeJson(this.#executionPath(state.execution_id), { ...state, kind: "execution" });
  }

  readAssignment(assignmentId) {
    return this.#readJson(this.#assignmentPath(assignmentId));
  }

  writeAssignment(state) {
    if (!state?.assignment_id) throw new Error("Ready assignment state requires assignment_id");
    return this.#writeJson(this.#assignmentPath(state.assignment_id), { ...state, kind: "assignment" });
  }

  readActiveTicket(projectRoot, ticketPath) {
    return this.#readJson(this.#activeTicketPath(projectRoot, ticketPath));
  }

  writeActiveTicket(projectRoot, ticketPath, state) {
    return this.#writeJson(this.#activeTicketPath(projectRoot, ticketPath), {
      ...state,
      kind: "active_ticket",
      project_root: path.resolve(projectRoot),
      ticket_path: path.resolve(ticketPath),
    });
  }

  clearActiveTicket(projectRoot, ticketPath, expectedIdentity = undefined) {
    const file = this.#activeTicketPath(projectRoot, ticketPath);
    const current = this.#readJson(file);
    if (!current) return false;
    if (expectedIdentity !== undefined && current.identity !== expectedIdentity) return false;
    try {
      fs.unlinkSync(file);
      return true;
    } catch (error) {
      if (error?.code === "ENOENT") return false;
      throw error;
    }
  }

  withLock(callback) {
    this.#ensureDirectories();
    const lockPath = path.join(this.locks, "state.lock");
    let descriptor;
    try {
      descriptor = fs.openSync(lockPath, "wx", 0o600);
      fs.writeFileSync(descriptor, JSON.stringify({ pid: process.pid, created_at: Date.now() }));
    } catch (error) {
      if (error?.code !== "EEXIST") throw error;
      let stale = false;
      try { stale = Date.now() - fs.statSync(lockPath).mtimeMs > LOCK_STALE_MS; } catch {}
      if (!stale) throw new Error("Ready runtime state lock is busy");
      try { fs.unlinkSync(lockPath); } catch {}
      descriptor = fs.openSync(lockPath, "wx", 0o600);
      fs.writeFileSync(descriptor, JSON.stringify({ pid: process.pid, created_at: Date.now() }));
    }
    try {
      return callback();
    } finally {
      try { fs.closeSync(descriptor); } finally {
        try { fs.unlinkSync(lockPath); } catch (error) { if (error?.code !== "ENOENT") throw error; }
      }
    }
  }
}
