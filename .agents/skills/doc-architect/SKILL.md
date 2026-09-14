---
name: doc-architect
description: Guides the structured synchronization of technical and functional documentation for Finnie AI. Only activate when a feature is 100% completed, all tests pass, and the developer has explicitly approved updating documentation.
---

# Documentation Architect Playbook (Technical & Functional)

This skill governs how technical and functional documentation is maintained across Finnie AI.

---

## 🛑 The Execution Gate (Strict Developer Handshake)

To prevent unwanted file churn during active development, follow this **Human-in-the-Loop Protocol**:

1. **NEVER update documentation during active coding iterations or intermediate debugging.**
2. **Prerequisites before even asking**:
   - All code is written and formatted according to repo standards.
   - Backend unit tests pass: `uv run python -m unittest discover -s tests`.
   - Frontend build succeeds: `npm run build`.
3. **The Developer Handshake**:
   When the above are green, you MUST pause, summarize what changed, and ask the developer for permission using this exact template:

```markdown
### 📋 Feature Verified & Complete: [Feature Name]
All code changes are implemented and verified:
- Backend: 14/14 unit tests passing
- Frontend: 0 errors / 0 warnings on production build

### 📚 Proposed Documentation Updates
Based on these changes, the following documents should be synchronized:
1. **[Technical]** `README.md` — [Specify: e.g., Update endpoint table with POST /new-route]
2. **[Technical]** `docs/DESIGN.md` — [Specify: e.g., Add sequence diagram for new agent node]
3. **[Functional]** `docs/PROGRESS_LOG.md` — [Specify: e.g., Record feature completion with date & test results]
4. **[Functional]** `docs/PROJECT_PLAN.md` — [Specify: e.g., Mark roadmap milestone as complete]

Would you like me to proceed with updating these documents?
```

4. **DO NOT modify any doc file until the developer responds with approval** (`"yes"`, `"proceed"`, `"approved"`, etc.).

---

## 🗺️ Change-to-Document Mapping Matrix

Once approved by the developer, inspect what changed in the codebase and update the corresponding documents:

| Component Changed in Code | Technical Documentation Target | Functional Documentation Target |
|---|---|---|
| **New Feature / Capability** | Promote `specs/upcoming/SPEC-XX.md` ➔ `specs/baseline/` | `docs/FEATURES_AND_AGENTS.md`, `README.md` |
| **API Endpoints / Schemas** (`main.py`, `models/`) | `README.md` (Endpoint Table), `docs/FEATURES_AND_AGENTS.md` | `specs/baseline/SPEC-XX.md` (Contract & ACs) |
| **Agent Nodes / Graph Flow** (`graph.py`, `agents/`) | `docs/ARCHITECTURE.md`, `docs/FEATURES_AND_AGENTS.md` | User-facing workflow & compliance disclaimers |
| **Financial Math / Scrapers** (`simulation.py`, `portfolio_analyst.py`) | `docs/FEATURES_AND_AGENTS.md` (Formulas, Retries) | `specs/baseline/SPEC-02/03.md` (Domain rules) |
| **UI Components / Tabs** (`components/`, `hooks/`) | `docs/UI_DESIGN_SYSTEM.md`, `frontend/src/config.ts` | User Journey & Component State Guide |
| **Knowledge Base & RAG** (`vector_store.py`, `data/`) | `docs/KNOWLEDGE_BASE_AND_RAG.md` | Grounding sources & regulatory corpus |
| **Deployment / Environment** (`Dockerfile`, compose, env) | `docs/DEPLOYMENT.md` | Deployment runbook & health checks |

---

## ✍️ Dual-Perspective Writing Guidelines

### 1. Technical Documentation Standards (For Engineers & AI Agents)
- **Precision & Code Links**: Always cite exact file paths using markdown links (e.g. [`main.py`](file:///Users/prajosh/Development/finnie-ai/backend/main.py)).
- **Contract Accuracy**: Document request/response JSON shapes, required headers (`Authorization: Bearer <token>`), and HTTP status codes.
- **Architectural Diagrams**: Use GitHub Flavored Mermaid diagrams for workflows and sequence flows.
  - Wrap node labels with quotes if they contain punctuation or spaces: `id["Label (Context)"]`.
- **Failure Modes & Edge Cases**: Explicitly document fallback behaviors (e.g., exponential backoff retries, `null` returns, defensive casing normalization).

### 2. Functional Documentation Standards (For Users & Stakeholders)
- **The "Why" and "What"**: Explain the user problem being solved before detailing the solution.
- **Plain-English Explanations**: Explain financial concepts without assuming Wall Street jargon (e.g., explain HHI as *"Concentration Risk: tells you if you have all your eggs in one tech basket"*).
- **Visual State Guidance**: Describe what the user will see in the UI:
  - What does the loading state look like?
  - What do the status badges (`ON TRACK`, `CAUTION`, `AT RISK`) mean?
  - What should the user do if an error occurs?
- **Step-by-Step User Journey**: Provide clear steps to test the feature from the browser (e.g., *"Navigate to Goal Planner → Set target year to 2040 → Click Generate Roadmap"*).

---

## 🧪 Documentation Quality Checklist
Before concluding documentation updates:
- [ ] No broken internal markdown links.
- [ ] Mermaid diagrams render cleanly without syntax errors.
- [ ] Timestamps, versions, and changelogs are updated to current date.
- [ ] Code snippets in markdown match actual current implementations (no stale signatures).
