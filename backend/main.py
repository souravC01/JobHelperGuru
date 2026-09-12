import os
import re
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Response, Depends, UploadFile, File, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.config import load_config
from backend.services.rate_limiter import RateLimiter, get_client_ip
from backend.services.resource_leases import ResourceLeases
from backend.models import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    Resume,
    ResumeCreate,
    ResumeUpdate,
    Settings,
    SettingsUpdate,
    ProviderProfileMetadata,
    ProviderProfileCreate,
    ProviderProfileUpdate,
    JobAnalysisResult,
    RankedResume,
    BulletOptimizationRequest,
    BulletOptimizationResponse,
    OutreachResponse,
    CoverLetterDocxRequest,
    User,
)
from backend.services.document_export import generate_cover_letter_docx, generate_docx_from_text
from backend.storage import StorageService
from backend.services.scraper import ScraperService
from backend.services.ai_engine import AIEngine, extract_raw_content_from_response
from backend.services.excel_exporter import ExcelExporter
from backend.services.object_storage import ObjectStorageService
from backend.services.outbound_http import SSRFBlockedError
from backend.routers.auth import router as auth_router, get_current_user, get_optional_user, set_storage_service


class LimitBodySizeMiddleware:
    """
    ASGI middleware enforcing body size caps:
    - 1 MiB for standard JSON / URL-encoded requests
    - 12 MiB for multipart/form-data uploads
    Rejects immediately via Content-Length or during streaming with HTTP 413.
    """

    def __init__(
        self,
        app: ASGIApp,
        max_json_bytes: int = 1024 * 1024,
        max_multipart_bytes: int = 12 * 1024 * 1024,
    ):
        self.app = app
        self.max_json_bytes = max_json_bytes
        self.max_multipart_bytes = max_multipart_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_type = headers.get(b"content-type", b"").decode("latin-1").lower()
        is_multipart = "multipart/form-data" in content_type
        limit = self.max_multipart_bytes if is_multipart else self.max_json_bytes

        content_length = headers.get(b"content-length")
        if content_length:
            try:
                cl = int(content_length.decode("latin-1"))
                if cl > limit:
                    res = Response(
                        content='{"detail":"Request body exceeds maximum allowed size."}',
                        status_code=413,
                        media_type="application/json",
                    )
                    await res(scope, receive, send)
                    return
            except ValueError:
                pass

        received_bytes = 0
        response_started = False

        class StreamingBodyTooLarge(Exception):
            pass

        async def limited_receive():
            nonlocal received_bytes
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                received_bytes += len(body)
                if received_bytes > limit:
                    raise StreamingBodyTooLarge()
            return message

        async def monitored_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, monitored_send)
        except StreamingBodyTooLarge:
            if not response_started:
                res = Response(
                    content='{"detail":"Request body exceeds maximum allowed size."}',
                    status_code=413,
                    media_type="application/json",
                )
                await res(scope, receive, send)
            else:
                raise


app = FastAPI(title="JobHelperGuru API", version="1.0.0")
app.include_router(auth_router)

# Body size limit middleware
app.add_middleware(LimitBodySizeMiddleware)

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
    expose_headers=["Content-Disposition", "X-Fallback-Generated"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


# Services
storage = StorageService(db_path=os.environ.get("JOB_HELPER_DB", "data/tracker.db"))
set_storage_service(storage)
if storage.is_postgres:
    print("[INFO] Connected to Neon PostgreSQL database.")
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
    if not user_id:
        return AIEngine(
            api_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key="",
            model_name="offline-heuristic",
        )
    settings = storage.get_settings(user_id=user_id)
    if settings.use_offline_mode:
        return AIEngine(
            api_base_url=settings.api_base_url,
            api_key="",
            model_name="offline-heuristic",
        )
    api_key = settings.api_key
    if settings.active_profile_id:
        profile_key = storage.get_provider_profile_secret(settings.active_profile_id, user_id=user_id)
        if profile_key:
            api_key = profile_key
    return AIEngine(
        api_base_url=settings.api_base_url,
        api_key=api_key,
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
    raw_text: Optional[str] = None


@app.post("/api/jobs/analyze")
@app.post("/api/analyze/job")
def analyze_job(
    req: JobAnalyzeRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
):
    job_input_text = req.text or req.raw_text
    if not req.url and not job_input_text:
        raise HTTPException(status_code=400, detail="Either a URL or job text must be provided.")

    limiter = RateLimiter(storage)
    if current_user:
        allowed, _, retry_after = limiter.check("user_ai_ops", current_user.id, limit=30, window_seconds=60)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many analysis requests. Please try again later.",
                headers={"Retry-After": str(int(retry_after))},
            )
    else:
        cfg = load_config()
        client_ip = get_client_ip(request, trust_proxy_headers=getattr(cfg, "trust_proxy_headers", False))
        allowed, _, retry_after = limiter.check("anon_analysis", client_ip, limit=10, window_seconds=60)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many analysis requests. Please try again later or sign in.",
                headers={"Retry-After": str(int(retry_after))},
            )

    cfg = load_config()
    client_ip = get_client_ip(request, trust_proxy_headers=getattr(cfg, "trust_proxy_headers", False))
    lease_service = ResourceLeases(storage)
    lease_subject = current_user.id if current_user else f"anon:{client_ip}"
    lease_id = lease_service.acquire(user_id=lease_subject, kind="analysis", ttl_seconds=30)

    try:
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
        elif job_input_text:
            parsed = scraper.parse_raw_text(job_input_text)
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

        UNKNOWN_TITLES = {"", "Open Position", "Detected Role", "Unknown Role", "Role Title", "Exact Role Title"}
        UNKNOWN_COMPANIES = {"", "Unknown Company", "Company", "Company Name", "Detected Company"}
        UNKNOWN_LOCATIONS = {"", "Unknown", "Identified Location", "City, State or Remote/Hybrid", "Unknown Location"}

        # Prefer scraped title/company/location if AI/heuristic returned generic placeholders
        if (not analysis.title or analysis.title in UNKNOWN_TITLES) and scraped_title and scraped_title not in UNKNOWN_TITLES:
            analysis.title = scraped_title
        if (not analysis.company or analysis.company in UNKNOWN_COMPANIES) and scraped_company and scraped_company not in UNKNOWN_COMPANIES:
            analysis.company = scraped_company
        if (not analysis.location or analysis.location in UNKNOWN_LOCATIONS) and scraped_location and scraped_location not in UNKNOWN_LOCATIONS:
            analysis.location = scraped_location

        analysis_dict = analysis.model_dump()
        analysis_dict["title"] = analysis.title
        analysis_dict["company"] = analysis.company
        analysis_dict["location"] = analysis.location

        return {
            "analysis": analysis_dict,
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
    finally:
        lease_service.release(lease_id)


from backend.services.document_parser import extract_text_from_file

# --- Resumes ---
@app.get("/api/resumes", response_model=List[Resume])
def get_resumes(current_user: User = Depends(get_current_user)):
    resumes = storage.get_resumes(user_id=current_user.id)
    for r in resumes:
        if r.file_key or r.attachment_id:
            r.download_url = f"/api/resumes/{r.id}/download"
    return resumes


MAX_RESUMES_PER_USER = 10
MAX_USER_STORAGE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".rtf"}
MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per file


@app.post("/api/resumes", response_model=Resume)
def add_resume(req: ResumeCreate, current_user: User = Depends(get_current_user)):
    if not req.name.strip() or not req.content.strip():
        raise HTTPException(status_code=400, detail="Resume name and content are required.")
    if len(req.content) > 100_000:
        raise HTTPException(
            status_code=422,
            detail="Resume content exceeds maximum limit of 100,000 characters.",
        )
    user_resume_count = storage.count_user_resumes(current_user.id)
    if user_resume_count >= MAX_RESUMES_PER_USER:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum limit of {MAX_RESUMES_PER_USER} resumes reached per account.",
        )
    return storage.add_resume(name=req.name, content=req.content, file_key=None, user_id=current_user.id)


@app.post("/api/resumes/upload", response_model=Resume)
def upload_resume_file(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    content_override: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    try:
        user_resume_count = storage.count_user_resumes(current_user.id)
        if user_resume_count >= MAX_RESUMES_PER_USER:
            raise HTTPException(
                status_code=422,
                detail=f"Maximum limit of {MAX_RESUMES_PER_USER} resumes reached per account.",
            )

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_RESUME_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}'. Allowed formats: .pdf, .docx, .doc, .txt, .md, .rtf",
            )

        content_bytes = file.file.read(MAX_RESUME_SIZE_BYTES + 1)
        if len(content_bytes) > MAX_RESUME_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="File exceeds maximum allowed size of 10MB.",
            )

        current_bytes = storage.get_user_upload_bytes(current_user.id)
        if current_bytes + len(content_bytes) > MAX_USER_STORAGE_BYTES:
            raise HTTPException(
                status_code=422,
                detail="Maximum total storage limit of 50MB reached for resumes.",
            )

        if content_override and content_override.strip():
            if len(content_override) > 100_000:
                raise HTTPException(
                    status_code=422,
                    detail="Resume content exceeds maximum limit of 100,000 characters.",
                )
            final_content = content_override.strip()
        else:
            extracted_text = extract_text_from_file(content_bytes, file.filename)
            if not extracted_text.strip():
                raise HTTPException(status_code=400, detail="No readable text could be extracted from this document.")
            final_content = extracted_text.strip()

        # Upload binary to Cloudflare R2 or local directory scoped to user_id
        try:
            file_key = object_storage.upload_file(
                content_bytes=content_bytes,
                filename=file.filename,
                content_type=file.content_type,
                user_id=current_user.id,
            )
        except RuntimeError as re:
            raise HTTPException(status_code=503, detail="Storage service temporarily unavailable.")

        storage_backend = "r2" if object_storage.is_configured else "local"
        attachment = storage.create_attachment(
            user_id=current_user.id,
            storage_backend=storage_backend,
            object_key=file_key,
            original_filename=file.filename,
            content_type=file.content_type,
            size_bytes=len(content_bytes),
        )

        resume_name = name.strip() if (name and name.strip()) else Path(file.filename).stem
        try:
            resume = storage.add_resume(
                name=resume_name,
                content=final_content,
                file_key=file_key,
                user_id=current_user.id,
                attachment_id=attachment.id,
            )
        except Exception as e:
            object_storage.delete_file(file_key, user_id=current_user.id)
            storage.update_attachment_deletion_state(attachment.id, "failed", user_id=current_user.id)
            raise HTTPException(status_code=500, detail="Failed to save resume record.")

        resume.download_url = f"/api/resumes/{resume.id}/download"
        return resume
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.post("/api/resumes/parse-file")
def parse_resume_file(
    file: UploadFile = File(...),
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

        return {
            "filename": file.filename,
            "suggested_title": Path(file.filename).stem,
            "text": extracted_text,
        }
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.post("/api/resumes/export-cover-letter-docx")
def export_cover_letter_docx(
    req: CoverLetterDocxRequest,
    current_user: User = Depends(get_current_user),
):
    if not req.cover_letter_text or not req.cover_letter_text.strip():
        raise HTTPException(status_code=422, detail="Cover letter text cannot be empty.")

    candidate_name = req.candidate_name or current_user.name or ""
    docx_bytes = generate_cover_letter_docx(
        cover_letter_text=req.cover_letter_text,
        candidate_name=candidate_name,
        company=req.company or "",
        role=req.role or "",
        subject_line=req.subject_line or "",
    )
    safe_company = re.sub(r'[^a-zA-Z0-9_-]', '_', req.company or "Company").strip('_') or "Company"
    safe_role = re.sub(r'[^a-zA-Z0-9_-]', '_', req.role or "Role").strip('_') or "Role"
    filename = f"Cover_Letter_{safe_company}_{safe_role}.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@app.get("/api/resumes/{resume_id}/download")
def download_resume_file(
    resume_id: str,
    current_user: User = Depends(get_current_user),
):
    resume = storage.get_resume(resume_id, user_id=current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    attachment = None
    if resume.attachment_id:
        attachment = storage.get_attachment(resume.attachment_id, user_id=current_user.id)
    elif resume.file_key:
        attachment = storage.get_attachment_by_key(resume.file_key, user_id=current_user.id)

    if attachment and attachment.deletion_state != "active":
        raise HTTPException(status_code=404, detail="File is no longer available.")

    object_key = attachment.object_key if attachment else resume.file_key
    raw_filename = (attachment.original_filename if attachment else None) or f"{resume.name}.pdf"
    safe_filename = re.sub(r'[\r\n"\\]', '_', raw_filename).strip() or "resume.pdf"
    content_type = (attachment.content_type if attachment else None) or "application/octet-stream"

    file_bytes = None
    if object_key:
        file_bytes = object_storage.get_file(object_key, user_id=current_user.id)

    if file_bytes:
        return Response(
            content=file_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition, X-Fallback-Generated",
            },
        )

    # Graceful fallback: synthesize clean .docx from saved resume text
    raw_text = (getattr(resume, "raw_text", None) or getattr(resume, "content", None) or "").strip()
    if raw_text:
        fallback_bytes = generate_docx_from_text(title=resume.name or "Resume", text=raw_text)
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', resume.name or "resume").strip('_') or "resume"
        fallback_filename = f"{safe_name}_generated.docx"
        return Response(
            content=fallback_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{fallback_filename}"',
                "X-Fallback-Generated": "true",
                "Access-Control-Expose-Headers": "Content-Disposition, X-Fallback-Generated",
            },
        )

    raise HTTPException(status_code=404, detail="Original uploaded file was not found in storage.")


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
    if updated.file_key or updated.attachment_id:
        updated.download_url = f"/api/resumes/{updated.id}/download"
    return updated


@app.delete("/api/resumes/{resume_id}")
def delete_resume(resume_id: str, current_user: User = Depends(get_current_user)):
    resume = storage.get_resume(resume_id, user_id=current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if resume.attachment_id or resume.file_key:
        attachment = None
        if resume.attachment_id:
            attachment = storage.get_attachment(resume.attachment_id, user_id=current_user.id)
        elif resume.file_key:
            attachment = storage.get_attachment_by_key(resume.file_key, user_id=current_user.id)

        if attachment:
            storage.update_attachment_deletion_state(attachment.id, "pending", user_id=current_user.id)
            deleted = object_storage.delete_file(attachment.object_key, user_id=current_user.id)
            if not deleted:
                storage.update_attachment_deletion_state(attachment.id, "failed", user_id=current_user.id)
                raise HTTPException(status_code=500, detail="Failed to delete associated storage file.")
            storage.delete_attachment(attachment.id, user_id=current_user.id)
        elif resume.file_key:
            object_storage.delete_file(resume.file_key, user_id=current_user.id)

    storage.delete_resume(resume_id, user_id=current_user.id)
    return {"success": True}


class MatchResumesRequest(BaseModel):
    job: JobAnalysisResult
    resumes: Optional[List[Resume]] = None


def _check_user_ai_rate_limit(user_id: str):
    limiter = RateLimiter(storage)
    allowed, _, retry_after = limiter.check("user_ai_ops", user_id, limit=30, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many AI operations requested. Please wait before retrying.",
            headers={"Retry-After": str(int(retry_after))},
        )


@app.post("/api/resumes/match", response_model=List[RankedResume])
def match_resumes(req: MatchResumesRequest, current_user: User = Depends(get_current_user)):
    _check_user_ai_rate_limit(current_user.id)
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
    _check_user_ai_rate_limit(current_user.id)
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
    candidate_name: Optional[str] = None


@app.post("/api/resumes/generate-outreach", response_model=OutreachResponse)
def generate_outreach(req: OutreachRequest, current_user: User = Depends(get_current_user)):
    _check_user_ai_rate_limit(current_user.id)
    resume = None
    if req.resume_id:
        resume = storage.get_resume(req.resume_id, user_id=current_user.id)
    if not resume and req.resume_content:
        resume = Resume(id="temp", name="Candidate", content=req.resume_content)
    if not resume:
        resumes = storage.get_resumes(user_id=current_user.id)
        resume = resumes[0] if resumes else Resume(id="temp", name="Candidate", content="")

    ai = get_ai_engine(user_id=current_user.id)
    # Prefer account info name (Google account name or account creation name)
    account_name = (current_user.name or "").strip() or (req.candidate_name or "").strip() or "Candidate"
    try:
        return ai.generate_outreach(req.job, resume, candidate_name=account_name)
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
    updated = storage.update_application(app_id, req, user_id=current_user.id)
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


# --- Settings & Provider Profiles ---
@app.get("/api/settings", response_model=Settings)
def get_settings(current_user: User = Depends(get_current_user)):
    s = storage.get_settings(user_id=current_user.id)
    s_dict = s.model_dump()
    s_dict["api_key"] = ""
    s_dict["saved_keys"] = "[]"
    return Settings(**s_dict)


@app.post("/api/settings", response_model=Settings)
def update_settings(req: SettingsUpdate, current_user: User = Depends(get_current_user)):
    s = storage.update_settings(req, user_id=current_user.id)
    s_dict = s.model_dump()
    s_dict["api_key"] = ""
    s_dict["saved_keys"] = "[]"
    return Settings(**s_dict)


@app.get("/api/settings/profiles", response_model=List[ProviderProfileMetadata])
def list_profiles(current_user: User = Depends(get_current_user)):
    return storage.get_provider_profiles(user_id=current_user.id)


@app.post("/api/settings/profiles", response_model=ProviderProfileMetadata)
def create_profile(req: ProviderProfileCreate, current_user: User = Depends(get_current_user)):
    return storage.create_provider_profile(user_id=current_user.id, profile_in=req)


@app.get("/api/settings/profiles/{profile_id}", response_model=ProviderProfileMetadata)
def get_profile(profile_id: str, current_user: User = Depends(get_current_user)):
    profile = storage.get_provider_profile(profile_id, user_id=current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Provider profile not found.")
    return profile


@app.patch("/api/settings/profiles/{profile_id}", response_model=ProviderProfileMetadata)
def update_profile(profile_id: str, req: ProviderProfileUpdate, current_user: User = Depends(get_current_user)):
    profile = storage.update_provider_profile(profile_id, user_id=current_user.id, updates=req)
    if not profile:
        raise HTTPException(status_code=404, detail="Provider profile not found.")
    return profile


@app.post("/api/settings/profiles/{profile_id}/activate", response_model=ProviderProfileMetadata)
def activate_profile(profile_id: str, current_user: User = Depends(get_current_user)):
    profile = storage.activate_provider_profile(profile_id, user_id=current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Provider profile not found.")
    return profile


@app.delete("/api/settings/profiles/{profile_id}")
def delete_profile(profile_id: str, current_user: User = Depends(get_current_user)):
    success = storage.delete_provider_profile(profile_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Provider profile not found.")
    return {"success": True}


@app.post("/api/settings/test-ai")
def test_ai(req: SettingsUpdate, current_user: User = Depends(get_current_user)):
    _check_user_ai_rate_limit(current_user.id)
    try:
        api_key = req.api_key
        if not api_key:
            s = storage.get_settings(user_id=current_user.id)
            if s.active_profile_id:
                api_key = storage.get_provider_profile_secret(s.active_profile_id, user_id=current_user.id)
                if not api_key:
                    prof = storage.get_provider_profile(s.active_profile_id, user_id=current_user.id)
                    if prof and prof.needs_reentry:
                        return {
                            "success": False,
                            "message": "The server encryption key was changed since this provider key was saved. Please re-enter your API key and click 'Save & Activate Key'.",
                        }
            if not api_key:
                api_key = s.api_key
        ai = AIEngine(
            api_base_url=req.api_base_url or "https://integrate.api.nvidia.com/v1",
            api_key=api_key or "",
            model_name=req.model_name or "nvidia/nemotron-4-340b-instruct",
        )
        client = ai._get_client()
        if not client or not ai.api_key:
            return {"success": False, "message": "No API key configured. App will use offline heuristic NLP."}

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
    except SSRFBlockedError as e:
        return {
            "success": False,
            "message": f"Connection blocked by security policy: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}. Check your API key, model name, and Base URL.",
        }


# --- Static frontend files mounting ---
dist_path = (Path(__file__).resolve().parent.parent / "frontend" / "dist").resolve()
if dist_path.exists() and dist_path.is_dir():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")
