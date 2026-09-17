"""Evidence-only extraction with source validation and conservative offline rules.

Requirement IDs depend on job classifications, never on the candidate. Provider
results are proposals: no proposal crosses this boundary without exact source
spans, complete chunk coverage, and known requirement IDs.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime

from pydantic import Field, StrictInt

from backend.services.heuristic_parser import (
    SKILL_TAXONOMY,
    HeuristicParser,
    extract_employer_grad_criteria,
)
from backend.services.skill_matching import contains_skill

from .chunking import chunk_text
from .models import (
    EligibilityResult,
    Evidence,
    EvidenceExtraction,
    MatchContract,
    NonEmptyString,
    RelevantInterval,
    Requirement,
    RequirementExtraction,
)
from .normalization import aliases_for_skill, canonicalize_skill

EXTRACTOR_VERSION = "v2.1"
_INSTRUCTION = re.compile(
    r"ignore\b.*\b(?:rubric|instructions?)|\bscore\s*\d+|\bsystem\s*prompt",
    re.IGNORECASE,
)
_NEGATIVE = re.compile(r"\b(?:no|not|never|without|lack(?:ing)?)\b", re.IGNORECASE)
_LEARNING = re.compile(
    r"\b(?:learning|studying|coursework|beginner|tutorial|want to learn|plan to learn)\b",
    re.IGNORECASE,
)
_ACTION = re.compile(
    r"\b(?:built|developed|implemented|delivered|deployed|maintained|designed|used|created|automated|led)\b",
    re.IGNORECASE,
)


class RequirementChunk(MatchContract):
    chunk_index: StrictInt = Field(ge=0)
    items: list[Requirement]
    warnings: list[NonEmptyString] = Field(default_factory=list)


class EvidenceChunk(MatchContract):
    chunk_index: StrictInt = Field(ge=0)
    items: list[Evidence]
    assessed_requirement_ids: list[NonEmptyString]
    unresolved_requirement_ids: list[NonEmptyString]
    warnings: list[NonEmptyString] = Field(default_factory=list)


def _metadata(text):
    return {
        "source_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "extractor_version": EXTRACTOR_VERSION,
    }


def _stable_requirement(item):
    alternatives = sorted({canonicalize_skill(a) for a in item.alternatives})
    canonical = canonicalize_skill(item.canonical_key)
    if alternatives:
        canonical = "|".join(alternatives)
    identity = [
        item.category.value,
        item.kind,
        canonical,
        alternatives,
        item.required_months,
    ]
    identifier = "req_" + hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:20]
    return item.model_copy(
        update={
            "id": identifier,
            "canonical_key": canonical,
            "alternatives": alternatives,
        }
    )


def _validate_quote(text, item, chunk=None):
    if item.source_quote is None:
        return
    start, end = item.source_start, item.source_end
    if text[start:end] != item.source_quote:
        raise ValueError("quote does not match original source offsets")
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    if _INSTRUCTION.search(text[line_start:line_end]):
        raise ValueError(
            "document instructions cannot supply credited source fragments"
        )
    if chunk and not (chunk.start <= start < end <= chunk.end):
        raise ValueError("quote is outside the acknowledged chunk")


def _lines(text):
    for match in re.finditer(r"[^\n]+", text):
        if not _INSTRUCTION.search(match.group()):
            yield match.start(), match.group()


def _requirement(
    quote, start, category, canonical, kind="skill", alternatives=(), months=None
):
    return _stable_requirement(
        Requirement(
            id="pending",
            category=category,
            kind=kind,
            canonical_key=canonical,
            alternatives=list(alternatives),
            source_quote=quote,
            source_start=start,
            source_end=start + len(quote),
            required_months=months,
        )
    )


def _offline_requirements(text):
    items = []
    section = None
    for start, line in _lines(text):
        lower = line.lower()
        heading = re.match(
            r"\s*(required(?: skills| qualifications)?|skills|requirements|preferred(?: qualifications| skills)?|nice to have|responsibilities)\s*:\s*",
            line,
            re.IGNORECASE,
        )
        if heading:
            name = heading.group(1).lower()
            section = (
                "responsibilities"
                if name == "responsibilities"
                else "preferred_qualifications"
                if name.startswith(("preferred", "nice"))
                else "required_skills"
            )
        category = section
        if not category and re.search(
            r"\b(?:must|required|proficiency|experience with)\b", lower
        ):
            category = "required_skills"
        if not category:
            continue
        body = line[heading.end() :] if heading else line
        offset = start + (heading.end() if heading else 0)
        if not body.strip():
            continue
        # Sentences are separate statements; periods inside Node.js/.NET remain intact.
        for statement in re.finditer(r".+?(?:[.!?](?=\s|$)|$)", body):
            quote = statement.group().strip()
            quote_start = (
                offset
                + statement.start()
                + len(statement.group())
                - len(statement.group().lstrip())
            )
            if not quote:
                continue
            if category == "responsibilities":
                items.append(
                    _requirement(
                        quote, quote_start, category, quote.casefold(), "semantic"
                    )
                )
                continue
            if "(" in quote or ")" in quote or "/" in quote:
                items.append(
                    _requirement(
                        quote, quote_start, category, quote.casefold(), "semantic"
                    )
                )
                continue
            tenure = re.search(
                r"\b(\d+)\+?\s*(years?|months?)\s+(?:of\s+)?(.+?)\s+experience\b",
                quote,
                re.IGNORECASE,
            )
            if tenure:
                months = int(tenure.group(1)) * (
                    12 if tenure.group(2).lower().startswith("year") else 1
                )
                items.append(
                    _requirement(
                        quote,
                        quote_start,
                        "relevant_experience",
                        tenure.group(3),
                        "tenure",
                        months=months,
                    )
                )
                continue
            # AND creates independent requirements; OR remains a single alternative group.
            for group in re.split(
                r"\s+and\s+|,|;", quote.rstrip(".!?"), flags=re.IGNORECASE
            ):
                parts = re.split(r"\s+or\s+", group, flags=re.IGNORECASE)
                keys = []
                for part in parts:
                    cleaned = re.sub(
                        r"^(?:must have|proficiency in|experience with|knowledge of)\s+",
                        "",
                        part.strip(),
                        flags=re.IGNORECASE,
                    )
                    cleaned = re.sub(
                        r"\s+(?:required|preferred)$", "", cleaned, flags=re.IGNORECASE
                    )
                    known = [
                        skill
                        for skill in sorted(SKILL_TAXONOMY, key=lambda x: (-len(x), x))
                        if contains_skill(cleaned, skill)
                    ]
                    if known:
                        # Suppress nested names, e.g. Java in JavaScript or Git in GitHub.
                        key = canonicalize_skill(known[0])
                    elif re.fullmatch(r"[\w+#.-]+(?:\s+[\w+#.-]+)?", cleaned):
                        key = canonicalize_skill(cleaned)
                    else:
                        key = None
                    if key:
                        keys.append(key)
                if len(keys) != len(parts):
                    items.append(
                        _requirement(
                            quote,
                            quote_start,
                            category,
                            group.strip().casefold(),
                            "semantic",
                        )
                    )
                elif keys:
                    items.append(
                        _requirement(
                            quote,
                            quote_start,
                            category,
                            keys[0],
                            alternatives=keys if len(keys) > 1 else (),
                        )
                    )
    return items


def extract_requirements(
    text: str, *, mode="offline", engine=None
) -> RequirementExtraction:
    """Freeze a whole job's rubric independently of any resume."""
    meta = _metadata(text)
    warnings = []
    try:
        chunks = chunk_text(text)
        if mode == "offline":
            # Parse the reassembled full source to retain section state across chunk boundaries.
            covered = 0
            parts = []
            for chunk in chunks:
                parts.append(chunk.text[max(0, covered - chunk.start) :])
                covered = chunk.end
            items = _offline_requirements("".join(parts))
        elif mode == "ai":
            items = []
            provider_ids = {}
            source_classifications = {}
            if engine is None:
                raise ValueError("AI extraction requires a configured engine")
            for index, chunk in enumerate(chunks):
                result = RequirementChunk.model_validate(
                    engine.extract_match_chunk(
                        {
                            "task": "requirements",
                            "chunk_index": index,
                            "chunk_count": len(chunks),
                            "source_start": chunk.start,
                            "source_text": chunk.text,
                            "schema": RequirementChunk.model_json_schema(),
                        }
                    )
                )
                if result.chunk_index != index:
                    raise ValueError("missing or incorrect chunk acknowledgement")
                for item in result.items:
                    _validate_quote(text, item, chunk)
                    if _INSTRUCTION.search(item.source_quote):
                        raise ValueError("document instructions cannot be requirements")
                    previous = provider_ids.get(item.id)
                    classification = (
                        item.category,
                        item.kind,
                        canonicalize_skill(item.canonical_key),
                        sorted(item.alternatives),
                        item.required_months,
                    )
                    if previous is not None and previous != classification:
                        raise ValueError(
                            "conflicting duplicate requirement classifications"
                        )
                    provider_ids[item.id] = classification
                    source_key = (
                        item.source_start,
                        item.source_end,
                        canonicalize_skill(item.canonical_key),
                    )
                    if (
                        source_key in source_classifications
                        and source_classifications[source_key] != classification
                    ):
                        raise ValueError(
                            "conflicting classifications for the same source requirement"
                        )
                    source_classifications[source_key] = classification
                    if item.kind == "skill":
                        for key in item.alternatives or [item.canonical_key]:
                            if not any(
                                contains_skill(item.source_quote, alias)
                                for alias in aliases_for_skill(key)
                            ):
                                raise ValueError(
                                    "literal requirements must occur in their source quote"
                                )
                    items.append(_stable_requirement(item))
                warnings.extend(result.warnings)
        else:
            raise ValueError("unsupported extraction mode")
        unique = {}
        for item in items:
            _validate_quote(text, item)
            unique.setdefault(item.id, item)
        items = sorted(unique.values(), key=lambda item: (item.source_start, item.id))
        if not items:
            warnings.append("No assessable job requirements were extracted.")
        return RequirementExtraction(
            status="complete" if items else "needs_review",
            items=items,
            assessed_requirement_ids=[r.id for r in items],
            warnings=warnings,
            **meta,
        )
    except Exception as exc:  # noqa: BLE001 - provider failures must invalidate the whole extraction
        return RequirementExtraction(
            status="failed",
            warnings=[f"Requirement extraction failed: {type(exc).__name__}: {exc}"],
            **meta,
        )


def _matches(text, requirement):
    return any(
        contains_skill(text, alias)
        for key in (requirement.alternatives or [requirement.canonical_key])
        for alias in aliases_for_skill(key)
    )


def _intervals(line, as_of):
    intervals = []
    month_names = {
        name: index
        for index, name in enumerate(
            (
                "jan",
                "feb",
                "mar",
                "apr",
                "may",
                "jun",
                "jul",
                "aug",
                "sep",
                "oct",
                "nov",
                "dec",
            ),
            1,
        )
    }

    def parse_month(value):
        if re.fullmatch(r"\d{4}-\d{2}", value):
            year, month = value.split("-")
            return date(int(year), int(month), 1)
        month, year = value.split()
        return date(int(year), month_names[month.lower()[:3]], 1)

    token = r"(?:\d{4}-\d{2}|[A-Za-z]+\s+\d{4})"
    for match in re.finditer(
        rf"\b({token})\s*[-–—]\s*({token}|present|current)\b", line, re.IGNORECASE
    ):
        try:
            start = parse_month(match[1])
            end = (
                as_of
                if match[2].lower() in {"present", "current"}
                else parse_month(match[2])
            )
            if start <= end and start <= as_of:
                intervals.append(RelevantInterval(start=start, end=min(end, as_of)))
        except (KeyError, ValueError):
            continue
    return intervals


def _offline_evidence(text, requirements, as_of):
    items, unresolved = [], []
    lines = []
    for start, line in _lines(text):
        for clause in re.finditer(r".+?(?:;|[.!?](?=\s|$)|$)", line):
            lines.append((start + clause.start(), clause.group()))
    for requirement in requirements:
        if requirement.kind not in {"skill", "tenure"}:
            unresolved.append(requirement.id)
            continue
        found = []
        for start, line in lines:
            if not _matches(line, requirement):
                continue
            level = (
                "contradicted"
                if _NEGATIVE.search(line)
                else "learning"
                if _LEARNING.search(line)
                else "demonstrated"
                if _ACTION.search(line)
                else "listed"
            )
            intervals = (
                _intervals(line, as_of)
                if requirement.kind == "tenure" and level == "demonstrated"
                else []
            )
            if requirement.kind == "tenure" and not intervals:
                continue
            found.append(
                Evidence(
                    requirement_id=requirement.id,
                    level=level,
                    source_quote=line,
                    source_start=start,
                    source_end=start + len(line),
                    relevant_intervals=intervals,
                )
            )
        if requirement.kind == "tenure" and not found:
            unresolved.append(requirement.id)
        else:
            items.extend(
                found
                or [Evidence(requirement_id=requirement.id, level="not_evidenced")]
            )
    return items, unresolved


def _validate_evidence_chunk(result, text, chunk, index, known, as_of):
    if result.chunk_index != index:
        raise ValueError("missing or incorrect chunk acknowledgement")
    assessed, unresolved = (
        set(result.assessed_requirement_ids),
        set(result.unresolved_requirement_ids),
    )
    if (
        assessed | unresolved != known
        or assessed & unresolved
        or len(assessed) != len(result.assessed_requirement_ids)
        or len(unresolved) != len(result.unresolved_requirement_ids)
    ):
        raise ValueError(
            "every chunk must assess or mark unresolved every known requirement"
        )
    if {item.requirement_id for item in result.items} != assessed:
        raise ValueError("unknown or unassessed requirement ID")
    seen = {}
    for item in result.items:
        _validate_quote(text, item, chunk)
        if item.source_quote and _INSTRUCTION.search(item.source_quote):
            raise ValueError("document instructions cannot be credited evidence")
        allowed_intervals = _intervals(item.source_quote or "", as_of)
        if any(
            interval not in allowed_intervals for interval in item.relevant_intervals
        ):
            raise ValueError("relevant intervals must be supported by quoted dates")
        key = item.requirement_id, item.source_start, item.source_end
        if key in seen and seen[key] != item:
            raise ValueError("conflicting duplicate evidence")
        seen[key] = item


def extract_evidence(
    text: str,
    requirements: list[Requirement],
    *,
    as_of: date,
    mode="offline",
    engine=None,
) -> EvidenceExtraction:
    """Assess a frozen requirement set; never calculate a score."""
    meta = _metadata(text)
    known = {r.id for r in requirements}
    warnings = []
    try:
        if len(known) != len(requirements):
            raise ValueError("duplicate input requirement IDs")
        chunks = chunk_text(text)
        if mode == "offline":
            items, unresolved = _offline_evidence(text, requirements, as_of)
        elif mode == "ai":
            if engine is None:
                raise ValueError("AI extraction requires a configured engine")
            items, unresolved = [], set()
            for index, chunk in enumerate(chunks):
                result = EvidenceChunk.model_validate(
                    engine.extract_match_chunk(
                        {
                            "task": "evidence",
                            "chunk_index": index,
                            "chunk_count": len(chunks),
                            "source_start": chunk.start,
                            "source_text": chunk.text,
                            "as_of": as_of.isoformat(),
                            "requirements": [
                                r.model_dump(mode="json") for r in requirements
                            ],
                            "schema": EvidenceChunk.model_json_schema(),
                        }
                    )
                )
                _validate_evidence_chunk(result, text, chunk, index, known, as_of)
                items.extend(result.items)
                unresolved.update(result.unresolved_requirement_ids)
                warnings.extend(result.warnings)
            if not chunks:
                items = [
                    Evidence(requirement_id=r.id, level="not_evidenced")
                    for r in requirements
                ]
        else:
            raise ValueError("unsupported extraction mode")
        unique = {}
        for item in items:
            _validate_quote(text, item)
            if item.requirement_id in unresolved:
                continue
            key = item.requirement_id, item.source_start, item.source_end
            if key in unique and unique[key] != item:
                raise ValueError("conflicting duplicate evidence across chunks")
            unique[key] = item
        positive_ids = {
            item.requirement_id
            for item in unique.values()
            if item.level != "not_evidenced"
        }
        items = [
            item
            for item in unique.values()
            if item.level != "not_evidenced" or item.requirement_id not in positive_ids
        ]
        if unresolved:
            warnings.append("Some requirements could not be assessed confidently.")
        return EvidenceExtraction(
            status="needs_review" if unresolved else "complete",
            items=items,
            assessed_requirement_ids=sorted(known - set(unresolved)),
            unresolved_requirement_ids=sorted(unresolved),
            warnings=warnings,
            **meta,
        )
    except Exception as exc:  # noqa: BLE001 - provider failures must invalidate the whole extraction
        return EvidenceExtraction(
            status="failed",
            unresolved_requirement_ids=sorted(known),
            warnings=[f"Evidence extraction failed: {type(exc).__name__}: {exc}"],
            **meta,
        )


def extract_eligibility(
    job_text: str, resume_text: str, *, as_of: date
) -> list[EligibilityResult]:
    """Keep graduation eligibility separate from merit evidence and reuse existing rules."""
    criterion = extract_employer_grad_criteria(job_text)
    if not criterion:
        return []
    result = HeuristicParser().check_new_grad_eligibility(
        resume_text,
        criterion,
        ref_date=datetime.combine(as_of, datetime.min.time()),
    )
    status = (
        "unknown"
        if result["eligible"] is None
        else "eligible"
        if result["eligible"]
        else "ineligible"
    )
    return [
        EligibilityResult(criterion=criterion, status=status, reason=result["status"])
    ]
