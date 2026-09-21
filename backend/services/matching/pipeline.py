"""Orchestration pipeline for evidence-based matching, concurrency control, and versioned snapshots."""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any

from backend.models import Resume

from .chunking import MAX_DOCUMENT_CHARS
from .extraction import (
    EXTRACTOR_VERSION,
    extract_eligibility,
    extract_evidence,
    extract_requirements,
)
from .models import (
    Evaluation,
    EvaluationBatch,
    EvaluationStatus,
    Requirement,
)
from .scoring import calculate_score, rank_evaluations

logger = logging.getLogger(__name__)

SCORER_VERSION = "v2"
ALIAS_VERSION = "v1"
PROMPT_VERSION = "v1"
DEFAULT_EVALUATION_DEADLINE_SECONDS = 300.0
MAX_SIMULTANEOUS_PROVIDER_CALLS = 2


def _compute_version_key(mode: str, engine: Any) -> str:
    model_name = getattr(engine, "model_name", "offline") if mode == "ai" else "offline"
    payload = f"{mode}:{model_name}:{EXTRACTOR_VERSION}:{ALIAS_VERSION}:{SCORER_VERSION}:{PROMPT_VERSION}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _evaluate_single_resume(
    resume: Resume,
    job_text: str,
    job_fingerprint: str,
    requirements: list[Requirement],
    *,
    user_id: str,
    as_of: date,
    mode: str,
    engine: Any,
    storage: Any,
    fresh: bool,
    version_key: str,
    deadline: float,
) -> Evaluation:
    resume_fingerprint = hashlib.sha256(resume.content.encode("utf-8")).hexdigest()
    source_fingerprint = hashlib.sha256(
        f"{job_fingerprint}:{resume_fingerprint}".encode()
    ).hexdigest()

    # Check cache if not fresh
    if not fresh and storage is not None:
        cached = storage.get_matching_snapshot(
            user_id=user_id,
            resume_id=resume.id,
            job_hash=job_fingerprint,
            version_key=version_key,
            as_of=as_of.isoformat(),
        )
        if cached and cached.get("source_hash") == resume_fingerprint:
            try:
                cached_data = json.loads(cached["payload_json"])
                return Evaluation.model_validate(cached_data)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to deserialize cached matching snapshot: %s", type(exc).__name__)

    # Deadline check before starting extraction
    if time.monotonic() > deadline:
        return Evaluation(
            resume_id=resume.id,
            status=EvaluationStatus.FAILED,
            as_of=as_of,
            job_fingerprint=job_fingerprint,
            resume_fingerprint=resume_fingerprint,
            source_fingerprint=source_fingerprint,
            warnings=["Evaluation deadline exceeded"],
        )

    # Document length guard
    if len(resume.content) > MAX_DOCUMENT_CHARS:
        return Evaluation(
            resume_id=resume.id,
            status=EvaluationStatus.FAILED,
            as_of=as_of,
            job_fingerprint=job_fingerprint,
            resume_fingerprint=resume_fingerprint,
            source_fingerprint=source_fingerprint,
            warnings=[f"Resume exceeds maximum character limit of {MAX_DOCUMENT_CHARS:,} characters."],
        )

    # Extract evidence & eligibility
    extraction_exc: Exception | None = None
    try:
        evidence_extraction = extract_evidence(
            resume.content,
            requirements,
            as_of=as_of,
            mode=mode,
            engine=engine,
        )
    except Exception as exc:  # noqa: BLE001
        evidence_extraction = None
        extraction_exc = exc

    eligibility = extract_eligibility(job_text, resume.content, as_of=as_of)

    if evidence_extraction is None or evidence_extraction.status != EvaluationStatus.COMPLETE:
        status = (
            EvaluationStatus.FAILED
            if evidence_extraction and evidence_extraction.status == EvaluationStatus.FAILED
            else EvaluationStatus.NEEDS_REVIEW
        )
        warnings = (
            evidence_extraction.warnings
            if evidence_extraction
            else [f"Evidence extraction failed: {type(extraction_exc).__name__}: {extraction_exc}"]
        )
        return Evaluation(
            resume_id=resume.id,
            status=status,
            as_of=as_of,
            job_fingerprint=job_fingerprint,
            resume_fingerprint=resume_fingerprint,
            source_fingerprint=source_fingerprint,
            eligibility=eligibility,
            warnings=warnings,
        )

    # Calculate deterministic score
    breakdown = calculate_score(requirements, evidence_extraction.items, as_of=as_of)
    evaluation_id = "eval_" + uuid.uuid4().hex[:16]

    evaluation = Evaluation(
        resume_id=resume.id,
        status=EvaluationStatus.COMPLETE,
        as_of=as_of,
        job_fingerprint=job_fingerprint,
        resume_fingerprint=resume_fingerprint,
        source_fingerprint=source_fingerprint,
        match_score=breakdown.match_score,
        raw_score=breakdown.raw_score,
        category_scores=breakdown.category_scores,
        requirement_results=breakdown.requirement_results,
        eligibility=eligibility,
        warnings=evidence_extraction.warnings,
        evaluation_id=evaluation_id,
        scorer_version=SCORER_VERSION,
    )

    # Persist snapshot if storage is configured
    if storage is not None:
        try:
            storage.save_matching_snapshot(
                id=evaluation_id,
                user_id=user_id,
                resume_id=resume.id,
                job_hash=job_fingerprint,
                source_hash=resume_fingerprint,
                version_key=version_key,
                as_of=as_of.isoformat(),
                payload_json=evaluation.model_dump_json(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to save matching snapshot: %s", type(exc).__name__)

    return evaluation


def evaluate_resumes(
    job_text: str,
    resumes: list[Resume],
    *,
    user_id: str,
    as_of: date,
    mode: str = "offline",
    engine: Any = None,
    storage: Any = None,
    fresh: bool = False,
    max_workers: int = MAX_SIMULTANEOUS_PROVIDER_CALLS,
    deadline_seconds: float = DEFAULT_EVALUATION_DEADLINE_SECONDS,
) -> EvaluationBatch:
    """Orchestrate multi-resume evaluation with frozen requirements, concurrency bounds, and caching."""
    clean_job = job_text.strip()
    job_fingerprint = hashlib.sha256(job_text.encode("utf-8")).hexdigest()
    deadline = time.monotonic() + deadline_seconds
    version_key = _compute_version_key(mode, engine)

    # Check for empty / oversized job input
    if not clean_job or len(job_text) > MAX_DOCUMENT_CHARS:
        warning_msg = (
            "Job text is empty."
            if not clean_job
            else f"Job text exceeds maximum character limit of {MAX_DOCUMENT_CHARS:,}."
        )
        unscorable_evals = [
            Evaluation(
                resume_id=r.id,
                status=EvaluationStatus.NEEDS_REVIEW,
                as_of=as_of,
                job_fingerprint=job_fingerprint,
                resume_fingerprint=hashlib.sha256(r.content.encode("utf-8")).hexdigest(),
                source_fingerprint=hashlib.sha256(
                    f"{job_fingerprint}:{hashlib.sha256(r.content.encode('utf-8')).hexdigest()}".encode()
                ).hexdigest(),
                warnings=[warning_msg],
            )
            for r in resumes
        ]
        return EvaluationBatch(
            job_fingerprint=job_fingerprint,
            comparison_complete=False,
            evaluations=unscorable_evals,
        )

    # Extract requirements once for the whole batch
    req_extraction = extract_requirements(job_text, mode=mode, engine=engine)

    if req_extraction.status != EvaluationStatus.COMPLETE or not req_extraction.items:
        reasons = req_extraction.warnings or ["No evaluable requirements could be extracted from the job."]
        unscorable_evals = [
            Evaluation(
                resume_id=r.id,
                status=EvaluationStatus.NEEDS_REVIEW,
                as_of=as_of,
                job_fingerprint=job_fingerprint,
                resume_fingerprint=hashlib.sha256(r.content.encode("utf-8")).hexdigest(),
                source_fingerprint=hashlib.sha256(
                    f"{job_fingerprint}:{hashlib.sha256(r.content.encode('utf-8')).hexdigest()}".encode()
                ).hexdigest(),
                warnings=reasons,
            )
            for r in resumes
        ]
        return EvaluationBatch(
            job_fingerprint=job_fingerprint,
            comparison_complete=False,
            evaluations=unscorable_evals,
        )

    requirements = req_extraction.items
    workers = min(max_workers, len(resumes) or 1)

    evaluations: list[Evaluation] = []
    if workers <= 1 or len(resumes) <= 1:
        for r in resumes:
            evaluations.append(
                _evaluate_single_resume(
                    r,
                    job_text,
                    job_fingerprint,
                    requirements,
                    user_id=user_id,
                    as_of=as_of,
                    mode=mode,
                    engine=engine,
                    storage=storage,
                    fresh=fresh,
                    version_key=version_key,
                    deadline=deadline,
                )
            )
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_resume = {
                executor.submit(
                    _evaluate_single_resume,
                    r,
                    job_text,
                    job_fingerprint,
                    requirements,
                    user_id=user_id,
                    as_of=as_of,
                    mode=mode,
                    engine=engine,
                    storage=storage,
                    fresh=fresh,
                    version_key=version_key,
                    deadline=deadline,
                ): r
                for r in resumes
            }
            for future in as_completed(future_to_resume):
                evaluations.append(future.result())

    # Rank complete evaluations and preserve unranked incomplete evaluations
    ranked_evaluations = rank_evaluations(evaluations)
    comparison_complete = (
        len(ranked_evaluations) > 0
        and all(e.status == EvaluationStatus.COMPLETE for e in ranked_evaluations)
    )

    return EvaluationBatch(
        job_fingerprint=job_fingerprint,
        comparison_complete=comparison_complete,
        evaluations=ranked_evaluations,
    )
