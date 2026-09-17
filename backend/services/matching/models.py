"""Strict public contracts for evidence-based resume matching v2."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    model_validator,
)

NonEmptyString = Annotated[StrictStr, Field(min_length=1)]


class RequirementCategory(str, Enum):
    REQUIRED_SKILLS = "required_skills"
    RESPONSIBILITIES = "responsibilities"
    RELEVANT_EXPERIENCE = "relevant_experience"
    PREFERRED_QUALIFICATIONS = "preferred_qualifications"


class EvidenceLevel(str, Enum):
    DEMONSTRATED = "demonstrated"
    LISTED = "listed"
    LEARNING = "learning"
    NOT_EVIDENCED = "not_evidenced"
    CONTRADICTED = "contradicted"


class EvaluationStatus(str, Enum):
    COMPLETE = "complete"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class MatchContract(BaseModel):
    """Base behavior shared by persisted and exchanged matching records."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Requirement(MatchContract):
    id: NonEmptyString
    category: RequirementCategory
    kind: NonEmptyString
    canonical_key: NonEmptyString
    alternatives: list[NonEmptyString] = Field(default_factory=list)
    source_quote: NonEmptyString
    source_start: StrictInt = Field(ge=0)
    source_end: StrictInt = Field(gt=0)
    required_months: StrictInt | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_source_span(self) -> Requirement:
        if self.source_end <= self.source_start:
            raise ValueError("source_end must be greater than source_start")
        if self.source_end - self.source_start != len(self.source_quote):
            raise ValueError("source offsets must span source_quote exactly")
        return self


class RelevantInterval(MatchContract):
    start: date
    end: date | None = None

    @model_validator(mode="after")
    def validate_date_order(self) -> RelevantInterval:
        if self.end is not None and self.end < self.start:
            raise ValueError("interval end cannot precede interval start")
        return self


class Evidence(MatchContract):
    requirement_id: NonEmptyString
    level: EvidenceLevel
    source_quote: NonEmptyString | None = None
    source_start: StrictInt | None = Field(default=None, ge=0)
    source_end: StrictInt | None = Field(default=None, gt=0)
    section: NonEmptyString | None = None
    relevant_intervals: list[RelevantInterval] = Field(default_factory=list)
    warnings: list[NonEmptyString] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_resume_provenance(self) -> Evidence:
        span_values = (self.source_quote, self.source_start, self.source_end)
        has_any_span_value = any(value is not None for value in span_values)
        has_complete_span = all(value is not None for value in span_values)
        requires_provenance = self.level is not EvidenceLevel.NOT_EVIDENCED

        if requires_provenance and not has_complete_span:
            raise ValueError("credited or contradicted evidence requires resume provenance")
        if has_any_span_value and not has_complete_span:
            raise ValueError("resume provenance must include quote and both offsets")
        if has_complete_span:
            assert self.source_quote is not None
            assert self.source_start is not None
            assert self.source_end is not None
            if self.source_end <= self.source_start:
                raise ValueError("source_end must be greater than source_start")
            if self.source_end - self.source_start != len(self.source_quote):
                raise ValueError("source offsets must span source_quote exactly")
        return self


class RequirementResult(MatchContract):
    requirement: Requirement
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_evidence_requirement_ids(self) -> RequirementResult:
        mismatched_ids = [
            item.requirement_id
            for item in self.evidence
            if item.requirement_id != self.requirement.id
        ]
        if mismatched_ids:
            raise ValueError("evidence requirement_id must match its requirement")
        return self


class Evaluation(MatchContract):
    resume_id: NonEmptyString
    status: EvaluationStatus
    match_score: StrictInt | None = Field(default=None, ge=0, le=100)
    category_scores: dict[RequirementCategory, Decimal] = Field(default_factory=dict)
    requirement_results: list[RequirementResult] = Field(default_factory=list)
    eligibility: dict[NonEmptyString, NonEmptyString] = Field(default_factory=dict)
    warnings: list[NonEmptyString] = Field(default_factory=list)
    rank: StrictInt | None = Field(default=None, ge=1)
    is_top_match: bool = False
    evaluation_id: NonEmptyString | None = None
    scorer_version: NonEmptyString = "v2"

    @model_validator(mode="after")
    def validate_score_state_and_requirement_coverage(self) -> Evaluation:
        incomplete = self.status in {
            EvaluationStatus.NEEDS_REVIEW,
            EvaluationStatus.FAILED,
        }
        if incomplete and (self.match_score is not None or self.rank is not None):
            raise ValueError("incomplete evaluations cannot have a score or rank")
        if self.status is EvaluationStatus.COMPLETE and self.match_score is None:
            raise ValueError("complete evaluations require a match_score")

        if self.match_score is not None:
            if not self.requirement_results:
                raise ValueError("scored evaluations require source-backed requirements")
            requirement_ids = [result.requirement.id for result in self.requirement_results]
            if len(requirement_ids) != len(set(requirement_ids)):
                raise ValueError("scored evaluations cannot contain duplicate requirement IDs")
        return self


class EvaluationBatch(MatchContract):
    job_fingerprint: NonEmptyString
    comparison_complete: bool
    evaluations: list[Evaluation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_resume_evaluations(self) -> EvaluationBatch:
        resume_ids = [evaluation.resume_id for evaluation in self.evaluations]
        if len(resume_ids) != len(set(resume_ids)):
            raise ValueError("evaluation batches cannot contain duplicate resume IDs")
        return self
