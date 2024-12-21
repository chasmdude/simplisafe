# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User as UserModel
from tests.conftest import BaseTest


class TestAuth(BaseTest):
    @pytest.fixture(scope="module")
    def create_test_user(self, db: Session):
        """Create a test user in the database."""
        hashed_password = get_password_hash("Testpassword1!")
        user = UserModel(
            username="testuser",
            email="testuser@example.com",
            hashed_password=hashed_password,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def test_register_success(self, client: TestClient, db):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Strongpassword1!"
            }
        )
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["username"] == "newuser"
        assert "id" in response_data

    def test_register_existing_username_or_email(self, client: TestClient, create_test_user: UserModel):
        """Test registering with existing username or email."""
        # Existing username
        response = client.post(
            "/auth/register",
            json={
                "username": create_test_user.username,
                "email": "uniqueemail@example.com",
                "password": "Strongpassword1!"
            }
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Username or email already exists"

        # Existing email
        response = client.post(
            "/auth/register",
            json={
                "username": "uniqueusername",
                "email": create_test_user.email,
                "password": "Strongpassword1!"
            }
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Username or email already exists"

    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing fields."""
        # Missing email since email is optional, user registration should still succeed
        response = client.post(
            "/auth/register",
            json={
                "username": "missingemail",
                "password": "Strongpassword1!"
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

    def test_register_weak_password(self, client: TestClient):
        """Test registration with a weak password."""
        response = client.post(
            "/auth/register",
            json={
                "username": "weakpassworduser",
                "email": "weakpassword@example.com",
                "password": "weak"
            }
        )
        assert response.status_code == 422
        response_json = response.json()["detail"]
        assert any("Password must be at least" in item["msg"] for item in response_json)

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/auth/register",
            json={
                "username": "invalidemailuser",
                "email": "not-an-email",
                "password": "Strongpassword1!"
            }
        )
        assert response.status_code == 422
        assert any("value is not a valid email address" in item["msg"] for item in response.json()["detail"])

    def test_login_success(self, client: TestClient, create_test_user: UserModel):
        """Test successful user login."""
        response = client.post(
            "/auth/login",
            json={"username": create_test_user.username, "password": "Testpassword1!"}
        )
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Login successful"
        assert "user_id" in response_data

    def test_login_invalid_credentials(self, client: TestClient, create_test_user: UserModel):
        """Test login with invalid credentials."""
        # Invalid password
        response = client.post(
            "/auth/login",
            json={"username": create_test_user.username, "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid password"

        # Invalid username
        response = client.post(
            "/auth/login",
            json={"username": "nonexistentuser", "password": "anypassword"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_login_empty_fields(self, client: TestClient):
        """Test login with empty fields."""
        response = client.post(
            "/auth/login",
            json={"username": "", "password": ""}
        )
        assert response.status_code == 422

    def test_logout(self, client: TestClient, create_test_user: UserModel):
        """Test user logout."""
        # Login first
        login_response = client.post(
            "/auth/login",
            json={"username": create_test_user.username, "password": "Testpassword1!"}
        )
        assert login_response.status_code == 200

        # Logout
        logout_response = client.post("/auth/logout")
        assert logout_response.status_code == 200
        assert logout_response.json() == {"message": "Successfully logged out"}

        # Logout without session
        response = client.post("/auth/logout")
        assert response.status_code == 400
        assert response.json()["detail"] == "No active session to log out from"
