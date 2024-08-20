# utils/security.py
import os
import jwt
import hashlib
import base64
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
import logging
from models.user import Token
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

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

def generate_key_from_password(password: str) -> str:
    digest = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_private_key_via_password(private_key, password: str) -> str:
    if private_key:
        key = generate_key_from_password(password)
        fernet = Fernet(key)
        
        pem_data = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        encrypted_pem_data = fernet.encrypt(pem_data).decode()
        return encrypted_pem_data
    return None

def decrypt_private_key_via_password(data: str, password: str) -> str:
    if data:
        key = generate_key_from_password(password)
        fernet = Fernet(key)
        try:
            decrypted_data = fernet.decrypt(data.encode()).decode()
            return decrypted_data
        except InvalidToken:
            logging.error("Invalid token for private key decryption.")
            return None
    return data

def encrypt_data(data: str, key: str) -> str:
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data.decode()

def decrypt_data(encrypted_data: str, key: str) -> str:
    fernet = Fernet(key)
    try:
        decrypted_data = fernet.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    except InvalidToken:
        return None

def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

    