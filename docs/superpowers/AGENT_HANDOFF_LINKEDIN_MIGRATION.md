# Antigravity IDE Agent Handoff: LinkedIn Corporate Modern UI Migration

> **For the executing Antigravity IDE Agent:**
> This document is your operational briefing and execution handoff to migrate the **JobHelperGuru** frontend from the dark "Kinetic Noir" theme to the **LinkedIn Corporate Modern** design system. Follow the implementation plan at `docs/superpowers/plans/2026-09-03-linkedin-corporate-modern-migration.md`.

---

## 1. Context & Mission

JobHelperGuru is an AI-driven career platform with job ingestion, ATS keyword extraction, multi-resume fit ranking, BulletSkill 2.0 bullet optimization, and an application pipeline tracker with Excel export.

The UI design has been codified and mocked up in **Stitch MCP** under project `2824221430501946855`. Your mission is to migrate the React/Tailwind frontend (`d:\Grind\Projects\JobHelperGuru\frontend`) to match these approved Stitch mockups with 100% fidelity.

---

## 2. Stitch Mockup References & Artifacts

All reference designs were generated with Gemini 3.1 Pro under Stitch Design System `assets/1fe8f07c16ef40d7876bad970ca3d89b` (*Professional Network Alpha*):

| Screen | Stitch Screen ID | Screenshot Preview | HTML Code Bundle |
|---|---|---|---|
| **Job Analyzer Dashboard** | `3087dc7dc9b94c1e840df74b57bb6e86` | [View Screenshot](https://lh3.googleusercontent.com/aida/AEtjO1UhvE43b5Vxmul6pDi0MpSliCJFEMRj9mTZN_xXb4Kz6OMS1NZT2bTK9AZXh56Sh7qy_s1ts15fcMaCq5Ycxqy00rorYTiXfa10PAvgrqhwhvOudNR6volBa59hy31kDXZd08tDGMzopiz4kbeYCdYGQbLdR23Fs8HzJLbOMzCtMVMh7324wSYqvqmY31UwbsHEs85BggFrzP-hDGbgm2-_VMFYzbQ6nEqilg-S3oq5Twlr63_SOcC7M_Y) | [Download HTML](https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sX2E3MGM5MjU3MjhiNTQzOWE5ZWE0YmU3NTE0MDc5YWRhEgsSBxD24t2B_RMYAZIBIwoKcHJvamVjdF9pZBIVQhMyODI0MjIxNDMwNTAxOTQ2ODU1&filename=&opi=96797242) |
| **Application Tracker Pipeline** | `8a324aca654a4f56913012c1a4f12663` | [View Screenshot](https://lh3.googleusercontent.com/aida/AEtjO1Wn0qq2jLhjd7D3XWf9DWhsyqcXzD7LO4xBqZt8Ekgpz0-O0dekr3Oa0cWE1jkTwFr3Z9p9pQTUhtL7BTM7W_GcI6u88pIvnTrL_mAY-wlG7q3PmU3xcvEzy1WXoo52j4jVrRQ2G2PnsKXGff6YqTBq0euTDs5aVHtxGfZy-ZCwRrtJzwX7uOkUDVWsq7G9ma3x_TpPOmfTYuPoxWfwCBs98leZ8JbysnGXlnKyjPS0FwBz3eBS9t3IuFU) | [Download HTML](https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sX2YyYzA1NWJiNjc0ZjRhYWI4NWM2ZDYwYmZmODU2MzNlEgsSBxD24t2B_RMYAZIBIwoKcHJvamVjdF9pZBIVQhMyODI0MjIxNDMwNTAxOTQ2ODU1&filename=&opi=96797242) |
| **BulletSkill 2.0 Studio** | `40fb891c6b944b879cf96a769fb38f5f` | [View Screenshot](https://lh3.googleusercontent.com/aida/AEtjO1VRBbT2PhHtltlIxtNXtXySZ49EA4LxHSbLaD0QsmyQ1Ppj9JWHVmL1rjJ9fFKn5AwkzgFgZkI0lIyAEAPDhDbNyAD901fA94xPsB7ZH8SiESkmAwu4T3EPV6F2Cp3UVXo5HJSCcqOkELjsBWGYrdV-jx3XRLil8F0QPCFQChwJuJ3VluwnhGKmZ-CAJ_YFCzUA2sVtJwLUsqyDyq4mSot6NU4SaHRnw0zO8qY-JR3r_ZjCLQrL-YwK720) | [Download HTML](https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzZhMDhlNDBkYTc4NjQ5ODE4NzY3NWNhNDM2MWYyZDllEgsSBxD24t2B_RMYAZIBIwoKcHJvamVjdF9pZBIVQhMyODI0MjIxNDMwNTAxOTQ2ODU1&filename=&opi=96797242) |
| **Application Tracker Table View** | `e26bb3c8ae5547d08c48434786fc2ab1` | [View Screenshot](https://lh3.googleusercontent.com/aida/AEtjO1WI5d_8-DdGlWiMK9r9EKsls56Kx-VNvZbS3fWN2aWuEYFV9q-py0mFJ6KmpxBvcZGoB87yeNqQIUhcY73ubGsSeOddaxzYOrD9fRO66iJ34LVKhwdIbpg8s5NbYljboBnBKOlzOIujEztHAWqPEiju3w09YWHKn51hvtEa6pMs4d9kyhS7mm3UHq8G7Py6ysfj2D9hB5ZwZsFPqvdqMxtoijfVjqhuPbzZNRr1yagz-DxrNmF__kWSzf4) | [Download HTML](https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sX2NkZDQ0MTgxYjc2MzQ5NGRiMTk2MWYwYjdkNzk1Yjc2EgsSBxD24t2B_RMYAZIBIwoKcHJvamVjdF9pZBIVQhMyODI0MjIxNDMwNTAxOTQ2ODU1&filename=&opi=96797242) |

---

## 3. Strict Rules & Quality Guardrails

1. **Zero Em-Dashes**:
   - The characters `—` and `–` are completely banned in all visible text strings, headlines, badges, and button labels. Use regular hyphens (`-`).
2. **Color System**:
   - Base canvas: `#f3f6f8` (never pure white page canvas).
   - Cards/Containers: `#ffffff` with 1px border `#e0e0e0` and 8px corners.
   - Primary: `#0a66c2` with white text `#ffffff`.
   - Text: `#000000` (primary headings/body), `#666666` (secondary/muted).
   - Alerts: `#b24020` (rust for overdue/missing), `#057642` (emerald for offers/verified).
   - Zero dark glassmorphic panels or AI-purple neon glows.
3. **Typography**:
   - High-performance system font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`).
   - 14px font size with 600 weight for labels and scannable items.
4. **Interactive Contract**:
   - Do NOT break existing API endpoints, token authentication, state handlers (`handleJobAnalyzed`, `handleOpenOptimizer`, `handleAdoptSkills`), or local heuristic evaluation.

---

## 4. Execution Step-by-Step

Execute tasks sequentially as defined in `docs/superpowers/plans/2026-09-03-linkedin-corporate-modern-migration.md`:

1. **Task 1**: Migrate `frontend/index.html` and `frontend/src/index.css`.
2. **Task 2**: Migrate `frontend/src/App.jsx` and `frontend/src/components/UserNav.jsx`.
3. **Task 3**: Migrate `frontend/src/components/JobAnalyzer.jsx`.
4. **Task 4**: Migrate `frontend/src/components/SkillsMatrix.jsx` and `frontend/src/components/ATSKeywordBank.jsx`.
5. **Task 5**: Migrate `frontend/src/components/ResumeFitRanker.jsx`.
6. **Task 6**: Migrate `frontend/src/components/ApplicationsTracker.jsx`, `KanbanBoard.jsx`, and `FollowUpBanner.jsx`.
7. **Task 7**: Migrate `frontend/src/components/BulletOptimizerModal.jsx`.
8. **Task 8**: Migrate supporting modals (`ResumeLibrary.jsx`, `SettingsModal.jsx`, `AuthModal.jsx`, etc.) and run full verification.

---

## 5. Verification Commands

Run these commands to verify each stage:

```bash
# Verify Frontend Compilation
cd frontend
npm run build

# Verify Backend Tests Suite
cd ..
python -m pytest tests/ -v
```
