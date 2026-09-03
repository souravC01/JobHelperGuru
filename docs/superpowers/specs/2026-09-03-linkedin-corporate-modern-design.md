# Design Specification: "LinkedIn Corporate Modern" UI/UX Migration

## 1. Goal
Migrate the entire JobHelperGuru web application from the previous "Kinetic Noir" dark aesthetic to the **LinkedIn Corporate Modern** design language. The new interface embodies institutional authority, accessibility-first WCAG AAA compliance, high-density scannability, and executive trust.

## 2. Design Rationale & Identity
- **Audience & Context**: Job seekers, engineers, technical candidates, and professionals applying to high-growth companies. The interface acts as a reliable, distraction-free productivity engine.
- **Visual Personality**: High-contrast, clean, flat surfaces with crisp 1px borders, zero drop shadows, predictable 4px/8px alignments, and focused information hierarchy.
- **Zero Em-Dash Rule**: Strictly replace all em-dash (`—`) and en-dash (`–`) occurrences with hyphens (`-`) or structural layout dividers.

## 3. Design Tokens & Color Architecture

### 3.1 Color Palette
- **Canvas Background**: `#f3f6f8` (Subtle light neutral gray).
- **Cards & Surfaces**: `#ffffff` (Pure white).
- **Surface Borders**: `#e0e0e0` (Crisp 1px solid border).
- **Primary Brand Color**: `#0a66c2` (LinkedIn Blue).
  - Used for: Primary CTA buttons, active navigation indicator, links, active tab underlines.
  - Button text: Pure white (`#ffffff` on `#0a66c2`), 12.6:1 contrast ratio (exceeds WCAG AAA).
- **Text Primary**: `#000000` (High contrast, 21:1 contrast ratio against white).
- **Text Muted / Secondary**: `#666666` (4.54:1 contrast ratio, WCAG AA compliant).
- **Semantic Accent - Rust**: `#b24020` (Warm burnt orange for overdue follow-ups, missing ATS keywords, unverified assumptions).
- **Semantic Success - Emerald**: `#057642` (Forest green for verified claims, offer status, 85%+ high match badges).
- **Semantic Info - Navy**: `#004e99` (Deep blue for interviewing stage).

### 3.2 Typography
- **Font Stack**: System font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`).
- **Heading Scales**:
  - Display / Major titles: 28px - 32px, font-weight 600, line-height 1.25.
  - Section headers: 20px - 24px, font-weight 600, line-height 1.25.
  - Card titles / Modal headers: 16px - 18px, font-weight 600.
- **Body & Labels**:
  - Primary UI labels / card headings: 14px, font-weight 600, line-height 1.25.
  - Descriptive body text: 14px, font-weight 400, line-height 1.4.
  - Metadata / Small tags: 12px, font-weight 600.

### 3.3 Shapes, Borders & Elevation
- **Border Radius**:
  - Cards & Containers: `8px` (`rounded-lg`).
  - Primary Buttons & Badges: `24px` (`rounded-full` pill shape).
  - Secondary / Outline Buttons: `24px` or `6px`.
  - Form Inputs: `4px` (`rounded`).
- **Shadows**:
  - Flat 1px border cards: `border: 1px solid #e0e0e0`, zero box-shadow.
  - Temporary Overlays / Modals: `box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), 0 0 0 1px #e0e0e0`.

---

## 4. Component Redesign Specifications

### 4.1 Global Navigation (`App.jsx`, `UserNav.jsx`)
- Height: 64px, `bg-white border-b border-[#e0e0e0]`.
- Brand Logo: `#0a66c2` icon box with pure white briefcase mark + bold "JobHelperGuru" wordmark.
- Search Input: Centered global input with 1px border `#e0e0e0`, 4px radius, placeholder "Search jobs, skills, or applications...".
- Navigation Tabs:
  - `Job Analyzer` (active state has 2px solid `#0a66c2` bottom indicator and blue text).
  - `Resume Library (N)`.
  - `Application Pipeline (N)`.
- Action Buttons:
  - `Export .xlsx`: Secondary outline button with Excel green badge.
  - User profile & settings: Clean circular avatar and subtle border icon button.

### 4.2 Job Ingestion & Role Brief (`JobAnalyzer.jsx`)
- **Ingestion Card**: White container, 1px `#e0e0e0` border, 8px radius.
  - Text input for pasting job links (LinkedIn, Greenhouse, Lever, Workday, etc.).
  - Primary action: Solid `#0a66c2` pill button "Analyze Job" (white text).
  - Smooth expansion toggle for raw job description text paste.
- **Parsed Role Metadata Strip**:
  - Position Title: 24px bold black text.
  - Company: 16px semi-bold with subtle verified badge.
  - Tag Pills: Location, Work Mode (Remote/Hybrid/Onsite), Salary Range ($175k - $210k), Job Type.

### 4.3 Categorized Skills Matrix & ATS Keyword Bank (`SkillsMatrix.jsx`, `ATSKeywordBank.jsx`)
- **Skills Matrix Card**:
  - 4 Tabs: Must-Haves, Preferred, Tech Stack, Soft Skills with count pills.
  - Rows with clear status markers: Verified (Emerald check) vs. Missing (Rust warning icon).
- **ATS Keyword Bank**:
  - Interactive pill tags with frequency numbers (`React 18 (4)`, `TypeScript (6)`, etc.).
  - 1-click "Copy All Keywords" secondary button.

### 4.4 Multi-Resume Best-Fit Ranker (`ResumeFitRanker.jsx`)
- Ranked cards showing match scores:
  - Top match highlighted with high-contrast `94% Match` emerald badge.
  - Breakdown: 16 matched skills, 2 missing skills.
  - Primary CTA: `#0a66c2` pill button "Optimize Bullets with BulletSkill".

### 4.5 Applications Tracker - Dual View (`ApplicationsTracker.jsx`, `KanbanBoard.jsx`)
- **Follow-Up Reminder Banner**:
  - Top banner with rust `#b24020` bell icon: "2 applications require follow-up today (Stripe, Airbnb)."
- **Control Bar**:
  - View switcher: Table View vs. Kanban Board.
  - Status filter dropdown, search input.
  - Actions: "Export to Excel (.xlsx)" and "+ Add Application" primary blue pill button.
- **Table View**:
  - Multi-select checkbox column.
  - Columns: Company & Role, Status Pill, ATS Match Score (%), Date Applied, Next Follow-Up (highlighting Today/Overdue in rust `#b24020`), Salary, Location, Tailored Resume, Actions (...).
  - Footer with item count, total pipeline value ($1.38M), and pagination.
- **Kanban View**:
  - 5 Columns: Wishlist, Applied, Interviewing, Offer Received, Archived.
  - Cards with 1px `#e0e0e0` borders, clean metadata tags, and quick menus.

### 4.6 BulletSkill 2.0 Optimizer Modal (`BulletOptimizerModal.jsx`)
- Modal Container: Max-width 1080px, white surface, 1px border `#e0e0e0`, subtle ambient overlay.
- Header: Title, target role, target missing ATS keyword in rust pill (`#b24020`).
- Original Bullet Input Box: 1px border with muted background `#f9fafb`.
- 3-Candidate Comparison Cards:
  - **Candidate A (ATS-Focused)**: WHAT + HOW + RESULT with verified tags.
  - **Candidate B (Concise)**: Compact, direct impact.
  - **Candidate C (Technical & Result - Recommended)**: 2px `#0a66c2` border, quantified metrics with `[X%]` safeguards.
- Verification Drawer: Safeguards checkbox confirming real hands-on experience, preventing fabricated claims.

---

## 5. Stitch MCP Reference Assets
- **Project Resource**: `projects/2824221430501946855`
- **Design System Asset**: `assets/1fe8f07c16ef40d7876bad970ca3d89b` (*Professional Network Alpha*)
- **Generated Stitch Screens**:
  1. Job Analyzer Dashboard: `projects/2824221430501946855/screens/3087dc7dc9b94c1e840df74b57bb6e86`
  2. Application Tracker Kanban Pipeline: `projects/2824221430501946855/screens/8a324aca654a4f56913012c1a4f12663`
  3. BulletSkill 2.0 Studio: `projects/2824221430501946855/screens/40fb891c6b944b879cf96a769fb38f5f`
  4. Application Tracker Table View: `projects/2824221430501946855/screens/e26bb3c8ae5547d08c48434786fc2ab1`
