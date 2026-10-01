# AI overall job-fit evaluation

Task 9 is **in progress** on `feat/ai-overall-job-fit`. The initial live development benchmark failed completeness and quality gates. Measured fixes are implemented and undergoing verification; untouched holdout and actual-size performance evidence remain pending. The matching feature remains default-off. Synthetic tests establish report/cache behavior, not ranking quality, live speed or readiness for release.

## What is measured

`scripts/evaluate_matching.py` runs the actual matching services with temporary isolated SQLite databases. It uses no production vault and changes no rollout flags. Pinned main is `9fa7b26a4ca78c38dd977d1eff0df1f30c11b5c5`; an archived backend runs in a separate process, using the same explicitly selected provider/model and allowed documents. Formal candidate comparisons require committed, clean code; targeted diagnostics are recorded separately. Reports record both commits, source/profile/rubric/evaluation fingerprints, the date, provider host/model and endpoint fingerprint.

Each job receives three cold evaluations, each with a fresh vault/rubric/profile cache. For the first cold interpretation, three fresh evidence assessments reuse its frozen rubric and prepared profiles. Report cold rubric drift separately from fixed-rubric evidence/ranking drift. The full-source diagnostic assesses the same original documents against that frozen rubric, without a profile prefilter; compare completeness, raw scores and pair ordering for profile omissions.

The lifecycle measures upload/profile preparation, the first job with prepared profiles, a different job against the same saved vault, an identical warm repeat, one saved content edit, and a local scorer-version bump. The prepared/second jobs must reuse profiles, the edit must extract only one changed profile, and warm/scorer-only runs must make zero provider calls and preserve evaluation IDs/raw scores. A scorer-version bump is a measurement of existing invalidation rules, never a score override.

Calls are counted at the SDK request boundary, including analysis, profile preparation, requirements and semantic assessment; the guarded client disables SDK retries. One hard request cap covers baseline and candidate together. Tokens are aggregated only when every corresponding response reports usage; missing usage remains null/unavailable. Report individual comparison duration separately from suite duration and include the upstream analysis duration in full-journey measurements. Failed or budget-denied measurements cannot pass completeness gates.

## Quality and performance gates

Strict human preferences retain correct, tied, reversed and unscored observations in their denominator. Explicitly reviewed ties have separate measurements. Main scores are labeled `legacy_keyword_alignment`, and their pair agreement is measured independently; they are not interchangeable with overall job-fit percentages.

Development requires allowed real versions of the same person's resume, an exact hash-bound human review record, three complete cold runs and three complete fixed-rubric runs per job, correct reviewed strict preferences, stable fixed-rubric ordering, valid quote provenance, and a complete full-source comparison preserving score/order. Synthetic or cross-person data cannot establish this result.

Holdout inputs are opened only after a passing live development report from the same provider and unchanged candidate commit. Holdout requires at least ten distinct real jobs and twenty strict human-reviewed pairs. Each of three frozen-rubric repetitions must reach at least 90% strict agreement, with complete evaluations, no tied/unscored strict preferences and no invalid positive quotes. Development examples and holdout labels must stay separate.

Performance uses one full authorized real JD and five full authorized real resume versions at their actual lengths, three complete cold comparisons each within 120 seconds, the complete cache lifecycle, and three measured main cold baselines. Reports include main/candidate comparison and full-journey latency deltas plus provider calls/tokens; regressions are reported rather than hidden in a suite total. The owner waived the exact 8,000-character workload. Do not pad or truncate documents to claim real-input performance.

The release gate stays false unless every required quality, development, performance and cache check passes. Failing gates and reason counts remain in the report; no benchmark run activates the application feature.

## Current inputs and outstanding evidence

The owner authorized documents in `D:/Grind/Resume stuff/No named resumes` and the saved `exp/gpt6 luna` profile, model `gpt-6-luna`. Provider metadata was located with a read-only database query; no key was printed. Five PDF resumes extracted without warnings. Two complete development JDs were selected from `JOB Descriptions.docx`; `JD 2nd set.docx` remains unopened for holdout.

Local inputs in `tests/fixtures/matching/private-dev.json` remove contact headers and consistently replace personal employer, institution and project names. They remain Git-ignored, along with their review record. Proposed preferences and the lifecycle edit are available locally in `scratch/task9-development-review.md`. The owner reviewed and accepted the four proposed preferences. The owner confirmed same-person ownership, all four proposed strict preferences, and a cap of 100 provider requests total for the initial main/candidate development benchmark. This does not authorize further reruns or holdout requests.

Current anonymized resumes contain 3,215–4,502 characters and the two development JDs contain 5,168 and 5,594 characters. These full documents are now the owner-approved performance workload; actual performance and a separately reviewed holdout remain outstanding. The encrypted saved-profile key could not be decrypted locally, but the owner confirmed an explicit `MATCHING_BENCHMARK_API_KEY` already existed in the source project dotenv. The resumed run used that explicit key with the approved saved-profile endpoint/model; no key was printed or changed.

## Running an authorized measurement

Provide only the selected endpoint/model/key through process-local `MATCHING_BENCHMARK_BASE_URL`, `MATCHING_BENCHMARK_MODEL` and `MATCHING_BENCHMARK_API_KEY`. Do not put keys in shell history, reports, argument lists or fixture files. Automatic personal dotenv loading is disabled. Saved keys should be decrypted privately in the launcher process, without opening the application's storage service or changing the provider profile.

A fixture is a JSON list of cases containing an anonymous `id`, `split`, `source_type`, full `job_text`, two to five resume versions (`id`, anonymous `owner_id`, full `content`), `expected_pairs` in preferred-first order and optional `expected_ties`. The lifecycle case also supplies a different `second_job_text` and an `edited_resume` referring to exactly one version with genuinely changed text. The review JSON contains `reviewed_by`, ISO `reviewed_at`, the SHA-256 of the exact fixture bytes, all `case_ids`, and explicit `approved_for_provider_use: true`. A machine must not invent the human review.

```text
python -B scripts/evaluate_matching.py --live
  --fixture tests/fixtures/matching/private-dev.json
  --review-record tests/fixtures/matching/private-dev-review.json
  --phase dev --max-provider-calls <approved-limit>
  --output scratch/matching/development-report.json
```

The example is one command, wrapped here for readability. Holdout additionally requires `--phase holdout --development-report <passing-report>`. By default, performance reuses the first reviewed five-version quality case and its measurements. A separate workload requires both `--performance-fixture` and `--performance-review-record`. Case IDs must remain unique across quality and performance fixtures. Reports contain validated evidence counts and category/skill scores, not document text, quotes, keys or response bodies. Inspect `development_gate_passed`, `release_gate_passed`, `failed_gates`, measurement completeness and token availability; an exit code alone is insufficient for diagnosis.

## Local verification

The initial dedicated benchmark suite passed 28 checks covering denominator/tie behavior, raw-score comparison, incomplete results, unavailable usage, source/secret projection, actual SDK call limits, real service cache lifecycle, frozen-rubric repeats, full-source diagnostics, input/review validation, and refusal to open holdout before development passes. The fresh full backend suite passed all 439 tests; only the existing Starlette/AnyIO deprecation warning remains. Existing frontend behavior is unchanged by this benchmark.


## Initial live development results — 2026-09-30

Provider: approved `gpt-6-luna` on the saved Experiential endpoint. Main commit: `9fa7b26a4ca78c38dd977d1eff0df1f30c11b5c5`. Candidate commit: `841dafe92d641a18af88ba356ae59a5091fb9946`. Two reviewed jobs, five versions of one person's resume, four strict preferences, three cold and three fresh-evidence observations per job. The untouched holdout was not opened.

| Measurement | Pinned main | Initial candidate |
|---|---:|---:|
| Complete cold comparisons | 6/6 | 0/6 |
| Strict preference observations correct | 9/12 (75%) | 0/12; all 12 unscored |
| Cold matching duration | 13.78–16.67 seconds | 30.01–165.71 seconds; incomplete |
| Main full journey including analysis | 18.82–24.55 seconds | Reported per run; incomplete |
| Provider requests | 12 | 61 |
| Total token usage | 43,521 | Unavailable because some requests failed |

Main reversed the reviewed FS-over-Python preference for the Java/full-stack job in all three repetitions. This is measured legacy keyword alignment, not a calibrated overall-fit percentage. The candidate produced no usable rankings, so it cannot claim improved ordering or speed. The benchmark suite took 1,656.23 seconds; this is not individual comparison latency. No cache/performance gate passed.

The candidate recorded 23 SDK failures, repeatedly around 30 seconds, despite the matching caller requesting up to 90 seconds. Its successful QA profile responses were also rejected by source validation. The report contains 90 `invalid_provider_response` evaluation observations and five `benchmark_operation_failed` observations from a full-source diagnostic without a frozen rubric; these are repeated measurements, not unique people/resumes.

A separate one-request diagnostic on the shortest reviewed resume returned usable JSON but fourteen unsupported skill facts. Some keys expanded acronyms or turned work activities into skill names absent from the quote. A valid REST APIs phrase also crossed a PDF line break and failed the literal matcher. After that diagnostic, recorded usage is **74/100 authorized requests**, leaving 26 for targeted checks. Aggregate token usage remains unavailable; the diagnostic itself reported 4,693 tokens. Raw responses and documents stay only in ignored private fixture files; the machine report is local at `scratch/matching/development-report.json`.

### Fixes traced to these measurements

- The guarded AI transport honors the SDK's finite positive read budget, capped at 90 seconds; explicit earlier deadlines and all DNS, port, redirect and response-size rules remain enforced. Ordinary outbound requests retain their 30-second default.
- Shared literal matching accepts whitespace between phrase words, including PDF line breaks, while retaining punctuation/token boundaries and exact original source spans.
- Source section checks recognize `Technical Skills and Tools` and `Education & Certificates`, prevent demonstrated-work credit for skills lists, and prevent dated work spans crossing into the combined education section.
- JD/profile prompts require literal skill names/acronyms from their quotes and classify described work activities separately. Unsupported expansions remain rejected. JD, profile and assessment versions are bumped to invalidate earlier derived artifacts.
- Fixed-rubric evidence repeats require prepared profiles. Failed upload preparation stops the lifecycle measurement instead of repeatedly rebuilding failed profiles under warm/scorer labels. Missing phases cannot pass any gate.

The first fixes passed 153 focused checks and all 448 backend tests. A subsequent bounded correction pass has passed 174 focused checks; all 452 backend tests also pass, and live smoke is pending. No passing development/holdout claim is made.


### Targeted follow-up and bounded correction

Candidate `296a316` received nine requests on the already reviewed QA-over-Java-without-skills pair. All nine SDK requests returned without transport failure (43,920 reported tokens), but none of the three cold comparisons completed. A source-backed Java profile was accepted; the QA profile still proposed a nonliteral Database skill. JD and evidence responses also failed strict source/schema validation. A one-request pipeline trace then identified a JD quote absent verbatim from the source. Cumulative development usage is **84/100 requests**, with 16 remaining. These are targeted diagnoses, not passing full-development observations.

One received response rejected by schema/source checks now receives at most one correction request using the identical source, schema and original deadline. The rejected response is untrusted input; feedback uses a fixed reason without private exception text or desired winners. The corrected response passes the same validator. Network failures, explicitly incomplete source, and missing/unresolved evidence do not trigger this correction. JD/profile/assessment versions invalidate earlier cached artifacts. No new dependencies or scoring weights were added.

During Task 9 the primary checkout independently moved onto `feat/ai-overall-job-fit`; the managed worktree became detached. The clean primary feature branch was safely fast-forwarded to the tested fixes. The original `feat/evidence-based-resume-matching` ref remains pinned at `bccc938`; historical source-file hash checks refer to that earlier checkout, not the now-switched primary directory. No PR, release activation or holdout access occurred.


### First correction smoke and JSON diagnosis

At `5b74b0c`, a cold comparison of the reviewed QA-over-Java-without-skills pair accepted the JD and both complete resume profiles. The evidence response failed JSON decoding, so both evaluations remained failed and unscored. This took 99.88 seconds and four provider requests (28,734 reported tokens), with zero SDK failures. This duration is matching only, without upstream job analysis. No warm or fixed-rubric repeats were attempted on the failed comparison.

One diagnostic repeated the identical evidence request. The provider reported `finish_reason=stop`; 3,311 content characters parsed as JSON (13,010 tokens). This establishes response-format variability, not a passing evidence assessment. Cumulative usage is **89/100 requests**, leaving 11. All-development token usage is still unavailable because earlier failed requests lacked usage.

The existing single-correction limit now also catches a received JSON decoding failure, supplies its body as untrusted feedback and keeps the same source, validator and deadline. It does not retry generic transport failures or allow a third attempt. A malformed-response check reproduced the failure before the fix; all 453 backend tests passed. Task 9 and all live release gates remain open.


### Final cold diagnostic and parser root cause

Candidate `248e5b2` used seven requests (77,311 reported tokens) in a 217.89-second cold QA-pair comparison. There were zero SDK failures. One ambiguous profile-evidence quote was corrected successfully; the full-source response and its correction both failed JSON decoding. Evaluations remained failed/unscored; no warm or fixed repeats followed. Cumulative usage is **96/100 requests**, leaving four.

Both JSON failures were `Extra data`: each contained an already complete JSON value followed by two closing delimiters. The shared parser now recovers only a complete value whose remaining suffix consists solely of whitespace/closing delimiters. Additional structured data and other trailing content cannot enter this fallback. Existing schema, complete coverage, original-quote and skill/section checks remain enforced. Cached extraction/assessment versions are bumped. An offline replay recovered the recorded full-source response and all 50 supplied evidence items for both resumes passed the unchanged source/coverage validator; this replay made zero provider requests and is not a live gate pass.

Fresh regression: **454 backend tests passed**, with the existing Starlette/AnyIO warning only. The last four requests are reserved for fresh full-source evidence against the recorded, validated development rubric. That diagnostic cannot establish cold/profile/cache performance or complete the broader development gates.


### Fresh source-only evidence results and remaining work

At candidate `c2b3f4105840721f8894688425d60e865eb192c4`, three fresh full-source comparisons used the same recorded, revalidated JD rubric and the reviewed QA-over-Java-without-skills pair. All three completed with source-validated evidence. The provider request payloads were identical; temperature remained zero. Each comparison used one evidence request, without profile preparation or upstream JD analysis. Total: three requests, 36,818 reported tokens, zero SDK failures.

| Repeat | QA raw score | Java without skills raw score | Reviewed order | Evidence duration |
|---|---:|---:|---|---:|
| 1 | 41.99 | 44.89 | Reversed | 47.85 s |
| 2 | 43.80 | 30.05 | Correct | 47.95 s |
| 3 | 40.18 | 36.56 | Correct | 47.28 s |

Strict agreement is **2/3 (66.7%)** on this single pair; no ties or unscored observations. This is not the full-development sample and does not satisfy its no-reversal rule. Source/schema completeness is now demonstrated for this targeted path, while ranking quality remains a failure.

Fourteen supplied semantic requirement credits varied across identical requests: five for Java without skills (three responsibilities, two required qualifications) and nine for QA (three responsibilities, six required qualifications). Literal skill credits did not vary in this diagnostic. Java responsibility coverage moved from 30.77% to 7.69% to 15.38%; QA responsibility coverage moved from 38.46% to 46.15% to 30.77%. The server applies deterministic scoring to those accepted evidence decisions. A valid source quote alone does not establish reliable semantic relevance or consistent grading.

**Next measured diagnosis:** review the unstable requirement/source pairings, distinguish direct action/object support from generic or transferable background, and tighten semantic evidence decisions without changing weights to fit expected winners. Then rerun the full two-job/five-version cold and frozen-rubric development comparisons plus the real cache lifecycle. Cold JD interpretation drift and profile-vs-source score/order agreement remain unverified on the latest candidate. No additional implementation is assumed from this report.

Cumulative approved development usage is **99/100 provider requests**, leaving one. Further development measurements need a higher approved total cap; no further calls or holdout access are authorized yet. Token usage for the entire campaign remains unavailable because earlier failed requests did not report usage; the figures above are known totals for each identified diagnostic, not a complete campaign total.

Task 9 remains in progress. Steps 4–7 are unchecked; Task 10 is pending. Holdout jobs/pairs remain separately unreviewed and unopened. Exact-size real performance inputs remain unavailable. The default-off feature flag is unchanged. Fresh backend regression remains 454 passed; only documentation changed after that verification. No PR, rollout or new GitHub push occurred.


### Development continuation: 200 total requests

The owner raised the development cap to **200 total requests**, not 200 additional; 99 were already consumed. The remaining semantic uncertainty is narrower than syntax/provenance: partial or related activities can receive inconsistent full-work credit. The assessment prompt now uses the original JD quote, direct action/object and every essential qualifier, scans every activity before absence, preserves true paraphrases and AND/OR meaning, and distinguishes work evidence from a tool/title/degree or unsupported extension to a different task. Only assessment version changes; profile/JD extraction and scorer weights remain unchanged.

The prior live control is the observed failure (2/3 reviewed order, 14 unstable semantic credits). Regression: 108 focused evidence/pipeline/provider/benchmark checks passed. A controlled three-repeat source comparison retains the exact original payload, including native IDs, frozen requirements and source text; only assessment instructions change. Its live outcome is pending. The broader development/cache/holdout/performance gates remain open.


### Controlled semantic result and profile-context waste

Candidate `4c6b60c` completed all three controlled source comparisons and matched the reviewed QA preference **3/3**, versus **2/3** under the previous instructions. Original request payloads, including native IDs/source/requirements, were asserted unchanged; no winner labels were supplied. Three requests brought usage to **102/200**. QA scores were 35.48, 30.77 and 43.08; Java without skills scored 30.05, 30.05 and 33.67. Scores still vary; this is a narrow development improvement, not the full gate.

A separate zero-request replay of complete recorded profiles traced unnecessary context inflation. The 3,215-character Java resume supplied 7,817 profile characters; merging overlapping original intervals preserves the same facts in 3,036 characters. The 3,842-character QA resume supplied 13,144 characters, exceeding the 8,000-character context limit and triggering source fallback; its merged context contains 3,236 characters. The existing extraction module now merges only overlapping/touching validated source intervals, retains every fact and original coordinate, and keeps nonoverlapping gaps and fallback/coverage rules. Profile caches remain reusable; only assessment identity changes.

The overlap regression reproduced source mode before the fix and profile mode afterward, with exact original evidence provenance and every fact retained. Fresh full backend regression: **455 passed**. Full five-version/two-job development and cache measurements are next; the untouched holdout and exact-size performance gates remain open.


### Real-size performance amendment and serial preparation diagnosis

The owner waived the fixed 8,000-character workload; full approved documents retain their actual lengths, with no padding/truncation. The 120-second target and quality/cache/holdout gates are unchanged. The five-version cold comparison at `7caa1ae` took 300.05 seconds and remained unscored: ten SDK calls, no evidence assessment reached, one SDK failure. JD extraction/correction took 66.34 seconds and seven serial profile requests took 233.45 seconds. Upstream job analysis took 7.36 seconds and is separately included in journey totals. Cumulative development usage is 112/200.

The existing two-worker pool now prepares resume profiles concurrently under the same shared deadline, preserving current-source checks and native cache writes. New regressions reproduced serial preparation failure and rejection of real-size performance evidence before implementation. Verification: 85 focused and 456 full backend tests passed, with the existing Starlette/AnyIO warning only. The fresh live retry is pending; no performance success is claimed.


### JD quote and alternative correction diagnosis

The live retry at `469bbbd` stopped before profile preparation: the first JD response contained ambiguous source quotes and invalid alternatives; its correction fixed the quotes but retained one-element alternatives and a group without an explicit OR. Three requests used 13,649 reported tokens, with zero SDK failures. The incomplete cold comparison took 49.78 seconds. Cumulative usage is 115/200; this does not measure the concurrent profile fix.

The JD instructions now require original sentences/bullets rather than isolated repeated names and explicitly distinguish empty single/AND alternatives from complete OR choices of at least two. The shared bounded correction reports only three fixed server rule codes for unique quotes, explicit OR groups and literal skill facts; unknown exceptions still receive generic feedback. No source validator or retry limit is relaxed. JD extraction identity is version 6; accepted reusable resume profiles and scoring weights stay unchanged. Verification: 155 focused and 456 full backend tests passed (existing Starlette/AnyIO warning only). Fresh live retry is pending.
