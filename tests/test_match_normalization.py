def test_aliases_dedupe_without_losing_unknown_skill():
    from backend.services.matching.normalization import canonicalize_skill
    from backend.services.skill_matching import match_skills, contains_skill
    assert canonicalize_skill("Postgres") == canonicalize_skill("PostgreSQL")
    assert canonicalize_skill("NewVendorDB") == "newvendordb"
    assert match_skills("Postgres and NewVendorDB", ["PostgreSQL", "postgres", "NewVendorDB"]) == (["PostgreSQL", "NewVendorDB"], [])
    assert contains_skill("K8s, ReactJS and C Sharp", "Kubernetes")
    assert not contains_skill("JavaScript NoSQL C++", "Java")
    assert not contains_skill("JavaScript NoSQL C++", "SQL")
    assert not contains_skill("JavaScript NoSQL C++", "C")


def test_microservices_name_and_architecture_phrase_share_explicit_identity():
    from backend.services.matching.normalization import canonicalize_skill
    from backend.services.skill_matching import contains_skill
    assert canonicalize_skill('Microservices Architecture') == canonicalize_skill('Microservices')
    assert contains_skill('Skills: Microservices', 'Microservices Architecture')
    assert not contains_skill('Skills: Monolithic architecture', 'Microservices Architecture')
