# JobHelperGuru 🚀
### Intelligent Job Application Assistant, ATS Optimizer & Excel Tracker

**JobHelperGuru** is an AI-powered pairs-programmer for your job hunt. Paste any job posting URL or description to extract required qualifications, identify missing ATS keywords, rank multiple resumes to find the best fit, optimize resume bullet points using the **Resume Guide 2.0 / BulletSkill** framework, and track your applications with 1-click **Excel (.xlsx)** export.

---

## Key Features

1. **Smart Job Ingestion & Web Scraper:**
   - Paste a job link (LinkedIn, Greenhouse, Lever, Indeed, Workday, etc.) or paste raw job text directly.
   - Automatically parses Company, Title, Location, Work Mode (Remote/Hybrid/Onsite), Salary Range, and Experience Level.

2. **Categorized Skills Matrix & ATS Keyword Bank:**
   - Separates **Required Must-Haves**, **Preferred Nice-to-Haves**, **Tech Stack & Tools**, and **Soft Skills**.
   - Generates a high-frequency **ATS Keyword Bank** with a 1-click "Copy All" button.

3. **Multi-Resume Library & Best-Fit Matcher:**
   - Upload and store multiple tailored resumes (e.g. *Backend*, *Full-Stack*, *Machine Learning*).
   - Automatically compares all your resumes against the job, computes a match percentage (0–100%), highlights why the top resume is recommended, and details matched vs. missing skills.

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

7. **Universal OpenAI-Compatible Model Support + Zero-Key Offline Mode:**
   - Connect to **MiniMax M3**, **NVIDIA Nemotron 3/4**, **Local Ollama**, or **OpenRouter** in the Settings modal.
   - Built-in **offline heuristic NLP engine** with 600+ skills taxonomy—works 100% free even without any API key or internet access!

---

## Quick Start (Single-Command Launch)

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

If you want live hot-reloading on both frontend and backend:

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

## Tech Stack
- **Backend:** Python 3.14, FastAPI, trafilatura, BeautifulSoup4, openpyxl, OpenAI SDK, SQLite
- **Frontend:** React 18, Vite, Lucide-React, Modern CSS Tokens & Glassmorphism Design
