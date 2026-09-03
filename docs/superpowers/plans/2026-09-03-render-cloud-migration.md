# Render Cloud Deployment & Keep-Alive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package and deploy JobHelperGuru as a unified full-stack web service on Render Free Tier (FastAPI + React + Neon PostgreSQL + Cloudflare R2), configure Google Cloud OAuth and environment variables, and establish 24/7 keep-alive monitoring via UptimeRobot at zero cost.

**Architecture:** Multi-stage Docker containerization and unified native build configuration that builds the React frontend (`frontend/dist`) and mounts it in FastAPI (`backend/main.py`), serving both API endpoints and the corporate modern UI from a single Render Web Service instance on `$PORT`.

**Tech Stack:** Render Web Service, Docker / Render Native Python+Node, FastAPI, Vite / React, Neon PostgreSQL, Cloudflare R2, Google OAuth GIS, UptimeRobot.

---

## Global Constraints

- Zero em-dashes: visible UI text and docs must use regular hyphens (`-`), never `—` or `–`.
- Zero-cost architecture: must fit entirely within Render Free Tier (single web service instance) and Neon / Cloudflare R2 free allowances.
- Single domain: frontend and backend share the Render service URL (`https://<app>.onrender.com`), eliminating cross-origin CORS latency and complex domain routing.
- Preserve backward compatibility: local development workflow (`python -m uvicorn ...` + `npm run dev`) must remain fully functional.

---

### Task 1: Root Production Requirements Specification

**Files:**
- Create: `requirements.txt` (repository root)
- Modify: `backend/requirements.txt`

**Interfaces:**
- Consumes: Python dependencies required across `backend/`
- Produces: Root `requirements.txt` for Render build detection

- [x] **Step 1: Create root `requirements.txt` with production dependencies**
  Include `fastapi`, `uvicorn[standard]`, `gunicorn`, `pydantic`, `psycopg2-binary`, `boto3`, `bcrypt`, `pyjwt`, `cryptography`, `trafilatura`, `beautifulsoup4`, `requests`, `openai`, `pypdf`, `python-docx`, `openpyxl`, `python-multipart`, `python-dotenv`, `curl_cffi`.

- [x] **Step 2: Verify dependency resolution**
  Run `pip install --dry-run -r requirements.txt` to ensure all packages resolve without conflict.

- [x] **Step 3: Commit Task 1 changes**
  Run `git add requirements.txt backend/requirements.txt && git commit -m "feat(deploy): add root production requirements.txt for Render"`

---

### Task 2: Production Containerization & Build Configuration

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `render.yaml`
- Create: `build.sh`

**Interfaces:**
- Consumes: `frontend/` package.json, `requirements.txt`, `backend/main.py`
- Produces: Production Docker container and Render Blueprint for 1-click deployment

- [x] **Step 1: Create multi-stage `Dockerfile`**
  - Stage 1 (`frontend-builder`): `node:20-alpine`, installs frontend dependencies and runs `npm run build`.
  - Stage 2 (`production`): `python:3.11-slim`, installs Python build tools, copies `requirements.txt` and installs wheels, copies `backend/`, `data/`, and copies built `frontend/dist` into `frontend/dist`.
  - Exposes port `$PORT` (default 8000) and starts with `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.

- [x] **Step 2: Create `.dockerignore`**
  Ignore `.git`, `node_modules`, `frontend/node_modules`, `__pycache__`, `.pytest_cache`, `tests`, `scratch`, `.env`.

- [x] **Step 3: Create `render.yaml` Blueprint**
  Define service `jobhelperguru` as type `web`, env `docker` (or native with `build.sh`), plan `free`, healthCheckPath `/api/health`.

- [x] **Step 4: Create native fallback `build.sh`**
  Add `build.sh` for users choosing Render native Python runtime:
  ```bash
  #!/usr/bin/env bash
  set -o errexit
  pip install -r requirements.txt
  cd frontend && npm install && npm run build && cd ..
  ```

- [x] **Step 5: Test local production build**
  Run `cd frontend && npm run build` and run a quick test curl against `backend.main:app` to confirm `frontend/dist` is mounted at root `/`.

- [x] **Step 6: Commit Task 2 changes**
  Run `git add Dockerfile .dockerignore render.yaml build.sh && git commit -m "feat(deploy): add Dockerfile, render.yaml blueprint and build script"`

---

### Task 3: Production Environment Variables & Google OAuth Configuration Guide

**Files:**
- Create: `.env.production.example`
- Create: `docs/RENDER_DEPLOYMENT_GUIDE.md`

**Interfaces:**
- Consumes: Environment requirements from `backend/main.py`, `backend/storage.py`, `backend/routers/auth.py`
- Produces: Complete, step-by-step deployment and credential configuration documentation

- [ ] **Step 1: Create `.env.production.example`**
  Document each required key with sample placeholders:
  - `DATABASE_URL` (Neon PostgreSQL)
  - `SETTINGS_ENCRYPTION_KEY` (Fernet 32-byte key)
  - `JWT_SECRET_KEY` (HS256 32-byte secret)
  - `ALLOWED_ORIGINS` (Render domain + local fallback)
  - `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

- [ ] **Step 2: Write `docs/RENDER_DEPLOYMENT_GUIDE.md`**
  Include:
  - Step 1: Connecting Render to the GitHub repository (`souravC01/JobHelperGuru`).
  - Step 2: Selecting Docker runtime or Native Python runtime via `render.yaml`.
  - Step 3: Copy-pasting environment variables into the Render Dashboard.
  - Step 4: Updating Google Cloud Console OAuth 2.0 Client ID:
    - Adding `https://<service-name>.onrender.com` to **Authorized JavaScript origins**.
    - Adding `https://<service-name>.onrender.com` to **Authorized redirect URIs**.

- [ ] **Step 3: Commit Task 3 changes**
  Run `git add .env.production.example docs/RENDER_DEPLOYMENT_GUIDE.md && git commit -m "docs(deploy): add production environment template and Render deployment guide"`

---

### Task 4: Zero-Cost Keep-Alive Setup (UptimeRobot) & Health Verification

**Files:**
- Modify: `docs/RENDER_DEPLOYMENT_GUIDE.md`
- Verify: `backend/main.py` (`/api/health`)

**Interfaces:**
- Consumes: `/api/health` endpoint
- Produces: Automated keep-alive instructions to prevent Render free-tier idle spin-down

- [ ] **Step 1: Document UptimeRobot monitor setup**
  - Monitor Type: `HTTP(s)`
  - Friendly Name: `JobHelperGuru Keep-Alive`
  - URL: `https://<your-app>.onrender.com/api/health`
  - Monitoring Interval: `Every 10 minutes` (keeps service alive before Render's 15-minute idle limit)
  - Expected Status: `200 - OK`

- [ ] **Step 2: Test `/api/health` endpoint behavior**
  Verify that `/api/health` executes fast (<50ms), does not perform heavy database queries or auth checks, and returns JSON:
  `{"status": "ok", "app": "JobHelperGuru", "database": "postgresql", "object_storage": "cloudflare_r2"}`.

- [ ] **Step 3: Commit Task 4 changes**
  Run `git add docs/RENDER_DEPLOYMENT_GUIDE.md && git commit -m "docs(deploy): add UptimeRobot keep-alive monitoring instructions"`
