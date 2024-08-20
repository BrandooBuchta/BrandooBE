# crud/user.py

from sqlalchemy.orm import Session
from models.user import User, Token, Code
from schemas.user import UserCreate, UserUpdate
from uuid import UUID
from utils.security import get_password_hash, verify_password, create_access_token
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet 
from utils.email import send_delete_user_email
from utils.security import decrypt_private_key_via_password, encrypt_private_key_via_password, generate_key_pair
import uuid
from cryptography.hazmat.primitives import serialization

def create_user(db: Session, user: UserCreate):
    private_key, public_key = generate_key_pair()

    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    db_user = User(
        id=uuid.uuid4(),
        name=user.name,
        email=user.email,
        password=get_password_hash(user.password),
        type=user.type,
        web_url=user.web_url,
        encrypted_private_key=encrypt_private_key_via_password(private_key, user.password),
        public_key=public_key_pem  # Store as string
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: UUID):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def update_user(db: Session, user_id: UUID, user_update: UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: UUID):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

def delete_unverified_users(db: Session):
    one_week_ago = datetime.now() - timedelta(weeks=1)
    
    db_users = db.query(User).filter(
        User.is_verified == False,
        User.created_at < one_week_ago
    ).all()
    
    for user in db_users:
        send_delete_user_email(user.email)
        db.delete(user)
    
    db.commit()

def create_token_via_id(db: Session, user_id: UUID):
    expires_at = datetime.utcnow() + timedelta(days=30)
    db_token = Token(
        id=uuid.uuid4(),
        auth_token=create_access_token(user_id),
        expires_at=expires_at,
        user_id=user_id
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def refresh_all_auth_tokens(db: Session):
    db_tokens = db.query(Token).filter(Token.expires_at <= datetime.utcnow()).all()
    
    for token in db_tokens:
        create_token_via_id(db, token.user_id)
    
    db.commit()
    
    for token in db_tokens:
        db.delete(token)
    
    db.commit()

def get_token(db: Session, user_id: UUID):
    return db.query(Token).filter(Token.user_id == user_id).first()

def create_code(db: Session, user_id: UUID, code_type: str):
    code = str(uuid.uuid4().int)[:6]
    db_code = Code(
        id=uuid.uuid4(),
        type=code_type,
        code=code,
        user_id=user_id
    )
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    return db_code    

def verify_code(db: Session, user_id: UUID, code: str) -> bool:
    db_code = db.query(Code).filter(Code.user_id == user_id, Code.code == code).first()
    if db_code:
        now = datetime.now(tz=timezone.utc)
        if (now - db_code.created_at).total_seconds() < 300:
            return True
    return False



def update_password(db: Session, user_id: UUID, new_password: str):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.password = get_password_hash(new_password)
        db.commit()
        db.refresh(db_user)
        return db_user
    return None

def delete_expired_code(db: Session):
    five_minutes = datetime.now() - timedelta(minutes=5)
    
    db_codes = db.query(Code).filter(
        Code.created_at < five_minutes
    ).all()
    
    for code in db_codes:
        db.delete(code)
    
    db.commit()