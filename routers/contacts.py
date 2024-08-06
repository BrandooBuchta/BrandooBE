from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas.contacts import ContactCreate, ContactUpdate, Contact as ContactSchema, ContactLabelCreate, ContactLabelUpdate, ContactLabel, UpdateContactLabels, UpdateDescription, FormCreate, Form, FormUpdate
from crud.contacts import get_label, create_label, get_labels, update_label, delete_label, create_form, update_form, delete_form, get_form, get_forms
from crud.contacts import (
    create_contact,
    get_contact,
    get_contacts,
    update_contact,
    delete_contact,
    get_user_by_email,
    verify_user_and_get_contact
)
from utils.security import verify_token
from fastapi.security import OAuth2PasswordBearer
from typing import List
from uuid import UUID
from models.user import User


origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://www.brandoo.cz",
    "https://app.brandoo.cz",
]

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user(db: Session, user_id: UUID):
    return db.query(User).filter(User.id == user_id).first()

@router.post("/new-contact/{form_id}", response_model=ContactSchema)
def create_new_contact(form_id: UUID, request: Request, contact: ContactCreate, db: Session = Depends(get_db)):
    status_code, form = get_form(db, form_id)
    if status_code == 404:
        raise HTTPException(status_code=status_code, detail="Form not found")
    
    user = get_user(db, form.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    request_origin = request.headers.get("origin")
    if not (user.web_url in request_origin or request_origin in origins):
        raise HTTPException(status_code=405, detail="Method not allowed")
    
    new_contact = create_contact(db, contact, user, form_id)
    return new_contact

@router.get("/get-contact/{contact_id}", response_model=ContactSchema)
def get_existing_contact(contact_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, contact = verify_user_and_get_contact(db, contact_id, token)
    if status == 404:
        raise HTTPException(status_code=404, detail="Contact not found")
    if status == 401:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == contact.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    decrypted_contact = get_contact(db, contact_id, user)
    return decrypted_contact

@router.get("/get-contacts/{user_id}", response_model=List[ContactSchema])
def get_existing_contacts(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    contacts = get_contacts(db, user_id, user)
    return contacts

@router.get("/get-unseen-contacts/{user_id}", response_model=int)
def get_existing_contacts(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    contacts = get_contacts(db, user_id, user)
    return len(list(filter(lambda e: not e['has_read_initial_message'], contacts)))

@router.put("/update-contact/{contact_id}", response_model=ContactSchema)
def update_existing_contact(contact_id: UUID, contact: ContactUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, contact_db = verify_user_and_get_contact(db, contact_id, token)
    if status == 404:
        raise HTTPException(status_code=404, detail="Contact not found")
    if status == 401:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == contact_db.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_contact = update_contact(db, contact_id, contact, user)
    if not updated_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated_contact

@router.delete("/delete-contact/{contact_id}")
def delete_existing_contact(contact_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, contact_db = verify_user_and_get_contact(db, contact_id, token)
    if status == 404:
        raise HTTPException(status_code=404, detail="Contact not found")
    if status == 401:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == contact_db.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = delete_contact(db, contact_id, user)
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"detail": "Contact deleted"}

@router.post("/label/{user_id}")
def create_new_label(user_id: UUID, contact_label_create: ContactLabelCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    create_label(db, contact_label_create, user_id)
    return {"detail": "Succcessfuly created new label!"}

@router.get("/label/{label_id}", response_model=ContactLabel)
def get_label_by_id(label_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, label = get_label(db, label_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Label not found")
    if not verify_token(db, label.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return label

@router.get("/labels/{user_id}", response_model=List[ContactLabel])
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

@router.put("/label/{label_id}")
def update_label_by_id(label_id: UUID, new_label: ContactLabelUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, label = get_label(db, label_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Label not found")
    if not verify_token(db, label.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    update_label(db, label_id, new_label)
    return {"detail": "Succcessfuly updated your label!"}

@router.delete("/label/{label_id}")
def delete_label_by_id(label_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, label = get_label(db, label_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Label not found")
    if not verify_token(db, label.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    delete_label(db, label_id)
    return {"detail": "Succcessfuly deleted your label!"}

@router.put("/update-contact-labels/{contact_id}")
def update_labels(contact_id: UUID, body: UpdateContactLabels, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, contact_db = verify_user_and_get_contact(db, contact_id, token)
    if status == 404:
        raise HTTPException(status_code=404, detail="Contact not found")
    if status == 401:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == contact_db.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    labels_dict = {"labels": body.labels}
    
    updated_contact = update_contact(db, contact_id, labels_dict, user)
    if not updated_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return {"detail": "Success"}

@router.put("/update-contact-description/{contact_id}")
def update_description(contact_id: UUID, body: UpdateDescription, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, contact_db = verify_user_and_get_contact(db, contact_id, token)
    if status == 404:
        raise HTTPException(status_code=404, detail="Contact not found")
    if status == 401:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == contact_db.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    desc_dict = {"description": body.description}

    updated_contact = update_contact(db, contact_id, desc_dict, user)
    if not updated_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"detail": "Success"}

@router.put("/has-read-initial-message/{contact_id}")
def update_description(contact_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, contact_db = verify_user_and_get_contact(db, contact_id, token)
    if status == 404:
        raise HTTPException(status_code=404, detail="Contact not found")
    if status == 401:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == contact_db.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    desc_dict = {"has_read_initial_message": True}

    updated_contact = update_contact(db, contact_id, desc_dict, user)
    if not updated_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"detail": "Success"}

@router.post("/form/{user_id}")
def create_new_form(user_id: UUID, form: FormCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    create_form(db, form, user_id)
    return {"detail": "Succcessfuly created new form!"}

@router.get("/form/{form_id}", response_model=Form)
def get_form_by_id(form_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, form = get_form(db, form_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Label not found")
    if not verify_token(db, form.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return form

@router.get("/forms/{user_id}", response_model=List[Form])
def get_form_by_user_id(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    status, forms = get_forms(db, user_id)
    if status == 404:
        return []
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return forms

@router.put("/form/{form_id}")
def update_form_by_id(form_id: UUID, form_to_update: FormUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, form = get_form(db, form_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Form not found")
    if not verify_token(db, form.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    update_form(db, form_id, form_to_update)
    return {"detail": "Succcessfuly updated your form!"}

@router.delete("/form/{form_id}")
def delete_form_by_id(form_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, form = get_form(db, form_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Form not found")
    if not verify_token(db, form.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    delete_form(db, form_id)
    return {"detail": "Succcessfuly deleted your form!"}

@router.get("/terms-and-conditions/{form_id}")
def get_terms_and_conditions(form_id: UUID, db: Session = Depends(get_db)):
    status, form = get_form(db, form_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Form not found")    
    user = get_user(db, form.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")    
    return {
        "registration_no": user.registration_no,
        "contact_email": user.contact_email,
        "contact_phone": user.contact_phone,
        "form_properties": form.form_properties
    }

@router.get("/form-info/{form_id}")
def get_terms_and_conditions(form_id: UUID, db: Session = Depends(get_db)):
    status, form = get_form(db, form_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Form not found")    
    return {
        "form_properties": form.form_properties,
        "name": form.name,
        "description": form.description,
    }