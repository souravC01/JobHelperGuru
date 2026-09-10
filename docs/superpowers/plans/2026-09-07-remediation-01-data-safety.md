# Data Safety and Ownership Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` task-by-task. Track steps with checkboxes.

**Goal:** Make tests safe to run, prevent cross-user data/file access, and stop accidental loss of application records.

**Architecture:** Keep the existing service structure, but make owner IDs mandatory for public-resource mutations. Add an explicit file-location/ownership record and a separate migration command; remove destructive work from application startup.

**Tech Stack:** FastAPI, Pydantic, pytest, SQLite/PostgreSQL, R2/local files.

**Spec:** [Audit](D:/Grind/Projects/JobHelperGuru/docs/SECURITY_AND_CODE_AUDIT_2026-09-07.md). Global constraints from the [roadmap](D:/Grind/Projects/JobHelperGuru/docs/superpowers/plans/2026-09-07-audit-remediation.md) apply.

## File boundaries

Modify `tests/conftest.py`, `backend/main.py`, `backend/models.py`, `backend/storage.py`, `backend/services/object_storage.py`, and the existing API/storage tests. Create focused tests `test_application_security.py`, `test_resume_file_security.py`, and `test_migration.py`. Create `backend/migrate.py` for explicit migration operations, never startup side effects.

## Task 1 - Make default tests unable to reach personal data or cloud services (D2)

**Interfaces:** produce a function-scoped `client` fixture and `two_users` fixture returning `(client, alpha_headers, beta_headers)`. They use a fresh database and fake object/AI clients. Existing helper tests may still instantiate their own temporary `StorageService`.

- [ ] Before any test module imports `backend.main`, suppress `.env` loading for this test process, set a new temporary `JOB_HELPER_DB`, blank database/R2 endpoints and credentials, and generate test-only JWT/encryption secrets. Do this at conftest collection time, not only in an autouse fixture that runs after imports.
- [ ] Per test, replace `main.storage` and the auth router's injected storage with a fresh SQLite service. Replace `main.object_storage`; set a temporary working/upload directory. Restore globals and close connections at teardown.
- [ ] Add a guard test with sentinel “personal database” and fake cloud URLs. Import/reset the app and perform upload/CRUD; assert the sentinel is byte-for-byte unchanged and external transports were never called. Block external transports rather than Windows loopback sockets needed by asyncio.
- [ ] Change the Indeed test to use a captured synthetic response. Mock DNS and the curl/standard transport in the Greenhouse test. Mark any future live integration test separately and exclude it by default.
- [ ] Add compatible pinned Vitest, React Testing Library and jsdom development dependencies, `test`/`test:run` scripts, and `frontend/src/test/setup.js`. Configure a synthetic DOM, mock fetch, and clear storage between tests. Add a passing render smoke test before other workstreams add component regressions; no browser test should contact the live app. Their final versions are re-audited in workstream 04.
- [ ] Run the existing suite twice. Both runs must be independent and leave the same sentinel unchanged. Commit as `Isolate test storage and external clients`.

Example fixture contract used by following tasks:

```python
@pytest.fixture
def two_users(client):
    def signup(email):
        response = client.post('/api/auth/register', json={
            'email': email, 'name': 'Test User', 'password': 'TestPassword123!'
        })
        assert response.status_code == 200
        return {'Authorization': 'Bearer ' + response.json()['token']}
    return client, signup('alpha@example.test'), signup('beta@example.test')
```

When verification is added in workstream 02, this fixture must create verified synthetic users through the test mail flow or storage fixture; it must not weaken production authentication.

## Task 2 - Enforce owner-scoped updates and reliable posting identity (S1, B1, B4)

**Files:** `backend/main.py`, `backend/storage.py`, `backend/models.py`, `tests/test_application_security.py`, `tests/test_storage.py`.

**Interfaces:** `StorageService.update_application(app_id: str, updates: ApplicationUpdate | dict, *, user_id: str) -> Application | None`. Every caller, including deduplication, supplies an owner. Add `canonical_posting_url(url: str) -> str | None` for shared storage identity decisions; frontend duplicate status should use the backend result instead of reimplementing fuzzy matching.

- [ ] Add and run this regression, expecting the current implementation to fail:

```python
def test_foreign_application_patch_is_not_found(two_users):
    client, alpha, beta = two_users
    owned = client.post('/api/applications', headers=beta,
                        json={'company': 'Acme', 'role': 'Engineer'}).json()
    for update in ({}, {'notes': 'changed'}):
        response = client.patch('/api/applications/' + owned['id'],
                                headers=alpha, json=update)
        assert response.status_code == 404
```

- [ ] Scope UPDATE and all return SELECTs by both `id` and `user_id`. Empty updates must also check ownership. Missing and foreign IDs have the same 404 response.
- [ ] Remove `create_user`'s automatic claim of all null-owner applications/resumes. Registering any account must leave unowned legacy records unchanged; only explicit migration mappings can assign them. Add a registration regression with synthetic unowned records.
- [ ] Remove `deduplicate_existing_applications()` from `_init_db`. Remove fuzzy company-prefix merging. Canonical URL identity must preserve posting IDs and meaningful query parameters; normalize only host casing, a trailing slash, and a documented set of tracking parameters. Different non-empty canonical URLs always create separate records, regardless of matching title/company/location.
- [ ] For manual text with no reliable posting ID, allow separate saves rather than silently merging by title/company. If needed, display a possible-duplicate warning while leaving the choice to the user. Add an owner-scoped unique index for non-empty canonical URLs only after a dry-run reports existing conflicts; do not delete conflicts automatically. Handle concurrent inserts by returning the existing owned posting.
- [ ] Reject explicit null for company, role, status, skill arrays, and keyword arrays with 422; omitted PATCH fields stay unchanged. Define empty-string clearing for notes/dates and null clearing only for nullable references. Validate before commit. Normalize already persisted JSON null arrays to `[]` through a targeted migration with counts.
- [ ] Tests: A/B owner matrix; no-ID/foreign-ID empty PATCH; same URL returns one record; different URLs survive restart; concurrent same-URL save; null update is 422 and listing stays 200; owner-separated identical URLs remain separate.
- [ ] Run `python -m pytest tests/test_application_security.py tests/test_storage.py tests/test_api.py -q`. Commit as `Enforce application ownership and posting identity`.

## Task 3 - Make file ownership and actual storage location authoritative (S2, B9)

**Files:** `backend/models.py`, `backend/storage.py`, `backend/main.py`, `backend/services/object_storage.py`, `frontend/src/api/client.js`, `frontend/src/components/ResumeLibrary.jsx`, `tests/test_resume_file_security.py`, `tests/test_object_storage.py`.

**Interfaces:** add a stored attachment record `{id, user_id, storage_backend, object_key, original_filename, content_type, size_bytes, deletion_state}` where deletion state is `active`, `pending`, or `failed`. Public resume creation accepts text/name only and forbids `file_key`/attachment IDs supplied by clients. Internal upload code attaches the newly stored object. `GET /api/resumes/{id}/download` authenticates and resolves ownership before reading or signing.

- [ ] Add failing tests for a foreign key, `../`, absolute Windows/POSIX paths, encoded traversal, and a symlink outside the upload root. Use only temporary sentinel files. Assert no foreign file is read, signed, overwritten, or deleted.
- [ ] Generate storage keys server-side under a validated user namespace using random identifiers. Store the original filename only as display/download metadata. Before local access, resolve the root and target and enforce containment, rejecting symlink escape. Do not retain basename fallback for authorization.
- [ ] Use the attachment record's owner and backend for every operation. In R2 mode, upload failure returns a controlled 503 and creates no successful resume row; do not write a fallback file to ephemeral disk. In local mode, serve an authenticated attachment response. For browser downloads, use the authenticated API client's blob download rather than an unauthenticated anchor to a protected URL.
- [ ] On DB failure after object upload, attempt cleanup and record a safe retryable orphan reference if cleanup fails. On deletion, do not return success while silently abandoning a failed file operation; use a recorded deletion state/retry path so either stage can be resumed without touching another owner.
- [ ] Migrate existing file references by joining them to their actual resume owner and resolving actual storage location. Preserve valid older keys through an explicit owner mapping. Report ambiguous/missing objects for repair; never guess an owner or make them public.
- [ ] Tests: owned local and R2 download/delete; foreign requests return 404; forged create fields rejected; R2 write failure creates no row; missing object gives controlled failure; malicious legacy paths quarantined; repeated delete cleanup remains scoped.
- [ ] Run `python -m pytest tests/test_resume_file_security.py tests/test_object_storage.py tests/test_api.py -q`. Commit as `Bind resume files to owners and storage backends`.

## Task 4 - Replace automatic legacy migration with a safe explicit command (B11)

**Files:** `backend/migrate.py`, `backend/storage.py`, `backend/main.py`, `tests/test_migration.py`, deployment guide.

**Interface:** `python -m backend.migrate --source <sqlite-path> --dry-run` emits record/conflict counts without secrets. `--apply` is mutually exclusive and requires a configured destination distinct from the source. Extend this command with the identity/profile migrations in workstream 02.

- [ ] Add a migration fixture containing two users, their settings/resumes/files/applications, same-title distinct jobs, and null-owner legacy records. Record all IDs/relationships before execution.
- [ ] Remove the `RUN_SQLITE_MIGRATION` startup execution path. The command must preserve user IDs, application IDs, resume IDs, file ownership/location, dates, and relationships. Never migrate per-user secrets into global settings.
- [ ] Implement a dry-run first; report identity/uniqueness conflicts and null-owner rows separately. Unowned records require an explicit administrator mapping supplied to the command; leave them untouched otherwise. Reject source=destination and any attempted implicit overwrite.
- [ ] Apply in transactions with a migration ledger and idempotent keys. A second execution makes no duplicate rows. Test rollback after an injected mid-migration failure. No migration should call the application's heuristic duplicate merger.
- [ ] Run `python -m pytest tests/test_migration.py -q` on SQLite fixtures and a disposable PostgreSQL destination; compare counts, IDs, ownership, settings, and file hashes. Commit as `Replace startup migration with explicit safe import`.
