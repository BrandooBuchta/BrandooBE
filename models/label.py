# models/label.py

from sqlalchemy import Column, String, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship 
from sqlalchemy.sql import func
import uuid
from database import Base
from datetime import timedelta

class Label(Base):
    __tablename__ = "label"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    color = Column(String, nullable=False)
    title = Column(String, nullable=False)