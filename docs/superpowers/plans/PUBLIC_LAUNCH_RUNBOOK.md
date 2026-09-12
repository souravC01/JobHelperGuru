# Public Launch Runbook

This runbook defines the operational deployment, migration, and pre-flight verification procedures for releasing JobHelperGuru to production.

---

## 1. Required Environment Variables

Ensure the following environment variables are set in production before starting the service:

### Core Configuration
- `PORT`: HTTP port to bind (default `8000` or assigned by host).
- `APP_BASE_URL`: Public canonical base URL (e.g. `https://jobhelper.guru`).
- `ENVIRONMENT`: Set to `production`.
- `JWT_SECRET`: High-entropy secret key for signing user authentication tokens.
- `ENCRYPTION_KEY`: Fernet encryption key for securing stored provider API keys (base64 url-safe 32-byte key).

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string (e.g. `postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require`).
- `JOB_HELPER_DB`: Optional path to local SQLite database when running outside PostgreSQL.

### Email Delivery (Brevo)
- `EMAIL_TRANSPORT`: Set to `brevo` for production delivery.
- `BREVO_API_KEY`: API key generated from Brevo account dashboard (SMTP & API -> API Keys).
- `BREVO_SENDER_EMAIL`: Verified sender email address registered with Brevo.
- `BREVO_SENDER_NAME`: Display name for outbound emails (e.g. `JobHelperGuru Support`).

### Storage Backend (S3 / Cloudflare R2 / GCS)
- `STORAGE_BACKEND`: `s3` (or `local` in staging environments).
- `S3_BUCKET_NAME`: Name of the private object storage bucket.
- `S3_ENDPOINT_URL`: Endpoint URL for S3-compatible providers (leave empty for AWS S3).
- `AWS_ACCESS_KEY_ID`: IAM access key.
- `AWS_SECRET_ACCESS_KEY`: IAM secret key.
- `AWS_REGION`: Storage region (e.g. `auto` or `us-east-1`).

### OAuth & Security
- `GOOGLE_CLIENT_ID`: Google OAuth client ID for SSO.
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins (e.g. `https://jobhelper.guru`).

---

## 2. Pre-Deployment Data Operations

### Step A: Audit and Repair Inconsistent Data
Before performing migrations, run the automated repair utility to resolve any legacy schema inconsistencies or orphaned attachments:

1. Dry run (read-only audit):
   ```bash
   python -m backend.repair_data
   ```
2. Apply repairs:
   ```bash
   python -m backend.repair_data --apply
   ```

### Step B: Database Migration to Production
Migrate data from local/staging SQLite database to the target PostgreSQL / Neon instance:

1. Verify record counts with dry-run:
   ```bash
   python -m backend.migrate --source data/tracker.db --dest "$DATABASE_URL" --dry-run
   ```
2. Execute migration:
   ```bash
   python -m backend.migrate --source data/tracker.db --dest "$DATABASE_URL" --apply
   ```
3. Verify migration summary logs:
   - Check `Users`, `Applications`, `Resumes`, `Attachments`, `User Settings`, `Global Settings`, and `Provider Profiles`.
   - Ensure `errors` list is empty.

---

## 3. Pre-Flight Verification Checklist

Run through the following verification scenarios prior to directing public traffic:

### 1. User Registration & Email Delivery
- Register a new user account with a valid test email.
- Verify delivery of verification email via Brevo transactional API.
- Click the verification link and confirm the SPA deep link loads `/verify-email?token=...` correctly without 404.

### 2. Account Recovery & Deep Link Navigation
- Request a password reset.
- Confirm reset email arrives with one-time token.
- Access `/reset-password?token=...` and verify form loads and completes password update.

### 3. Resume Lifecycle & Quota Enforcement
- Upload a PDF/DOCX resume.
- Verify file metadata is recorded and storage object is created.
- Download the resume and verify Unicode filename preservation (`filename*` RFC 5987).
- Verify upload quota enforces maximum 10 active resumes per user.
- Delete the resume and confirm idempotent cleanup in database and object storage.

### 4. Job Pipeline & Duplicate Detection
- Ingest a job URL into the Analyzer.
- Enter a duplicate URL already in the pipeline and verify inline notice displays: `Already tracked: [Company] ([Role]) [[Status]]`.
- Verify Kanban board horizontally scrolls smoothly with clear column widths on mobile and desktop viewports.

### 5. Outbound Connection & SSRF Protection
- Ensure requests targeting internal or link-local IP addresses (`127.0.0.1`, `169.254.169.254`, `10.0.0.0/8`, `192.168.0.0/16`) are blocked with HTTP 400.

### 6. Concurrency & Rate Limiting
- Confirm rate limiting returns `Retry-After` header when limit is exceeded.
- Confirm frontend automatically parses `Retry-After` and handles throttling transparently.

---

## 4. Rollback Plan

If unexpected failures occur during launch:
1. Revert DNS/routing to previous stable environment.
2. In the event of a database rollback, point `DATABASE_URL` back to the previous snapshot or restore from the pre-migration dump.
3. Review application logs via `journalctl` or hosting platform log stream.
