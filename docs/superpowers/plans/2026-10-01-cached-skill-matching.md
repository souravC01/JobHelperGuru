# Cached Skill Matching — Task 9 Revision

> **For agentic workers:** Use `superpowers:executing-plans` for the owner's existing native, task-by-task execution method. Update checkboxes only after verification. This is the active Task 9 specification; the 2026-09-30 overall-job-fit plan records the earlier implementation.

**Goal:** Extract job skills once, compare them with cached resume skills, and calculate consistent skill-fit scores entirely in the backend.

**Architecture:** Keep the existing resume vault, validated job-independent profiles, frozen JD cache, normalization, authenticated endpoints and ranking UI. AI prepares resume facts on upload/content change and extracts a new JD's skills. A pure local matcher and scorer perform every comparison; there is no job-specific AI evidence, responsibility assessment or source-passage selection call.

**Tech Stack:** Existing Python/FastAPI/Pydantic/Decimal, SQLite/PostgreSQL, guarded AI client, React/Vite/Vitest and pytest. No new dependency, service or database table.

**Spec:** The owner's 2026-10-01 instruction approves this pivot and adjustment of Task 9. This document supersedes earlier overall-fit scope, semantic-assessment gates and the proposed passage-reference experiment. Product implementation is pending; this update changes planning documents only.

## Global constraints

- Work on the existing `feat/ai-overall-job-fit` branch; its name does not define the new score's meaning. No branch rename, new source-branch transfer, push, PR or release activation is part of this adjustment.
- Compare versions of one person's resume. Public label: **Skill fit**; `score_scope="skill_fit"`. This measures skill coverage, not hiring probability, responsibility fit, experience suitability or an external ATS score.
- Keep user/provider/source isolation, current-source validation, upload failure isolation, file limits, full chunk coverage, the existing 300-second deadline and at most two simultaneous extraction calls. Preserve original documents without truncation.
- AI use is limited to missing/invalid JD or resume extraction artifacts. New JD: no resume extraction for already valid profiles. Cached JD plus valid profiles: zero provider requests, including `fresh=True` or a scorer-only change.
- Keep the shared extraction parser, guarded transport and existing maximum of one correction for a received invalid extraction response. Remove evidence-comparison-specific corrections with their retired caller. No new retry strategy.
- Existing complete profiles remain reusable without a profile-version bump merely because non-skill facts are unused. Read their skill facts; do not rebuild the vault just for this pivot. Missing/invalid profiles prepare once through the existing lifecycle.
- Resume content edits invalidate only that resume's derived data; rename does not. JD changes invalidate its extraction and dependent results. Matcher/scorer changes invalidate derived results without repeating valid extraction.
- The feature stays default-off. Private documents, response bodies and keys remain ignored. No live requests are needed for this planning update. Development usage is **173/200**, including two conservative interrupted-call reservations; **27 remain**. Holdout stays unopened and requires separate authorization before use.

## Review focus

- A skill named inside a responsibility bullet must survive JD extraction, while the responsibility itself earns no points (9.1).
- Aliases, unknown technologies, AND/OR groups and duplicate mentions must have a stable denominator (9.1–9.2).
- Learning-only, negated, contradictory or incomplete resume facts must not become a positive skill match (9.2).
- Cached, edited and simultaneously updated resumes must share the same frozen JD and never publish stale or foreign-user results (9.3).
- Ties, missing skills and requests finishing out of order must remain truthful in the API/UI; old overall-fit snapshots cannot appear as skill-fit results (9.3–9.4).

## Score contract

Use the existing required/preferred category weights **60:5**, renormalized over populated skill categories. Retire responsibility weight 20 and relevant-experience weight 15. This preserves the existing required/preferred weighting rather than fitting new weights to preferred winners.

For each unique requested skill or OR group, credit is **1** when a complete cached profile has a positive canonical/alias match, otherwise **0**. Both `listed` and `demonstrated` skill facts establish presence and receive the same credit. Learning-only and explicitly negated skills receive zero. Conflicting positive/contradicted facts for the same canonical skill require review; do not choose whichever fact improves the score. Resolve each alternative separately: a conflict-free positive Java fact can satisfy “Java or Python” even if Python is absent or negated.

`raw_score = 100 * sum(category_weight * matched_groups / total_groups) / sum(populated_category_weights)`.

Example: required Java and Python; preferred SQL. A resume containing Java and SQL scores `(60 * 1/2 + 5 * 1) / 65 * 100 = 53.85`. Required-only or preferred-only JDs use the populated category's coverage. No assessable skills means `needs_review` with no score. A complete profile with no matching skills scores zero.

- “Java or Python” is one group; “Java and Python” is two requirements. Duplicate/alias-equivalent requirements count once. Identical required and preferred skills count only as required; overlapping nonidentical OR groups remain separate qualifications.
- Use existing explicit aliases and punctuation-aware boundaries. Java is not JavaScript; SQL is not NoSQL. Keep unknown literal technologies. No fuzzy similarity, inferred tool equivalence, embeddings, keyword-frequency bonus or AI relevance score.
- Retain Decimal arithmetic, two-decimal raw scores and half-up integer display. Rank by raw score; competition ties share rank. All-zero results have no top match. An incomplete comparison has no ranks or automatic winner.
- Expose required/preferred coverage and matched/missing skills using existing requirement results. Keep `skill_coverage_score` as the unweighted skill-group coverage; label it separately from weighted Skill fit. Source spans already stored with facts may support internal validation; do not generate or assess new quotations during comparison.

## Keep, change and remove

| Existing component | Task 9 action |
|---|---|
| `profiles.py`, profile storage and upload/edit lifecycle | Reuse complete cached skill facts and validation; preserve non-skill stored facts without scoring them |
| `normalization.py`, `skill_matching.py`, `chunking.py`, `provenance.py` | Reuse aliases, boundaries, source coverage and extraction validation |
| `extraction.py:extract_requirements`, `ai_engine.py:extract_match_chunk` | Narrow JD proposals to explicit required/preferred skills; keep all relevant document chunks |
| `scoring.py`, `models.py` | Add pure cached-skill matching, update presence credits and scope; retain arithmetic/ranking contracts |
| `pipeline.py`, snapshot storage | Replace AI assessment orchestration with local matching; version out old rubrics/results while retaining valid resume profiles |
| `extract_evidence_batch`, `_assessment_round`, evidence wire models and `evidence_batch` prompt | Remove after all production/benchmark callers migrate; remove their comparison-only correction context |
| Responsibility/tenure scoring and full-source AI fallback | Remove from the new matching path; delete orphan helpers/tests after checking other callers; retain source/date helpers still used by profile validation |
| Passage-reference prototype and atomic-semantic prompt experiment | Cancel; they target the retired AI comparison stage |
| Existing API/UI and benchmark | Adapt in place; no second matching product, redesign, offline upgrade or parallel scoring implementation |

## Task 9.1: Extract a frozen skills-only JD

**Files:** `backend/services/matching/extraction.py`, `backend/services/ai_engine.py`, `tests/test_match_extraction.py`.

**Interface:** Keep `extract_requirements(text: str, *, engine, deadline: float) -> RequirementExtraction`. Complete output contains only `kind="skill"`, category `required_skills` or `preferred_qualifications`, canonical key/alternatives and validated original source spans; `required_months=None`. Use JD extractor version `skill-jd-v1` to reject old overall rubrics.

- [ ] Write regressions `test_skill_jd_keeps_tools_from_responsibilities`, `test_skill_jd_excludes_semantic_tenure_and_eligibility`, and grouping/alias/unknown-skill cases. “Build Java services” yields Java; generic collaboration and “three years experience” yield no scored criterion. A JD with no named skills remains unscored.
- [ ] Run `.venv/Scripts/python.exe -B -m pytest tests/test_match_extraction.py -q`; confirm the new assertions fail on the old broad extraction contract.
- [ ] Narrow the provider task and server acceptance contract. Extract skills from required work/qualification sections as required, explicit nice-to-haves as preferred; exclude company boilerplate and explicitly unnecessary skills. Preserve source validation, complete coverage, AND/OR grouping, canonical deduplication and the 64-requirement limit without trimming.
- [ ] Rerun the focused extraction checks and existing parser/normalization checks. All must pass; no live calls in this step.
- [ ] Commit the extraction change and update this checklist.

## Task 9.2: Match cached skills and calculate exact scores

**Files:** `backend/services/matching/scoring.py`, `backend/services/matching/models.py`, `tests/test_match_scoring.py`, `tests/test_match_ranking.py`, `tests/test_match_contracts.py`; replace comparison-specific tests in `tests/test_match_evidence.py` with local matcher checks.

**Interfaces:** Add `match_cached_skills(requirements: list[Requirement], profile: ResumeProfile) -> list[Evidence]` in `scoring.py`; it consumes a complete source-validated profile and has no engine/network dependency. Retain `calculate_score(requirements, evidence, *, as_of) -> ScoreBreakdown` and `rank_evaluations(evaluations)`. Define `MATCHER_VERSION="cached-skills-v1"` and `SCORER_VERSION="skill-fit-v1"`. Use the existing `assessment_version` result field for matcher identity to avoid an unrelated transport rename.

- [ ] Write exact-value checks: the Java/Python/SQL example is `Decimal("53.85")`; listed and demonstrated presence give equal credit; duplicating a fact or resume does not alter a score; Java/JavaScript and SQL/NoSQL stay distinct; an OR group receives at most one credit. Check learning/negation, same-skill contradictions and an incomplete profile staying unscored. Add raw-score tie and no-skill-JD checks.
- [ ] Run the four matching/scoring/ranking/contract test files and confirm the new score/scope assertions fail before implementation.
- [ ] Implement matching from `kind="skill"` profile facts using the existing canonical aliases. Reuse cached source fields in Evidence; emit explicit absence for unmatched groups only when profile coverage is complete. Raise a validation error for unresolved same-skill conflicts; the pipeline maps it to `needs_review`. Apply the score contract above and `score_scope="skill_fit"`; reject non-skill score inputs.
- [ ] Run those tests to green, including reordering and adding another resume preserving every individual's score. No weights or exceptions keyed to the real development winners.
- [ ] Commit and update the checklist.

## Task 9.3: Route comparisons through local matching and retire AI assessment

**Files:** `backend/services/matching/pipeline.py`, `backend/services/matching/extraction.py`, `backend/services/ai_engine.py`, `tests/test_match_pipeline.py`, `tests/test_match_snapshots.py`, `tests/test_match_profiles.py`; change storage only if an existing contract requires it.

**Interface:** Keep `evaluate_resumes(job_text, resumes, *, user_id, as_of, engine, storage, fresh=False, deadline_seconds=300.0) -> EvaluationBatch`. Extraction uses the engine only on valid artifact misses; matching/scoring calls Task 9.2. Snapshot identity includes JD/profile fingerprints, source, alias/matcher identity and scope. Scorer-only changes recalculate locally; preserve stable evaluation IDs where the existing contract permits. Do not alter profile extractor version solely for this change.

- [ ] Add `test_cached_skills_comparison_forbids_provider_calls` with an engine that raises on every call after setup; assert complete exact scores and identical results across three repeats. Add `test_new_jd_only_calls_requirements`, `test_fresh_recomputes_locally`, `test_old_overall_snapshot_cannot_be_skill_fit`, and edit/rename/scorer/provider/isolation race regressions. For ordinary one-chunk input, a prepared vault plus new JD uses one successful requirements request, or at most two with the existing correction; zero `evidence_batch` calls in every case.
- [ ] Run pipeline/profile/snapshot tests and observe the expected failures on the old semantic path.
- [ ] Replace assessment partitions, profile-context dispatch and full-source AI fallback with local skill matching. Retain current-source/profile/rubric validation, atomic freeze, ownership and stale-result guards. Rebuild cheap match outcomes from validated cached facts; do not call `_validate_evidence_proposal` or trust old AI outcomes. Map incomplete/conflicting input to existing unscored statuses.
- [ ] Migrate remaining production and benchmark callers, then remove orphan assessment wire models, `_assessment_round`, `extract_evidence_batch`, the `evidence_batch` prompt and comparison-only correction metadata. Keep `_validated_chunk` and safe JD/profile extraction feedback. Delete obsolete semantic/tenure tests only with replacement checks for the new behavior; retain source validators still used during extraction. Search all callers before deletion.
- [ ] Run focused backend tests to green and confirm no runtime path invokes the retired provider task. Commit and update the checklist.

## Task 9.4: Show and explain Skill fit in the existing API/UI

**Files:** `backend/main.py`, `backend/services/matching/models.py`, `frontend/src/components/ResumeFitRanker.jsx`, `frontend/src/api/client.js` only if needed; `tests/test_match_api.py`, `frontend/src/test/ResumeFitRanker.test.jsx`, `frontend/src/test/ClientMatching.test.jsx`, `frontend/src/test/ResumeLibrary.test.jsx`.

**Interface:** Retain `/api/resumes/evaluate`, vault profile preparation and the existing default-off feature flag. Return `skill_fit`, backend raw/display scores, coverage and per-skill results. Keep selected provider identity/security checks; a temporarily unreachable provider must not prevent a valid cached comparison through a network call.

- [ ] Update API/UI assertions for the exact label `Skill fit`, required/preferred matched and missing skills, truthful ties and null incomplete scores. Retain edit/job/provider switch race checks and save-success despite extraction failure. Confirm generic responsibilities/tenure do not appear as scored categories.
- [ ] Run `.venv/Scripts/python.exe -B -m pytest tests/test_match_api.py -q` and, in `frontend`, `npm run test:run -- src/test/ResumeFitRanker.test.jsx src/test/ClientMatching.test.jsx src/test/ResumeLibrary.test.jsx`; observe the intended scope/copy failures.
- [ ] Adapt existing summaries and error copy to skill extraction/matching. Explain weighted Skill fit and unweighted Skill coverage plainly; use existing requirement results for matched/missing skills. Preserve accessible selection, stale-response guards, legacy mode labeling and the existing upload/edit flow.
- [ ] Rerun these tests and `npm run build` in frontend; commit and update the checklist.

## Task 9.5: Replace obsolete gates and measure the agreed workflow

**Files:** `scripts/evaluate_matching.py`, `tests/test_match_benchmark.py`, `docs/ai-matching-evaluation.md`; approved private fixtures/review sheets remain ignored.

**Interfaces:** Adapt existing `run_quality`, `run_lifecycle` and `performance_gate`. Record `score_scope="skill_fit"`, candidate/provider/extractor/matcher/scorer identities, document hashes/lengths, exact scores, extraction calls/tokens, local comparison latency, completeness and review provenance. Missing token usage stays unavailable. Never label historical overall-fit measurements as skill-fit results.

- [ ] Add report checks proving a comparison with cached JD/profiles makes zero requests, an evidence-task call fails the gate, fixed extracted inputs produce identical per-resume scores/ranks in three repeats, and unreviewed extraction labels cannot pass the quality gate. Keep strict ties/unscored observations in the denominator, privacy and request-cap accounting.
- [ ] Run `.venv/Scripts/python.exe -B -m pytest tests/test_match_benchmark.py -q`, observe new behavior failures, then adapt the runner. Replace repeated AI-evidence/full-source comparison gates with reviewed extraction accuracy and deterministic local comparisons. Keep cold extraction drift separate from local scoring stability.
- [ ] Prepare a private review sheet of required/preferred JD skill groups and cached resume skills for the already authorized two JDs/five resumes. Check every proposed skill against the real source and expose omissions. Obtain human review before treating these sets as ground truth. Keep the four earlier overall-fit preferences as historical evidence; they are not automatically skill-fit labels and must not determine new weights.
- [ ] Run the local reviewed-fixture comparisons first: exact expected arithmetic, 100% matching/alias/grouping checks, complete comparisons and identical three-repeat scores/ranks. A fresh live extraction must match the reviewed skill sets/categories/groups, with no unsupported additions or omissions, before it can count as passing on these small development fixtures.
- [ ] Run an initial live extraction smoke on an authorized JD with the prepared vault, capped at two of the remaining 27 requests. Stop and diagnose if extraction fails. Count every SDK request, including failures/corrections, against the existing shared 200-request cap; the two interrupted-call reservations remain charged. Never consume the holdout to debug development.
- [ ] Once the smoke passes, measure three independent cold extraction comparisons per approved job only as the remaining request cap permits, plus the lifecycle: preparation, prepared first JD, different JD, warm repeat, one content edit, rename and scorer-only change. Ordinary prepared/new jobs call JD extraction only; warm/rename/scorer/fresh reranking use zero calls; content edit extracts only that resume. Report profile preparation and any separate job-metadata analysis independently and include both in full-journey totals.
**Budget feasibility:** Six entirely cold five-resume comparisons need at least 36 successful extraction requests for one-chunk documents, before corrections or the smoke test. The remaining 27 cannot complete that entire gate. Prioritize local verification and the prepared-vault lifecycle; report unfunded cold runs as not run and obtain an increased total cap only before the additional live measurements. Do not silently redefine cold, drop a gate, or exceed the approved cap.

- [ ] Retain the 120-second full cold comparison target and real document lengths; no artificial 8,000-character requirement or padding. Report local comparison time separately and compare costs/latency with the recorded main baseline without claiming the two scores mean the same thing. No latency improvement is claimed from payload-size estimates alone.
- [ ] After development passes, retain the separate held-out quality gate of at least ten real jobs and twenty reviewed strict pairs, now explicitly reviewed for skill fit: at least 90% strict agreement, 100% complete evaluations and three identical fixed-input local repeats. Held-out extraction correctness must be reviewed too; use no unsupported skill credit. Acquire missing inputs/labels and explicit holdout request authorization at that stage. The current documents and development permission do not establish this gate.
- [ ] Publish pass/fail/not-run for each revised gate, request usage and limitations. Run the full backend suite, frontend tests/build and `git diff --check` after the final code changes. Update this plan and commit. Task 9 remains open until its required gates actually pass; Task 10 and activation remain separate.

## Acceptance and self-review

- [x] Owner-approved pivot recorded; old passage-reference/semantic experiments cancelled.
- [x] Existing extraction/cache/scoring/UI files and caller dependencies identified; no new architecture layer or database migration assumed.
- [x] Score arithmetic, grouping, absence/conflict semantics, public scope, cache compatibility and request budget specified.
- [x] Every Review Focus item maps to a named test step; old preferences/results are explicitly separated from the new score's validation.
- [ ] Tasks 9.1–9.5 implemented and verified. Nothing in this planning update establishes passing product behavior.

Next implementation unit: **Task 9.1**. Continue with the preserved native, task-by-task execution method when execution resumes.
