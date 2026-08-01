# Task Ownership Snapshots

## Purpose

Task ownership snapshots protect pre-existing user changes and report physical mutations observed
during one Worker call. They are filesystem and scope evidence only: they do not identify the actor
that changed a path. They do not run commands, understand package semantics, establish coverage,
replace the shared Baseline Capsule, or verify product behavior.

Every artifact contains `ownershipOnly: true`. ImplementationResult does not embed these artifacts;
they remain run-scoped attribution evidence and never become Acceptance or completion evidence.

## Capture sequence

1. Select the project root and freeze the task's allowed mutation patterns before Worker dispatch.
2. Capture an immutable `before.json` outside the product root.
3. Dispatch exactly one selected Worker with exclusive mutation authority for the frozen scope.
4. Capture a fresh immutable `after.json` using the same exclusion policy.
5. Compare the artifacts and inspect every actual changed path.
6. Treat any path outside the frozen envelope as `OUTSIDE_ENVELOPE` and enter nonterminal
   reconciliation. The comparison result is not itself `BLOCKED` and does not prove Worker causation.
7. Combine the physical delta with observed actor information and contextual source relationships.
   Continue for preserved disjoint external changes, remediate attributable Worker scope violations,
   and block only unresolved overlapping ownership or preservation loss.

Each capture performs two complete physical scans. A mismatch, disappearing entry, or file changing
while it is hashed produces `SOURCE_CHANGED_DURING_CAPTURE` rather than a partial snapshot.

## Physical identity

- Regular files: SHA-256 content, size, and permission mode.
- Symlinks: link target and mode; links are never followed.
- Directories: mode.
- Special entries: type and mode.
- Ignored and untracked entries: included by default.
- `.git/**`: excluded because repository control metadata is not product mutation evidence;
  `.gitignore` remains included.

There are no implicit cache, generated-output, or `.scratch` exclusions. A repository that needs exclusions must
freeze explicit project-relative patterns and use the identical policy before and after. Exclusions
reduce preservation coverage and therefore require contextual review.

## Attribution and planning artifacts

`WITHIN_ENVELOPE` means only that every physical change matched a frozen allowed pattern. It does not
prove that the Worker made those changes; an observed concurrent actor touching an affected path still
requires reconciliation. `OUTSIDE_ENVELOPE` means only that at least one changed path did not match.

Another `.scratch/<work-slug>/**` tree may be concurrent planning work. It can be recorded as a
reconciled external change only after the Lead confirms that it is not the current Ticket, Spec,
blocker, or UI authority and is disjoint from task impact. It remains in physical and final source
identity; it is not used as task completion evidence. Never add it to the Worker envelope after the
change or exclude all of `.scratch/**` merely to obtain a clear comparison.

## Rename candidates

Deleted and created non-directory entries with identical physical identity are reported as rename
candidates. They are hints for review, not proof of logical rename intent. Both endpoints remain in
the complete changed-path list and must be within the allowed mutation envelope.

## CLI

```text
python3 ownership_snapshot.py capture \
  --project-root /absolute/project \
  --output /tmp/implementation-lead/<run>/task-1-before.json

python3 ownership_snapshot.py compare \
  --before /tmp/implementation-lead/<run>/task-1-before.json \
  --after /tmp/implementation-lead/<run>/task-1-after.json \
  --allow 'src/**' --allow 'tests/**'
```

Artifact creation is exclusive and refuses overwrite. Exit `10` from compare means reconciliation is
required because the delta is outside the envelope; it is not a terminal ownership verdict. Exit `2`
means invalid input, inconsistent capture, or invalid artifact and routes to the failure matrix.
