# tests/conftest.py
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.deps import get_db
from app.core.security import get_password_hash
from app.db.base import Base
from app.main import app
from app.models.cluster import Cluster as ClusterModel
from app.models.organization import Organization as OrganizationModel
from app.models.organization_member import OrganizationMember
from app.models.user import User as UserModel

# Database setup for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test User Data
TEST_USER_NAME = "testuser"
TEST_USER_PASSWORD = "TestPassword1!"
TEST_USER_EMAIL = "testuser@email.com"

# Test Organization Data
TEST_ORG_NAME = "Test Organization"

# Test Cluster Data
TEST_CLUSTER_NAME = "Test Cluster"
TEST_CLUSTER_CPU = 4.0
TEST_CLUSTER_RAM = 16.0
TEST_CLUSTER_GPU = 2.0


@pytest.fixture
def get_test_user(db: Session) -> UserModel:
    """
    Helper function to create a test user in the database for each test.
    """
    return create_user(db, TEST_USER_EMAIL, TEST_USER_PASSWORD, TEST_USER_NAME)


@pytest.fixture
def get_logged_in_test_user_cookies(db: Session, client: TestClient, get_test_user) -> Cookies:
    """
    Fixture to return cookies after logging in test user for each test.
    """
    return login_user(client, get_test_user.username, TEST_USER_PASSWORD)


@pytest.fixture
def get_logged_in_test_org_admin_cookies(db: Session, client: TestClient, get_test_org_admin) -> Cookies:
    """
    Fixture to return cookies after logging in test user for each test.
    """
    return login_user(client, get_test_org_admin.username, TEST_USER_PASSWORD)


@pytest.fixture
def get_test_org_admin(db: Session, get_test_user, get_test_org) -> UserModel:
    """
    Helper function to create a user in the database.
    """
    add_user_to_org(db, get_test_org, get_test_user, role="admin")
    return get_test_user


@pytest.fixture
def get_test_org_with_admin(db: Session, get_test_user, get_test_org) -> OrganizationModel:
    """
    Helper function to create a Test organization and add the user as an admin.
    """
    add_user_to_org(db, get_test_org, get_test_user, role="admin")
    return get_test_org


@pytest.fixture
def get_test_org(db: Session) -> OrganizationModel:
    org = create_org(db, TEST_ORG_NAME)
    return org


@pytest.fixture
def get_test_cluster(db: Session, get_test_org_with_admin) -> ClusterModel:
    org_id = get_test_org_with_admin.id
    print(f"Creating cluster for organization ID: {org_id}")
    cluster = create_cluster(db, org_id, TEST_CLUSTER_NAME, TEST_CLUSTER_CPU, TEST_CLUSTER_RAM, TEST_CLUSTER_GPU)
    print(f"Created cluster: {cluster}")
    return cluster


def login_user(client: TestClient, username: str, password: str):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.cookies


def create_user(db: Session, email, plain_password, username):
    hashed_password = get_password_hash(plain_password)

    user = UserModel(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    db.commit()

    return user


def create_org(db, org_name):
    organization = OrganizationModel(name=org_name, invite_code=OrganizationModel.generate_invite_code())
    db.add(organization)
    db.commit()

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
    db.refresh(cluster)  # Ensure relationships are loaded

    return cluster


def add_user_to_org(db: Session, organization: OrganizationModel, user: UserModel, role: str = "member"):
    """
    Helper function to add a user to an organization with a specific role. default role is "member".
    """
    organization_member = OrganizationMember(user_id=user.id, organization_id=organization.id, role=role)
    db.add(organization_member)
    db.commit()

    db.refresh(organization)
    db.refresh(user)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Create all tables at the start of the test session and drop them afterward.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def db() -> Generator:
    """
    Fixture to setup and tear down a transaction for each test.
    Automatically applied to all tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session  # Provide the session to the test
    finally:
        session.close()
        transaction.rollback()  # Rollback the transaction after each test
        connection.close()


# Session-scoped fixture for creating the test client with overridden dependency
@pytest.fixture(scope="session")
def client_config() -> Generator:
    """
    Session-scoped fixture to configure the client (base path, etc.)
    """
    # Configure base path once for the whole session
    with TestClient(app) as c:
        c.base_url = "http://testserver/api/v1"
        yield c


# Function-scoped fixture for client that overrides the db session
@pytest.fixture
def client(client_config, db) -> Generator:
    """
    Function-scoped fixture to override the database session for each test.
    """

    # Override the `get_db` dependency to use the session from the db fixture
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Use the configured client from the session-scoped fixture
    yield client_config


def test_base_path(client: TestClient):
    # Send a request to an endpoint, e.g., "/users"
    response = client.get("/users")  # This should be automatically prefixed with "/api/v1"

    # Validate that the request URL starts with the base path
    expected_url = "/api/v1/users"  # Adjust this based on the endpoint you're testing
    assert response.request.url.path == expected_url