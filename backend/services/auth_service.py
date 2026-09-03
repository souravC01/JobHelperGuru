import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jobhelperguru-super-secret-dev-jwt-key-2026")
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str, name: str, expires_delta_days: int = 7) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=expires_delta_days)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None
