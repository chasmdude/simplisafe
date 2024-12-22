# app/models/organization.py
import uuid
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Organization(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    invite_code = Column(String, unique=True, index=True)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    clusters = relationship("Cluster", back_populates="organization")

    @staticmethod
    def generate_invite_code():
        return str(uuid.uuid4())