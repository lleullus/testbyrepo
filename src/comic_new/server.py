"""Single-process FastAPI server for the production Comic Studio."""

from __future__ import annotations

import asyncio
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import threading
import time
from typing import Annotated, Any, AsyncIterator, Literal
from urllib.parse import quote, urlencode
from uuid import uuid4

from fastapi import FastAPI, Path as ApiPath, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, StrictStr, model_validator
import uvicorn

from comic_new.composition import (
    CANONICAL_HEIGHT,
    CANONICAL_WIDTH,
    CompositionError,
    CompositionRenderError,
    CompositionValidationError,
    SourceAssetError,
    TypographyError,
    normalize_state,
)
from comic_new.composition_service import (
    ArtifactNoLongerCurrentError,
    ArtifactReadbackError,
    CompositionService,
    MaterializedArtifact,
)
from comic_new.generation import (
    GenerationRunner,
    GenerationService,
    find_session_or_group_pids,
    is_process_alive_with_token,
)
from comic_new.store import (
    ConflictError,
    InvalidArtifactClosureError,
    RealizationIncompleteError,
    RunnerAlreadyActiveError,
    TransactionalStore,
    TransactionalStoreError,
    ValidationError,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
_HASHED_ASSET_RE = re.compile(r"^/assets/[^/?#]+-[A-Za-z0-9_-]{8,}\.(?:js|css)$")
_EVENT_RING_SIZE = 64
_MONITOR_INTERVAL_SECONDS = 0.1
_STARTUP_SETTLEMENT_SECONDS = 30.0
_SHUTDOWN_SETTLEMENT_SECONDS = 15.0

NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
CutId = Literal[1, 2, 3, 4, 5]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
CutPathId = Annotated[int, ApiPath(ge=1, le=5)]
PositiveQueryInt = Annotated[int, Query(ge=1)]


class ServerPreflightError(RuntimeError):
    """The production server cannot safely open its listening socket."""


class ApiProblem(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        expected_revision: int | None = None,
        actual_revision: int | None = None,
        current_snapshot: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision
        self.current_snapshot = current_snapshot


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BaselineCutDTO(WireModel):
    cut_id: CutId
    role: StrictStr
    beat: StrictStr


class BaselineStructureDTO(WireModel):
    source_brief: StrictStr
    cuts: list[BaselineCutDTO]

    @model_validator(mode="after")
    def validate_exact_five(self) -> "BaselineStructureDTO":
        if [cut.cut_id for cut in self.cuts] != [1, 2, 3, 4, 5]:
            raise ValueError("structure.cuts must contain ordered cut_id values 1 through 5 exactly once")
        return self


class CutIntentDTO(WireModel):
    prompt: StrictStr
    dialogue: StrictStr


class BaselineIntentDTO(WireModel):
    cut_id: CutId
    intent: CutIntentDTO


class BaselineRequest(WireModel):
    expected_authority_revision: NonNegativeInt
    mutation_id: StrictStr
    baseline_id: StrictStr
    structure: BaselineStructureDTO
    intents: list[BaselineIntentDTO]

    @model_validator(mode="after")
    def validate_request(self) -> "BaselineRequest":
        if not self.mutation_id or not self.baseline_id:
            raise ValueError("mutation_id and baseline_id must be non-empty")
        if [item.cut_id for item in self.intents] != [1, 2, 3, 4, 5]:
            raise ValueError("intents must contain ordered cut_id values 1 through 5 exactly once")
        return self


class IntentRequest(WireModel):
    expected_authority_revision: NonNegativeInt
    mutation_id: StrictStr
    intent: CutIntentDTO

    @model_validator(mode="after")
    def validate_mutation_id(self) -> "IntentRequest":
        if not self.mutation_id:
            raise ValueError("mutation_id must be non-empty")
        return self


class CompositionRequest(WireModel):
    expected_authority_revision: NonNegativeInt
    expected_composition_revision: NonNegativeInt
    mutation_id: StrictStr
    state: dict[str, Any]

    @model_validator(mode="after")
    def validate_mutation_id(self) -> "CompositionRequest":
        if not self.mutation_id:
            raise ValueError("mutation_id must be non-empty")
        return self


class GenerationRequest(WireModel):
    expected_authority_revision: NonNegativeInt
    cut_id: CutId | None


class MaterializeRequest(WireModel):
    expected_authority_revision: NonNegativeInt
    expected_composition_revision: NonNegativeInt


class AuthorizeRequest(WireModel):
    expected_authority_revision: NonNegativeInt
    content_hash: Sha256


class _AssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.javascript: list[str] = []
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.javascript.append(values["src"] or "")
        elif tag == "link" and values.get("href"):
            rel = (values.get("rel") or "").split()
            if "stylesheet" in rel:
                self.stylesheets.append(values["href"] or "")


def _preflight_static(static_dir: Path) -> Path:
    index_path = static_dir / "index.html"
    if not index_path.is_file():
        raise ServerPreflightError(f"Generated Studio index is missing: {index_path}")
    try:
        parser = _AssetReferenceParser()
        parser.feed(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise ServerPreflightError(f"Generated Studio index is unreadable: {index_path}") from exc

    if not parser.javascript or not parser.stylesheets:
        raise ServerPreflightError("Generated Studio index must reference hashed JavaScript and CSS assets")

    static_root = static_dir.resolve()
    typed_references = [
        *((reference, ".js") for reference in parser.javascript),
        *((reference, ".css") for reference in parser.stylesheets),
    ]
    for reference, expected_suffix in typed_references:
        if not _HASHED_ASSET_RE.fullmatch(reference) or not reference.endswith(expected_suffix):
            raise ServerPreflightError(f"Generated Studio index has invalid asset reference: {reference}")
        asset_path = (static_dir / reference.removeprefix("/")).resolve()
        if not asset_path.is_relative_to(static_root) or not asset_path.is_file():
            raise ServerPreflightError(f"Generated Studio asset is missing: {reference}")
    return index_path


def _preflight_font(font_path: Path | str) -> tuple[Path, str]:
    path = Path(font_path)
    if not path.is_absolute():
        raise ServerPreflightError("The Studio font path must be absolute")
    path = path.resolve()
    if not path.is_file():
        raise ServerPreflightError(f"Studio font is not a readable regular file: {path}")
    try:
        font_bytes = path.read_bytes()
    except OSError as exc:
        raise ServerPreflightError(f"Studio font is unreadable: {path}") from exc
    if not font_bytes:
        raise ServerPreflightError(f"Studio font is empty: {path}")
    return path, hashlib.sha256(font_bytes).hexdigest()


def _preflight_project(project_dir: Path | str) -> TransactionalStore:
    try:
        return TransactionalStore.open_project(Path(project_dir).resolve())
    except Exception as exc:
        raise ServerPreflightError(f"Studio project preflight failed: {exc}") from exc


@dataclass(frozen=True)
class _Event:
    event_id: str
    event: str
    data: dict[str, Any]

    def encode(self) -> str:
        payload = json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        return f"id: {self.event_id}\nevent: {self.event}\ndata: {payload}\n\n"


class SnapshotBroadcaster:
    """Bounded process-local SSE replay for authoritative SQLite snapshots."""

    def __init__(self, store: TransactionalStore, font_sha256: str) -> None:
        self.store = store
        self.font_sha256 = font_sha256
        self.boot_id = uuid4().hex
        self._ring: deque[_Event] = deque(maxlen=_EVENT_RING_SIZE)
        self._subscribers: set[asyncio.Queue[_Event | None]] = set()
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._monitor_stop = threading.Event()
        self._monitor: threading.Thread | None = None
        self.monitor_error: Exception | None = None

    @property
    def latest_revision(self) -> int | None:
        with self._lock:
            return self._ring[-1].data["authority_revision"] if self._ring else None

    def start(self, loop: asyncio.AbstractEventLoop, initial_snapshot: dict[str, Any]) -> None:
        self._loop = loop
        self.publish(initial_snapshot)
        self._monitor = threading.Thread(
            target=self._monitor_loop,
            name="comic-new-snapshot-monitor",
            daemon=True,
        )
        self._monitor.start()

    def publish(self, snapshot: dict[str, Any]) -> None:
        revision = snapshot["authority_revision"]
        gap_event: _Event | None = None
        with self._lock:
            previous = self._ring[-1].data["authority_revision"] if self._ring else None
            if previous is not None and revision <= previous:
                return
            if previous is not None and revision > previous + 1:
                gap_event = self._required_event("revision-gap", revision)
            event = _Event(
                event_id=f"{self.boot_id}:{revision}",
                event="studio.snapshot",
                data={
                    "schema": "studio-event/v1",
                    "boot_id": self.boot_id,
                    "authority_revision": revision,
                    "snapshot": snapshot,
                },
            )
            self._ring.append(event)
            subscribers = tuple(self._subscribers)
        if gap_event is not None:
            self._dispatch(gap_event, subscribers)
        self._dispatch(event, subscribers)

    def flush_latest(self) -> None:
        with self._lock:
            if not self._ring:
                return
            event = self._ring[-1]
            subscribers = tuple(self._subscribers)
        self._dispatch(event, subscribers)

    def _required_event(self, reason: str, revision: int) -> _Event:
        return _Event(
            event_id=f"{self.boot_id}:{revision}",
            event="snapshot-required",
            data={
                "schema": "studio-event/v1",
                "reason": reason,
                "authority_revision": revision,
            },
        )

    def _dispatch(
        self,
        event: _Event,
        subscribers: tuple[asyncio.Queue[_Event | None], ...],
    ) -> None:
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        for queue in subscribers:
            loop.call_soon_threadsafe(self._offer, queue, event)

    def _offer(self, queue: asyncio.Queue[_Event | None], event: _Event) -> None:
        if queue.full():
            while not queue.empty():
                queue.get_nowait()
            queue.put_nowait(self._required_event("replay-miss", event.data["authority_revision"]))
        queue.put_nowait(event)

    @staticmethod
    def _close_queue(queue: asyncio.Queue[_Event | None]) -> None:
        while not queue.empty():
            queue.get_nowait()
        queue.put_nowait(None)

    def _monitor_loop(self) -> None:
        while not self._monitor_stop.wait(_MONITOR_INTERVAL_SECONDS):
            try:
                snapshot = self.store.snapshot()
                self.publish(_snapshot_dto(snapshot, self.font_sha256))
                self.monitor_error = None
            except Exception as exc:
                self.monitor_error = exc

    def subscribe(self, last_event_id: str | None) -> tuple[asyncio.Queue[_Event | None], list[_Event]]:
        queue: asyncio.Queue[_Event | None] = asyncio.Queue(maxsize=_EVENT_RING_SIZE + 2)
        with self._lock:
            ring = list(self._ring)
            current_revision = ring[-1].data["authority_revision"] if ring else 0
            if last_event_id is None:
                replay = ring[-1:]
            elif not last_event_id.startswith(f"{self.boot_id}:"):
                replay = [self._required_event("boot-changed", current_revision)]
            else:
                matching_index = next(
                    (index for index, event in enumerate(ring) if event.event_id == last_event_id),
                    None,
                )
                if matching_index is None:
                    replay = [self._required_event("replay-miss", current_revision)]
                else:
                    replay = ring[matching_index + 1 :]
            self._subscribers.add(queue)
        return queue, replay

    def unsubscribe(self, queue: asyncio.Queue[_Event | None]) -> None:
        with self._lock:
            self._subscribers.discard(queue)

    def close(self) -> None:
        self._monitor_stop.set()
        if self._monitor is not None:
            self._monitor.join(timeout=2.0)
            if self._monitor.is_alive():
                raise RuntimeError("SQLite revision monitor did not settle")
        with self._lock:
            subscribers = tuple(self._subscribers)
            self._subscribers.clear()
        loop = self._loop
        if loop is not None and not loop.is_closed():
            for queue in subscribers:
                loop.call_soon_threadsafe(self._close_queue, queue)


class RunnerSupervisor:
    """One condition-driven owner of GenerationRunner.run_until_idle()."""

    def __init__(self, store: TransactionalStore) -> None:
        self.store = store
        self._condition = threading.Condition()
        self._wake_requested = True
        self._closing = False
        self._thread: threading.Thread | None = None
        self.last_error: Exception | None = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run,
            name="comic-new-generation-supervisor",
            daemon=True,
        )
        self._thread.start()

    def wake(self) -> None:
        with self._condition:
            if not self._closing:
                self.last_error = None
                self._wake_requested = True
                self._condition.notify()

    def _run(self) -> None:
        while True:
            with self._condition:
                while not self._wake_requested and not self._closing:
                    self._condition.wait()
                if self._closing:
                    return
                self._wake_requested = False
            try:
                GenerationRunner(self.store).run_until_idle()
            except Exception as exc:
                self.last_error = exc

    def close(self, timeout: float = _SHUTDOWN_SETTLEMENT_SECONDS) -> None:
        with self._condition:
            self._closing = True
            self._condition.notify_all()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                raise RuntimeError("Generation runner supervisor did not settle")


def _default_composition(font_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "gap_px": 24,
        "font_sha256": font_sha256,
        "bubbles": [],
    }


def _realization_url(cut: dict[str, Any]) -> str | None:
    if cut.get("realized_asset_id") is None or cut.get("realized_revision") is None:
        return None
    query = urlencode(
        {
            "asset_id": cut["realized_asset_id"],
            "revision": cut["realized_revision"],
        }
    )
    return f"/api/cuts/{cut['cut_id']}/realization?{query}"


def _snapshot_dto(
    snapshot: dict[str, Any],
    font_sha256: str,
) -> dict[str, Any]:
    composition = snapshot["composition"]
    raw_state = composition["state"]
    if composition["revision"] == 0 and raw_state == {}:
        state = None
    else:
        state = normalize_state(raw_state)

    cuts = []
    for cut in snapshot["cuts"]:
        cuts.append(
            {
                "cut_id": cut["cut_id"],
                "desired_revision": cut["desired_revision"],
                "effective_intent": cut["effective_intent"],
                "realized_revision": cut["realized_revision"],
                "realized_asset_id": cut["realized_asset_id"],
                "realized_content_hash": cut["realized_content_hash"],
                "realized_asset_url": _realization_url(cut),
                "currency": cut["currency"],
            }
        )

    jobs = []
    for job in snapshot["jobs"]:
        jobs.append(
            {
                "job_id": job["job_id"],
                "cut_id": job["cut_id"],
                "target_desired_revision": job["target_desired_revision"],
                "status": job["status"],
                "terminal_detail": job["terminal_detail"],
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
                "attempts": [
                    {
                        "attempt_id": attempt["attempt_id"],
                        "ordinal": attempt["ordinal"],
                        "status": attempt["status"],
                        "started_at": attempt["started_at"],
                        "finished_at": attempt["finished_at"],
                        "detail": attempt["detail"],
                        "provider_request_id": attempt["provider_request_id"],
                    }
                    for attempt in job["attempts"]
                ],
            }
        )

    artifacts = [
        {
            **artifact,
            "asset_url": f"/api/review-artifacts/{quote(artifact['artifact_id'], safe='')}/content",
        }
        for artifact in snapshot["review_artifacts"]
    ]

    effective_font_hash = font_sha256
    return {
        "schema_version": snapshot["schema_version"],
        "authority_revision": snapshot["authority_revision"],
        "baseline": snapshot["baseline"],
        "cuts": cuts,
        "realization_complete": snapshot["realization_complete"],
        "composition": {
            "revision": composition["revision"],
            "state": state,
            "updated_at": composition["updated_at"],
        },
        "render_contract": {
            "width": CANONICAL_WIDTH,
            "height": CANONICAL_HEIGHT,
            "default_composition": _default_composition(effective_font_hash),
        },
        "jobs": jobs,
        "review_artifacts": artifacts,
        "release_authorization": snapshot["release_authorization"],
        "delivery_attempts": snapshot["delivery_attempts"],
        "generation_control": snapshot["generation_control"],
    }


def _artifact_dto(artifact: MaterializedArtifact, created_at: str) -> dict[str, Any]:
    try:
        image = Image.open(io.BytesIO(artifact.bytes_data))
        image.load()
        metadata = json.loads(image.text["comic_new_closure"])
        cuts = metadata["cuts"]
    except Exception as exc:
        raise ArtifactReadbackError("Verified artifact closure could not be projected") from exc
    return {
        "artifact_id": artifact.artifact_id,
        "content_hash": artifact.content_hash,
        "composition_revision": artifact.composition_revision,
        "created_at": created_at,
        "cuts": [
            {
                "cut_id": cut["cut_id"],
                "desired_revision": cut["desired_revision"],
                "realized_revision": cut["realized_revision"],
                "asset_id": cut["asset_id"],
                "source_content_hash": cut["source_content_hash"],
            }
            for cut in cuts
        ],
        "asset_url": f"/api/review-artifacts/{quote(artifact.artifact_id, safe='')}/content",
    }


def _api_error(problem: ApiProblem) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": problem.code,
            "message": problem.message,
        }
    }
    error = body["error"]
    if problem.expected_revision is not None:
        error["expected_revision"] = problem.expected_revision
    if problem.actual_revision is not None:
        error["actual_revision"] = problem.actual_revision
    if problem.current_snapshot is not None:
        error["current_snapshot"] = problem.current_snapshot
    return JSONResponse(status_code=problem.status_code, content=body)


def _ensure_accepting(app: FastAPI) -> None:
    if not app.state.accepting_mutations:
        raise ApiProblem(503, "internal_error", "Server is shutting down and is not accepting mutations")


def _active_or_queued(snapshot: dict[str, Any]) -> bool:
    return any(job["status"] in {"queued", "running"} for job in snapshot["jobs"])


def _assert_no_live_generation_process(snapshot: dict[str, Any]) -> None:
    remaining: set[int] = set()
    for job in snapshot["jobs"]:
        for attempt in job["attempts"]:
            pid = attempt.get("process_pid")
            token = attempt.get("process_start_token")
            pgid = attempt.get("process_group_id")
            if pid and is_process_alive_with_token(pid, token):
                remaining.add(pid)
            if pgid:
                remaining.update(find_session_or_group_pids(pgid, token))
    if remaining:
        raise RuntimeError(f"Generation process tree remains alive: {sorted(remaining)}")


def create_app(project_dir: Path | str, font_path: Path | str) -> FastAPI:
    """Create one production app after strict project/font/static preflight."""
    store = _preflight_project(project_dir)
    resolved_font, font_sha256 = _preflight_font(font_path)
    index_path = _preflight_static(STATIC_DIR)
    generation_service = GenerationService(store)
    composition_service = CompositionService(store, resolved_font)
    broadcaster = SnapshotBroadcaster(store, font_sha256)
    supervisor = RunnerSupervisor(store)

    initial = store.snapshot()
    control = initial["generation_control"]
    runner_pid = control.get("runner_pid")
    if runner_pid and runner_pid != os.getpid() and is_process_alive_with_token(
        runner_pid, control.get("runner_start_token")
    ):
        raise RunnerAlreadyActiveError(
            f"Runner {control.get('runner_id')} (pid {runner_pid}) is currently active"
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async def settle_runtime() -> Exception | None:
            shutdown_error: Exception | None = None
            try:
                before_stop = await asyncio.to_thread(store.snapshot)
                if _active_or_queued(before_stop):
                    await asyncio.to_thread(generation_service.stop_all)
            except Exception as exc:
                shutdown_error = exc
            try:
                supervisor.close()
            except Exception as exc:
                shutdown_error = shutdown_error or exc
            try:
                final_raw = await asyncio.to_thread(store.snapshot)
                _assert_no_live_generation_process(final_raw)
                broadcaster.publish(_snapshot_dto(final_raw, font_sha256))
                broadcaster.flush_latest()
            except Exception as exc:
                shutdown_error = shutdown_error or exc
            try:
                broadcaster.close()
            except Exception as exc:
                shutdown_error = shutdown_error or exc
            return shutdown_error

        async def settle_when_requested() -> None:
            await app.state.shutdown_requested.wait()
            app.state.accepting_mutations = False
            broadcaster.flush_latest()
            app.state.shutdown_error = await settle_runtime()
            app.state.shutdown_settled.set()

        app.state.accepting_mutations = True
        app.state.shutdown_error = None
        app.state.shutdown_requested = asyncio.Event()
        app.state.shutdown_settled = asyncio.Event()
        initial_snapshot = _snapshot_dto(store.snapshot(), font_sha256)
        loop = asyncio.get_running_loop()
        broadcaster.start(loop, initial_snapshot)
        settlement_task = asyncio.create_task(settle_when_requested())
        startup_running = {
            job["job_id"] for job in initial["jobs"] if job["status"] == "running"
        }
        if startup_running:
            supervisor.start()

        try:
            if startup_running:
                deadline = time.monotonic() + _STARTUP_SETTLEMENT_SECONDS
                while True:
                    if supervisor.last_error is not None:
                        raise RuntimeError("Generation startup recovery failed") from supervisor.last_error
                    fresh = store.snapshot()
                    unsettled = {
                        job["job_id"]
                        for job in fresh["jobs"]
                        if job["job_id"] in startup_running and job["status"] == "running"
                    }
                    if not unsettled:
                        broadcaster.publish(_snapshot_dto(fresh, font_sha256))
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError(
                            f"Generation startup recovery did not settle jobs: {sorted(unsettled)}"
                        )
                    await asyncio.sleep(0.05)
        except Exception:
            app.state.shutdown_requested.set()
            await app.state.shutdown_settled.wait()
            await settlement_task
            if app.state.shutdown_error is not None:
                raise RuntimeError("Studio startup cleanup did not settle execution") from app.state.shutdown_error
            raise

        if not startup_running:
            loop.call_soon(supervisor.start)

        try:
            yield
        finally:
            app.state.shutdown_requested.set()
            await app.state.shutdown_settled.wait()
            await settlement_task
            if app.state.shutdown_error is not None:
                raise RuntimeError("Studio shutdown failed to settle authoritative execution") from app.state.shutdown_error

    app = FastAPI(
        title="Comic New Studio",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.store = store
    app.state.generation_service = generation_service
    app.state.composition_service = composition_service
    app.state.broadcaster = broadcaster
    app.state.runner_supervisor = supervisor
    app.state.font_sha256 = font_sha256
    app.state.accepting_mutations = False
    app.state.shutdown_error = None

    def dto(snapshot: dict[str, Any]) -> dict[str, Any]:
        return _snapshot_dto(snapshot, font_sha256)

    def fresh_and_publish() -> dict[str, Any]:
        snapshot = dto(store.snapshot())
        broadcaster.publish(snapshot)
        return snapshot

    @app.exception_handler(ApiProblem)
    async def handle_api_problem(_request: Request, exc: ApiProblem) -> JSONResponse:
        return _api_error(exc)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return _api_error(ApiProblem(422, "validation_error", "Request body or parameters are invalid"))

    @app.exception_handler(ConflictError)
    async def handle_conflict(_request: Request, exc: ConflictError) -> JSONResponse:
        current = dto(store.snapshot())
        return _api_error(
            ApiProblem(
                409,
                "conflict",
                "Authoritative revision conflict",
                expected_revision=exc.expected,
                actual_revision=exc.actual,
                current_snapshot=current,
            )
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if request.url.path.startswith("/api"):
            code = "not_found" if exc.status_code == 404 else "validation_error"
            message = "API resource was not found" if exc.status_code == 404 else "API request is not allowed"
            return _api_error(ApiProblem(exc.status_code, code, message))
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RealizationIncompleteError)
    async def handle_incomplete(_request: Request, _exc: RealizationIncompleteError) -> JSONResponse:
        return _api_error(ApiProblem(409, "realization_incomplete", "Exactly five current realizations are required"))

    async def artifact_not_current(_request: Request, _exc: Exception) -> JSONResponse:
        return _api_error(
            ApiProblem(
                409,
                "artifact_not_current",
                "Review artifact is not current",
                current_snapshot=dto(store.snapshot()),
            )
        )

    app.add_exception_handler(InvalidArtifactClosureError, artifact_not_current)
    app.add_exception_handler(ArtifactNoLongerCurrentError, artifact_not_current)

    @app.exception_handler(RunnerAlreadyActiveError)
    async def handle_runner_busy(_request: Request, _exc: RunnerAlreadyActiveError) -> JSONResponse:
        return _api_error(ApiProblem(409, "runner_busy", "Another generation runner is active"))

    @app.exception_handler(ValidationError)
    async def handle_domain_validation(_request: Request, exc: ValidationError) -> JSONResponse:
        return _api_error(ApiProblem(400, "validation_error", str(exc)))

    async def handle_composition_validation(_request: Request, exc: Exception) -> JSONResponse:
        return _api_error(ApiProblem(400, "validation_error", str(exc)))

    app.add_exception_handler(CompositionValidationError, handle_composition_validation)
    app.add_exception_handler(TypographyError, handle_composition_validation)

    @app.exception_handler(TransactionalStoreError)
    async def handle_store_error(_request: Request, exc: TransactionalStoreError) -> JSONResponse:
        message = str(exc).lower()
        if "failed to terminate" in message or "process tree" in message:
            return _api_error(
                ApiProblem(503, "process_settlement_failed", "Generation process tree did not settle")
            )
        return _api_error(ApiProblem(500, "internal_error", "Authoritative store operation failed"))

    @app.exception_handler(CompositionError)
    async def handle_composition_error(_request: Request, exc: CompositionError) -> JSONResponse:
        if isinstance(exc, (CompositionRenderError, SourceAssetError, ArtifactReadbackError)):
            return _api_error(ApiProblem(500, "internal_error", "Canonical artifact operation failed"))
        return _api_error(ApiProblem(400, "validation_error", str(exc)))

    @app.exception_handler(Exception)
    async def handle_internal(_request: Request, _exc: Exception) -> JSONResponse:
        return _api_error(ApiProblem(500, "internal_error", "Internal server error"))

    @app.get("/api/studio/snapshot")
    async def get_snapshot() -> dict[str, Any]:
        return await asyncio.to_thread(lambda: dto(store.snapshot()))

    @app.post("/api/baselines")
    async def approve_baseline(body: BaselineRequest) -> dict[str, Any]:
        _ensure_accepting(app)
        intents = {item.cut_id: item.intent.model_dump() for item in body.intents}
        await asyncio.to_thread(
            store.approve_structural_baseline,
            body.expected_authority_revision,
            body.baseline_id,
            body.structure.model_dump(),
            intents,
        )
        return {"accepted_mutation_id": body.mutation_id, "snapshot": fresh_and_publish()}

    @app.post("/api/cuts/{cut_id}/intent")
    async def accept_intent(cut_id: CutPathId, body: IntentRequest) -> dict[str, Any]:
        _ensure_accepting(app)
        await asyncio.to_thread(
            store.accept_cut_intent,
            body.expected_authority_revision,
            cut_id,
            body.intent.model_dump(),
        )
        return {"accepted_mutation_id": body.mutation_id, "snapshot": fresh_and_publish()}

    @app.put("/api/composition")
    async def accept_composition(body: CompositionRequest) -> dict[str, Any]:
        _ensure_accepting(app)
        normalized = normalize_state(body.state)
        await asyncio.to_thread(
            store.accept_composition,
            body.expected_authority_revision,
            body.expected_composition_revision,
            normalized,
        )
        return {"accepted_mutation_id": body.mutation_id, "snapshot": fresh_and_publish()}

    @app.post("/api/generation/jobs")
    async def enqueue_generation(body: GenerationRequest) -> dict[str, Any]:
        _ensure_accepting(app)
        control = store.snapshot()["generation_control"]
        active_runner_pid = control.get("runner_pid")
        if (
            active_runner_pid
            and active_runner_pid != os.getpid()
            and is_process_alive_with_token(active_runner_pid, control.get("runner_start_token"))
        ):
            raise RunnerAlreadyActiveError(
                f"Runner {control.get('runner_id')} (pid {active_runner_pid}) is currently active"
            )
        receipt = await asyncio.to_thread(
            generation_service.enqueue,
            body.cut_id,
            body.expected_authority_revision,
        )
        supervisor.wake()
        snapshot = fresh_and_publish()
        created_ids = {job["job_id"] for job in receipt.jobs}
        return {
            "jobs": [job for job in snapshot["jobs"] if job["job_id"] in created_ids],
            "snapshot": snapshot,
        }

    @app.post("/api/generation/jobs/{job_id}/stop")
    async def stop_generation_job(job_id: str) -> dict[str, Any]:
        _ensure_accepting(app)
        existing = store.snapshot()
        if not any(job["job_id"] == job_id for job in existing["jobs"]):
            raise ApiProblem(404, "not_found", "Generation job was not found")
        receipt = await asyncio.to_thread(generation_service.cancel, job_id)
        return {"receipt": receipt.to_dict(), "snapshot": fresh_and_publish()}

    @app.post("/api/generation/stop")
    async def stop_all_generation() -> dict[str, Any]:
        _ensure_accepting(app)
        receipt = await asyncio.to_thread(generation_service.stop_all)
        return {"receipt": receipt.to_dict(), "snapshot": fresh_and_publish()}

    @app.post("/api/review-artifacts")
    async def materialize_review(body: MaterializeRequest) -> dict[str, Any]:
        _ensure_accepting(app)
        artifact = await asyncio.to_thread(
            composition_service.materialize,
            body.expected_authority_revision,
            body.expected_composition_revision,
        )
        registered = require_artifact(artifact.artifact_id)
        return {
            "artifact": _artifact_dto(artifact, registered["created_at"]),
            "snapshot": fresh_and_publish(),
        }

    def require_artifact(artifact_id: str) -> dict[str, Any]:
        snapshot = store.snapshot()
        registered = next(
            (item for item in snapshot["review_artifacts"] if item["artifact_id"] == artifact_id),
            None,
        )
        if registered is None:
            raise ApiProblem(404, "not_found", "Review artifact was not found")
        return registered

    @app.get("/api/review-artifacts/{artifact_id}")
    async def read_review(artifact_id: str) -> dict[str, Any]:
        registered = require_artifact(artifact_id)
        artifact = await asyncio.to_thread(composition_service.read_artifact, artifact_id)
        return _artifact_dto(artifact, registered["created_at"])

    @app.get("/api/review-artifacts/{artifact_id}/content")
    async def read_review_content(artifact_id: str) -> Response:
        require_artifact(artifact_id)
        artifact = await asyncio.to_thread(composition_service.read_artifact, artifact_id)
        return Response(
            content=artifact.bytes_data,
            media_type="image/png",
            headers={
                "ETag": f'"{artifact.content_hash}"',
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )

    @app.get("/api/cuts/{cut_id}/realization")
    async def read_realization(
        cut_id: CutPathId,
        asset_id: str,
        revision: PositiveQueryInt,
    ) -> Response:
        snapshot = store.snapshot()
        cut = snapshot["cuts"][cut_id - 1]
        if (
            revision != cut["realized_revision"]
            or asset_id != cut["realized_asset_id"]
            or not cut["realized_asset_path"]
            or not cut["realized_content_hash"]
        ):
            raise ApiProblem(404, "not_found", "Cut realization was not found")
        raw_path = Path(cut["realized_asset_path"])
        path = (raw_path if raw_path.is_absolute() else store.project_dir / raw_path).resolve()
        project_root = store.project_dir.resolve()
        if not path.is_relative_to(project_root) or not path.is_file():
            raise ApiProblem(500, "internal_error", "Canonical realization bytes are unavailable")
        try:
            content = path.read_bytes()
            actual_hash = hashlib.sha256(content).hexdigest()
            if actual_hash != cut["realized_content_hash"]:
                raise ValueError("hash mismatch")
            image = Image.open(io.BytesIO(content))
            image.load()
            if image.format != "PNG":
                raise ValueError("not PNG")
        except Exception as exc:
            raise ApiProblem(500, "internal_error", "Canonical realization bytes failed verification") from exc
        return Response(
            content=content,
            media_type="image/png",
            headers={"ETag": f'"{actual_hash}"'},
        )

    @app.post("/api/review-artifacts/{artifact_id}/authorize")
    async def authorize_review(artifact_id: str, body: AuthorizeRequest) -> dict[str, Any]:
        _ensure_accepting(app)
        current = store.snapshot()
        artifact_row = next(
            (item for item in current["review_artifacts"] if item["artifact_id"] == artifact_id),
            None,
        )
        if artifact_row is None:
            raise ApiProblem(404, "not_found", "Review artifact was not found")
        if artifact_row["content_hash"] != body.content_hash:
            raise ApiProblem(
                409,
                "artifact_not_current",
                "Submitted artifact hash does not match the registered artifact",
                current_snapshot=dto(current),
            )
        authorization_id = f"authorization-{uuid4().hex}"
        await asyncio.to_thread(
            store.authorize_release,
            body.expected_authority_revision,
            authorization_id,
            artifact_id,
            body.content_hash,
        )
        return {
            "authorization_id": authorization_id,
            "submitted_artifact_id": artifact_id,
            "submitted_content_hash": body.content_hash,
            "snapshot": fresh_and_publish(),
        }

    @app.get("/api/events")
    async def studio_events(request: Request) -> StreamingResponse:
        last_event_id = request.headers.get("last-event-id")

        async def stream() -> AsyncIterator[str]:
            queue, replay = broadcaster.subscribe(last_event_id)
            try:
                yield ": connected\n\n"
                for event in replay:
                    yield event.encode()
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    except asyncio.TimeoutError:
                        yield ": heartbeat\n\n"
                        continue
                    if event is None:
                        return
                    yield event.encode()
            finally:
                broadcaster.unsubscribe(queue)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(index_path, media_type="text/html")

    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    return app


class _StudioUvicornServer(uvicorn.Server):
    """Delay Uvicorn connection draining until the Studio closes its SSE streams."""

    def __init__(self, config: uvicorn.Config, app: FastAPI) -> None:
        super().__init__(config)
        self._studio_app = app
        self._settling_exit: asyncio.Task[None] | None = None

    def handle_exit(self, sig: int, frame: Any) -> None:
        requested = getattr(self._studio_app.state, "shutdown_requested", None)
        settled = getattr(self._studio_app.state, "shutdown_settled", None)
        if requested is None or settled is None or requested.is_set():
            super().handle_exit(sig, frame)
            return
        requested.set()
        self._settling_exit = asyncio.create_task(self._exit_after_settlement(sig, frame, settled))

    async def _exit_after_settlement(
        self,
        sig: int,
        frame: Any,
        settled: asyncio.Event,
    ) -> None:
        await settled.wait()
        super().handle_exit(sig, frame)


def serve(
    project_dir: Path | str,
    font_path: Path | str,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Run the production Studio and propagate startup/shutdown settlement failures."""
    app = create_app(project_dir, font_path)
    config = uvicorn.Config(app=app, host=host, port=port, lifespan="on")
    server = _StudioUvicornServer(config, app)
    server.run()
    if app.state.shutdown_error is not None:
        raise RuntimeError("Studio server shutdown did not settle") from app.state.shutdown_error
    if not server.started:
        raise RuntimeError("Studio server failed before readiness")
