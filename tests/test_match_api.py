from datetime import date
from unittest.mock import Mock

import pytest
from backend import main
from tests.test_match_pipeline import Provider, JOB, QUOTE

JOB = JOB.replace("Required:", "Required skills for this software engineering position:")


@pytest.fixture
def setup(two_users,monkeypatch):
    client,a,b=two_users
    monkeypatch.setenv("MATCHING_V2_ENABLED","true")
    p=Provider(); monkeypatch.setattr(main,"get_ai_engine",lambda **kw:p)
    r=client.post("/api/resumes",headers=a,json={"name":"Resume","content":"Projects:\n"+QUOTE}).json()
    return client,a,b,r,p


def evaluate(client,headers,ids,job=JOB,**extra):
    return client.post("/api/resumes/evaluate",headers=headers,json={"job_text":job,"resume_ids":ids,**extra})


def test_unresolved_profile_is_visible_cached_and_never_scored(setup, monkeypatch):
    client,a,b,r,p=setup
    original=p.extract_match_chunk
    def extract(payload, *, timeout):
        response=original(payload,timeout=timeout)
        if payload['task']=='resume_profile':
            response['items'].append(dict(kind='skill',canonical_key='InventedTool',level='listed',source_line=2))
        return response
    monkeypatch.setattr(p,'extract_match_chunk',extract)
    empty=client.get(f'/api/resumes/{r["id"]}/profile',headers=a)
    assert empty.status_code==200 and empty.json()['status']=='not_prepared' and not p.calls
    first=client.post(f'/api/resumes/{r["id"]}/profile',headers=a)
    assert first.status_code==200 and first.json()['status']=='needs_review'
    assert first.json()['unresolved_skills']==['inventedtool']
    assert client.get(f'/api/resumes/{r["id"]}/profile',headers=a).json()==first.json()
    assert client.get(f'/api/resumes/{r["id"]}/profile',headers=b).status_code==404
    assert client.post(f'/api/resumes/{r["id"]}/profile',headers=a).json()==first.json()
    assert p.counts()=={'resume_profile':1}
    result=evaluate(client,a,[r['id']])
    assert result.status_code==200
    evaluation=result.json()['evaluations'][0]
    assert evaluation['raw_score'] is None and evaluation['rank'] is None
    assert evaluation['reason_codes']==['unresolved_skill_claims']
    assert p.counts()=={'resume_profile':1,'requirements':1}


def test_flag_off_preserves_legacy(setup,monkeypatch):
    client,a,b,r,p=setup; monkeypatch.delenv("MATCHING_V2_ENABLED")
    p.rank_resumes=Mock(return_value=[])
    assert client.get("/api/features",headers=a).json()=={"matching_v2_enabled":False}
    assert evaluate(client,a,[r["id"]]).status_code==404
    assert client.post(f'/api/resumes/{r["id"]}/profile',headers=a).status_code==404
    old=client.post("/api/resumes/match",headers=a,json={"job":{"required_skills":["Python"]}})
    assert old.status_code==200 and isinstance(old.json(),list) and p.calls==[]


@pytest.mark.parametrize("route",["features","evaluate","profile"])
def test_new_endpoints_require_auth(setup,route):
    client,a,b,r,p=setup
    if route=="features": response=client.get("/api/features")
    elif route=="evaluate": response=evaluate(client,{},[r["id"]])
    else: response=client.post(f'/api/resumes/{r["id"]}/profile')
    assert response.status_code==401 and p.calls==[]


def test_foreign_duplicate_and_unknown_resume_ids_rejected(setup):
    client,a,b,r,p=setup
    assert evaluate(client,b,[r["id"]]).status_code==404
    assert evaluate(client,a,[r["id"],r["id"]]).status_code==400
    assert evaluate(client,a,["missing"]).status_code==404
    assert evaluate(client,a,[]).status_code==400
    assert client.post(f'/api/resumes/{r["id"]}/profile',headers=b).status_code==404
    assert client.post('/api/resumes/missing/profile',headers=a).status_code==404
    assert p.calls==[]


@pytest.mark.parametrize("job",["","  ","X"*100001],ids=["empty","whitespace","oversized"])
def test_empty_or_oversized_job_rejected(setup,job):
    client,a,b,r,p=setup
    assert evaluate(client,a,[r["id"]],job=job).status_code==400 and p.calls==[]


@pytest.mark.parametrize("field,value",[("as_of","2025-01-01"),("weights",{}),("rubric",{}),("resumes",[]),("api_key","secret"),("scorer_version","custom")])
def test_client_scoring_fields_rejected(setup,field,value):
    client,a,b,r,p=setup
    assert evaluate(client,a,[r["id"]],**{field:value}).status_code==422 and p.calls==[]


@pytest.mark.parametrize("extra",[{"job_text":42},{"resume_ids":[42]},{"fresh":"true"}])
def test_evaluation_contract_is_strict(setup,extra):
    client,a,b,r,p=setup
    body={"job_text":JOB,"resume_ids":[r["id"]],**extra}
    response=client.post('/api/resumes/evaluate',headers=a,json=body)
    assert response.status_code==422 and p.calls==[]


@pytest.mark.parametrize("mode",["offline","offline-heuristic","no_key"])
def test_offline_profile_does_not_enter_ai_evaluation(setup,mode):
    client,a,b,r,p=setup
    if mode=="no_key": p.api_key=""
    else: p.model_name=mode
    for response in [evaluate(client,a,[r["id"]]),client.post(f'/api/resumes/{r["id"]}/profile',headers=a)]:
        assert response.status_code==409 and response.json()["detail"]["error_type"]=="ai_provider_required"
    assert p.calls==[]


def test_provider_failure_never_returns_legacy_percentage(setup,caplog):
    client,a,b,r,p=setup
    p.rank_resumes=Mock(side_effect=AssertionError("Legacy fallback forbidden"))
    def fail(payload): raise RuntimeError("private resume body sk-secret-token")
    p.hook=fail
    for response in [evaluate(client,a,[r["id"]]),client.post(f'/api/resumes/{r["id"]}/profile',headers=a)]:
        assert response.status_code==502
        assert "private resume body" not in response.text and "sk-secret-token" not in response.text
        assert response.json()["detail"]["can_switch_offline"] is False
    p.rank_resumes.assert_not_called()
    assert "sk-secret-token" not in caplog.text
    assert client.get('/api/resumes',headers=a).json()[0]["content"]==r["content"]


def test_full_raw_jd_reaches_pipeline(setup,monkeypatch):
    client,a,b,r,p=setup
    from backend.services.matching.pipeline import evaluate_resumes
    seen=[]
    def capture(job_text,resumes,**kwargs):
        seen.append((job_text,resumes,kwargs))
        return evaluate_resumes(job_text,resumes,**kwargs)
    monkeypatch.setattr(main,"evaluate_resumes",capture,raising=False)
    base_extract=p.extract_match_chunk
    def anchored(payload,*,timeout):
        if payload["task"]=="requirements":
            from tests.test_match_extraction import proposal
            p.calls.append(payload)
            quote=JOB.splitlines()[-1]
            return dict(chunk_index=payload["chunk_index"],complete=True,
                        items=[proposal(quote,"Python","required_skills","skill")] if quote in payload["source_text"] else [])
        return base_extract(payload,timeout=timeout)
    monkeypatch.setattr(p,"extract_match_chunk",anchored)
    raw="  "+JOB+"\n\n"+"Context.\n"*1000
    response=evaluate(client,a,[r["id"]],job=raw,fresh=True)
    assert response.status_code==200
    assert seen[0][0]==raw and seen[0][1][0].content==r["content"]
    assert seen[0][2]["as_of"]==date.today() and seen[0][2]["fresh"] is True


def test_profile_preparation_is_minimal_and_repeat_makes_zero_calls(setup):
    client,a,b,r,p=setup; url=f'/api/resumes/{r["id"]}/profile'
    first=client.post(url,headers=a)
    assert first.status_code==200 and first.json()["status"]=="complete"
    assert set(first.json())=={"resume_id","status","source_hash","profile_fingerprint","warnings"}
    assert p.counts()=={"resume_profile":1}; p.calls.clear()
    assert client.post(url,headers=a).json()==first.json() and p.calls==[]
    assert evaluate(client,a,[r["id"]]).status_code==200 and p.counts()=={"requirements":1}


@pytest.mark.parametrize("body",[{"content":"fake"},{"api_key":"fake"},{"facts":[]},{"source_hash":"fake"}])
def test_profile_endpoint_rejects_caller_facts_or_text(setup,body):
    client,a,b,r,p=setup
    assert client.post(f'/api/resumes/{r["id"]}/profile',headers=a,json=body).status_code==422
    assert p.calls==[]


def test_profile_edit_during_preparation_is_incomplete(setup):
    client,a,b,r,p=setup
    uid=client.get('/api/auth/me',headers=a).json()["id"]
    p.hook=lambda payload: main.storage.update_resume(r["id"],content="Edited content",user_id=uid)
    result=client.post(f'/api/resumes/{r["id"]}/profile',headers=a)
    assert result.status_code==200 and result.json()["status"]=="needs_review"
    assert result.json()["profile_fingerprint"] is None and result.json()["warnings"]==["source_incomplete"]
    assert client.get('/api/resumes',headers=a).json()[0]["content"]=="Edited content"


def test_incomplete_comparison_returns_null_scores_and_no_winner(setup):
    client,a,b,r,p=setup
    uid=client.get("/api/auth/me",headers=a).json()["id"]
    warned=main.storage.add_resume("Unreadable",r["content"],extraction_warnings=["source_incomplete"],user_id=uid)
    response=evaluate(client,a,[warned.id])
    assert response.status_code==200 and not response.json()["comparison_complete"]
    e=response.json()["evaluations"][0]
    assert e["raw_score"] is None and e["rank"] is None and not e["is_top_match"]
    assert "source_incomplete" in e["reason_codes"]


@pytest.mark.parametrize("route",["evaluate","profile"])
def test_new_routes_share_authenticated_ai_rate_limit(setup,route):
    from backend.services.rate_limiter import RateLimiter
    client,a,b,r,p=setup
    uid=client.get('/api/auth/me',headers=a).json()["id"]
    limiter=RateLimiter(main.storage)
    for _ in range(30): limiter.check("user_ai_ops",uid,limit=30,window_seconds=60)
    response=evaluate(client,a,[r["id"]]) if route=="evaluate" else client.post(f'/api/resumes/{r["id"]}/profile',headers=a)
    assert response.status_code==429 and int(response.headers["Retry-After"])>0 and p.calls==[]


def test_saved_provider_selection_and_missing_key_are_respected(two_users,monkeypatch):
    client,a,b=two_users; monkeypatch.setenv("MATCHING_V2_ENABLED","true")
    r=client.post('/api/resumes',headers=a,json={"name":"R","content":"Projects:\n"+QUOTE}).json()
    p=Provider(); engines=[]
    def fake_extract(self,payload,*,timeout):
        engines.append((self.api_base_url,self.model_name,self.api_key))
        return p.extract_match_chunk(payload,timeout=timeout)
    monkeypatch.setattr(main.AIEngine,"extract_match_chunk",fake_extract)
    for i in range(2):
        profile=client.post('/api/settings/profiles',headers=a,json={"name":f"P{i}","api_base_url":"https://api.openai.com/v1","model_name":f"model-{i}","api_key":f"test-secret-{i}","is_active":True})
        assert profile.status_code==200
        assert evaluate(client,a,[r["id"]]).status_code==200
        assert engines[-1]==("https://api.openai.com/v1",f"model-{i}",f"test-secret-{i}")
    profile=client.post('/api/settings/profiles',headers=a,json={"name":"No key","api_base_url":"https://api.openai.com/v1","model_name":"new-model","is_active":True})
    assert profile.status_code==200
    assert evaluate(client,a,[r["id"]]).status_code==409


@pytest.mark.parametrize("raw,expected",[(None,False),("false",False),("unexpected",False),("",False),(" TRUE ",True),("1",True),("yes",True)])
def test_rollout_flag_fails_closed(monkeypatch,raw,expected):
    from backend.config import matching_v2_enabled
    if raw is None: monkeypatch.delenv("MATCHING_V2_ENABLED",raising=False)
    else: monkeypatch.setenv("MATCHING_V2_ENABLED",raw)
    assert matching_v2_enabled() is expected


def test_selected_foreign_profile_cannot_fall_back_to_unrelated_key(two_users,monkeypatch):
    client,a,b=two_users; monkeypatch.setenv("MATCHING_V2_ENABLED","true")
    r=client.post('/api/resumes',headers=a,json={"name":"R","content":"Projects:\n"+QUOTE}).json()
    foreign=client.post('/api/settings/profiles',headers=b,json={"name":"B","api_base_url":"https://api.openai.com/v1","model_name":"b-model","api_key":"b-secret"}).json()
    settings=client.post('/api/settings',headers=a,json={"active_profile_id":foreign["id"],"api_key":"a-unrelated-secret"})
    assert settings.status_code==200
    spy=Mock(side_effect=AssertionError("No provider request allowed"))
    monkeypatch.setattr(main.AIEngine,"extract_match_chunk",spy)
    assert evaluate(client,a,[r["id"]]).status_code==409
    spy.assert_not_called()


def test_authenticated_analyze_save_edit_switch_and_rollback_journey(setup,monkeypatch):
    from backend.models import JobAnalysisResult
    client,a,b,r,p=setup
    p.analyze_job=lambda text,**kwargs:JobAnalysisResult(required_skills=["Python"])
    analyzed=client.post('/api/jobs/analyze',headers=a,json={"text":JOB})
    assert analyzed.status_code==200 and analyzed.json()["raw_text"]==JOB
    initial=evaluate(client,a,[r["id"]],job=analyzed.json()["raw_text"])
    assert initial.status_code==200 and initial.json()["comparison_complete"]
    p.calls.clear()
    assert evaluate(client,a,[r["id"]]).json()==initial.json() and p.calls==[]
    edited=client.patch(f'/api/resumes/{r["id"]}',headers=a,json={"content":r["content"]+"\nAdded context."})
    assert edited.status_code==200
    after_edit=evaluate(client,a,[r["id"]])
    assert after_edit.status_code==200 and after_edit.json()["evaluations"][0]["evaluation_id"]!=initial.json()["evaluations"][0]["evaluation_id"]
    assert p.counts()=={"resume_profile":1}
    p.calls.clear()
    assert evaluate(client,a,[r["id"]],job="Required:\nPython knowledge.").status_code==200
    assert p.counts()=={"requirements":1}
    p.calls.clear(); p.model_name="another-provider-model"
    assert evaluate(client,a,[r["id"]]).status_code==200 and p.counts()=={"requirements":1,"resume_profile":1}
    p.calls.clear()
    old=client.post('/api/resumes/evaluate',headers=a,json={"job":analyzed.json()["analysis"],"resume_ids":[r["id"]]})
    assert old.status_code==422 and p.calls==[]
    monkeypatch.setenv("MATCHING_V2_ENABLED","false")
    assert client.get('/api/features',headers=a).json()=={"matching_v2_enabled":False}
    assert evaluate(client,a,[r["id"]]).status_code==404
    p.rank_resumes=Mock(return_value=[])
    legacy=client.post('/api/resumes/match',headers=a,json={"job":analyzed.json()["analysis"]})
    assert legacy.status_code==200 and isinstance(legacy.json(),list) and p.calls==[]


def test_incomplete_saved_source_never_receives_score_or_profile(setup):
    client,a,b,r,p=setup
    uid=client.get('/api/auth/me',headers=a).json()["id"]
    warned=main.storage.add_resume("Unreadable","Some source",user_id=uid,extraction_warnings=["unreadable_pages"])
    response=client.post(f'/api/resumes/{warned.id}/profile',headers=a)
    assert response.status_code==200 and response.json()["warnings"]==["source_incomplete"]
    assert response.json()["profile_fingerprint"] is None and p.calls==[]
    response=evaluate(client,a,[warned.id])
    assert response.status_code==200 and response.json()["evaluations"][0]["raw_score"] is None
    assert p.counts()=={"requirements":1}


def test_engine_resolution_errors_are_sanitized(setup,monkeypatch):
    client,a,b,r,p=setup
    def fail(**kwargs): raise RuntimeError("private-key-in-config-error")
    monkeypatch.setattr(main,"get_ai_engine",fail)
    for response in [evaluate(client,a,[r["id"]]),client.post(f'/api/resumes/{r["id"]}/profile',headers=a)]:
        assert response.status_code==502 and "private-key-in-config-error" not in response.text


def test_skill_fit_response_and_cached_fresh_comparison(setup):
    client,a,b,r,p=setup
    first=evaluate(client,a,[r["id"]])
    assert first.status_code==200
    row=first.json()["evaluations"][0]
    assert row["score_scope"]=="skill_fit"
    assert all(v["requirement"]["kind"]=="skill" for v in row["requirement_results"])
    calls=p.counts().copy()
    p.hook=lambda *args: (_ for _ in ()).throw(AssertionError("Cached comparison contacted AI"))
    again=client.post("/api/resumes/evaluate",headers=a,json={"job_text":JOB,"resume_ids":[r["id"]],"fresh":True})
    assert again.status_code==200 and p.counts()==calls
    assert again.json()["evaluations"][0]["raw_score"]==row["raw_score"]


@pytest.mark.parametrize("accept", [False, True])
def test_review_resolves_claim_without_ai_and_rejects_stale_foreign_input(setup, monkeypatch, accept):
    client,a,b,r,p=setup
    original=p.extract_match_chunk
    def extract(payload, *, timeout):
        response=original(payload,timeout=timeout)
        if payload['task']=='resume_profile':
            response['items'].append(dict(kind='skill',canonical_key='Python' if accept else 'InventedTool',level='listed',source_quote='Projects:'))
        return response
    monkeypatch.setattr(p,'extract_match_chunk',extract)
    # Heading reference cannot recover across a section boundary.
    first=client.post(f'/api/resumes/{r["id"]}/profile',headers=a).json()
    assert first['status']=='needs_review'
    key=first['unresolved_skills'][0]
    body=dict(review_token=first['review_token'], decisions=[dict(skill=key,source_quote=QUOTE if accept else None)])
    url=f'/api/resumes/{r["id"]}/profile/review'
    before=p.counts().copy()
    assert client.post(url,json=body).status_code==401
    assert client.post(url,headers=b,json=body).status_code==404
    assert client.post(url,headers=a,json={**body,'review_token':'stale'}).status_code==409
    assert client.post(url,headers=a,json={**body,'decisions':[dict(skill=key,source_quote='fabricated source')]}).status_code==422
    done=client.post(url,headers=a,json=body)
    assert done.status_code==200 and done.json()['status']=='complete'
    assert p.counts()==before
    assert client.post(url,headers=a,json=body).status_code==409
    assert client.get(f'/api/resumes/{r["id"]}/profile',headers=a).json()['status']=='complete'
    assert evaluate(client,a,[r['id']]).json()['comparison_complete']
    assert p.counts()=={'resume_profile':1,'requirements':1}


def test_review_save_rejects_content_edit_during_transaction(setup, monkeypatch):
    client,a,b,r,p=setup
    original=p.extract_match_chunk
    def extract(payload, *, timeout):
        response=original(payload,timeout=timeout)
        if payload['task']=='resume_profile':
            response['items'].append(dict(kind='skill',canonical_key='InventedTool',level='listed',source_quote='Projects:'))
        return response
    monkeypatch.setattr(p,'extract_match_chunk',extract)
    first=client.post(f'/api/resumes/{r["id"]}/profile',headers=a).json()
    body=dict(review_token=first['review_token'],decisions=[dict(skill='inventedtool',source_quote=None)])
    save=main.storage.save_resume_profile
    def race(**kwargs):
        assert client.patch(f'/api/resumes/{r["id"]}',headers=a,json={'content':'Skills: Rust'}).status_code==200
        return save(**kwargs)
    monkeypatch.setattr(main.storage,'save_resume_profile',race)
    assert client.post(f'/api/resumes/{r["id"]}/profile/review',headers=a,json=body).status_code==409
    assert client.get(f'/api/resumes/{r["id"]}/profile',headers=a).json()['status']=='not_prepared'
    assert p.counts()=={'resume_profile':1}


def test_reviewed_full_text_unblocks_unreadable_resume_only_with_explicit_confirmation(setup):
    client,a,b,r,p=setup
    uid=client.get('/api/auth/me',headers=a).json()['id']
    warned=main.storage.add_resume('Unreadable','Partial',user_id=uid,extraction_warnings=['page missing'])
    url=f'/api/resumes/{warned.id}'
    text='Projects:\n'+QUOTE
    assert client.patch(url,headers=a,json={'content':text}).json()['extraction_warnings']
    assert client.patch(url,headers=a,json={'source_reviewed':True}).status_code==422
    assert client.patch(url,headers=b,json={'content':text,'source_reviewed':True}).status_code==404
    resolved=client.patch(url,headers=a,json={'content':text,'source_reviewed':True})
    assert resolved.status_code==200 and not resolved.json()['extraction_warnings']
    assert client.post(url+'/profile',headers=a).json()['status']=='complete'
    assert evaluate(client,a,[warned.id]).json()['comparison_complete']
