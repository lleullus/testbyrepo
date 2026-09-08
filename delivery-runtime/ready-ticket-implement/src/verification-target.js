import fs from "node:fs";
import path from "node:path";
import { isInsideProject } from "./authority-binding.js";
import { hashBytes } from "./plan-binding.js";

export function canonicalPath(raw, root) {
  let cursor = path.resolve(root, raw), suffix = [];
  while (!fs.existsSync(cursor)) {
    const parent = path.dirname(cursor);
    if (parent === cursor) break;
    suffix.unshift(path.basename(cursor)); cursor = parent;
  }
  return path.join(fs.realpathSync(cursor), ...suffix);
}

export function validateOutputPaths(root, paths = []) {
  return paths.map(raw => {
    const file = canonicalPath(raw, root);
    if (isInsideProject(root, file) || isInsideProject(file, root)) throw new Error(`allowed output must be an exact outside-root file: ${raw}`);
    if (fs.existsSync(file) && !fs.statSync(file).isFile()) throw new Error(`allowed output is not a file: ${file}`);
    return file;
  });
}

export function fileIdentity(file) {
  try {
    const stat = fs.lstatSync(file);
    if (stat.isSymbolicLink()) return { kind: "symlink", target: fs.readlinkSync(file) };
    if (stat.isFile()) return { kind: "file", sha256: hashBytes(fs.readFileSync(file)), mode: stat.mode & 0o777 };
    return { kind: "other", mode: stat.mode };
  } catch (error) { if (error.code === "ENOENT") return { kind: "missing" }; throw error; }
}

function collect(file, files) {
  if (!fs.existsSync(file) || !fs.lstatSync(file).isDirectory()) { files.add(file); return; }
  for (const entry of fs.readdirSync(file)) collect(path.join(file, entry), files);
}

export async function captureVerificationTarget({ projectRoot, targetPaths = [], allowedOutputPaths = [], methodPaths = [], productPaths = [], executeArgv }) {
  const root = fs.realpathSync(projectRoot);
  const allowed = validateOutputPaths(root, allowedOutputPaths);
  const explicit = targetPaths.map(raw => {
    const file = canonicalPath(raw, root);
    if (!isInsideProject(root, file)) throw new Error(`verification target outside Project Root: ${file}`);
    return file;
  });
  if (!executeArgv) throw new Error("CAPABILITY_UNAVAILABLE: product inventory requires structured executeArgv");
  const result = await executeArgv(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], { cwd: root, timeout: 30000 });
  if (result.interrupted || result.terminationState !== "settled" || result.exitCode !== 0) throw new Error("cannot capture current Git product universe");
  const files = new Set(String(result.stdout).split("\0").filter(Boolean).map(name => path.resolve(root, name)));
  for (const file of explicit) collect(file, files);
  const methods = methodPaths.map(file => canonicalPath(file, root));
  const requiredProducts = new Set(productPaths.map(file => canonicalPath(file, root)));
  const context = new Set(methods.filter(file => !requiredProducts.has(file) && !explicit.some(target => isInsideProject(target, file))));
  const manifest = {}, methodManifest = {};
  for (const file of [...files].sort()) {
    if (context.has(file)) methodManifest[file] = fileIdentity(file);
    else manifest[path.relative(root, file).split(path.sep).join("/")] = fileIdentity(file);
  }
  for (const file of context) methodManifest[file] = fileIdentity(file);
  return { project_root: root, target_paths: explicit, allowed_output_paths: allowed, method_paths: methods, product_paths: [...requiredProducts], manifest, method_manifest: methodManifest, digest: hashBytes(JSON.stringify(manifest)) };
}

export async function checkVerificationTarget(binding, { executeArgv, expectedTicket } = {}) {
  const current = await captureVerificationTarget({ projectRoot: binding.project_root, targetPaths: binding.target_paths, allowedOutputPaths: binding.allowed_output_paths, methodPaths: binding.method_paths, productPaths: binding.product_paths, executeArgv });
  const changed = [];
  for (const name of new Set([...Object.keys(binding.manifest), ...Object.keys(current.manifest)])) {
    const after = current.manifest[name], before = binding.manifest[name];
    if (expectedTicket && path.resolve(binding.project_root, name) === expectedTicket.path && after?.sha256 === expectedTicket.sha256 && before?.mode === after.mode) continue;
    if (JSON.stringify(before) !== JSON.stringify(after)) changed.push(name);
  }
  return { current: !changed.length, changed, method_current: JSON.stringify(binding.method_manifest) === JSON.stringify(current.method_manifest), current_binding: current };
}
