# Upstream Source Manifest

## Scope

Task 0-2 preserves the selected upstream planning-skill source files without local policy, translation, Ticket-contract, or other content changes. `SOURCE.md` is local provenance metadata; every other file under this directory is an upstream byte copy. No Git checkout metadata is stored here.

## Verified Upstream

| Field | Value |
| --- | --- |
| Remote URL | `https://github.com/mattpocock/skills.git` |
| Release/tag | `v1.1.0` |
| Required commit | `d574778f94cf620fcc8ce741584093bc650a61d3` |
| Tag object | `eabea89380927aadb93abf6e290a19334d249292` |
| Temporary checkout | `/tmp/opencode/matt-pocock-skills-v1.1.0` |

Remote verification command and result:

```text
git ls-remote --tags https://github.com/mattpocock/skills.git refs/tags/v1.1.0 'refs/tags/v1.1.0^{}'
eabea89380927aadb93abf6e290a19334d249292	refs/tags/v1.1.0
d574778f94cf620fcc8ce741584093bc650a61d3	refs/tags/v1.1.0^{}
```

`v1.1.0` is an annotated tag. Its dereferenced target is the required commit. A detached checkout at that commit returned the same `HEAD` and `git describe --exact-match --tags HEAD` returned `v1.1.0`.

## Selected Planning Skills

All 13 initial planning candidates in workplan section 3.1 exist at the fixed upstream revision and are preserved at their original paths:

| Skill | Stored source path |
| --- | --- |
| `setup-matt-pocock-skills` | `skills/engineering/setup-matt-pocock-skills/SKILL.md` |
| `ask-matt` | `skills/engineering/ask-matt/SKILL.md` |
| `grill-me` | `skills/productivity/grill-me/SKILL.md` |
| `grilling` | `skills/productivity/grilling/SKILL.md` |
| `grill-with-docs` | `skills/engineering/grill-with-docs/SKILL.md` |
| `domain-modeling` | `skills/engineering/domain-modeling/SKILL.md` |
| `codebase-design` | `skills/engineering/codebase-design/SKILL.md` |
| `research` | `skills/engineering/research/SKILL.md` |
| `prototype` | `skills/engineering/prototype/SKILL.md` |
| `wayfinder` | `skills/engineering/wayfinder/SKILL.md` |
| `to-spec` | `skills/engineering/to-spec/SKILL.md` |
| `to-tickets` | `skills/engineering/to-tickets/SKILL.md` |
| `handoff` | `skills/productivity/handoff/SKILL.md` |

There are no absent candidates from the supplied initial-candidate list.

## Required Support Files

These files are direct relative-document references from selected skills or their selected support documents. They retain their upstream directory structure.

| Referenced by | Stored support files |
| --- | --- |
| `setup-matt-pocock-skills/SKILL.md` | `issue-tracker-github.md`, `issue-tracker-gitlab.md`, `issue-tracker-local.md`, `triage-labels.md`, `domain.md` |
| `domain-modeling/SKILL.md` | `CONTEXT-FORMAT.md`, `ADR-FORMAT.md` |
| `codebase-design/SKILL.md` | `DEEPENING.md`, `DESIGN-IT-TWICE.md` |
| `prototype/SKILL.md` | `LOGIC.md`, `UI.md` |

`CONTEXT-FORMAT.md` has three relative Markdown links inside a fenced multi-context `CONTEXT-MAP.md` example. They intentionally illustrate paths in a consuming project (`./src/ordering/CONTEXT.md`, `./src/billing/CONTEXT.md`, and `./src/fulfillment/CONTEXT.md`); they do not exist in the upstream checkout and are not source dependencies to copy. All actual relative source-document links resolve to a selected skill or the support files above.

## Excluded Files

No execution skill sources were copied: `skills/engineering/implement/`, `skills/engineering/tdd/`, and `skills/engineering/code-review/` are absent. No other upstream `SKILL.md` is stored. Some preserved upstream prose names these skills as possible downstream actions; that prose remains unchanged and does not include their source files.

The upstream MIT license is preserved as `LICENSE`.

## Byte Preservation Verification

Each listed source file was copied from the detached fixed checkout. This command compares bytes first and then prints the local SHA-256 values:

```text
for path in <the 25 paths listed below>; do
  cmp -s "/tmp/opencode/matt-pocock-skills-v1.1.0/$path" "/home/user01/project/matt/upstream/$path" || exit 1
done
sha256sum <the 25 paths listed below>
```

Result: all 25 files, including `LICENSE`, passed `cmp`; the following SHA-256 values were produced from `upstream/`.

```text
0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5  LICENSE
8cd1fa43ff89492320404e5b18fb06d9488256be5dffc291ff038fc98bb98fb9  skills/engineering/setup-matt-pocock-skills/SKILL.md
52e9f9f1ec0f6d47c6785ac500708ac0521f34abb4cc5475b5dc747165dab17e  skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md
4470f2f64d015fba01af877233296b401bb0d44b5acb9572ffc3ff6b30e8de88  skills/engineering/setup-matt-pocock-skills/issue-tracker-gitlab.md
e0dd9835e3658909132058e9a5fdd851e972220bbadaf78a57e3c6220d470922  skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md
4f53c9b40ce2651e3611aa090eaedbd6dbc9b71ef8c5f7e65eac0d8263190d0d  skills/engineering/setup-matt-pocock-skills/triage-labels.md
25be404b58798b3cb2d51c93dba2ab052fc3a425632185726ac3f5fcff193b99  skills/engineering/setup-matt-pocock-skills/domain.md
b7dbb3249695841cf28f87555acc77dc630dafba0f1d544ecce252ff63b0933e  skills/engineering/ask-matt/SKILL.md
6189dfceb7304a6e5558f75d87e68fa3bc7fcf7ba120e44f21f8a61fe01eba54  skills/productivity/grill-me/SKILL.md
5a35925d03a391bcfa46940868b649b72dba89ec9c19525e785bbb6bd3a7f478  skills/productivity/grilling/SKILL.md
610d091047bcfb9db0f75c057d15538481a721111579fc5ec7f83ad9131a2165  skills/engineering/grill-with-docs/SKILL.md
152e2c97239affb12a60c5f4a7e74ab546a49ae169688c81f4e2ccc42dafa579  skills/engineering/domain-modeling/SKILL.md
b8cc318f2a4285b530e908b6bc43901c3c5cd11100362636bbc4216639bef597  skills/engineering/domain-modeling/CONTEXT-FORMAT.md
f1f36cd3f8d3b6474ddd5855da4e233bfc4ae1a1c5024909ccf11871819a41b2  skills/engineering/domain-modeling/ADR-FORMAT.md
a8d50abac5a4018f60e1d911d4b6f4e36454ca14d6c390c0695a578c7de65dad  skills/engineering/codebase-design/SKILL.md
125e6b77413ad2bc7cf7a772bc74336d580a50f9e797db2178ed133d62333d06  skills/engineering/codebase-design/DEEPENING.md
21c3264953bd30ee87b181a3ccaf0e70649f461e5ffd7dc654acee4ba1788b31  skills/engineering/codebase-design/DESIGN-IT-TWICE.md
af378829f015775a3bcd65ff466826722e99359017ae6bae227ca4c9bd14049c  skills/engineering/research/SKILL.md
efa2a92a2f0f8e7d9d0ecb0cfc65ffd5748c73fa3a25fe164e1c8f426938fb52  skills/engineering/prototype/SKILL.md
da91dc92195c00d5dc33863b8c1a030998025a0f8583ebf2babd770825b7f70c  skills/engineering/prototype/LOGIC.md
d76d565149ee50456c5ddc5e29c27fec8737637874fe5c37d970db085a200b27  skills/engineering/prototype/UI.md
bef437de697fb6984a8a90b7fd82f128609148d6e02f635ce419d03555b351e1  skills/engineering/wayfinder/SKILL.md
267638edd513b5918de626ad5605d261952abb7428cb308869c663ca924e93e7  skills/engineering/to-spec/SKILL.md
918bdefab9313100cb1f7ccb412e2a773fe2f2801dd20d44f6b2acf7a42ca456  skills/engineering/to-tickets/SKILL.md
57c9f1f392d7352cdc85b1e39ca49eddc70ce1dc278bd9653fb4f23dfc2560fc  skills/productivity/handoff/SKILL.md
```
