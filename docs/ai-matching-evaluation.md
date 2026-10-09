# AI skill-matching evaluation

## Current result — Task 9 completed, 2026-10-08

The owner explicitly deferred unseen-document validation and authorized completing implementation plus development validation. **Task 9 is complete on that basis; general extraction/ranking accuracy remains unverified and activation remains off.** Task 10 carries the deferred check.

The remaining gaps are implemented: explicit Agile/Scrum and SDLC/STLC component matching (without arbitrary slash splitting); and an authenticated in-vault review form for unsupported claims. Every skill requires an explicit exclude or supporting-text decision. Supporting text must locate a unique saved passage; validation reads its original full lines and wrapped context, preserving negation and learning. Exclusion keeps already verified occurrences. No AI call occurs during review. A token tied to the profile and transactional comparison protect against stale reviews, concurrent edits and cross-user access.

The final saved-data development check used the original captured 89-observation resume response, verified the rejected indices still matched the owner's 11 approved exclusions, and resolved them through the new review service. It retained 78 verified facts. The saved JD became 15 required groups and one preferred OR group. Eight required groups matched: programming languages, test automation frameworks, functional testing, end-to-end testing, CI/CD, SDLC, Agile and Scrum. Preferred coverage was zero. Independent arithmetic: `(60 × 8/15 + 5 × 0/1) / 65 × 100 = 49.23`; unweighted coverage 50%. The score change from 30.77 is exactly the three additional explicit compound components, not a weight change.

Local saved-response processing took **0.040 seconds**; cached fresh comparison **0.028 seconds**, identical result and zero extraction calls. These timings exclude the earlier live extraction and human review. This turn made **zero live AI requests**, usage remains **247/300**, 53 remaining. It does not measure cold extraction or unseen-document accuracy. Private evidence: `scratch/matching/task9-completion-result.json` and preserved original captures.

Final checks: **525 backend tests, 93 frontend tests and production build pass**. Source/review guards include negation, Java/JavaScript and SQL/NoSQL boundaries, conflicting/stale/foreign reviews, concurrent saved-text edits, duplicate-fact preservation and cached scoring. Fresh review found the wrapped-context omission, which was reproduced then fixed; no further substantive finding. One existing Starlette/AnyIO deprecation warning. Manual browser inspection not performed. JD extractor is v5 and matcher v4; existing profile-v5 facts are reused.

Next: Task 10 final regression, selective cleanup and release handoff, with the explicitly deferred unseen-document check before activation. No new live benchmark, push, PR or activation in Task 9 completion. Historical measurements and formerly open statuses below are retained as history and superseded by this result.

## Historical bounded result — 2026-10-08, local OR-group completion

**Task 9's revised implementation and bounded functional check are complete.** The production path accepts the reviewed saved resume and saved JD response, computes **30.77/100 skill fit**, and reproduces the identical comparison from cache with zero extraction calls. This is not a fresh unreviewed extraction or a general accuracy/performance pass. Feature remains default-off.

The backend now repairs separately proposed alternatives only when they share one exact source span and category and the combined list passes the existing complete explicit-OR validation. AND lists remain separate. Missing options, conflicting categories and invented acronym expansions remain blocked. Parenthetical names normalize only when the short and expanded forms resolve to the same known skill. JD extractor v4 and matcher v3 invalidate changed interpretations/results while retaining reusable resume profiles.

Final local saved-response processing took **0.039 seconds**; the fresh local comparison using both cached artifacts took **0.028 seconds**, produced identical results and made **zero extraction calls**. The original live inputs cost one resume request (5,167 tokens) and one JD request (3,317 tokens), with explicit human review of 11 resume exclusions in between. This implementation turn made **zero live requests**. Budget remains **247/300; 53 remaining**.

| Score component | Result |
|---|---|
| Required skill groups | 5/15 matched (33.33%) |
| Preferred OR group | 0/1 matched (0%) |
| Weighted score | `(60 × 5/15 + 5 × 0/1) / 65 × 100 = 30.77` |
| Unweighted coverage | 5/16 = 31.25% |

Matched groups: programming languages, test automation frameworks, functional testing, end-to-end testing, CI/CD. The preferred group is one requirement: WebdriverIO OR BDD OR performance testing.

Known accuracy limit: resume keys such as `agile/scrum` and `sdlc/stlc` do not currently split into component skills. Broad phrases such as testing methodologies also have no general semantic inference. Thus this score verifies the present deterministic rules, not comprehensive skill recognition. No additional synonyms or inferred credit were added to improve this example's score. One resume cannot demonstrate comparative ranking quality.

Validation: **517 backend tests passed**, followed by **88 focused pipeline/scoring/source tests** after the matcher version bump. The earlier 92 frontend tests and successful build still apply because this turn changed no frontend code. A fresh review found no substantive issue and recommended the applied matcher-version bump; the reviewer's independent test attempt was blocked by its temporary SQLite setup. Executor tests passed. Existing Starlette/AnyIO deprecation warning only.

Remaining work: Task 10/release preparation, broader unseen-document accuracy/performance checks, compound skill handling if product requirements warrant it, and a general user-facing cached-claim approval workflow. The current development exclusions were explicitly reviewed; they are not an automatic discard policy. No push, PR or activation. Private final evidence: `scratch/matching/task9-or-final-result.json` and the preserved original captures.

## Earlier result — 2026-10-08

**Task 9 remains open: reviewed resume preparation passes, but the single JD response fails OR-group validation.** No score was produced, no retry was made, and the feature remains default-off.

Implemented and verified: explicit testing shorthand and bounded neighboring-line recovery; wrapped negation/learning context is retained; valid resume facts survive unsupported claims in a cached `needs_review` profile. Scores are withheld until review. The vault exposes unresolved skills, including after reopening through a read-only cached-status endpoint. Repeated preparation reuses the review record without another AI request. There is no general approve/reject review endpoint yet; this development check applied the owner's explicit exclusions to a saved response.

The owner approved excluding observations 47, 48, 61, 74, 75, 80, 82, 83, 84, 85 and 88 from the original 89-observation resume response. All other observations were retained. Production preparation accepted **78 verified facts** in **0.098 seconds**, using the saved reviewed response and **zero new resume requests**. This is reviewed-input validation, not a fresh unreviewed extraction success.

The one authorized new JD extraction consumed **1 request**, **3,317 tokens** (2,222 input + 1,095 output), with **12.26 seconds** provider time and **13.06 seconds** through the comparison path. Transport and schema succeeded. Of 18 proposed requirements, 15 individually passed source validation. Three preferred items failed: the source says “WebdriverIO, BDD (Behavior Driven Development), or performance testing,” but the provider returned three independent requirements. The combined BDD name also differed from the literal source. Accepting the split would incorrectly treat alternatives as independent scoring requirements, so the batch remained unscored.

**Next:** resolve explicit source-backed OR grouping locally using this saved response, preserving the full option group and recognized acronym identity; add the smallest regression check, then replay locally. Do not run another live benchmark or silently drop preferred requirements. Cache timing and score for this pair are still unmeasured. General unseen-document quality/performance and activation remain separate pre-release work.

Verification after the follow-up review fixes: **514 backend tests, 92 frontend tests, production build passed**. Existing Starlette/AnyIO deprecation warning only. Important review findings fixed: wrapped negation/learning, shorthand OR omissions, and saved review visibility after reopening. Manual browser inspection was not performed. The review-record storage hash remains an unused internal column; cached facts are revalidated and review records cannot score.

Development usage: **247/300**, **53 remaining**. Private captures, approval record, diagnosis and result are in ignored `scratch/matching/task9-reviewed-*` and `task9-approved-*` files. Original provider captures were preserved. Changes are uncommitted in the managed C: worktree at detached HEAD 13cf424; no push, PR or activation occurred.

## Historical result — 2026-10-07

**Task 9 remains in progress.** The approved one-pass implementation is locally verified, but its one authorized production-pair check stopped at resume extraction. No live retry or repeated benchmark was run. The feature remains default-off. Larger unseen-document accuracy/performance validation is deferred to pre-release under the owner's revised plan.

Implemented: no automatic correction requests; source line references instead of AI-copied unique quotations; backend reconstruction of exact source spans; precise synonyms and clear testing-list expansion; directional mappings for programming languages, test automation frameworks and cloud platforms. JD v3 and matcher v2 reflect changed interpretations/results. Matching-only vocabulary preserves valid profile-v5 caches. Generic-duty exclusions were clarified in the extraction prompt; this is not proof that every model output follows them.

Verification: **490 backend tests passed** after review fixes, with one existing Starlette/AnyIO deprecation warning. Coverage includes warm/new-JD/edit/rename/scorer cache behavior, isolation, deterministic scoring, source bounds, negation, unknown skills and complete AND/OR groups. Review exposed three important bugs (whitespace roundtrip, full alias spans in OR groups, expanded-skill negation); all seven reproductions failed before fixes and passed afterward. No frontend changes; prior frontend/build results below are historical.

### Single production-pair attempt

| Measure | Result |
|---|---|
| Approved inputs | QA Engineer I JD (5,594 characters); QA–SDET resume (3,842 characters) |
| Provider/model | Approved Experiential / gpt-6-luna |
| Actual requests | **1**, resume preparation only; zero corrections |
| Resume preparation / total | 30.44 / 30.48 seconds |
| Reported tokens | 1,540 input + 3,627 output = **5,167** |
| Provider transport and JSON/schema | Succeeded; 89 skill observations returned |
| Backend source validation | Failed: 25 observations unsupported by their referenced source spans |
| JD extraction, comparison, score | Not attempted / no score |
| Cached live timing | Not measured because preparation failed |
| Total development usage | **246/300**, including historical reservations; **54 remaining** |

Local inspection of the saved response found two concrete gaps. First, the resume's `QA & Testing: Functional, Regression, ...` heading/list is expanded into names such as `functional testing`; the backend currently supports trailing shared-suffix lists but not this heading form. Phrases such as `unit and integration tests` also differ from returned `unit testing`. Second, some references miss the actual line: `REST APIs` appears on line 36 but was cited on line 37. Other observations infer a testing skill from a described outcome or activity; they must not all be accepted indiscriminately.

The failure is **source interpretation/reference validation**, not malformed JSON, transport failure or repeated AI requests. No new score or general accuracy improvement is claimed. The remaining work is to accept supported shorthand and recover source locations consistently without accepting invented skills, using the saved response as a local regression fixture first. The planned bounded stop was honored; no second live attempt was made.

Private artifacts remain ignored: `scratch/matching/task9-single-pass-production-result.json`, `scratch/matching/task9-single-pass-captures.json` and its isolated database. The shared D: budget and this active worktree's mirrored budget both record 246/300. Current implementation is in the managed C: worktree; the previous D: source checkout was not edited apart from its authorized request counter. No push, PR or activation.

## Historical continuation — 2026-10-01

**Task 9 has not passed.** Implementation and regression checks are complete, but the independent live development gate failed. The feature remains default-off; Task 10, holdout, publication and activation have not started. The owner granted 100 additional requests, raising the total development cap to **300**. Current usage is **243/300**, including earlier conservative interrupted-call reservations; **57 remain**.

This continuation added a JD instruction distinguishing slash-separated distinct skills from compound names such as CI/CD, and bumped JD extraction to `skill-jd-v2`. A fresh run split Agile and Scrum correctly. The shared explicit Microservices/Microservices Architecture alias now makes their JD/resume spellings comparable; normal alias-identity invalidation can require one lazy preparation, without a bulk rebuild or profile-version bump.

The benchmark now verifies edited source-chunk hashes and permits the existing single correction per changed chunk, instead of incorrectly requiring exactly one request. It measures the full cold journey, including successful upstream job analysis, against 120 seconds. It also stops lifecycle measurements when preparation or the first job fails, rather than treating later extraction attempts as warm-cache comparisons. Source validators, transport guards, weights and the one-correction limit remain enforced.

Final regression: **462 backend tests, 90 frontend tests and production build passed**. Existing Starlette/AnyIO deprecation warning only. A fresh reviewer found the full-journey gate defect; its regression reproduced the false pass before the fix. No Critical finding was reported.

### Independent cold measurements

Product candidate: `7ade7f7ae2f8951a9beabd1cf150a0752d617e8c`. Provider: the approved Experiential `gpt-6-luna` profile. Each run used a new isolated vault/cache and the full authorized documents. Upstream job analysis is measured separately and included in the full journey. Six runs consumed **47 requests / 339,983 reported tokens**, with **zero SDK failures**. Successful SDK responses can still fail source/schema validation.

| Anonymous job | Repeat | Complete selected comparison | Matching seconds | Full journey seconds | Extraction requests |
|---|---:|---|---:|---:|---:|
| Java/full-stack | 1 | Fail | 61.90 | 69.39 | 2 |
| Java/full-stack | 2 | Pass, 5/5 | 232.86 | 240.02 | 12 |
| Java/full-stack | 3 | Fail | 223.79 | 231.26 | 11 |
| QA engineer | 1 | Fail | 46.79 | 52.20 | 2 |
| QA engineer | 2 | Fail | 46.53 | 53.59 | 2 |
| QA engineer | 3 | Fail | 261.78 | 267.53 | 12 |

The request column excludes the one upstream analysis request per row; all six analysis requests are included in the 47-request total. **Completeness is 1/6 comparisons**, and the sole complete cold journey exceeds 120 seconds. Fresh extraction sets did not match the proposed reviewed fixture sets. The second JD is still unreviewed, so it cannot establish reviewed quality even if a response completes. No new skill-fit preference agreement is claimed from the earlier overall-fit pairs.

Failures are source interpretation/validation rather than transport or JSON syntax: missing/non-unique original quotes, incomplete/invalid OR groups, and proposed skill phrases unsupported by their quoted text. Some unsupported names expand abbreviated lists; others are not literal spellings in the selected passage. Received invalid responses get one correction; persistent invalid output remains unscored. The data does not support another broad “parsing fixed” claim or a faster-cold claim.

The historical pinned-main observations remain separately labeled legacy keyword alignment: six complete comparisons, 13.78–16.67 seconds matching. Their JD hashes and resume source-hash sets agree with these development inputs. Those observations were not rerun or charged again. The two score scopes remain different.

### Cached arithmetic and lifecycle

Current validators revalidated fully valid recorded live JD/profile artifacts in isolated storage. Both jobs then completed three local repeats each: **0.099–0.104 seconds**, **zero provider requests**, identical raw scores/ranks, and exact agreement with an independent Decimal implementation of the approved score formula. This proves arithmetic and cache behavior for accepted extracted inputs; it is not new extraction, preparation timing, ground-truth accuracy or a cold-performance pass.

A separate live lifecycle attempt at `230861d56e97fdb6b7347f9e91d739d53c305d79` consumed **9 resume-preparation requests / 78,546 tokens**. Preparation took **306.67 seconds** sequentially and was incomplete because a profile still failed source validation after its allowed correction. The benchmark therefore stopped before prepared/new-job, edit or warm phases. This sequential preparation time must not be confused with the two-worker cold comparison times above. Earlier successful recorded-artifact lifecycle observations remain historical diagnostics, not substitutes for this current live gate.

| Required gate | Current status |
|---|---|
| Runtime/scoring/UI regression | **Pass** |
| Cached comparison: no requests, exact arithmetic, stable scores/ranks | **Pass** on source-revalidated recorded artifacts |
| Fresh slash-group smoke | Agile/Scrum split correctly; **not full extraction agreement** |
| Human-reviewed JD/resume extraction sets | First JD/resumes approved; second JD supplement **pending** |
| Full fresh extraction agreement | **Fail / incomplete review** |
| Three complete cold runs per job | **Fail**, 1/6 complete |
| 120-second full cold journey | **Fail** |
| Full current live lifecycle | **Fail at preparation; subsequent phases not run** |
| Separate ten-job/twenty-pair reviewed holdout | **Not run**; no qualifying reviewed fixture available; not opened |
| Release/activation | **Not approved; default-off** |

The first-JD review marks Docker required, while its source line “Docker, Kubernetes (preferred)” was freshly interpreted as both preferred. The owner was asked to settle that ambiguity; the approved gold was not silently changed. The second-JD supplement and the holdout-or-deferral question also remain unanswered. Exact-name matching can produce low/tied scores for broad category requirements that are not literal cached skill names; it deliberately does not infer Java → “programming languages” or a framework → a general testing category. Vocabulary/category review is required before claiming that those ranks are useful job-fit judgments.

This continuation used **57 requests**, **424,135 reported tokens**: 180,706 prompt and 243,429 completion. All requests used the authorized development documents/model and stayed under the shared cap. Overall historical token usage is still unavailable for earlier failed/interrupted requests. Private documents, response captures, review sheets, score-oracle data and raw reports remain ignored.

Execution rulings: keep the last approved gold while its ambiguous category is pending (cost: reviewed accuracy cannot pass yet); count cold failures rather than discard them (cost: no development/release claim); retain source checks and the correction bound rather than accept invalid output to finish a benchmark (cost: some comparisons remain unavailable); use the successful captured-artifact replay only for local arithmetic/cache proof (cost: extraction quality and timing remain independent); holdout is not waived by more request capacity (cost: Task 9 remains open until inputs/labels arrive or the owner explicitly changes that gate).

Deferred minor: identical text at two chunk positions shares one hashed accounting identity, so a valid multi-chunk edit with a correction can conservatively fail the performance gate. Include chunk index with the hash when validating such workloads. All current approved source documents are one chunk. Manual UI inspection remains deferred for this continuation's unchanged UI; full suites were run by the implementer rather than repeated by the reviewer.

**Next:** resolve the outstanding review questions, then decide the extraction repair against these captured failures before another full live run. Repeating the same prompts is not evidence that extraction has improved. Keep Task 9 open and the flag off while its measured gates fail.

## Earlier checkpoint — before this continuation

## Current scope — owner-approved pivot on 2026-10-01

Task 9 now targets **Skill fit**: one-time JD/resume skill extraction, reuse of cached resume skills, and deterministic backend matching/scoring. AI responsibility judgments, per-comparison evidence requests, full-source AI consistency runs and the proposed passage-reference repair are retired from the active plan. See [the revised Task 9 plan](superpowers/plans/2026-10-01-cached-skill-matching.md) for implementation steps, score rules, extraction review and replacement gates.

Tasks 9.1–9.4 and Task 9.5's benchmark implementation are complete. AI extracts required/preferred JD skills and prepares reusable resume skills; every comparison matches and scores locally. Listed/demonstrated skills earn equal presence credit. Required/preferred weights remain 60:5, normalized over populated categories. Responsibility/tenure scoring, provider evidence assessment and full-source comparison fallback are removed. The API/UI show `skill_fit` / Skill fit, unweighted Skill coverage and matched/missing groups.

New resume extraction requests/materializes skill facts only. Existing valid rich profiles keep their schema, source validation and `resume-profile-v5` version, without being rebuilt just to remove unused activity facts. Shared JS/JavaScript and OOP/OOPS aliases change the existing alias cache identity, so previously cached profiles can require one lazy preparation. No bulk backfill runs. Coursework stays learning even when AI calls it listed; comma-separated OR groups cannot be split; alias-equivalent OR choices collapse to one stored qualification and round-trip through cache validation.

Final verification: **457 backend tests, 90 frontend tests, production build and diff checks pass**. A fresh reviewer found the coursework and OR-group defects; both were fixed with failing regressions. Live diagnostics then found a missing JD correction-feedback code, OOP/OOPS alias mismatch, and unused activity quotes blocking new profiles. These were fixed without relaxing retained skill source validation or adding retries. At most one received-invalid-response correction remains allowed.

### Current live measurements — 2026-10-01

All diagnostics use the approved Experiential `gpt-6-luna` endpoint, full authorized source text and isolated storage. Cached artifacts seeded from recorded provider responses are explicitly revalidated, not counted as fresh/cold extraction or profile-preparation timing. Measurements span the recorded candidates; latest product candidate is `7955269e41f432d897a25c119b4fa4e5714f2623`.

| Measurement | Result | Meaning |
|---|---|---|
| Initial prepared-vault JD smoke | 5/5 complete, 23.192s, 1 JD request | Candidate `22617cd`; reusable recorded profiles; no cold claim |
| First-JD reviewed artifact arithmetic | Exact independent expected scores; 3 identical score/rank repeats, zero requests | Owner approved first-JD/resume lists; confirmed again under final normalization |
| Fresh first-JD extraction against approved set | **Fail**: combined Agile/Scrum into one group instead of approved separate Agile and Scrum | 29 vs 30 groups; no special case or weight tuning added to force a pass |
| Fresh second JD after literal-feedback fix | 5/5 complete, 37.957s, 2 JD requests, zero profile requests | Candidate `6f530ac`; 13 proposed groups await separate review |
| Latest cached first/second JD comparisons | 5/5 complete, 0.074 / 0.087s, zero requests | Revalidated recorded JD/profile artifacts under final candidate |
| Latest warm / rename / fresh / scorer-only | 0.072 / 0.072 / 0.089 / 0.092s; zero requests; same scores/IDs | Deterministic local reranking |
| Latest content edit | 5/5 complete, 68.990s, 2 requests for that edited resume only | Initial extraction + one correction; unchanged resumes/JD make zero requests |
| Three independent cold comparisons per JD | **Not run** | Six five-resume cold comparisons need at least36 requests before corrections |
| 120s cold performance gate / separate holdout | **Not run** | Original real lengths and target retained; no padding/truncation or activation |

This implementation run used **13 requests** and **88,825 provider-reported tokens** (39,305 prompt;49,520 completion). Development usage is **186/200**, including the two earlier conservative interrupted-call reservations; **14 remain**. Overall historical token usage remains unavailable where earlier failed/interrupted requests lacked usage. The latest edited-profile pair reported17,767 tokens; both captured payloads identify only the edited source.

Task9 stays **in progress**: functional local matching passes; complete fresh extraction agreement, second-JD review, independent cold/performance and separate holdout gates remain open. No passing development/release gate is claimed. The feature remains default-off; Task10, publication and activation are separate. Source documents, quotes, responses, review sheets and raw diagnostic reports remain ignored/private.

### Revised benchmark inputs and remaining steps

The runner checks exact raw scores/ranks, zero provider comparison calls, complete selected sets and reviewed extraction sets. Fixtures add `expected_requirements` (required/preferred category + canonical alternative groups) and `expected_resume_skills` (canonical key/presence level per version). A hash-bound human review must explicitly set `score_scope: "skill_fit"` and `skills_reviewed: true`. Earlier overall-fit preference pairs remain historical; they cannot silently become skill-fit labels. The owner approved the original first-JD/resume lists. The initial sheet accidentally omitted second-JD groups; the13-group supplement corrects that omission and is awaiting review.

Next: review that supplement; standardize extraction of slash-separated distinct skills against reviewed source semantics; then repeat reviewed extraction checks. Acquire additional request capacity only when ready for the full cold gate. Holdout still requires its separate authorized inputs and at least ten real jobs/twenty reviewed strict skill-fit pairs after development passes.

Deferred review minor: the performance gate currently requires exactly one edited-profile request. The product supports chunking and the one allowed correction, so the latest two-request edit is functionally correct but cannot pass that stricter performance gate. Replace that counter with edited-source/chunk accounting when validating those live workloads; until then report the gate as unmet.

Execution rulings: use native Windows bookkeeping (shell-helper portability only); migrate the coupled score contract and fixtures together (integration regressions checked by the full suite); add explicit JS/OOP aliases with normal lazy cache invalidation (one preparation may be required); extract only new skill facts while preserving rich old caches (unused new activity/date facts are omitted). Real quality/cold costs remain independent gates; UI text/list changes use component/build checks with manual visual polish deferred; final suites were run by the implementer rather than repeated by the reviewer. The final integrated suite is the regression evidence, not a rollout approval.

All sections below are **historical measurements of the superseded overall-fit design**. Their scores, human preferences, gates and proposed next fixes must not be interpreted as validation requirements or achievements for Skill fit. Preserve them as the audit record; append new measurements with the new score scope when execution resumes.

---

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


### Per-resume requirement IDs and unnecessary rubric context

The live comparison at `1b8bd3c` accepted the JD after one correction and all five profiles (one unsupported skill corrected). It reached assessment but still exhausted the 300-second cold deadline: twelve requests including upstream analysis, one timed-out SDK correction, cumulative 127/200. Known token subtotals: JD 13,844; profiles 43,396; analysis 2,081. Whole-run usage is unavailable because the timed-out response did not report tokens. Profile SDK durations sum to 183.24 seconds while overlapping; that sum is not wall-clock comparison time.

The full-source response assessed IDs from the shared rubric that were not requested for those resumes. The payload supplied all 39 requirements although the profile round needed 15 and the source round's union needed 17. The existing assessment adapter now supplies only the union of requested IDs; per-resume authoritative subsets and strict foreign/duplicate rejection remain. Instructions distinguish the shared lookup from each resume's task list, with one fixed foreign-ID correction code. Locally verified evidence retains its credit and never gets reassessed. Assessment identity is version 8; accepted JD/profile caches and scoring weights remain unchanged. A canonical synthetic fixture reproduced the failure without the filter and verified complete retained local/semantic credit with it. Verification: 111 focused and 457 full backend tests passed (existing Starlette/AnyIO warning only). The fresh live retry is pending.


### Resumed Task 9 checkpoint

The owner paused execution for review, then explicitly resumed Task 9. At `3d27875`, the Java/full-stack cold comparison completed in 299.48 seconds; its warm repeat took 0.20 seconds with zero calls and identical scores/IDs. Three fresh fixed-rubric runs completed in 58.37, 67.79 and 64.38 seconds, preserving the five-version ordering and both reviewed Java-job preferences, while raw scores varied. The full-source consistency check remained invalid after its single correction: the original response contained four IDs outside their resume's requested set, all present in the shared lookup; its correction contained two such IDs, two unsupported literal claims and two ambiguous/unsupported quotes. No invalid evidence earned credit. A subsequent cold repetition was interrupted for diagnosis.

The separate live cache diagnostic revalidated recorded real profiles and a frozen JD; it is not independent cold evidence. Prepared first-job matching completed in 50.67 seconds with two calls; the second JD completed in 125.92 seconds with three calls and zero profile calls. QA beat Python but tied Java-no-skills, failing that reviewed strict preference. Warm reuse took 0.21 seconds with zero calls and identical scores/IDs. Editing one resume took 59.01 seconds, with one profile and one assessment call; scorer-only reuse took 0.22 seconds with zero calls and identical scores/IDs. All five lifecycle measurements completed.

Budget accounting is 160/200: 158 confirmed requests plus two conservatively reserved possible interrupted calls. Forty remain. Task 9 Steps 4-7 remain open, Task 10 is pending, holdout remains unopened and the feature stays default-off. Next diagnosis compares the exact failed source inputs using isolated per-resume requests under two-worker concurrency and the same strict validators/deadline, without changing weights or claiming an experimental orchestration passes production gates.


### Isolated source probe and precise evidence correction

An isolated diagnostic at `3932571` assessed the same five original full-source requests separately, using the same frozen rubric, unchanged validators and at most two simultaneous calls. Four of five completed in 112.16 seconds overall; seven provider requests produced zero foreign checklist IDs. Java-with-skills remained unscored after its bounded correction. This is a diagnostic, not a production routing change or a cold/performance gate pass.

The remaining source failures exposed a shared feedback gap: evidence validators raised fixed ambiguous-quote/literal-skill errors that the existing correction whitelist did not recognize. They now map to existing safe rule codes. Evidence correction instructions preserve frozen requirement IDs and keys, require unique literal source support and distinguish listed skills from performed work. The two-attempt cap, strict validators, scorer weights, JD/profile extraction and production batching remain unchanged; assessment cache version is v9.

Both regression cases failed before the fix. All 158 focused checks and 459 backend tests pass afterwards. Cumulative conservative usage is **167/200 development requests**, with 33 remaining, including the previous two interrupted-call reservations. Live verification of the correction is next. Steps 4–7 and all release gates remain open; the untouched holdout stays unopened.


### Live correction trace and invalid-claim feedback

The assessment-v9 retry of the previously failed Java-with-skills source input remained unscored: two received responses, 52.02 seconds, 20,351 reported tokens and zero SDK failures. Both responses retained two nonexistent quotes; the correction also introduced an ambiguous quote. Usage is **169/200**, leaving 31 requests. Generic rule feedback alone did not repair this example.

The shared assessment validator now examines every claim for recognized quote/literal errors and identifies all affected server-supplied resume/requirement IDs and fixed rule codes in the existing single correction pass. Arbitrary exception text is excluded. Any remaining invalid claim still rejects the assessment; no partial scoring, extra attempts or looser quotes. Assessment version v10. The new regression failed before the fix; 138 focused and all 460 backend tests pass afterwards. Live verification is pending.

A separate offline trace found 21 QA criteria using 16 original source sentences: three proficiency targets share one sentence, and four understanding targets share another. The assessment prompt currently asks for the whole original sentence while extraction has split these targets. This is a concrete ambiguity to investigate, not proof that any particular cloud/pipeline credit is invalid or a reason to change scoring weights.


### Latest verification and architecture checkpoint

The assessment-v10 retry identified both invalid claims in its correction feedback, but the final response still failed the unchanged quote validator. Two requests took 122.43 seconds and reported 19,720 tokens, with zero SDK failures. No score was published. Checklist filtering, generic rule feedback and precise claim feedback have not made this original full-source example reliable. Further quote-prompt variations are paused for architectural discussion.

A runtime-only controlled QA diagnostic kept the same recorded frozen rubric and two prepared source contexts. It compared the existing whole-sentence instruction with an instruction limiting assessment to the frozen atomic criterion and its relevant source qualifiers. Both requests returned `InternalServerError` before a received assessment; the run stopped after the first control/experimental pair. No semantic quality conclusion or production prompt change follows from those calls.

An offline request-size estimate on the recorded five-resume QA assessment removed only fact IDs, employment links and original character offsets, plus JD character offsets. All facts, keys, levels, sections, dates and source text were retained. Serialized payload size fell from 123,379 to 82,701 characters (**33.0%**). This is a size estimate, not a measured speed/token reduction; no production payload change is included.

Cumulative conservative development usage is **173/200 requests**, leaving **27**. This resumed segment used 13 requests: seven isolated-source, two generic-feedback, two precise-feedback, and two failed semantic-control requests. The 11 received requests reported 99,445 tokens; the two SDK failures reported no usage. Campaign-wide total tokens remain unavailable. Latest production code is `e2e7f42`, with 460 backend tests passing. No holdout access, push, PR, deployment or release activation occurred.

**Proposed next decision:** replace freely generated evidence quotes with selection of server-supplied source-passage references. Preserve AI relevance decisions, strict source/completeness checks, the existing single correction, native cache ownership and fixed scoring. References resolve to original saved text and offsets on the server; unknown/foreign references fail. Reuse profile spans and chunk helpers, without a new persistence table or an additional model call. This changes evidence transport rather than asking the model to reproduce text accurately. It does not by itself solve semantic grading or the 120-second cold target.

The plan contains the proposed bounded prototype and checks. Owner architectural feedback is pending before implementation. Task 9 Steps 4–7 remain unchecked, and Task 10 has not started.
