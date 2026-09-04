# JobHelperGuru 🚀
### Intelligent Job Application Assistant, ATS Optimizer & Excel Tracker

[![Live Demo](https://img.shields.io/badge/Live%20Demo-jobhelperguru.onrender.com-0a66c2?style=for-the-badge&logo=render&logoColor=white)](https://jobhelperguru.onrender.com)
[![Tests](https://img.shields.io/badge/Tests-62%2F62%20Passing-057642?style=for-the-badge)](tests/)

🌐 **Live Application:** [https://jobhelperguru.onrender.com](https://jobhelperguru.onrender.com)

**JobHelperGuru** is an AI-powered pairs-programmer for your job hunt. Paste any job posting URL or description to extract required qualifications, identify missing ATS keywords, rank multiple resumes to find the best fit, optimize resume bullet points using the **Resume Guide 2.0 / BulletSkill** framework, and track your applications with 1-click **Excel (.xlsx)** export.

---

## Key Features

1. **Smart Job Ingestion & Web Scraper:**
   - Paste a job link (LinkedIn, Greenhouse, Lever, Indeed, Workday, etc.) or paste raw job text directly.
   - Automatically parses Company, Title, Location, Work Mode (Remote/Hybrid/Onsite), Salary Range, and Experience Level.

2. **Categorized Skills Matrix & ATS Keyword Bank:**
   - Separates **Required Must-Haves**, **Preferred Nice-to-Haves**, **Tech Stack & Tools**, and **Soft Skills**.
   - Generates a high-frequency **ATS Keyword Bank** with a 1-click "Copy All" button.

3. **Multi-Resume Vault & Best-Fit Matcher:**
   - Upload and store multiple tailored resumes (.pdf, .docx, .doc, .txt, .rtf) backed by Cloudflare R2 object storage or local storage.
   - **Custom Title Retention:** Specify custom resume profile titles (e.g. *Senior Backend Engineer*, *Full-Stack Lead*) without raw filename overwriting.
   - **Inline Renaming:** Rename existing vault resumes directly on each card with an edit pencil icon and keyboard shortcuts (Enter to save, Escape to cancel).
   - **Full-Screen Quick View Reader:** Inspect complete extracted text in a clean reader modal with live word count, 1-click copy-to-clipboard, and direct file download.
   - **Intelligent Best-Fit Ranking:** Automatically compare all vault resumes against target job postings, compute a match percentage (0-100%), highlight why the top resume is recommended, and detail matched vs. missing skills.

4. **BulletSkill 2.0 Resume Bullet Optimizer (powered by `Bulletskill.md`):**
   - Click any missing keyword to generate revised resume bullet points.
   - Strictly enforces the framework: **WHAT/Keyword + HOW it was used + RESULT and/or REASON**.
   - Generates 3 alternatives:
     - **Candidate A:** ATS-focused
     - **Candidate B:** Concise
     - **Candidate C:** Technical & result-focused
   - Strict claim classification:
     - `VERIFIED`: Claims supported by your resume context.
     - `UNVERIFIED_SKILL`: Clearly flags missing skills with stated assumptions and a confirmation prompt (*"Yes, I used this!"*).
     - `UNVERIFIED_METRIC`: Uses placeholders like `[X%]`, never inventing fabricated numbers.

5. **Application Tracker (Table & Kanban Views):**
   - Interactive table and Kanban boards (`Wishlist` ➔ `Applied` ➔ `Interviewing` ➔ `Offered` ➔ `Rejected`).
   - Inline editing for status, follow-up dates, and notes.
   - Automated **Follow-Up Reminder Banner** alerting you to applications due today or past due.

6. **Professional Excel (.xlsx) Export:**
   - 1-click export of a styled, multi-sheet Excel workbook (`job_tracker.xlsx`).
   - Includes frozen headers, deep navy styling, auto-fitted column widths, clickable hyperlinks, and color-coded status pills.

7. **Universal Model Support + Zero-Key Offline Mode:**
   - Connect to **MiniMax M3**, **NVIDIA Nemotron 3/4**, **Local Ollama**, or **OpenRouter** in the Settings modal.
   - Built-in **offline heuristic NLP engine** with 600+ skills taxonomy - works 100% free even without any API key or internet access!

8. **Multi-Tenant Security & Cloud Storage:**
   - Secure user authentication via Google One-Tap / OAuth 2.0 or email/password (JWT + bcrypt).
   - Multi-tenant data isolation on Neon Serverless PostgreSQL with automated fallback to local SQLite.
   - Secure Cloudflare R2 document storage with time-limited signed download URLs.
   - AES-256 encrypted-at-rest user API keys.

---

## Quick Start (Run Locally)

If you want to run or develop JobHelperGuru locally on your machine:

### 1. Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Launch the Application Locally
```bash
python run.py
```
Open your browser to: **[http://localhost:8000](http://localhost:8000)**

---

## Development Mode (Live Hot Reload)

If you want live hot-reloading for local frontend and backend development:

1. Start backend server:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```
2. In a separate terminal, start frontend Vite server:
   ```bash
   cd frontend
   npm run dev
   ```
   Open: **[http://localhost:5173](http://localhost:5173)**

---

## Running Automated Tests

Run the full pytest suite:
```bash
python -m pytest tests/ -v
```

---

## Production Deployment

JobHelperGuru is configured for 1-click deployment on Render with automated Docker builds.

For step-by-step instructions on environment variables, Google OAuth configuration, and deployment setup, see:
- **[Render Deployment Guide](docs/RENDER_DEPLOYMENT_GUIDE.md)**
- **[Render Blueprint Specification](render.yaml)**
- **[Production Environment Template](.env.production.example)**

---

## Tech Stack
- **Backend:** Python, FastAPI, Neon PostgreSQL / SQLite, Cloudflare R2 / Local Storage, OpenAI SDK, cryptography
- **Frontend:** React 18, Vite, Tailwind CSS v4, Lucide Icons, Google Identity Services (OAuth 2.0)
- **Deployment:** Render Web Service, Multi-stage Docker
