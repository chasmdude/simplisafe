from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import deps
from app.models.cluster import Cluster
from app.models.deployment import Deployment as DeploymentModel, DeploymentStatus, valid_state_transitions
from app.models.user import User
from app.schedulers.scheduler_interface import Scheduler
from app.schemas.deployment import Deployment, DeploymentCreate, DeploymentStatusUpdate

# Connect to Redis
# redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
# deployment_queue = Queue('deployment_queue', connection=redis_client)

router = APIRouter()


@router.post("/", response_model=Deployment, responses={
    200: {"description": "Deployment created successfully", "content": {"application/json": {"example": {"id": 1, "name": "Deployment1", "docker_image": "my_image", "cpu_required": 2, "ram_required": 4, "gpu_required": 1, "priority": 1, "status": "running", "cluster_id": 1}}}},
    404: {"description": "Cluster not found", "content": {"application/json": {"example": {"detail": "Cluster not found"}}}},
})
async def create_deployment(
        *,
        db: Session = Depends(deps.get_db),
        deployment_in: DeploymentCreate,
        scheduler: Scheduler = Depends(deps.get_scheduler)

):
    """
    Create a deployment and add it to a cluster if resources are available.
    If not, queue the deployment for scheduling later, with preemption for high-priority deployments.
    """
    # Check if the cluster exists
    cluster = db.query(Cluster).filter(Cluster.id == deployment_in.cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found"
        )

    # Use the scheduler to handle deployment
    deployment = scheduler.schedule(db, cluster, deployment_in)
    return deployment


@router.get("/", response_model=List[Deployment], responses={
    200: {"description": "List of deployments for the user's organization", "content": {"application/json": {"example": [{"id": 1, "name": "Deployment1", "docker_image": "my_image", "cpu_required": 2, "ram_required": 4, "gpu_required": 1, "priority": 1, "status": "running", "cluster_id": 1}]}}},
    400: {"description": "User is not part of any organization", "content": {"application/json": {"example": {"detail": "User is not part of any organization"}}}},
})
async def list_deployments(
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_user)
):
    """
    List all deployments for the current user's organization.
    """
    if not current_user.org_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not part of any organization"
        )

    deployments = db.query(DeploymentModel).join(Cluster).filter(
        Cluster.organization_id == current_user.org_member.organization_id
    ).all()

    return deployments


@router.patch("/{deployment_id}/status", response_model=Deployment, responses={
    400: {"description": "Invalid status transition", "content": {"application/json": {"example": {"detail": "Invalid status transition from completed to failed"}}}},
    404: {"description": "Deployment not found", "content": {"application/json": {"example": {"detail": "Deployment not found"}}}},
})
async def update_deployment_status(
    *,
    deployment_id: int,
    status_update: DeploymentStatusUpdate,
    db: Session = Depends(deps.get_db),
    scheduler: Scheduler = Depends(deps.get_scheduler),
):
    """
    Update the status of a deployment and deallocate resources if necessary.
    """
    # Fetch the deployment
    deployment = db.query(DeploymentModel).filter(DeploymentModel.id == deployment_id).first()
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found"
        )

    if status_update.status not in valid_state_transitions[deployment.status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {deployment.status} to {status_update.status}",
        )

    scheduler.process_deployment_stopped_running(db, deployment, status_update)

    # Update the deployment status
    deployment.status = status_update.status
    db.commit()

    return deployment