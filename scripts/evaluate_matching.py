"""AI benchmark measurements. Synthetic checks never establish release quality."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stdout, redirect_stderr
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
from itertools import combinations
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASELINE_REF = '9fa7b26a4ca78c38dd977d1eff0df1f30c11b5c5'
TOKENS = ('prompt_tokens', 'completion_tokens', 'total_tokens')
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class RequestLimit(RuntimeError):
    pass


class CountingEngine:
    """Observe SDK calls; fake-provider calls are counted only in hermetic tests."""
    def __init__(self, engine, *, max_calls):
        if type(max_calls) is not int or max_calls < 1:
            raise ValueError('A positive provider request limit is required')
        self.engine = engine
        self.records = []
        self.max_calls = max_calls
        self.exhausted = False
        self.lock = threading.Lock()
        self.context = threading.local()
        self.client_factory = getattr(engine, '_get_client', None)
        if self.client_factory:
            # This engine belongs exclusively to this benchmark, never the application.
            engine._get_client = self._get_client

    def __getattr__(self, name):
        return getattr(self.engine, name)

    def mark(self):
        with self.lock:
            return len(self.records)

    def _observe(self, operation):
        stage, sources = getattr(self.context, 'task', ('unknown', []))
        record = dict(stage=stage, source_ids=sources, token_usage=None, elapsed_seconds=0, failed=False)
        with self.lock:
            if len(self.records) >= self.max_calls:
                self.exhausted = True
                raise RequestLimit('Provider request limit reached')
            self.records.append(record)
        started = time.monotonic()
        try:
            response = operation()
            usage = getattr(response, 'usage', None)
            values = {k: getattr(usage, k, None) for k in TOKENS}
            if all(type(v) is int and v >= 0 for v in values.values()):
                record['token_usage'] = values
            return response
        except Exception:
            record['failed'] = True
            raise
        finally:
            record['elapsed_seconds'] = time.monotonic() - started

    def _get_client(self):
        client = self.client_factory()
        if client is not None:
            create = client.chat.completions.create
            client.chat.completions.create = lambda **kwargs: self._observe(lambda: create(**kwargs))
        return client

    def invoke(self, stage, method, *args, sources=None, **kwargs):
        previous = getattr(self.context, 'task', ('unknown', []))
        self.context.task = (stage, sources or [])
        try:
            operation = lambda: getattr(self.engine, method)(*args, **kwargs)
            return operation() if self.client_factory else self._observe(operation)
        finally:
            self.context.task = previous

    def extract_match_chunk(self, payload, *, timeout=None):
        sources = [r['resume_id'] for r in payload.get('resumes', []) if r.get('mode') == 'source']
        return self.invoke(payload['task'], 'extract_match_chunk', payload, sources=sources, timeout=timeout)

    def since(self, mark):
        with self.lock:
            records = [dict(r) for r in self.records[mark:]]
        def metrics(items):
            available = all(r['token_usage'] is not None for r in items)
            return dict(calls=len(items), elapsed_seconds=sum(r['elapsed_seconds'] for r in items),
                        failures=sum(r['failed'] for r in items), usage_available=available,
                        token_usage={k: sum(r['token_usage'][k] for r in items) for k in TOKENS} if available else None)
        combined = metrics(records)
        return dict(provider_calls=combined.pop('calls'), **combined,
                    stages={stage: metrics([r for r in records if r['stage']==stage]) for stage in sorted({r['stage'] for r in records})},
                    full_source_resume_chunks=sum(len(r['source_ids']) for r in records),
                    full_source_resume_ids=sorted({id for r in records for id in r['source_ids']}),
                    request_limit_reached=self.exhausted)


def source_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def validate_cases(cases):
    if not isinstance(cases, list) or not cases:
        raise ValueError('At least one benchmark case is required')
    seen = set()
    for case in cases:
        if not isinstance(case,dict): raise ValueError('Each case must be an object')
        id = case.get('id')
        if not isinstance(id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',id) or id in seen:
            raise ValueError('Case IDs must be unique anonymous identifiers')
        seen.add(id)
        if case.get('split') not in {'dev','holdout'} or case.get('source_type') not in {'synthetic','anonymized_real'}:
            raise ValueError('Case split and source type must be explicit')
        if not isinstance(case.get('resumes'),list) or any(not isinstance(r,dict) for r in case['resumes']): raise ValueError('Resume versions must be objects')
        if any(r.get('owner_id') is not None and (not isinstance(r['owner_id'],str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',r['owner_id'])) for r in case['resumes']): raise ValueError('Owners must use anonymous identifiers')
        documents = [case.get('job_text')] + [r.get('content') for r in case.get('resumes',[])]
        if not 2 <= len(case.get('resumes',[])) <= 5 or any(not isinstance(t,str) or not t.strip() or len(t)>100000 for t in documents):
            raise ValueError('Use two to five resume versions and complete documents within 100000 characters')
        ids = [r.get('id') for r in case['resumes']]
        if len(set(ids)) != len(ids) or any(not isinstance(id,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',id) for id in ids):
            raise ValueError('Resume IDs must be unique anonymous identifiers')
        if any(not isinstance(case.get(k,[]),list) for k in ('expected_pairs','expected_ties')): raise ValueError('Reviewed pairs must be lists')
        pairs = case.get('expected_pairs',[])+case.get('expected_ties',[])
        if any(not isinstance(p,list) or len(p)!=2 or any(not isinstance(id,str) for id in p) for p in pairs): raise ValueError('Each reviewed pair must contain two anonymous IDs')
        if not pairs or len({tuple(sorted(p)) for p in pairs}) != len(pairs):
            raise ValueError('Reviewed pairs must be nonempty and unique')
        if any(len(p)!=2 or p[0]==p[1] or not set(p)<=set(ids) for p in pairs):
            raise ValueError('Reviewed pairs must reference distinct saved versions')
        edit = case.get('edited_resume')
        if edit is not None and not isinstance(edit,dict): raise ValueError('Edited resume must be an object')
        if edit and (edit.get('id') not in ids or not isinstance(edit.get('content'),str) or not edit['content'].strip() or len(edit['content'])>100000):
            raise ValueError('Edited resume must identify a saved version with complete allowed text')
        if edit and edit['content']==next(r['content'] for r in case['resumes'] if r['id']==edit['id']): raise ValueError('Edited measurement requires a real content change')
        second = case.get('second_job_text')
        if second is not None and (not isinstance(second,str) or not second.strip() or len(second)>100000 or second==case['job_text']):
            raise ValueError('Second job must be a different complete description')
    return cases


def verify_review(cases, record, fixture_hash):
    ids = [c['id'] for c in cases]
    try:
        date.fromisoformat(record.get('reviewed_at','')[:10])
        return bool(record.get('reviewed_by') and record.get('fixture_sha256')==fixture_hash
                    and record.get('approved_for_provider_use') is True
                    and len(record.get('case_ids',[]))==len(ids) and set(record['case_ids'])==set(ids))
    except (TypeError,ValueError,KeyError):
        return False


def _score(evaluation):
    try:
        score = Decimal(str(evaluation['raw_score']))
        return score if evaluation['status']=='complete' and score.is_finite() and 0<=score<=100 else None
    except (KeyError,TypeError,InvalidOperation):
        return None


def _order(run, a, b):
    if not run.get('comparison_complete'):
        return None
    rows = {e['resume_id']:e for e in run.get('evaluations',[])}
    first, second = _score(rows.get(a,{})), _score(rows.get(b,{}))
    return None if first is None or second is None else (first>second)-(first<second)


def baseline_pairs(cases, runs):
    result = dict(total=0,correct=0,tied=0,reversed=0,unscored=0)
    for case in cases:
        for repeat in range(3):
            run=next((r for r in runs if r['case_id']==case['id'] and r['repeat']==repeat), {})
            for a,b in case.get('expected_pairs',[]):
                order=_order(run,a,b)
                result['total']+=1
                result['unscored' if order is None else 'correct' if order==1 else 'tied' if order==0 else 'reversed']+=1
    return result


def _projection(evaluation, content):
    fields = ('resume_id','status','match_score','raw_score','rank','is_top_match','job_fingerprint',
              'source_fingerprint','profile_fingerprint','rubric_fingerprint','evaluation_id','scorer_version',
              'assessment_version','category_scores','skill_coverage_score','reason_codes')
    result = {k:evaluation.get(k) for k in fields if k in evaluation}
    quotes = errors = 0
    levels = Counter()
    for rr in evaluation.get('requirement_results',[]):
        for evidence in rr.get('evidence',[]):
            levels[evidence['level']] += 1
            quote = evidence.get('source_quote')
            if quote is not None:
                quotes += 1
                start,end = evidence.get('source_start'),evidence.get('source_end')
                errors += not (type(start) is int and type(end) is int and 0<=start<end<=len(content) and content[start:end]==quote)
            elif evidence['level'] in {'demonstrated','listed'}:
                errors += 1
    result.update(quote_count=quotes, quote_validation_failures=errors, evidence_levels=dict(levels),
                  unsupported_score=evaluation.get('status')=='complete' and not evaluation.get('requirement_results'))
    return result


def _safe_evaluation(evaluation,content):
    if 'requirement_results' in evaluation: return _projection(evaluation,content)
    fields=('resume_id','status','match_score','raw_score','rank','is_top_match','job_fingerprint','source_fingerprint','profile_fingerprint','rubric_fingerprint','evaluation_id','scorer_version','assessment_version','category_scores','skill_coverage_score','reason_codes','quote_count','quote_validation_failures','evidence_levels','unsupported_score')
    return {k:evaluation[k] for k in fields if k in evaluation}


def build_report(cases, runs, *, execution='synthetic', review_verified=False, suite_elapsed_seconds=None, provider=None):
    validate_cases(cases)
    contents={c['id']:{r['id']:r['content'] for r in c['resumes']} for c in cases}
    runs=[{**run, 'evaluations':[_safe_evaluation(e,contents[run['case_id']].get(e['resume_id'],'')) for e in run.get('evaluations',[])]} for run in runs]
    strict = dict(total=0,correct=0,tied=0,reversed=0,unscored=0)
    reviewed_ties = dict(total=0,correct=0,unscored=0)
    reversed_pairs=set(); changed_pairs=set(); unscored_pairs=set(); score_drift=set()
    rubric_drift = dict(cold_cases=0,fixed_cases=0)
    repeats_complete = True
    for c in cases:
        fixed = sorted([r for r in runs if r['case_id']==c['id'] and r['phase']=='fixed_rubric'],key=lambda r:r['repeat'])
        cold = [r for r in runs if r['case_id']==c['id'] and r['phase']=='cold']
        quality = fixed or cold[:1] or [dict(comparison_complete=False,evaluations=[])]
        repeats_complete &= len(fixed)==3 and {r['repeat'] for r in fixed}=={0,1,2}
        for run in quality:
            for a,b in c.get('expected_pairs',[]):
                order = _order(run,a,b); strict['total']+=1
                strict['unscored' if order is None else 'correct' if order==1 else 'tied' if order==0 else 'reversed']+=1
            for a,b in c.get('expected_ties',[]):
                order = _order(run,a,b); reviewed_ties['total']+=1
                reviewed_ties['correct']+=order==0; reviewed_ties['unscored']+=order is None
        for phase, measurements in [('cold',cold),('fixed',fixed)]:
            fingerprints = {tuple(sorted({e.get('rubric_fingerprint') for e in r['evaluations'] if e.get('rubric_fingerprint')})) for r in measurements}
            rubric_drift[phase+'_cases'] += len(fingerprints)>1
        for a,b in combinations(sorted(r['id'] for r in c['resumes']),2):
            values=[_order(r,a,b) for r in fixed]
            key=(c['id'],a,b)
            if any(v is None for v in values): unscored_pairs.add(key)
            valid={v for v in values if v is not None}
            if 1 in valid and -1 in valid: reversed_pairs.add(key)
            if len(valid)>1: changed_pairs.add(key)
        for id in (r['id'] for r in c['resumes']):
            values={str(_score(e)) for r in fixed for e in r['evaluations'] if e['resume_id']==id}
            if len(values)>1: score_drift.add((c['id'],id))
    strict['agreement_pct'] = strict['correct']*100/strict['total'] if strict['total'] else 0
    evaluations=[e for r in runs for e in r.get('evaluations',[])]
    reasons = Counter(reason for e in evaluations for reason in e.get('reason_codes',[]))
    measurements=[metrics for r in runs for metrics in (r['metrics'],r.get('analysis_metrics')) if metrics is not None]
    calls=sum(m['provider_calls'] for m in measurements)
    available=all(m['token_usage'] is not None for m in measurements)
    tokens={k:sum(m['token_usage'][k] for m in measurements) for k in TOKENS} if available else None
    same_person=all(len({r.get('owner_id') for r in c['resumes']})==1 and all(r.get('owner_id') for r in c['resumes']) for c in cases)
    quotes=sum(e.get('quote_count',0) for e in evaluations)
    quote_errors=sum(e.get('quote_validation_failures',0) for e in evaluations)
    quality_complete = all(r.get('comparison_complete') for r in runs if r['phase'] in {'fixed_rubric','cold'}) and bool(runs)
    cold_pairs=baseline_pairs(cases,[r for r in runs if r['phase']=='cold'])
    cold_complete=all(len([r for r in runs if r['case_id']==c['id'] and r['phase']=='cold'])==3 for c in cases)
    development_checks=dict(three_cold_runs=cold_complete, cold_preferences=cold_pairs['correct']==cold_pairs['total'], reviewed_ties=reviewed_ties['correct']==reviewed_ties['total'], live_provider=execution=='live' and calls>0, reviewed_labels=review_verified,
        same_person=same_person, real_sources=all(c['source_type']=='anonymized_real' for c in cases),
        three_fixed_runs=repeats_complete, complete_evaluations=quality_complete,
        no_preference_reversal=strict['reversed']==0 and strict['unscored']==0 and strict['tied']==0,
        stable_evidence_order=not changed_pairs and not unscored_pairs,
        frozen_rubric=rubric_drift['fixed_cases']==0, quote_provenance=quote_errors==0 and quotes>0,
        supported_scores=all(not e.get('unsupported_score',True) for e in evaluations),
        request_budget=all(not r['metrics'].get('request_limit_reached',False) for r in runs))
    dev_pass=all(development_checks.values())
    holdout_jobs=len({source_hash(c['job_text']) for c in cases if c['split']=='holdout'})
    holdout_pairs=sum(len(c.get('expected_pairs',[])) for c in cases if c['split']=='holdout')
    release_checks={**development_checks, 'holdout_only':all(c['split']=='holdout' for c in cases),
        'ten_real_jobs_twenty_pairs':holdout_jobs>=10 and holdout_pairs>=20,
        'ninety_percent_each_run':all(sum(_order(r,a,b)==1 for c in cases for r in runs if r['case_id']==c['id'] and r['phase']=='fixed_rubric' and r['repeat']==i for a,b in c.get('expected_pairs',[]))*100/max(holdout_pairs,1)>=90 for i in range(3)),
        'live_performance_and_cache':False, 'development_passed_before_holdout':False}
    # Release-only agreement permits reviewed mistakes under 90%; zero reversal is a development gate.
    release_checks.pop('no_preference_reversal')
    release_checks.pop('cold_preferences')
    release_checks['strict_pairs_scored_without_ties']=strict['unscored']==0 and strict['tied']==0
    safe_runs=[]
    contents={c['id']:{r['id']:r['content'] for r in c['resumes']} for c in cases}
    for run in runs:
        fields=('case_id','phase','repeat','elapsed_seconds','comparison_complete','job_fingerprint','metrics','analysis_seconds','analysis_metrics','analysis_succeeded','full_journey_seconds','same_scores_and_ids','score_changes','ranking_changes','completeness_regression')
        safe={k:run[k] for k in fields if k in run}
        safe['evaluations']=[_safe_evaluation(e,contents[run['case_id']].get(e['resume_id'],'')) for e in run.get('evaluations',[])]
        safe_runs.append(safe)
    return dict(execution=execution, provider=provider, strict_pairs=strict, cold_strict_pairs=cold_pairs, reviewed_ties=reviewed_ties,
        complete_evaluations=sum(e.get('status')=='complete' for e in evaluations),
        incomplete_evaluations=sum(e.get('status')!='complete' for e in evaluations), reason_codes=dict(reasons),
        quote_validation_failures=quote_errors, validated_quotes=quotes, provider_calls=calls, token_usage=tokens, usage_available=available,
        suite_elapsed_seconds=suite_elapsed_seconds, runs=safe_runs,
        stability=dict(reversed_pairs=len(reversed_pairs),changed_pairs=len(changed_pairs),unscored_pairs=len(unscored_pairs),score_drift_resumes=len(score_drift)),
        rubric_drift=rubric_drift, holdout_jobs=holdout_jobs, holdout_strict_labels=holdout_pairs,
        development_gate_passed=dev_pass, release_gate_passed=False,
        gates=release_checks, failed_gates=[k for k,v in release_checks.items() if not v])


def _stored_cases(storage, case):
    stored=[storage.add_resume(r['id'],r['content'],user_id='benchmark',extraction_warnings=r.get('extraction_warnings',[])) for r in case['resumes']]
    return stored, {r.id:spec['id'] for r,spec in zip(stored,case['resumes'])}


def _measure(case, phase, repeat, engine, operation, aliases, sources):
    mark=engine.mark(); started=time.monotonic()
    try:
        batch=operation()
        rows=batch.model_dump(mode='json')['evaluations']
        complete=batch.comparison_complete
        job=batch.job_fingerprint
    except Exception:
        rows=[dict(resume_id=id,status='failed',reason_codes=['benchmark_operation_failed']) for id in aliases]
        complete=False; job=source_hash(case['job_text'])
    metrics=engine.since(mark)
    metrics['full_source_resume_ids']=sorted({aliases.get(id,id) for id in metrics['full_source_resume_ids']})
    result=[]
    for e in rows:
        id=e['resume_id']; e['resume_id']=aliases.get(id,id)
        result.append(_projection(e,sources.get(id,'')))
    return dict(case_id=case['id'],phase=phase,repeat=repeat,job_fingerprint=job,
                elapsed_seconds=time.monotonic()-started,comparison_complete=complete,evaluations=result,metrics=metrics)


def _same(a,b):
    return a['comparison_complete'] and b['comparison_complete'] and sorted((e['resume_id'],e.get('raw_score'),e.get('evaluation_id')) for e in a['evaluations'])==sorted((e['resume_id'],e.get('raw_score'),e.get('evaluation_id')) for e in b['evaluations'])


def run_lifecycle(case, *, engine, as_of):
    from backend.storage import StorageService
    from backend.services.matching import pipeline, profiles, scoring
    validate_cases([case])
    runs=[]
    with tempfile.TemporaryDirectory(prefix='matching-benchmark-') as folder:
        storage=StorageService(str(Path(folder)/'isolated.db'),force_sqlite=True)
        try:
            resumes,aliases=_stored_cases(storage,case)
            mark=engine.mark(); started=time.monotonic()
            profiles_ready=[profiles.get_or_build_resume_profile(r,user_id='benchmark',engine=engine,storage=storage,deadline=time.monotonic()+300).status=='complete' for r in resumes]
            runs.append(dict(case_id=case['id'],phase='profile_preparation',repeat=0,elapsed_seconds=time.monotonic()-started,
                comparison_complete=all(profiles_ready),evaluations=[],metrics=engine.since(mark)))
            def measure(phase,job=None):
                sources={r.id:r.content for r in resumes}
                return _measure(case,phase,0,engine,lambda:pipeline.evaluate_resumes(job or case['job_text'],resumes,user_id='benchmark',as_of=as_of,engine=engine,storage=storage),aliases,sources)
            first=measure('prepared_first_job'); runs.append(first)
            if case.get('second_job_text'): runs.append(measure('second_job',case['second_job_text']))
            warm=measure('warm'); warm['same_scores_and_ids']=_same(first,warm); runs.append(warm)
            edit=case.get('edited_resume')
            if edit:
                id=next(id for id,alias in aliases.items() if alias==edit['id'])
                storage.update_resume(id,content=edit['content'],user_id='benchmark')
                resumes=[storage.get_resume(r.id,user_id='benchmark') for r in resumes]
                previous=measure('edited_resume'); runs.append(previous)
            else: previous=warm
            original=scoring.SCORER_VERSION
            try:
                scoring.SCORER_VERSION=original+'-benchmark'
                bumped=measure('scorer_only'); bumped['same_scores_and_ids']=_same(previous,bumped); runs.append(bumped)
            finally: scoring.SCORER_VERSION=original
        finally: storage.close()
    return runs


def _full_source(case, resumes, aliases, frozen_batch, storage, engine, as_of):
    from backend.services.matching import extraction, scoring
    from backend.services.matching.models import Evaluation, EvaluationBatch, RequirementExtraction
    from backend.services.matching.pipeline import rubric_version_key
    row=storage.get_matching_rubric(user_id='benchmark',job_hash=source_hash(case['job_text']),version_key=rubric_version_key(engine))
    if not row:
        raise ValueError('No frozen rubric for source diagnostic')
    requirements=RequirementExtraction.model_validate_json(row['payload_json']).items
    deadline=time.monotonic()+300
    evidence=extraction.extract_evidence_batch(resumes,{},requirements,as_of=as_of,engine=engine,deadline=deadline)
    evaluations=[]
    for resume in resumes:
        extracted=evidence[resume.id]
        common=dict(resume_id=resume.id,status=extracted.status,as_of=as_of,job_fingerprint=source_hash(case['job_text']),
                    resume_fingerprint=source_hash(resume.content),source_fingerprint=source_hash(resume.content),
                    rubric_fingerprint=row['rubric_fingerprint'],scorer_version=scoring.SCORER_VERSION)
        if extracted.status=='complete':
            common.update(scoring.calculate_score(requirements,extracted.items,as_of=as_of).model_dump())
        else:
            common['reason_codes']=extracted.warnings or ['missing_assessment']
        evaluations.append(Evaluation(**common))
    ranked=scoring.rank_evaluations(evaluations)
    return EvaluationBatch(job_fingerprint=source_hash(case['job_text']),comparison_complete=all(e.status=='complete' for e in ranked),evaluations=ranked)


def run_quality(cases, *, engine, as_of):
    from backend.storage import StorageService
    from backend.services.matching.pipeline import evaluate_resumes
    validate_cases(cases); runs=[]
    for case in cases:
        for repeat in range(3):
            if engine.exhausted: break
            with tempfile.TemporaryDirectory(prefix='matching-quality-') as folder:
                storage=StorageService(str(Path(folder)/'isolated.db'),force_sqlite=True)
                try:
                    resumes,aliases=_stored_cases(storage,case); sources={r.id:r.content for r in resumes}
                    def evaluate(fresh=False):
                        return evaluate_resumes(case['job_text'],resumes,user_id='benchmark',as_of=as_of,engine=engine,storage=storage,fresh=fresh)
                    analysis_seconds=None; analysis_metrics=None; analysis_succeeded=None
                    if hasattr(engine.engine,'analyze_job'):
                        mark=engine.mark(); start=time.monotonic()
                        try:
                            engine.invoke('analysis','analyze_job',case['job_text']); analysis_succeeded=True
                        except Exception: analysis_succeeded=False
                        analysis_seconds=time.monotonic()-start; analysis_metrics=engine.since(mark)
                    cold=_measure(case,'cold',repeat,engine,evaluate,aliases,sources)
                    cold.update(analysis_seconds=analysis_seconds,analysis_metrics=analysis_metrics,analysis_succeeded=analysis_succeeded,
                                full_journey_seconds=cold['elapsed_seconds']+analysis_seconds if analysis_seconds is not None else None)
                    runs.append(cold)
                    if repeat==0:
                        for index in range(3):
                            if engine.exhausted: break
                            runs.append(_measure(case,'fixed_rubric',index,engine,lambda:evaluate(True),aliases,sources))
                        if not engine.exhausted:
                            full=_measure(case,'full_source',0,engine,lambda:_full_source(case,resumes,aliases,cold,storage,engine,as_of),aliases,sources)
                            first={e['resume_id']:e for e in cold['evaluations']}; second={e['resume_id']:e for e in full['evaluations']}
                            full['score_changes']=sum(first[id].get('raw_score')!=second[id].get('raw_score') for id in first)
                            full['ranking_changes']=sum(_order(cold,a,b)!=_order(full,a,b) for a,b in combinations(sorted(first),2))
                            full['completeness_regression']=cold['comparison_complete'] and not full['comparison_complete']
                            runs.append(full)
                finally: storage.close()
    return runs


def performance_gate(evidence):
    cold=evidence.get('cold',[])
    main=evidence.get('main_cold',[])
    phases={r['phase']:r for r in evidence.get('lifecycle',[])}
    required={'profile_preparation','prepared_first_job','second_job','warm','edited_resume','scorer_only'}
    if not required<=set(phases): return False
    return bool(evidence.get('execution')=='live' and evidence.get('job_chars')==8000 and evidence.get('resume_chars')==[8000]*5
        and len(cold)==3 and all(r['comparison_complete'] and r['elapsed_seconds']<=120 and r['metrics']['provider_calls']>0 for r in cold)
        and len(main)==3 and all(r['comparison_complete'] and r['metrics']['provider_calls']>0 for r in main)
        and all(r['comparison_complete'] for r in phases.values())
        and phases['prepared_first_job']['metrics']['stages'].get('resume_profile',{}).get('calls',0)==0
        and phases['second_job']['metrics']['stages'].get('resume_profile',{}).get('calls',0)==0
        and phases['edited_resume']['metrics']['stages'].get('resume_profile',{}).get('calls',0)==1
        and all(phases[p]['metrics']['provider_calls']==0 and phases[p].get('same_scores_and_ids') for p in ('warm','scorer_only')))


def load_live_inputs(fixture, review_path, *, phase, development_report, provider):
    if phase=='holdout':
        if not development_report:
            raise ValueError('Passing development evidence is required before opening holdout data')
        try: development=json.loads(Path(development_report).read_text(encoding='utf-8'))
        except (OSError,ValueError): raise ValueError('Passing development evidence is unavailable') from None
        if not (development.get('execution')=='live' and development.get('development_gate_passed') is True and development.get('provider')==provider):
            raise ValueError('Passing development evidence must use this approved provider/model')
    try:
        raw=Path(fixture).read_bytes(); cases=json.loads(raw.decode('utf-8'))
        review=json.loads(Path(review_path).read_text(encoding='utf-8'))
    except (OSError,ValueError): raise ValueError('Allowed fixture or review record is unavailable') from None
    digest=hashlib.sha256(raw).hexdigest()
    validate_cases(cases)
    if any(c['split']!=phase for c in cases): raise ValueError('Keep development and holdout in separate fixture files')
    if not verify_review(cases,review,digest): raise ValueError('An exact hash-bound human review and provider-use permission is required')
    if phase=='holdout' and (len({source_hash(c['job_text']) for c in cases})<10 or sum(len(c.get('expected_pairs',[])) for c in cases)<20):
        raise ValueError('Holdout requires at least ten jobs and twenty reviewed strict pairs')
    return cases,digest


def _git(*args):
    return subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}',*args],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()


def _engine(max_calls):
    from backend.services.ai_engine import AIEngine
    values=[os.getenv(k,'').strip() for k in ('MATCHING_BENCHMARK_BASE_URL','MATCHING_BENCHMARK_MODEL','MATCHING_BENCHMARK_API_KEY')]
    if not all(values): raise ValueError('Set explicit benchmark endpoint, model and key environment variables')
    parts=urlsplit(values[0])
    if parts.username or parts.password or parts.query or parts.fragment: raise ValueError('Provider URL must not contain credentials or query parameters')
    if values[1] in {'offline','offline-heuristic'}: raise ValueError('An AI model is required')
    return CountingEngine(AIEngine(api_base_url=values[0],model_name=values[1],api_key=values[2]),max_calls=max_calls)


def _legacy_cases(cases, engine, as_of):
    from backend.models import Resume
    runs=[]
    for c in cases:
        resumes=[Resume(id=r['id'],name=r['id'],content=r['content']) for r in c['resumes']]
        for repeat in range(3):
            if engine.exhausted: break
            mark=engine.mark(); start=time.monotonic(); analyzed=time.monotonic()
            try:
                job=engine.invoke('analysis','analyze_job',c['job_text'])
                analysis=time.monotonic()-analyzed; ranked_at=time.monotonic()
                results=engine.invoke('legacy_ranking','rank_resumes',resumes,job)
                elapsed=time.monotonic()-ranked_at
                rows=[dict(resume_id=r.resume_id,status='complete',match_score=r.match_score,raw_score=str(r.match_score),
                    score_scope='legacy_keyword_alignment',source_fingerprint=source_hash(next(v.content for v in resumes if v.id==r.resume_id))) for r in results]
                complete={e['resume_id'] for e in rows}=={r.id for r in resumes} and engine.since(mark)['failures']==0 and engine.since(mark)['provider_calls']>0
            except Exception:
                analysis=None; elapsed=time.monotonic()-start; rows=[]; complete=False
            runs.append(dict(case_id=c['id'],phase='legacy_cold',repeat=repeat,job_fingerprint=source_hash(c['job_text']),evaluations=rows,
                comparison_complete=complete,analysis_seconds=analysis,elapsed_seconds=elapsed,
                full_journey_seconds=time.monotonic()-start,metrics=engine.since(mark)))
    return runs


def _baseline_worker(folder, payload):
    sys.path.insert(0,str(Path(folder).resolve()))
    with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
        engine=_engine(payload['max_calls'])
        rows=_legacy_cases(payload['cases'],engine,date.fromisoformat(payload['as_of']))
    return dict(runs=rows,metrics=engine.since(0),scope='legacy_keyword_alignment')


def run_main_baseline(cases, *, as_of, max_calls, ref=BASELINE_REF):
    commit=_git('rev-parse',ref+'^{commit}')
    with tempfile.TemporaryDirectory(prefix='matching-main-baseline-') as folder:
        archive=Path(folder)/'baseline.zip'
        subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}','archive','--format=zip','-o',str(archive),commit,'backend'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        with zipfile.ZipFile(archive) as files:
            files.extractall(folder)
        worker=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--baseline-worker',folder],
            input=json.dumps(dict(cases=cases,as_of=as_of.isoformat(),max_calls=max_calls)),text=True,
            capture_output=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'},check=False)
        if worker.returncode: raise ValueError('Pinned main baseline failed; no provider response is exposed')
        result=json.loads(worker.stdout)
    return {**result,'commit':commit}


def main(argv=None):
    # Disable automatic personal .env loading; benchmark keys are explicit and storage is isolated.
    os.environ['PYTHON_DOTENV_DISABLED']='1'
    os.environ.setdefault('JWT_SECRET_KEY',secrets.token_urlsafe(48))
    os.environ.setdefault('SETTINGS_ENCRYPTION_KEY',secrets.token_urlsafe(48))
    arguments=sys.argv[1:] if argv is None else argv
    if len(arguments)==2 and arguments[0]=='--baseline-worker':
        print(json.dumps(_baseline_worker(arguments[1],json.load(sys.stdin))))
        return 0
    parser=argparse.ArgumentParser(description='Measure approved AI resume-version ranking; no rollout flag is changed.')
    parser.add_argument('--live',action='store_true',help='Explicitly select provider calls with reviewed, allowed inputs')
    parser.add_argument('--fixture',type=Path,required=True)
    parser.add_argument('--review-record',type=Path,required=True)
    parser.add_argument('--phase',choices=('dev','holdout'),default='dev')
    parser.add_argument('--development-report',type=Path)
    parser.add_argument('--max-provider-calls',type=int,required=True)
    parser.add_argument('--performance-fixture',type=Path)
    parser.add_argument('--performance-review-record',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(arguments)
    if not args.live: parser.error('Select --live only after provider, reviewed inputs and request limit are approved')
    if args.max_provider_calls<1: parser.error('Provider request limit must be positive')
    provider=dict(host=urlsplit(os.getenv('MATCHING_BENCHMARK_BASE_URL','')).hostname,model=os.getenv('MATCHING_BENCHMARK_MODEL',''),endpoint_fingerprint=source_hash(os.getenv('MATCHING_BENCHMARK_BASE_URL','')))
    try:
        candidate_commit=_git('rev-parse','HEAD')
        if _git('status','--porcelain'): raise ValueError('Commit the benchmark before taking live measurements')
        cases,digest=load_live_inputs(args.fixture,args.review_record,phase=args.phase,development_report=args.development_report,provider=provider)
        if args.phase=='holdout':
            development=json.loads(args.development_report.read_text(encoding='utf-8'))
            if development.get('candidate_commit')!=candidate_commit: raise ValueError('Development evidence must cover the unchanged candidate commit')
        performance_cases=None
        if bool(args.performance_fixture)!=bool(args.performance_review_record): raise ValueError('Performance fixture and its review record must be provided together')
        if args.performance_fixture:
            performance_cases,_=load_live_inputs(args.performance_fixture,args.performance_review_record,phase='dev',development_report=None,provider=provider)
            if len(performance_cases)!=1 or len(performance_cases[0]['job_text'])!=8000 or [len(r['content']) for r in performance_cases[0]['resumes']]!=[8000]*5:
                raise ValueError('Performance input must contain one 8000-character JD and five 8000-character versions')
        started=time.monotonic(); as_of=date.today()
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            baseline_cases=validate_cases(cases+(performance_cases or []))
            baseline=run_main_baseline(baseline_cases,as_of=as_of,max_calls=args.max_provider_calls)
            baseline['strict_pairs']=baseline_pairs(cases,baseline['runs'])
            remaining=args.max_provider_calls-baseline['metrics']['provider_calls']
            engine=_engine(max(remaining,1))
            engine.exhausted=remaining<1
            quality=run_quality(cases,engine=engine,as_of=as_of)
            lifecycle=run_lifecycle(cases[0],engine=engine,as_of=as_of) if not engine.exhausted else []
            performance=None
            if performance_cases and not engine.exhausted:
                perf=performance_cases[0]
                perf_runs=run_quality([perf],engine=engine,as_of=as_of)
                perf_lifecycle=run_lifecycle(perf,engine=engine,as_of=as_of) if not engine.exhausted else []
                performance=dict(execution='live',job_chars=8000,resume_chars=[8000]*5,cold=[r for r in perf_runs if r['phase']=='cold'],lifecycle=perf_lifecycle,main_cold=[r for r in baseline['runs'] if r['case_id']==perf['id']])
                performance['matching_latency_deltas']=[new['elapsed_seconds']-old['elapsed_seconds'] for new,old in zip(performance['cold'],performance['main_cold'])]
                performance['journey_latency_deltas']=[new['full_journey_seconds']-old['full_journey_seconds'] for new,old in zip(performance['cold'],performance['main_cold']) if new.get('full_journey_seconds') is not None]
        report=build_report(cases,quality+lifecycle,execution='live',review_verified=True,provider=provider,suite_elapsed_seconds=time.monotonic()-started)
        report.update(candidate_commit=candidate_commit,baseline=baseline,fixture_sha256=digest,as_of=as_of.isoformat(),performance=performance,
            all_provider_metrics=engine.since(0),baseline_provider_calls=baseline['metrics']['provider_calls'],
            total_provider_calls=baseline['metrics']['provider_calls']+engine.since(0)['provider_calls'],request_limit=args.max_provider_calls)
        totals=engine.since(0)
        report.update(provider_calls=totals['provider_calls'],token_usage=totals['token_usage'],usage_available=totals['usage_available'])
        baseline_tokens=baseline['metrics']['token_usage']
        report['total_token_usage']={k:baseline_tokens[k]+totals['token_usage'][k] for k in TOKENS} if baseline_tokens is not None and totals['token_usage'] is not None else None
        compared=[r for r in quality+lifecycle if r['phase'] not in {'full_source','profile_preparation'}]
        report['profile_fallback']=dict(resume_chunks=sum(r['metrics']['full_source_resume_chunks'] for r in compared),resume_comparisons=sum(len(r['evaluations']) for r in compared),resume_fallbacks=sum(len(r['metrics']['full_source_resume_ids']) for r in compared))
        report['gates']['live_performance_and_cache']=performance_gate(performance or {})
        report['gates']['development_passed_before_holdout']=args.phase=='holdout'
        diagnostics=[r for r in quality if r['phase']=='full_source']
        report['gates']['profile_quality_preserved']=len(diagnostics)==len(cases) and all(r['comparison_complete'] and r['score_changes']==0 and r['ranking_changes']==0 for r in diagnostics)
        report['development_gate_passed'] &= report['gates']['profile_quality_preserved']
        report['release_gate_passed']=all(report['gates'].values())
        report['failed_gates']=[k for k,v in report['gates'].items() if not v]
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(dict(report=str(args.output),development_gate_passed=report['development_gate_passed'],release_gate_passed=report['release_gate_passed'],provider_calls=report['total_provider_calls'])))
        return 0 if (report['release_gate_passed'] if args.phase=='holdout' else report['development_gate_passed']) else 1
    except (ValueError,OSError,subprocess.SubprocessError):
        parser.error('Benchmark inputs or execution failed; verify reviewed files, provider configuration, committed code and request budget')


if __name__=='__main__':
    raise SystemExit(main())
