# Baseline Capsule Protocol v1

## Purpose

Baseline Capsule preserves immutable physical source evidence before the first
product mutation. It owns source projection, identity, retained payload,
durable storage, read leases, retention, quota enforcement, and cleanup. It
does not own planning, implementation state, verification policy, Adapter
selection, commands, findings, or verdicts.

## Public interface

```text
create(projectRoot) -> CapsuleHandle
captureIdentity(projectRoot) -> SourceIdentity
acquireRead(capsuleRef) -> CapsuleView
releaseRead(readLeaseId)
cleanupExpired()
```

`CapsuleHandle` contains only:

```text
capsuleRef
formatVersion = baseline-capsule-v1
projectionPolicyId = source-evidence-v1
baselineSourceIdentity
createdAt
expiresAt
```

`CapsuleView` additionally exposes the canonical project root, immutable sealed
root, and opaque read lease ID. The sealed root is available only while the
lease is active.

## Projection policy

Identity and retained payload use the same closed `source-evidence-v1`
projection. The policy excludes only:

- VCS administrative roots: `.git`, `.hg`, and `.svn`;
- dependency environments: `node_modules`, `.tox`, `.nox`, and directories
  identified by a direct `pyvenv.cfg` child;
- tool-specific volatile caches: `.gocache`, `.cache/go-build`,
  `node_modules/.cache`, `.next/cache`, `.mypy_cache`, `.pytest_cache`,
  `.ruff_cache`, `__pycache__`, `.turbo`, `.parcel-cache`, `.nyc_output`,
  `.eslintcache`, and `*.tsbuildinfo`.

Ambiguous names such as `build`, `dist`, `out`, `.cache`, `coverage`, `tmp`, and
`vendor` are included. All other regular files, contained symlinks, and
directories are included regardless of Git tracked or ignored state. Special
filesystem entries and symlinks that resolve outside the project root make
creation fail.

## Storage policy

- default store: `~/.local/state/opencode/baseline-capsules`;
- retention: 7 days;
- maximum retained regular file: 256 MiB;
- maximum retained payload per capsule: 2 GiB;
- store, staging, capsule, and lease directories: owner-only;
- descriptor and retained regular files: owner-readable only after publish;
- capsules become visible only by atomic publication;
- unknown format or projection versions fail closed;
- missing, expired, corrupt, partial, or quota-exceeding capsules are never
  replaced or silently re-sealed.

## Identity and stability

The identity is SHA-256 over the canonical projected entry manifest. Regular
files contribute mode, size, and content digest; directories contribute mode;
symlinks contribute mode and target. Capture performs a stable source scan,
copies the projected payload into private staging, rescans source and retained
payload, and publishes only when all projected manifests are identical.

## Read and cleanup

Every read revalidates descriptor shape, format, projection, expiry, and the
sealed payload identity before returning a view. Cleanup must not remove a
capsule with an active unexpired lease. A lease is an access pin, not an
exclusive verification lock; concurrent readers are allowed.

## Errors

Stable error codes include:

```text
INVALID_PROJECT_ROOT
STORE_INSIDE_PROJECT
PROJECT_INSIDE_STORE
SOURCE_CHANGED_DURING_CAPTURE
FILE_QUOTA_EXCEEDED
CAPSULE_QUOTA_EXCEEDED
UNSUPPORTED_ENTRY
SYMLINK_ESCAPE
CAPSULE_NOT_FOUND
CAPSULE_EXPIRED
CAPSULE_CORRUPT
UNSUPPORTED_FORMAT
INVALID_CAPSULE_REF
INVALID_LEASE
```
