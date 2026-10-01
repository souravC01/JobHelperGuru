"""Strict public contracts for evidence-based resume matching v2."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    model_validator,
)

NonEmptyString = Annotated[StrictStr, Field(min_length=1)]
CategoryScore = Annotated[Decimal, Field(ge=0, le=100)]
RawScore = Annotated[Decimal, Field(ge=0, le=100)]


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


class EligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    UNKNOWN = "unknown"


class MatchContract(BaseModel):
    """Base behavior shared by persisted and exchanged matching records."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Requirement(MatchContract):
    id: NonEmptyString
    category: RequirementCategory
    kind: Literal["skill", "semantic", "tenure", "credential", "experience"]
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
            raise ValueError(
                "credited or contradicted evidence requires resume provenance"
            )
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


def has_evidence_conflict(levels: set[EvidenceLevel]) -> bool:
    """Positive claims and explicit contradiction need review, never a guessed score."""
    return EvidenceLevel.CONTRADICTED in levels and bool(levels & {EvidenceLevel.DEMONSTRATED, EvidenceLevel.LISTED})


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


class ExtractionResult(MatchContract):
    status: EvaluationStatus
    warnings: list[NonEmptyString] = Field(default_factory=list)
    source_hash: NonEmptyString
    extractor_version: NonEmptyString
    assessed_requirement_ids: list[NonEmptyString] = Field(default_factory=list)
    unresolved_requirement_ids: list[NonEmptyString] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_coverage(self) -> ExtractionResult:
        assessed = set(self.assessed_requirement_ids)
        unresolved = set(self.unresolved_requirement_ids)
        if (
            len(assessed) != len(self.assessed_requirement_ids)
            or len(unresolved) != len(self.unresolved_requirement_ids)
            or assessed & unresolved
        ):
            raise ValueError("coverage IDs must be unique and disjoint")
        if self.status is EvaluationStatus.COMPLETE and unresolved:
            raise ValueError(
                "complete extraction cannot contain unresolved requirements"
            )
        if self.status is EvaluationStatus.FAILED and (assessed or self.items):
            raise ValueError("failed extraction cannot publish partial outcomes")
        return self


class RequirementExtraction(ExtractionResult):
    items: list[Requirement] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_requirements(self) -> RequirementExtraction:
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate requirement IDs")
        if set(ids) != set(
            self.assessed_requirement_ids + self.unresolved_requirement_ids
        ):
            raise ValueError("coverage must describe every extracted requirement")
        if self.status is EvaluationStatus.COMPLETE and not ids:
            raise ValueError("complete requirements extraction needs requirements")
        return self


class EvidenceExtraction(ExtractionResult):
    items: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_evidence(self) -> EvidenceExtraction:
        if {item.requirement_id for item in self.items} != set(
            self.assessed_requirement_ids
        ):
            raise ValueError("assessed IDs must have explicit evidence outcomes")
        for id in self.assessed_requirement_ids:
            if has_evidence_conflict({item.level for item in self.items if item.requirement_id == id}):
                raise ValueError("Conflicting evidence remains unresolved")
        seen = {}
        for item in self.items:
            key = (item.requirement_id, item.source_start, item.source_end)
            if key in seen:
                raise ValueError("duplicate evidence provenance")
            seen[key] = item
        return self


class EligibilityResult(MatchContract):
    criterion: NonEmptyString
    status: EligibilityStatus
    reason: NonEmptyString | None = None


class Evaluation(MatchContract):
    resume_id: NonEmptyString
    status: EvaluationStatus
    as_of: date
    job_fingerprint: NonEmptyString
    resume_fingerprint: NonEmptyString
    source_fingerprint: NonEmptyString
    match_score: StrictInt | None = Field(default=None, ge=0, le=100)
    score_scope: Literal["skill_fit"] = "skill_fit"
    rubric_fingerprint: NonEmptyString | None = None
    skill_coverage_score: CategoryScore | None = None
    reason_codes: list[Literal["source_incomplete", "rubric_limit", "invalid_provider_response", "missing_assessment", "unresolved_evidence", "deadline_exceeded", "no_assessable_requirements"]] = Field(default_factory=list)
    raw_score: RawScore | None = None
    category_scores: dict[RequirementCategory, CategoryScore] = Field(
        default_factory=dict
    )
    requirement_results: list[RequirementResult] = Field(default_factory=list)
    eligibility: list[EligibilityResult] = Field(default_factory=list)
    warnings: list[NonEmptyString] = Field(default_factory=list)
    rank: StrictInt | None = Field(default=None, ge=1)
    is_top_match: bool = False
    evaluation_id: NonEmptyString | None = None
    scorer_version: NonEmptyString = "v2"
    profile_fingerprint: NonEmptyString | None = None
    assessment_version: NonEmptyString | None = None

    @model_validator(mode="after")
    def validate_score_state_and_requirement_coverage(self) -> Evaluation:
        incomplete = self.status in {
            EvaluationStatus.NEEDS_REVIEW,
            EvaluationStatus.FAILED,
        }
        if incomplete and (
            self.match_score is not None or self.raw_score is not None or self.category_scores
            or self.skill_coverage_score is not None or self.rank is not None or self.is_top_match
        ):
            raise ValueError(
                "incomplete evaluations cannot have a score, rank, or top-match flag"
            )
        if self.status is EvaluationStatus.COMPLETE:
            if self.match_score is None or self.raw_score is None or not self.rubric_fingerprint:
                raise ValueError("complete evaluations require scores and rubric identity")
            if self.reason_codes:
                raise ValueError("complete evaluations cannot contain unresolved reasons")

        if self.raw_score is not None:
            expected_display_score = int(
                self.raw_score.quantize(Decimal(1), rounding=ROUND_HALF_UP)
            )
            if self.match_score != expected_display_score:
                raise ValueError(
                    "match_score must be the half-up display value of raw_score"
                )

        if self.is_top_match and (self.rank != 1 or (self.raw_score or 0) <= 0):
            raise ValueError("top matches must have rank 1 and a positive score")
        if self.rank is not None:
            expected_top = self.rank == 1 and (self.raw_score or 0) > 0
            if self.is_top_match != expected_top:
                raise ValueError("rank and top-match flag must agree")

        if self.match_score is not None:
            if not self.requirement_results:
                raise ValueError(
                    "scored evaluations require source-backed requirements"
                )
            requirement_ids = [
                result.requirement.id for result in self.requirement_results
            ]
            if len(requirement_ids) != len(set(requirement_ids)):
                raise ValueError(
                    "scored evaluations cannot contain duplicate requirement IDs"
                )
            if any(not result.evidence for result in self.requirement_results):
                raise ValueError(
                    "scored requirements require an explicit evidence outcome"
                )
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
        if any(e.job_fingerprint != self.job_fingerprint for e in self.evaluations):
            raise ValueError("batch evaluations must share the job fingerprint")
        rubrics = {e.rubric_fingerprint for e in self.evaluations if e.rubric_fingerprint}
        if len(rubrics) > 1:
            raise ValueError("batch evaluations must share one frozen rubric")
        if self.comparison_complete:
            if not self.evaluations or any(e.status != EvaluationStatus.COMPLETE for e in self.evaluations):
                raise ValueError("complete comparisons require all evaluations complete")
            requirement_sets = {frozenset(r.requirement.id for r in e.requirement_results) for e in self.evaluations}
            if len(requirement_sets) != 1:
                raise ValueError("complete comparisons require identical requirement coverage")
        elif any(e.rank is not None or e.is_top_match for e in self.evaluations):
            raise ValueError("incomplete comparisons cannot publish ranks or winners")
        return self


class ScoreBreakdown(MatchContract):
    skill_coverage_score: CategoryScore | None = None
    match_score: StrictInt = Field(ge=0, le=100)
    raw_score: RawScore
    category_scores: dict[RequirementCategory, CategoryScore] = Field(
        default_factory=dict
    )
    requirement_results: list[RequirementResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_display_score(self) -> ScoreBreakdown:
        if self.match_score != int(self.raw_score.quantize(Decimal(1), rounding=ROUND_HALF_UP)):
            raise ValueError("match_score must be the half-up display value of raw_score")
        return self


class SourceSpan(MatchContract):
    start: StrictInt = Field(ge=0)
    end: StrictInt = Field(gt=0)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("Invalid source chunk")
        return self


class ProfileFact(MatchContract):
    id: NonEmptyString
    kind: Literal["skill", "activity", "credential", "employment"]
    canonical_key: NonEmptyString
    level: EvidenceLevel
    source_quote: NonEmptyString
    source_start: StrictInt = Field(ge=0)
    source_end: StrictInt = Field(gt=0)
    section: NonEmptyString
    employment_id: NonEmptyString | None = None
    start: date | None = None
    end: date | None = None

    @model_validator(mode="after")
    def provenance(self):
        Evidence(requirement_id=self.id, level=self.level, source_quote=self.source_quote,
                 source_start=self.source_start, source_end=self.source_end)
        if self.kind != "employment" and (self.start is not None or self.end is not None):
            raise ValueError("Only employment has dates")
        if self.kind == "employment" and self.start is None:
            raise ValueError("Employment needs a verified start date")
        if self.start and self.end and self.end < self.start:
            raise ValueError("Invalid employment dates")
        return self


class ResumeProfile(MatchContract):
    resume_id: NonEmptyString
    source_hash: NonEmptyString
    status: EvaluationStatus
    extractor_version: NonEmptyString
    version_key: NonEmptyString
    profile_fingerprint: NonEmptyString | None = None
    facts: list[ProfileFact] = Field(default_factory=list)
    processed_source_chunks: list[SourceSpan] = Field(default_factory=list)
    warnings: list[NonEmptyString] = Field(default_factory=list)

    @model_validator(mode="after")
    def completeness(self):
        ids = [f.id for f in self.facts]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate profile facts")
        provenance = [(f.kind, f.canonical_key, f.source_start, f.source_end) for f in self.facts]
        if len(provenance) != len(set(provenance)):
            raise ValueError("Duplicate or conflicting profile provenance")
        employment = {f.id for f in self.facts if f.kind == "employment"}
        if any(f.employment_id and f.employment_id not in employment for f in self.facts):
            raise ValueError("Unknown employment fact")
        if self.status == EvaluationStatus.COMPLETE:
            if not self.profile_fingerprint or not self.processed_source_chunks or self.warnings:
                raise ValueError("Complete profile needs coverage and identity, no unresolved warnings")
        elif self.profile_fingerprint:
            raise ValueError("Incomplete profile cannot publish a fingerprint")
        return self
