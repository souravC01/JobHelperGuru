# JobHelperGuru Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build JobHelperGuru, a modern web app that ingests job links or text, extracts job details and required/preferred skills, highlights ATS keywords, ranks multiple uploaded resumes to identify the best fit, generates Bulletskill.md-compliant resume bullet point revisions to incorporate missing keywords, tracks applications in an interactive table & Kanban board with follow-up alerts, and exports a professionally styled Excel workbook (`.xlsx`).

**Architecture:** A lightweight Python (FastAPI) backend handles web scraping (`trafilatura` + BeautifulSoup), Universal OpenAI-compatible AI analysis (supporting MiniMax M3, NVIDIA Nemotron 3 Ultra, Ollama, OpenRouter) with an offline heuristic fallback, SQLite local persistence, and `openpyxl` multi-sheet Excel generation. The frontend is a modern React + Vite single-page application with dark/light styling, interactive skills matrix, multi-resume ranker, Bulletskill.md optimizer modal, and Kanban/Table tracking. A single `run.py` launches the entire app.

**Tech Stack:** Python 3.14 (FastAPI, uvicorn, trafilatura, beautifulsoup4, openpyxl, openai, pydantic, pytest), Node.js / React 19 (Vite, Lucide React, Tailwind-style modern CSS design tokens).

**Spec:** [`docs/superpowers/specs/2026-09-02-job-helper-guru-design.md`](file:///d:/Grind/Projects/JobHelperGuru/docs/superpowers/specs/2026-09-02-job-helper-guru-design.md) and [`Bulletskill.md`](file:///D:/Grind/Projects/JobHelperGuru/Bulletskill.md).

## Global Constraints
- Must run locally on Windows without requiring complex external dependencies.
- Universal AI support: Must work with OpenAI-compatible endpoints (MiniMax M3, Nemotron 3 Ultra, Ollama, OpenRouter) and have a 100% functional offline heuristic fallback when no API key is provided.
- Resume Bullet Optimizer MUST strictly comply with `Bulletskill.md`: `What / Keyword + How + Result/Reason`, explicit claim statuses (`VERIFIED`, `UNVERIFIED_SKILL`, `UNVERIFIED_METRIC`), no fake metrics, and 2-3 alternatives per bullet.
- Excel export MUST use `openpyxl` with styled headers, status color-coding, auto-width columns, and clickable links.
- TDD approach: Every backend component has corresponding unit tests executed with `pytest`.

---

### Task 1: Environment Setup, Data Models & Storage Service

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/models.py`
- Create: `backend/storage.py`
- Create: `backend/requirements.txt`
- Create: `tests/__init__.py`
- Create: `tests/test_storage.py`

**Interfaces:**
- Produces:
  - `StorageService`:
    - `add_application(app: ApplicationCreate) -> Application`
    - `get_applications() -> list[Application]`
    - `update_application(id: str, updates: ApplicationUpdate) -> Application | None`
    - `delete_application(id: str) -> bool`
    - `add_resume(name: str, content: str) -> Resume`
    - `get_resumes() -> list[Resume]`
    - `delete_resume(id: str) -> bool`
    - `get_settings() -> Settings`
    - `update_settings(settings: SettingsUpdate) -> Settings`

- [ ] **Step 1: Create requirements.txt and install Python dependencies**
```txt
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.8.0
openpyxl>=3.1.5
trafilatura>=1.12.0
beautifulsoup4>=4.12.3
requests>=2.32.0
openai>=1.40.0
pytest>=8.3.0
httpx>=0.27.0
```
Run: `pip install -r backend/requirements.txt`

- [ ] **Step 2: Write the failing test for StorageService**
```python
# tests/test_storage.py
import pytest
from backend.storage import StorageService
from backend.models import ApplicationCreate, ApplicationStatus, SettingsUpdate

def test_storage_crud(tmp_path):
    db_path = str(tmp_path / "test_tracker.db")
    storage = StorageService(db_path=db_path)
    
    # Resumes
    r = storage.add_resume(name="Backend Resume", content="Python, FastAPI, Docker, SQL")
    assert r.id is not None
    assert len(storage.get_resumes()) == 1
    
    # Applications
    app_data = ApplicationCreate(
        company="Acme Corp",
        role="Senior Backend Engineer",
        status=ApplicationStatus.APPLIED,
        location="Remote",
        salary="$130k - $160k",
        url="https://example.com/job",
        required_skills=["Python", "FastAPI"],
        ats_keywords=["Microservices", "Docker"],
        notes="Applied via website",
        best_resume_id=r.id
    )
    app = storage.add_application(app_data)
    assert app.id is not None
    assert app.company == "Acme Corp"
    
    apps = storage.get_applications()
    assert len(apps) == 1
    
    # Update
    updated = storage.update_application(app.id, {"status": ApplicationStatus.INTERVIEWING})
    assert updated.status == ApplicationStatus.INTERVIEWING
    
    # Settings
    storage.update_settings(SettingsUpdate(api_base_url="https://api.minimax.chat/v1", model_name="minimax-01"))
    settings = storage.get_settings()
    assert settings.api_base_url == "https://api.minimax.chat/v1"
```

- [ ] **Step 3: Run test to verify it fails**
Run: `pytest tests/test_storage.py`
Expected: FAIL (ModuleNotFoundError: No module named 'backend')

- [ ] **Step 4: Implement models.py and storage.py**
Create Pydantic data models for `Application`, `Resume`, `Settings`, and the SQLite database repository with table initialization and CRUD methods.

- [ ] **Step 5: Run test to verify it passes**
Run: `pytest tests/test_storage.py`
Expected: PASS

- [ ] **Step 6: Commit Task 1**
```bash
git add backend/ requirements.txt tests/test_storage.py
git commit -m "feat(backend): implement data models and SQLite storage service"
```

---

### Task 2: Web Scraping & Ingestion Service

**Files:**
- Create: `backend/services/scraper.py`
- Create: `tests/test_scraper.py`

**Interfaces:**
- Consumes: URL or raw text string
- Produces:
  - `ScraperService`:
    - `scrape_url(url: str) -> ScrapedJob`
    - `parse_raw_text(text: str, source_url: str = "") -> ScrapedJob`
    - `ScrapedJob` dataclass: `title: str`, `company: str`, `location: str`, `raw_text: str`, `source_url: str`

- [ ] **Step 1: Write the failing test for scraper**
```python
# tests/test_scraper.py
import pytest
from backend.services.scraper import ScraperService

def test_parse_raw_text():
    scraper = ScraperService()
    text = """
    Software Engineer at Stripe
    Location: San Francisco, CA (Hybrid)
    Requirements:
    - 3+ years experience with Python and Go
    - Strong knowledge of distributed systems and PostgreSQL
    """
    job = scraper.parse_raw_text(text, source_url="https://stripe.com/jobs/123")
    assert "Stripe" in job.company or "Software Engineer" in job.title
    assert len(job.raw_text) > 50
    assert job.source_url == "https://stripe.com/jobs/123"

def test_extract_from_html():
    scraper = ScraperService()
    html = """
    <html>
      <head><title>Senior Python Developer - TechCorp</title></head>
      <body>
        <main>
          <h1>Senior Python Developer</h1>
          <div class="company">TechCorp</div>
          <div class="location">Remote, US</div>
          <div class="description">
            We are looking for a Senior Python Developer with 5+ years of experience in FastAPI, Docker, and AWS.
          </div>
        </main>
      </body>
    </html>
    """
    job = scraper.extract_from_html(html, "https://techcorp.com/jobs/456")
    assert "Python" in job.title
    assert "TechCorp" in job.company or "TechCorp" in job.raw_text
    assert "FastAPI" in job.raw_text
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_scraper.py`
Expected: FAIL

- [ ] **Step 3: Implement `backend/services/scraper.py`**
Implement `ScraperService` using `trafilatura` for primary content extraction, `BeautifulSoup4` for custom meta tag/header extraction, and HTTP request headers mimicking modern browsers.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_scraper.py`
Expected: PASS

- [ ] **Step 5: Commit Task 2**
```bash
git add backend/services/scraper.py tests/test_scraper.py
git commit -m "feat(scraper): implement web scraper and text ingestion service"
```

---

### Task 3: Heuristic Keyword & Skill Extraction (Offline Fallback)

**Files:**
- Create: `backend/services/heuristic_parser.py`
- Create: `tests/test_heuristic_parser.py`

**Interfaces:**
- Produces:
  - `HeuristicParser`:
    - `analyze_job_text(text: str) -> JobAnalysisResult`
    - `match_resume(resume_text: str, job_analysis: JobAnalysisResult) -> ResumeMatchResult`

- [ ] **Step 1: Write the failing test for heuristic parser**
```python
# tests/test_heuristic_parser.py
from backend.services.heuristic_parser import HeuristicParser

def test_heuristic_skill_extraction():
    parser = HeuristicParser()
    sample_jd = """
    Senior Backend Engineer at Netflix
    Salary: $140,000 - $180,000
    Location: Los Gatos, CA (Hybrid)
    Requirements:
    - 5+ years with Python, FastAPI, and PostgreSQL.
    - Experience with Docker, Kubernetes, and AWS is required.
    - Excellent communication and Agile collaboration.
    Bonus:
    - Experience with Kafka or GraphQL.
    """
    analysis = parser.analyze_job_text(sample_jd)
    assert any("Python" in s for s in analysis.required_skills)
    assert any("PostgreSQL" in s for s in analysis.required_skills)
    assert any("Docker" in s or "Kubernetes" in s for s in analysis.tech_stack)
    assert "$140,000 - $180,000" in analysis.salary_range
    assert "Hybrid" in analysis.work_mode
    assert len(analysis.ats_keywords) >= 5

def test_heuristic_resume_matching():
    parser = HeuristicParser()
    sample_jd = "Requirements: Python, Docker, Kubernetes, PostgreSQL, AWS"
    analysis = parser.analyze_job_text(sample_jd)
    
    resume_backend = "Experience: 4 years writing Python, Docker, and PostgreSQL applications."
    match = parser.match_resume(resume_backend, analysis)
    assert "Python" in match.matched_keywords
    assert "Docker" in match.matched_keywords
    assert "Kubernetes" in match.missing_keywords or "AWS" in match.missing_keywords
    assert 40 <= match.match_score <= 80
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_heuristic_parser.py`
Expected: FAIL

- [ ] **Step 3: Implement `backend/services/heuristic_parser.py`**
Build a comprehensive dictionary of 600+ skills across backend, frontend, databases, DevOps, testing, cloud, and soft skills. Include regex for salary, work mode, and experience levels, plus frequency-weighted ATS keyword extraction.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_heuristic_parser.py`
Expected: PASS

- [ ] **Step 5: Commit Task 3**
```bash
git add backend/services/heuristic_parser.py tests/test_heuristic_parser.py
git commit -m "feat(nlp): implement offline heuristic skill and keyword extraction"
```

---

### Task 4: AI Analysis Engine & Bulletskill.md Optimizer

**Files:**
- Create: `backend/services/ai_engine.py`
- Create: `tests/test_ai_engine.py`

**Interfaces:**
- Consumes: OpenAI-compatible configuration (Base URL, API Key, Model Name)
- Produces:
  - `AIEngine`:
    - `analyze_job(text: str) -> JobAnalysisResult`
    - `rank_resumes(resumes: list[Resume], job: JobAnalysisResult) -> list[RankedResume]`
    - `optimize_bullet(request: BulletOptimizationRequest) -> BulletOptimizationResponse`
    - `generate_outreach(job: JobAnalysisResult, resume: Resume) -> OutreachResponse`

- [ ] **Step 1: Write the failing test for AI Engine and Bulletskill optimizer**
```python
# tests/test_ai_engine.py
from backend.services.ai_engine import AIEngine
from backend.models import BulletOptimizationRequest, ClaimStatus

def test_bulletskill_optimization_schema():
    engine = AIEngine(api_key=None) # Tests fallback / template generation
    req = BulletOptimizationRequest(
        target_job_title="Senior Java Developer",
        section_type="project",
        target_keyword="Kafka",
        existing_bullet="Built backend microservices for order processing.",
        evidence_context=["Used Spring Boot", "Used PostgreSQL"]
    )
    res = engine.optimize_bullet(req)
    assert res.target_keyword == "Kafka"
    assert res.claim_status in [ClaimStatus.UNVERIFIED_SKILL, ClaimStatus.VERIFIED]
    assert len(res.alternatives) >= 1
    # Check What + How + Result format
    alt = res.alternatives[0]
    assert alt.what != ""
    assert alt.how != ""
    assert alt.result_or_reason != ""
    if res.claim_status == ClaimStatus.UNVERIFIED_SKILL:
        assert res.requires_confirmation is True
        assert res.warning is not None
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_ai_engine.py`
Expected: FAIL

- [ ] **Step 3: Implement `backend/services/ai_engine.py`**
Implement the OpenAI-compatible AI client with strict prompts encoding:
- Job Analysis schema extraction
- Multi-resume ranking and scoring
- `Bulletskill.md` rules:
  - Framework: `What + How + Result/Reason`
  - Claim classification: `VERIFIED`, `UNVERIFIED_SKILL`, `UNVERIFIED_METRIC`, `VERIFIED_DERIVED_METRIC`
  - Work history (Job summary 1st bullet, 3-8 bullets) vs. Project rules (max 3 bullets, no dates)
  - 3 alternatives: Candidate A (ATS-focused), Candidate B (Concise), Candidate C (Technical/result)
  - Clear assumptions & confirmation warnings
- Fallback to `HeuristicParser` whenever the API key is not provided or connection fails.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_ai_engine.py`
Expected: PASS

- [ ] **Step 5: Commit Task 4**
```bash
git add backend/services/ai_engine.py tests/test_ai_engine.py
git commit -m "feat(ai): implement universal AI analysis and Bulletskill optimizer"
```

---

### Task 5: Excel Exporter Service (`openpyxl`)

**Files:**
- Create: `backend/services/excel_exporter.py`
- Create: `tests/test_excel_exporter.py`

**Interfaces:**
- Consumes: list of `Application` objects
- Produces:
  - `ExcelExporter`:
    - `export_workbook(applications: list[Application]) -> bytes`

- [ ] **Step 1: Write the failing test for Excel export**
```python
# tests/test_excel_exporter.py
import io
import openpyxl
from backend.services.excel_exporter import ExcelExporter
from backend.models import Application, ApplicationStatus

def test_generate_excel_workbook():
    exporter = ExcelExporter()
    apps = [
        Application(
            id="1",
            company="Google",
            role="Staff Software Engineer",
            status=ApplicationStatus.INTERVIEWING,
            location="Mountain View, CA",
            salary="$220,000 - $280,000",
            url="https://careers.google.com/jobs/1",
            required_skills=["Python", "Distributed Systems", "Kubernetes"],
            ats_keywords=["GCP", "High Throughput", "Architecture"],
            date_added="2026-09-01",
            application_date="2026-09-02",
            follow_up_date="2026-09-09",
            notes="Completed screening call with recruiter"
        )
    ]
    excel_bytes = exporter.export_workbook(apps)
    assert len(excel_bytes) > 1000
    
    # Validate with openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    assert "Applications Tracker" in wb.sheetnames
    assert "Skills & ATS Keywords" in wb.sheetnames
    
    ws = wb["Applications Tracker"]
    assert ws.cell(row=1, column=2).value == "Company"
    assert ws.cell(row=2, column=2).value == "Google"
    assert ws.cell(row=2, column=4).value == "Interviewing"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_excel_exporter.py`
Expected: FAIL

- [ ] **Step 3: Implement `backend/services/excel_exporter.py`**
Implement workbook generation using `openpyxl`:
- Sheet 1: `Applications Tracker` with styled navy header (`#1E293B`), white bold text, freeze header pane, auto-sized columns, clickable URLs, and color-coded status pills.
- Sheet 2: `Skills & ATS Keywords` containing detailed breakdown of must-haves, tools, and keywords.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_excel_exporter.py`
Expected: PASS

- [ ] **Step 5: Commit Task 5**
```bash
git add backend/services/excel_exporter.py tests/test_excel_exporter.py
git commit -m "feat(excel): implement styled openpyxl Excel export engine"
```

---

### Task 6: FastAPI Application Endpoints & Runner

**Files:**
- Create: `backend/main.py`
- Create: `run.py`
- Create: `tests/test_api.py`

**Interfaces:**
- Exposes REST API on `/api/*` and serves frontend static assets.
- Endpoints:
  - `POST /api/jobs/analyze` (URL or text)
  - `GET /api/resumes`, `POST /api/resumes`, `DELETE /api/resumes/{id}`
  - `POST /api/resumes/match`
  - `POST /api/resumes/optimize-bullet`
  - `POST /api/resumes/generate-outreach`
  - `GET /api/applications`, `POST /api/applications`, `PATCH /api/applications/{id}`, `DELETE /api/applications/{id}`
  - `GET /api/export/excel`
  - `GET /api/settings`, `POST /api/settings`, `POST /api/settings/test-ai`

- [ ] **Step 1: Write the failing test for API endpoints**
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_analyze_job_endpoint():
    res = client.post("/api/jobs/analyze", json={"text": "Software Engineer at Apple in Cupertino. Python, Swift, AWS required."})
    assert res.status_code == 200
    data = res.json()
    assert "Python" in data["required_skills"] or "Python" in data["tech_stack"]
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_api.py`
Expected: FAIL

- [ ] **Step 3: Implement `backend/main.py` and `run.py`**
Wire up FastAPI router, CORS middleware, error handlers, and single-click launch script `run.py`.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_api.py`
Expected: PASS

- [ ] **Step 5: Commit Task 6**
```bash
git add backend/main.py run.py tests/test_api.py
git commit -m "feat(api): implement FastAPI endpoints and single command runner"
```

---

### Task 7: Frontend Scaffolding, Styling & Design System

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/api/client.js`

**Interfaces:**
- Produces: Complete Vite + React frontend foundation with modern glassmorphism design tokens, active tab routing, and typed API client wrapper.

- [ ] **Step 1: Initialize Vite React app in `frontend/`**
Install Vite, React, Lucide-React for modern icons.
Run: `cd frontend && npm install`

- [ ] **Step 2: Create `frontend/src/index.css` with sleek dark/light design system**
Implement vibrant color tokens, dark mode palette, glassmorphism panels, pill badges, and smooth animations.

- [ ] **Step 3: Create `frontend/src/api/client.js`**
Centralized fetch client for backend endpoints with error toast notifications.

- [ ] **Step 4: Verify frontend builds without errors**
Run: `cd frontend && npm run build`
Expected: Success

- [ ] **Step 5: Commit Task 7**
```bash
git add frontend/
git commit -m "feat(frontend): initialize React Vite app with modern design tokens"
```

---

### Task 8: Frontend — Job Analyzer, Skills Matrix & ATS Keyword Bank

**Files:**
- Create: `frontend/src/components/JobAnalyzer.jsx`
- Create: `frontend/src/components/SkillsMatrix.jsx`
- Create: `frontend/src/components/ATSKeywordBank.jsx`

**Interfaces:**
- Consumes: `POST /api/jobs/analyze`, `POST /api/applications`
- Produces: URL fetch bar, text input toggle, formatted company/role card, categorized skill badges (Required, Preferred, Tech Stack, Soft Skills), and one-click copy ATS keyword cloud.

- [ ] **Step 1: Build `JobAnalyzer.jsx` component**
Input bar for pasting URL or toggling to raw text. Loading animation during fetch/parsing.

- [ ] **Step 2: Build `SkillsMatrix.jsx` and `ATSKeywordBank.jsx`**
Categorized pill badges with color differentiation (Red/Purple for Required, Blue for Preferred, Emerald for Tech Stack, Amber for Soft Skills) and copy-all button for ATS keywords.

- [ ] **Step 3: Integrate with "Save to Tracker" dialog**
Allows instant saving of analyzed job to applications table with one click.

- [ ] **Step 4: Verify in browser and build**
Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 5: Commit Task 8**
```bash
git add frontend/src/components/
git commit -m "feat(frontend): add job analyzer, skills matrix, and keyword bank"
```

---

### Task 9: Frontend — Multi-Resume Library & Best-Fit Matcher

**Files:**
- Create: `frontend/src/components/ResumeLibrary.jsx`
- Create: `frontend/src/components/ResumeFitRanker.jsx`

**Interfaces:**
- Consumes: `GET /api/resumes`, `POST /api/resumes`, `DELETE /api/resumes/{id}`, `POST /api/resumes/match`
- Produces:
  - Resume Library: Manage multiple resumes (e.g. "Backend Resume", "Full Stack Resume").
  - Best-Fit Matcher: Ranked list of resumes with match score progress gauges (0-100%), selection explanation, and Matched vs. Missing keyword badges.

- [ ] **Step 1: Build `ResumeLibrary.jsx`**
Modal/View to upload, paste, rename, and manage multiple resume versions.

- [ ] **Step 2: Build `ResumeFitRanker.jsx`**
Displays each uploaded resume ranked by fit against the currently analyzed job. Highlights the top resume with a "Best Match" star badge, match percentage gauge, and side-by-side view of matched (green) vs. missing (amber/red) keywords.

- [ ] **Step 3: Test component interaction and build**
Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 4: Commit Task 9**
```bash
git add frontend/src/components/ResumeLibrary.jsx frontend/src/components/ResumeFitRanker.jsx
git commit -m "feat(frontend): add multi-resume manager and best-fit ranking component"
```

---

### Task 10: Frontend — Bulletskill.md Optimizer & Cover Letter Generator

**Files:**
- Create: `frontend/src/components/BulletOptimizerModal.jsx`
- Create: `frontend/src/components/CoverLetterModal.jsx`

**Interfaces:**
- Consumes: `POST /api/resumes/optimize-bullet`, `POST /api/resumes/generate-outreach`
- Produces:
  - Bullet Optimizer Modal:
    - Target missing keyword selector.
    - User bullet input / selector.
    - Displays Candidate A (ATS-focused), Candidate B (Concise), Candidate C (Technical).
    - Highlights `What + How + Result` breakdown.
    - Displays claim classification badge: `VERIFIED` (Green), `UNVERIFIED_SKILL` (Yellow with warning & confirmation prompt), `UNVERIFIED_METRIC` (with `[X%]` placeholder).
    - "Confirm & Verify" toggle to make the bullet export-ready!
  - Cover Letter Modal: Generates tailored pitch with 1-click copy.

- [ ] **Step 1: Build `BulletOptimizerModal.jsx`**
Strictly implement the UI presentation dictated by `Bulletskill.md`.

- [ ] **Step 2: Build `CoverLetterModal.jsx`**
Generates concise 3-paragraph tailored cold outreach note / cover letter.

- [ ] **Step 3: Test component rendering and build**
Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 4: Commit Task 10**
```bash
git add frontend/src/components/BulletOptimizerModal.jsx frontend/src/components/CoverLetterModal.jsx
git commit -m "feat(frontend): implement Bulletskill optimizer modal and cover letter generator"
```

---

### Task 11: Frontend — Applications Tracker (Table & Kanban) + Excel Export

**Files:**
- Create: `frontend/src/components/ApplicationsTracker.jsx`
- Create: `frontend/src/components/KanbanBoard.jsx`
- Create: `frontend/src/components/FollowUpBanner.jsx`

**Interfaces:**
- Consumes: `GET /api/applications`, `PATCH /api/applications/{id}`, `DELETE /api/applications/{id}`, `GET /api/export/excel`
- Produces:
  - Filterable, searchable application table with inline status dropdowns and follow-up date pickers.
  - Interactive Kanban board (`Wishlist`, `Applied`, `Interviewing`, `Offered`, `Rejected`).
  - Follow-up reminder alert banner.
  - "Export to Excel (.xlsx)" button that immediately triggers browser file download.

- [ ] **Step 1: Build `ApplicationsTracker.jsx` with Table and Kanban views**
Provide toggle between Table view and Kanban board. Search by company or role. Filter by status.

- [ ] **Step 2: Add Follow-up alerts banner**
Highlights applications whose follow-up date is today or overdue.

- [ ] **Step 3: Wire up Excel Export button**
Triggers `/api/export/excel` and downloads `job_tracker.xlsx`.

- [ ] **Step 4: Verify build and user flow**
Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 5: Commit Task 11**
```bash
git add frontend/src/components/ApplicationsTracker.jsx frontend/src/components/KanbanBoard.jsx frontend/src/components/FollowUpBanner.jsx
git commit -m "feat(frontend): implement applications table, kanban board, follow-up alerts, and Excel export"
```

---

### Task 12: End-to-End Verification, Settings & Single-Command Launch

**Files:**
- Create: `frontend/src/components/SettingsModal.jsx`
- Create: `README.md`
- Modify: `run.py`

**Interfaces:**
- Full system verification with live mock URLs, resume uploads, bullet optimization, and Excel export verification.

- [ ] **Step 1: Implement `SettingsModal.jsx`**
Allows user to set API Base URL (MiniMax, Nemotron, Ollama, OpenRouter), API Key, and Model Name, with "Test Connection" button.

- [ ] **Step 2: Build production frontend bundle into backend static directory**
Run: `cd frontend && npm run build`
Ensure `backend/main.py` serves the built frontend so `python run.py` works out of the box on `http://localhost:8000`.

- [ ] **Step 3: Run full backend test suite**
Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 4: Verify full application flow via browser subagent or manual test**
Test URL parsing, multi-resume best-fit ranking, Bulletskill optimizer suggestions, table/kanban interactions, and Excel file download.

- [ ] **Step 5: Create README.md with clear instructions**
Document how to run (`python run.py`), how to configure MiniMax/Nemotron/Ollama keys, and feature breakdown.

- [ ] **Step 6: Commit Task 12**
```bash
git add frontend/src/components/SettingsModal.jsx README.md run.py
git commit -m "feat(release): finalize settings modal, end-to-end integration, and docs"
```
