# External Planning Workspace

This shared tool prepares one planning workspace outside the product
`Project-Root`. Resolve it from the canonical physical `iis-skills` repository;
do not search for a same-named copy.

```text
python3 planning-workspace/planning_workspace.py prepare \
  (--project-root <canonical-existing-product-root> | \
   --future-project-root <normalized-absolute-future-root>) \
  --work-slug <lowercase-kebab-case> \
  [--workspace <exact-external-workspace>]
```

Use `--future-project-root` only while drafting or approving a Spec before the
product root is provisioned. The helper validates the absolute lexical identity
and requires its deepest existing canonical non-symlink ancestor to be
current-user-owned, safely permissioned, writable, and searchable. It checks
disjointness as far as the absent path permits and does not create the future root. Its result
has `rootReady: false`. Once that exact root exists, pass the same
`planningWorkspace` through `--workspace` with strict `--project-root` before
creating a `ready` Ticket.

Without `--workspace`, it exclusively creates
`/tmp/opencode/planning/<task-owned-id>/<work-slug>/`. It validates the managed
ancestor owner, permissions, and non-symlink identity, creates owner-only task
directories, and never adopts an existing generated task path.
Reusing a generated workspace with `--workspace` revalidates the complete
managed root, task-directory, and workspace chain. Changed ownership, unsafe
permissions, or symlink/retargeted identity fails closed. Generated task and
workspace directories must retain exact mode `0700`. Any supplied path below
the default planning root remains in the generated namespace: it must have the
exact `<task-owned-id>/<work-slug>` shape and match the supplied work slug, and
cannot be reclassified as a durable user-supplied workspace.

An explicitly supplied workspace may be an existing durable directory or a new
exact directory under an existing canonical safe parent. It must be owned and
writable by the current user, non-symlink, canonical, and not group/world
writable. Default and supplied workspaces must be disjoint from the product root:
neither may equal, contain, or be contained by it.

The JSON `planningWorkspace` is the canonical identity for the whole planning
flow. Preserve it in current planning context and pass it back with
`--workspace` for every later artifact. Do not create a new task identity per
Spec, Ticket, Wayfinder, Handoff, research report, Project Map, or Matt brief.
Existing planning input inside a product `.scratch` remains readable but is not
a valid destination for newly generated planning Markdown.

Any helper failure is terminal for workspace preparation. A planning agent must
not manually create, repair, or adopt a workspace as a fallback.
