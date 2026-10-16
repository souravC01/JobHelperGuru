# Task 10 browser verification

Date: 2026-10-16. Status: **in progress**. Tests use the actual app and authenticated API with synthetic data and a fake provider on localhost. No paid AI request was made. The user completed sign-in; no authentication dialog was automated.

## Completed browser checks

| Scenario | Observed result |
|---|---|
| Correct incomplete saved text | Explicit completeness confirmation cleared the old warning; resume became Ready for job comparison. |
| Paste/analyze full JD | Synthetic JD produced backend Skill fit results in the actual UI. The fake provider intentionally extracts only Python for this test. |
| Scores and ties | Three positive resumes showed 100/100, rank 1, tied-top-fit labels and explicit-choice guidance. |
| Explicit selection | Choosing Version A displayed Selected for tailoring. |
| Edit and rerank | Replacing Version A text with Rust updated it to 0/100; old tailoring selection disappeared while the other resumes retained their ties. |
| Readable DOCX upload | Synthetic readable.docx uploaded and became Ready for job comparison. |
| Partial PDF upload | Synthetic partial.pdf retained its unreadable page 2 warning and needs-review status. |
| Incomplete batch | Presence of the partial PDF removed all batch ranks and top-fit assignment; no false zero for the incomplete resume. |
| Extraction failure and retry | Fake provider's incomplete Java-or-Python interpretation caused a visible extraction error and cleared previous scores; retry stayed unscored. No offline fallback dialog appeared. |
| Recover after failure | Restoring the valid JD cleared the extraction error; the batch truthfully remained incomplete because of the partial PDF. |

## Remaining checks

- Switch job while an older extraction is deliberately delayed.
- Switch provider while an older extraction is deliberately delayed.
- Verify flag rollback in the browser.
- Older source-less job: retain existing component coverage; confirm whether a current browser path can load such an old object (App currently creates currentJob only through analysis).

A second isolated fixture is prepared at 127.0.0.1:8766 with controlled delays, two synthetic provider profiles and a test-only flag toggle. It needs manual sign-in under the computer-use skill before the remaining UI checks. Controls affect only that scratch fixture; production configuration is unchanged.

## Limits

This walkthrough is functional UI verification with deliberately simple fake extraction. It does not validate live model output, unseen-document accuracy or cold extraction performance. Existing 526 backend/94 frontend/build results are separate automated evidence. No release activation, push or PR occurred. Browser cases above are new observations, not inferred from component tests.


## Separate Browser Use service attempt — 2026-10-16

At the owner's request, used the newly available Browser Use controller. This controls a separate browser session; it is not the embedded browser tab inside the ChatGPT app. Earlier wording conflated these two surfaces. The first attempt found the fixture stopped. Restarted the isolated fixture and confirmed it locally returned HTTP401 (authentication required) at `http://127.0.0.1:8766/api/features`. Retried the exact app URL in the same browser session; the separate browser session still returned `ERR_CONNECTION_REFUSED` at `http://127.0.0.1:8766/app`.

That separate Browser Use session could not reach this PC's local test service in the current setup. This result does not establish whether the ChatGPT app's embedded browser can reach localhost. The app reports an embedded tab pointing to http://127.0.0.1:8766/app, but no direct embedded-tab controller is exposed in the current toolset. No sign-in or additional product check completed in that browser, no matching-provider call was made, and no public tunnel, external preview or production instance was used. The earlier local-Chrome observations remain valid; delayed job/provider switching and browser rollback remain pending. A browser-accessible authorized test preview is needed to finish those cases using this controller.


## Pre-push verification — 2026-10-16

The final client diff review exposed an update-only `source_reviewed` field accidentally referenced by `addResume` without a binding. A new client regression reproduced the ReferenceError. Removed that field from creation requests while preserving it on reviewed text updates. The regression and full frontend suite pass: **95 tests**, production build passed. Backend code remains the version verified by the **526-test** run. Diff whitespace check passes.

The owner authorized pushing the existing feature branch without a PR. This publication does not mark Task 10 complete or authorize activation. The remaining browser cases and deferred unseen-document validation stay open; no scratch fixtures, synthetic credentials, local databases or original private source documents are included.
