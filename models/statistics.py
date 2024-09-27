from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base

class Statistic(Base):
    __tablename__ = "statistic"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    values = relationship("StatisticValue", back_populates="statistic", cascade="all, delete-orphan")

class StatisticValue(Base):
    __tablename__ = "statistic_value"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statistic_id = Column(UUID(as_uuid=True), ForeignKey('statistic.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    time = Column(Time(timezone=False), nullable=True)
    number = Column(Integer, nullable=True)
    boolean = Column(Boolean, nullable=True)
    text = Column(String, nullable=True)

    statistic = relationship("Statistic", back_populates="values")
