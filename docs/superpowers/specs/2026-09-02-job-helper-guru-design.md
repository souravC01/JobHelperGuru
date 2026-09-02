# JobHelperGuru — Architecture & System Design Specification

**Date:** 2026-09-02  
**Status:** Approved by User  
**Target Project:** `JobHelperGuru` (`d:\Grind\Projects\JobHelperGuru`)

---

## 1. Executive Summary & Goals

**JobHelperGuru** is an intelligent job application assistant and tracker web application. It automates the tedious parts of the job search:
1. **Job Ingestion & Parsing:** Extracts job postings directly from a URL (e.g. LinkedIn, Indeed, Greenhouse, Lever, Workday) or raw text paste.
2. **Deep Information & Skills Extraction:** Breaks down required vs. preferred skills, technical stack, soft skills, compensation, and high-priority ATS keywords.
3. **Multi-Resume Library & Best-Fit Matching:** Users can upload multiple resumes (e.g. Frontend, Backend, ML, Full Stack). The app compares each resume against the job description, ranks them by fit score, highlights matched vs. missing keywords, and explains why the top resume is the best match.
4. **Resume Bullet Point Optimizer:** For any missing keywords in the chosen resume, the AI suggests tailored revisions to existing resume bullet points to naturally incorporate the missing keywords.
5. **Application Tracker:** Provides a full pipeline dashboard (Table & Kanban views) with application statuses (`Wishlist`, `Applied`, `Interviewing`, `Offered`, `Rejected`) and follow-up alerts.
6. **Styled Excel Export (.xlsx):** Generates and downloads a professionally formatted, multi-sheet Excel spreadsheet with color-coded status badges, frozen panes, and auto-adjusted columns on demand.
7. **Universal Model Support:** Operates seamlessly with OpenAI-compatible endpoints (including user-specified models like **MiniMax M3**, **NVIDIA Nemotron 3 Ultra**, local Ollama, or OpenRouter), with a built-in offline heuristic fallback when no API key is set.

---

## 2. System Architecture

```
+-------------------------------------------------------------------------+
|                          Web Frontend (React + Vite)                    |
|  - Ingestion Bar (URL / Text)         - Multi-Resume Library            |
|  - Skills & ATS Keyword Bank          - Best-Fit Resume Matcher         |
|  - Bullet Point Optimizer             - Tailored Outreach Pitch         |
|  - Applications Table & Kanban        - 1-Click Styled Excel Export     |
+------------------------------------+------------------------------------+
                                     | HTTP REST API
+------------------------------------v------------------------------------+
|                         Backend (Python / FastAPI)                      |
|                                                                         |
|  +------------------------+   +---------------------------------------+ |
|  | Scraper & Ingestor     |   | AI & NLP Analysis Engine              | |
|  | - trafilatura          |   | - Universal OpenAI-compatible client  | |
|  | - BeautifulSoup4       |   |   (MiniMax M3, Nemotron, Ollama, etc.)| |
|  | - ATS custom rules     |   | - Offline Heuristic Fallback Engine   | |
|  +------------------------+   +---------------------------------------+ |
|                                                                         |
|  +------------------------+   +---------------------------------------+ |
|  | Excel Export Engine    |   | Local Persistence Layer               | |
|  | - openpyxl formatting  |   | - SQLite / JSON DB (`tracker.db`)     | |
|  | - Multi-sheet workbook |   | - Resumes, Applications, Settings     | |
|  +------------------------+   +---------------------------------------+ |
+-------------------------------------------------------------------------+
```

---

## 3. Detailed Component Specifications

### 3.1 Data Ingestion & Scraping Pipeline (`backend/services/scraper.py`)
- **Primary Scraper:** `trafilatura` handles article body extraction, removing header/footer/nav boilerplate.
- **ATS Portal Parsers:** Specialized selectors for known job boards:
  - Greenhouse (`boards.greenhouse.io`, `job-boards.greenhouse.io`)
  - Lever (`jobs.lever.co`)
  - Workday (`*.myworkdayjobs.com`)
  - Indeed / LinkedIn public job postings
- **Text Paste Fallback:** Direct input area for password-protected postings or anti-bot Cloudflare challenges.
- **Output Schema:**
  - `title`: Extracted or detected job title
  - `company`: Detected company name
  - `location`: Detected location (City, State, Remote, Hybrid)
  - `raw_text`: Cleaned text content
  - `source_url`: Original URL or "manual_paste"

### 3.2 AI & NLP Analysis Engine (`backend/services/ai_engine.py`)
- **Client Configuration:**
  - Standard OpenAI Python SDK configured with:
    - `api_base_url`: Defaults to configurable URL (e.g. OpenRouter, NVIDIA NIM, MiniMax, or local `http://localhost:11434/v1`).
    - `api_key`: Stored in user settings / `.env`.
    - `model_name`: Defaults to user-specified (e.g. `minimax/minimax-01`, `nvidia/nemotron-4-340b-instruct`, etc.).
- **Tasks Performed by AI Engine:**
  1. **Job Analysis & Skill Breakdown:** Structured JSON extraction:
     - `company`: string
     - `title`: string
     - `location`: string
     - `work_mode`: "Remote" | "Hybrid" | "Onsite" | "Unknown"
     - `salary_range`: string (e.g. "$120,000 - $150,000" or "Not specified")
     - `experience_level`: "Entry" | "Mid" | "Senior" | "Lead" | "Executive"
     - `required_skills`: list of strings (must-haves)
     - `preferred_skills`: list of strings (nice-to-haves)
     - `tech_stack`: list of strings (tools, languages, frameworks, clouds)
     - `soft_skills`: list of strings (leadership, communication, Agile)
     - `ats_keywords`: list of strings (top 15-25 keywords ranked by importance)
     - `summary`: 2-3 sentence overview of the role
  2. **Multi-Resume Best-Fit Matcher:**
     - Accepts `job_analysis` and a list of saved `resumes` (id, title, content).
     - Computes match score (0–100%) for each resume based on required skills & keywords.
     - Selects the `#1 Best-Fit Resume` with clear rationale.
     - For the selected resume: lists `matched_keywords` and `missing_keywords`.
  3. **Resume Bullet Point Optimizer:**
     - Input: Target missing keyword + user's existing resume bullet point (or relevant experience context).
     - Output: 2–3 rewritten bullet points highlighting the missing keyword with strong action verbs and quantified impact metrics.
  4. **Tailored Outreach / Cover Letter Generator:**
     - Generates a concise, highly relevant 3-paragraph pitch connecting the candidate's matched skills to the job description.
- **Offline / Heuristic Fallback (`backend/services/heuristic_parser.py`):**
  - If no API key is provided or the endpoint is unreachable:
    - Runs regex matching against a dictionary of 600+ tech skills, frameworks, tools, and certifications.
    - Extracts compensation patterns (`\$[0-9]{2,3}(?:,[0-9]{3})*(?:k)?`).
    - Performs basic token frequency analysis for ATS keywords.
    - Computes resume keyword overlap using Jaccard and substring matching.

### 3.3 Multi-Resume Management (`backend/services/resume_manager.py`)
- Allows creating, naming, editing, and deleting multiple resume versions:
  - Example: "Full Stack Resume", "Python Backend Resume", "Machine Learning Resume".
  - Text input or file upload (.txt, .md, .pdf parsing via `pypdf` or raw text).
- Resumes are stored locally in the SQLite database and cached in the frontend.

### 3.4 Application Tracker & Storage (`backend/services/storage.py`)
- SQLite database (`data/tracker.db`) with schemas for:
  - `applications`: `id`, `company`, `role`, `status`, `location`, `salary`, `url`, `required_skills`, `ats_keywords`, `date_added`, `application_date`, `follow_up_date`, `notes`, `best_resume_id`, `created_at`, `updated_at`.
  - `resumes`: `id`, `name`, `content`, `created_at`, `updated_at`.
  - `settings`: key-value store for AI base URL, API key, model name, default follow-up days.

### 3.5 Excel Export Engine (`backend/services/excel_exporter.py`)
- Generates an `.xlsx` workbook using `openpyxl`:
  - **Sheet 1: `Applications Tracker`**:
    - Freeze header row.
    - Styling: Deep navy header (`#1E293B`), white bold text, alternating row shading.
    - Columns: Date Added, Company, Role, Status, Location, Salary, Job URL (clickable hyperlink), Application Date, Follow-up Date, Key ATS Keywords, Required Skills, Notes.
    - Status column formatted with conditional fills:
      - `Wishlist`: Light Gray (`#E2E8F0`)
      - `Applied`: Soft Blue (`#DBEAFE`)
      - `Interviewing`: Light Amber (`#FEF3C7`)
      - `Offered`: Soft Green (`#DCFCE7`)
      - `Rejected`: Soft Rose (`#FFE4E6`)
    - Auto-adjusted column widths based on maximum cell content.
  - **Sheet 2: `Skills & ATS Keyword Bank`**:
    - Detailed row-by-row breakdown of all tracked jobs with full required skills, preferred skills, and keywords.
- Generates file in-memory for immediate download via FastAPI `StreamingResponse`.

### 3.6 Frontend User Experience (`frontend/`)
- Built with React (Vite) + Tailwind-style custom CSS tokens (sleek modern dark/light mode, glassmorphism, responsive).
- **Core Views:**
  1. **Job Analyzer:**
     - Ingestion input (URL input + text area fallback).
     - Job overview card (Company, Title, Location, Salary, Summary).
     - Categorized Skill Badges (Required, Preferred, Tech Stack, Soft Skills).
     - ATS Keywords Cloud (one-click copy).
     - Multi-Resume Matcher widget: Ranks all resumes, displays Match Score gauge (0-100%), shows matched vs. missing keywords.
     - Bullet Point Optimizer modal: Enter a bullet point and missing keyword to get AI suggestions.
     - Cover Letter Generator modal: Generate and copy tailored outreach.
     - "Save Application to Tracker" button.
  2. **Tracker (Table & Kanban):**
     - Table view with instant search, status filters, inline status updating, and note editing.
     - Kanban view with drag/drop or click-to-move between columns.
     - Follow-up reminder banner for items needing attention.
     - "Export to Excel (.xlsx)" primary action button.
  3. **Resume Library:**
     - Manage and upload multiple resume versions.
  4. **Settings:**
     - OpenAI-compatible endpoint settings (`API Base URL`, `API Key`, `Model Name`).
     - Test Connection button with live status ping.

---

## 4. Error Handling & Edge Cases
- **Scraping Failures:** If a URL is protected by Cloudflare bot protection (e.g. LinkedIn private links), the UI gracefully prompts the user to paste the job text into the text tab.
- **AI API Errors:** If API credentials fail or the user has no credits/offline, automatic fallback to the offline heuristic extractor ensures the application never crashes.
- **Empty / Incomplete Job Descriptions:** Heuristic defaults for missing salaries, locations, or dates.
- **Excel Concurrency:** Dynamic in-memory generation on download avoids Windows file-lock issues.

---

## 5. Verification & Testing Plan
- **Backend Unit Tests:**
  - `test_scraper.py`: Tests URL fetching and HTML cleaning on mock HTML pages.
  - `test_ai_engine.py`: Tests JSON parsing from AI responses and heuristic fallback behavior.
  - `test_excel_exporter.py`: Validates `.xlsx` structure, sheets, styling, and column headers.
  - `test_storage.py`: CRUD operations for applications and resumes in SQLite.
- **Frontend Verification:**
  - Run dev server, test URL parsing, resume matching, bullet point optimization, and table/kanban interactions.
  - Test Excel download and verify valid `.xlsx` format.
