# Project-Local Planning Root

IIS keeps durable planning and authority artifacts in one canonical location:

```text
<Project-Root>/docs/planning/
```

Prepare or revalidate it with:

```text
python3 planning-workspace/planning_workspace.py prepare \
  --project-root <canonical-existing-project-root> \
  --work-slug <lowercase-kebab-case-slug> \
  [--kind work|initiative]
```

The helper returns `planningRoot`, the persistent `behaviorRoot`, and the
work- or initiative-specific `artifactWorkspace`. It may create directories
below an existing project root, but it never creates the project root itself.
It rejects symlinked, non-canonical, unsafe, or external workspace paths.

```text
docs/planning/
├── behavior/
│   ├── INDEX.md
│   ├── contexts/
│   ├── lifecycles/
│   └── invariants/
├── work/<work-slug>/
│   ├── DESIGN.md
│   ├── SPEC.md
│   └── tickets/
└── initiatives/<initiative-slug>/
    ├── PROJECT-MAP.md
    └── matt-briefs/
```

Approved Behavior, Design, Spec, Project Map, brief, and Ticket artifacts live
with the project and its Git branch. Planning roles may mutate only
`docs/planning/**` before implementation. Product source, tests, configuration,
data, and runtime state remain outside planning authority.

Legacy external planning artifacts may be read as historical context, but IIS
does not adopt them as current authority or use them as a new destination.
