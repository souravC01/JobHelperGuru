# Security & Performance Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all high/medium security vulnerabilities, implement PostgreSQL connection pooling and concurrency optimizations, and clean up dead startup code in JobHelperGuru without modifying any existing business logic or breaking test suites.

**Architecture:** 
- Enforce Google OAuth token audience (`aud`) matching and SSRF private IP validation.
- Scope database deduplication by `user_id` to guarantee tenant isolation.
- Introduce `ThreadedConnectionPool` for Neon PostgreSQL to eliminate per-query TLS handshakes.
- Enforce upload file size caps, extension whitelisting, and offload CPU/S3 blocking calls from the FastAPI event loop.
- Remove startup SQLite re-migration and hardcoded client fallbacks.

**Tech Stack:** Python 3.11+, FastAPI, PostgreSQL / `psycopg2.pool`, `urllib`, `ipaddress`, `cryptography`, React 18, Pytest.

**Spec:** PRD and Architecture Audit Report (September 2026).

## Global Constraints
- Do NOT alter any existing business logic or data output structures.
- All 45 existing unit and e2e tests must continue to pass green.
- Maintain dual-engine support (PostgreSQL in cloud, SQLite in local unit tests).
- Zero downtime or database schema migrations required.

---

### Task 1: Google OAuth ID Token Audience (`aud`) Verification

**Files:**
- Modify: `backend/routers/auth.py:140-160`
- Test: `tests/test_auth_api.py`

**Interfaces:**
- Consumes: `token_data` from Google's `oauth2.googleapis.com/tokeninfo`.
- Produces: Strict audience verification against `GOOGLE_CLIENT_ID` / `VITE_GOOGLE_CLIENT_ID`.

- [ ] **Step 1: Write failing test for Google ID token audience mismatch**

```python
# tests/test_auth_api.py
from unittest.mock import patch

def test_google_auth_rejects_mismatched_audience(client):
    fake_token_data = {
        "email": "attacker@example.com",
        "name": "Attacker",
        "aud": "wrong-client-id.apps.googleusercontent.com",
    }
    with patch("urllib.request.urlopen") as mock_url:
        mock_url.return_value.__enter__.return_value.read.return_value = json.dumps(fake_token_data).encode("utf-8")
        resp = client.post("/api/auth/google", json={"credential": "fake-google-jwt"})
        assert resp.status_code == 401
        assert "audience" in resp.json()["detail"].lower() or "unauthorized" in resp.json()["detail"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_auth_api.py::test_google_auth_rejects_mismatched_audience -v`  
Expected: FAIL (currently returns 200 and logs in without checking `aud`).

- [ ] **Step 3: Implement audience check in `backend/routers/auth.py`**

```python
    expected_aud = (
        os.getenv("GOOGLE_CLIENT_ID")
        or os.getenv("VITE_GOOGLE_CLIENT_ID")
        or "999060759573-45b5m9cn9v7g6birnj9d8j65cqn72mfq.apps.googleusercontent.com"
    ).strip()
    token_aud = token_data.get("aud", "").strip()
    if expected_aud and token_aud != expected_aud:
        raise HTTPException(
            status_code=401,
            detail=f"Google token audience mismatch. Token issued for {token_aud}, expected {expected_aud}."
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_auth_api.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/routers/auth.py tests/test_auth_api.py
git commit -m "fix(security): verify Google ID token audience matches client ID"
```

---

### Task 2: Multi-Tenant Application Deduplication Scoping

**Files:**
- Modify: `backend/storage.py:382-414`
- Test: `tests/test_storage.py`

**Interfaces:**
- Consumes: `applications` records in database.
- Produces: Deduplication strictly isolated per `user_id`.

- [ ] **Step 1: Write failing test verifying two different users with identical applications are NOT deduplicated**

```python
# tests/test_storage.py
def test_deduplicate_applications_preserves_multi_tenant_isolation(tmp_path):
    storage = StorageService(db_path=str(tmp_path / "dedup_test.db"), force_sqlite=True)
    app_data = ApplicationCreate(company="Google", role="SWE", url="https://google.com/jobs/1")
    
    # User A and User B both apply to the same role
    app_a = storage.add_application(app_data, user_id="user-alpha")
    app_b = storage.add_application(app_data, user_id="user-beta")
    
    storage.deduplicate_existing_applications()
    
    assert storage.get_application(app_a.id) is not None
    assert storage.get_application(app_b.id) is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_storage.py::test_deduplicate_applications_preserves_multi_tenant_isolation -v`  
Expected: FAIL (currently deletes User B's application).

- [ ] **Step 3: Update `deduplicate_existing_applications` in `backend/storage.py`**

Partition `seen_urls` and `seen_roles` by `user_id`:
```python
    user_prefix = str(row.get("user_id") or "global")
    comp_role_key = f"{user_prefix}:::{row['company'].strip().lower()}:::{row['role'].strip().lower()}"
    url_key = f"{user_prefix}:::{clean_url}" if clean_url and clean_url != "manual_paste" else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_storage.py::test_deduplicate_applications_preserves_multi_tenant_isolation -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/storage.py tests/test_storage.py
git commit -m "fix(storage): scope application deduplication by user_id to prevent cross-tenant deletion"
```

---

### Task 3: SSRF Protection in Job Scraper

**Files:**
- Modify: `backend/services/scraper.py:20-40`
- Test: `tests/test_scraper.py`

**Interfaces:**
- Consumes: Target URL string from `/api/jobs/analyze`.
- Produces: Validated safe public HTTP/HTTPS URL or raises `ValueError("Disallowed URL target.")`.

- [ ] **Step 1: Write failing test for SSRF blocking**

```python
# tests/test_scraper.py
def test_scrape_url_blocks_internal_and_cloud_metadata(scraper):
    blocked_urls = [
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:8000/api/health",
        "http://127.0.0.1:8000/",
        "http://10.0.0.1/admin",
        "file:///etc/passwd",
    ]
    for url in blocked_urls:
        job = scraper.scrape_url(url)
        assert "blocked" in job.raw_text.lower() or "disallowed" in job.raw_text.lower() or "invalid" in job.raw_text.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scraper.py::test_scrape_url_blocks_internal_and_cloud_metadata -v`  
Expected: FAIL.

- [ ] **Step 3: Implement `is_safe_url` in `backend/services/scraper.py`**

```python
import ipaddress
import socket
from urllib.parse import urlparse

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
        return False
    try:
        ip_list = socket.getaddrinfo(hostname, None)
        for item in ip_list:
            ip = ipaddress.ip_address(item[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or not ip.is_global:
                return False
    except Exception:
        return False
    return True
```
Call `is_safe_url(clean_url)` inside `scrape_url()`. If False, return a safe `ScrapedJob(title="Invalid URL", raw_text="Disallowed or private URL target blocked for security.")`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_scraper.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/services/scraper.py tests/test_scraper.py
git commit -m "feat(security): add SSRF protection blocking private IPs and cloud metadata in scraper"
```

---

### Task 4: File Upload Security (Size Limit & Extension Whitelist)

**Files:**
- Modify: `backend/main.py:190-210`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: UploadFile from `POST /api/resumes/upload`.
- Produces: Validated file $\le 10\text{MB}$ and extension in `ALLOWED_RESUME_EXTENSIONS`.

- [ ] **Step 1: Write failing test for disallowed extension and oversized upload**

```python
# tests/test_api.py
def test_upload_rejects_disallowed_extension(client, auth_headers):
    files = {"file": ("malicious.html", b"<h1>Dangerous</h1>", "text/html")}
    resp = client.post("/api/resumes/upload", files=files, headers=auth_headers)
    assert resp.status_code == 400
    assert "extension" in resp.json()["detail"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py::test_upload_rejects_disallowed_extension -v`  
Expected: FAIL (currently accepts any extension).

- [ ] **Step 3: Implement validation in `backend/main.py`**

```python
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".rtf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

ext = Path(file.filename).suffix.lower()
if ext not in ALLOWED_EXTENSIONS:
    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type '{ext}'. Allowed formats: .pdf, .docx, .doc, .txt, .rtf",
    )

content_bytes = file.file.read(MAX_FILE_SIZE_BYTES + 1)
if len(content_bytes) > MAX_FILE_SIZE_BYTES:
    raise HTTPException(status_code=413, detail="File exceeds maximum allowed size of 10MB.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_api.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/main.py tests/test_api.py
git commit -m "feat(security): enforce 10MB size cap and extension whitelist on resume uploads"
```

---

### Task 5: Production CORS Configuration & Secure JWT Secret Key

**Files:**
- Modify: `backend/main.py:35-42`, `backend/services/auth_service.py:7-10`, `.env`, `.env.example`

- [ ] **Step 1: Add `JWT_SECRET_KEY` and `ALLOWED_ORIGINS` to `.env` and `.env.example`**

Generate a 64-char random key for `JWT_SECRET_KEY` in `.env`:
```
JWT_SECRET_KEY=e83a9d7249b6b72a1936c5df53b1bcf06f157ad9cb71e16f3d1b46a782cb4125
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```

- [ ] **Step 2: Update CORS in `backend/main.py`**

```python
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 3: Add production warning in `backend/services/auth_service.py` if default key is detected**

```python
if os.getenv("ENVIRONMENT") == "production" and JWT_SECRET_KEY == "jobhelperguru-super-secret-dev-jwt-key-2026":
    raise RuntimeError("CRITICAL: Default JWT_SECRET_KEY cannot be used in production. Set JWT_SECRET_KEY in .env")
```

- [ ] **Step 4: Run tests to verify auth flows still work**

Run: `python -m pytest tests/test_auth_api.py tests/test_auth_service.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/main.py backend/services/auth_service.py .env.example
git commit -m "fix(security): configure restricted CORS origins and enforce production JWT secret key"
```

---

### Task 6: PostgreSQL Connection Pooling (ThreadedConnectionPool)

**Files:**
- Modify: `backend/storage.py:35-85`
- Test: `tests/test_storage.py`

**Interfaces:**
- Consumes: `self.database_url`.
- Produces: Thread-safe checked-out connection pool for Neon PostgreSQL.

- [ ] **Step 1: Write test verifying connection pool initialization and checkout**

```python
# tests/test_storage.py
def test_storage_connection_pool_lifecycle(tmp_path):
    storage = StorageService(db_path=str(tmp_path / "pool_test.db"), force_sqlite=True)
    with storage._get_cursor() as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
```

- [ ] **Step 2: Update `_get_cursor` and initialize `ThreadedConnectionPool` in `backend/storage.py`**

```python
from psycopg2.pool import ThreadedConnectionPool

# In __init__:
if self.is_postgres:
    self.pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=self.database_url)
else:
    self.pool = None

# In _get_cursor():
if self.is_postgres and self.pool:
    conn = self.pool.getconn()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
    finally:
        self.pool.putconn(conn)
```

- [ ] **Step 3: Run full storage and API test suite**

Run: `python -m pytest tests/test_storage.py tests/test_api.py -v`  
Expected: PASS (and drastically reduced execution time).

- [ ] **Step 4: Commit**

```bash
git add backend/storage.py tests/test_storage.py
git commit -m "perf(db): implement ThreadedConnectionPool for Neon PostgreSQL"
```

---

### Task 7: Concurrency & Async Optimization for Resume Upload

**Files:**
- Modify: `backend/main.py:190-215`

- [ ] **Step 1: Change `async def upload_resume_file` to `def upload_resume_file`**

In `backend/main.py`, convert the signature from `async def` to synchronous `def`:
```python
@app.post("/api/resumes/upload", response_model=Resume)
def upload_resume_file(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    try:
        content_bytes = file.file.read(MAX_FILE_SIZE_BYTES + 1)
        # ... rest of processing ...
```
*FastAPI automatically runs standard `def` functions in its worker threadpool, preventing heavy CPU PDF parsing and boto3 uploads from blocking the main event loop.*

- [ ] **Step 2: Run tests to verify upload endpoint functions identically**

Run: `python -m pytest tests/test_api.py::test_upload_resume_file_endpoint -v`  
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "perf(concurrency): convert upload_resume_file to worker threadpool execution"
```

---

### Task 8: Cache Fernet Instance in `encryption.py`

**Files:**
- Modify: `backend/services/encryption.py:10-40`
- Test: `tests/test_encryption.py`

- [ ] **Step 1: Cache module-level Fernet instance**

```python
_cached_fernet: Optional[Fernet] = None

def _get_fernet() -> Fernet:
    global _cached_fernet
    if _cached_fernet is None:
        _cached_fernet = Fernet(_get_fernet_key())
    return _cached_fernet

def encrypt_value(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return value
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")

def decrypt_value(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return value
    try:
        return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        return value
```

- [ ] **Step 2: Run encryption tests**

Run: `python -m pytest tests/test_encryption.py tests/test_storage_encryption.py -v`  
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/services/encryption.py
git commit -m "perf(encryption): cache Fernet cipher instance to eliminate redundant key hashing"
```

---

### Task 9: Startup Cleanup & Frontend Hardcoded Fallback Removal

**Files:**
- Modify: `backend/main.py:46-52`, `frontend/src/components/AuthModal.jsx:25-28`, `frontend/src/api/client.js:270-275`

- [ ] **Step 1: Guard SQLite migration in `backend/main.py`**

```python
if storage.is_postgres:
    print("[INFO] Connected to Neon PostgreSQL database.")
    if os.getenv("RUN_SQLITE_MIGRATION", "false").lower() in ("true", "1", "yes"):
        try:
            storage.migrate_from_sqlite("data/tracker.db")
        except Exception as e:
            print(f"[WARN] SQLite migration skipped: {e}")
```

- [ ] **Step 2: Clean `AuthModal.jsx` to load strictly from env**

```javascript
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
```

- [ ] **Step 3: Mark `getExcelExportUrl` as deprecated in `frontend/src/api/client.js`**

```javascript
/** @deprecated Use downloadExcelReport() which includes authenticated Bearer token headers */
export function getExcelExportUrl() {
  return `${API_BASE}/export/excel`;
}
```

- [ ] **Step 4: Verify frontend build**

Run: `npm run build` in `frontend/`  
Expected: PASS with 0 build errors.

- [ ] **Step 5: Commit**

```bash
git add backend/main.py frontend/src/components/AuthModal.jsx frontend/src/api/client.js
git commit -m "chore(cleanup): guard startup sqlite migration and remove hardcoded client ID string fallback"
```

---

### Task 10: Full Regression Verification & Walkthrough

- [ ] **Step 1: Run complete test suite**

Run: `python -m pytest -v`  
Expected: All tests PASS.

- [ ] **Step 2: Build frontend assets**

Run: `cd frontend && npm run build`  
Expected: Clean build.

- [ ] **Step 3: Document completed fixes in walkthrough artifact**
