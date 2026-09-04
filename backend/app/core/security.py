from datetime import datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """
    Hash plain-text password using bcrypt.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain-text password against bcrypt hashed password.
    """
    try:
        pwd_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.AUTH_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate JWT access token.
    """
    try:
        payload = jwt.decode(token, settings.AUTH_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
