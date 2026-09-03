# Kinetic Noir UI/UX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the JobHelperGuru frontend interface into an ultra-sleek, minimalist, developer-grade "Kinetic Noir" dark aesthetic inspired by Linear, Raycast, and Vercel.

**Architecture:** Update foundational design tokens and typography in `index.html` and `index.css`, followed by component-by-component redesign of the Header Navigation (`App.jsx`), Ingestion Command Bar & Role Brief (`JobAnalyzer.jsx`), Match Gauge & Bullet Optimizer Card (`ResumeFitRanker.jsx`), KPI Strip & Data Pipeline (`ApplicationsTracker.jsx`), and Resume Vault & Modals (`ResumeLibrary.jsx`, modals).

**Tech Stack:** React, TailwindCSS, Lucide React icons, Vite, Google Fonts (Geist, Inter, JetBrains Mono).

**Spec:** `docs/superpowers/specs/2026-09-02-kinetic-noir-ui-redesign.md`

## Global Constraints
- OLED canvas base `#09090b` with `border-white/10` light-leak edges.
- Typography: Geist for headlines, Inter for UI body, JetBrains Mono for metrics and ATS tokens.
- Maintain all existing state, handlers, dynamic score recalculation, and offline mode functionality with 100% backward compatibility.
- Ensure `npm run build` succeeds with zero errors after every task.

---

### Task 1: Design Tokens & Typography Foundation
**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Update Google Fonts in `frontend/index.html`**
  - Import Geist (wght 400, 600, 700), Inter (wght 400, 500, 600), and JetBrains Mono (wght 500, 600).
  - Set `body` class to `bg-[#09090b] text-zinc-100 font-sans selection:bg-indigo-500 selection:text-white`.

- [ ] **Step 2: Update `frontend/src/index.css` with Kinetic Noir Tokens**
  - Define `.glass-panel`, `.glass-card`, `.glass-input`, and `.glass-command-bar` utilities with `backdrop-filter: blur(16px)` and `border-white/10`.
  - Add gradient utility `.btn-gradient` (`bg-gradient-to-r from-indigo-500 via-indigo-600 to-violet-600`).
  - Add radial glow and hover transition utilities.

- [ ] **Step 3: Verify build**
  - Run: `cd frontend && npm run build`
  - Expected: Build succeeds.

---

### Task 2: Modern Top Navigation Bar & App Shell
**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Redesign Top Header**
  - Sticky blurred header `backdrop-blur-xl bg-[#09090b]/80 border-b border-white/5`.
  - Glowing gradient spark icon + clean "JobHelperGuru" wordmark.
  - Centered pill tab switcher (`bg-white/[0.04] p-1 rounded-full border border-white/5`).
  - Status pill (`Offline Heuristic Active` or `AI Active`) with pulse indicator.
  - Quick action settings icon button with subtle border.

- [ ] **Step 2: Verify build**
  - Run: `cd frontend && npm run build`
  - Expected: Build succeeds.

---

### Task 3: Raycast-Style Command Bar & Role Brief
**Files:**
- Modify: `frontend/src/components/JobAnalyzer.jsx`

- [ ] **Step 1: Implement Floating Command Bar**
  - Centered floating glass command bar with search icon, input field, and embedded gradient `⚡ Analyze Role` action button.
  - Clean "Or Paste Job Description Text" toggle with subtle transition.

- [ ] **Step 2: Redesign Job Overview Panel**
  - Company badge, role title with tight tracking, metadata chips (Work Mode, Location, Salary).
  - Modern skill chips cloud with count badges.

- [ ] **Step 3: Verify build**
  - Run: `cd frontend && npm run build`
  - Expected: Build succeeds.

---

### Task 4: Radial Match Gauge & BulletSkill 2.0 Card
**Files:**
- Modify: `frontend/src/components/ResumeFitRanker.jsx`

- [ ] **Step 1: Build Radial Score Gauge & Resume Switcher**
  - Glowing circular progress SVG or meter displaying match percentage in JetBrains Mono (`88% Match - Top Candidate`).
  - Pill-shaped switcher for toggling between candidate resumes.

- [ ] **Step 2: Redesign Skill Chip Badges**
  - Emerald chips for Matched Skills.
  - Amber chips with `+ Add` for Missing Skills.
  - Electric Blue chips for Potentially Added Skills with dynamic score recalculation.

- [ ] **Step 3: Polish BulletSkill 2.0 Card**
  - Deep indigo glass container highlighting target project/work section.
  - 1-click `Adopt Bullet` primary button and `Draft Tailored Pitch` floating action.

- [ ] **Step 4: Verify build**
  - Run: `cd frontend && npm run build`
  - Expected: Build succeeds.

---

### Task 5: KPI Metrics Strip & Pipeline Data Grid
**Files:**
- Modify: `frontend/src/components/ApplicationsTracker.jsx`

- [ ] **Step 1: Add 4 KPI Stat Summary Cards**
  - Total Applications, Active Interviews, Avg Fit Score, Follow-up Alerts.

- [ ] **Step 2: Add Horizontal Status Filter Bar**
  - Pill chips: `All`, `Applied`, `Interviewing`, `Offer`, `Rejected`.

- [ ] **Step 3: Redesign Data Grid Table**
  - Generous row padding, subtle hover glow, clean status badges, and action icons.

- [ ] **Step 4: Verify build**
  - Run: `cd frontend && npm run build`
  - Expected: Build succeeds.

---

### Task 6: Resume Vault & Modals Polish
**Files:**
- Modify: `frontend/src/components/ResumeLibrary.jsx`
- Modify: `frontend/src/components/BulletOptimizerModal.jsx`
- Modify: `frontend/src/components/CoverLetterModal.jsx`
- Modify: `frontend/src/components/SettingsModal.jsx`
- Modify: `frontend/src/components/OfflineSwitchModal.jsx`

- [ ] **Step 1: Redesign Resume Vault Cards & Upload Area**
  - Glass card styling with resume stats and delete/edit actions.
- [ ] **Step 2: Apply Consistent Glassmorphic Modal Styling**
  - Deep black backdrop blur `bg-black/80 backdrop-blur-md` and `border-white/10`.

- [ ] **Step 3: Verify build**
  - Run: `cd frontend && npm run build`
  - Expected: Build succeeds.

---

### Task 7: End-to-End Verification & Live Check
**Files:**
- Test all components end-to-end.

- [ ] **Step 1: Rebuild frontend**
  - Run: `cd frontend && npm run build`
- [ ] **Step 2: Run all backend tests**
  - Run: `python -m pytest tests/ -v`
  - Expected: All 29 tests pass.
- [ ] **Step 3: Restart Uvicorn server and verify live preview on port 8000**
