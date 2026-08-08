"""
Security primitives: password hashing (bcrypt) and JWT access tokens.

The JWT secret comes from the JWT_SECRET env var. A development-only default is
used when it is unset so tests/preview work, but production MUST set JWT_SECRET
(the app logs a warning and never ships this default knowingly to prod).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET") or "dev-only-insecure-secret-change-me"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _pwd.verify(password, hashed)
    except ValueError:
        return False


def create_access_token(subject: str, extra: Optional[dict] = None,
                        expires_minutes: Optional[int] = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": str(subject), "iat": now, "exp": exp}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except InvalidTokenError:
        return None
