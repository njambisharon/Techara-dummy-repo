import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta

import jwt

ALGORITHM = "HS256"


def get_jwt_secret():
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is not set.")
    return secret


def get_token_minutes():
    return int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))


def create_access_token(user_id, role, organisation_id, expires_minutes=None):
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes if expires_minutes is not None else get_token_minutes()
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "org": str(organisation_id),
        "exp": expire,
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=ALGORITHM)


def decode_access_token(token):
    return jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])


def generate_device_token():
    return secrets.token_urlsafe(32)


def hash_device_token(token):
    return hashlib.sha256(token.encode()).hexdigest()
