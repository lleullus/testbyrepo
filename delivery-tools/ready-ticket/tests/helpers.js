import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
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
    schema: "iis-plan-review/v2",
    project_root: root,
    plans: [{ path: plan, sha256: hashBytes(fs.readFileSync(plan)) }],
    contracts: [{ ticket_path: ticket, ticket_sha256: authority.ticket_sha256, authority_digest: authority.authority_digest }],
    review_origin: { reviewer: "fixture-independent-invocation", evidence_reference: "fixture-byte-pairing-only" },
    decisions: [{ ticket_path: ticket, decision: "ADMIT", rationale: "fixture", start_scope: "cli.js", projection: { status: "preserved", basis: "CLI outcome is owned by this Ticket." }, findings: [], conditions: [] }],
  };
  fs.writeFileSync(review, JSON.stringify(reviewData));
  return { base, root, work, ticket, plan, review, behavior, stable, effect, validatorPath, authority, reviewData };
}

export async function materializeReadyBundle(base, mutate = () => {}) {
  const sourceRoot = fileURLToPath(new URL("../", import.meta.url));
  const bundleId = hashBytes(`${base}:${crypto.randomUUID()}`);
  const release = path.join(base, "releases", bundleId);
  const relatives = [
    "package.json",
    ...fs.readdirSync(sourceRoot).filter(name => name.endsWith(".js")).map(name => name),
    ...fs.readdirSync(path.join(sourceRoot, "src")).filter(name => name.endsWith(".js")).map(name => `src/${name}`),
  ].sort();
  const files = {};
  for (const packageRelative of relatives) {
    const source = path.join(sourceRoot, packageRelative);
    const target = path.join(release, "delivery-tools/ready-ticket", packageRelative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    const bytes = fs.readFileSync(source);
    const mode = fs.statSync(source).mode & 0o555;
    fs.writeFileSync(target, bytes, { mode });
    fs.chmodSync(target, mode);
    files[`delivery-tools/ready-ticket/${packageRelative}`] = { sha256: hashBytes(bytes), mode };
  }
  const repository = path.resolve(sourceRoot, "../..");
  function copyMember(relative) {
    const source = path.join(repository, relative);
    const stat = fs.statSync(source);
    if (stat.isDirectory()) {
      for (const entry of fs.readdirSync(source)) {
        if (entry !== "__pycache__") copyMember(`${relative}/${entry}`);
      }
      return;
    }
    const target = path.join(release, relative);
    const bytes = fs.readFileSync(source);
    const mode = stat.mode & 0o555;
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, bytes, { mode });
    fs.chmodSync(target, mode);
    files[relative] = { sha256: hashBytes(bytes), mode };
  }
  for (const relative of ["matt", "product-thesis", "scope-shaper", "iis_path_contract.py", "iis-workflow/SKILL.md", "companion-skills/ready-ticket-plan", "companion-skills/ready-ticket-implement", "companion-skills/ready-ticket-verify", "companion-skills/ready-ticket-coverage"]) copyMember(relative);
  const manifest = {
    schema: "iis-bundle/v2",
    protocol: 2,
    family: "ready-boundary-tools",
    bundle_id: bundleId,
    files,
  };
  mutate({ release, manifest });
  const manifestPath = path.join(release, "bundle.json");
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, { mode: 0o444 });
  fs.chmodSync(manifestPath, 0o444);
  const specifier = pathToFileURL(path.join(release, "delivery-tools/ready-ticket/omp.js")).href;
  return { bundleId, release, validatorPath: path.join(release, "matt/skills/to-tickets/validate_ticket.py"), core: await import(pathToFileURL(path.join(release, "delivery-tools/ready-ticket/src/core.js")).href), module: await import(`${specifier}?fixture=${crypto.randomUUID()}`) };
}
