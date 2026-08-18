#!/usr/bin/env node
import assert from "node:assert/strict";
import {
  existsSync,
  readFileSync,
  readdirSync,
  statSync,
} from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

function readJson(file) {
  return JSON.parse(readFileSync(path.join(root, file), "utf8"));
}

function walk(dir) {
  const absolute = path.join(root, dir);
  const files = [];
  for (const entry of readdirSync(absolute)) {
    const child = path.join(absolute, entry);
    const rel = path.relative(root, child);
    if (statSync(child).isDirectory()) files.push(...walk(rel));
    else files.push(rel);
  }
  return files;
}

const pkg = readJson("package.json");
assert.deepEqual(pkg.omp?.extensions, ["./extensions/lumin-repo-lens.ts"]);

const catalog = readJson(".omp-plugin/marketplace.json");
assert.equal(catalog.name, "lumin-repo-lens-omp-marketplace");
assert.equal(catalog.plugins?.[0]?.name, "lumin-repo-lens");
assert.equal(catalog.plugins?.[0]?.source, "./");

const expectedCommands = [
  "audit.md",
  "canon-draft.md",
  "check-canon.md",
  "full.md",
  "lumin-repo-lens.md",
  "post-write.md",
  "pre-write.md",
  "refactor-plan.md",
  "welcome.md",
];
for (const command of expectedCommands) {
  assert.ok(existsSync(path.join(root, "commands", command)), `missing command: ${command}`);
}

for (const skill of [
  "lumin-repo-lens",
  "lumin-repo-lens-canon",
  "lumin-repo-lens-write-gate",
]) {
  assert.ok(
    existsSync(path.join(root, "skills", skill, "SKILL.md")),
    `missing skill: ${skill}`,
  );
}

assert.ok(existsSync(path.join(root, "extensions", "lumin-repo-lens.ts")));
assert.ok(!existsSync(path.join(root, ".claude-plugin")));
assert.ok(!existsSync(path.join(root, "hooks")));

const hostFacingFiles = [
  ...walk("commands"),
  ...walk("extensions"),
  ...walk(".omp-plugin"),
  "README.md",
  "README.ko.md",
].filter((file) => /\.(?:md|mjs|ts|json)$/.test(file));

for (const file of hostFacingFiles) {
  const text = readFileSync(path.join(root, file), "utf8");
  assert.ok(
    !text.includes("${CLAUDE_PLUGIN_ROOT}"),
    `${file} still contains CLAUDE_PLUGIN_ROOT`,
  );
}

console.log(
  `[verify-omp-port] ok: ${expectedCommands.length} commands, 3 skills, OMP extension + marketplace`,
);
