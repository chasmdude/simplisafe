# tests/test_auth.py
from fastapi.testclient import TestClient

from tests.conftest import get_test_user, TEST_USER_PASSWORD


def register_user(client, user_email, user_name, user_password):
    response = client.post(
        "/auth/register",
        json={
            "username": user_name,
            "email": user_email,
            "password": user_password
        }
    )
    return response


def login_user(client, password, username):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password}
    )
    return response


def test_register_success(client: TestClient, db):
    """Test successful user registration."""
    new_user_name = "newuser"
    new_user_email = "newuser@example.com"
    new_user_password = "Strongpassword1!"

    response = register_user(client, new_user_email, new_user_name, new_user_password)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == new_user_name
    assert "id" in response_data


def test_register_existing_username_or_email(client: TestClient, get_test_user):
    """Test registering with existing username or email."""
    response = register_user(client, "uniqueemail@example.com", get_test_user.username, "Strongpassword1!")
    assert response.status_code == 400
    assert response.json()["detail"] == "Username or email already exists"

    # Existing email
    response = register_user(client, get_test_user.email, "uniqueusername", "Strongpassword1!")
    assert response.status_code == 400
    assert response.json()["detail"] == "Username or email already exists"


def test_register_missing_fields(client: TestClient):
    """Test registration with missing fields."""
    # Missing email since email is optional, user registration should still succeed
    response = client.post(
        "/auth/register",
        json={
            "username": "missingemail",
            "password": "Strongpassword1!",
            # missing email
        }
    )
    assert response.status_code == 200

    # Missing username
    response = client.post(
        "/auth/register",
        json={
            "email": "missingusername@example.com",
            "password": "Strongpassword1!"
        }
    )
    assert response.status_code == 422

    # Missing password
    response = client.post(
        "/auth/register",
        json={
            "username": "missingpassword",
            "email": "missingpassword@example.com"
        }
    )
    assert response.status_code == 422


def test_register_weak_password(client: TestClient):
    """Test registration with a weak password."""
    response = register_user(client, "weakpassword@example.com", "weakpassworduser", "weak")
    assert response.status_code == 422
    response_json = response.json()["detail"]
    assert any("Password must be at least" in item["msg"] for item in response_json)


def test_register_invalid_email(client: TestClient):
    """Test registration with invalid email format."""
    response = register_user(client, "not-an-email", "invalidemailuser", "Strongpassword1!")
    assert response.status_code == 422
    assert any("value is not a valid email address" in item["msg"] for item in response.json()["detail"])


def test_login_success(client: TestClient, get_test_user):
    """Test successful user login."""
    response = login_user(client, TEST_USER_PASSWORD, get_test_user.username)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Login successful"
    assert "user_id" in response_data


def test_login_invalid_credentials(client: TestClient, get_test_user):
    """Test login with invalid credentials."""
    # Invalid password
    response = login_user(client, "wrongpassword", get_test_user.username)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password"

    # Invalid username
    response = login_user(client, "anypassword", "nonexistentuser")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_login_empty_fields(client: TestClient):
    """Test login with empty fields."""
    response = login_user(client, "", "")
    assert response.status_code == 422


def test_logout(client: TestClient, get_test_user):
    """Test user logout."""
    # Login first
    login_response = login_user(client, TEST_USER_PASSWORD, get_test_user.username)
    assert login_response.status_code == 200

    # Logout
    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Successfully logged out"}

    # Logout without session
    response = client.post("/auth/logout")
    assert response.status_code == 400
    assert response.json()["detail"] == "No active session to log out from"
