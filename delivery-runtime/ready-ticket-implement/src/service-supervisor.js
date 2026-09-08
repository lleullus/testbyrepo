import { spawn } from "node:child_process";
import { validateMutationRequest } from "./argv-policy.js";

export class ManagedServiceRegistry {
  constructor({ lifecycle }) {
    this.lifecycle = lifecycle;
    this.children = new Map();
  }

  start(executionId, ownerSessionId, request) {
    const state = this.lifecycle.status(executionId);
    if (state.session_id !== ownerSessionId) throw new Error("only the Ready execution owner may start a managed service");
    if (state.phase !== "ACTIVE") throw new Error(`managed service requires ACTIVE execution; found ${state.phase}`);
    if (state.worker_inactive) throw new Error("suspended worker cannot start a managed service");
    if (state.active_operation) throw new Error(`Ready execution already has active guarded operation ${state.active_operation.tool_call_id}`);
    if (state.managed_service || this.children.has(executionId)) throw new Error("Ready execution already owns a managed service");

    const { argv } = validateMutationRequest({ version: request?.version, argv: request?.argv });
    const child = spawn(argv[0], argv.slice(1), {
      cwd: state.project_root,
      shell: false,
      detached: process.platform !== "win32",
      stdio: ["ignore", "pipe", "pipe"],
    });
    child.stdout?.resume();
    child.stderr?.resume();
    this.children.set(executionId, child);

    state.managed_service = {
      pid: child.pid,
      argv,
      owner_session_id: ownerSessionId,
      started_at: new Date().toISOString(),
    };
    state.updated_at = new Date().toISOString();
    this.lifecycle.store.writeExecution(state);

    const clear = () => {
      this.children.delete(executionId);
      const current = this.lifecycle.store.readExecution(executionId);
      if (current?.managed_service?.pid === child.pid) {
        current.managed_service = null;
        current.updated_at = new Date().toISOString();
        this.lifecycle.store.writeExecution(current);
      }
    };
    child.once("close", clear);
    child.once("error", clear);
    return state.managed_service;
  }

  async stop(executionId, requesterSessionId) {
    const state = this.lifecycle.status(executionId);
    if (state.session_id !== requesterSessionId && state.parent_session_id !== requesterSessionId) {
      throw new Error("only the bound Ready worker or parent may stop the managed service");
    }
    const service = state.managed_service;
    if (!service) return null;
    const child = this.children.get(executionId);
    if (!child) throw new Error("managed service handle is unavailable; prove external containment before closing this execution");
    if (child.exitCode === null && child.signalCode === null) {
      const kill = signal => {
        try { if (process.platform !== "win32") process.kill(-child.pid, signal); else child.kill(signal); }
        catch (error) { if (error.code !== "ESRCH") throw error; }
      };
      const closed = new Promise(resolve => child.once("close", resolve));
      kill("SIGTERM");
      const escalation = setTimeout(() => kill("SIGKILL"), 2_000);
      escalation.unref?.();
      try { await closed; } finally { clearTimeout(escalation); }
    }
    this.children.delete(executionId);
    const current = this.lifecycle.status(executionId);
    current.managed_service = null;
    current.updated_at = new Date().toISOString();
    this.lifecycle.store.writeExecution(current);
    return service;
  }

  status(executionId) {
    return this.lifecycle.status(executionId).managed_service;
  }

  async cleanupSession(sessionId) {
    const session = this.lifecycle.sessionState(sessionId);
    if (!session?.execution_id) return;
    const state = this.lifecycle.store.readExecution(session.execution_id);
    if (!state?.managed_service || state.session_id !== sessionId) return;
    await this.stop(state.execution_id, sessionId);
  }
}
