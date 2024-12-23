import threading
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.cluster import Cluster
from app.models.deployment import Deployment as DeploymentModel, DeploymentStatus
from app.schedulers.scheduler_interface import Scheduler
from app.schemas.deployment import DeploymentCreate, DeploymentStatusUpdate


def cluster_has_sufficient_resources(cluster, deployment):
    return (cluster.cpu_available >= deployment.cpu_required
            and cluster.ram_available >= deployment.ram_required
            and cluster.gpu_available >= deployment.gpu_required)


class AdvancedScheduler(Scheduler):

    def __init__(self):
        # This dictionary will map cluster IDs to locks for thread safety.
        self.cluster_locks: Dict[int, threading.Lock] = {}

    def _get_cluster_lock(self, cluster_id: int) -> threading.Lock:
        """
        Get or create a lock for the given cluster ID to ensure thread safety for the same cluster.
        """
        if cluster_id not in self.cluster_locks:
            # Create a new lock for this cluster if it doesn't already exist.
            self.cluster_locks[cluster_id] = threading.Lock()
        return self.cluster_locks[cluster_id]


    def schedule(
            self,
            db: Session,
            cluster: Cluster,
            deployment_in: DeploymentCreate
    ) -> DeploymentModel:
        """
        Processes the deployment:
        - Allocates resources if available.
        - If resources are unavailable, attempts to preempt lower priority deployments.
        """
        deployment = DeploymentModel(
            name=deployment_in.name,
            docker_image=deployment_in.docker_image,
            cpu_required=deployment_in.cpu_required,
            ram_required=deployment_in.ram_required,
            gpu_required=deployment_in.gpu_required,
            priority=deployment_in.priority,
            status=DeploymentStatus.PENDING,
            cluster_id=deployment_in.cluster_id,
        )

        # Get a lock for this specific cluster
        cluster_lock = self._get_cluster_lock(deployment.cluster_id)

        with cluster_lock:
            # Try to allocate resources for the new deployment
            if cluster_has_sufficient_resources(cluster, deployment):
                self._allocate_resources(deployment, cluster, db)
                deployment.status = DeploymentStatus.RUNNING
            else:
                # If resources aren't available, attempt preemption
                self._handle_preemption(db, deployment, cluster)

        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        return deployment

    def process_deployment_status_update(self, db: Session, deployment: DeploymentModel ,  status_uddate: DeploymentStatusUpdate):
        # If the deployment is no longer active, deallocate resources
        if deployment.status == DeploymentStatus.RUNNING:
            cluster = db.query(Cluster).filter(Cluster.id == deployment.cluster_id).first()
            # Get a lock for this specific cluster
            cluster_lock = self._get_cluster_lock(deployment.cluster_id)

            # Lock the critical section to ensure thread safety during resource deallocation
            with cluster_lock:
                self._deallocate_resources(deployment, cluster, db)

    def _allocate_resources(
            self, deployment: DeploymentModel, cluster: Cluster, db: Session
    ) -> bool:
        """
        Internal method to allocate resources for the deployment.
        This method should be protected by a lock.
        """
        # Allocate resources
        cluster.cpu_available -= deployment.cpu_required
        cluster.ram_available -= deployment.ram_required
        cluster.gpu_available -= deployment.gpu_required
        db.commit()

    def _deallocate_resources(
            self, deployment: DeploymentModel, cluster: Cluster, db: Session
    ):
        """
        Internal method to deallocate resources for a deployment.
        This method should be protected by a lock.
        """
        cluster.cpu_available += deployment.cpu_required
        cluster.ram_available += deployment.ram_required
        cluster.gpu_available += deployment.gpu_required
        db.commit()

    def _handle_preemption(self, db: Session, deployment: DeploymentModel, cluster: Cluster):
        """
        Handle preemption: If resources are not available, attempt to preempt lower-priority deployments.
        """
        # Find the lower-priority deployments that are currently running
        preempted_deployments = db.query(DeploymentModel).filter(
            DeploymentModel.cluster_id == deployment.cluster_id,
            DeploymentModel.status == DeploymentStatus.RUNNING,
            DeploymentModel.priority < deployment.priority
        ).order_by(DeploymentModel.priority.asc()).all()

        available_cluster_cpu = cluster.cpu_available
        available_cluster_ram = cluster.ram_available
        available_cluster_gpu = cluster.gpu_available

        cpu_required_for_new_deployment = deployment.cpu_required
        ram_required_for_new_deployment = deployment.ram_required
        gpu_required_for_new_deployment = deployment.gpu_required

        for preempted_deployment in preempted_deployments:
            cpu_required_for_preempted_deployment = preempted_deployment.cpu_required
            ram_required_for_preempted_deployment = preempted_deployment.ram_required
            gpu_required_for_preempted_deployment = preempted_deployment.gpu_required
            if (
                    available_cluster_cpu + cpu_required_for_preempted_deployment < cpu_required_for_new_deployment or
                    available_cluster_ram + ram_required_for_preempted_deployment < ram_required_for_new_deployment or
                    available_cluster_gpu + gpu_required_for_preempted_deployment < gpu_required_for_new_deployment
            ):
                continue
            # deallocating resources of the lower-priority deployment
            self._deallocate_resources(preempted_deployment, cluster, db)
            preempted_deployment.status = DeploymentStatus.PENDING

            # Once resources are freed, allocate to the new deployment
            self._allocate_resources(deployment, cluster, db)
            deployment.status = DeploymentStatus.RUNNING
            break
