from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.collector import TripFlightCollector
from src.models import RoundTripOffer
from src.naver_collector import NaverFlightCollector

logger = logging.getLogger(__name__)


@dataclass
class MultiSourceResult:
    """멀티 소스 검색 결과 및 발생한 경고 목록."""
    offers: List[RoundTripOffer] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class MultiSourceFlightCollector:
    """트립닷컴과 네이버 항공권을 병렬 수집하고 장애를 격리하는 오케스트레이터."""

    def __init__(
        self,
        timeout_ms: int = 60000,
        trip_collector: Optional[TripFlightCollector] = None,
        naver_collector: Optional[NaverFlightCollector] = None,
    ) -> None:
        self.timeout_ms = timeout_ms
        self.trip_collector = trip_collector or TripFlightCollector(timeout_ms=timeout_ms)
        self.naver_collector = naver_collector or NaverFlightCollector(timeout_ms=timeout_ms)

    def search(
        self,
        origin: str,
        dest: str,
        depart_date: str,
        return_date: str,
        direct_only: bool = False,
        limit: int = 20,
        adults: int = 2,
        provider: str = "all",
        no_card: bool = False,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> MultiSourceResult:
        """지정된 프로바이더(all, trip, naver)로부터 비행 데이터를 수집하고 정렬된 결과 반환."""
        prov = provider.lower().strip()
        if prov not in ("all", "trip", "naver"):
            raise ValueError(f"지원하지 않는 provider: {provider} (all, trip, naver 중 선택)")

        offers: List[RoundTripOffer] = []
        warnings: List[str] = []

        max_workers = 2 if prov == "all" else 1

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {}

            if prov in ("all", "trip"):
                f_trip = executor.submit(
                    self.trip_collector.search_round_trip,
                    origin=origin,
                    dest=dest,
                    depart_date=depart_date,
                    return_date=return_date,
                    direct_only=direct_only,
                    limit=limit,
                    adults=adults,
                )
                future_to_name[f_trip] = "트립닷컴"

            if prov in ("all", "naver"):
                f_naver = executor.submit(
                    self.naver_collector.search_round_trip,
                    origin=origin,
                    dest=dest,
                    depart_date=depart_date,
                    return_date=return_date,
                    direct_only=direct_only,
                    limit=limit,
                    adults=adults,
                    no_card=no_card,
                )
                future_to_name[f_naver] = "네이버 항공권"

            for future in as_completed(future_to_name):
                prov_name = future_to_name[future]
                try:
                    res_offers = future.result()
                    if res_offers:
                        offers.extend(res_offers)
                    if progress_callback:
                        progress_callback(
                            "provider_complete",
                            {
                                "provider": prov_name,
                                "offers": [o.to_dict() for o in (res_offers or [])],
                                "count": len(res_offers or []),
                            },
                        )
                except Exception as e:
                    msg = f"{prov_name} 수집 실패: {e}"
                    logger.warning(msg)
                    warnings.append(msg)
                    if progress_callback:
                        progress_callback(
                            "provider_error",
                            {
                                "provider": prov_name,
                                "error": str(e),
                            },
                        )
        # 3단계 정렬: 직항 우선(0/1) -> 최종 총액 오름차순 -> 총 소요시간 오름차순
        offers.sort(key=lambda o: o.sort_key())

        if limit > 0:
            offers = offers[:limit]

        return MultiSourceResult(offers=offers, warnings=warnings)
