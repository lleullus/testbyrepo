from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from starlette.responses import FileResponse, StreamingResponse
from starlette.staticfiles import StaticFiles

from src.multi_collector import MultiSourceFlightCollector, MultiSourceResult

logger = logging.getLogger(__name__)

app = FastAPI(
    title="FlyMeta API",
    description="Flight Meta Search Web API & Real-time SSE Streaming",
    version="0.1.0",
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def get_collector() -> MultiSourceFlightCollector:
    """Dependency provider for MultiSourceFlightCollector."""
    return MultiSourceFlightCollector()


@dataclass
class SearchParams:
    from_airport: str
    to_airport: str
    depart: str
    return_date: str
    adults: int = 2
    direct_only: bool = False
    no_card: bool = False
    provider: str = "all"


def validate_search_params(
    from_: str = Query(..., alias="from", description="출발 공항 IATA 코드 (영문 대문자 3자리)"),
    to: str = Query(..., alias="to", description="도착 공항 IATA 코드 (영문 대문자 3자리)"),
    depart: str = Query(..., alias="depart", description="출발일 (YYYY-MM-DD)"),
    return_: str = Query(..., alias="return", description="귀국일 (YYYY-MM-DD)"),
    adults: int = Query(2, ge=1, le=9, description="성인 탑승객 수 (1-9)"),
    direct_only: bool = Query(False, alias="direct_only", description="직항만 검색"),
    no_card: bool = Query(False, alias="no_card", description="카드할인 제외"),
    provider: str = Query("all", alias="provider", description="제공자 (all, trip, naver)"),
) -> SearchParams:
    """IATA 공항 코드, 날짜 범위, 제공자 파라미터 유효성 검증."""
    # 1. IATA 공항 코드 영문 대문자 3자리 검증
    if not re.match(r"^[A-Z]{3}$", from_):
        raise HTTPException(
            status_code=422,
            detail=f"유효하지 않은 출발 공항 코드입니다 ('{from_}'). 영문 대문자 3자리여야 합니다.",
        )
    if not re.match(r"^[A-Z]{3}$", to):
        raise HTTPException(
            status_code=422,
            detail=f"유효하지 않은 도착 공항 코드입니다 ('{to}'). 영문 대문자 3자리여야 합니다.",
        )
    if from_ == to:
        raise HTTPException(
            status_code=422,
            detail=f"출발 공항({from_})과 도착 공항({to})은 서로 달라야 합니다.",
        )

    # 2. 날짜 형식 (YYYY-MM-DD) 검증
    try:
        dep_date = datetime.strptime(depart, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"유효하지 않은 출발일 날짜 형식입니다 ('{depart}'). YYYY-MM-DD 형식이어야 합니다.",
        )
    try:
        ret_date = datetime.strptime(return_, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"유효하지 않은 귀국일 날짜 형식입니다 ('{return_}'). YYYY-MM-DD 형식이어야 합니다.",
        )
    if ret_date < dep_date:
        raise HTTPException(
            status_code=422,
            detail=f"귀국일({return_})은 출발일({depart})과 같거나 이후여야 합니다.",
        )

    # 3. 제공자 검증
    norm_provider = provider.lower().strip()
    if norm_provider not in ("all", "trip", "naver"):
        raise HTTPException(
            status_code=422,
            detail=f"유효하지 않은 provider입니다 ('{provider}'). all, trip, naver 중 하나여야 합니다.",
        )

    return SearchParams(
        from_airport=from_,
        to_airport=to,
        depart=depart,
        return_date=return_,
        adults=adults,
        direct_only=direct_only,
        no_card=no_card,
        provider=norm_provider,
    )


@app.get("/", response_class=FileResponse)
async def serve_index() -> FileResponse:
    """루트 대시보드 HTML 서빙 엔드포인트."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard index.html not found")
    return FileResponse(str(index_path))


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """서버 상태 헬스체크 엔드포인트."""
    return {"status": "ok"}


@app.get("/api/search")
async def search_flights(
    params: SearchParams = Depends(validate_search_params),
    collector: MultiSourceFlightCollector = Depends(get_collector),
) -> Dict[str, Any]:
    """블로킹 JSON 항공권 검색 엔드포인트 (asyncio.to_thread 기반 스레드 격리)."""
    result: MultiSourceResult = await asyncio.to_thread(
        collector.search,
        origin=params.from_airport,
        dest=params.to_airport,
        depart_date=params.depart,
        return_date=params.return_date,
        direct_only=params.direct_only,
        adults=params.adults,
        provider=params.provider,
        no_card=params.no_card,
    )

    # 양측 프로바이더 모두 실패한 경우에만 HTTP 502 Bad Gateway
    if len(result.offers) == 0 and len(result.warnings) > 0:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "모든 항공권 제공자 수집에 실패했습니다.",
                "warnings": result.warnings,
            },
        )

    serialized_offers = [o.to_dict() for o in result.offers]
    return {
        "offers": serialized_offers,
        "warnings": result.warnings,
        "is_partial": bool(result.warnings and serialized_offers),
        "total_count": len(serialized_offers),
    }


@app.get("/api/search/stream")
async def search_flights_stream(
    params: SearchParams = Depends(validate_search_params),
    collector: MultiSourceFlightCollector = Depends(get_collector),
) -> StreamingResponse:
    """실시간 SSE 스트리밍 항공권 검색 엔드포인트."""
    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[Optional[tuple[str, Dict[str, Any]]]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        # 대상 프로바이더 목록
        if params.provider == "all":
            providers = ["trip", "naver"]
        else:
            providers = [params.provider]

        # 1. started 이벤트 전송
        started_data = {
            "status": "started",
            "providers": providers,
        }
        yield f"event: started\ndata: {json.dumps(started_data, ensure_ascii=False)}\n\n"

        def progress_callback(event_type: str, data: Dict[str, Any]) -> None:
            if event_type == "provider_complete":
                payload = {
                    "provider": data.get("provider"),
                    "status": "completed",
                    "count": data.get("count", 0),
                    "offers": data.get("offers", []),
                }
            else:  # provider_error
                payload = {
                    "provider": data.get("provider"),
                    "status": "failed",
                    "error": data.get("error", ""),
                    "count": 0,
                    "offers": [],
                }
            loop.call_soon_threadsafe(queue.put_nowait, ("progress", payload))

        async def worker() -> None:
            try:
                result: MultiSourceResult = await asyncio.to_thread(
                    collector.search,
                    origin=params.from_airport,
                    dest=params.to_airport,
                    depart_date=params.depart,
                    return_date=params.return_date,
                    direct_only=params.direct_only,
                    adults=params.adults,
                    provider=params.provider,
                    no_card=params.no_card,
                    progress_callback=progress_callback,
                )
                serialized = [o.to_dict() for o in result.offers]
                complete_data = {
                    "status": "complete",
                    "total_count": len(serialized),
                    "offers": serialized,
                    "warnings": result.warnings,
                }
                loop.call_soon_threadsafe(queue.put_nowait, ("complete", complete_data))
            except Exception as e:
                logger.exception("Error in worker thread during search")
                err_complete_data = {
                    "status": "complete",
                    "total_count": 0,
                    "offers": [],
                    "warnings": [f"검색 실패: {e}"],
                }
                loop.call_soon_threadsafe(queue.put_nowait, ("complete", err_complete_data))
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        worker_task = asyncio.create_task(worker())

        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                event_name, event_data = item
                yield f"event: {event_name}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            worker_task.cancel()
            raise
        finally:
            if not worker_task.done():
                worker_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.web_api:app", host="0.0.0.0", port=8000, reload=True)
