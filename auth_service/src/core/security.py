
import datetime
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.settings import settings


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def create_access_token(user_id: uuid.UUID) -> str:
    expires_at = datetime.datetime.now() + datetime.timedelta(
        minutes=settings.access_token_expire_minute,
    )

    payload = {
        "sub": str(user_id), 
        "exp": expires_at,
        "type": "access_token",
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token() -> tuple[str, datetime.datetime]:
    expires_at = datetime.datetime.now() + datetime.timedelta(
        days=settings.refresh_token_expire_days,
    )

    refresh_token = token_urlsafe(64)

    return refresh_token, expires_at

def decode_refresh_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, "HS256")
    except JWTError:
        return None

def get_access_token_payload(token) -> uuid.UUID | None:
    payload = decode_refresh_token(token)
    if payload is None:
        return None 
    
    if payload["type"] != "access_token":
        return None 
    
    sub = payload["sub"]
    if isinstance(sub, uuid.UUID):
        return None
    
    return sub

def hash_refresh_token(token: str):
    return sha256(token.encode("utf-8")).hexdigest()    
