"""Local matching of cached skills and comparable skill-fit arithmetic."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from .models import (
    Evaluation, EvaluationBatch, Evidence, EvidenceLevel, ResumeProfile, Requirement,
    RequirementCategory, RequirementResult, ScoreBreakdown, has_evidence_conflict,
)

MATCHER_VERSION = "cached-skills-v1"
SCORER_VERSION = "skill-fit-v1"
CATEGORY_WEIGHTS = {
    RequirementCategory.REQUIRED_SKILLS: Decimal(60),
    RequirementCategory.PREFERRED_QUALIFICATIONS: Decimal(5),
}


def match_cached_skills(requirements: list[Requirement], profile: ResumeProfile) -> list[Evidence]:
    """Match complete, source-validated profile facts; no job-specific AI judgment."""
    from .normalization import canonicalize_skill
    if profile.status != "complete" or not profile.profile_fingerprint:
        raise ValueError("Complete cached profile required")
    facts = {}
    for fact in profile.facts:
        if fact.kind == "skill":
            facts.setdefault(canonicalize_skill(fact.canonical_key), []).append(fact)
    evidence = []
    for requirement in requirements:
        if requirement.kind != "skill" or requirement.category not in CATEGORY_WEIGHTS or requirement.required_months is not None:
            raise ValueError("Only required or preferred skills can be matched")
        positives, conflict = [], False
        for key in requirement.alternatives or [requirement.canonical_key]:
            candidates = facts.get(canonicalize_skill(key), [])
            if has_evidence_conflict({f.level for f in candidates}):
                conflict = True
                continue
            positives.extend(f for f in candidates if f.level in {EvidenceLevel.DEMONSTRATED, EvidenceLevel.LISTED})
        if positives:
            fact = min(positives, key=lambda f: (f.level != EvidenceLevel.DEMONSTRATED, f.source_start, f.source_end, f.id))
            evidence.append(Evidence(requirement_id=requirement.id, level=fact.level, source_quote=fact.source_quote,
                                     source_start=fact.source_start, source_end=fact.source_end, section=fact.section))
        elif conflict:
            raise ValueError("Conflicting cached skill facts")
        else:
            evidence.append(Evidence(requirement_id=requirement.id, level="not_evidenced"))
    return evidence


def calculate_score(requirements: list[Requirement], evidence: list[Evidence], *, as_of: date) -> ScoreBreakdown:
    """Score skill presence against a shared required/preferred denominator."""
    ids = [r.id for r in requirements]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Scoring requires unique nonempty requirements")
    grouped = {id: [] for id in ids}
    for item in evidence:
        if item.requirement_id not in grouped:
            raise ValueError("Unknown evidence requirement")
        grouped[item.requirement_id].append(item)
    credits = {}
    results = []
    for requirement in requirements:
        items = grouped[requirement.id]
        if not items:
            raise ValueError("Missing assessment cannot be scored as absence")
        levels = {item.level for item in items}
        if has_evidence_conflict(levels):
            raise ValueError("Conflicting evidence is unresolved")
        if requirement.kind != "skill" or requirement.category not in CATEGORY_WEIGHTS or requirement.required_months is not None:
            raise ValueError("Only required or preferred skills can be scored")
        credit = Decimal(1) if levels & {EvidenceLevel.DEMONSTRATED, EvidenceLevel.LISTED} else Decimal(0)
        credits[requirement.id] = credit
        # Exact repeated observations cannot change credit or persisted evidence volume.
        distinct = []
        for item in items:
            if item not in distinct: distinct.append(item)
        results.append(RequirementResult(requirement=requirement, evidence=distinct))
    categories = {}
    weighted = Decimal(0)
    denominator = Decimal(0)
    for category, weight in CATEGORY_WEIGHTS.items():
        values = [credits[r.id] for r in requirements if r.category == category]
        if not values: continue
        percent = sum(values, Decimal(0)) * 100 / Decimal(len(values))
        categories[category] = percent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        weighted += weight * percent
        denominator += weight
    raw = (weighted / denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    skills = [credits[r.id] for r in requirements if r.kind == "skill"]
    coverage = (sum(skills, Decimal(0)) * 100 / Decimal(len(skills))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if skills else None
    return ScoreBreakdown(raw_score=raw, match_score=int(raw.quantize(Decimal(1), rounding=ROUND_HALF_UP)),
                          category_scores=categories, skill_coverage_score=coverage, requirement_results=results)


def rank_evaluations(evaluations: list[Evaluation]) -> list[Evaluation]:
    """Rank raw scores with competition ties; incomplete comparisons have no winner."""
    if not evaluations: return []
    cleared = [Evaluation.model_validate({**e.model_dump(), "rank": None, "is_top_match": False}) for e in evaluations]
    complete = all(e.status == "complete" for e in cleared)
    EvaluationBatch(job_fingerprint=cleared[0].job_fingerprint, comparison_complete=complete, evaluations=cleared)
    if len({(e.as_of, e.scorer_version) for e in cleared}) != 1:
        raise ValueError("Comparison requires one date and scorer version")
    if not complete: return sorted(cleared, key=lambda e: e.resume_id)
    rubrics = [sorted((r.requirement.model_dump(mode="json") for r in e.requirement_results), key=lambda r: r["id"]) for e in cleared]
    if any(rubric != rubrics[0] for rubric in rubrics[1:]):
        raise ValueError("Comparison requires identical requirement definitions")
    ordered = sorted(cleared, key=lambda e: (-e.raw_score, e.resume_id))
    ranked = []
    previous_score = None
    rank = None
    for index, evaluation in enumerate(ordered, 1):
        if evaluation.raw_score != previous_score: rank = index
        ranked.append(Evaluation.model_validate({**evaluation.model_dump(), "rank": rank,
                                                "is_top_match": rank == 1 and evaluation.raw_score > 0}))
        previous_score = evaluation.raw_score
    return ranked
