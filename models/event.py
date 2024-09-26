# models/form.py

from sqlalchemy import Column, String, DateTime, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from database import Base

class Event(Base):
    __tablename__ = "event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    title = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    from_date = Column(String, nullable=True)  # Změna typu z DateTime na String
    to_date = Column(String, nullable=True)    # Změna typu z DateTime na String
    all_day = Column(String, nullable=True)
    links = Column(String, nullable=True)
    address = Column(String, nullable=True)
    files = Column(String, nullable=True)
