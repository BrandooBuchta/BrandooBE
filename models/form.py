# models/form.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum, ARRAY, Boolean, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship 
from sqlalchemy.sql import func
import uuid
from database import Base
from datetime import timedelta

class Form(Base):
    __tablename__ = "form"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    form_properties_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)  # Ensure this is UUID, not string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    properties = relationship("FormProperty", back_populates="form", cascade="all, delete-orphan")
    responses = relationship("FormResponse", back_populates="form", cascade="all, delete-orphan")
    values = relationship("FormValue", back_populates="form", cascade="all, delete-orphan")

class FormProperty(Base):
    __tablename__ = "form_property"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    form_id = Column(UUID(as_uuid=True), ForeignKey('form.id'), nullable=False)
    label = Column(String, nullable=False)
    key = Column(String, nullable=False)
    options = Column(ARRAY(String), nullable=True)
    required = Column(Boolean, default=True)

    property_type = Column(Enum(
        "short_text", 
        "long_text", 
        "boolean", 
        "string_array", 
        "radio", 
        "checkbox", 
        "selection",
        "date_time",
        "time",
        "file",  # Přidána podpora pro soubory
        name="property_type_enum"), 
        nullable=False
    )

    position = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    form = relationship("Form", back_populates="properties")

class FormValue(Base):
    __tablename__ = "form_value"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    form_id = Column(UUID(as_uuid=True), ForeignKey('form.id'), nullable=False)
    property_id = Column(UUID(as_uuid=True), nullable=False)
    response_id = Column(UUID(as_uuid=True), nullable=False)
    property_key = Column(String, nullable=True)
    property_type = Column(Enum(
        "short_text", 
        "long_text", 
        "boolean", 
        "string_array", 
        "radio", 
        "checkbox", 
        "selection", 
        "date_time",
        "time",
        "file",
        name="property_type_enum"), 
        nullable=False
    )
    
    value = Column(String, nullable=True)  # Nový sloupec pro šifrované hodnoty

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    form = relationship("Form", back_populates="values")
    
class FormResponse(Base):
    __tablename__ = "form_response"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    form_id = Column(UUID(as_uuid=True), ForeignKey('form.id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    form_values_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)  # Ensure this is UUID, not string
    labels = Column(ARRAY(String), nullable=False)
    seen = Column(Boolean, default=False)
    alias = Column(String, nullable=True)

    form = relationship("Form", back_populates="responses")

class FormResponseMessage(Base):
    __tablename__ = "form_response_message"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    editable_until = Column(DateTime(timezone=True), server_default=func.now() + timedelta(minutes=15))
    message = Column(String, nullable=False)