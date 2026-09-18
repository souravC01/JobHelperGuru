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

EXTRACTOR_VERSION = "v2.3"
_INSTRUCTION = re.compile(
    r"ignore\b.*\b(?:rubric|instructions?)|\bscore\s*\d+|\bsystem\s*prompt",
    re.IGNORECASE,
)
_NEGATIVE = re.compile(r"\b(?:no|not|never|without|lack(?:ing)?)\b", re.IGNORECASE)
_LEARNING = re.compile(
    r"\b(?:learning|studying|coursework|beginner|tutorial|want(?:s|ed)? to learn|plan to learn)\b",
    re.IGNORECASE,
)
_ACTION = re.compile(
    r"\b(?:built|developed|implemented|delivered|deployed|maintained|designed|used|created|automated|led)\b",
    re.IGNORECASE,
)
_PREDICATE = f"(?:{_ACTION.pattern}|{_LEARNING.pattern}|{_NEGATIVE.pattern})"
_TECHNOLOGIES = SKILL_TAXONOMY | {"React Native", "NoSQL"}
_ELIGIBILITY = re.compile(
    r"\bgraduat(?:ion|ing|ed|es?)\b|\bclass\s+of\b|\bdegree\s+completion\b",
    re.IGNORECASE,
)


def _literal_key(value):
    """Recognize a complete literal name; never substitute a matching substring."""
    value = value.strip()
    if canonicalize_skill(value) != value.casefold():
        return canonicalize_skill(value)
    if any(value.casefold() == skill.casefold() for skill in _TECHNOLOGIES):
        return canonicalize_skill(value)
    if re.fullmatch(r"[\w+#.-]+", value):
        return canonicalize_skill(value)
    if re.fullmatch(r"[A-Z][\w+#.-]*(?:\s+[A-Z][\w+#.-]*){1,3}", value):
        return canonicalize_skill(value)
    return None


def _conjuncts(text):
    """Split clear AND clauses without breaking a between-dates eligibility window."""
    start = 0
    for delimiter in re.finditer(r"\s+and\s+|,|;", text, re.IGNORECASE):
        prefix = text[: delimiter.start()]
        if prefix.count("(") > prefix.count(")"):
            continue
        current = text[start : delimiter.start()]
        if (
            _ELIGIBILITY.search(current)
            and re.search(r"\bbetween\b", current, re.IGNORECASE)
            and not re.search(r"\band\b", current, re.IGNORECASE)
        ):
            continue
        yield start, current
        start = delimiter.end()
    yield start, text[start:]


def _literal_spans(text, key):
    """Exact aliases with punctuation boundaries and longest technology precedence."""
    for alias in aliases_for_skill(key):
        prefix = r"(?<![\w+#.])" if alias.startswith(".") else r"(?<![\w+#])"
        for match in re.finditer(
            prefix + re.escape(alias) + r"(?![\w+#])", text, re.IGNORECASE
        ):
            shadowed = False
            for technology in _TECHNOLOGIES:
                if len(technology) <= len(alias) or canonicalize_skill(
                    technology
                ) == canonicalize_skill(key):
                    continue
                if not contains_skill(technology, alias):
                    continue
                for longer in re.finditer(
                    r"(?<![\w+#])" + re.escape(technology) + r"(?![\w+#])",
                    text,
                    re.IGNORECASE,
                ):
                    if longer.start() <= match.start() and match.end() <= longer.end():
                        shadowed = True
            if not shadowed:
                yield match


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


def _heading_name(line):
    """Recognize standalone heading-like transitions, including unknown sections."""
    value = line.strip()
    if _ACTION.match(value) or _LEARNING.match(value) or _NEGATIVE.match(value):
        return None
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 &/'’()-]{0,79}:?", value):
        return None
    if len(value.split()) > 8:
        return None
    if not value.endswith(":") and len(value.split()) < 2:
        return None
    return value.rstrip(":").strip().casefold()


def _eligibility_spans(text):
    """Identify eligibility clauses without interpreting their date-window rules."""
    for line_start, line in _lines(text):
        for sentence in re.finditer(r".+?(?:[.!?](?=\s|$)|$)", line):
            for offset, clause in _conjuncts(sentence.group()):
                if _ELIGIBILITY.search(clause):
                    start = line_start + sentence.start() + offset
                    yield start, start + len(clause)


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
    lines = list(_lines(text))
    for index, (start, line) in enumerate(lines):
        lower = line.lower()
        heading = re.match(
            r"\s*(required(?: skills| qualifications)?|(?:basic|minimum) qualifications|qualifications|skills|requirements|preferred(?: qualifications| skills)?|nice to have|responsibilities|what you bring|what you(?: will|'ll|’ll) do|about us|benefits|compensation|perks|who we are)\s*(?::\s*|$)",
            line,
            re.IGNORECASE,
        )
        if heading:
            name = heading.group(1).lower()
            section = (
                "non_requirements"
                if name
                in {"about us", "benefits", "compensation", "perks", "who we are"}
                else "responsibilities"
                if name == "responsibilities"
                or (name.startswith("what you") and name.endswith("do"))
                else "preferred_qualifications"
                if name.startswith(("preferred", "nice"))
                else "required_skills"
            )
        elif _heading_name(line) is not None:
            next_line = lines[index + 1][1] if index + 1 < len(lines) else ""
            if re.match(r"\s*[-*•]\s+", next_line):
                section = "unclassified_requirements"
                continue
            if line.rstrip().endswith(":"):
                section = None
                continue
        if section == "non_requirements":
            continue
        category = (
            "required_skills" if section == "unclassified_requirements" else section
        )
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
            if any(mark in quote for mark in "()/") and not _ELIGIBILITY.search(quote):
                items.append(
                    _requirement(
                        quote, quote_start, category, quote.casefold(), "semantic"
                    )
                )
                continue
            # AND creates independent requirements; OR remains a single alternative group.
            for group_offset, raw_group in _conjuncts(quote.rstrip(".!?")):
                group = re.sub(r"^\s*[-*•]\s*", "", raw_group).strip()
                group_start = (
                    quote_start + group_offset + raw_group.index(group)
                    if group
                    else quote_start
                )
                if not group or _ELIGIBILITY.search(group):
                    continue
                if (
                    category == "responsibilities"
                    or section == "unclassified_requirements"
                ):
                    items.append(
                        _requirement(
                            group, group_start, category, group.casefold(), "semantic"
                        )
                    )
                    continue
                tenure = re.fullmatch(
                    r"(?:at least\s+)?(\d+)\+?\s*(years?|months?)\s+(?:of\s+)?(?:professional\s+)?(.+?)\s+(?:professional\s+)?experience",
                    group,
                    re.IGNORECASE,
                )
                tenure_key = _literal_key(tenure.group(3)) if tenure else None
                if tenure_key:
                    months = int(tenure.group(1)) * (
                        12 if tenure.group(2).lower().startswith("year") else 1
                    )
                    items.append(
                        _requirement(
                            group,
                            group_start,
                            "relevant_experience",
                            tenure_key,
                            "tenure",
                            months=months,
                        )
                    )
                    continue
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
                    key = _literal_key(cleaned)
                    if key:
                        keys.append(key)
                if len(keys) != len(parts):
                    items.append(
                        _requirement(
                            group,
                            group_start,
                            category,
                            group.strip().casefold(),
                            "semantic",
                        )
                    )
                elif keys:
                    items.append(
                        _requirement(
                            group,
                            group_start,
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
            eligibility_spans = list(_eligibility_spans(text))
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
                    if any(
                        start <= item.source_start and item.source_end <= end
                        for start, end in eligibility_spans
                    ):
                        continue
                    if _ELIGIBILITY.search(item.canonical_key.replace("_", " ")) or (
                        item.kind != "skill" and _ELIGIBILITY.search(item.source_quote)
                    ):
                        continue
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
                                item.source_start <= span.start()
                                and span.end() <= item.source_end
                                for span in _literal_spans(text, key)
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
        any(_literal_spans(text, key))
        for key in (requirement.alternatives or [requirement.canonical_key])
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


def _source_clauses(text):
    """Keep original spans and document sections while separating clear modifiers."""
    section = "unknown"
    headings = {
        "work": r"work experience|professional experience|employment history|employment|work history",
        "projects": r"personal projects?|projects?|hobby projects?",
        "coursework": r"coursework|courses|training",
        "education": r"education|academic background",
        "skills": r"(?:technical )?skills",
    }
    for line_start, line in _lines(text):
        heading_name = _heading_name(line)
        if heading_name is not None:
            section = "unknown"
            if re.search(r"\bprojects?\b|\bopen[- ]source\b", heading_name):
                section = "projects"
            elif re.search(r"\bcoursework\b|\bcourses\b|\btraining\b", heading_name):
                section = "coursework"
            elif re.search(r"\beducation\b|\bacademic background\b", heading_name):
                section = "education"
        for name, pattern in headings.items():
            if re.match(rf"^\s*(?:{pattern})\s*(?::|$)", line, re.IGNORECASE):
                section = name
                break
        local_section = section
        if re.search(r"\b(?:personal|hobby)\s+project\b", line, re.IGNORECASE):
            local_section = "projects"
        for sentence in re.finditer(r".+?(?:;|[.!?](?=\s|$)|$)", line):
            value = sentence.group()
            start = 0
            # A bare technology conjunction shares its modifier. A new explicit
            # predicate starts a separate clause, so its polarity cannot leak back.
            boundary = rf"\s+(?=without\b)|(?:\s+(?:and|but)\s+|,\s*)(?=(?:(?:currently|actively)\s+)?{_PREDICATE})"
            for split in re.finditer(boundary, value, re.IGNORECASE):
                yield (
                    line_start + sentence.start() + start,
                    value[start : split.start()],
                    local_section,
                )
                start = split.end()
            yield line_start + sentence.start() + start, value[start:], local_section


def _context_level(clause, section):
    if _NEGATIVE.search(clause):
        return "contradicted"
    if _LEARNING.search(clause) or section == "coursework":
        return "learning"
    return "demonstrated" if _ACTION.search(clause) else "listed"


def _offline_evidence(text, requirements, as_of):
    items, unresolved = [], []
    lines = list(_source_clauses(text))
    for requirement in requirements:
        if requirement.kind not in {"skill", "tenure"}:
            unresolved.append(requirement.id)
            continue
        found = []
        for start, line, section in lines:
            if not _matches(line, requirement):
                continue
            level = _context_level(line, section)
            intervals = (
                _intervals(line, as_of)
                if requirement.kind == "tenure"
                and level == "demonstrated"
                and section == "work"
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
                    section=section,
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


def _validate_evidence_chunk(result, text, chunk, index, requirements, as_of):
    requirement_by_id = {r.id: r for r in requirements}
    known = set(requirement_by_id)
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
    clauses = list(_source_clauses(text))
    for item in result.items:
        _validate_quote(text, item, chunk)
        if item.source_quote and _INSTRUCTION.search(item.source_quote):
            raise ValueError("document instructions cannot be credited evidence")
        allowed_intervals = _intervals(item.source_quote or "", as_of)
        if any(
            interval not in allowed_intervals for interval in item.relevant_intervals
        ):
            raise ValueError("relevant intervals must be supported by quoted dates")
        requirement = requirement_by_id[item.requirement_id]
        if item.source_quote is not None:
            contexts = [
                (start, clause, section)
                for start, clause, section in clauses
                if start < item.source_end and item.source_start < start + len(clause)
            ]
            sections = {section for _, _, section in contexts}
            derived_section = next(iter(sections)) if len(sections) == 1 else "unknown"
            if item.section is not None and item.section != derived_section:
                raise ValueError("provider section does not match the source document")
            item.section = derived_section
            if (
                requirement.kind in {"skill", "tenure"}
                and item.level != "not_evidenced"
            ):
                if not _matches(item.source_quote, requirement):
                    raise ValueError(
                        "literal evidence must quote the required technology or an explicit alias"
                    )
                levels = set()
                for start, clause, section in contexts:
                    spans = [
                        span
                        for key in (
                            requirement.alternatives or [requirement.canonical_key]
                        )
                        for span in _literal_spans(clause, key)
                    ]
                    if any(
                        item.source_start <= start + span.start()
                        and start + span.end() <= item.source_end
                        for span in spans
                    ):
                        levels.add(_context_level(clause, section))
                if not levels:
                    raise ValueError(
                        "quoted fragment is not a complete matching technology in its source context"
                    )
                if "contradicted" in levels and item.level != "contradicted":
                    raise ValueError(
                        "positive provider evidence conflicts with explicit source negation"
                    )
                if "learning" in levels and item.level not in {
                    "learning",
                    "contradicted",
                }:
                    raise ValueError(
                        "positive provider evidence conflicts with learning context"
                    )
                if item.level == "contradicted" and "contradicted" not in levels:
                    raise ValueError(
                        "provider contradiction lacks an explicit negative context"
                    )
            if item.relevant_intervals and (
                requirement.kind != "tenure"
                or derived_section != "work"
                or item.level != "demonstrated"
            ):
                raise ValueError(
                    "professional tenure requires source-backed employment context"
                )
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
                _validate_evidence_chunk(
                    result, text, chunk, index, requirements, as_of
                )
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
