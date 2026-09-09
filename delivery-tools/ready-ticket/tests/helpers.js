import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { bindAuthority, executeArgvNode, hashBytes } from "../src/core.js";

export async function fixture(t) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "iis-boundary-"));
  t.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const root = path.join(base, "project");
  const work = path.join(root, "docs/planning/work/runtime-boundary");
  const ticket = path.join(work, "tickets/TICKET-001.md");
  const plan = path.join(work, "plans/PLAN-001.md");
  const review = path.join(base, "review.json");
  const behavior = path.join(root, "docs/planning/behavior/contexts/cli.md");
  const stable = path.join(root, "cli.js");
  const effect = path.join(root, "runtime-state.json");
  for (const file of [ticket, plan, behavior]) fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(path.join(work, "SPEC.md"), `# Spec\n\nStatus: approved\nOwner: test\n\n## Verification Expectations\n\n- Outcome: observable result\n  Acceptance boundary: local CLI output\n  Trigger or inspection target: run CLI\n  Expected observable result: expected product output\n  Authoritative readback: CLI stdout\n  Disposition: Independent\n  Independent verification required: yes\n  Acceptance surface: Existing | local CLI output\n  External condition: None\n\n## Behavior Authorities\n\n- docs/planning/behavior/contexts/cli.md | Scope: behavior\n\n## Open Questions\n\nNone\n`);
  fs.writeFileSync(behavior, "# Behavior\n\nStatus: approved\n");
  fs.writeFileSync(ticket, `# Ticket\n\nStatus: ready\nParent-Spec: ../SPEC.md\nProject-Root: ${root}\nWorker:\nUI: no\n\n## Acceptance Criteria\n\n- expected product output\n\n## Scope\n\nlocal CLI output\n\n## Blockers\n\nNone\n\n## Verification\n\n- Parent outcome ordinal: 1\n  AC ordinals: 1\n  Behavior authority ordinals: 1\n  Initial state: clean input\n  Trigger or inspection target: run CLI\n  Acceptance boundary: local CLI output\n  Expected observable result: expected product output\n  Authoritative readback: CLI stdout\n  Decision boundary: stdout equals expected product output\n  Disposition: Independent\n  Independent verification required: yes\n  Acceptance surface: Existing | local CLI output\n  External condition: None\n\n## Behavior Authorities\n\n- docs/planning/behavior/contexts/cli.md | Scope: behavior\n`);
  fs.writeFileSync(plan, "# Method\n\nInspect ordinary CLI output; edit only cli.js.\n");
  fs.writeFileSync(stable, "console.log('expected product output');\n");
  fs.writeFileSync(effect, "{}\n");
  const validatorPath = fileURLToPath(new URL("../../../matt/skills/to-tickets/validate_ticket.py", import.meta.url));
  const authority = await bindAuthority({ projectRoot: root, ticketPath: ticket, validatorPath, executeArgv: executeArgvNode });
  const reviewData = {
    schema: "iis-plan-review/v1",
    project_root: root,
    plans: [{ path: plan, sha256: hashBytes(fs.readFileSync(plan)) }],
    contracts: [{ ticket_path: ticket, ticket_sha256: authority.ticket_sha256, authority_digest: authority.authority_digest }],
    review_origin: { reviewer: "fixture-independent-invocation", evidence_reference: "fixture-byte-pairing-only" },
    heuristic: { evidence_reference: "fixture-not-semantic-proof", disposition_summary: "test input" },
    decisions: [{ ticket_path: ticket, decision: "ADMIT", rationale: "fixture", start_scope: "cli.js", conditions: [] }],
  };
  fs.writeFileSync(review, JSON.stringify(reviewData));
  return { base, root, work, ticket, plan, review, behavior, stable, effect, validatorPath, authority, reviewData };
}
