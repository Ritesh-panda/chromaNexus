import pytest
from backend.app.ai.clinical_extractor.validator import (
    ClinicalDataValidator,
    ValidatedLab,
    ValidatedMedication,
    ValidatedDisease,
)


def test_validator_valid_lab_value():
    lab = ClinicalDataValidator.validate_lab_result(
        test_name="HbA1c",
        value_str="6.8",
        unit_str="%",
        reference_range="<5.7"
    )
    assert isinstance(lab, ValidatedLab)
    assert lab.is_valid is True
    assert lab.normalized_numeric_value == 6.8
    assert lab.status == "high"


def test_validator_invalid_lab_value():
    lab = ClinicalDataValidator.validate_lab_result(
        test_name="Glucose",
        value_str="not_a_number_reading",
        unit_str="mg/dL"
    )
    assert lab.is_valid is False
    assert lab.normalized_numeric_value is None


def test_validator_date_normalization():
    # Standard YYYY-MM-DD
    assert ClinicalDataValidator.validate_and_normalize_date("2024-03-15") == "2024-03-15"
    
    # Month name format
    assert ClinicalDataValidator.validate_and_normalize_date("March 15, 2024") == "2024-03-15"
    
    # Slash format
    assert ClinicalDataValidator.validate_and_normalize_date("03/15/2024") == "2024-03-15"
    
    # Invalid date returns None
    assert ClinicalDataValidator.validate_and_normalize_date("completely_invalid_date_xyz") is None


def test_validator_medication():
    med = ClinicalDataValidator.validate_medication(
        name="Metformin",
        dosage="500mg",
        frequency="Twice daily"
    )
    assert isinstance(med, ValidatedMedication)
    assert med.is_valid is True
    assert med.name == "Metformin"
    assert med.dosage == "500mg"


def test_validator_disease():
    disease = ClinicalDataValidator.validate_disease(
        name="Type 2 Diabetes Mellitus",
        icd_code="E11.9",
        status="chronic"
    )
    assert isinstance(disease, ValidatedDisease)
    assert disease.is_valid is True
    assert disease.icd_code == "E11.9"
    assert disease.status == "chronic"

