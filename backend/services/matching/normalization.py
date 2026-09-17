"""Deterministic skill canonicalization and explicit alias lookup."""

from __future__ import annotations

CANONICAL_SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "go": ("Go", "Golang"),
    "aws": ("AWS", "Amazon Web Services"),
    "gcp": ("GCP", "Google Cloud Platform"),
    "postgresql": ("PostgreSQL", "Postgres"),
    "node.js": ("Node.js", "NodeJS"),
    "kubernetes": ("Kubernetes", "K8s"),
    "c#": ("C#", "C Sharp"),
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
