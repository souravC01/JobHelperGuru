"""Reusable, source-verified resume analysis without job or scorer dependence."""
import time
from typing import Any, Literal

from pydantic import Field, StrictBool, StrictInt
from backend.models import Resume
from backend.services.skill_matching import supports_extracted_skill
from .chunking import TextChunk, chunk_text
from .models import MatchContract, NonEmptyString, EvaluationStatus, EvidenceLevel, ProfileFact, ResumeProfile, SourceSpan
from .normalization import CANONICAL_SKILL_ALIASES, canonicalize_skill
from .provenance import SourceReference, proposal_span, date_ranges, fingerprint, section_at, source_hash, verified_level, work_span

PROFILE_EXTRACTOR_VERSION = "resume-profile-v5"


class UnsupportedSkill(ValueError):
    """A well-formed proposed skill has no verified source support."""


class FactProposal(SourceReference):
    kind: Literal["skill", "activity", "credential", "employment"]
    canonical_key: NonEmptyString
    level: EvidenceLevel


class ProfileChunk(MatchContract):
    chunk_index: StrictInt = Field(ge=0)
    complete: StrictBool
    items: list[FactProposal]


class SkillReviewDecision(MatchContract):
    skill: NonEmptyString
    source_quote: NonEmptyString | None


class ProfileReviewRequest(MatchContract):
    review_token: NonEmptyString
    decisions: list[SkillReviewDecision] = Field(min_length=1, max_length=512)


def resolve_profile_review(profile, resume, decisions):
    validate_profile(profile, resume, allow_review=True)
    if profile.status != "needs_review" or not profile.unresolved_skills:
        raise ValueError("No unresolved skills")
    keys = [d.skill for d in decisions]
    if len(keys) != len(set(keys)) or set(keys) != set(profile.unresolved_skills):
        raise ValueError("Review every unresolved skill exactly once")
    facts = {f.id: f for f in profile.facts}
    for decision in decisions:
        if decision.source_quote is not None:
            chunk = TextChunk(0,len(resume.content),resume.content)
            _, start, end = proposal_span(SourceReference(source_quote=decision.source_quote),chunk)
            # Resolve the entire original lines, including wrapped negation/learning context.
            fact = _fact(FactProposal(kind="skill",canonical_key=decision.skill,level="listed",
                source_line=len((resume.content[:start]+'x').splitlines()),
                source_end_line=len(resume.content[:end].splitlines())),chunk,resume.content)
            if not any((f.kind,f.canonical_key,f.source_start,f.source_end) ==
                       (fact.kind,fact.canonical_key,fact.source_start,fact.source_end) for f in facts.values()):
                facts[fact.id] = fact
    result = profile.model_copy(update={"status": EvaluationStatus.COMPLETE, "unresolved_skills": [],
        "warnings": [], "facts": sorted(facts.values(),key=lambda f:(f.source_start,f.source_end,f.id))})
    result.profile_fingerprint = _profile_fingerprint(result)
    return validate_profile(ResumeProfile.model_validate(result.model_dump()), resume)


def profile_version_key(engine):
    return fingerprint([PROFILE_EXTRACTOR_VERSION, engine.api_base_url, engine.model_name,
                        "openai-chat-v1", CANONICAL_SKILL_ALIASES])


def _fact(proposal, chunk, text):
    key = canonicalize_skill(proposal.canonical_key)
    quote, start, end = proposal_span(proposal, chunk, skill=key if proposal.kind == "skill" else None)
    if not key:
        raise ValueError("Empty skill identity")
    if proposal.kind == "skill" and not supports_extracted_skill(quote, key):
        raise UnsupportedSkill("Unsupported skill fact")
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
    # Preserve identities of existing complete profiles predating the review field.
    return fingerprint(profile.model_dump(mode="json", exclude={"profile_fingerprint", "unresolved_skills"}))


def validate_profile(profile, resume, version_key=None, *, allow_review=False):
    review = (allow_review and profile.status == "needs_review" and profile.unresolved_skills
              and profile.warnings == ["unresolved_skill_claims"] and not profile.profile_fingerprint)
    if (profile.status != "complete" and not review) or profile.resume_id != resume.id or profile.source_hash != source_hash(resume.content) or resume.extraction_warnings:
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
    if not review and profile.profile_fingerprint != _profile_fingerprint(profile):
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
        unresolved=set()
        for index, chunk in enumerate(chunks):
            remaining=deadline-time.monotonic()
            if remaining<=0: raise TimeoutError
            payload=dict(task="resume_profile",source_text=chunk.text,section_context=section_at(resume.content,chunk.start),
                         chunk_index=index,chunk_count=len(chunks),schema=ProfileChunk.model_json_schema())
            def validate(response):
                result=ProfileChunk.model_validate(response)
                if result.chunk_index!=index or not result.complete: raise ValueError("Incomplete source analysis")
                facts=[]
                for proposal in result.items:
                    if proposal.kind != "skill": continue
                    try: facts.append(_fact(proposal,chunk,resume.content))
                    except UnsupportedSkill: unresolved.add(canonicalize_skill(proposal.canonical_key))
                return facts
            for f in _validated_chunk(payload,engine=engine,deadline=deadline,validate=validate):
                unique.setdefault(f.id,f)
        facts=sorted(unique.values(),key=lambda f:(f.source_start,f.source_end,f.id))
        if unresolved:
            return ResumeProfile(status="needs_review", facts=facts, unresolved_skills=sorted(unresolved),
                processed_source_chunks=[SourceSpan(start=c.start,end=c.end) for c in chunks],
                warnings=["unresolved_skill_claims"], **metadata)
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
            accepted=validate_profile(ResumeProfile.model_validate_json(cached["payload_json"]),resume,key,allow_review=True)
            current=storage.get_resume(resume.id,user_id=user_id)
            if not current or current.content!=resume.content or current.extraction_warnings: return stale()
            return accepted
        except (ValueError,TypeError,KeyError): storage.delete_resume_profiles(user_id=user_id,resume_id=resume.id)
    profile=extract_resume_profile(resume,engine=engine,deadline=deadline)
    if profile.status!="complete" and not (profile.status=="needs_review" and profile.unresolved_skills): return profile
    validate_profile(profile,resume,key,allow_review=True)
    try:
        storage.save_resume_profile(user_id=user_id,resume_id=resume.id,source_hash=profile.source_hash,
                                    version_key=key,payload_json=profile.model_dump_json())
    except ValueError: return stale()
    winner=storage.get_resume_profile(user_id=user_id,resume_id=resume.id,source_hash=profile.source_hash,version_key=key)
    current=storage.get_resume(resume.id,user_id=user_id)
    if not current or current.content!=resume.content or current.extraction_warnings or not winner: return stale()
    return validate_profile(ResumeProfile.model_validate_json(winner["payload_json"]),resume,key,allow_review=True)
