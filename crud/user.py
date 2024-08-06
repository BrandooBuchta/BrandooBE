from sqlalchemy.orm import Session
from models.user import User, Token, Code
from schemas.user import UserCreate, UserUpdate
from uuid import UUID
from utils.security import get_password_hash, verify_password, create_access_token, create_constant_token
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
import uuid

def create_user(db: Session, user: UserCreate):
    db_user = User(
        id=uuid.uuid4(),
        name=user.name,
        email=user.email,
        password=get_password_hash(user.password),
        type=user.type,
        web_url=user.web_url,
        encryption_key=Fernet.generate_key().decode()
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

def create_token_via_id(db: Session, user_id: UUID):
    expires_at = datetime.utcnow() + timedelta(days=30)
    db_token = Token(
        id=uuid.uuid4(),
        auth_token=create_access_token(user_id),
        constant_access_token=create_constant_token(user_id),
        expires_at=expires_at,
        user_id=user_id
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def create_token_via_access_token(db: Session, constant_access_token: str):
    db_token = db.query(Token).filter(Token.constant_access_token == constant_access_token).first()
    if not db_token:
        return None
    expires_at = datetime.utcnow() + timedelta(days=30)
    new_auth_token = create_access_token(db_token.user_id)
    db_token.auth_token = new_auth_token
    db_token.expires_at = expires_at
    db.commit()
    db.refresh(db_token)
    return db_token

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
