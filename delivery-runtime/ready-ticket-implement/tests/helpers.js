import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { bindAuthority, RuntimeStore, ReadyLifecycle } from "../src/core.js";
import { hashBytes } from "../src/plan-binding.js";
const exec = promisify(execFile);
export async function executeArgv(argv, options = {}) {
  try { const result = await exec(argv[0], argv.slice(1), { cwd: options.cwd, timeout: options.timeout, signal: options.signal, maxBuffer: 8 * 1024 * 1024 }); return { exitCode: 0, terminationState: "settled", interrupted: false, ...result }; }
  catch (error) { return { exitCode: typeof error.code === "number" ? error.code : null, terminationState: error.killed ? "unknown" : "settled", interrupted: Boolean(error.killed), stdout: error.stdout ?? "", stderr: error.stderr ?? error.message }; }
}
export async function fixture(t, options = {}) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "iis-v2-"));
  t.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const root = path.join(base, "project"); fs.mkdirSync(root);
  const work = path.join(root, "docs/planning/work/runtime-boundary");
  const ticket = path.join(work, "tickets/TICKET-001.md"), plan = path.join(work, "plans/PLAN-001.md"), review = path.join(base, "review.json");
  const behavior = path.join(root, "docs/planning/behavior/contexts/cli.md");
  for (const file of [ticket, plan, behavior]) fs.mkdirSync(path.dirname(file), { recursive: true });
  const validatorPath = fileURLToPath(new URL("../../../matt/skills/to-tickets/validate_ticket.py", import.meta.url));
  fs.writeFileSync(path.join(work, "SPEC.md"), `# Spec\n\nStatus: approved\nOwner: test\n\n## Verification Expectations\n\n- Outcome: observable result\n  Acceptance boundary: local CLI output\n  Trigger or inspection target: run CLI\n  Expected observable result: expected product output\n  Authoritative readback: CLI stdout\n  Disposition: Independent\n  Independent verification required: yes\n  Acceptance surface: Existing | local CLI output\n  External condition: None\n\n## Behavior Authorities\n\n- docs/planning/behavior/contexts/cli.md | Scope: behavior\n\n## Open Questions\n\nNone\n`);
  fs.writeFileSync(behavior, "# Behavior\n\nStatus: approved\n");
  fs.writeFileSync(ticket, `# Ticket\n\nStatus: ready\nParent-Spec: ../SPEC.md\nProject-Root: ${root}\nWorker:\nUI: no\n\n## Acceptance Criteria\n\n- expected product output\n\n## Scope\n\nlocal CLI output\n\n## Blockers\n\nNone\n\n## Verification\n\n- Parent outcome ordinal: 1\n  AC ordinals: 1\n  Behavior authority ordinals: 1\n  Initial state: clean input\n  Trigger or inspection target: run CLI\n  Acceptance boundary: local CLI output\n  Expected observable result: expected product output\n  Authoritative readback: CLI stdout\n  Decision boundary: stdout equals expected product output\n  Disposition: Independent\n  Independent verification required: yes\n  Acceptance surface: Existing | local CLI output\n  External condition: None\n\n## Behavior Authorities\n\n- docs/planning/behavior/contexts/cli.md | Scope: behavior\n`);
  fs.writeFileSync(plan, "# Method\n\nInspect ordinary CLI output; edit only cli.js.\n");
  fs.writeFileSync(path.join(root, "cli.js"), "console.log('expected product output');\n");
  const initialized = await executeArgv(["git", "init"], { cwd: root });
  if (initialized.exitCode !== 0) throw new Error(initialized.stderr);
  const authority = await bindAuthority({ projectRoot: root, ticketPath: ticket, validatorPath, executeArgv });
  const reviewData = { schema: "iis-plan-review/v1", project_root: root, plans: [{ path: plan, sha256: hashBytes(fs.readFileSync(plan)) }], contracts: [{ ticket_path: ticket, ticket_sha256: authority.ticket_sha256, authority_digest: authority.authority_digest }], review_origin: { reviewer: "fixture-independent-invocation", evidence_reference: "fixture-byte-pairing-only" }, heuristic: { evidence_reference: "fixture-not-semantic-proof", disposition_summary: "test input" }, decisions: [{ ticket_path: ticket, decision: "ADMIT", rationale: "fixture", start_scope: "cli.js", conditions: [] }] };
  fs.writeFileSync(review, JSON.stringify(reviewData));
  const store = new RuntimeStore(path.join(base, "state"));
  const lifecycle = new ReadyLifecycle({ store, validatorPath, executeArgv, ...options });
  const input = { projectRoot: root, ticketPath: ticket, planReviewPath: review };
  return { base, root, ticket, plan, review, authority, reviewData, store, lifecycle, input, validatorPath };
}
