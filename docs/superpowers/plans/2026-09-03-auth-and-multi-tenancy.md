# User Authentication & Multi-Tenant Personalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Google OAuth 2.0 and Email/Password authentication with multi-tenant data isolation for applications, resumes, settings, and Cloudflare R2 files before cloud deployment.

**Architecture:** A FastAPI backend authentication service using `bcrypt` and `pyjwt` (HS256) storing users in Neon PostgreSQL (with SQLite test fallback). Multi-tenant scoping filters all database queries by `user_id`. The React frontend manages session state via `AuthContext`, injects JWT tokens via `client.js`, and provides an `AuthModal` with Google Identity Services and email login.

**Tech Stack:** FastAPI, Python 3.14, `bcrypt`, `pyjwt`, Neon PostgreSQL, SQLite, Cloudflare R2 (`boto3`), React, TailwindCSS, Google Identity Services.

**Spec:** [`docs/superpowers/specs/2026-09-03-auth-and-multi-tenancy-design.md`](file:///d:/Grind/Projects/JobHelperGuru/docs/superpowers/specs/2026-09-03-auth-and-multi-tenancy-design.md)

## Global Constraints

- Never use emojis in backend console logging or prints; use clean ASCII tags like `[INFO]`, `[WARN]`, `[SUCCESS]`.
- All database queries must support dual-mode (PostgreSQL with `%s` and SQLite with `?`) via `_format_sql`.
- Automated tests in `tests/` must run in isolated local SQLite databases and never mutate the live Neon database (`isolate_test_database` in `conftest.py`).
- Passwords must be at least 8 characters long.
- Keep the health check endpoint `/api/health` completely public (unprotected) for uptime monitors.

---

### Task 1: Core User Models, Password Hashing & JWT Security Utilities

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/models.py`
- Create: `backend/services/auth_service.py`
- Test: `tests/test_auth_service.py`

**Interfaces:**
- Produces:
  - `backend.models.User`: `(id: str, email: str, name: str, avatar_url: Optional[str], provider: str, created_at: str, updated_at: str)`
  - `backend.models.UserRegisterRequest`: `(email: str, password: str, name: str)`
  - `backend.models.UserLoginRequest`: `(email: str, password: str)`
  - `backend.models.AuthResponse`: `(token: str, user: User)`
  - `backend.services.auth_service.hash_password(password: str) -> str`
  - `backend.services.auth_service.verify_password(plain_password: str, hashed_password: str) -> bool`
  - `backend.services.auth_service.create_access_token(user_id: str, email: str, name: str, expires_delta_days: int = 7) -> str`
  - `backend.services.auth_service.decode_access_token(token: str) -> Optional[dict]`

- [ ] **Step 1: Install dependencies and update requirements**

Run:
```bash
python -m pip install bcrypt pyjwt
```
Add `bcrypt>=4.2.0` and `pyjwt>=2.9.0` to [`backend/requirements.txt`](file:///d:/Grind/Projects/JobHelperGuru/backend/requirements.txt).

- [ ] **Step 2: Write failing unit tests for auth utilities**

Create [`tests/test_auth_service.py`](file:///d:/Grind/Projects/JobHelperGuru/tests/test_auth_service.py):
```python
import pytest
from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hashing_and_verification():
    raw_pass = "SuperSecret123!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_decoding():
    token = create_access_token(
        user_id="usr-12345",
        email="test@example.com",
        name="Test User",
    )
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "usr-12345"
    assert payload["email"] == "test@example.com"
    assert payload["name"] == "Test User"


def test_invalid_jwt_decoding():
    assert decode_access_token("invalid.token.payload") is None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_auth_service.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.services.auth_service'`

- [ ] **Step 4: Implement User models and AuthService**

Update [`backend/models.py`](file:///d:/Grind/Projects/JobHelperGuru/backend/models.py) with `User`, `UserRegisterRequest`, `UserLoginRequest`, `AuthResponse`:
```python
class User(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    provider: str = "email"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class UserRegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: User
```

Create [`backend/services/auth_service.py`](file:///d:/Grind/Projects/JobHelperGuru/backend/services/auth_service.py):
```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_auth_service.py -v`  
Expected: PASS (3 tests passed)

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/models.py backend/services/auth_service.py tests/test_auth_service.py
git commit -m "feat(auth): implement core user models, password hashing, and jwt service"
```

---

### Task 2: Database Schema & Multi-Tenant Storage Scoping

**Files:**
- Modify: `backend/storage.py`
- Test: `tests/test_storage_auth.py`

**Interfaces:**
- Consumes: `backend.models.User`, `backend.models.Application`, `backend.models.Resume`
- Produces:
  - `StorageService.create_user(email, hashed_password, name, avatar_url, provider) -> User`
  - `StorageService.get_user_by_email(email) -> Optional[dict]` (returns raw dict including `hashed_password`)
  - `StorageService.get_user_by_id(user_id) -> Optional[User]`
  - `StorageService.get_applications(user_id: str) -> List[Application]`
  - `StorageService.add_application(app_data: ApplicationCreate, user_id: str) -> Application`
  - `StorageService.get_resumes(user_id: str) -> List[Resume]`
  - `StorageService.add_resume(name: str, content: str, file_key: Optional[str], user_id: str) -> Resume`
  - `StorageService.get_settings(user_id: str) -> Settings`
  - `StorageService.save_settings(settings: Settings, user_id: str)`

- [ ] **Step 1: Write failing multi-tenancy tests**

Create [`tests/test_storage_auth.py`](file:///d:/Grind/Projects/JobHelperGuru/tests/test_storage_auth.py):
```python
import pytest
from backend.storage import StorageService
from backend.models import ApplicationCreate, ApplicationStatus


def test_multi_tenant_isolation(tmp_path):
    storage = StorageService(db_path=str(tmp_path / "test_multi_tenant.db"), force_sqlite=True)

    # 1. Create two separate users
    u1 = storage.create_user(email="alice@test.com", hashed_password="pwd", name="Alice")
    u2 = storage.create_user(email="bob@test.com", hashed_password="pwd", name="Bob")

    # 2. Alice creates an application
    app_alice = storage.add_application(
        ApplicationCreate(
            company="Alice Corp",
            role="Engineer",
            status=ApplicationStatus.WISHLIST,
        ),
        user_id=u1.id,
    )

    # 3. Bob creates an application
    app_bob = storage.add_application(
        ApplicationCreate(
            company="Bob Inc",
            role="Designer",
            status=ApplicationStatus.APPLIED,
        ),
        user_id=u2.id,
    )

    # 4. Verify isolation
    alice_apps = storage.get_applications(user_id=u1.id)
    bob_apps = storage.get_applications(user_id=u2.id)

    assert len(alice_apps) == 1
    assert alice_apps[0].company == "Alice Corp"

    assert len(bob_apps) == 1
    assert bob_apps[0].company == "Bob Inc"


def test_user_retrieval(tmp_path):
    storage = StorageService(db_path=str(tmp_path / "test_user_crud.db"), force_sqlite=True)
    user = storage.create_user(email="carol@test.com", hashed_password="pwd_hash", name="Carol")

    found_email = storage.get_user_by_email("carol@test.com")
    assert found_email is not None
    assert found_email["id"] == user.id
    assert found_email["hashed_password"] == "pwd_hash"

    found_id = storage.get_user_by_id(user.id)
    assert found_id is not None
    assert found_id.email == "carol@test.com"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_storage_auth.py -v`  
Expected: FAIL with `AttributeError: 'StorageService' object has no attribute 'create_user'`

- [ ] **Step 3: Update `backend/storage.py` schemas and methods**

In `backend/storage.py`:
1. In `_init_db()`:
   - Create `users` table (`id`, `email`, `hashed_password`, `name`, `avatar_url`, `provider`, `created_at`, `updated_at`).
   - Add `user_id TEXT` column to `applications` and `resumes` using `ALTER TABLE ... ADD COLUMN IF NOT EXISTS user_id TEXT`.
   - Create `user_settings` table (`user_id TEXT, key TEXT, value TEXT, PRIMARY KEY (user_id, key)`).
2. Implement user CRUD methods: `create_user`, `get_user_by_email`, `get_user_by_id`.
3. Update `get_applications`, `add_application`, `get_resumes`, `add_resume`, `get_settings`, `save_settings` to accept `user_id: Optional[str] = None` and scope queries by `WHERE user_id = ?`.
4. Auto-migration: on user creation, if `user_id IS NULL` rows exist in `applications` or `resumes`, auto-assign them to the first user created.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_storage_auth.py -v`  
Expected: PASS

- [ ] **Step 5: Run full storage regression tests**

Run: `python -m pytest tests/test_storage.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/storage.py tests/test_storage_auth.py
git commit -m "feat(storage): add users table and multi-tenant scoping for applications and resumes"
```

---

### Task 3: Authentication API Router & Token Dependency

**Files:**
- Create: `backend/routers/auth.py`
- Modify: `backend/main.py`
- Test: `tests/test_auth_api.py`

**Interfaces:**
- Consumes: `backend.services.auth_service`, `backend.storage.StorageService`
- Produces:
  - `POST /api/auth/register` -> `AuthResponse`
  - `POST /api/auth/login` -> `AuthResponse`
  - `POST /api/auth/google` -> `AuthResponse`
  - `GET /api/auth/me` -> `User`
  - `backend.routers.auth.get_current_user` FastAPI dependency

- [ ] **Step 1: Write failing API authentication tests**

Create [`tests/test_auth_api.py`](file:///d:/Grind/Projects/JobHelperGuru/tests/test_auth_api.py):
```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_auth_register_login_and_me():
    # 1. Register new user
    reg_payload = {
        "email": "fresh_user@example.com",
        "password": "Password123!",
        "name": "Fresh User",
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    assert res_reg.status_code == 200
    data_reg = res_reg.json()
    assert "token" in data_reg
    assert data_reg["user"]["email"] == "fresh_user@example.com"
    token = data_reg["token"]

    # 2. Access /api/auth/me with Bearer token
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "fresh_user@example.com"

    # 3. Access without token should return 401
    res_no_auth = client.get("/api/auth/me")
    assert res_no_auth.status_code == 401

    # 4. Login with registered user
    login_payload = {
        "email": "fresh_user@example.com",
        "password": "Password123!",
    }
    res_login = client.post("/api/auth/login", json=login_payload)
    assert res_login.status_code == 200
    assert "token" in res_login.json()

    # 5. Login with wrong password
    res_bad = client.post(
        "/api/auth/login",
        json={"email": "fresh_user@example.com", "password": "WrongPassword!"},
    )
    assert res_bad.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_auth_api.py -v`  
Expected: FAIL with `404 Not Found` for `/api/auth/register`

- [ ] **Step 3: Implement `backend/routers/auth.py`**

Create [`backend/routers/auth.py`](file:///d:/Grind/Projects/JobHelperGuru/backend/routers/auth.py) implementing:
- `router = APIRouter(prefix="/api/auth", tags=["auth"])`
- `get_current_user` dependency validating JWT from `HTTPBearer()` header.
- Endpoint `/register`: validates email, checks duplicates, creates user, returns token.
- Endpoint `/login`: verifies credentials with `verify_password`, returns token.
- Endpoint `/google`: verifies token with Google Tokeninfo or `urllib.request` against `https://oauth2.googleapis.com/tokeninfo?id_token={token}`, auto-creates user if not found, returns token.
- Endpoint `/me`: returns `current_user`.

- [ ] **Step 4: Wire router into `backend/main.py` and protect data routes**

In `backend/main.py`:
- Include `app.include_router(auth_router)`.
- Inject `current_user: User = Depends(get_current_user)` into:
  - `GET /api/applications`, `POST /api/applications`, `DELETE /api/applications/{id}`
  - `GET /api/resumes`, `POST /api/resumes`, `POST /api/resumes/upload`, `DELETE /api/resumes/{id}`
  - `GET /api/settings`, `POST /api/settings`
- Pass `user_id=current_user.id` to storage calls.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_auth_api.py -v`  
Expected: PASS

- [ ] **Step 6: Update existing API tests with auth helper**

Update [`tests/test_api.py`](file:///d:/Grind/Projects/JobHelperGuru/tests/test_api.py) to register a test user and include `{"Authorization": f"Bearer {token}"}` on protected endpoints.
Run: `python -m pytest tests/ -v`  
Expected: PASS (all 32+ tests passing)

- [ ] **Step 7: Commit**

```bash
git add backend/routers/auth.py backend/main.py tests/test_auth_api.py tests/test_api.py
git commit -m "feat(api): add auth router with JWT protection and multi-tenant endpoint isolation"
```

---

### Task 4: Scoping Cloudflare R2 Uploads by User ID

**Files:**
- Modify: `backend/services/object_storage.py`
- Modify: `backend/main.py`
- Modify: `tests/test_object_storage.py`

**Interfaces:**
- Consumes: `user_id: str`
- Produces: `object_storage.upload_file(content_bytes, filename, content_type, user_id) -> "resumes/{user_id}/{unique_key}"`

- [ ] **Step 1: Write failing test for user-scoped upload**

Update [`tests/test_object_storage.py`](file:///d:/Grind/Projects/JobHelperGuru/tests/test_object_storage.py):
```python
def test_user_scoped_upload(tmp_path, monkeypatch):
    monkeypatch.setenv("R2_ACCOUNT_ID", "")
    storage = ObjectStorageService()
    test_content = b"%PDF-1.4 User scoped resume test"
    key = storage.upload_file(test_content, "resume.pdf", user_id="usr-999")
    assert key.startswith("resumes/usr-999/")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_object_storage.py::test_user_scoped_upload -v`  
Expected: FAIL

- [ ] **Step 3: Update `backend/services/object_storage.py`**

In `upload_file`:
```python
prefix = f"resumes/{user_id}" if user_id else "resumes"
unique_key = f"{prefix}/{uuid.uuid4().hex}_{safe_name}{ext}"
```

- [ ] **Step 4: Update `POST /api/resumes/upload` in `backend/main.py`**

Pass `user_id=current_user.id` to `object_storage.upload_file(...)`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_object_storage.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/services/object_storage.py backend/main.py tests/test_object_storage.py
git commit -m "feat(storage): isolate Cloudflare R2 resume uploads by user_id"
```

---

### Task 5: Frontend Auth Context & API Client Interceptor

**Files:**
- Create: `frontend/src/context/AuthContext.jsx`
- Modify: `frontend/src/api/client.js`
- Modify: `frontend/src/main.jsx`

**Interfaces:**
- Produces:
  - `useAuth()` hook: `{ user, token, isAuthenticated, login, register, loginWithGoogle, logout, isLoading }`
  - `apiClient`: automatically appends `Authorization: Bearer ${token}` header and intercepts 401s to clear session.

- [ ] **Step 1: Create `AuthContext.jsx`**

Create [`frontend/src/context/AuthContext.jsx`](file:///d:/Grind/Projects/JobHelperGuru/frontend/src/context/AuthContext.jsx):
- Checks `localStorage.getItem("jobhelperguru_token")`.
- On startup, calls `/api/auth/me`. If successful, sets `user`.
- Provides `login(email, password)`, `register(name, email, password)`, `loginWithGoogle(credential)`, and `logout()`.

- [ ] **Step 2: Update `client.js` with Bearer token injector**

Update [`frontend/src/api/client.js`](file:///d:/Grind/Projects/JobHelperGuru/frontend/src/api/client.js):
- Add helper to inject `Authorization: Bearer ${localStorage.getItem("jobhelperguru_token")}` to all outgoing `fetch` requests.
- If response status is 401, remove token and dispatch an auth expiration event.

- [ ] **Step 3: Wrap `main.jsx` with `AuthProvider`**

In [`frontend/src/main.jsx`](file:///d:/Grind/Projects/JobHelperGuru/frontend/src/main.jsx), wrap `<App />` with `<AuthProvider>`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/context/AuthContext.jsx frontend/src/api/client.js frontend/src/main.jsx
git commit -m "feat(frontend): implement AuthContext and automatic bearer token injection"
```

---

### Task 6: Modern AuthModal UI & Top Navbar Profile Badge

**Files:**
- Create: `frontend/src/components/AuthModal.jsx`
- Modify: `frontend/src/components/Navbar.jsx` (or top header in `frontend/src/App.jsx`)
- Modify: `frontend/index.html` (include Google Identity Services script)

**Interfaces:**
- `AuthModal`: Glassmorphism modal with:
  - Google Sign-In button
  - Tab switch: "Sign In" vs "Create Account"
  - Form validation and error alerts
- User Profile Badge in top navigation:
  - Shows user avatar / initials
  - Shows full name and email
  - Dropdown menu with "AI Settings" and "Sign Out"

- [ ] **Step 1: Add Google Identity Services script in `index.html`**

In [`frontend/index.html`](file:///d:/Grind/Projects/JobHelperGuru/frontend/index.html), add:
```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

- [ ] **Step 2: Create `frontend/src/components/AuthModal.jsx`**

Implement sleek dark-card modal with:
- Google Sign-in button rendered via `window.google.accounts.id`.
- Toggle between Sign In and Sign Up.
- Email, password, and name input fields with focus glow effects.
- Clean error banner.

- [ ] **Step 3: Integrate User Profile Dropdown into Header**

In [`frontend/src/App.jsx`](file:///d:/Grind/Projects/JobHelperGuru/frontend/src/App.jsx):
- When logged in: display user avatar/initials, name, and sign out button in header.
- When logged out: display "Sign In" button that triggers `AuthModal`.
- If user is logged out, show friendly welcome banner encouraging sign-in to save applications.

- [ ] **Step 4: Test frontend build**

Run:
```bash
cd frontend && npm run build
```
Verify build succeeds with zero errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/src/components/AuthModal.jsx frontend/src/App.jsx
git commit -m "feat(ui): add glassmorphic AuthModal and navbar user profile dropdown"
```

---

### Task 7: Full System Verification & Regression Suite

**Files:**
- All tests in `tests/`
- Full E2E flow in `tests/test_e2e_flow.py`

- [ ] **Step 1: Run full pytest suite**

Run: `python -m pytest tests/ -v`  
Expected: All 33+ tests passing.

- [ ] **Step 2: Verify live server health and endpoints**

Start server:
```bash
python -m uvicorn backend.main:app --port 8000
```
Verify `http://127.0.0.1:8000/api/health` returns:
```json
{
  "status": "ok",
  "app": "JobHelperGuru",
  "database": "postgresql",
  "object_storage": "cloudflare_r2"
}
```

- [ ] **Step 3: Test user registration, login, and multi-tenant isolation live**

Run automated script creating two distinct users and verifying private pipeline records.

- [ ] **Step 4: Final commit and push to main**

```bash
git push origin main
```
