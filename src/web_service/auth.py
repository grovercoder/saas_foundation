import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    secret_key = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    if not secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable not set.")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    secret_key = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = "HS256"
    if not secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable not set.")
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
