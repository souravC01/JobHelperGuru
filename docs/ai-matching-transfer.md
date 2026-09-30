# AI matching source transfer record

Date: 2026-09-30. Task 1 only; no application code transferred.

- Source branch: feat/evidence-based-resume-matching
- Source commit: `bccc93836303f5b2ede0faf34e4c1b8d6c6316fa` (includes formerly uncommitted prototype fixes).
- Fetched main/base: `9fa7b26a4ca78c38dd977d1eff0df1f30c11b5c5`.
- Destination branch: `codex/ai-overall-job-fit`.
- Source chat: Review resume matching logic (`01a0b14d-175b-7460-8a42-fcb597b3c979`).
- Source status at capture: clean tracked/untracked status. Ignored planning/private files remain untouched.
- Full selected-source diff and JSON hash inventory: local ignored `.superpowers/sdd/2026-09-30-ai-overall-job-fit/`; never copy private scratch inputs.
- Commit plan explicitly because `docs/superpowers/` is ignored. No application files, keys, private inputs or provider profiles are staged.

## Selective transfer rules

Borrow aliases, strict contracts, quote/context/date validation, chunking, category arithmetic, tie handling, warning propagation, cache patterns and associated tests. Extract helpers with their dependencies; do not restore whole files over newer main blindly.

Build resume profiles and lean AI batching/orchestration. Replace free-form percentages and unsafe result defaults on the new path. Exclude role/presentation bonuses, learning credit, offline expansion, repair loops, full evidence UI, unrelated landing/deployment changes and private development data. Preserve legacy endpoint compatibility. Audit transport deadline changes separately with existing outbound restrictions unchanged.

Source tests paired with implementation: normalization/skill tests for aliases; extraction tests for quotes, context, negation, date/tenure and metadata; scoring/ranking tests for category arithmetic/ties; pipeline/snapshot/API tests for cache/ownership/warnings; parser tests for unreadable pages; frontend tests for callback and request lifecycle; transport tests for deadlines. Expected policy changes must update tests explicitly rather than importing historical expected scores.

## Captured source files

| File | SHA-256 of source working bytes | Provenance |
|---|---|---|
| `backend/config.py` | `511b36968f0db6ce2fe188909c11231ed3aec4972a9e23a6741f56b49bc66103` | committed at source HEAD |
| `backend/main.py` | `540e0b7195b4d783d5a2a1764b0e36e8c99e1819d04b2799ab57e33ff4dd462a` | committed at source HEAD |
| `backend/models.py` | `564fe9589346f44462479a829bce31539eb0704464649391844e89bb6ae1d7b5` | committed at source HEAD |
| `backend/services/ai_engine.py` | `daad2e252c7cdc1cb64ae9c3fcb530ae82c6b1d6730bbc814778957f6cb35430` | committed at source HEAD |
| `backend/services/document_parser.py` | `1b03c647ed36bb04a32a0267d0233b044dfcb8bde5ad0c2466a239ddefcdf5d9` | committed at source HEAD |
| `backend/services/heuristic_parser.py` | `b7fc1e947425d91a15abb28bc50c15df149a651c24963c0467eab151e110b251` | committed at source HEAD |
| `backend/services/matching/__init__.py` | `2acc7e77a759e39577046f70838d497de8bc477010a82cbd4dd655da1f0f9656` | committed at source HEAD |
| `backend/services/matching/chunking.py` | `d159e88fa557db2452bdb364c975a8780fc5c4e9e9cbd1a1da119c6748943fd2` | committed at source HEAD |
| `backend/services/matching/extraction.py` | `a574705944089ab2d42d062d77dc93c7d8ae38be40f5e27670a3f515f70a40cf` | committed at source HEAD |
| `backend/services/matching/models.py` | `2ce2a0fef59ab78b76c9ecdc7cc1b4919ce8ba52b76a6d68d2a2bcb7a87c86f6` | committed at source HEAD |
| `backend/services/matching/normalization.py` | `75ec2ed77a76720347ee5e0cefc6794b5e84685262b50337dc04b649e8a73510` | committed at source HEAD |
| `backend/services/matching/pipeline.py` | `1cd1a9193ca35e3052992d1f8a6a3777e03d59eaaf69d403b91c2ddd962591e5` | committed at source HEAD |
| `backend/services/matching/scoring.py` | `6c4aa84292f77b94ee726ba8fcee1204ccdefd94c3f6b43ee3d041d63beaf94d` | committed at source HEAD |
| `backend/services/pinned_transport.py` | `69c6511b8d4c8b627d26cf63a99c232a243256bb8c52e56a4935cfc76e1fa46c` | committed at source HEAD |
| `backend/services/resume_files.py` | `259bbcd656767334a85d409393dd3700c26a88a1181a0a908a3268fbdade6bbd` | committed at source HEAD |
| `backend/services/skill_matching.py` | `48f10c162a7b36a913c4f9ef17f71309d85d644b595695d8b055355a5a4225cf` | committed at source HEAD |
| `backend/storage.py` | `2401fb997234b7ab2f45e26a99555b5302eff1c17db6e1b68bb325859f1164aa` | committed at source HEAD |
| `docs/matching-evaluation.md` | `940093756f70a9f3755ba94be1a6679b6741ec0b18087d3d2ab46e45a55c2d1d` | committed at source HEAD |
| `frontend/src/App.jsx` | `1de436448486253fbb390782a639457ae47d95d391ee001eb92649518768c2c7` | committed at source HEAD |
| `frontend/src/api/client.js` | `a159cf6c153ff7e214fa3a27789a0b827e3a57a280306a10c0d262e61dda377b` | committed at source HEAD |
| `frontend/src/components/MatchEvidenceDetails.jsx` | `45cfaf2fe0145d46548ca595e46c2e3678b337b31fcd6c15affbceacb2590b22` | committed at source HEAD |
| `frontend/src/components/ResumeFitRanker.jsx` | `aad9b974c269b86a53e9e8a4f2918bbba259381058087dbfed97bd694648f07f` | committed at source HEAD |
| `frontend/src/components/ResumeLibrary.jsx` | `111c77554928c806620f1bd162e393f58611e5d8fc468a30c425d03f34a10dc0` | committed at source HEAD |
| `frontend/src/test/MatchEvidenceDetails.test.jsx` | `4b043843f73a0ece8adc75a5d9abb2afb8973062ed031766e55c0a1dcbc64bae` | committed at source HEAD |
| `frontend/src/test/ResumeFitRanker.test.jsx` | `477bce7dc2aa3464a4cfa32ea80abab1afc9256a6abf07c5380dd4e01ceed8b6` | committed at source HEAD |
| `scripts/evaluate_matching.py` | `9f53305b17f7019586b6e41351eb620ebafd241bcf3d86e078b817bd04a55a28` | committed at source HEAD |
| `tests/test_ai_engine.py` | `a07763714c20e2c5836d1a4700e89324c0879d524db95e5ab17bafb977fd780c` | committed at source HEAD |
| `tests/test_document_parser.py` | `5772dbab30d207ab0deeac3e19311176560584a43db5026a866049081cf5f892` | committed at source HEAD |
| `tests/test_match_api.py` | `ac0e18f78e272b665d592fa52d3a6cfd94f4d29a45466caaef6a1fe52bfed7e9` | committed at source HEAD |
| `tests/test_match_benchmark.py` | `a48df8fd8f0d38ace3a3ef0d0c46f9be58c721a6101e145d8f463cc413ed2b38` | committed at source HEAD |
| `tests/test_match_chunking.py` | `c26c58e8e6accfdc18e40bfaeb90e4a40a873938b4a059f044625ffedc0c1344` | committed at source HEAD |
| `tests/test_match_contracts.py` | `6a7ac61f61b35d481d859e0e06d36f4428ffca8d20cf1a7f54837581e4cacbca` | committed at source HEAD |
| `tests/test_match_extraction.py` | `755970208291ad7381a1fc6113498320c4517c6697fe00a5750ea6c299691755` | committed at source HEAD |
| `tests/test_match_normalization.py` | `0bc396ab35dda3699d8c088d3985d611b0bfe987f673e8149a9efe91ed55de87` | committed at source HEAD |
| `tests/test_match_pipeline.py` | `bc2e50aa8e6dc3f6e9409bb6d78c34cc04610dbf508669e5608da05aee66a0bf` | committed at source HEAD |
| `tests/test_match_ranking.py` | `13dd2335f5a0369baff52afdc08cd51530c51ece9832e689c487693915dfce29` | committed at source HEAD |
| `tests/test_match_scoring.py` | `0021c53b4a6116078944a2ae409b0f88105fe5a3a592a7559b81d5dd10e36bba` | committed at source HEAD |
| `tests/test_match_snapshots.py` | `ed8a28e24d3a5915c474dc9d358838f41ca8d781688c982101479ddaadb3232b` | committed at source HEAD |
| `tests/test_matching_metadata_claims.py` | `93dbe346219cd1cb6e3802a3280c8c7402831169a089a3729bad220c962e3f92` | committed at source HEAD |
| `tests/test_pinned_transport.py` | `ad513ef62f21c7a98305e064f7f1d658caa5124a14fd5a39a66f606daf6ad4f2` | committed at source HEAD |

## Baseline verification

Verified in the isolated destination before any application transfer:

- Backend: `D:/Grind/Projects/JobHelperGuru/.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider --basetemp=scratch/pytest-task1-verified` — 211 passed; one existing Starlette/AnyIO deprecation warning.
- Frontend dependencies: `npm ci --no-audit --no-fund` — installed from lockfile. npm reported an uncovered esbuild install-script approval entry; the build nevertheless succeeded without granting extra script approval.
- Frontend: `npm run test:run` — 67 tests passed across 17 files.
- Frontend: `npm run build` — production build passed, 1,593 modules transformed.
- Initial backend setup attempt had 211 setup errors because the fresh checkout lacked parent `scratch/`; creating that ignored directory resolved it. No application fix was made.
- Rechecked all 40 source hashes after tests: unchanged. Source branch remains clean at the pinned source commit.
- Destination implementation files remain identical to the fetched main base; this task adds planning records only.
- Full test logs and source patch/hash JSON are kept in the ignored task workspace. No live AI requests made.

## Subsequent execution

Tasks 1–4, including 4A, are complete. Task 5 and later tasks remain pending per the owner's task-by-task scope. The profile task executes as 4A before Task 4. No push, PR, deployment, or source-branch merge was performed.

## Task 2 transfer and verification

- Borrowed pinned-source normalization, chunking, skill aliases, warning-aware document parser, and selected matching contracts. Adapted contracts to overall job fit; no offline imports, role bonus fields, scorer, pipeline, or provider requests were transferred.
- Added typed requirement kinds, known reason codes, nullable skill coverage, rubric identity required for complete results, no scores/ranks on incomplete results, shared job/rubric/coverage batch checks, and half-up display consistency. Top status uses positive raw score, not rounded percentage.
- Kept the legacy string-only parser wrapper for existing callers. Upload reparses the file even when preview text is resubmitted as content_override so unreadable-page warnings cannot disappear.
- Added additive warning migrations/JSON persistence and hydration through reserve/upload, Resume responses, individual reads and vault list. SQLite legacy schema upgrade was executed; PostgreSQL SQL/JSON/tenant-filter behavior was checked with recording mocks, not a live PostgreSQL instance.
- RED: 14 initial focused checks failed for missing functionality; a further raw-score-leading edge check failed before its correction.
- GREEN: 37 focused tests passed; full backend suite 229 passed with the existing Starlette/AnyIO warning. No frontend implementation changes; Task 1 frontend baseline remains the latest frontend test/build run.
- Original source files rehashed after Task 2: all 40 unchanged. Future evaluator warning gating belongs to Tasks 4A/6, which are not implemented yet.

## Task 3 transfer and verification

- Built a lean AI-only JD adapter rather than copying the source branch's offline taxonomy, candidate classification choices or evidence pipeline. Adapted its whitespace-only quote location and explicit minimum-tenure helpers, alongside the Task 2 canonicalization/chunking contracts.
- Processes every 8,000-character chunk with 400-character overlap and carries the preceding section heading. Requires explicit complete chunk acknowledgment and a strict proposal schema. Derives exact source offsets and stable IDs from source hash, extractor version and accepted identity; no provider offsets, IDs, scores or weights accepted.
- Deduplicates overlap and equivalent aliases, retains required interpretations over equivalent preferred requirements, rejects other category conflicts, and preserves distinct tenure thresholds. Checks explicit literal OR groups against the source, including omitted alternatives. Semantic qualifications do not require lexical overlap or taxonomy membership.
- Keeps all proposals in an over-64 rubric as unresolved needs_review; does not shorten the rubric. Empty rubrics and expired deadlines cannot become complete. Provider failures expose only sanitized reason codes; source-size violations remain caller errors.
- RED: 18 initial failures, then 3 section/group/non-fit failures and 1 partial-OR failure were observed before corresponding corrections. GREEN: 41 focused tests and 253 full backend tests pass, with the existing Starlette/AnyIO deprecation warning.
- Guarded request tests verify full payload, schema, temperature 0 and remaining timeout through the existing configured-provider transport. No live provider calls, frontend changes or deployment occurred. Actual semantic extraction quality still requires Task 9's authorized measurements; persisted rubric freezing belongs to Task 6.
- All 40 pinned source hashes remain unchanged and the source checkout remains clean. Task 4A is the next task; later plan checkboxes remain unchecked.

## Tasks 4A and 4 transfer and verification

- Built lean reusable profile contracts/extractor/storage and batched evidence assessment. Reused the existing guarded provider client, chunking and canonicalization; moved the validated quote helper into shared provenance and adapted pinned-source month/date and source-level learning rules. No offline pipeline, taxonomy selection gate, embeddings, role bonus or scoring code imported.
- Complete profiles retain job-independent skills, activities, credentials, dated employment, exact saved-source spans and all processed chunks. Complete profiles only are saved; tenant/source/provider/version identity excludes secrets, jobs and scorers. Cache loads revalidate source coverage, facts and fingerprint; concurrent inserts read the first accepted winner. SQLite CRUD/concurrency and PostgreSQL schema/locking/parameter/JSON behavior were verified (PostgreSQL recording mocks, no live server).
- Profile preparation failures preserve saved resumes. Rename reuses profile; content edits and deletion remove derived rows in the same transaction. Preparation/cache read checks current source before publishing. Fixed an existing concurrent rename race that could restore stale content by reading authoritative name/content under the update transaction/row lock.
- Assessment carries one rubric and explicit per-resume requirement/chunk IDs. All source-backed positive proposals validate before coverage reconciliation. Omitted observations remain unresolved, not zero or fabricated 50. Duplicate/foreign IDs, unsupported quotes, response scores, and conflicts fail closed. Semantic paraphrases need no JD keyword overlap.
- Skills-list/bare mentions are listed; learning and negation cannot earn demonstrated credit. Relevant tenure uses verified work dates; education/projects/future work and cross-section quotes cannot supply intervals. Ongoing work remains job-independent in the profile and is capped at assessment as_of.
- All profile activities remain available for semantic matching. Literal misses inspect original text; unsupported profile absences escalate to full source chunks. Overlap positives survive absence in another chunk; conflicting classification of the same span is rejected. Five prepared semantic resumes were assessed in one mock call; this is functional call-count evidence, not measured live latency/quality.
- RED: missing profile/evidence APIs, stale cached-read/rename races, bare-list/cross-section overcredit and conflicting overlap classifications were reproduced before correction. One overlap fixture was corrected from 7,984 to 8,684 chars, then its defect was re-observed against original aggregation before restoring the fix.
- GREEN: 87 focused tests and 293 full backend tests passed, with the existing Starlette/AnyIO deprecation warning. Source hashes unchanged. No live AI requests, frontend changes, push or deployment occurred.
- Combined 4A/4 commit keeps the consumer fallback and shared provenance fixes together. Task 5 is next; endpoint/vault preparation/UI activation and authorized provider quality/performance gates remain later tasks.
