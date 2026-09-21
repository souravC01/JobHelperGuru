"""Contracts and services for evidence-based resume matching."""

from .models import (
    CategoryScore,
    EligibilityResult,
    EligibilityStatus,
    Evaluation,
    EvaluationBatch,
    EvaluationStatus,
    Evidence,
    EvidenceExtraction,
    EvidenceLevel,
    MatchContract,
    RawScore,
    RelevantInterval,
    Requirement,
    RequirementCategory,
    RequirementExtraction,
    RequirementResult,
    ScoreBreakdown,
)
from .scoring import (
    calculate_score,
    calculate_verified_months,
    rank_evaluations,
)


def __getattr__(name: str):
    if name == "evaluate_resumes":
        from .pipeline import evaluate_resumes

        return evaluate_resumes
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CategoryScore",
    "EligibilityResult",
    "EligibilityStatus",
    "Evaluation",
    "EvaluationBatch",
    "EvaluationStatus",
    "Evidence",
    "EvidenceExtraction",
    "EvidenceLevel",
    "MatchContract",
    "RawScore",
    "RelevantInterval",
    "Requirement",
    "RequirementCategory",
    "RequirementExtraction",
    "RequirementResult",
    "ScoreBreakdown",
    "calculate_score",
    "calculate_verified_months",
    "evaluate_resumes",
    "rank_evaluations",
]
