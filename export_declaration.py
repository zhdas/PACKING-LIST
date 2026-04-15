from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import pdfplumber


def _default_export_result() -> Dict[str, Any]:
    return {
        "hs_code": "",
        "weight": "",
        "status": "OK",
        "error": "",
    }


def extract_export_declaration_info(pdf_path: Path) -> Dict[str, Any]:
    result = _default_export_result()

    try:
        text_parts = []

        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)

        full_text = "\n".join(text_parts)

        if not full_text.strip():
            result["status"] = "ERROR"
            result["error"] = "PDF is empty or text could not be extracted"
            return result

        hs_match = re.search(r"세번부호\s*([\d\.\-]+)", full_text)
        weight_match = re.search(r"순중량\s*([\d,\.]+)", full_text)

        result["hs_code"] = hs_match.group(1).strip() if hs_match else ""

        if weight_match:
            result["weight"] = weight_match.group(1).replace(",", "").strip()

        if not result["hs_code"] and not result["weight"]:
            result["status"] = "ERROR"
            result["error"] = "HS CODE and WEIGHT were not found"
            return result

        return result

    except Exception as exc:
        result["status"] = "ERROR"
        result["error"] = f"Export declaration parser error: {exc}"
        return result