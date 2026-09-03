import json
import re
import urllib.request
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from backend.models import User, UserRegisterRequest, UserLoginRequest, AuthResponse
from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = HTTPBearer(auto_error=False)

# Storage dependency placeholder (injected from main.py)
_storage_service = None


def set_storage_service(storage):
    global _storage_service
    _storage_service = storage


def get_storage():
    if _storage_service is None:
        from backend.main import storage
        return storage
    return _storage_service


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    storage = get_storage()
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class GoogleAuthRequest(BaseModel):
    credential: str


@router.post("/register", response_model=AuthResponse)
def register(req: UserRegisterRequest):
    email = req.email.strip().lower()
    name = req.name.strip()
    password = req.password

    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")

    storage = get_storage()
    existing = storage.get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    hashed = hash_password(password)
    user = storage.create_user(
        email=email,
        hashed_password=hashed,
        name=name,
        provider="email",
    )
    token = create_access_token(user.id, user.email, user.name)
    return AuthResponse(token=token, user=user)


@router.post("/login", response_model=AuthResponse)
def login(req: UserLoginRequest):
    email = req.email.strip().lower()
    password = req.password

    storage = get_storage()
    raw_user = storage.get_user_by_email(email)
    if not raw_user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not raw_user.get("hashed_password") and raw_user.get("provider") == "google":
        raise HTTPException(
            status_code=400,
            detail="This account was registered via Google Sign-In. Please click 'Continue with Google'.",
        )

    if not verify_password(password, raw_user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user = storage.get_user_by_id(raw_user["id"])
    token = create_access_token(user.id, user.email, user.name)
    return AuthResponse(token=token, user=user)


@router.post("/google", response_model=AuthResponse)
def google_auth(req: GoogleAuthRequest):
    token = req.credential.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Google credential token is missing.")

    # Validate token against Google tokeninfo endpoint
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        req_obj = urllib.request.Request(url, headers={"User-Agent": "JobHelperGuru/1.0"})
        with urllib.request.urlopen(req_obj, timeout=5) as response:
            token_data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google token verification failed: {e}")

    email = token_data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Google token does not contain a verified email.")

    name = token_data.get("name") or token_data.get("given_name") or email.split("@")[0]
    picture = token_data.get("picture")

    storage = get_storage()
    raw_user = storage.get_user_by_email(email)
    if not raw_user:
        user = storage.create_user(
            email=email,
            hashed_password=None,
            name=name,
            avatar_url=picture,
            provider="google",
        )
    else:
        user = storage.get_user_by_id(raw_user["id"])

    access_token = create_access_token(user.id, user.email, user.name)
    return AuthResponse(token=access_token, user=user)


@router.get("/me", response_model=User)
def me(current_user: User = Depends(get_current_user)):
    return current_user
