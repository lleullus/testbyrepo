"""Async OpenCodex draft client with strict schema and bounded fallback."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import re
import time
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, model_validator

from .prompts import STORYBOARD_SYSTEM_PROMPT, build_user_message

DEFAULT_BASE_URL = "http://127.0.0.1:10100/v1"
PRIMARY_MODEL = "google-antigravity/gemini-3.8-flash"
PRIMARY_REASONING = "high"
PRIMARY_TIMEOUT = 45.0
FALLBACK_MODEL = "gpt-5.6-luna"
FALLBACK_REASONING = "max"
FALLBACK_TIMEOUT = 90.0
TOTAL_BUDGET_SECONDS = 150.0

_RELATIVE_REFERENCE_RE = re.compile(
    r"same\s+as\s+(?:the\s+)?(?:previous|prior|earlier|above|preceding|last|before)|"
    r"character\s+as\s+(?:above|before)|same\s+character\s+as|"
    r"as\s+(?:stated\s+)?(?:above|before)|ditto|"
    r"refer\s+to\s+(?:the\s+)?(?:previous|prior|earlier|last|above)|"
    r"continue\s+from\s+(?:the\s+)?(?:previous|prior|earlier|last)|"
    r"이전\s*(?:컷|장면)과\s*(?:동일|같)|앞\s*(?:컷|장면)과\s*같|위와\s*(?:동일|같)",
    re.IGNORECASE,
)


class DraftCut(BaseModel):
    """One validated, editable storyboard proposal cut."""

    model_config = ConfigDict(extra="forbid")

    draft_id: StrictStr
    display_order: StrictInt = Field(ge=1)
    role: StrictStr
    beat: StrictStr
    dialogue: StrictStr
    prompt: StrictStr

    @model_validator(mode="after")
    def validate_non_empty_fields(self) -> "DraftCut":
        if not self.draft_id.strip():
            raise ValueError("draft_id must be a non-empty string")
        if not self.role.strip():
            raise ValueError("role must be a non-empty string")
        if not self.beat.strip():
            raise ValueError("beat must be a non-empty string")
        if not self.prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        prompt = self.prompt.lower()
        if _RELATIVE_REFERENCE_RE.search(self.prompt):
            raise ValueError("prompt must be self-contained and cannot use relative cut references")
        if not re.search(r"negative\s+space", prompt):
            raise ValueError("prompt must reserve clean negative space")
        if not re.search(r"speech\s+(?:balloon|bubble)s?|말풍선", prompt):
            raise ValueError("prompt must reserve space for speech balloons")
        if not re.search(r"no\s+(?:rendered\s+)?text", prompt):
            raise ValueError("prompt must prohibit rendered text")
        if not re.search(r"no\s+[^.]{0,120}\btypography\b|typography\s+(?:must\s+not|not|is\s+prohibited|rendered)", prompt):
            raise ValueError("prompt must prohibit typography")
        return self


class _LLMStoryboardPayload(BaseModel):
    """Exact provider object; envelope fields are supplied by this client."""

    model_config = ConfigDict(extra="forbid")
    cuts: list[DraftCut]


class DraftAttempt(BaseModel):
    """Sanitized public record of one provider attempt."""

    model_config = ConfigDict(extra="forbid")
    model: StrictStr
    reasoning_effort: StrictStr
    outcome: StrictStr
    status_code: int | None = None
    elapsed_ms: int = Field(ge=0)
    category: str | None = None


class DraftProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: StrictStr
    selected_model: StrictStr
    attempts: list[DraftAttempt]


class DraftGenerationResponse(BaseModel):
    """Validated API response returned by ``generate_draft``."""

    model_config = ConfigDict(extra="forbid")
    source_brief: StrictStr
    cut_count: StrictInt = Field(ge=1)
    cuts: list[DraftCut]
    provenance: DraftProvenance

    @model_validator(mode="after")
    def validate_envelope(self) -> "DraftGenerationResponse":
        if len(self.cuts) != self.cut_count:
            raise ValueError("cuts length must equal cut_count")
        orders = [cut.display_order for cut in self.cuts]
        if orders != list(range(1, self.cut_count + 1)):
            raise ValueError("cuts must use display_order values in exact order")
        identities = [cut.draft_id.strip() for cut in self.cuts]
        if len(set(identities)) != len(identities):
            raise ValueError("draft_id values must be unique")
        if not self.source_brief.strip():
            raise ValueError("source_brief must be non-empty")
        if not self.provenance.attempts:
            raise ValueError("provenance must include attempts")
        if self.provenance.attempts[-1].outcome != "succeeded":
            raise ValueError("selected attempt must be successful")
        if self.provenance.selected_model != self.provenance.attempts[-1].model:
            raise ValueError("selected_model must match the successful attempt")
        return self


@dataclass(frozen=True)
class _ModelSpec:
    model: str
    reasoning_effort: str
    read_timeout: float


class DraftGenerationError(Exception):
    """Raised when no provider attempt produces a valid draft."""

    def __init__(self, message: str, attempts: list[DraftAttempt]) -> None:
        super().__init__(message)
        self.attempts = attempts

    @property
    def unavailable_only(self) -> bool:
        return not self.attempts or all(
            attempt.category in {"connection", "timeout", "budget_exhausted"}
            and attempt.status_code is None
            for attempt in self.attempts
        )


    def public_details(self) -> list[dict[str, Any]]:
        return [attempt.model_dump(mode="json") for attempt in self.attempts]

class OpenCodexClient:
    """OpenAI-compatible async client with Gemini-primary/Luna fallback."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        primary_model: str = PRIMARY_MODEL,
        primary_reasoning: str = PRIMARY_REASONING,
        primary_timeout: float = PRIMARY_TIMEOUT,
        fallback_model: str = FALLBACK_MODEL,
        fallback_reasoning: str = FALLBACK_REASONING,
        fallback_timeout: float = FALLBACK_TIMEOUT,
        connect_timeout: float = 5.0,
        total_budget_sec: float = TOTAL_BUDGET_SECONDS,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.primary_model = primary_model
        self.primary_reasoning = primary_reasoning
        self.primary_timeout = primary_timeout
        self.fallback_model = fallback_model
        self.fallback_reasoning = fallback_reasoning
        self.fallback_timeout = fallback_timeout
        self.primary = _ModelSpec(primary_model, primary_reasoning, primary_timeout)
        self.fallback = _ModelSpec(fallback_model, fallback_reasoning, fallback_timeout)
        self.connect_timeout = connect_timeout
        self.total_budget_sec = total_budget_sec
        self._external_client = client

    @staticmethod
    def _content_from_response(response: httpx.Response) -> str:
        try:
            payload = response.json()
            choices = payload["choices"]
            message = choices[0]["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ValueError("OpenCodex response did not contain message content") from exc
        if not isinstance(content, str):
            raise ValueError("OpenCodex message content must be a string")
        text = content.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
        return (fenced.group(1) if fenced else text).strip()

    @staticmethod
    def _category_for_exception(exc: BaseException) -> str:
        if isinstance(exc, (asyncio.TimeoutError, TimeoutError, httpx.TimeoutException)):
            return "timeout"
        if isinstance(exc, (httpx.ConnectError, httpx.NetworkError, OSError)):
            return "connection"
        return "invalid_response"

    async def _invoke(
        self,
        client: httpx.AsyncClient,
        spec: _ModelSpec,
        messages: list[dict[str, str]],
        deadline: float,
    ) -> tuple[_LLMStoryboardPayload | None, DraftAttempt]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None, DraftAttempt(
                model=spec.model,
                reasoning_effort=spec.reasoning_effort,
                outcome="failed",
                elapsed_ms=0,
                category="budget_exhausted",
            )

        timeout = httpx.Timeout(
            connect=min(self.connect_timeout, remaining),
            read=min(spec.read_timeout, remaining),
            write=min(10.0, remaining),
            pool=min(5.0, remaining),
        )
        payload = {
            "model": spec.model,
            "reasoning_effort": spec.reasoning_effort,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }
        started = time.monotonic()
        status_code: int | None = None
        try:
            async with asyncio.timeout(remaining):
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    timeout=timeout,
                )
            elapsed_ms = max(0, round((time.monotonic() - started) * 1000))
            status_code = response.status_code
            if status_code != 200:
                category = "rate_limited" if status_code == 429 else (
                    "upstream_5xx" if 500 <= status_code <= 599 else "invalid_response"
                )
                return None, DraftAttempt(
                    model=spec.model,
                    reasoning_effort=spec.reasoning_effort,
                    outcome="failed",
                    status_code=status_code,
                    elapsed_ms=elapsed_ms,
                    category=category,
                )
            content = self._content_from_response(response)
            parsed = _LLMStoryboardPayload.model_validate(json.loads(content))
            return parsed, DraftAttempt(
                model=spec.model,
                reasoning_effort=spec.reasoning_effort,
                outcome="succeeded",
                status_code=200,
                elapsed_ms=elapsed_ms,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            elapsed_ms = max(0, round((time.monotonic() - started) * 1000))
            return None, DraftAttempt(
                model=spec.model,
                reasoning_effort=spec.reasoning_effort,
                outcome="failed",
                status_code=status_code,
                elapsed_ms=elapsed_ms,
                category=self._category_for_exception(exc),
            )

    async def _sleep_before_retry(self, deadline: float) -> bool:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        try:
            async with asyncio.timeout(remaining):
                await asyncio.sleep(min(0.5, remaining))
        except asyncio.CancelledError:
            raise
        except (asyncio.TimeoutError, TimeoutError):
            return False
        return time.monotonic() < deadline

    async def generate_draft(self, source_brief: str, cut_count: int = 5) -> DraftGenerationResponse:
        """Generate a validated non-authoritative draft or raise a sanitized error."""
        if not isinstance(source_brief, str) or not source_brief.strip():
            raise ValueError("source_brief must be a non-empty string")
        if isinstance(cut_count, bool) or not isinstance(cut_count, int) or cut_count < 1:
            raise ValueError("cut_count must be a positive integer")

        brief = source_brief.strip()
        messages = [
            {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(brief, cut_count)},
        ]
        deadline = time.monotonic() + self.total_budget_sec
        attempts: list[DraftAttempt] = []
        should_close = self._external_client is None
        client = self._external_client or httpx.AsyncClient()
        try:
            for spec in (self.primary, self.fallback):
                for retry_index in range(2):
                    if deadline - time.monotonic() <= 0:
                        break
                    parsed, attempt = await self._invoke(client, spec, messages, deadline)
                    attempts.append(attempt)
                    if parsed is not None:
                        result = DraftGenerationResponse(
                            source_brief=brief,
                            cut_count=cut_count,
                            cuts=parsed.cuts,
                            provenance=DraftProvenance(
                                provider="opencodex",
                                selected_model=spec.model,
                                attempts=attempts,
                            ),
                        )
                        return result
                    if attempt.category == "budget_exhausted":
                        break
                    retryable = attempt.status_code == 429 or (
                        attempt.status_code is not None and 500 <= attempt.status_code <= 599
                    )
                    if retryable and retry_index == 0:
                        if not await self._sleep_before_retry(deadline):
                            break
                    else:
                        break
                if deadline - time.monotonic() <= 0:
                    break
            raise DraftGenerationError(
                "OpenCodex did not return a valid storyboard draft",
                attempts,
            )
        finally:
            if should_close:
                await client.aclose()
