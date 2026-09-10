# Dependencies, Cleanup, and Release Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` task-by-task. Track steps with checkboxes.

**Goal:** Finish remediation with reproducible dependency checks, conservative cleanup, and a tested release/rollback procedure.

**Architecture:** Keep build and runtime dependencies separate, consolidate manifests without breaking local/Docker commands, and remove only proven unused code. Stage additive schema changes and validate rollout against disposable data before production.

**Tech Stack:** npm/Vite, Python dependency locking/auditing, pytest, frontend tests, Docker, SQLite/PostgreSQL.

**Spec:** [Audit](D:/Grind/Projects/JobHelperGuru/docs/SECURITY_AND_CODE_AUDIT_2026-09-07.md); [roadmap constraints](D:/Grind/Projects/JobHelperGuru/docs/superpowers/plans/2026-09-07-audit-remediation.md). Requires the behavior/security workstreams for release readiness; dependency assessment may start earlier.

## Task 1 - Upgrade audited dependencies and make builds reproducible (D1)

**Files:** `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.js`, `requirements.txt`, `backend/requirements.txt`, `Dockerfile`, `build.sh`, README. Create runtime/development input and lock files under `requirements/`.

**Interfaces:** root `requirements.txt` includes the locked runtime set. `backend/requirements.txt` becomes a compatibility include of the root file so documented local commands keep working. A separate locked development set supplies pytest, frontend-equivalent test tooling for Python, Ruff, and auditing tools without putting them in the runtime image.

- [ ] Record current resolved versions, Node/Python versions and audit output. Requery advisories at execution time; do not assume September 7's vulnerability list remains complete. Distinguish npm production/dev findings and Python audit-tool/bootstrap findings from application runtime dependencies.
- [ ] Select a maintained compatible Vite/plugin/Node combination that removes all listed Vite and esbuild advisories. Read the official migration notes for the chosen major. Update Docker's build-stage Node version only as needed and verify Windows local development. Do not run an unreviewed `npm audit fix --force`.
- [ ] Pin a tested Python runtime baseline compatible with the Python 3.11 production image, or explicitly update both the image and local instructions if the resolved set requires a newer runtime. The audit used Python 3.12; it is not proof of compatibility with 3.11. Resolve runtime and dev requirements for the actual production platform, lock transitive dependencies and hashes, and verify installation from a clean environment.
- [ ] Include the Google verification, frontend test, and RTF parser dependencies introduced earlier. Avoid incompatible upper/lower bounds hidden by open-ended requirements. Update pip/build tooling in the image from an audited version; do not count the audit machine's old pip as a discovered production runtime flaw.
- [ ] Switch Docker/frontend builds to `npm ci`; install the locked runtime requirements. Keep tests/audit tools in development dependencies. Check lockfiles are consistent with manifests and contain no local paths or credentials.
- [ ] Run a clean frontend install, component tests and production build, Python suite under the chosen production runtime, Docker build, `npm audit --json`, `npm audit --omit=dev --json`, and an audit of the locked Python runtime set. Document any remaining finding with exploitability and a specific mitigation; no “zero risk” claim.
- [ ] Commit as `Lock dependencies and upgrade the audited toolchain`.

## Task 2 - Remove verified unused code and consolidate duplicate files

**Files:** existing frontend API client/components, backend service imports, `run.py`, dependency manifests and README. No schema or user-data changes belong in this task.

- [ ] Repeat reference/scope analysis on the post-fix code. Remove `fetchHealth` and deprecated `getExcelExportUrl` only if they still have no caller; keep the backend health routes used by Render.
- [ ] Remove unused default React bindings only where the automatic JSX runtime and lack of `React.*` calls make them redundant. Preserve `main.jsx`'s used React binding and named hooks. Remove the tracker's unused `appliedCount` if the synchronization fix has not already removed it.
- [ ] Remove the audit's ten unused Python imports and unused bindings, rechecking them after earlier changes. Preserve side effects such as `storage.delete_resume(...)` when removing an unused assignment. Remove duplicate optimizer evidence assignments if still present.
- [ ] Remove unused direct `clsx`, `autoprefixer`, and `postcss` declarations only if the updated build still has no direct use. Regenerate the lockfile; transitive PostCSS may legitimately remain. Do not manually delete package directories.
- [ ] Consolidate the identical Python manifests through the compatibility include from Task 1. Keep `build.sh` as a thin supported alternative invoking the canonical dependency/build commands unless the native workflow is explicitly retired; do not delete it simply because Docker does not invoke it.
- [ ] Retain historical design documents, package `__init__.py` files, and `Bulletskill.md`; correct documentation that claims AES-256 for Fernet, universal offline support, or guaranteed verified claims. Retain `ObjectStorageService.get_file` if used by the new local-download path. Remove the unsafe old migration implementation only after its replacement and command references are verified.
- [ ] Do not delete `.env`, databases, uploads, user-authored scratch artifacts, or the audit's evidence as part of automated cleanup. List obsolete scratch/cache files separately; remove only task-created disposable files with verified paths. Cache deletion is optional housekeeping, not a release requirement.
- [ ] Run Ruff's unused-name checks, frontend scope/lint checks, component tests/build, and affected backend tests. No new tests are needed solely to assert an import was removed. Commit as `Remove verified unused code and consolidate manifests`.

## Task 3 - Verify all findings and rehearse data migration/recovery

**Files:** regression suites, `backend/migrate.py`, deployment guide; create `docs/REMEDIATION_VALIDATION.md` containing results and known limitations.

- [ ] Match every S1-S10, D1-D2, B1-B15 and additional input/format issue in the roadmap to a prevention test or specific operational check. Re-run the original attack shapes locally after converting their expected outcomes; “the vulnerability still reproduces” is a failed release gate.
- [ ] Run the entire deterministic backend suite, frontend component suite and production build. Run disposable PostgreSQL tests for ownership, canonical URL uniqueness, counter atomicity, profile activation/deletion, identity uniqueness, and all migrations. Complete one synthetic browser journey: verify account → upload/edit resume → analyze → rank → draft → save → update tracker → export → logout → second account.
- [ ] Rehearse additive schema migration on a disposable copy with mixed legacy records: old ciphertext, unverified email accounts, null-owner files, duplicate posting URLs, missing binaries, and null arrays. Compare pre/post IDs, owners, content, hashes and counts. The dry-run must report conflicts rather than resolve them by deletion.
- [ ] Test backup restoration and interrupted-migration recovery. Keep old columns until the new read/write paths are stable. Ensure any rollback build is compatible with the additive schema and cannot reintroduce the unsafe startup migration. If it cannot safely run, use a controlled maintenance response/forward fix rather than silently restoring vulnerable behavior.
- [ ] Verify mail transport, sender/public URL, secrets, cloud mode, provider-host list, trusted proxy configuration and R2 mode using synthetic checks in staging. No real-data probe, email blast, destructive migration, or credential rotation is permitted as a smoke test.
- [ ] Record exact versions, commands, pass/fail counts, advisory applicability and unresolved limitations. Commit as `Document remediation validation and rollout procedure`.

## Task 4 - Prepare the production rollout decision

- [ ] Prepare a concrete change summary and migration dry-run report, including any unresolved owner/identity conflicts and the user impact of verification or one-time re-login. Explain that original uploaded documents remain original even when extracted text is edited.
- [ ] Confirm restorable database backup and preservation of resume objects before any live migration. Protect backup credentials and contents; never include them in a PR or audit report.
- [ ] Prepare a staged order: provision required settings/mail → additive schema migration → coordinated backend/frontend release → synthetic owned-account smoke checks → monitor errors/auth/downloads → retire old columns only in a later migration. Backend and frontend provider-profile/auth changes must deploy together or have a tested compatibility window.
- [ ] Present the reviewable result for production rollout approval. The planning request alone does not authorize merging to the auto-deploy branch, applying migrations, or changing live credentials. If the user later explicitly authorizes rollout, carry out the prepared steps within that scope without inventing another approval gate.

## Acceptance

The release is ready when every audit item is accounted for, all required local/staging checks pass, no unauthorized cross-user/network/file action succeeds, and migration/recovery is demonstrated. Conditional cleanup items may remain with their retention reason; they are not security blockers.
