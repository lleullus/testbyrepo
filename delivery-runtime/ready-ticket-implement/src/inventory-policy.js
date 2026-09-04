const RG_VALUE_OPTIONS = new Set(["-g", "--glob", "--iglob", "--ignore-file", "--max-depth", "--type", "-t", "-T"]);

function nonOptionArgs(argv, start = 1, valueOptions = new Set()) {
  const values = [];
  for (let index = start; index < argv.length; index += 1) {
    const arg = argv[index];
    if (valueOptions.has(arg)) {
      index += 1;
      continue;
    }
    if (arg === "--") {
      values.push(...argv.slice(index + 1));
      break;
    }
    if (!String(arg).startsWith("-")) values.push(String(arg));
  }
  return values;
}

function rootish(paths) {
  return paths.length === 0 || (paths.length === 1 && [".", "./"].includes(paths[0]));
}

export function isBroadInventory(toolName, input) {
  const tool = String(toolName).toLowerCase();
  if (tool === "glob") {
    const pattern = String(input?.pattern ?? "").trim();
    return pattern === "*" || pattern === "**" || pattern === "**/*" || pattern.startsWith("**/");
  }
  if (tool !== "bash") return false;

  const argv = Array.isArray(input?.argv) ? input.argv.map(String) : [];
  if (argv.length === 0) return false;
  const command = argv[0];

  if (command === "rg" && argv.includes("--files")) {
    return rootish(nonOptionArgs(argv, 1, RG_VALUE_OPTIONS));
  }
  if (command === "find") return rootish(nonOptionArgs(argv));
  if (command === "tree") return rootish(nonOptionArgs(argv));
  if (command === "ls") {
    const recursive = argv.some(arg => arg === "--recursive" || /^-[^-]*R/.test(arg));
    return recursive && rootish(nonOptionArgs(argv));
  }
  if (command === "git" && argv[1] === "ls-files") {
    return rootish(nonOptionArgs(argv, 2));
  }
  if (command === "git" && argv[1] === "ls-tree") {
    const recursive = argv.includes("-r") || argv.includes("--recursive");
    if (!recursive) return false;
    const separator = argv.indexOf("--");
    return separator < 0 || rootish(argv.slice(separator + 1));
  }
  return false;
}

export function inventoryAllowedForPhase(state, broadInventory) {
  if (!broadInventory) return { allowed: true };
  if (state.phase === "ACTIVE") {
    const directImplementationPreflight = (
      (state.purpose ?? "implement") === "implement"
      && state.execution_mode === "DIRECT"
      && state.implementation_mutation_started === false
    );
    if (!directImplementationPreflight) {
      return { allowed: false, reason: "Ready runtime blocks repository-wide inventory rescans after implementation mutation begins." };
    }
  }
  if (state.preflight_broad_inventory_used) {
    return { allowed: false, reason: "Ready runtime allows at most one repository-wide inventory during preflight; narrow the next read/search." };
  }
  state.preflight_broad_inventory_used = true;
  return { allowed: true };
}
