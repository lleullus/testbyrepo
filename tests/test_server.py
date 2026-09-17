"""Backend regressions for production startup refusal and shutdown settlement."""

from __future__ import annotations

import asyncio
import hashlib
import io
from pathlib import Path
import sys
import time

from PIL import Image
import pytest
from starlette.testclient import TestClient

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


def test_initial_sse_subscription_replays_latest_snapshot(tmp_path: Path) -> None:
    store = TransactionalStore.create_project(tmp_path / "project")
    broadcaster = server_module.SnapshotBroadcaster(store, "font-hash")
    initial = {"authority_revision": 0, "cuts": []}
    broadcaster.publish(initial)

    _queue, replay = broadcaster.subscribe(None)

    assert len(replay) == 1
    assert replay[0].event == "studio.snapshot"
    assert replay[0].data["snapshot"] == initial


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


def test_plan002_snapshot_and_enqueue_dto_sequence_projection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_dir = tmp_path / "proj_server_seq"
    store = TransactionalStore.create_project(project_dir)
    revision = _approve_baseline(store)

    static_dir = tmp_path / "static"
    _write_static_bundle(static_dir)
    monkeypatch.setattr(server_module, "STATIC_DIR", static_dir)

    app = create_app(project_dir, FONT_PATH.resolve())

    with TestClient(app) as client:
        # 1. Initial snapshot check
        resp = client.get("/api/studio/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        for cut in data["cuts"]:
            assert "latest_generation_request_seq" in cut
            assert cut["latest_generation_request_seq"] == 0

        # 2. Enqueue generation jobs
        post_resp = client.post(
            "/api/generation/jobs",
            json={"expected_authority_revision": revision, "cut_id": 2},
        )
        assert post_resp.status_code == 200
        post_data = post_resp.json()
        # Created jobs in response must expose request_seq
        created_jobs = post_data.get("jobs", [])
        assert len(created_jobs) == 1
        assert created_jobs[0]["cut_id"] == 2
        assert created_jobs[0]["request_seq"] == 1

        # Snapshot in response must expose both sequence fields
        snap_data = post_data.get("snapshot", {})
        cut2 = [c for c in snap_data["cuts"] if c["cut_id"] == 2][0]
        assert cut2["latest_generation_request_seq"] == 1
        job_in_snap = [j for j in snap_data["jobs"] if j["job_id"] == created_jobs[0]["job_id"]][0]
        assert job_in_snap["request_seq"] == 1

        # 3. Fresh GET snapshot check matches store snapshot values exactly
        store_snap = store.snapshot()
        fresh_resp = client.get("/api/studio/snapshot")
        assert fresh_resp.status_code == 200
        fresh_data = fresh_resp.json()
        for c_dto, c_store in zip(fresh_data["cuts"], store_snap["cuts"]):
            assert c_dto["cut_id"] == c_store["cut_id"]
            assert c_dto["latest_generation_request_seq"] == c_store["latest_generation_request_seq"]
        for j_dto, j_store in zip(fresh_data["jobs"], store_snap["jobs"]):
            assert j_dto["job_id"] == j_store["job_id"]
            assert j_dto["request_seq"] == j_store["request_seq"]


def _setup_server_project_with_five_current_cuts(
    project_dir: Path,
) -> tuple[TransactionalStore, int, int, list[str]]:
    store = TransactionalStore.create_project(project_dir)
    revision = _approve_baseline(store)

    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
    canonical_hashes: list[str] = []
    for idx, col in enumerate(colors):
        cid = idx + 1
        img = Image.new("RGB", (1024, 1536), col)
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        png_bytes = bio.getvalue()
        chash = hashlib.sha256(png_bytes).hexdigest()
        canonical_hashes.append(chash)
        asset_id = f"asset-cut-{cid}-{chash[:8]}"
        rel_path = f"assets/realizations/cut-{cid}/rev-1-{asset_id}.png"
        abs_path = project_dir / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(png_bytes)

        with store._connect() as con:
            revision += 1
            con.execute("BEGIN IMMEDIATE;")
            con.execute(
                """
                UPDATE cuts
                SET realized_revision = 1,
                    realized_asset_id = ?,
                    realized_asset_path = ?,
                    realized_content_hash = ?
                WHERE cut_id = ?
                """,
                (asset_id, rel_path, chash, cid),
            )
            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (revision,))
            con.execute("COMMIT;")

    comp = {
        "schema_version": 2,
        "canvas_width_px": 1024,
        "gap_px": 10,
        "slot_heights_px": [1528, 1528, 1528, 1528, 1528],
        "fit": "contain",
        "font_sha256": "acb6440a713d880a13a21b468ba7cd43f5a2b2934972e51be791c880730777b8",
        "bubbles": [],
    }
    revision, comp_rev = store.accept_composition(revision, 0, comp)
    return store, revision, comp_rev, canonical_hashes


def test_plan003_review_materialize_route_race_before_registration_returns_artifact_not_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PLAN-003 Route Regression: POST /api/review-artifacts returns HTTP 409 artifact_not_current when race occurs before registration.

    1. Seed 5 current cuts and composition.
    2. First POST /api/review-artifacts materializes and returns HTTP 200 with artifact receipt.
    3. Second POST /api/review-artifacts encounters same-revision enqueue right before registration.
    4. Duplicate convergence catches sequence-staleness and raises ArtifactNoLongerCurrentError.
    5. Server returns HTTP 409 Conflict with code artifact_not_current.
    6. Historical GET /api/review-artifacts/{id} and content still succeed with 200 OK.
    7. Artifact row, file, and canonical assets remain intact.
    """
    project_dir = tmp_path / "proj_server_race_before_reg"
    store, rev, comp_rev, canonical_hashes = _setup_server_project_with_five_current_cuts(project_dir)

    static_dir = tmp_path / "static"
    _write_static_bundle(static_dir)
    monkeypatch.setattr(server_module, "STATIC_DIR", static_dir)

    app = create_app(project_dir, FONT_PATH.resolve())

    with TestClient(app) as client:
        # 1. Initial materialization succeeds with 200 OK
        resp1 = client.post(
            "/api/review-artifacts",
            json={"expected_authority_revision": rev, "expected_composition_revision": comp_rev},
        )
        assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}: {resp1.text}"
        art1_data = resp1.json()["artifact"]
        art1_id = art1_data["artifact_id"]
        art1_hash = art1_data["content_hash"]

        fresh_rev = store.snapshot()["authority_revision"]

        # 2. Race on second materialize: hook app.state.store.register_review_artifact to enqueue same-revision generation
        orig_register = app.state.store.register_review_artifact

        def hooked_register(*args, **kwargs):
            cur_auth = app.state.store.snapshot()["authority_revision"]
            app.state.store.enqueue_generation_jobs(expected_authority_revision=cur_auth, cut_id=1)
            return orig_register(*args, **kwargs)

        app.state.store.register_review_artifact = hooked_register

        try:
            race_resp = client.post(
                "/api/review-artifacts",
                json={"expected_authority_revision": fresh_rev, "expected_composition_revision": comp_rev},
            )
        finally:
            app.state.store.register_review_artifact = orig_register
        assert race_resp.status_code == 409
        race_error = race_resp.json()["error"]
        assert race_error["code"] == "artifact_not_current"
        assert race_error["message"] == "Review artifact is not current"
        assert race_error["current_snapshot"]["realization_complete"]["complete"] is False
        assert race_error["current_snapshot"]["realization_complete"]["status"] == "UNRESOLVED"
        assert race_error["current_snapshot"]["cuts"][0]["currency"] == "STALE"

        # 4. Historical read via GET /api/review-artifacts/{artifact_id} succeeds with 200
        get_resp = client.get(f"/api/review-artifacts/{art1_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["artifact_id"] == art1_id
        assert get_resp.json()["content_hash"] == art1_hash

        # 5. Content read via GET /api/review-artifacts/{artifact_id}/content succeeds
        content_resp = client.get(f"/api/review-artifacts/{art1_id}/content")
        assert content_resp.status_code == 200
        assert content_resp.headers["content-type"] == "image/png"
        assert hashlib.sha256(content_resp.content).hexdigest() == art1_hash

        # 6. Canonical realizations and review artifact row in SQLite preserved
        fresh_store_snap = store.snapshot()
        assert len(fresh_store_snap["review_artifacts"]) == 1
        assert fresh_store_snap["review_artifacts"][0]["artifact_id"] == art1_id
        for c_row, expected_hash in zip(fresh_store_snap["cuts"], canonical_hashes):
            assert c_row["realized_content_hash"] == expected_hash
            c_path = project_dir / c_row["realized_asset_path"]
            assert c_path.is_file()
            assert hashlib.sha256(c_path.read_bytes()).hexdigest() == expected_hash


def test_plan003_review_materialize_route_race_after_registration_returns_artifact_not_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PLAN-003 Route Regression: POST /api/review-artifacts returns HTTP 409 artifact_not_current when race occurs after registration.

    1. Seed 5 current cuts and composition.
    2. Hook register_review_artifact: let it register and commit successfully, then immediately
       enqueue same-revision regeneration for cut 2 before returning.
    3. POST /api/review-artifacts readback catches sequence-staleness and raises ArtifactNoLongerCurrentError.
    4. Server returns HTTP 409 Conflict with code artifact_not_current.
    5. Newly registered artifact is preserved in DB and on disk.
    6. Historical GET /api/review-artifacts/{id} and content still succeed with 200 OK.
    7. Canonical realization assets remain intact.
    """
    project_dir = tmp_path / "proj_server_race_after_reg"
    store, rev, comp_rev, canonical_hashes = _setup_server_project_with_five_current_cuts(project_dir)

    static_dir = tmp_path / "static"
    _write_static_bundle(static_dir)
    monkeypatch.setattr(server_module, "STATIC_DIR", static_dir)

    app = create_app(project_dir, FONT_PATH.resolve())

    with TestClient(app) as client:
        orig_register = app.state.store.register_review_artifact
        registered_id: str | None = None
        registered_hash: str | None = None

        def hooked_register(expected_authority_revision, artifact_id, content_hash, composition_revision, cut_closure):
            nonlocal registered_id, registered_hash
            registered_id = artifact_id
            registered_hash = content_hash
            orig_register(
                expected_authority_revision=expected_authority_revision,
                artifact_id=artifact_id,
                content_hash=content_hash,
                composition_revision=composition_revision,
                cut_closure=cut_closure,
            )
            cur_auth = app.state.store.snapshot()["authority_revision"]
            app.state.store.enqueue_generation_jobs(expected_authority_revision=cur_auth, cut_id=2)

        app.state.store.register_review_artifact = hooked_register
        try:
            race_resp = client.post(
                "/api/review-artifacts",
                json={"expected_authority_revision": rev, "expected_composition_revision": comp_rev},
            )
        finally:
            app.state.store.register_review_artifact = orig_register

        # Must return HTTP 409 Conflict with artifact_not_current
        assert race_resp.status_code == 409
        race_error = race_resp.json()["error"]
        assert race_error["code"] == "artifact_not_current"
        assert race_error["message"] == "Review artifact is not current"
        assert race_error["current_snapshot"]["realization_complete"]["complete"] is False
        assert race_error["current_snapshot"]["realization_complete"]["status"] == "UNRESOLVED"
        assert race_error["current_snapshot"]["cuts"][1]["currency"] == "STALE"

        # Newly registered artifact is preserved in DB and on disk
        assert registered_id is not None
        assert registered_hash is not None

        # Historical read succeeds
        get_resp = client.get(f"/api/review-artifacts/{registered_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["artifact_id"] == registered_id
        assert get_resp.json()["content_hash"] == registered_hash

        content_resp = client.get(f"/api/review-artifacts/{registered_id}/content")
        assert content_resp.status_code == 200
        assert hashlib.sha256(content_resp.content).hexdigest() == registered_hash

        # Canonical realization assets preserved
        fresh_snap = store.snapshot()
        for c_row, expected_hash in zip(fresh_snap["cuts"], canonical_hashes):
            assert c_row["realized_content_hash"] == expected_hash
            c_path = project_dir / c_row["realized_asset_path"]
            assert c_path.is_file()
            assert hashlib.sha256(c_path.read_bytes()).hexdigest() == expected_hash
