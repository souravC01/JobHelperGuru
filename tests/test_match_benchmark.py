"""Real report/runner checks; synthetic provider results cannot approve rollout."""
from datetime import date
from types import SimpleNamespace
import json

import pytest
from tests.test_match_pipeline import Provider, JOB, QUOTE


def benchmark():
    from scripts import evaluate_matching
    return evaluate_matching


def case(id='one', **changes):
    return dict(id=id, split='dev', source_type='synthetic', job_text=JOB,
                resumes=[dict(id='a', owner_id='person', content='Projects:\n'+QUOTE),
                         dict(id='b', owner_id='person', content='Projects:\nOther work.')],
                expected_pairs=[['a','b']], **changes)


def record(id='one', scores=(80,40), elapsed=2, repeat=0, phase='fixed_rubric'):
    return dict(case_id=id, phase=phase, repeat=repeat, elapsed_seconds=elapsed,
                comparison_complete=all(s is not None for s in scores), job_fingerprint=id,
                evaluations=[dict(resume_id=r, status='complete' if score is not None else 'needs_review',
                                  raw_score=str(score) if score is not None else None,
                                  match_score=score, rank=None, is_top_match=False, rubric_fingerprint='frozen',
                                  evaluation_id=r, source_fingerprint=r, profile_fingerprint=r,
                                  category_scores={}, skill_coverage_score=None,
                                  reason_codes=['missing_assessment'] if score is None else [], requirement_results=[])
                             for r,score in zip(('a','b'),scores)],
                metrics=dict(provider_calls=1, token_usage=None, usage_available=False, stages={},
                             full_source_resume_chunks=0, full_source_resume_ids=[]))


def test_tied_and_unscored_pairs_stay_in_denominator():
    m=benchmark(); cases=[case(id=i) for i in ('one','two','three')]
    report=m.build_report(cases,[record('one'),record('two',(50,50)),record('three',(None,20))])
    assert report['strict_pairs']==dict(total=3,correct=1,tied=1,reversed=0,unscored=1,agreement_pct=pytest.approx(100/3))


def test_report_separates_per_job_latency_from_suite_total():
    m=benchmark(); report=m.build_report([case('one'),case('two')],[record('one',elapsed=70),record('two',elapsed=80)],suite_elapsed_seconds=154)
    assert [r['elapsed_seconds'] for r in report['runs']]==[70,80]
    assert report['suite_elapsed_seconds']==154
    assert not report['release_gate_passed']


def test_missing_usage_is_unavailable():
    report=benchmark().build_report([case()],[record()])
    assert report['token_usage'] is None and not report['usage_available']


def test_same_person_gate_rejects_cross_person_fixture():
    c=case(); c['source_type']='anonymized_real'; c['split']='holdout'; c['resumes'][1]['owner_id']='different-person'
    report=benchmark().build_report([c],[record()],execution='live',review_verified=True)
    assert not report['release_gate_passed']
    assert 'same_person' in report['failed_gates']


def test_stability_reports_repeated_order_changes():
    report=benchmark().build_report([case()],[record(scores=(80,40),repeat=0),record(scores=(40,80),repeat=1),record(scores=(80,40),repeat=2)])
    assert report['stability']['reversed_pairs']==1
    assert not report['development_gate_passed']


def test_rounded_display_tie_is_not_raw_score_tie():
    r=record(scores=(80.49,80.01)); report=benchmark().build_report([case()],[r])
    assert report['strict_pairs']['correct']==1 and report['strict_pairs']['tied']==0


def test_missing_repeat_and_synthetic_results_cannot_pass_gate():
    report=benchmark().build_report([case()],[record()],review_verified=True)
    assert not report['development_gate_passed'] and not report['release_gate_passed']
    assert 'live_provider' in report['failed_gates'] and 'three_fixed_runs' in report['failed_gates']


def test_freeze_and_cold_rubric_drift_are_separate():
    cold=record(repeat=1,phase='cold'); cold['evaluations'][0]['rubric_fingerprint']='changed'
    report=benchmark().build_report([case()],[record(phase='cold'),cold,record(),record(repeat=1),record(repeat=2)])
    assert report['rubric_drift']['cold_cases']==1
    assert report['rubric_drift']['fixed_cases']==0


def test_counting_engine_tracks_tasks_fallback_and_zero_call_usage():
    m=benchmark(); engine=m.CountingEngine(Provider(),max_calls=10)
    before=engine.mark(); engine.extract_match_chunk(dict(task='requirements',source_text=JOB,chunk_index=0),timeout=5)
    metrics=engine.since(before)
    assert metrics['provider_calls']==1 and metrics['stages']['requirements']['calls']==1
    assert metrics['token_usage'] is None
    assert engine.since(engine.mark())['token_usage']==dict(prompt_tokens=0,completion_tokens=0,total_tokens=0)


def test_sdk_usage_and_request_cap_are_observed_without_keys_or_source():
    m=benchmark(); calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=7,completion_tokens=3,total_tokens=10))
    class Engine:
        api_base_url='https://provider.example/v1'; model_name='model'; api_key='never-record-this-key'
        def _get_client(self): return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        def extract_match_chunk(self,payload,*,timeout): return self._get_client().chat.completions.create(messages=[payload])
    engine=m.CountingEngine(Engine(),max_calls=1); mark=engine.mark()
    engine.extract_match_chunk(dict(task='evidence_batch',resumes=[dict(resume_id='a',mode='source',source_text='private text')]),timeout=5)
    metrics=engine.since(mark)
    assert metrics['token_usage']==dict(prompt_tokens=7,completion_tokens=3,total_tokens=10)
    assert metrics['full_source_resume_chunks']==1
    with pytest.raises(m.RequestLimit): engine.extract_match_chunk(dict(task='requirements'),timeout=5)
    assert len(calls)==1
    assert 'private text' not in json.dumps(metrics) and 'never-record' not in json.dumps(metrics)


def test_warm_second_job_edit_and_scorer_lifecycle_uses_real_pipeline(tmp_path):
    m=benchmark(); c=case(); c['second_job_text']='Required:\nPython knowledge.'
    c['edited_resume']=dict(id='a',content='Projects:\nOther work.')
    provider=m.CountingEngine(Provider(),max_calls=80)
    runs=m.run_lifecycle(c,engine=provider,as_of=date(2026,9,30))
    phases={r['phase']:r for r in runs}
    assert phases['second_job']['metrics']['stages'].get('resume_profile',{}).get('calls',0)==0
    assert phases['warm']['comparison_complete'] and phases['warm']['metrics']['provider_calls']==0
    assert phases['warm']['same_scores_and_ids']
    assert phases['edited_resume']['metrics']['stages']['resume_profile']['calls']==1
    assert phases['scorer_only']['metrics']['provider_calls']==0
    assert phases['scorer_only']['same_scores_and_ids']
    assert all(e['scorer_version'].endswith('-benchmark') for e in phases['scorer_only']['evaluations'])
    assert 'source_text' not in json.dumps(runs)


def test_case_validation_rejects_unknown_pairs_and_invalid_documents():
    m=benchmark(); c=case(); c['expected_pairs']=[['a','missing']]
    with pytest.raises(ValueError): m.validate_cases([c])
    c=case(); c['job_text']='x'*100001
    with pytest.raises(ValueError): m.validate_cases([c])


def test_human_review_is_bound_to_exact_fixture_and_provider_permission():
    m=benchmark(); c=case(); c['source_type']='anonymized_real'
    review=dict(reviewed_by='Reviewer',reviewed_at='2026-09-30',fixture_sha256='hash',case_ids=['one'],approved_for_provider_use=True)
    c.update(expected_requirements=[dict(category='required_skills',alternatives=['python'])],expected_resume_skills={'a':[],'b':[]})
    review.update(score_scope='skill_fit',skills_reviewed=True)
    assert m.verify_review([c],review,'hash')
    assert not m.verify_review([c],review,'edited-hash')
    review['approved_for_provider_use']=False
    assert not m.verify_review([c],review,'hash')


def test_real_runner_separates_cold_rubrics_from_fixed_assessment_repeats():
    m=benchmark(); engine=m.CountingEngine(Provider(),max_calls=80)
    runs=m.run_quality([case()],engine=engine,as_of=date(2026,9,30))
    fixed=[r for r in runs if r['phase']=='fixed_rubric']
    cold=[r for r in runs if r['phase']=='cold']
    assert len(fixed)==len(cold)==3
    assert len({e['rubric_fingerprint'] for r in fixed for e in r['evaluations']})==1
    assert all(r['metrics']['stages'].get('resume_profile',{}).get('calls',0)==0 for r in fixed)
    assert all(r['metrics']['stages']['requirements']['calls']==1 for r in cold)
    assert all(r['comparison_complete'] for r in runs)


def test_local_repeats_use_cached_skills_without_source_assessment():
    m=benchmark(); engine=m.CountingEngine(Provider(),max_calls=80)
    runs=m.run_quality([case()],engine=engine,as_of=date(2026,9,30))
    assert not [r for r in runs if r['phase']=='full_source']
    fixed=[r for r in runs if r['phase']=='fixed_rubric']
    assert len(fixed)==3 and all(r['comparison_complete'] and r['metrics']['provider_calls']==0 for r in fixed)
    assert all(r['metrics']['stages'].get('evidence_batch',{}).get('calls',0)==0 for r in runs)


def test_gate_requires_each_cold_comparison_and_complete_profile_measurements():
    m=benchmark()
    evidence=dict(execution='live',job_chars=8000,resume_chars=[8000]*5,cold=[dict(comparison_complete=True,elapsed_seconds=121,metrics={'provider_calls':8})],
                  warm=dict(comparison_complete=True,same_scores_and_ids=True,metrics={'provider_calls':0}),
                  lifecycle=[])
    assert not m.performance_gate(evidence)
    evidence['cold'][0]['elapsed_seconds']=90
    assert not m.performance_gate(evidence)  # Missing three-run and profile-lifecycle measurements.


def test_report_rejects_invalid_positive_quote_and_never_exports_private_text():
    m=benchmark(); r=record(); r['evaluations'][0]['requirement_results']=[dict(evidence=[dict(level='demonstrated',source_quote='private invented quote',source_start=0,source_end=22)])]
    report=m.build_report([case()],[r])
    assert report['quote_validation_failures']==1
    assert 'private invented quote' not in json.dumps(report)


def test_holdout_is_not_opened_without_passing_development_evidence(tmp_path):
    m=benchmark(); path=tmp_path/'untouched.json'
    assert not path.exists()
    with pytest.raises(ValueError,match='development'):
        m.load_live_inputs(path,tmp_path/'review.json',phase='holdout',development_report=None,provider={'host':'provider.example','model':'test'})


def test_live_cli_refuses_ambient_keys_without_explicit_live_selection(tmp_path):
    m=benchmark()
    with pytest.raises(SystemExit) as error:
        m.main(['--fixture',str(tmp_path/'missing.json')])
    assert error.value.code==2


def test_fixture_review_covers_secondary_jobs_and_edits_in_the_same_hashed_file(tmp_path):
    m=benchmark(); c=case(); c['source_type']='anonymized_real'; c['second_job_text']='Different approved JD'
    c['edited_resume']=dict(id='a',content='New allowed text')
    c.update(expected_requirements=[dict(category='required_skills',alternatives=['python'])],expected_resume_skills={'a':[],'b':[]})
    fixture=tmp_path/'dev.json'; fixture.write_text(json.dumps([c]),encoding='utf-8')
    review=tmp_path/'review.json'; review.write_text(json.dumps(dict(reviewed_by='Reviewer',reviewed_at='2026-09-30',fixture_sha256=m.source_hash(fixture.read_text()),case_ids=['one'],approved_for_provider_use=True,score_scope='skill_fit',skills_reviewed=True)),encoding='utf-8')
    loaded,digest=m.load_live_inputs(fixture,review,phase='dev',development_report=None,provider={'host':'provider.example','model':'test'})
    assert loaded==[c] and digest==m.source_hash(fixture.read_text())


def test_quality_report_includes_job_analysis_calls_and_usage():
    m=benchmark(); r=record(); r['analysis_metrics']=dict(provider_calls=1,token_usage=None)
    report=m.build_report([case()],[r])
    assert report['provider_calls']==2 and report['token_usage'] is None


def test_zero_measurements_and_edited_source_cannot_pass_development():
    m=benchmark(); c=case(); c['source_type']='anonymized_real'
    report=m.build_report([c],[],execution='live',review_verified=True)
    assert not report['development_gate_passed'] and report['strict_pairs']['unscored']==1


def test_perf_gate_accepts_only_three_complete_cold_runs_and_required_reuse():
    m=benchmark(); metrics=lambda calls:dict(provider_calls=calls,stages={'resume_profile':{'calls':calls}})
    evidence=dict(execution='live',job_chars=3200,resume_chars=[3215,3842,4000,4200,4502],
        cold=[dict(comparison_complete=True,elapsed_seconds=100,metrics=metrics(8)) for _ in range(3)],
        main_cold=[dict(comparison_complete=True,elapsed_seconds=80,metrics=metrics(2)) for _ in range(3)],
        lifecycle=[dict(phase=phase,comparison_complete=True,metrics=metrics(calls),same_scores_and_ids=True)
                   for phase,calls in [('profile_preparation',5),('prepared_first_job',0),('second_job',0),('warm',0),('rename',0),('fresh',0),('edited_resume',1),('scorer_only',0)]])
    for row in evidence['lifecycle']:
        if row['phase'] in {'prepared_first_job','second_job'}: row['metrics']=dict(provider_calls=1,stages={'requirements':{'calls':1}})
        if row['phase']=='edited_resume':
            row['expected_profile_source_hashes']=['edited']
            row['metrics']['profile_source_call_counts']={'edited':1}
    assert m.performance_gate(evidence)
    for dimensions in ([0,3842,4000,4200,4502], [3215]*4, [100001]*5):
        assert not m.performance_gate({**evidence,'resume_chars':dimensions})
    evidence['cold'][1]['comparison_complete']=False
    assert not m.performance_gate(evidence)


def test_report_projects_nested_source_and_secret_fields_instead_of_copying_them():
    m=benchmark(); r=record(); r['private_source']='private body'; r['evaluations'][0]['api_key']='private secret'
    report=m.build_report([case()],[r])
    serialized=json.dumps(report)
    assert 'private body' not in serialized and 'private secret' not in serialized


def test_reviewed_input_rejects_nonanonymous_owner_and_changed_edit():
    m=benchmark(); c=case(); c['resumes'][0]['owner_id']={}
    with pytest.raises(ValueError): m.validate_cases([c])
    c=case(); c['edited_resume']=dict(id='a',content=c['resumes'][0]['content'])
    with pytest.raises(ValueError): m.validate_cases([c])


def test_cold_main_baseline_report_measures_pair_agreement_without_score_scope_confusion():
    m=benchmark(); runs=[record(phase='legacy_cold'),record(scores=(50,50),repeat=1,phase='legacy_cold'),record(scores=(40,80),repeat=2,phase='legacy_cold')]
    pairs=m.baseline_pairs([case()],runs)
    assert pairs==dict(total=3,correct=1,tied=1,reversed=1,unscored=0)


def test_performance_gate_requires_main_baseline_and_prepared_profiles():
    m=benchmark()
    metrics=lambda calls:dict(provider_calls=calls,stages={'resume_profile':{'calls':calls}})
    evidence=dict(execution='live',job_chars=8000,resume_chars=[8000]*5,
        cold=[dict(comparison_complete=True,elapsed_seconds=100,metrics=metrics(8)) for _ in range(3)],
        lifecycle=[dict(phase=p,comparison_complete=True,metrics=metrics(n),same_scores_and_ids=True)
            for p,n in [('profile_preparation',5),('prepared_first_job',0),('second_job',0),('warm',0),('rename',0),('fresh',0),('edited_resume',1),('scorer_only',0)]])
    assert not m.performance_gate(evidence)
    evidence['main_cold']=[dict(comparison_complete=True,metrics=metrics(2)) for _ in range(3)]
    evidence['lifecycle'][1]['metrics']=metrics(1)
    assert not m.performance_gate(evidence)


def test_development_requires_preferred_pairs_in_cold_runs_too():
    m=benchmark(); c=case(); c['source_type']='anonymized_real'
    runs=[record(repeat=i) for i in range(3)]+[record(scores=(40,80),phase='cold')]
    # Supply the already-verified projection as the synthetic representation of live evidence.
    for r in runs:
        for e in r['evaluations']:
            e.update(quote_count=1,quote_validation_failures=0,unsupported_score=False)
    report=m.build_report([c],runs,execution='live',review_verified=True)
    assert not report['development_gate_passed']
    assert report['cold_strict_pairs']['reversed']==1


def test_failed_preparation_does_not_repeat_profiles_as_fixed_evidence_or_lifecycle():
    m=benchmark()
    class FailedProfiles(Provider):
        def extract_match_chunk(self,payload,*,timeout=None):
            if payload['task']=='resume_profile':
                self.calls.append(payload)
                return {'invalid':True}
            return super().extract_match_chunk(payload,timeout=timeout)
    engine=m.CountingEngine(FailedProfiles(),max_calls=80)
    runs=m.run_quality([case()],engine=engine,as_of=date(2026,9,30))
    assert len([r for r in runs if r['phase']=='cold'])==3
    assert not [r for r in runs if r['phase']=='fixed_rubric']
    assert engine.engine.counts()['resume_profile']==12
    engine=m.CountingEngine(FailedProfiles(),max_calls=80)
    lifecycle=m.run_lifecycle(case(),engine=engine,as_of=date(2026,9,30))
    assert [r['phase'] for r in lifecycle]==['profile_preparation']
    assert engine.engine.counts()['resume_profile']==4


def test_skill_gate_requires_exact_scores_ranks_and_zero_comparison_calls():
    m=benchmark(); c=case()
    runs=[record(repeat=i) for i in range(3)]
    for run in runs:
        run['metrics']['provider_calls']=0
        for e in run['evaluations']: e['score_scope']='skill_fit'
    report=m.build_report([c],runs)
    assert report['score_scope']=='skill_fit'
    assert report['gates']['local_comparisons']
    assert report['gates']['identical_local_scores_and_ranks']
    runs[1]['evaluations'][0]['raw_score']='81'
    report=m.build_report([c],runs)
    assert not report['gates']['identical_local_scores_and_ranks']
    runs[1]['evaluations'][0]['raw_score']='80'
    runs[1]['evaluations'][0]['rank']=2
    assert not m.build_report([c],runs)['gates']['identical_local_scores_and_ranks']
    runs[1]['metrics']['stages']['evidence_batch']={'calls':1}
    assert not m.build_report([c],runs)['gates']['local_comparisons']


def test_old_review_cannot_approve_skill_extraction_quality():
    m=benchmark(); c=case()
    review=dict(reviewed_by='Reviewer',reviewed_at='2026-09-30',fixture_sha256='hash',case_ids=['one'],approved_for_provider_use=True)
    assert not m.verify_review([c],review,'hash')
    assert not m.build_report([c],[record()],execution='live',review_verified=True)['gates']['reviewed_skill_extractions']


def test_cold_extraction_checks_reviewed_skill_sets_without_extra_requests():
    m=benchmark(); c=case()
    c.update(expected_requirements=[dict(category='required_skills',alternatives=['python'])],
             expected_resume_skills={'a':[dict(canonical_key='python',level='demonstrated')],'b':[]})
    engine=m.CountingEngine(Provider(),max_calls=9)
    runs=m.run_quality([c],engine=engine,as_of=date(2026,9,30))
    cold=[r for r in runs if r['phase']=='cold']
    assert len(cold)==3 and all(r['extraction_matches'] for r in cold)
    assert all(r['metrics']['provider_calls']==3 for r in cold)
    c['expected_requirements'][0]['alternatives']=['java']
    runs=m.run_quality([c],engine=m.CountingEngine(Provider(),max_calls=9),as_of=date(2026,9,30))
    assert all(not r['extraction_matches'] for r in runs if r['phase']=='cold')


def test_local_repeats_continue_after_exact_extraction_request_cap():
    m=benchmark(); engine=m.CountingEngine(Provider(),max_calls=3)
    runs=m.run_quality([case()],engine=engine,as_of=date(2026,9,30))
    assert len([r for r in runs if r['phase']=='fixed_rubric'])==3
    assert all(r['metrics']['provider_calls']==0 for r in runs if r['phase']=='fixed_rubric')


def test_edit_gate_allows_one_correction_per_changed_source_chunk_only():
    m=benchmark()
    metrics=lambda n: dict(provider_calls=n,stages={'resume_profile':{'calls':n}})
    lifecycle=[dict(phase=p,comparison_complete=True,metrics=metrics(n),same_scores_and_ids=True)
        for p,n in [('profile_preparation',5),('prepared_first_job',1),('second_job',1),('warm',0),('rename',0),('fresh',0),('edited_resume',2),('scorer_only',0)]]
    for row in lifecycle:
        if row['phase'] in {'prepared_first_job','second_job'}:
            row['metrics']=dict(provider_calls=1,stages={'requirements':{'calls':1}})
    edit=next(r for r in lifecycle if r['phase']=='edited_resume')
    edit['expected_profile_source_hashes']=['edited-chunk']
    edit['metrics']['profile_source_call_counts']={'edited-chunk':2}
    evidence=dict(execution='live',job_chars=3200,resume_chars=[4000]*5,
        cold=[dict(comparison_complete=True,elapsed_seconds=100,metrics=metrics(6)) for _ in range(3)],
        main_cold=[dict(comparison_complete=True,metrics=metrics(2)) for _ in range(3)],lifecycle=lifecycle)
    assert m.performance_gate(evidence)
    edit['metrics']['profile_source_call_counts']={'unchanged-chunk':2}
    assert not m.performance_gate(evidence)
    edit['metrics']['profile_source_call_counts']={'edited-chunk':3}
    edit['metrics']['provider_calls']=3
    edit['metrics']['stages']['resume_profile']['calls']=3
    assert not m.performance_gate(evidence)


def test_profile_source_accounting_observes_calls_without_exposing_content():
    m=benchmark(); engine=m.CountingEngine(Provider(),max_calls=2)
    payload=dict(task='resume_profile',source_text='Projects:\n'+QUOTE,chunk_index=0)
    engine.extract_match_chunk(payload,timeout=30)
    engine.extract_match_chunk({**payload,'validation_feedback':{}},timeout=30)
    metrics=engine.since(0)
    assert metrics['profile_source_call_counts']=={m.source_hash(payload['source_text']):2}
    assert metrics['full_source_resume_ids']==[]
    assert payload['source_text'] not in json.dumps(metrics)
