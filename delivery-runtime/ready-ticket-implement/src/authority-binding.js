import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

function sha256File(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function existingRealpath(file, label) {
  let resolved;
  try {
    resolved = fs.realpathSync(file);
  } catch (error) {
    throw new Error(`${label} does not exist: ${file}`);
  }
  if (!fs.statSync(resolved).isFile() && label !== "Project Root") {
    throw new Error(`${label} is not a file: ${resolved}`);
  }
  return resolved;
}

function canonicalProjectRoot(projectRoot) {
  const resolved = fs.realpathSync(projectRoot);
  if (!fs.statSync(resolved).isDirectory()) throw new Error(`Project Root is not a directory: ${resolved}`);
  return resolved;
}

export function isInsideProject(projectRoot, target) {
  const relative = path.relative(projectRoot, target);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function requireInside(projectRoot, target, label) {
  if (!isInsideProject(projectRoot, target)) throw new Error(`${label} is outside Project Root: ${target}`);
  return target;
}

function metadataValue(text, label) {
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
  const values = rawValue
    .split(" | ")
    .map(value => value.trim())
    .filter(Boolean);
  if (values.length < 1 || values.length > 2) {
    throw new Error("Ticket Parent-Spec must contain one path or matching relative and absolute paths");
  }
  const resolved = values.map(value =>
    existingRealpath(resolveReference(path.dirname(ticketPath), value), "Parent Spec"),
  );
  if (resolved.some(value => value !== resolved[0])) {
    throw new Error("Ticket Parent-Spec paths do not identify the same file");
  }
  return resolved[0];
}

function parseBehaviorAuthorities(ticketText, projectRoot) {
  const body = section(ticketText, "Behavior Authorities");
  const authorities = [];
  for (const line of body.split(/\r?\n/)) {
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
  const ui = (metadataValue(ticketText, "UI") || "no").toLowerCase();
  if (ui !== "yes") return null;
  const parentText = fs.readFileSync(parentSpecPath, "utf8");
  const uiSection = section(parentText, "UI / UX");
  if (/^Not applicable\s*$/i.test(uiSection)) throw new Error("Ticket declares UI: yes but Parent Spec UI / UX is Not applicable");

  const parentDirectory = path.dirname(parentSpecPath);
  const authoredPaths = uiSection
    .split(/\r?\n/)
    .map(line => line.match(/^\s*-\s+(.+?)(?:\s+\|\s*Scope:\s*.+)?\s*$/)?.[1]?.trim())
    .filter(Boolean);
  const inlinePaths = [...uiSection.matchAll(/`([^`]+)`/g)].map(match => match[1].trim());
  for (const value of [...authoredPaths, ...inlinePaths]) {
    const candidate = resolveReference(parentDirectory, value);
    if (fs.existsSync(candidate)) return existingRealpath(candidate, "UI Authority");
  }
  if (/this Spec itself|이 Spec 자체/i.test(uiSection)) return parentSpecPath;

  const excluded = new Set([parentSpecPath, ...behaviorAuthorities.map(item => item.path)]);
  return { unresolved: true, excluded };
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
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
}

export function resolveCanonicalValidator(validatorPath) {
  return existingRealpath(validatorPath ?? path.join(repoRootFromModule(), "matt/skills/to-tickets/validate_ticket.py"), "Ticket validator");
}

export async function validateTicket(validator, ticketPath, projectRoot, executeArgv) {
  if (!executeArgv) throw new Error("CAPABILITY_UNAVAILABLE: canonical validator requires structured executeArgv");
  const result = await executeArgv(["python3", "-B", validator, ticketPath], { cwd: projectRoot, timeout: 30000 });
  if (result.interrupted || result.terminationState !== "settled" || result.exitCode !== 0 || String(result.stdout ?? "").trim() !== "VALID") {
    throw new Error(`canonical Ticket validator did not return exact VALID: ${result.stderr ?? result.stdout ?? result.outputRef ?? "no output"}`);
  }
}

export async function bindAuthority({ ticketPath, projectRoot, allowedStatuses = ["ready"], validatorPath, executeArgv, runtimeProtocol = "iis-ready/v2", bundleIdentity = "source" }) {
  const canonicalRoot = canonicalProjectRoot(projectRoot);
  const canonicalTicket = existingRealpath(ticketPath, "Ticket");
  requireInside(canonicalRoot, canonicalTicket, "Ticket");
  const ticketText = fs.readFileSync(canonicalTicket, "utf8");
  const status = metadataValue(ticketText, "Status");
  const admittedStatuses = new Set(allowedStatuses);
  if (!admittedStatuses.has(status)) {
    throw new Error(`Ticket status must be one of ${[...admittedStatuses].join(", ")}; found ${status ?? "missing"}`);
  }
  const authoredProjectRoot = metadataValue(ticketText, "Project-Root");
  if (authoredProjectRoot !== canonicalRoot) {
    throw new Error(`Ticket Project-Root does not match requested Project Root: ${authoredProjectRoot ?? "missing"}`);
  }

  const validator = resolveCanonicalValidator(validatorPath);
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

  const authorityDigest = crypto.createHash("sha256").update(JSON.stringify({ protectedArtifacts, runtimeProtocol, bundleIdentity })).digest("hex");
  return {
    project_root: canonicalRoot,
    ticket_path: canonicalTicket,
    ticket_sha256: protectedArtifacts[0].sha256,
    ticket_status_at_start: status,
    parent_spec_path: parentSpec,
    parent_spec_sha256: sha256File(parentSpec),
    behavior_authorities: behaviorAuthorities,
    ui_authority: uiAuthority,
    validator_path: validator,
    validator_sha256: sha256File(validator),
    runtime_protocol: runtimeProtocol,
    bundle_identity: bundleIdentity,
    authority_digest: authorityDigest,
    protected_artifacts: protectedArtifacts,
  };
}

export async function checkAuthorityCurrentness(binding) {
  const changed = [];
  for (const artifact of binding.protected_artifacts || []) {
    let actual = null;
    try {
      actual = sha256File(artifact.path);
    } catch {
      actual = null;
    }
    if (actual !== artifact.sha256) changed.push({ kind: artifact.kind, path: artifact.path, expected: artifact.sha256, actual });
  }
  return { current: changed.length === 0, changed };
}
