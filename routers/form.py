# routers/form.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import desc
from database import SessionLocal
from utils.security import verify_token, rsa_decrypt_data, decrypt_private_key_for_fe
from utils.email import send_free_subscription_on_month_email, send_form_for_our_services
from fastapi.security import OAuth2PasswordBearer
from schemas.form import CreateForm, FormModel, FormModelPublic, UpdateForm, FormWithoutProperties, FormResponseMessagePublic, FormResponseMessageCreate, FormResponseMessageUpdate, UpdateContactLabels, FormPropertyManageModel, TermsAndConditions, PublicOptions
from crud.form import create_form, get_form, update_form, delete_form, get_users_form_menu, create_response, get_response_by_id, get_plain_response, update_response, create_form_response_message, get_messages_by_response_id, update_form_response_message, count_unseen_responses_by_user_id, delete_response, get_property
from crud.user import get_user, create_code_for_new_user
from models.form import Form
from uuid import UUID
from typing import List, Optional
from models.form import FormResponse, FormValue
from fastapi import Query
from datetime import datetime
from sqlalchemy.orm import selectinload
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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_optional_token(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    return token

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

@router.post("/create-form/{user_id}", response_model=FormModel)
def create_new_form(user_id: UUID, form: CreateForm, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        if not verify_token(db, user_id, token):
            raise HTTPException(status_code=401, detail="Unauthorized")

        form = create_form(db, form, user_id)

        initial_properties = [
            {
                "key": "email", 
                "property_type": "short_text", 
                "position": 1, 
                "label": "Email", 
                "required": True
            },
            {
                "key": "privacyPolicy", 
                "property_type": "boolean", 
                "position": 2, 
                "label": "Souhlasím s podmínkami zpracování osobních údajů", 
                "required": True
            }
        ]
        
        update_form_data = UpdateForm(
            properties=[FormPropertyManageModel(**prop) for prop in initial_properties]
        )
        update_form(db, form.id, update_form_data)
        
        return form
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")


@router.get("/get-form/{form_id}", response_model=FormModel)
def get_form_by_id(form_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    form = get_form(db, form_id)

    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    if not verify_token(db, form.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return form
    
@router.get("/get-public-form/{form_id}", response_model=FormModelPublic)
def get_form_by_id(form_id: UUID, db: Session = Depends(get_db)):
    form = get_form(db, form_id)
    
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return form
    
@router.put("/update-form/{form_id}", response_model=FormModel)
def update_existing_form(form_id: UUID, update_data: UpdateForm, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        form = update_form(db, form_id, update_data)
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        return form
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")

@router.delete("/delete-form/{form_id}")
def remove_form(form_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        delete_form(db, form_id)
        return {"message": "Form deleted successfully"}
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")

@router.get("/get-users-forms/{user_id}", response_model=List[FormWithoutProperties])
def get_users_forms_menu(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    forms = get_users_form_menu(db, user_id)
    if not forms:
        raise HTTPException(status_code=404, detail="Unauthorized")

    return forms

@router.post("/create-response/{form_id}")
async def create_form_response(
    form_id: UUID, 
    request: Request, 
    token: Optional[str] = Depends(get_optional_token),
    db: Session = Depends(get_db)
):
    form = get_form(db, form_id)
    user = get_user(db, form.user_id)

    request_origin = request.headers.get("origin")

    if request_origin and "localhost" in request_origin:
        if not verify_token(db, user.id, token):
            raise HTTPException(status_code=401, detail="Unauthorized for localhost")

    elif request_origin not in origins and request_origin != f"https://{user.web_url}":
        raise HTTPException(status_code=403, detail="Forbidden: Origin not allowed")

    try:
        data = await request.json()
        create_response(db, form_id, data)

        # if str(form_id) == "2aa1a8f2-a82d-4d8f-94b4-dd97abce4981":
        #     send_free_subscription_on_month_email(data['email'], create_code_for_new_user(db, "1"))

        if str(form_id) == "5893c160-908e-4f3e-ab51-5a574aa5da70":
            send_form_for_our_services(data['email'])

        return {"message": "Successfully created a response"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/property/options/{property_id}", response_model=PublicOptions)
async def get_form_property_options(
    property_id: UUID, 
    request: Request, 
    token: Optional[str] = Depends(get_optional_token),
    db: Session = Depends(get_db)
):
    prop, status = get_property(db, property_id)
    form = get_form(db, prop.form_id)
    user = get_user(db, form.user_id)

    request_origin = request.headers.get("origin")

    if request_origin and "localhost" in request_origin:
        if not verify_token(db, user.id, token):
            raise HTTPException(status_code=401, detail="Unauthorized for localhost")

    elif request_origin not in origins and request_origin != f"https://{user.web_url}":
        raise HTTPException(status_code=403, detail="Forbidden: Origin not allowed")

    return PublicOptions(
        options=prop.options,
        property_name=prop.label,
        form_name=form.name
    )

@router.delete("/delete-response/{response_id}")
def delete_form_response(response_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        db_response, status = get_plain_response(db, response_id)
        if status == 404:
            raise HTTPException(status_code=404, detail="Response not found")

        if not verify_token(db, db_response.user_id, token):
            raise HTTPException(status_code=401, detail="Unauthorized")

        deleted_response = delete_response(db, response_id)
        if not deleted_response:
            raise HTTPException(status_code=404, detail="Response not found")

        return {"message": "Response deleted successfully"}
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")

@router.get("/get-response/{response_id}")
def get_form_response(response_id: UUID, request: Request, db: Session = Depends(get_db)):
    try:
        private_key = request.headers.get("X-Private-Key")
        if not private_key:
            raise HTTPException(status_code=400, detail="Missing X-Private-Key header")

        decrypted_response = get_response_by_id(db, response_id, decrypt_private_key_for_fe(private_key))
        return decrypted_response
    except HTTPException as e:
        raise e
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")

@router.get("/form-table/{form_id}")
async def get_form_table(
    form_id: UUID, 
    request: Request, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number to retrieve"),
    per_page: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search_query: Optional[str] = Query(None, description="Search query to filter responses"),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc")
):
    try:
        private_key = request.headers.get("X-Private-Key")
        if not private_key:
            raise HTTPException(status_code=400, detail="Missing X-Private-Key header")

        form = get_form(db, form_id)
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")

        query = db.query(FormResponse).filter(FormResponse.form_id == form_id)

        if search_query:
            query = query.filter(
                FormResponse.some_field.ilike(f"%{search_query}%")
            )

        if sort_by == "created_at":
            query = query.order_by(FormResponse.created_at.asc() if sort_order == "asc" else FormResponse.created_at.desc())

        total_responses = query.count()

        responses = query.offset((page - 1) * per_page).limit(per_page).all()

        decrypted_responses = []
        for response in responses:
            decrypted_response = get_response_by_id(db, response.id, decrypt_private_key_for_fe(private_key))
            decrypted_responses.append((response, decrypted_response))

        header = [
            {"key": prop.key, "label": prop.label, "position": prop.position, "property_type": prop.property_type}
            for prop in sorted(form.properties, key=lambda x: x.position)
        ]

        header += [
            {"key": "labels", "label": "Labels", "position": len(header) + 1, "property_type": "labels"},
            {"key": "createdAt", "label": "Vytvořeno", "position": len(header) + 3, "property_type": "date_time"}
        ]

        body = []
        for response, decrypted_response in decrypted_responses:
            row = {header_item["key"]: decrypted_response.get(header_item["key"], None) for header_item in header}
            row["labels"] = response.labels
            row["seen"] = response.seen
            row["created_at"] = response.created_at.isoformat()
            row["id"] = response.id
            
            body.append(row)

        return {
            "table": {
                "header": header, 
                "body": body
            },
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_pages": (total_responses + per_page - 1) // per_page,
                "total_items": total_responses
            }
        }

    except HTTPException as e:
        raise e
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")

@router.get("/users-forms-table/{user_id}")
async def get_users_forms_table(
    user_id: UUID, 
    request: Request, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number to retrieve"),
    per_page: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search_query: Optional[str] = Query(None, description="Search query to filter responses"),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc")
):
    try:
        private_key = request.headers.get("X-Private-Key")
        if not private_key:
            raise HTTPException(status_code=400, detail="Missing X-Private-Key header")

        forms = db.query(Form).filter(Form.user_id == user_id).options(selectinload(Form.properties)).all()

        if not forms:
            raise HTTPException(status_code=404, detail="No forms found for user")

        responses_query = db.query(FormResponse).filter(FormResponse.form_id.in_([f.id for f in forms]))

        if sort_by == "created_at":
            responses_query = responses_query.order_by(
                FormResponse.created_at.asc() if sort_order == "asc" else FormResponse.created_at.desc()
            )

        responses = responses_query.offset((page - 1) * per_page).limit(per_page).all()

        decrypted_responses = []
        for response in responses:
            decrypted_data = get_response_by_id(db, response.id, decrypt_private_key_for_fe(private_key))
            decrypted_responses.append((response, decrypted_data))

        filtered_responses = []
        for response, decrypted_response in decrypted_responses:
            if not search_query or any(search_query.lower() in str(value).lower() for value in decrypted_response.values()):
                filtered_responses.append((response, decrypted_response))

        common_keys = set(decrypted_responses[0][1].keys()) if decrypted_responses else set()
        for _, decrypted_response in decrypted_responses:
            common_keys.intersection_update(decrypted_response.keys())

        header = []
        for idx, key in enumerate(common_keys):
            form_property = next((prop for prop in forms[0].properties if prop.key == key), None)
            label = form_property.label if form_property else key  # Fallback to key if no matching property
            property_type = form_property.property_type if form_property else 'unknown'
            header.append({"key": key, "label": label, "position": idx + 1, "property_type": property_type})

        header += [
            {"key": "labels", "label": "Labels", "position": len(header) + 1, "property_type": "labels"},
            {"key": "createdAt", "label": "Vytvořeno", "position": len(header) + 2, "property_type": "date_time"}
        ]

        body = []
        for response, decrypted_response in filtered_responses:
            row = {key: decrypted_response.get(key, None) for key in common_keys}
            row["labels"] = response.labels
            row["seen"] = response.seen
            row["created_at"] = response.created_at.isoformat()
            row["id"] = response.id
            body.append(row)

        total_responses = len(filtered_responses)
        total_pages = (total_responses + per_page - 1) // per_page

        return {
            "table": {
                "header": header, 
                "body": body
            },
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_items": total_responses
            }
        }

    except HTTPException as e:
        raise e
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")

@router.get("/get-single-response/{response_id}")
def get_single_response(response_id: UUID, request: Request, db: Session = Depends(get_db)):
    try:
        private_key = request.headers.get("X-Private-Key")
        if not private_key:
            raise HTTPException(status_code=400, detail="Missing X-Private-Key header")

        decrypted_response = get_response_by_id(db, response_id, decrypt_private_key_for_fe(private_key))
        
        if not decrypted_response:
            raise HTTPException(status_code=404, detail="Response not found")

        response = db.query(FormResponse).filter(FormResponse.id == response_id).first()
        if not response:
            raise HTTPException(status_code=404, detail="Form response not found")

        form = response.form
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")

        # Adding labels, created_at, and property_type to the formatted response
        formatted_response = []
        for key, value in decrypted_response.items():
            form_property = next((prop for prop in form.properties if prop.key == key), None)
            if form_property:
                label = form_property.label
                property_type = form_property.property_type
                formatted_response.append({"label": label, "value": value, "property_type": property_type})

        return {
            "id": response_id,
            "alias": response.alias or None,
            "labels": response.labels,
            "createdAt": response.created_at.isoformat(),
            "response": formatted_response
        }

    except HTTPException as e:
        raise e
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection failed, please try again later")

@router.put("/update-contact-labels/{response_id}")
def update_labels(response_id: UUID, body: UpdateContactLabels, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_response, status = get_plain_response(db, response_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Response not found")

    if not verify_token(db, db_response.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    updated_response = update_response(db, response_id, {"labels": body.labels})
    if not updated_response:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return {"detail": "Success"}

@router.put("/user-has-seen-response/{response_id}")
def user_has_seen_response(response_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_response, status = get_plain_response(db, response_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Response not found")

    if not verify_token(db, db_response.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    updated_response = update_response(db, response_id, {"seen": True})
    if not updated_response:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return {"detail": "Success"}

@router.put("/update-response-alias/{response_id}")
def user_has_seen_response(response_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), alias: str = Query(None)):
    db_response, status = get_plain_response(db, response_id)
    if status == 404:
        raise HTTPException(status_code=404, detail="Response not found")

    if not verify_token(db, db_response.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    updated_response = update_response(db, response_id, {"alias": alias})
    if not updated_response:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return {"detail": "Success"}

@router.post("/form-response-message", response_model=FormResponseMessagePublic)
def create_message(message_data: FormResponseMessageCreate, db: Session = Depends(get_db)):
    message = create_form_response_message(db, message_data)
    return message

@router.put("/form-response-message/{message_id}", response_model=FormResponseMessagePublic)
def update_message(message_id: UUID, update_data: FormResponseMessageUpdate, db: Session = Depends(get_db)):
    updated_message = update_form_response_message(db, message_id, update_data)
    return updated_message

@router.get("/form-response-messages/{response_id}", response_model=List[FormResponseMessagePublic])
def get_messages(response_id: UUID, request: Request, db: Session = Depends(get_db)):
    messages = get_messages_by_response_id(db, response_id)

    private_key = request.headers.get("X-Private-Key")
    if not private_key:
        raise HTTPException(status_code=400, detail="Missing X-Private-Key header")
    
    if not messages:
        return []

    decrypted_messages = []

    for m in messages:
        m_dict = m.__dict__
        m_dict.pop("_sa_instance_state", None)

        decrypted_messages.append({
            **m_dict,
            "message": rsa_decrypt_data(m.message, decrypt_private_key_for_fe(private_key))
        })

    return decrypted_messages

@router.get("/unseen-responses/{user_id}", response_model=int)
def count_unseen_responses_user(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    unseen_count = count_unseen_responses_by_user_id(db, user_id)
    
    return unseen_count

@router.get("/terms-and-conditions/{form_id}", response_model=TermsAndConditions)
def count_unseen_responses_user(form_id: UUID, db: Session = Depends(get_db)):
    form = get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    user = get_user(db, form.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    props = []

    for prop in form.properties:
        props.append(prop.label)
    
    return TermsAndConditions(
        contact_email=user.contact_email,
        contact_phone=user.contact_phone,
        registration_no=user.registration_no,
        form_properties=props
    )

