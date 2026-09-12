# Step-by-Step Production Launch Guide

This guide walks you through every action required on your end to launch JobHelperGuru to production.

---

## Overview of Tasks

1. [Step 1: Set Up Brevo Transactional Email](#step-1-set-up-brevo-transactional-email) (5 minutes)
2. [Step 2: Generate Production Cryptographic Secrets](#step-2-generate-production-cryptographic-secrets) (1 minute)
3. [Step 3: Database & Object Storage Credentials](#step-3-database--object-storage-credentials) (5 minutes)
4. [Step 4: Run Database Repair & Migration](#step-4-run-database-repair--migration) (2 minutes)
5. [Step 5: Push Branch to GitHub & Deploy](#step-5-push-branch-to-github--deploy) (3 minutes)
6. [Step 6: Live Smoke Test Checklist](#step-6-live-smoke-test-checklist) (5 minutes)

---

## Step 1: Set Up Brevo Transactional Email

JobHelperGuru uses Brevo (formerly Sendinblue) to deliver account verification emails and password reset links. Brevo provides 300 free emails per day with high deliverability.

### 1. Create / Log In to Brevo
1. Go to [https://www.brevo.com](https://www.brevo.com) and sign up or sign in.
2. Complete your organization details (you can use "JobHelperGuru").

### 2. Verify Your Sender Email Address
1. In the top-right corner, click your account name and select **Senders, Domains & Dedicated IPs** (or go directly to [https://app.brevo.com/senders](https://app.brevo.com/senders)).
2. Click **Add a Sender**.
3. Enter:
   - **Sender Name**: `JobHelperGuru Support`
   - **Sender Email**: Your email (e.g. `sourav.chandhok01@gmail.com` or your domain email `support@jobhelper.guru`).
4. Brevo will send a 6-digit verification code to that email address. Enter the code in Brevo to verify.

### 3. Generate Your Brevo API Key
1. In the top-right account dropdown, click **SMTP & API** (or visit [https://app.brevo.com/settings/keys/api](https://app.brevo.com/settings/keys/api)).
2. Go to the **API Keys** tab.
3. Click **Generate a new API key**.
4. Name it `jobhelperguru-production`.
5. Click **Generate** and immediately copy the key (it starts with `xkeysib-...`). Save it securely.

### Your Brevo Configuration:
```env
EMAIL_TRANSPORT=brevo
BREVO_API_KEY=xkeysib-your-copied-api-key
BREVO_SENDER_EMAIL=your-verified-sender-email@gmail.com
BREVO_SENDER_NAME=JobHelperGuru Support
```

---

## Step 2: Generate Production Cryptographic Secrets

You need two random high-entropy secrets for production. Run these two quick one-liners directly in your terminal:

### 1. Generate `JWT_SECRET` (For signing user auth tokens):
Run in PowerShell / Terminal:
```bash
python -c "import secrets; print('JWT_SECRET=' + secrets.token_hex(32))"
```
*Copy the generated 64-character string.*

### 2. Generate `ENCRYPTION_KEY` (For encrypting stored LLM provider keys):
Run in PowerShell / Terminal:
```bash
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```
*Copy the generated 44-character base64 string.*

---

## Step 3: Database & Object Storage Credentials

### 1. PostgreSQL Database (Neon Serverless Postgres)
If you are using Neon (free tier Postgres):
1. Log in to [https://console.neon.tech](https://console.neon.tech).
2. Select your project (or click **New Project** -> name: `jobhelperguru-db`).
3. Under **Dashboard**, copy your connection string:
   ```
   postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require
   ```
4. Set this as `DATABASE_URL`.

### 2. Cloud Storage for Resume Files (AWS S3 or Cloudflare R2)
If you want resume PDF uploads stored in the cloud:
- **Cloudflare R2** (Recommended: 10GB free, $0 egress fees):
  - In Cloudflare Dashboard -> R2 -> Create bucket: `jobhelperguru-resumes`.
  - Create API Token with Admin Read/Write permissions.
  - Set:
    ```env
    STORAGE_BACKEND=s3
    S3_BUCKET_NAME=jobhelperguru-resumes
    AWS_ACCESS_KEY_ID=your-r2-access-key-id
    AWS_SECRET_ACCESS_KEY=your-r2-secret-access-key
    AWS_REGION=auto
    S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
    ```
- **Local Storage Alternative** (If running locally or with a persistent disk):
  ```env
  STORAGE_BACKEND=local
  ```

---

## Step 4: Run Database Repair & Migration

Before sending traffic to your production database, run the automated repair and migration scripts from your repository root.

### 1. Clean Local Data Inconsistencies
Run this command to audit and fix any corrupted records in your local `data/tracker.db`:
```pwsh
python -m backend.repair_data --apply
```
*Expected output: `Audit results: {'corrupt_applications': ..., 'corrupt_settings': ..., 'orphaned_attachments': ..., 'applied': True}`.*

### 2. Migrate Data to PostgreSQL
Set your production `DATABASE_URL` in your terminal session and run the migration:

**In PowerShell:**
```pwsh
$env:DATABASE_URL = "postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require"

# First run a dry-run check (read-only):
python -m backend.migrate --source data/tracker.db --dest $env:DATABASE_URL --dry-run

# Then apply the migration to production:
python -m backend.migrate --source data/tracker.db --dest $env:DATABASE_URL --apply
```

**In Linux / macOS Bash:**
```bash
export DATABASE_URL="postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require"

# First run a dry-run check (read-only):
python -m backend.migrate --source data/tracker.db --dest "$DATABASE_URL" --dry-run

# Then apply the migration to production:
python -m backend.migrate --source data/tracker.db --dest "$DATABASE_URL" --apply
```

Verify the output shows `Mode: APPLIED` and `Errors encountered:` is not present.

---

## Step 5: Push Branch to GitHub & Deploy

All fixes have been committed locally to branch `launch-readiness`.

### 1. Push `launch-readiness` to GitHub
Run in PowerShell:
```pwsh
git push origin launch-readiness
```

### 2. Merge into `main` (When ready to release)
You can either open a Pull Request on GitHub and merge it, or merge locally:
```pwsh
git checkout main
git merge launch-readiness
git push origin main
```

### 3. Configure Production Environment Variables on Host
On your hosting dashboard (e.g. Render, Google Cloud Run, or Railway), enter the environment variables gathered from Steps 1, 2, and 3:

```env
ENVIRONMENT=production
APP_BASE_URL=https://your-domain.com
JWT_SECRET=<generated-in-step-2>
ENCRYPTION_KEY=<generated-in-step-2>
DATABASE_URL=<your-neon-postgres-url>
EMAIL_TRANSPORT=brevo
BREVO_API_KEY=<generated-in-step-1>
BREVO_SENDER_EMAIL=<verified-sender-in-step-1>
BREVO_SENDER_NAME=JobHelperGuru Support
STORAGE_BACKEND=s3
S3_BUCKET_NAME=jobhelperguru-resumes
AWS_ACCESS_KEY_ID=<your-storage-key>
AWS_SECRET_ACCESS_KEY=<your-storage-secret>
AWS_REGION=auto
GOOGLE_CLIENT_ID=<your-google-oauth-client-id>
```

---

## Step 6: Live Smoke Test Checklist

Once the production service is live, perform this 5-minute end-to-end verification:

### Test 1: User Registration & Email Delivery
1. Open your production site in an incognito window.
2. Register a new account using your real email address.
3. Check your email inbox for the message: **"Verify your email - JobHelperGuru"**.
4. Click the verification button in the email.
5. Confirm it loads `https://your-domain.com/verify-email?token=...` and displays:
   **"Email verified successfully! You can now log in."** (no 404 error).

### Test 2: Password Recovery
1. On the login screen, click **Forgot password?**.
2. Enter your email and submit.
3. Check your inbox for the reset link: **"Reset your password - JobHelperGuru"**.
4. Click the link and enter a new password.
5. Confirm successful reset and log in with the new password.

### Test 3: Resume Management & Unicode Download
1. Log in to your account.
2. Go to **Resumes** and upload a resume (PDF or DOCX).
3. Verify the resume appears in your Resume Library.
4. Click **Download** and verify the file downloads intact with the correct filename.
5. Delete the resume and confirm it is removed cleanly.

### Test 4: Job Analyzer & Duplicate Detection
1. In the **Analyzer**, paste a job URL (e.g., from LinkedIn or Greenhouse) and click **Analyze Job**.
2. Click **Add to Pipeline**.
3. Now paste the exact same job URL into the input field again.
4. Verify the inline notice appears immediately:
   `Already tracked: [Company] ([Role]) [[Status]]`.
5. Switch to the **Application Pipeline** tab and switch to **Kanban view**.
6. Resize your browser down to mobile width (or open on your phone) and verify the columns scroll smoothly horizontally without clipping.

---

When all 6 steps are complete, JobHelperGuru is officially public-launch ready!
