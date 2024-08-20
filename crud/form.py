# crud/form.py

from sqlalchemy.orm import Session
from models.form import Form, FormProperty, FormResponse, FormValue
from schemas.form import CreateFormRequest, FormPropertyCRUDModel, UpdateFormRequest, FormPropertyCRUDModelOptional
from uuid import UUID, uuid4
from utils.security import encrypt_data
from crud.user import get_user
from typing import Dict, Any

def create_form(db: Session, form: CreateFormRequest, user_id: UUID):
    db_form = Form(
        id=uuid.uuid4(),
        user_id=user_id,
        name=form.name,
        description=form.description,
    )
    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    
    return db_form

def get_form(db: Session, form_id: UUID):
    db_form = db.query(Form).filter(Form.id == form_id).first()
    
    if not db_form:
        return 404, None
    return 200, db_form

def update_form(db: Session, form_id: UUID, form: UpdateFormRequest):
    status, db_form = get_form(db, form_id)
    if not db_form:
        return 404, None
    for key, value in form.dict(exclude_unset=True).items():
        setattr(db_form, key, value)
    db.commit()
    db.refresh(db_form)
    return 200, db_form

def delete_form(db: Session, form_id: UUID):
    status, db_form = get_form(db, form_id)
    if db_form:
        db.delete(db_form)
        db.commit()
        return True
    return False

def get_form_property(db: Session, property_id: UUID):
    db_form_property = db.query(FormProperty).filter(FormProperty.id == property_id).first()
    
    if not db_form_property:
        return 404, None
    return 200, db_form_property
    
def get_form_properties(db: Session, form_id: UUID):
    db_form_properties = db.query(FormProperty).filter(FormProperty.form_id == form_id).all()
    
    if not db_form_properties:
        return 404, None
    return 200, db_form_properties

def create_form_property(db: Session, prop: FormPropertyCRUDModel, form_id: UUID, user_id: UUID):
    db_property = FormProperty(
        id=uuid.uuid4(),
        user_id=user_id,
        form_id=form_id,
        label=prop.label,
        key=prop.key,
        description=prop.description,
        property_type=prop.property_type,
    )
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    
    return db_property

def update_form_property(db: Session, prop: FormPropertyCRUDModelOptional, property_id: UUID):
    status, db_property = get_form_property(db, property_id)
    if not db_property:
        return 404, None
    for key, value in prop.dict(exclude_unset=True).items():
        setattr(db_property, key, value)
    db.commit()
    db.refresh(db_property)
    return 200, db_property

def delete_form_property(db: Session, property_id: UUID):
    status, db_property = get_form_property(db, property_id)
    if db_property:
        db.delete(db_property)
        db.commit()
        return True
    return False

def create_form_response(db: Session, form_id: UUID):
    status, form = get_form(db, form_id)
    db_response = FormResponse(
        id=uuid.uuid4(),
        user_id=form.user_id,
        form_id=form_id,
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    
    return db_response

def get_response_values(db: Session, response_id: UUID):
    db_values = db.query(FormValue).filter(FormValue.response_id == response_id).all()
    
    if not db_values:
        return 404, None
    return 200, db_values

def create_response(db: Session, form_id: UUID, values: Dict[str, Any]):
    status, db_properties = get_form_properties(db, form_id)
    status, form = get_form(db, form_id)
    user = get_user(db, form.user_id)

    response = create_form_response(db, form_id)

    for key, value in values.items():
        matching_property = next((prop for prop in db_properties if prop.key == key), None)
        
        if matching_property:
            print(f"Found matching property for key '{key}': {matching_property}")

        db_value = FormValue(
            id=uuid.uuid4(),
            user_id=form.user_id,
            form_id=form_id,
            property_id=matching_property.id,
            property_type=matching_property.property_type,
            response_id=response.id,
            property_key=key,
        )

        setattr(db_value, matching_property.property_type, encrypt_data(value, user.public_key))

        db.add(db_value)
        db.commit()
        db.refresh(db_value)

    form_values_ids = []
    status, response_values = get_response_values(db, response.id)
    for v in response_values:
        form_values_ids.append(v.id)

    response.form_values_ids = form_values_ids
    db.commit()
    db.refresh(response)

    return response
