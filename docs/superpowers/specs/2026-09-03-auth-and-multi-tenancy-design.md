# JobHelperGuru: User Authentication & Multi-Tenant Personalization Specification

**Date**: 2026-09-03  
**Status**: Draft / Under Review  
**Topic**: User Authentication (Google OAuth + Email/Password) & Multi-Tenant Data Isolation  

---

## 1. Executive Summary & Goals

JobHelperGuru is transitioning from a single-tenant local application to a cloud-ready, multi-user web service. To enable multiple users to manage their job searches privately before deploying to Render:
1. **Authentication**: Users can sign in via **Google Sign-In (OAuth 2.0)** with one click, or register/login with **Email & Password**.
2. **Multi-Tenant Data Isolation**: Every tracked job application, uploaded resume, and AI model setting is strictly scoped by `user_id`.
3. **Personalized Cloud Storage**: Resumes stored in Cloudflare R2 are segregated under `resumes/{user_id}/`.
4. **Backward Compatibility**: Automated database migrations will ensure existing records in Neon PostgreSQL are assigned safely to the primary account.

---

## 2. Database Schema Changes

### 2.1 `users` Table (New)

```sql
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT,
    name TEXT NOT NULL,
    avatar_url TEXT,
    provider TEXT NOT NULL DEFAULT 'email', -- 'email' or 'google'
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

### 2.2 Table Schema Alterations

All tenant data tables will be updated to include `user_id`:

```sql
-- Applications scoped by user
ALTER TABLE applications ADD COLUMN IF NOT EXISTS user_id TEXT REFERENCES users(id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);

-- Resumes scoped by user
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS user_id TEXT REFERENCES users(id);
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);

-- Settings scoped by user
CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT NOT NULL REFERENCES users(id),
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (user_id, key)
);
```

### 2.3 Historical Data Migration Strategy
On startup or during first registration:
- If unassigned rows exist in `applications` or `resumes` (`user_id IS NULL`), they will be automatically associated with the first registered account (or the designated owner email `souravchandhok01@gmail.com`).
- This guarantees zero loss of the existing tracked jobs and resume data.

---

## 3. Authentication & Security Architecture

### 3.1 Password Security
- **Algorithm**: `bcrypt` (salted, slow-hash algorithm).
- Passwords must be at least 8 characters long.
- Password hashes are stored in `users.hashed_password`. Google OAuth users have `hashed_password = NULL`.

### 3.2 JWT Session Tokens
- **Algorithm**: `HS256` signed using `JWT_SECRET_KEY` (configured in `.env` with a secure fallback for local dev).
- **Token Payload**:
  ```json
  {
    "sub": "<user_id>",
    "email": "user@example.com",
    "name": "Full Name",
    "exp": 1756900000
  }
  ```
- **Validity**: 7 days.
- **Client Transmission**: Sent as an HTTP header `Authorization: Bearer <token>`.

### 3.3 Google Sign-In (OAuth 2.0)
- The frontend renders Google Identity Services (GSI) One Tap / Sign-in button using `GOOGLE_CLIENT_ID`.
- When the user signs in with Google, Google provides a signed JWT `credential` (ID token).
- The frontend POSTs this credential to `/api/auth/google`.
- The FastAPI backend validates the token using Google's public certificates or tokeninfo API (`https://oauth2.googleapis.com/tokeninfo?id_token=...`).
- The backend extracts `email`, `name`, and `picture`. If the user does not exist in `users`, they are automatically registered with `provider: "google"`. An access token is returned.

---

## 4. API Endpoints

### 4.1 `/api/auth` Router

| Method | Path | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Create account with name, email, password | No |
| `POST` | `/api/auth/login` | Login with email and password | No |
| `POST` | `/api/auth/google` | Verify Google ID token and return session | No |
| `GET` | `/api/auth/me` | Fetch currently authenticated user profile | Yes (Bearer) |

### 4.2 Route Protection with `Depends(get_current_user)`

FastAPI dependency:
```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    ...
```
Protected Endpoints:
- `GET /api/applications` -> returns only applications where `user_id == current_user.id`.
- `POST /api/applications` -> saves application with `user_id = current_user.id`.
- `GET /api/resumes` -> returns resumes where `user_id == current_user.id`.
- `POST /api/resumes/upload` -> uploads file to `resumes/{current_user.id}/...` and saves record with `user_id = current_user.id`.
- `GET /api/settings` & `POST /api/settings` -> saves and loads from `user_settings` table for `current_user.id`.
- `POST /api/ai/*` -> runs AI optimizations with the user's specific API settings.

Public Endpoints:
- `GET /api/health` (unprotected for uptime monitors like UptimeRobot).

---

## 5. Frontend UI & State Architecture

### 5.1 Auth State (`AuthContext.jsx`)
- State: `user` (`null` or User object), `token` (persisted in `localStorage`), `isLoading` (boolean).
- Methods: `login(email, password)`, `register(name, email, password)`, `loginWithGoogle(credential)`, `logout()`.
- On application mount: verifies token via `GET /api/auth/me`. If invalid/expired, clears `localStorage`.

### 5.2 Central API Interceptor (`frontend/src/api/client.js`)
- Injects `Authorization: Bearer ${token}` header on every HTTP request.
- Automatically handles `401 Unauthorized` responses by triggering `logout()`.

### 5.3 UI Components

1. **`AuthModal.jsx`**:
   - Modern glassmorphic modal with glowing dark aesthetics.
   - Tab switcher: **Sign In** vs **Create Account**.
   - One-click **Continue with Google** button.
   - Clean email, password, and full name form inputs.
   - Error banner for validation feedback.

2. **`Navbar.jsx` (User Profile Header)**:
   - When authenticated: displays user avatar (Google photo or color initials fallback), display name, and a dropdown menu with:
     - Profile details
     - AI API Settings modal trigger
     - Sign Out button
   - When unauthenticated: displays **Sign In** button that opens `AuthModal`.

---

## 6. Verification & Testing Plan

1. **Backend Unit & Integration Tests (`tests/test_auth.py`)**:
   - Test password hashing & verification.
   - Test user registration with valid and invalid email/password.
   - Test duplicate email rejection.
   - Test login with correct and incorrect credentials.
   - Test JWT token generation and validation.
   - Test route protection: accessing `/api/applications` without token returns 401.
   - Test multi-tenant isolation: User A cannot see or mutate User B's applications or resumes.
2. **End-to-End Browser Flow**:
   - Register a new user via email/password in the browser.
   - Add an application and upload a resume.
   - Sign out and register User B. Verify User B sees an empty pipeline.
   - Sign back in as User A. Verify all applications and resumes are intact.
3. **Continuous Integration**:
   - Run `python -m pytest tests/ -v` (all tests passing against isolated SQLite test databases).
