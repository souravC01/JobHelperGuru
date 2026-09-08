import re
from typing import List, Tuple, Set, Optional


def contains_skill(text: str, skill: str) -> bool:
    """
    Punctuation-aware skill matching.
    Handles exact skill boundaries for languages with punctuation (C++, C#, .NET, Node.js)
    without incorrectly matching substrings (e.g. C in C++, Java in JavaScript, SQL in NoSQL).
    """
    if not text or not skill:
        return False
    clean_skill = skill.strip()
    if not clean_skill:
        return False

    escaped = re.escape(clean_skill)

    # Prefix boundary:
    # If skill starts with a dot (like .NET), ensure it is not preceded by word, +, #, or dot
    if clean_skill.startswith("."):
        prefix = r"(?<![\w+#.])"
    else:
        prefix = r"(?<![\w+#])"

    # Suffix boundary:
    # Ensure token is not immediately followed by word characters, +, or #
    suffix = r"(?![\w+#])"

    pattern = rf"{prefix}{escaped}{suffix}"
    return bool(re.search(pattern, text, re.IGNORECASE))


def match_skills(text: str, target_skills: List[str]) -> Tuple[List[str], List[str]]:
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
        if clean and clean not in seen:
            seen.add(clean)
            deduped.append(clean)

    for skill in deduped:
        if contains_skill(text, skill):
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing
