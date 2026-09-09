import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  bindAuthority,
  canonicalProjectRoot,
  checkAuthorityCurrentness,
  hashBytes,
  isInsideProject,
} from "./authority-binding.js";

function canonicalPotentialPath(raw, root) {
  if (typeof raw !== "string" || !raw.trim()) throw new Error("verification path must be a non-empty string");
  let cursor = path.isAbsolute(raw) ? path.resolve(raw) : path.resolve(root, raw);
  const suffix = [];
  while (!fs.existsSync(cursor)) {
    const parent = path.dirname(cursor);
    if (parent === cursor) throw new Error(`cannot resolve verification path: ${raw}`);
    suffix.unshift(path.basename(cursor));
    cursor = parent;
  }
  const canonical = path.join(fs.realpathSync(cursor), ...suffix);
  if (!isInsideProject(root, canonical)) throw new Error(`verification path outside Project Root: ${canonical}`);
  return canonical;
}

function overlaps(a, b) {
  return isInsideProject(a, b) || isInsideProject(b, a);
}

function relativeKey(root, file) {
  return path.relative(root, file).split(path.sep).join("/") || ".";
}

export function fileIdentity(file) {
  try {
    const stat = fs.lstatSync(file);
    if (stat.isSymbolicLink()) return { kind: "symlink", target: fs.readlinkSync(file) };
    if (stat.isFile()) return { kind: "file", sha256: hashBytes(fs.readFileSync(file)), mode: stat.mode & 0o777 };
    if (stat.isDirectory()) return { kind: "directory", mode: stat.mode & 0o777 };
    return { kind: "other", mode: stat.mode & 0o777 };
  } catch (error) {
    if (error.code === "ENOENT") return { kind: "missing" };
    throw error;
  }
}

function collectSnapshot(root, file, manifest) {
  const identity = fileIdentity(file);
  manifest[relativeKey(root, file)] = identity;
  if (identity.kind !== "directory") return;
  for (const entry of fs.readdirSync(file).sort()) collectSnapshot(root, path.join(file, entry), manifest);
}

export function snapshotStableTargets(projectRoot, stableTargetPaths) {
  const manifest = {};
  for (const target of stableTargetPaths) collectSnapshot(projectRoot, target, manifest);
  return manifest;
}

function exactOutsideFile(file, projectRoot, label) {
  if (typeof file !== "string" || !path.isAbsolute(file)) throw new Error(`${label} must be an exact absolute path`);
  const canonical = fs.realpathSync(file);
  if (canonical !== file || !fs.statSync(canonical).isFile()) throw new Error(`${label} must be a canonical file`);
  if (isInsideProject(projectRoot, canonical)) throw new Error(`${label} must be outside Project Root`);
  return canonical;
}

function navigationBinding(planReviewPath, projectRoot) {
  if (!planReviewPath) return { navigation: {}, planPaths: [] };
  const reviewPath = exactOutsideFile(planReviewPath, projectRoot, "Plan Review");
  const bytes = fs.readFileSync(reviewPath);
  const review = JSON.parse(bytes);
  const planPaths = Array.isArray(review.plans) ? review.plans.map(item => {
    if (typeof item?.path !== "string" || !path.isAbsolute(item.path)) throw new Error("Plan Review contains a non-exact Plan path");
    const canonical = fs.realpathSync(item.path);
    if (!isInsideProject(projectRoot, canonical) || !fs.statSync(canonical).isFile()) throw new Error("Plan Review contains a non-project Plan path");
    return canonical;
  }) : [];
  return {
    navigation: { plan_review_path: reviewPath, plan_review_sha256: hashBytes(bytes) },
    planPaths,
  };
}

function defaultBindingPath() {
  return path.join(os.homedir(), ".cache", "iis-ready", "verification-bindings", `${crypto.randomUUID()}.json`);
}

function canonicalNewOutsidePath(rawPath, projectRoot) {
  if (!path.isAbsolute(rawPath)) throw new Error("binding_path must be an exact absolute path");
  fs.mkdirSync(path.dirname(rawPath), { recursive: true, mode: 0o700 });
  const parent = fs.realpathSync(path.dirname(rawPath));
  const file = path.join(parent, path.basename(rawPath));
  if (isInsideProject(projectRoot, file)) throw new Error("verification binding must be outside Project Root");
  if (fs.existsSync(file)) throw new Error(`verification binding already exists: ${file}`);
  return file;
}

function atomicCreate(file, bytes) {
  const temporary = path.join(path.dirname(file), `.iis-binding-${crypto.randomUUID()}.tmp`);
  try {
    const fd = fs.openSync(temporary, "wx", 0o600);
    try {
      fs.writeFileSync(fd, bytes);
      fs.fchmodSync(fd, 0o600);
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }
    fs.linkSync(temporary, file);
    const directory = fs.openSync(path.dirname(file), "r");
    try { fs.fsyncSync(directory); } finally { fs.closeSync(directory); }
  } finally {
    if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
  }
}

export async function captureVerification({
  projectRoot,
  ticketPath,
  stableTargetPaths = [],
  scenarioEffectPaths = [],
  planReviewPath,
  bindingPath,
  validatorPath,
  executeArgv,
  bundleIdentity = "source",
}) {
  const root = canonicalProjectRoot(projectRoot);
  if (!Array.isArray(stableTargetPaths) || !stableTargetPaths.length) throw new Error("stable_target_paths must contain at least one path");
  const authority = await bindAuthority({
    projectRoot: root,
    ticketPath,
    allowedStatuses: ["ready", "done"],
    validatorPath,
    executeArgv,
    bundleIdentity,
  });
  const stable = [...new Set(stableTargetPaths.map(raw => canonicalPotentialPath(raw, root)))];
  const effects = [...new Set((scenarioEffectPaths || []).map(raw => canonicalPotentialPath(raw, root)))];
  for (const stablePath of stable) {
    for (const effectPath of effects) {
      if (overlaps(stablePath, effectPath)) throw new Error(`stable target overlaps scenario effect path: ${stablePath} <> ${effectPath}`);
    }
  }
  const { navigation, planPaths } = navigationBinding(planReviewPath, root);
  const protectedPaths = [...authority.protected_artifacts.map(item => item.path), ...planPaths, navigation.plan_review_path].filter(Boolean);
  for (const effectPath of effects) {
    const conflict = protectedPaths.find(protectedPath => overlaps(protectedPath, effectPath));
    if (conflict) throw new Error(`scenario effect path overlaps protected authority/method path: ${effectPath} <> ${conflict}`);
  }
  const manifest = snapshotStableTargets(root, stable);
  const binding = {
    schema: "iis-verification-binding/v1",
    bundle_identity: authority.bundle_identity,
    boundary_protocol: authority.boundary_protocol,
    project_root: root,
    ticket_path: authority.ticket_path,
    ticket_status_at_capture: authority.ticket_status_at_capture,
    ticket_sha256: authority.ticket_sha256,
    authority_digest: authority.authority_digest,
    protected_artifacts: authority.protected_artifacts,
    validator_path: authority.validator_path,
    stable_target_paths: stable,
    stable_target_manifest: manifest,
    stable_target_digest: hashBytes(JSON.stringify(manifest)),
    scenario_effect_paths: effects,
    navigation,
  };
  const destination = canonicalNewOutsidePath(bindingPath ?? defaultBindingPath(), root);
  binding.binding_path = destination;
  const bytes = Buffer.from(`${JSON.stringify(binding, null, 2)}\n`);
  atomicCreate(destination, bytes);
  return {
    schema: binding.schema,
    binding_path: destination,
    binding_sha256: hashBytes(bytes),
    binding,
  };
}

export function readVerificationBinding(bindingPath, bindingSha256) {
  if (typeof bindingPath !== "string" || !path.isAbsolute(bindingPath)) throw new Error("binding_path must be an exact absolute path");
  const canonical = fs.realpathSync(bindingPath);
  if (canonical !== bindingPath || !fs.statSync(canonical).isFile()) throw new Error("verification binding path is not canonical");
  const bytes = fs.readFileSync(canonical);
  if (hashBytes(bytes) !== bindingSha256) throw new Error("verification binding SHA256 mismatch");
  const binding = JSON.parse(bytes);
  if (binding.schema !== "iis-verification-binding/v1") throw new Error("unsupported verification binding schema");
  const root = canonicalProjectRoot(binding.project_root);
  if (binding.project_root !== root || binding.binding_path !== canonical || isInsideProject(root, canonical)) throw new Error("verification binding identity/root mismatch");
  return { binding, bytes, binding_path: canonical, binding_sha256: hashBytes(bytes) };
}

export async function checkVerificationCurrentness(binding, { expectedTicketSha256 } = {}) {
  const authority = await checkAuthorityCurrentness(binding, { expectedTicketSha256 });
  const currentManifest = snapshotStableTargets(binding.project_root, binding.stable_target_paths || []);
  const changed = [];
  const ticketKey = relativeKey(binding.project_root, binding.ticket_path);
  for (const name of new Set([...Object.keys(binding.stable_target_manifest || {}), ...Object.keys(currentManifest)])) {
    const before = binding.stable_target_manifest?.[name];
    const after = currentManifest[name];
    if (name === ticketKey && expectedTicketSha256 && before?.kind === "file" && after?.kind === "file" && after.sha256 === expectedTicketSha256 && before.mode === after.mode) continue;
    if (JSON.stringify(before) !== JSON.stringify(after)) changed.push(name);
  }
  return {
    current: authority.current && changed.length === 0,
    authority_current: authority.current,
    authority_changed: authority.changed,
    stable_target_current: changed.length === 0,
    stable_target_changed: changed,
    stable_target_digest: hashBytes(JSON.stringify(currentManifest)),
  };
}
