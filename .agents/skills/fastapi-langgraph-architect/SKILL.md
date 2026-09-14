---
name: fastapi-langgraph-architect
description: Guides the design, implementation, and debugging of FastAPI backends coupled with LangGraph multi-agent systems and SQLAlchemy 2.0 ORM. Use when creating API endpoints, adding agent nodes, or defining database models.
---

# FastAPI & LangGraph Architecture Playbook

This skill outlines the architectural standards and implementation recipes for building backend services and multi-agent workflows in Finnie AI.

---

## 1. LangGraph Hub-and-Spoke Pattern

Finnie AI uses a stateful hub-and-spoke graph topology defined in `backend/src/graph.py`.

### A. The Core Contract: State Immutability
All agent nodes receive `state: FinnieState` and return a dictionary delta. Never modify the input state dictionary directly.

```python
# ✅ Correct
def my_agent_node(state: FinnieState) -> dict:
    user_message = state["messages"][-1].content
    # Compute or call LLM...
    return {"messages": [AIMessage(content="Result text")]}
```

### B. Sync vs Async Alignment
In Finnie AI, all graph nodes are **synchronous `def`**. Never declare an agent node as `async def` in a synchronous graph, as mixed dispatch causes event-loop deadlocks during execution.

### C. The Supervisor Router & Direct Bypass
- **General Inquiries (`/chat`)**: Enter at `START` → `supervisor_node` → route to specialized worker based on intent.
- **Specialized API Endpoints (`/portfolio/analysis`, `/goals/calculate`)**: Inject `next_step="PORTFOLIO_ANALYST"` or `next_step="GOAL_STRATEGIST"` into initial state. The conditional edge `start_node` routes directly to the worker, bypassing the supervisor LLM call to save tokens and eliminate latency.

### D. Compliance Gatekeeper
Every agent node path terminates at `compliance_guardian_node` before reaching `END`.

---

## 2. FastAPI Endpoint Architecture

### A. Multi-Tenant Injection
Every protected endpoint handler must resolve tenant identity from the JWT dependency:

```python
from src.auth.jwt import get_current_user
from src.models.user import User

@app.get("/portfolio")
def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    effective_id = current_user.id
    rows = db.query(Holding).filter(Holding.user_id == effective_id).all()
    return HoldingResponse(...)
```

### B. Defensive Bulk Ingestion
When accepting lists of records, defensively aggregate duplicates before inserting:

```python
# Aggregate duplicate (ticker, exchange) pairs
consolidated = {}
for h in req.holdings:
    key = (h.ticker.upper(), h.exchange.upper())
    if key in consolidated:
        consolidated[key]["shares"] += h.shares
    else:
        consolidated[key] = { ... }

for item in consolidated.values():
    db.add(Holding(**item))
db.commit()
```

---

## 3. Database & ORM Standards (SQLAlchemy 2.0)

- **Database Agnosticism**: Use standard SQLAlchemy models. The application runs on SQLite in local/dev and seamlessly targets PostgreSQL in production via `DATABASE_URL`.
- **Timezone-Aware Timestamps**:
  ```python
  from datetime import datetime, timezone
  created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
  ```
- **Composite Unique Constraints**:
  ```python
  __table_args__ = (
      UniqueConstraint("user_id", "ticker", "exchange", name="uq_user_ticker_exchange"),
  )
  ```

---

## 4. Indentation, Formatting & Code Style Conventions

All backend Python code must follow these strict syntactic standards:
- **Indentation**: STRICT **4 spaces per indentation level** (PEP 8). NEVER use tab characters (`\t`).
- **Line Length**: Max **100 characters** per line.
- **Quotes**: Double quotes (`"..."`) for strings and docstrings; single quotes (`'...'`) acceptable for internal dictionary keys.
- **Blank Lines**: 2 blank lines between top-level classes/functions; 1 blank line between methods within a class.
- **Naming Conventions**:
  - Modules: `snake_case.py`
  - Models / Classes: `PascalCase`
  - Functions / Methods / Variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
- **Import Organization**:
  ```python
  # 1. Standard library
  import os
  from datetime import datetime, timezone
  # 2. Third-party packages
  from fastapi import APIRouter, Depends, HTTPException
  from sqlalchemy.orm import Session
  from pydantic import BaseModel
  # 3. Internal application modules
  from src.database import get_db
  from src.models.user import User
  from src.auth.jwt import get_current_user
  ```

---

## 5. Lifecycle: How to Structure New Backend Functionality

When introducing ANY new backend agent, endpoint, or analytical capability, follow this 6-step lifecycle:

```text
1. Model (src/models/) ──> 2. Schemas (src/models/) ──> 3. Business Node (src/agents/ or utils/)
                                                              │
6. Offline Tests (tests/) <── 5. Route (main.py) <────── 4. Graph Wiring (src/graph.py)
```

1. **Step 1: Database ORM Entity (`src/models/<domain>.py`)**:
   Define model with indexed `user_id`, composite `UniqueConstraint`, and timezone-aware `created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))`.
2. **Step 2: Pydantic Schemas (`src/models/<domain>_schemas.py` or `chat.py`)**:
   Define type-safe `Request` and `Response` models with Pydantic v2 validation.
3. **Step 3: Analytical Logic / Agent Node (`src/agents/<name>.py`)**:
   Implement synchronous `def agent_node(state: FinnieState) -> dict`. Guard calculations with `valid_symbols` and add 3-attempt exponential backoff retries for external market calls.
4. **Step 4: LangGraph Routing (`src/graph.py`)**:
   Register node with `workflow.add_node(...)`. Ensure all paths route to `compliance_guardian_node` before reaching `END`.
5. **Step 5: FastAPI REST Endpoint (`main.py`)**:
   Inject `current_user: User = Depends(get_current_user)` and derive `effective_id = current_user.id`. Defensively aggregate duplicate inputs.
6. **Step 6: Offline Unit Tests (`tests/test_unit.py`)**:
   Write mock-based unit tests verifying mathematical bounds, edge cases, and schema validation.
   Run: `uv run python -m unittest discover -s tests`.

---

## 6. Verification Recipe

After modifying any backend agent or endpoint:
1. Run unit test suite:
   ```bash
   cd backend
   uv run python -m unittest discover -s tests
   ```
2. Verify all tests pass without errors or deprecation warnings.

