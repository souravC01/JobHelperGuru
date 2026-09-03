# LinkedIn Corporate Modern UI Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the entire JobHelperGuru frontend from the "Kinetic Noir" dark aesthetic to the "LinkedIn Corporate Modern" design system featuring high-contrast white surfaces, 1px `#e0e0e0` borders, `#0a66c2` primary blue accents, `#b24020` rust alerts, and zero em-dashes.

**Architecture:** Replace the global theme variables in `index.html` and `index.css` with LinkedIn Corporate Modern tokens. Refactor the application shell and header in `App.jsx`, followed by systematically migrating each component (`JobAnalyzer`, `SkillsMatrix`, `ATSKeywordBank`, `ResumeFitRanker`, `ApplicationsTracker`, `KanbanBoard`, `BulletOptimizerModal`, and modals) to the new design system.

**Tech Stack:** React 18, Tailwind CSS v4, Lucide React icons, Vite.

**Spec:** `docs/superpowers/specs/2026-09-03-linkedin-corporate-modern-design.md`

## Global Constraints
- Canvas base background `#f3f6f8` with pure white cards `#ffffff` and 1px borders `#e0e0e0`. Zero drop shadows on standard cards.
- Primary CTA color `#0a66c2` (LinkedIn Blue) with pure white text `#ffffff` and `24px` pill radius (`rounded-full`).
- Text primary `#000000` (WCAG AAA 21:1 contrast); Text muted `#666666` (WCAG AA 4.5:1).
- Accent rust `#b24020` for overdue alerts and missing skills; Accent emerald `#057642` for verified claims and high matches.
- Typography: System font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`).
- ZERO em-dashes (`—`) or en-dashes (`–`) anywhere in visible text. Use regular hyphens (`-`).
- Maintain 100% backward compatibility with existing API client calls, auth states, modal triggers, and offline heuristic engine.
- Every task must end with `cd frontend && npm run build` exiting with code 0.

---

### Task 1: Design Tokens, CSS Utilities & Base HTML Migration
**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: Tailwind CSS setup, root CSS variables.
- Produces: Corporate design tokens (`--bg-canvas: #f3f6f8`, `--primary-blue: #0a66c2`, `.card-corporate`, `.btn-primary-corporate`, `.btn-secondary-corporate`, `.badge-corporate`).

- [x] **Step 1: Update `frontend/index.html`**
  Update `<title>` to `JobHelperGuru | Intelligent Job Application Assistant & ATS Optimizer`.
  Set `<body>` classes to `bg-[#f3f6f8] text-[#000000] font-sans antialiased selection:bg-[#0a66c2] selection:text-white`.

- [x] **Step 2: Update `frontend/src/index.css` with LinkedIn Corporate Modern Tokens**
  Replace `:root` variables:
  ```css
  :root {
    --bg-canvas: #f3f6f8;
    --bg-surface: #ffffff;
    --border-color: #e0e0e0;
    --border-hover: #c1c6d4;
    --border-focus: #0a66c2;
    
    --primary-blue: #0a66c2;
    --primary-blue-hover: #004e99;
    --accent-rust: #b24020;
    --accent-emerald: #057642;
    --accent-navy: #004e99;
    --text-primary: #000000;
    --text-muted: #666666;
  }
  ```
  Replace dark glassmorphism classes with corporate utilities:
  ```css
  .card-corporate {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: none;
    transition: border-color 0.15s ease;
  }
  .card-corporate:hover {
    border-color: #c1c6d4;
  }
  .btn-primary-corporate {
    background-color: #0a66c2;
    color: #ffffff;
    font-weight: 600;
    font-size: 0.875rem;
    padding: 8px 18px;
    border-radius: 9999px;
    border: 1px solid transparent;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: background-color 0.15s ease, transform 0.1s ease;
  }
  .btn-primary-corporate:hover {
    background-color: #004e99;
  }
  .btn-secondary-corporate {
    background-color: #ffffff;
    color: #0a66c2;
    font-weight: 600;
    font-size: 0.875rem;
    padding: 7px 16px;
    border-radius: 9999px;
    border: 1px solid #0a66c2;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: background-color 0.15s ease, border-color 0.15s ease;
  }
  .btn-secondary-corporate:hover {
    background-color: #f0f7fe;
    border-color: #004e99;
  }
  .input-corporate {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 0.875rem;
    color: #000000;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }
  .input-corporate:focus {
    outline: none;
    border-color: #0a66c2;
    box-shadow: 0 0 0 2px rgba(10, 102, 194, 0.2);
  }
  ```

- [x] **Step 3: Run Vite build to verify CSS syntax**
  Command: `cd frontend && npm run build`
  Expected: Build succeeds with 0 errors.

- [x] **Step 4: Commit changes**
  ```bash
  git add frontend/index.html frontend/src/index.css
  git commit -m "feat(design): implement LinkedIn Corporate Modern design tokens and base utilities"
  ```

---

### Task 2: Global Navigation & Application Shell (`App.jsx`, `UserNav.jsx`)
**Files:**
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/UserNav.jsx`

**Interfaces:**
- Consumes: Corporate design tokens, auth state, tab switching.
- Produces: 64px corporate header, active blue underline indicator, clean light application frame.

- [x] **Step 1: Refactor Header Navigation in `frontend/src/App.jsx`**
  - Replace `bg-zinc-950/80` and `border-white/[0.08]` with `bg-white border-b border-[#e0e0e0] shadow-none`.
  - Brand Logo: 36x36px `#0a66c2` rounded square (`rounded-md`) with pure white briefcase icon. Bold black text "JobHelperGuru".
  - Tab Switcher:
    - Tab buttons on a clean white background.
    - Active tab has text color `#0a66c2`, font weight 600, and a 2px bottom border `border-b-2 border-[#0a66c2]` positioned on the bottom edge of the 64px header.
    - Inactive tabs: text `#666666`, hover text `#000000`.
  - Action buttons:
    - Replace `.btn-excel` with `.btn-secondary-corporate` with spreadsheet green icon.
    - Settings button: `border border-[#e0e0e0] text-[#666666] hover:text-[#000000] hover:bg-[#f3f6f8] rounded-full`.
  - Main container: `min-h-screen bg-[#f3f6f8] text-[#000000] flex flex-col font-sans`.

- [x] **Step 2: Update `frontend/src/components/UserNav.jsx`**
  - Update user menu dropdown to white background `#ffffff`, 1px border `#e0e0e0`, rounded-lg (8px), no dark backgrounds.
  - Avatar button: clean circular border `border-2 border-[#0a66c2]` or neutral gray.
  - Menu item hover: `hover:bg-[#f3f6f8] text-[#000000]`.

- [x] **Step 3: Run Vite build**
  Command: `cd frontend && npm run build`
  Expected: Build succeeds with 0 errors.

- [x] **Step 4: Commit changes**
  ```bash
  git add frontend/src/App.jsx frontend/src/components/UserNav.jsx
  git commit -m "feat(ui): migrate App shell and Top Navigation to LinkedIn Corporate Modern design"
  ```

---

### Task 3: Job Ingestion & Role Metadata Brief (`JobAnalyzer.jsx`)
**Files:**
- Modify: `frontend/src/components/JobAnalyzer.jsx`

**Interfaces:**
- Consumes: Job parsing API, skills extraction.
- Produces: Corporate white ingestion card, 1px `#e0e0e0` borders, `#0a66c2` Analyze button, parsed role metadata pills.

- [x] **Step 1: Refactor Command Bar to Corporate Ingestion Card**
  - Change main ingestion wrapper from dark glass container to `.card-corporate p-6 bg-white border border-[#e0e0e0] rounded-lg`.
  - Input field: `input-corporate w-full h-11 text-sm text-[#000000] placeholder:text-[#666666]`.
  - Action button: Solid `#0a66c2` pill button with white text "Analyze Job" (44px touch height).
  - Text paste toggle: Clean link/button `text-[#0a66c2] hover:underline font-semibold text-xs`.
  - Expanded raw text box: `bg-[#ffffff] border border-[#e0e0e0] rounded text-sm text-[#000000] p-3`.

- [x] **Step 2: Refactor Parsed Role Overview Panel**
  - White container with 1px `#e0e0e0` border.
  - Role Title: `text-2xl font-bold text-[#000000]`.
  - Company: `text-base font-semibold text-[#666666] flex items-center gap-2`.
  - Metadata pills: `bg-[#f3f6f8] text-[#000000] border border-[#e0e0e0] px-3 py-1 rounded-full text-xs font-semibold`.

- [x] **Step 3: Run Vite build**
  Command: `cd frontend && npm run build`
  Expected: Build succeeds with 0 errors.

- [x] **Step 4: Commit changes**
  ```bash
  git add frontend/src/components/JobAnalyzer.jsx
  git commit -m "feat(ui): migrate JobAnalyzer ingestion card and role brief to LinkedIn Corporate style"
  ```

---

### Task 4: Skills Matrix & ATS Keyword Bank (`SkillsMatrix.jsx`, `ATSKeywordBank.jsx`)
**Files:**
- Modify: `frontend/src/components/SkillsMatrix.jsx`
- Modify: `frontend/src/components/ATSKeywordBank.jsx`

**Interfaces:**
- Consumes: Categorized skills list, frequency counts.
- Produces: Scannable 4-tab qualification matrix, copyable ATS keyword pills with count metrics.

- [x] **Step 1: Refactor `SkillsMatrix.jsx`**
  - Card container: `card-corporate p-6 bg-white border border-[#e0e0e0] rounded-lg`.
  - Tab header: 4 tabs ('Must-Haves', 'Preferred', 'Tech Stack', 'Soft Skills').
    - Active tab: `text-[#0a66c2] border-b-2 border-[#0a66c2] font-semibold`.
    - Inactive tabs: `text-[#666666] hover:text-[#000000]`.
  - Skill rows:
    - Verified items: Green check icon (`#057642`), text `#000000`.
    - Missing items: Rust alert icon (`#b24020`), text `#b24020`, with an interactive "+ Add" or "Optimize" button.

- [x] **Step 2: Refactor `ATSKeywordBank.jsx`**
  - Card container: `card-corporate p-6 bg-white border border-[#e0e0e0] rounded-lg`.
  - Keyword chips: `inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#f3f6f8] text-[#000000] border border-[#e0e0e0] hover:border-[#0a66c2] transition-colors`.
  - Frequency badge: `bg-[#e0e0e0] text-[#000000] px-1.5 py-0.2 rounded-full text-[10px] font-bold`.
  - "Copy All Keywords" button: `btn-secondary-corporate text-xs`.

- [x] **Step 3: Run Vite build**
  Command: `cd frontend && npm run build`
  Expected: Build succeeds with 0 errors.

- [x] **Step 4: Commit changes**
  ```bash
  git add frontend/src/components/SkillsMatrix.jsx frontend/src/components/ATSKeywordBank.jsx
  git commit -m "feat(ui): migrate SkillsMatrix and ATSKeywordBank to corporate light theme"
  ```

---

### Task 5: Multi-Resume Best-Fit Ranker (`ResumeFitRanker.jsx`)
**Files:**
- Modify: `frontend/src/components/ResumeFitRanker.jsx`

**Interfaces:**
- Consumes: Resumes list, ATS match algorithm, BulletSkill triggers.
- Produces: Ranked resume comparison cards, match percentage pills, 1-click BulletSkill trigger.

- [x] **Step 1: Refactor Resume Cards & Match Badges**
  - Container: `card-corporate p-6 bg-white border border-[#e0e0e0] rounded-lg`.
  - Top Match Resume Card:
    - 1px border `#0a66c2` (highlighted) with a clean white background.
    - Match Badge: `bg-[#057642]/10 text-[#057642] border border-[#057642]/20 font-bold px-3 py-1 rounded-full text-sm`.
    - Resume title: `font-bold text-base text-[#000000]`.
    - Matched vs. Missing summary: `text-xs text-[#666666]`.
  - Secondary Resume Cards:
    - Neutral 1px border `#e0e0e0`, match badge in muted navy or gray.
  - Action Button: `btn-primary-corporate w-full` with text "Optimize Bullets with BulletSkill".

- [x] **Step 2: Run Vite build**
  Command: `cd frontend && npm run build`
  Expected: Build succeeds with 0 errors.

- [x] **Step 3: Commit changes**
  ```bash
  git add frontend/src/components/ResumeFitRanker.jsx
  git commit -m "feat(ui): migrate ResumeFitRanker to LinkedIn Corporate Modern design"
  ```

---

### Task 6: Applications Tracker - Table View & Kanban Board (`ApplicationsTracker.jsx`, `KanbanBoard.jsx`, `FollowUpBanner.jsx`)
**Files:**
- Modify: `frontend/src/components/ApplicationsTracker.jsx`
- Modify: `frontend/src/components/KanbanBoard.jsx`
- Modify: `frontend/src/components/FollowUpBanner.jsx`

**Interfaces:**
- Consumes: Applications database, status pipeline, Excel export.
- Produces: Table View with 7 columns, Kanban board with 5 columns, Follow-up urgency banner.

- [ ] **Step 1: Refactor `FollowUpBanner.jsx`**
  - White container with 1px border `#e0e0e0`, rounded-lg.
  - Rust alert badge: `bg-[#b24020]/10 text-[#b24020] border border-[#b24020]/30 px-2 py-0.5 rounded-full font-bold text-xs`.
  - Text: `text-sm font-medium text-[#000000]`.

- [ ] **Step 2: Refactor Controls & Action Bar in `ApplicationsTracker.jsx`**
  - View switcher:
    - Table View button vs. Kanban Board button.
    - Active view: `bg-[#0a66c2] text-white rounded-full px-4 py-1.5 font-semibold text-xs`.
    - Inactive view: `text-[#666666] hover:text-[#000000] px-4 py-1.5 font-medium text-xs`.
  - Status filter: `input-corporate text-xs h-9`.
  - Primary button: "+ Add Application" (`btn-primary-corporate`).
  - Excel button: "Export to Excel (.xlsx)" (`btn-secondary-corporate`).

- [ ] **Step 3: Implement High-Density Data Table View**
  - Clean `<table>` with white background `#ffffff` and `border border-[#e0e0e0] rounded-lg overflow-hidden`.
  - Header `<thead>`: `bg-[#f3f6f8] text-[#000000] font-semibold text-xs border-b border-[#e0e0e0] py-3 px-4`.
  - Rows `<tr>`: `border-b border-[#e0e0e0] hover:bg-[#f9fafb] transition-colors py-3 px-4 text-sm text-[#000000]`.
  - Status Pills:
    - `Applied`: `bg-[#0a66c2]/10 text-[#0a66c2] border border-[#0a66c2]/20`.
    - `Interviewing`: `bg-[#004e99]/10 text-[#004e99] border border-[#004e99]/20`.
    - `Offered`: `bg-[#057642]/10 text-[#057642] border border-[#057642]/20 font-bold`.
    - `Wishlist`: `bg-[#f3f6f8] text-[#666666] border border-[#e0e0e0]`.
  - Follow-up date cell: Highlight "Today" and "Overdue" with rust badge (`bg-[#b24020]/10 text-[#b24020]`).
  - Table Footer: Left shows item counts and pipeline valuation; right shows pagination buttons.

- [ ] **Step 4: Refactor `KanbanBoard.jsx`**
  - 5 Columns: `Wishlist`, `Applied`, `Interviewing`, `Offer Received`, `Archived`.
  - Column background: `#f3f6f8` with 1px border `#e0e0e0`, rounded-lg.
  - Kanban Cards: Pure white `#ffffff`, 1px border `#e0e0e0`, rounded-lg, 0px shadow.

- [ ] **Step 5: Run Vite build**
  Command: `cd frontend && npm run build`
  Expected: Build succeeds with 0 errors.

- [ ] **Step 6: Commit changes**
  ```bash
  git add frontend/src/components/ApplicationsTracker.jsx frontend/src/components/KanbanBoard.jsx frontend/src/components/FollowUpBanner.jsx
  git commit -m "feat(ui): implement LinkedIn Corporate Modern Table View and Kanban Board"
  ```

---

### Task 7: BulletSkill 2.0 Resume Bullet Optimizer Studio (`BulletOptimizerModal.jsx`)
**Files:**
- Modify: `frontend/src/components/BulletOptimizerModal.jsx`

**Interfaces:**
- Consumes: Resume bullet points, missing keywords, candidate generation API.
- Produces: Candidate A/B/C comparison cards, WHAT+HOW+RESULT structure, claim verification tags.

- [ ] **Step 1: Refactor Modal Frame & Header**
  - Modal overlay: `bg-black/40 backdrop-blur-sm fixed inset-0 z-50 flex items-center justify-center p-4`.
  - Modal container: Max-width 1080px, `bg-white border border-[#e0e0e0] rounded-xl shadow-xl overflow-hidden`.
  - Modal header: Title "BulletSkill 2.0 Resume Bullet Optimizer", subtitle, target role, and target missing skill in rust pill (`#b24020`).

- [ ] **Step 2: Refactor Candidate Comparison Cards**
  - Grid of 3 cards (`grid grid-cols-1 md:grid-cols-3 gap-4`).
  - Card A (ATS-focused): White card, 1px border `#e0e0e0`, verified tags in emerald (`#057642`).
  - Card B (Concise): White card, 1px border `#e0e0e0`.
  - Card C (Technical & Result - Recommended): Highlighted with 2px `#0a66c2` border, "Accept & Insert" primary button (`btn-primary-corporate`).

- [ ] **Step 3: Verification & Safeguards Drawer**
  - Verification checkbox: "I verify that I have hands-on experience with this skill."
  - Metric safeguards: Highlight placeholders `[X%]` in amber.

- [ ] **Step 4: Run Vite build**
  Command: `cd frontend && npm run build`
  Expected: Build succeeds with 0 errors.

- [ ] **Step 5: Commit changes**
  ```bash
  git add frontend/src/components/BulletOptimizerModal.jsx
  git commit -m "feat(ui): migrate BulletSkill 2.0 Optimizer Modal to corporate design"
  ```

---

### Task 8: Supporting Modals & Polish (`ResumeLibrary.jsx`, `SettingsModal.jsx`, `AuthModal.jsx`, `CoverLetterModal.jsx`, `OfflineSwitchModal.jsx`)
**Files:**
- Modify: `frontend/src/components/ResumeLibrary.jsx`
- Modify: `frontend/src/components/SettingsModal.jsx`
- Modify: `frontend/src/components/AuthModal.jsx`
- Modify: `frontend/src/components/CoverLetterModal.jsx`
- Modify: `frontend/src/components/OfflineSwitchModal.jsx`

**Interfaces:**
- Consumes: Modal state, user profile, AI settings.
- Produces: Harmonized white card dialogs, 1px borders, corporate form inputs and buttons.

- [ ] **Step 1: Refactor `ResumeLibrary.jsx`**
  - White cards with 1px border `#e0e0e0`, resume upload dropzone in `#f3f6f8` with dashed 1px border.

- [ ] **Step 2: Refactor `SettingsModal.jsx`, `AuthModal.jsx`, `CoverLetterModal.jsx`, `OfflineSwitchModal.jsx`**
  - White surface `#ffffff`, 1px borders `#e0e0e0`, corporate inputs, primary blue buttons `#0a66c2`.

- [ ] **Step 3: Comprehensive End-to-End Build & Test Verification**
  - Command: `cd frontend && npm run build`
  - Command: `python -m pytest tests/ -v`
  - Expected: Frontend compiles with 0 errors; all automated tests pass.

- [ ] **Step 4: Commit changes**
  ```bash
  git add frontend/src/components/
  git commit -m "feat(ui): complete LinkedIn Corporate Modern migration across all modals and views"
  ```
