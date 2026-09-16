"""Comprehensive test suite for BLOCK-05 Release Authorization & Destination Readback.

Covers Scope Acceptance A-G and Baseline Exit 1-33:
- Acceptance A (Exit 1-4): Release authorization binding and restart persistence
- Acceptance B (Exit 5-9, Gate 2): Immediate revocation upon recipient-perceptible mutation
- Acceptance C (Exit 10-14, Gate 1): All-or-Nothing integrity gates (stale cut, missing assets)
- Acceptance D (Exit 15-18): Lossless zero-reflow canonical PNG export
- Acceptance E (Exit 19-23): Blogger delivery with destination readback
- Acceptance F (Exit 24-29, Gate 4): Honest unknown preservation on timeout/disconnect
- Acceptance G (Exit 30-33): Counterexample gates (Gate 1 Currency, Gate 2 Identity, Gate 3 Interruption, Gate 4 External Truth)
"""

from __future__ import annotations

import hashlib
import http.server
import json
import os
from pathlib import Path
import threading
import time
from typing import Any
import urllib.parse
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from comic_new.composition import CANONICAL_HEIGHT, CANONICAL_WIDTH
from comic_new.composition_service import CompositionService
from comic_new.delivery import (
    BloggerAuthoritativeError,
    BloggerTransportTimeoutError,
    ControlledBloggerAdapter,
    DeliveryService,
    GoogleBloggerAdapter,
    ReleasePreflightError,
    SourceAssetMissingError,
)
from comic_new.server import create_app
from comic_new.store import (
    AuthorizationRevokedError,
    ConflictError,
    InvalidArtifactClosureError,
    RealizationIncompleteError,
    TransactionalStore,
)
from test_composition import setup_project_with_five_current_cuts, SYSTEM_FONT_PATH, EXPECTED_FONT_HASH


def _setup_full_project(project_dir: Path):
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)
    comp_state = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [
            {
                "bubble_id": "b-1",
                "cut_id": 1,
                "shape": "ellipse",
                "x_pct": 10.0,
                "y_pct": 2.0,
                "w_pct": 30.0,
                "h_pct": 6.0,
                "text": "Hello world!",
                "font_size_pct": 2.0,
                "line_spacing_pct": 20.0,
                "text_align": "center",
                "text_rgba": "#000000FF",
                "fill_rgba": "#FFFFFFFF",
                "outline_rgba": "#000000FF",
                "outline_width_pct": 0.2,
                "padding_pct": 5.0,
            }
        ],
    }
    rev, comp_rev = store.accept_composition(rev, 0, comp_state)
    comp_svc = CompositionService(store, SYSTEM_FONT_PATH)
    mat = comp_svc.materialize(rev, comp_rev)
    rev = store.snapshot()["authority_revision"]
    return store, comp_svc, mat, rev


def test_acceptance_a_authorization_binding_and_restart(tmp_path: Path):
    """Acceptance A / Baseline Exit 1-4: Exact binding, restart persistence, separate attempts."""
    project_dir = tmp_path / "proj_a"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)

    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    # 1. Snapshot and SQLite readback
    snap = store.snapshot()
    active_auth = snap["release_authorization"]["active"]
    assert active_auth is not None
    assert active_auth["authorization_id"] == auth_id
    assert active_auth["artifact_id"] == mat.artifact_id
    assert active_auth["artifact_content_hash"] == mat.content_hash
    assert active_auth["revoked_authority_revision"] is None

    # Delivery attempts must remain empty on authorization
    assert len(snap["delivery_attempts"]) == 0

    # 2. Server restart simulation: close and reopen store
    reopened = TransactionalStore.open_project(project_dir)
    reopened_snap = reopened.snapshot()
    reopened_auth = reopened_snap["release_authorization"]["active"]
    assert reopened_auth is not None
    assert reopened_auth["authorization_id"] == auth_id
    assert reopened_auth["artifact_content_hash"] == mat.content_hash
    assert len(reopened_snap["delivery_attempts"]) == 0


def test_acceptance_b_revocation_on_mutations_and_gate_2(tmp_path: Path):
    """Acceptance B / Baseline Exit 5-9 & Gate 2: Revocation on text, geometry, gap, style, intent, baseline."""
    # Sub-case 1: Text modification revokes authorization
    project_dir = tmp_path / "proj_b1"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    # Mutate 1 bubble character
    snap = store.snapshot()
    comp = dict(snap["composition"]["state"])
    comp["bubbles"] = [dict(comp["bubbles"][0], text="Hello world!!")]
    rev, _ = store.accept_composition(rev, snap["composition"]["revision"], comp)

    # Verify authorization is immediately revoked
    fresh_snap = store.snapshot()
    assert fresh_snap["release_authorization"]["active"] is None
    history = fresh_snap["release_authorization"]["history"]
    assert len(history) == 1
    assert history[0]["authorization_id"] == auth_id
    assert history[0]["revoked_authority_revision"] == rev

    # Gate 2: Release attempt with old authorization must fail
    delivery_svc = DeliveryService(store, comp_svc)
    with pytest.raises(AuthorizationRevokedError):
        delivery_svc.export_png(rev, authorization_id=auth_id)

    # Sub-case 2: Gap modification revokes authorization
    project_dir2 = tmp_path / "proj_b2"
    store2, comp_svc2, mat2, rev2 = _setup_full_project(project_dir2)
    auth_id2 = f"auth-{mat2.artifact_id}"
    rev2 = store2.authorize_release(rev2, auth_id2, mat2.artifact_id, mat2.content_hash)

    snap2 = store2.snapshot()
    comp2 = dict(snap2["composition"]["state"])
    comp2["gap_px"] = 15  # 10 -> 15
    rev2, _ = store2.accept_composition(rev2, snap2["composition"]["revision"], comp2)
    assert store2.snapshot()["release_authorization"]["active"] is None

    # Sub-case 3: Cut intent modification revokes authorization
    project_dir3 = tmp_path / "proj_b3"
    store3, comp_svc3, mat3, rev3 = _setup_full_project(project_dir3)
    auth_id3 = f"auth-{mat3.artifact_id}"
    rev3 = store3.authorize_release(rev3, auth_id3, mat3.artifact_id, mat3.content_hash)

    rev3 = store3.accept_cut_intent(rev3, 3, {"prompt": "New prompt for cut 3", "text": "New intent"})
    assert store3.snapshot()["release_authorization"]["active"] is None

    # Sub-case 4: Bubble geometry modification (x, y, w, h) revokes authorization
    project_dir4 = tmp_path / "proj_b4"
    store4, comp_svc4, mat4, rev4 = _setup_full_project(project_dir4)
    auth_id4 = f"auth-{mat4.artifact_id}"
    rev4 = store4.authorize_release(rev4, auth_id4, mat4.artifact_id, mat4.content_hash)
    snap4 = store4.snapshot()
    comp4 = dict(snap4["composition"]["state"])
    comp4["bubbles"] = [dict(comp4["bubbles"][0], x_pct=15.0)]
    rev4, _ = store4.accept_composition(rev4, snap4["composition"]["revision"], comp4)
    assert store4.snapshot()["release_authorization"]["active"] is None

    # Sub-case 5: Bubble style modification (fill_rgba) revokes authorization
    project_dir5 = tmp_path / "proj_b5"
    store5, comp_svc5, mat5, rev5 = _setup_full_project(project_dir5)
    auth_id5 = f"auth-{mat5.artifact_id}"
    rev5 = store5.authorize_release(rev5, auth_id5, mat5.artifact_id, mat5.content_hash)
    snap5 = store5.snapshot()
    comp5 = dict(snap5["composition"]["state"])
    comp5["bubbles"] = [dict(comp5["bubbles"][0], fill_rgba="#FF0000FF")]
    rev5, _ = store5.accept_composition(rev5, snap5["composition"]["revision"], comp5)
    assert store5.snapshot()["release_authorization"]["active"] is None

    # Sub-case 6: Structural baseline approval revokes authorization
    project_dir6 = tmp_path / "proj_b6"
    store6, comp_svc6, mat6, rev6 = _setup_full_project(project_dir6)
    auth_id6 = f"auth-{mat6.artifact_id}"
    rev6 = store6.authorize_release(rev6, auth_id6, mat6.artifact_id, mat6.content_hash)
    rev6 = store6.approve_structural_baseline(
        rev6,
        "base-new-2",
        {"grid": "vertical-5", "title": "New Baseline"},
        {c: {"prompt": f"cut {c}"} for c in range(1, 6)},
    )
    assert store6.snapshot()["release_authorization"]["active"] is None

    # Sub-case 7: Registering a new review artifact revokes active authorization
    project_dir7 = tmp_path / "proj_b7"
    store7, comp_svc7, mat7, rev7 = _setup_full_project(project_dir7)
    auth_id7 = f"auth-{mat7.artifact_id}"
    rev7 = store7.authorize_release(rev7, auth_id7, mat7.artifact_id, mat7.content_hash)
    snap7 = store7.snapshot()
    cut_closure = [
        {"cut_id": c["cut_id"], "realized_revision": c["realized_revision"], "asset_id": c["realized_asset_id"]}
        for c in snap7["cuts"]
    ]
    rev7 = store7.register_review_artifact(
        rev7,
        "art-new-999",
        "hash-new-999",
        snap7["composition"]["revision"],
        cut_closure,
    )
    assert store7.snapshot()["release_authorization"]["active"] is None


def test_acceptance_c_all_or_nothing_integrity_and_gate_1(tmp_path: Path):
    """Acceptance C / Baseline Exit 10-14 & Gate 1: Currency check and physical file validation."""
    project_dir = tmp_path / "proj_c"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    # 1. Gate 1: When cut 2 is STALE, release preflight must reject
    snap = store.snapshot()
    # Mutating cut intent will revoke active authorization, so create a new project branch or test preflight directly
    project_stale = tmp_path / "proj_c_stale"
    store_s, comp_svc_s, mat_s, rev_s = _setup_full_project(project_stale)
    auth_id_s = f"auth-{mat_s.artifact_id}"
    rev_s = store_s.authorize_release(rev_s, auth_id_s, mat_s.artifact_id, mat_s.content_hash)
    # Invalidate cut 2 currency in cuts table by updating cut_intents desired_revision
    with store_s._connect() as con:
        con.execute("BEGIN IMMEDIATE;")
        con.execute(
            "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) "
            "VALUES (2, 999, NULL, '{}', 1, '2026-09-16T00:00:00Z')"
        )
        con.execute("UPDATE cuts SET desired_revision = 999 WHERE cut_id = 2")
        con.execute("COMMIT;")
    
    delivery_svc_s = DeliveryService(store_s, comp_svc_s)
    with pytest.raises(RealizationIncompleteError):
        delivery_svc_s.export_png(rev_s)

    # 2. Simulate physical asset missing for cut 4 on project_dir
    cut4_path = project_dir / "assets" / "realizations" / "cut-4"
    cut4_file = next(cut4_path.glob("*.png"))
    cut4_file.unlink()

    delivery_svc = DeliveryService(store, comp_svc)
    with pytest.raises(SourceAssetMissingError, match="Cut 4 asset file missing"):
        delivery_svc.export_png(rev)

def test_acceptance_d_lossless_png_export(tmp_path: Path):
    """Acceptance D / Baseline Exit 15-18: Zero reflow byte identical export."""
    project_dir = tmp_path / "proj_d"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    delivery_svc = DeliveryService(store, comp_svc)
    out_png = project_dir / "exports" / "comic_final.png"
    result = delivery_svc.export_png(rev, output_path=out_png)

    assert result.outcome == "confirmed_success"
    assert result.content_hash == mat.content_hash

    # Byte identity readback
    exported_bytes = out_png.read_bytes()
    assert hashlib.sha256(exported_bytes).hexdigest() == mat.content_hash

    # Image specs
    with Image.open(out_png) as im:
        assert im.size == (CANONICAL_WIDTH, CANONICAL_HEIGHT)
        assert im.format == "PNG"

    # Verify attempt recorded in DB
    snap = store.snapshot()
    attempts = snap["delivery_attempts"]
    assert len(attempts) == 1
    assert attempts[0]["kind"] == "png"
    assert attempts[0]["outcome"] == "confirmed_success"
    assert attempts[0]["destination_id"] == "comic_final.png"


def test_acceptance_e_blogger_delivery_and_destination_readback(tmp_path: Path):
    """Acceptance E / Baseline Exit 19-23: Blogger delivery with post_id and URL readback."""
    project_dir = tmp_path / "proj_e"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    adapter = ControlledBloggerAdapter(
        mode="success",
        post_id="post-987654",
        destination_url="https://testblog.blogspot.com/2026/09/web-comic-e1.html",
    )
    delivery_svc = DeliveryService(store, comp_svc, adapter)

    result = delivery_svc.deliver_blogger(
        rev,
        blog_id="testblog-1",
        title="Web Comic Episode 1",
        adapter=adapter,
    )

    assert result.outcome == "confirmed_success"
    assert result.destination_id == "post-987654"
    assert result.destination_url == "https://testblog.blogspot.com/2026/09/web-comic-e1.html"

    # Verify adapter received raw canonical PNG bytes
    assert len(adapter.calls) == 1
    call = adapter.calls[0]
    assert call["blog_id"] == "testblog-1"
    assert call["title"] == "Web Comic Episode 1"
    assert call["bytes_len"] == len(mat.bytes_data)

    # Verify SQLite persistence
    snap = store.snapshot()
    attempts = snap["delivery_attempts"]
    assert len(attempts) == 1
    att = attempts[0]
    assert att["kind"] == "blogger"
    assert att["outcome"] == "confirmed_success"
    assert att["destination_id"] == "post-987654"
    assert att["destination_url"] == "https://testblog.blogspot.com/2026/09/web-comic-e1.html"
    assert att["evidence"]["raw_response"]["status"] == "LIVE"


def test_cfw1_lock_separation_during_adapter_delay(tmp_path: Path):
    """CFW-1: Verify SQLite write lock is NOT held during adapter I/O, allowing concurrent snapshot queries."""
    project_dir = tmp_path / "proj_cfw1"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    delay_seconds = 1.0
    adapter = ControlledBloggerAdapter(mode="success", delay_seconds=delay_seconds)
    delivery_svc = DeliveryService(store, comp_svc, adapter)

    delivery_result: list[Any] = []
    delivery_error: list[Exception] = []

    def _worker():
        try:
            res = delivery_svc.deliver_blogger(rev, blog_id="test-blog", adapter=adapter)
            delivery_result.append(res)
        except Exception as e:
            delivery_error.append(e)

    th = threading.Thread(target=_worker, daemon=True)
    th.start()

    # Wait slightly so worker completes start_delivery_attempt (Tx 1) and enters adapter I/O
    time.sleep(0.2)
    assert th.is_alive()

    # Read snapshot concurrently during adapter I/O delay: must return immediately without lock blockage
    t0 = time.perf_counter()
    snap = store.snapshot()
    elapsed = time.perf_counter() - t0

    assert elapsed < 0.2, f"store.snapshot() was blocked for {elapsed:.3f}s, indicating write lock held during adapter I/O"

    # In-flight attempt must be visible with outcome='unknown'
    attempts = snap["delivery_attempts"]
    assert len(attempts) == 1
    assert attempts[0]["outcome"] == "unknown"

    # Wait for delivery to finish
    th.join(timeout=5.0)
    assert not th.is_alive()
    assert not delivery_error
    assert len(delivery_result) == 1
    assert delivery_result[0].outcome == "confirmed_success"

    # Final readback confirms transition to confirmed_success (Tx 2)
    final_snap = store.snapshot()
    final_att = final_snap["delivery_attempts"][0]
    assert final_att["outcome"] == "confirmed_success"


def test_controlled_blogger_adapter_rejects_empty_blog_id(tmp_path: Path):
    """Verify ControlledBloggerAdapter definitively rejects empty or whitespace blog_id."""
    project_dir = tmp_path / "proj_ctrl_empty_blog"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    adapter = ControlledBloggerAdapter(mode="success")
    delivery_svc = DeliveryService(store, comp_svc, adapter)

    res = delivery_svc.deliver_blogger(rev, blog_id="   ", adapter=adapter)
    assert res.outcome == "confirmed_failure"
    assert res.evidence["status_code"] == 400
    assert "Missing Blogger blog id" in res.evidence["message"]

def test_acceptance_f_honest_unknown_preservation_and_gate_4(tmp_path: Path):
    """Acceptance F / Baseline Exit 24-29 & Gate 4: Honest unknown on timeout/disconnect, failure on auth error."""
    # Sub-case 1: Timeout preserves Unknown
    project_dir = tmp_path / "proj_f1"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    timeout_adapter = ControlledBloggerAdapter(mode="timeout")
    delivery_svc = DeliveryService(store, comp_svc, timeout_adapter)

    result = delivery_svc.deliver_blogger(rev, blog_id="test-blog", adapter=timeout_adapter)

    # Gate 4: Timeout MUST NOT invent success. Outcome remains unknown!
    assert result.outcome == "unknown"
    assert result.destination_id is None
    assert result.destination_url is None

    snap = store.snapshot()
    att = snap["delivery_attempts"][-1]
    assert att["outcome"] == "unknown"
    assert att["destination_id"] is None
    assert att["destination_url"] is None
    evidence = att["evidence"]
    assert evidence["error"] == "BloggerTransportTimeoutError"

    # Sub-case 2: Auth rejection records confirmed_failure
    auth_fail_adapter = ControlledBloggerAdapter(mode="auth_failure")
    rev2 = snap["authority_revision"]
    result2 = delivery_svc.deliver_blogger(rev2, blog_id="test-blog", adapter=auth_fail_adapter)

    assert result2.outcome == "confirmed_failure"
    snap2 = store.snapshot()
    att2 = snap2["delivery_attempts"][-1]
    assert att2["outcome"] == "confirmed_failure"
    evidence2 = att2["evidence"]
    assert evidence2["status_code"] == 401


def test_server_api_release_endpoints(tmp_path: Path):
    """Verify FastAPI /api/release/export-png and /api/release/blogger endpoints with ControlledBloggerAdapter."""
    project_dir = tmp_path / "proj_server"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    adapter = ControlledBloggerAdapter(mode="success", post_id="post-api-123", destination_url="https://blogger.com/post-123")
    app = create_app(project_dir, SYSTEM_FONT_PATH, blogger_adapter=adapter)
    with TestClient(app) as client:
        # 1. Export PNG endpoint
        res_export = client.post(
            "/api/release/export-png",
            json={"expected_authority_revision": rev, "output_path": "exports/server_export.png"},
        )
        assert res_export.status_code == 200
        data_export = res_export.json()
        assert data_export["kind"] == "png"
        assert data_export["content_hash"] == mat.content_hash

        # Verify path traversal rejection
        cur_rev = data_export["snapshot"]["authority_revision"]
        res_traversal = client.post(
            "/api/release/export-png",
            json={"expected_authority_revision": cur_rev, "output_path": "../../outside.png"},
        )
        assert res_traversal.status_code == 400
        assert res_traversal.json()["error"]["code"] == "invalid_path"

        # 2. Blogger release endpoint
        cur_rev = client.get("/api/studio/snapshot").json()["authority_revision"]
        res_blogger = client.post(
            "/api/release/blogger",
            json={"expected_authority_revision": cur_rev, "blog_id": "api-blog", "title": "API Episode"},
        )
        assert res_blogger.status_code == 200
        data_blogger = res_blogger.json()
        assert data_blogger["outcome"] == "confirmed_success"
        assert data_blogger["destination_id"] == "post-api-123"
        assert data_blogger["destination_url"] == "https://blogger.com/post-123"
def test_cli_release_commands(tmp_path: Path):
    """Verify CLI export-png and release-blogger subcommands."""
    project_dir = tmp_path / "proj_cli"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    from comic_new.cli import main
    out_file = tmp_path / "cli_exported.png"
    code = main(["export-png", str(project_dir), str(out_file)])
    assert code == 0
    assert out_file.is_file()
    assert hashlib.sha256(out_file.read_bytes()).hexdigest() == mat.content_hash

    code2 = main(["release-blogger", str(project_dir), "--blog-id", "cli-blog", "--title", "CLI Episode"])
    # Missing credentials must not succeed (External Truth / false-success prevention)
    assert code2 == 1
    snap = store.snapshot()
    last_att = snap["delivery_attempts"][-1]
    assert last_att["outcome"] == "confirmed_failure"
    assert last_att["evidence"]["status_code"] == 401
    assert last_att["evidence"]["details"]["configured"] is False


def test_default_delivery_service_uses_google_blogger_adapter_and_rejects_missing_credentials(tmp_path: Path):
    """Verify production DeliveryService defaults to GoogleBloggerAdapter and rejects unconfigured credentials."""
    project_dir = tmp_path / "proj_default_service"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    delivery_svc = DeliveryService(store, comp_svc)
    assert isinstance(delivery_svc.default_blogger_adapter, GoogleBloggerAdapter)
    assert not isinstance(delivery_svc.default_blogger_adapter, ControlledBloggerAdapter)

    result = delivery_svc.deliver_blogger(rev, blog_id="prod-blog", title="Episode 1")
    assert result.outcome == "confirmed_failure"
    assert result.destination_id is None
    assert result.destination_url is None

    snap = store.snapshot()
    attempts = snap["delivery_attempts"]
    assert len(attempts) == 1
    att = attempts[0]
    assert att["outcome"] == "confirmed_failure"
    assert att["evidence"]["status_code"] == 401
    assert att["evidence"]["details"]["configured"] is False


def test_default_server_api_release_endpoints_reject_missing_credentials(tmp_path: Path):
    """Verify production FastAPI server defaults to GoogleBloggerAdapter and rejects release without credentials."""
    project_dir = tmp_path / "proj_default_server"
    store, comp_svc, mat, rev = _setup_full_project(project_dir)
    auth_id = f"auth-{mat.artifact_id}"
    rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

    # Production app without injected adapter
    app = create_app(project_dir, SYSTEM_FONT_PATH)
    with TestClient(app) as client:
        cur_rev = client.get("/api/studio/snapshot").json()["authority_revision"]
        res_blogger = client.post(
            "/api/release/blogger",
            json={"expected_authority_revision": cur_rev, "blog_id": "api-blog", "title": "API Episode"},
        )
        assert res_blogger.status_code == 200
        data_blogger = res_blogger.json()
        assert data_blogger["outcome"] == "confirmed_failure"
        assert data_blogger["destination_id"] is None
        assert data_blogger["destination_url"] is None


class _MockBloggerHttpHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        recorded: list[dict[str, Any]] = getattr(self.server, "recorded_calls", [])
        recorded.append({
            "method": "POST",
            "path": self.path,
            "headers": dict(self.headers),
            "body": body,
        })

        if self.path == "/oauth2/token":
            form = urllib.parse.parse_qs(body.decode("utf-8"))
            if form.get("grant_type") != ["refresh_token"] or not form.get("refresh_token"):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "invalid_grant"}')
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"access_token": "mock-access-token-999"}).encode("utf-8"))
        elif "/posts" in self.path:
            auth = self.headers.get("Authorization") or ""
            if not auth.startswith("Bearer "):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b'{"error": "unauthorized"}')
                return

            post_mode = getattr(self.server, "post_mode", "success")
            if post_mode == "401":
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b'{"error": "unauthorized"}')
                return

            if post_mode == "400":
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": {"code": 400, "message": "Invalid title"}}')
                return
            elif post_mode == "500":
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": {"code": 500, "message": "uncertain"}}')
                return
            elif post_mode == "incomplete":
                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"kind": "blogger#post"}')
                return
            elif post_mode == "timeout":
                time.sleep(1.5)
                self.send_response(504)
                self.end_headers()
                return

            host = self.headers.get("Host") or f"127.0.0.1:{self.server.server_port}"
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "kind": "blogger#post",
                "id": "post-http-real-123",
                "url": f"http://{host}/readback/post-http-real-123.html",
                "status": "LIVE",
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        recorded: list[dict[str, Any]] = getattr(self.server, "recorded_calls", [])
        recorded.append({
            "method": "GET",
            "path": self.path,
            "headers": dict(self.headers),
        })

        readback_mode = getattr(self.server, "readback_mode", "success")
        if self.path == "/readback/post-http-real-123.html":
            if readback_mode == "404":
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")
            elif readback_mode == "timeout":
                time.sleep(1.5)
                self.send_response(504)
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<!DOCTYPE html><html><body><h1>Episode 1 Readback OK</h1></body></html>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def test_google_blogger_adapter_real_local_http_transport_and_readback(tmp_path: Path):
    """Verify GoogleBloggerAdapter performs real HTTP token exchange, Blogger insert, and destination readback."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _MockBloggerHttpHandler)
    server.recorded_calls = []
    server.post_mode = "success"
    server.readback_mode = "success"
    port = server.server_port
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()

    try:
        project_dir = tmp_path / "proj_http_real"
        store, comp_svc, mat, rev = _setup_full_project(project_dir)
        auth_id = f"auth-{mat.artifact_id}"
        rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

        adapter = GoogleBloggerAdapter(
            client_id="my-client-id",
            client_secret="my-client-secret",
            refresh_token="my-refresh-token",
            token_url=f"http://127.0.0.1:{port}/oauth2/token",
            api_base_url=f"http://127.0.0.1:{port}",
            timeout_seconds=5.0,
        )
        delivery_svc = DeliveryService(store, comp_svc, adapter)

        result = delivery_svc.deliver_blogger(
            rev,
            blog_id="test-blog-888",
            title="Real HTTP Episode 1",
            adapter=adapter,
        )

        # 1. Verify outcome confirmed_success
        assert result.outcome == "confirmed_success"
        assert result.destination_id == "post-http-real-123"
        assert result.destination_url == f"http://127.0.0.1:{port}/readback/post-http-real-123.html"

        # 2. Verify all three wire interactions were actually observed by local HTTP server
        calls = server.recorded_calls
        assert len(calls) == 3
        token_call, insert_call, readback_call = calls[0], calls[1], calls[2]

        assert token_call["method"] == "POST"
        assert token_call["path"] == "/oauth2/token"
        parsed_token_body = urllib.parse.parse_qs(token_call["body"].decode("utf-8"))
        assert parsed_token_body["grant_type"] == ["refresh_token"]
        assert parsed_token_body["client_id"] == ["my-client-id"]
        assert parsed_token_body["client_secret"] == ["my-client-secret"]
        assert parsed_token_body["refresh_token"] == ["my-refresh-token"]

        assert insert_call["method"] == "POST"
        assert insert_call["path"] == "/blogs/test-blog-888/posts"
        assert insert_call["headers"]["Authorization"] == "Bearer mock-access-token-999"
        insert_body = json.loads(insert_call["body"].decode("utf-8"))
        assert insert_body["kind"] == "blogger#post"
        assert insert_body["title"] == "Real HTTP Episode 1"
        assert "comic-" in insert_body["content"]

        assert readback_call["method"] == "GET"
        assert readback_call["path"] == "/readback/post-http-real-123.html"
        assert "User-Agent" in readback_call["headers"]

        # 3. Verify SQLite persistence
        snap = store.snapshot()
        attempts = snap["delivery_attempts"]
        assert len(attempts) == 1
        att = attempts[0]
        assert att["outcome"] == "confirmed_success"
        assert att["destination_id"] == "post-http-real-123"
        assert att["destination_url"] == f"http://127.0.0.1:{port}/readback/post-http-real-123.html"
        assert att["evidence"]["raw_response"]["status"] == "LIVE"
    finally:
        server.shutdown()
        server.server_close()


def test_google_blogger_adapter_authoritative_rejection_and_transport_error(tmp_path: Path):
    """Verify real HTTP 404 readback and 400 insert trigger confirmed_failure, while disconnect triggers unknown."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _MockBloggerHttpHandler)
    server.recorded_calls = []
    port = server.server_port
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()

    try:
        project_dir = tmp_path / "proj_http_errors"
        store, comp_svc, mat, rev = _setup_full_project(project_dir)
        auth_id = f"auth-{mat.artifact_id}"
        rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

        # Subcase 1: Destination readback 404 returns confirmed_failure
        server.post_mode = "success"
        server.readback_mode = "404"
        adapter_404 = GoogleBloggerAdapter(
            access_token="direct-token-1",
            api_base_url=f"http://127.0.0.1:{port}",
            timeout_seconds=3.0,
        )
        delivery_svc = DeliveryService(store, comp_svc, adapter_404)
        res1 = delivery_svc.deliver_blogger(rev, blog_id="blog-404", title="Episode 404", adapter=adapter_404)
        assert res1.outcome == "confirmed_failure"
        assert res1.evidence["status_code"] == 404
        assert "Destination URL readback rejected (404)" in res1.evidence["message"]

        # Subcase 2: Blogger insert 400 Bad Request returns confirmed_failure
        server.post_mode = "400"
        rev2 = store.snapshot()["authority_revision"]
        adapter_400 = GoogleBloggerAdapter(
            access_token="direct-token-2",
            api_base_url=f"http://127.0.0.1:{port}",
            timeout_seconds=3.0,
        )
        res2 = delivery_svc.deliver_blogger(rev2, blog_id="blog-400", title="Episode 400", adapter=adapter_400)
        assert res2.outcome == "confirmed_failure"
        assert res2.evidence["status_code"] == 400

        # Subcase 3: Connection refused / transport failure returns honest unknown
        rev3 = store.snapshot()["authority_revision"]
        adapter_conn = GoogleBloggerAdapter(
            access_token="direct-token-3",
            api_base_url="http://127.0.0.1:59998",
            timeout_seconds=0.5,
        )
        res3 = delivery_svc.deliver_blogger(rev3, blog_id="blog-timeout", title="Episode Timeout", adapter=adapter_conn)
        assert res3.outcome == "unknown"
        assert res3.evidence["error"] == "BloggerTransportTimeoutError"

        # Subcase 4: A 5xx after POST may have applied remotely, so it stays unknown.
        server.post_mode = "500"
        rev4 = store.snapshot()["authority_revision"]
        adapter_500 = GoogleBloggerAdapter(
            access_token="direct-token-4",
            api_base_url=f"http://127.0.0.1:{port}",
            timeout_seconds=3.0,
        )
        res4 = delivery_svc.deliver_blogger(rev4, blog_id="blog-500", title="Episode 500", adapter=adapter_500)
        assert res4.outcome == "unknown"

        # Subcase 5: A success response without authoritative identity/readback is unknown.
        server.post_mode = "incomplete"
        rev5 = store.snapshot()["authority_revision"]
        adapter_incomplete = GoogleBloggerAdapter(
            access_token="direct-token-5",
            api_base_url=f"http://127.0.0.1:{port}",
            timeout_seconds=3.0,
        )
        res5 = delivery_svc.deliver_blogger(
            rev5,
            blog_id="blog-incomplete",
            title="Episode Incomplete",
            adapter=adapter_incomplete,
        )
        assert res5.outcome == "unknown"
    finally:
        server.shutdown()
        server.server_close()


def test_cli_release_with_real_local_http_transport(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify CLI release-blogger succeeds against a real local HTTP transport when environment is configured."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _MockBloggerHttpHandler)
    server.recorded_calls = []
    server.post_mode = "success"
    server.readback_mode = "success"
    port = server.server_port
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()

    try:
        project_dir = tmp_path / "proj_cli_http"
        store, comp_svc, mat, rev = _setup_full_project(project_dir)
        auth_id = f"auth-{mat.artifact_id}"
        rev = store.authorize_release(rev, auth_id, mat.artifact_id, mat.content_hash)

        monkeypatch.setenv("BLOGGER_TOKEN_URL", f"http://127.0.0.1:{port}/oauth2/token")
        monkeypatch.setenv("BLOGGER_API_BASE_URL", f"http://127.0.0.1:{port}")
        monkeypatch.setenv("BLOGGER_CLIENT_ID", "cli-cid")
        monkeypatch.setenv("BLOGGER_CLIENT_SECRET", "cli-csec")
        monkeypatch.setenv("BLOGGER_REFRESH_TOKEN", "cli-rtok")

        from comic_new.cli import main
        code = main(["release-blogger", str(project_dir), "--blog-id", "cli-blog", "--title", "CLI Episode"])
        assert code == 0

        snap = store.snapshot()
        last_att = snap["delivery_attempts"][-1]
        assert last_att["outcome"] == "confirmed_success"
        assert last_att["destination_id"] == "post-http-real-123"
        assert last_att["destination_url"] == f"http://127.0.0.1:{port}/readback/post-http-real-123.html"
    finally:
        server.shutdown()
        server.server_close()
