"""Reusable, source-verified resume analysis without job or scorer dependence."""
import time
from typing import Any, Literal

from pydantic import Field, StrictBool, StrictInt
from backend.models import Resume
from backend.services.skill_matching import contains_skill
from .chunking import TextChunk, chunk_text
from .models import MatchContract, NonEmptyString, EvaluationStatus, EvidenceLevel, ProfileFact, ResumeProfile, SourceSpan
from .normalization import CANONICAL_SKILL_ALIASES, canonicalize_skill
from .provenance import _quote_span, date_ranges, fingerprint, section_at, source_hash, verified_level, work_span

PROFILE_EXTRACTOR_VERSION = "resume-profile-v3"


class FactProposal(MatchContract):
    kind: Literal["skill", "activity", "credential", "employment"]
    canonical_key: NonEmptyString
    level: EvidenceLevel
    source_quote: NonEmptyString


class ProfileChunk(MatchContract):
    chunk_index: StrictInt = Field(ge=0)
    complete: StrictBool
    items: list[FactProposal]


def profile_version_key(engine):
    return fingerprint([PROFILE_EXTRACTOR_VERSION, engine.api_base_url, engine.model_name,
                        "openai-chat-v1", CANONICAL_SKILL_ALIASES])


def _fact(proposal, chunk, text):
    quote, start, end = _quote_span(proposal.source_quote, chunk)
    key = canonicalize_skill(proposal.canonical_key)
    if not key or (proposal.kind == "skill" and not contains_skill(quote, key)):
        raise ValueError("Unsupported skill fact")
    level = verified_level(text, start, end, key, proposal.level.value)
    section = section_at(text, start)
    # A quote including its own heading must get that heading's section.
    if section == "unknown": section = section_at(text, end)
    if section == "skills" and level == "demonstrated": level = "listed"
    dates = date_ranges(quote) if proposal.kind == "employment" else []
    if proposal.kind == "employment" and (not work_span(text, start, end) or len(dates) != 1 or level != "demonstrated"):
        raise ValueError("Employment needs one dated, non-negated work entry")
    values = dict(kind=proposal.kind, canonical_key=key, level=level, source_quote=quote,
                  source_start=start, source_end=end, section=section,
                  start=dates[0][0] if dates else None, end=dates[0][1] if dates else None)
    return ProfileFact(id="fact_"+fingerprint([source_hash(text), PROFILE_EXTRACTOR_VERSION, values])[:20], **values)


def _profile_fingerprint(profile):
    return fingerprint(profile.model_dump(mode="json", exclude={"profile_fingerprint"}))


def validate_profile(profile, resume, version_key=None):
    if profile.status != "complete" or profile.resume_id != resume.id or profile.source_hash != source_hash(resume.content) or resume.extraction_warnings:
        raise ValueError("Profile is not complete for current source")
    if profile.extractor_version != PROFILE_EXTRACTOR_VERSION or (version_key and profile.version_key != version_key):
        raise ValueError("Profile version mismatch")
    expected = [(c.start,c.end) for c in chunk_text(resume.content)]
    if [(s.start,s.end) for s in profile.processed_source_chunks] != expected:
        raise ValueError("Missing source coverage")
    for fact in profile.facts:
        if resume.content[fact.source_start:fact.source_end] != fact.source_quote:
            raise ValueError("Invalid cached provenance")
        recreated = _fact(FactProposal(kind=fact.kind, canonical_key=fact.canonical_key,
                                     level=fact.level, source_quote=fact.source_quote),
                          TextChunk(fact.source_start,fact.source_end,fact.source_quote),resume.content)
        if recreated.model_dump(exclude={"employment_id"}) != fact.model_dump(exclude={"employment_id"}):
            raise ValueError("Invalid cached facts")
        if fact.employment_id:
            employment=next(e for e in profile.facts if e.id==fact.employment_id)
            if not employment.source_start <= fact.source_start < fact.source_end <= employment.source_end:
                raise ValueError("Invalid employment association")
    if profile.profile_fingerprint != _profile_fingerprint(profile):
        raise ValueError("Invalid profile fingerprint")
    return profile


def extract_resume_profile(resume: Resume, *, engine: Any, deadline: float) -> ResumeProfile:
    metadata=dict(resume_id=resume.id, source_hash=source_hash(resume.content),
                  extractor_version=PROFILE_EXTRACTOR_VERSION, version_key=profile_version_key(engine))
    from .extraction import _validated_chunk
    chunks=chunk_text(resume.content)
    if resume.extraction_warnings or not chunks:
        return ResumeProfile(status="needs_review",warnings=["source_incomplete"],**metadata)
    try:
        unique={}
        for index, chunk in enumerate(chunks):
            remaining=deadline-time.monotonic()
            if remaining<=0: raise TimeoutError
            payload=dict(task="resume_profile",source_text=chunk.text,section_context=section_at(resume.content,chunk.start),
                         chunk_index=index,chunk_count=len(chunks),schema=ProfileChunk.model_json_schema())
            def validate(response):
                result=ProfileChunk.model_validate(response)
                if result.chunk_index!=index or not result.complete: raise ValueError("Incomplete source analysis")
                return [_fact(proposal,chunk,resume.content) for proposal in result.items]
            for f in _validated_chunk(payload,engine=engine,deadline=deadline,validate=validate):
                unique.setdefault(f.id,f)
        facts=sorted(unique.values(),key=lambda f:(f.source_start,f.source_end,f.id))
        employment=[f for f in facts if f.kind=="employment"]
        for f in facts:
            if f.kind=="employment": continue
            linked=[e for e in employment if e.source_start<=f.source_start<f.source_end<=e.source_end]
            if len(linked)==1: f.employment_id=linked[0].id
        profile=ResumeProfile.model_construct(status=EvaluationStatus.COMPLETE, facts=facts,
                    processed_source_chunks=[SourceSpan(start=c.start,end=c.end) for c in chunks],warnings=[],**metadata)
        profile.profile_fingerprint=_profile_fingerprint(profile)
        return validate_profile(ResumeProfile.model_validate(profile.model_dump()),resume)
    except TimeoutError:
        return ResumeProfile(status="needs_review",warnings=["deadline_exceeded"],**metadata)
    except Exception:
        return ResumeProfile(status="failed",warnings=["invalid_provider_response"],**metadata)


def get_or_build_resume_profile(resume: Resume, *, user_id: str, engine: Any, storage: Any, deadline: float) -> ResumeProfile:
    key=profile_version_key(engine)
    def stale():
        return ResumeProfile(resume_id=resume.id,source_hash=source_hash(resume.content),status="needs_review",
                             extractor_version=PROFILE_EXTRACTOR_VERSION,version_key=key,warnings=["source_incomplete"])
    current=storage.get_resume(resume.id,user_id=user_id)
    if not current or current.content!=resume.content or current.extraction_warnings: return stale()
    cached=storage.get_resume_profile(user_id=user_id,resume_id=resume.id,source_hash=source_hash(resume.content),version_key=key)
    if cached:
        try:
            accepted=validate_profile(ResumeProfile.model_validate_json(cached["payload_json"]),resume,key)
            current=storage.get_resume(resume.id,user_id=user_id)
            if not current or current.content!=resume.content or current.extraction_warnings: return stale()
            return accepted
        except (ValueError,TypeError,KeyError): storage.delete_resume_profiles(user_id=user_id,resume_id=resume.id)
    profile=extract_resume_profile(resume,engine=engine,deadline=deadline)
    if profile.status!="complete": return profile
    try:
        storage.save_resume_profile(user_id=user_id,resume_id=resume.id,source_hash=profile.source_hash,
                                    version_key=key,payload_json=profile.model_dump_json())
    except ValueError: return stale()
    winner=storage.get_resume_profile(user_id=user_id,resume_id=resume.id,source_hash=profile.source_hash,version_key=key)
    current=storage.get_resume(resume.id,user_id=user_id)
    if not current or current.content!=resume.content or current.extraction_warnings or not winner: return stale()
    return validate_profile(ResumeProfile.model_validate_json(winner["payload_json"]),resume,key)
