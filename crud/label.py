# crud/label.py

from sqlalchemy.orm import Session, joinedload, join
from models.label import Label
from schemas.label import ContactLabelCreate, ContactLabelUpdate
from uuid import UUID, uuid4
from fastapi import HTTPException
from crud.user import get_user

def get_label(db: Session, label_id: UUID):
    db_label = db.query(Label).filter(Label.id == label_id).first()
    if db_label:
        return 200, db_label
    return 404, None
    
def get_labels(db: Session, user_id: UUID):
    db_labels = db.query(Label).filter(Label.user_id == user_id).all()
    if db_labels:
        return 200, db_labels
    return 404, None

def create_label(db: Session, label: ContactLabelCreate, user_id: UUID):
    db_label = Label(
        id=uuid4(),
        user_id=user_id,
        color=label.color,
        title=label.title,
    )
    db.add(db_label)
    db.commit()
    db.refresh(db_label)
    return db_label

def update_label(db: Session, label_id: UUID, label: ContactLabelUpdate):
    status, db_label =  get_label(db, label_id)
    if not db_label:
        return 404, None
    for key, value in label.dict(exclude_unset=True).items():
        setattr(db_label, key, value)
    db.commit()
    db.refresh(db_label)
    return db_label

def delete_label(db: Session, label_id: UUID):
    status, db_label = get_label(db, label_id)
    if db_label:
        db.delete(db_label)
        db.commit()
        return 200, True
    return 404, False
    