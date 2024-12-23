import pytest
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlalchemy.orm import Session

from app.models.organization import Organization as OrganizationModel
from app.models.organization_member import OrganizationMember
from app.models.user import User as UserModel
from tests.conftest import create_user, login_user, create_org, TEST_ORG_NAME, \
    TEST_USER_NAME

# Test Member User Data
TEST_MEMBER_USER_NAME = "seconduser"
TEST_MEMBER_USER_EMAIL = "seconduser@example.com"
TEST_MEMBER_USER_PASSWORD = "TestPassword2!"


@pytest.fixture
def create_user_for_member(db: Session) -> UserModel:
    """
    Helper function to create a test user in the database for each test.
    """
    return create_user(db, TEST_MEMBER_USER_EMAIL, TEST_MEMBER_USER_PASSWORD, TEST_MEMBER_USER_NAME)


def create_organization(client: TestClient, cookies, name: str):
    response = client.post(
        "/organizations",
        json={"name": name},
        cookies=cookies
    )
    return response


def validate_role_of_user_in_org(create_test_user, db, org_id, role):
    organization_member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == create_test_user.id,
        OrganizationMember.organization_id == org_id
    ).first()
    assert organization_member is not None
    assert organization_member.role == role


def validate_created_org(user, db, response_data, org_name):
    assert response_data["name"] == org_name
    assert "id" in response_data
    assert "invite_code" in response_data

    created_org = db.query(OrganizationModel).filter(OrganizationModel.id == response_data["id"]).first()
    assert created_org

    members_of_created_org_matching_current_user = [member for member in created_org.members if
                                                    member.user_id == user.id]
    assert members_of_created_org_matching_current_user
    assert len(members_of_created_org_matching_current_user) == 1


def test_create_organization_success(client: TestClient, db: Session, get_test_user: UserModel,
                                     get_logged_in_test_user_cookies: Cookies):
    user = get_test_user
    cookies = get_logged_in_test_user_cookies

    organization_name = "test-organization"
    response = create_organization(client, cookies, organization_name)

    assert response.status_code == 200
    response_data = response.json()

    user = db.merge(user)
    validate_created_org(user, db, response_data, organization_name)

    org_id = response_data["id"]
    assert user.org_member.organization_id == org_id
    validate_role_of_user_in_org(user, db, org_id, "admin")


def test_create_organization_already_a_member(client: TestClient, get_test_org_admin: UserModel,
                                              get_logged_in_test_user_cookies: Cookies):
    cookies = get_logged_in_test_user_cookies

    response = create_organization(client, cookies, "second organization")

    # Assert that the response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Assert that the response contains the expected error message
    assert f'You are already part of an organization: {TEST_ORG_NAME}, Admin: {TEST_USER_NAME}' == response.json()[
        "detail"]


def test_join_organization_success(client: TestClient, db: Session, create_user_for_member: UserModel,
                                   get_test_org_with_admin: OrganizationModel):
    organization = get_test_org_with_admin
    member_user = create_user_for_member

    cookies = login_user(client, member_user.username, TEST_MEMBER_USER_PASSWORD)
    response = client.post(
        f"/organizations/{organization.invite_code}/join",
        cookies=cookies
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully joined the organization"

    #  Re-query the user to ensure it's attached to the session and relationships are loaded
    member_user = db.query(UserModel).get(member_user.id)
    assert member_user.org_member.organization_id == organization.id

    validate_role_of_user_in_org(member_user, db, organization.id, "member")


def test_join_organization_invalid_code(client: TestClient, get_logged_in_test_user_cookies: Cookies):
    cookies = get_logged_in_test_user_cookies

    response = client.post(
        "/organizations/invalidcode/join",
        cookies=cookies
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Organization not found"


def test_join_organization_already_member(client: TestClient, db: Session, get_test_user: UserModel,
                                          get_test_org_with_admin: OrganizationModel,
                                          get_logged_in_test_org_admin_cookies: Cookies):
    organization = get_test_org_with_admin
    cookies = get_logged_in_test_org_admin_cookies

    response = client.post(
        f"/organizations/{organization.invite_code}/join",
        cookies=cookies
    )
    assert response.status_code == 400
    assert response.json()["detail"] == ("You are already part of an organization: Test Organization, Admin: "
                                         "testuser")


def test_join_second_organization(client: TestClient, db: Session, get_test_org_admin: UserModel,
                                  get_logged_in_test_org_admin_cookies: dict):
    second_organization_name = "Second Organization"
    second_organization = create_org(db, second_organization_name)

    cookies = get_logged_in_test_org_admin_cookies

    # Attempt to join the second organization
    response = client.post(
        f"/organizations/{second_organization.invite_code}/join",
        cookies=cookies
    )

    # Assert that the response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Assert that the response contains the expected error message
    assert f"You are already part of an organization: Test Organization, Admin: {get_test_org_admin.username}" == \
           response.json()[
               "detail"]
