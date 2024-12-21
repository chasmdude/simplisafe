from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.base_class import Base

class DeploymentStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"

class Deployment(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    cluster_id = Column(Integer, ForeignKey("cluster.id"))
    docker_image = Column(String)
    status = Column(Enum(DeploymentStatus))
    priority = Column(Integer, default=0)
    
    # Resource requirements
    cpu_required = Column(Float)
    ram_required = Column(Float)
    gpu_required = Column(Float)
    
    # Relationships
    cluster = relationship("Cluster", back_populates="deployments")
