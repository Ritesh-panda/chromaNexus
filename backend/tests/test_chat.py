def test_get_conversations(client):
    response = client.get("/api/v1/chat/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == "th_1"


def test_send_message_with_cholesterol_query(client):
    response = client.post(
        "/api/v1/chat/conversations/th_1/messages",
        json={"text": "When was my highest cholesterol reading?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sender"] == "ai"
    assert "cholesterol" in data["text"].lower()
    assert len(data["citations"]) > 0

