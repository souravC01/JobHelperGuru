# JobHelperGuru public launch readiness review

Reviewed: 11 September 2026. Branch: `launch-readiness`. Commit: `c54bb1f`.

**Recommendation: hold public promotion until the security and account-recovery issues below are fixed and retested.** The application builds and its existing tests pass, but targeted checks exposed failures those tests do not cover.

This review covers the current local source, authentication, account isolation, uploads, outbound requests, generated documents, persistence, frontend flows, deployment files, dependencies, and cleanup candidates. Findings are about this checkout; they do not establish which commit or configuration is running on Render. No production accounts, databases, credentials, or files were used for the reproductions. No fixes or deployment changes were made.

## Verification results

| Check | Result |
| --- | --- |
| Backend test suite | 165 passed; two tooling/deprecation warnings |
| Frontend test suite | 19 passed across nine files |
| Frontend production build | Passed |
| Targeted synthetic checks | Confirmed the failures described below |
| Frontend production dependency audit | No known advisories returned |
| Full frontend dependency audit | One advisory affecting two development packages: Vitest and its mocker |
| Installed Python environment audit | Findings only for the audit environment's `pip` installer; no other installed package was flagged |
| Python unused import/binding check | 13 findings: 11 imports and two exception bindings |

Tests ran with Python 3.12.14 and Node 24.19.0 on Windows. Docker/CI specify Python 3.11 and Node 20. A Linux production-image run, PostgreSQL concurrency run, and deployed end-to-end verification remain necessary. Python requirements are not locked, so the local dependency result is not a scan of the deployed container.

Local reproduction scripts and machine-readable results are in ignored `scratch/launch-review-20260911/`. They use temporary SQLite databases, synthetic identities, fake file storage, and mocked HTTP transports. The print check parses the actual handler's generated HTML with jsdom; it is not a live-browser exploitation test.

## Fix before public promotion

### L01 — High: cover-letter printing renders untrusted text as executable HTML

**Location:** `frontend/src/components/CoverLetterModal.jsx:90`, especially the interpolation into `document.write`; token storage at `frontend/src/api/client.js:4`.

The print/PDF handler inserts the candidate name, company, subject, and generated cover-letter paragraphs into an HTML document without escaping. The popup is opened as a same-origin blank window with an opener. Text containing HTML can therefore become script rather than document content.

**Evidence:** extracting the actual print handler and parsing its emitted HTML executed an injected, harmless script that changed a synthetic opener marker. No real tokens were accessed.

**Impact:** if hostile job metadata or generated content reaches these fields and the user prints it, script can run with the application's origin and potentially access its localStorage session token or act as that user. A complete malicious-job-to-provider-output attack was not tested; the unsafe rendering sink is confirmed.

**Fix:** build the print document with text nodes, or escape every interpolated value consistently. Preserve line breaks without treating input as markup. Remove opener access where possible as additional protection. Test each interpolated field with HTML characters and verify that it remains visible text.

### L02 — High: Google login can attach a third-party email identity without current mailbox proof

**Location:** `backend/routers/auth.py:395`, email matching/linking around line 453.

The route automatically links an existing account by matching email whenever Google reports `email_verified`, without checking whether Google is authoritative for that mailbox. This matters for Google accounts created using third-party email addresses.

**Evidence:** at the verified-provider boundary, synthetic claims containing a third-party email, `email_verified=true`, and no `hd` claim were accepted and issued a session for an existing verified password account with that email. The test mocks provider verification; it does not forge a Google signature.

**Impact:** under the mailbox-ownership-change scenario documented by Google, an older Google identity can be linked to the current mailbox owner's application account. Google recommends an additional password or other challenge for these non-authoritative addresses. See [Google's ID-token verification guidance](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token).

**Fix:** require existing-account authentication or fresh mailbox verification before linking a non-authoritative identity. Continue using `sub` for established identities. Use Google's production token-verification library with required audience, issuer, and expiration checks; the current conditional audience check also accepts an absent `aud`, and `tokeninfo` is intended for development/debugging. Test Gmail, Workspace, third-party mail, identity collisions, and missing claims separately.

### L03 — High: outbound-request protections do not control the actual connection

**Locations:** `backend/services/outbound_http.py:63`, `backend/services/outbound_http.py:149`, `backend/services/scraper.py:70`, `backend/services/ai_engine.py:169`.

Scraping validates DNS addresses, then gives the original hostname to a separate HTTP/curl request, which resolves DNS again. An attacker-controlled job hostname can change its DNS response between validation and connection. The checked addresses are not pinned to the connection.

AI requests validate only the initial URL, then use an ordinary OpenAI client. Redirects do not pass through the project's destination policy. AI validation also does not check resolved addresses. The IP helper accepts shared-address space such as `100.64.0.1`, despite describing its policy as globally routable public addresses.

**Evidence:** code inspection confirms the DNS validation/connection gap. With HTTP transport mocked, the actual AI client followed an initial allowed provider URL to `https://127.0.0.1/internal`. The IP helper accepted `100.64.0.1`. No private service was contacted.

**Impact:** scraping can potentially reach internal services through DNS rebinding. The AI redirect issue additionally requires a redirect from an allowed provider or an operator-approved endpoint; it is not an arbitrary-provider bypass by itself. Reachability and damage depend on the deployment's network.

**Fix:** enforce public destination addresses at connection time, preserving hostname/TLS verification, or use a controlled outbound proxy. Apply the same policy to every transport and redirect. Reject non-global addresses and explicitly define permitted ports. Add connection-level tests rather than relying only on URL-validator tests.

### L04 — High: scraper response limits do not bound memory consumption

**Locations:** `backend/services/scraper.py:70`, `backend/services/outbound_http.py:149`.

The preferred curl path reads the response into memory and accesses `.text` without a body-size limit. The fallback uses `client.request`, which buffers the response before checking `.content` against the 2 MiB limit. The check is therefore too late to prevent a large download from consuming memory. Redirects/retries can also multiply per-request timeout budgets.

**Evidence:** confirmed from transport control flow; no memory-exhaustion load test was run.

**Impact:** a submitted job URL serving a very large or slowly delivered response can consume worker capacity, memory, and bandwidth. This is especially relevant to a small shared web instance.

**Fix:** stream all responses, stop at the decoded-byte limit, and enforce an overall deadline across retries and redirects. Bound concurrent scraping and document parsing. Test chunked responses and compressed bodies without allocating large fixtures.

### L05 — High: rate limits and storage quotas are bypassable

**Locations:** `backend/main.py:221`, `backend/main.py:356`, `backend/main.py:373`, `backend/main.py:394`, `backend/services/rate_limiter.py:37`, `backend/routers/auth.py:395`.

Authenticated job analysis skips the limiter entirely. Google authentication has no route-level limiter, despite making an external token-verification request. The database limiter performs a separate read and absolute-value update rather than an atomic increment. Resume quotas likewise count before inserting or uploading, without reserving capacity.

**Evidence:**

- Authenticated analysis returned 200 with zero calls to the limiter, even when the mocked limiter would reject any call.
- With one rate-limit slot remaining, two coordinated requests both succeeded; the database counted two requests when three had actually been allowed.
- With the resume limit set to two for a small test and one existing resume, two concurrent creates both returned 200, leaving three resumes.

**Impact:** users can exceed advertised limits, and attackers can consume shared resources. The storage-byte quota has the same check-before-write structure; that separate race was not load-tested.

**Fix:** apply limits to all expensive routes, including authenticated analysis and Google login. Use database-atomic counters and quota reservations, with transaction-safe release on failures. Add per-user concurrency limits and a service-wide ceiling. Verify behavior under PostgreSQL as well as SQLite.

### L06 — High launch blocker: verification and password-reset emails cannot complete their browser journey

**Locations:** `backend/services/email_service.py:91`, `backend/main.py` final static mount, `frontend/src/components/AuthModal.jsx:6`, `frontend/src/api/client.js:112` and `:134`.

Emails point to `/verify-email?token=...` and `/reset-password?token=...`. Neither has a frontend route/token handler. The production static mount also returns 404 for these paths. The confirmation API functions exist but have no callers in the UI.

**Evidence:** both URLs returned 404 through the application with the built frontend present. Backend tests that directly call confirmation APIs do not exercise this flow.

Delivery has additional configuration gaps: absent `SMTP_HOST` selects the in-memory fake transport, and the default public URL is localhost. The checked-in Render blueprint supplies neither mail configuration nor `APP_URL`. Also, it selects the free plan, where outbound SMTP ports 25, 465, and 587 are blocked; the implemented SMTP transport defaults to 587. See [Render's free-service limitations](https://render.com/docs/free). Deployed dashboard overrides were not inspected.

**Impact:** password users cannot recover accounts, and enabling mandatory email verification can stop registrations from completing. With missing SMTP configuration, the application can claim that a link was sent while sending no email. SMTP also lacks an explicit connection timeout.

**Fix:** implement browser confirmation/reset screens and route fallback, configure the actual public URL and supported delivery transport, and reject invalid production mail configuration. Keep generic responses for unknown email addresses, but distinguish delivery/configuration failures in operator monitoring. Test a complete real-inbox journey on staging, including expired and reused links, before enabling verification.

## Additional defects to address

### L07 — Medium: accepted null values leave persistent account data unreadable

**Locations:** `backend/models.py:38`, `backend/models.py:123`, `backend/storage.py:850`, `backend/storage.py:1136`.

- Creating an application with `status: null` commits the string `"None"`, then returns 500. Later application-list requests for that account also return 500.
- Updating settings with `default_follow_up_days: null` persists an empty value, then fails during integer conversion. Subsequent reads and even a repair update return 500 because updates first load the broken settings.

Both cases were reproduced through the API using synthetic accounts. They affect the submitting user's data; no cross-account corruption was observed. Validate the final model before committing, reject null for non-nullable fields, and add a repair path for already-invalid rows. Test that rejected input leaves storage unchanged. Resume updates also lack the 100,000-character content bound applied to creation; make limits consistent.

### L08 — Medium: some resume filenames cannot be downloaded

**Location:** `backend/main.py:541` through the `Content-Disposition` response.

Uploading a synthetic Chinese-named `.txt` file returned 200, but downloading it returned 500. The filename is placed directly into a header that must be encoded by Starlette; characters outside Latin-1 cause failure. Use an ASCII fallback plus RFC-compatible UTF-8 `filename*` encoding. Verify accents, CJK text, spaces, quotes, and emoji.

### L09 — Medium: missing files and partial failures leave inconsistent resume storage

**Locations:** `backend/main.py:426`, `backend/main.py:600`, `backend/services/object_storage.py:192`.

When a resume's binary is already missing, deletion returns failure instead of treating absence as a completed deletion. Two consecutive delete attempts both returned 500 in the synthetic test; the resume remains and its attachment is marked failed.

Separately, uploading the binary and creating its attachment record happen outside the later resume-record cleanup block. An attachment-creation failure can leave an orphan binary. After a later resume-creation failure, cleanup marks the attachment failed even when binary deletion succeeds, leaving bookkeeping to reconcile. These partial-failure paths were identified by inspection.

Make deletion idempotent, distinguish missing objects from transport errors, and provide reliable compensation/reconciliation for each upload step. Operations should honor the attachment's recorded backend when moving between local storage and R2. Test each failure boundary. The privacy dialog's immediate-deletion wording currently overstates these failure cases.

### L10 — Medium: migration reports success while omitting settings; PostgreSQL destination handling is incorrect

**Locations:** `backend/migrate.py:82`, `backend/migrate.py:226`, `backend/storage.py:68`.

The user-settings migration expects `created_at` and `updated_at`, but the active table only has `user_id`, `key`, and `value`. A broad exception handler silently skips the section.

**Evidence:** migrating a temporary database containing one user-setting row reported `success: true` and a source count of one; the destination had zero user-setting rows.

The migration also passes a PostgreSQL URL through the `db_path` parameter. The storage constructor treats an explicit nondefault `db_path` as SQLite unless the separate database-URL path is selected. This is a code-confirmed routing defect; no production/PostgreSQL migration was attempted.

Pass PostgreSQL URLs explicitly via `database_url`, migrate the actual schema, fail visibly on errors, and verify destination counts and values. Do not use the migration tool for real data until a round-trip test and restore rehearsal pass.

### L11 — Low/medium: remaining frontend correctness issues

- **Stale account cache:** `frontend/src/api/client.js:162` writes a delayed `/auth/me` response into `jh_user` before `App.jsx:139` checks its session guard. A response from account A can overwrite account B's cached identity after switching. Guard the storage write using the request's token/session. Server ownership checks still apply; this is not evidence of cross-account API access.
- **False email success:** the verification/reset request helpers at `frontend/src/api/client.js:103` and `:125` do not reject non-success HTTP responses. A 429 JSON response can lead the modal to display a sent-email state. Check `res.ok` and show retry feedback.
- **Incorrect duplicate label:** `frontend/src/components/JobAnalyzer.jsx` uses company/title equality even when two posting URLs differ. A separate opening at the same company can be labelled “In Pipeline (Update).” The button is still clickable; this is misleading state, not a proven inability to save. Align frontend identity rules with backend canonical posting URLs.
- **Kanban layout:** `frontend/src/components/KanbanBoard.jsx:30` creates six fractional columns while each child requires at least 260 px. On typical desktop widths these constraints compete. Use explicit minimum-width grid tracks or a horizontal flex row; verify at desktop/tablet widths. This was identified by layout inspection, not a fresh browser rendering test.

## Dependency and deployment follow-up

The full npm audit reports [GHSA-82fw-gwwq-j7x9](https://github.com/advisories/GHSA-82fw-gwwq-j7x9) for Vitest and `@vitest/mocker`. This is one moderate advisory affecting two development packages, not two independent production vulnerabilities. Upgrade to a patched supported release and verify tests. Avoid blindly applying a major-version audit fix.

The Python scan returned 12 entries for local `pip` 25.0.1, with duplicate entries representing six unique advisory IDs. These concern the installer, not the application request handlers. Update the audit/build toolchain, and scan a reproducible deployment image. The deployed installer's version and applicability were not established.

Runtime Python requirements use broad lower bounds without a lock. Docker installs the root list, while CI development requirements include the separately duplicated runtime list. Consolidate the source of truth and lock/test the resolved runtime dependencies.

Before launch, verify the deployed commit, production mode, secret configuration, private R2 access, persistent database, and a tested backup/restore path. The app can fall back to local storage when cloud storage is absent. Local files on Render's free service disappear on restart/redeploy; that makes accidental fallback a data-loss risk. See [Render's storage limitations](https://render.com/docs/free). This is a conditional deployment risk, not a finding that your live database currently uses SQLite.

The proxy-IP helper trusts `render-proxy-client-ip` or the first forwarded IP whenever proxy trust is enabled, which defaults on in production. Verify that the actual ingress overwrites these values and disallows bypassing the proxy; otherwise callers can choose rate-limit identities. Header spoofability through Render's current edge was not tested.

For any data created before the earlier ownership fixes, inspect legacy resume file keys and attachment ownership mappings. R2 get/delete operations do not themselves enforce the supplied user namespace, and the routes retain a legacy file-key fallback when no owned attachment is found. Newly created resume metadata is constrained, so this is a conditional legacy-data concern rather than a reproduced new-account exploit.

## Redundant code and safe cleanup candidates

Safe mechanical cleanup, preserving existing behavior:

| Location | Candidate |
| --- | --- |
| `backend/main.py:7` | Unused `RedirectResponse` import |
| `backend/main.py:422`, `:444` | Unused exception bindings; retain exception handling |
| `backend/services/ai_engine.py:22` | Unused `match_skills` import |
| `backend/services/document_export.py:2` | Unused `re` import |
| `backend/services/email_service.py:4` | Unused `urllib.parse` import |
| `backend/services/outbound_http.py:5` | Unused `Any` import |
| `backend/services/scraper.py:4`, `:5`, `:6`, `:19` | Unused `urlparse`, `ipaddress`, `socket`, `SSRFBlockedError` imports |
| `backend/services/skill_matching.py:2` | Unused `Set` and `Optional` imports |
| `frontend/src/components/CoverLetterModal.jsx:100` | Unused `role` binding |
| `frontend/src/components/PrivacyModal.jsx:1` | Unused React import under the automatic JSX transform |
| `frontend/src/test/ClientDownload.test.jsx:2` | Unused `exportCoverLetterDocx` import |

The frontend scope scan also found unused catch bindings and an unused `currentUser` prop in SettingsModal. These are minor cleanup; remove bindings rather than discarding useful error handling.

Larger candidates need a deliberate compatibility decision:

- `StorageService.migrate_from_sqlite` at `backend/storage.py:1555` has no current repository caller and overlaps the explicit migration command. It also uses legacy ownership-free inserts. Retire it after confirming no external scripts rely on it.
- Root `requirements.txt` and `requirements/runtime.txt` duplicate the same list. Consolidate using an include, while retaining the root installation entry point referenced by Docker, README, and `build.sh`.
- `backend/requirements.txt` is a compatibility include, not a second dependency list. Remove only if that install entry point is no longer supported.
- `build.sh` is unused by the checked-in Docker deployment, but could support an external native-build setup. Confirm that setup is retired before deletion.
- `GOOGLE_CLIENT_SECRET` is requested by `render.yaml` but is not consumed by the current ID-token login implementation. Remove the unused configuration requirement if no other deployed integration depends on it.

Do not remove the unused email confirmation API helpers: wire them to the missing screens. `deduplicate_existing_applications` still has a test caller. Keep `Bulletskill.md`, package initializers, tests, screenshots, and historical audit documents. No entire active class or React component was proven safely removable. Ignored scratch/build/cache directories are local artifacts, not shipped source; personal databases, uploads, and secrets are not cleanup candidates.

## Recommended release sequence

1. Fix L01–L05, with regression checks for untrusted HTML, identity linking, connection destinations, bounded reads, and concurrent limits.
2. Complete L06 and demonstrate registration, verification, login, password reset, and old-session invalidation in a staging browser and real inbox.
3. Repair L07–L10, reconcile any already-invalid records, and validate uploads/downloads/deletions plus migration/restore behavior.
4. Resolve frontend defects and dependency drift; perform mechanical cleanup separately so it remains easy to review.
5. Run the production container and PostgreSQL checks, verify deployment settings and backups, then invite a small beta group before broad promotion.

Passing the current unit suites is useful evidence, but it is not sufficient launch approval while the confirmed security and recovery failures remain.
