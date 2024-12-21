# test_organizations.py
import pytest
from sqlalchemy.orm import Session
from app.models.organization import Organization as OrganizationModel
from app.models.organization_member import OrganizationMember
from app.models.user import User as UserModel
from app.core.security import get_password_hash

@pytest.fixture
def test_user(db: Session):
    user = db.query(UserModel).filter(UserModel.username == "testuser").first()
    if not user:
        user = UserModel(username="testuser", email="testuser@example.com", hashed_password=get_password_hash("testpassword"))
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def test_create_organization(client, test_user, db: Session):
    response = client.post("/api/v1/organizations/", json={"name": "Test Organization"}, headers={"Authorization": f"Bearer {test_user.id}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Organization"

def test_join_organization(client, test_user, db: Session):
    organization = OrganizationModel(name="Test Organization", invite_code="invite123")
    db.add(organization)
    db.commit()
    db.refresh(organization)
    response = client.post(f"/api/v1/organizations/{organization.invite_code}/join", headers={"Authorization": f"Bearer {test_user.id}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully joined the organization"