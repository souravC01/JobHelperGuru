"""Pure deterministic scoring and shared competition ranking for match evaluations."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from .models import (
    CategoryScore,
    Evaluation,
    EvaluationStatus,
    Evidence,
    EvidenceLevel,
    RelevantInterval,
    Requirement,
    RequirementCategory,
    RequirementResult,
    ScoreBreakdown,
)

CATEGORY_WEIGHTS: dict[RequirementCategory, Decimal] = {
    RequirementCategory.REQUIRED_SKILLS: Decimal(60),
    RequirementCategory.RESPONSIBILITIES: Decimal(20),
    RequirementCategory.RELEVANT_EXPERIENCE: Decimal(15),
    RequirementCategory.PREFERRED_QUALIFICATIONS: Decimal(5),
}

LEVEL_CREDITS: dict[EvidenceLevel, Decimal] = {
    EvidenceLevel.DEMONSTRATED: Decimal("1.00"),
    EvidenceLevel.LISTED: Decimal("0.50"),
    EvidenceLevel.LEARNING: Decimal("0.25"),
    EvidenceLevel.NOT_EVIDENCED: Decimal("0.00"),
    EvidenceLevel.CONTRADICTED: Decimal("0.00"),
}


def calculate_verified_months(
    intervals: list[RelevantInterval],
    as_of: date,
) -> Decimal:
    """Calculate the union of relevant intervals in months, avoiding double-counting."""
    normalized: list[tuple[date, date]] = []
    for interval in intervals:
        start = interval.start
        if start > as_of:
            continue
        end = min(interval.end or as_of, as_of)
        if end < start:
            continue
        normalized.append((start, end))

    if not normalized:
        return Decimal(0)

    # Sort by start date, then end date
    normalized.sort(key=lambda span: (span[0], span[1]))

    # Merge overlapping or contiguous spans
    merged: list[tuple[date, date]] = []
    current_start, current_end = normalized[0]

    for next_start, next_end in normalized[1:]:
        if next_start <= current_end + timedelta(days=1):
            current_end = max(current_end, next_end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = next_start, next_end
    merged.append((current_start, current_end))

    total_months = Decimal(0)
    for start, end in merged:
        months = (end.year - start.year) * 12 + (end.month - start.month)
        day_diff = end.day - start.day
        if day_diff != 0:
            months_dec = Decimal(months) + Decimal(day_diff) / Decimal(30)
        else:
            months_dec = Decimal(months)
        total_months += months_dec

    return max(Decimal(0), total_months)


def calculate_score(
    requirements: list[Requirement],
    evidence: list[Evidence],
    *,
    as_of: date,
) -> ScoreBreakdown:
    """Calculate deterministic evidence-based percentage score and category breakdown."""
    if not requirements:
        raise ValueError("cannot score empty requirements")

    req_ids = [r.id for r in requirements]
    if len(req_ids) != len(set(req_ids)):
        raise ValueError("duplicate requirement IDs")

    req_map = {r.id: r for r in requirements}

    # Group evidence by requirement ID and validate known IDs
    ev_by_req: dict[str, list[Evidence]] = {r.id: [] for r in requirements}
    for item in evidence:
        if item.requirement_id not in req_map:
            raise ValueError(f"evidence references unknown requirement ID: {item.requirement_id}")
        ev_by_req[item.requirement_id].append(item)

    requirement_results: list[RequirementResult] = []
    credits_by_req: dict[str, Decimal] = {}

    for req in requirements:
        items = ev_by_req[req.id]
        if not items:
            credit = Decimal("0.00")
            result_evidence = [Evidence(requirement_id=req.id, level=EvidenceLevel.NOT_EVIDENCED)]
        else:
            has_contradicted = any(e.level == EvidenceLevel.CONTRADICTED for e in items)
            has_positive = any(
                e.level in {EvidenceLevel.DEMONSTRATED, EvidenceLevel.LISTED, EvidenceLevel.LEARNING}
                for e in items
            )
            if has_contradicted and has_positive:
                # Conflicting claims flagged -> 0 credit
                credit = Decimal("0.00")
            elif req.kind == "tenure" and req.required_months:
                tenure_intervals = [
                    interval
                    for e in items
                    if e.level == EvidenceLevel.DEMONSTRATED
                    for interval in e.relevant_intervals
                ]
                verified_months = calculate_verified_months(tenure_intervals, as_of=as_of)
                credit = min(Decimal("1.00"), verified_months / Decimal(req.required_months))
            else:
                credit = max(LEVEL_CREDITS[e.level] for e in items)

            result_evidence = items

        credits_by_req[req.id] = credit
        requirement_results.append(
            RequirementResult(requirement=req, evidence=result_evidence)
        )

    # Group requirements by category
    reqs_by_cat: dict[RequirementCategory, list[Requirement]] = {
        cat: [] for cat in RequirementCategory
    }
    for req in requirements:
        reqs_by_cat[req.category].append(req)

    # Calculate category scores for populated categories only
    category_scores: dict[RequirementCategory, CategoryScore] = {}
    weighted_sum = Decimal(0)
    total_populated_weight = Decimal(0)

    for cat in RequirementCategory:
        cat_reqs = reqs_by_cat[cat]
        if not cat_reqs:
            continue
        weight = CATEGORY_WEIGHTS[cat]
        total_populated_weight += weight

        cat_mean_credit = sum(credits_by_req[r.id] for r in cat_reqs) / Decimal(len(cat_reqs))
        cat_score = (cat_mean_credit * Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        category_scores[cat] = cat_score

        weighted_sum += weight * (cat_mean_credit * Decimal(100))

    if total_populated_weight == 0:
        raw_score = Decimal("0.00")
        match_score = 0
    else:
        raw_score = (weighted_sum / total_populated_weight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        match_score = int(raw_score.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    return ScoreBreakdown(
        match_score=match_score,
        raw_score=raw_score,
        category_scores=category_scores,
        requirement_results=requirement_results,
    )


def rank_evaluations(evaluations: list[Evaluation]) -> list[Evaluation]:
    """Assign standard competition ranks (1, 1, 3) and top fit labels to evaluations."""
    if not evaluations:
        return []

    scorable: list[Evaluation] = []
    unscorable: list[Evaluation] = []

    for item in evaluations:
        if item.status == EvaluationStatus.COMPLETE and item.match_score is not None:
            scorable.append(item)
        else:
            unscorable.append(item)

    # Sort scorable: match_score descending, tie-break stably by resume_id ascending
    scorable.sort(key=lambda e: (-e.match_score, e.resume_id))

    ranked_scorable: list[Evaluation] = []
    for index, item in enumerate(scorable):
        if index == 0:
            item_rank = 1
        else:
            prev = ranked_scorable[index - 1]
            if item.match_score == prev.match_score:
                item_rank = prev.rank
            else:
                item_rank = index + 1

        is_top = (item_rank == 1 and item.match_score > 0)
        ranked_scorable.append(
            item.model_copy(update={"rank": item_rank, "is_top_match": is_top})
        )

    unranked = [
        item.model_copy(update={"rank": None, "is_top_match": False})
        for item in unscorable
    ]

    return ranked_scorable + unranked
