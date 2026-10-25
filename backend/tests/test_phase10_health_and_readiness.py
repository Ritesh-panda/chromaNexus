import pytest


def test_health_liveness_endpoint(client):
    """
    Verifies /health and /api/v1/health liveness probe endpoints.
    """
    res1 = client.get("/health")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "healthy"
    assert "service" in data1
    assert "version" in data1

    res2 = client.get("/api/v1/health")
    assert res2.status_code == 200
    assert res2.json()["status"] == "healthy"


def test_ready_readiness_endpoint(client, db_session):
    """
    Verifies /ready and /api/v1/ready dependency readiness probes.
    Validates that database, vector store, and storage readiness are reported.
    """
    res1 = client.get("/ready")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "ready"
    assert "components" in data1

    comps = data1["components"]
    assert "database" in comps
    assert comps["database"]["status"] == "connected"
    assert "storage" in comps
    assert comps["storage"]["status"] == "writable"
    assert "vector_store" in comps
    assert "inference_provider" in comps

    res2 = client.get("/api/v1/ready")
    assert res2.status_code == 200
    assert res2.json()["status"] == "ready"
