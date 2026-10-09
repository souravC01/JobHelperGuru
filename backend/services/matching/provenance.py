"""Source rules shared by reusable profiles and job-specific evidence."""
import hashlib
import json
import re
from datetime import date
from .chunking import TextChunk
from pydantic import Field, StrictInt, model_validator
from .models import MatchContract, NonEmptyString


class SourceReference(MatchContract):
    """New proposals cite lines; old stored facts still use exact source quotes."""
    source_line: StrictInt | None = Field(default=None, ge=1)
    source_end_line: StrictInt | None = Field(default=None, ge=1)
    source_quote: NonEmptyString | None = None

    @model_validator(mode="after")
    def validate_reference(self):
        if (self.source_line is None) == (self.source_quote is None):
            raise ValueError("Supply either source lines or a legacy quote")
        if self.source_end_line is not None and (self.source_line is None or self.source_end_line < self.source_line):
            raise ValueError("Invalid source line range")
        return self


def proposal_span(proposal: SourceReference, chunk: TextChunk, *, skill: str | None = None) -> tuple[str, int, int]:
    if proposal.source_line is None:
        return _quote_span(proposal.source_quote, chunk)
    lines = chunk.text.splitlines(keepends=True)
    last = proposal.source_end_line or proposal.source_line
    if last > len(lines):
        raise ValueError("Source line outside supplied chunk")
    start = sum(map(len, lines[:proposal.source_line-1]))
    quote = "".join(lines[proposal.source_line-1:last]).rstrip("\r\n")
    if not quote.strip():
        raise ValueError("Empty source line")
    if skill:
        from backend.services.skill_matching import supports_extracted_skill
        def continuation(line):
            return bool(line.strip()) and not HEADINGS.fullmatch(line.strip()) and not re.match(r"\s*(?:[•●*\-]|\d+[.)])\s", line)
        if not supports_extracted_skill(quote, skill):
            # Recover only an adjacent wrapped line; never jump to another bullet or section.
            candidates = []
            if proposal.source_line > 1 and continuation(lines[proposal.source_line-1]) and lines[proposal.source_line-2].strip() and not HEADINGS.fullmatch(lines[proposal.source_line-2].strip()):
                candidates.append(proposal.model_copy(update={"source_line": proposal.source_line-1, "source_end_line": last}))
            if last < len(lines) and continuation(lines[last]):
                candidates.append(proposal.model_copy(update={"source_end_line": last+1}))
            supported = [span for candidate in candidates for span in [proposal_span(candidate, chunk)]
                         if supports_extracted_skill(span[0], skill)]
            if len(supported) == 1:
                quote, absolute_start, absolute_end = supported[0]
                start = absolute_start-chunk.start
        if supports_extracted_skill(quote, skill):
            # Both direct and recovered references can start within a wrapped sentence.
            end = start + len(quote)
            prefix_lines = chunk.text[:start].splitlines(keepends=True)
            while prefix_lines and continuation(quote.splitlines()[0]):
                previous = prefix_lines[-1]
                if not previous.strip() or HEADINGS.fullmatch(previous.strip()) or previous.rstrip().endswith(('.', '!', '?', ':')):
                    break
                prefix_lines.pop()
                start -= len(previous)
                quote = chunk.text[start:end]
    return quote, chunk.start + start, chunk.start + start + len(quote)

def _quote_span(quote: str, chunk: TextChunk) -> tuple[str, int, int]:
    # Cache reconstruction supplies the exact stored span, including indentation.
    if quote == chunk.text and quote.strip():
        return quote, chunk.start, chunk.end
    # Borrowed source provenance rule: only whitespace can vary; persist exact text.
    pattern = r"\s+".join(re.escape(part) for part in quote.split())
    matches = list(re.finditer(pattern, chunk.text)) if pattern else []
    if len(matches) != 1:
        raise ValueError("Source quote must occur exactly once in the supplied chunk")
    match = matches[0]
    return chunk.text[match.start():match.end()], chunk.start + match.start(), chunk.start + match.end()


INSTRUCTION = re.compile(r"ignore\b.*\b(?:rubric|instructions?)|\bscore\s*\d+|\bsystem\s*prompt", re.I)
HEADINGS = re.compile(r"^\s*(skills(?: and tools)?|technical skills(?: and tools)?|work experience|professional experience|employment history|employment|work history|experience|projects?|personal projects?|education(?: & certificates)?|academic background|coursework|courses|training|certifications?)\s*:?\s*$", re.I | re.M)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def source_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def section_at(text, start):
    headings = [h for h in HEADINGS.finditer(text) if h.start() <= start]
    if not headings:
        return "unknown"
    name = headings[-1][1].lower()
    if "skill" in name: return "skills"
    if "project" in name: return "projects"
    if name.startswith("education") or name == "academic background": return "education"
    if name in {"coursework", "courses", "training"}: return "coursework"
    if "certif" in name: return "credentials"
    return "work"


def verified_level(text, start, end, key, level):
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    quote = text[line_start:line_end if line_end != -1 else len(text)]
    if INSTRUCTION.search(quote):
        raise ValueError("Document instructions cannot supply evidence")
    from .normalization import matching_aliases_for_skill as aliases_for_skill
    from backend.services.skill_matching import supports_extracted_skill
    negative_skill = any(re.search(r"\b(?:no|not|without)\s+(?:any\s+)?" + re.escape(alias) + r"(?![\w+#])", quote, re.I) for alias in aliases_for_skill(key))
    # Use the same shared-suffix interpretation as skill validation for negated lists.
    negative_skill |= any(supports_extracted_skill(m[1], key) for m in re.finditer(
        r"\b(?:no|not|without)\s+(?:any\s+)?([^.;:\n]+?\b(?:testing|tests?|test cases))\b", quote, re.I)
        if not re.search(r"\b(?:but|however)\b", m[1], re.I))
    if level == "contradicted" or negative_skill or re.search(r"\b(?:never|lack(?:ing)?|no experience|not (?:use[ds]?|built|worked|implemented|proficient|familiar|experienced))\b", quote, re.I):
        return "contradicted"
    # Source context takes precedence over a provider's positive presence level.
    section = section_at(text, start)
    if re.search(r"\b(?:(?<!machine )(?<!deep )(?<!reinforcement )learning|studying|coursework|tutorial|beginner|plan to learn)\b", quote, re.I) or (section == "coursework" and level in {"listed", "demonstrated"}):
        return "learning"
    if level == "demonstrated" and (section == "skills" or quote.strip(" •-*\t\r\n").casefold() == key.casefold()
            or re.fullmatch(r"[\w+#./-]+(?:\s*[,|;]\s*[\w+#./-]+)+", quote.strip())):
        return "listed"
    return level


def date_ranges(text):
    # Adapted from pinned source _intervals; ongoing dates remain job independent.
    month_names = {name: i for i, name in enumerate(("jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"),1)}
    def parse(value):
        if re.fullmatch(r"\d{4}-\d{2}", value):
            year, month = value.split("-"); return date(int(year), int(month), 1)
        month, year = value.split(); return date(int(year), month_names[month.lower()[:3]], 1)
    token = r"(?:\d{4}-\d{2}|[A-Za-z]+\s+\d{4})"
    result = []
    for m in re.finditer(rf"\b({token})\s*[-–—]\s*({token}|present|current)\b",text,re.I):
        try:
            start=parse(m[1]); end=None if m[2].lower() in {"present","current"} else parse(m[2])
            if end is None or start <= end: result.append((start,end))
        except (KeyError,ValueError): pass
    return result


def work_span(text, start, end):
    return section_at(text, start) == "work" and all(
        section_at(text, h.end()-1) == "work" for h in HEADINGS.finditer(text)
        if start < h.start() < end)
