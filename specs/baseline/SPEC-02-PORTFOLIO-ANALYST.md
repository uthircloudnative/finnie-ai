# Baseline Spec: SPEC-02 — Multi-Market Portfolio Analyst

> **Status**: 🟢 **VERIFIED & IN PRODUCTION**  
> **Scope**: Portfolio Diagnostics, Country Benchmarks, HHI Diversification, LangGraph Agent

---

## 1. 🎯 Business Objective & Domain Rules
- **Problem**: Individual investors holding assets across multi-jurisdictional markets (US, India, UK, Canada, Germany) lack institutional-grade portfolio risk diagnostics (Market Beta, Annualized Volatility, Sector Diversification) tailored to their local geographic markets without expensive advisory fees.
- **Country Benchmark Mapping**: Every country portfolio must be benchmarked against its primary domestic index:
  - `US` ➔ `^GSPC` (S&P 500)
  - `IN` ➔ `^NSEI` (NIFTY 50)
  - `UK` ➔ `^FTSE` (FTSE 100)
  - `CA` ➔ `^GSPTSE` (S&P/TSX Composite)
  - `DE` ➔ `^GDAXI` (DAX Performance Index)
  - `ALL` ➔ `^GSPC` (Global baseline)
- **Herfindahl-Hirschman Index (HHI) Diversification**: Sector concentration is calculated strictly via HHI:
  $$HHI = \sum (\text{sector\_weight}_i)^2$$
  $$\text{Diversification Score} = 10 \times \left(1 - \frac{HHI - HHI_{min}}{1 - HHI_{min}}\right)$$
  where $HHI_{min} = 1 / N_{sectors}$.
- **Regulatory Compliance**: Every portfolio diagnosis must be routed through `compliance_guardian_node` to append the mandatory `$NFA` disclaimer before delivery.

---

## 2. 🔌 Technical Contracts & Endpoints

### A. API Endpoints
- `GET /portfolio/analysis?country={country}`: Returns comprehensive risk metrics (Beta, Volatility, HHI score, sector breakdown) and AI 3-card strategic insights.
- `GET /portfolio/diversification?country={country}`: Returns fast, on-demand sector breakdown and HHI diversification score without running full LLM synthesis.

### B. Analytical Math Guardrails
- **Defensive Symbol Array Alignment (`valid_symbols`)**:
  Market Beta and Volatility calculations compute returns across price series. Both arrays are built strictly from the intersection of valid ticker return series and benchmark data:
  ```python
  valid_symbols = [s for s in symbols if s in asset_returns and s in asset_vols]
  ```
  Symbols with missing history or unmapped benchmarks are safely excluded without crashing array calculations.
- **Exponential Backoff Scraper Retries**:
  External calls to Yahoo Finance (`yf.Ticker(sym).info`) employ a 3-attempt exponential backoff retry loop (`attempts=3, delay=1.0, backoff=2.0`). If rate limits persist, sector is labeled `"Unknown"` and `diversification_score` safely defaults to `None`.

### C. Agent Topology & LangGraph Wiring
- **Node Function**: Synchronous `def portfolio_analyst_node(state: FinnieState) -> dict`.
- **Knowledge Base**: Retrieves quantitative risk heuristics from ChromaDB collection `analytical_kb` (`k=3`).
- **Graph Path**: `supervisor_node` ➔ `portfolio_analyst_node` ➔ `compliance_guardian_node` ➔ `END`.

---

## 3. 🖥️ Frontend Architecture & Presentation
- **Hook**: `useCountryPortfolio.ts` handles:
  - Multi-tab country switching (`ALL`, `US`, `IN`, `UK`, etc.).
  - Session-level caching in state to prevent duplicate LLM invocations when switching between tabs.
  - Dedicated `fetchDiversification(country)` trigger for retry upon scraper timeout.
- **Component**: `PortfolioAnalyst.tsx`:
  - 3-card modular insight display: **Risk Profile**, **Diversification Assessment**, and **Recommended Next Steps**.
  - Sector allocation breakdown bar chart with color-coded badges.
  - Interactive retry button for HHI sector calculations.

---

## 4. ✅ Verified Acceptance Criteria (Regression Baseline)
- [x] **AC-1**: Requesting `/portfolio/analysis?country=IN` evaluates covariance against `^NSEI` rather than `^GSPC`.
- [x] **AC-2**: Portfolios with a single holding yield an HHI score of 0.0 (maximum sector concentration).
- [x] **AC-3**: Portfolios with missing ticker price history exclude the delisted ticker via `valid_symbols` guard and calculate remaining portfolio metrics without throwing a 500 error.
- [x] **AC-4**: Every response string contains the compliance suffix `"$NFA: Finnie AI is an educational guidance tool"`.
- [x] **AC-5**: Offline unit tests in `test_unit.py` (`test_compute_hhi_single_sector`, `test_compute_hhi_multi_sector`, `test_compute_hhi_empty`) pass cleanly.
