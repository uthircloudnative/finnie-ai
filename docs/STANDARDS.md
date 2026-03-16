# Finnie AI: Engineering Standards & Guidelines

This document serves as the source of truth for all code implementations in the Finnie AI project. Following these guidelines ensures consistency, readability, and long-term maintainability.

---

## 1. General Principles
### 1.1 KISS (Keep It Simple, Stupid)
- Avoid over-engineering. Solve the problem with the simplest, most readable solution first.

### 1.2 DRY (Don't Repeat Yourself)
- Extract common logic into reusable functions or components.
- However, follow the Rule of Three: only abstract when you see a pattern used three times.

### 1.3 Clean Code Basics
- **Meaningful Names**: Variables and functions should describe their intent (e.g., `get_user_portfolio()` instead of `get_data()`).
- **Small Functions**: Functions should do one thing and do it well. Aim for < 20 lines.

---

## 2. Project Directory Structure
All code must adhere to the following organized structure:

### 2.1 Backend (Python/FastAPI)
- `backend/src/agents/`: Specialized LangGraph worker nodes (e.g., `portfolio_analyst.py`).
- `backend/src/tools/`: Custom external tool integrations (e.g., `alpha_vantage_client.py`).
- `backend/src/models/`: Pydantic schemas for data validation and API request/response.
- `backend/src/utils/`: Shared utility functions (e.g., `llm_factory.py`, `logger.py`).
- `backend/tests/`: Unit and integration test suites.

### 2.2 Frontend (React/TypeScript)
- `frontend/src/components/`: Reusable UI components (e.g., `DashboardCard/`).
- `frontend/src/hooks/`: Custom React hooks for business logic and data fetching.
- `frontend/src/styles/`: Global CSS variables and shared style modules.
- `frontend/src/assets/`: Static images, icons, and fonts.
- `frontend/public/`: Root-level static assets.

---

## 3. Backend Standards (Python & FastAPI)
### 2.1 Type Hinting
- **Strict Typing**: All function signatures must include type hints for parameters and return values.
- **Pydantic**: Use Pydantic models for all Request and Response bodies to ensure data validation.

### 2.2 Error Handling
- Use specific exceptions, not generic `Exception`.
- FastAPI specific: Use `HTTPException` for client-facing errors with clear status codes.

### 2.3 Async/Await
- Use `async` for I/O bound operations (API calls, DB queries).
- Do not block the event loop with synchronous operations in async routes.

### 2.4 Documentation
- Use Google-style docstrings for complex logic.
- Keep comments focused on "Why" something is done, rather than "What" (the code should be the "What").

---

## 3. Frontend Standards (React & TypeScript)
### 3.1 Component Architecture
- **Functional Components only**: Use React Hooks (never Classes).
- **Separation of Concerns**: Keep business logic in custom hooks (`/hooks`) and UI in components (`/components`).

### 3.2 State Management
- Prefer local state (`useState`, `useReducer`) or Context API for simple needs.
- Keep the state as close as possible to where it's used.

### 3.3 CSS & Styling
- Use **Vanilla CSS Modules** or standard CSS with a clear naming convention (BEM preferred if not using modules).
- Avoid inline styles unless dynamic.

### 3.4 Design Tokens (Glassmorphism)
- Use CSS variables for the "Glass-Finance" theme (colors, opacity, blurs) to ensure UI consistency.

---

## 4. Multi-Agent (LangGraph) Specifics
### 4.1 State Immutability
- Always treat the Graph State as immutable; return updates rather than modifying the state in-place.

### 4.2 Deterministic Routing
- Conditional edges should have clear, loggable logic to make debugging agent decisions easier.

---

## 5. Deployment & Git
- **AI Assistant Policy (CRITICAL)**: The AI Assistant must NEVER run `git commit` or `git push` automatically. Always allow the USER to manually review the `git status` or `git diff` first, and only execute commits or pushes when explicitly commanded to do so.
- **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat: add goal planning simulation`).
- **Review Culture**: All code changes should ideally be reviewed against these standards.
