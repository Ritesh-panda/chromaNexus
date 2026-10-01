def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "alex.vance@example.com", "password": "Password123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alex.vance@example.com"


def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "alex.vance@example.com", "password": "WrongPassword999!"}
    )
    assert response.status_code == 401


def test_signup_new_user(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Dr. Angela Ramos",
            "email": "angela.ramos@example.com",
            "password": "SecurePassword123!",
            "role": "doctor"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["name"] == "Dr. Angela Ramos"
    assert data["user"]["role"] == "doctor"


def test_get_me(client):
    # Log in
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "alex.vance@example.com", "password": "Password123!"}
    )
    token = login_res.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alex Vance"
