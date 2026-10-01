"""AI-only JD proposals validated against the complete, unchanged source."""

from __future__ import annotations

import hashlib
import json
import re
import time
from decimal import Decimal
from datetime import date

from backend.models import Resume
from typing import Any, Literal

from pydantic import Field, StrictBool, StrictInt

from backend.services.skill_matching import contains_skill
from .chunking import TextChunk, chunk_text
from .provenance import _quote_span
from .models import MatchContract, NonEmptyString, Requirement, RequirementCategory, RequirementExtraction, ResumeProfile, EvidenceExtraction, has_evidence_conflict
from .normalization import aliases_for_skill, canonicalize_skill

EXTRACTOR_VERSION = "overall-jd-v4"
ASSESSMENT_VERSION = "overall-assessment-v4"
MAX_REQUIREMENTS = 64
_INSTRUCTION = re.compile(r"ignore\b.*\b(?:rubric|instructions?)|\bscore\s*\d+|\bsystem\s*prompt", re.I)
_ELIGIBILITY = re.compile(r"\b(?:work authorization|legally authorized|sponsorship|graduation window|class of 20\d{2})\b", re.I)

_NON_FIT = re.compile(r"^\s*(?:company(?: overview)?|about (?:us|the company)|benefits|salary|compensation)\s*:", re.I)
_SECTION = re.compile(r"^\s*(?:required(?: skills| qualifications)?|requirements|responsibilities|relevant experience|preferred(?: skills| qualifications)?|nice.to.haves)\s*:\s*$", re.I | re.M)


class RequirementProposal(MatchContract):
    category: RequirementCategory
    kind: Literal["skill", "semantic", "tenure", "credential", "experience"]
    canonical_key: NonEmptyString
    alternatives: list[NonEmptyString]
    source_quote: NonEmptyString
    required_months: StrictInt | None = Field(gt=0)


class RequirementChunk(MatchContract):
    chunk_index: StrictInt = Field(ge=0)
    complete: StrictBool
    items: list[RequirementProposal]




def _tenure_months(quote: str) -> set[int]:
    # Borrowed minimum-range semantics; no provider-invented experience thresholds.
    factor = lambda unit: 12 if unit.lower().startswith("year") else 1
    span = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)\s*(years?|months?)\b", quote, re.I)
    if span:
        lower, upper = Decimal(span[1]), Decimal(span[2])
        months = lower * factor(span[3])
        return {int(months)} if lower <= upper and months == int(months) else set()
    return {int(months) for match in re.finditer(r"\b(\d+(?:\.\d+)?)\+?\s*(years?|months?)\b", quote, re.I)
            if (months := Decimal(match[1]) * factor(match[2])) == int(months)}


def _skill_group(quote: str, key: str, alternatives: list[str]) -> None:
    def spans(value):
        return sorted({(m.start(), m.end()) for alias in aliases_for_skill(value)
                       for m in re.finditer(r"(?<![\w+#])" + re.escape(alias) + r"(?![\w+#])", quote, re.I)})
    if not alternatives:
        for start, end in spans(key):
            if re.search(r"\bor\s*$", quote[:start], re.I) or re.match(r"\s+or\b", quote[end:], re.I):
                raise ValueError("A skill in an OR clause needs the whole alternative group")
        return
    located = [spans(a) for a in alternatives]
    if any(len(matches) != 1 for matches in located):
        raise ValueError("Alternative skill names must be unambiguous")
    ordered = sorted(matches[0] for matches in located)
    if re.search(r"\bor\s*$", quote[:ordered[0][0]], re.I) or re.match(r"\s+or\b", quote[ordered[-1][1]:], re.I):
        raise ValueError("An OR group cannot omit a neighboring alternative")
    joins = [quote[left[1]:right[0]] for left, right in zip(ordered, ordered[1:])]
    if not all(re.fullmatch(r"\s*(?:,\s*)?(?:or\s*)?", join, re.I) for join in joins) or not any(re.search(r"\bor\b", join, re.I) for join in joins):
        raise ValueError("Alternatives must form one explicit OR group")


def _materialize(item: RequirementProposal, chunk: TextChunk, source: str, source_hash: str) -> Requirement:
    quote, start, end = _quote_span(item.source_quote, chunk)
    line_start = source.rfind("\n", 0, start) + 1
    line_end = source.find("\n", end)
    context = source[line_start:line_end if line_end != -1 else len(source)]
    if _INSTRUCTION.search(context) or _ELIGIBILITY.search(quote) or _NON_FIT.search(context):
        raise ValueError("Instructions and eligibility are not fit requirements")
    key = canonicalize_skill(item.canonical_key)
    alternatives = sorted({canonicalize_skill(a) for a in item.alternatives})
    if not key or any(not a for a in alternatives):
        raise ValueError("Empty requirement identity")
    if item.kind == "tenure":
        if alternatives or item.category not in {RequirementCategory.RELEVANT_EXPERIENCE, RequirementCategory.PREFERRED_QUALIFICATIONS}:
            raise ValueError("Invalid tenure classification")
        if _tenure_months(quote) != {item.required_months}:
            raise ValueError("Tenure must use the explicit source minimum")
    elif item.required_months is not None:
        raise ValueError("Only tenure requirements have numeric months")
    if alternatives:
        if len(alternatives) < 2 or not re.search(r"\bor\b", quote, re.I):
            raise ValueError("Alternatives require an explicit OR group")
        key = "|".join(alternatives)
    if item.kind == "skill":
        if item.category not in {RequirementCategory.REQUIRED_SKILLS, RequirementCategory.PREFERRED_QUALIFICATIONS}:
            raise ValueError("Skills are qualifications, not activities or tenure")
        _skill_group(quote, key, alternatives)
        if not all(contains_skill(quote, a) for a in alternatives or [key]):
            raise ValueError("Literal skill must occur in its source quote")
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


def _validated_chunk(payload, *, engine, deadline, validate):
    """Correct one received invalid response; every attempt uses the same source and validator."""
    for attempt in range(2):
        remaining=deadline-time.monotonic()
        if remaining<=0: raise TimeoutError
        try:
            response=engine.extract_match_chunk(payload,timeout=remaining)
        except json.JSONDecodeError as exc:
            if attempt: raise
            payload={**payload,'validation_feedback':dict(reason='invalid_json_response',previous_response=exc.doc)}
            continue
        if time.monotonic()>=deadline: raise TimeoutError
        try:
            return validate(response)
        except (ValueError,TypeError,KeyError):
            if attempt or isinstance(response,dict) and response.get('complete') is False:
                raise
            # Exception messages may contain private text; feedback uses a fixed server-owned reason.
            payload={**payload,'validation_feedback':dict(reason='schema_or_source_validation_failed',previous_response=response)}


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
                return [_materialize(p,chunk,text,metadata["source_hash"]) for p in result.items]
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


class EvidenceProposal(MatchContract):
    requirement_id: NonEmptyString
    level: Literal["demonstrated", "listed", "learning", "not_evidenced", "contradicted"]
    source_quote: NonEmptyString | None


class ResumeEvidenceProposal(MatchContract):
    resume_id: NonEmptyString
    chunk_index: StrictInt = Field(ge=0)
    items: list[EvidenceProposal]
    assessed_requirement_ids: list[NonEmptyString]
    unresolved_requirement_ids: list[NonEmptyString]


class EvidenceBatchProposal(MatchContract):
    items: list[ResumeEvidenceProposal]


def _verified_intervals(quote, start, end, resume, profile, as_of):
    from .models import RelevantInterval
    from .provenance import date_ranges, work_span
    if not work_span(resume.content, start, end):
        return []
    parents = [f for f in profile.facts if f.kind == "employment" and
               f.source_start <= start < end <= f.source_end] if profile else []
    if len(parents) == 1:
        ranges = [(parents[0].start, parents[0].end)]
    else:
        ranges = date_ranges(quote)
        if len(ranges) != 1:
            return []
    return [RelevantInterval(start=a, end=min(b or as_of, as_of)) for a, b in ranges
            if a <= as_of and (b is None or b >= a)]


def _local_evidence(resume, profile, requirement, as_of):
    from .models import Evidence
    keys = requirement.alternatives or [requirement.canonical_key]
    if requirement.kind == "skill":
        facts = [f for f in profile.facts if f.kind == "skill" and f.canonical_key in keys] if profile else []
        if facts:
            return [Evidence(requirement_id=requirement.id, level=f.level, source_quote=f.source_quote,
                             source_start=f.source_start, source_end=f.source_end, section=f.section)
                    for f in facts]
        if not any(contains_skill(resume.content, k) for k in keys):
            return [Evidence(requirement_id=requirement.id, level="not_evidenced")]
    if profile and requirement.kind in {"tenure", "credential"}:
        kind = "employment" if requirement.kind == "tenure" else "credential"
        facts = [f for f in profile.facts if f.kind == kind and f.level == "demonstrated"
                 and any(contains_skill(f.source_quote, k) for k in keys)]
        result = []
        for f in facts:
            intervals = _verified_intervals(f.source_quote, f.source_start, f.source_end, resume, profile, as_of) if kind == "employment" else []
            if kind == "employment" and not intervals: continue
            result.append(Evidence(requirement_id=requirement.id, level=f.level, source_quote=f.source_quote,
                                   source_start=f.source_start, source_end=f.source_end, section=f.section,
                                   relevant_intervals=intervals))
        if result: return result
    return None


def _validate_evidence_proposal(proposal, requirement, resume, contexts, profile, as_of):
    from .models import Evidence
    from .provenance import section_at, verified_level
    if proposal.level == "not_evidenced":
        if proposal.source_quote is not None:
            raise ValueError("Absence does not publish a positive quote")
        return Evidence(requirement_id=requirement.id, level="not_evidenced")
    if proposal.source_quote is None:
        raise ValueError("Evidence needs a source quote")
    spans = set()
    for context in contexts:
        try: spans.add(_quote_span(proposal.source_quote, context))
        except ValueError: continue
    if len(spans) != 1:
        raise ValueError("Ambiguous or unsupported evidence quote")
    quote, start, end = spans.pop()
    if resume.content[start:end] != quote:
        raise ValueError("Quote does not match saved source")
    if requirement.kind == "skill" and not any(contains_skill(quote, k) for k in requirement.alternatives or [requirement.canonical_key]):
        raise ValueError("Unsupported literal skill")
    level = verified_level(resume.content, start, end, requirement.canonical_key, proposal.level)
    intervals = []
    if requirement.kind == "tenure" and level == "demonstrated":
        intervals = _verified_intervals(quote, start, end, resume, profile, as_of)
        if not intervals: raise ValueError("Relevant tenure needs dated work provenance")
    return Evidence(requirement_id=requirement.id, level=level, source_quote=quote,
                    source_start=start, source_end=end, section=section_at(resume.content, start),
                    relevant_intervals=intervals)


def _assessment_round(requests, requirements, engine, deadline, as_of):
    """Validate claims before reconciling the provider's coverage metadata."""
    remaining = deadline - time.monotonic()
    if remaining <= 0: raise TimeoutError
    payload = dict(task="evidence_batch", requirements=[r.model_dump(mode="json") for r in requirements],
                   resumes=[request["payload"] for request in requests], schema=EvidenceBatchProposal.model_json_schema())
    def validate(response):
        wire = EvidenceBatchProposal.model_validate(response)
        records = {r.resume_id: r for r in wire.items}
        expected_resumes = {r["resume"].id for r in requests}
        if len(records) != len(wire.items) or not set(records) <= expected_resumes:
            raise ValueError("Duplicate or foreign resume IDs")
        outcomes = {}
        for request in requests:
            resume, profile = request["resume"], request["profile"]
            expected = set(request["payload"]["requirement_ids"])
            record = records.get(resume.id)
            if record is None:
                outcomes[resume.id] = ([], expected, "missing_assessment")
                continue
            if record.chunk_index != request["payload"]["chunk_index"]:
                raise ValueError("Wrong source chunk acknowledgment")
            by_id = {r.id: r for r in requirements}
            items = []
            seen = set()
            for proposal in record.items:
                if proposal.requirement_id not in expected or proposal.requirement_id in seen:
                    raise ValueError("Duplicate or foreign requirement IDs")
                seen.add(proposal.requirement_id)
                items.append(_validate_evidence_proposal(proposal, by_id[proposal.requirement_id], resume,
                                                        request["contexts"], profile, as_of))
            assessed, unresolved = set(record.assessed_requirement_ids), set(record.unresolved_requirement_ids)
            if len(assessed) != len(record.assessed_requirement_ids) or len(unresolved) != len(record.unresolved_requirement_ids) or assessed & unresolved or not (assessed | unresolved) <= expected:
                raise ValueError("Invalid requirement coverage")
            if seen - assessed:
                raise ValueError("Positive outcome cannot repair unsupported coverage")
            missing = expected - (seen & assessed)
            outcomes[resume.id] = (items, missing, "missing_assessment" if expected - (assessed | unresolved) or assessed - seen else "unresolved_evidence" if missing else None)
        return outcomes
    return _validated_chunk(payload,engine=engine,deadline=deadline,validate=validate)


def extract_evidence_batch(resumes: list[Resume], profiles: dict[str, ResumeProfile], requirements: list[Requirement], *, as_of: date, engine: Any, deadline: float) -> dict[str, EvidenceExtraction]:
    """Assess one supplied batch; source fallback covers all original chunks."""
    from .models import Evidence, EvidenceExtraction
    from .profiles import profile_version_key, validate_profile
    from .provenance import source_hash, section_at
    identifiers = [r.id for r in resumes]
    requirement_ids = [r.id for r in requirements]
    if len(identifiers) != len(set(identifiers)) or len(requirement_ids) != len(set(requirement_ids)):
        raise ValueError("Duplicate input IDs")
    if len(resumes) > 5: raise ValueError("Partition evidence into at most five resumes")
    by_id = {r.id: r for r in requirements}
    outputs = {}
    observations = {r.id: {} for r in resumes}
    unresolved = {r.id: set() for r in resumes}
    warnings = {r.id: set() for r in resumes}
    accepted_profiles = {}
    fallback = {}
    def result(resume, status, reason=None, items=None, pending=None):
        items = items or []
        return EvidenceExtraction(status=status, source_hash=source_hash(resume.content), extractor_version=ASSESSMENT_VERSION,
                                  warnings=[reason] if reason else sorted(warnings[resume.id]), items=items,
                                  assessed_requirement_ids=sorted({i.requirement_id for i in items}),
                                  unresolved_requirement_ids=sorted(pending or []))
    def observe(resume_id, outcome):
        items, missing, reason = outcome
        unresolved[resume_id].update(missing)
        if reason: warnings[resume_id].add(reason)
        for item in items: observations[resume_id].setdefault(item.requirement_id, []).append(item)
    try:
        profile_requests = []
        for resume in resumes:
            if resume.extraction_warnings or not resume.content or not requirements or len(requirements)>64:
                reason="rubric_limit" if len(requirements)>64 else "no_assessable_requirements" if not requirements else "source_incomplete"
                outputs[resume.id]=result(resume,"needs_review",reason,pending=requirement_ids)
                continue
            chunk_text(resume.content)  # Enforce source limits even when a profile is available.
            profile = profiles.get(resume.id)
            if profile and profile.status == "complete":
                validate_profile(profile, resume, profile_version_key(engine))
            else: profile = None
            accepted_profiles[resume.id] = profile
            pending = []
            for requirement in requirements:
                local = _local_evidence(resume,profile,requirement,as_of)
                if local is None: pending.append(requirement.id)
                else: observations[resume.id][requirement.id] = local
            if not pending: continue
            contexts = [TextChunk(f.source_start,f.source_end,f.source_quote) for f in profile.facts] if profile else []
            # No keyword filter: all activities/credentials/work context may support semantics.
            text = "\n".join(c.text for c in contexts)
            missing_literal = any(by_id[id].kind=="skill" for id in pending)
            if not contexts or len(text)>8000 or missing_literal:
                fallback[resume.id]=pending
                continue
            profile_requests.append(dict(resume=resume,profile=profile,contexts=contexts,payload=dict(
                resume_id=resume.id,profile_fingerprint=profile.profile_fingerprint,mode="profile",chunk_index=0,
                chunk_count=1,source_text=text, facts=[f.model_dump(mode="json", exclude={"source_quote"}) for f in profile.facts],requirement_ids=pending)))
        if profile_requests:
            outcomes = _assessment_round(profile_requests,requirements,engine,deadline,as_of)
            for request in profile_requests:
                id = request["resume"].id
                items, missing, reason = outcomes[id]
                absent = {i.requirement_id for i in items if i.level == "not_evidenced"}
                # Only an explicit absence with otherwise valid coverage triggers source escalation.
                if absent and not missing:
                    fallback[id]=sorted(absent)
                    items=[i for i in items if i.requirement_id not in absent]
                observe(id,(items,missing,reason))
        sources={id:chunk_text(next(r.content for r in resumes if r.id==id)) for id in fallback}
        for index in range(max((len(c) for c in sources.values()),default=0)):
            requests=[]
            for resume in resumes:
                if resume.id not in sources or index>=len(sources[resume.id]): continue
                chunk=sources[resume.id][index]
                requests.append(dict(resume=resume,profile=accepted_profiles[resume.id],contexts=[chunk],payload=dict(
                    resume_id=resume.id,mode="source",chunk_index=index,chunk_count=len(sources[resume.id]),
                    source_text=chunk.text,section_context=section_at(resume.content,chunk.start),
                    requirement_ids=fallback[resume.id])))
            outcomes=_assessment_round(requests,requirements,engine,deadline,as_of)
            for id,outcome in outcomes.items(): observe(id,outcome)
        for resume in resumes:
            if resume.id in outputs: continue
            missing=set(requirement_ids)-set(observations[resume.id])
            unresolved[resume.id].update(missing)
            if missing: warnings[resume.id].add("missing_assessment")
            items=[]
            for id,observed in observations[resume.id].items():
                if id in unresolved[resume.id]: continue
                if has_evidence_conflict({i.level for i in observed}):
                    unresolved[resume.id].add(id)
                    warnings[resume.id].add("unresolved_evidence")
                    continue
                positive=[i for i in observed if i.level!="not_evidenced"]
                distinct={}
                for item in positive:
                    span=(item.source_start,item.source_end)
                    if span in distinct and distinct[span].model_dump()!=item.model_dump():
                        raise ValueError("Conflicting classifications for identical evidence")
                    distinct[span]=item
                items.extend(distinct.values() if positive else [Evidence(requirement_id=id,level="not_evidenced")])
            outputs[resume.id]=result(resume,"needs_review" if unresolved[resume.id] else "complete",items=items,pending=unresolved[resume.id])
        return outputs
    except TimeoutError:
        return {r.id:result(r,"needs_review","deadline_exceeded",pending=requirement_ids) for r in resumes}
    except Exception:
        return {r.id:result(r,"failed","invalid_provider_response") for r in resumes}
