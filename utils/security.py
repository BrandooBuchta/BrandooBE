# utils/security

import os
import jwt
import hashlib
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
import logging
from models.user import Token
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import b64encode, b64decode, urlsafe_b64encode, urlsafe_b64decode

from urllib.parse import unquote

load_dotenv()

SECRET_KEY = os.getenv("AUTH_TOKEN_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
SECRET_KEY_FOR_FE_ENCRYPTION = urlsafe_b64decode(os.getenv("SECRET_KEY_FOR_FE_ENCRYPTION"))

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
    return urlsafe_b64encode(digest)

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

def rsa_encrypt_data(data: str, public_key_pem: str) -> str:
    public_key = serialization.load_pem_public_key(public_key_pem.encode(), backend=default_backend())
    encrypted_data = public_key.encrypt(
        data.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_data.hex()

def rsa_decrypt_data(encrypted_data: str, private_key_pem: str) -> str:
    try:
        decoded_private_key = unquote(private_key_pem)
        private_key = serialization.load_pem_private_key(
            decoded_private_key.encode(),
            password=None,
            backend=default_backend()
        )
        decrypted_data = private_key.decrypt(
            bytes.fromhex(encrypted_data),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted_data.decode()
    except ValueError:
        logging.error("Invalid private key")
        raise
    except Exception as e:
        logging.error(f"Error during decryption: {e}")
        raise

def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def encrypt_private_key_for_fe(private_key: str) -> str:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(SECRET_KEY_FOR_FE_ENCRYPTION), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(private_key.encode()) + encryptor.finalize()
    return b64encode(iv + encrypted_data).decode('utf-8')

def decrypt_private_key_for_fe(encrypted_data: str) -> str:
    encrypted_data_bytes = b64decode(encrypted_data)
    iv = encrypted_data_bytes[:16]
    cipher = Cipher(algorithms.AES(SECRET_KEY_FOR_FE_ENCRYPTION), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data_bytes[16:]) + decryptor.finalize()
    return decrypted_data.decode('utf-8')