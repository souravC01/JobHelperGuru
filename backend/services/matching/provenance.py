"""Source rules shared by reusable profiles and job-specific evidence."""
import hashlib
import json
import re
from datetime import date
from .chunking import TextChunk

def _quote_span(quote: str, chunk: TextChunk) -> tuple[str, int, int]:
    # Borrowed source provenance rule: only whitespace can vary; persist exact text.
    pattern = r"\s+".join(re.escape(part) for part in quote.split())
    matches = list(re.finditer(pattern, chunk.text)) if pattern else []
    if len(matches) != 1:
        raise ValueError("Source quote must occur exactly once in the supplied chunk")
    match = matches[0]
    return chunk.text[match.start():match.end()], chunk.start + match.start(), chunk.start + match.end()


INSTRUCTION = re.compile(r"ignore\b.*\b(?:rubric|instructions?)|\bscore\s*\d+|\bsystem\s*prompt", re.I)
HEADINGS = re.compile(r"^\s*(skills(?: and tools)?|technical skills|work experience|professional experience|employment history|employment|work history|experience|projects?|personal projects?|education|academic background|coursework|courses|training|certifications?)\s*:?\s*$", re.I | re.M)


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
    if name in {"education", "academic background"}: return "education"
    if name in {"coursework", "courses", "training"}: return "coursework"
    if "certif" in name: return "credentials"
    return "work"


def verified_level(text, start, end, key, level):
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    quote = text[line_start:line_end if line_end != -1 else len(text)]
    if INSTRUCTION.search(quote):
        raise ValueError("Document instructions cannot supply evidence")
    if level == "demonstrated" and (quote.strip(" •-*\t\r\n").casefold() == key.casefold()
            or re.fullmatch(r"[\w+#./-]+(?:\s*[,|;]\s*[\w+#./-]+)+", quote.strip())):
        return "listed"
    # Retain the source branch's learning distinction, including machine learning.
    if re.search(r"\b(?:(?<!machine )(?<!deep )(?<!reinforcement )learning|studying|coursework|tutorial|beginner|plan to learn)\b", quote, re.I):
        return "learning"
    from .normalization import aliases_for_skill
    negative_skill = any(re.search(r"\b(?:no|not|without)\s+(?:any\s+)?" + re.escape(alias) + r"(?![\w+#])", quote, re.I) for alias in aliases_for_skill(key))
    if negative_skill or re.search(r"\b(?:never|lack(?:ing)?|no experience|not (?:use[ds]?|built|worked|implemented|proficient|familiar|experienced))\b", quote, re.I):
        return "contradicted"
    if section_at(text, start) in {"skills", "coursework"} and level == "demonstrated":
        return "listed" if section_at(text, start) == "skills" else "learning"
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
