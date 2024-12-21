from pydantic import BaseModel, Field


class ClusterBase(BaseModel):
    name: str
    cpu_limit: float = Field(ge=0, description="CPU limit must be a non-negative float")
    ram_limit: float = Field(ge=0, description="RAM limit must be a non-negative float")
    gpu_limit: float = Field(ge=0, description="GPU limit must be a non-negative float")


class ClusterCreate(ClusterBase):
    organization_id: int


class ClusterUpdate(ClusterBase):
    pass


class Cluster(ClusterBase):
    id: int
    organization_id: int
    cpu_available: float
    ram_available: float
    gpu_available: float

    class Config:
        from_attributes = True
