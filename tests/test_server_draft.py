from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from comic_new.llm import (
    DraftAttempt,
    DraftCut,
    DraftGenerationError,
    DraftGenerationResponse,
    DraftProvenance,
)
from comic_new.server import create_app
from comic_new.store import TransactionalStore

FONT_PATH = Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf")


def make_result(topic: str, count: int = 5) -> DraftGenerationResponse:
    cuts = [
        DraftCut(
            draft_id=f"cut-{index}",
            display_order=index,
            role="establishing" if index == 1 else "reaction",
            beat=f"beat {index}",
            dialogue="",
            prompt=(
                f"Standalone scene {index}, detailed subject and environment, medium shot, warm light. "
                "Clean negative space for speech balloons. No rendered text or typography in the illustration."
            ),
        )
        for index in range(1, count + 1)
    ]
    return DraftGenerationResponse(
        source_brief=topic.strip(),
        cut_count=count,
        cuts=cuts,
        provenance=DraftProvenance(
            provider="opencodex",
            selected_model="google-antigravity/gemini-3.8-flash",
            attempts=[
                DraftAttempt(
                    model="google-antigravity/gemini-3.8-flash",
                    reasoning_effort="high",
                    outcome="succeeded",
                    status_code=200,
                    elapsed_ms=1,
                )
            ],
        ),
    )


class FakeDraftClient:
    def __init__(self, result: DraftGenerationResponse | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[str, int]] = []

    async def generate_draft(self, topic: str, cut_count: int) -> DraftGenerationResponse:
        self.calls.append((topic, cut_count))
        if self.error:
            raise self.error
        assert self.result is not None
        return self.result


def test_generate_draft_route_is_non_authoritative_and_validates_topic(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    TransactionalStore.create_project(project_dir)
    fake = FakeDraftClient(make_result("one line", 5))
    app = create_app(project_dir, FONT_PATH, draft_client=fake)  # type: ignore[arg-type]

    with TestClient(app) as client:
        before = client.get("/api/studio/snapshot").json()
        success = client.post("/api/baselines/generate-draft", json={"topic": "one line"})
        after = client.get("/api/studio/snapshot").json()
        empty = client.post("/api/baselines/generate-draft", json={"topic": "   "})
        wrong_type = client.post("/api/baselines/generate-draft", json={"topic": "ok", "cut_count": "5"})

    assert success.status_code == 200
    body = success.json()
    assert body["source_brief"] == "one line"
    assert [cut["display_order"] for cut in body["cuts"]] == [1, 2, 3, 4, 5]
    assert fake.calls == [("one line", 5)]
    assert after["authority_revision"] == before["authority_revision"]
    assert before["baseline"] is None
    assert after["baseline"] is None
    assert after["jobs"] == before["jobs"] == []
    assert empty.status_code == 400
    assert empty.json()["error"]["code"] == "validation_error"
    assert wrong_type.status_code == 422


def test_generate_draft_route_maps_unavailable_and_provider_failures(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    TransactionalStore.create_project(project_dir)
    unavailable = FakeDraftClient(error=DraftGenerationError(
        "failed",
        [DraftAttempt(
            model="google-antigravity/gemini-3.8-flash",
            reasoning_effort="high",
            outcome="failed",
            status_code=None,
            elapsed_ms=1,
            category="connection",
        )],
    ))
    app = create_app(project_dir, FONT_PATH, draft_client=unavailable)  # type: ignore[arg-type]
    with TestClient(app) as client:
        response = client.post("/api/baselines/generate-draft", json={"topic": "offline"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "draft_service_unavailable"
    assert response.json()["error"]["details"]["attempts"][0]["category"] == "connection"

    project_dir2 = tmp_path / "project2"
    TransactionalStore.create_project(project_dir2)
    provider_error = DraftGenerationError(
        "failed",
        [DraftAttempt(
            model="google-antigravity/gemini-3.8-flash",
            reasoning_effort="high",
            outcome="failed",
            status_code=502,
            elapsed_ms=1,
            category="upstream_5xx",
        )],
    )
    app2 = create_app(project_dir2, FONT_PATH, draft_client=FakeDraftClient(error=provider_error))  # type: ignore[arg-type]
    with TestClient(app2) as client:
        response2 = client.post("/api/baselines/generate-draft", json={"topic": "provider error"})
    assert response2.status_code == 502
    assert response2.json()["error"]["code"] == "draft_generation_failed"


def test_baseline_save_preserves_llm_draft_origin(tmp_path: Path) -> None:
    project_dir = tmp_path / "project-origin"
    TransactionalStore.create_project(project_dir)
    app = create_app(project_dir, FONT_PATH)
    with TestClient(app) as client:
        initial = client.get("/api/studio/snapshot").json()
        request = {
            "expected_authority_revision": initial["authority_revision"],
            "mutation_id": "origin-mutation",
            "baseline_id": "origin-baseline",
            "structure": {
                "source_brief": "origin brief",
                "cuts": [
                    {"cut_id": index, "role": f"role {index}", "beat": f"beat {index}"}
                    for index in range(1, 6)
                ],
            },
            "intents": [
                {
                    "cut_id": index,
                    "intent": {
                        "prompt": f"prompt {index}",
                        "dialogue": "",
                        "prompt_origin": "llm_draft" if index == 1 else "user",
                    },
                }
                for index in range(1, 6)
            ],
        }
        response = client.post("/api/baselines", json=request)
        snapshot = client.get("/api/studio/snapshot").json()
    assert response.status_code == 200
    assert snapshot["cuts"][0]["effective_intent"]["prompt_origin"] == "llm_draft"
    assert snapshot["cuts"][1]["effective_intent"]["prompt_origin"] == "user"

def test_generate_draft_route_accepts_synopsis_only(tmp_path: Path) -> None:
    project_dir = tmp_path / "project-synopsis"
    TransactionalStore.create_project(project_dir)
    fake_client = FakeDraftClient(result=make_result("synopsis topic", 5))
    app = create_app(project_dir, FONT_PATH, draft_client=fake_client)  # type: ignore[arg-type]
    with TestClient(app) as client:
        response = client.post("/api/baselines/generate-draft", json={"synopsis": "synopsis topic"})
    assert response.status_code == 200
    assert fake_client.calls == [("synopsis topic", 5)]

def test_generate_draft_route_accepts_whitespace_topic_with_valid_synopsis(tmp_path: Path) -> None:
    project_dir = tmp_path / "project-ws-topic"
    TransactionalStore.create_project(project_dir)
    fake_client = FakeDraftClient(result=make_result("valid synopsis", 5))
    app = create_app(project_dir, FONT_PATH, draft_client=fake_client)  # type: ignore[arg-type]
    with TestClient(app) as client:
        response = client.post("/api/baselines/generate-draft", json={"topic": "   \t  ", "synopsis": "valid synopsis"})
    assert response.status_code == 200
    assert fake_client.calls == [("valid synopsis", 5)]
