# routers/user.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas.user import UserCreate, UserUpdate, SignInResponse, CodeVerification, PasswordReset, User as UserSchema, UserSignIn
from crud.user import create_user, get_user, get_user_by_email, update_user, delete_user, create_token_via_id, create_code, verify_code, update_password, get_token, create_code_for_new_user, verify_code_without_user_id
from utils.security import verify_password, create_access_token, verify_token, decrypt_private_key_via_password, encrypt_private_key_for_fe, generate_key_pair, encrypt_private_key_via_password
from utils.email import send_verification_email, send_reset_email
from uuid import UUID
from fastapi.security import OAuth2PasswordBearer
from utils.email import send_verification_email, send_reset_email
from cryptography.hazmat.primitives import serialization

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

@router.post("/create-code-for-new-user")
def post_code_for_new_user(db: Session = Depends(get_db), months_of_activity: str = Query(None)):
    code = create_code_for_new_user(db, months_of_activity)
    return code

@router.post("/create")
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, user)
    token = create_token_via_id(db, new_user.id)
    return {"detail": "Succesfully created new user!"}

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

@router.post("/sign-in", response_model=SignInResponse)
def sign_in_user(sign_in_data: UserSignIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, sign_in_data.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not db_user or not verify_password(sign_in_data.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    private_key = decrypt_private_key_via_password(db_user.encrypted_private_key, sign_in_data.password)
    token = get_token(db, db_user.id)

    return {
        "user": db_user,
        "security": {
            "token": token,
            "private_key": encrypt_private_key_for_fe(private_key)
        }, 
    }

@router.post("/start-verification/{user_id}")
def start_verification(user_id: UUID, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    verification_code = create_code(db, user_id, "verification")
    send_verification_email(db_user.email, verification_code.code)
    return {"detail": "Verification email sent"}

@router.post("/finish-verification/{user_id}")
def finish_verification(user_id: UUID, code: str = Query(None), db: Session = Depends(get_db)):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_verified = verify_code(db, user_id, code)
    
    if is_verified:
        db_user.is_verified = True
        db.commit()
        db.refresh(db_user)
    
    return {"is_verified": is_verified}

@router.post("/verify-code/new")
def verify_new_user_code(code: str = Query(None), db: Session = Depends(get_db)):
    is_code_valid = verify_code_without_user_id(db, code)
    return {"isEqual": is_code_valid}

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
        raise HTTPException(status_code=404, detail="Code is wrong or expired")
    
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
    
    private_key, public_key = generate_key_pair()

    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    encrypted_private_key = encrypt_private_key_via_password(private_key, password)

    db_user.encrypted_private_key = encrypted_private_key
    db_user.public_key = public_key_pem
    
    db.commit()
    db.refresh(db_user)
    
    return {"detail": "Password and keys updated successfully"}
