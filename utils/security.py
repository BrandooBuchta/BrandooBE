# utils/security.py
import os
import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
import logging
from models.user import Token

load_dotenv()

SECRET_KEY = os.getenv("AUTH_TOKEN_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logging.basicConfig(level=logging.INFO)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_constant_token(user_id: str) -> str:
    to_encode = {"sub": str(user_id), "type": "constant"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(db: Session, user_id: str, token: str) -> bool:
    db_token = db.query(Token).filter(Token.user_id == user_id).first()
    if not db_token:
        return False
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_id: str = payload.get("sub")
        if token_id is None or token_id != str(user_id):
            return False
        if token != db_token.auth_token:
            return False
        return True
    except jwt.PyJWTError:
        return False

def encrypt_data(data: str, key: str) -> str:
    if data:
        fernet = Fernet(key.encode())
        return fernet.encrypt(data.encode()).decode()
    return data

def decrypt_data(data: str, key: str) -> str:
    if data:
        fernet = Fernet(key.encode())
        try:
            decrypted_data = fernet.decrypt(data.encode()).decode()
            return decrypted_data
        except InvalidToken:
            return None
    return data
