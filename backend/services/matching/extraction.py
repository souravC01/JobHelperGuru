"""AI-only JD proposals validated against the complete, unchanged source."""

from __future__ import annotations

import hashlib
import json
import re
import time

from typing import Any, Literal

from pydantic import Field, StrictBool, StrictInt

from backend.services.skill_matching import supports_extracted_skill
from .chunking import TextChunk, chunk_text
from .provenance import SourceReference, proposal_span
from .models import MatchContract, NonEmptyString, Requirement, RequirementCategory, RequirementExtraction
from .normalization import matching_aliases_for_skill as aliases_for_skill, canonicalize_match_skill as canonicalize_skill, skill_components

EXTRACTOR_VERSION = "skill-jd-v5"
MAX_REQUIREMENTS = 64
_INSTRUCTION = re.compile(r"ignore\b.*\b(?:rubric|instructions?)|\bscore\s*\d+|\bsystem\s*prompt", re.I)
_ELIGIBILITY = re.compile(r"\b(?:work authorization|legally authorized|sponsorship|graduation window|class of 20\d{2})\b", re.I)

_NON_FIT = re.compile(r"^\s*(?:company(?: overview)?|about (?:us|the company)|benefits|salary|compensation)\s*:", re.I)
_SECTION = re.compile(r"^\s*(?:required(?: skills| qualifications)?|requirements|responsibilities|relevant experience|preferred(?: skills| qualifications)?|nice.to.haves)\s*:\s*$", re.I | re.M)


class RequirementProposal(SourceReference):
    category: RequirementCategory
    kind: Literal["skill"]
    canonical_key: NonEmptyString
    alternatives: list[NonEmptyString]
    required_months: None


class RequirementChunk(MatchContract):
    chunk_index: StrictInt = Field(ge=0)
    complete: StrictBool
    items: list[RequirementProposal]




def _skill_group(quote: str, key: str, alternatives: list[str]) -> None:
    # A known acronym expansion is annotation, not another OR alternative.
    def remove_expansion(match):
        prefix = quote[:match.start()]
        equivalent = any(re.search(r"(?<![\w+#])" + re.escape(alias) + r"\s*$", prefix, re.I)
                         for alias in aliases_for_skill(match[1]))
        return "" if equivalent else match[0]
    quote = re.sub(r"\s*\(([^()\n]+)\)", remove_expansion, quote)
    def spans(value, literal=False):
        def locate(aliases):
            return {(m.start(), m.end()) for alias in aliases
                    for m in re.finditer(r"(?<![\w+#])" + re.escape(alias) + r"(?![\w+#])", quote, re.I)}
        equivalents = locate(aliases_for_skill(value))
        if not equivalents and supports_extracted_skill(quote, value):
            # Locate the actual shorthand token so it cannot hide an OR neighbor.
            for alias in aliases_for_skill(value):
                if alias.casefold().endswith(" testing"):
                    prefix = alias[:-8]
                    equivalents |= locate((prefix+" tests", prefix+" test cases")) or locate((prefix,))
        positions = locate((value,)) if literal else equivalents
        # Prefer the full alias at each occurrence, but keep distinct OR occurrences.
        return sorted({max((p for p in equivalents if p[0] <= start and p[1] >= end),
                           key=lambda p: p[1]-p[0], default=(start,end)) for start,end in positions})
    # A comma list ending in OR belongs to one qualification, including unknown tools.
    def omitted_neighbor(start, end, grouped):
        before, after = quote[:start], quote[end:]
        return (grouped and re.search(r",\s*$", before)) or re.match(r"\s*,\s*(?:[\w+#./-]+(?:\s+[\w+#./-]+)*\s*,\s*)*or\b", after, re.I)
    def is_or_group(positions):
        joins = [quote[left[1]:right[0]] for left, right in zip(positions, positions[1:])]
        return bool(joins) and all(re.fullmatch(r"\s*(?:,\s*)?(?:or\s*)?", join, re.I) for join in joins) and any(re.search(r"\bor\b", join, re.I) for join in joins)
    if not alternatives:
        ordered = spans(key)
        # Canonical aliases can already be collapsed to a single stored qualification.
        if not is_or_group(ordered):
            for start, end in ordered:
                if omitted_neighbor(start,end,False):
                    raise ValueError("An OR group cannot omit a neighboring alternative")
                if re.search(r"\bor\s*$", quote[:start], re.I) or re.match(r"\s+or\b", quote[end:], re.I):
                    raise ValueError("A skill in an OR clause needs the whole alternative group")
            return
    else:
        located = [spans(a,literal=True) or spans(a) for a in alternatives]
        if any(len(matches) != 1 for matches in located):
            raise ValueError("Alternative skill names must be unambiguous")
        ordered = sorted(matches[0] for matches in located)
    if omitted_neighbor(ordered[0][0],ordered[-1][1],True):
        raise ValueError("An OR group cannot omit a neighboring alternative")
    if re.search(r"\bor\s*$", quote[:ordered[0][0]], re.I) or re.match(r"\s+or\b", quote[ordered[-1][1]:], re.I):
        raise ValueError("An OR group cannot omit a neighboring alternative")
    if not is_or_group(ordered):
        raise ValueError("Alternatives must form one explicit OR group")


def _materialize(item: RequirementProposal, chunk: TextChunk, source: str, source_hash: str) -> Requirement:
    quote, start, end = proposal_span(item, chunk)
    line_start = source.rfind("\n", 0, start) + 1
    line_end = source.find("\n", end)
    context = source[line_start:line_end if line_end != -1 else len(source)]
    if _INSTRUCTION.search(context) or _ELIGIBILITY.search(quote) or _NON_FIT.search(context):
        raise ValueError("Instructions and eligibility are not fit requirements")
    key = canonicalize_skill(item.canonical_key)
    raw_alternatives = list(dict.fromkeys(item.alternatives))
    alternatives = sorted({canonicalize_skill(a) for a in raw_alternatives})
    if not key or any(not a for a in alternatives):
        raise ValueError("Empty requirement identity")
    if raw_alternatives and (len(raw_alternatives) < 2 or not re.search(r"\bor\b", quote, re.I)):
        raise ValueError("Alternatives require an explicit OR group")
    if item.category not in {RequirementCategory.REQUIRED_SKILLS, RequirementCategory.PREFERRED_QUALIFICATIONS}:
        raise ValueError("Skills are qualifications, not activities or tenure")
    # Validate against the surrounding source too: a short quote cannot hide an option.
    _skill_group(context, key, raw_alternatives)
    if not all(supports_extracted_skill(quote, a) for a in alternatives or [key]):
        raise ValueError("Literal skill must occur in its source quote")
    if alternatives:
        key = "|".join(alternatives)
        if len(alternatives) == 1: alternatives = []
    identity = [source_hash, EXTRACTOR_VERSION, item.category.value, item.kind, key, alternatives, item.required_months]
    identifier = "req_" + hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode("utf-8")).hexdigest()[:20]
    return Requirement(id=identifier, category=item.category, kind=item.kind, canonical_key=key,
                       alternatives=alternatives, source_quote=quote, source_start=start, source_end=end,
                       required_months=item.required_months)


def _deduplicate(items: list[Requirement]) -> list[Requirement]:
    selected = {}
    for item in sorted(items, key=lambda r: (r.source_start, r.source_end, r.id)):
        identity = (item.kind, item.canonical_key, tuple(item.alternatives), item.required_months)
        previous = selected.get(identity)
        if previous is None:
            selected[identity] = item
        elif previous.category != item.category:
            categories = {previous.category, item.category}
            if categories not in ({RequirementCategory.REQUIRED_SKILLS, RequirementCategory.PREFERRED_QUALIFICATIONS},
                                  {RequirementCategory.RELEVANT_EXPERIENCE, RequirementCategory.PREFERRED_QUALIFICATIONS}):
                raise ValueError("Non-equivalent category conflict")
            if previous.category == RequirementCategory.PREFERRED_QUALIFICATIONS:
                selected[identity] = item
    return sorted(selected.values(), key=lambda r: (r.source_start, r.id))


def _materialize_proposals(items, chunk, source, source_hash):
    groups = {}
    for item in items:
        quote, start, end = proposal_span(item, chunk)
        if item.alternatives:
            groups.setdefault((start, end, item.category), []).append(item)
        else:
            for key in skill_components(item.canonical_key):
                groups.setdefault((start, end, item.category), []).append(item.model_copy(update={"canonical_key": key}))
    result = []
    for group in groups.values():
        try:
            accepted = [_materialize(item, chunk, source, source_hash) for item in group]
        except ValueError:
            if len(group) < 2 or any(item.alternatives for item in group):
                raise
            # ponytail: only co-located proposals; ambiguous/multiple clauses remain unscored.
            alternatives = list(dict.fromkeys(canonicalize_skill(item.canonical_key) for item in group))
            combined = group[0].model_copy(update={"alternatives": alternatives})
            accepted = [_materialize(combined, chunk, source, source_hash)]
        result.extend(accepted)
    return result


def _validated_chunk(payload, *, engine, deadline, validate):
    """Validate one response without correction requests or provider retries."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError
    response = engine.extract_match_chunk(payload, timeout=remaining)
    if time.monotonic() >= deadline:
        raise TimeoutError
    return validate(response)


def extract_requirements(text: str, *, engine: Any, deadline: float) -> RequirementExtraction:
    """Freeze an accepted interpretation; never score partial provider observations."""
    metadata = dict(source_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(), extractor_version=EXTRACTOR_VERSION)
    # Input limits are caller errors, not provider failures.
    chunks = chunk_text(text)
    items = []
    try:
        for index, chunk in enumerate(chunks):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            headings = list(_SECTION.finditer(text, 0, chunk.start))
            section_context = headings[-1].group().strip() if headings else ""
            payload = dict(task="requirements", chunk_index=index, chunk_count=len(chunks),
                           section_context=section_context,
                           source_text=chunk.text, schema=RequirementChunk.model_json_schema())
            def validate(response):
                result=RequirementChunk.model_validate(response)
                if result.chunk_index!=index or not result.complete:
                    raise ValueError("Missing complete chunk acknowledgment")
                return _materialize_proposals(result.items,chunk,text,metadata["source_hash"])
            items.extend(_validated_chunk(payload,engine=engine,deadline=deadline,validate=validate))
        items = _deduplicate(items)
    except TimeoutError:
        return RequirementExtraction(status="needs_review", warnings=["deadline_exceeded"], **metadata)
    except Exception:
        # Provider messages can contain keys or source text; never expose them.
        return RequirementExtraction(status="failed", warnings=["invalid_provider_response"], **metadata)
    reason = "rubric_limit" if len(items) > MAX_REQUIREMENTS else "no_assessable_requirements" if not items else None
    return RequirementExtraction(status="needs_review" if reason else "complete", items=items,
                                 assessed_requirement_ids=[] if reason else [r.id for r in items],
                                 unresolved_requirement_ids=[r.id for r in items] if reason else [],
                                 warnings=[reason] if reason else [], **metadata)
