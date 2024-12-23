from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from app.models.deployment import Deployment as DeploymentModel
from app.models.cluster import Cluster
from app.schemas.deployment import DeploymentCreate, DeploymentStatusUpdate


class Scheduler(ABC):
    @abstractmethod
    def schedule(self, db: Session, cluster: Cluster, deployment_in: DeploymentCreate) -> DeploymentModel:
        """
        Schedule a single deployment, checking resources and preemption.
        """
        pass

    @abstractmethod
    def process_deployment_status_update(self, db: Session, deployment: DeploymentModel, status_update: DeploymentStatusUpdate):
        """
        process updated deployments to dealloc resources if applicable
        """
        pass
