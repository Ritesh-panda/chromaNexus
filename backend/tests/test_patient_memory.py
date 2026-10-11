import pytest
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.models.clinical_entity import Disease, Medication, LabResult
from backend.app.core.security import create_access_token


def test_get_patient_diagnoses(client):
    response = client.get("/api/v1/patients/me/diagnoses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    disease_names = [d["name"] for d in data]
    assert "Type 2 Diabetes Mellitus" in disease_names
    assert "Essential (Primary) Hypertension" in disease_names


def test_get_patient_medications(client):
    response = client.get("/api/v1/patients/me/medications")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    med_names = [m["name"] for m in data]
    assert "Metformin HCl" in med_names
    assert "Lisinopril" in med_names


def test_get_patient_labs(client):
    response = client.get("/api/v1/patients/me/labs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 6
    test_names = [l["testName"] for l in data]
    assert "Hemoglobin A1c (HbA1c)" in test_names
    assert "Total Cholesterol" in test_names


def test_patient_data_isolation(client, db_session):
    # Create second user and patient
    user_b = User(
        id="usr_patient_b_002",
        name="Patient B",
        email="patient.b@example.com",
        hashed_password="hashed_password_b",
        role="patient"
    )
    db_session.add(user_b)
    db_session.flush()

    patient_b = Patient(
        id="pat_patient_b_002",
        user_id=user_b.id,
        gender="female"
    )
    db_session.add(patient_b)

    # Add 1 disease to Patient B
    disease_b = Disease(
        id="dis_b_001",
        patient_id=patient_b.id,
        name="Asthma",
        status="active",
        diagnosed_date="2025-01-01"
    )
    db_session.add(disease_b)
    db_session.commit()

    # Create token for Patient B
    token_b = create_access_token(user_b.id)

    # Call /patients/me/diagnoses with Patient B's Bearer token
    headers = {"Authorization": f"Bearer {token_b}"}
    response = client.get("/api/v1/patients/me/diagnoses", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Asthma"
    assert data[0]["id"] == "dis_b_001"
