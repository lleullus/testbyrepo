from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from camoufox.sync_api import Camoufox

from src.collector import BotDetectionBlockedError, FlightSearchError, NetworkTimeoutError
from src.models import FlightLeg, RoundTripOffer

logger = logging.getLogger(__name__)

NAVER_FLIGHT_HOME = "https://flight.naver.com"
NAVER_SEARCH_API = "https://flight-api.naver.com/flight/international/searchFlights"

FETCH_JS = r"""
async ([url, body]) => {
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify(body),
      credentials: 'include'
    });
    const text = await r.text();
    return { status: r.status, text: text };
  } catch (err) {
    return { error: String(err) };
  }
}
"""

PARTNER_CODE_MAP: Dict[str, str] = {
    "AGD217": "아고다",
    "CTR013": "트립닷컴",
    "HNT001": "하나투어",
    "MOD001": "모두투어",
    "WEB001": "웹투어",
    "ITP001": "인터파크투어",
    "YLT001": "노랑풍선",
    "WMT001": "위메프",
    "TMT001": "티몬",
    "ONL001": "온라인투어",
    "MYR001": "마이리얼트립",
    "JIN001": "진에어",
    "JEJ001": "제주항공",
    "TWA001": "티웨이항공",
    "AAR001": "아시아나항공",
    "KAL001": "대한항공",
}


def build_naver_search_payload(
    origin: str,
    dest: str,
    depart_date: str,
    return_date: str,
    adults: int = 2,
    direct_only: bool = False,
    limit: int = 100,
) -> Dict[str, Any]:
    """네이버 항공권 실시간 국제선 왕복 검색 요청 페이로드 생성."""
    dep_date = depart_date.replace("-", "").strip()
    ret_date = return_date.replace("-", "").strip()
    return {
        "tripType": "RT",
        "device": "pc",
        "seatClass": "Y",
        "adultCount": adults,
        "childCount": 0,
        "infantCount": 0,
        "isNonstop": direct_only,
        "openReturnDays": 0,
        "initialRequest": True,
        "itineraries": [
            {
                "departureLocationCode": origin.upper(),
                "arrivalLocationCode": dest.upper(),
                "departureLocationType": "airport",
                "arrivalLocationType": "airport",
                "departureDate": dep_date,
            },
            {
                "departureLocationCode": dest.upper(),
                "arrivalLocationCode": origin.upper(),
                "departureLocationType": "airport",
                "arrivalLocationType": "airport",
                "departureDate": ret_date,
            },
        ],
        "flightFilter": {
            "filter": {
                "airlines": [],
                "departureAirports": [],
                "arrivalAirports": [],
                "departureTime": [],
                "fareTypes": [],
                "flightDurationSeconds": [],
                "hasCardBenefit": True,
                "isIndividual": False,
                "isLowCarbonEmission": False,
                "isSameAirlines": False,
                "isSameDepArrAirport": True,
                "isTravelClub": False,
                "minFare": {},
                "viaCount": [],
                "selectedItineraries": [],
            },
            "limit": max(limit, 100),
            "skip": 0,
            "sort": {"adultMinFare": 1},
        },
    }


def parse_naver_sse(raw_text: str) -> Optional[Dict[str, Any]]:
    """네이버 항공권 SSE 응답 텍스트('data:{...}')에서 유효한 JSON 객체 추출."""
    if not raw_text:
        return None
    for line in raw_text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            payload_str = line[5:].strip()
            try:
                data = json.loads(payload_str)
                if isinstance(data, dict) and ("itineraries" in data or "fareMappings" in data):
                    return data
            except json.JSONDecodeError:
                continue
    try:
        data = json.loads(raw_text.strip())
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


def _parse_naver_flight_leg(
    itin: Dict[str, Any],
    airlines_code_map: Dict[str, str],
    has_checked_baggage: bool,
    baggage_desc: str,
) -> Optional[FlightLeg]:
    """단일 Naver itinerary 객체로부터 FlightLeg 도메인 모델 생성."""
    segments = itin.get("segments", [])
    if not segments:
        return None

    is_direct = len(segments) == 1 and not bool(segments[0].get("hiddenStops"))

    if len(segments) == 1:
        carrier_code = segments[0].get("marketingCarrier", {}).get("airlineCode", "")
        airline_name = airlines_code_map.get(carrier_code, carrier_code)
    else:
        carrier_codes = [s.get("marketingCarrier", {}).get("airlineCode", "") for s in segments]
        names = [airlines_code_map.get(c, c) for c in carrier_codes if c]
        airline_name = names[0] if len(set(names)) == 1 else "/".join(names)

    flight_nums = []
    for s in segments:
        mc = s.get("marketingCarrier", {})
        code = mc.get("airlineCode", "")
        fno = mc.get("flightNumber", "")
        flight_nums.append(f"{code}{fno}")
    flight_number = "/".join(flight_nums)

    first_seg = segments[0]
    last_seg = segments[-1]

    dep_d = first_seg.get("departure", {}).get("date", "")
    dep_t = first_seg.get("departure", {}).get("time", "")
    arr_d = last_seg.get("arrival", {}).get("date", "")
    arr_t = last_seg.get("arrival", {}).get("time", "")

    depart_time = (
        f"{dep_d[:4]}-{dep_d[4:6]}-{dep_d[6:8]} {dep_t[:2]}:{dep_t[2:4]}:00"
        if len(dep_d) >= 8 and len(dep_t) >= 4
        else f"{dep_d} {dep_t}"
    )
    arrive_time = (
        f"{arr_d[:4]}-{arr_d[4:6]}-{arr_d[6:8]} {arr_t[:2]}:{arr_t[2:4]}:00"
        if len(arr_d) >= 8 and len(arr_t) >= 4
        else f"{arr_d} {arr_t}"
    )

    depart_airport = first_seg.get("departure", {}).get("airportCode", "")
    arrive_airport = last_seg.get("arrival", {}).get("airportCode", "")

    duration_sec = itin.get("duration", 0)
    duration_minutes = int(duration_sec // 60)

    return FlightLeg(
        airline_name=airline_name,
        flight_number=flight_number,
        depart_time=depart_time,
        arrive_time=arrive_time,
        depart_airport=depart_airport,
        arrive_airport=arrive_airport,
        duration_minutes=duration_minutes,
        is_direct=is_direct,
        has_checked_baggage=has_checked_baggage,
        baggage_desc=baggage_desc,
    )


def parse_naver_flight_offers(
    data: Dict[str, Any],
    origin: str,
    dest: str,
    depart_date: str,
    return_date: str,
    direct_only: bool = False,
    limit: int = 20,
    adults: int = 2,
    no_card: bool = False,
) -> List[RoundTripOffer]:
    """네이버 항공권 응답 데이터(itineraries + fareMappings)를 RoundTripOffer 리스트로 정규화."""
    if not data:
        return []

    status_obj = data.get("status", {})
    airlines_code_map = status_obj.get("airlinesCodeMap", {})
    fare_types_code_map = status_obj.get("fareTypesCodeMap", {})
    itineraries_list = data.get("itineraries", [])
    fare_mappings = data.get("fareMappings", [])

    itin_dict = {it.get("itineraryId"): it for it in itineraries_list if it.get("itineraryId")}

    dep_date_clean = depart_date.replace("-", "").strip()
    ret_date_clean = return_date.replace("-", "").strip()

    offers: List[RoundTripOffer] = []

    for fm in fare_mappings:
        itin_ids_str = fm.get("itineraryIds", "")
        parts = itin_ids_str.split("-")
        if len(parts) != 2:
            continue
        out_id, in_id = parts[0], parts[1]
        out_itin = itin_dict.get(out_id)
        in_itin = itin_dict.get(in_id)
        if not out_itin or not in_itin:
            continue

        fares = fm.get("fares", [])
        if not fares:
            continue

        if no_card:
            eligible_fares = [f for f in fares if f.get("fareType") == "A01"]
        else:
            eligible_fares = fares

        if not eligible_fares:
            continue

        best_fare = min(
            eligible_fares,
            key=lambda f: f.get("adult", {}).get("totalFare", float("inf")),
        )

        adult_obj = best_fare.get("adult", {})
        per_adult_fare = adult_obj.get("totalFare", 0)
        if per_adult_fare <= 0:
            continue
        total_price = int(per_adult_fare * adults)

        fare_type = best_fare.get("fareType", "A01")
        has_card_discount = (fare_type != "A01")

        if has_card_discount:
            cond_raw = fare_types_code_map.get(fare_type, {}).get("name", "카드할인")
            if cond_raw.startswith("성인/"):
                cond_raw = cond_raw[3:]
            payment_condition = cond_raw
        else:
            payment_condition = "모든 결제수단"

        partner_code = best_fare.get("partnerCode", "")
        seller_name = PARTNER_CODE_MAP.get(partner_code, partner_code)

        baggage_fee_type = best_fare.get("baggageFeeType", "UNKNOWN")
        has_checked_baggage = (baggage_fee_type == "FREE")
        baggage_desc = "위탁수하물 포함" if has_checked_baggage else "위탁수하물 미포함"

        out_leg = _parse_naver_flight_leg(
            out_itin,
            airlines_code_map=airlines_code_map,
            has_checked_baggage=has_checked_baggage,
            baggage_desc=baggage_desc,
        )
        in_leg = _parse_naver_flight_leg(
            in_itin,
            airlines_code_map=airlines_code_map,
            has_checked_baggage=has_checked_baggage,
            baggage_desc=baggage_desc,
        )

        if not out_leg or not in_leg:
            continue

        is_direct = bool(out_leg.is_direct and in_leg.is_direct)
        if direct_only and not is_direct:
            continue

        # 네이버 상세 딥링크 URL 생성
        out_carrier = (
            out_itin.get("segments", [{}])[0].get("marketingCarrier", {}).get("airlineCode", "")
        )
        in_carrier = (
            in_itin.get("segments", [{}])[0].get("marketingCarrier", {}).get("airlineCode", "")
        )
        selected_flight = (
            f"1:{out_id}:{fare_type}:HK:{out_carrier}:,2:{in_id}:{fare_type}:HK:{in_carrier}:"
        )
        deeplink_url = (
            f"https://flight.naver.com/flights/international/detail/"
            f"{origin.upper()}-{dest.upper()}-{dep_date_clean}/"
            f"{dest.upper()}-{origin.upper()}-{ret_date_clean}"
            f"?adult={adults}&fareType=Y&selectedFlight={selected_flight}"
        )

        offer = RoundTripOffer(
            outbound_leg=out_leg,
            inbound_leg=in_leg,
            total_price=total_price,
            currency="KRW",
            is_direct=is_direct,
            deeplink_url=deeplink_url,
            provider="네이버",
            seller_name=seller_name,
            payment_condition=payment_condition,
            has_card_discount=has_card_discount,
        )
        offers.append(offer)

    offers.sort(key=lambda o: o.sort_key())
    if limit > 0:
        offers = offers[:limit]
    return offers


class NaverFlightCollector:
    """Camoufox 헤드리스 세션 기반 네이버 항공권 실시간 수집기."""

    def __init__(self, timeout_ms: int = 60000) -> None:
        self.timeout_ms = timeout_ms

    def search_round_trip(
        self,
        origin: str,
        dest: str,
        depart_date: str,
        return_date: str,
        direct_only: bool = False,
        limit: int = 20,
        adults: int = 2,
        no_card: bool = False,
        max_retries: int = 1,
        backoff_seconds: float = 1.5,
    ) -> List[RoundTripOffer]:
        """네이버 항공권 실시간 왕복 항공권 검색 및 결과 반환.

        WAF 503 차단(`BotDetectionBlockedError`) 또는 네트워크 오류
        (`NetworkTimeoutError`) 발생 시 `backoff_seconds`만큼 대기한 뒤 새
        Camoufox 세션으로 재시도한다. 재시도는 `max_retries`회로 엄격히 제한되어
        영구 장애 상황에서 무한 루프에 빠지지 않는다.
        """
        last_exception: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.warning(
                        f"네이버 항공권 수집 1차 실패 후 {backoff_seconds}초 백오프 대기 후 {attempt}회차 재시도 실행..."
                    )
                    time.sleep(backoff_seconds)
                return self._execute_search_once(
                    origin=origin,
                    dest=dest,
                    depart_date=depart_date,
                    return_date=return_date,
                    direct_only=direct_only,
                    limit=limit,
                    adults=adults,
                    no_card=no_card,
                )
            except (BotDetectionBlockedError, NetworkTimeoutError) as e:
                last_exception = e
                logger.warning(f"네이버 항공권 수집 시도 {attempt + 1} 실패: {e}")
                if attempt >= max_retries:
                    raise
        if last_exception:
            raise last_exception
        return []

    def _execute_search_once(
        self,
        origin: str,
        dest: str,
        depart_date: str,
        return_date: str,
        direct_only: bool = False,
        limit: int = 20,
        adults: int = 2,
        no_card: bool = False,
    ) -> List[RoundTripOffer]:
        """단일 Camoufox 세션을 기동하여 네이버 항공권을 1회 수집한다."""
        logger.info(f"네이버 항공권 세션 시작: {origin} ➔ {dest} ({depart_date} ~ {return_date})")

        payload = build_naver_search_payload(
            origin=origin,
            dest=dest,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            direct_only=direct_only,
            limit=max(limit * 5, 100),
        )

        with Camoufox(
            headless=True,
            os="windows",
            locale="ko-KR",
            block_images=False,
        ) as browser:
            page = browser.new_page()
            try:
                page.goto(
                    NAVER_FLIGHT_HOME,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )
            except Exception as e:
                raise NetworkTimeoutError(f"네이버 항공권 페이지 진입 중 오류 발생: {e}")

            try:
                res = page.evaluate(FETCH_JS, [NAVER_SEARCH_API, payload])
            except Exception as e:
                raise NetworkTimeoutError(f"네이버 항공권 API 호출 중 오류 발생: {e}")

            if not isinstance(res, dict):
                raise NetworkTimeoutError("네이버 항공권 응답을 수신하지 못했습니다.")

            if res.get("error"):
                raise NetworkTimeoutError(f"네이버 항공권 fetch 에러: {res['error']}")

            status_code = res.get("status")
            if status_code in (403, 429, 430, 503):
                raise BotDetectionBlockedError(
                    f"네이버 항공권 WAF에 의해 차단되었습니다 (HTTP {status_code})."
                )
            if status_code != 201:
                raise FlightSearchError(
                    f"네이버 항공권 API 비정상 응답 코드 (HTTP {status_code})."
                )

            raw_text = res.get("text", "")
            data = parse_naver_sse(raw_text)
            if not data:
                raise NetworkTimeoutError("네이버 항공권 SSE 응답 데이터를 파싱할 수 없습니다.")

            offers = parse_naver_flight_offers(
                data=data,
                origin=origin,
                dest=dest,
                depart_date=depart_date,
                return_date=return_date,
                direct_only=direct_only,
                limit=limit,
                adults=adults,
                no_card=no_card,
            )
            return offers
