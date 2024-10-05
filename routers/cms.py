# routers/csm.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import SessionLocal
from utils.security import verify_token
from fastapi.security import OAuth2PasswordBearer
from crud.cms import (
    create_root_content, 
    get_root_content, 
    update_root_content, 
    delete_root_content,
    get_users_root_contents,
    update_content,
    get_content,
    create_new_item_property,
    update_property,
    create_empty_list_item_property_at_index,
    add_property_to_list_item_content_at_index,
    reorder_list_item_content_in_db,
    delete_property_from_content,
    get_root_public_content,
    delete_item_from_list_item_content
)
from schemas.cms import RootContentLight, ContentUpdate, BaseContent, ContentWithProperties, ReorderRequest
from fastapi import Query
from typing import List
from crud.user import get_user
from fastapi import HTTPException

from uuid import UUID

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/root/{user_id}")
def post_root_content(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    create_root_content(db, user_id)
    return {"detail": "Succcessfuly created root content!"}

@router.put("/root/{content_id}")
def put_root_content(content_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), alias: str = Query(None)):
    content, status = get_root_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    update_root_content(db, content_id, alias)
    return {"detail": "Succcessfuly updated root content!"}

@router.delete("/root/{content_id}")
def remove_root_content(content_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content, status = get_root_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    delete_root_content(db, content_id)
    return {"detail": "Successfully deleted root content!"}

@router.get("/root/users/{user_id}", response_model=List[RootContentLight])
def fetch_users_root_contents(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), alias: str = Query(None)):
    contents, status = get_users_root_contents(db, user_id)
    
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if status == 404:
        return []
    
    root_content_light_list = [RootContentLight(id=str(content.id), alias=content.alias, is_root=content.is_root) for content in contents]
    
    return root_content_light_list

@router.put("/{content_id}")
def put_content(content_id: UUID, content_to_update: ContentUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content, status = get_root_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    update_content(db, content_id, content_to_update)
    return {"detail": "Succcessfuly updated root content!"}

@router.get("/{content_id}", response_model=ContentWithProperties)
def get_content_ep(content_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content = get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return content

@router.post("/property/{content_id}/{root_id}")
def create_property(content_id: UUID, root_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content = get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    prop, status = create_new_item_property(db, content_id, root_id)

    return {"detail": "Succesfully created new property!"}

@router.put("/property/{property_id}")
def update_property_endpoint(
    property_id: UUID, 
    token: str = Depends(oauth2_scheme), 
    key: str = Query(None), 
    db: Session = Depends(get_db)
):
    prop, status = update_property(db, property_id, key)

    if status == 404:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if not verify_token(db, prop.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return {"detail": "Successfully updated property"}

@router.post("/list_item_content/{content_id}")
def create_empty_list_item_content(content_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content = get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    status = initialize_empty_list_item_content(db, content_id)
    
    if status == 200:
        return {"detail": "Successfully created new empty list item content!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to create new list item content")

@router.post("/list-item-content/{content_id}")
def create_empty_list_item_content(content_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content = get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    status = create_empty_list_item_property_at_index(db, content_id)

    if status == 200:
        return {"detail": "Successfully created new empty list item content!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to create new list item content")

@router.post("/list-item-content/{content_id}/{index}/{root_id}/property")
def add_property_to_list_item_content(content_id: UUID, root_id: UUID, index: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content = get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    status = add_property_to_list_item_content_at_index(db, content_id, index, root_id)

    if status == 200:
        return {"detail": "Successfully added new property to list item content!"}
    elif status == 400:
        raise HTTPException(status_code=400, detail="Index out of range or list_item_content does not exist")
    else:
        raise HTTPException(status_code=500, detail="Failed to add property to list item content")

@router.delete("/list-item-content/{content_id}/{index}")
def delete_property_from_list_item(content_id: UUID, index: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content = get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    status, message = delete_item_from_list_item_content(db, content_id, index)

    if status == 200:
        return {"detail": "Successfully added new property to list item content!"}
    elif status == 400:
        raise HTTPException(status_code=400, detail="Index out of range or list_item_content does not exist")
    else:
        raise HTTPException(status_code=500, detail="Failed to add property to list item content")

@router.put("/list-item-content/{content_id}/reorder")
def reorder_list_item_content(content_id: UUID, request: ReorderRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content = get_content(db, content_id)
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Extrahuj new_order z requestu
    new_order = request.new_order
    
    status = reorder_list_item_content_in_db(db, content_id, new_order)
    
    if status == 200:
        return {"detail": "Successfully reordered list item content!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reorder list item content")

@router.get("/{content_id}/public")
def get_root_content_endpoint(content_id: UUID, request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content = get_root_public_content(db, content_id)
    raw_content = get_content(db, content_id)
    user = get_user(db, raw_content.user_id)

    request_origin = request.headers.get("origin")
    if request_origin and "localhost" in request_origin:
        if not verify_token(db, user.id, token):
            raise HTTPException(status_code=401, detail="Unauthorized for localhost")

    elif request_origin not in origins and request_origin != f"https://{user.web_url}" and request_origin != f"http://{user.web_url}":
        raise HTTPException(status_code=403, detail="Forbidden: Origin not allowed")

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return content

@router.delete("/{content_id}/property/{property_id}")
def delete_item_property(content_id: UUID, property_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    content = get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if not verify_token(db, content.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    deleted_property = delete_property_from_content(db, content_id, property_id)
    
    if deleted_property == 200:
        return { "detail": "Successfully deleted property" }
