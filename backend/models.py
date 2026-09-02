from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    WISHLIST = "Wishlist"
    APPLIED = "Applied"
    INTERVIEWING = "Interviewing"
    OFFERED = "Offered"
    REJECTED = "Rejected"
    ARCHIVED = "Archived"


class Application(BaseModel):
    id: str
    company: str
    role: str
    status: ApplicationStatus = ApplicationStatus.WISHLIST
    location: Optional[str] = "Unknown"
    salary: Optional[str] = "Not specified"
    url: Optional[str] = ""
    required_skills: List[str] = Field(default_factory=list)
    ats_keywords: List[str] = Field(default_factory=list)
    date_added: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    application_date: Optional[str] = ""
    follow_up_date: Optional[str] = ""
    notes: Optional[str] = ""
    best_resume_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ApplicationCreate(BaseModel):
    company: str
    role: str
    status: Optional[ApplicationStatus] = ApplicationStatus.WISHLIST
    location: Optional[str] = "Unknown"
    salary: Optional[str] = "Not specified"
    url: Optional[str] = ""
    required_skills: Optional[List[str]] = Field(default_factory=list)
    ats_keywords: Optional[List[str]] = Field(default_factory=list)
    application_date: Optional[str] = ""
    follow_up_date: Optional[str] = ""
    notes: Optional[str] = ""
    best_resume_id: Optional[str] = None


class ApplicationUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    url: Optional[str] = None
    required_skills: Optional[List[str]] = None
    ats_keywords: Optional[List[str]] = None
    application_date: Optional[str] = None
    follow_up_date: Optional[str] = None
    notes: Optional[str] = None
    best_resume_id: Optional[str] = None


class Resume(BaseModel):
    id: str
    name: str
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ResumeCreate(BaseModel):
    name: str
    content: str


class Settings(BaseModel):
    api_base_url: str = "https://integrate.api.nvidia.com/v1"
    api_key: str = ""
    model_name: str = "nvidia/nemotron-4-340b-instruct"
    default_follow_up_days: int = 7


class SettingsUpdate(BaseModel):
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    default_follow_up_days: Optional[int] = None


class ScrapedJob(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    raw_text: str = ""
    source_url: str = ""


class JobAnalysisResult(BaseModel):
    company: str = "Unknown Company"
    title: str = "Open Position"
    location: str = "Unknown"
    work_mode: str = "Unknown"  # Remote, Hybrid, Onsite, Unknown
    salary_range: str = "Not specified"
    experience_level: str = "Not specified"  # Entry, Mid, Senior, Lead
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    ats_keywords: List[str] = Field(default_factory=list)
    summary: str = ""


class ResumeMatchResult(BaseModel):
    resume_id: Optional[str] = None
    resume_name: Optional[str] = ""
    match_score: int = 0
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    fit_summary: str = ""


class RankedResume(BaseModel):
    resume_id: str
    resume_name: str
    match_score: int
    matched_keywords: List[str]
    missing_keywords: List[str]
    fit_summary: str
    is_best_fit: bool = False


class ClaimStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED_SKILL = "unverified_skill"
    UNVERIFIED_METRIC = "unverified_metric"
    VERIFIED_DERIVED_METRIC = "verified_derived_metric"


class BulletAlternative(BaseModel):
    variant_name: str = "Candidate A (ATS-focused)"
    bullet: str
    what: str
    how: str
    result_or_reason: str
    claim_status: ClaimStatus = ClaimStatus.VERIFIED
    requires_confirmation: bool = False
    assumption: Optional[str] = None


class BulletOptimizationRequest(BaseModel):
    target_job_title: str
    section_type: str = "work_history"  # "work_history" or "project"
    target_keyword: Optional[str] = ""
    target_keywords: List[str] = Field(default_factory=list)
    existing_bullet: Optional[str] = ""
    evidence_context: List[str] = Field(default_factory=list)


class BulletOptimizationResponse(BaseModel):
    status: str = "rewritten"  # rewritten, suggested, no_change_needed
    target_keyword: str = ""
    target_keywords: List[str] = Field(default_factory=list)
    claim_status: ClaimStatus
    selected_bullet_index: int = 0
    alternatives: List[BulletAlternative] = Field(default_factory=list)
    requires_confirmation: bool = False
    warning: Optional[str] = None
    validation: Dict[str, bool] = Field(default_factory=dict)
    target_project_name: Optional[str] = None
    original_bullet_to_replace: Optional[str] = None
    replacement_rationale: Optional[str] = None
    available_resume_bullets: List[Dict[str, str]] = Field(default_factory=list)


class OutreachResponse(BaseModel):
    subject_line: str
    cover_letter_pitch: str
    connection_note: str
