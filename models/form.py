# models/form.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum, ARRAY, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship 
from sqlalchemy.sql import func
import uuid
from database import Base

class Form(Base):
    __tablename__ = "form"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    form_properties = Column(ARRAY(String), nullable=True)
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
    description = Column(String, nullable=False)

    property_type = Column(Enum(
        "short_text", 
        "long_text", 
        "boolean", 
        "string_array", 
        "radio", 
        "checkbox", 
        "selection", 
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
        name="property_type_enum"), 
        nullable=False
    )
    
    # values
    short_text = Column(String, nullable=True)
    long_text = Column(String, nullable=True)
    boolean = Column(Boolean, nullable=True)
    single_choice = Column(String, nullable=True)
    multiple_choice = Column(ARRAY(String), nullable=True)
    radio = Column(String, nullable=True)
    checkbox = Column(ARRAY(String), nullable=True)

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
    form_values_ids = Column(ARRAY(String), nullable=False)
    labels = Column(ARRAY(String), nullable=False)
    seen = Column(Boolean, default=False)

    form = relationship("Form", back_populates="responses")

class Label(Base):
    __tablename__ = "label"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    color = Column(String, nullable=False)
    title = Column(String, nullable=False)
