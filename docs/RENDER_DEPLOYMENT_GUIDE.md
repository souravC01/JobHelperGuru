# Render Cloud Deployment & 24/7 Keep-Alive Guide

This guide details how to deploy JobHelperGuru as a unified full-stack web service on Render Free Tier at zero cost ($0.00/month) with automated 24/7 keep-alive monitoring via UptimeRobot.

---

## Architecture Overview

JobHelperGuru is deployed as a single, unified web service:
- **FastAPI Backend + React Frontend:** The React frontend (`frontend/dist`) is built during deployment and mounted directly inside FastAPI at root (`/`). Both the API routes (`/api/*`) and the corporate modern web application run on a single Render web service instance on `$PORT`.
- **Database:** Serverless Neon PostgreSQL (Free Tier, 0.5 GB storage).
- **Binary Storage:** Cloudflare R2 Object Storage (Free Tier, 10 GB storage, zero egress fees) for uploaded PDF and Word documents.
- **Keep-Alive Monitor:** UptimeRobot (Free Tier, 50 monitors) pings `/api/health` every 10 minutes, preventing Render from putting the free instance to sleep after 15 minutes of idle time.

```
+-------------------------------------------------------------------+
|                        Zero-Cost Architecture                     |
|                                                                   |
|   +---------------------+         +---------------------------+   |
|   |     UptimeRobot     | ------> |      Render Web Service   |   |
|   |  (Pings /api/health |         |  FastAPI + React UI on    |   |
|   |   every 10 minutes) |         |  https://app.onrender.com |   |
|   +---------------------+         +-------------+-------------+   |
|                                                 |                 |
|                                   +-------------+-------------+   |
|                                   |                           |   |
|                        +----------v----------+     +----------v--+ |
|                        |   Neon PostgreSQL   |     | Cloudflare  | |
|                        | (Relational Storage)|     |  R2 (Files) | |
|                        +---------------------+     +-------------+ |
+-------------------------------------------------------------------+
```

---

## Prerequisites

Before deploying, ensure you have:
1. A GitHub account with access to `souravC01/JobHelperGuru`.
2. A free account on [Render](https://render.com).
3. A free database on [Neon](https://neon.tech).
4. (Optional) A free bucket on [Cloudflare R2](https://dash.cloudflare.com).
5. A Google Cloud Console project with OAuth 2.0 configured.
6. A free account on [UptimeRobot](https://uptimerobot.com).

---

## Step 1: Deploy to Render

You can deploy using either the automated Blueprint or manual Web Service setup.

### Option A: Render Blueprint (Recommended)
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** in the top navigation and select **Blueprint**.
3. Connect your repository: `souravC01/JobHelperGuru`.
4. Render will detect `render.yaml` automatically.
5. Provide your environment values when prompted (see Step 2 below).
6. Click **Apply**. Render will automatically build the multi-stage Dockerfile and launch your application.

### Option B: Manual Web Service
1. In Render Dashboard, click **New +** and select **Web Service**.
2. Select your repository `souravC01/JobHelperGuru`.
3. Fill in the service configuration:
   - **Name:** `jobhelperguru` (or your preferred name)
   - **Region:** Ohio (US East) or Oregon (US West)
   - **Branch:** `main`
   - **Language / Runtime:** `Docker` (Render automatically uses the root `Dockerfile`)
   - **Instance Type:** `Free`
4. Click **Advanced** and configure Environment Variables (detailed in Step 2).
5. Click **Create Web Service**.

---

## Step 2: Configure Environment Variables in Render

In your Render Service Dashboard, navigate to **Environment** and add the following keys:

| Environment Variable | Description | Example / Generator |
| :--- | :--- | :--- |
| `DATABASE_URL` | Neon PostgreSQL pooled connection string | `postgresql://user:pass@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require` |
| `SETTINGS_ENCRYPTION_KEY` | AES-256 Fernet key for encrypting user API keys | Generate using command below |
| `JWT_SECRET_KEY` | 64-char secret key for JWT session tokens | Generate using command below |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `https://jobhelperguru.onrender.com,http://localhost:5173,http://localhost:8000` |
| `R2_ACCOUNT_ID` | Cloudflare Account ID | Found on Cloudflare Dashboard |
| `R2_ACCESS_KEY_ID` | Cloudflare R2 Access Key ID | Generated in R2 API Tokens |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 Secret Access Key | Generated in R2 API Tokens |
| `R2_BUCKET_NAME` | Cloudflare R2 Bucket Name | `jobhelperguru-resumes` |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Web Client ID | `xxxx.apps.googleusercontent.com` |
| `VITE_GOOGLE_CLIENT_ID` | Matching Google Client ID | `xxxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | From Google Cloud Console |

### Quick Key Generation Commands

Run these on your local terminal to create cryptographic keys:

```bash
# Generate SETTINGS_ENCRYPTION_KEY (Fernet 32-byte key)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate JWT_SECRET_KEY (Hex 64-char secret)
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 3: Update Google Cloud Console OAuth 2.0 Settings

To enable Google One-Tap and Google Sign-In on your Render domain:

1. Open [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials).
2. Select your JobHelperGuru project.
3. Under **OAuth 2.0 Client IDs**, click your Web Client ID.
4. Under **Authorized JavaScript origins**, click **Add URI** and add your Render URL:
   - `https://<your-service-name>.onrender.com`
   - (Keep `http://localhost:5173` and `http://localhost:8000` for local development)
5. Under **Authorized redirect URIs**, click **Add URI** and add:
   - `https://<your-service-name>.onrender.com`
6. Click **Save**.

Changes in Google Cloud Console take effect within 1-2 minutes.

---

## Step 4: Zero-Cost 24/7 Keep-Alive via UptimeRobot

Render's free tier automatically suspends web services after 15 minutes of inactivity. When a new request arrives, a cold start takes approximately 50 seconds.

By setting up an automated HTTP check every 10 minutes, UptimeRobot keeps the service hot 24/7 at $0.00/month.

### Setting Up the UptimeRobot Monitor:

1. Sign up or log in to [UptimeRobot](https://uptimerobot.com).
2. Click **+ Add New Monitor** on the dashboard.
3. Configure the monitor settings:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `JobHelperGuru Keep-Alive`
   - **URL (or IP):** `https://<your-service-name>.onrender.com/api/health`
   - **Monitoring Interval:** `Every 10 minutes`
   - **Monitor Timeout:** `30 seconds`
4. Under **Alert Contacts To Notify**, select your email if you want notifications when the service is down.
5. Click **Create Monitor**.

### Endpoint Verification (`/api/health`):

The `/api/health` endpoint is specifically engineered for low-latency, lightweight keep-alive checks:
- Execution time: < 15ms.
- Does not trigger heavy database write locks or external API calls.
- Expected HTTP status code: `200 OK`.
- Expected JSON response:
  ```json
  {
    "status": "ok",
    "app": "JobHelperGuru",
    "database": "postgresql",
    "object_storage": "cloudflare_r2"
  }
  ```

---

## Step 5: Verification Checklist

Once Render reports "Live" status:

1. **Visit Root Domain:** Navigate to `https://<your-service-name>.onrender.com`. Verify the corporate modern LinkedIn UI loads cleanly without any console errors.
2. **Check API Health:** Open `https://<your-service-name>.onrender.com/api/health` in your browser. Verify the response is `status: ok`.
3. **Test Authentication:**
   - Click **Sign In** in the top navigation.
   - Verify the Google Sign-In button renders.
   - Log in with Google or register with email/password.
4. **Test Core AI Features:**
   - Add your API key (or test with offline mode).
   - Parse a job description and generate tailored resume bullets.
   - Check the Tracker tab to ensure applications save to PostgreSQL.
5. **Verify UptimeRobot Status:** Check UptimeRobot after 10-20 minutes to confirm successful green heartbeat checks.
