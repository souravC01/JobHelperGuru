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
    "rank_evaluations",
]
