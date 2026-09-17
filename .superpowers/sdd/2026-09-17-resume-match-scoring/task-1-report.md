# Task 1 report — v2 matching contracts and fixtures

## Implementation

- Added strict Pydantic contracts under `backend/services/matching/` for the four
  scored requirement categories, evidence levels, evaluation states, requirements,
  source-backed evidence, relevant date intervals, per-requirement results,
  evaluations, and evaluation batches.
- Validation rejects unknown categories, empty IDs, invalid source spans, missing
  provenance for credited or contradicted evidence, evidence assigned to the wrong
  requirement, duplicate requirement IDs in a scored evaluation, duplicate resume
  IDs in a batch, out-of-range scores, and scores or ranks on incomplete results.
- `not_evidenced` remains a valid zero-credit result without an invented resume
  quote, following the pre-flight ruling.
- Added immutable JSON fixtures for backend and frontend resume versions, aliases,
  explicit negation, missing resume text, OR/AND requirements, dated tenure, a
  skill after the previous 3,000-character boundary, and weighted arithmetic.
  `weighted_73.json` has complete source-backed requirements and evidence with
  80/60/50/100 category coverage, raw 72.5, and display score 73.

## Tests and results

- Focused contracts: `python -m pytest tests/test_match_contracts.py -q
  --basetemp .test-tmp-contracts` — **7 passed**.
- Lint: `ruff check backend/services/matching tests/test_match_contracts.py` —
  **all checks passed**.
- Full backend suite: `python -m pytest -q --disable-warnings --basetemp
  .test-tmp-full` — all collected backend tests completed successfully (the test
  runner emitted the complete 33%/66%/100% progress stream). The workspace has a
  pre-existing pytest-cache path warning; the suite also has a pre-existing
  Starlette anyio deprecation warning.

Pytest was given a workspace-local `--basetemp` because the sandbox account cannot
read the host-owned default `C:\\Users\\soura\\AppData\\Local\\Temp\\pytest-of-soura`
directory. This does not change application behavior.

## Exact TDD evidence

### RED 1

Command:

```text
.venv/Scripts/python.exe -m pytest tests/test_match_contracts.py -q
```

Observed result before production code existed:

```text
ModuleNotFoundError: No module named 'backend.services.matching'
```

### GREEN 1

After adding the minimum matching contract implementation and the weighted fixture:

```text
......                                                                   [100%]
6 passed, 2 warnings in 0.17s
```

### RED 2

After adding the fixture-coverage behavior test and before adding the remaining
fixtures:

```text
FAILED tests/test_match_contracts.py::test_immutable_fixture_set_covers_the_required_matching_regressions
Extra items in the left set: 'negation', 'dated_tenure', 'missing_data',
'or_and_requirements', 'backend_resume_version', ...
```

### GREEN 2

After adding the required immutable fixture set and correcting the late-document
offset:

```text
.......                                                                  [100%]
7 passed, 2 warnings in 0.23s
```

## Files changed

- `backend/services/matching/__init__.py`
- `backend/services/matching/models.py`
- `tests/test_match_contracts.py`
- `tests/fixtures/matching/aliases.json`
- `tests/fixtures/matching/backend_resume_version.json`
- `tests/fixtures/matching/dated_tenure.json`
- `tests/fixtures/matching/frontend_resume_version.json`
- `tests/fixtures/matching/late_document_skill.json`
- `tests/fixtures/matching/missing_data.json`
- `tests/fixtures/matching/negation.json`
- `tests/fixtures/matching/or_and_requirements.json`
- `tests/fixtures/matching/weighted_73.json`

## Self-review

- Checked that every non-zero or contradicted evidence item requires a complete
  quote/offset span, while a zero-credit `not_evidenced` item does not.
- Checked that source span widths equal quote lengths and all weighted-fixture
  spans resolve exactly into the job or resume text.
- Checked that incomplete evaluations cannot expose a synthetic percentage or
  rank and that all scored requirement IDs are unique.
- Ran whitespace validation with `git diff --check` and static validation with
  Ruff.

## Concerns

- Source-span validation here establishes structurally valid provenance. Task 3
  must still compare each quote and offsets against the complete source document
  before accepting extractor output.
- The existing `.pytest_cache` layout causes a non-failing pytest cache warning;
  it is unrelated to this task and was left unchanged.
