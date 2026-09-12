# Public Launch Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Execute sequentially, reviewing each task before starting the next.

**Goal:** Resolve the launch review's security, recovery, data-reliability, and operational gaps before inviting public users.

**Architecture:** Keep the FastAPI, React/Vite, PostgreSQL/SQLite, and object-storage architecture. Centralize outbound network enforcement, move concurrent limits into database transactions, and complete existing account-recovery APIs instead of replacing the application. Separate security, account flows, persistence, and release preparation into independently reviewable changes.

**Tech Stack:** Python/FastAPI/Pydantic, React/Vite, PostgreSQL and SQLite, R2/local storage, pytest, Vitest, Docker, Render.

**Spec:** [Launch readiness review](../../LAUNCH_READINESS_REVIEW_2026-09-11.md), based on commit `c54bb1f` on `launch-readiness`.

## Global Constraints

- Planning only at this stage. Execution does not imply authorization to deploy, send unsolicited emails, or migrate/delete production records.
- Work sequentially on the existing remediation branch after verifying its current state. Follow the professional-git-workflow skill for any branch or commit operations; preserve unrelated work.
- Keep the public API compatible except where rejecting previously unsafe input or identity linking is necessary.
- Preserve offline operation and intentionally configured local AI endpoints in local mode. Production must not permit local/private AI or scraping destinations.
- Keep the existing advertised limits: 10 resumes per account, 50 MiB binary storage, 10 MiB per uploaded document, and 100,000 characters per saved resume.
- Use synthetic accounts, disposable databases, fake mail, and mocked outbound services for automated tests. Disable dotenv loading and real SMTP/R2/AI credentials before application imports.
- Every security or data-integrity task gets a regression test that fails before the fix and passes afterward. Mechanical cleanup does not need invented tests.
- No silent data deletion or automatic repairs of ambiguous legacy records. Repairs default to inspection/dry-run and require a backup before application to real data.
- Scan and test the exact release image. The prior Windows Python 3.12/Node 24 results do not establish Linux container behavior.
- A phase is complete only after its stated gate passes. A blocked operational task does not prevent completing independent local fixes.

## Delivery map

| Phase | Tasks | Review coverage | Deliverable |
| --- | --- | --- | --- |
| 1. Close security gaps | 1–3 | L01, L02, L03, L04 | Safe printing, identity matching, and outbound requests |
| 2. Make limits and files reliable | 4–5 | L05, L08, L09; legacy ownership | Atomic limits and recoverable file operations |
| 3. Complete account recovery | 6 | L06; email part of L11 | Working verification/reset browser journeys and delivery configuration |
| 4. Protect stored data | 7–8 | L07, L10 | Validated writes, explicit repairs, verified migrations |
| 5. Polish and stabilize builds | 9–10 | Remaining L11; dependencies and cleanup | Correct frontend state, reproducible builds, reduced dead code |
| 6. Verify and release gradually | 11–12 | Deployment, ingress, backups, final regression | Staging evidence, private beta, controlled public launch |

## File ownership and boundaries

Paths below are relative to the repository root.

- `frontend/src/utils/printCoverLetter.js` (new): create a printable document using DOM text APIs. `CoverLetterModal.jsx` keeps UI state and calls it.
- `backend/services/outbound_http.py`: destination policy, redirect policy, response budgets, public-IP classification.
- `backend/services/pinned_transport.py` (new): connection-time address enforcement with preserved TLS hostname validation. Only the outbound module and AI client factory consume this adapter.
- `backend/services/rate_limiter.py`: retain the public limiter interface; use atomic storage operations.
- `backend/services/resource_leases.py` (new): bounded in-flight work with expiring database leases, independent of worker process count.
- `backend/services/resume_files.py` (new): reserve capacity and coordinate binary/attachment/resume lifecycles. Routes remain thin; `object_storage.py` handles bytes and backend errors.
- `backend/routers/auth.py`, `auth_service.py`, `email_service.py`: identity verification, single-use authentication tokens, mail transport selection. Avoid an unrelated authentication rewrite.
- `frontend/src/components/AuthLinkPage.jsx` (new): verification and password-reset states for emailed links.
- `backend/storage.py`, `models.py`, `migrate.py`: validation, transactional persistence, migration correctness. Add `backend/repair_data.py` for explicit legacy-data inspection/repair.
- Existing frontend components: local fixes only, without redesigning the app.
- `requirements/`, Dockerfile, CI, Render configuration, and deployment docs: one dependency source of truth and release verification.

## Execution conventions

For each task: add the listed regression, run it to reproduce the issue, implement the specified behavior, run its focused suite, inspect the diff, and checkpoint the change using the established Git workflow. Do not group unrelated fixes into the same commit.

Backend commands below assume an isolated environment with test dependencies installed and real services disabled; use `python -m pytest ...`. Frontend commands run in `frontend/`. Record actual results, not just intended commands, in `docs/LAUNCH_REMEDIATION_VALIDATION.md` (new).

### Task 1: Make printable cover letters text-safe

**Files:** create `frontend/src/utils/printCoverLetter.js`; modify `frontend/src/components/CoverLetterModal.jsx`; extend `frontend/src/test/CoverLetterModal.test.jsx`.

**Interface:** `renderCoverLetter(document, { candidateName, company, subject, body, dateLabel })` mutates only the supplied print document. Every property is treated as text.

- [ ] Add a regression that prints hostile HTML strings separately in name, company, subject, and body. Verify the popup contains the literal text, no script/event-handler nodes, and no injected opener mutation.
- [ ] Run `npm run test:run -- src/test/CoverLetterModal.test.jsx`; confirm the regression fails on the current handler.
- [ ] Replace interpolated `document.write` with DOM construction. The basic rendering pattern is:

```javascript
function appendText(document, parent, tag, value, className = '') {
  const node = document.createElement(tag);
  node.textContent = String(value ?? '');
  node.className = className;
  parent.appendChild(node);
  return node;
}
```

Use static trusted CSS with `white-space: pre-wrap` for body paragraphs. Set `document.title` as text. Trigger printing from the parent handler rather than injecting a script. Set the child opener to null after retaining its window reference; preserve popup-blocked feedback.
- [ ] Test line breaks, punctuation, ordinary names, cancellation, and blocked popups. Keep DOCX export working.
- [ ] Inspect a synthetic print preview in a browser and confirm layout and literal HTML rendering. Gate: no untrusted value is parsed as markup.

### Task 2: Close unsafe Google account-linking behavior

**Files:** modify `backend/routers/auth.py`, `backend/services/auth_service.py`, runtime dependency source; extend `tests/test_identity_linking.py`, `tests/test_auth_api.py`.

**Interfaces:** retain `verify_google_id_token(token)` as the verification boundary. Add `google_is_authoritative(claims: dict) -> bool`. Preserve existing lookup by immutable `sub`.

- [ ] Adapt the synthetic third-party-email probe into a regression: an existing verified password account plus a new non-authoritative Google `sub` must return 409 without changing password, subject, verification state, or session version.
- [ ] Run `python -m pytest tests/test_identity_linking.py tests/test_auth_api.py -q` and observe the new failure.
- [ ] Use Google's verification library for signature, issuer, expiration, and required audience. Require configured production client ID; remove the silent hard-coded audience fallback. Use this authority predicate only after token verification:

```python
def google_is_authoritative(claims: dict) -> bool:
    email = str(claims.get("email", "")).lower()
    verified = claims.get("email_verified") is True
    return verified and (email.endswith("@gmail.com") or bool(claims.get("hd")))
```

- [ ] For a new subject colliding with an existing email and lacking authority, reject linking with a clear instruction to use password sign-in/recovery. Do not add an account-linking UI for this release. Existing subject matches remain valid. For a new non-authoritative email account, require application mailbox verification before issuing a full application session.
- [ ] Preserve authoritative Gmail/Workspace handling, collision rejection, and pre-account-hijacking protections. Invalidate outstanding verification/reset tokens whenever linking revokes credentials; perform identity updates atomically.
- [ ] Cover missing/wrong audience, expired token, wrong issuer, unverified mail, Gmail, Workspace, third-party addresses, existing subject, and collision. Gate: email equality alone never attaches a non-authoritative identity to an existing account.

### Task 3: Enforce network destinations and response budgets at the transport

**Files:** modify `backend/services/outbound_http.py`, `scraper.py`, `ai_engine.py`; create `backend/services/pinned_transport.py`, `tests/test_pinned_transport.py`; extend `tests/test_outbound_http.py`, `tests/test_scraper.py`, `tests/test_ai_engine.py`.

**Interfaces:** retain `SafeHttpClient.get/post/request` and `AIEngine._get_client`. Add `resolve_public_addresses(host: str, port: int) -> tuple[str, ...]` and `PinnedTransport`, an HTTP client transport compatible with the pinned SDK/HTTP dependency versions established during implementation.

- [ ] Add these classification tests and connection-level regressions. Run them before changing the implementation:

```python
@pytest.mark.parametrize("address", [
    "127.0.0.1", "169.254.169.254", "100.64.0.1",
    "10.0.0.1", "::1", "::ffff:127.0.0.1",
])
def test_nonpublic_addresses_are_rejected(address):
    assert not is_safe_ip_string(address)
```

The fake resolver returns a public address first and private address second; the fake dialer records actual connection addresses. Assert that no unvalidated address is dialed, not merely that the URL was checked. Add an SDK redirect response pointing to loopback and assert no follow-up request occurs.
- [ ] Reject non-global addresses, empty DNS results, credentials in URLs, and ports outside policy. Production scraping permits HTTP 80 and HTTPS 443; production AI requires HTTPS 443 and a nonempty host allowlist. Local loopback AI remains explicitly local-mode only.
- [ ] Implement one resolved-address connection adapter: resolve once per new connection, validate all returned addresses, connect only to validated literal addresses, retain the original hostname for Host/SNI and certificate checks, and prohibit an implicit second DNS lookup or ambient proxy bypass. Pin and integration-test the HTTP library version used by this adapter.
- [ ] Route scraper traffic, including ATS helper requests, through this adapter. Remove the independent curl impersonation route unless it enforces the same invariants; initial release may use the safe standard transport and existing paste-text fallback. Never downgrade TLS validation to keep a scraper working.
- [ ] Configure the AI client with the protected transport and redirects disabled. Reject provider redirects with actionable feedback instead of forwarding credentials or request bodies. Audit the SDK's installed HTTP transport API before wiring it; the review environment used `httpx2`, so do not assume an unrelated `httpx` client is accepted.
- [ ] Read decoded response bytes incrementally. Use a 2 MiB scraping budget, at most five validated scrape redirects, and a 30-second overall deadline including retries; use an explicit 2 MiB AI-response budget and no unbounded SDK retries. Abort and close streams immediately on overflow. A loop invariant for decoded chunks is:

```python
total = 0
for chunk in response.iter_bytes():
    total += len(chunk)
    if total > limit_bytes:
        raise ValueError("Response body exceeds configured limit")
    chunks.append(chunk)
```

Apply bounded decompression too: decoded iteration must not materialize an unbounded decompressed chunk before the check. Limit decompressor output per call and test compressed expansion.
- [ ] Run focused network/scraper/AI suites. Test public redirects, mixed public/private DNS answers, IPv6, TLS hostname mismatch, cross-origin credentials, oversize chunked/compressed responses, deadlines, and local-mode exceptions. Gate: no raw curl/SDK path bypasses policy and no oversized response is fully buffered.

### Task 4: Make rate and concurrent-work limits atomic

**Files:** modify `backend/services/rate_limiter.py`, `backend/storage.py`, `backend/main.py`, `backend/routers/auth.py`, `backend/config.py`; create `backend/services/resource_leases.py`; extend `tests/test_rate_limits.py`; create `tests/test_resource_leases.py`.

**Interfaces:** keep `RateLimiter.check(bucket, subject, limit, window_seconds, now_epoch=None)` and its `(allowed, remaining, retry_after)` result. Add `ResourceLeases.acquire(user_id: str, kind: str, ttl_seconds: int) -> str` and `release(lease_id: str) -> None`; exhausted capacity becomes HTTP 429 with Retry-After.

- [ ] Promote the coordinated counter probe into a regression: starting with one remaining slot, exactly one of two concurrent requests succeeds. Also test concurrent first use, window reset, and expiry.
- [ ] Replace separate reads/absolute updates with transactionally safe creation and increment: PostgreSQL row locks/conditional UPSERT; SQLite `BEGIN IMMEDIATE` around the decision and write. Preserve a single result even on first-insert conflicts. Use database time consistently for shared-worker expiry where available.
- [ ] Add per-user analysis limiting using the existing 30/minute AI bucket and retain anonymous analysis at 10/minute/IP. Add Google-login limiting at 10/minute/IP before provider verification. Apply the shared user limit consistently to expensive AI operations.
- [ ] Add expiring database leases for scraping, document parsing, and AI work: default two active operations per authenticated user and eight globally, configurable after staging measurement. Lease TTL must exceed the enforced operation deadline and abandoned leases must expire. Acquire before work, release in `finally`; capacity failures never begin external work.
- [ ] Exercise the actual API with exhausted buckets. Assertions must include status and Retry-After, and assert the scraper/provider was not called:

```python
assert response.status_code == 429
assert int(response.headers["Retry-After"]) >= 1
provider_call.assert_not_called()
```

- [ ] Use proxy headers only from a configured trusted ingress. Configure one verified Render header source; do not silently trust the leftmost forwarded header from arbitrary peers. Retain a safe direct-peer fallback. Prove header behavior in staging during Task 11.
- [ ] Run limiter/lease tests against SQLite and disposable PostgreSQL using real concurrent connections. Gate: exact budgets under concurrency and bounded in-flight work across workers, not just per process.

### Task 5: Make resume ownership, quotas, downloads, and deletion reliable

**Files:** create `backend/services/resume_files.py`; modify `backend/main.py`, `backend/storage.py`, `backend/services/object_storage.py`; extend `tests/test_resume_file_security.py`, `tests/test_object_storage.py`, `tests/test_resume_edits.py`; create `tests/test_resume_lifecycle.py`.

**Interfaces:** `ResumeFiles.create_upload(user_id, filename, content_type, content_bytes, resume_name, resume_text) -> Resume`; `ResumeFiles.delete(user_id, resume_id) -> None`. Object deletion returns success for an absent object and raises a typed error for an actual backend failure. File access requires both owned attachment metadata and matching user namespace.

- [ ] Add regressions for the two-slot/three-resume race, 50 MiB reservation races, Unicode filenames, missing-object deletion, wrong-owner keys, and every database/object-store failure boundary.
- [ ] Add a per-user quota ledger/reservations under the same database locking strategy as Task 4. Count stored plus reserved resumes/bytes before starting the upload. Reserve text-only resumes too. Keep transactions short; never hold a database lock during an object-store call.
- [ ] Reserve a deterministic owned object key and pending attachment before uploading. Commit the resume and active attachment after upload success. On failure, remove the binary and release reservations; if deletion fails, retain a retryable pending record and keep its bytes accounted for. Add a bounded reconciliation command for expired reservations and orphaned pending objects.
- [ ] Require attachment ownership for downloads/deletes. Legacy records must be explicitly mapped after confirming namespace ownership; reject ambiguous or cross-user keys. Honor each attachment's recorded local/R2 backend rather than only current global configuration.
- [ ] Treat object absence as successful deletion; keep genuine backend failures retryable and visible. Repeat deletion safely. Only release quota once the resource state justifies it. Update deletion copy to describe pending failures accurately.
- [ ] Generate Unicode-safe headers, retaining injection sanitization:

```python
from urllib.parse import quote

def download_disposition(filename: str) -> str:
    clean = filename.replace("\r", "_").replace("\n", "_")
    return "attachment; filename=\"resume\"; filename*=UTF-8''" + quote(clean, safe="")
```

Retain a useful ASCII fallback extension in the final implementation. Test CJK, emoji, quotes, CR/LF, and byte-for-byte original-file downloads.
- [ ] Run lifecycle and ownership suites with fake local/R2 backends and PostgreSQL quota concurrency. Gate: no cross-account access, quota overshoot, untracked partial upload, or permanently undeletable missing binary.

### Task 6: Complete verification and password recovery

**Files:** create `frontend/src/components/AuthLinkPage.jsx`, `frontend/src/test/AuthLinkPage.test.jsx`; modify `frontend/src/App.jsx`, `components/AuthModal.jsx`, `api/client.js`, `backend/main.py`, `backend/routers/auth.py`, `backend/services/email_service.py`, `backend/config.py`, `backend/storage.py`, `.env.production.example`, `render.yaml`, `docs/RENDER_DEPLOYMENT_GUIDE.md`; extend auth/token/config tests.

**Interfaces:** retain existing `/api/auth/verify-email/confirm` and `/api/auth/password-reset/confirm` request bodies. `AuthLinkPage` consumes `pathname` and the query token; states are loading, ready, submitting, success, expired/invalid, and retryable failure.

- [ ] Add production-static-route regressions and frontend tests. A representative route assertion after building assets is:

```python
@pytest.mark.parametrize("path", ["/verify-email", "/reset-password"])
def test_auth_link_serves_frontend(client, path):
    response = client.get(path + "?token=synthetic")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
```

Also assert unknown `/api/...` routes still return API 404 rather than the SPA document.
- [ ] Add explicit frontend shell routes for the two email destinations before the static mount. Parse and retain the token in component memory; remove it from the address bar with `history.replaceState` after capture. Use `Referrer-Policy: no-referrer` on these pages and avoid analytics/third-party scripts before consumption.
- [ ] Verification uses an explicit confirm button so link scanners do not consume tokens. Reset displays new-password/confirmation inputs and the existing password rules. Success returns to sign-in; expired links offer a fresh request. Never store recovery tokens in localStorage or logs.
- [ ] Make request helpers reject non-2xx responses, show 429 retry feedback, and keep account-existence responses generic. Consume auth tokens atomically with expiry checks and associated password/session updates; simultaneous confirmation of the same token must have exactly one success.
- [ ] Keep fake mail only in local/test modes. For production, select an HTTPS transactional-mail provider through `EmailTransport.send(recipient, subject, text_body)`; implement the adapter against the chosen provider's verified official API with a 10-second deadline, fixed destination, and bounded retries/idempotency. SMTP remains optional only on a deployment that supports the configured port, with an explicit timeout.
- [ ] Operational prerequisite for the mail adapter: the owner supplies the provider choice/account, verified sender domain, and secret API key through deployment settings. This choice is not permission to purchase a service or send mail. Local screens, contract tests, and fake transport tests proceed without credentials. Before implementing the provider-specific adapter, record its exact endpoint, authentication header, idempotency behavior, and error mapping from official documentation in the validation record.
- [ ] Require HTTPS `APP_URL`, configured delivery, sender, and Google client ID in production; no silent fake-mail fallback. Expose delivery failure to operator logs/metrics without recipient tokens or credentials. Add only secret names to blueprint/examples.
- [ ] Run auth tests plus `npm run test:run -- src/test/AuthLinkPage.test.jsx`. Gate: all browser states work; staging later proves real delivery, link reuse rejection, password change, and old-session invalidation. Mandatory verification is enabled only after that evidence exists.

### Task 7: Validate before writing and repair invalid data explicitly

**Files:** modify `backend/models.py`, `backend/storage.py`, `backend/main.py`; create `backend/repair_data.py`, `tests/test_data_repair.py`; extend `tests/test_application_security.py`, `tests/test_settings_isolation.py`, `tests/test_resume_edits.py`.

**Interfaces:** retain existing create/update routes. `python -m backend.repair_data --database <target>` inspects only; `--apply` is a separate explicit mutation mode. Inspection output reports counts and opaque record IDs, not resume contents or secrets.

- [ ] Add API regressions asserting null application status and null follow-up days return 422 and leave subsequent lists/settings reads healthy:

```python
def test_null_status_does_not_poison_list(two_users):
    client, owner, _ = two_users
    response = client.post("/api/applications", headers=owner,
        json={"company": "Synthetic", "role": "Engineer", "status": None})
    assert response.status_code == 422
    assert client.get("/api/applications", headers=owner).status_code == 200
```

- [ ] Reject explicit null for non-nullable fields while preserving omitted patch fields and intentional nullable fields such as active profile selection. Put the 100,000-character bound on both resume create/update models and uploaded/extracted text paths.
- [ ] Validate merged settings before encryption/storage using `Settings.model_validate(merged)`. Build/validate the resulting Application before inserting it. Keep validation failures outside committed writes.
- [ ] Add inspection for existing invalid statuses/days, orphan attachments, and ambiguous legacy keys. Provide deterministic repair only where safe: invalid follow-up days can reset to the documented seven-day default; invalid application status requires an explicit target status chosen during repair. Back up original values in a restricted repair log; never expose API keys.
- [ ] Verify dry-run changes nothing and repair is repeatable. Gate: malformed input causes no persisted invalid state; users with previously bad records have a documented recovery path.

### Task 8: Make migration accurate and verifiable

**Files:** modify `backend/migrate.py`, `backend/storage.py`; extend `tests/test_migration.py`; update deployment/migration documentation.

**Interface:** retain `run_migration(source_path, dest_path, dry_run=True, map_unowned_to=None)`. Success means verified migration, not merely that the function reached its end.

- [ ] Add a source fixture containing users, session versions, Google subjects, applications, resumes, attachments, user settings, encrypted provider profiles, and global settings. Assert values and ownership survive, not just row counts. Reproduce the current omitted-settings result.
- [ ] Select the destination explicitly:

```python
if dest_target.startswith(("postgres://", "postgresql://")):
    dest_storage = StorageService(database_url=dest_target)
else:
    dest_storage = StorageService(db_path=dest_target, force_sqlite=True)
```

- [ ] Migrate the actual three-column user-settings schema. Replace swallowed exceptions with explicit missing-legacy-table handling and hard failures for schema/write errors. Roll back on failure and close source/destination resources reliably.
- [ ] Keep reruns idempotent but detect conflicting destination records instead of silently skipping divergent values. Verify per-table counts and field values, including identity/session state and attachment ownership. Do not print secrets or full connection URLs.
- [ ] Require explicit ownership mapping for unowned legacy data. Document that copying database rows does not copy local binaries or rotate encryption keys; preserve the existing encryption key or use a separately verified rotation procedure.
- [ ] Run SQLite-to-SQLite and SQLite-to-disposable-PostgreSQL round trips, an injected mid-migration failure, rerun, and backup restoration. Gate: no success result on dropped data, and a demonstrated rollback/restore path.

### Task 9: Correct remaining frontend state and layout

**Files:** modify `frontend/src/api/client.js`, `App.jsx`, `components/JobAnalyzer.jsx`, `components/KanbanBoard.jsx`, `components/PrivacyModal.jsx`; extend account-switch tests; create `frontend/src/test/JobIdentity.test.jsx`.

- [ ] Extend the account-switch regression to assert persisted `jh_user`, not just rendered state. Capture the request token before fetching `/auth/me` and write cache only if it still matches:

```javascript
const requestToken = getToken();
const res = await authFetch(`${API_BASE}/auth/me`);
if (!res.ok) throw new Error('Failed to get user profile');
const user = await res.json();
if (requestToken && requestToken === getToken()) {
  localStorage.setItem('jh_user', JSON.stringify(user));
}
return user;
```

- [ ] Test two URLs with equal company/title, tracking-parameter variants of one URL, and manual-paste jobs. Match backend canonical URL rules: when both have real URLs, URL identity takes precedence; only use company/role fallback where the backend also does so.
- [ ] Replace conflicting Kanban fractional tracks with explicit minimum-width tracks, for example `lg:grid-cols-[repeat(6,minmax(260px,1fr))]`, within a bounded horizontal scroll container. Preserve mobile stacking and keyboard access.
- [ ] Update privacy copy to explain external-provider processing, actual deletion failure states, and the support path for account/data deletion. Avoid claims the implementation or operational policy cannot guarantee.
- [ ] Run frontend tests and inspect 390 px, 768 px, and 1280 px layouts with synthetic jobs. Gate: no stale-account cache, misleading posting identity, or overlapping columns.

### Task 10: Stabilize dependencies and remove proven redundancy

**Files:** modify `requirements.txt`, `requirements/runtime.txt`, `requirements/dev.txt`, `frontend/package.json`, `frontend/package-lock.json`, Dockerfile, `.github/workflows/ci.yml`, `render.yaml`, README, and the exact unused-import locations in the review; create `requirements/runtime.lock` and `requirements/dev.lock`.

- [ ] Make `requirements/runtime.txt` the human-maintained runtime source and root `requirements.txt` an include. Generate tested, hashed dependency locks for the Linux production Python version, including the security/mail dependencies selected in earlier tasks. Docker and CI install the same locked runtime; separate development tools.
- [ ] Upgrade Vitest/mocker to a currently patched supported version and update the lockfile. Check official advisories at execution time. Refresh build/audit installers; do not interpret duplicate installer advisories as application vulnerabilities.
- [ ] Align CI and container runtimes on supported versions verified at execution time. Build with exact image digests for the candidate release and establish a scheduled update process; do not blindly retain an obsolete Node version because it appeared in the old baseline.
- [ ] Remove the review's 11 unused Python imports, two unused exception bindings, unused frontend `role`, React/test imports, and unnecessary prop plumbing. Preserve error handling and tests.
- [ ] Retire the unused legacy migration method after checking repository/documented external callers. Keep `build.sh` and compatibility requirement entry points unless their alternative install workflow is confirmed obsolete. Remove the unused Google-client-secret requirement from the blueprint, without deleting any deployed secret.
- [ ] Run the existing suites, `npm run build`, `npm audit --omit=dev`, full npm audit, Python locked-environment audit, and the production-image build. Use `python -m ruff check backend run.py --select F401,F841`. Gate: no unexplained applicable high/critical production advisories, the known Vitest advisory resolved, and identical tested runtime resolution in CI/deployment.

### Task 11: Prove readiness on staging

**Files:** modify `backend/config.py`, `render.yaml`, deployment guide and CI as required; record evidence in `docs/LAUNCH_REMEDIATION_VALIDATION.md`; create `docs/PUBLIC_LAUNCH_RUNBOOK.md`.

- [ ] Make production fail clearly when persistent database or configured durable object storage is absent. Keep SQLite/local fallback for local/test mode only unless a persistent production disk is explicitly configured and verified. Confirm R2 bucket access is private and API downloads enforce ownership.
- [ ] Prepare a staging release from the exact reviewed commit using a separate database, object namespace/bucket, and test identities. Record image digest, runtime versions, configuration presence checks, and redacted dependency results.
- [ ] Verify ingress behavior with harmless test requests: supplied forwarding headers must not let a client select arbitrary limiter identities. Confirm direct backend bypass is unavailable; if it is, narrow trusted peers/headers before release.
- [ ] Exercise browser journeys: register, verification, password login, Google login/collision handling, logout/account switch, password recovery, upload/edit/download/delete, job URL and pasted-text analysis, offline/BYOK modes, tracker, cover-letter print/DOCX, and spreadsheet export. Use an explicitly authorized staging inbox for delivery tests.
- [ ] Measure a bounded staging burst with ten synthetic users, at most 20 concurrent requests for two minutes, with mocked AI where appropriate. Expected: excess work gets predictable 429 responses, no quota overflow/cross-account access, no unexpected 500s, and memory returns near baseline. Adjust resource ceilings based on measurements without weakening validation.
- [ ] Restore a backup into a disposable database and verify synthetic resume files plus encrypted profile usability. Record recovery duration, backup retention, encryption-key backup handling, and who can execute rollback. Test the prior image against any additive schema changes.
- [ ] Set up actionable monitoring for 5xx spikes, auth/mail delivery failures, storage failures, quota reconciliation, database capacity, and request latency. Logs must omit credentials, auth-link tokens, and resume bodies. Document a user support contact and data-deletion process.
- [ ] Gate: every mandatory release item below has evidence, not an assumption. Do not declare production ready if mail, PostgreSQL concurrency, durable storage, or restore checks remain unverified.

### Task 12: Release to a small beta, then promote

**Files:** update `docs/PUBLIC_LAUNCH_RUNBOOK.md`, README, and validation record.

- [ ] Prepare the release/rollback instructions and user-facing known limitations. Obtain deployment authorization only after the candidate and evidence are reviewable; no production mutations are included in this planning request.
- [ ] Deploy the approved candidate, run smoke tests, and confirm deployed commit/image identity. Keep the previous image and backup available. Do not apply repair commands to real data without first reviewing their dry-run output and backup.
- [ ] Invite 5–10 consenting beta users. Observe for 48–72 hours, covering at least one registration/recovery cycle and real upload/download/delete workflow. Do not send invitations or promotional posts without explicit authorization.
- [ ] Roll back or disable the affected feature immediately for cross-account access, token exposure, data loss, or broken recovery; investigate unexpected 500s before increasing traffic. Rollback must account for schema compatibility and must not blindly overwrite newly created user data.
- [ ] When the beta gate passes, promote gradually: a small initial post, observe errors/capacity, then broader Reddit/LinkedIn sharing. Describe it as beta if remaining documented limitations justify that label. Budget monitoring continues beyond launch.

## Public-launch acceptance checklist

- [ ] L01–L06 security/recovery blockers fixed with regression evidence.
- [ ] L07–L10 data/file/migration defects fixed; required legacy inspection completed.
- [ ] L11 account cache, email errors, duplicate labels, and layout verified.
- [ ] Real staging mail delivery and complete verification/reset journeys pass.
- [ ] Google third-party-email collision cannot attach to another account by email alone.
- [ ] No unvalidated connection destinations, unbounded response reads, or worker-local-only resource ceilings.
- [ ] SQLite and PostgreSQL concurrent limits/quotas pass.
- [ ] Production image, dependency audit, frontend build, and full tests pass.
- [ ] Persistent private storage, exact deployed configuration, and trusted ingress verified.
- [ ] Backup restoration and rollback rehearsed; monitoring/support/deletion procedures documented.
- [ ] Private beta has no unresolved security, data-loss, recovery, or recurring server-error issue.

Mechanical cleanup is not, by itself, a public-launch blocker. Neither passing tests nor a quiet beta proves the absence of all vulnerabilities; the release decision is based on the specific safeguards and evidence above.

## Decisions and handoff

Recommended execution is sequentially in the current task, one phase at a time, preserving the existing branch unless its state requires isolation. No subagents are needed for this plan.

The only external setup choice required early is the transactional-email provider and verified sender. Staging/production access and a backup destination are needed for the final operational gate. Those prerequisites do not block local security, data, UI, or fake-mail work.

This plan is saved under the writing-plans skill's default directory, which the repository currently ignores. Preserve a tracked copy or adjust the documentation ignore rule during execution if the plan should ship with the remediation PR. Do not force-add ignored scratch artifacts or personal data.
