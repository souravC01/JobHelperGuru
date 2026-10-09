import re

from backend.services.matching.normalization import (
    aliases_for_skill,
    canonicalize_skill,
)


def _contains_literal_skill(text: str, skill: str) -> bool:
    """
    Punctuation-aware skill matching.
    Handles exact skill boundaries for languages with punctuation (C++, C#, .NET, Node.js)
    without incorrectly matching substrings (e.g. C in C++, Java in JavaScript, SQL in NoSQL).
    """
    escaped = r"\s+".join(re.escape(word) for word in skill.split())

    # Prefix boundary:
    # If skill starts with a dot (like .NET), ensure it is not preceded by word, +, #, or dot
    if skill.startswith("."):
        prefix = r"(?<![\w+#.])"
    else:
        prefix = r"(?<![\w+#])"

    # Suffix boundary:
    # Ensure token is not immediately followed by word characters, +, or #
    suffix = r"(?![\w+#])"

    pattern = rf"{prefix}{escaped}{suffix}"
    return bool(re.search(pattern, text, re.IGNORECASE))


def contains_skill(text: str, skill: str) -> bool:
    """Match a skill or its explicit aliases with punctuation-aware boundaries."""
    if not text or not skill:
        return False
    clean_skill = skill.strip()
    if not clean_skill:
        return False
    return any(_contains_literal_skill(text, alias) for alias in aliases_for_skill(clean_skill))


def supports_extracted_skill(text: str, skill: str) -> bool:
    """Verify a named skill, explicit synonym, or clear shared-suffix testing list."""
    from backend.services.matching.normalization import matching_aliases_for_skill
    aliases = matching_aliases_for_skill(skill)
    if any(_contains_literal_skill(text, alias) for alias in aliases):
        return True
    # ponytail: explicit testing syntax only; related work outcomes are not skill claims.
    methods = {"manual", "automated", "functional", "regression", "integration", "performance", "accessibility", "unit", "api", "database", "ui", "end-to-end", "cross-browser"}
    method = "(?:" + "|".join(re.escape(m) for m in sorted(methods)) + ")"
    for alias in aliases:
        name = alias.casefold().removesuffix(" testing")
        if name not in methods or not alias.casefold().endswith(" testing"):
            continue
        pattern = r"(?<![\w+#])" + re.escape(name) + r"(?:\s*(?:,\s*(?:(?:and|or)\s+)?|(?:and|or)\s+|/\s*)" + method + r")*\s+(?:testing|tests?|test cases)\b"
        if re.search(pattern, text, re.I):
            return True
        for line in text.splitlines():
            heading = re.match(r"\s*(?:QA\s*&\s*)?Testing\s*:\s*([^.;]+)", line, re.I)
            if heading and any(part.strip().casefold() == name for part in re.split(r",|\||;|\band\b", heading[1], flags=re.I)):
                return True
    return False


def match_skills(text: str, target_skills: list[str]) -> tuple[list[str], list[str]]:
    """
    Matches target skills against text using punctuation-aware matching.
    Returns:
        (matched_skills, missing_skills)
    Results are returned in deterministic, stably-sorted order.
    """
    matched = []
    missing = []

    # Deduplicate while preserving order, then evaluate
    seen = set()
    deduped = []
    for s in target_skills:
        clean = s.strip()
        canonical = canonicalize_skill(clean)
        if clean and canonical not in seen:
            seen.add(canonical)
            deduped.append(clean)

    for skill in deduped:
        if contains_skill(text, skill):
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing
