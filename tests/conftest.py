# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.main import app
from app.core.deps import get_db
from app.models.user import User as UserModel
from app.core.security import get_password_hash

# Database setup for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class CustomTestClient(TestClient):
    def __init__(self, app, base_path: str, **kwargs):
        super().__init__(app, **kwargs)
        self.base_path = base_path

    def request(self, method: str, url: str, **kwargs):
        url = f"{self.base_path}{url}"
        return super().request(method, url, **kwargs)


def create_user(db, username: str, email: str, password: str) -> UserModel:
    """
    Helper function to create a user in the database.
    """
    hashed_password = get_password_hash(password)
    user = UserModel(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(client: TestClient, username: str, password: str):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.cookies

class BaseTest:
    base_path = "/api/v1"  # Set the base path here

    @pytest.fixture(scope="session")
    def db(self):
        """Create the database tables before tests and drop them after."""
        Base.metadata.create_all(bind=engine)
        yield TestingSessionLocal()
        Base.metadata.drop_all(bind=engine)

    @pytest.fixture(scope="session")
    def client(self):
        """Override the FastAPI dependency to use the test database session."""

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        with CustomTestClient(app, self.base_path) as client:
            yield client