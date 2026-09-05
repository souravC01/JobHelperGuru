import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Response, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.models import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    Resume,
    ResumeCreate,
    ResumeUpdate,
    Settings,
    SettingsUpdate,
    JobAnalysisResult,
    RankedResume,
    BulletOptimizationRequest,
    BulletOptimizationResponse,
    OutreachResponse,
    User,
)
from backend.storage import StorageService
from backend.services.scraper import ScraperService
from backend.services.ai_engine import AIEngine, extract_raw_content_from_response
from backend.services.excel_exporter import ExcelExporter
from backend.services.object_storage import ObjectStorageService
from backend.routers.auth import router as auth_router, get_current_user, get_optional_user, set_storage_service

app = FastAPI(title="JobHelperGuru API", version="1.0.0")
app.include_router(auth_router)

# CORS Setup
allowed_origins_raw = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000",
)
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
storage = StorageService(db_path=os.environ.get("JOB_HELPER_DB", "data/tracker.db"))
set_storage_service(storage)
if storage.is_postgres:
    print("[INFO] Connected to Neon PostgreSQL database.")
    if os.getenv("RUN_SQLITE_MIGRATION", "false").lower() in ("true", "1", "yes"):
        try:
            storage.migrate_from_sqlite("data/tracker.db")
        except Exception as e:
            print(f"[INFO] SQLite migration note: {e}")
else:
    print("[INFO] Using local SQLite storage (data/tracker.db).")

scraper = ScraperService()
excel_exporter = ExcelExporter()
object_storage = ObjectStorageService()
if object_storage.is_configured:
    print("[INFO] Connected to Cloudflare R2 Object Storage.")
else:
    print("[INFO] Cloudflare R2 not configured. Using local file storage fallback.")


def get_ai_engine(user_id: Optional[str] = None) -> AIEngine:
    settings = storage.get_settings(user_id=user_id)
    if settings.use_offline_mode:
        return AIEngine(
            api_base_url=settings.api_base_url,
            api_key="",
            model_name="offline-heuristic",
        )
    return AIEngine(
        api_base_url=settings.api_base_url,
        api_key=settings.api_key,
        model_name=settings.model_name,
    )


# --- Health ---
@app.api_route("/api/health", methods=["GET", "HEAD"])
@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {
        "status": "ok",
        "app": "JobHelperGuru",
        "database": "postgresql" if storage.is_postgres else "sqlite",
        "object_storage": "cloudflare_r2" if object_storage.is_configured else "local",
    }


# --- Job Analysis & Scraping ---
class JobAnalyzeRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None


@app.post("/api/jobs/analyze")
def analyze_job(req: JobAnalyzeRequest, current_user: Optional[User] = Depends(get_optional_user)):
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

    if (
        not job_text
        or len(job_text.strip()) < 30
        or job_text.strip().startswith("Error fetching URL:")
        or job_text.strip().startswith("Disallowed or private URL target")
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not extract readable text from this job URL (it may require login or block automated scraping). "
                "Please copy and paste the job description text directly into the 'Paste Job Text' tab."
            ),
        )

    user_id = current_user.id if current_user else None
    ai = get_ai_engine(user_id=user_id)
    try:
        analysis = ai.analyze_job(job_text, source_url=source_url)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(e),
                "can_switch_offline": True,
                "error_type": "ai_api_error",
                "model_name": ai.model_name,
            },
        )

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
        "experience_level": analysis.experience_level,
        "experience_required": analysis.experience_required,
        "is_new_grad_role": analysis.is_new_grad_role,
        "new_grad_criteria": analysis.new_grad_criteria,
        "required_skills": analysis.required_skills,
        "preferred_skills": analysis.preferred_skills,
        "tech_stack": analysis.tech_stack,
        "soft_skills": analysis.soft_skills,
        "ats_keywords": analysis.ats_keywords,
        "summary": analysis.summary,
    }


from backend.services.document_parser import extract_text_from_file

# --- Resumes ---
@app.get("/api/resumes", response_model=List[Resume])
def get_resumes(current_user: User = Depends(get_current_user)):
    resumes = storage.get_resumes(user_id=current_user.id)
    for r in resumes:
        if r.file_key:
            r.download_url = object_storage.generate_download_url(r.file_key)
    return resumes


@app.post("/api/resumes", response_model=Resume)
def add_resume(req: ResumeCreate, current_user: User = Depends(get_current_user)):
    if not req.name.strip() or not req.content.strip():
        raise HTTPException(status_code=400, detail="Resume name and content are required.")
    return storage.add_resume(name=req.name, content=req.content, file_key=req.file_key, user_id=current_user.id)


ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".rtf"}
MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@app.post("/api/resumes/upload", response_model=Resume)
def upload_resume_file(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    try:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_RESUME_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}'. Allowed formats: .pdf, .docx, .doc, .txt, .rtf",
            )

        content_bytes = file.file.read(MAX_RESUME_SIZE_BYTES + 1)
        if len(content_bytes) > MAX_RESUME_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="File exceeds maximum allowed size of 10MB.",
            )

        extracted_text = extract_text_from_file(content_bytes, file.filename)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text could be extracted from this document.")

        # Upload raw binary (.pdf / .docx) to Cloudflare R2 or local uploads scoped by user_id
        file_key = object_storage.upload_file(
            content_bytes=content_bytes,
            filename=file.filename,
            content_type=file.content_type,
            user_id=current_user.id,
        )

        resume_name = name.strip() if (name and name.strip()) else Path(file.filename).stem
        resume = storage.add_resume(name=resume_name, content=extracted_text, file_key=file_key, user_id=current_user.id)
        if file_key:
            resume.download_url = object_storage.generate_download_url(file_key)
        return resume
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.post("/api/resumes/parse-file")
def parse_resume_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed formats: .pdf, .docx, .doc, .txt, .rtf",
        )
    content_bytes = file.file.read(MAX_RESUME_SIZE_BYTES + 1)
    if len(content_bytes) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File exceeds maximum allowed size of 10MB.",
        )
    extracted_text = extract_text_from_file(content_bytes, file.filename)
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No readable text could be extracted from this document.")

    return {
        "filename": file.filename,
        "suggested_title": Path(file.filename).stem,
        "text": extracted_text,
    }


@app.patch("/api/resumes/{resume_id}", response_model=Resume)
def update_resume(
    resume_id: str,
    req: ResumeUpdate,
    current_user: User = Depends(get_current_user),
):
    updated = storage.update_resume(
        resume_id,
        name=req.name,
        content=req.content,
        user_id=current_user.id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if updated.file_key:
        updated.download_url = object_storage.generate_download_url(updated.file_key)
    return updated


@app.delete("/api/resumes/{resume_id}")
def delete_resume(resume_id: str, current_user: User = Depends(get_current_user)):
    resume = storage.get_resume(resume_id, user_id=current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if resume.file_key:
        object_storage.delete_file(resume.file_key)
    success = storage.delete_resume(resume_id, user_id=current_user.id)
    return {"success": True}


class MatchResumesRequest(BaseModel):
    job: JobAnalysisResult
    resumes: Optional[List[Resume]] = None


@app.post("/api/resumes/match", response_model=List[RankedResume])
def match_resumes(req: MatchResumesRequest, current_user: User = Depends(get_current_user)):
    resumes = req.resumes or storage.get_resumes(user_id=current_user.id)
    ai = get_ai_engine(user_id=current_user.id)
    try:
        return ai.rank_resumes(resumes, req.job)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(e),
                "can_switch_offline": True,
                "error_type": "ai_api_error",
                "model_name": ai.model_name,
            },
        )


# --- Bulletskill Optimizer ---
@app.post("/api/resumes/optimize-bullet", response_model=BulletOptimizationResponse)
def optimize_bullet(req: BulletOptimizationRequest, current_user: User = Depends(get_current_user)):
    ai = get_ai_engine(user_id=current_user.id)
    try:
        return ai.optimize_bullet(req)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(e),
                "can_switch_offline": True,
                "error_type": "ai_api_error",
                "model_name": ai.model_name,
            },
        )


# --- Tailored Outreach Pitch ---
class OutreachRequest(BaseModel):
    job: JobAnalysisResult
    resume_id: Optional[str] = None
    resume_content: Optional[str] = None


@app.post("/api/resumes/generate-outreach", response_model=OutreachResponse)
def generate_outreach(req: OutreachRequest, current_user: User = Depends(get_current_user)):
    resume = None
    if req.resume_id:
        resume = storage.get_resume(req.resume_id, user_id=current_user.id)
    if not resume and req.resume_content:
        resume = Resume(id="temp", name="Candidate", content=req.resume_content)
    if not resume:
        resumes = storage.get_resumes(user_id=current_user.id)
        resume = resumes[0] if resumes else Resume(id="temp", name="Candidate", content="")

    ai = get_ai_engine(user_id=current_user.id)
    try:
        return ai.generate_outreach(req.job, resume)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(e),
                "can_switch_offline": True,
                "error_type": "ai_api_error",
                "model_name": ai.model_name,
            },
        )


# --- Applications Tracker CRUD ---
@app.get("/api/applications", response_model=List[Application])
def get_applications(current_user: User = Depends(get_current_user)):
    return storage.get_applications(user_id=current_user.id)


@app.post("/api/applications", response_model=Application)
def add_application(req: ApplicationCreate, current_user: User = Depends(get_current_user)):
    return storage.add_application(req, user_id=current_user.id)


@app.patch("/api/applications/{app_id}", response_model=Application)
def update_application(app_id: str, req: ApplicationUpdate, current_user: User = Depends(get_current_user)):
    updated = storage.update_application(app_id, req)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found.")
    return updated


@app.delete("/api/applications/{app_id}")
def delete_application(app_id: str, current_user: User = Depends(get_current_user)):
    success = storage.delete_application(app_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found.")
    return {"success": True}


# --- Excel Export ---
@app.get("/api/export/excel")
def export_excel(current_user: User = Depends(get_current_user)):
    apps = storage.get_applications(user_id=current_user.id)
    excel_bytes = excel_exporter.export_workbook(apps)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=job_tracker.xlsx"},
    )


# --- Settings ---
@app.get("/api/settings", response_model=Settings)
def get_settings(current_user: User = Depends(get_current_user)):
    return storage.get_settings(user_id=current_user.id)


@app.post("/api/settings", response_model=Settings)
def update_settings(req: SettingsUpdate, current_user: User = Depends(get_current_user)):
    return storage.update_settings(req, user_id=current_user.id)


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
            max_tokens=100,
        )
        content = extract_raw_content_from_response(resp)
        response_preview = f" Response: {content}" if content else ""
        return {
            "success": True,
            "message": f"Successfully connected to {ai.model_name}!{response_preview}",
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
