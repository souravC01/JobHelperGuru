"""Synthetic providers exercise cache behavior without external requests."""
from collections import Counter
from datetime import date
from threading import Lock
import time

import pytest
from backend.storage import StorageService
from tests.test_match_profiles import fact

JOB = "Responsibilities:\nMaintain service availability."
QUOTE = "Cut outages by deploying redundant workers."
AS_OF = date(2026, 9, 30)


class Provider:
    api_base_url = "https://provider.example/v1"
    model_name = "test-model"
    api_key = "secret-not-an-identity"
    def __init__(self):
        self.calls = []
        self.incomplete = set()
        self.hook = None
        self.active = self.peak = 0
        self.lock = Lock()
    def extract_match_chunk(self, payload, *, timeout):
        assert timeout > 0
        with self.lock:
            self.calls.append(payload)
            self.active += 1
            self.peak = max(self.peak, self.active)
        try:
            if self.hook: self.hook(payload)
            task = payload["task"]
            if task == "requirements":
                quote = payload["source_text"].splitlines()[-1]
                return dict(chunk_index=payload["chunk_index"], complete=True, items=[dict(
                    category="responsibilities",kind="semantic",canonical_key=quote,
                    alternatives=[],source_quote=quote,required_months=None)])
            if task == "resume_profile":
                items = [fact(QUOTE,"reliability","activity")] if QUOTE in payload["source_text"] else []
                return dict(chunk_index=payload["chunk_index"],complete=True,items=items)
            assert task == "evidence_batch"
            records=[]
            for r in payload["resumes"]:
                ids=r["requirement_ids"]
                if r["resume_id"] in self.incomplete: continue
                records.append(dict(resume_id=r["resume_id"],chunk_index=r["chunk_index"],
                    assessed_requirement_ids=ids,unresolved_requirement_ids=[],items=[dict(
                        requirement_id=id,level="demonstrated" if QUOTE in r["source_text"] else "not_evidenced",
                        source_quote=QUOTE if QUOTE in r["source_text"] else None) for id in ids]))
            return dict(items=records)
        finally:
            with self.lock: self.active -= 1
    def counts(self): return Counter(c["task"] for c in self.calls)


@pytest.fixture
def setup(tmp_path):
    storage=StorageService(str(tmp_path/"pipeline.db"),force_sqlite=True)
    r=storage.add_resume("Resume", "Projects:\n"+QUOTE, user_id="u")
    yield storage,r,Provider()
    storage.close()


def run(storage, resumes, engine, **kwargs):
    from backend.services.matching.pipeline import evaluate_resumes
    return evaluate_resumes(JOB,resumes,user_id=kwargs.pop("user_id","u"),as_of=kwargs.pop("as_of",AS_OF),
                            engine=engine,storage=storage,**kwargs)


def test_warm_comparison_zero_calls_same_ids(setup):
    s,r,p=setup
    cold=run(s,[r],p); p.calls.clear()
    warm=run(s,[r],p)
    assert cold.comparison_complete and warm.model_dump()==cold.model_dump()
    assert p.calls==[] and warm.evaluations[0].evaluation_id


def test_partial_cache_hit_reuses_frozen_rubric(setup):
    s,r,p=setup
    old=run(s,[r],p).evaluations[0]; p.calls.clear()
    new=s.add_resume("New",r.content,user_id="u")
    mixed=run(s,[new,r],p)
    assert mixed.comparison_complete and len({e.rubric_fingerprint for e in mixed.evaluations})==1
    assert next(e for e in mixed.evaluations if e.resume_id==r.id).evaluation_id==old.evaluation_id
    assert p.counts()=={"resume_profile":1,"evidence_batch":1}
    assert [x["resume_id"] for x in p.calls[-1]["resumes"]]==[new.id]
    p.calls.clear()
    subset=run(s,[new],p)
    assert subset.evaluations[0].rank==1 and p.calls==[]


@pytest.mark.parametrize("change",["endpoint","model","jd","assessment","profile"])
def test_provider_endpoint_model_and_versions_invalidate(setup,monkeypatch,change):
    from backend.services.matching import extraction,profiles
    s,r,p=setup; old=run(s,[r],p); p.calls.clear()
    if change=="endpoint": p.api_base_url += "/new"
    elif change=="model": p.model_name="new-model"
    elif change=="jd": monkeypatch.setattr(extraction,"EXTRACTOR_VERSION","jd-new")
    elif change=="assessment": monkeypatch.setattr(extraction,"ASSESSMENT_VERSION","assessment-new")
    else: monkeypatch.setattr(profiles,"PROFILE_EXTRACTOR_VERSION","profile-new")
    new=run(s,[r],p)
    assert new.comparison_complete and new.evaluations[0].evaluation_id!=old.evaluations[0].evaluation_id
    assert p.counts()["evidence_batch"]==1
    assert p.counts()["resume_profile"]==(change in {"endpoint","model","profile"})


def test_users_cannot_share_rubric_or_evidence(setup):
    s,r,p=setup; run(s,[r],p); p.calls.clear()
    with pytest.raises(ValueError): run(s,[r],p,user_id="other")
    assert p.calls==[]
    other=s.add_resume("Other",r.content,user_id="other")
    assert run(s,[other],p,user_id="other").comparison_complete
    assert p.counts()=={"requirements":1,"resume_profile":1,"evidence_batch":1}


def test_resume_edit_or_delete_invalidates(setup):
    s,r,p=setup; run(s,[r],p)
    s.update_resume(r.id,content="Projects:\nOther activity.",user_id="u")
    with s._get_cursor() as c:
        c.execute("SELECT COUNT(*) FROM matching_snapshots"); assert c.fetchone()[0]==0
    with pytest.raises(ValueError): run(s,[r],p)
    edited=s.get_resume(r.id,user_id="u"); assert run(s,[edited],p).comparison_complete
    s.delete_resume(r.id,user_id="u")
    with s._get_cursor() as c:
        c.execute("SELECT COUNT(*) FROM matching_snapshots"); assert c.fetchone()[0]==0


def test_deadline_result_not_scored_or_cached(setup):
    s,r,p=setup
    p.hook=lambda payload: time.sleep(.025) if payload["task"]=="evidence_batch" else None
    result=run(s,[r],p,deadline_seconds=.02)
    assert not result.comparison_complete
    assert result.evaluations[0].raw_score is None and "deadline_exceeded" in result.evaluations[0].reason_codes
    with s._get_cursor() as c:
        c.execute("SELECT COUNT(*) FROM matching_snapshots"); assert c.fetchone()[0]==0


def test_partition_respects_five_docs_and_forty_thousand_chars(setup):
    s,r,p=setup
    resumes=[r]+[s.add_resume(str(i),r.content,user_id="u") for i in range(11)]
    p.hook=lambda payload: time.sleep(.015) if payload["task"]=="evidence_batch" else None
    result=run(s,list(reversed(resumes)),p)
    assert result.comparison_complete
    calls=[c for c in p.calls if c["task"]=="evidence_batch"]
    assert len(calls)==3 and p.peak<=2
    assert all(len(c["resumes"])<=5 and sum(len(r["source_text"]) for r in c["resumes"])<=40000 for c in calls)
    assert sorted(r["resume_id"] for c in calls for r in c["resumes"])==sorted(r.id for r in resumes)


def test_incomplete_batch_has_no_winner(setup):
    s,r,p=setup; run(s,[r],p)
    new=s.add_resume("New",r.content,user_id="u"); p.incomplete.add(new.id)
    result=run(s,[r,new],p)
    assert not result.comparison_complete and all(e.rank is None and not e.is_top_match for e in result.evaluations)
    assert next(e for e in result.evaluations if e.resume_id==r.id).raw_score==100


@pytest.mark.parametrize("table",["matching_snapshots","matching_rubrics"])
def test_invalid_cached_json_recomputed_safely(setup,table):
    s,r,p=setup; run(s,[r],p); p.calls.clear()
    with s._get_cursor() as c: c.execute(f"UPDATE {table} SET payload_json = ?", ('{"bad":true}',))
    assert run(s,[r],p).comparison_complete
    assert p.counts()["evidence_batch"]==1 and p.counts()["resume_profile"]==0
    assert p.counts()["requirements"]==(table=="matching_rubrics")


def test_scorer_change_recomputes_without_provider_calls(setup,monkeypatch):
    from backend.services.matching import scoring
    from decimal import Decimal
    s,r,p=setup; old=run(s,[r],p); p.calls.clear()
    original=scoring.calculate_score
    def changed(*args,**kwargs):
        score=original(*args,**kwargs)
        return score.model_copy(update={"raw_score":Decimal("75.00"),"match_score":75})
    monkeypatch.setattr(scoring,"SCORER_VERSION","score-new")
    monkeypatch.setattr(scoring,"calculate_score",changed)
    result=run(s,[r],p)
    assert result.evaluations[0].raw_score==75 and result.evaluations[0].scorer_version=="score-new"
    assert result.evaluations[0].evaluation_id==old.evaluations[0].evaluation_id and p.calls==[]
    with s._get_cursor() as c:
        c.execute("SELECT payload_json FROM matching_snapshots")
        assert 'score-new' in c.fetchone()[0]


def test_new_job_reuses_profiles_but_assesses_new_requirements(setup):
    from backend.services.matching.pipeline import evaluate_resumes
    s,r,p=setup; run(s,[r],p); p.calls.clear()
    result=evaluate_resumes("Responsibilities:\nPrevent service outages.",[r],user_id="u",as_of=AS_OF,engine=p,storage=s)
    assert result.comparison_complete and p.counts()=={"requirements":1,"evidence_batch":1}


def test_changed_resume_only_reextracts_changed_profile(setup):
    s,r,p=setup; b=s.add_resume("B",r.content,user_id="u"); run(s,[r,b],p); p.calls.clear()
    b=s.update_resume(b.id,content=b.content+"\nMore context.",user_id="u")
    assert run(s,[r,b],p).comparison_complete
    assert p.counts()=={"resume_profile":1,"evidence_batch":1}


def test_profile_version_invalidates_dependent_assessment(setup,monkeypatch):
    test_provider_endpoint_model_and_versions_invalidate(setup,monkeypatch,"profile")


def test_fresh_and_date_change_reuse_profile_and_rubric(setup):
    s,r,p=setup; run(s,[r],p); p.calls.clear()
    p.api_key="changed-secret"
    assert run(s,[r],p).comparison_complete and p.calls==[]
    assert run(s,[r],p,fresh=True).comparison_complete and p.counts()=={"evidence_batch":1}
    p.calls.clear()
    assert run(s,[r],p,as_of=date(2026,10,1)).comparison_complete and p.counts()=={"evidence_batch":1}


def test_edit_during_assessment_is_not_published(setup):
    s,r,p=setup
    p.hook=lambda payload: s.update_resume(r.id,content="Edited",user_id="u") if payload["task"]=="evidence_batch" else None
    result=run(s,[r],p)
    assert not result.comparison_complete and result.evaluations[0].raw_score is None
    with s._get_cursor() as c:
        c.execute("SELECT COUNT(*) FROM matching_snapshots"); assert c.fetchone()[0]==0


def test_cached_provenance_tampering_reassesses(setup):
    import json
    s,r,p=setup; run(s,[r],p); p.calls.clear()
    with s._get_cursor() as c:
        c.execute("SELECT payload_json FROM matching_snapshots"); data=json.loads(c.fetchone()[0])
        data["requirement_results"][0]["evidence"][0]["source_quote"]="X"*len(QUOTE)
        c.execute("UPDATE matching_snapshots SET payload_json=?",(json.dumps(data),))
    assert run(s,[r],p).comparison_complete and p.counts()=={"evidence_batch":1}


def test_logs_contain_call_types_durations_and_reasons_without_sources(setup,caplog):
    import logging
    s,r,p=setup
    with caplog.at_level(logging.INFO): assert run(s,[r],p).comparison_complete
    text=caplog.text
    assert all(task in text for task in ["resume_profile","requirements","evidence_batch"])
    assert "duration" in text and "reason" in text
    assert QUOTE not in text and JOB not in text and p.api_key not in text


def test_deadline_after_cached_read_never_enters_scorer(setup,monkeypatch):
    from backend.services.matching import pipeline,scoring
    s,r,p=setup; run(s,[r],p); p.calls.clear()
    clock=[0.0]; monkeypatch.setattr(pipeline.time,"monotonic",lambda:clock[0])
    original=s.get_matching_snapshot
    def late(**kwargs):
        result=original(**kwargs); clock[0]=301; return result
    monkeypatch.setattr(s,"get_matching_snapshot",late)
    calls=[]; original_score=scoring.calculate_score
    def score(*args,**kwargs): calls.append(1); return original_score(*args,**kwargs)
    monkeypatch.setattr(scoring,"calculate_score",score)
    result=run(s,[r],p)
    assert not result.comparison_complete and calls==[] and p.calls==[]


def test_edit_after_snapshot_save_cannot_publish_old_score(setup,monkeypatch):
    s,r,p=setup
    original=s.save_matching_snapshot
    def edit(**kwargs):
        original(**kwargs); s.update_resume(r.id,content="Edited after saving",user_id="u")
    monkeypatch.setattr(s,"save_matching_snapshot",edit)
    result=run(s,[r],p)
    assert not result.comparison_complete and result.evaluations[0].raw_score is None


def test_simultaneous_cold_requests_share_winning_rubric(setup):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    s,r,p=setup; barrier=Barrier(2)
    class DifferentInterpretation(Provider):
        def __init__(self,key): super().__init__(); self.key=key
        def extract_match_chunk(self,payload,*,timeout):
            if payload["task"]=="requirements": barrier.wait(timeout=5)
            result=super().extract_match_chunk(payload,timeout=timeout)
            if payload["task"]=="requirements": result["items"][0]["canonical_key"]=self.key
            return result
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda provider:run(s,[r],provider),[DifferentInterpretation("availability"),DifferentInterpretation("reliability")]))
    assert all(result.comparison_complete for result in results)
    a,b=[result.evaluations[0] for result in results]
    assert a.rubric_fingerprint==b.rubric_fingerprint and a.requirement_results==b.requirement_results


def test_five_prepared_resumes_one_semantic_call(setup):
    from tests.test_match_profiles import build
    s,r,p=setup; resumes=[r]+[s.add_resume(str(i),r.content,user_id="u") for i in range(4)]
    for resume in resumes: assert build(resume,p,s).status=="complete"
    p.calls.clear()
    assert run(s,resumes,p).comparison_complete and p.counts()=={"requirements":1,"evidence_batch":1}


def test_long_source_fallback_processes_all_chunks_within_batch_bounds(setup):
    s,r,p=setup
    resumes=[s.add_resume(str(i),"Projects:\n"+"Context.\n"*1100+QUOTE,user_id="u") for i in range(6)]
    assert run(s,resumes,p).comparison_complete
    calls=[c for c in p.calls if c["task"]=="evidence_batch"]
    for c in calls:
        assert len(c["resumes"])<=5 and sum(len(r["source_text"]) for r in c["resumes"])<=40000
    # Make profiles deliberately incomplete in fact coverage while source analysis remains complete.
    with s._get_cursor() as c: c.execute("DELETE FROM resume_profiles")
    class EmptyProfiles(Provider):
        def extract_match_chunk(self,payload,*,timeout):
            result=super().extract_match_chunk(payload,timeout=timeout)
            if payload["task"]=="resume_profile": result["items"]=[]
            return result
    p=EmptyProfiles(); assert run(s,resumes,p,fresh=True).comparison_complete
    calls=[c for c in p.calls if c["task"]=="evidence_batch"]
    assert all(r["mode"]=="source" for c in calls for r in c["resumes"])
    for resume in resumes:
        indices={r["chunk_index"] for c in calls for r in c["resumes"] if r["resume_id"]==resume.id}
        assert indices=={0,1}
    assert all(sum(len(r["source_text"]) for r in c["resumes"])<=40000 for c in calls)


def test_alias_version_change_invalidates_extraction_and_assessment(setup,monkeypatch):
    from backend.services.matching.normalization import CANONICAL_SKILL_ALIASES
    s,r,p=setup; old=run(s,[r],p); p.calls.clear()
    monkeypatch.setitem(CANONICAL_SKILL_ALIASES,"new-alias",("NewAlias",))
    result=run(s,[r],p)
    assert result.comparison_complete and result.evaluations[0].evaluation_id!=old.evaluations[0].evaluation_id
    assert p.counts()=={"requirements":1,"resume_profile":1,"evidence_batch":1}


def test_local_skills_credentials_and_tenure_roundtrip_without_assessment(tmp_path):
    from backend.services.matching.pipeline import evaluate_resumes
    from tests.test_match_extraction import proposal
    work="Jan 2024 - Jan 2025\nBuilt Python services."
    degree="Bachelor of Computer Science."
    jd="Required: Python.\nRequired: 1 year Python experience.\nBachelor degree required."
    class LocalProvider(Provider):
        def extract_match_chunk(self,payload,*,timeout):
            self.calls.append(payload)
            assert payload["task"]!="evidence_batch"
            items=[proposal("Required: Python.","python"),
                   proposal("Required: 1 year Python experience.","python","relevant_experience","tenure",months=12),
                   proposal("Bachelor degree required.","bachelor",kind="credential")] if payload["task"]=="requirements" else [
                   fact("Skills:\nPython","python",level="listed"),fact(work,"python","employment"),fact(degree,"bachelor","credential")]
            return dict(chunk_index=payload["chunk_index"],complete=True,items=items)
    s=StorageService(str(tmp_path/"local.db"),force_sqlite=True)
    r=s.add_resume("R","Skills:\nPython\nWork Experience:\n"+work+"\nEducation:\n"+degree,user_id="u")
    p=LocalProvider()
    cold=evaluate_resumes(jd,[r],user_id="u",as_of=AS_OF,engine=p,storage=s)
    assert cold.comparison_complete; p.calls.clear()
    warm=evaluate_resumes(jd,[r],user_id="u",as_of=AS_OF,engine=p,storage=s)
    assert warm.model_dump()==cold.model_dump() and p.calls==[]
    s.close()


@pytest.mark.parametrize("case",["duplicate","empty_job","long_job","negative_deadline","nan_deadline"])
def test_invalid_inputs_make_no_provider_calls(setup,case):
    from backend.services.matching.pipeline import evaluate_resumes
    s,r,p=setup
    kwargs=dict(job_text=JOB,resumes=[r],user_id="u",as_of=AS_OF,engine=p,storage=s)
    if case=="duplicate": kwargs["resumes"]=[r,r]
    elif case=="empty_job": kwargs["job_text"]=" "
    elif case=="long_job": kwargs["job_text"]="X"*100001
    elif case=="negative_deadline": kwargs["deadline_seconds"]=-1
    else: kwargs["deadline_seconds"]=float("nan")
    with pytest.raises(ValueError): evaluate_resumes(**kwargs)
    assert p.calls==[]
