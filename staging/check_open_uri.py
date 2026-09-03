#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def write_executable(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(0o755)


with tempfile.TemporaryDirectory(prefix="ttyd-open-uri-") as tmp:
    tmp_path = Path(tmp)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    argv_log = tmp_path / "argv.log"
    marker = tmp_path / "SHOULD_NOT_EXIST"

    write_executable(fake_bin / "xset", "#!/bin/sh\nexit 0\n")
    write_executable(
        fake_bin / "xdg-open",
        textwrap.dedent(
            f"""\
            #!/bin/sh
            printf '%s\\n' "$#" > {argv_log}
            for arg in "$@"; do
              printf '%s\\n' "$arg" >> {argv_log}
            done
            exit 0
            """
        ),
    )

    harness = tmp_path / "open_uri_harness.c"
    harness.write_text(
        textwrap.dedent(
            """\
            int open_uri(char *uri);

            int main(int argc, char **argv) {
              if (argc != 2) return 2;
              return open_uri(argv[1]);
            }
            """
        )
    )

    binary = tmp_path / "open_uri_harness"
    cc = os.environ.get("CC", "cc")
    subprocess.run(
        [cc, str(harness), str(ROOT / "src" / "utils.c"), "-o", str(binary)],
        check=True,
        cwd=ROOT,
    )

    uri = f"http://example.invalid/;touch {marker} & echo $HOME `id` | cat > /tmp/nope ' quote"
    env = os.environ.copy()
    env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
    subprocess.run([str(binary), uri], check=True, env=env, cwd=ROOT)

    assert not marker.exists(), marker
    lines = argv_log.read_text().splitlines()
    assert lines == ["1", uri], lines

    print(
        {
            "xdgOpenExecuted": True,
            "argc": int(lines[0]),
            "uriPreservedAsSingleArg": lines[1] == uri,
            "markerInjection": marker.exists(),
        }
    )
