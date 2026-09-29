from __future__ import annotations

import copy
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from camoufox.sync_api import Camoufox

from src.models import FlightLeg, RoundTripOffer

logger = logging.getLogger(__name__)

SSE_ENDPOINT = "https://kr.trip.com/restapi/soa2/27015/FlightListSearchSSE"

FETCH_JS = r"""
async ([url, body]) => {
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
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


class FlightSearchError(Exception):
    """항공권 검색 기본 예외."""
    pass


class BotDetectionBlockedError(FlightSearchError):
    """트립닷컴 WAF 또는 캡차 차단 예외."""
    pass


class NetworkTimeoutError(FlightSearchError):
    """네트워크 타임아웃 또는 데이터 수신 실패 예외."""
    pass


def build_showfarefirst_url(
    origin: str,
    dest: str,
    depart_date: str,
    return_date: str,
    adults: int = 2,
) -> str:
    """트립닷컴 왕복 항공권 검색 및 예약 딥링크 URL 생성."""
    return (
        f"https://kr.trip.com/flights/showfarefirst"
        f"?dcity={origin.upper()}&acity={dest.upper()}"
        f"&ddate={depart_date}&rdate={return_date}"
        f"&triptype=rt&class=y&quantity={adults}&locale=ko-KR&curr=KRW"
    )


def extract_sse_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """SSE 형식 ('data:{...}') 텍스트에서 JSON 객체 추출."""
    if not raw_text:
        return None
    for line in raw_text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            payload = line[5:].strip()
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                continue
    # data: 프리픽스가 없는 단독 JSON 문자열인 경우
    try:
        return json.loads(raw_text.strip())
    except Exception:
        return None


def extract_airline_map(data: Dict[str, Any]) -> Dict[str, str]:
    """airlineList로부터 항공사 코드 -> 한글 명칭 맵핑 테이블 생성."""
    mapping: Dict[str, str] = {}
    for item in data.get("airlineList", []):
        code = item.get("code")
        name = item.get("name") or item.get("airlineName")
        if code and name:
            mapping[code] = name
    return mapping

def extract_linked_inbound_flight(short_policy_id: str) -> Optional[str]:
    """shortPolicyId에서 2번째 여정(귀국편)의 항공편 편명 추출.
    예: 'SEL,NHA,2027-01-13|NHA,SEL,2027-01-16;1;1,1,1,VJ835,1,...|2,1,1,VJ836,1,1800113400000' -> 'VJ836'
    """
    if not short_policy_id:
        return None
    match = re.search(r"\|2,\d+,\d+,([A-Z0-9]+),", short_policy_id)
    if match:
        return match.group(1).upper()
    return None


def parse_flight_leg_from_itinerary(
    itin: Dict[str, Any],
    airline_map: Dict[str, str],
    journey_index: int = 0,
) -> Optional[FlightLeg]:
    """Itinerary 객체의 journeyList[journey_index]로부터 FlightLeg 모델 추출."""
    journey_list = itin.get("journeyList", [])
    if not journey_list or len(journey_list) <= journey_index:
        return None

    journey = journey_list[journey_index]
    trans_sections = journey.get("transSectionList", [])
    if not trans_sections:
        return None

    # 소요시간 (분)
    duration = journey.get("duration") or sum(s.get("duration", 0) for s in trans_sections)

    # 최초 출발편 및 최종 도착편
    first_sec = trans_sections[0]
    last_sec = trans_sections[-1]

    depart_time = first_sec.get("departDateTime", "")
    arrive_time = last_sec.get("arriveDateTime", "")
    depart_airport = first_sec.get("departPoint", {}).get("airportCode", "")
    arrive_airport = last_sec.get("arrivePoint", {}).get("airportCode", "")

    # 항공사 및 편명
    airline_codes = [s.get("flightInfo", {}).get("airlineCode", "") for s in trans_sections]
    flight_numbers = [s.get("flightInfo", {}).get("flightNo", "") for s in trans_sections]

    primary_airline_code = airline_codes[0] if airline_codes else ""
    airline_name = airline_map.get(primary_airline_code, primary_airline_code)

    flight_number_str = "/".join(filter(None, flight_numbers))

    # 직항 여부: transSectionList 길이가 1이거나 flagList에 DIRECT_FLIGHT 존재
    flag_list = itin.get("flagList", [])
    is_direct = (len(trans_sections) == 1) or ("DIRECT_FLIGHT" in flag_list)

    # 수하물 정보: policyFlags 또는 flagList 내 FREE_CHECKED_BAGGAGE 확인
    policies = itin.get("policies", [])
    policy_flags = policies[0].get("policyFlags", []) if policies else []
    has_checked_baggage = "FREE_CHECKED_BAGGAGE" in policy_flags or "FREE_CHECKED_BAGGAGE" in flag_list
    baggage_desc = "위탁수하물 포함" if has_checked_baggage else "위탁수하물 미포함"

    return FlightLeg(
        airline_name=airline_name,
        flight_number=flight_number_str,
        depart_time=depart_time,
        arrive_time=arrive_time,
        depart_airport=depart_airport,
        arrive_airport=arrive_airport,
        duration_minutes=int(duration or 0),
        is_direct=is_direct,
        has_checked_baggage=has_checked_baggage,
        baggage_desc=baggage_desc,
    )


class TripFlightCollector:
    """Camoufox 헤드리스 세션 기반 트립닷컴 왕복 항공권 실시간 수집기."""

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
    ) -> List[RoundTripOffer]:
        """트립닷컴 실시간 왕복 항공권 수집 (1단계 출국편 SSE -> 2단계 연계 귀국편 SSE)."""
        url = build_showfarefirst_url(origin, dest, depart_date, return_date, adults=adults)

        logger.info(f"트립닷컴 세션 시작: {origin} ➔ {dest} ({depart_date} ~ {return_date})")

        with Camoufox(
            headless=True,
            os="windows",
            locale="ko-KR",
            humanize=True,
            block_images=False,
        ) as browser:
            page = browser.new_page()

            captured_requests: List[str] = []
            captured_responses: List[str] = []
            blocked_status: List[int] = []

            def on_response(resp: Any) -> None:
                try:
                    if resp.status in (403, 429, 430):
                        blocked_status.append(resp.status)
                    if "FlightListSearchSSE" in resp.url:
                        post_data = resp.request.post_data
                        if post_data:
                            captured_requests.append(post_data)
                        text = resp.text()
                        if text:
                            captured_responses.append(text)
                except Exception:
                    pass

            page.on("response", on_response)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            except Exception as e:
                raise NetworkTimeoutError(f"페이지 진입 중 타임아웃/오류 발생: {e}")

            # 1차 SSE 데이터 수신 대기 (최대 25초)
            page.wait_for_timeout(25000)

            # 유효한 비행 데이터 SSE 수신 여부 확인
            if not captured_requests or not captured_responses:
                # 데이터 미수신 시 차단 상태 코드 또는 캡차 모달 진단
                if blocked_status:
                    raise BotDetectionBlockedError(
                        f"트립닷컴 WAF에 의해 접근이 차단되었습니다 (HTTP {blocked_status[0]})."
                    )
                self._check_captcha_or_block(page)
                raise NetworkTimeoutError("트립닷컴 비행 검색 SSE 응답을 수신하지 못했습니다.")

            # 1차 SSE 페이로드 파싱 (Journey 1 출국편)
            base_request_body = json.loads(captured_requests[0])
            first_sse_data = extract_sse_json(captured_responses[0])
            if not first_sse_data:
                self._check_captcha_or_block(page)
                raise NetworkTimeoutError("출국편 SSE 응답 데이터를 파싱할 수 없습니다.")
            airline_map = extract_airline_map(first_sse_data)
            itinerary_list = first_sse_data.get("itineraryList", [])

            if not itinerary_list:
                # 검색 결과 없음
                return []

            offers = self._collect_return_legs_and_combine(
                page=page,
                base_request_body=base_request_body,
                itinerary_list=itinerary_list,
                airline_map=airline_map,
                deeplink_url=url,
                direct_only=direct_only,
                limit=limit,
                adults=adults,
            )

            return offers

    def _check_captcha_or_block(self, page: Any) -> None:
        """DOM 및 렌더링된 화면에서 WAF 캡차 모달 노출 여부 정밀 탐지."""
        try:
            # 1. 화면에 표시된 모달 엘리먼트 검사 (#verification-pop 또는 dialog-Verification)
            modal_info = page.evaluate("""() => {
                const el = document.querySelector('#verification-pop, [data-testid="dialog-Verification"]');
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                const isVisible = (rect.width > 0 && rect.height > 0) || el.getAttribute('data-status') === 'visible';
                return {
                    visible: isVisible,
                    text: (el.innerText || '').trim()
                };
            }""")
            if modal_info and modal_info.get("visible"):
                txt = modal_info.get("text", "")
                raise BotDetectionBlockedError(
                    f"트립닷컴 보안 인증 모달이 감지되어 조회가 차단되었습니다 ({txt[:60]})."
                )

            # 2. 본문 렌더링 텍스트 내 차단/캡차 안내 문구 검사
            body_text = page.evaluate("() => document.body ? document.body.innerText : ''")
            for kw in ("시도 제한 횟수를 초과했습니다", "밀어서 퍼즐 완성하기", "아래의 인증을 완료해 주세요"):
                if kw in body_text:
                    raise BotDetectionBlockedError(
                        f"트립닷컴 보안 캡차가 감지되어 조회가 차단되었습니다 (문구: '{kw}')."
                    )
        except BotDetectionBlockedError:
            raise
        except Exception:
            pass

    def _collect_return_legs_and_combine(
        self,
        page: Any,
        base_request_body: Dict[str, Any],
        itinerary_list: List[Dict[str, Any]],
        airline_map: Dict[str, str],
        deeplink_url: str,
        direct_only: bool,
        limit: int,
        adults: int = 2,
    ) -> List[RoundTripOffer]:
        """1차 출국편의 policyId를 이용해 2차 귀국편 SSE를 수집하고 왕복 조합을 생성."""
        offers: List[RoundTripOffer] = []
        seen_combos = set()

        # 직항 출국편 우선 탐색
        direct_itins = [
            it for it in itinerary_list
            if "DIRECT_FLIGHT" in it.get("flagList", [])
            or (it.get("journeyList") and len(it["journeyList"][0].get("transSectionList", [])) == 1)
        ]
        non_direct_itins = [it for it in itinerary_list if it not in direct_itins]

        target_itins = direct_itins if direct_only else (direct_itins + non_direct_itins)

        # 처리할 최대 출국편 수 (너무 많은 fetch로 인한 지연 방지)
        candidates = target_itins[: max(15, limit)]

        stage2_attempts = 0
        stage2_block_errors: List[int] = []
        stage2_network_errors: List[str] = []

        for ob_itin in candidates:
            outbound_leg = parse_flight_leg_from_itinerary(ob_itin, airline_map, journey_index=0)
            if not outbound_leg:
                continue

            policies = ob_itin.get("policies", [])
            if not policies:
                continue

            primary_policy = policies[0]
            policy_id = primary_policy.get("policyId")
            total_price = int(primary_policy.get("price", {}).get("totalPrice") or 0)
            currency = primary_policy.get("price", {}).get("currency") or "KRW"
            base_bundle_price = total_price
            linked_inbound = extract_linked_inbound_flight(primary_policy.get("shortPolicyId", ""))

            if not policy_id:
                continue

            # 2차 귀국편 SSE 요청 (Journey 2)
            req_body = copy.deepcopy(base_request_body)
            req_body["searchCriteria"]["journeyNo"] = 2
            req_body["searchCriteria"]["policyId"] = policy_id
            if "passengerInfoType" in req_body["searchCriteria"]:
                req_body["searchCriteria"]["passengerInfoType"]["adultCount"] = adults
            stage2_attempts += 1
            try:
                res = page.evaluate(FETCH_JS, [SSE_ENDPOINT, req_body])
                if not isinstance(res, dict):
                    raw_text = str(res)
                    status_code = 200
                elif "error" in res:
                    stage2_network_errors.append(res["error"])
                    logger.warning(f"귀국편 SSE fetch 네트워크 실패 (policyId: {policy_id[:30]}): {res['error']}")
                    continue
                else:
                    status_code = res.get("status", 200)
                    raw_text = res.get("text", "")

                if status_code in (403, 429, 430):
                    stage2_block_errors.append(status_code)
                    logger.warning(f"귀국편 SSE fetch 차단 (HTTP {status_code})")
                    continue

                inbound_sse_data = extract_sse_json(raw_text)
            except Exception as e:
                stage2_network_errors.append(str(e))
                logger.warning(f"귀국편 SSE fetch 실패 (policyId: {policy_id[:30]}): {e}")
                continue

            if not inbound_sse_data:
                continue

            # 귀국편 airlineList 보강
            airline_map.update(extract_airline_map(inbound_sse_data))

            inbound_itins = inbound_sse_data.get("itineraryList", [])
            if not inbound_itins:
                continue
            for ib_itin in inbound_itins:
                inbound_leg = parse_flight_leg_from_itinerary(ib_itin, airline_map, journey_index=0)
                if not inbound_leg:
                    continue

                # direct_only 활성화 시: 출국편 또는 귀국편 중 하나라도 경유이면 제외
                if direct_only and (not outbound_leg.is_direct or not inbound_leg.is_direct):
                    continue
                # 2차 귀국편 itinerary의 policy로부터 실제 결합 가격(권위 있는 왕복 총액) 추출
                ib_policies = ib_itin.get("policies", [])
                if ib_policies:
                    ib_primary_policy = ib_policies[0]
                    actual_currency = ib_primary_policy.get("price", {}).get("currency") or currency
                    more_price = ib_primary_policy.get("price", {}).get("morePrice") or {}
                    diff = more_price.get("priceDifference")
                    if linked_inbound and (
                        inbound_leg.flight_number.upper() == linked_inbound
                        or linked_inbound in inbound_leg.flight_number.upper().split("/")
                    ):
                        actual_price = base_bundle_price
                    elif diff is not None:
                        actual_price = base_bundle_price + int(diff)
                    else:
                        actual_price = int(ib_primary_policy.get("price", {}).get("totalPrice") or base_bundle_price)
                else:
                    actual_price = base_bundle_price
                    actual_currency = currency

                combo_key = (
                    outbound_leg.flight_number,
                    outbound_leg.depart_time,
                    inbound_leg.flight_number,
                    inbound_leg.depart_time,
                    actual_price,
                )
                if combo_key in seen_combos:
                    continue
                seen_combos.add(combo_key)

                offer = RoundTripOffer(
                    outbound_leg=outbound_leg,
                    inbound_leg=inbound_leg,
                    total_price=actual_price,
                    currency=actual_currency,
                    deeplink_url=deeplink_url,
                )
                offers.append(offer)

            # 짧은 대기 (레이트 리밋 보호)
            page.wait_for_timeout(1000)

        # 출국편 후보가 존재했으나 2단계 귀국편 조회가 모두 차단/에러로 실패한 경우 에러 격리 보고
        if not offers and stage2_attempts > 0:
            if stage2_block_errors:
                raise BotDetectionBlockedError(
                    f"트립닷컴 귀국편 조회 중 WAF에 의해 접근이 차단되었습니다 (HTTP {stage2_block_errors[0]})."
                )
            if stage2_network_errors:
                raise NetworkTimeoutError(
                    f"트립닷컴 귀국편 조회 중 네트워크 연결 실패가 발생했습니다: {stage2_network_errors[0]}"
                )

        # 3단계 정렬 적용
        offers.sort(key=lambda o: o.sort_key())
        return offers
