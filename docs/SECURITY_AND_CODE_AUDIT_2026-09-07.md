# JobHelperGuru security, bugs, and cleanup audit

Reviewed commit: `14a58fbe45b18eb53b78ab9a8689323d75e082b4` (`main`). Review started September 6 and completed September 7, 2026.

**Several high-priority security defects are confirmed. Fix authorization, file ownership, outbound request validation, account linking, and account-switch state before expanding public use.** This report does not establish that anyone has exploited the live application.

## Scope and evidence

- Reviewed backend routes, authentication, persistence, document/object storage, scraping, AI processing, exports, frontend state and workflows, tests, dependency manifests, and deployment files.
- Ran **16 backend/security reproduction probes and 2 frontend handler/state probes**. All 18 reproduced the described behavior. Some probes cover different paths of the same finding. They use actual application code, synthetic accounts/files, a fresh SQLite database, mocked Google responses, and intercepted outbound HTTP. No exploit requests were sent to the live website or real internal services.
- Ran the existing suite in an isolated environment: **64 passed, 2 deselected**. The excluded tests were the live Indeed test and the incompletely mocked Greenhouse scraping test. An initial harness run failed because its network block also blocked Windows' event-loop sockets and pytest selected an inaccessible temporary directory; those harness issues were corrected before obtaining the 64-pass result.
- Frontend production build succeeded, with output placed in the ignored audit scratch directory.
- Ruff reported **10 unused Python imports and 3 unused variable bindings**. Frontend Babel scope analysis found redundant default React imports and an unused `appliedCount` calculation; repository reference searches identified two unused frontend API helpers.
- Queried npm advisories against the frontend lockfile. Audited a freshly resolved Python environment, since there is no Python lockfile. The deployed Python package versions were not inspected.
- A heuristic scan of currently tracked files found example/test credential patterns, but no additional convincing live credential literals. `.env` is untracked and no `.env` file appeared in the local Git history path check. This is not an exhaustive historical secret scan.
- No application source, existing tests, dependencies, or production data were changed. Audit scripts and their isolated environment are in the ignored `scratch/security-audit-20260906/` directory. This report is a new local file.

## Security findings

### S1 - High: authenticated users can read and modify another user's application

**Confirmed locally.** [Application PATCH endpoint](D:/Grind/Projects/JobHelperGuru/backend/main.py:401) authenticates a user but calls [the storage update](D:/Grind/Projects/JobHelperGuru/backend/storage.py:623) without ownership information. SQL filters only by application ID. An empty PATCH returns the complete existing application, so this is both a confidentiality and integrity issue.

The probe created two users. User A read User B's private notes with an empty PATCH, then changed them; both requests returned 200. Exploitation requires knowing the victim's application UUID; this review did not establish a public UUID enumeration path.

**Fix:** require `user_id` in the update service, scope both UPDATE and returned SELECT by owner, and return 404 for non-owned IDs. Add two-user tests for empty and non-empty PATCH, not just list/delete isolation.

### S2 - High: client-selected resume file keys bypass object ownership and permit local file deletion

**Confirmed locally.** [Resume creation](D:/Grind/Projects/JobHelperGuru/backend/main.py:205) accepts a client-provided `file_key`. Listing generates signed downloads for that key; deleting the caller's resume deletes the referenced binary without checking whether that binary belongs to the caller. [Local deletion](D:/Grind/Projects/JobHelperGuru/backend/services/object_storage.py:161) also joins an unvalidated key onto `data/uploads`.

One probe attached another synthetic user's uploaded key to an attacker-owned resume and deleted the victim's binary. Another attached an absolute path to a disposable file outside `data/uploads` and successfully deleted it. With R2, a known foreign object key can be signed or deleted; arbitrary filesystem deletion applies when local storage is used or the R2 delete falls back to disk. Filesystem permissions still constrain accessible targets.

**Fix:** stop accepting arbitrary file keys in public resume creation. Bind uploaded objects to their authenticated owner server-side; validate ownership before signing or deletion. Resolve local paths and enforce containment within that user's upload directory. Do not use basename fallback as an authorization mechanism.

### S3 - High: unauthenticated AI connection testing permits requests to private addresses

**Confirmed with intercepted HTTP.** [The connection-test endpoint](D:/Grind/Projects/JobHelperGuru/backend/main.py:440) has no authentication dependency and accepts an arbitrary provider base URL. [Client construction](D:/Grind/Projects/JobHelperGuru/backend/services/ai_engine.py:83) forwards it to the OpenAI client.

A request without a login and with a fake API key attempted an HTTP POST to a loopback address and returned the mocked response. The request has the SDK's path/body shape, so this is not an arbitrary-method proxy, but it can reach otherwise private services and consume outbound request capacity.

**Fix:** authenticate connection tests, validate provider destinations, and enforce outbound network restrictions in cloud mode. Preserve local Ollama support through an explicit local-deployment policy rather than allowing private addresses on the public service. Reject insecure credential transport where inappropriate and apply request limits.

### S4 - High: the scraper's private-address protection is bypassed after the first URL

**Confirmed with intercepted HTTP.** [Initial URL validation](D:/Grind/Projects/JobHelperGuru/backend/services/scraper.py:70) is not repeated for redirected destinations. The standard request follows redirects. [Embedded iframe fetching](D:/Grind/Projects/JobHelperGuru/backend/services/scraper.py:327) checks whether a known ATS name occurs anywhere in a URL rather than validating its hostname and resolved address.

Probes confirmed a public-to-loopback redirect and an iframe pointing to loopback with an ATS name only in its query string. Both reached the mocked private destination. Job analysis accepts anonymous requests.

**Fix:** validate each redirect and embedded destination, parse and compare hostnames, cap redirects, and use transport/network-level protections against DNS resolution races. Apply the same policy to every fetch path, including browser-impersonation requests.

### S5 - High: Google sign-in can inherit an attacker-created email/password account

**Confirmed using mocked Google verification.** [Registration](D:/Grind/Projects/JobHelperGuru/backend/routers/auth.py:86) does not verify ownership of an email. [Google sign-in](D:/Grind/Projects/JobHelperGuru/backend/routers/auth.py:170) automatically finds an existing account by email and retains its password login. It does not bind identity to Google's `sub`, and it ignores `email_verified`.

The probe registered a future user's email with an attacker-known password, then simulated that email owner's valid Google login. Both signed into the same account, and the original password remained usable. A separate probe confirmed that `email_verified=false` is accepted. This verifies application logic, not the ability to forge Google's signed tokens.

**Fix:** verify email ownership before enabling password accounts, bind Google identities by issuer/subject, and require a secure account-linking flow. Check email authority appropriately. Google also recommends a production token-verification library; the current `tokeninfo` dependency is intended for debugging and can be throttled. [Google backend authentication guidance](https://developers.google.com/identity/sign-in/web/backend-auth).

### S6 - High: previous-account resume content survives logout and account switching

**Confirmed with the actual App component in a synthetic hook harness.** [Logout and unauthorized handlers](D:/Grind/Projects/JobHelperGuru/frontend/src/App.jsx:134) clear some state but retain `selectedResumeForJob`, modal state, and other account-dependent state. [Initial loading](D:/Grind/Projects/JobHelperGuru/frontend/src/App.jsx:125) only replaces the selected resume when the new account has at least one resume.

After User A logged out and User B logged in with no resumes, both optimizer and outreach still received User A's selected resume. Their request builders send that content as evidence, so subsequent actions can disclose it to the new account's AI provider. This scenario requires an account switch in the same running page; it is not remote access to another browser session.

**Fix:** reset all account-bound state and close/remount modals on logout, expiry, and identity changes. Set the selected resume to `resumesData[0] ?? null`. Cancel or ignore outstanding requests belonging to the previous identity.

### S7 - Medium: exported job data becomes executable spreadsheet formulas

**Confirmed locally.** [Excel cell creation](D:/Grind/Projects/JobHelperGuru/backend/services/excel_exporter.py:91) assigns untrusted company, role, notes, and other values directly to cells. Harmless `=1+1` values became formula cells in the exported workbook. Job text can originate from third-party pages; S1 also permits another account to alter those values if it knows an application ID.

**Fix:** explicitly encode untrusted values as text in both worksheets and validate hyperlink schemes. Only deliberate, application-owned formulas should use formula cell types. Actual formula execution capabilities depend on the spreadsheet application and its protections; this is not a demonstrated remote-code-execution finding.

### S8 - High if secrets are omitted: public default signing/encryption secrets remain usable

**Code-confirmed, deployment configuration not checked.** [JWT initialization](D:/Grind/Projects/JobHelperGuru/backend/services/auth_service.py:7) has a hardcoded fallback and refuses it only when `ENVIRONMENT` is exactly `production`. The [Render blueprint](D:/Grind/Projects/JobHelperGuru/render.yaml:1) and Dockerfile do not set that flag. [Settings encryption](D:/Grind/Projects/JobHelperGuru/backend/services/encryption.py:12) silently uses a public fallback if neither encryption secret is supplied.

A correctly configured deployment avoids this condition. If deployed without the relevant secrets, JWTs can be forged for known user IDs and encrypted settings lack meaningful protection against someone who obtains the database.

**Fix:** fail startup on absent/weak secrets in deployed environments, require explicit development mode for development defaults, and validate required configuration. Do not silently treat a failed decryption as valid plaintext for modern encrypted records; use a versioned legacy migration.

### S9 - Medium: plaintext API keys persist in browser storage after logout

**Code-confirmed.** [Saved profiles](D:/Grind/Projects/JobHelperGuru/frontend/src/components/SettingsModal.jsx:313) write complete API keys to localStorage. [Logout cleanup](D:/Grind/Projects/JobHelperGuru/frontend/src/api/client.js:12) removes only the JWT and user record. Per-user localStorage key names do not provide access isolation within the same origin/browser profile. Settings responses also return plaintext keys.

This increases exposure on shared browser profiles and if same-origin script execution is compromised. No standalone XSS exploit was established in this review.

**Fix:** keep provider secrets on the backend, return masked profile metadata, activate profiles by ID, and remove legacy plaintext browser copies. Consider HttpOnly session cookies with corresponding CSRF protections if changing session storage.

### S10 - Medium: public and expensive operations lack application-level abuse limits

**Code-confirmed; no load attack performed.** Register/login, anonymous scraping/analysis, and AI testing have no rate limiter in the application. Most [request models](D:/Grind/Projects/JobHelperGuru/backend/models.py:35) do not bound string lengths, list counts, or stored resume counts. The 10 MB upload check does not bound decompressed DOCX/PDF processing or all JSON/text ingestion paths.

**Fix:** add per-IP and per-user limits, payload and storage quotas, bounded document extraction, and request/concurrency budgets. Verify any provider-side protections rather than assuming the repository implements them.

## Dependency and test risks

### D1 - Upgrade the development toolchain; distinguish it from the production server

The lockfile resolves **Vite 5.4.21** and **esbuild 0.21.5**. npm reported **two affected packages: one high, one moderate**, covering multiple advisories. Vite includes a Windows file-deny bypass, relevant when its development server is exposed to the network. The current Vite config does not explicitly expose it, and the Docker runtime serves built assets with FastAPI rather than running Vite.

See [Vite's Windows advisory](https://github.com/vitejs/vite/security/advisories/GHSA-fx2h-pf6j-xcff), [optimized-dependency map traversal](https://github.com/advisories/GHSA-4w7w-66w2-5vf9), [Windows editor-path advisory](https://github.com/advisories/GHSA-v6wh-96g9-6wx3), and [esbuild's development-server advisory](https://github.com/evanw/esbuild/security/advisories/GHSA-67mh-4wv8-2f99). Select a maintained compatible toolchain and recheck all advisories; do not apply a forced major upgrade blindly.

The fresh Python resolution had no reported vulnerabilities in the application packages. The audit environment's bundled **pip 25.0.1** had seven advisory entries, including a duplicate identifier; these are tooling findings, not evidence of seven production application vulnerabilities. Python dependencies use open-ended minimums rather than a lockfile, so the installed deployment can differ. Record and audit a reproducible production dependency set.

### D2 - High development-data risk: the normal test command is not fully isolated

[The shared fixture](D:/Grind/Projects/JobHelperGuru/tests/conftest.py:1) clears only `DATABASE_URL`. Importing `backend.main` still initializes the default local `data/tracker.db`, loads environment configuration, and creates the object-storage client. API upload tests can therefore use configured R2 credentials, while other tests can write to the user's normal SQLite database. Startup also invokes automatic deduplication.

**Fix:** set a fresh per-run/per-test database before application import, disable `.env` loading for tests, replace R2/AI/network clients with test doubles, and make app creation/services injectable. Separate live integration tests from deterministic tests. This audit supplied those isolation controls externally.

## Functional bugs

| ID / priority | Evidence and trigger | Recommended correction |
|---|---|---|
| **B1 / High: distinct postings collapse into one application** | **Reproduced:** [deduplication](D:/Grind/Projects/JobHelperGuru/backend/storage.py:415) merges jobs with the same company/title even when their URLs and locations differ. The second posting overwrote the first. [Startup cleanup](D:/Grind/Projects/JobHelperGuru/backend/storage.py:474) can also delete distinct rows by company/title. | Use a canonical posting identifier; use title/company fallback only when a reliable posting ID is absent. Replace destructive startup deduplication with an explicit reviewed migration. |
| **B2 / Medium: editing extracted resume text has no effect on save** | **Reproduced with actual handlers:** [save](D:/Grind/Projects/JobHelperGuru/frontend/src/components/ResumeLibrary.jsx:81) uploads the original file and title whenever a file is selected, ignoring the editable `newContent`. | Save the edited text explicitly, while distinguishing it from the original document binary. |
| **B3 / Medium: Markdown is offered but rejected in Add Resume** | **Reproduced API rejection:** [the UI](D:/Grind/Projects/JobHelperGuru/frontend/src/components/ResumeLibrary.jsx:124) reads `.md`, retains it as `selectedFile`, then uploads it to an endpoint whose [allowlist](D:/Grind/Projects/JobHelperGuru/backend/main.py:208) excludes `.md`. Quick Upload takes a different text route. | Align the two upload paths and backend format allowlist. |
| **B4 / Medium: nullable application updates can break the entire list** | **Reproduced:** `required_skills: null` is accepted, committed as JSON null, and then fails response validation. Both PATCH and subsequent listing return 500. See [update](D:/Grind/Projects/JobHelperGuru/backend/storage.py:623) and [deserialization](D:/Grind/Projects/JobHelperGuru/backend/storage.py:661). Other nullable fields also need validation. | Reject null for non-null collections or normalize it consistently before committing. Validate persisted output inside the transaction. |
| **B5 / Medium: exact C++, C#, and .NET matches score as missing** | **Reproduced:** a resume containing all three scored 0 for those required skills. [Word-boundary regexes](D:/Grind/Projects/JobHelperGuru/backend/services/heuristic_parser.py:278) are unsuitable for tokens beginning/ending in punctuation. The same pattern affects extraction and evidence checking. | Use appropriate token boundaries and aliases, with punctuation-specific tests. |
| **B6 / Medium: offline analysis discards known company/location** | **Reproduced:** [the heuristic](D:/Grind/Projects/JobHelperGuru/backend/services/heuristic_parser.py:250) returns `Detected Company` / `Identified Location`; [the merge](D:/Grind/Projects/JobHelperGuru/backend/main.py:162) does not recognize these placeholders and therefore ignores correctly scraped metadata. | Use missing values consistently or explicitly prefer reliable scraped fields over placeholders. |
| **B7 / Medium: claim-aware generation still fabricates or overstates evidence** | **Reproduced:** [offline Candidate C](D:/Grind/Projects/JobHelperGuru/backend/services/ai_engine.py:536) adds `99.9%` reliability without evidence. Other templates assert achievements based only on keyword presence; offline outreach claims job-required skills even for an empty resume. [Online alternatives](D:/Grind/Projects/JobHelperGuru/backend/services/ai_engine.py:497) accept model-provided verification flags rather than enforcing the server's decision per alternative. | Remove invented metrics/achievements, distinguish keyword presence from evidence, and enforce confirmation flags and output checks after generation. |
| **B8 / Medium: deleting the active key does not deactivate it** | **Code-confirmed:** [key deletion](D:/Grind/Projects/JobHelperGuru/frontend/src/components/SettingsModal.jsx:224) updates only `saved_keys`; backend `api_key`, model, and online mode remain active. Reopening settings can recreate a profile from the active key. | Atomically delete/deactivate a profile or select another active profile; update the backend active fields too. |
| **B9 / Medium: uploaded files can appear saved but be undownloadable** | **Code-confirmed:** [R2 upload failure](D:/Grind/Projects/JobHelperGuru/backend/services/object_storage.py:98) silently falls back to local disk, but download URL generation still signs an R2 object that was never uploaded. Pure local mode returns no download URL and has no authenticated download route. | Track the actual storage location, serve local downloads through an owned-resource endpoint, and avoid silent ephemeral-disk fallback in cloud deployments. |
| **B10 / Medium: long passwords produce server errors** | **Reproduced with bcrypt 5.0.0:** a 73-byte password passes [registration validation](D:/Grind/Projects/JobHelperGuru/backend/routers/auth.py:93), then hashing returns 500. Older dependency resolutions may truncate instead. | Validate the password's encoded byte length or use a password-hashing scheme supporting the intended length; lock the tested dependency behavior. |
| **B11 / Medium: the SQLite migration does not preserve tenant data** | **Code-confirmed; only applies when enabled:** [migration](D:/Grind/Projects/JobHelperGuru/backend/storage.py:745) does not migrate users/user settings, loses resume ownership/file keys, and recreates applications with new IDs and no owner. Authenticated users cannot see those migrated rows normally. | Replace it with an explicit tenant-aware migration preserving identities, relationships, ownership, and file locations; do not run it as-is on real tenant data. |
| **B12 / Low: dashboard totals remain stale after tracker edits** | **Code-confirmed:** [the tracker](D:/Grind/Projects/JobHelperGuru/frontend/src/components/ApplicationsTracker.jsx:50) maintains its own application array, while [App](D:/Grind/Projects/JobHelperGuru/frontend/src/App.jsx:473) receives no change callback. Status changes and deletes do not update header/profile counts or analyzer duplicate state until reload. | Use one shared source of application state or report mutations to the parent. |
| **B13 / Low: dates and follow-up defaults do not behave consistently** | **Code-confirmed:** [reminders](D:/Grind/Projects/JobHelperGuru/frontend/src/components/FollowUpBanner.jsx:5) use UTC calendar dates, which can be tomorrow during a Toronto evening. `default_follow_up_days` is stored but never used to set dates; changing status to Applied only changes status. | Use the user's local date for reminders and implement or remove the unused default-days setting. |
| **B14 / Medium: new-grad eligibility ignores the employer's actual window** | **Code-confirmed:** [eligibility](D:/Grind/Projects/JobHelperGuru/backend/services/heuristic_parser.py:97) always applies a fixed four-month-before/six-month-after window; [AI parsing](D:/Grind/Projects/JobHelperGuru/backend/services/ai_engine.py:135) also substitutes that fixed criterion. | Extract the stated employer window and assess against it; report uncertainty when none is specified instead of presenting a definitive eligibility decision. |
| **B15 / Low: archived jobs disappear in Kanban** | **Code-confirmed:** [Kanban columns](D:/Grind/Projects/JobHelperGuru/frontend/src/components/KanbanBoard.jsx:4) omit Archived even though the tracker offers an Archived filter. Selecting that filter in Kanban yields no cards. | Include an Archived column or provide an explicit archived view. |

Additional bounded validation improvements: `existing_bullet=null` reaches an unconditional `.lower()` before the guarded assignment in the optimizer; null settings fields can persist values that later fail parsing; `.rtf` currently goes through raw text decoding instead of RTF extraction. These belong in the same input/format-validation work rather than a broad refactor.

## Cleanup candidates

### Safe code cleanup based on current repository references

| Candidate | Evidence / condition |
|---|---|
| [Frontend `fetchHealth`](D:/Grind/Projects/JobHelperGuru/frontend/src/api/client.js:67) | Exported helper has no caller in the repository. Keep the backend health endpoints: Render uses them. |
| [Deprecated `getExcelExportUrl`](D:/Grind/Projects/JobHelperGuru/frontend/src/api/client.js:300) | No callers; the authenticated `downloadExcelReport` replaced it. |
| Redundant default `React` imports in `App.jsx` and component files | Automatic JSX runtime is enabled; scope analysis found the default binding unused. Preserve named hook imports and the actually used React import in `main.jsx`. |
| [Unused `appliedCount` in ApplicationsTracker](D:/Grind/Projects/JobHelperGuru/frontend/src/components/ApplicationsTracker.jsx:98) | Calculated but not rendered or otherwise referenced. App's separate displayed counter is still used. |
| Ten unused Python imports | `Dict`/`Any` in `main.py`; `Any` in `models.py`; `ResumeMatchResult` in `ai_engine.py`; `Optional` in `document_parser.py`; `Tuple` in `heuristic_parser.py`; local `html` in `_try_fetch_embedded_ats`; `ResumeCreate` in `storage.py`; `sys`/`subprocess` in `run.py`. Confirmed by Ruff. |
| Unused variable bindings | `success` in resume deletion, `locale` in Workday extraction, and caught `e` in the document parser. Preserve the deletion call and any other side effects when removing assignments. Unused catch parameter names in frontend code are also optional cleanup. |
| [Duplicate evidence assignments](D:/Grind/Projects/JobHelperGuru/backend/services/ai_engine.py:349) | The first `evidence_blob`/`existing_blob` assignments are overwritten before use. Removing the redundant unguarded `.lower()` also addresses the null-bullet failure. |
| Direct frontend dependency declarations: `clsx`, `autoprefixer`, `postcss` | No application/config usage found; Tailwind uses its Vite plugin. Remove unnecessary direct declarations and regenerate the lockfile. PostCSS may remain as Vite's transitive dependency; do not manually delete its package directory. |

### Files that can be consolidated or retired with a stated condition

- **Duplicate requirements files:** root and backend versions have identical SHA-256 hashes. Docker uses the root file and README uses the backend file. Consolidate to one source with an include or update every consumer before deleting either file.
- **`build.sh`:** unused by the checked-in Docker-based Render configuration. Retire it only if the alternate native build workflow is no longer supported.
- **Old scratch files:** `scratch/b64_design_md.txt`, `scratch/encode_design_md.py`, and `scratch/pr3_body.md` are ignored migration/PR artifacts with no application imports. Safe to remove for runtime purposes once their author confirms no unfinished work depends on them. The new audit scratch directory can likewise be removed after its evidence is no longer needed.
- **Caches:** `__pycache__` and `.pytest_cache` are regenerable. `frontend/dist` and `node_modules` are also regenerable but removing them disrupts the current local run until rebuilt/reinstalled.
- **Historical design/planning documents:** not runtime dependencies, but useful project history. Archive rather than deleting solely because code does not import them.

**No entire active application class or React component was proven unused.** Keep package `__init__.py` files. `ObjectStorageService.get_file` is currently exercised by tests and is a reasonable building block for the missing local-download fix; it is not an unconditional deletion candidate. The migration function is wired to an environment flag, so it is defective/legacy rather than dead code. `Bulletskill.md` is documentation, not dynamically loaded at runtime; keep or revise it as the framework's source document.

Do not treat `.env`, SQLite databases, or `data/uploads` as redundant files: they may contain real credentials or user data.

## Suggested order of work

1. Fix S1-S6 with ownership, request-destination, identity-linking, and account-switch regression coverage. Ensure no local/cloud file operation trusts client-provided paths.
2. Enforce deployment secrets, isolate the test suite, and address spreadsheet injection, browser key persistence, and abuse limits.
3. Fix data-loss and correctness bugs first: B1-B9, then migration and remaining validation/date/UI issues. Add tests at the failing route or handler rather than only testing helper functions.
4. Upgrade/audit a reproducible dependency set, then perform the small verified cleanup. Avoid combining security fixes with large unrelated refactors.

The passing baseline and build are useful checks, but they do not invalidate the additional security and correctness reproductions above.
