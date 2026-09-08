# Identity, Secrets, and Network Security Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` task-by-task. Track steps with checkboxes.

**Goal:** Close identity, account-switch, secret-storage, outbound-request, and abuse-control gaps.

**Architecture:** Keep existing auth and AI routes but move configuration, secret profiles, and outbound HTTP policy behind narrow services. Add verified identity and session-version records using the existing database. SMTP is configurable and external services are mocked in tests.

**Tech Stack:** FastAPI, JWT/bcrypt, Fernet, Google verification library, standard-library SMTP, React component tests, SQLite/PostgreSQL.

**Spec:** [Audit](D:/Grind/Projects/JobHelperGuru/docs/SECURITY_AND_CODE_AUDIT_2026-09-07.md); [roadmap constraints](D:/Grind/Projects/JobHelperGuru/docs/superpowers/plans/2026-09-07-audit-remediation.md). Requires workstream 01's isolated fixtures and ownership contracts.

## File boundaries

Create `backend/config.py`, `backend/services/outbound_http.py`, `backend/services/email_service.py`, `backend/services/provider_profiles.py`, and `backend/services/rate_limiter.py` for their named responsibilities. Modify existing auth, AI, scraping, encryption, storage, model, settings, and app files. Put narrow backend regressions in `tests/test_security_config.py`, `test_outbound_http.py`, `test_identity_linking.py`, `test_provider_profiles.py`, and `test_rate_limits.py`. Add `frontend/src/test/setup.js` and component tests beside App/settings/auth components.

## Task 1 — Fail closed on deployment secrets (S8)

**Interfaces:** `load_config() -> AppConfig` reads `APP_MODE` (`local`, `test`, `production`; default `production`) and returns public app URL, allowed provider hosts, secrets, and resource limits. Production startup calls this before service initialization. `decrypt_value` raises a typed decryption error for encrypted records that cannot be decrypted.

- [ ] Add tests that production refuses missing/default/short JWT and encryption secrets, missing Google audience configuration, and local-only network flags. Test that explicit local/test mode can run using generated non-public secrets. No hardcoded signing key should remain usable.
- [ ] Consolidate environment loading in `backend/config.py`. Set `APP_MODE=production` in Docker/Render, `APP_MODE=test` before test collection, and `APP_MODE=local` in the documented local setup. Absent mode defaults to production and therefore fails without required secrets. Generate local secrets only once into a protected, ignored local configuration file, preserving configured values; never regenerate the encryption key at each restart. Tests alone may use disposable per-run secrets.
- [ ] Version encrypted settings. Preserve the existing SHA-256/Fernet derivation for reading existing ciphertext; do not reinterpret the same configured secret as a different key format. Convert known legacy plaintext only in the explicit migration, never by catching arbitrary decryption exceptions.
- [ ] Test wrong-key, corrupted-token, whitespace, legacy plaintext migration, and valid old ciphertext. Decryption failure gives a safe “re-enter provider key” error and never passes ciphertext as an API credential. Do not log decrypted keys or rotate working production keys as incidental cleanup.
- [ ] Run `python -m pytest tests/test_security_config.py tests/test_encryption.py tests/test_storage_encryption.py -q`; update env templates and deployment guide. Commit as `Validate deployment secrets and encrypted settings`.

## Task 2 — Use one outbound request policy for all user-selected destinations (S3, S4)

**Interfaces:** `OutboundPolicy(mode, allowed_provider_hosts, local_ai_hosts)` and `SafeHttpClient.request(method, url, *, policy, timeout, max_bytes, **kwargs)` enforce scheme, hostname, port, resolved-address, redirect, and response-size rules. The OpenAI SDK transport and scraper transports consume this same policy; no bypass through curl or iframe helpers.

- [ ] Port the audit's intercepted-loopback, redirect, and iframe probes into prevention tests. Include private IPv4/IPv6, IPv4-mapped IPv6, link-local/metadata addresses, hostname suffix tricks, userinfo, DNS answers containing mixed public/private IPs, and a DNS-change test between validation and connection.
- [ ] Cloud AI profiles allow HTTPS on port 443 only to administrator-configured exact hostnames. Cloud scraping may visit arbitrary public HTTPS/HTTP pages on approved web ports but rejects every non-global address. Reject URL credentials and ambiguous host syntax. Local mode permits configured loopback AI hosts only; it never enables private-address scraping by default.
- [ ] Disable automatic redirects at the underlying client; revalidate each hop, limit to five, reject HTTPS downgrade for credential-bearing calls, and never forward Authorization to a different host. Validate iframe parsed hostnames against known ATS hosts, not substring matches.
- [ ] Enforce the check at connection time: connect only to an approved resolved address while retaining the original hostname for TLS verification/SNI. A check-then-resolve-again implementation does not pass the DNS-change test. If a transport cannot enforce this, remove that transport path rather than leaving an exception.
- [ ] Require `get_current_user` on `/api/settings/test-ai`; test the route returns 401 before creating any network client for anonymous requests. Inject the safe transport into the SDK. Bound scraper response bodies to 2 MiB and give the entire fetch/redirect attempt a 30-second deadline.
- [ ] Run `python -m pytest tests/test_outbound_http.py tests/test_scraper.py tests/test_ai_engine.py -q`. Keep a separate opt-in compatibility smoke test for public ATS sites and local Ollama. Commit as `Enforce outbound network policy on every fetch`.

## Task 3 — Verify email ownership and bind Google identities safely (S5, B10)

**Interfaces:** add user verification state and `session_version`; add unique `(issuer, subject)` identities. Add `POST /api/auth/verify-email/request`, `POST /api/auth/verify-email/confirm`, and password-recovery request/confirm routes. Registration creates a pending account and returns no authenticated data-access token. `EmailService.send_verification(recipient, link)` uses a fake transport in tests and configured SMTP in production.

- [ ] Write the pre-hijacking regression: attacker registers an unverified victim email; the real Google identity cannot inherit the attacker's still-valid password/session. Test `email_verified=false`, changed third-party email ownership, wrong audience, expiry, replay, and identity-subject collision. Keep Google signature verification mocked only at the library boundary.
- [ ] Verify Google tokens with the maintained Google verification library, configured audience, issuer and expiry. Look up by issuer/subject. A matching email alone never links an identity. Use verification/recovery for existing-email collisions, then revoke old sessions and any unverified password credential before linking. Non-authoritative third-party Google emails require email proof; do not treat `email_verified=true` alone as proof Google currently controls that mailbox.
- [ ] Implement 32-byte random verification/recovery tokens, store only their hashes, expire after 30 minutes, consume once transactionally, and invalidate prior outstanding tokens after success. Requests return a generic response to reduce account enumeration. Build links from a configured public app URL, never the request Host header. Never log tokens or return them from production APIs.
- [ ] Existing unverified password accounts receive a controlled verification/recovery path; do not automatically mark all legacy users verified. Configure and test mail delivery before enforcing the policy on production. Data remains stored during verification. Add `session_version` to JWTs and require a match on authenticated requests; recovery, credential changes, and security-sensitive linking increment it. Existing tokens without the version require one re-login.
- [ ] For bcrypt, validate new passwords as at least 8 characters and at most 72 UTF-8 bytes; reject overlength input with 422 before hashing. Never silently truncate a new password. Provide recovery for legacy users with overlength passwords; document the boundary in the form. Test ASCII and multibyte input, wrong passwords, and normal legacy bcrypt hashes.
- [ ] Update `AuthModal.jsx` and the API client for pending verification, confirmation, resend and recovery states. Add synthetic component tests for success, expired link, resend limit, and recovery. Do not send real emails while testing.
- [ ] Run `python -m pytest tests/test_identity_linking.py tests/test_auth_api.py tests/test_auth_service.py -q` and auth component tests. Extend migration dry-run/rollback coverage. Commit as `Verify account ownership and secure identity linking`.

## Task 4 — Store provider secrets only on the server (S9, B8, settings validation)

**Interfaces:** separate internal `ProviderProfileSecret` from public metadata `{id, name, api_base_url, model_name, has_api_key, key_suffix, is_active}`. Introduce owner-scoped profile create/edit/delete/activate endpoints under `/api/settings/profiles`. `get_ai_engine(user_id)` resolves the active secret internally. Public settings include `active_profile_id`, `use_offline_mode`, and `default_follow_up_days`, not decrypted keys or legacy secret JSON.

- [ ] Add tests asserting that GET settings/profile responses never include a supplied synthetic secret and that another user cannot read, activate, edit, test, or delete the profile. Confirm an omitted replacement key keeps the existing secret; explicit deletion is a distinct operation, not an ambiguous null update.
- [ ] Migrate each user's encrypted `saved_keys` and active key into owned profile rows using stable migration IDs. Preserve working provider URLs/models; quarantine invalid URLs under the outbound policy for user correction. Deduplicate within one user only. Do not move any global key into a new user's profile.
- [ ] Make anonymous job analysis use the heuristic engine without a provider secret. Legacy global settings must not give public requests access to an owner's billable credentials; retain them only in migration backup until explicitly resolved.
- [ ] Make deletion of an active profile transactional: remove/deactivate it, clear the active reference, and select offline mode. Do not silently activate another billed provider. Activating a profile must atomically set active reference and online mode.
- [ ] Rewrite SettingsModal to send a secret only when creating/replacing it. Use metadata for listing and profile IDs for activation/testing. Remove plaintext localStorage persistence and purge legacy key caches. Server records are authoritative; browser-only keys require the owning user to re-enter them. Never import another browser account's cache into the current account.
- [ ] Reject null/invalid mode, default-days, URL and model fields before storing; range-check default follow-up days to 1–90. Empty “new key” input cannot erase a working secret. Keep UI errors free of provider response bodies that may contain credentials.
- [ ] Run `python -m pytest tests/test_provider_profiles.py tests/test_settings_isolation.py -q` and SettingsModal tests. Verify delete/reopen does not resurrect a profile. Commit as `Keep provider keys server-side and deactivate deletions`.

## Task 5 — Reset identity-bound frontend state and ignore stale requests (S6)

**Files:** `App.jsx`, API client, optimizer/outreach/settings/auth components, `App.test.jsx`. Introduce a keyed account workspace inside the existing app file if needed; keep the public analyzer and current navigation structure.

**Interface:** account identity/generation determines the lifetime of resumes, applications, current job, selected resume, adopted skills, modal results/errors, and pending retries. API requests capture their originating token/identity and must not change the current session after identity changes.

- [ ] Port the actual-component account-switch probe to Vitest/React Testing Library. Cover A → logout → B with zero resumes; A's modal open during expiry; and a delayed A response arriving after B logs in. Add a stale 401 case that must not log out B.
- [ ] On logout, expiry, or identity change, close all private modals and discard private state/results/retry closures. Set selection to the first currently owned resume or null on every resume-list change, including deletion of the selected resume.
- [ ] Abort old requests where possible and also guard response application by identity generation. Key private components by user ID so their internal hooks cannot retain old account data. Guard 401 handling with the token that originated the response.
- [ ] Verify new requests use B's token and never include A's resume/content; ensure an empty vault offers upload instead of inventing a selected resume. Tests use fake data only.
- [ ] Run frontend App, optimizer, outreach and settings tests. Commit as `Clear account state and reject stale responses`.

## Task 6 — Bound public requests and stored resources (S10)

**Interfaces:** `RateLimiter.check(bucket, subject, *, limit, window_seconds)` uses atomic counters in the existing database and returns retry timing. Limits are configurable through AppConfig, not user settings. Add an ASGI body-size limiter that counts streamed bytes rather than trusting Content-Length.

- [ ] Write fake-clock tests for exact limit, expiry, atomic concurrent increments, user separation and 429 `Retry-After`. IP rate limiting must derive addresses through a trusted-proxy configuration; never trust arbitrary forwarded headers. No real load attack is required.
- [ ] Initial limits: login attempts 10/minute/IP and 10/minute/email hash; registration and verification/recovery requests 5/hour/IP and 3/hour/email hash; anonymous analysis 10/minute/IP; authenticated AI operations 30/minute/user with at most two in flight. These are configuration defaults, not permanent product promises.
- [ ] Add streamed JSON body cap 1 MiB and multipart cap 12 MiB, individual file cap 10 MiB, extracted text cap 100,000 characters, at most 100 PDF pages, and DOCX decompressed total cap 50 MiB. Reject before expensive parsing wherever possible and return 413/422, not unhandled 500.
- [ ] Limit new storage to 30 resumes and 100 MiB of binary uploads per user, enforced transactionally; accounts already above a limit keep their data and can delete/export but must reduce usage before new uploads. Bound resume arrays/keyword lists and reject invalid fields without truncating silently.
- [ ] Add stale-counter cleanup, deterministic clock injection and SQLite/PostgreSQL concurrency checks. Test limits with synthetic small thresholds rather than creating large real files.
- [ ] Run `python -m pytest tests/test_rate_limits.py tests/test_api.py tests/test_document_parser.py -q`; document configurable limits. Commit as `Bound request rates and document resource usage`.
