from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    org_member = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan", uselist=False)

