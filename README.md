# Logtrim

Offline log trimming utility for Linux, Kubernetes, pod, component, and journal output.

## What It Does

Logtrim reads raw text from `input.txt`, compresses repeated noise, and writes a readable summary to `output.txt`.

It is designed for offline use on Windows inside a `venv` and uses only the Python standard library for the core path.

It keeps source families separate:

- Linux event logs
- Kubernetes pod logs
- Pod-internal application logs
- Kubernetes component logs
- `kubectl get` snapshot output
- `kubectl describe` structured output

It prefers under-merging to over-merging, so distinct failures stay visible even if some duplicates remain unmerged.

## Installation

### Option A: One-click setup (recommended)

If you received this project as a zip/tar.gz archive:

1. Extract the archive
2. Run **one** of these commands in the extracted folder:

**Windows:** Double-click `setup.bat` or run from Command Prompt:
```cmd
setup.bat
```

**Linux / macOS:** Run from Terminal:
```bash
./setup.sh
```

This creates a `.venv` virtual environment and installs `logtrim` automatically. After setup, you can use the `logtrim` command directly (Windows) or via `python -m logtrim` (any platform).

### Option B: pip / pipx

If you have the project source locally:

```bash
# Using pipx (recommended for CLI tools)
pipx install .

# Or using pip
pip install .
```

Then run:
```bash
logtrim --input your-log.txt
```

## Quick Start

Place a log file as `input.txt` in the project root, then:

```bash
logtrim --input input.txt
```

Open `output.txt` to see the grouped summary.

## Required Files

- Put the raw capture in `input.txt` at the project root.
- The tool writes the result to `output.txt` in the same directory.
- You can override both paths with `--input` and `--output`.

## Command Line

Default run:

```bash
logtrim --input input.txt --output output.txt
```

The available options are:

- `--input` defaults to `input.txt`
- `--output` defaults to `output.txt`

## Supported Inputs

Logtrim understands mixed captures and routes them by family.

Event stream logs:

- Linux syslog-like output
- `journalctl` output
- Kubernetes component logs
- pod-internal application logs

JSON logs:

- One JSON object per line
- Wrapped JSON across multiple lines
- JSON arrays of log records

Snapshot output:

- `kubectl get pod`
- `kubectl get node`
- similar tabular `kubectl get` output

Structured descriptions:

- `kubectl describe pod`
- `kubectl describe node`
- similar sectioned `kubectl describe` output

## How Output Is Structured

Event logs are grouped into blocks that look like:

```text
[count] canonical pattern
count: count
sample: example record
first_seen: first example
last_seen: last example
```

Snapshot output is summarized as a state snapshot instead of a raw event stream.

Describe output is summarized by section instead of line-by-line similarity.

## Typical Workflow

1. Save a raw capture into `input.txt`.
2. Run `logtrim`.
3. Open `output.txt` and review the grouped summary.
4. If needed, rerun with `--input` or `--output` to use different paths.

## Examples

Example event log input:

```text
2026-04-07T11:00:00Z app[1]: Failed to start
Traceback (most recent call last):
  File "app.py", line 1, <module>
ValueError: bad input
```

Example output:

```text
Event Logs
[1] <TS> app[<PID>]: Failed to start
Traceback (most recent call last):
  File "app.py", line 1, <module>
ValueError: bad input
count: 1
sample: 2026-04-07T11:00:00Z app[1]: Failed to start
Traceback (most recent call last):
  File "app.py", line 1, <module>
ValueError: bad input
first_seen: 2026-04-07T11:00:00Z app[1]: Failed to start
Traceback (most recent call last):
  File "app.py", line 1, <module>
ValueError: bad input
last_seen: 2026-04-07T11:00:00Z app[1]: Failed to start
Traceback (most recent call last):
  File "app.py", line 1, <module>
ValueError: bad input
```

Example snapshot input:

```text
NAME READY STATUS RESTARTS AGE
api-7c9d8f6b7c-abc12 1/1 Running 0 2d
api-7c9d8f6b7c-def34 0/1 CrashLoopBackOff 4 2d
```

Example snapshot output:

```text
Snapshot Output
Pods by workload and state:
- api: CrashLoopBackOff (1 pod), Running (1 pod)
```

## Testing

From the project root:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Troubleshooting

**Setup shows "externally-managed-environment" error (Debian/Ubuntu)**

This happens on minimal Linux installs where `python3-venv` is not installed. The setup script handles this automatically by installing directly to your system. If it fails:

```bash
# Option A: Install the venv package and retry
sudo apt install python3-venv
bash setup.sh

# Option B: Create a virtual environment manually
python3 -m venv .venv
source .venv/bin/activate
pip install .

# Option C: Force install system-wide (may need sudo)
sudo pip3 install --break-system-packages .
```

**`logtrim` command not found after setup on Linux**

After a direct (non-venv) install, `logtrim` goes to `~/.local/bin/`. If that's not on your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
# Or add it to ~/.bashrc permanently
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

**On Windows, logtrim command not available after setup closes**

Use `logtrim.bat` (created by setup) or activate the venv first:

```cmd
call .venv\Scripts\activate.bat
logtrim --input input.txt
```

## Notes

- The tool writes `output.txt` only after successful processing.
- If `input.txt` is missing, the command fails clearly and does not create a misleading output file.
- The project is intentionally stdlib-only for the main compression path.
