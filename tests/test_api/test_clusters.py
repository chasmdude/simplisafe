from fastapi.testclient import TestClient
from httpx import Response, Cookies


def create_cluster(client: TestClient, cookies: Cookies, cluster_data: dict) -> Response:
    """
    Helper function to create a cluster via the API.
    """
    response = client.post("/clusters/", json=cluster_data, cookies=cookies)
    return response


def list_clusters(client: TestClient, cookies: Cookies) -> Response:
    """
    Helper function to list clusters via the API.
    """
    response = client.get("/clusters/", cookies=cookies)
    return response


def test_create_cluster_success(client: TestClient, get_logged_in_test_org_admin_cookies: Cookies):
    cookies = get_logged_in_test_org_admin_cookies

    cluster_data = {
        "name": "test-cluster",
        "cpu_limit": 4.0,
        "ram_limit": 16.0,
        "gpu_limit": 2.0
    }
    response = create_cluster(client, cookies, cluster_data)

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["name"] == cluster_data["name"]
    assert response_data["cpu_limit"] == cluster_data["cpu_limit"]
    assert response_data["ram_limit"] == cluster_data["ram_limit"]
    assert response_data["gpu_limit"] == cluster_data["gpu_limit"]


def test_create_cluster_invalid_resource_limits(client: TestClient, get_logged_in_test_org_admin_cookies):
    cookies = get_logged_in_test_org_admin_cookies

    cluster_data = {
        "name": "test-cluster",
        "cpu_limit": -1.0,  # Invalid CPU limit
        "ram_limit": 0.0,  # Invalid RAM limit
        "gpu_limit": -2.0  # Invalid GPU limit
    }
    response = create_cluster(client, cookies, cluster_data)

    assert response.status_code == 422
    response_data = response.json()
    assert all('Input should be greater than or equal to 0' == item["msg"] for item in response_data["detail"])


def test_create_cluster_user_not_in_org(client: TestClient, get_logged_in_test_user_cookies):
    # Create a user who is not part of any organization
    cookies = get_logged_in_test_user_cookies

    cluster_data = {
        "name": "test-cluster",
        "cpu_limit": 4.0,
        "ram_limit": 16.0,
        "gpu_limit": 2.0
    }
    response = create_cluster(client, cookies, cluster_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "User is not part of any organization"}


def test_list_clusters_success(client: TestClient, get_logged_in_test_org_admin_cookies):
    cookies = get_logged_in_test_org_admin_cookies

    cluster_data = {
        "name": "test-cluster",
        "cpu_limit": 4.0,
        "ram_limit": 16.0,
        "gpu_limit": 2.0
    }
    create_cluster(client, cookies, cluster_data)

    response = list_clusters(client, cookies)

    assert response.status_code == 200
    response_data = response.json()

    assert len(response_data) == 1
    assert response_data[0]["name"] == cluster_data["name"]
    assert response_data[0]["cpu_limit"] == cluster_data["cpu_limit"]
    assert response_data[0]["ram_limit"] == cluster_data["ram_limit"]
    assert response_data[0]["gpu_limit"] == cluster_data["gpu_limit"]


def test_list_clusters_empty(client: TestClient, get_logged_in_test_org_admin_cookies: Cookies):
    cookies = get_logged_in_test_org_admin_cookies
    response = list_clusters(client, cookies)

    assert response.status_code == 200
    assert response.json() == []


def test_list_clusters_user_not_in_org(client: TestClient, get_logged_in_test_user_cookies: Cookies):
    # Create a user who is not part of any organization
    cookies = get_logged_in_test_user_cookies

    response = list_clusters(client, cookies)

    assert response.status_code == 400
    assert response.json() == {"detail": "User is not part of any organization"}

# def test_list_clusters_success(self, client: TestClient, db: Session):
#     cookies = login_user(client, self.create_test_user.username, "Testpassword1!")
#     cluster_data = {
#         "name": "test-cluster",
#         "cpu_limit": 4.0,
#         "ram_limit": 16.0,
#         "gpu_limit": 2.0
#     }
#     # Create a cluster
#     client.post("/clusters/", json=cluster_data, cookies=cookies)
#
#     # List clusters
#     response = client.get("/clusters/", cookies=cookies)
#
#     assert response.status_code == 200
#     response_data = response.json()
#
#     assert len(response_data) == 1
#     assert response_data[0]["name"] == cluster_data["name"]
#     assert response_data[0]["cpu_limit"] == cluster_data["cpu_limit"]
#     assert response_data[0]["ram_limit"] == cluster_data["ram_limit"]
#     assert response_data[0]["gpu_limit"] == cluster_data["gpu_limit"]

# def test_create_cluster_success(self, client: TestClient, db: Session):
#     cookies = login_user(client, self.create_test_user.username, "Testpassword1!")
#     cluster_data = {
#         "name": "test-cluster",
#         "cpu_limit": 4.0,
#         "ram_limit": 16.0,
#         "gpu_limit": 2.0
#     }
#     response = client.post("/clusters/", json=cluster_data, cookies=cookies)
#
#     assert response.status_code == 200
#     response_data = response.json()
#
#     assert response_data["name"] == cluster_data["name"]
#     assert response_data["cpu_limit"] == cluster_data["cpu_limit"]
#     assert response_data["ram_limit"] == cluster_data["ram_limit"]
#     assert response_data["gpu_limit"] == cluster_data["gpu_limit"]
#
# def create_user(db, username, email, password):
#     hashed_password = get_password_hash(password)
#     user = UserModel(
#         username=username,
#         email=email,
#         hashed_password=hashed_password,
#         is_active=True,
#     )
#     db.add(user)
#     db.commit()
#     db.refresh(user)
#     return user
#
#
# def add_user_to_org(db, organization_id, user_id, role="member"):
#     organization_member = OrganizationMember(user_id=user_id, organization_id=organization_id, role=role)
#     db.add(organization_member)
#     db.commit()
#
#
# def create_organization(db, name, user_id):
#     organization = OrganizationModel(name=name, invite_code=OrganizationModel.generate_invite_code())
#     db.add(organization)
#     db.commit()
#     db.refresh(organization)
#     add_user_to_org(db, organization.id, user_id, role="admin")
#     return organization

# class TestCluster(BaseTest):
#     @pytest.fixture(autouse=True)
#     def setup_and_teardown(self, db: Session):
#         # Setup: Ensure the database is clean before each test
#         db.query(ClusterModel).delete()
#         db.query(OrganizationModel).delete()
#         db.query(OrganizationMember).delete()
#         db.query(UserModel).delete()
#         db.commit()
#
#         # Create test user and organization
#         self.create_test_user = test_user(db, "testuser", "testuser@example.com", "Testpassword1!")
#         self.create_test_org = create_organization_with_user_as_admin(db, "test-organization", self.create_test_user.id)
#
#         yield
#
#         # Teardown: Clean up the database after each test
#         db.query(ClusterModel).delete()
#         db.query(OrganizationModel).delete()
#         db.query(OrganizationMember).delete()
#         db.query(UserModel).delete()
#         db.commit()