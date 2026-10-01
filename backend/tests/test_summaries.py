def test_get_latest_summary(client):
    response = client.get("/api/v1/summaries/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["patientName"] == "Alex Vance"
    assert len(data["currentDiseases"]) > 0
    assert len(data["activeMedications"]) > 0


def test_generate_summary(client):
    response = client.post("/api/v1/summaries/generate")
    assert response.status_code == 200
    data = response.json()
    assert "summaryOverview" in data
    assert "timelineHighlights" in data
