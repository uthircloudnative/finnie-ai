# AGENTS.md — Universal Agent Constitution & Repository Guide

Welcome, Agent! This document is the single source of truth for all AI coding assistants (Google Antigravity, Claude Code, Cursor, GitHub Copilot, Codex) interacting with **Finnie AI**. Follow these guidelines strictly.

---

## 🏛️ Project Architecture & Tech Stack

Finnie AI is a multi-agent financial guidance platform designed around a **"Dashboard-First, Agent-Assisted"** user experience.

- **Backend**: Python 3.13 · FastAPI · LangGraph (Hub-and-Spoke Stateful Graph) · SQLAlchemy 2.0 ORM (SQLite for local/dev, PostgreSQL cloud-ready) · ChromaDB Vector Store · yfinance & Alpha Vantage financial scrapers.
- **Frontend**: React 19 · TypeScript 5.7 · Vite 6 · Vanilla CSS Design System with Glassmorphism tokens (`tokens.css`, `global.css`) · Recharts visualization.
- **Security & Multi-Tenancy**: Stateless JWT authentication (`python-jose`, direct `bcrypt`), tenant data isolation on every endpoint, composite database unique constraints.
- **Compliance**: SEC/FINRA regulatory compliance post-processor node enforcing `$NFA` (Not Financial Advice) disclaimers on all outputs.

---

## 📂 Repository Directory Layout

```text
finnie-ai/
├── AGENTS.md                         # This file (universal agent entrypoint)
├── .agents/                          # Customizations & specialized skills
│   ├── rules/                        # Always-on modular standards
│   │   ├── backend_standards.md      # Python, FastAPI, SQLAlchemy, LangGraph
│   │   ├── frontend_standards.md     # React 19, TypeScript, Custom Hooks
│   │   └── ux_design_standards.md    # Glass-Finance tokens, accessibility, states
│   └── skills/                       # Executable playbooks (with YAML frontmatter)
│       ├── fullstack-code-review/    # Senior P0/P1/P2/UX review rubric
│       ├── fastapi-langgraph-architect/ # Graph topology & backend patterns
│       ├── react-glass-ui/           # Component & design token craft
│       ├── finnie-domain-guardian/   # $NFA compliance, financial math & RAG
│       ├── spec-driven-dev/          # Spec-driven development lifecycle & promotion
│       └── doc-architect/            # Human-in-the-loop documentation synchronization
├── specs/                            # Spec-Driven Development (SDD) source of truth
│   ├── baseline/                     # Production-verified specifications (SPEC-01 to SPEC-05)
│   └── upcoming/                     # Proposed & in-flight feature specifications
├── backend/                          # FastAPI + LangGraph application
│   ├── main.py                       # REST API endpoints & route handlers
│   ├── src/
│   │   ├── agents/                   # LangGraph agent node implementations
│   │   ├── auth/                     # JWT tokens & bcrypt password hashing
│   │   ├── models/                   # SQLAlchemy ORM & Pydantic API schemas
│   │   └── utils/                    # Simulations, vector store, scrapers
│   └── tests/                        # Offline unit tests (test_unit.py)
├── frontend/                         # Vite + React 19 SPA
│   ├── src/
│   │   ├── components/               # Pure presentational UI components
│   │   ├── context/                  # AuthContext and global session state
│   │   ├── hooks/                    # Custom hooks owning all API calls & caching
│   │   ├── config.ts                 # Centralized API_BASE and route endpoints
│   │   └── styles/                   # tokens.css and global.css design system
│   └── package.json
└── docs/                             # Deep-dive architecture & planning docs
```

---

## ⚡ Mandatory Golden Rules for Agents

1. **Multi-Tenant Isolation (Non-Negotiable)**:
   - NEVER accept raw user IDs from request bodies or URLs for authorization.
   - ALWAYS inject `current_user: User = Depends(get_current_user)` and use `effective_id = current_user.id`.
2. **LangGraph Node Uniformity**:
   - All LangGraph node functions MUST maintain uniform async signatures. If the graph uses synchronous dispatch, all nodes must be `def node(state: FinnieState) -> dict`. Do NOT mix `async def` and `def` nodes.
   - Every node MUST route to `compliance_guardian_node` before reaching `END`.
3. **No Deprecated Python APIs**:
   - Do NOT use `datetime.utcnow()`. ALWAYS use `datetime.now(timezone.utc)`.
4. **Centralized Frontend Config**:
   - NEVER hardcode `localhost:8000` or API URLs in frontend files. ALWAYS import `API_BASE` or `API_ENDPOINTS` from `src/config.ts`.
5. **Decoupled React Architecture**:
   - UI components MUST NOT execute direct `fetch` calls. All networking, caching, and state management belongs in custom hooks (`src/hooks/`).
6. **Financial Math Defensive Bounds**:
   - Never compute averages over mismatched symbol arrays. Build metric arrays exclusively from `valid_symbols`.
   - External market calls (yfinance info lookups) MUST include exponential backoff retries (3 attempts).
7. **Strict Indentation & Code Formatting**:
   - **Backend**: Strict **4 spaces per indent** (PEP 8). No tabs. `snake_case` functions/modules, `PascalCase` classes/models, `UPPER_SNAKE_CASE` constants. Max 100 chars/line.
   - **Frontend**: Strict **2 spaces per indent**. No tabs. No semicolons. Single quotes for strings. `PascalCase` components, `camelCase` hooks/functions.
8. **Structured Lifecycle for New Functionality**:
   - **New Backend Feature**: Model (`src/models/`) → Schemas (`src/models/`) → Agent Node (`src/agents/`) → Graph Wiring (`src/graph.py`) → REST Route (`main.py`) → Unit Tests (`tests/test_unit.py`).
   - **New Frontend View**: Endpoint (`src/config.ts`) → Types → Custom Hook (`src/hooks/`) → Component (`src/components/` with skeleton/empty/error states) → View/Sidebar wiring → `npm run build`.
9. **Verification Before Concluding**:
   - Backend changes MUST pass: `uv run python -m unittest discover -s tests` (inside `backend/`).
   - Frontend changes MUST pass: `npm run build` (inside `frontend/`).
10. **Feature Completion & Documentation Gate (Human-in-the-Loop)**:
    - Documentation is NEVER modified on granular code edits or during intermediate debugging.
    - ONLY when a feature is fully completed and all verification tests pass, the agent MUST summarize the completed feature, list the affected technical and functional doc files, and **explicitly ask the developer for permission** before updating documentation.
    - Only proceed with documentation updates after receiving the developer's explicit approval.
11. **Spec-Driven Development (SDD)**:
    - All new features or non-trivial architectural enhancements MUST originate with a specification drafted in `specs/upcoming/` using `specs/upcoming/SPEC_TEMPLATE.md`.
    - Implementation begins only after Acceptance Criteria and contracts are defined.
    - Upon verification, specs are promoted to `specs/baseline/`.

---

## 📚 Skill References

When performing specific workflows, activate the specialized skills in `.agents/skills/`:
- **Code Review**: Read [`.agents/skills/fullstack-code-review/SKILL.md`](file:///.agents/skills/fullstack-code-review/SKILL.md)
- **Backend & LangGraph Engineering**: Read [`.agents/skills/fastapi-langgraph-architect/SKILL.md`](file:///.agents/skills/fastapi-langgraph-architect/SKILL.md)
- **Frontend & Glass UI Design**: Read [`.agents/skills/react-glass-ui/SKILL.md`](file:///.agents/skills/react-glass-ui/SKILL.md)
- **Financial Domain & Compliance**: Read [`.agents/skills/finnie-domain-guardian/SKILL.md`](file:///.agents/skills/finnie-domain-guardian/SKILL.md)
- **Spec-Driven Development**: Read [`.agents/skills/spec-driven-dev/SKILL.md`](file:///.agents/skills/spec-driven-dev/SKILL.md)
- **Documentation Architect**: Read [`.agents/skills/doc-architect/SKILL.md`](file:///.agents/skills/doc-architect/SKILL.md)


