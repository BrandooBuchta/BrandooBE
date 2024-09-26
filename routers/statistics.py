from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload
from database import SessionLocal
from schemas.statistics import StatisticCreate, StatisticUpdate, StatisticValueCreate, Statistic as StatisticSchema, StatisticValue as StatisticValueSchema
from crud.statistics import create_statistic, get_statistic, get_user_statistics, update_statistic, delete_statistic, create_statistic_value, delete_statistic_value, get_statistic_type, reset_statistic
from utils.security import verify_token
from uuid import UUID
from fastapi.security import OAuth2PasswordBearer
from models.statistics import Statistic
from models.user import User

def get_user(db: Session, user_id: UUID):
    return db.query(User).filter(User.id == user_id).first()

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_user_via_token(db: Session, user_id: UUID, token: str):
    if not verify_token(db, user_id, token):
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/new-statistic/{user_id}", response_model=StatisticSchema)
def create_new_statistic(user_id: UUID, statistic: StatisticCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    verify_user_via_token(db, user_id, token)
    new_statistic = create_statistic(db, statistic, user_id)
    return new_statistic

@router.get("/get-statistic/{statistic_id}", response_model=StatisticSchema)
def read_statistic(statistic_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    statistic = db.query(Statistic).options(joinedload(Statistic.values)).filter(Statistic.id == statistic_id).first()
    if not statistic:
        raise HTTPException(status_code=404, detail="Statistic not found")
    return statistic

@router.get("/get-users-statistics/{user_id}", response_model=list[StatisticSchema])
def read_user_statistics(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    verify_user_via_token(db, user_id, token)
    statistics = db.query(Statistic).options(joinedload(Statistic.values)).filter(Statistic.user_id == user_id).all()
    return statistics

@router.delete("/delete-statistic/{statistic_id}")
def remove_statistic(statistic_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    statistic = get_statistic(db, statistic_id)
    if not statistic:
        raise HTTPException(status_code=404, detail="Statistic not found")
    verify_user_via_token(db, statistic.user_id, token)
    delete_statistic(db, statistic_id)
    return {"detail": "Statistic deleted"}

@router.put("/update-statistic/{statistic_id}", response_model=StatisticSchema)
def modify_statistic(statistic_id: UUID, statistic: StatisticUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_statistic = get_statistic(db, statistic_id)
    if not db_statistic:
        raise HTTPException(status_code=404, detail="Statistic not found")
    verify_user_via_token(db, db_statistic.user_id, token)
    updated_statistic = update_statistic(db, statistic_id, statistic)
    return updated_statistic

# TODO: Test it
@router.post("/value/{statistic_id}", response_model=StatisticValueSchema)
def add_statistic_value(statistic_id: UUID, request: Request, value: StatisticValueCreate, db: Session = Depends(get_db)):
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
    if request_origin not in origins and request_origin != f"https://{user.web_url}" and request_origin != f"http://{user.web_url}":
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