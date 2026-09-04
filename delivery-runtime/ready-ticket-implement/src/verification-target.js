import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

function git(projectRoot, args) {
  const result = spawnSync("git", ["-C", projectRoot, ...args], {
    encoding: null,
    shell: false,
    timeout: 30_000,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`git ${args.join(" ")} failed: ${Buffer.from(result.stderr ?? "").toString("utf8").trim()}`);
  }
  return Buffer.from(result.stdout ?? Buffer.alloc(0));
}

function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function canonicalProjectPath(projectRoot, raw, label, { allowMissing = false } = {}) {
  const absolute = path.isAbsolute(raw) ? path.resolve(raw) : path.resolve(projectRoot, raw);
  const relative = path.relative(projectRoot, absolute);
  if (relative === ".." || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error(`${label} is outside Project Root: ${raw}`);
  }
  if (!allowMissing && !fs.existsSync(absolute)) throw new Error(`${label} does not exist: ${absolute}`);
  return absolute;
}

function underAny(target, prefixes) {
  return prefixes.some(prefix => target === prefix || target.startsWith(`${prefix}${path.sep}`));
}

function collectExplicit(target, files) {
  if (!fs.existsSync(target)) {
    files.add(target);
    return;
  }
  const stat = fs.lstatSync(target);
  if (!stat.isDirectory()) {
    files.add(target);
    return;
  }
  const stack = [target];
  while (stack.length) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const child = path.join(current, entry.name);
      if (entry.isDirectory()) stack.push(child);
      else files.add(child);
    }
  }
}

function fileIdentity(file) {
  try {
    const stat = fs.lstatSync(file);
    if (stat.isSymbolicLink()) return { kind: "symlink", target: fs.readlinkSync(file) };
    if (stat.isFile()) return { kind: "file", sha256: sha256(fs.readFileSync(file)) };
    return { kind: "other", mode: stat.mode };
  } catch (error) {
    if (error?.code === "ENOENT") return { kind: "missing" };
    throw error;
  }
}

export function captureVerificationTarget({ projectRoot, targetPaths = [], allowedOutputPaths = [] }) {
  const root = fs.realpathSync(projectRoot);
  const allowed = allowedOutputPaths.map(raw => canonicalProjectPath(root, raw, "allowed verification output", { allowMissing: true }));
  const explicit = targetPaths.map(raw => canonicalProjectPath(root, raw, "verification target", { allowMissing: true }));

  const files = new Set();
  const discovered = git(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    .toString("utf8")
    .split("\0")
    .filter(Boolean);
  for (const relative of discovered) files.add(path.resolve(root, relative));
  for (const target of explicit) collectExplicit(target, files);

  const manifest = {};
  for (const absolute of [...files].sort()) {
    if (underAny(absolute, allowed)) continue;
    const relative = path.relative(root, absolute).split(path.sep).join("/");
    manifest[relative] = fileIdentity(absolute);
  }
  const gitHead = git(root, ["rev-parse", "HEAD"]).toString("utf8").trim();
  const digest = sha256(JSON.stringify({ git_head: gitHead, manifest }));
  return {
    project_root: root,
    git_head: gitHead,
    target_paths: explicit,
    allowed_output_paths: allowed,
    manifest,
    digest,
  };
}

export function checkVerificationTarget(binding) {
  const current = captureVerificationTarget({
    projectRoot: binding.project_root,
    targetPaths: binding.target_paths,
    allowedOutputPaths: binding.allowed_output_paths,
  });
  if (current.git_head === binding.git_head && current.digest === binding.digest) {
    return { current: true, changed: [], current_binding: current };
  }
  const changed = [];
  const names = new Set([...Object.keys(binding.manifest || {}), ...Object.keys(current.manifest || {})]);
  for (const name of [...names].sort()) {
    if (JSON.stringify(binding.manifest?.[name] ?? null) !== JSON.stringify(current.manifest?.[name] ?? null)) changed.push(name);
  }
  if (current.git_head !== binding.git_head) changed.unshift(`git_head:${binding.git_head}->${current.git_head}`);
  return { current: false, changed, current_binding: current };
}
