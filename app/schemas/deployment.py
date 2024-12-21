from pydantic import BaseModel, Field

from app.models.deployment import DeploymentStatus


class DeploymentBase(BaseModel):
    name: str
    docker_image: str
    cpu_required: float = Field(ge=0, description="CPU required must be a non-negative float")
    ram_required: float = Field(ge=0, description="RAM required must be a non-negative float")
    gpu_required: float = Field(ge=0, description="GPU required must be a non-negative float")
    priority: int = Field(ge=0, description="Priority must be a non-negative integer")


class DeploymentCreate(DeploymentBase):
    cluster_id: int


class DeploymentUpdate(DeploymentBase):
    pass


class Deployment(DeploymentBase):
    id: int
    cluster_id: int
    status: DeploymentStatus

    class Config:
        from_attributes = True
