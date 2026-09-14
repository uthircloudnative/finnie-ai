---
name: fullstack-code-review
description: Conducts rigorous, senior-level code reviews across Python backends (FastAPI, LangGraph, SQLAlchemy) and React/TypeScript frontends using a structured P0/P1/P2/UX rubric. Use whenever asked to review code, PRs, or architecture changes.
---

# Full-Stack Senior Code Review Playbook

When asked to review a feature, commit, pull request, or file in this codebase, execute this systematic audit and format your report using the standardized priority tiers below.

---

## 🔍 The Review Methodology

Review every submission across these dimensions in order:
1. **Spec Alignment & Acceptance Criteria**: Does code fulfill the feature spec in `specs/`?
2. **Security & Multi-Tenancy**: Can user data leak? Are tokens validated?
3. **Correctness & Robustness**: Will math divide by zero? Are external APIs retried?
4. **Architecture & Clean Code**: Are hooks decoupled? Are URLs centralized?
5. **Performance & Token Economy**: Are LLM calls cached? Are re-renders minimized?
6. **UX & Accessibility**: Are states handled? Are tokens respected?

---

## 📋 The Review Rubric

### 🔴 P0 — Blocker (Security, Multi-Tenancy & Regulatory)
*Flag these immediately; they block any merge or deployment.*
- [ ] **Tenant Isolation**: Does every DB query filter by `current_user.id`? Is `user_id` ever accepted from client payload?
- [ ] **Constraint Collisions**: Can duplicate submissions trigger an unhandled database `IntegrityError`?
- [ ] **Secret Exposure**: Are API keys, tokens, or tenant UUIDs checked into git or client bundles?
- [ ] **Compliance Gatekeeper**: Can any AI financial response reach the user without the mandatory `$NFA` disclaimer?

### 🟡 P1 — Correctness & Robustness (Fix Before Production)
*Issues that degrade reliability or produce incorrect financial results.*
- [ ] **Spec & Acceptance Criteria Alignment**: Does the implementation satisfy all Acceptance Criteria (AC-1 to AC-N) documented in the feature spec (`specs/upcoming/` or `specs/baseline/`)?
- [ ] **Sync/Async Mismatches**: Are LangGraph node functions mixing `async def` and `def`?
- [ ] **Financial Math Integrity**:
  - Are metrics computed over mismatched arrays (e.g. beta vs volatility length mismatch)?
  - Is there guarded fallback for missing tickers, zero shares, or delisted stocks?
- [ ] **API Resilience**: Do external scrapers (yfinance, Alpha Vantage) have bounded retries and exponential backoff?
- [ ] **Deprecated APIs**: Is `datetime.utcnow()` used instead of `datetime.now(timezone.utc)`?
- [ ] **Broken Error Handling**: Does an endpoint silently return empty lists or crash with a 500 when an external service is down?

### 🟢 P2 — Maintainability & Standards (Clean Code)
*Code quality, typing, and architectural hygiene.*
- [ ] **Configuration Centralization**: Are API routes or base URLs hardcoded instead of imported from `src/config.ts`?
- [ ] **Separation of Concerns**: Is data fetching performed inside a UI component instead of a custom hook?
- [ ] **Type Safety**: Are there loose `any` types in TypeScript or missing Pydantic schemas in FastAPI?
- [ ] **Testing**: Are new endpoints or math functions accompanied by offline unit tests in `test_unit.py`?
- [ ] **Dead Code**: Are unused stubs, commented code blocks, or debug print statements left behind?

### 💡 UX & Design Polish
*User-facing visual and interactive quality.*
- [ ] **Micro-Interactions**: Does the screen provide immediate feedback while agents reason (thinking indicators, loading spinners)?
- [ ] **Empty & Error States**: If a user has no holdings or a scraper fails, is there an informative card and a CTA button?
- [ ] **Rich Formatting**: Is LLM text rendered via structured markdown (status badges, bold metrics, bullet lists) instead of raw text?
- [ ] **Accessibility**: Are interactive elements keyboard navigable with visible focus states?

---

## 📝 Required Output Format

Structure your code review response as follows:

```markdown
# 🔍 Code Review: [Feature / PR Name]

### 📊 Summary Assessment
- **Overall Verdict**: [Approved | Changes Requested | Blocked]
- **Key Highlight**: [1-2 sentences summarizing the change]

---

### 🔴 P0 — Blockers
*(List any blockers with file links and code fixes, or write "None identified.")*

### 🟡 P1 — Correctness & Robustness
*(List any math, retry, or contract issues with recommended fixes)*

### 🟢 P2 — Maintainability & Clean Code
*(List any configuration, typing, or architecture improvements)*

### 💡 UX & Accessibility Suggestions
*(List visual polish or user experience feedback)*

---

### 🧪 Automated Verification Status
- **Backend Tests**: `uv run python -m unittest discover -s tests` → [Pass / Fail]
- **Frontend Build**: `npm run build` → [Pass / Fail]
```
