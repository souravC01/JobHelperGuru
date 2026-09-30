# AI Overall Job Fit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Execution method must be selected by the owner before implementation.

**Goal:** Help one person choose among their resume versions using complete, source-backed AI assessments, a shared overall-job-fit rubric, logical comparable scores, and cached results.

**Architecture:** Start a new branch from up-to-date remote main in an isolated checkout at execution time. Borrow small validated contracts, normalization, scoring, document-warning, and cache components; build a lean AI requirement/evidence adapter rather than copying the current dual-mode extraction pipeline. AI interprets source text; the server validates coverage and provenance, calculates scores, and assigns ties. Preserve the separately labeled existing matching endpoint for rollback and offline use.

**Approved extension:** Analyze each saved resume into a reusable, job-independent evidence profile. Store canonical skills, evidence levels, activities, credentials and dated work with validated source spans. New jobs reuse those profiles; job-specific semantic assessment and deterministic scoring remain separate. This replaces repeated full-resume extraction, not the original source document.

**Tech Stack:** Existing Python/FastAPI/Pydantic, OpenAI-compatible guarded client, SQLite/PostgreSQL storage, React/Vite/Vitest, pytest. No new runtime dependency.

**Spec:** This plan's “Design baseline” section records the in-chat design and the owner's choice of overall job fit. Earlier evidence-branch specs are reference material, not authority for the new branch. The proposed numeric weights, credits, batching ceilings, and release thresholds below require owner review with this plan before execution.

**Execution status:** The owner authorized implementation task-by-task. Tasks 1–3 are complete on `codex/ai-overall-job-fit`; Task 4A and all later tasks remain pending. Each completion updates this plan and the execution ledger. Live provider requests and release activation remain unauthorized.

**Plan persistence:** The repository ignores `docs/superpowers/`. This file is saved locally but is not automatically tracked. Task 1 must explicitly transfer it to the destination and force-add this one approved plan path when committing planning records; do not change the ignore rule or force-add the entire directory.

## Current task status

| Task | Status | Verification |
|---|---|---|
| 1 — isolated branch and transfer records | Complete | Backend 211, frontend 67, production build passed; commit `6a924c5` |
| 2 — contracts and document completeness | Complete | 37 focused and 229 backend tests passed; commit `17ef20b` |
| 3 — full-source overall-fit JD rubric | Complete | 41 focused and 253 backend tests passed; no live provider requests |
| 4A — reusable resume profiles | Pending — next | Must precede Task 4 |
| 4 — requirement evidence assessment | Pending | |
| 5 — deterministic scoring and ranking | Pending | |
| 6 — rubric and assessment caches | Pending | |
| 7 — authenticated API | Pending | |
| 8 — truthful UI and request lifecycle | Pending | |
| 9 — provider quality and performance gates | Pending | |
| 10 — final regression and handoff | Pending | |

Task 3 accepts validated proposals with stable source/version-based requirement IDs; persisted frozen rubrics belong to Task 6. Its provider schema requires exact chunk acknowledgment and explicit completion. Unknown technologies survive without a taxonomy gate. Server validation rejects ambiguous quotes, split/partial literal OR groups, unsupported tenure minima, non-equivalent category conflicts and explicit document instructions. Semantic interpretation remains the AI's responsibility and is not yet validated by live quality measurements. Over-limit rubrics remain needs_review without trimming.

## Global Constraints

- Compare versions of one person's resume, not different applicants; the percentage is documented overall job fit, never a hiring probability or an actual external ATS score.
- Use the same frozen job requirements, category weights, credits, and denominator for every resume in a comparison.
- Reuse unchanged resume profiles across different jobs. A scoring change must not trigger resume-profile extraction or repeat already validated job-specific evidence assessment.
- Preserve existing provider profiles, key storage, optional profile name/base URL/model fields, outbound host policy, authentication, rate limiting, file limits, and tenant isolation.
- Keep a 100,000-character cap per JD/resume, at most two concurrent provider requests, and a 300-second evaluation deadline. Never silently truncate accepted text.
- Missing assessments and unresolved qualifications are incomplete, not zero-credit absence. Never fabricate a fallback percentage or a winner for an incomplete comparison.
- Positive and contradicted claims require validated source evidence. Skills-list mentions and learning plans must never count as demonstrated work.
- Keep the new experience default-off until reviewed quality gates pass. Keep offline enhancements out of scope.
- Keep private resume/JD text, keys, and provider response bodies out of tracked fixtures, logs, and public reports. Live development/holdout usage needs explicit permission for the selected documents, provider, and costs; other-chat permissions are not assumed to cover new requests.
- Preserve the dirty source checkout. Do not stash, reset, clean, switch it, or commit another chat's work to facilitate transfer.

## Review Focus

- A late requirement or project must survive extraction and matching, including documents above ordinary request-batch limits (Tasks 2–4).
- “Java or Python,” “Java and Python,” preferred tenure, and the same qualification repeated in multiple sections must produce the correct denominator (Tasks 2–3).
- An omitted/duplicate resume or requirement ID, injected instruction, or plausible unsupported quote must not become a completed evaluation (Tasks 3–4).
- A cached resume mixed with an edited/new resume must still use one frozen rubric, and different users/providers must never share results (Task 6).
- A job/profile switch during an in-flight request, resume edit with unchanged count, or tied result must not display stale scores or an invented winner (Tasks 7–8).

## Design baseline

### Meaning of the score

| Category | Starting weight | Interpretation |
|---|---:|---|
| Required skills and qualifications | 60 | Explicit must-have skills, knowledge, certifications, or education |
| Responsibilities | 20 | Specific activities demonstrable from work or projects |
| Relevant experience | 15 | Explicit required experience; numeric tenure verified against relevant employment dates |
| Preferred qualifications | 5 | Explicit nice-to-haves, including preferred experience |

For category c, let m[c] be the mean credit of its unique requirements. Score = sum(weight[c] * m[c]) / sum(populated weight[c]) * 100. Equal requirement influence within a category; no model-generated importance multipliers in version one. Empty categories are excluded from the denominator, not awarded full credit. No assessable requirements means needs_review, not 0% or 100%.

- Technical skill: demonstrated = 1.0, listed = 0.5, learning/absent/contradicted = 0.0. Preferred technical skills use the same evidence credits.
- Responsibility: demonstrated = 1.0, otherwise 0.0. A loosely related passage does not establish the requested action/object.
- Required education/certification: explicit source-backed satisfaction = 1.0, otherwise 0.0; ambiguous equivalence is unresolved. Do not turn a degree into a missing technical keyword.
- Quantitative tenure: min(verified relevant months / requested minimum months, 1.0). Union overlapping intervals, cap ongoing work at server evaluation date, exclude education/projects and negated work. A range such as 1–3 years uses its one-year minimum, not a three-year maximum.
- Nonquantitative relevant experience: demonstrated relevant work = 1.0, otherwise 0.0. Projects can demonstrate skills/responsibilities; only count them as experience if the JD explicitly accepts project experience.
- An OR group has one requirement and takes the best qualifying alternative. An AND group has separate constituent requirements. Preserve grouping from source, not from resume content.
- Deduplicate equivalent requirements within category using canonical keys plus qualification semantics. If the same qualification appears as both preferred and required, retain the explicit required interpretation and its source spans. A tenure threshold and a skill are distinct; do not multiply credit for repeated wording.
- Keep source-based evidence and stable requirement IDs; expose skill-only coverage separately using skill-kind requirements and their credits. Return null for that metric when there are no technical-skill requirements.
- Use Decimal, two-decimal raw scores, and ROUND_HALF_UP display integers. Rank on raw_score, not rounded display percentages. Equal raw scores receive competition ranks 1, 1, 3; all tied leaders are marked top matches and described as tied.
- Eligibility is separate context. No resume-name/title bonus, extra role-specialization share, keyword-frequency bonus, or invented qualification.

### Product and API boundary

- Keep `/api/resumes/match` and its existing list response for legacy/offline clients; do not make old clients consume a new object.
- Add the existing branch's authenticated `/api/features` and `/api/resumes/evaluate` route patterns, adapting evaluation to configured AI only. `MATCHING_V2_ENABLED=false` remains the rollout flag to avoid inventing parallel flags.
- Evaluate request: `{job_text, resume_ids, fresh: false}`. Fetch selected stored resumes using current user; reject duplicate IDs and missing/foreign IDs. Do not accept caller-supplied resume text or caller-supplied scores/rubrics on this endpoint.
- Response: borrowed `EvaluationBatch`/`Evaluation`, with `score_scope="overall_job_fit"`, `skill_coverage_score`, and `rubric_fingerprint`. Complete results carry raw/display/category scores and requirement evidence. Incomplete results carry null scores/ranks and actionable reason codes.
- Keep old jobs lacking raw source text on a clearly labeled legacy experience; ask for the full JD before overall-fit evaluation. Never build an overall-fit rubric from keyword lists alone.
- If AI is unavailable/offline, use the existing legacy mode explicitly. A configured provider failure remains a provider error, not silent offline fallback.
- An incomplete batch may display complete individual assessments, but no comparison ranks, top-match badges, or automatic best-resume selection.

### Performance boundary

- Ordinary evaluation with existing profiles: one uncached JD-rubric request, then at most one batched semantic-assessment request for up to five resumes when size permits. Resolve safely conclusive literal skills/credentials locally; skip the semantic request if all requirements are already conclusively assessed. Profile creation and existing job-metadata analysis are separate costs; count them in total journey measurements.
- Evidence batching: at most five documents and 40,000 supplied evidence/source characters per request; include the frozen rubric and cap it at 64 assessable requirements. Use relevant profile evidence and source context rather than resending whole resumes by default. These are starting application bounds, not claims about every provider's context capacity.
- JD/documents beyond 8,000 characters use borrowed source-preserving 8,000-character chunks with 400-character overlap. Process all chunks and deduplicate overlap. Chunk results are intermediate observations, never independent scores. An explicitly unresolved observation remains unresolved; absence in one chunk cannot erase evidence in another.
- If a configured provider cannot process an accepted request, return an actionable error; do not trim input or silently guess a context limit. Split only on application size limits initially. No automatic repair/retry loop in version one.
- A warm unchanged comparison makes zero provider calls and reuses evaluation IDs. A partial cache hit evaluates only changed/missing resumes against the cached rubric. Reordering the comparison never changes individual scores.
- Fresh means refresh job-specific assessments against the existing valid frozen rubric and resume profiles, not re-extract unchanged resumes. A rubric change occurs only when JD/provider/extractor versions change; development cold-rubric experiments use an isolated cache namespace/storage and invalidate dependent scores.

### Resume vault evidence profiles

- Store the original resume independently from its derived profile. The profile has no job IDs, requirement IDs, category weights, rank or score. It is a reusable evidence index, not a keyword bag or an AI-written replacement resume.
- Store canonical skills/aliases with demonstrated/listed/learning/contradicted evidence, verbatim work/project activity records, credentials, employment entries and source-backed dates. Each fact refers to exact source spans and its source section. Unknown technologies remain supported.
- Key profiles by user ID, resume ID, exact content hash, provider endpoint/model/protocol, profile extractor/prompt version and alias version. Exclude job fingerprints and scorer versions. Changing a job or weights reuses the profile; changing resume content or extraction identity rebuilds it. Store uncapped source dates; compute ongoing tenure at scoring time.
- After a successful upload or content edit, request profile preparation through an authenticated endpoint when the AI feature is enabled and a provider is configured. Save success is independent of analysis success: preserve the resume if extraction fails, show pending/failed analysis with retry, and never publish a partial profile as complete. No background worker/queue is needed in version one.
- Existing vault resumes are profiled lazily on their first AI comparison. No mass migration or automatic billable backfill. Offline uploads remain usable in legacy mode and get profiles only after a configured AI action.
- Use profile facts for cheap canonical skill matching and source-verified education/date checks; AI assesses job-specific semantic relevance. Employment duration is not automatically relevant duration: the JD must match the work evidence before those dates count.
- A missing profile keyword is not proof of absence. For an unmatched technical term, scan the entire original source with aliases and context checks. For semantic requirements, consider all profile activity records; if context/coverage is insufficient, inspect source chunks in a bounded AI assessment. No lexical-only prefilter may turn a valid paraphrase into absence. Account for every relevant chunk before returning not_evidenced; otherwise return unresolved.
- Content edits invalidate that resume's profiles and dependent assessments/scores; rename-only edits update displayed names without re-extraction. Deletes remove derived profiles/results for that user and resume. A late extraction for an old content hash cannot overwrite the current profile.
- Concurrent requests use atomic first-valid-writer persistence, then read the accepted profile. Complete profiles are revalidated against current source/hash on load. The system may make duplicate calls in a race initially, but must not mix competing profiles within one comparison.

| Layer | Reused across | Invalidated by |
|---|---|---|
| Resume profile | All jobs for the same unchanged resume/extraction identity | Content or profile-extractor/provider/alias identity |
| Frozen JD rubric | All selected resume versions for that JD | JD content or rubric-extraction identity |
| Validated job-specific evidence | Score recomputation for the same profile/rubric | Profile/rubric or evidence-assessment identity |
| Derived score/rank | Unchanged evaluations; ranks recalculated for selected set | Scoring version or comparison selection; no profile extraction |

## Sources and transfer inventory

Source chat: **Review resume matching logic**, thread `01a0b14d-175b-7460-8a42-fcb597b3c979`. Its latest work was inspected read-only. The source checkout and chat are shared context, not a clean patch queue.

Recorded refs on 2026-09-30: local main `521f46cc16ac1965d291c556bc03b45e57cb3cdc`; saved origin/main `9fa7b26a4ca78c38dd977d1eff0df1f30c11b5c5`; source branch HEAD `231c3dd`. Fetch and pin fresh full SHAs at execution time. The two recorded main refs have identical matching backend logic. The source working tree contains substantial uncommitted improvements, so HEAD alone is insufficient.

| Source | Action in new branch | Dependency or exclusion |
|---|---|---|
| `matching/normalization.py`, `skill_matching.py` | Borrow aliases and canonical deduplication | Keep unknown technologies literal; taxonomy must not be a whitelist for AI extraction |
| `matching/models.py` | Borrow/adapt strict requirement/evidence/evaluation contracts | Remove role bonus fields; add overall scope, rubric identity, nullable skill metric, reason codes; do not copy unused exports |
| `matching/chunking.py` | Borrow source-preserving bounds and offsets | Use only for overflow; protect overlap reconciliation |
| `matching/extraction.py` | Extract selected provenance, section/context, negation, date-interval helpers | Do not copy the whole file, offline extractor, fixed technical candidate restrictions, distinctive-term semantic gate, or repair loop |
| `matching/scoring.py` | Borrow weighted category calculation, interval union, competition-rank structure | Learning credit becomes zero; responsibility credit differs from skill credit; remove role/presentation bonus; rank raw scores |
| `matching/pipeline.py` | Borrow complete-snapshot verification, hashing, deadlines, failure handling | Build smaller AI-only orchestration and batching; do not copy per-resume call fan-out or mode switch wholesale |
| `storage.py` | Borrow user-scoped snapshot migration/CRUD and edit/delete invalidation | Add job-rubric cache; preserve latest-main storage locking and PostgreSQL fixes |
| Reusable vault profile | Build new; not present in source branch | Reuse provenance/alias/date helpers, not job-dependent Evidence records as the profile schema |
| `document_parser.py`, `Resume` warning fields, upload routes | Borrow extraction-warning propagation and unreadable-page handling | Preserve main's decompression/file guards; inspect new metadata/model migrations together |
| `ai_engine.py:extract_match_chunk`, token accounting | Borrow guarded-client request and usage-reporting patterns | Replace payload/prompt for lean tasks; no new provider abstraction; do not globally relax transport policy/timeouts |
| `ResumeFitRanker.jsx`, API helpers | Adapt default-off routing, abort support, true ties, callback hardening | Do not copy the entire rewritten interface or `MatchEvidenceDetails.jsx` |
| Focused matching tests and fixtures | Port relevant provenance, aliases, tenure, tie, cache, and API cases | Rewrite role/offline-specific expectations; existing synthetic cross-person cases are not a release gate |
| `scripts/evaluate_matching.py`, `docs/matching-evaluation.md` | Borrow measurement concepts and historical failure evidence | Build an AI-only report; do not import offline rollout gates or claim historical test counts were rerun |

Important uncommitted source fixes include locally validated dated tenure, negated-work rejection, `Technical Skills and Tools` section detection, provider coverage consistency checks, profile-aware cache identity, warning propagation, and transport deadline changes. Copy only with their regression checks. The locally computed tenure path is useful for AI mode even though it originated in offline helpers.

Latest recorded source result: 25/25 complete evaluations, 6/10 strict preferred pairs correct, two ties, two reversals; 33 calls across five jobs. A separate QA run changed ordering. This is development evidence, not a verified release baseline for the new branch.

### Build, replace, delete, defer

- **Build:** reusable resume evidence profiles and preparation lifecycle, compact AI rubric/evidence wire schemas, profile-based batch assessment, lean pipeline, job-rubric cache, overall-fit API wiring, category/skill summary, stale-response guards, AI-only evaluation report.
- **Replace on the new path:** truncated inputs, free-form AI percentages, candidate-dependent rubric choices, unvalidated keywords, default-50 evaluation handling, rounded-score ordering.
- **Delete from borrowed code:** role/presentation bonuses and fields, learning credit, offline dispatch/exports, repair loops, speculative wrappers. Remove projected-score/Boost UI on the new path; preserve old compatibility functions unless all callers are migrated.
- **Defer:** improving offline matching, OCR, embeddings/vector databases, fine-tuning, provider frameworks, configurable scoring UI, full evidence UI, automatic semantic repair, job-metadata/rubric call consolidation until measured duplication justifies it.
- Never delete or change files on the source branch as part of this plan. Do not cherry-pick entire feature commits that introduce unrelated landing/UI, storage, or deployment changes already present in main.

## File map in the new branch

| Files | Responsibility |
|---|---|
| Create/adapt `backend/services/matching/{__init__,models,normalization,chunking,scoring}.py` | Narrow contracts, shared aliases, bounds, pure arithmetic/ranking |
| Create `backend/services/matching/extraction.py` | Lean AI extraction, wire-schema validation, selected source/date helpers; no offline API |
| Create `backend/services/matching/pipeline.py` | Frozen rubric, batching, cache, deadline, complete-comparison policy |
| Create `backend/services/matching/profiles.py`; profile contracts in `models.py` | Job-independent profile extraction, validation and reuse; existing extraction helpers remain shared |
| Modify `backend/services/{ai_engine,skill_matching,document_parser}.py`, `backend/models.py` | Existing provider integration and warning propagation |
| Modify `backend/{main,config,storage}.py` | Authenticated endpoints/flag and tenant-scoped caches/migrations |
| Modify `frontend/src/api/client.js`, `frontend/src/components/ResumeFitRanker.jsx`, `frontend/src/App.jsx` | Request lifecycle, source availability, summaries, resume selection |
| Modify `frontend/src/components/ResumeLibrary.jsx` | Preserve parser warnings and prepare profiles after content saves; show analysis status without UI redesign |
| Create/port `tests/test_match_{contracts,normalization,chunking,extraction,scoring,ranking,pipeline,snapshots,api}.py`; modify parser/AI tests | Contract and behavior regressions in existing pytest setup |
| Create `tests/test_match_profiles.py` | Profile reuse across jobs, invalidation, source fallback, persistence and upload failure isolation |
| Create/port `frontend/src/test/ResumeFitRanker.test.jsx`; modify `AppRouting.test.jsx` if caller coverage needs it | User-visible state and callback regressions |
| Create/adapt `scripts/evaluate_matching.py`, `tests/test_match_benchmark.py`, `docs/ai-matching-evaluation.md` | AI-only measurements and release record |

## Task 1: Preserve source work and pin a clean base

**Files:** Transfer this plan; create `docs/ai-matching-transfer.md` in the destination checkout only. Read source status/diffs, main refs, applicable instructions, and relevant source tests.

**Interfaces:** Produces destination workspace, pinned base SHA, source HEAD SHA, and a manifest mapping each selected source file/helper/test to committed or working-tree provenance and SHA-256. No product implementation yet.

- [x] **Step 1: Record source status and full relevant diffs, without keys/private documents.** Record hashes for selected working files and identify commit-only versus working-tree fixes. Read applicable AGENTS.md instructions before mutations.
- [x] **Step 2: Fetch main and create the approved new branch in an isolated worktree.** Use the app-managed worktree workflow at execution time; create from fetched origin/main. Suggested branch subject: `ai-overall-job-fit`; apply higher-priority branch-prefix rules. Never switch the dirty source checkout. Transfer the plan into the destination.
- [x] **Step 3: Verify the destination base.** Confirm clean destination status, full base SHA and source remains unchanged; establish baseline backend tests and frontend build. Record failures before any code transfer.
- [x] **Step 4: Write the transfer manifest.** Explicitly list exclusions and source fix/test pairs from the inventory above. Recheck source hashes just before each copy; if another chat changes them, inspect the new diff rather than silently absorbing it.
- [x] **Step 5: Commit only destination planning records.** Subject: `docs: record AI matching transfer scope`.

## Task 2: Contracts, aliases, input bounds, and document completeness

**Files:** Borrow/adapt `matching/models.py`, `normalization.py`, `chunking.py`, minimal `__init__.py`; modify `skill_matching.py`, `document_parser.py`, `backend/models.py`, upload/parse routes and warning persistence in `storage.py`. Tests: contracts, normalization, chunking, document parser, resume API.

**Interfaces:** `Requirement`, `Evidence`, `RequirementResult`, `RequirementExtraction`, `EvidenceExtraction`, `ScoreBreakdown`, `Evaluation`, `EvaluationBatch` retain source branch names; add `Requirement.kind` allowed values `skill|semantic|tenure|credential|experience`, category enum, and `Evaluation.rubric_fingerprint: str`, `skill_coverage_score: Decimal|None`, `reason_codes: list[str]`. Initial reason codes are `source_incomplete`, `rubric_limit`, `invalid_provider_response`, `missing_assessment`, `unresolved_evidence`, `deadline_exceeded`, `no_assessable_requirements`; human-readable warnings are separate. `chunk_text(text: str) -> list[TextChunk]`; `canonicalize_skill(value: str) -> str`. `Resume.extraction_warnings: list[str]` defaults empty; storage migration is additive.

- [x] **Step 1: Add focused failing checks.** `test_incomplete_evaluation_has_no_score_or_rank` asserts null score/rank and false top flag; `test_score_bounds_are_strict` rejects -1, 101 and string scores; `test_aliases_dedupe_without_losing_unknown_skill` checks Postgres/PostgreSQL and an unknown literal; `test_chunks_cover_late_text` proves full coverage beyond 8,000 characters; `test_partial_pdf_persists_warning` verifies one unreadable page blocks complete matching even with readable pages.

```python
assert canonicalize_skill("Postgres") == canonicalize_skill("PostgreSQL")
assert canonicalize_skill("NewVendorDB") == "newvendordb"
assert incomplete.match_score is None and incomplete.rank is None
assert incomplete.is_top_match is False
assert saved_resume.extraction_warnings
```
- [x] **Step 2: Run those focused tests.** `./.venv/Scripts/python.exe -m pytest -q tests/test_match_contracts.py tests/test_match_normalization.py tests/test_match_chunking.py tests/test_document_parser.py`. Confirm failures correspond to missing new behavior.
- [x] **Step 3: Port minimal contracts/helpers and warning propagation.** Restrict exported names; remove role fields and offline import wiring. Keep source coordinates immutable. Verify both SQLite and PostgreSQL warning migrations; API warning metadata cannot be lost through parse/save.
- [x] **Step 4: Rerun the focused tests plus existing skill/parser callers.** Expected PASS, including Java versus JavaScript, C versus C++, SQL versus NoSQL. Audit every caller of modified shared helpers.
- [x] **Step 5: Commit the cohesive contract/input change.** Subject: `feat: validate matching inputs and evidence contracts`.

## Task 3: Extract and freeze the full overall-fit JD rubric

**Files:** Create lean `matching/extraction.py`; modify `AIEngine.extract_match_chunk(payload: dict[str, Any], *, timeout: float|None=None) -> Any`; tests `test_match_extraction.py`, `test_ai_engine.py`.

**Interfaces:** `extract_requirements(text: str, *, engine: Any, deadline: float) -> RequirementExtraction`. Provider task `requirements` returns chunk acknowledgment and proposals `{category, kind, canonical_key, alternatives, source_quote, required_months}` without scores/offsets/IDs. Backend locates source spans, validates type/grouping and deduplicates, then assigns stable IDs from normalized requirement identity plus JD source fingerprint. Identical source plus extractor version yields stable IDs for the same accepted interpretation. AI classification itself is not assumed deterministic; cache freezes the accepted rubric.

- [x] **Step 1: Add failing extraction tests.** `test_overall_rubric_keeps_late_responsibility_and_preferred_tenure`; `test_or_is_one_requirement_and_and_is_two`; `test_repeated_required_and_preferred_skill_counts_once`; `test_unknown_technology_survives_taxonomy`; `test_unquoted_or_injected_requirement_is_rejected`; `test_over_limit_rubric_fails_without_trimming`. Assert all four categories and minimum-month semantics, no benefit/company/eligibility requirements, and exact stored source slices.

```python
assert len(or_requirements) == 1 and len(and_requirements) == 2
assert set(or_requirements[0].alternatives) == {"java", "python"}
assert tenure.required_months == 12  # JD explicitly requests 1–3 years.
assert all(jd[r.source_start:r.source_end] == r.source_quote for r in requirements)
```
- [x] **Step 2: Run `./.venv/Scripts/python.exe -m pytest -q tests/test_match_extraction.py tests/test_ai_engine.py`.** New tests should fail until task implemented.
- [x] **Step 3: Implement full-source AI extraction with the defined wire contract.** Supply category/group definitions, explicit untrusted-document instructions and JSON schema in the guarded request. Derive offsets server-side using selected provenance helpers. Use full documents up to 8,000 characters and all overlapping chunks beyond that. Dedupe source overlap and semantic identity; reject non-equivalent category conflicts rather than guessing. Avoid technical candidate whitelisting and lexical gates that prevent legitimate semantic matches. Accepted rubric above 64 unique requirements is needs_review with `rubric_limit`, not shortened.
- [x] **Step 4: Verify focused tests and request shape.** Ensure no `text[:6000]` on the new path, no model-generated score/weights, temperature 0, valid chunk coverage. A successful JSON parse alone must not imply successful extraction.
- [x] **Step 5: Commit.** Subject: `feat: extract a shared overall job fit rubric`.

## Task 4: Batch AI evidence assessment without invented completion

**Files:** Lean `matching/extraction.py`, existing `ai_engine.py`; `test_match_extraction.py`, `test_ai_engine.py`.

**Interfaces:** `extract_evidence_batch(resumes: list[Resume], profiles: dict[str, ResumeProfile], requirements: list[Requirement], *, as_of: date, engine: Any, deadline: float) -> dict[str, EvidenceExtraction]`. Provider task `evidence_batch` includes resume IDs, relevant validated profile records/source contexts and one rubric; supply full source chunks only when the profile cannot conclusively support assessment. Result contains one record per supplied resume ID, explicit assessed/unresolved ID sets, and evidence proposals. Server computes offsets, sections and validated intervals. Pipeline owns batch partitioning; this function validates a supplied batch. Implement Task 4A before this task.

- [ ] **Step 1: Add failing checks.** `test_omitted_resume_is_incomplete_not_fifty`; `test_duplicate_or_foreign_ids_reject_batch`; `test_missing_requirement_not_treated_as_absence`; `test_listed_and_learning_not_demonstrated`; `test_semantic_paraphrase_can_match_with_source_quote`; `test_negation_and_injection_cannot_earn_credit`; `test_verified_tenure_does_not_need_provider_guess`; `test_overlap_dedup_preserves_positive_evidence`. Include a responsibility supported by different wording so a lexical-overlap gate would fail.

```python
assert omitted.status != EvaluationStatus.COMPLETE
assert missing_id in omitted.unresolved_requirement_ids
assert skills_list_item.level == EvidenceLevel.LISTED
assert learning_item.level == EvidenceLevel.LEARNING
assert semantic_item.level == EvidenceLevel.DEMONSTRATED
assert resume_text[semantic_item.source_start:semantic_item.source_end] == semantic_item.source_quote
```
- [ ] **Step 2: Run extraction/AI tests and confirm intended failures.** No live provider use in these tests.
- [ ] **Step 3: Implement validation and selected local verification.** Require unique exact resume/requirement coverage. Source quote whitespace normalization may locate a quote, but store the exact saved-source substring. Reject ambiguity instead of using the first match. Use proven local relevant dated-work checks and explicit credential verification where safely conclusive; otherwise AI interprets semantic evidence. Do not require a JD word to occur verbatim for semantic support, but do require the quote to demonstrate the specific requirement. Validate positive items before considering any coverage-metadata reconciliation. Unsupported metadata/claims fail closed; no retry loop.
- [ ] **Step 4: Rerun focused checks.** Assert omission reason codes, no positive credits from negative/learning text, all chunk observations accounted for, and all response scores/ranks ignored/rejected. Interval sources exclude education, future work and unrelated roles.
- [ ] **Step 5: Commit.** Subject: `feat: assess resume evidence in validated AI batches`.

## Task 4A: Prepare and reuse job-independent resume evidence profiles

**Execution order:** 1 -> 2 -> 3 -> 4A -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10. The inserted task preserves existing task references.

**Files:** Create `matching/profiles.py`, `tests/test_match_profiles.py`; adapt `matching/models.py`, guarded `AIEngine.extract_match_chunk`, `storage.py`; preparation endpoint/UI integration belongs to Tasks 7–8.

**Interfaces:** `ProfileFact` has `id`, `kind: skill|activity|credential|employment`, `canonical_key`, `level: EvidenceLevel`, `source_quote`, `source_start`, `source_end`, `section`, optional `employment_id` and source-verified start/end dates. `ResumeProfile` has resume/source identity, status, profile extractor version, profile fingerprint, facts, processed source-chunk spans and warnings; no job/scorer fields. `extract_resume_profile(resume: Resume, *, engine: Any, deadline: float) -> ResumeProfile`; `get_or_build_resume_profile(resume: Resume, *, user_id: str, engine: Any, storage: Any, deadline: float) -> ResumeProfile`. Storage: `get_resume_profile(*, user_id: str, resume_id: str, source_hash: str, version_key: str) -> dict|None`, `save_resume_profile(*, user_id: str, resume_id: str, source_hash: str, version_key: str, payload_json: str) -> None`, `delete_resume_profiles(*, user_id: str, resume_id: str) -> int`.

- [ ] **Step 1: Add failing profile checks.** `test_two_jobs_extract_resume_once`; `test_scorer_change_reuses_profile`; `test_content_edit_invalidates_but_rename_does_not`; `test_profile_is_user_and_provider_scoped`; `test_profile_covers_late_activity_and_all_chunks`; `test_failed_profile_keeps_saved_resume`; `test_late_old_content_profile_not_current`; `test_deleted_resume_removes_profiles`; `test_missing_profile_skill_checks_original_source`; `test_semantic_paraphrase_not_lost_by_keyword_prefilter`. Add SQLite/PostgreSQL persistence checks and corrupt-cache rejection.

```python
assert first_job_profile.profile_fingerprint == second_job_profile.profile_fingerprint
assert profile_extractor.calls == 1
assert rescored_profile.profile_fingerprint == original_profile.profile_fingerprint
assert renamed_profile.profile_fingerprint == original_profile.profile_fingerprint
assert edited_profile.source_hash != original_profile.source_hash
assert storage.get_resume(resume.id, user_id=user_id) is not None  # Analysis failed, save succeeded.
```

- [ ] **Step 2: Run `./.venv/Scripts/python.exe -m pytest -q tests/test_match_profiles.py`.** Confirm failures identify absent profile behavior, not unrelated fixtures.
- [ ] **Step 3: Implement full-source profile extraction and atomic persistence.** Provider task `resume_profile` receives source chunks, schema and untrusted-document instructions, never JD data. Reuse exact-span, section, negation and date helpers. Deduplicate overlapping facts; validate coverage for all chunks. Persist only complete source-validated profiles in `resume_profiles` with unique `(user_id,resume_id,source_hash,version_key)` and profile fingerprint. Read the accepted row after concurrent insert; verify the resume still exists with the same content hash before publishing. Do not duplicate raw resume text in the table beyond quoted evidence.
- [ ] **Step 4: Verify reuse and safe fallback.** New JD and scorer changes do not call profile extraction. Demonstrated skills/activities retain quote context; unclear job relevance still routes through Task 4, rather than inheriting generic demonstrated credit. Literal misses check the full original source; semantic retrieval considers all activities and escalates inadequate context to source assessment. Failed source coverage stays unresolved. No embeddings or keyword-only ranking.
- [ ] **Step 5: Commit.** Subject: `perf: reuse resume vault evidence profiles`.

## Task 5: Pure scoring and honest competition ranking

**Files:** Borrow/adapt `matching/scoring.py`; tests `test_match_scoring.py`, `test_match_ranking.py`.

**Interfaces:** `calculate_score(requirements: list[Requirement], evidence: list[Evidence], *, as_of: date) -> ScoreBreakdown`; `calculate_verified_months(intervals: list[RelevantInterval], as_of: date) -> Decimal`; `rank_evaluations(evaluations: list[Evaluation]) -> list[Evaluation]`. No `role_focus` parameter. Add `ScoreBreakdown.skill_coverage_score: Decimal|None`. Pipeline calls scorer only after explicit complete assessment.

- [ ] **Step 1: Add failing arithmetic checks.** `test_category_weights_produce_overall_score`: category credits 1, .5, 0, 1 yield 75.00 and display 75 under 60/20/15/5. `test_absent_categories_renormalize`: only required/preferred, credits .5/1, yields 53.85. `test_learning_has_zero_credit`; `test_responsibility_listing_has_zero_credit`; `test_tenure_union_and_minimum_threshold`; `test_repeated_evidence_never_multiplies_credit`; `test_raw_scores_rank_before_display_rounding`; `test_equal_raw_scores_rank_one_one_three`.

```python
assert four_category_result.raw_score == Decimal("75.00")
assert four_category_result.match_score == 75
assert two_category_result.raw_score == Decimal("53.85")
assert learning_only_result.match_score == 0
assert [e.rank for e in tied_rankings] == [1, 1, 3]
assert [e.is_top_match for e in tied_rankings] == [True, True, False]
```
- [ ] **Step 2: Run `./.venv/Scripts/python.exe -m pytest -q tests/test_match_scoring.py tests/test_match_ranking.py`.** Verify the deliberate departures from source weights/credits/ranking fail before adaptation.
- [ ] **Step 3: Implement the design-baseline formula.** Retain Decimal and interval union; remove role/presentation arithmetic and learning credit. Sort raw score descending with stable resume ID for display only. Distinct raw scores rounded to the same integer are not ties; expose raw score in summary. Keep category-qualified credits and skill-only metric distinct. A positive/contradicted conflict becomes unresolved at validation, never hidden as a confident zero.
- [ ] **Step 4: Verify exact arithmetic and invariance.** Reordering resumes or adding another version cannot change an individual's score under the same rubric; cached scores and newly computed scores use identical arithmetic.
- [ ] **Step 5: Commit.** Subject: `feat: calculate comparable overall fit scores`.

## Task 6: Frozen rubric cache, result cache, batching, deadlines

**Files:** Create lean `matching/pipeline.py`; adapt selected migrations/CRUD in `storage.py`; tests `test_match_pipeline.py`, `test_match_snapshots.py`.

**Interfaces:** `evaluate_resumes(job_text: str, resumes: list[Resume], *, user_id: str, as_of: date, engine: Any, storage: Any, fresh: bool=False, deadline_seconds: float=300.0) -> EvaluationBatch`. Load/build profiles through Task 4A, then call Task 4 with them. Storage retains source `save_matching_snapshot/get_matching_snapshot/delete_matching_snapshots_for_resume` signatures. Add `save_matching_rubric(*, id: str, user_id: str, job_hash: str, version_key: str, payload_json: str) -> None` and `get_matching_rubric(*, user_id: str, job_hash: str, version_key: str) -> dict|None`. Add `Evaluation.profile_fingerprint: str` and `assessment_version: str` to reference accepted evidence provenance.

- [ ] **Step 1: Add failing tests.** `test_warm_comparison_zero_calls_same_ids`; `test_partial_cache_hit_reuses_frozen_rubric`; `test_provider_endpoint_model_and_versions_invalidate`; `test_users_cannot_share_rubric_or_evidence`; `test_resume_edit_or_delete_invalidates`; `test_deadline_result_not_scored_or_cached`; `test_partition_respects_five_docs_and_forty_thousand_chars`; `test_incomplete_batch_has_no_winner`; `test_invalid_cached_json_recomputed_safely`. Cover one cache hit plus one new resume against an identical rubric fingerprint.

```python
assert warm_provider.calls == 0
assert [e.evaluation_id for e in warm.evaluations] == [e.evaluation_id for e in cold.evaluations]
assert len({e.rubric_fingerprint for e in mixed.evaluations}) == 1
assert incomplete_batch.comparison_complete is False
assert all(e.rank is None and not e.is_top_match for e in incomplete_batch.evaluations)
```
- [ ] **Step 2: Run pipeline/snapshot tests; confirm missing behavior fails.** Add SQLite and PostgreSQL migration/CRUD coverage using existing storage test patterns.
- [ ] **Step 3: Implement minimal orchestration and caches.** Add `matching_rubrics` with unique `(user_id,job_hash,version_key)`, payload, fingerprint and creation time. Rubric identity includes endpoint/model/protocol and extractor/prompt/alias versions, never secret keys. Assessment snapshot identity additionally includes rubric/profile fingerprints, assessment version, resume source hash and server as_of date; scorer version stays in the payload for local score recomputation. Cache complete validated artifacts only; revalidate loaded payload against current source/contracts. Delete dependent snapshots if a rubric is replaced. Keep first persisted rubric under concurrent creation via atomic conflict-safe insertion then read winner; never let two concurrent requests score the same cache identity with different rubrics. Snapshot writes use existing storage locks.
- [ ] **Step 3A: Separate reusable evidence from derived scoring in the snapshot identity.** The persisted evidence snapshot key includes rubric/profile fingerprints, provider and assessment versions and assessment date, but excludes scorer version. Keep scorer version inside the payload; when only scoring changes, load and validate cached requirement evidence, recompute raw/category/skill scores locally and persist the updated evaluation. Do not add a second assessment table. Profile extraction keys exclude both assessment date and scorer version. Test `test_scorer_change_recomputes_without_provider_calls`, `test_new_job_reuses_profiles_but_assesses_new_requirements`, `test_changed_resume_only_reextracts_changed_profile`, and `test_profile_version_invalidates_dependent_assessment`. Old cached scoring must never be displayed unchanged after a version bump.
- [ ] **Step 4: Implement bounded batches and verify tests.** Ordinary five prepared resumes need at most one semantic evidence call; overflow partitions supplied profile/source context deterministically and uses at most two simultaneous calls. Any needed source fallback processes all chunks before scoring. Propagate remaining deadline to profile extraction and guarded assessment transport; reject late responses before scoring/caching. Log separate profile/rubric/assessment calls, durations and reason codes, no source text. Warm results are re-ranked for the current selected set rather than reusing stale rank metadata.
- [ ] **Step 5: Commit.** Subject: `perf: cache frozen rubrics and resume assessments`.

## Task 7: Authenticated AI-only endpoint and source availability

**Files:** `backend/main.py`, `backend/config.py`, `backend/models.py`, `frontend/src/api/client.js`; tests `test_match_api.py`, existing API/client tests.

**Interfaces:** `/api/features -> {matching_v2_enabled: bool}`; `POST /api/resumes/evaluate` consumes the baseline request and returns EvaluationBatch. `evaluateResumes(jobText, resumeIds, {fresh=false, signal=null}={})` forwards AbortSignal. Derive as_of server-side; reject client attempts to supply dates/weights/rubrics on this endpoint.

**Profile lifecycle interface:** Add authenticated `POST /api/resumes/{resume_id}/profile` to prepare/reuse the current saved profile via Task 4A; no caller-provided text, keys or facts. Return `{resume_id, status, source_hash, profile_fingerprint, warnings}` with sanitized errors, not full profile facts. Respect the same feature flag, configured-provider checks and AI rate limit. The vault calls it after a successful content save when enabled; older resumes use lazy preparation through evaluation. Failed preparation cannot roll back upload/save. Verify foreign IDs, repeat preparation zero extraction calls, offline/flag-off behavior, and content edits during preparation.

- [ ] **Step 1: Add failing API checks.** `test_flag_off_preserves_legacy`; `test_foreign_duplicate_and_unknown_resume_ids_rejected`; `test_empty_or_oversized_job_rejected`; `test_offline_profile_does_not_enter_ai_evaluation`; `test_provider_failure_never_returns_legacy_percentage`; `test_full_raw_jd_reaches_pipeline`; `test_client_scoring_fields_rejected`. Preserve authenticated rate limiting.

```python
assert flag_off_response.status_code == 404
assert offline_response.status_code == 409
assert failed_provider_response.status_code == 502
assert pipeline_job_text == full_jd
assert legacy_response.status_code == 200
assert isinstance(legacy_response.json(), list)
```
- [ ] **Step 2: Run `./.venv/Scripts/python.exe -m pytest -q tests/test_match_api.py`.** Confirm expected new route/contract failures, no external calls.
- [ ] **Step 3: Adapt branch route/flag/client patterns.** Fetch authoritative user-owned resumes; use saved provider selection; forward raw JD. Return 404 when flag disabled, 409 with `ai_provider_required` for offline/unconfigured mode, normal 400/422 input errors, and sanitized 502 provider failure. Do not log provider response bodies or keys. Incomplete source-backed evaluations return structured statuses/reasons, not fabricated legacy results.
- [ ] **Step 4: Verify old endpoint tests and new authenticated journey.** Analyze job -> save resumes -> evaluate -> edit/save -> evaluate -> switch job/profile -> rollback flag. Confirm older jobs without source text cannot produce overall-fit scores and continue using a labeled legacy experience.
- [ ] **Step 5: Commit.** Subject: `feat: expose guarded AI overall fit evaluation`.

## Task 8: Minimal truthful UI and request lifecycle

**Files:** `ResumeFitRanker.jsx`, `App.jsx`, client helper; `ResumeLibrary.jsx` only if required to preserve warnings. Tests `ResumeFitRanker.test.jsx` and applicable App tests.

**Interfaces:** Existing `onBestResumeSelected` accepts a stored Resume or null at the App boundary. New batch results use `resume_id`; resolve against current stored resumes. With a unique completed leader select its Resume; for tied/incomplete results clear automatic selection and allow explicit selection. Keep `id`/`resume_id` compatibility guards from source callback fixes.

- [ ] **Step 1: Add failing UI checks.** `reranks_after_same_count_content_edit`; `ignores_previous_job_response`; `ignores_previous_profile_response`; `ties_show_equal_rank_without_auto_choice`; `incomplete_batch_has_no_top_badge`; `adopted_keyword_does_not_raise_backend_score`; `missing_raw_text_requests_full_jd`; `nullable_best_resume_callback_is_safe`.

```javascript
expect(onBestResumeSelected).not.toHaveBeenCalledWith(expect.objectContaining({ id: 'tied-a' }));
expect(screen.queryByText('Top Fit')).not.toBeInTheDocument(); // Incomplete batch.
expect(screen.queryByText(/Boost/)).not.toBeInTheDocument(); // Overall-fit mode.
expect(screen.getByText('Overall job fit')).toBeInTheDocument();
```
- [ ] **Step 2: Run `npm run test:run -- src/test/ResumeFitRanker.test.jsx` in frontend.** Confirm failures target these behaviors.
- [ ] **Step 3: Adapt only useful routing/state pieces.** Abort obsolete requests and use a monotonically increasing request token to reject late results even when cancellation is ineffective. Dependencies include source/content revisions and provider/profile refresh identity, not resume count alone. Clear old results when source changes or request fails. Prevent older requests' finally blocks from clearing a newer request's loading state.
- [ ] **Step 3A: Prepare profiles after vault saves without failing the save.** In `ResumeLibrary.jsx` and the API helper, request profile preparation after successful upload/content edit only when AI feature/provider is enabled. Show preparing/ready/failed-with-retry status; do not expose fact schemas or cache keys. Name-only edits reuse profiles. Existing vault entries remain usable and prepare lazily on comparison. Add `profile_analysis_failure_preserves_uploaded_resume`, `repeat_profile_preparation_reuses_saved_analysis`, and `old_resume_profiles_lazily_without_bulk_calls` checks.
- [ ] **Step 4: Show backend-authoritative overall/raw/category and separate skill-coverage summaries.** Label `Overall job fit`; explain percentage as source-backed fit, never hiring probability. Show tied leaders and actionable review/error states with accessible controls. Remove projected-score/Boost arithmetic on the new path; adopted suggestions trigger a real reevaluation only after saved resume text changes. No new full evidence component. Verify tests and frontend build.
- [ ] **Step 5: Commit.** Subject: `fix: display current evidence backed fit rankings`.

## Task 9: Quality, stability, speed, and release evidence

**Files:** Adapt `scripts/evaluate_matching.py`; `tests/test_match_benchmark.py`; `docs/ai-matching-evaluation.md`; anonymized authorized fixtures under `tests/fixtures/matching/` only.

**Interfaces:** AI-only report contains run/source/rubric fingerprints, provider/model (no keys), complete/incomplete counts and reasons, correct/tied/reversed/unscored strict pairs, per-category/skill scores, per-job elapsed time, cache behavior, provider calls/tokens and usage availability. Missing token usage is unavailable, not zero. Existing cross-person/offline fixture outcomes never satisfy this gate.

**Profile measurement extension:** Report profile extraction, rubric extraction and semantic assessment calls/tokens separately. Measure (a) first upload/profile preparation, (b) first job with prepared profiles, (c) a second different job against the same vault, (d) a warm identical comparison, (e) one edited resume, and (f) a scorer-only version bump. Second-job comparison must make zero profile-extraction calls; scorer-only change must make zero profile-extraction/assessment calls. Count original-source fallback frequency and compare ranking quality against full-source assessment to detect profile omissions. A speed gain that hides evidence or worsens completeness does not pass.

- [ ] **Step 1: Add failing report checks.** `test_tied_and_unscored_pairs_stay_in_denominator`; `test_report_separates_per_job_latency_from_suite_total`; `test_missing_usage_is_unavailable`; `test_same_person_gate_rejects_cross_person_fixture`; `test_stability_reports_repeated_order_changes`.

```python
assert report["strict_pairs"]["total"] == 3  # One correct, one tied, one unscored.
assert report["strict_pairs"]["correct"] == 1
assert report["token_usage"] is None  # Provider omitted usage metadata.
assert cross_person_report["release_gate_passed"] is False
assert changing_order_report["stability"]["reversed_pairs"] == 1
```
- [ ] **Step 2: Run `./.venv/Scripts/python.exe -m pytest -q tests/test_match_benchmark.py`.** Confirm intentional missing report behavior fails.
- [ ] **Step 3: Implement lean measurement/reporting.** Establish main and new-branch baselines with the same approved provider and same allowed development inputs. Use temporary isolated storage for true cold runs; test repeated evidence against a fixed rubric separately from repeated cold rubric extraction. Report rubric drift separately from evidence/ranking drift. No test-only score overrides or desired-winner bonuses.
- [ ] **Step 4: Perform authorized development measurements.** At least three runs on each approved development comparison. Require complete evaluations and no preferred-pair reversal across those repeats before freezing a fresh holdout. If it fails, trace category/evidence contributions and fix the measured cause; do not add weight knobs or consume holdout prematurely.
- [ ] **Step 5: Run untouched reviewed holdout and performance gates only after development passes.** Proposed gate: at least 10 real same-person jobs and 20 strict reviewed pairs; >=90% strict ordering agreement, 100% evaluation completeness, no invalid quote credits. Ties/unscored strict preferences are failures; explicitly reviewed ties are measured separately. Repeat holdout evaluation three times against the frozen rubric; all runs must satisfy the gate. These requirements are new proposed gates, not historical achievements.
- [ ] **Step 6: Measure individual cold/warm comparisons.** Five 8,000-character resumes plus one 8,000-character JD: complete each cold comparison within 120 seconds, report actual per-job latency and calls/tokens; warm repeats preserve IDs/scores with zero calls. Compare to main cold baseline, and report any latency/token regression honestly. A five-job total cannot establish the single-job target. Include analysis-call latency when reporting the full user journey.
- [ ] **Step 7: Publish the gate report and commit.** Subject: `test: measure AI ranking quality and cache performance`. Leave flag off if any required gate fails; list exact failures and next diagnosis.

## Task 10: Final regression, selective cleanup, and release handoff

**Files:** Only implementation paths above plus README/`docs/ai-matching-evaluation.md`. Do not import unrelated source-branch changes.

**Interfaces:** Produces reviewed destination diff, check results, source-transfer audit, default-off rollout instructions, and rollback instructions.

- [ ] **Step 1: Audit imports/callers and delete unused borrowed code.** Remove offline-only exports, unused wire models and role fields from the new module; retain legacy functions still called by old endpoints/optimizer. Verify no scoring/quote validation exists in the frontend and no separate scorer calculates the same percentage.
- [ ] **Step 2: Run full relevant verification in the destination.** `./.venv/Scripts/python.exe -m pytest -q --basetemp=scratch/pytest-ai-overall-fit`; frontend `npm run test:run`, `npm run build`; `git diff --check`. Record exact outcomes, not historical 517/82 counts. Any unexplained baseline or new failure blocks a ready-for-release claim.
- [ ] **Step 3: Verify the browser journey.** Upload readable/unreadable resume, analyze/paste JD, view scores and ties, save edit, rerank, switch job/provider mid-request, retry failure, use older source-less job, and disable flag. Confirm no stale selection/percentage or private-source logging.
- [ ] **Step 4: Review the complete destination diff against the transfer manifest.** Every borrowed working-tree fix has a corresponding regression; source checkout hashes/status remain intact except independently authored source-chat changes. No keys, private fixtures, unrelated main changes, or deployment changes included.
- [ ] **Step 5: Commit final documentation and hand off for owner review.** Subject: `docs: document AI matching validation and rollout`. Push/PR only when authorized by the subsequent execution request/workflow. Release flag activation requires explicit approval after passing gates; rollback disables the flag and restores labeled legacy/offline behavior without deleting saved data.

## Acceptance and coverage checklist

| Loose end | Owning task | Completion evidence |
|---|---|---|
| Dirty source checkout / newer fixes in another chat | 1, 10 | Pinned refs, source hashes, selective manifest, preserved source state |
| JD/resume truncation and partial parser output | 2–4 | Full chunk coverage and persisted unreadable-page warnings |
| Aliases / unknown skills / grouping / repeated requirements | 2–3 | Canonical, source-backed stable rubric tests |
| Semantic matching and role-relevant work | 3–5 | Paraphrase evidence accepted; generic similarities rejected; responsibilities included |
| Arbitrary percentages / skill-list overcredit / learning credit | 4–5 | Verified statuses and exact deterministic arithmetic |
| Invented tenure / overlapping dates / eligibility mixing | 4–5 | Relevant dated-work checks, interval union, eligibility separate |
| Missing/duplicate responses / false zero / fabricated 50% | 4, 7 | Exact coverage validation, incomplete/null score |
| Ties / rounded-score ordering / automatic best selection | 5, 8 | Raw-score ordering, competition ties, safe selection |
| Job-rubric drift / mixed cache results / concurrent writes | 6 | Atomic frozen rubric and fingerprint-dependent snapshots |
| Repeated costs / model switches / cross-user cache leakage | 6–9 | Zero-call warm run, invalidation and isolation tests |
| Repeated full-resume extraction for new jobs | 4A, 4, 6, 9 | Same profile fingerprints across jobs; zero second-job profile calls |
| Incomplete profile mistaken for absent evidence | 4A, 4, 9 | Full-source literal/semantic fallback and omission quality checks |
| Vault edits, failed preparation, rename and deletion | 4A, 7–8 | Save survives analysis failure; content-only invalidation and derived-data cleanup |
| Scorer-only change unnecessarily repeats AI work | 5–6, 9 | Reused profile and validated evidence; locally recalculated score |
| Stale frontend requests / same-count edits / projected boosts | 8 | Cancellation plus generation guard and authoritative percentages |
| Synthetic-only “quality” / unstable rankings / misleading speed | 9 | Reviewed same-person gates, repeated runs, per-job measurements |
| Legacy clients / offline fallback / safe rollback | 7–10 | Separate old route, explicit modes, default-off flag journey |

## Self-review record

- Design requirements map to Tasks 1–10 plus inserted Task 4A and the coverage table; there is no planned offline enhancement or unexplained role bonus. Execute Task 4A before Task 4.
- Signatures/model names are consistent across extraction, scoring, pipeline, storage and API tasks. New fields have explicit null/incomplete semantics.
- Source helpers are references to copy with dependencies/tests, not assumed available on main. Current model/schema changes are explicitly marked adaptations.
- All five Review Focus items have named checks in owning tasks. Execution outcomes are tracked in Current task status; no live provider quality runs have been performed.
- Numeric/batching/release choices are proposals for owner review, not externally established best practices or proven quality improvements.
- Only this plan document is created at planning time. Execution, source transfer, branch creation, external provider use and rollout remain later steps.
