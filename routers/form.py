# routers/form.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas.form import CreateFormRequest, CreateForm, CreateFormPropertiesRequest, FormPropertyCRUDModelOptional, CreateFormResponseRequest
from crud.form import create_form, get_form, create_form_property, update_form, delete_form, update_form_property, get_form_property, delete_form_property, create_response
from utils.security import verify_token
from fastapi.security import OAuth2PasswordBearer
from uuid import UUID
from typing import Optional, List
from datetime import datetime

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

@router.post("/create-form/{user_id}", response_model=CreateForm)
def create_new_form(user_id: UUID, form: CreateFormRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    form = create_form(db, form, user_id)

    return form

@router.put("/update-form/{form_id}", response_model=CreateForm)
def update_current_form(form_id: UUID, form: CreateFormRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    form = update_form(db, form_id, form)

    return form

@router.delete("/delete-form/{form_id}")
def update_current_form(form_id: UUID, form: CreateFormRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    delete_form(db, form_id)

    return { "detail": "Successfuly deleted form!" }

@router.get("/get-form-with-properties/{form_id}", response_model=CreateForm)
def update_current_form(form_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    form = db.query(Form).options(joinedload(Form.properties)).filter(Form.id == form_id).first()

    if not verify_token(db, form.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return form

@router.post("/create-form-properties")
def create_new_form_properties(form_properties_request: CreateFormPropertiesRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not verify_token(db, form_properties_request.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    for prop in form_properties_request.properties:
        create_form_property(db, prop, form_properties_request.user_id, form_properties_request.user_id)
    
    return { "detail": "Successfully created new properties!" }

@router.put("/update-form-property/{property_id}")
def update_current_form_property(property_id: UUID, updated_form_property: FormPropertyCRUDModelOptional, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, form_property = get_form_property(db, property_id)
    if not verify_token(db, form_property.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    update_form_property(db, updated_form_property, property_id)
    
    return { "detail": "Successfully updated form property!" }


@router.delete("/delete-form-property/{property_id}")
def delete_current_form_property(property_id: UUID, updated_form_property: FormPropertyCRUDModelOptional, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    status, form_property = get_form_property(db, property_id)
    if not verify_token(db, form_property.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    update_form_property(db, updated_form_property, property_id)
    
    return { "detail": "Successfully updated form property!" }

@router.post("/new-response/{form_id}")
def create_new_response(form_id: UUID, request: Request, body: CreateFormResponseRequest, db: Session = Depends(get_db)):
    status_code, form = get_form(db, form_id)
    if status_code == 404:
        raise HTTPException(status_code=status_code, detail="Form not found")
    
    user = get_user(db, form.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    request_origin = request.headers.get("origin")
    if not (user.web_url in request_origin or request_origin in origins):
        raise HTTPException(status_code=405, detail="Method not allowed")
    
    new_response = create_response(db, form_id, body.values)


@router.get("/get-form-with-responses/{form_id}", response_model=CreateForm)
def get_form_with_responses(
    form_id: UUID,
    db: Session = Depends(get_db),
    label_ids: Optional[List[UUID]] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query('asc'),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search_query: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 10,
):
    form = db.query(Form).options(joinedload(Form.properties), joinedload(Form.responses)).filter(Form.id == form_id).first()

    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Sort form properties by position
    form_properties = [
        { "key": prop.key, "label": prop.label }
        for prop in sorted(form.properties, key=lambda p: p.position)
    ]
    
    # Add additional properties
    form_properties.extend([
        { "key": "labels", "label": "Štítky" },
        { "key": "created_at", "label": "Vytvořeno" },
        { "key": "seen", "label": "Zobrazeno" }
    ])

    # Filter and sort responses
    responses_query = db.query(FormResponse).filter(FormResponse.form_id == form_id)

    if label_ids:
        responses_query = responses_query.filter(FormResponse.labels.any(label_ids))

    if date_from:
        responses_query = responses_query.filter(FormResponse.created_at >= date_from)

    if date_to:
        responses_query = responses_query.filter(FormResponse.created_at <= date_to)

    if search_query:
        search_query = f"%{search_query}%"
        responses_query = responses_query.filter(
            FormResponse.id.in_(
                db.query(FormProperty.id).filter(
                    FormProperty.form_id == form_id,
                    FormProperty.key.ilike(search_query)
                )
            )
        )

    if sort_by:
        sort_column = getattr(FormResponse, sort_by)
        if sort_order == 'desc':
            sort_column = sort_column.desc()
        responses_query = responses_query.order_by(sort_column)

    total_responses = responses_query.count()

    responses = responses_query.offset((page - 1) * page_size).limit(page_size).all()

    # Create the form_responses list with additional fields
    form_responses = []
    for response in responses:
        values = {value.property_key: value.short_text for value in db.query(FormProperty).filter(FormProperty.form_id == form_id).all()}
        values.update({
            "labels": response.labels,
            "created_at": response.created_at,
            "seen": response.seen,
        })
        form_responses.append(values)

    result = {
        "name": form.name,
        "description": form.description,
        "form_properties": form_properties,
        "form_responses": form_responses,
        "total": total_responses,
        "page": page,
        "page_size": page_size
    }

    return result