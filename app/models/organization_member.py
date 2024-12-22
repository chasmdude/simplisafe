from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class OrganizationMember(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    role = Column(String, default="member")  # Example: 'admin', 'member'

    # Relationships
    user = relationship("User", back_populates="organization")
    organization = relationship("Organization", back_populates="members")
