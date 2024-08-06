from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas.user import UserCreate, UserUpdate, Token, CodeVerification, PasswordReset, auth_tokenRequest, auth_tokenResponse, User as UserSchema, UserSignIn
from crud.user import create_user, get_user, get_user_by_email, update_user, delete_user, create_token_via_id, create_token_via_access_token, create_code, verify_code, update_password, get_token
from utils.security import verify_password, create_access_token, verify_token
from utils.email import send_verification_email, send_reset_email
from uuid import UUID
from fastapi.security import OAuth2PasswordBearer
from models.user import Token as TokenModel

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

@router.post("/create", response_model=UserSchema)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, user)
    token = create_token_via_id(db, new_user.id)
    return new_user

@router.delete("/delete/{user_id}")
def delete_existing_user(user_id: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    verify_user_via_token(db, user_id, token)
    delete_user(db, user_id)
    return {"detail": "User deleted"}

@router.put("/update/{user_id}", response_model=UserSchema)
def update_existing_user(user_id: UUID, user: UserUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    verify_user_via_token(db, user_id, token)
    updated_user = update_user(db, user_id, user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.post("/sign-in", response_model=Token)
def sign_in_user(sign_in_data: UserSignIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, sign_in_data.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not db_user or not verify_password(sign_in_data.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = get_token(db, db_user.id)
    token = create_token_via_access_token(db, access_token.constant_access_token)
    return {"token": token, "user": db_user}

@router.post("/start-verification/{user_id}")
def start_verification(user_id: UUID, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    verification_code = create_code(db, user_id, "verification")
    send_verification_email(db_user.email, verification_code.code)
    return {"detail": "Verification email sent"}

@router.post("/finish-verification/{user_id}", response_model=UserSchema)
def finish_verification(user_id: UUID, code: CodeVerification, db: Session = Depends(get_db)):
    if not verify_code(db, user_id, code.code):
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    db_user = get_user(db, user_id) 
    db_user.is_verified = True
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/password-reset/start")
def start_password_reset(email: str, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    reset_code = create_code(db, db_user.id, "reset")
    send_reset_email(db_user.email, reset_code.code)
    return {"detail": "Password reset email sent"}

@router.post("/password-reset/code-verification")
def verify_reset_code(code: str, email: str, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email)
    if not db_user:
        return {"isEqual": False}
    
    is_code_valid = verify_code(db, db_user.id, code)
    return {"isEqual": is_code_valid}


@router.post("/password-reset/finish")
def finish_password_reset(code: str, password: str, email: str, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_code(db, db_user.id, code):
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    updated_user = update_password(db, db_user.id, password)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "Password updated"}

@router.post("/getauth_token", response_model=auth_tokenResponse)
def get_auth_token(request: auth_tokenRequest, db: Session = Depends(get_db)):
    new_token = create_token_via_access_token(db, request.constant_access_token)
    if not new_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return new_token
