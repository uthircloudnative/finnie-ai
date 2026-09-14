# Baseline Spec: SPEC-03 — Goal Strategist & Monte Carlo GPS

> **Status**: 🟢 **VERIFIED & IN PRODUCTION**  
> **Scope**: Long-Term Wealth Planning, 10,000-Path Monte Carlo Simulation, Regional Tax RAG, Roadmap Presentation

---

## 1. 🎯 Business Objective & Domain Rules
- **Problem**: Investors pursuing long-term financial milestones (retirement, home purchase, college savings) often rely on naive, static compound-interest calculators that ignore market volatility, sequence-of-returns risk, and regional tax-advantaged account limits.
- **Monte Carlo Modeling**: Projections must evaluate uncertainty using a **10,000-iteration geometric Brownian motion** simulation parameterized by the investor's current portfolio annualized volatility ($\sigma$) and expected drift ($\mu$):
  $$S_t = S_0 \exp\left(\left(\mu - \frac{1}{2}\sigma^2\right)t + \sigma \sqrt{t} Z\right)$$
- **Percentile Invariant Rule**: Confidence bounds must strictly satisfy:
  $$P_{05} \le \text{Median} \le P_{95}$$
  A goal target falling below $P_{05}$ is categorized as high confidence (>90%), while one above $P_{95}$ indicates a high-risk trajectory.
- **Regional Statute & Tax RAG**: Projections must retrieve statutory annual contribution caps and tax rules from the ChromaDB collection `goal_rules` based on the user's jurisdiction (e.g. IRS 401(k) / Roth IRA limits in the US; Section 80C / NPS limits in India).
- **Mandatory Compliance**: All synthesized roadmaps must conclude with the regulatory `$NFA` disclaimer.

---

## 2. 🔌 Technical Contracts & Endpoints

### A. API Endpoints
- `GET /goals`: Fetches the authenticated user's current active goal configuration.
- `POST /goals/calculate`: Dispatches simulation and synthesis engine:
  - **Request Body**:
    ```python
    class GoalRequest(BaseModel):
        target_amount: float
        target_year: int
        initial_amount: float
        monthly_contribution: float
        country: Optional[str] = "US"
        risk_tolerance: Optional[str] = "moderate"
    ```
  - **Response Payload**:
    ```python
    class GoalResponse(BaseModel):
        confidence_score: float         # Percentage 0.0 to 100.0
        p05_outcome: float
        median_outcome: float
        p95_outcome: float
        roadmap_markdown: str           # Synthesized strategic plan
        recommended_allocation: Dict[str, float]
        disclaimer: str
    ```

### B. Agent Topology & LangGraph Wiring
- **Node Function**: Synchronous `def goal_strategist_node(state: FinnieState) -> dict`.
- **Simulation**: Executed in `backend/src/utils/simulation.py` via vectorized NumPy operations across 10,000 trajectory paths.
- **RAG Integration**: Queries `goal_rules` collection using semantic search conditioned on `country`.
- **Graph Path**: `supervisor_node` ➔ `goal_strategist_node` ➔ `compliance_guardian_node` ➔ `END`.

---

## 3. 🖥️ Frontend Architecture & Presentation
- **Hook**: `useGoalStrategist.ts`:
  - Handles simulation parameter state, submission dispatch, and local goal persistence.
- **Components**:
  - `GoalPlanner.tsx`: Glassmorphic simulation control panel, probability fan chart (Recharts), and confidence gauge.
  - `RoadmapRenderer.tsx`: Zero-dependency custom markdown parser rendering:
    - Glowing status chips: `.status-on-track` (`● ON TRACK`), `.status-caution` (`▲ CAUTION`), `.status-at-risk` (`■ AT RISK`).
    - Milestone checkpoints (`Phase 1`, `Phase 2`, `Target Horizon`).
    - Regulatory callout banners with glassmorphism borders for `$NFA` notices.

---

## 4. ✅ Verified Acceptance Criteria (Regression Baseline)
- [x] **AC-1**: Running 10,000 Monte Carlo paths produces monotonic outcomes ($P_{05} \le \text{Median} \le P_{95}$).
- [x] **AC-2**: Specifying a 0-year target horizon returns `confidence_score = 0.0` with median equal to initial capital without division-by-zero errors.
- [x] **AC-3**: Tax contribution limits for the selected jurisdiction (e.g. US 401(k) / IRA) are incorporated into the synthesized roadmap markdown.
- [x] **AC-4**: `RoadmapRenderer.tsx` accurately parses markdown headers (`###`), bullet lists, and status chips without external heavyweight DOM parsers.
- [x] **AC-5**: Offline unit tests in `test_unit.py` (`test_monte_carlo_positive_horizon`, `test_monte_carlo_zero_horizon`, `test_goal_model_validation`) pass cleanly.
