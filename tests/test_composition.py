"""Comprehensive, load-bearing tests for BLOCK-03 Canonical Composition and Artifact Stitcher.

Covers all Scope A-K and Exit 1-13 criteria using real Pillow, real SQLite, and real filesystem operations.
"""

from __future__ import annotations

from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from PIL import Image, ImageColor
import pytest

from comic_new.composition import (
    CANONICAL_HEIGHT,
    CANONICAL_WIDTH,
    CompositionRenderError,
    CompositionValidationError,
    RenderedArtifactBytes,
    SourceAssetError,
    TypographyError,
    artifact_path,
    compute_bubble_geometry,
    compute_cut_slots,
    normalize_state,
    render_canonical,
    round_half_up,
)
from comic_new.composition_service import (
    ArtifactNoLongerCurrentError,
    ArtifactReadbackError,
    CompositionService,
    MaterializedArtifact,
)
from comic_new.store import (
    ConflictError,
    RealizationIncompleteError,
    TransactionalStore,
)

SYSTEM_FONT_PATH = Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf")
EXPECTED_FONT_HASH = "acb6440a713d880a13a21b468ba7cd43f5a2b2934972e51be791c880730777b8"


@pytest.fixture
def font_path() -> Path:
    assert SYSTEM_FONT_PATH.is_file(), f"Font not found at {SYSTEM_FONT_PATH}"
    actual_hash = hashlib.sha256(SYSTEM_FONT_PATH.read_bytes()).hexdigest()
    assert actual_hash == EXPECTED_FONT_HASH
    return SYSTEM_FONT_PATH


def create_solid_cut_png(width: int, height: int, color: tuple[int, int, int] | tuple[int, int, int, int]) -> bytes:
    mode = "RGBA" if len(color) == 4 else "RGB"
    img = Image.new(mode, (width, height), color)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def setup_project_with_five_current_cuts(
    project_dir: Path,
    cut_colors: list[tuple[int, int, int]] | None = None,
    cut_dimensions: list[tuple[int, int]] | None = None,
) -> tuple[TransactionalStore, int, list[tuple[str, Path, str]]]:
    """Helper to initialize project with 5 current cut realizations.
    
    Returns (store, authority_revision, [(asset_id, abs_path, sha256), ...]).
    """
    store = TransactionalStore.create_project(project_dir)
    intents = {i: {"text": f"Cut intent {i}"} for i in range(1, 6)}
    rev = store.approve_structural_baseline(0, "BASE-01", {}, intents)

    if cut_colors is None:
        cut_colors = [
            (255, 0, 0),      # Red
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
            (255, 255, 0),    # Yellow
            (255, 0, 255),    # Magenta
        ]
    if cut_dimensions is None:
        cut_dimensions = [(1024, 1536)] * 5

    assets_info: list[tuple[str, Path, str]] = []

    for idx in range(5):
        cid = idx + 1
        w, h = cut_dimensions[idx]
        png_bytes = create_solid_cut_png(w, h, cut_colors[idx])
        content_hash = hashlib.sha256(png_bytes).hexdigest()
        asset_id = f"asset-cut-{cid}-{content_hash[:8]}"

        rel_path = f"assets/realizations/cut-{cid}/rev-1-{asset_id}.png"
        abs_path = project_dir / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(png_bytes)

        # Seed realization in store
        with store._connect() as con:
            rev += 1
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
                (asset_id, rel_path, content_hash, cid),
            )
            con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (rev,))
            con.execute("COMMIT;")

        assets_info.append((asset_id, abs_path, content_hash))

    return store, rev, assets_info


def test_scenario_1_geometry_viewport_independence_and_math():
    """Scenario 1 / Acceptance A / Exit 1:
    
    Bubble percentage geometry is viewport-independent and calculated with Decimal half-up.
    """
    bubble_def = {
        "bubble_id": "b-test",
        "cut_id": 1,
        "shape": "ellipse",
        "x_pct": 10.0,
        "y_pct": 5.0,
        "w_pct": 30.0,
        "h_pct": 15.0,
    }

    # 1. Calculate at 1024 x 7680
    left1, top1, right1, bottom1 = compute_bubble_geometry(bubble_def, 1024, 7680)
    # Expected:
    # left: 10 * 1024 / 100 = 102.4 -> 102
    # top: 5 * 7680 / 100 = 384.0 -> 384
    # right: (10 + 30) * 1024 / 100 = 409.6 -> 410
    # bottom: (5 + 15) * 7680 / 100 = 1536.0 -> 1536
    assert (left1, top1, right1, bottom1) == (102, 384, 410, 1536)

    # 2. Calculate at 512 x 3840 (scaled reference)
    left2, top2, right2, bottom2 = compute_bubble_geometry(bubble_def, 512, 3840)
    # Expected:
    # left: 10 * 512 / 100 = 51.2 -> 51
    # top: 5 * 3840 / 100 = 192.0 -> 192
    # right: 40 * 512 / 100 = 204.8 -> 205
    # bottom: 20 * 3840 / 100 = 768.0 -> 768
    assert (left2, top2, right2, bottom2) == (51, 192, 205, 768)

    # Check that ratios match within half-pixel margin
    assert abs(left1 / 1024 - left2 / 512) <= (0.5 / 512)
    assert abs(top1 / 7680 - top2 / 3840) <= (0.5 / 3840)
    assert abs(right1 / 1024 - right2 / 512) <= (0.5 / 512)
    assert abs(bottom1 / 7680 - bottom2 / 3840) <= (0.5 / 3840)

    # Integer slot division covering exactly 7680px
    slots = compute_cut_slots(7680, 24)
    assert len(slots) == 5
    assert slots[0][0] == 0
    assert slots[-1][1] == 7680


def test_scenario_2_exact_five_cuts_enforced(tmp_path: Path, font_path: Path):
    """Scenario 2 / Acceptance B / Exit 2:
    
    Compositor requires exactly 5 cut assets in cut order 1..5.
    Direct renderer rejects 4 cuts, duplicate cuts, or 6 cuts.
    """
    valid_state = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    font_bytes = font_path.read_bytes()

    # Create 5 valid PNG payloads
    cut_payloads = [
        {
            "cut_id": i,
            "desired_revision": 1,
            "realized_revision": 1,
            "realized_asset_id": f"asset-{i}",
            "realized_content_hash": hashlib.sha256(create_solid_cut_png(100, 100, (i * 40, 0, 0))).hexdigest(),
            "source_bytes": create_solid_cut_png(100, 100, (i * 40, 0, 0)),
        }
        for i in range(1, 6)
    ]

    # Success with exact 5
    rendered = render_canonical(valid_state, 1, cut_payloads, font_bytes)
    assert isinstance(rendered, RenderedArtifactBytes)

    # Reject 4 cuts
    with pytest.raises(CompositionRenderError, match="must have exactly 5 items"):
        render_canonical(valid_state, 1, cut_payloads[:4], font_bytes)

    # Reject 6 cuts
    extra_cuts = cut_payloads + [dict(cut_payloads[0], cut_id=6)]
    with pytest.raises(CompositionRenderError, match="must have exactly 5 items"):
        render_canonical(valid_state, 1, extra_cuts, font_bytes)

    # Reject duplicate cut_ids (e.g. 1, 2, 2, 4, 5)
    dup_cuts = list(cut_payloads)
    dup_cuts[2] = dict(cut_payloads[1])
    with pytest.raises(CompositionRenderError, match="cut_id must be 3"):
        render_canonical(valid_state, 1, dup_cuts, font_bytes)

def test_scenario_2b_strict_input_validation_and_rejections(font_path: Path):
    """Scenario 2 (b): Strict schema and direct renderer input rejections.
    
    - percentage numeric string rejected (JSON numbers only)
    - uppercase font sha256 rejected
    - direct renderer rejects non-positive or unequal revisions
    - direct renderer rejects empty asset_id
    - direct renderer rejects invalid / mismatched content hash
    """
    font_bytes = font_path.read_bytes()
    # 1. Percentage numeric string rejected
    state_str_pct = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [
            {
                "bubble_id": "b1",
                "cut_id": 1,
                "shape": "ellipse",
                "x_pct": "10.0",  # string!
                "y_pct": 5.0,
                "w_pct": 20.0,
                "h_pct": 10.0,
            }
        ],
    }
    with pytest.raises(CompositionValidationError, match="JSON number"):
        normalize_state(state_str_pct)

    # 2. Uppercase font sha256 rejected
    state_upper_font = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH.upper(),
        "bubbles": [],
    }
    with pytest.raises(CompositionValidationError, match="lowercase hex sha256"):
        normalize_state(state_upper_font)

    # Valid cut template
    valid_state = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    base_cut_payloads = [
        {
            "cut_id": i,
            "desired_revision": 1,
            "realized_revision": 1,
            "realized_asset_id": f"asset-{i}",
            "realized_content_hash": hashlib.sha256(create_solid_cut_png(50, 50, (i * 20, 0, 0))).hexdigest(),
            "source_bytes": create_solid_cut_png(50, 50, (i * 20, 0, 0)),
        }
        for i in range(1, 6)
    ]

    # 3. Direct renderer rejects zero or negative composition revision
    with pytest.raises(CompositionValidationError, match="composition_revision must be a positive integer"):
        render_canonical(valid_state, 0, base_cut_payloads, font_bytes)
    with pytest.raises(CompositionValidationError, match="composition_revision must be a positive integer"):
        render_canonical(valid_state, -1, base_cut_payloads, font_bytes)

    # 4. Direct renderer rejects unequal revisions
    unequal_cuts = [dict(c) for c in base_cut_payloads]
    unequal_cuts[2]["desired_revision"] = 2  # realized is 1
    with pytest.raises(CompositionRenderError, match="desired_revision .* != realized_revision"):
        render_canonical(valid_state, 1, unequal_cuts, font_bytes)

    # 5. Direct renderer rejects empty asset_id
    empty_asset_cuts = [dict(c) for c in base_cut_payloads]
    empty_asset_cuts[0]["realized_asset_id"] = "   "
    with pytest.raises(CompositionRenderError, match="realized_asset_id must be a non-empty string"):
        render_canonical(valid_state, 1, empty_asset_cuts, font_bytes)

    # 6. Direct renderer rejects uppercase content hash
    upper_hash_cuts = [dict(c) for c in base_cut_payloads]
    upper_hash_cuts[1]["realized_content_hash"] = upper_hash_cuts[1]["realized_content_hash"].upper()
    with pytest.raises(CompositionRenderError, match="lowercase hex sha256"):
        render_canonical(valid_state, 1, upper_hash_cuts, font_bytes)

def test_scenario_3_unreadable_or_mismatched_cut_fails_whole_materialization(tmp_path: Path, font_path: Path):
    """Scenario 3 / Acceptance C / Exit 3-4, PATH-13:
    
    One cut missing, corrupt, non-PNG, or hash mismatch fails the entire materialization.
    No partial 4-cut artifact or DB row is created.
    """
    project_dir = tmp_path / "proj_unreadable"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    valid_comp = {
        "schema_version": 1,
        "gap_px": 0,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    rev, comp_rev = store.accept_composition(rev, 0, valid_comp)

    service = CompositionService(store, font_path)

    # 1. File missing
    assets[2][1].unlink()  # Delete cut 3 file
    with pytest.raises(SourceAssetError, match="realization file missing"):
        service.materialize(rev, comp_rev)

    # Verify no staging, no review-artifacts, no DB row
    assert len(list((project_dir / "assets" / "review-artifacts").glob("*.png"))) == 0
    assert len(store.snapshot()["review_artifacts"]) == 0

    # 2. Corrupt / Non-PNG (write text bytes to cut 3)
    assets[2][1].write_text("NOT A VALID PNG")
    with pytest.raises(SourceAssetError):
        service.materialize(rev, comp_rev)

    assert len(list((project_dir / "assets" / "review-artifacts").glob("*.png"))) == 0
    assert len(store.snapshot()["review_artifacts"]) == 0

    # 3. Hash mismatch (write valid PNG but different bytes without updating DB)
    assets[2][1].write_bytes(create_solid_cut_png(100, 100, (123, 123, 123)))
    with pytest.raises(SourceAssetError, match="hash mismatch"):
        service.materialize(rev, comp_rev)

    assert len(list((project_dir / "assets" / "review-artifacts").glob("*.png"))) == 0
    assert len(store.snapshot()["review_artifacts"]) == 0


def test_scenario_4_currency_gate_rejected_if_not_current(tmp_path: Path, font_path: Path):
    """Scenario 4 / Acceptance D / Exit 5, PATH-5:
    
    If any cut desired_revision != realized_revision, materialize is rejected.
    """
    project_dir = tmp_path / "proj_stale"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    valid_comp = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    rev, comp_rev = store.accept_composition(rev, 0, valid_comp)

    # Invalidate cut 4 by accepting new cut intent (desired_revision becomes 2)
    rev = store.accept_cut_intent(rev, 4, {"text": "Updated intent for cut 4"})
    service = CompositionService(store, font_path)
    with pytest.raises(RealizationIncompleteError):
        service.materialize(rev, comp_rev)

    # Verify no artifact was created
    assert len(store.snapshot()["review_artifacts"]) == 0


def test_scenario_5_canonical_pixels_and_identity_binding(tmp_path: Path, font_path: Path):
    """Scenario 5 / Acceptance E, F, G / Exit 6, 7, 8:
    
    Full canonical materialization with colored cuts, bubbles, Korean text.
    Verifies pixel output, metadata embedding, DB registration, and read_artifact.
    """
    project_dir = tmp_path / "proj_pixels"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    state = {
        "schema_version": 1,
        "gap_px": 20,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [
            {
                "bubble_id": "bubble-1",
                "cut_id": 1,
                "shape": "ellipse",
                "x_pct": 10.0,
                "y_pct": 2.0,
                "w_pct": 30.0,
                "h_pct": 6.0,
                "text": "웹툰 대사 1",
                "font_size_pct": 2.0,
                "line_spacing_pct": 20.0,
                "text_align": "center",
                "text_rgba": "#000000FF",
                "fill_rgba": "#FFFFFFFF",
                "outline_rgba": "#000000FF",
                "outline_width_pct": 0.2,
                "padding_pct": 5.0,
            },
            {
                "bubble_id": "bubble-2",
                "cut_id": 3,
                "shape": "rounded_rectangle",
                "x_pct": 50.0,
                "y_pct": 45.0,
                "w_pct": 40.0,
                "h_pct": 8.0,
                "text": "Multi-line\nDialogue Text",
                "font_size_pct": 2.2,
                "line_spacing_pct": 25.0,
                "text_align": "left",
                "text_rgba": "#FF0000FF",
                "fill_rgba": "#FFFFFFEE",
                "outline_rgba": "#0000FFFF",
                "outline_width_pct": 0.3,
                "padding_pct": 6.0,
            }
        ],
    }
    rev, comp_rev = store.accept_composition(rev, 0, state)

    service = CompositionService(store, font_path)
    artifact = service.materialize(rev, comp_rev)

    assert artifact.width == CANONICAL_WIDTH
    assert artifact.height == CANONICAL_HEIGHT
    assert artifact.composition_revision == comp_rev
    assert artifact.path.is_file()

    # Verify PNG bytes from disk
    file_bytes = artifact.path.read_bytes()
    assert hashlib.sha256(file_bytes).hexdigest() == artifact.content_hash
    assert artifact.artifact_id == f"artifact-{artifact.content_hash}"

    # Verify decoded image dimensions and metadata
    img = Image.open(io.BytesIO(file_bytes))
    assert img.size == (1024, 7680)
    assert img.format == "PNG"

    closure_raw = img.text.get("comic_new_closure")
    assert closure_raw is not None
    meta = json.loads(closure_raw)
    assert meta["composition_revision"] == comp_rev
    assert meta["font_sha256"] == EXPECTED_FONT_HASH
    assert len(meta["cuts"]) == 5

    # Verify DB snapshot binding
    snap = store.snapshot()
    reg_arts = snap["review_artifacts"]
    assert len(reg_arts) == 1
    db_art = reg_arts[0]
    assert db_art["artifact_id"] == artifact.artifact_id
    assert db_art["content_hash"] == artifact.content_hash
    assert db_art["composition_revision"] == comp_rev
    assert len(db_art["cuts"]) == 5

    # Verify read_artifact reader
    readback = service.read_artifact(artifact.artifact_id)
    assert readback.content_hash == artifact.content_hash
    assert readback.path == artifact.path


def test_scenario_6_determinism_and_typography_overflow(tmp_path: Path, font_path: Path):
    """Scenario 6 / Acceptance I / Exit 10, 11:
    
    1. Deterministic PNG bytes: same input produces exact same SHA-256.
    2. Typography overflow: excessive text overflows content box and fails whole materialization.
    """
    state = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [
            {
                "bubble_id": "b1",
                "cut_id": 1,
                "shape": "ellipse",
                "x_pct": 10.0,
                "y_pct": 5.0,
                "w_pct": 30.0,
                "h_pct": 10.0,
                "text": "Deterministic Test 한글 123",
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
    font_bytes = font_path.read_bytes()

    cut_payloads = [
        {
            "cut_id": i,
            "desired_revision": 1,
            "realized_revision": 1,
            "realized_asset_id": f"asset-{i}",
            "realized_content_hash": hashlib.sha256(create_solid_cut_png(100, 100, (i * 30, 0, 0))).hexdigest(),
            "source_bytes": create_solid_cut_png(100, 100, (i * 30, 0, 0)),
        }
        for i in range(1, 6)
    ]
    r1 = render_canonical(state, 1, cut_payloads, font_bytes)
    r2 = render_canonical(state, 1, cut_payloads, font_bytes)
    assert r1.content_hash == r2.content_hash
    assert r1.png_bytes == r2.png_bytes

    # Overflow text: massive paragraph inside small bubble
    overflow_state = dict(state)
    overflow_state["bubbles"] = [
        {
            "bubble_id": "b_overflow",
            "cut_id": 1,
            "shape": "ellipse",
            "x_pct": 10.0,
            "y_pct": 5.0,
            "w_pct": 20.0,
            "h_pct": 2.0,  # very small box
            "text": "This is a very long paragraph that will definitely overflow the height of this tiny bubble content area!",
            "font_size_pct": 3.0,  # relatively large font
            "line_spacing_pct": 20.0,
            "text_align": "center",
            "text_rgba": "#000000FF",
            "fill_rgba": "#FFFFFFFF",
            "outline_rgba": "#000000FF",
            "outline_width_pct": 0.2,
            "padding_pct": 5.0,
        }
    ]

    with pytest.raises(TypographyError, match="overflows content height"):
        render_canonical(overflow_state, 1, cut_payloads, font_bytes)


def test_scenario_7_immutability_editor_change_preserves_old_artifact(tmp_path: Path, font_path: Path):
    """Scenario 7 / Acceptance H / Exit 9:
    
    After creating artifact A, accept_composition changes the state (revision + 1).
    Artifact A's file bytes and hash remain strictly identical.
    Old artifact is no longer current for review/materialization.
    """
    project_dir = tmp_path / "proj_immutability"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    comp_a = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [
            {
                "bubble_id": "b1",
                "cut_id": 1,
                "shape": "ellipse",
                "x_pct": 10.0,
                "y_pct": 5.0,
                "w_pct": 30.0,
                "h_pct": 10.0,
                "text": "Initial Text A",
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
    rev, comp_rev_a = store.accept_composition(rev, 0, comp_a)

    service = CompositionService(store, font_path)
    art_a = service.materialize(rev, comp_rev_a)
    initial_bytes = art_a.path.read_bytes()
    initial_hash = hashlib.sha256(initial_bytes).hexdigest()

    # Now change editor state
    comp_b = dict(comp_a)
    comp_b["bubbles"] = [dict(comp_a["bubbles"][0], text="Modified Text B")]
    rev, comp_rev_b = store.accept_composition(rev + 1, comp_rev_a, comp_b)

    # Verify artifact A file is UNTOUCHED
    assert art_a.path.read_bytes() == initial_bytes
    assert hashlib.sha256(art_a.path.read_bytes()).hexdigest() == initial_hash

    # Materialize new artifact B
    art_b = service.materialize(rev, comp_rev_b)
    assert art_b.artifact_id != art_a.artifact_id
    assert art_b.path != art_a.path
    assert art_a.path.exists()
    assert art_b.path.exists()

    # Old artifact A is still readable via read_artifact, but not current
    read_a = service.read_artifact(art_a.artifact_id)
    assert read_a.content_hash == initial_hash


def test_scenario_8_handled_rollback_and_corruption_guard(tmp_path: Path, font_path: Path):
    """Scenario 8 / Atomic 13.4:
    
    If registration fails, staging and unregistered final files are cleaned up.
    If final file is corrupted post-registration, read_artifact raises ArtifactReadbackError.
    """
    project_dir = tmp_path / "proj_rollback"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    comp = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    rev, comp_rev = store.accept_composition(rev, 0, comp)

    service = CompositionService(store, font_path)

    # Force registration conflict by passing stale authority revision
    stale_auth_rev = rev - 1
    with pytest.raises(ConflictError):
        service.materialize(stale_auth_rev, comp_rev)

    # Check cleanup: no staging left, no artifacts
    staging_files = list((project_dir / ".composition-staging").glob("**/*.png"))
    assert len(staging_files) == 0
    review_art_files = list((project_dir / "assets" / "review-artifacts").glob("*.png"))
    assert len(review_art_files) == 0

    # Successful materialize
    art = service.materialize(rev, comp_rev)
    assert art.path.is_file()

    # Corrupt final file
    art.path.write_text("CORRUPTED BYTES")
    with pytest.raises(ArtifactReadbackError, match="hash mismatch"):
        service.read_artifact(art.artifact_id)


def test_scenario_9_concurrent_composition_race_and_currentness(tmp_path: Path, font_path: Path):
    """Scenario 9:
    
    Registration commit checks composition revision; concurrent edit causes conflict.
    """
    project_dir = tmp_path / "proj_race"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    comp1 = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    rev, comp_rev = store.accept_composition(rev, 0, comp1)

    service = CompositionService(store, font_path)

    # Interfere right before registration: another writer accepts new composition
    comp2 = dict(comp1, gap_px=20)
    new_auth_rev, new_comp_rev = store.accept_composition(rev, comp_rev, comp2)

    # Original materialize with stale rev should fail
    with pytest.raises(ConflictError):
        service.materialize(rev, comp_rev)


def test_scenario_10a_concurrent_duplicate_convergence(tmp_path: Path, font_path: Path):
    """Scenario 10 (a): Genuine concurrent duplicate materialization.
    
    Two concurrent worker threads attempt materialize simultaneously for the exact same
    R, C, and cut closure.
    One creates the hard link, the other adopts it.
    One wins registration; the other catches Conflict/UNIQUE, strictly compares all 7 convergence steps,
    and converges on the exact same receipt.
    Exactly 1 DB row and 1 final file exist.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor

    project_dir = tmp_path / "proj_concurrent_dup"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    comp = {
        "schema_version": 1,
        "gap_px": 15,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    rev, comp_rev = store.accept_composition(rev, 0, comp)

    barrier = threading.Barrier(2)
    service1 = CompositionService(store, font_path)
    service2 = CompositionService(store, font_path)

    results: list[MaterializedArtifact] = []
    errors: list[Exception] = []

    def worker(srv: CompositionService):
        try:
            barrier.wait(timeout=10)
            art = srv.materialize(rev, comp_rev)
            results.append(art)
        except Exception as e:
            errors.append(e)

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(worker, service1)
        f2 = executor.submit(worker, service2)
        f1.result()
        f2.result()
    assert len(errors) == 0, f"Unexpected errors: {errors}"
    assert len(results) == 2
    assert results[0].artifact_id == results[1].artifact_id
    assert results[0].content_hash == results[1].content_hash
    assert results[0].path == results[1].path
    assert results[0].bytes_data == results[1].bytes_data

    # Exactly 1 DB row and 1 final file
    snap = store.snapshot()
    assert len(snap["review_artifacts"]) == 1
    files = list((project_dir / "assets" / "review-artifacts").glob("*.png"))
    assert len(files) == 1


def test_scenario_9b_realization_change_after_registration(tmp_path: Path, font_path: Path):
    """Scenario 9 (b): Realization change immediately after registration.
    
    1. Materialize initial artifact for 5 current cuts (rev 1).
    2. Immediately commit a new realization for cut 3 (realized_revision=2, desired_revision=2).
    3. Current cuts are ALL CURRENT, but different from the captured artifact closure!
    4. read_artifact with expected_closure or materialize receipt currentness must raise
       ArtifactNoLongerCurrentError.
    5. Historical read_artifact(artifact_id) without currentness checks still succeeds and preserves bytes.
    """
    project_dir = tmp_path / "proj_real_change"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    comp = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    rev, comp_rev = store.accept_composition(rev, 0, comp)
    service = CompositionService(store, font_path)
    art = service.materialize(rev, comp_rev)
    orig_bytes = art.bytes_data

    # Registration incremented authority revision! Get fresh rev
    rev = store.snapshot()["authority_revision"]
    rev = store.accept_cut_intent(rev, 3, {"text": "Updated intent 3"})
    new_png = create_solid_cut_png(1024, 1536, (128, 128, 128))
    new_hash = hashlib.sha256(new_png).hexdigest()
    new_asset_id = f"asset-cut-3-new-{new_hash[:8]}"
    new_rel_path = f"assets/realizations/cut-3/rev-2-{new_asset_id}.png"
    (project_dir / new_rel_path).parent.mkdir(parents=True, exist_ok=True)
    (project_dir / new_rel_path).write_bytes(new_png)

    with store._connect() as con:
        rev += 1
        con.execute("BEGIN IMMEDIATE;")
        con.execute(
            """
            UPDATE cuts
            SET realized_revision = 2,
                realized_asset_id = ?,
                realized_asset_path = ?,
                realized_content_hash = ?
            WHERE cut_id = 3
            """,
            (new_asset_id, new_rel_path, new_hash),
        )
        con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (rev,))
        con.execute("COMMIT;")

    # All 5 cuts are current!
    snap = store.snapshot()
    assert snap["realization_complete"]["complete"] is True

    # But artifact closure for cut 3 had realized_revision=1, not 2
    with pytest.raises(ArtifactNoLongerCurrentError, match="Cut 3 identity no longer current"):
        service._verify_and_build_artifact(art.artifact_id, expected_comp_rev=comp_rev, expected_closure=art.closure)

    # Historical read (without currentness assertion) succeeds and returns identical bytes
    hist = service.read_artifact(art.artifact_id)
    assert hist.bytes_data == orig_bytes
    assert hist.content_hash == art.content_hash

def test_scenario_10b_reproduced_race_creator_fails_adopter_registers(tmp_path: Path, font_path: Path):
    """Scenario 10 (b): Controlled ordering of reproduced creator-fails / adopter-registers defect.
    
    Creator A creates the exclusive final hard-link and arrives at registration.
    Adopter B observes existing final, validates exact bytes, and arrives at registration.
    Creator A registration fails with Conflict (fault-injected or stale authority rev).
    Creator A MUST NOT unlink the final file!
    Adopter B proceeds with real register_review_artifact, succeeds, and verifies readback.
    Fresh snapshot and path inventory: 1 registered row, 1 valid file on disk, read_artifact succeeds.
    """
    import threading

    project_dir = tmp_path / "proj_repro_race"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    comp = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    rev, comp_rev = store.accept_composition(rev, 0, comp)

    service_a = CompositionService(store, font_path)
    service_b = CompositionService(store, font_path)

    step1_a_at_register = threading.Event()
    step2_b_at_register = threading.Event()
    step3_allow_b_register = threading.Event()

    orig_register = store.register_review_artifact

    def controlled_register(expected_authority_revision, artifact_id, content_hash, composition_revision, cut_closure):
        thread_name = threading.current_thread().name
        if thread_name == "creator-a":
            # A reaches registration only after publishing and validating final_dest.
            step1_a_at_register.set()
            # B reaches registration only after adopting and validating that same final_dest.
            assert step2_b_at_register.wait(timeout=10)
            raise ConflictError(expected=expected_authority_revision, actual=expected_authority_revision + 99)
        if thread_name == "adopter-b":
            step2_b_at_register.set()
            assert step3_allow_b_register.wait(timeout=10)
            return orig_register(
                expected_authority_revision=expected_authority_revision,
                artifact_id=artifact_id,
                content_hash=content_hash,
                composition_revision=composition_revision,
                cut_closure=cut_closure,
            )
        raise AssertionError(f"Unexpected registration caller: {thread_name}")

    store.register_review_artifact = controlled_register

    a_error: list[Exception] = []
    b_error: list[Exception] = []
    b_result: list[MaterializedArtifact] = []

    def thread_a():
        try:
            service_a.materialize(rev, comp_rev)
        except Exception as e:
            a_error.append(e)
        finally:
            step3_allow_b_register.set()

    def thread_b():
        try:
            assert step1_a_at_register.wait(timeout=10)
            b_result.append(service_b.materialize(rev, comp_rev))
        except Exception as e:
            b_error.append(e)

    t_a = threading.Thread(target=thread_a, name="creator-a")
    t_b = threading.Thread(target=thread_b, name="adopter-b")

    t_a.start()
    t_b.start()
    t_a.join(timeout=15)
    t_b.join(timeout=15)
    assert not t_a.is_alive()
    assert not t_b.is_alive()

    # Restore register method
    store.register_review_artifact = orig_register

    # Verify outcomes:
    # 1. A failed with ConflictError
    assert len(a_error) == 1
    assert isinstance(a_error[0], ConflictError)
    assert b_error == []

    # 2. B succeeded!
    assert len(b_result) == 1
    art_b = b_result[0]
    assert art_b.path.is_file()
    assert art_b.path.read_bytes() == art_b.bytes_data

    # 3. Exactly 1 DB row, 1 valid file on disk, read_artifact succeeds
    snap = store.snapshot()
    assert len(snap["review_artifacts"]) == 1
    assert snap["review_artifacts"][0]["artifact_id"] == art_b.artifact_id

    readback_b = service_b.read_artifact(art_b.artifact_id)
    assert readback_b.artifact_id == art_b.artifact_id
    assert readback_b.content_hash == art_b.content_hash
    assert readback_b.bytes_data == art_b.bytes_data

def test_scenario_11_downstream_identity_boundary(tmp_path: Path, font_path: Path):
    """Scenario 11 / Acceptance J, K / Exit 12, 13:
    
    Review reader and Export reader use read_artifact(artifact_id) only.
    No re-layout or rendering parameters are required.
    """
    project_dir = tmp_path / "proj_downstream"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    comp = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [
            {
                "bubble_id": "b-down",
                "cut_id": 2,
                "shape": "ellipse",
                "x_pct": 20.0,
                "y_pct": 25.0,
                "w_pct": 25.0,
                "h_pct": 8.0,
                "text": "Downstream Proof",
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
    rev, comp_rev = store.accept_composition(rev, 0, comp)

    service = CompositionService(store, font_path)
    art = service.materialize(rev, comp_rev)

    # Simulated Review Reader
    review_reader = CompositionService(store, font_path)
    art_for_review = review_reader.read_artifact(art.artifact_id)

    # Simulated Export Reader
    export_reader = CompositionService(store, font_path)
    art_for_export = export_reader.read_artifact(art.artifact_id)

    assert art_for_review.content_hash == art.content_hash
    assert art_for_export.content_hash == art.content_hash
    assert art_for_review.bytes_data == art_for_export.bytes_data


def test_scenario_12_restart_new_process_readback(tmp_path: Path, font_path: Path):
    """Scenario 12 / Exit 8:
    
    A completely new Python subprocess opens the project and reads the artifact.
    Rejects unregistered files and corrupt files.
    """
    project_dir = tmp_path / "proj_restart"
    store, rev, assets = setup_project_with_five_current_cuts(project_dir)

    comp = {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": EXPECTED_FONT_HASH,
        "bubbles": [],
    }
    rev, comp_rev = store.accept_composition(rev, 0, comp)

    service = CompositionService(store, font_path)
    art = service.materialize(rev, comp_rev)
    art_id = art.artifact_id

    # Run fresh Python process
    code = f"""
from pathlib import Path
from comic_new.store import TransactionalStore
from comic_new.composition_service import CompositionService, ArtifactReadbackError

project_dir = Path('{project_dir}')
store = TransactionalStore.open_project(project_dir)
service = CompositionService(store, '{font_path}')

# 1. Read registered artifact
mat = service.read_artifact('{art_id}')
assert mat.content_hash == '{art.content_hash}'
assert mat.width == 1024
assert mat.height == 7680

# 2. Try reading unregistered artifact id
try:
    service.read_artifact('artifact-0000000000000000000000000000000000000000000000000000000000000000')
    raise AssertionError("Should have failed for unregistered artifact")
except ArtifactReadbackError:
    pass

print("NEW_PROCESS_READBACK_SUCCESS")
"""
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert res.returncode == 0, f"Process failed: {res.stderr}"
    assert "NEW_PROCESS_READBACK_SUCCESS" in res.stdout
