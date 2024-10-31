# routers/statistics.py

import random
from fastapi import APIRouter, Depends, HTTPException, Request, Depends, Query
from sqlalchemy.orm import Session, joinedload
from database import SessionLocal
from schemas.statistics import StatisticCreate, StatisticUpdate, StatisticValueCreate, Statistic as StatisticSchema, StatisticValue as StatisticValueSchema
from crud.statistics import create_statistic, get_statistic, get_user_statistics, update_statistic, delete_statistic, create_statistic_value, delete_statistic_value, get_statistic_type, reset_statistic, get_aggregated_statistic_value, reset_user_statistics
from utils.security import verify_token
from uuid import UUID
from fastapi.security import OAuth2PasswordBearer
from models.statistics import Statistic, StatisticValue
from models.user import User
from typing import List, Optional
from datetime import datetime, timedelta

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "https://www.brandoo.cz",
    "https://app.brandoo.cz",
    "https://api.brandoo.cz",
    "https://dev.api.brandoo.cz",
    "https://dev.app.brandoo.cz",
]

def get_user(db: Session, user_id: UUID):
    return db.query(User).filter(User.id == user_id).first()

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

@router.post("/new-statistic/{user_id}", response_model=StatisticSchema)
def create_new_statistic(user_id: UUID, statistic: StatisticCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    new_statistic = create_statistic(db, statistic, user_id)
    return new_statistic

@router.get("/get-statistic/{statistic_id}", response_model=StatisticSchema)
def read_statistic(statistic_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    statistic = db.query(Statistic).options(joinedload(Statistic.values)).filter(Statistic.id == statistic_id).first()

    if not statistic:
        raise HTTPException(status_code=404, detail="Statistic not found")

    if not verify_token(db, statistic.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return statistic

@router.get("/get-users-statistics/{user_id}", response_model=List[StatisticSchema])
def read_user_statistics(
    user_id: UUID, 
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db),
    searchQuery: Optional[str] = Query(None, alias="searchQuery")
):
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    query = db.query(Statistic).options(joinedload(Statistic.values)).filter(Statistic.user_id == user_id)
    
    if searchQuery:
        query = query.filter(Statistic.name.ilike(f"%{searchQuery}%"))
    
    statistics = query.all()
    return statistics

@router.delete("/delete-statistic/{statistic_id}")
def remove_statistic(statistic_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    statistic = get_statistic(db, statistic_id)
    if not statistic:
        raise HTTPException(status_code=404, detail="Statistic not found")

    if not verify_token(db, statistic.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    delete_statistic(db, statistic_id)
    return {"detail": "Statistic deleted"}

@router.put("/update-statistic/{statistic_id}", response_model=StatisticSchema)
def modify_statistic(statistic_id: UUID, statistic: StatisticUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_statistic = get_statistic(db, statistic_id)
    if not db_statistic:
        raise HTTPException(status_code=404, detail="Statistic not found")
    
    if not verify_token(db, db_statistic.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    updated_statistic = update_statistic(db, statistic_id, statistic)
    return updated_statistic

@router.post("/value/{statistic_id}", response_model=StatisticValueSchema)
def add_statistic_value(
    statistic_id: UUID, 
    request: Request, 
    value: StatisticValueCreate, 
    token: Optional[str] = Depends(get_optional_token),
    db: Session = Depends(get_db)
):
    statistic_type = get_statistic_type(db, statistic_id)
    if not statistic_type:
        raise HTTPException(status_code=404, detail="Statistic not found")

    statistic = get_statistic(db, statistic_id)
    if not statistic:
        raise HTTPException(status_code=404, detail="Statistic not found")

    user = get_user(db, statistic.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    request_origin = request.headers.get("origin")

    if request_origin and "localhost" in request_origin:
        if not verify_token(db, user.id, token):
            raise HTTPException(status_code=401, detail="Unauthorized for localhost")

    elif request_origin not in origins and request_origin != f"https://{user.web_url}":
        raise HTTPException(status_code=403, detail="Forbidden: Origin not allowed")

    if statistic_type == "number" and value.number is not None:
        new_value = create_statistic_value(db, statistic_id, value)
    elif statistic_type == "boolean" and value.boolean is not None:
        new_value = create_statistic_value(db, statistic_id, value)
    elif statistic_type == "text" and value.text is not None:
        new_value = create_statistic_value(db, statistic_id, value)
    elif statistic_type == "time" and value.time is not None:
        new_value = create_statistic_value(db, statistic_id, value)
    else:
        raise HTTPException(status_code=400, detail="Invalid value for statistic type")

    return new_value

@router.get("/value/{statistic_id}")
def get_statistic_value(
    statistic_id: UUID, 
    request: Request, 
    token: Optional[str] = Depends(get_optional_token),
    db: Session = Depends(get_db)
):
    statistic = get_statistic(db, statistic_id)
    if not statistic:
        raise HTTPException(status_code=404, detail="Statistic not found")

    user = get_user(db, statistic.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    request_origin = request.headers.get("origin")

    if request_origin and "localhost" in request_origin:
        if not verify_token(db, user.id, token):
            raise HTTPException(status_code=401, detail="Unauthorized for localhost")

    elif request_origin not in origins and request_origin != f"https://{user.web_url}":
        raise HTTPException(status_code=403, detail="Forbidden: Origin not allowed")

    result = get_aggregated_statistic_value(db, statistic_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Statistic not found or invalid type.")
    return result

@router.post("/delete-statistic-value/{statistic_id}")
def remove_statistic_value(statistic_id: UUID, db: Session = Depends(get_db)):
    if not delete_statistic_value(db, statistic_id):
        raise HTTPException(status_code=404, detail="Statistic value not found")
    return {"detail": "Statistic value deleted"}

@router.delete("/reset/{statistic_id}")
def read_user_statistics(statistic_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    statistic = get_statistic(db, statistic_id)
    if not verify_token(db, statistic.user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    reset_statistic(db, statistic_id)
    return { "detail": "Successfully reseted statistic." }

@router.delete("/reset-user-statistics/{user_id}")
def reset_user_statistics_endpoint(
    user_id: UUID, 
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    reset_user_statistics(db, user_id)
    return {"detail": "Successfully reset all statistics for the user."}

@router.get("/random-statistics/{user_id}", response_model=List[StatisticSchema])
def get_random_statistics(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    one_week_ago = datetime.now() - timedelta(weeks=1)

    statistics = db.query(Statistic).join(Statistic.values).filter(Statistic.user_id == user_id, StatisticValue.created_at >= one_week_ago).all()
    
    if not statistics:
        return []


    if len(statistics) == 0:
        raise HTTPException(status_code=404, detail="No statistics found for this week.")
    
    random_statistics = random.sample(statistics, min(len(statistics), 3))

    return random_statistics

