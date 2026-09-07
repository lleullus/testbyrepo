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

const SED_LINE_PRINT_EXPRESSION = /^\s*(?:\d+|\$)\s*(?:,\s*(?:\d+|\$)\s*)?p\s*$/;
const SED_SAFE_LONG_OPTIONS = new Set([
  "--null-data", "--posix", "--regexp-extended", "--sandbox", "--separate", "--unbuffered",
]);
const SED_SAFE_SHORT_OPTIONS = new Set(["E", "r", "s", "u", "z"]);
const SORT_DENIED_LONG_OPTIONS = new Set(["--compress-program", "--output", "--temporary-directory"]);
const SORT_DENIED_SHORT_OPTIONS = new Set(["o", "T"]);
const SORT_LONG_OPTIONS_WITH_OPERANDS = new Set([
  "--batch-size", "--buffer-size", "--field-separator", "--files0-from", "--key", "--parallel", "--random-source", "--sort",
]);
const SORT_SHORT_OPTIONS_WITH_OPERANDS = new Set(["k", "S", "t"]);
const RG_DENIED_LONG_OPTIONS = new Set(["--hostname-bin", "--hyperlink-format", "--pre", "--pre-glob", "--search-zip"]);
const RG_DENIED_SHORT_OPTIONS = new Set(["z"]);
const RG_LONG_OPTIONS_WITH_OPERANDS = new Set([
  "--after-context", "--before-context", "--color", "--colors", "--context", "--encoding", "--engine", "--file", "--glob",
  "--iglob", "--ignore-file", "--max-columns", "--max-count", "--max-depth", "--max-filesize", "--path-separator", "--regexp",
  "--replace", "--sort", "--sortr", "--threads", "--type", "--type-add", "--type-clear", "--type-not",
]);
const RG_SHORT_OPTIONS_WITH_OPERANDS = new Set(["A", "B", "C", "E", "M", "T", "d", "e", "f", "g", "j", "m", "r", "t"]);
const FILE_DENIED_LONG_OPTIONS = new Set(["--compile", "--no-sandbox", "--preserve-date", "--uncompress", "--uncompress-noreport"]);
const FILE_DENIED_SHORT_OPTIONS = new Set(["C", "S", "Z", "p", "z"]);
const FILE_LONG_OPTIONS_WITH_OPERANDS = new Set(["--exclude", "--exclude-quiet", "--files-from", "--magic-file", "--parameter", "--separator"]);
const FILE_SHORT_OPTIONS_WITH_OPERANDS = new Set(["F", "P", "e", "f", "m"]);
const FIND_OPTIONS_WITH_OPERANDS = new Set([
  "-D", "-amin", "-anewer", "-atime", "-cmin", "-cnewer", "-ctime", "-files0-from", "-fstype", "-gid", "-group",
  "-ilname", "-iname", "-inum", "-ipath", "-iregex", "-links", "-lname", "-maxdepth", "-mindepth", "-mmin", "-mtime",
  "-name", "-newer", "-path", "-perm", "-printf", "-regex", "-regextype", "-samefile", "-size", "-type", "-uid", "-user",
  "-used", "-wholename", "-xtype",
]);
const FIND_SIDE_EFFECTING_ACTIONS = new Set(["-delete", "-exec", "-execdir", "-fls", "-fprintf", "-fprint", "-fprint0", "-ok", "-okdir"]);
const GIT_DENIED_LONG_OPTIONS = new Set(["--ext-diff", "--filters", "--open-files-in-pager", "--output", "--textconv"]);
const GIT_WORKTREE_LIST_OPTIONS = new Set(["--porcelain", "--verbose", "-v", "-z"]);
const EMPTY_OPTIONS = new Set();
const TREE_DENIED_SHORT_OPTIONS = new Set(["R", "o"]);
const TREE_SHORT_OPTIONS_WITH_OPERANDS = new Set(["H", "I", "L", "P", "T"]);
const OPTION_POLICIES = {
  sort: {
    deniedLong: SORT_DENIED_LONG_OPTIONS,
    deniedShort: SORT_DENIED_SHORT_OPTIONS,
    longWithOperands: SORT_LONG_OPTIONS_WITH_OPERANDS,
    shortWithOperands: SORT_SHORT_OPTIONS_WITH_OPERANDS,
  },
  rg: {
    deniedLong: RG_DENIED_LONG_OPTIONS,
    deniedShort: RG_DENIED_SHORT_OPTIONS,
    longWithOperands: RG_LONG_OPTIONS_WITH_OPERANDS,
    shortWithOperands: RG_SHORT_OPTIONS_WITH_OPERANDS,
  },
  file: {
    deniedLong: FILE_DENIED_LONG_OPTIONS,
    deniedShort: FILE_DENIED_SHORT_OPTIONS,
    longWithOperands: FILE_LONG_OPTIONS_WITH_OPERANDS,
    shortWithOperands: FILE_SHORT_OPTIONS_WITH_OPERANDS,
  },
  tree: {
    deniedLong: EMPTY_OPTIONS,
    deniedShort: TREE_DENIED_SHORT_OPTIONS,
    shortWithOperands: TREE_SHORT_OPTIONS_WITH_OPERANDS,
  },
};
const GIT_OPTION_POLICY = { deniedLong: GIT_DENIED_LONG_OPTIONS, startIndex: 2 };
const GIT_GREP_OPTION_POLICY = {
  ...GIT_OPTION_POLICY,
  deniedShort: new Set(["O"]),
  longWithOperands: new Set(["--after-context", "--before-context", "--context", "--file", "--max-count", "--max-depth", "--regexp", "--threads"]),
  shortWithOperands: new Set(["A", "B", "C", "e", "f", "m"]),
};

function assertArgv(argv) {
  if (!Array.isArray(argv) || argv.length === 0 || argv.some(item => typeof item !== "string") || argv[0].length === 0) {
    throw new Error("structured argv must be a non-empty array of strings with a non-empty executable");
  }
  if (SHELL_INTERPRETERS.has(argv[0].toLowerCase())) {
    throw new Error("structured argv cannot invoke a shell interpreter");
  }
  return argv.slice();
}

// GNU-style parsers accept unambiguous long-option prefixes, so deny prefixes too.
function isDeniedLongOption(name, deniedLong) {
  for (const denied of deniedLong) {
    if (name === denied || denied.startsWith(name)) return true;
  }
  return false;
}

function hasDeniedOption(argv, {
  deniedLong,
  deniedShort = EMPTY_OPTIONS,
  longWithOperands = EMPTY_OPTIONS,
  shortWithOperands = EMPTY_OPTIONS,
  startIndex = 1,
}) {
  let options = true;
  for (let index = startIndex; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!options) continue;
    if (argument === "--") {
      options = false;
      continue;
    }
    if (argument === "-" || !argument.startsWith("-")) continue;
    if (argument.startsWith("--")) {
      const equals = argument.indexOf("=");
      const name = equals === -1 ? argument : argument.slice(0, equals);
      if (isDeniedLongOption(name, deniedLong)) return true;
      if (equals === -1 && longWithOperands.has(name)) index += 1;
      continue;
    }

    for (let offset = 1; offset < argument.length; offset += 1) {
      const option = argument[offset];
      if (deniedShort.has(option)) return true;
      if (shortWithOperands.has(option)) {
        if (offset === argument.length - 1) index += 1;
        break;
      }
    }
  }
  return false;
}

// sed programs can write files or launch processes; inspection only needs addressed, quiet printing.
function isReadOnlySed(argv) {
  const scripts = [];
  let explicitExpression = false;
  let quiet = false;
  let options = true;

  for (let index = 1; index < argv.length; index += 1) {
    const argument = argv[index];
    if (options && argument === "--") {
      options = false;
      continue;
    }
    if (options && argument.startsWith("--")) {
      if (argument === "--quiet" || argument === "--silent") {
        quiet = true;
        continue;
      }
      if (argument === "--expression") {
        if (index + 1 >= argv.length) return false;
        explicitExpression = true;
        scripts.push(argv[index += 1]);
        continue;
      }
      if (argument.startsWith("--expression=")) {
        explicitExpression = true;
        scripts.push(argument.slice("--expression=".length));
        continue;
      }
      if (SED_SAFE_LONG_OPTIONS.has(argument)) {
        continue;
      }
      return false;
    }
    if (options && argument.startsWith("-") && argument !== "-") {
      for (let offset = 1; offset < argument.length; offset += 1) {
        const option = argument[offset];
        if (option === "n") {
          quiet = true;
          continue;
        }
        if (SED_SAFE_SHORT_OPTIONS.has(option)) continue;
        if (option !== "e") return false;

        explicitExpression = true;
        const attached = argument.slice(offset + 1);
        if (attached) scripts.push(attached);
        else {
          if (index + 1 >= argv.length) return false;
          scripts.push(argv[index += 1]);
        }
        break;
      }
      continue;
    }
    if (!explicitExpression && scripts.length === 0) scripts.push(argument);
  }

  return quiet && scripts.length > 0 && scripts.every(script => SED_LINE_PRINT_EXPRESSION.test(script));
}




// Keep find's useful test grammar, but exclude every standard action that writes or launches a process.
function isReadOnlyFind(argv) {
  for (let index = 1; index < argv.length; index += 1) {
    const argument = argv[index];
    if (FIND_SIDE_EFFECTING_ACTIONS.has(argument)) return false;
    if (FIND_OPTIONS_WITH_OPERANDS.has(argument) || /^-newer[acmB][acmB]$/.test(argument)) index += 1;
  }
  return true;
}


function isReadOnlyGit(argv) {
  if (argv.length < 2 || !READ_ONLY_GIT_SUBCOMMANDS.has(argv[1])) return false;
  if (argv[1] === "worktree") {
    if (argv.length < 3 || argv[2] !== "list") return false;
    for (let index = 3; index < argv.length; index += 1) {
      if (!GIT_WORKTREE_LIST_OPTIONS.has(argv[index])) return false;
    }
    return true;
  }
  return !hasDeniedOption(argv, argv[1] === "grep" ? GIT_GREP_OPTION_POLICY : GIT_OPTION_POLICY);
}

export function isReadOnlyArgv(argv) {
  const normalized = assertArgv(argv);
  const executable = normalized[0].toLowerCase();
  if (!READ_ONLY_COMMANDS.has(executable) && executable !== "git") return false;
  if (executable === "sed") return isReadOnlySed(normalized);
  const optionPolicy = OPTION_POLICIES[executable];
  if (optionPolicy) return !hasDeniedOption(normalized, optionPolicy);
  if (executable === "find") return isReadOnlyFind(normalized);
  if (executable === "git") return isReadOnlyGit(normalized);
  return true;
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

export function validateExecutionRequest(request) {
  if (request?.version !== 1) throw new Error("unsupported ready_argv execute version");
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
