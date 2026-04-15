from __future__ import annotations

import re
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

CAR365_URL = "https://www.car365.go.kr/ccpt/carlife/scrcar/schdcarXportView.do"
REQUEST_TIMEOUT = 25


def _default_car365_result() -> Dict[str, Any]:
    return {
        "returned_chassis_no": "",
        "vehicle_trademark": "",
        "vehicle_first_registration": "",
        "vehicle_fuel": "",
        "vehicle_displacement": "",
        "status": "SKIPPED",
        "error": "",
    }


def normalize_vin(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def _clean_text(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _trim_noise(value: str) -> str:
    value = _clean_text(value)
    stop_words = [
        "차량 정보",
        "Vehicle information",
        "수출신고",
        "Export declaration",
        "최종 주행거리",
        "Final drive distance",
        "색상",
        "Color",
        "승차정원",
        "Riding Capacity",
        "길이",
        "Length",
        "너비",
        "Width",
        "높이",
        "Height",
        "전손 여부",
        "Full damaged Y/N",
    ]
    for stop_word in stop_words:
        pos = value.find(stop_word)
        if pos > 0:
            value = value[:pos].strip()
    return value


def _extract_field_value(text: str, ko_label: str, en_label: Optional[str] = None) -> str:
    patterns = []

    if en_label:
        patterns.append(
            rf"{re.escape(ko_label)}\s*\(\s*{re.escape(en_label)}\s*\)\s*[:：]?\s*(.+?)(?=\s+(?:차명|차대번호|최초등록일|연료|배기량|최종 주행거리|색상|승차정원|길이|너비|높이|전손 여부)\b|$)"
        )

    patterns.append(
        rf"{re.escape(ko_label)}\s*[:：]?\s*(.+?)(?=\s+(?:차명|차대번호|최초등록일|연료|배기량|최종 주행거리|색상|승차정원|길이|너비|높이|전손 여부)\b|$)"
    )

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            value = _trim_noise(match.group(1))
            if value:
                return value

    return ""


def fetch_car365_vehicle_info(vin: str) -> Dict[str, Any]:
    result = _default_car365_result()
    expected_vin = normalize_vin(vin)

    if not expected_vin:
        result["status"] = "ERROR"
        result["error"] = "VIN is empty"
        return result

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": CAR365_URL,
        }
    )

    try:
        # If you already have a working way to submit VIN to Car365,
        # keep it. Below is only a safe result validation.
        response = session.get(CAR365_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        parsed = _parse_car365_html(response.text, expected_vin)
        result.update(parsed)
        return result

    except Exception as exc:
        result["status"] = "ERROR"
        result["error"] = f"Car365 request error: {exc}"
        return result


def _parse_car365_html(html: str, expected_vin: str) -> Dict[str, Any]:
    result = _default_car365_result()

    soup = BeautifulSoup(html, "html.parser")
    text = _clean_text(soup.get_text(" ", strip=True))

    returned_chassis_no = _extract_field_value(
        text,
        ko_label="차대번호",
        en_label="Chassis No",
    )
    returned_chassis_no = normalize_vin(returned_chassis_no)
    result["returned_chassis_no"] = returned_chassis_no

    if not returned_chassis_no:
        result["status"] = "ERROR"
        result["error"] = "Chassis No not found on Car365 page"
        return result

    if returned_chassis_no != expected_vin:
        result["status"] = "VIN_MISMATCH"
        result["error"] = (
            f"VIN mismatch. OCR VIN: {expected_vin}, Car365 Chassis No: {returned_chassis_no}"
        )
        return result

    if (
        "차량 수출정보가 확인되지 않습니다" in text
        or "Vehicle export information is not confirmed" in text
    ):
        result["status"] = "NOT_CONFIRMED"
        result["error"] = "Car365 did not confirm export information"
        return result

    result["vehicle_trademark"] = _extract_field_value(
        text,
        ko_label="차명",
        en_label="Trademark of vehicle",
    )
    result["vehicle_first_registration"] = _extract_field_value(
        text,
        ko_label="최초등록일",
        en_label="Date of first Registration",
    )
    result["vehicle_fuel"] = _extract_field_value(
        text,
        ko_label="연료",
        en_label="Fuel",
    )
    result["vehicle_displacement"] = _extract_field_value(
        text,
        ko_label="배기량",
        en_label="Displacement",
    )

    if not any(
        [
            result["vehicle_trademark"],
            result["vehicle_first_registration"],
            result["vehicle_fuel"],
            result["vehicle_displacement"],
        ]
    ):
        result["status"] = "ERROR"
        result["error"] = "Car365 fields were not recognized"
        return result

    result["status"] = "OK"
    return result