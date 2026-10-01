import io
import pytest
from fastapi.testclient import TestClient
from backend.app.ai.ingestion.ingestion_status import ingestion_registry, IngestionStage


def test_get_document_status_not_found(client: TestClient):
    response = client.get("/api/v1/documents/non_existent_doc/status")
    assert response.status_code == 404


def test_upload_document_endpoint(client: TestClient):
    file_content = b"Medical Report: Fasting Blood Glucose 95 mg/dL. Normal range."
    files = {
        "file": ("blood_test.txt", io.BytesIO(file_content), "text/plain")
    }
    data = {
        "category": "blood_report",
        "hospital_name": "API Test Clinic",
        "doctor_name": "Dr. Test",
        "report_date": "2024-06-01"
    }
    
    response = client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 201
    result = response.json()
    assert "id" in result
    assert result["category"] == "blood_report"
    assert result["hospitalName"] == "API Test Clinic"
    
    # Check status endpoint for the uploaded doc
    doc_id = result["id"]
    status_resp = client.get(f"/api/v1/documents/{doc_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["document_id"] == doc_id
    assert "progress_percent" in status_data

