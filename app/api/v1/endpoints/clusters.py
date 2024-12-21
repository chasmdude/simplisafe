from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core import deps
from app.schemas.cluster import Cluster, ClusterCreate
from app.models.user import User
from app.models.cluster import Cluster as ClusterModel  # Import the Cluster model

router = APIRouter()

@router.post("/", response_model=Cluster)
def create_cluster(
    *,
    db: Session = Depends(deps.get_db),
    cluster_in: ClusterCreate,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new cluster associated with the current user.
    """
    # Check if the user has an active organization
    if not current_user.memberships:
        raise HTTPException(
            status_code=400,
            detail="User is not part of any organization"
        )

    # Create a new Cluster instance with the provided resources and limits
    cluster = ClusterModel(
        name=cluster_in.name,
        cpu_limit=cluster_in.cpu_limit,
        ram_limit=cluster_in.ram_limit,
        gpu_limit=cluster_in.gpu_limit,
        cpu_available=cluster_in.cpu_limit,  # Initially, all resources are available
        ram_available=cluster_in.ram_limit,
        gpu_available=cluster_in.gpu_limit,
        organization_id=current_user.organization_id,  # Assign the current user's organization ID
    )

    db.add(cluster)
    db.commit()
    db.refresh(cluster)  # Refresh the cluster to get the ID and other database-generated fields

    return cluster


@router.get("/", response_model=List[Cluster])
def list_clusters(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all clusters associated with the current user's organization.
    """
    # Check if the user has an active organization
    if not current_user.organization:
        raise HTTPException(
            status_code=400,
            detail="User is not part of any organization"
        )

    # Retrieve clusters for the user's organization
    clusters = db.query(ClusterModel).filter(ClusterModel.organization_id == current_user.organization.id).all()

    if not clusters:
        raise HTTPException(
            status_code=404,
            detail="No clusters found for your organization"
        )

    return clusters
