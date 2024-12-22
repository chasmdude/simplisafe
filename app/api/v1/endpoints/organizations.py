# app/api/v1/endpoints/organizations.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core import deps
from app.schemas.organization import Organization, OrganizationCreate
from app.models.user import User
from app.models.organization import Organization as OrganizationModel
from app.models.organization_member import OrganizationMember

router = APIRouter()

def check_if_user_is_already_a_member(current_user, db):
    existing_member = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
    if existing_member:
        existing_org = db.query(OrganizationModel).filter(
            OrganizationModel.id == existing_member.organization_id).first()
        admin_member = db.query(OrganizationMember).filter(OrganizationMember.organization_id == existing_org.id,
                                                           OrganizationMember.role == "admin").first()
        admin_user = db.query(User).filter(User.id == admin_member.user_id).first()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are already part of an organization: {existing_org.name}, Admin: {admin_user.username}"
        )

@router.post("/", response_model=Organization, responses={
    201: {"description": "Organization created successfully", "content": {"application/json": {"example": {"id": 1, "name": "MyOrganization", "invite_code": "ABC123"}}}},
    400: {"description": "User is already part of an organization", "content": {"application/json": {"example": {"detail": "You are already part of an organization: MyOrganization, Admin: adminuser"}}}},
})
def create_organization(
        *,
        db: Session = Depends(deps.get_db),
        organization_in: OrganizationCreate,
        current_user: User = Depends(deps.get_current_user)
):
    # Check if the user is already part of an organization
    check_if_user_is_already_a_member(current_user, db)

    # Generate invite code
    invite_code = OrganizationModel.generate_invite_code()

    # Create the organization
    organization = OrganizationModel(name=organization_in.name, invite_code=invite_code)
    db.add(organization)
    db.commit()
    db.refresh(organization)

    # Add the current user as the first member/admin
    organization_member = OrganizationMember(user_id=current_user.id, organization_id=organization.id, role="admin")
    db.add(organization_member)
    db.commit()

    # # Update the current_user's organization
    # current_user.organization = organization
    # current_user.organization_id = organization.id
    # db.commit()
    # db.refresh(current_user)

    return organization


@router.post("/{invite_code}/join", responses={
    200: {"description": "Successfully joined the organization", "content": {"application/json": {"example": {"message": "Successfully joined the organization"}}}},
    400: {"description": "User is already part of an organization", "content": {"application/json": {"example": {"detail": "You are already part of an organization: MyOrganization, Admin: adminuser"}}}},
    404: {"description": "Organization not found", "content": {"application/json": {"example": {"detail": "Organization not found"}}}},
})
def join_organization(
        *,
        db: Session = Depends(deps.get_db),
        invite_code: str,
        current_user: User = Depends(deps.get_current_user)
):
    """
    Implement logic for joining an organization using an invite code.
    """
    # Check if the user is already part of any organization
    check_if_user_is_already_a_member(current_user, db)

    # Fetch the organization associated with the invite code
    organization = db.query(OrganizationModel).filter(OrganizationModel.invite_code == invite_code).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Add the user to the organization
    organization_member = OrganizationMember(user_id=current_user.id, organization_id=organization.id, role="member")
    db.add(organization_member)
    db.commit()

    # Update current_user's organization
    # current_user.organization = organization
    # current_user.organization_id = organization.id
    # db.commit()
    # db.refresh(current_user)

    return {"message": "Successfully joined the organization"}

