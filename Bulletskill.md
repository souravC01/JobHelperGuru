---
name: optimizing-resume-bullets
description: Use when JobHelperGuru drafts, rewrites, reviews, or suggests Work History, internship, or project bullets against a target job description, qualification list, or missing ATS keyword.
---

# BulletSkill — Resume Work History & Project Optimizer

## Purpose

This skill defines how **JobHelperGuru** should create, review, and optimize resume bullets.

It is based on the user's **Resume Guide 2.0** framework:

**Keyword / What + HOW it was used + Result and/or Reason**

The goal is to help users tailor resumes toward a specific job title while clearly separating:

1. **Verified resume claims**
2. **Unverified skill suggestions**
3. **Unverified metric opportunities**

The app may suggest missing skills or stronger metrics, but it must never silently present an unverified claim as verified.

---

# Core Principle

A strong bullet does not merely list keywords.

It shows:

**WHAT / Keyword**
+
**HOW it was used**
+
**RESULT and/or REASON**

Example:

> Investigated defects across REST APIs and Oracle database layers using Postman and SQL to identify root causes and verify fixes.

---

# Claim Classification

Every suggested change must be assigned one of these statuses.

## 1. VERIFIED

Use when the user's resume, project context, uploaded evidence, or confirmed answers support the claim.

Example:

> Secured user workflows with Spring Security, BCrypt password hashing, and session-based authentication to restrict protected actions to authorized users.

This may be inserted into the resume directly.

---

## 2. UNVERIFIED_SKILL

Use when a missing job keyword is not currently supported by the user's evidence but could plausibly be relevant.

The app may show how that keyword **could** be incorporated if the user actually used it.

Example:

Target keyword: `Kafka`

> Implemented Kafka-based event messaging to decouple notification workflows and support asynchronous processing.

Label:

> **Unverified skill suggestion — confirm that Kafka was actually used before adding this bullet.**

The app must not silently treat this as factual.

---

## 3. UNVERIFIED_METRIC

Use when the bullet could benefit from quantified impact but no verified number is available.

Use a placeholder, not a fabricated realistic-looking number.

Good:

> Automated Maven build and test validation through GitHub Actions CI, reducing deployment validation time by **[X%]**.

Label:

> **Unverified metric — replace [X%] with a value you can support.**

Bad:

> Reduced deployment time by 37%.

unless the user actually supplied evidence supporting 37%.

---

## 4. VERIFIED_DERIVED_METRIC

Use when JobHelperGuru can calculate a metric from user-provided values.

Example evidence:

- Before: 30 minutes
- After: 10 minutes

The app may calculate:

> Reduced validation time by approximately 67%.

Because the source numbers were supplied by the user.

---

# Resume Export Rule

The optimizer UI may display:

- Verified claims
- Unverified skill suggestions
- Unverified metric suggestions

However:

**Only verified or explicitly user-confirmed claims should be eligible for final resume export.**

An unverified suggestion may become verified after the user confirms it.

Example flow:

`UNVERIFIED_SKILL`
→ user clicks **Yes, I used this**
→ status becomes `VERIFIED`
→ eligible for export

If the user rejects it, remove it from export consideration.

---

# Required Inputs

The optimizer should accept as much of the following as available:

```json
{
  "target_job_title": "Java Developer",
  "section_type": "project",
  "target_keyword": "Kafka",
  "keyword_priority": "required",
  "matched_keywords": ["Java", "Spring Boot", "Docker"],
  "missing_keywords": ["Kafka", "Kubernetes"],
  "existing_bullets": [
    "Built and modernized a Java marketplace..."
  ],
  "resume_wide_keyword_coverage": {
    "Java": "strong",
    "Spring Boot": "strong",
    "Kafka": "missing"
  },
  "evidence_context": {
    "verified_facts": [
      "Used Spring Boot",
      "Used PostgreSQL",
      "Used GitHub Actions"
    ],
    "verified_metrics": [],
    "source_text": "Optional raw resume or project context"
  },
  "role_or_project_metadata": {
    "name": "YU Bazaar",
    "company": null,
    "job_title": null
  }
}
```

---

# Work History Rules

## 1. First bullet = Job Summary

The first Work History bullet must summarize the overall job.

Requirements:

- Explain the job simply enough for a non-industry reader to understand.
- Prefer wording simple enough for an 8-year-old to broadly understand.
- Include approximately **3 important target-job keywords** when natural.
- Do not cram the summary with every keyword.
- Write in **past tense**, even for a current role.
- Target approximately **3 resume lines maximum**.
- Use no more than **1 period**.

### Summary pattern

> Supported / Developed / Helped [simple description of work] using [Keyword 1], [Keyword 2], and [Keyword 3] to [simple purpose/result].

Example:

> Supported the development, testing, and release of government applications using Java, REST APIs, and SDLC practices to deliver reliable public services.

The summary bullet should explain the job, not every accomplishment.

---

## 2. Evidence bullets = What + How + Result/Reason

Every Work History bullet after the summary should answer:

### WHAT
What qualification, technology, responsibility, or keyword was used?

### HOW
What did the candidate actually do with it?

### RESULT / REASON
What happened because of the work, or why was the work performed?

### Pattern

> [Action verb] [keyword/qualification] by/using [how] to/while [result or reason].

Examples:

> Implemented Java application-logic changes to update business rules and workflows while resolving functional defects and business change requests.

> Investigated defects across REST APIs and Oracle database layers using Postman and SQL to identify root causes and verify fixes.

> Built and executed 500+ automated and manual test cases using Selenium to validate functional and regression requirements before release.

---

## 3. Work History bullet count

For each role:

- Minimum: **3 bullets total**
- Maximum: **8 bullets total**
- Total includes the summary bullet

Prefer rewriting an existing bullet over adding another when the role is already near the limit.

---

# Project Rules

A project is work not paid for by a company.

If the candidate was paid by a company for the work, treat it as Work History.

For Projects:

- **Do not include dates.**
- Maximum **3 bullets per project**.
- Prioritize projects by relevance to the target job title.
- Write in **past tense**.
- Target approximately **3 resume lines maximum**.
- Use no more than **1 period per bullet**.
- Every bullet follows:
  **Keyword / What + HOW + Result and/or Reason**

---

# Recommended 3-Bullet Project Structure

## Bullet 1 — What was built + purpose

Explain the product simply and include the strongest primary qualification.

Example:

> Built a Spring Boot application that simulated employee access changes before they occurred, helping teams identify affected workflows and evaluate safer replacement options.

## Bullet 2 — Technical depth

Show architecture, domain logic, security, algorithms, OOP, messaging, or another high-value qualification.

## Bullet 3 — Complementary engineering evidence

Use infrastructure, cloud, CI/CD, testing, persistence, deployment, or another useful qualification.

When a project already has 3 bullets, revise or replace a bullet instead of adding a fourth.

---

# Keyword Integration Strategy

## Step 1 — Respect keyword priority

Priority order:

1. Required skills
2. High-priority ATS keywords
3. Preferred skills
4. Nice-to-have terms

Do not distort a strong bullet to chase a low-priority keyword.

---

## Step 2 — Check resume-wide coverage

Before changing a bullet, determine whether the keyword is already:

- `strong`
- `adequate`
- `weak`
- `missing`

If it is already `strong`, usually return:

`no_change_needed`

unless the new use demonstrates meaningfully different evidence.

---

## Step 3 — Classify the keyword

For each missing keyword, determine:

### `direct`
Exact evidence exists.

Example:
Keyword: Spring Security  
Evidence: user says Spring Security was used.

### `equivalent`
A genuinely equivalent wording exists.

Example:
Keyword: RESTful APIs  
Evidence: REST APIs.

### `related_not_equivalent`
Evidence is related but does not prove the target term.

Example:
Keyword: Hibernate  
Evidence: Spring Data JPA.

Do not silently upgrade the claim.

You may show an unverified suggestion if useful.

### `unsupported`
No evidence supports the keyword.

Do not ignore it.

Instead:
- clearly show that it is missing,
- offer a hypothetical bullet showing how it could be incorporated,
- label it `UNVERIFIED_SKILL`,
- require confirmation before export.

---

# Missing Keyword Behavior

When a target keyword is not verified:

Do **not** simply return "unsupported" and stop.

Return:

1. The missing keyword
2. Why it is currently unverified
3. A possible bullet showing how it could be used
4. The exact assumption behind the suggestion
5. A confirmation prompt

Example:

```json
{
  "target_keyword": "Kafka",
  "status": "unverified_skill",
  "suggested_bullet": "Implemented Kafka-based event messaging to decouple notification workflows and support asynchronous processing.",
  "assumption": "The project used Kafka for asynchronous event communication.",
  "requires_confirmation": true,
  "warning": "Confirm that Kafka was actually used before adding this to the resume."
}
```

---

# Bullet Selection Algorithm

When the optimizer receives a target keyword and multiple bullets:

1. Extract factual concepts from each bullet.
2. Compare each bullet with the target keyword.
3. Identify which bullet is the most natural place for that qualification.
4. Score candidates by:
   - direct evidence,
   - relevance to the target job,
   - ability to preserve What + How + Result/Reason,
   - low duplication,
   - low increase in length.
5. Select the highest-scoring bullet.

If no current bullet naturally fits:
- propose replacing the least relevant bullet, or
- suggest a hypothetical bullet,
- label it unverified if the skill itself is unverified.

Never choose a bullet only because it has spare space.

---

# Rewriting Rules

A verified rewrite should:

- preserve factual meaning,
- integrate the target keyword naturally,
- use a clear action verb,
- state HOW it was used,
- include a result or reason,
- stay concise,
- avoid redundant technology lists.

Example:

Weak:

> Worked with APIs and SQL.

Better:

> Validated REST API data flows using Postman and SQL to identify backend integration issues and verify fixes.

---

# Unverified Skill Suggestion Rules

JobHelperGuru is allowed to suggest missing technologies or skills even when they are not currently verified.

However, the suggestion must be visually and structurally separated from verified resume content.

Every unverified suggestion must include:

- `status: unverified_skill`
- target keyword
- proposed bullet
- assumption
- confirmation required
- warning that it should not be exported until confirmed

Example UI:

**Missing keyword: Kafka**

**Possible integration — Unverified**

> Implemented Kafka-based event messaging to decouple notification workflows and support asynchronous processing.

**Assumption:** Kafka was used to connect application services.

⚠️ Confirm before adding to your resume.

---

# Unverified Metrics Policy

If a verified metric is unavailable, do not ignore the opportunity.

Instead:

1. Keep the verified bullet without a metric.
2. Offer a metric-enhanced alternative using placeholders.
3. Label it `UNVERIFIED_METRIC`.

Example:

Verified:

> Automated Maven build and test validation through GitHub Actions CI to catch integration failures before deployment.

Metric-enhanced suggestion:

> Automated Maven build and test validation through GitHub Actions CI, reducing deployment validation time by **[X%]**.

Label:

> **Unverified metric — replace [X%] with a value you can support.**

Allowed placeholders include:

- `[X%]`
- `[N users]`
- `[N requests/day]`
- `[N minutes]`
- `[N hours/week]`
- `[N releases]`
- `[N test cases]`
- `[N defects]`

Do not create fake-looking numbers such as `37%`, `2,500 users`, or `45ms` without evidence.

---

# Metric Discovery

When possible, JobHelperGuru should ask users for facts that can produce a real metric.

Example prompts:

- How long did this process take before automation?
- How long did it take afterward?
- Approximately how many users used the system?
- How many releases did you support?
- How many test cases did you create?
- How many defects did you identify?
- How many requests or records were processed?

If the user supplies enough values, calculate the metric and classify it as:

`VERIFIED_DERIVED_METRIC`

---

# Alternative Generation

When the UI asks for 2–3 suggestions:

Return **2–3 alternative versions of the same selected bullet**, not 2–3 additional bullets.

Recommended variants:

### Candidate A — ATS-focused
Prioritize natural inclusion of the target keyword.

### Candidate B — Concise
Minimize length while preserving What + How + Result/Reason.

### Candidate C — Technical/result-focused
Emphasize implementation depth or outcome.

Do not invent different achievements just to make the alternatives different.

---

# Output Contract

Return structured JSON suitable for JobHelperGuru's AI engine.

## Verified rewrite example

```json
{
  "status": "rewritten",
  "target_keyword": "Spring Security",
  "claim_status": "verified",
  "selected_bullet_index": 1,
  "selection_reason": "The authentication bullet directly supports Spring Security.",
  "alternatives": [
    {
      "bullet": "Secured user and listing workflows with Spring Security, BCrypt password hashing, session-based authentication, OTP verification, password-reset links, and owner-only authorization for protected actions.",
      "what": "Spring Security",
      "how": "Protected authentication and listing workflows",
      "result_or_reason": "Restricted protected actions to authorized users",
      "claim_status": "verified",
      "requires_confirmation": false
    }
  ],
  "validation": {
    "past_tense": true,
    "one_sentence": true,
    "one_period_max": true,
    "what_how_result_present": true,
    "keyword_stuffing": false
  }
}
```

---

# Unverified Skill Output Example

```json
{
  "status": "suggested",
  "target_keyword": "Kafka",
  "claim_status": "unverified_skill",
  "selected_bullet_index": 2,
  "alternatives": [
    {
      "bullet": "Implemented Kafka-based event messaging to decouple notification workflows and support asynchronous processing.",
      "what": "Kafka",
      "how": "Published and consumed asynchronous application events",
      "result_or_reason": "Decoupled notification processing from user-facing workflows",
      "claim_status": "unverified_skill",
      "requires_confirmation": true,
      "assumption": "Kafka was actually used for asynchronous event communication."
    }
  ],
  "warnings": [
    "Kafka is not verified in the current resume or evidence.",
    "Confirm this implementation before adding it to the exported resume."
  ]
}
```

---

# Unverified Metric Output Example

```json
{
  "status": "suggested",
  "claim_status": "unverified_metric",
  "verified_bullet": "Automated Maven build and test validation through GitHub Actions CI to catch integration failures before deployment.",
  "metric_alternative": {
    "bullet": "Automated Maven build and test validation through GitHub Actions CI, reducing deployment validation time by [X%].",
    "placeholder": "[X%]",
    "requires_confirmation": true
  },
  "follow_up_question": "Do you know approximately how much validation time was saved?"
}
```

---

# Allowed Status Values

## `rewritten`
A verified rewrite was produced.

## `suggested`
An unverified skill or metric suggestion was produced.

## `no_change_needed`
The keyword is already strongly represented or the original bullet is better.

## `manual_review`
The relationship between the keyword and evidence is ambiguous.

## `confirmed`
A previously unverified suggestion was explicitly confirmed by the user.

## `rejected`
The user rejected the unverified suggestion.

---

# Resume-Wide Review Mode

Before finalizing multiple changes, review the entire selected resume.

Check:

- Which required qualifications are already strong?
- Which are genuinely missing?
- Which have equivalent wording?
- Which are only related but not equivalent?
- Which missing keywords deserve hypothetical suggestions?
- Which suggestions remain unverified?
- Is the same keyword repeated unnecessarily?
- Are important qualifications visible early?
- Are Work History roles within 3–8 bullets?
- Are Projects capped at 3 bullets?
- Does each bullet contain What + How + Result/Reason?

A resume should not be changed merely to maximize raw keyword overlap.

---

# Offline / Heuristic Fallback

When the AI endpoint is unavailable, the heuristic layer may:

- identify exact keyword matches,
- identify likely equivalent wording,
- rank bullets by overlap,
- flag potential bullets for optimization,
- detect keyword repetition,
- identify missing keywords.

The heuristic layer may also provide **template-level** suggestions such as:

> "Consider adding [Kafka] to a messaging/event-processing bullet if you actually used it."

But it should not silently classify an unverified skill as factual.

---

# Final Review Checklist

Before returning any bullet:

- [ ] Target job title is known when available.
- [ ] Section type is known.
- [ ] Keyword priority is known when available.
- [ ] Claim status is explicit.
- [ ] Verified claims are supported.
- [ ] Unverified skills are clearly labeled.
- [ ] Unverified metrics use placeholders.
- [ ] No realistic-looking fake metric was invented.
- [ ] WHAT is clear.
- [ ] HOW is clear.
- [ ] Result or Reason is clear.
- [ ] Bullet is past tense.
- [ ] Bullet is one sentence.
- [ ] Bullet uses no more than one period.
- [ ] Bullet is concise enough for roughly 3 resume lines.
- [ ] Keyword is not unnecessarily duplicated.
- [ ] Work History summary rules are preserved.
- [ ] Work History remains within 3–8 bullets.
- [ ] Projects remain at 3 bullets maximum.
- [ ] Suggestions are alternatives, not extra bullets.
- [ ] Only verified or user-confirmed claims are marked export-ready.

---

# Final Principle

JobHelperGuru should not ignore missing keywords.

It should distinguish between:

**What the user has already proven**
and
**what could strengthen the resume if the user truly has that experience.**

Verified:

> Developed persistence infrastructure using Spring Data JPA, PostgreSQL, and Docker with Flyway-managed migrations to support reliable database behavior.

Unverified skill suggestion:

> Implemented Kafka-based event messaging to decouple notification workflows and support asynchronous processing.

Unverified metric suggestion:

> Automated CI validation, reducing deployment validation time by **[X%]**.

**Show the qualification, show how it was used, show why it mattered, and clearly tell the user which parts still need confirmation.**
