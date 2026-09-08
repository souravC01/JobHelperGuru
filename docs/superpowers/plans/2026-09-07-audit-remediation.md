# Audit Remediation Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this roadmap task-by-task. Steps use checkbox syntax for tracking. This document authorizes no production rollout by itself.

**Goal:** Resolve the security, correctness, dependency, and redundancy findings in the September 7 audit while preserving user accounts, resumes, and applications.

**Architecture:** Keep the React/FastAPI application and its PostgreSQL/SQLite and R2/local deployment options. Introduce focused boundaries for configuration, outbound HTTP, provider secrets, and file ownership; avoid a framework rewrite. Ship independently reviewable changes with regression coverage and explicit, reversible data migrations.

**Tech Stack:** Python/FastAPI/Pydantic, PostgreSQL/SQLite, React/Vite/Tailwind, pytest; add frontend component tests, Google token verification, and configurable SMTP delivery where specified.

**Spec:** [Security and code audit](D:/Grind/Projects/JobHelperGuru/docs/SECURITY_AND_CODE_AUDIT_2026-09-07.md), reviewed commit `14a58fbe45b18eb53b78ab9a8689323d75e082b4`.

## Global constraints

- Planning only at this stage. Do not implement, install packages, delete files, change infrastructure, or deploy as part of creating this plan.
- At execution, start from the current checkout after checking changes; do not overwrite the audit or user work. Use `security/audit-remediation` and small commits, following the subsequently requested professional Git naming convention. The checked-in Render service auto-deploys; do not merge/push to its deployment branch incidentally.
- First isolate tests. Never run exploit probes against production or use real accounts/files for regressions.
- Preserve both Google and email/password sign-in. Verified email delivery and account recovery must work before enabling the new password-account policy in production.
- Preserve local Ollama access only in explicit local mode. The hosted service must not reach user-selected private/internal addresses.
- Keep existing IDs, owner relationships, dates, notes, and original resume binaries. Never use startup cleanup to delete suspected duplicates.
- Keep production provider keys backend-only. Plan for one-time reauthentication and possible re-entry of browser-only legacy keys; explain this in release notes.
- Add narrow modules only where they create an enforceable security boundary. Do not move all routes/components solely for style.
- Database migrations are additive first, dry-run capable, idempotent, and tested on disposable SQLite and PostgreSQL databases. Back up production before applying them.
- Each defect task follows: failing regression → minimal implementation → focused passing checks → commit. Convert the audit's “defect reproduced” assertions into “defect prevented” assertions.

## Sequence and milestones

| Order | Workstream | Deliverable / exit gate |
|---|---|---|
| 1 | [Safety and data ownership](D:/Grind/Projects/JobHelperGuru/docs/superpowers/plans/2026-09-07-remediation-01-data-safety.md) | Isolated tests; owned application/file operations; no destructive deduplication; safe input and file persistence. |
| 2 | [Identity, secrets, and outbound requests](D:/Grind/Projects/JobHelperGuru/docs/superpowers/plans/2026-09-07-remediation-02-security.md) | Account-linking and account-switch regressions pass; keys stay server-side; network and abuse policies enforced. |
| 3 | [User workflows and output correctness](D:/Grind/Projects/JobHelperGuru/docs/superpowers/plans/2026-09-07-remediation-03-workflows.md) | Resume edits persist; scores/metadata/claims are correct; exports safe; tracker and dates consistent. |
| 4 | [Dependencies, cleanup, and release](D:/Grind/Projects/JobHelperGuru/docs/superpowers/plans/2026-09-07-remediation-04-release.md) | Reproducible audited build; verified unused code removed; migrations/recovery rehearsed; release checklist complete. |

An urgent first patch may contain only test isolation, owner checks, rejection of client file keys, private-destination blocking, and complete logout reset. It must not pretend to resolve the remaining identity, migration, or provider-secret work. There is no requirement to deploy every workstream separately.

## Coverage ledger

| Audit finding | Planned task |
|---|---|
| S1 application read/write ownership | 01 Task 2 |
| S2 unowned objects / filesystem escape | 01 Task 3 |
| S3 AI test SSRF; S4 scraper redirects/iframes | 02 Task 2 |
| S5 unsafe Google/email linking | 02 Task 3 |
| S6 account-switch resume leak | 02 Task 5 |
| S7 spreadsheet formulas | 03 Task 3 |
| S8 default secrets / decryption fallback | 02 Task 1 |
| S9 browser API keys | 02 Task 4 |
| S10 resource abuse | 02 Task 6 |
| D1 dependency advisories | 04 Task 1 |
| D2 test data/cloud isolation | 01 Task 1 |
| B1 distinct postings merged/deleted | 01 Task 2 |
| B2 discarded edits; B3 Markdown | 03 Task 1 |
| B4 null persistence | 01 Task 2 and 02 Task 4 |
| B5 punctuation skills; B6 placeholders; B7 unsupported claims | 03 Task 2 |
| B8 deleted active key remains active | 02 Task 4 |
| B9 broken storage fallback/download | 01 Task 3 |
| B10 password length | 02 Task 3 |
| B11 tenant migration | 01 Task 4, extended by 02 Tasks 3–4 |
| B12 stale tracker totals; B13 dates/defaults; B15 archived Kanban | 03 Task 4 |
| B14 employer graduation window | 03 Task 2 |
| Null bullet/settings inputs; RTF decoding | 02 Task 4 and 03 Tasks 1–2 |
| Unused functions/imports/variables/declarations; duplicate requirements | 04 Task 2 |
| Scratch/build scripts/history/cache candidates | 04 Task 2, retention decisions specified there |

## Validation and release policy

- [ ] Baseline: reproduce the previous 64 deterministic test passes after replacing the unsafe test setup; mock the two previously external tests so the default suite can run offline.
- [ ] Security: cover both owners, empty and non-empty PATCH, unknown/foreign IDs, traversal and symlinks, private IPv4/IPv6 destinations, redirects, iframe hostnames, session changes, and Google/password identity collisions.
- [ ] Persistence: run ownership, uniqueness, profile activation, and migration tests against SQLite and a disposable PostgreSQL database. Do not infer PostgreSQL correctness from SQLite alone.
- [ ] Frontend: test the actual components with mocked requests; include late responses from an old account and save/reload flows. Use a browser smoke check for the full synthetic journey.
- [ ] Dependency checks: inspect full and production-only audit results separately; verify remediation of the specific Vite/esbuild advisories without a forced unreviewed upgrade.
- [ ] Release: prove backup/restore and migration dry-run on a disposable copy; verify SMTP verification/recovery, required secrets, and R2 failure behavior before switching production.
- [ ] Present the tested change set, migration impact, configuration requirements, and rollback procedure for the production rollout decision. No real-data migration, key rotation, or deployment is implied by the request to plan.

## Infrastructure/configuration prerequisites

Email verification uses configurable SMTP transport rather than choosing a new paid provider. Before rollout, configure a sender address, SMTP host/port and authentication, required TLS, and a fixed public application URL. No SMTP credentials are needed to implement or test with a fake transport.

Set explicit deployment mode, strong JWT/encryption secrets, an approved cloud AI-provider host list, and persistent object storage. Existing R2/Neon resources can be retained. Shared rate-limit counters use the existing database, so a Redis service is not required.

## Completion definition

Every S/D/B entry above has its prevention regression or a documented operational validation; no real user data is silently discarded; the full deterministic suite, frontend tests/build, and disposable PostgreSQL checks pass. The report records remaining limitations honestly, including that generated resume claims still require the user's review.

Only documentation is changed by this planning task. Implementation begins under a subsequent execution instruction.
