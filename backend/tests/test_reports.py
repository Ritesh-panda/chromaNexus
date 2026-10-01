import io


def test_get_reports_list(client):
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8
    first = data[0]
    assert "title" in first
    assert "category" in first
    assert "extractedEntities" in first


def test_get_report_by_id(client):
    response = client.get("/api/v1/reports/rep_008")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "rep_008"
    assert "Comprehensive" in data["title"]
    assert len(data["extractedEntities"]) > 0


def test_create_report_metadata(client):
    response = client.post(
        "/api/v1/reports",
        json={
            "title": "Renal Function Blood Work",
            "category": "blood_report",
            "hospitalName": "Metro General Hospital",
            "doctorName": "Dr. Sarah Jenkins, MD"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Renal Function Blood Work"
    assert data["category"] == "blood_report"


def test_upload_document(client):
    file_content = b"%PDF-1.4 Mock medical document content for testing"
    file_tuple = ("test_lab_report.pdf", io.BytesIO(file_content), "application/pdf")

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": file_tuple},
        data={
            "category": "blood_report",
            "hospital_name": "Quest Diagnostics",
            "doctor_name": "Dr. Robert Chen, MD"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "Test Lab Report" in data["title"]
    assert data["hospitalName"] == "Quest Diagnostics"
