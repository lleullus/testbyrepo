# Baseline Capsule

Shared immutable source-baseline module for the independent Implementation Lead
and Verification Lead skills. It is not an OpenCode skill and owns no planning
or verification lifecycle state.

```bash
python3 baseline_capsule.py create --project-root /absolute/project
python3 baseline_capsule.py identity --project-root /absolute/project
python3 baseline_capsule.py acquire-read --capsule-ref capsule:v1:<id>
python3 baseline_capsule.py release-read --lease-id lease:v1:<capsule-id>:<lease-id>
python3 baseline_capsule.py cleanup-expired
```

The default durable store is
`~/.local/state/opencode/baseline-capsules`. Override it for isolated tests with
`--store-root` or `BASELINE_CAPSULE_STORE`.

See [`PROTOCOL.md`](PROTOCOL.md) for the complete v1 contract.
