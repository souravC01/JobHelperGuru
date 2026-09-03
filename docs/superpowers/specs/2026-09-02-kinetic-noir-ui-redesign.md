# Design Specification: "Kinetic Noir" UI/UX Redesign

## Goal
Transform the JobHelperGuru interface from its utilitarian dashboard aesthetic into an ultra-modern, minimalist, developer-grade application inspired by **Linear**, **Raycast**, and **Vercel**.

## Architecture & Visual System

### 1. Canvas & Surface Hierarchy
- **Canvas Base**: `#09090b` (OLED pitch black).
- **Surface Elevation 1**: `rgba(255, 255, 255, 0.02)` for cards and structural containers.
- **Surface Elevation 2 (Glassmorphic)**: `rgba(255, 255, 255, 0.04)` with `backdrop-filter: blur(16px)`.
- **Borders & Outlines**: 1px crisp `border-white/10` with subtle hover glow `border-white/20`.

### 2. Semantic Glowing Palette
- **Primary Accent**: Electric Indigo (`#6366f1`) to Violet (`#8b5cf6`) gradient for primary CTAs and active states.
- **Success / High Match**: Emerald (`#10b981`) for match scores (80%+), verified skills, and active indicators.
- **Missing Skills / Alerts**: Amber (`#f59e0b`) for missing requirements and follow-up warnings.
- **Potentially Added Skills**: Electric Blue (`#3b82f6`) for user-adopted skills with live re-evaluation.
- **Tech Stack Tokens**: Cyan (`#06b6d4`) for technical tags.

### 3. Typography
- **Headings & Body UI**: **Geist** and **Inter** with tight tracking (`tracking-tight`).
- **Data & ATS Metrics**: **JetBrains Mono** for fit percentages, token counts, and monetary compensation numbers.

---

## Component Specifications

### 1. Global Navigation (`TopNavBar` in `App.jsx`)
- Sticky blurred header with `backdrop-blur-xl bg-[#09090b]/80 border-b border-white/5`.
- Glowing brand icon (gradient purple spark) + "JobHelperGuru".
- Centered pill tab switcher with smooth transitions (`Job Analyzer`, `Resume Vault`, `Application Pipeline`).
- Status indicator pill (`⚡ Offline Heuristic Active` or `AI Provider: Active`).
- Quick action buttons with tooltips.

### 2. Raycast-Style Command Bar (`JobAnalyzer.jsx`)
- Floating centered command bar with `backdrop-blur-xl bg-white/[0.03] border border-white/10 hover:border-white/20 focus-within:border-indigo-500/60 shadow-2xl`.
- Unified input field supporting LinkedIn, Dayforce, Greenhouse, Workday, and Lever links.
- Embedded gradient button: `⚡ Analyze Role`.
- Secondary toggle for direct text pasting with a smooth expansion animation.

### 3. Role Overview Panel (`JobAnalyzer.jsx`)
- Clean company badge, role title, and metadata chips (Work Mode, Location, Salary band).
- Required skills and tech stack displayed as subtle, interactive pill chips.

### 4. Resume Best-Fit & BulletSkill 2.0 Card (`ResumeFitRanker.jsx`)
- Radial glowing match meter showing percentage and tier (`88% Match - Top Candidate`).
- Pill-shaped switcher for toggling between active candidate resumes.
- Color-coded skill breakdown:
  - Matched skills (emerald).
  - Missing skills (amber with quick-add button).
  - Potentially added skills (blue with remove action and score boost).
- Deep indigo glass container for **BulletSkill 2.0**:
  - Highlights specific project/work history section target.
  - Display Action Verb + Quantified Metric + Skill keywords.
  - 1-click **"Adopt Bullet"** action.
- Floating bar for **"Draft Tailored Pitch & Cover Letter"**.

### 5. Application Pipeline & KPI Strip (`ApplicationsTracker.jsx`)
- 4 KPI summary cards at top: Total Applications, Active Interviews, Avg Fit Score, Follow-up Needed.
- Horizontal filter chip bar (`All`, `Applied`, `Interviewing`, `Offer`, `Rejected`).
- High-density data grid with row hover effects, clear status badges, and quick action icons.

### 6. Modals & Dialogs
- Consistent glassmorphism across `BulletOptimizerModal`, `CoverLetterModal`, `SettingsModal`, and `OfflineSwitchModal`.
