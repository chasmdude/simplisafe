# app/api/v1/endpoints/organizations.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core import deps
from app.schemas.organization import Organization, OrganizationCreate
from app.models.user import User
from app.models.organization import Organization as OrganizationModel
from app.models.organization_member import OrganizationMember

router = APIRouter()

@router.post("/", response_model=Organization)
def create_organization(
        *,
        db: Session = Depends(deps.get_db),
        organization_in: OrganizationCreate,
        current_user: User = Depends(deps.get_current_user)
):
    # Check if the user is already part of an organization
    existing_member = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already part of an organization"
        )

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

    # Update the current_user's organization
    current_user.organization = organization
    current_user.organization_id = organization.id
    db.commit()
    db.refresh(current_user)

    return organization



@router.post("/{invite_code}/join")
def join_organization(
        *,
        db: Session = Depends(deps.get_db),
        invite_code: str,
        current_user: User = Depends(deps.get_current_user)
):
    """
    Implement logic for joining an organization using an invite code.
    """
    # Fetch the organization associated with the invite code
    organization = db.query(OrganizationModel).filter(OrganizationModel.invite_code == invite_code).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if the user is already part of the organization
    existing_member = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id,
                                                          OrganizationMember.organization_id == organization.id).first()
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization"
        )

    # Add the user to the organization
    organization_member = OrganizationMember(user_id=current_user.id, organization_id=organization.id, role="member")
    db.add(organization_member)
    db.commit()

    # Update current_user's organization
    current_user.organization = organization
    current_user.organization_id = organization.id
    db.commit()
    db.refresh(current_user)

    return {"message": "Successfully joined the organization"}

