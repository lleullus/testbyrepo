"""Backend regressions for production startup refusal and shutdown settlement."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import time

import pytest

from comic_new.generation import (
    GenerationService,
    find_session_or_group_pids,
    is_pid_non_zombie_alive,
)
from comic_new.server import ServerPreflightError, create_app
import comic_new.server as server_module
from comic_new.store import TransactionalStore

FONT_PATH = Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf")
CONTROLLED_PROVIDER = Path(__file__).parent / "mock_provider.py"


def _write_static_bundle(static_dir: Path, *, include_css: bool = True) -> None:
    assets = static_dir / "assets"
    assets.mkdir(parents=True)
    (assets / "index-AbCd1234.js").write_text("export {};", encoding="utf-8")
    if include_css:
        (assets / "index-EfGh5678.css").write_text(":root {}", encoding="utf-8")
    (static_dir / "index.html").write_text(
        '<!doctype html><html><head><link rel="stylesheet" href="/assets/index-EfGh5678.css"></head>'
        '<body><div id="app"></div><script type="module" src="/assets/index-AbCd1234.js"></script></body></html>',
        encoding="utf-8",
    )


def _approve_baseline(store: TransactionalStore) -> int:
    structure = {
        "source_brief": "Shutdown settlement",
        "cuts": [
            {"cut_id": cut_id, "role": f"Role {cut_id}", "beat": f"Beat {cut_id}"}
            for cut_id in range(1, 6)
        ],
    }
    intents = {
        cut_id: {"prompt": f"Long-running cut {cut_id}", "dialogue": ""}
        for cut_id in range(1, 6)
    }
    return store.approve_structural_baseline(0, "baseline-server-test", structure, intents)


@pytest.mark.parametrize("failure", ["missing-index", "missing-referenced-asset"])
def test_create_app_refuses_incomplete_generated_static(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    project_dir = tmp_path / "project"
    TransactionalStore.create_project(project_dir)
    static_dir = tmp_path / "static"
    if failure == "missing-referenced-asset":
        _write_static_bundle(static_dir, include_css=False)
    else:
        static_dir.mkdir()
    monkeypatch.setattr(server_module, "STATIC_DIR", static_dir)

    with pytest.raises(ServerPreflightError, match="missing"):
        create_app(project_dir, FONT_PATH.resolve())


def test_lifespan_shutdown_settles_real_process_tree_and_preserves_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dir = tmp_path / "project"
    store = TransactionalStore.create_project(project_dir)
    revision = _approve_baseline(store)
    GenerationService(store).enqueue(expected_authority_revision=revision)

    static_dir = tmp_path / "static"
    _write_static_bundle(static_dir)
    monkeypatch.setattr(server_module, "STATIC_DIR", static_dir)
    monkeypatch.setenv("COMIC_NEW_IMA2_BIN", f"{sys.executable} {CONTROLLED_PROVIDER}")
    monkeypatch.setenv("MOCK_SLEEP", "60")
    monkeypatch.setenv("MOCK_SPAWN_DESCENDANT", "1")

    app = create_app(project_dir, FONT_PATH.resolve())
    observed_processes: set[int] = set()

    async def run_lifecycle() -> None:
        async with app.router.lifespan_context(app):
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                snapshot = store.snapshot()
                for job in snapshot["jobs"]:
                    for attempt in job["attempts"]:
                        pid = attempt.get("process_pid")
                        pgid = attempt.get("process_group_id")
                        token = attempt.get("process_start_token")
                        if pid:
                            observed_processes.add(pid)
                        if pgid:
                            observed_processes.update(find_session_or_group_pids(pgid, token))
                if len(observed_processes) >= 2:
                    break
                await asyncio.sleep(0.05)
            assert len(observed_processes) >= 2, "provider root and descendant did not both start"

    asyncio.run(run_lifecycle())

    for pid in observed_processes:
        assert not is_pid_non_zombie_alive(pid), f"generation process {pid} survived server shutdown"

    fresh = TransactionalStore.open_project(project_dir).snapshot()
    assert all(job["status"] not in {"queued", "running"} for job in fresh["jobs"])
    assert all(cut["desired_revision"] == 1 for cut in fresh["cuts"])
    assert all(cut["currency"] == "STALE" for cut in fresh["cuts"])
    assert fresh["realization_complete"] == {"complete": False, "status": "UNRESOLVED"}
