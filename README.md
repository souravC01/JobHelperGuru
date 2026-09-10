# JobHelperGuru 🚀
### Intelligent Job Application Assistant, ATS Optimizer & Excel Tracker

[![Live Demo](https://img.shields.io/badge/Live%20Demo-jobhelperguru.onrender.com-0a66c2?style=for-the-badge&logo=render&logoColor=white)](https://jobhelperguru.onrender.com)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-160%2F160%20Passing-057642?style=for-the-badge)](tests/)
[![Frontend Tests](https://img.shields.io/badge/Frontend%20Tests-17%2F17%20Passing-057642?style=for-the-badge)](frontend/src/test/)
[![CI/CD Pipeline](https://github.com/souravC01/JobHelperGuru/actions/workflows/ci.yml/badge.svg)](https://github.com/souravC01/JobHelperGuru/actions/workflows/ci.yml)

🌐 **Live Application:** [https://jobhelperguru.onrender.com](https://jobhelperguru.onrender.com)

**JobHelperGuru** is an AI-powered copilot for your job hunt. Paste any job posting URL or job description to extract core qualifications, identify missing ATS keywords, rank multiple resumes to identify the best fit, optimize resume bullet points using the **Resume Guide 2.0 / BulletSkill** framework, generate tailored 3-paragraph cover letters with Word (.docx) and PDF downloads, and track your applications with 1-click **Excel (.xlsx)** export.

---

## Key Features

1. **Smart Job Ingestion & Web Scraper:**
   - Paste a job link (LinkedIn, Greenhouse, Lever, Indeed, Workday, etc.) or raw job text directly.
   - Automatically extracts Company, Title, Location, Work Mode (Remote/Hybrid/Onsite), Salary Range, and Experience Level.
   - Built-in SSRF protection prevents network abuse against private addresses or internal cloud metadata endpoints.

2. **Categorized Skills Matrix & ATS Keyword Bank:**
   - Categorizes skills into **Required Must-Haves**, **Preferred Nice-to-Haves**, **Tech Stack & Tools**, and **Soft Skills**.
   - Generates a high-frequency **ATS Keyword Bank** with a 1-click "Copy All" button.

3. **Multi-Resume Vault, Reader & Best-Fit Matcher:**
   - Upload and store multiple tailored resumes (.pdf, .docx, .doc, .txt, .rtf, .md) backed by Cloudflare R2 object storage or local disk storage.
   - **Direct Streaming Downloads:** Fast, authenticated file downloads directly through FastAPI, avoiding cross-origin presigned URL issues.
   - **Graceful Fallback:** If an uploaded binary file is ever missing from cloud storage, the system automatically synthesizes a clean .docx document from saved resume text and alerts the user transparently.
   - **Inline Renaming & Text Overrides:** Rename resumes in place and preserve manual text edits across uploads.
   - **Full-Screen Reader:** Inspect extracted text with word count stats, copy actions, and instant preview.
   - **Intelligent Best-Fit Ranking:** Compares all vault resumes against target jobs, computes match percentages (0-100%), and highlights matched vs. missing skills.

4. **BulletSkill 2.0 Resume Bullet Optimizer (powered by `Bulletskill.md`):**
   - Click any missing keyword to generate targeted resume bullet points.
   - Enforces the structured framework: **WHAT/Keyword + HOW it was used + RESULT and/or REASON**.
   - Generates 3 alternative variations:
     - **Candidate A:** ATS-focused
     - **Candidate B:** Concise
     - **Candidate C:** Technical and result-focused
   - Strict claim classification:
     - `VERIFIED`: Claims directly supported by your resume context.
     - `UNVERIFIED_SKILL`: Flags missing skills with clear assumptions and confirmation prompts.
     - `UNVERIFIED_METRIC`: Uses placeholders like `[X%]`, never fabricating unsupported metrics.

5. **Tailored 3-Paragraph Cover Letter & Outreach Generator:**
   - Generates a full 3-paragraph application pitch tailored to the target role and matched resume evidence:
     - **Salutation:** Formal greeting to the hiring team.
     - **Paragraph 1:** Role hook, company interest, and domain overview.
     - **Paragraph 2:** Concrete technical achievements and evidence matching target requirements.
     - **Paragraph 3:** Value-add proposition and proactive call to action.
     - **Sign-Off:** Professional closing with candidate name.
   - **Account-Derived Candidate Name:** Automatically derives the candidate name from your account profile (Google account name or registration name) rather than the resume filename.
   - **Zero Em-Dash Standard:** Formatted with standard ASCII punctuation for clean typography across all email and ATS clients.
   - **Word (.docx) & PDF Export:** Export polished Microsoft Word (.docx) files with 1-inch margins and styling, or generate printable PDFs directly.
   - **Networking Notes:** Generates a suggested email subject line and a concise LinkedIn / recruiter InMail note (<300 characters) with 1-click copy buttons.

6. **Application Tracker (Table & Kanban Views):**
   - Track applications across stages: `Wishlist` ➔ `Applied` ➔ `Interviewing` ➔ `Offered` ➔ `Rejected` ➔ `Archived`.
   - Supports both interactive tabular list and drag-and-drop Kanban board views.
   - Timezone-safe local dates prevent UTC rollover discrepancies.
   - Automated **Follow-Up Reminder Banner** alerting you to applications due today or past due.

7. **Professional Excel (.xlsx) Export with Security Protections:**
   - 1-click export of a styled, multi-sheet Excel workbook (`job_tracker.xlsx`).
   - Features frozen headers, deep navy corporate styling, auto-fitted columns, clickable hyperlinks, and color-coded status badges.
   - Spreadsheet formula injection defenses sanitize cells starting with `=`, `+`, `-`, or `@` to protect against malicious workbook execution.

8. **Multi-Provider AI Engine & Secure Encryption:**
   - Connect to **TokenRouter**, **OpenRouter**, **MiniMax**, **OpenAI**, **Anthropic**, or local **Ollama** models in the Settings modal.
   - Full support for reasoning/thinking models (such as `GLM-5.3` and `DeepSeek-R1`) with automatic `<think>` tag and `reasoning_content` handling.
   - User provider keys are encrypted at rest using server-side authenticated Fernet encryption (AES-128-CBC + HMAC-SHA256) and masked on retrieval.
   - Built-in **heuristic NLP engine** with 600+ skills taxonomy operates free offline without requiring an external AI API key.

9. **Multi-Tenant Architecture & Security Hardening:**
   - User authentication via Google One-Tap / OAuth 2.0 or email/password (JWT + bcrypt).
   - Multi-tenant data isolation on Neon Serverless PostgreSQL with automatic fallback to local SQLite.
   - Anti-automation sliding-window rate limiters protecting authentication, AI generation, and web scraping endpoints.
   - Strict user-scoping across all application and resume endpoints prevents cross-account data leaks.

---

## Quick Start (Run Locally)

If you want to run JobHelperGuru locally on your machine:

### 1. Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Launch the Application
```bash
python run.py
```
Open your browser to: **[http://localhost:8000](http://localhost:8000)**

---

## Development Mode (Live Hot Reload)

For active frontend and backend development with hot-reloading:

1. **Start the backend server:**
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```
2. **Start the frontend Vite server:**
   ```bash
   cd frontend
   npm run dev
   ```
   Open: **[http://localhost:5173](http://localhost:5173)**

---

## Running Automated Tests

### Backend Test Suite (Pytest)
Run all 160 unit and integration tests:
```bash
python -m pytest tests/ -v
```
Or run quietly:
```bash
python -m pytest -q
```

### Frontend Test Suite (Vitest)
Run all 17 component and workflow tests:
```bash
cd frontend
npm run test:run
```

### Frontend Production Build
Validate production bundling:
```bash
cd frontend
npm run build
```

---

## Database Migrations

Database migrations are explicit, transactional, and non-destructive:

```bash
# Perform a dry-run check without applying changes:
python -m backend.migrate --dry-run

# Apply pending migrations:
python -m backend.migrate
```

---

## Production Deployment

JobHelperGuru is configured for automated containerized deployment on Render with multi-stage Docker builds.

For configuration details and environment setup:
- **[Render Deployment Guide](docs/RENDER_DEPLOYMENT_GUIDE.md)**
- **[Render Blueprint Specification](render.yaml)**
- **[Production Environment Template](.env.production.example)**

---

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, Neon Serverless PostgreSQL / SQLite, Cloudflare R2 / Local Disk Storage, python-docx, openpyxl, cryptography (Fernet), OpenAI SDK
- **Frontend:** React 18, Vite, Tailwind CSS v4, Lucide Icons, Google Identity Services (OAuth 2.0)
- **Testing:** Pytest, pytest-asyncio, Vitest, React Testing Library
- **Deployment:** Render Web Service, Multi-stage Docker
