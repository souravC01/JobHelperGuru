# AI overall job-fit evaluation

Task 9 is **in progress** on `feat/ai-overall-job-fit`. The benchmark is implemented; live development is blocked by an unreadable saved provider credential, and untouched holdout/exact-size performance evidence are pending. The matching feature remains default-off. Synthetic tests establish report/cache behavior, not ranking quality, live speed or readiness for release.

## What is measured

`scripts/evaluate_matching.py` runs the actual matching services with temporary isolated SQLite databases. It uses no production vault and changes no rollout flags. Pinned main is `9fa7b26a4ca78c38dd977d1eff0df1f30c11b5c5`; an archived backend runs in a separate process, using the same explicitly selected provider/model and allowed documents. Candidate measurements require committed, clean code. Reports record both commits, source/profile/rubric/evaluation fingerprints, the date, provider host/model and endpoint fingerprint.

Each job receives three cold evaluations, each with a fresh vault/rubric/profile cache. For the first cold interpretation, three fresh evidence assessments reuse its frozen rubric and prepared profiles. Report cold rubric drift separately from fixed-rubric evidence/ranking drift. The full-source diagnostic assesses the same original documents against that frozen rubric, without a profile prefilter; compare completeness, raw scores and pair ordering for profile omissions.

The lifecycle measures upload/profile preparation, the first job with prepared profiles, a different job against the same saved vault, an identical warm repeat, one saved content edit, and a local scorer-version bump. The prepared/second jobs must reuse profiles, the edit must extract only one changed profile, and warm/scorer-only runs must make zero provider calls and preserve evaluation IDs/raw scores. A scorer-version bump is a measurement of existing invalidation rules, never a score override.

Calls are counted at the SDK request boundary, including analysis, profile preparation, requirements and semantic assessment; the guarded client disables SDK retries. One hard request cap covers baseline and candidate together. Tokens are aggregated only when every corresponding response reports usage; missing usage remains null/unavailable. Report individual comparison duration separately from suite duration and include the upstream analysis duration in full-journey measurements. Failed or budget-denied measurements cannot pass completeness gates.

## Quality and performance gates

Strict human preferences retain correct, tied, reversed and unscored observations in their denominator. Explicitly reviewed ties have separate measurements. Main scores are labeled `legacy_keyword_alignment`, and their pair agreement is measured independently; they are not interchangeable with overall job-fit percentages.

Development requires allowed real versions of the same person's resume, an exact hash-bound human review record, three complete cold runs and three complete fixed-rubric runs per job, correct reviewed strict preferences, stable fixed-rubric ordering, valid quote provenance, and a complete full-source comparison preserving score/order. Synthetic or cross-person data cannot establish this result.

Holdout inputs are opened only after a passing live development report from the same provider and unchanged candidate commit. Holdout requires at least ten distinct real jobs and twenty strict human-reviewed pairs. Each of three frozen-rubric repetitions must reach at least 90% strict agreement, with complete evaluations, no tied/unscored strict preferences and no invalid positive quotes. Development examples and holdout labels must stay separate.

Performance requires an authorized 8,000-character JD and five authorized 8,000-character resume versions, three complete cold comparisons each within 120 seconds, the complete cache lifecycle, and three measured main cold baselines. Reports include main/candidate comparison and full-journey latency deltas plus provider calls/tokens; regressions are reported rather than hidden in a suite total. Do not pad short documents to claim the exact-size real-input test passed.

The release gate stays false unless every required quality, development, performance and cache check passes. Failing gates and reason counts remain in the report; no benchmark run activates the application feature.

## Current inputs and outstanding evidence

The owner authorized documents in `D:/Grind/Resume stuff/No named resumes` and the saved `exp/gpt6 luna` profile, model `gpt-6-luna`. Provider metadata was located with a read-only database query; no key was printed. Five PDF resumes extracted without warnings. Two complete development JDs were selected from `JOB Descriptions.docx`; `JD 2nd set.docx` remains unopened for holdout.

Local inputs in `tests/fixtures/matching/private-dev.json` remove contact headers and consistently replace personal employer, institution and project names. They remain Git-ignored, along with their review record. Proposed preferences and the lifecycle edit are available locally in `scratch/task9-development-review.md`. The owner reviewed and accepted the four proposed preferences. The owner confirmed same-person ownership, all four proposed strict preferences, and a cap of 100 provider requests total for the initial main/candidate development benchmark. This does not authorize further reruns or holdout requests.

Current anonymized resumes contain 3,215–4,502 characters and the two development JDs contain 5,168 and 5,594 characters. They do not satisfy the exact-size performance workload. That evidence, a separately reviewed holdout, and any additional request budget remain outstanding. No live provider call or semantic quality result has been recorded. The authorized launch stopped before AI requests because the named saved credential could not be decrypted using either the source dotenv encryption key or source local encryption secret. No credential was changed or printed; zero of the approved 100 requests were consumed. The owner has been asked to supply the selected provider key privately through the local `MATCHING_BENCHMARK_API_KEY` setting. Live development remains blocked until that key is readable.

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

The example is one command, wrapped here for readability. Holdout additionally requires `--phase holdout --development-report <passing-report>`. Exact-size performance inputs require both `--performance-fixture` and `--performance-review-record`. Case IDs must remain unique across quality and performance fixtures. Reports contain validated evidence counts and category/skill scores, not document text, quotes, keys or response bodies. Inspect `development_gate_passed`, `release_gate_passed`, `failed_gates`, measurement completeness and token availability; an exit code alone is insufficient for diagnosis.

## Local verification

The dedicated benchmark suite currently passes 28 checks covering denominator/tie behavior, raw-score comparison, incomplete results, unavailable usage, source/secret projection, actual SDK call limits, real service cache lifecycle, frozen-rubric repeats, full-source diagnostics, input/review validation, and refusal to open holdout before development passes. The fresh full backend suite passed all 439 tests; only the existing Starlette/AnyIO deprecation warning remains. Existing frontend behavior is unchanged by this benchmark.
