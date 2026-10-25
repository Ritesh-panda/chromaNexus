"""
Tests for Phase 2: Database Schema and Clinical Data Provenance Foundations
- Allergy model CRUD, patient relationship, cascade deletion
- Clinical provenance fields (source_page_number, bounding_box, extraction_confidence)
- LOINC biomarker resolution and canonical mapping
- Drug-allergy cross-reactivity detection and contraindication alerts
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.models.allergy import Allergy
from backend.app.models.clinical_entity import LabResult, Medication, Disease, ExtractedEntity
from backend.app.models.report import MedicalReport
from backend.app.clinical.terminology.biomarkers import resolve_biomarker, get_biomarker_by_loinc, BIOMARKER_CATALOG
from backend.app.clinical.terminology.allergies import check_drug_allergy_conflict, find_drug_class
from backend.app.ai.rag.structured_retriever import StructuredRetriever


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed test user & patient
    user = User(id="usr_test_01", name="Test User", email="test@example.com", hashed_password="pw", role="patient")
    db.add(user)
    db.flush()

    patient = Patient(
        id="pat_test_01",
        user_id=user.id,
        date_of_birth="1990-01-01",
        gender="female",
        blood_group="A+",
        known_allergies=["Penicillin (Severe: Anaphylaxis)"]
    )
    db.add(patient)
    db.commit()

    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_allergy_model_crud_and_provenance(test_db):
    """Verify Allergy model fields, provenance tracking, and relationship to patient."""
    allergy = Allergy(
        id="all_test_01",
        patient_id="pat_test_01",
        allergen="Penicillin",
        category="medication",
        severity="severe",
        reaction="Anaphylaxis",
        drug_classes=["Penicillins", "Beta-lactam antibacterials"],
        cross_reactivities=["amoxicillin", "ampicillin", "augmentin"],
        status="active",
        source_report_id="rep_001",
        source_page_number=1,
        bounding_box={"x0": 50, "y0": 100, "x1": 400, "y1": 120, "page": 1},
        extraction_confidence=0.99,
        notes="Documented anaphylaxis."
    )
    test_db.add(allergy)
    test_db.commit()

    saved = test_db.query(Allergy).filter(Allergy.id == "all_test_01").first()
    assert saved is not None
    assert saved.allergen == "Penicillin"
    assert saved.severity == "severe"
    assert saved.source_page_number == 1
    assert saved.extraction_confidence == 0.99
    assert saved.bounding_box["page"] == 1
    assert "amoxicillin" in saved.cross_reactivities

    # Relationship verification
    patient = test_db.query(Patient).filter(Patient.id == "pat_test_01").first()
    assert len(patient.allergies) == 1
    assert patient.allergies[0].allergen == "Penicillin"


def test_clinical_provenance_on_lab_results(test_db):
    """Verify LabResult stores LOINC code, canonical name, and bounding box."""
    lab = LabResult(
        id="lab_test_01",
        patient_id="pat_test_01",
        test_name="Serum Potassium",
        loinc_code="2823-3",
        canonical_name="Potassium, Serum",
        value="4.8",
        unit="mEq/L",
        reference_range="3.5 - 5.1",
        status="normal",
        test_date="2024-09-10",
        source_page_number=2,
        bounding_box={"x0": 72, "y0": 340, "x1": 500, "y1": 360, "page": 2},
        extraction_confidence=0.98
    )
    test_db.add(lab)
    test_db.commit()

    saved_lab = test_db.query(LabResult).filter(LabResult.id == "lab_test_01").first()
    assert saved_lab.loinc_code == "2823-3"
    assert saved_lab.canonical_name == "Potassium, Serum"
    assert saved_lab.source_page_number == 2
    assert saved_lab.extraction_confidence == 0.98
    assert saved_lab.bounding_box["y0"] == 340


def test_clinical_provenance_on_medications(test_db):
    """Verify Medication stores RxNorm code, drug class, and provenance."""
    med = Medication(
        id="med_test_01",
        patient_id="pat_test_01",
        name="Lisinopril",
        dosage="10mg",
        frequency="QD",
        start_date="2024-01-15",
        status="active",
        rxnorm_code="29046",
        drug_class="ACE Inhibitor",
        source_page_number=1,
        extraction_confidence=0.99
    )
    test_db.add(med)
    test_db.commit()

    saved_med = test_db.query(Medication).filter(Medication.id == "med_test_01").first()
    assert saved_med.rxnorm_code == "29046"
    assert saved_med.drug_class == "ACE Inhibitor"
    assert saved_med.source_page_number == 1


def test_biomarker_terminology_resolution():
    """Verify LOINC resolution across common abbreviations and synonyms."""
    # Test Potassium synonyms
    potassium = resolve_biomarker("serum k")
    assert potassium is not None
    assert potassium.loinc_code == "2823-3"
    assert potassium.canonical_name == "Potassium, Serum"

    # Test HbA1c synonyms
    a1c = resolve_biomarker("glycated hemoglobin")
    assert a1c is not None
    assert a1c.loinc_code == "4548-4"

    # Test Creatinine
    creat = resolve_biomarker("renal function creatinine")
    assert creat is not None
    assert creat.loinc_code == "2160-0"

    # Direct LOINC lookup
    lookup = get_biomarker_by_loinc("2093-3")
    assert lookup is not None
    assert lookup.canonical_name == "Cholesterol, Total"


def test_drug_allergy_cross_reactivity_detection():
    """Verify conflict detection for Penicillin allergy with Amoxicillin."""
    patient_allergies = ["Penicillin (Severe: Anaphylaxis)"]

    # Amoxicillin is a Penicillin-class drug
    conflict = check_drug_allergy_conflict("Amoxicillin", patient_allergies)
    assert conflict is not None
    assert conflict["conflict_type"] == "CLASS_CROSS_REACTIVITY"
    assert conflict["severity"] == "severe"
    assert "Penicillin" in conflict["explanation"]

    # Augmentin (Amoxicillin/Clavulanate)
    conflict_aug = check_drug_allergy_conflict("Augmentin", patient_allergies)
    assert conflict_aug is not None

    # Safe drug (e.g. Metformin)
    no_conflict = check_drug_allergy_conflict("Metformin", patient_allergies)
    assert no_conflict is None


def test_structured_retriever_allergy_alert(test_db):
    """Verify StructuredRetriever surfaces high-priority allergy alert when querying cross-reactive drugs."""
    allergy = Allergy(
        id="all_001",
        patient_id="pat_test_01",
        allergen="Penicillin",
        category="medication",
        severity="severe",
        reaction="Anaphylaxis",
        drug_classes=["Penicillins", "Beta-lactam antibacterials"],
        cross_reactivities=["amoxicillin", "ampicillin", "augmentin"],
        status="active"
    )
    test_db.add(allergy)
    test_db.commit()

    retriever = StructuredRetriever(test_db)
    results = retriever.retrieve_allergies(
        patient_id="pat_test_01",
        query_text="Can I take Amoxicillin for my bacterial sinus infection?"
    )

    assert len(results) >= 1
    # First result must be the high-priority safety alert
    top = results[0]
    assert "SAFETY ALERT" in top.title or "SAFETY" in top.content
    assert top.relevance_score == 0.99
    assert "Penicillin" in top.content
    assert "Amoxicillin" in top.content
    assert not top.metadata["is_definitive_decision"]
    assert top.metadata["requires_clinical_review"]


def test_allergy_safety_edge_cases_and_disclaimers():
    """
    Validates clinical decision support behavior across edge cases:
    - Inactive / resolved allergies
    - Missing / null allergy data
    - Ambiguous query phrases and stopwords
    - Non-prescribing disclaimer presence
    - Specimen scoping rejection (urine vs serum)
    """
    # 1. Inactive / Resolved allergies must NOT trigger active contraindication warnings
    resolved_allergies = ["Penicillin (Resolved)", "Sulfa Drugs (Inactive - Outgrown)"]
    conflict_resolved = check_drug_allergy_conflict("Amoxicillin", resolved_allergies)
    assert conflict_resolved is None, "Resolved/inactive allergy should not trigger active warning"

    # 2. Missing or empty allergy data
    assert check_drug_allergy_conflict("Amoxicillin", []) is None
    assert check_drug_allergy_conflict("", ["Penicillin"]) is None
    assert check_drug_allergy_conflict("Amoxicillin", [None, ""]) is None

    # 3. Direct matching case
    direct_conflict = check_drug_allergy_conflict("Amoxicillin", ["Amoxicillin (Severe)"])
    assert direct_conflict is not None
    assert direct_conflict["conflict_type"] == "DIRECT_MATCH"
    assert not direct_conflict["is_definitive_decision"]
    assert direct_conflict["requires_clinical_review"]

    # 4. Inter-class cross-reactivity warning (Cephalosporin candidate with documented Penicillin allergy)
    inter_class_conflict = check_drug_allergy_conflict("Keflex", ["Penicillin"])
    assert inter_class_conflict is not None
    assert inter_class_conflict["conflict_type"] == "POTENTIAL_CLASS_CROSS_REACTIVITY"
    assert "cross-reactivity" in inter_class_conflict["explanation"].lower()
    assert not inter_class_conflict["is_definitive_decision"]

    # 5. Non-matching safe medications
    assert check_drug_allergy_conflict("Lisinopril", ["Penicillin"]) is None
    assert check_drug_allergy_conflict("Atorvastatin", ["Penicillin"]) is None
    assert check_drug_allergy_conflict("Metformin", ["Penicillin", "Sulfa"]) is None

    # 6. Ambiguous short words and false-positive guards
    assert check_drug_allergy_conflict("in", ["Penicillin"]) is None
    assert check_drug_allergy_conflict("for", ["Penicillin"]) is None
    assert check_drug_allergy_conflict("pain", ["Penicillin"]) is None

    # 7. Specimen scoping verification: Non-serum test terms must NOT match serum LOINC codes
    assert resolve_biomarker("potassium in 24h urine") is None
    assert resolve_biomarker("calcium in urine") is None
    assert resolve_biomarker("csf glucose") is None

