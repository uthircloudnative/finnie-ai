# Baseline Spec: SPEC-05 — Global Wealth Executive Dashboard

> **Status**: 🟢 **VERIFIED & IN PRODUCTION**  
> **Scope**: High-Speed Holdings Overview, Batch Market Data Ingestion, Programmatic P&L Calculations

---

## 1. 🎯 Business Objective & Domain Rules
- **Problem**: Investors managing holdings across domestic and international accounts require an instantaneous, aggregated overview of their positions, current valuations, and daily unrealized profit/loss (P&L) without enduring LLM generation latency.
- **Zero-LLM Latency Rule**: The Executive Dashboard is strictly **programmatic and deterministic**. It bypasses the AI reasoning graph entirely, querying the relational database and downloading batched market prices directly.
- **Tenant Isolation**: Only positions owned by the authenticated tenant (`current_user.id`) are queried and aggregated.
- **Batched Market Data Retrieval**: Tickers are batched into a single Yahoo Finance `yf.download(tickers, period="5d")` invocation to minimize network overhead and eliminate N+1 query patterns.

---

## 2. 🔌 Technical Contracts & Endpoints

### A. API Endpoints
- `GET /dashboard`: Fetches real-time valuations and daily performance metrics for all user holdings.
  - **Headers**: `Authorization: Bearer <token>`
  - **Response Payload**:
    ```python
    class AssetRow(BaseModel):
        ticker: str
        shares: float
        current_price: float
        prev_close: float
        asset_pnl: float
        asset_pnl_percent: float
        total_value: float

    class DashboardResponse(BaseModel):
        total_assets: int
        assets: List[AssetRow]
    ```

### B. Valuation & P&L Calculation Logic
For each position:
$$\text{Total Value} = \text{shares} \times \text{current\_price}$$
$$\text{Asset P\&L} = (\text{current\_price} - \text{prev\_close}) \times \text{shares}$$
$$\text{Asset P\&L \%} = \frac{\text{current\_price} - \text{prev\_close}}{\text{prev\_close}} \times 100$$
If price history is unavailable for a given ticker, the system defensively assigns `current_price = 0.0`, `asset_pnl = 0.0`, and `asset_pnl_percent = 0.0` rather than aborting the request.

---

## 3. 🖥️ Frontend Architecture & Presentation
- **Hook**: `useDashboard.ts`:
  - Communicates with `GET /dashboard` via `API_ENDPOINTS.DASHBOARD`.
  - Manages cached dashboard metrics, loading states, and error propagation.
- **Component**: `Dashboard.tsx`:
  - Executive metric cards displaying Net Portfolio Value, Daily Unrealized Gain/Loss ($ and %), and Asset Count.
  - Table and card views featuring colored trend pills (green for positive, red for negative).
  - Elegant empty state with actionable CTA routing users to the Portfolio Management tab when zero holdings exist.

---

## 4. ✅ Verified Acceptance Criteria (Regression Baseline)
- [x] **AC-1**: Requesting `/dashboard` executes with sub-second response times without invoking LangGraph agent nodes.
- [x] **AC-2**: Users with zero positions receive `{ "total_assets": 0, "assets": [] }` with HTTP 200 OK.
- [x] **AC-3**: Ticker symbols across multiple exchanges (e.g. US and Indian equities) are queried in a consolidated batch download.
- [x] **AC-4**: Unauthenticated requests to `/dashboard` receive `401 Unauthorized`.
- [x] **AC-5**: The frontend UI renders intuitive empty states when no holdings are registered.
