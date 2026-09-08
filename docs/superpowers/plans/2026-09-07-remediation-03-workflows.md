# Workflow and Output Correctness Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` task-by-task. Track steps with checkboxes.

**Goal:** Repair resume saving, analysis and claim accuracy, spreadsheet output, and application tracking behavior.

**Architecture:** Extend the existing components and services with explicit data contracts, shared token/date helpers, and a single application-state owner. Original document bytes remain distinguishable from edited text; generated claims are treated as drafts rather than independently verified achievements.

**Tech Stack:** React component tests, FastAPI/Pydantic, pytest, document parsers, openpyxl.

**Spec:** [Audit](D:/Grind/Projects/JobHelperGuru/docs/SECURITY_AND_CODE_AUDIT_2026-09-07.md); [roadmap constraints](D:/Grind/Projects/JobHelperGuru/docs/superpowers/plans/2026-09-07-audit-remediation.md). Requires owned files from 01 and frontend isolation/test infrastructure from 02.

## Task 1 — Persist edited resume text and align upload formats (B2, B3, RTF)

**Files:** `ResumeLibrary.jsx`, API client, `backend/main.py`, `backend/models.py`, `document_parser.py`, API/document parser tests, `ResumeLibrary.test.jsx`.

**Interface:** authenticated upload accepts `file`, `name`, and optional `content_override`; omission means use extracted text, present text means use the validated user edit. It returns one owned resume whose `content` is the actual text used for ranking and whose original binary is unchanged.

- [ ] Add failing handler/API tests: parse a file, edit text, save, reload, then match. The stored and matched text must equal the edited text. Test a failure between upload and DB persistence using the object cleanup behavior from 01.
- [ ] Send the edited text with file uploads and validate its non-empty/size constraints. Label download as “Original uploaded file”; editing extracted text does not claim to regenerate the PDF. Manual text entries remain supported.
- [ ] Share supported extensions between UI/API contract tests: `.pdf`, `.docx`, `.txt`, `.md`, `.rtf`, and `.doc` only to the extent the existing legacy extraction produces valid text. Parse Markdown as text and RTF with a real bounded parser; reject malformed/unsupported legacy Word documents with a clear conversion message rather than saving binary gibberish. Any added parser is pinned/audited in 04.
- [ ] Use the same validated path for Quick Upload and Add Resume. Do not allow async completion of an older file parse to overwrite a newer selection or the user's title/text edits; cancel/ignore stale parsing results.
- [ ] Run `python -m pytest tests/test_document_parser.py tests/test_api.py -q` and ResumeLibrary component tests. Commit as `Preserve resume text edits across upload workflows`.

## Task 2 — Correct keyword matching, metadata and evidence claims (B5, B6, B7, B14)

**Files:** `heuristic_parser.py`, `ai_engine.py`, `models.py`, `main.py`, `ResumeFitRanker.jsx`, `BulletOptimizerModal.jsx`, `CoverLetterModal.jsx`, existing AI/heuristic tests. Add `backend/services/skill_matching.py` and its tests for shared skill matching only.

**Interfaces:** `contains_skill(text: str, skill: str) -> bool` handles punctuation-aware boundaries and explicit aliases. Graduation assessment consumes the extracted employer window, not a fixed global rule, and returns `eligible`, `ineligible`, or `unknown` with a reason. The UI must display unknown separately from ineligible.

- [ ] Start with this regression and negative near-matches:

```python
def test_punctuation_skills_match_exact_resume():
    job = JobAnalysisResult(required_skills=['C++', 'C#', '.NET'])
    result = HeuristicParser().match_resume('Built with C++, C# and .NET.', job)
    assert result.match_score == 100
    assert result.missing_keywords == []
```

- [ ] Implement shared boundaries, for example `(?<![\w+#])` and `(?![\w+#])` around escaped skill tokens, with explicit tests for C/C++, C#/C, .NET, Node.js, Java/JavaScript and SQL/NoSQL. Validate the exact boundary behavior rather than assuming one regex fits every alias. Use stable sorting before slicing sets/lists so offline scores and keyword order are deterministic.
- [ ] Represent unavailable company/location as missing or a shared unknown sentinel. Merge reliable scraped metadata over unknown placeholders consistently. Test mocked scraped company/location survives both AI and heuristic paths.
- [ ] Remove invented `99.9%` and other template accomplishments. When no evidence supports a claim, generate a suggested draft with explicit confirmation required; an empty resume cannot produce affirmative experience claims in outreach. Keyword presence alone is not verified achievement evidence. Keep three alternatives but use placeholders for unsupported metrics.
- [ ] Enforce each alternative's claim/confirmation flags in server postprocessing; model output cannot downgrade an unverified claim. Check numeric claims against supplied evidence and require confirmation for unsupported/ambiguous quantities. Do not claim factual verification from automatic checks alone. Reject null `existing_bullet` or normalize it once before `.lower()`; remove duplicate assignments.
- [ ] Extract explicit employer graduation date ranges or relative windows into structured fields. Evaluate only with adequate candidate dates and employer criteria; otherwise return unknown. Do not overwrite actual employer criteria with the old four/six-month heuristic. Test dates at boundaries and absent/ambiguous dates.
- [ ] Run `python -m pytest tests/test_heuristic_parser.py tests/test_ai_engine.py tests/test_api.py -q` and ranker/optimizer/outreach component tests. Commit as `Correct matching metadata and evidence-aware drafts`.

## Task 3 — Export untrusted values as spreadsheet text (S7)

**Files:** `backend/services/excel_exporter.py`, `tests/test_excel_exporter.py`.

**Interface:** export still returns the existing two-sheet workbook. Only application-owned formulas, if any are deliberately added, may have formula cell type.

- [ ] Add a failing workbook test using harmless `=1+1` in company, title, location, notes, skills and keywords on both worksheets:

```python
def test_untrusted_company_is_exported_as_text():
    payload = ExcelExporter().export_workbook([
        Application(id='test', company='=1+1', role='Engineer')
    ])
    wb = openpyxl.load_workbook(io.BytesIO(payload), data_only=False)
    assert wb['Applications Tracker']['B2'].data_type == 's'
    assert wb['Applications Tracker']['B2'].value == '=1+1'
```

- [ ] Centralize text-cell assignment and explicitly force string data type for untrusted values. Strip unsupported XML control characters and bound values to Excel's cell limit with a documented visible truncation marker. Validate job hyperlinks as HTTP/HTTPS only; do not create `file:`, `javascript:`, or other executable links.
- [ ] Verify formulas remain inert after save/reopen, all styles/headers and valid hyperlinks remain, and empty exports still work. Open only benign synthetic output in the visual smoke check.
- [ ] Run `python -m pytest tests/test_excel_exporter.py tests/test_api.py -q`. Commit as `Export untrusted spreadsheet content as text`.

## Task 4 — Keep tracker state, local dates and archived views consistent (B12, B13, B15)

**Files:** `App.jsx`, `ApplicationsTracker.jsx`, `KanbanBoard.jsx`, `FollowUpBanner.jsx`, `JobAnalyzer.jsx`, API client, backend application update logic, associated tests. Add `frontend/src/utils/localDate.js` for shared date-only formatting.

**Interfaces:** App owns the application array. `ApplicationsTracker({applications, onApplicationsChanged})` reports successful authoritative records/deletions; parent counts and analyzer duplicate state derive from that array. `localDate(date = new Date())` returns local `YYYY-MM-DD` using year/month/day getters rather than UTC conversion.

- [ ] Add component regressions: update status and delete a record; header/profile/tracker counts and duplicate UI update immediately. Test failed updates do not show a false successful state.
- [ ] Remove the second independent tracker array and its unsynchronized initial fetch. Reuse the parent refresh path after create/edit/delete; use returned server data when it supplies dates or normalized values.
- [ ] On first transition to Applied, send the client's local calendar date. Backend validates it, sets `application_date` if empty and calculates `follow_up_date` using the user's configured default days only when no follow-up date is set. Repeated saves and later status transitions must not overwrite user-selected dates. API clients omitting the date use documented server UTC fallback rather than guessing a timezone.
- [ ] Use the same local-date helper and terminal-status exclusions for due banners and row coloring. Test Toronto near midnight/UTC rollover, DST boundaries, completed/rejected/archived jobs, and a manually cleared follow-up date.
- [ ] Include an Archived Kanban column or explicit archived pane selected by the same filter; the selected Archived view must actually display its records. Retain button-based status moves; drag-and-drop is outside remediation scope.
- [ ] Run tracker/date component tests and `python -m pytest tests/test_storage.py tests/test_api.py -q`. Commit as `Synchronize tracker state and follow-up dates`.
