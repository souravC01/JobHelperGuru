import json
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set


class InsecureSecretError(ValueError):
    """Raised when application secrets do not meet production security standards."""
    pass


INSECURE_DEFAULT_SECRETS: Set[str] = {
    "jobhelperguru-super-secret-dev-jwt-key-2026",
    "jobhelperguru-default-secret-salt-2026",
    "secret",
    "changeme",
    "default",
    "password",
}

DEFAULT_ALLOWED_AI_HOSTS: List[str] = [
    "generativelanguage.googleapis.com",
    "api.openai.com",
    "api.anthropic.com",
    "openrouter.ai",
    "api.deepseek.com",
    "api.groq.com",
    "api.together.xyz",
    "api.tokenrouter.com",
    "integrate.api.nvidia.com",
]

DEFAULT_LOCAL_AI_HOSTS: List[str] = [
    "localhost",
    "127.0.0.1",
]


@dataclass
class AppConfig:
    app_mode: str = "production"  # production, local, test
    app_url: str = "http://localhost:5173"
    jwt_secret_key: str = ""
    encryption_secret: str = ""
    google_client_id: Optional[str] = None
    allowed_provider_hosts: List[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_AI_HOSTS))
    local_ai_hosts: List[str] = field(default_factory=lambda: list(DEFAULT_LOCAL_AI_HOSTS))
    max_request_body_bytes: int = 10 * 1024 * 1024  # 10 MB


def _get_or_create_local_secrets(secrets_dir: Optional[str] = None) -> dict:
    target_dir = Path(secrets_dir or "data").resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    secrets_file = target_dir / ".local_secrets.json"

    if secrets_file.exists():
        try:
            data = json.loads(secrets_file.read_text(encoding="utf-8"))
            if data.get("jwt_secret_key") and data.get("encryption_secret"):
                return data
        except Exception:
            pass

    # Generate persistent random 32-byte secrets for local developer machine
    generated = {
        "jwt_secret_key": secrets.token_urlsafe(32),
        "encryption_secret": secrets.token_urlsafe(32),
    }
    secrets_file.write_text(json.dumps(generated, indent=2), encoding="utf-8")
    return generated


def load_config() -> AppConfig:
    """
    Loads application configuration based on APP_MODE.
    Defaults to production if APP_MODE is unset or invalid.
    Fails closed on missing or insecure secrets in production.
    """
    raw_mode = (os.getenv("APP_MODE") or os.getenv("ENVIRONMENT") or "production").strip().lower()
    if raw_mode not in ("production", "local", "test"):
        raw_mode = "production"

    app_url = os.getenv("APP_URL") or os.getenv("PUBLIC_APP_URL") or "http://localhost:5173"
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")

    custom_ai_hosts_raw = os.getenv("ALLOWED_AI_HOSTS")
    if custom_ai_hosts_raw:
        allowed_hosts = [h.strip() for h in custom_ai_hosts_raw.split(",") if h.strip()]
    else:
        allowed_hosts = list(DEFAULT_ALLOWED_AI_HOSTS)

    if raw_mode == "production":
        jwt_key = (os.getenv("JWT_SECRET_KEY") or "").strip()
        if not jwt_key:
            raise InsecureSecretError("Production configuration error: JWT_SECRET_KEY must be set in environment.")
        if jwt_key in INSECURE_DEFAULT_SECRETS:
            raise InsecureSecretError("Production configuration error: JWT_SECRET_KEY is set to an insecure default secret.")
        if len(jwt_key) < 32:
            raise InsecureSecretError(f"Production configuration error: JWT_SECRET_KEY must be at least 32 characters (got {len(jwt_key)}).")

        enc_key = (os.getenv("SETTINGS_ENCRYPTION_KEY") or os.getenv("SECRET_KEY") or "").strip()
        if not enc_key:
            raise InsecureSecretError("Production configuration error: SETTINGS_ENCRYPTION_KEY must be set in environment.")
        if enc_key in INSECURE_DEFAULT_SECRETS:
            raise InsecureSecretError("Production configuration error: SETTINGS_ENCRYPTION_KEY is set to an insecure default secret.")
        if len(enc_key) < 32:
            raise InsecureSecretError(f"Production configuration error: SETTINGS_ENCRYPTION_KEY must be at least 32 characters (got {len(enc_key)}).")

        return AppConfig(
            app_mode="production",
            app_url=app_url,
            jwt_secret_key=jwt_key,
            encryption_secret=enc_key,
            google_client_id=google_client_id,
            allowed_provider_hosts=allowed_hosts,
            local_ai_hosts=[],  # Local AI loopback hosts disabled in production
        )

    elif raw_mode == "local":
        local_secrets = _get_or_create_local_secrets(os.getenv("LOCAL_SECRETS_DIR"))
        jwt_key = os.getenv("JWT_SECRET_KEY") or local_secrets["jwt_secret_key"]
        enc_key = os.getenv("SETTINGS_ENCRYPTION_KEY") or os.getenv("SECRET_KEY") or local_secrets["encryption_secret"]

        return AppConfig(
            app_mode="local",
            app_url=app_url,
            jwt_secret_key=jwt_key,
            encryption_secret=enc_key,
            google_client_id=google_client_id,
            allowed_provider_hosts=allowed_hosts,
            local_ai_hosts=list(DEFAULT_LOCAL_AI_HOSTS),
        )

    else:  # test mode
        jwt_key = os.getenv("JWT_SECRET_KEY") or "test-jwt-secret-key-for-automated-tests-32chars"
        enc_key = os.getenv("SETTINGS_ENCRYPTION_KEY") or "test-enc-secret-key-for-automated-tests-32chars"

        return AppConfig(
            app_mode="test",
            app_url="http://testserver",
            jwt_secret_key=jwt_key,
            encryption_secret=enc_key,
            google_client_id=google_client_id or "test-google-client-id",
            allowed_provider_hosts=allowed_hosts,
            local_ai_hosts=list(DEFAULT_LOCAL_AI_HOSTS),
        )
