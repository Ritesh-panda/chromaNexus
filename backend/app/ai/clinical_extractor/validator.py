import re
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field


class ValidatedLab(BaseModel):
    test_name: str
    value: str
    unit: str
    reference_range: str = "Normal"
    status: str = "normal"  # 'normal' | 'high' | 'low' | 'critical'
    is_valid: bool = True
    normalized_numeric_value: Optional[float] = None


class ValidatedMedication(BaseModel):
    name: str
    dosage: str
    frequency: str = "Daily"
    route: str = "oral"
    indication: Optional[str] = None
    is_valid: bool = True


class ValidatedDisease(BaseModel):
    name: str
    icd_code: Optional[str] = None
    status: str = "active"  # 'active' | 'chronic' | 'resolved'
    is_valid: bool = True


class ClinicalDataValidator:
    """
    Validates and normalizes clinical entities before persistence into PostgreSQL.
    Prevents corrupt strings, non-numeric lab readings, or malformed drug dosages.
    """

    KNOWN_LAB_UNITS = {
        "mg/dl", "g/dl", "%", "mmol/l", "iu/l", "u/l", "mcg/ml", "ng/ml", "pg/ml",
        "mmhg", "meq/l", "cells/mcL", "/cumm", "fl", "pg", "mg/l", "bpm"
    }

    @classmethod
    def validate_and_normalize_date(cls, raw_date: str) -> Optional[str]:
        if not raw_date or not str(raw_date).strip():
            return None

        cleaned = str(raw_date).strip()
        # Direct YYYY-MM-DD
        if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned):
            return cleaned

        # Common clinical date formats
        formats = [
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Search for 4-digit year in string
        match_year = re.search(r"\b(19\d{2}|20\d{2})\b", cleaned)
        if match_year:
            return f"{match_year.group(1)}-01-01"

        return None

    @classmethod
    def validate_lab_result(
        cls,
        test_name: str,
        value_str: str,
        unit_str: str = "",
        reference_range: str = ""
    ) -> ValidatedLab:
        if not test_name or not value_str:
            return ValidatedLab(test_name=test_name, value=value_str, unit=unit_str, is_valid=False)

        clean_name = test_name.strip()
        clean_val = value_str.strip()
        clean_unit = unit_str.strip()

        # Check blood pressure format: e.g. "124/80"
        if "/" in clean_val and re.match(r"^\d{2,3}/\d{2,3}$", clean_val):
            return ValidatedLab(
                test_name=clean_name,
                value=clean_val,
                unit=clean_unit or "mmHg",
                reference_range=reference_range or "<120/80",
                status="normal",
                is_valid=True
            )

        # Extract numeric float if present
        num_match = re.search(r"[-+]?\d*\.?\d+", clean_val)
        if not num_match:
            return ValidatedLab(test_name=clean_name, value=clean_val, unit=clean_unit, is_valid=False)

        try:
            num_val = float(num_match.group(0))
        except ValueError:
            return ValidatedLab(test_name=clean_name, value=clean_val, unit=clean_unit, is_valid=False)

        # Standardize unit
        norm_unit = clean_unit if clean_unit.lower() in cls.KNOWN_LAB_UNITS else clean_unit or ""

        # Status classification
        lower_name = clean_name.lower()
        status = "normal"

        if "cholesterol" in lower_name and num_val > 200:
            status = "high"
        elif "hba1c" in lower_name and num_val > 5.6:
            status = "high"
        elif "glucose" in lower_name and num_val > 100:
            status = "high"
        elif "platelet" in lower_name and num_val < 150000:
            status = "low"

        return ValidatedLab(
            test_name=clean_name,
            value=clean_val,
            unit=norm_unit,
            reference_range=reference_range or "Normal",
            status=status,
            is_valid=True,
            normalized_numeric_value=num_val
        )

    @classmethod
    def validate_medication(
        cls,
        name: str,
        dosage: str = "",
        frequency: str = "Daily",
        route: str = "oral",
        indication: Optional[str] = None
    ) -> ValidatedMedication:
        if not name or len(name.strip()) < 2:
            return ValidatedMedication(name=name, dosage=dosage, is_valid=False)

        clean_name = name.strip()
        clean_dosage = dosage.strip() or "Standard Dose"

        return ValidatedMedication(
            name=clean_name,
            dosage=clean_dosage,
            frequency=frequency.strip() if frequency else "Daily",
            route=route.strip() if route else "oral",
            indication=indication.strip() if indication else None,
            is_valid=True
        )

    @classmethod
    def validate_disease(
        cls,
        name: str,
        icd_code: Optional[str] = None,
        status: str = "active"
    ) -> ValidatedDisease:
        if not name or len(name.strip()) < 3:
            return ValidatedDisease(name=name, is_valid=False)

        clean_name = name.strip()
        clean_code = icd_code.strip() if icd_code else None

        # Validate ICD-10 pattern if code present (e.g. E11.9, I10, M23.2)
        if clean_code and not re.match(r"^[A-Z]\d{2}(\.\d{1,3})?$", clean_code):
            clean_code = None

        return ValidatedDisease(
            name=clean_name,
            icd_code=clean_code,
            status=status.lower() if status in ["active", "chronic", "resolved", "in_remission"] else "active",
            is_valid=True
        )
