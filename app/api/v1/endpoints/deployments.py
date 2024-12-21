from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import deps
from app.models.cluster import Cluster
from app.models.deployment import Deployment as DeploymentModel, DeploymentStatus
from app.models.user import User
from app.schemas.deployment import Deployment, DeploymentCreate

router = APIRouter()


@router.post("/", response_model=Deployment)
def create_deployment(
        *,
        db: Session = Depends(deps.get_db),
        deployment_in: DeploymentCreate,
        current_user: User = Depends(deps.get_current_user)
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

    # Check if the cluster has enough resources
    if (
            cluster.cpu_available >= deployment_in.cpu_required
            and cluster.ram_available >= deployment_in.ram_required
            and cluster.gpu_available >= deployment_in.gpu_required
    ):
        # Allocate resources and mark the deployment as running
        cluster.cpu_available -= deployment_in.cpu_required
        cluster.ram_available -= deployment_in.ram_required
        cluster.gpu_available -= deployment_in.gpu_required
        deploy_status = DeploymentStatus.RUNNING
    else:
        # Attempt to preempt lower-priority deployments to free resources
        preempted_deployments = db.query(DeploymentModel).filter(
            DeploymentModel.cluster_id == deployment_in.cluster_id,
            DeploymentModel.status == DeploymentStatus.RUNNING,
            DeploymentModel.priority < deployment_in.priority  # Only preempt lower-priority deployments
        ).order_by(DeploymentModel.priority.asc()).all()

        resources_freed = False
        for deployment in preempted_deployments:
            # Check if preempted deployment can be stopped
            if (
                    cluster.cpu_available >= deployment_in.cpu_required
                    and cluster.ram_available >= deployment_in.ram_required
                    and cluster.gpu_available >= deployment_in.gpu_required
            ):
                # Free resources by marking deployment as failed
                deployment.status = DeploymentStatus.FAILED
                cluster.cpu_available += deployment.cpu_required
                cluster.ram_available += deployment.ram_required
                cluster.gpu_available += deployment.gpu_required
                db.commit()

                # Once enough resources are freed, allocate to the new deployment
                resources_freed = True
                break

        if not resources_freed:
            # If resources are still not enough, queue the deployment
            deploy_status = DeploymentStatus.PENDING

        else:
            # If resources are freed, proceed with running the new deployment
            deploy_status = DeploymentStatus.RUNNING

            # Allocate resources
            cluster.cpu_available -= deployment_in.cpu_required
            cluster.ram_available -= deployment_in.ram_required
            cluster.gpu_available -= deployment_in.gpu_required

    # Create the deployment record
    deployment = DeploymentModel(
        name=deployment_in.name,
        docker_image=deployment_in.docker_image,
        cpu_required=deployment_in.cpu_required,
        ram_required=deployment_in.ram_required,
        gpu_required=deployment_in.gpu_required,
        priority=deployment_in.priority,
        status=deploy_status,
        cluster_id=deployment_in.cluster_id,
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    return deployment


# app/api/v1/endpoints/deployments.py
@router.get("/", response_model=List[Deployment])
def list_deployments(
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(deps.get_current_user)
):
    """
    List all deployments for the current user's organization.
    """
    if not current_user.organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not part of any organization"
        )

    deployments = db.query(DeploymentModel).join(Cluster).filter(
        Cluster.organization_id == current_user.organization.id
    ).all()

    return deployments