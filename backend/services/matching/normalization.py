"""Deterministic skill canonicalization and explicit alias lookup."""

from __future__ import annotations

import re

CANONICAL_SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "microservices": ("Microservices", "Microservices Architecture"),
    "oop": ("OOP", "OOPS", "Object-Oriented Programming", "Object Oriented Programming"),
    "javascript": ("JavaScript", "JS"),
    "go": ("Go", "Golang"),
    "aws": ("AWS", "Amazon Web Services"),
    "gcp": ("GCP", "Google Cloud Platform"),
    "postgresql": ("PostgreSQL", "Postgres"),
    "node.js": ("Node.js", "NodeJS"),
    "kubernetes": ("Kubernetes", "K8s"),
    "c#": ("C#", "C Sharp"),
    "react": ("React", "React.js", "ReactJS"),
    "rest apis": ("REST APIs", "RESTful APIs"),
    "test automation": (
        "Test Automation", "Automated Tests", "Automated Testing",
        "Automated Test Cases",
    ),
}

SKILL_ALIASES = {
    alias.casefold(): canonical
    for canonical, aliases in CANONICAL_SKILL_ALIASES.items()
    for alias in aliases
}


def canonicalize_skill(value: str) -> str:
    """Return a stable key while leaving unknown technologies literal."""
    literal = value.strip().casefold()
    return SKILL_ALIASES.get(literal, literal)


def aliases_for_skill(value: str) -> tuple[str, ...]:
    """Return the explicit spellings that are equivalent to ``value``."""
    canonical = canonicalize_skill(value)
    return CANONICAL_SKILL_ALIASES.get(canonical, (value.strip(),))


# Comparison vocabulary is separate from extraction cache identity: new matching
# rules can use old verified facts without sending resumes to the provider again.
MATCHING_ALIASES = {
    "ci/cd": ("CI/CD", "CI/CD pipelines", "continuous integration / continuous delivery", "continuous integration and continuous delivery"),
    "agile": ("Agile", "Agile software development practices"),
    "sdlc": ("SDLC", "software development life cycle", "software development lifecycle"),
    "bdd": ("BDD", "behavior driven development", "behaviour driven development", "behavior-driven development"),
    "test case design": ("test case design", "test case development"),
    "programming languages": ("programming languages", "programming language"),
    "test automation frameworks": ("test automation frameworks", "test automation framework"),
    "cloud platforms": ("cloud platforms", "cloud platform"),
    "selenium": ("Selenium", "Selenium WebDriver"),
}

# Directional membership, never equivalence between individual tools.
SKILL_CATEGORY_MEMBERS = {
    "programming languages": frozenset({"python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin"}),
    "test automation frameworks": frozenset({"playwright", "cypress", "selenium", "webdriverio", "pytest", "junit", "testng", "robot framework"}),
    "cloud platforms": frozenset({"aws", "gcp", "azure", "microsoft azure"}),
}


def skill_components(value: str) -> tuple[str, ...]:
    key = canonicalize_match_skill(value)
    # Only reviewed compound labels; slash is not a universal AND operator (CI/CD).
    return {"agile/scrum": ("agile", "scrum"), "sdlc/stlc": ("sdlc", "stlc")}.get(
        re.sub(r"\s*/\s*", "/", key), (key,))


def canonicalize_match_skill(value: str) -> str:
    literal = canonicalize_skill(" ".join(value.split()))
    expansion = re.fullmatch(r"([^()]+)\s*\(([^()]+)\)", literal)
    if expansion:
        short, long = (canonicalize_match_skill(part) for part in expansion.groups())
        if short == long:
            return short
    return next((key for key, aliases in MATCHING_ALIASES.items()
                 if literal in {a.casefold() for a in aliases}), literal)


def matching_aliases_for_skill(value: str) -> tuple[str, ...]:
    key = canonicalize_match_skill(value)
    return MATCHING_ALIASES.get(key, aliases_for_skill(value))
