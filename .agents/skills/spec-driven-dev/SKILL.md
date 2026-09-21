---
name: spec-driven-dev
description: Orchestrates the Spec-Driven Development (SDD) lifecycle for Finnie AI. Use when authoring feature specifications, reviewing specs, performing test-first implementation, and promoting verified specs to the baseline.
---

# Spec-Driven Development (SDD) Playbook

This skill governs the end-to-end Spec-Driven Development lifecycle across **Finnie AI**.

---

## 🧭 The SDD Lifecycle Overview

```text
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│ 1. SPECIFY     │ ───► │ 2. ALIGN       │ ───► │ 3. TEST-FIRST   │
│ Draft in       │      │ Review & Agree │      │ Write failing  │
│ specs/upcoming │      │ on ACs & Types │      │ unit tests     │
└────────────────┘      └────────────────┘      └────────────────┘
                                                        │
                                                        ▼
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│ 6. PROMOTION   │ ◄─── │ 5. VERIFY      │ ◄─── │ 4. IMPLEMENT   │
│ Move to        │      │ Unit Tests Pass│      │ Backend ➔ UI   │
│ specs/baseline │      │ Build Clean    │      │ Clean code     │
└────────────────┘      └────────────────┘      └────────────────┘
```

---

## 🛠️ Phase-by-Phase Execution

### Phase 1: Specify (`specs/upcoming/`)
- When a new feature or major enhancement is requested, **never jump directly into code**.
- Copy [`specs/upcoming/SPEC_TEMPLATE.md`](file:///specs/upcoming/SPEC_TEMPLATE.md) to `specs/upcoming/SPEC-[XX]-[FEATURE_NAME].md`.
- Fill out:
  1. **Business Objective & Domain Rules**: Specific problem, boundaries, financial formulas, compliance `$NFA` needs.
  2. **Technical Contracts**: REST routes, Pydantic schemas, SQLAlchemy models, LangGraph node signatures.
  3. **Frontend Presentation**: Custom hook signatures, caching behavior, component UX states (Loading, Empty, Error, Success).
  4. **Resilience & Edge Cases**: Failure modes, third-party timeouts, fallback mechanisms.
  5. **Acceptance Criteria (AC-1 to AC-N)**: Concrete, testable verification checkpoints.

### Phase 2: Align & Review
- Present the upcoming spec to the user/developer for review.
- Confirm consensus on:
  - Database schema changes (foreign keys, composite unique constraints).
  - API request/response shapes.
  - Multi-tenant security boundaries (`effective_id = current_user.id`).
  - Regulatory compliance disclosures.

### Phase 3: Test-First (TDD Alignment)
- Translate Acceptance Criteria into automated test cases:
  - **Backend**: Unit test cases in `backend/tests/test_unit.py`.
  - **Frontend**: Integration test suites in `frontend/src/components/<Feature>/__tests__/<Feature>Flow.test.tsx` using Vitest + React Testing Library.
- Run tests to confirm expected failure (Red phase) before writing feature implementation code.

### Phase 4: Implement
Follow the structured 8-step lifecycle defined in `AGENTS.md` and `.agents/rules/`:
1. **Model**: Database entities in `backend/src/models/` with composite unique constraints.
2. **Schemas**: Pydantic input/output schemas in `backend/src/models/`.
3. **Agent Node**: Synchronous `def node(state: FinnieState) -> dict` in `backend/src/agents/`.
4. **Graph Wiring**: Node registration and conditional edge in `backend/src/graph.py` routing to `compliance_guardian_node`.
5. **REST Route**: Clean endpoint in `backend/main.py` with `Depends(get_current_user)`.
6. **Frontend Config**: Register endpoint in `frontend/src/config.ts`.
7. **Custom Hook**: React custom hook in `frontend/src/hooks/` managing state and auth headers.
8. **Component**: React 19 UI in `frontend/src/components/` with skeleton, empty, and error states.

### Phase 5: Sequential Verification Pipeline (Fail-Fast Gate)
Before concluding any implementation or PR, execute the mandatory 3-step pipeline in order:
1. **Step 1 (Backend Core)**: `uv run python -m unittest discover -s tests` (inside `backend/` — MUST pass 100%).
2. **Step 2 (Frontend Integration)**: `npm test` (inside `frontend/` — MUST pass 100% across all critical UI flows).
3. **Step 3 (Production Bundle Build)**: `npm run build` (inside `frontend/` — MUST pass with 0 errors and 0 warnings).

### Phase 6: Spec Promotion & Human-in-the-Loop Doc Gate
- Once all verification tests pass:
  1. Update spec status in `specs/upcoming/SPEC-[XX]-[NAME].md` to:
     `> **Status**: 🟢 **VERIFIED & IN PRODUCTION**`
  2. Move the spec from `specs/upcoming/` to `specs/baseline/`.
  3. Follow **Golden Rule #10** and the [`doc-architect`](file:///.agents/skills/doc-architect/SKILL.md) skill:
     - Summarize changes.
     - Propose synchronized updates to technical & functional documentation (`docs/FEATURES_AND_AGENTS.md`, `docs/ARCHITECTURE.md`, `README.md`).
     - **Request explicit developer approval before modifying documentation**.
