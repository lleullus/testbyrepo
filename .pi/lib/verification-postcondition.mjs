import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { lstat, readFile, readdir, readlink, realpath } from "node:fs/promises";
import { isAbsolute, relative, resolve, sep } from "node:path";

const SNAPSHOT_FILE_LIMIT = 50_000;
const SNAPSHOT_BYTE_LIMIT = 256 * 1024 * 1024;

function execute(command, args, options = {}) {
  const { promise, resolve: resolveExecution, reject } = Promise.withResolvers();
  execFile(command, args, { ...options, encoding: "buffer", maxBuffer: 16 * 1024 * 1024 }, (error, stdout, stderr) => {
    if (error) {
      error.stdout = stdout;
      error.stderr = stderr;
      reject(error);
    } else {
      resolveExecution({ stdout, stderr });
    }
  });
  return promise;
}

function inside(root, path) {
  const rel = relative(root, path);
  return rel === "" || (!rel.startsWith(`..${sep}`) && rel !== ".." && !isAbsolute(rel));
}

async function gitRoot(projectRoot) {
  try {
    const result = await execute("git", ["-C", projectRoot, "rev-parse", "--show-toplevel"]);
    return realpath(result.stdout.toString("utf8").trim());
  } catch {
    return null;
  }
}

async function filesystemPaths(root, excludedTicket) {
  const paths = [];
  const directories = [root];
  while (directories.length) {
    const directory = directories.pop();
    const entries = await readdir(directory, { withFileTypes: true });
    entries.sort((left, right) => left.name.localeCompare(right.name));
    for (const entry of entries) {
      if (entry.name === ".git") continue;
      const absolute = resolve(directory, entry.name);
      if (!inside(root, absolute)) throw new Error(`filesystem snapshot found an escaping path: ${absolute}`);
      if (absolute === excludedTicket) continue;
      if (entry.isDirectory()) directories.push(absolute);
      else paths.push(relative(root, absolute));
      if (paths.length > SNAPSHOT_FILE_LIMIT) {
        throw new Error(`non-Git verification snapshot exceeds ${SNAPSHOT_FILE_LIMIT} files`);
      }
    }
  }
  return paths.sort();
}

async function hashPaths(root, paths, excludedTicket, byteLimit = Number.POSITIVE_INFINITY) {
  const digest = createHash("sha256");
  let fileCount = 0;
  let byteCount = 0;
  for (const path of paths) {
    const absolute = resolve(root, path);
    if (!inside(root, absolute)) throw new Error(`snapshot returned an escaping path: ${path}`);
    if (absolute === excludedTicket) continue;
    digest.update(path);
    digest.update("\0");
    try {
      const info = await lstat(absolute);
      digest.update(String(info.mode));
      digest.update("\0");
      if (info.isSymbolicLink()) digest.update(await readlink(absolute));
      else if (info.isFile()) {
        byteCount += info.size;
        if (byteCount > byteLimit) {
          throw new Error(`verification snapshot exceeds ${byteLimit} bytes`);
        }
        digest.update(await readFile(absolute));
      } else digest.update(`<${info.isDirectory() ? "directory" : "special"}>`);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
      digest.update("<missing>");
    }
    digest.update("\0");
    fileCount += 1;
  }
  return { digest: digest.digest("hex"), fileCount };
}

async function repositorySnapshot(projectRoot, excludedTicket) {
  const canonicalProjectRoot = await realpath(projectRoot);
  const discoveredGitRoot = await gitRoot(canonicalProjectRoot);
  if (discoveredGitRoot) {
    const result = await execute("git", [
      "-C",
      discoveredGitRoot,
      "ls-files",
      "-z",
      "--cached",
      "--others",
      "--exclude-standard",
    ]);
    const paths = result.stdout.toString("utf8").split("\0").filter(Boolean).sort();
    const snapshot = await hashPaths(discoveredGitRoot, paths, excludedTicket);
    return { root: discoveredGitRoot, scope: "Git tracked and non-ignored untracked content", ...snapshot };
  }

  const paths = await filesystemPaths(canonicalProjectRoot, excludedTicket);
  const snapshot = await hashPaths(canonicalProjectRoot, paths, excludedTicket, SNAPSHOT_BYTE_LIMIT);
  return { root: canonicalProjectRoot, scope: "Full non-Git Project Root content excluding .git and the Ticket", ...snapshot };
}

function sha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

function exactReadyToDone(before, after) {
  const beforeLines = before.split("\n");
  const afterLines = after.split("\n");
  if (beforeLines.length !== afterLines.length) return false;
  let changes = 0;
  for (let index = 0; index < beforeLines.length; index += 1) {
    if (beforeLines[index] === afterLines[index]) continue;
    if (beforeLines[index] !== "Status: ready" || afterLines[index] !== "Status: done") return false;
    changes += 1;
  }
  return changes === 1;
}

export async function captureVerificationPostcondition(projectRoot, ticket) {
  const canonicalTicket = await realpath(ticket);
  const ticketContent = await readFile(canonicalTicket, "utf8");
  const repository = await repositorySnapshot(projectRoot, canonicalTicket);
  return {
    projectRoot,
    ticket: canonicalTicket,
    ticketContent,
    ticketSha256: sha256(ticketContent),
    repository,
  };
}

export async function verifyVerificationPostcondition(before) {
  const ticketContent = await readFile(before.ticket, "utf8");
  const repository = await repositorySnapshot(before.projectRoot, before.ticket);
  if (
    repository.root !== before.repository.root ||
    repository.scope !== before.repository.scope ||
    repository.digest !== before.repository.digest
  ) {
    throw new Error(
      `verification mutated protected product content (${before.repository.scope}): before=${before.repository.digest} after=${repository.digest}`,
    );
  }

  let ticketChange = "UNCHANGED";
  if (ticketContent !== before.ticketContent) {
    if (!exactReadyToDone(before.ticketContent, ticketContent)) {
      throw new Error("verification mutated Ticket content beyond the exact Status: ready -> Status: done transition");
    }
    ticketChange = "READY_TO_DONE";
  }

  return {
    status: "PASSED",
    scope: repository.scope,
    repositoryRoot: repository.root,
    repositoryDigestBefore: before.repository.digest,
    repositoryDigestAfter: repository.digest,
    fileCount: repository.fileCount,
    ticketChange,
    ticketSha256Before: before.ticketSha256,
    ticketSha256After: sha256(ticketContent),
  };
}
