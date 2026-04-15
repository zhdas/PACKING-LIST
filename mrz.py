from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

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