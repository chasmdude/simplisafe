import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.organization import Organization as OrganizationModel
from app.models.organization_member import OrganizationMember
from app.models.user import User as UserModel
from tests.conftest import BaseTest, create_user, login_user


def create_test_org(db):
    organization = OrganizationModel(name="test-organization", invite_code=OrganizationModel.generate_invite_code())
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


def add_user_to_org(db, organization_id, user_id, role="member"):
    organization_member = OrganizationMember(user_id=user_id, organization_id=organization_id, role=role)
    db.add(organization_member)
    db.commit()


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


def validate_created_org(create_test_user, db, response_data, org_name):
    assert response_data["name"] == org_name
    assert "id" in response_data
    assert "invite_code" in response_data

    created_org = db.query(OrganizationModel).filter(OrganizationModel.id == response_data["id"]).first()
    assert created_org

    members_of_created_org_matching_current_user = [member for member in created_org.members if
                                                    member.user_id == create_test_user.id]
    assert members_of_created_org_matching_current_user
    assert len(members_of_created_org_matching_current_user) == 1


def create_user_for_member(db, user_password="TestPassword2!"):
    hashed_password = get_password_hash(user_password)
    user = UserModel(
        username="seconduser",
        email="seconduser@example.com",
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestOrganization(BaseTest):
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, db: Session):
        # Setup: Ensure the database is clean before each test
        db.query(OrganizationMember).delete()
        db.query(OrganizationModel).delete()
        db.query(UserModel).delete()
        db.commit()

        self.create_test_user = create_user(db, "testuser", "testuser@example.com", "Testpassword1!")
        yield
        # Teardown: Clean up the database after each test
        db.query(OrganizationMember).delete()
        db.query(OrganizationModel).delete()
        db.query(UserModel).delete()
        db.commit()

    def test_create_organization_success(self, client: TestClient, db: Session):
        cookies = login_user(client, self.create_test_user.username, "Testpassword1!")
        organization_name = "test-organization"
        response = create_organization(client, cookies, organization_name)

        assert response.status_code == 200
        response_data = response.json()

        validate_created_org(self.create_test_user, db, response_data, organization_name)

        org_id = response_data["id"]

        assert self.create_test_user.organization.id == org_id

        validate_role_of_user_in_org(self.create_test_user, db, org_id, "admin")

    def test_create_organization_already_a_member(self, client: TestClient, db: Session):
        cookies = login_user(client, self.create_test_user.username, "Testpassword1!")
        create_organization(client, cookies, "first organization")

        response = create_organization(client, cookies, "second organization")

        # Assert that the response status code is 400 (Bad Request)
        assert response.status_code == 400

        # Assert that the response contains the expected error message
        assert response.json()[
                   "detail"] == "You are already part of an organization: first organization, Admin: testuser"

    def test_join_organization_success(self, client: TestClient, db: Session):
        organization = create_test_org(db)
        cookies = login_user(client, self.create_test_user.username, "Testpassword1!")
        response = client.post(
            f"/organizations/{organization.invite_code}/join",
            cookies=cookies
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully joined the organization"

        assert self.create_test_user.organization.id == organization.id

        validate_role_of_user_in_org(self.create_test_user, db, organization.id, "member")

    def test_join_organization_invalid_code(self, client: TestClient, db: Session):
        cookies = login_user(client, self.create_test_user.username, "Testpassword1!")
        response = client.post(
            "/organizations/invalidcode/join",
            cookies=cookies
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Organization not found"

    def test_join_organization_already_member(self, client: TestClient, db: Session):
        organization = create_test_org(db)

        add_user_to_org(db, organization.id, self.create_test_user.id, "admin")

        member_user_password = "TestPassword2!"
        member_user = create_user_for_member(db, member_user_password)
        cookies = login_user(client, member_user.username, member_user_password)

        add_user_to_org(db, organization.id, member_user.id, "member")

        response = client.post(
            f"/organizations/{organization.invite_code}/join",
            cookies=cookies
        )
        assert response.status_code == 400
        assert response.json()["detail"] == ("You are already part of an organization: test-organization, Admin: "
                                             "testuser")
        # # Clean up the member user
        # db.query(UserModel).filter(UserModel.id == member_user.id).delete()

    def test_join_second_organization(self, client: TestClient, db: Session):
        # Create the first organization and add the user as a member
        first_organization = create_test_org(db)
        add_user_to_org(db, first_organization.id, self.create_test_user.id, "admin")

        # Create the second organization
        second_organization = OrganizationModel(name="second-organization",
                                                invite_code=OrganizationModel.generate_invite_code())
        db.add(second_organization)
        db.commit()
        db.refresh(second_organization)

        member_user_password = "TestPassword2!"
        member_user = create_user_for_member(db, member_user_password)
        add_user_to_org(db, first_organization.id, member_user.id)

        cookies = login_user(client, member_user.username, member_user_password)

        # Attempt to join the second organization
        response = client.post(
            f"/organizations/{second_organization.invite_code}/join",
            cookies=cookies
        )

        # Assert that the response status code is 400 (Bad Request)
        assert response.status_code == 400

        # Assert that the response contains the expected error message
        assert "You are already part of an organization: test-organization, Admin: testuser" == response.json()[
            "detail"]

        # Clean up the member user
        # db.query(UserModel).filter(UserModel.id == member_user.id).delete()
