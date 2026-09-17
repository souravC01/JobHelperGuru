import pytest


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("Go", "Golang"),
        ("AWS", "Amazon Web Services"),
        ("GCP", "Google Cloud Platform"),
        ("PostgreSQL", "Postgres"),
        ("Node.js", "NodeJS"),
        ("Kubernetes", "K8s"),
        ("C#", "C Sharp"),
    ],
)
def test_explicit_aliases_share_a_stable_canonical_key(left, right):
    from backend.services.matching.normalization import canonicalize_skill

    assert canonicalize_skill(left) == canonicalize_skill(right)


def test_aliases_do_not_merge_distinct_languages_or_unknown_terms():
    from backend.services.matching.normalization import canonicalize_skill

    assert canonicalize_skill("Java") != canonicalize_skill("JavaScript")
    assert canonicalize_skill("React") != canonicalize_skill("React Native")
    assert canonicalize_skill("Internal Platform") == "internal platform"


def test_matching_accepts_explicit_aliases_without_changing_requested_labels():
    from backend.services.skill_matching import match_skills

    matched, missing = match_skills(
        "Built services in Golang on Amazon Web Services with NodeJS and C Sharp.",
        ["Go", "AWS", "Node.js", "C#"],
    )

    assert matched == ["Go", "AWS", "Node.js", "C#"]
    assert missing == []
