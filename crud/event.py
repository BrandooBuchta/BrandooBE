# crud/form.py

from sqlalchemy.orm import Session, joinedload, join
from models.form import Form
from schemas.event import FormResponseEventManageSchema
from uuid import UUID, uuid4
from fastapi import HTTPException
from crud.user import get_user
from utils.security import rsa_encrypt_data, rsa_decrypt_data
from models.event import Event
from datetime import datetime
import json
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

def create_event(db: Session, event_data: FormResponseEventManageSchema):
    user = get_user(db, event_data.user_id)

    # Encrypt datetime and boolean fields as strings
    encrypted_from_date = rsa_encrypt_data(event_data.from_date.isoformat(), user.public_key) if event_data.from_date else None
    encrypted_to_date = rsa_encrypt_data(event_data.to_date.isoformat(), user.public_key) if event_data.to_date else None
    encrypted_all_day = rsa_encrypt_data(str(event_data.all_day).lower(), user.public_key) if event_data.all_day is not None else None

    event = Event(
        id=uuid4(),
        response_id=event_data.response_id,
        user_id=event_data.user_id,
        title=rsa_encrypt_data(event_data.title, user.public_key),
        notes=rsa_encrypt_data(event_data.notes, user.public_key) if event_data.notes else None,
        from_date=encrypted_from_date,
        to_date=encrypted_to_date,
        all_day=encrypted_all_day,
        links=rsa_encrypt_data(event_data.links, user.public_key) if event_data.links else None,
        address=rsa_encrypt_data(event_data.address, user.public_key) if event_data.address else None,
        files=rsa_encrypt_data(json.dumps(event_data.files), user.public_key) if event_data.files else rsa_encrypt_data(json.dumps([]), user.public_key)  # Inicializuj na prázdný seznam
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def update_event(db: Session, event_id: UUID, event_data: FormResponseEventManageSchema):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user = get_user(db, event.user_id)
    if not user or not user.public_key:
        raise HTTPException(status_code=404, detail="User or public_key not found")

    # Update title
    if event_data.title:
        event.title = rsa_encrypt_data(event_data.title, user.public_key)

    # Update notes
    if event_data.notes:
        event.notes = rsa_encrypt_data(event_data.notes, user.public_key)

    # Update from_date (ensure proper datetime conversion and encryption)
    if event_data.from_date:
        event.from_date = rsa_encrypt_data(event_data.from_date.isoformat(), user.public_key)

    # Update to_date (ensure proper datetime conversion and encryption)
    if event_data.to_date:
        event.to_date = rsa_encrypt_data(event_data.to_date.isoformat(), user.public_key)

    # Update all_day (convert boolean to string and encrypt)
    if event_data.all_day is not None:
        event.all_day = rsa_encrypt_data(str(event_data.all_day).lower(), user.public_key)

    # Update links
    if event_data.links:
        event.links = rsa_encrypt_data(event_data.links, user.public_key)

    # Update address
    if event_data.address:
        event.address = rsa_encrypt_data(event_data.address, user.public_key)

    # Update files (convert to string and encrypt)
    if event_data.files is not None:
        encrypted_files = rsa_encrypt_data(json.dumps(event_data.files), user.public_key)
        event.files = encrypted_files

    # Commit the changes
    db.commit()
    db.refresh(event)
    
    return event

def delete_event(db: Session, event_id: UUID, private_key: str):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    decrypted_files = rsa_decrypt_data(event.files, private_key) if event.files else "[]"
    files = json.loads(decrypted_files)

    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)

        for file in files:
            file_name = os.path.basename(file)
            remote_file_path = f"{SFTP_UPLOAD_DIR}/{file_name}"
            sftp.remove(remote_file_path)

        sftp.close()
        transport.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")

    db.delete(event)
    db.commit()

    return {"detail": "Event and associated files deleted successfully"}

def decrypt_event_data(event: Event, private_key: str):
    try:
        decrypted_files = rsa_decrypt_data(event.files, private_key) if event.files else "[]"
        files = json.loads(decrypted_files)
    except json.JSONDecodeError:
        files = []

    return {
        "id": event.id,
        "response_id": event.response_id,
        "user_id": event.user_id,
        "title": rsa_decrypt_data(event.title, private_key) if event.title else None,
        "notes": rsa_decrypt_data(event.notes, private_key) if event.notes else None,
        "from_date": datetime.fromisoformat(rsa_decrypt_data(event.from_date, private_key)) if event.from_date else None,
        "to_date": datetime.fromisoformat(rsa_decrypt_data(event.to_date, private_key)) if event.to_date else None,
        "all_day": rsa_decrypt_data(event.all_day, private_key).lower() == 'true' if event.all_day else None,
        "links": rsa_decrypt_data(event.links, private_key) if event.links else None,
        "address": rsa_decrypt_data(event.address, private_key) if event.address else None,
        "files": files,  # Ensure the files are correctly decrypted and parsed
        "created_at": event.created_at,
        "updated_at": event.updated_at
    }

def get_event_by_id(db: Session, event_id: UUID, private_key: str):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return decrypt_event_data(event, private_key)

def get_events_by_response_id(db: Session, response_id: UUID, private_key: str):
    events = db.query(Event).filter(Event.response_id == response_id).all()
    
    return [decrypt_event_data(event, private_key) for event in events]

def get_events_by_user_id(db: Session, user_id: UUID, private_key: str):
    events = db.query(Event).filter(Event.user_id == user_id).all()
    
    return [decrypt_event_data(event, private_key) for event in events]
