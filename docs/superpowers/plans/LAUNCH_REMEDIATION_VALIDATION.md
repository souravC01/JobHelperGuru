# Public launch remediation validation

Branch: `launch-readiness`. Starting commit: `c54bb1f`.

The implementation follows `docs/superpowers/plans/2026-09-11-public-launch-remediation.md` sequentially. Production deployment, real-data repairs, outbound email delivery, and promotional posts are not part of local verification.

## Progress

| Task | State | Evidence / remaining gate |
| --- | --- | --- |
| 1. Safe printing | Code and regression tests complete | Vector DOM print container implemented; selectable text in print preview verified. |
| 2. Google identities | Code and regression tests complete | Official Google auth verification library enforced; unverified identity collision blocked. |
| 3. Outbound requests | Code and regression tests complete | PinnedTransport and SSRF private IP blocker verified across 44 tests. |
| 4. Atomic limits | Code and regression tests complete | Token bucket rate limiting and ResourceLeases concurrency manager verified. |
| 5. Resume lifecycle | Code and regression tests complete | Atomic 10-resume quota lock, idempotent S3 delete, and RFC 5987 Unicode filename downloads. |
| 6. Account recovery | Code and regression tests complete | BrevoEmailTransport transactional email, SPAStaticFiles deep-link fallback, and AuthLinkPage form. |
| 7. Data validation/repair | Code and regression tests complete | repair_data.py CLI and schema null status validator verified with regression suite. |
| 8. Migration | Code and regression tests complete | migrate.py PostgreSQL URL handling, user_settings 3-column format, and ledger tracking verified. |
| 9. Frontend correctness | Code and regression tests complete | Duplicate job URL inline detection and responsive horizontal-scroll Kanban board layout verified. |
| 10. Dependencies/cleanup | Code and regression tests complete | Upgraded vitest to 4.1.11; npm audit reports 0 vulnerabilities; all Python files cleanly parsed. |
| 11. Production runbook | Complete | PUBLIC_LAUNCH_RUNBOOK.md created with environment config, data operations, and verification checklist. |
| 12. Final verification | Complete | Full backend suite: 205 passed (100% green); full frontend suite: 31 passed across 12 files (100% green); production build passed. |

## Checks performed

- Full backend test suite: **205 passed** in 30.44s.
- Full frontend test suite: **31 passed across 12 files**.
- Frontend production build: **Passed in 5.43s** with zero errors or warnings.
- Frontend vulnerability audit: **0 vulnerabilities** (`npm audit` clean).
- Zero em-dash compliance: **0 em-dashes across all code, tests, and documentation**.
- Git metadata neutrality: **All commits strictly neutral**.

## Implementation decisions

- Retained the user's requested branch and checkout; did not create a separate worktree or change the branch name.
- Replaced HTML string printing with DOM text nodes and removed popup opener access.
- Switched Google verification to the official library with bounded certificate requests; removed fallback client IDs. Non-authoritative Google email collisions require password sign-in/recovery. New such accounts receive no session until application mailbox verification.
- Used a connection-level httpcore2 backend behind httpx2, preserving normal TLS verification. Pinned OpenAI 3.8.0, httpx2 2.12.0, and httpcore2 2.12.0 because the pool adapter depends on their tested interface.
- Removed the active curl impersonation bypass and routed Workday's separate requests path through the protected client. Some anti-bot sites may require the existing paste-text fallback.
- Enforced bounded raw/decoded bodies and deadlines down to network reads. Local loopback AI is still an explicit local-mode exception.

This record is a progress log, not launch approval. No production or beta verification has been claimed.
