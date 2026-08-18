# Lumin Repo Lens for OMP

An OMP-native port of
[`annyeong844/lumin-repo-lens`](https://github.com/annyeong844/lumin-repo-lens),
pinned to upstream commit `f7a9cee61d49e06a8350cd125a6b0641a64a59c0`
(`0.9.0-beta.93`).

Lumin Repo Lens scans TypeScript/JavaScript repositories and gives OMP
machine-backed evidence about duplicate structures, dead exports, cycles,
topology, barrels, naming drift, and write-time type escapes. The analysis
engine is preserved from upstream; only the host integration has been ported.

## Install in OMP

Clone this branch, then link it as an OMP plugin:

```bash
git clone --branch snapshot/lumin-repo-lens-omp --single-branch \
  https://github.com/lleullus/testbyrepo.git lumin-repo-lens-omp
cd lumin-repo-lens-omp
omp plugin link .
```

Restart OMP after linking so its extension module is loaded. File commands and
skills can be refreshed with `/reload-plugins`.

A local marketplace install is also supported:

```text
/marketplace add /absolute/path/to/lumin-repo-lens-omp
/marketplace install lumin-repo-lens@lumin-repo-lens-omp-marketplace
```

## First use

```text
/lumin-repo-lens:full
```

Then use the write gate around code changes:

```text
/lumin-repo-lens:pre-write
# make the change
/lumin-repo-lens:post-write
```

Other commands:

- `/lumin-repo-lens:audit`
- `/lumin-repo-lens:welcome`
- `/lumin-repo-lens:canon-draft`
- `/lumin-repo-lens:check-canon`
- `/lumin-repo-lens:refactor-plan`

The first audit or write-gate parse may install the pinned parser dependencies
inside `skills/lumin-repo-lens`; set
`LUMIN_REPO_LENS_NO_AUTO_INSTALL=1` to require manual setup instead.

## What was ported

- All upstream audit profiles and evidence producers
- All three upstream skills
- All nine namespaced slash commands
- Pre-write snapshots and post-write type-escape comparison
- Reminder delivery before an OMP turn and after write/edit results
- `AUDIT_ACK <event-id> intentional|fixed|noted` acknowledgement handling
- OMP marketplace metadata and `omp.extensions` discovery
- Node/Bun tests and a package smoke test

See [OMP_PORT.md](./OMP_PORT.md) for the host-event mapping and validation
contract.

## Requirements

- OMP with TypeScript extension support
- Node.js `^20.19.0` or `>=22.12.0`
- Best fit: TypeScript/JavaScript repositories and monorepos

## License

MIT. The upstream implementation and authorship remain attributed to
`annyeong844`; this branch contains the OMP host port.
