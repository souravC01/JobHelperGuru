import hashlib
import os
import re
import secrets
import requests
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.config import load_config
from backend.services.rate_limiter import RateLimiter, get_client_ip, get_email_hash
from backend.models import (
    AuthResponse,
    EmailVerificationConfirm,
    EmailVerificationRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    User,
    UserLoginRequest,
    UserRegisterRequest,
)
from backend.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.services.email_service import EmailService, SMTPEmailTransport

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = HTTPBearer(auto_error=False)


def _create_email_service() -> EmailService:
    cfg = load_config()
    if cfg.smtp_host:
        transport = SMTPEmailTransport(
            host=cfg.smtp_host,
            port=cfg.smtp_port,
            user=cfg.smtp_user,
            password=cfg.smtp_password,
            from_address=cfg.smtp_from,
        )
        return EmailService(transport=transport)
    return EmailService()


# Email service instance (mockable in tests)
email_service = _create_email_service()

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
    token_session_version = payload.get("session_version")
    storage = get_storage()
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_session_version is None or user.session_version != token_session_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or was revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
) -> Optional[User]:
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = payload["sub"]
    token_session_version = payload.get("session_version")
    storage = get_storage()
    user = storage.get_user_by_id(user_id)
    if not user:
        return None
    if token_session_version is None or user.session_version != token_session_version:
        return None
    return user


class GoogleAuthRequest(BaseModel):
    credential: str


def verify_google_id_token(token: str) -> Dict[str, Any]:
    """Verify signature, issuer, expiry and this application's audience."""
    audience = load_config().google_client_id
    if not audience:
        raise ValueError("Google sign-in is not configured")
    with requests.Session() as session:
        session.trust_env = False
        request = GoogleRequest(session=session)
        def bounded_request(url, method="GET", body=None, headers=None, **kwargs):
            return request(url, method=method, body=body, headers=headers, timeout=5)
        return id_token.verify_oauth2_token(token, bounded_request, audience=audience)


def google_is_authoritative(claims: Dict[str, Any]) -> bool:
    email = str(claims.get("email", "")).lower()
    return claims.get("email_verified") is True and (
        email.endswith("@gmail.com") or bool(claims.get("hd"))
    )


def google_verification_pending(user: User, is_new: bool = False) -> AuthResponse:
    if is_new:
        token = secrets.token_urlsafe(32)
        get_storage().create_auth_token(
            user.id, hashlib.sha256(token.encode()).hexdigest(), "verify_email",
            (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
        )
        try:
            email_service.send_verification(user.email, token, load_config().app_url)
        except Exception:
            # Tokens and transport credentials must never enter logs.
            print("[WARN] Google account verification email delivery failed")
    return AuthResponse(user=user, is_new_user=is_new, requires_verification=True,
                        message="Please verify your email before signing in. You can request a new link.")


@router.post("/register", response_model=AuthResponse)
def register(req: UserRegisterRequest, request: Request):
    email = req.email.strip().lower()
    name = req.name.strip()
    password = req.password

    storage = get_storage()
    cfg = load_config()

    limiter = RateLimiter(storage)
    client_ip = get_client_ip(request, trust_proxy_headers=getattr(cfg, "trust_proxy_headers", False))
    email_h = get_email_hash(email)

    allowed_ip, _, retry_ip = limiter.check("register_ip", client_ip, limit=5, window_seconds=3600)
    if not allowed_ip:
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Please try again later.",
            headers={"Retry-After": str(int(retry_ip))},
        )

    allowed_email, _, retry_email = limiter.check("register_email", email_h, limit=3, window_seconds=3600)
    if not allowed_email:
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts for this email. Please try again later.",
            headers={"Retry-After": str(int(retry_email))},
        )

    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")

    existing = storage.get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    hashed = hash_password(password)
    user = storage.create_user(
        email=email,
        hashed_password=hashed,
        name=name,
        provider="email",
        email_verified=False,
        session_version=1,
    )

    # Generate 32-byte verification token
    verify_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(verify_token.encode("utf-8")).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    storage.create_auth_token(
        user_id=user.id,
        token_hash=token_hash,
        token_type="verify_email",
        expires_at=expires_at,
    )

    try:
        email_service.send_verification(recipient=user.email, token=verify_token, app_url=cfg.app_url)
    except Exception as e:
        print(f"[WARN] Failed to send verification email: {e}")

    if cfg.require_email_verification:
        return AuthResponse(
            token=None,
            user=user,
            message="Verification email sent. Please verify your email before logging in.",
            is_new_user=True,
        )

    token = create_access_token(user.id, user.email, user.name, session_version=user.session_version)
    return AuthResponse(token=token, user=user, is_new_user=True)


@router.post("/login", response_model=AuthResponse)
def login(req: UserLoginRequest, request: Request):
    email = req.email.strip().lower()
    password = req.password

    storage = get_storage()
    cfg = load_config()

    limiter = RateLimiter(storage)
    client_ip = get_client_ip(request, trust_proxy_headers=getattr(cfg, "trust_proxy_headers", False))
    email_h = get_email_hash(email)

    allowed_ip, _, retry_ip = limiter.check("login_ip", client_ip, limit=10, window_seconds=60)
    if not allowed_ip:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(int(retry_ip))},
        )

    allowed_email, _, retry_email = limiter.check("login_email", email_h, limit=10, window_seconds=60)
    if not allowed_email:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts for this account. Please try again later.",
            headers={"Retry-After": str(int(retry_email))},
        )

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

    if cfg.require_email_verification and not raw_user.get("email_verified"):
        raise HTTPException(
            status_code=403,
            detail="Email address has not been verified. Please check your inbox or request a new verification link.",
        )

    user = storage.get_user_by_id(raw_user["id"])
    token = create_access_token(user.id, user.email, user.name, session_version=user.session_version)
    return AuthResponse(token=token, user=user, is_new_user=False)


@router.post("/verify-email/request")
def request_email_verification(req: EmailVerificationRequest, request: Request):
    email = req.email.strip().lower()
    storage = get_storage()
    cfg = load_config()

    limiter = RateLimiter(storage)
    client_ip = get_client_ip(request, trust_proxy_headers=getattr(cfg, "trust_proxy_headers", False))
    email_h = get_email_hash(email)

    allowed_ip, _, retry_ip = limiter.check("verify_ip", client_ip, limit=5, window_seconds=3600)
    if not allowed_ip:
        raise HTTPException(
            status_code=429,
            detail="Too many verification requests. Please try again later.",
            headers={"Retry-After": str(int(retry_ip))},
        )

    allowed_email, _, retry_email = limiter.check("verify_email", email_h, limit=3, window_seconds=3600)
    if not allowed_email:
        raise HTTPException(
            status_code=429,
            detail="Too many verification requests for this email. Please try again later.",
            headers={"Retry-After": str(int(retry_email))},
        )

    raw_user = storage.get_user_by_email(email)

    if raw_user and not raw_user.get("email_verified"):
        verify_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(verify_token.encode("utf-8")).hexdigest()
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        storage.invalidate_prior_auth_tokens(raw_user["id"], "verify_email")
        storage.create_auth_token(raw_user["id"], token_hash, "verify_email", expires_at)
        try:
            email_service.send_verification(recipient=email, token=verify_token, app_url=cfg.app_url)
        except Exception as e:
            print(f"[WARN] Failed to send verification email: {e}")

    # Generic response to prevent account enumeration
    return {"message": "If an account exists with that email, a verification link has been sent."}


@router.post("/verify-email/confirm")
def confirm_email_verification(req: EmailVerificationConfirm):
    clean_token = req.token.strip()
    token_hash = hashlib.sha256(clean_token.encode("utf-8")).hexdigest()
    storage = get_storage()
    record = storage.get_auth_token(token_hash, "verify_email")

    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")

    now_iso = datetime.now(timezone.utc).isoformat()
    if record["expires_at"] < now_iso:
        raise HTTPException(status_code=400, detail="Verification link has expired. Please request a new one.")

    storage.consume_auth_token(record["id"])
    storage.invalidate_prior_auth_tokens(record["user_id"], "verify_email")
    storage.update_user_verification(record["user_id"], verified=True)
    storage.increment_user_session_version(record["user_id"])

    return {"success": True, "message": "Email verified successfully. You may now log in."}


@router.post("/password-reset/request")
def request_password_reset(req: PasswordResetRequest, request: Request):
    email = req.email.strip().lower()
    storage = get_storage()
    cfg = load_config()

    limiter = RateLimiter(storage)
    client_ip = get_client_ip(request, trust_proxy_headers=getattr(cfg, "trust_proxy_headers", False))
    email_h = get_email_hash(email)

    allowed_ip, _, retry_ip = limiter.check("reset_ip", client_ip, limit=5, window_seconds=3600)
    if not allowed_ip:
        raise HTTPException(
            status_code=429,
            detail="Too many password reset requests. Please try again later.",
            headers={"Retry-After": str(int(retry_ip))},
        )

    allowed_email, _, retry_email = limiter.check("reset_email", email_h, limit=3, window_seconds=3600)
    if not allowed_email:
        raise HTTPException(
            status_code=429,
            detail="Too many password reset requests for this email. Please try again later.",
            headers={"Retry-After": str(int(retry_email))},
        )

    raw_user = storage.get_user_by_email(email)

    if raw_user:
        reset_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(reset_token.encode("utf-8")).hexdigest()
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        storage.invalidate_prior_auth_tokens(raw_user["id"], "reset_password")
        storage.create_auth_token(raw_user["id"], token_hash, "reset_password", expires_at)
        try:
            email_service.send_password_reset(recipient=email, token=reset_token, app_url=cfg.app_url)
        except Exception as e:
            print(f"[WARN] Failed to send password reset email: {e}")

    # Generic response to prevent account enumeration
    return {"message": "If an account exists with that email, a password reset link has been sent."}


@router.post("/password-reset/confirm")
def confirm_password_reset(req: PasswordResetConfirm):
    clean_token = req.token.strip()
    token_hash = hashlib.sha256(clean_token.encode("utf-8")).hexdigest()
    storage = get_storage()
    record = storage.get_auth_token(token_hash, "reset_password")

    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset link.")

    now_iso = datetime.now(timezone.utc).isoformat()
    if record["expires_at"] < now_iso:
        raise HTTPException(status_code=400, detail="Password reset link has expired. Please request a new one.")

    hashed = hash_password(req.new_password)
    storage.consume_auth_token(record["id"])
    storage.invalidate_prior_auth_tokens(record["user_id"], "reset_password")
    storage.update_user_password(record["user_id"], hashed, increment_session=True)

    return {"success": True, "message": "Password updated successfully. Please log in with your new password."}


@router.post("/google", response_model=AuthResponse)
def google_auth(req: GoogleAuthRequest):
    token = req.credential.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Google credential token is missing.")

    try:
        token_data = verify_google_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Google token verification failed. Please sign in again.")

    cfg = load_config()
    expected_aud = (cfg.google_client_id or "").strip()
    token_aud = token_data.get("aud")
    if not expected_aud or token_aud != expected_aud:
        raise HTTPException(
            status_code=401,
            detail="Google token audience mismatch. Token was not issued for this application.",
        )

    # Verify email verified in Google token
    ev = token_data.get("email_verified")
    if ev is not True and str(ev).lower() != "true":
        raise HTTPException(
            status_code=400,
            detail="Google token does not contain a verified email address.",
        )

    email = token_data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Google token does not contain an email address.")

    sub = token_data.get("sub", "").strip()
    if not sub:
        raise HTTPException(status_code=400, detail="Google token does not contain a subject identifier.")

    name = token_data.get("name") or token_data.get("given_name") or email.split("@")[0]
    picture = token_data.get("picture")

    storage = get_storage()

    # 1. Search by immutable google_sub
    existing_by_sub = storage.get_user_by_google_sub(sub)
    if existing_by_sub:
        user = storage.get_user_by_id(existing_by_sub["id"])
        if not user.email_verified:
            return google_verification_pending(user)
        access_token = create_access_token(user.id, user.email, user.name, session_version=user.session_version)
        return AuthResponse(token=access_token, user=user, is_new_user=False)

    # 2. Search by email
    existing_by_email = storage.get_user_by_email(email)
    if existing_by_email:
        # Check for Google identity collision
        current_sub = existing_by_email.get("google_sub")
        if current_sub and current_sub != sub:
            raise HTTPException(
                status_code=409,
                detail="This email address is already bound to a different Google account.",
            )

        if not google_is_authoritative(token_data):
            raise HTTPException(status_code=409, detail="Use password sign-in or password recovery for this account. Google cannot confirm current ownership of this email address.")

        # Pre-account hijacking protection: if existing account was unverified, revoke password and sessions
        was_unverified = not bool(existing_by_email.get("email_verified"))
        try:
            storage.link_google_identity(
                user_id=existing_by_email["id"], google_sub=sub,
                clear_password=was_unverified, verify_email=True,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        user = storage.get_user_by_id(existing_by_email["id"])
        access_token = create_access_token(user.id, user.email, user.name, session_version=user.session_version)
        return AuthResponse(token=access_token, user=user, is_new_user=False)

    # 3. Create new user with verified Google identity
    user = storage.create_user(
        email=email,
        hashed_password=None,
        name=name,
        avatar_url=picture,
        provider="google",
        email_verified=google_is_authoritative(token_data),
        session_version=1,
        google_sub=sub,
    )
    if not user.email_verified:
        return google_verification_pending(user, is_new=True)
    access_token = create_access_token(user.id, user.email, user.name, session_version=user.session_version)
    return AuthResponse(token=access_token, user=user, is_new_user=True)


@router.get("/me", response_model=User)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/config")
def get_auth_config():
    cfg = load_config()
    client_id = (cfg.google_client_id or "").strip()
    return {
        "google_client_id": client_id,
        "require_email_verification": cfg.require_email_verification,
    }
