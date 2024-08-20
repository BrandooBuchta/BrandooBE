# # models/contacts.py

# from sqlalchemy import Column, String, DateTime, Boolean, ARRAY
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.sql import func
# import uuid
# from database import Base

# class Contact(Base):
#     __tablename__ = "contact"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     user_id = Column(UUID(as_uuid=True), nullable=False)
#     name = Column(String, nullable=True)
#     first_name = Column(String, nullable=True)
#     middle_name = Column(String, nullable=True)
#     last_name = Column(String, nullable=True)
#     company_name = Column(String, nullable=True)
#     job = Column(String, nullable=True)
#     country = Column(String, nullable=True)
#     state = Column(String, nullable=True)
#     city = Column(String, nullable=True)
#     postal_code = Column(String, nullable=True)
#     preffered_contact_method = Column(String, nullable=True)
#     preffered_contact_time = Column(String, nullable=True)
#     secondary_email = Column(String, nullable=True)
#     secondary_phone = Column(String, nullable=True)
#     referral_source = Column(String, nullable=True)
#     notes = Column(String, nullable=True)
#     email = Column(String, nullable=True)
#     phone = Column(String, nullable=True)
#     address = Column(String, nullable=True)
#     initial_message = Column(String, nullable=True)
#     description = Column(String, nullable=True)
#     seen = Column(Boolean, default=False)
#     agreed_to_privacy_policy = Column(Boolean, default=False)
#     agreed_to_news_letter = Column(Boolean, default=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#     form_id = Column(UUID(as_uuid=True), nullable=False)
#     labels = Column(ARRAY(String), nullable=False)

# class Form(Base):
#     __tablename__ = "form"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     user_id = Column(UUID(as_uuid=True), nullable=False)
#     name = Column(String, nullable=False)
#     description = Column(String, nullable=False)
#     form_properties = Column(ARRAY(String), nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# class Label(Base):
#     __tablename__ = "label"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     user_id = Column(UUID(as_uuid=True), nullable=False)
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     color = Column(String, nullable=False)
#     title = Column(String, nullable=False)
