# Backend & Architecture Standards — Finnie AI

This document establishes the mandatory architectural, security, and coding standards for all backend services in Finnie AI.

---

## 1. Python Environment & Version Standards
- **Python Version**: Strict Python 3.13 compatibility.
- **Package Management**: Managed via Astral's `uv`. Run all commands using `uv run ...`.
- **Datetime Modernization**:
  - `datetime.utcnow()` is strictly banned (deprecated in Python 3.12+).
  - Use `datetime.now(timezone.utc)` for all timestamps and default factory callables:
    ```python
    # ✅ Correct
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ```
  - When calculating ages against timestamps retrieved from legacy SQLite storage (which might strip timezone metadata), defensively normalize naive timestamps before subtraction:
    ```python
    now = datetime.now(timezone.utc)
    ts = self.timestamp
    if ts is not None and ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age = now - ts
    ```

---

## 2. Security & Multi-Tenant Data Isolation
- **Authentication**: Stateless HMAC-SHA256 JWT tokens via `python-jose` with direct `bcrypt` password hashing (bypassing `passlib` version incompatibilities with Python 3.13).
- **Tenant Context**:
  - Every protected endpoint MUST declare `current_user: User = Depends(get_current_user)`.
  - Derive `effective_id = current_user.id`. NEVER accept `user_id` as a client-supplied query, path, or body parameter for data access.
- **Database Schema Constraints**:
  - Every tenant-scoped model MUST include an indexed `user_id` column.
  - Declare composite unique constraints to prevent duplicate resource creation:
    ```python
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", "exchange", name="uq_user_ticker_exchange"),
    )
    ```
- **Defensive Ingestion**:
  - Endpoint handlers that accept bulk inputs (e.g., `POST /portfolio/save`) MUST aggregate and deduplicate items in memory before issuing database `INSERT` commands.

---

## 3. LangGraph Orchestrator & Node Conventions
- **Uniform Signatures**:
  - All nodes in a compiled graph MUST share the same sync/async signature. In Finnie AI, all node functions are synchronous:
    ```python
    def node_name(state: FinnieState) -> dict:
        ...
        return {"messages": [AIMessage(...)], ...}
    ```
- **State Immutability**:
  - Never mutate `state` in-place. Return partial state delta dictionaries that LangGraph merges into `FinnieState`.
- **Supervisor Routing & Intent Bypass**:
  - General chat queries route through `supervisor_node` using structured outputs (`RoutingDecision`).
  - Dedicated REST endpoints (e.g. `POST /portfolio/analysis`) may inject `next_step` directly to bypass LLM supervisor reasoning and save tokens/latency.
- **Compliance Gateway**:
  - The compiled graph MUST route all agent paths through `compliance_guardian_node` before reaching `END`.

---

## 4. API Schema & Error Handling
- **Pydantic v2 Boundaries**:
  - Every endpoint MUST have typed request (`BaseModel`) and response (`BaseModel`) schemas.
  - Return standardized HTTP status codes: `400` for invalid inputs, `401` for unauthorized, `404` for missing records, `500` with clear diagnostic messages for unhandled exceptions.
- **CORS Configuration**:
  - CORS middleware MUST read `ALLOWED_ORIGINS` from environment variables, defaulting safely to local development ports (`http://localhost:5173`, `http://localhost:5174`).

---

## 5. Indentation, Formatting & Code Style Conventions
- **Indentation**:
  - STRICT **4 spaces per indentation level**. NEVER use tab characters (`\t`).
  - Continuation lines must align with wrapped elements or use a hanging 4-space indent.
- **Line Length & Whitespace**:
  - Maximum line length is **100 characters** (soft limit 120 for long docstrings/SQL statements).
  - 2 blank lines before top-level functions and classes; 1 blank line between methods inside a class.
- **Naming Conventions**:
  - **Modules / Files**: `snake_case.py` (e.g., `portfolio_analyst.py`, `market_cache.py`).
  - **Classes / Models**: `PascalCase` (e.g., `FinancialGoal`, `Holding`, `FinnieState`).
  - **Functions & Variables**: `snake_case` (e.g., `compute_hhi_diversification`, `effective_id`).
  - **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TTL_MINUTES`, `ALLOWED_ORIGINS`).
  - **FastAPI Endpoints**: Pluralized lower-case kebab or slash routes (e.g., `/portfolio/analysis`, `/market/news`).
- **Import Ordering & Grouping** (separated by single blank line):
  1. Standard library imports (`os`, `sys`, `datetime`, `uuid`)
  2. Third-party library imports (`fastapi`, `pydantic`, `sqlalchemy`, `langgraph`)
  3. Internal application imports (`src.models...`, `src.auth...`, `src.utils...`)

---

## 6. Lifecycle: How to Structure New Backend Functionality
When introducing ANY new backend capability or agent workflow, follow this 6-step order:

```text
1. Model (src/models/) ──> 2. Schemas (src/models/) ──> 3. Business Node (src/agents/ or utils/)
                                                              │
6. Offline Tests (tests/) <── 5. Route (main.py) <────── 4. Graph Wiring (src/graph.py)
```

1. **Step 1: Database ORM Entity (`src/models/<domain>.py`)**:
   - Define model inheriting from `Base`.
   - Include `user_id` (indexed), UTC `created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))`.
   - Add composite `UniqueConstraint` where duplicates are prohibited.
2. **Step 2: API Contract & Pydantic Schemas (`src/models/<domain>_schemas.py` or `chat.py`)**:
   - Define explicit `Input` and `Response` Pydantic models with field validation.
3. **Step 3: Analytical Logic / Agent Node (`src/agents/<agent_name>.py`)**:
   - Implement synchronous function `def agent_node(state: FinnieState) -> dict`.
   - Bounded mathematical operations: use `valid_symbols` filters, handle zero-division, and wrap external scrapers with 3-attempt exponential backoff retries.
4. **Step 4: LangGraph Routing (`src/graph.py`)**:
   - Register node in `workflow.add_node("<agent_name>", agent_node)`.
   - Add conditional edge from `supervisor_node` AND wire transition directly to `compliance_guardian_node`.
5. **Step 5: FastAPI REST Endpoint (`main.py`)**:
   - Inject `current_user: User = Depends(get_current_user)`.
   - Derive `effective_id = current_user.id`.
   - Defensively consolidate duplicate inputs before database insertion.
6. **Step 6: Offline Unit Verification (`tests/test_unit.py`)**:
   - Write offline mock-based unit tests asserting mathematical correctness, edge cases, and schema validation without external network calls.
   - Run `uv run python -m unittest discover -s tests`.
7. **Step 7: Documentation Sync Gate (Human-in-the-Loop)**:
   - When Step 6 passes cleanly, present the completed feature to the developer and propose updating technical and functional documentation (`README.md`, `docs/DESIGN.md`, `docs/PROGRESS_LOG.md`).
   - NEVER update documentation without explicit developer approval.


