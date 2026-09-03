# Work Experience Detection & Header Badge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect and display professional work experience requirements (e.g. "1-4 years", "3+ years", "New Grad", or "Not specified") at the top of the job analysis view alongside the job title and metadata.

**Architecture:** 
- Add `experience_required: str = "Not specified"` to the `JobAnalysisResult` Pydantic model.
- Enhance `AIEngine` (LLM prompt + regex post-processor) and `HeuristicJobParser` (deterministic rule-based extractor) to parse exact years (e.g. "1-4 years", "3+ years"), detect recent/new grad indicators, and default to "Not specified".
- Display a prominent experience pill/badge in `frontend/src/components/JobAnalyzer.jsx` directly underneath the job title in the primary header card.

**Tech Stack:** Python 3.11+, Pydantic v2, FastAPI, React 18, Tailwind CSS / Vanilla CSS tokens, Pytest.

**Spec:** User feature request for professional work experience extraction and top header display (September 2026).

## Global Constraints
- Preserve existing `experience_level` ("Entry", "Mid", "Senior", "Lead") for backward compatibility.
- Ensure strict parsing: If tenure numbers are present (e.g., "1-4 years", "3+ years", "5 years"), preserve the exact number/range.
- If recent grad / new grad is detected, format as "New Grad".
- If no tenure requirement appears in the text, format as "Not specified".
- All 52 existing tests must continue to pass without regressions.

---

### Task 1: Add `experience_required` to Data Models & Heuristic Parser

**Files:**
- Modify: `backend/models.py:107-124`
- Modify: `backend/services/heuristic_parser.py:150-170,220-237`
- Test: `tests/test_heuristic_parser.py`

**Interfaces:**
- Consumes: Raw job text string in `HeuristicJobParser.parse_job_description()`.
- Produces: `JobAnalysisResult.experience_required` containing exact years, "New Grad", or "Not specified".

- [x] **Step 1: Write failing tests for experience extraction in `tests/test_heuristic_parser.py`**

```python
# tests/test_heuristic_parser.py

def test_heuristic_experience_required_range():
    parser = HeuristicJobParser()
    text = "We are seeking a Backend Engineer with 1-4 years of professional experience in Python."
    res = parser.parse_job_description(text)
    assert res.experience_required == "1-4 years"

def test_heuristic_experience_required_plus_notation():
    parser = HeuristicJobParser()
    text = "Senior DevOps Engineer. Must have 5+ years of experience with Kubernetes and AWS."
    res = parser.parse_job_description(text)
    assert res.experience_required == "5+ years"

def test_heuristic_experience_required_recent_grad():
    parser = HeuristicJobParser()
    text = "Associate Developer role open to recent grads and university graduates with strong Java skills."
    res = parser.parse_job_description(text)
    assert res.experience_required == "New Grad"

def test_heuristic_experience_required_not_specified():
    parser = HeuristicJobParser()
    text = "Software Developer at Acme. Build high quality web applications using React and Node.js."
    res = parser.parse_job_description(text)
    assert res.experience_required == "Not specified"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_heuristic_parser.py::test_heuristic_experience_required_range -v`  
Expected: FAIL (`AttributeError: 'JobAnalysisResult' object has no attribute 'experience_required'`).

- [x] **Step 3: Update `backend/models.py` and `backend/services/heuristic_parser.py`**

In `backend/models.py`:
```python
class JobAnalysisResult(BaseModel):
    company: str = "Unknown Company"
    title: str = "Open Position"
    location: str = "Unknown"
    work_mode: str = "Unknown"
    salary_range: str = "Not specified"
    experience_level: str = "Not specified"  # Entry, Mid, Senior, Lead
    experience_required: str = "Not specified"  # "1-4 years", "3+ years", "New Grad", "Not specified"
    is_new_grad_role: bool = False
    new_grad_criteria: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    ats_keywords: List[str] = Field(default_factory=list)
    summary: str = ""
```

In `backend/services/heuristic_parser.py`:
```python
def extract_experience_required(text: str, is_new_grad: bool = False) -> str:
    if is_new_grad or re.search(r"\b(recent grads?|recent graduates?|new grads?|new graduates?|fresh graduates?|university graduates?)\b", text, re.I):
        return "New Grad"
    patterns = [
        r"(?:(?:minimum|at least)\s+)?(\d+\s*(?:-|to)\s*\d+)\+?\s*(?:years?|yrs?)(?:\s*(?:of)?\s*(?:professional|relevant|software|work|industry)?\s*experience)?",
        r"(?:(?:minimum|at least)\s+)?(\d+\+)\s*(?:years?|yrs?)(?:\s*(?:of)?\s*(?:professional|relevant|software|work|industry)?\s*experience)?",
        r"(?:(?:minimum|at least)\s+)?(\d+)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:professional|relevant|software|work|industry)?\s*experience",
        r"(?:minimum|at least)\s+(\d+)\s*(?:years?|yrs?)",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            val = m.group(1).strip()
            val_cleaned = re.sub(r"\s*to\s*", "-", val, flags=re.I)
            val_cleaned = re.sub(r"\s+", "", val_cleaned)
            return f"{val_cleaned} years"
    return "Not specified"
```
Call `extract_experience_required(text, is_new_grad=is_new_grad)` in `parse_job_description` and pass `experience_required` to `JobAnalysisResult`.

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_heuristic_parser.py -v`  
Expected: PASS (all heuristic tests green).

- [x] **Step 5: Commit**

```bash
git add backend/models.py backend/services/heuristic_parser.py tests/test_heuristic_parser.py
git commit -m "feat(models): add experience_required extraction and model field"
```

---

### Task 2: Enhance AI Engine Prompt & Extraction Fallback

**Files:**
- Modify: `backend/services/ai_engine.py:75-115`
- Test: `tests/test_ai_engine.py`

**Interfaces:**
- Consumes: LLM output and raw job description.
- Produces: Normalized `experience_required` field in `JobAnalysisResult`.

- [x] **Step 1: Write test for AI Engine experience extraction in `tests/test_ai_engine.py`**

```python
# tests/test_ai_engine.py

def test_ai_engine_extracts_experience_required_offline(ai_engine):
    text = "Senior Python Engineer at Datadog. Requires 3-5 years of backend experience."
    res = ai_engine.analyze_job(text)
    assert res.experience_required in ("3-5 years", "3-5 years")
```

- [x] **Step 2: Run test to verify it fails or needs implementation**

Run: `python -m pytest tests/test_ai_engine.py::test_ai_engine_extracts_experience_required_offline -v`  
Expected: Verify behavior.

- [x] **Step 3: Update `analyze_job` in `backend/services/ai_engine.py`**

1. Add `"experience_required": "Exact years of experience requested e.g. '1-4 years', '3+ years', '5 years', or 'New Grad' if for recent graduates, or 'Not specified' if not stated",` to the system prompt JSON schema.
2. In post-processing, import `extract_experience_required` from `backend.services.heuristic_parser`.
3. If `data.get("experience_required") in (None, "", "Not specified")`:
   Fall back to `extract_experience_required(text, is_new_grad=data.get("is_new_grad_role", False))`.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ai_engine.py -v`  
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add backend/services/ai_engine.py tests/test_ai_engine.py
git commit -m "feat(ai): support experience_required in AI engine prompt and fallback"
```

---

### Task 3: Display Experience Badge in UI Header

**Files:**
- Modify: `frontend/src/components/JobAnalyzer.jsx:225-255`
- Modify: `frontend/src/index.css` (if custom badge styling needed)

**Interfaces:**
- Consumes: `currentJob.experience_required` and `currentJob.experience_level`.
- Produces: Prominent visual badge in the Job Analyzer top header card with contextual styling (New Grad, Exact Years, Not specified).

- [x] **Step 1: Update `JobAnalyzer.jsx` to render the experience badge**

Import `Clock` icon from `lucide-react`.
Underneath the job title, in the metadata flex row:
```jsx
{/* Professional Experience Badge */}
<div
  className={clsx(
    "flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium border text-xs transition-colors",
    (currentJob.experience_required === "New Grad" || currentJob.is_new_grad_role)
      ? "bg-cyan-500/10 border-cyan-500/25 text-cyan-300"
      : currentJob.experience_required && currentJob.experience_required !== "Not specified"
      ? "bg-amber-500/10 border-amber-500/25 text-amber-300 font-mono"
      : "bg-white/[0.03] border-white/[0.08] text-zinc-400"
  )}
  title="Required Professional Work Experience"
>
  <Clock size={13} className={
    (currentJob.experience_required === "New Grad" || currentJob.is_new_grad_role)
      ? "text-cyan-400"
      : currentJob.experience_required && currentJob.experience_required !== "Not specified"
      ? "text-amber-400"
      : "text-zinc-500"
  } />
  <span>
    Exp: {currentJob.experience_required || currentJob.experience_level || "Not specified"}
  </span>
</div>
```

- [x] **Step 2: Build the frontend to verify compilation**

Run: `cd frontend && npm run build`  
Expected: Clean build, 0 errors.

- [x] **Step 3: Commit**

```bash
git add frontend/src/components/JobAnalyzer.jsx
git commit -m "feat(ui): display professional work experience badge in JobAnalyzer header"
```

---

### Task 4: End-to-End Regression & Verification

- [x] **Step 1: Run full pytest test suite**

Run: `python -m pytest -v`  
Expected: All 56+ tests PASS.

- [x] **Step 2: Live test with Indeed URL and custom text**

Verify Indeed URL `https://ca.indeed.com/viewjob?jk=d721d1b5ad371161&from=shareddesktop_copy` extracts and renders `experience_required`.

- [x] **Step 3: Update walkthrough artifact with screenshots/results**
