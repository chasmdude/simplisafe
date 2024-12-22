# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.base import Base
from app.main import app
from app.core.deps import get_db
from app.models.organization_member import OrganizationMember
from app.models.user import User as UserModel
from app.models.organization import Organization as OrganizationModel
from app.models.cluster import Cluster as ClusterModel
from app.core.security import get_password_hash

# Database setup for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_test_user_model(db, username: str, email: str, password: str) -> UserModel:
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


def create_organization_with_user_as_admin(db: Session, name: str, user_id: int) -> OrganizationModel:
    """
    Helper function to create an organization and add the user as an admin.
    """
    organization = create_test_org(db, name)

    add_user_to_org(db, organization.id, user_id, role="admin")

    return organization


def add_user_to_org(db: Session, organization_id: int, user_id: int, role: str = "member"):
    """
    Helper function to add a user to an organization with a specific role.
    """
    organization_member = OrganizationMember(user_id=user_id, organization_id=organization_id, role=role)
    db.add(organization_member)
    db.commit()


def create_test_org(db, org_name="test-organization"):
    organization = OrganizationModel(name=org_name, invite_code=OrganizationModel.generate_invite_code())
    db.add(organization)
    db.commit()
    db.refresh(organization)

    return organization


def create_cluster(db, organization_id: int, name: str, cpu: float, ram: float, gpu: float) -> ClusterModel:
    """
    Helper function to create a cluster in the database.
    """
    cluster = ClusterModel(
        name=name,
        cpu_limit=cpu,
        ram_limit=ram,
        gpu_limit=gpu,
        cpu_available=cpu,
        ram_available=ram,
        gpu_available=gpu,
        organization_id=organization_id
    )
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    return cluster


class CustomTestClient(TestClient):
    def __init__(self, app_for_client, base_path: str, **kwargs):
        super().__init__(app_for_client, **kwargs)
        self.base_path = base_path

    def request(self, method: str, url: str, **kwargs):
        url = f"{self.base_path}{url}"
        return super().request(method, url, **kwargs)


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
