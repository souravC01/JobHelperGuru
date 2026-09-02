import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.models import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    Resume,
    ResumeCreate,
    Settings,
    SettingsUpdate,
    JobAnalysisResult,
    RankedResume,
    BulletOptimizationRequest,
    BulletOptimizationResponse,
    OutreachResponse,
)
from backend.storage import StorageService
from backend.services.scraper import ScraperService
from backend.services.ai_engine import AIEngine
from backend.services.excel_exporter import ExcelExporter

app = FastAPI(title="JobHelperGuru API", version="1.0.0")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
storage = StorageService(db_path=os.environ.get("JOB_HELPER_DB", "data/tracker.db"))
scraper = ScraperService()
excel_exporter = ExcelExporter()


def get_ai_engine() -> AIEngine:
    settings = storage.get_settings()
    return AIEngine(
        api_base_url=settings.api_base_url,
        api_key=settings.api_key,
        model_name=settings.model_name,
    )


# --- Health ---
@app.get("/api/health")
def health():
    return {"status": "ok", "app": "JobHelperGuru"}


# --- Job Analysis & Scraping ---
class JobAnalyzeRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None


@app.post("/api/jobs/analyze")
def analyze_job(req: JobAnalyzeRequest):
    if not req.url and not req.text:
        raise HTTPException(status_code=400, detail="Either a URL or job text must be provided.")

    scraped_title = ""
    scraped_company = ""
    scraped_location = ""
    job_text = ""
    source_url = req.url or ""

    if req.url:
        scraped = scraper.scrape_url(req.url)
        scraped_title = scraped.title
        scraped_company = scraped.company
        scraped_location = scraped.location
        job_text = scraped.raw_text
    elif req.text:
        parsed = scraper.parse_raw_text(req.text)
        scraped_title = parsed.title
        scraped_company = parsed.company
        scraped_location = parsed.location
        job_text = parsed.raw_text

    ai = get_ai_engine()
    analysis = ai.analyze_job(job_text, source_url=source_url)

    # Prefer scraped title/company if AI/heuristic couldn't detect specific ones
    if (not analysis.title or analysis.title in ["Open Position", "Detected Role"]) and scraped_title and scraped_title not in ["Open Position", "Detected Role", "Unknown Role"]:
        analysis.title = scraped_title
    if (not analysis.company or analysis.company in ["Unknown Company", "Company"]) and scraped_company and scraped_company not in ["Unknown Company"]:
        analysis.company = scraped_company
    if (not analysis.location or analysis.location == "Unknown") and scraped_location and scraped_location not in ["Unknown"]:
        analysis.location = scraped_location

    return {
        "analysis": analysis.model_dump(),
        "raw_text": job_text,
        "source_url": source_url,
        "title": analysis.title,
        "company": analysis.company,
        "location": analysis.location,
        "salary_range": analysis.salary_range,
        "work_mode": analysis.work_mode,
        "required_skills": analysis.required_skills,
        "preferred_skills": analysis.preferred_skills,
        "tech_stack": analysis.tech_stack,
        "soft_skills": analysis.soft_skills,
        "ats_keywords": analysis.ats_keywords,
        "summary": analysis.summary,
    }


from fastapi import FastAPI, HTTPException, Response, Depends, UploadFile, File, Form
from backend.services.document_parser import extract_text_from_file

# --- Resumes ---
@app.get("/api/resumes", response_model=List[Resume])
def get_resumes():
    return storage.get_resumes()


@app.post("/api/resumes", response_model=Resume)
def add_resume(req: ResumeCreate):
    if not req.name.strip() or not req.content.strip():
        raise HTTPException(status_code=400, detail="Resume name and content are required.")
    return storage.add_resume(name=req.name, content=req.content)


@app.post("/api/resumes/upload", response_model=Resume)
async def upload_resume_file(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
):
    try:
        content_bytes = await file.read()
        extracted_text = extract_text_from_file(content_bytes, file.filename)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text could be extracted from this document.")

        resume_name = name.strip() if (name and name.strip()) else Path(file.filename).stem
        resume = storage.add_resume(name=resume_name, content=extracted_text)
        return resume
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.delete("/api/resumes/{resume_id}")
def delete_resume(resume_id: str):
    success = storage.delete_resume(resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return {"success": True}


class MatchResumesRequest(BaseModel):
    job: JobAnalysisResult
    resumes: Optional[List[Resume]] = None


@app.post("/api/resumes/match", response_model=List[RankedResume])
def match_resumes(req: MatchResumesRequest):
    resumes = req.resumes or storage.get_resumes()
    ai = get_ai_engine()
    return ai.rank_resumes(resumes, req.job)


# --- Bulletskill Optimizer ---
@app.post("/api/resumes/optimize-bullet", response_model=BulletOptimizationResponse)
def optimize_bullet(req: BulletOptimizationRequest):
    ai = get_ai_engine()
    return ai.optimize_bullet(req)


# --- Tailored Outreach Pitch ---
class OutreachRequest(BaseModel):
    job: JobAnalysisResult
    resume_id: Optional[str] = None
    resume_content: Optional[str] = None


@app.post("/api/resumes/generate-outreach", response_model=OutreachResponse)
def generate_outreach(req: OutreachRequest):
    resume = None
    if req.resume_id:
        resume = storage.get_resume(req.resume_id)
    if not resume and req.resume_content:
        resume = Resume(id="temp", name="Candidate", content=req.resume_content)
    if not resume:
        resumes = storage.get_resumes()
        resume = resumes[0] if resumes else Resume(id="temp", name="Candidate", content="")

    ai = get_ai_engine()
    return ai.generate_outreach(req.job, resume)


# --- Applications Tracker CRUD ---
@app.get("/api/applications", response_model=List[Application])
def get_applications():
    return storage.get_applications()


@app.post("/api/applications", response_model=Application)
def add_application(req: ApplicationCreate):
    return storage.add_application(req)


@app.patch("/api/applications/{app_id}", response_model=Application)
def update_application(app_id: str, req: ApplicationUpdate):
    updated = storage.update_application(app_id, req)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found.")
    return updated


@app.delete("/api/applications/{app_id}")
def delete_application(app_id: str):
    success = storage.delete_application(app_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found.")
    return {"success": True}


# --- Excel Export ---
@app.get("/api/export/excel")
def export_excel():
    apps = storage.get_applications()
    excel_bytes = excel_exporter.export_workbook(apps)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=job_tracker.xlsx"},
    )


# --- Settings ---
@app.get("/api/settings", response_model=Settings)
def get_settings():
    return storage.get_settings()


@app.post("/api/settings", response_model=Settings)
def update_settings(req: SettingsUpdate):
    return storage.update_settings(req)


@app.post("/api/settings/test-ai")
def test_ai(req: SettingsUpdate):
    ai = AIEngine(
        api_base_url=req.api_base_url or "https://integrate.api.nvidia.com/v1",
        api_key=req.api_key,
        model_name=req.model_name or "nvidia/nemotron-4-340b-instruct",
    )
    client = ai._get_client()
    if not client or not ai.api_key:
        return {"success": False, "message": "No API key configured. App will use offline heuristic NLP."}

    try:
        resp = client.chat.completions.create(
            model=ai.model_name,
            messages=[{"role": "user", "content": "Ping. Respond with 'pong'"}],
            max_tokens=10,
        )
        return {
            "success": True,
            "message": f"Successfully connected to {ai.model_name}! Response: {resp.choices[0].message.content.strip()}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}. Check your API key, model name, and Base URL.",
        }


# --- Static frontend files mounting ---
dist_path = Path("frontend/dist")
if dist_path.exists() and dist_path.is_dir():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")
