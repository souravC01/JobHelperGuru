"""AI-only comparison orchestration with frozen rubrics and reusable evidence."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import logging
import math
import time
from typing import Any

from backend.models import Resume
from . import extraction, profiles, scoring
from .chunking import TextChunk, chunk_text
from .models import Evaluation, EvaluationBatch, EvidenceExtraction, RequirementExtraction
from .normalization import CANONICAL_SKILL_ALIASES
from .provenance import fingerprint, source_hash

logger = logging.getLogger(__name__)


class _LoggedEngine:
    def __init__(self, engine): self.engine = engine
    def __getattr__(self, name): return getattr(self.engine, name)
    def extract_match_chunk(self, payload, *, timeout):
        started = time.monotonic()
        reason = "received"
        try:
            return self.engine.extract_match_chunk(payload, timeout=timeout)
        except TimeoutError:
            reason = "deadline_exceeded"
            raise
        except Exception:
            reason = "invalid_provider_response"
            raise
        finally:
            logger.info("matching call task=%s duration=%.3f reason=%s", payload["task"], time.monotonic()-started, reason)


def rubric_version_key(engine):
    return fingerprint([engine.api_base_url, engine.model_name, "openai-chat-v1",
                        extraction.EXTRACTOR_VERSION, CANONICAL_SKILL_ALIASES])


def _validate_rubric(row, text):
    result = RequirementExtraction.model_validate_json(row["payload_json"])
    if (result.status != "complete" or result.warnings or len(result.items)>extraction.MAX_REQUIREMENTS or
        result.source_hash != source_hash(text) or result.extractor_version != extraction.EXTRACTOR_VERSION or
        row["rubric_fingerprint"] != fingerprint(result.model_dump(mode="json"))):
        raise ValueError("Invalid cached rubric")
    for r in result.items:
        if text[r.source_start:r.source_end] != r.source_quote: raise ValueError("Invalid job provenance")
        proposal = extraction.RequirementProposal(**r.model_dump(exclude={"id","source_start","source_end"}))
        recreated = extraction._materialize(proposal, TextChunk(r.source_start,r.source_end,r.source_quote), text, result.source_hash)
        if recreated != r: raise ValueError("Invalid cached requirement identity")
    if extraction._deduplicate(result.items) != result.items: raise ValueError("Duplicate cached requirements")
    return result


def _validate_cached(evaluation, resume, rubric, profile, *, as_of, rubric_fingerprint, evaluation_id):
    if (evaluation.status != "complete" or evaluation.resume_id != resume.id or evaluation.as_of != as_of or
        evaluation.job_fingerprint != rubric.source_hash or evaluation.source_fingerprint != source_hash(resume.content) or
        evaluation.resume_fingerprint != source_hash(resume.content) or evaluation.rubric_fingerprint != rubric_fingerprint or
        evaluation.profile_fingerprint != profile.profile_fingerprint or evaluation.assessment_version != extraction.ASSESSMENT_VERSION or
        evaluation.evaluation_id != evaluation_id):
        raise ValueError("Cached assessment identity mismatch")
    if [r.requirement for r in evaluation.requirement_results] != rubric.items:
        raise ValueError("Cached rubric coverage mismatch")
    evidence = []
    for result in evaluation.requirement_results:
        for item in result.evidence:
            contexts = []
            if item.source_quote is not None:
                if resume.content[item.source_start:item.source_end] != item.source_quote:
                    raise ValueError("Cached source quote mismatch")
                contexts = [TextChunk(item.source_start,item.source_end,item.source_quote)]
            proposal = extraction.EvidenceProposal(requirement_id=item.requirement_id,level=item.level.value,source_quote=item.source_quote)
            accepted = extraction._validate_evidence_proposal(proposal,result.requirement,resume,contexts,profile,as_of)
            if accepted != item: raise ValueError("Cached evidence does not match verified source")
            evidence.append(item)
    EvidenceExtraction(status="complete",source_hash=source_hash(resume.content),extractor_version=extraction.ASSESSMENT_VERSION,
                       items=evidence,assessed_requirement_ids=[r.id for r in rubric.items])
    return evidence


def _partition(resumes):
    # Each extraction round supplies at most one <=8k profile/source context per resume.
    # Long profiles use all original chunks through the existing evidence adapter.
    ordered = sorted(resumes,key=lambda r:r.id)
    return [ordered[i:i+5] for i in range(0,len(ordered),5)]


def evaluate_resumes(job_text: str, resumes: list[Resume], *, user_id: str, as_of: date,
                     engine: Any, storage: Any, fresh: bool=False, deadline_seconds: float=300.0) -> EvaluationBatch:
    """Reuse validated artifacts, then score and rank only the current selected set."""
    if not job_text.strip() or not resumes or not user_id: raise ValueError("Job, resumes and user are required")
    chunk_text(job_text)
    if len({r.id for r in resumes}) != len(resumes): raise ValueError("Duplicate resume IDs")
    if not math.isfinite(deadline_seconds) or deadline_seconds<0: raise ValueError("Invalid deadline")
    deadline = time.monotonic()+min(deadline_seconds,300.0)
    job_hash = source_hash(job_text)
    for resume in resumes:
        chunk_text(resume.content)
        current = storage.get_resume(resume.id,user_id=user_id)
        if not current or current.content != resume.content or current.extraction_warnings != resume.extraction_warnings:
            raise ValueError("Resume is not the current user-owned source")
    engine = _LoggedEngine(engine)
    rubric_key = rubric_version_key(engine)
    identity = dict(user_id=user_id,job_hash=job_hash,version_key=rubric_key)
    frozen = None
    rubric_fingerprint = None

    def incomplete(resume, reason, status="needs_review", profile=None):
        logger.info("matching outcome status=%s reason=%s",status,reason)
        return Evaluation(resume_id=resume.id,status=status,as_of=as_of,job_fingerprint=job_hash,
                          resume_fingerprint=source_hash(resume.content),source_fingerprint=source_hash(resume.content),
                          rubric_fingerprint=rubric_fingerprint,reason_codes=[reason],
                          profile_fingerprint=profile.profile_fingerprint if profile else None,
                          assessment_version=extraction.ASSESSMENT_VERSION,scorer_version=scoring.SCORER_VERSION)

    def batch(evaluations):
        ranked = scoring.rank_evaluations(evaluations)
        return EvaluationBatch(job_fingerprint=job_hash,comparison_complete=all(e.status=="complete" for e in ranked),evaluations=ranked)

    if time.monotonic() >= deadline: return batch([incomplete(r,"deadline_exceeded") for r in resumes])
    row = storage.get_matching_rubric(**identity)
    if row:
        try: frozen = _validate_rubric(row,job_text)
        except (ValueError,TypeError,KeyError):
            storage.delete_matching_rubric(**identity,payload_json=row["payload_json"])
    if frozen is None:
        proposed = extraction.extract_requirements(job_text,engine=engine,deadline=deadline)
        if proposed.status != "complete":
            return batch([incomplete(r,proposed.warnings[0],proposed.status.value) for r in resumes])
        storage.save_matching_rubric(id=fingerprint(["rubric",user_id,job_hash,rubric_key]),
                                    payload_json=proposed.model_dump_json(),**identity)
        row = storage.get_matching_rubric(**identity)
        # Conflict-safe insert freezes the first complete interpretation for every caller.
        frozen = _validate_rubric(row,job_text)
    rubric_fingerprint = row["rubric_fingerprint"]
    prepared, results, misses, keys, cached_payloads = {}, {}, [], {}, {}
    ordered = sorted(resumes,key=lambda r:r.id)
    def prepare(resume):
        if time.monotonic() >= deadline: return None
        return profiles.get_or_build_resume_profile(resume,user_id=user_id,engine=engine,storage=storage,deadline=deadline)
    if len(ordered)>1:
        with ThreadPoolExecutor(max_workers=2) as pool:
            prepared_profiles = list(pool.map(prepare,ordered))
    else: prepared_profiles = [prepare(r) for r in ordered]
    for resume, profile in zip(ordered,prepared_profiles):
        if profile is None or time.monotonic() >= deadline:
            results[resume.id] = incomplete(resume,"deadline_exceeded")
            continue
        if profile.status != "complete":
            results[resume.id] = incomplete(resume,profile.warnings[0],profile.status.value)
            continue
        prepared[resume.id] = profile
        key = fingerprint([rubric_key,rubric_fingerprint,profile.profile_fingerprint,extraction.ASSESSMENT_VERSION,
                           source_hash(resume.content),as_of.isoformat()])
        id = fingerprint([user_id,resume.id,job_hash,key,as_of.isoformat()])
        keys[resume.id] = (key,id)
        cached = None if fresh else storage.get_matching_snapshot(user_id=user_id,resume_id=resume.id,job_hash=job_hash,
                                                                 version_key=key,as_of=as_of.isoformat())
        if cached:
            try:
                evaluation = Evaluation.model_validate_json(cached["payload_json"])
                evidence = _validate_cached(evaluation,resume,frozen,profile,as_of=as_of,
                                            rubric_fingerprint=rubric_fingerprint,evaluation_id=id)
                if time.monotonic() >= deadline:
                    results[resume.id] = incomplete(resume,"deadline_exceeded")
                    continue
                cached_payloads[resume.id] = cached["payload_json"]
                breakdown = scoring.calculate_score(frozen.items,evidence,as_of=as_of)
                results[resume.id] = Evaluation.model_validate({**evaluation.model_dump(),**breakdown.model_dump(),
                                          "scorer_version":scoring.SCORER_VERSION,"rank":None,"is_top_match":False})
                continue
            except (ValueError,TypeError,KeyError):
                logger.info("matching cache reason=invalid_cached_assessment")
        misses.append(resume)
    partitions = _partition(misses)
    def assess(partition):
        return extraction.extract_evidence_batch(partition,prepared,frozen.items,as_of=as_of,engine=engine,deadline=deadline)
    if len(partitions)>1:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assessments = list(pool.map(assess,partitions))
    else: assessments = [assess(p) for p in partitions]
    outcomes = {id: outcome for part in assessments for id,outcome in part.items()}
    for resume in misses:
        outcome = outcomes[resume.id]
        if outcome.status != "complete":
            results[resume.id] = incomplete(resume,outcome.warnings[0],outcome.status.value,prepared[resume.id])
            continue
        if time.monotonic() >= deadline:
            results[resume.id] = incomplete(resume,"deadline_exceeded")
            continue
        breakdown = scoring.calculate_score(frozen.items,outcome.items,as_of=as_of)
        results[resume.id] = Evaluation(resume_id=resume.id,status="complete",as_of=as_of,job_fingerprint=job_hash,
                    resume_fingerprint=source_hash(resume.content),source_fingerprint=source_hash(resume.content),
                    rubric_fingerprint=rubric_fingerprint,profile_fingerprint=prepared[resume.id].profile_fingerprint,
                    assessment_version=extraction.ASSESSMENT_VERSION,scorer_version=scoring.SCORER_VERSION,
                    evaluation_id=keys[resume.id][1],**breakdown.model_dump())
    for resume in resumes:
        evaluation = results[resume.id]
        if time.monotonic() >= deadline:
            results[resume.id] = incomplete(resume,"deadline_exceeded")
            continue
        current = storage.get_resume(resume.id,user_id=user_id)
        if not current or current.content != resume.content or current.extraction_warnings:
            results[resume.id] = incomplete(resume,"source_incomplete")
            continue
        if evaluation.status != "complete": continue
        if time.monotonic() >= deadline:
            results[resume.id] = incomplete(resume,"deadline_exceeded")
            continue
        if cached_payloads.get(resume.id) == evaluation.model_dump_json(): continue
        key,id = keys[resume.id]
        try:
            storage.save_matching_snapshot(id=id,user_id=user_id,resume_id=resume.id,job_hash=job_hash,
                source_hash=source_hash(resume.content),version_key=key,as_of=as_of.isoformat(),payload_json=evaluation.model_dump_json())
        except ValueError:
            results[resume.id] = incomplete(resume,"source_incomplete")
    # Recheck the whole set after writes: another resume may have changed while we waited.
    current_rubric = storage.get_matching_rubric(**identity)
    try:
        _validate_rubric(current_rubric,job_text)
        rubric_current = current_rubric["rubric_fingerprint"] == rubric_fingerprint
    except (ValueError,TypeError,KeyError): rubric_current = False
    for resume in resumes:
        current = storage.get_resume(resume.id,user_id=user_id)
        if not rubric_current:
            results[resume.id] = incomplete(resume,"invalid_provider_response")
        elif not current or current.content != resume.content or current.extraction_warnings:
            results[resume.id] = incomplete(resume,"source_incomplete")
    if time.monotonic() >= deadline:
        return batch([incomplete(r,"deadline_exceeded") for r in resumes])
    return batch(list(results.values()))
