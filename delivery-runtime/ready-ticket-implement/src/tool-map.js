export const NATIVE_TOOL_POLICY = Object.freeze({
  read: "observation",
  grep: "observation",
  glob: "observation",
  edit: "mutation",
  write: "mutation",
  hub: "hub",
  todo: "session_control",
  bash: "unsupported"
});

export function buildExactToolMap(pi) {
  const available = pi.getAllTools?.();
  const inventory = Array.isArray(available) ? available : [];
  const mapped = {};
  const boundaries = [];

  for (const [name, policy] of Object.entries(NATIVE_TOOL_POLICY)) {
    const matches = inventory.filter(tool => tool?.name === name);
    const builtin = matches.find(tool => tool?.sourceInfo?.source === "builtin");
    if (!builtin) {
      boundaries.push({
        name,
        reason: matches.length > 0 ? "tool name exists but source provenance is not builtin" : "builtin tool not present",
        sources: matches.map(tool => tool?.sourceInfo ?? null),
      });
      continue;
    }
    mapped[name] = {
      name,
      policy,
      source: builtin.sourceInfo.source,
      path: builtin.sourceInfo.path,
      scope: builtin.sourceInfo.scope,
      origin: builtin.sourceInfo.origin,
    };
  }

  const customMutationBoundary = inventory
    .filter(tool => !Object.hasOwn(NATIVE_TOOL_POLICY, tool?.name))
    .filter(tool => ["mcp", "extension", "sdk"].includes(tool?.sourceInfo?.source))
    .map(tool => ({ name: tool.name, sourceInfo: tool.sourceInfo }));

  return { mapped, boundaries, customMutationBoundary };
}

export function mappedPolicy(toolMap, toolName) {
  return toolMap?.mapped?.[toolName]?.policy ?? null;
}
