# routers/form.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import SessionLocal
from utils.security import verify_token
from fastapi.security import OAuth2PasswordBearer
from schemas.label import ContactLabel, ContactLabelCreate, ContactLabelUpdate
from crud.label import create_label, get_labels, get_label, update_label, delete_label
from crud.user import get_user
from uuid import UUID
from typing import List, Optional
from fastapi import Query
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

@router.post("/{user_id}")
def create_new_label(user_id: UUID, contact_label_create: ContactLabelCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    create_label(db, contact_label_create, user_id)
    return {"detail": "Succcessfuly created new label!"}

@router.get("/{label_id}", response_model=ContactLabel)
def get_label_by_id(label_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, label = get_label(db, label_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Label not found")
    if not verify_token(db, label.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return label

@router.get("/user/{user_id}", response_model=List[ContactLabel])
def get_labels_by_id(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    status, labels = get_labels(db, user_id)
    if status == 404:
        return []
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return labels

@router.put("/{label_id}")
def update_label_by_id(label_id: UUID, new_label: ContactLabelUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, label = get_label(db, label_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Label not found")
    if not verify_token(db, label.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    update_label(db, label_id, new_label)
    return {"detail": "Succcessfuly updated your label!"}

@router.delete("/{label_id}")
def delete_label_by_id(label_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, label = get_label(db, label_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Label not found")
    if not verify_token(db, label.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    delete_label(db, label_id)
    return {"detail": "Succcessfuly deleted your label!"}
