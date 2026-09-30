"""Pure overall-job-fit arithmetic and ranking of comparable evaluations."""
from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from .models import (
    Evaluation, EvaluationBatch, Evidence, EvidenceLevel, RelevantInterval, Requirement,
    RequirementCategory, RequirementResult, ScoreBreakdown, has_evidence_conflict,
)

SCORER_VERSION = "overall-fit-v1"
CATEGORY_WEIGHTS = {
    RequirementCategory.REQUIRED_SKILLS: Decimal(60),
    RequirementCategory.RESPONSIBILITIES: Decimal(20),
    RequirementCategory.RELEVANT_EXPERIENCE: Decimal(15),
    RequirementCategory.PREFERRED_QUALIFICATIONS: Decimal(5),
}


def calculate_verified_months(intervals: list[RelevantInterval], as_of: date) -> Decimal:
    """Union elapsed work intervals, then count calendar months and residual days."""
    spans = sorted((i.start, min(i.end or as_of, as_of)) for i in intervals if i.start <= as_of)
    merged = []
    for start, end in spans:
        if end <= start: continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    total = Decimal(0)
    for start, end in merged:
        months = (end.year - start.year) * 12 + end.month - start.month
        def anniversary(offset):
            year, month = divmod(start.year * 12 + start.month - 1 + offset, 12)
            return year, month + 1, min(start.day, monthrange(year, month + 1)[1])
        anchor = date(*anniversary(months))
        if anchor > end:
            months -= 1
            anchor = date(*anniversary(months))
        # Avoid inventing a month or losing short spans at month-end boundaries.
        next_day = anniversary(months + 1)[2]
        days_to_next = monthrange(anchor.year, anchor.month)[1] - anchor.day + next_day
        total += Decimal(months) + Decimal((end - anchor).days) / Decimal(days_to_next)
    return total


def calculate_score(requirements: list[Requirement], evidence: list[Evidence], *, as_of: date) -> ScoreBreakdown:
    """Score already source-validated, explicitly complete requirement evidence."""
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
        if requirement.kind == "tenure":
            if not requirement.required_months or requirement.category not in {
                RequirementCategory.RELEVANT_EXPERIENCE, RequirementCategory.PREFERRED_QUALIFICATIONS,
            }:
                raise ValueError("Tenure requires a valid minimum and category")
            demonstrated = [i for i in items if i.level == EvidenceLevel.DEMONSTRATED]
            if any(not i.relevant_intervals or i.section != "work" for i in demonstrated):
                raise ValueError("Demonstrated tenure requires verified work intervals")
            months = calculate_verified_months([span for i in demonstrated for span in i.relevant_intervals], as_of)
            credit = min(Decimal(1), months / Decimal(requirement.required_months))
        else:
            if requirement.kind == "skill" and requirement.category not in {
                RequirementCategory.REQUIRED_SKILLS, RequirementCategory.PREFERRED_QUALIFICATIONS,
            }:
                raise ValueError("Literal skills require a qualification category")
            if requirement.required_months is not None:
                raise ValueError("Only tenure has required months")
            credit = Decimal(1) if EvidenceLevel.DEMONSTRATED in levels else Decimal(0)
            if requirement.kind == "skill" and EvidenceLevel.LISTED in levels:
                credit = max(credit, Decimal("0.5"))
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
