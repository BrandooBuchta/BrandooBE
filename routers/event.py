# routers/event.py

# TODO: Implement verification via token

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import desc
from database import SessionLocal
from utils.security import verify_token, decrypt_private_key_for_fe
from fastapi.security import OAuth2PasswordBearer
from schemas.event import FormResponseEventSchema, FormResponseEventManageSchema
from crud.event import create_event, get_event_by_id, update_event, delete_event, get_events_by_response_id, get_events_by_user_id
from uuid import UUID
from typing import List
from datetime import datetime
import base64
import logging

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://www.brandoo.cz",
    "https://app.brandoo.cz",
    "https://api.brandoo.cz",
    "https://dev.api.brandoo.cz",
    "https://dev.app.brandoo.cz",
]

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def validate_iso_format(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

@router.post("")
def create_new_event(event_data: FormResponseEventManageSchema, db: Session = Depends(get_db)):
    logging.info(event_data.json())
    try:
        # Ensure that required fields are validated
        if not isinstance(event_data.all_day, bool):
            raise HTTPException(status_code=400, detail="Invalid value for all_day, must be a boolean")

        if event_data.from_date:
            event_data.from_date = validate_iso_format(event_data.from_date.isoformat())

        if event_data.to_date:
            event_data.to_date = validate_iso_format(event_data.to_date.isoformat())

        # Create event and handle encryption issues
        event = create_event(db, event_data)
        return event
        
    except OperationalError as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{event_id}", response_model=FormResponseEventSchema)
def get_event(event_id: UUID, request: Request, db: Session = Depends(get_db)):
    try:
        private_key = request.headers.get("X-Private-Key")
        if not private_key:
            raise HTTPException(status_code=400, detail="Missing X-Private-Key header")

        event = get_event_by_id(db, event_id, decrypt_private_key_for_fe(private_key))

        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return event

    except HTTPException as e:
        raise e
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")


@router.put("/{event_id}")
def update_existing_event(event_id: UUID, update_data: FormResponseEventSchema, db: Session = Depends(get_db)):
    event = update_event(db, event_id, update_data)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event updated successfully"}
    
@router.delete("/{event_id}")
def delete_existing_event(event_id: UUID, request: Request, db: Session = Depends(get_db)):
    private_key = request.headers.get("X-Private-Key")
    if not private_key:
        raise HTTPException(status_code=400, detail="Missing X-Private-Key header")

    event = delete_event(db, event_id, decrypt_private_key_for_fe(private_key))

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return {"message": "Event and associated files deleted successfully"}


@router.get("/events/response/{response_id}", response_model=List[FormResponseEventSchema])
def get_events_for_response(response_id: UUID, request: Request, db: Session = Depends(get_db)):
    try:
        private_key = request.headers.get("X-Private-Key")
        if not private_key:
            raise HTTPException(status_code=400, detail="Missing X-Private-Key header")

        events = get_events_by_response_id(db, response_id, decrypt_private_key_for_fe(private_key))

        return events if events else []

    except HTTPException as e:
        raise e
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")

@router.get("/events/user/{user_id}", response_model=List[FormResponseEventSchema])
def get_events_for_user(user_id: UUID, request: Request, db: Session = Depends(get_db)):
    try:
        private_key = request.headers.get("X-Private-Key")
        if not private_key:
            raise HTTPException(status_code=400, detail="Missing X-Private-Key header")

        events = get_events_by_user_id(db, user_id, decrypt_private_key_for_fe(private_key))

        return events if events else []

    except HTTPException as e:
        raise e
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")
