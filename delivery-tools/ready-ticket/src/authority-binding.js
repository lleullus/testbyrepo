import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const BOUNDARY_PROTOCOL = "iis-ready-boundary/v1";
export const hashBytes = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
export const sha256File = file => hashBytes(fs.readFileSync(file));

function existingRealpath(file, label, { directory = false } = {}) {
  let resolved;
  try {
    resolved = fs.realpathSync(file);
  } catch {
    throw new Error(`${label} does not exist: ${file}`);
  }
  const stat = fs.statSync(resolved);
  if (directory ? !stat.isDirectory() : !stat.isFile()) {
    throw new Error(`${label} is not a ${directory ? "directory" : "file"}: ${resolved}`);
  }
  return resolved;
}

export function canonicalProjectRoot(projectRoot) {
  return existingRealpath(projectRoot, "Project Root", { directory: true });
}

export function isInsideProject(projectRoot, target) {
  const relative = path.relative(projectRoot, target);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function requireInside(projectRoot, target, label) {
  if (!isInsideProject(projectRoot, target)) throw new Error(`${label} is outside Project Root: ${target}`);
  return target;
}

export function metadataValue(text, label) {
  const match = text.match(new RegExp(`^${label}:\\s*(.+?)\\s*$`, "mi"));
  return match ? match[1].trim() : null;
}

function section(text, heading) {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = text.match(new RegExp(`^##\\s+${escaped}\\s*$([\\s\\S]*?)(?=^##\\s+|(?![\\s\\S]))`, "mi"));
  return match ? match[1].trim() : "";
}

function resolveReference(baseDirectory, value) {
  const cleaned = value.trim().replace(/^`|`$/g, "");
  return path.isAbsolute(cleaned) ? cleaned : path.resolve(baseDirectory, cleaned);
}

function resolveParentSpec(ticketPath, rawValue) {
  const values = rawValue.split(" | ").map(value => value.trim()).filter(Boolean);
  if (values.length < 1 || values.length > 2) {
    throw new Error("Ticket Parent-Spec must contain one path or matching relative and absolute paths");
  }
  const resolved = values.map(value => existingRealpath(resolveReference(path.dirname(ticketPath), value), "Parent Spec"));
  if (resolved.some(value => value !== resolved[0])) throw new Error("Ticket Parent-Spec paths do not identify the same file");
  return resolved[0];
}

function parseBehaviorAuthorities(ticketText, projectRoot) {
  const authorities = [];
  for (const line of section(ticketText, "Behavior Authorities").split(/\r?\n/)) {
    const match = line.match(/^\s*-\s+(.+?)\s+\|\s*Scope:\s*(.+?)\s*$/);
    if (!match) continue;
    const target = existingRealpath(path.resolve(projectRoot, match[1].trim()), "Behavior Authority");
    requireInside(projectRoot, target, "Behavior Authority");
    authorities.push({ path: target, scope: match[2].trim(), sha256: sha256File(target) });
  }
  return authorities;
}

function parseReferencePaths(ticketText, ticketDirectory) {
  return section(ticketText, "References")
    .split(/\r?\n/)
    .map(line => line.match(/^\s*-\s+(.+?)\s*$/)?.[1]?.trim())
    .filter(Boolean)
    .map(value => resolveReference(ticketDirectory, value));
}

function extractUiAuthority(ticketText, parentSpecPath, behaviorAuthorities) {
  if ((metadataValue(ticketText, "UI") || "no").toLowerCase() !== "yes") return null;
  const parentText = fs.readFileSync(parentSpecPath, "utf8");
  const uiSection = section(parentText, "UI / UX");
  if (/^Not applicable\s*$/i.test(uiSection)) throw new Error("Ticket declares UI: yes but Parent Spec UI / UX is Not applicable");
  const parentDirectory = path.dirname(parentSpecPath);
  const authoredPaths = uiSection.split(/\r?\n/).map(line => line.match(/^\s*-\s+(.+?)(?:\s+\|\s*Scope:\s*.+)?\s*$/)?.[1]?.trim()).filter(Boolean);
  const inlinePaths = [...uiSection.matchAll(/`([^`]+)`/g)].map(match => match[1].trim());
  for (const value of [...authoredPaths, ...inlinePaths]) {
    const candidate = resolveReference(parentDirectory, value);
    if (fs.existsSync(candidate)) return existingRealpath(candidate, "UI Authority");
  }
  if (/this Spec itself|이 Spec 자체/i.test(uiSection)) return parentSpecPath;
  return { unresolved: true, excluded: new Set([parentSpecPath, ...behaviorAuthorities.map(item => item.path)]) };
}

function resolveUiAuthority(ticketText, ticketPath, parentSpecPath, behaviorAuthorities, projectRoot) {
  const parsed = extractUiAuthority(ticketText, parentSpecPath, behaviorAuthorities);
  if (!parsed) return null;
  if (typeof parsed === "string") {
    const resolved = existingRealpath(parsed, "UI Authority");
    requireInside(projectRoot, resolved, "UI Authority");
    return { path: resolved, sha256: sha256File(resolved) };
  }
  for (const raw of parseReferencePaths(ticketText, path.dirname(ticketPath))) {
    if (!fs.existsSync(raw)) continue;
    const candidate = existingRealpath(raw, "Reference");
    if (parsed.excluded.has(candidate)) continue;
    requireInside(projectRoot, candidate, "UI Authority");
    return { path: candidate, sha256: sha256File(candidate) };
  }
  throw new Error("Ticket declares UI: yes but no canonical UI Authority could be resolved from Parent Spec or Ticket References");
}

function repoRootFromModule() {
  return path.resolve(path.dirname(fs.realpathSync(fileURLToPath(import.meta.url))), "..", "..", "..");
}

export function resolveCanonicalValidator(validatorPath) {
  return existingRealpath(validatorPath ?? path.join(repoRootFromModule(), "matt/skills/to-tickets/validate_ticket.py"), "Ticket validator");
}

function bundleNavigation(validator, bundleIdentity) {
  const root = repoRootFromModule();
  const documents = [
    "iis-workflow/SKILL.md",
    "matt/skills/to-spec/SKILL.md",
    "matt/skills/to-tickets/SKILL.md",
    "companion-skills/ready-ticket-plan/SKILL.md",
    "companion-skills/ready-ticket-plan/references/plan.md",
    "companion-skills/ready-ticket-plan/references/review.md",
    "companion-skills/ready-ticket-implement/SKILL.md",
    "companion-skills/ready-ticket-implement/references/implement.md",
    "companion-skills/ready-ticket-verify/SKILL.md",
    "companion-skills/ready-ticket-verify/references/verify.md",
    "companion-skills/ready-ticket-coverage/SKILL.md",
  ];
  if (bundleIdentity !== "source") {
    const invalid = detail => { throw new Error(`READY_BUNDLE_INVALID: ${detail}`); };
    const manifest = JSON.parse(fs.readFileSync(path.join(root, "bundle.json"), "utf8"));
    if (manifest.schema !== "iis-bundle/v2" || manifest.protocol !== 2 || manifest.family !== "ready-boundary-tools" ||
        manifest.bundle_id !== bundleIdentity || path.basename(root) !== bundleIdentity) invalid("loaded release identity mismatch");
    const relativeValidator = "matt/skills/to-tickets/validate_ticket.py";
    if (validator !== path.join(root, relativeValidator)) invalid("validator must belong to the loaded release");
    for (const relative of [relativeValidator, ...documents]) {
      const file = path.join(root, relative);
      const expected = manifest.files?.[relative];
      const stat = fs.lstatSync(file);
      if (!stat.isFile() || stat.isSymbolicLink() || fs.realpathSync(file) !== file || !expected ||
          sha256File(file) !== expected.sha256 || (stat.mode & 0o777) !== expected.mode) invalid(`role/validator file drift: ${relative}`);
    }
  }
  return { bundle_root: root, role_document_paths: documents.map(relative => path.join(root, relative)) };
}

export async function validateTicket(validator, ticketPath, projectRoot, executeArgv) {
  if (!executeArgv) throw new Error("CAPABILITY_UNAVAILABLE: canonical validator requires structured executeArgv");
  const result = await executeArgv(["python3", "-B", validator, ticketPath], { cwd: projectRoot, timeout: 30000 });
  if (result.interrupted || result.terminationState !== "settled" || result.exitCode !== 0 || String(result.stdout ?? "").trim() !== "VALID") {
    throw new Error(`canonical Ticket validator did not return exact VALID: ${result.stderr ?? result.stdout ?? "no output"}`);
  }
}

export async function bindAuthority({
  ticketPath,
  projectRoot,
  allowedStatuses = ["ready"],
  validatorPath,
  executeArgv,
  boundaryProtocol = BOUNDARY_PROTOCOL,
  bundleIdentity = "source",
}) {
  const canonicalRoot = canonicalProjectRoot(projectRoot);
  const canonicalTicket = existingRealpath(ticketPath, "Ticket");
  requireInside(canonicalRoot, canonicalTicket, "Ticket");
  const ticketText = fs.readFileSync(canonicalTicket, "utf8");
  const status = metadataValue(ticketText, "Status");
  const admittedStatuses = new Set(allowedStatuses);
  if (!admittedStatuses.has(status)) throw new Error(`Ticket status must be one of ${[...admittedStatuses].join(", ")}; found ${status ?? "missing"}`);
  const authoredProjectRoot = metadataValue(ticketText, "Project-Root");
  if (authoredProjectRoot !== canonicalRoot) throw new Error(`Ticket Project-Root does not match requested Project Root: ${authoredProjectRoot ?? "missing"}`);

  const validator = resolveCanonicalValidator(validatorPath);
  const navigation = bundleNavigation(validator, bundleIdentity);
  await validateTicket(validator, canonicalTicket, canonicalRoot, executeArgv);
  const parentValue = metadataValue(ticketText, "Parent-Spec");
  if (!parentValue) throw new Error("Ticket Parent-Spec metadata is missing");
  const parentSpec = resolveParentSpec(canonicalTicket, parentValue);
  requireInside(canonicalRoot, parentSpec, "Parent Spec");
  const behaviorAuthorities = parseBehaviorAuthorities(ticketText, canonicalRoot);
  const uiAuthority = resolveUiAuthority(ticketText, canonicalTicket, parentSpec, behaviorAuthorities, canonicalRoot);
  const protectedArtifacts = [
    { path: canonicalTicket, sha256: sha256File(canonicalTicket), kind: "ticket" },
    { path: parentSpec, sha256: sha256File(parentSpec), kind: "parent_spec" },
    ...behaviorAuthorities.map(item => ({ path: item.path, sha256: item.sha256, kind: "behavior" })),
    ...(uiAuthority ? [{ path: uiAuthority.path, sha256: uiAuthority.sha256, kind: "ui" }] : []),
    { path: validator, sha256: sha256File(validator), kind: "validator" },
  ];
  const authorityDigest = hashBytes(JSON.stringify({ protected_artifacts: protectedArtifacts, boundary_protocol: boundaryProtocol, bundle_identity: bundleIdentity }));
  return {
    project_root: canonicalRoot,
    ticket_path: canonicalTicket,
    ticket_sha256: protectedArtifacts[0].sha256,
    ticket_status_at_capture: status,
    parent_spec_path: parentSpec,
    parent_spec_sha256: sha256File(parentSpec),
    behavior_authorities: behaviorAuthorities,
    ui_authority: uiAuthority,
    validator_path: validator,
    validator_sha256: sha256File(validator),
    boundary_protocol: boundaryProtocol,
    bundle_identity: bundleIdentity,
    ...navigation,
    authority_digest: authorityDigest,
    protected_artifacts: protectedArtifacts,
  };
}

export async function checkAuthorityCurrentness(binding, { expectedTicketSha256 } = {}) {
  const changed = [];
  for (const artifact of binding.protected_artifacts || []) {
    let actual = null;
    try { actual = sha256File(artifact.path); } catch { actual = null; }
    const expected = artifact.kind === "ticket" && expectedTicketSha256 ? expectedTicketSha256 : artifact.sha256;
    if (actual !== expected) changed.push({ kind: artifact.kind, path: artifact.path, expected, actual });
  }
  return { current: changed.length === 0, changed };
}
