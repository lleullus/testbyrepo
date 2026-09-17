from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from comic_new.llm import DraftGenerationError, OpenCodexClient


def prompt_for(index: int) -> str:
    return (
        f"Cut {index}: a red-jacketed courier crosses a rainy alley, medium shot, blue lighting. "
        "Clean negative space at upper left for speech balloons. No rendered text or typography in the illustration."
    )


def payload(count: int = 5) -> dict:
    return {
        "cuts": [
            {
                "draft_id": f"draft-{index}",
                "display_order": index,
                "role": "establishing" if index == 1 else "reaction",
                "beat": f"The courier reaches beat {index}.",
                "dialogue": "" if index == 2 else f"Line {index}",
                "prompt": prompt_for(index),
            }
            for index in range(1, count + 1)
        ]
    }


def response(data: dict, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        json={"choices": [{"message": {"content": json.dumps(data)}}]},
        request=httpx.Request("POST", "http://test/v1/chat/completions"),
    )


@pytest.mark.asyncio
async def test_primary_payload_and_validated_result() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response(payload())

    client = OpenCodexClient(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    result = await client.generate_draft("rainy courier")
    await client._external_client.aclose()  # type: ignore[union-attr]

    assert result.source_brief == "rainy courier"
    assert result.cut_count == 5
    assert [cut.display_order for cut in result.cuts] == [1, 2, 3, 4, 5]
    assert result.cuts[1].dialogue == ""
    assert len(requests) == 1
    body = json.loads(requests[0].content)
    assert body["model"] == "google-antigravity/gemini-3.8-flash"
    assert body["reasoning_effort"] == "high"
    assert body["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_primary_retry_then_fallback_and_schema_failure() -> None:
    statuses = [429, 200, 200]
    calls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body["model"])
        status = statuses.pop(0)
        return response(payload(), status) if status == 200 else response({}, status)

    client = OpenCodexClient(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        total_budget_sec=10,
    )
    result = await client.generate_draft("fallback story")
    await client._external_client.aclose()  # type: ignore[union-attr]

    assert result.provenance.selected_model == "google-antigravity/gemini-3.8-flash"
    assert calls == [
        "google-antigravity/gemini-3.8-flash",
        "google-antigravity/gemini-3.8-flash",
    ]
    assert [attempt.status_code for attempt in result.provenance.attempts] == [429, 200]


@pytest.mark.asyncio
async def test_invalid_primary_moves_to_fallback_without_partial_success() -> None:
    calls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body["model"])
        if len(calls) == 1:
            return response({"cuts": [{"draft_id": "partial"}]})
        return response(payload())

    client = OpenCodexClient(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        total_budget_sec=10,
    )
    result = await client.generate_draft("fallback story")
    await client._external_client.aclose()  # type: ignore[union-attr]

    assert result.provenance.selected_model == "gpt-5.6-luna"
    assert calls == ["google-antigravity/gemini-3.8-flash", "gpt-5.6-luna"]
    assert result.cuts[0].draft_id == "draft-1"


@pytest.mark.asyncio
async def test_both_connection_failures_are_sanitized_503_category() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("secret host token", request=request)

    client = OpenCodexClient(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        total_budget_sec=10,
    )
    with pytest.raises(DraftGenerationError) as caught:
        await client.generate_draft("offline story")
    await client._external_client.aclose()  # type: ignore[union-attr]

    error = caught.value
    assert error.unavailable_only
    assert len(error.attempts) == 2
    assert all(attempt.category == "connection" for attempt in error.attempts)
    assert "secret host token" not in str(error)


@pytest.mark.asyncio
async def test_cancellation_propagates() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(60)
        return response(payload())

    client = OpenCodexClient(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        total_budget_sec=10,
    )
    task = asyncio.create_task(client.generate_draft("cancel story"))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await client._external_client.aclose()  # type: ignore[union-attr]


@pytest.mark.asyncio
@pytest.mark.parametrize("relative_phrase", [
    "Same as prior shot, medium angle with negative space and speech balloon, no text, no typography.",
    "Same as earlier panel, warm lighting, clean negative space for speech balloons, no text, no typography.",
    "Same as last shot, medium angle with negative space and speech balloon, no text, no typography.",
    "Character as above in a dark room with negative space for speech bubble, no rendered text, no typography.",
    "Refer to the previous panel, dramatic lighting with negative space for speech balloon, no text, no typography.",
    "As before, standing in rain with clean negative space for speech balloon, no text, no typography.",
])
async def test_relative_reference_prompts_are_rejected(relative_phrase: str) -> None:
    invalid_payload = payload()
    invalid_payload["cuts"][0]["prompt"] = relative_phrase

    async def handler(request: httpx.Request) -> httpx.Response:
        return response(invalid_payload)

    client = OpenCodexClient(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        total_budget_sec=10,
    )
    with pytest.raises(DraftGenerationError):
        await client.generate_draft("relative reference prompt test")
    await client._external_client.aclose()  # type: ignore[union-attr]
