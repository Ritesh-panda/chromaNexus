def test_global_search_diabetes(client):
    response = client.get("/api/v1/search?q=diabetes")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "diabetes"
    assert data["totalMatches"] > 0
    assert len(data["diseases"]) > 0


def test_global_search_cholesterol(client):
    response = client.get("/api/v1/search?q=cholesterol")
    assert response.status_code == 200
    data = response.json()
    assert data["totalMatches"] > 0
