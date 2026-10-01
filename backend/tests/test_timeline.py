def test_get_timeline_events(client):
    response = client.get("/api/v1/timeline")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8
    years = [e["year"] for e in data]
    assert 2026 in years
    assert 2019 in years


def test_timeline_filter_by_year(client):
    response = client.get("/api/v1/timeline?year=2026")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(e["year"] == 2026 for e in data)


def test_timeline_event_by_id(client):
    response = client.get("/api/v1/timeline/ev_001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ev_001"
    assert "HbA1c" in data["title"]
