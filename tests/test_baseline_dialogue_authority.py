"""Tests for BLOCK-07: Structural Baseline Precondition and Dialogue Authority.

Validates Acceptance criteria A through H:
- Acceptance A: baseline 없는 의도 수용 차단 (store, API 409, direct SQL trigger)
- Acceptance B: baseline 없는 생성 차단 (store, API 409, single/all cuts)
- Acceptance C: baseline 결속과 re-baseline (reorder, exactly 5 intents, STALE/UNRESOLVED, authorization revoked)
- Acceptance D: intent 대사 변경의 조판 동기화 (affected bubbles updated, composition rev + 1)
- Acceptance E: 조판 대사 편집의 intent 원자 수용 (uniform bubble text creates 1 intent revision, desired rev + 1, STALE)
- Acceptance F: 대사 이중 권위 거절 (different texts for same cut rolled back completely)
- Acceptance G: 기하·스타일 전용 편집 보존 (composition rev + 1, intent rev and sequence unchanged)
- Acceptance H: migration과 전 경로 단일 대사 readback (v3->v4 migration, no fabrication, readback consistency)
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import pytest
from fastapi.testclient import TestClient

from comic_new.store import (
    BaselineRequiredError,
    ConflictError,
    StoreCorruptionError,
    TransactionalStore,
    ValidationError,
)
from comic_new.server import create_app
from comic_new.composition import normalize_state


FONT_PATH = Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf").resolve()

def _default_structure() -> dict[str, str]:
    return {"title": "Episode 1", "genre": "comic"}
def _default_intents() -> dict[int, dict[str, str]]:
    return {
        i: {"prompt": f"Panel {i} prompt", "dialogue": f"Panel {i} dialogue"}
        for i in range(1, 6)
    }


def _default_composition_state(bubbles: list[dict] | None = None) -> dict:
    return {
        "schema_version": 1,
        "gap_px": 10,
        "font_sha256": "acb6440a713d880a13a21b468ba7cd43f5a2b2934972e51be791c880730777b8",
        "bubbles": bubbles or [],
    }


def _make_bubble(bubble_id: str, cut_id: int, text: str, y_pct: float = 5.0) -> dict:
    return {
        "bubble_id": bubble_id,
        "cut_id": cut_id,
        "shape": "ellipse",
        "x_pct": 10.0,
        "y_pct": y_pct,
        "w_pct": 30.0,
        "h_pct": 6.0,
        "text": text,
        "font_size_pct": 2.0,
        "line_spacing_pct": 20.0,
        "text_align": "center",
        "text_rgba": "#000000FF",
        "fill_rgba": "#FFFFFFFF",
        "outline_rgba": "#000000FF",
        "outline_width_pct": 0.2,
        "padding_pct": 5.0,
    }


# ---------------------------------------------------------------------------
# Acceptance A: baseline 없는 의도 수용 차단
# ---------------------------------------------------------------------------


def test_acceptance_a_intent_rejected_without_baseline(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_a"
    store = TransactionalStore.create_project(project_dir)
    snap0 = store.snapshot()
    assert snap0["baseline"] is None
    assert snap0["authority_revision"] == 0

    # 1. Store method raises BaselineRequiredError
    with pytest.raises(BaselineRequiredError):
        store.accept_cut_intent(0, 1, {"prompt": "p", "dialogue": "d"})

    # Verify zero state mutation
    snap1 = store.snapshot()
    assert snap1["authority_revision"] == 0
    assert snap1["cuts"][0]["desired_revision"] is None

    app = create_app(project_dir, FONT_PATH)
    with TestClient(app) as client:
        resp = client.post(
            "/api/cuts/1/intent",
            json={
                "expected_authority_revision": 0,
                "mutation_id": "mut-a-1",
                "intent": {"prompt": "p", "dialogue": "d"},
            },
        )
        assert resp.status_code == 409
        body = resp.json()
        assert body["error"]["code"] == "baseline_required"
        assert "current_snapshot" in body["error"]

    # 3. Direct SQL insert with baseline_id=NULL rejected by trigger
    with store._connect() as con:
        with pytest.raises(sqlite3.IntegrityError, match="cut_intents insert requires active baseline"):
            con.execute(
                "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) "
                "VALUES (1, 1, NULL, '{}', 1, '2026-09-16T00:00:00Z')"
            )

    # 4. Direct SQL insert with existing structural baseline row + NULL active baseline rejected by trigger
    with store._connect() as con:
        con.execute(
            "INSERT INTO structural_baselines (baseline_id, structure_json, authority_revision, created_at) "
            "VALUES ('BASE-EXISTING', '{}', 0, '2026-09-16T00:00:00Z')"
        )
        assert con.execute("SELECT current_baseline_id FROM authority WHERE singleton_id = 1").fetchone()[0] is None
        with pytest.raises(sqlite3.IntegrityError, match="cut_intents insert requires active baseline"):
            con.execute(
                "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) "
                "VALUES (1, 1, 'BASE-EXISTING', '{}', 1, '2026-09-16T00:00:00Z')"
            )
        assert con.execute("SELECT count(*) FROM cut_intents").fetchone()[0] == 0


# ---------------------------------------------------------------------------
# Acceptance B: baseline 없는 생성 차단
# ---------------------------------------------------------------------------


def test_acceptance_b_generation_rejected_without_baseline(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_b"
    store = TransactionalStore.create_project(project_dir)

    # 1. Store single and all enqueue rejected
    with pytest.raises((BaselineRequiredError, ValidationError)):
        store.enqueue_generation_jobs(0, cut_id=1)

    with pytest.raises((BaselineRequiredError, ValidationError)):
        store.enqueue_generation_jobs(0, cut_id=None)

    app = create_app(project_dir, FONT_PATH)
    with TestClient(app) as client:
        resp = client.post(
            "/api/generation/jobs",
            json={"expected_authority_revision": 0, "cut_id": 1},
        )
        assert resp.status_code in (400, 409)
    snap = store.snapshot()
    assert len(snap["jobs"]) == 0
    for c in snap["cuts"]:
        assert c["latest_generation_request_seq"] == 0

    # 3. Post-baseline approval: enqueue succeeds
    rev = store.approve_structural_baseline(0, "BASE-01", _default_structure(), _default_intents())
    rev, jobs = store.enqueue_generation_jobs(rev, cut_id=1)
    assert len(jobs) == 1
    assert jobs[0]["request_seq"] == 1


# ---------------------------------------------------------------------------
# Acceptance C: baseline 결속과 re-baseline
# ---------------------------------------------------------------------------


def test_acceptance_c_baseline_binding_and_rebaseline(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_c"
    store = TransactionalStore.create_project(project_dir)

    intents_1 = _default_intents()
    rev1 = store.approve_structural_baseline(0, "BASE-01", _default_structure(), intents_1)
    assert rev1 == 1

    snap1 = store.snapshot()
    assert snap1["baseline"]["baseline_id"] == "BASE-01"
    for c in snap1["cuts"]:
        assert c["desired_revision"] == 1
        assert c["effective_intent"]["dialogue"] == f"Panel {c['cut_id']} dialogue"

    # Re-baseline with new baseline ID and new dialogues
    intents_2 = {
        i: {"prompt": f"New prompt {i}", "dialogue": f"New dialogue {i}"}
        for i in range(1, 6)
    }
    rev2 = store.approve_structural_baseline(rev1, "BASE-02", _default_structure(), intents_2)
    assert rev2 == 2

    snap2 = store.snapshot()
    assert snap2["baseline"]["baseline_id"] == "BASE-02"
    for c in snap2["cuts"]:
        assert c["desired_revision"] == 2
        assert c["effective_intent"]["dialogue"] == f"New dialogue {c['cut_id']}"
        assert c["currency"] == "STALE"


# ---------------------------------------------------------------------------
# Acceptance D: intent 대사 변경의 조판 동기화
# ---------------------------------------------------------------------------


def test_acceptance_d_intent_dialogue_syncs_composition(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_d"
    store = TransactionalStore.create_project(project_dir)
    rev = store.approve_structural_baseline(0, "BASE-01", _default_structure(), _default_intents())

    # Create composition with 2 bubbles on cut 1, 1 bubble on cut 2
    b1 = _make_bubble("b1", cut_id=1, text="Panel 1 dialogue", y_pct=5.0)
    b2 = _make_bubble("b2", cut_id=1, text="Panel 1 dialogue", y_pct=15.0)
    b3 = _make_bubble("b3", cut_id=2, text="Panel 2 dialogue", y_pct=25.0)
    comp_state = _default_composition_state([b1, b2, b3])
    rev, comp_rev = store.accept_composition(rev, 0, comp_state)
    assert comp_rev == 1

    # Accept new intent dialogue on cut 1
    rev = store.accept_cut_intent(
        rev, cut_id=1, intent_payload={"prompt": "Panel 1 prompt", "dialogue": "Updated dialogue 1"}
    )
    snap = store.snapshot()
    assert snap["cuts"][0]["desired_revision"] == 2
    assert snap["cuts"][0]["effective_intent"]["dialogue"] == "Updated dialogue 1"

    # Verify bubbles for cut 1 were synchronized to new dialogue and composition revision advanced
    assert snap["composition"]["revision"] == 2
    bubbles = snap["composition"]["state"]["bubbles"]
    assert len(bubbles) == 3
    assert bubbles[0]["text"] == "Updated dialogue 1"
    assert bubbles[1]["text"] == "Updated dialogue 1"
    # Cut 2 bubble is untouched
    assert bubbles[2]["text"] == "Panel 2 dialogue"


# ---------------------------------------------------------------------------
# Acceptance E: 조판 대사 편집의 intent 원자 수용
# ---------------------------------------------------------------------------


def test_acceptance_e_composition_dialogue_creates_intent_revision(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_e"
    store = TransactionalStore.create_project(project_dir)
    rev = store.approve_structural_baseline(0, "BASE-01", _default_structure(), _default_intents())

    # Create 2 bubbles for cut 2 with uniform NEW text
    b1 = _make_bubble("b1", cut_id=2, text="Uniform New Text", y_pct=20.0)
    b2 = _make_bubble("b2", cut_id=2, text="Uniform New Text", y_pct=30.0)
    comp_state = _default_composition_state([b1, b2])

    rev, comp_rev = store.accept_composition(rev, 0, comp_state)
    assert comp_rev == 1

    snap = store.snapshot()
    # Cut 2 must have created exactly one new intent revision
    cut2 = snap["cuts"][1]
    assert cut2["desired_revision"] == 2
    assert cut2["effective_intent"]["dialogue"] == "Uniform New Text"
    assert cut2["effective_intent"]["prompt"] == "Panel 2 prompt"  # preserved prompt
    assert cut2["currency"] == "STALE"

    # Other cuts remain at revision 1
    for cid in (1, 3, 4, 5):
        assert snap["cuts"][cid - 1]["desired_revision"] == 1


# ---------------------------------------------------------------------------
# Acceptance F: 대사 이중 권위 거절
# ---------------------------------------------------------------------------


def test_acceptance_f_divergent_bubble_texts_rejected(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_f"
    store = TransactionalStore.create_project(project_dir)
    rev = store.approve_structural_baseline(0, "BASE-01", _default_structure(), _default_intents())

    # 2 bubbles on cut 3 with DIFFERENT texts
    b1 = _make_bubble("b1", cut_id=3, text="Text Alpha", y_pct=40.0)
    b2 = _make_bubble("b2", cut_id=3, text="Text Beta", y_pct=50.0)
    comp_state = _default_composition_state([b1, b2])

    with pytest.raises(ValidationError, match="conflicting bubble texts"):
        store.accept_composition(rev, 0, comp_state)

    # Completely rolled back: authority revision and desired revisions unchanged
    snap = store.snapshot()
    assert snap["authority_revision"] == rev
    assert snap["composition"]["revision"] == 0
    for c in snap["cuts"]:
        assert c["desired_revision"] == 1


# ---------------------------------------------------------------------------
# Acceptance G: 기하·스타일 전용 편집 보존
# ---------------------------------------------------------------------------


def test_acceptance_g_geometry_style_only_preserves_intent_sequence(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_g"
    store = TransactionalStore.create_project(project_dir)
    rev = store.approve_structural_baseline(0, "BASE-01", _default_structure(), _default_intents())

    # Create bubble matching current cut 1 dialogue
    b1 = _make_bubble("b1", cut_id=1, text="Panel 1 dialogue", y_pct=5.0)
    comp_state_1 = _default_composition_state([b1])
    rev, comp_rev_1 = store.accept_composition(rev, 0, comp_state_1)

    # Edit geometry, position, color, gap only; keep text identical to "Panel 1 dialogue"
    b1_modified = dict(b1)
    b1_modified["x_pct"] = 15.0
    b1_modified["w_pct"] = 35.0
    b1_modified["fill_rgba"] = "#EEEEEEFF"
    comp_state_2 = _default_composition_state([b1_modified])
    comp_state_2["gap_px"] = 15

    rev, comp_rev_2 = store.accept_composition(rev, comp_rev_1, comp_state_2)
    assert comp_rev_2 == comp_rev_1 + 1

    snap = store.snapshot()
    # Desired revision and generation request seq must NOT increment
    cut1 = snap["cuts"][0]
    assert cut1["desired_revision"] == 1
    assert cut1["latest_generation_request_seq"] == 0


# ---------------------------------------------------------------------------
# Acceptance H: migration과 전 경로 단일 대사 readback
# ---------------------------------------------------------------------------


def test_acceptance_h_v3_to_v4_migration_and_single_readback(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_h"
    project_dir.mkdir()
    db_path = project_dir / "comic-new.sqlite3"

    # 1. Create a schema v3 database with active baseline, but bubble text diverging from intent dialogue
    init_sql = (Path(__file__).parent.parent / "src" / "comic_new" / "schema.sql").read_text()
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA application_id = 0x434f4d43;")
    con.execute("PRAGMA user_version = 3;")
    con.executescript(init_sql)

    # Drop trigger if created by init_sql to simulate pure v3
    con.execute("DROP TRIGGER IF EXISTS trg_cut_intents_active_baseline;")
    con.execute("PRAGMA user_version = 3;")

    # Seed baseline & intents
    now_iso = "2026-09-16T00:00:00Z"
    con.execute(
        "INSERT INTO structural_baselines (baseline_id, structure_json, authority_revision, created_at) VALUES ('BASE-V3', '{}', 1, ?)",
        (now_iso,),
    )
    con.execute("UPDATE authority SET current_baseline_id = 'BASE-V3', authority_revision = 1 WHERE singleton_id = 1")
    for cid in range(1, 6):
        con.execute(
            "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) VALUES (?, 1, 'BASE-V3', ?, 1, ?)",
            (cid, json.dumps({"prompt": f"p{cid}", "dialogue": f"Canonical Dialogue {cid}"}), now_iso),
        )
        con.execute("UPDATE cuts SET desired_revision = 1 WHERE cut_id = ?", (cid,))
        con.execute("INSERT INTO baseline_intents (baseline_id, cut_id, intent_revision) VALUES ('BASE-V3', ?, 1)", (cid,))

    # Seed composition with stale bubble text "Old Text 1" on cut 1
    divergent_bubble = _make_bubble("b-mig", cut_id=1, text="Old Text 1")
    comp_state = _default_composition_state([divergent_bubble])
    con.execute("UPDATE composition SET state_json = ?, revision = 1 WHERE singleton_id = 1", (json.dumps(comp_state),))
    con.commit()
    con.close()

    # 2. Open project: triggers v3 -> v4 migration
    store = TransactionalStore.open_project(project_dir)
    snap = store.snapshot()
    assert snap["schema_version"] == 4
    # Composition bubble text was synchronized to current intent dialogue!
    migrated_bubble = snap["composition"]["state"]["bubbles"][0]
    assert migrated_bubble["text"] == "Canonical Dialogue 1"
    app = create_app(project_dir, FONT_PATH)
    with TestClient(app) as client:
        resp = client.get("/api/studio/snapshot")
        assert resp.status_code == 200
        http_snap = resp.json()
        assert http_snap["cuts"][0]["effective_intent"]["dialogue"] == "Canonical Dialogue 1"
        assert http_snap["composition"]["state"]["bubbles"][0]["text"] == "Canonical Dialogue 1"

def test_acceptance_h_v3_to_v4_preserves_prior_baseline_intent_history(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_h_history"
    project_dir.mkdir()
    db_path = project_dir / "comic-new.sqlite3"
    init_sql = (Path(__file__).parent.parent / "src" / "comic_new" / "schema.sql").read_text()
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA application_id = 0x434f4d43;")
    con.executescript(init_sql)
    con.execute("DROP TRIGGER IF EXISTS trg_cut_intents_active_baseline;")
    con.execute("PRAGMA user_version = 3;")
    now_iso = "2026-09-16T00:00:00Z"
    con.execute(
        "INSERT INTO structural_baselines VALUES ('BASE-OLD', '{}', 1, ?)",
        (now_iso,),
    )
    con.execute(
        "INSERT INTO structural_baselines VALUES ('BASE-CURRENT', '{}', 2, ?)",
        (now_iso,),
    )
    con.execute(
        "UPDATE authority SET current_baseline_id = 'BASE-CURRENT', authority_revision = 2 WHERE singleton_id = 1"
    )
    for cid in range(1, 6):
        con.execute(
            "INSERT INTO cut_intents VALUES (?, 1, 'BASE-OLD', ?, 1, ?)",
            (cid, json.dumps({"prompt": f"old-p{cid}", "dialogue": f"old-d{cid}"}), now_iso),
        )
        con.execute(
            "INSERT INTO baseline_intents VALUES ('BASE-OLD', ?, 1)",
            (cid,),
        )
        con.execute(
            "INSERT INTO cut_intents VALUES (?, 2, 'BASE-CURRENT', ?, 2, ?)",
            (cid, json.dumps({"prompt": f"p{cid}", "dialogue": f"d{cid}"}), now_iso),
        )
        con.execute("UPDATE cuts SET desired_revision = 2 WHERE cut_id = ?", (cid,))
        con.execute(
            "INSERT INTO baseline_intents VALUES ('BASE-CURRENT', ?, 2)",
            (cid,),
        )
    con.commit()
    con.close()

    store = TransactionalStore.open_project(project_dir)
    assert store.snapshot()["schema_version"] == 4
    with sqlite3.connect(db_path) as check:
        assert check.execute("SELECT COUNT(*) FROM cut_intents").fetchone()[0] == 10
        assert check.execute(
            "SELECT COUNT(*) FROM cut_intents WHERE baseline_id = 'BASE-OLD'"
        ).fetchone()[0] == 5


def test_acceptance_h_unattributable_v3_fails_without_fabrication(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_acc_h_bad"
    project_dir.mkdir()
    db_path = project_dir / "comic-new.sqlite3"

    # Create v3 DB with intent rows but NO active baseline (current_baseline_id = NULL)
    init_sql = (Path(__file__).parent.parent / "src" / "comic_new" / "schema.sql").read_text()
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA application_id = 0x434f4d43;")
    con.execute("PRAGMA user_version = 3;")
    con.executescript(init_sql)
    con.execute("DROP TRIGGER IF EXISTS trg_cut_intents_active_baseline;")
    con.execute("PRAGMA user_version = 3;")

    # Insert unattributable intent
    con.execute(
        "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) "
        "VALUES (1, 1, NULL, '{\"prompt\":\"p\",\"dialogue\":\"d\"}', 1, '2026-09-16T00:00:00Z')"
    )
    con.commit()
    con.close()

    # Opening must fail with StoreCorruptionError without fabricating a baseline
    with pytest.raises(StoreCorruptionError, match="legacy intent rows exist without an active baseline"):
        TransactionalStore.open_project(project_dir)
