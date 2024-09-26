# models/cms.py

from sqlalchemy import Column, String, DateTime, Enum, Boolean, Integer, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base
from sqlalchemy import event

class Content(Base):
    __tablename__ = "content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    position = Column(Integer, nullable=False)
    root_content_id = Column(UUID(as_uuid=True), nullable=True)
    parent_content_id = Column(UUID(as_uuid=True), nullable=True)

    is_root = Column(Boolean, default=False)
    alias = Column(String, nullable=True)

    content_type = Column(Enum(
        "text",
        "image",
        "html",
        "item_content",
        "list_text_content",
        "list_item_content",
        name="content_type_enum"),
        nullable=True
    )
    text = Column(String, nullable=True)
    image = Column(String, nullable=True)  # Path
    html = Column(String, nullable=True)
    list_text_content = Column(ARRAY(String), nullable=True)
    item_content = Column(ARRAY(UUID(as_uuid=True)), default=[])
    list_item_content = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ContentItemProperty(Base): # Object property
    __tablename__ = "content_item_property"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_content_id = Column(UUID(as_uuid=True), nullable=False)
    root_content_id = Column(UUID(as_uuid=True), nullable=False)

    user_id = Column(UUID(as_uuid=True), nullable=False)

    key = Column(String, nullable=True)
    content_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
