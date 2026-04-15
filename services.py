from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import pdfplumber


DYNAMSOFT_LICENSE = (
    "t0123NQMAACjyKSqohUqI9GVALb08SKLayHN9n6bbyjQsgqDmQtphwWHSdKDx0o/HkGCzct9LAM6Me054PL4qhrEGVni3p4aVQ09s4n4t6SUjf1YMhYGzbpnyA1PbM9eavjPVc672mfbgNVN+YGp75m2fD5jewmCOWABVtKbT;t0124NQMAAKs1p7t9OU9wVOv8LlLwGTCtESBc4pfOvTbL4aEzrSDo8QLHofoa/ji9mbst0BFxdhkTxKHsNotAotHnKMN+x7EesxxaYhW3saSXjPxYEQsDR10y5Qemfs9canrPVONQ7TP9g8dM+YGp3zMv+7zBNB+id8QEek6m4w=="
)


def _default_passport_result() -> Dict[str, Any]:
    return {
        "document_type": "",
        "document_id": "",
        "surname": "",
        "given_name": "",
        "nationality": "",
        "issuer": "",
        "gender": "",
        "date_of_birth": "",
        "date_of_expiry": "",
        "status": "OK",
        "error": "",
    }


def _default_vin_result() -> Dict[str, Any]:
    return {
        "vin_string": "",
        "wmi": "",
        "region": "",
        "vds": "",
        "vis": "",
        "model_year": "",
        "plant_code": "",
        "status": "OK",
        "error": "",
    }


def _default_export_result() -> Dict[str, Any]:
    return {
        "hs_code": "",
        "weight": "",
        "status": "OK",
        "error": "",
    }


def normalize_vin(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def extract_passport_info(image_path: Path) -> Dict[str, Any]:
    result = _default_passport_result()

    try:
        from dynamsoft_capture_vision_bundle import (  # type: ignore
            CaptureVisionRouter,
            EnumErrorCode,
            EnumValidationStatus,
            LicenseManager,
        )

        error_code, error_message = LicenseManager.init_license(DYNAMSOFT_LICENSE)
        if error_code not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_WARNING):
            result["status"] = "ERROR"
            result["error"] = f"License init failed: {error_message}"
            return result

        cvr = CaptureVisionRouter()
        result_array = cvr.capture_multi_pages(str(image_path), "ReadPassportAndId")
        results = result_array.get_results()

        if not results:
            result["status"] = "ERROR"
            result["error"] = "MRZ not recognized"
            return result

        for capture_result in results:
            parsed_result = capture_result.get_parsed_result()
            if parsed_result is None:
                continue

            items = parsed_result.get_items()
            if not items:
                continue

            for item in items:
                result["document_type"] = item.get_code_type() or ""

                if item.get_field_value("passportNumber") and item.get_field_validation_status("passportNumber") != EnumValidationStatus.VS_FAILED:
                    result["document_id"] = item.get_field_value("passportNumber")
                elif item.get_field_value("documentNumber") and item.get_field_validation_status("documentNumber") != EnumValidationStatus.VS_FAILED:
                    result["document_id"] = item.get_field_value("documentNumber")

                if item.get_field_value("primaryIdentifier") and item.get_field_validation_status("primaryIdentifier") != EnumValidationStatus.VS_FAILED:
                    result["surname"] = item.get_field_value("primaryIdentifier")

                if item.get_field_value("secondaryIdentifier") and item.get_field_validation_status("secondaryIdentifier") != EnumValidationStatus.VS_FAILED:
                    result["given_name"] = item.get_field_value("secondaryIdentifier")

                if item.get_field_value("nationality") and item.get_field_validation_status("nationality") != EnumValidationStatus.VS_FAILED:
                    result["nationality"] = item.get_field_value("nationality")

                if item.get_field_value("issuingState") and item.get_field_validation_status("issuingState") != EnumValidationStatus.VS_FAILED:
                    result["issuer"] = item.get_field_value("issuingState")

                if item.get_field_value("sex") and item.get_field_validation_status("sex") != EnumValidationStatus.VS_FAILED:
                    result["gender"] = item.get_field_value("sex")

                if item.get_field_value("dateOfBirth") and item.get_field_validation_status("dateOfBirth") != EnumValidationStatus.VS_FAILED:
                    result["date_of_birth"] = item.get_field_value("dateOfBirth")

                if item.get_field_value("dateOfExpiry") and item.get_field_validation_status("dateOfExpiry") != EnumValidationStatus.VS_FAILED:
                    result["date_of_expiry"] = item.get_field_value("dateOfExpiry")

                return result

        result["status"] = "ERROR"
        result["error"] = "Passport fields not found"
        return result

    except Exception as exc:
        result["status"] = "ERROR"
        result["error"] = f"Passport parser error: {exc}"
        return result


def extract_vin_info(image_path: Path) -> Dict[str, Any]:
    result = _default_vin_result()

    try:
        from dynamsoft_capture_vision_bundle import (  # type: ignore
            CaptureVisionRouter,
            EnumErrorCode,
            EnumValidationStatus,
            LicenseManager,
        )

        error_code, error_message = LicenseManager.init_license(DYNAMSOFT_LICENSE)
        if error_code not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_WARNING):
            result["status"] = "ERROR"
            result["error"] = f"License init failed: {error_message}"
            return result

        cvr = CaptureVisionRouter()
        templates = ["ReadVINText", "ReadVINBarcode"]
        last_error = "VIN fields not found"

        for template_name in templates:
            result_array = cvr.capture_multi_pages(str(image_path), template_name)
            results = result_array.get_results()

            if not results:
                continue

            for capture_result in results:
                parsed_result = capture_result.get_parsed_result()
                if parsed_result is None:
                    continue

                items = parsed_result.get_items()
                if not items:
                    continue

                for item in items:
                    if item.get_code_type() != "VIN":
                        continue

                    raw_vin = item.get_field_value("vinString")
                    if raw_vin:
                        result["vin_string"] = normalize_vin(raw_vin)

                    if item.get_field_value("WMI") and item.get_field_validation_status("WMI") != EnumValidationStatus.VS_FAILED:
                        result["wmi"] = item.get_field_value("WMI")
                    if item.get_field_value("region") and item.get_field_validation_status("region") != EnumValidationStatus.VS_FAILED:
                        result["region"] = item.get_field_value("region")
                    if item.get_field_value("VDS") and item.get_field_validation_status("VDS") != EnumValidationStatus.VS_FAILED:
                        result["vds"] = item.get_field_value("VDS")
                    if item.get_field_value("VIS") and item.get_field_validation_status("VIS") != EnumValidationStatus.VS_FAILED:
                        result["vis"] = item.get_field_value("VIS")
                    if item.get_field_value("modelYear") and item.get_field_validation_status("modelYear") != EnumValidationStatus.VS_FAILED:
                        result["model_year"] = item.get_field_value("modelYear")
                    if item.get_field_value("plantCode") and item.get_field_validation_status("plantCode") != EnumValidationStatus.VS_FAILED:
                        result["plant_code"] = item.get_field_value("plantCode")

                    if result["vin_string"]:
                        return result

            last_error = f"VIN not found using {template_name}"

        result["status"] = "ERROR"
        result["error"] = last_error
        return result

    except Exception as exc:
        result["status"] = "ERROR"
        result["error"] = f"VIN parser error: {exc}"
        return result


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