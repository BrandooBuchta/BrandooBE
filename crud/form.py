# crud/form.py

from sqlalchemy.orm import Session, joinedload, join
from models.form import Form, FormProperty, FormResponse, FormValue
from schemas.form import CreateForm, UpdateForm, FormResponseMessageCreate, FormResponseMessageUpdate
from uuid import UUID, uuid4
from fastapi import HTTPException
from crud.user import get_user
from utils.security import rsa_encrypt_data, rsa_decrypt_data
from models.form import FormResponseMessage
import ast
from datetime import datetime, timezone
import time
import json
import logging
import paramiko
from dotenv import load_dotenv
import os

load_dotenv()

SFTP_HOST = os.getenv("SFTP_HOST")
SFTP_PORT = int(os.getenv("SFTP_PORT"))
SFTP_USERNAME = os.getenv("SFTP_USERNAME")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
SFTP_UPLOAD_DIR = os.getenv("SFTP_UPLOAD_DIR")

def validate_iso_format(date_str):
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

def create_form(db: Session, form: CreateForm, user_id: UUID):
    db_form = Form(
        id=uuid4(),
        user_id=user_id,
        name=form.name,
        description=form.description,
        form_properties_ids=[],
    )
    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    
    return db_form

def get_form(db: Session, form_id: UUID):
    form = db.query(Form).options(joinedload(Form.properties)).filter(Form.id == form_id).first()

    if form:
        form.properties = sorted(form.properties, key=lambda prop: prop.position)

    return form

def update_form(db: Session, form_id: UUID, update_data: UpdateForm):
    form = db.query(Form).filter(Form.id == form_id).first()

    if not form:
        return None

    if update_data.name:
        form.name = update_data.name
    if update_data.description:
        form.description = update_data.description

    existing_properties = {str(p.id): p for p in form.properties}
    incoming_properties = {str(p.id): p for p in update_data.properties if p.id}

    new_properties = []
    for prop in update_data.properties:
        print(f"prop: {prop}")
        if prop.id:
            existing_property = existing_properties[str(prop.id)]
            existing_property.label = prop.label
            existing_property.position = prop.position
            existing_property.options = prop.options
        elif not prop.id:
            new_property = FormProperty(
                id=uuid4(),
                form_id=form_id,
                user_id=form.user_id,
                label=prop.label,
                key=prop.key,
                options=prop.options,
                position=prop.position,
                property_type=prop.property_type,
                required=prop.required
            )
            new_properties.append(new_property)

    properties_to_delete = [p for p_id, p in existing_properties.items() if p_id not in incoming_properties]
    for prop in properties_to_delete:
        db.delete(prop)

    db.add_all(new_properties)
    db.commit()
    db.refresh(form)

    return form

def delete_form(db: Session, form_id: UUID):
    form = db.query(Form).filter(Form.id == form_id).first()

    if not form:
        return None

    db.query(FormProperty).filter(FormProperty.form_id == form_id).delete()
    db.query(FormResponse).filter(FormResponse.form_id == form_id).delete()
    db.query(FormValue).filter(FormValue.form_id == form_id).delete()

    db.delete(form)
    db.commit()

    return form

def get_users_form_menu(db: Session, user_id: UUID):
    db_forms = db.query(Form).filter(Form.user_id == user_id).all()
    
    if not db_forms:
        return []
    
    forms = []

    for form in db_forms:
        forms.append({
            "id": form.id,
            "name": form.name
        })

    return forms

def create_response(db: Session, form_id: UUID, data: dict):
    form = db.query(Form).options(joinedload(Form.properties)).filter(Form.id == form_id).first()
    user = get_user(db, form.user_id)

    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    user_id = form.user_id

    required_properties = {prop.key: prop for prop in form.properties if prop.required}
    missing_keys = [key for key in required_properties.keys() if key not in data.keys()]

    if missing_keys:
        raise HTTPException(status_code=400, detail=f"Missing required keys: {', '.join(missing_keys)}")

    response_id = uuid4()
    new_response = FormResponse(
        id=response_id,
        user_id=user_id,
        form_id=form_id,
        form_values_ids=[],
        labels=[],
        seen=False,
    )
    db.add(new_response)
    db.commit()

    form_value_ids = []
    for key, value in data.items():
        prop = next((p for p in form.properties if p.key == key), None)
        if not prop:
            continue

        value_str = str(value)
        
        form_value = FormValue(
            id=uuid4(),
            user_id=user_id,
            form_id=form_id,
            property_id=prop.id,
            response_id=response_id,
            property_key=key,
            property_type=prop.property_type,
            value=rsa_encrypt_data(value_str, user.public_key)
        )

        db.add(form_value)
        db.commit()
        form_value_ids.append(form_value.id)

    new_response.form_values_ids = form_value_ids
    db.commit()

    return {"response_id": new_response.id}

def get_plain_response(db: Session, response_id):
    response = db.query(FormResponse).filter(FormResponse.id == response_id).first()

    if not response:
        return None, 404

    return response, 200

def update_response(db: Session, response_id: UUID, response_update: dict):
    # Najít existující odpověď podle ID
    response = db.query(FormResponse).filter(FormResponse.id == response_id).first()

    if not response:
        return None
    
    for key, value in response_update.items():
        if key == "labels" and isinstance(value, list):
            # Předpokládá se, že 'value' je seznam řetězců
            response.labels = value
        else:
            setattr(response, key, value)

    # Uložit změny do databáze
    db.commit()
    db.refresh(response)
    
    return response

def get_response_by_id(db: Session, response_id: UUID, private_key: str):
    response = db.query(FormResponse).options(joinedload(FormResponse.form)).filter(FormResponse.id == response_id).first()

    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    form = response.form
    user = get_user(db, response.user_id)

    decrypted_data = {}
    for form_value_id in response.form_values_ids:
        form_value = db.query(FormValue).filter(FormValue.id == form_value_id).first()
        if not form_value:
            continue

        # Dešifrování
        decrypted_value = rsa_decrypt_data(form_value.value, private_key)

        # Deserializace na základě typu property
        if form_value.property_type == "boolean":
            decrypted_value = decrypted_value.lower() == 'true'
        elif form_value.property_type == "checkbox":
            try:
                decrypted_value = ast.literal_eval(decrypted_value)  # Deserializace na seznam
            except (ValueError, SyntaxError) as e:
                decrypted_value = decrypted_value.split(',')  # Fallback metoda
        elif form_value.property_type == "file":
            try:
                decrypted_value = ast.literal_eval(decrypted_value)  # Deserializace na seznam
            except (ValueError, SyntaxError) as e:
                decrypted_value = decrypted_value.strip("[]").replace('"', '').split(',')  # Fallback metoda
        elif form_value.property_type == "date_time":
            decrypted_value = datetime.fromisoformat(decrypted_value)
        elif form_value.property_type == "time":
            try:
                decrypted_value = datetime.strptime(decrypted_value, "%H:%M:%S").time()
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid time format: {decrypted_value}")
        else:
            decrypted_value = decrypted_value

        decrypted_data[form_value.property_key] = decrypted_value

    return decrypted_data

def create_form_response_message(db: Session, message_data: FormResponseMessageCreate):
    user = get_user(db, message_data.user_id)

    db_message = FormResponseMessage(
        id=uuid4(),
        response_id=message_data.response_id,
        user_id=message_data.user_id,
        message=rsa_encrypt_data(message_data.message, user.public_key)
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages_by_response_id(db: Session, response_id: UUID):
    return db.query(FormResponseMessage).filter(FormResponseMessage.response_id == response_id).all()

def update_form_response_message(db: Session, message_id: UUID, update_data: FormResponseMessageUpdate):
    message = db.query(FormResponseMessage).filter(FormResponseMessage.id == message_id).first()
    user = get_user(db, message.user_id)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if update_data.message:
        message.message = rsa_encrypt_data(update_data.message, user.public_key)

    db.commit()
    db.refresh(message)
    return message

def count_unseen_responses_by_user_id(db: Session, user_id: UUID):
    return db.query(FormResponse).join(Form).filter(Form.user_id == user_id, FormResponse.seen == False).count()

