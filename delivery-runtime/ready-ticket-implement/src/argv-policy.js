import { spawn } from "node:child_process";

const SHELL_INTERPRETERS = new Set([
  "bash", "cmd", "cmd.exe", "dash", "fish", "ksh", "powershell", "powershell.exe", "pwsh", "sh", "zsh",
]);

const READ_ONLY_COMMANDS = new Set([
  "basename", "cat", "cmp", "cut", "diff", "dirname", "du", "file", "find", "grep", "head", "ls", "pwd",
  "readlink", "realpath", "rg", "sed", "sort", "stat", "tail", "test", "tree", "tr", "true", "type", "wc", "which",
]);

const READ_ONLY_GIT_SUBCOMMANDS = new Set([
  "cat-file", "check-ignore", "describe", "diff", "for-each-ref", "grep", "log", "ls-files", "ls-tree", "name-rev",
  "rev-parse", "show", "status", "worktree",
]);

function assertArgv(argv) {
  if (!Array.isArray(argv) || argv.length === 0 || argv.some(item => typeof item !== "string" || item.length === 0)) {
    throw new Error("structured argv must be a non-empty array of non-empty strings");
  }
  if (SHELL_INTERPRETERS.has(argv[0].toLowerCase())) {
    throw new Error("structured argv cannot invoke a shell interpreter");
  }
  return argv.slice();
}

export function isReadOnlyArgv(argv) {
  const normalized = assertArgv(argv);
  const executable = normalized[0].toLowerCase();
  if (READ_ONLY_COMMANDS.has(executable)) return true;
  if (executable === "git") return normalized.length >= 2 && READ_ONLY_GIT_SUBCOMMANDS.has(normalized[1]);
  return false;
}

export function validateInspectRequest(request) {
  if (request?.version !== 1) throw new Error("unsupported ready_argv inspect version");
  if (!Array.isArray(request.commands) || request.commands.length === 0 || request.commands.length > 8) {
    throw new Error("ready_argv inspect requires 1-8 commands");
  }
  const commands = request.commands.map(command => {
    const argv = assertArgv(command);
    if (!isReadOnlyArgv(argv)) throw new Error(`ready_argv inspect command is outside the read-only allowlist: ${argv[0]}`);
    return argv;
  });
  return { version: 1, commands };
}

export function validateMutationRequest(request) {
  if (request?.version !== 1) throw new Error("unsupported ready_argv mutate version");
  return { version: 1, argv: assertArgv(request.argv) };
}

export function tokenizeSimpleCommand(command) {
  const source = String(command ?? "").trim();
  if (!source) throw new Error("empty bash command");
  if (/[|&;<>()$`\n\r]/.test(source)) throw new Error("bash command contains shell control syntax");

  const argv = [];
  let current = "";
  let quote = null;
  let escaped = false;
  for (const character of source) {
    if (escaped) {
      current += character;
      escaped = false;
      continue;
    }
    if (character === "\\" && quote !== "'") {
      escaped = true;
      continue;
    }
    if (quote) {
      if (character === quote) quote = null;
      else current += character;
      continue;
    }
    if (character === "'" || character === '"') {
      quote = character;
      continue;
    }
    if (/\s/.test(character)) {
      if (current) {
        argv.push(current);
        current = "";
      }
      continue;
    }
    current += character;
  }
  if (escaped || quote) throw new Error("bash command has incomplete quoting or escaping");
  if (current) argv.push(current);
  return assertArgv(argv);
}

export function parseSimpleReadOnlyCommand(command) {
  try {
    const argv = tokenizeSimpleCommand(command);
    return isReadOnlyArgv(argv) ? argv : null;
  } catch {
    return null;
  }
}

export async function runArgv(argv, { cwd, timeoutMs = 120_000, signal } = {}) {
  const normalized = assertArgv(argv);
  return new Promise((resolve, reject) => {
    const options = {
      cwd,
      shell: false,
      stdio: ["ignore", "pipe", "pipe"],
    };
    if (signal) options.signal = signal;
    const child = spawn(normalized[0], normalized.slice(1), options);
    const stdout = [];
    const stderr = [];
    child.stdout.on("data", chunk => stdout.push(chunk));
    child.stderr.on("data", chunk => stderr.push(chunk));
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill("SIGTERM");
    }, timeoutMs);
    timer.unref?.();
    child.once("error", error => {
      clearTimeout(timer);
      reject(error);
    });
    child.once("close", (code, childSignal) => {
      clearTimeout(timer);
      resolve({
        argv: normalized,
        exitCode: code,
        signal: childSignal,
        timedOut,
        stdout: Buffer.concat(stdout).toString("utf8"),
        stderr: Buffer.concat(stderr).toString("utf8"),
      });
    });
  });
}
