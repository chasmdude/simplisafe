# tests/test_deployment.py
from fastapi.testclient import TestClient
from httpx import Cookies

from app.models.cluster import Cluster as ClusterModel
from app.models.deployment import DeploymentStatus


def test_create_deployment_success(client: TestClient, get_test_cluster: ClusterModel, get_logged_in_test_user_cookies: Cookies):
    """Test successful deployment creation."""
    cookies = get_logged_in_test_user_cookies

    deployment_data = {
        "name": "test-deployment",
        "docker_image": "my_image",
        "cpu_required": 2,
        "ram_required": 4,
        "gpu_required": 1,
        "priority": 1,
        "cluster_id": get_test_cluster.id
    }

    response = client.post("/deployments/", json=deployment_data, cookies=cookies)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "test-deployment"
    assert response_data["status"] == DeploymentStatus.RUNNING.value


def test_create_deployment_insufficient_resources(client: TestClient, get_test_cluster: ClusterModel,
                                                  get_logged_in_test_user_cookies: Cookies):
    """Test deployment creation with insufficient resources."""
    cookies = get_logged_in_test_user_cookies

    deployment_data = {
        "name": "test-deployment",
        "docker_image": "my_image",
        "cpu_required": 10,  # Exceeds available CPU
        "ram_required": 20,  # Exceeds available RAM
        "gpu_required": 5,   # Exceeds available GPU
        "priority": 1,
        "cluster_id": get_test_cluster.id
    }

    response = client.post("/deployments/", json=deployment_data, cookies=cookies)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "test-deployment"
    assert response_data["status"] == DeploymentStatus.PENDING.value

def test_list_deployments_success(client: TestClient, get_test_cluster: ClusterModel, get_logged_in_test_user_cookies: Cookies):
    """Test listing deployments."""
    cookies = get_logged_in_test_user_cookies

    deployment_data = {
        "name": "test-deployment",
        "docker_image": "my_image",
        "cpu_required": 2,
        "ram_required": 4,
        "gpu_required": 1,
        "priority": 1,
        "cluster_id": get_test_cluster.id
    }

    # c
    client.post("/deployments/", json=deployment_data, cookies=cookies)

    response = client.get("/deployments/", cookies=cookies)

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["name"] == "test-deployment"

def test_list_deployments_user_not_in_org(client: TestClient, get_logged_in_test_user_cookies: Cookies):
    """Test listing deployments for a user not in any organization."""
    cookies = get_logged_in_test_user_cookies

    response = client.get("/deployments/", cookies=cookies)

    assert response.status_code == 400
    assert response.json() == {"detail": "User is not part of any organization"}


#
# # tests/test_deployment.py
# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy.orm import Session
# from app.models.cluster import Cluster as ClusterModel
# from app.models.organization_member import OrganizationMember
# from app.models.user import User as UserModel
# from app.models.deployment import Deployment as DeploymentModel, DeploymentStatus
# from app.models.organization import Organization as OrganizationModel
# from tests.conftest import BaseTest, get_test_user, create_cluster, create_organization_with_user_as_admin, login_user
#
# class TestDeployment(BaseTest):
#     @pytest.fixture(autouse=True)
#     def setup_and_teardown(self, db: Session):
#         # Setup: Ensure the database is clean before each test
#         db.query(DeploymentModel).delete()
#         db.query(ClusterModel).delete()
#         db.query(OrganizationModel).delete()
#         db.query(OrganizationMember).delete()
#         db.query(UserModel).delete()
#         db.commit()
#
#         self.create_test_user = get_test_user(db, "testuser", "testuser@example.com", "Testpassword1!")
#         self.test_organization = create_organization_with_user_as_admin(db, "test-organization", self.create_test_user.id)
#         self.create_test_cluster = create_cluster(db, self.test_organization.id, "test-cluster", 4.0, 16.0, 2.0)
#
#         yield
#         # Teardown: Clean up the database after each test
#         db.query(DeploymentModel).delete()
#         db.query(ClusterModel).delete()
#         db.query(OrganizationModel).delete()
#         db.query(OrganizationMember).delete()
#         db.query(UserModel).delete()
#         db.commit()
#
#     def test_create_deployment_success(self, client: TestClient, db: Session):
#         """Test successful deployment creation."""
#         cookies = login_user(client, self.create_test_user.username, "Testpassword1!")
#         deployment_data = {
#             "name": "test-deployment",
#             "docker_image": "my_image",
#             "cpu_required": 2,
#             "ram_required": 4,
#             "gpu_required": 1,
#             "priority": 1,
#             "cluster_id": self.create_test_cluster.id
#         }
#         response = client.post("/deployments/", json=deployment_data, cookies=cookies)
#         assert response.status_code == 200
#         response_data = response.json()
#         assert response_data["name"] == "test-deployment"
#         assert response_data["status"] == DeploymentStatus.RUNNING.value
#
#     def test_create_deployment_insufficient_resources(self, client: TestClient, db: Session):
#         """Test deployment creation with insufficient resources."""
#         cookies = login_user(client, self.create_test_user.username, "Testpassword1!")
#         deployment_data = {
#             "name": "test-deployment",
#             "docker_image": "my_image",
#             "cpu_required": 10,  # Exceeds available CPU
#             "ram_required": 20,  # Exceeds available RAM
#             "gpu_required": 5,   # Exceeds available GPU
#             "priority": 1,
#             "cluster_id": self.create_test_cluster.id
#         }
#         response = client.post("/deployments/", json=deployment_data, cookies=cookies)
#         assert response.status_code == 200
#         response_data = response.json()
#         assert response_data["name"] == "test-deployment"
#         assert response_data["status"] == DeploymentStatus.PENDING.value
#
#     def test_list_deployments_success(self, client: TestClient, db: Session):
#         """Test listing deployments."""
#         cookies = login_user(client, self.create_test_user.username, "Testpassword1!")
#         deployment_data = {
#             "name": "test-deployment",
#             "docker_image": "my_image",
#             "cpu_required": 2,
#             "ram_required": 4,
#             "gpu_required": 1,
#             "priority": 1,
#             "cluster_id": self.create_test_cluster.id
#         }
#         client.post("/deployments/", json=deployment_data, cookies=cookies)
#         response = client.get("/deployments/", cookies=cookies)
#         assert response.status_code == 200
#         response_data = response.json()
#         assert len(response_data) == 1
#         assert response_data[0]["name"] == "test-deployment"
#
#     def test_list_deployments_user_not_in_org(self, client: TestClient, db: Session):
#         """Test listing deployments for a user not in any organization."""
#         user_not_in_org = get_test_user(db, "usernotinorg", "usernotinorg@example.com", "Testpassword1!")
#         cookies = login_user(client, user_not_in_org.username, "Testpassword1!")
#         response = client.get("/deployments/", cookies=cookies)
#         assert response.status_code == 400
#         assert response.json() == {"detail": "User is not part of any organization"}