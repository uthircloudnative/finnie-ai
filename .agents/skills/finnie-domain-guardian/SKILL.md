---
name: finnie-domain-guardian
description: Enforces financial domain accuracy, SEC/FINRA compliance guidelines ($NFA), multi-jurisdiction market routing, and mathematical robustness across all analytical agent nodes in Finnie AI. Use when modifying portfolio math, RAG tax rules, or compliance logic.
---

# Finnie Domain & Compliance Guardian Playbook

This skill defines the domain rules, financial mathematics safeguards, and regulatory compliance constraints unique to Finnie AI.

---

## 1. SEC / FINRA Compliance Standards ($NFA)

Finnie AI is strictly an **educational guidance assistant**, NOT a licensed investment advisor or fiduciary.

### The Immutable Rule:
Every user-facing financial insight emitted by any agent or endpoint MUST conclude with the standardized compliance disclaimer:
```text
$NFA: This information is for educational purposes only and does not constitute financial, investment, or tax advice. Consult a certified financial planner or tax advisor before making investment decisions.
```

### Architectural Enforcement:
- The LangGraph orchestrator routes all agent nodes (`portfolio_analyst`, `financial_qa`, `market_insights`, `goal_strategist`) into `compliance_guardian_node` before reaching `END`.
- The node inspects the final `AIMessage` in `state["messages"]`. If the disclaimer is absent, it automatically appends it idempotently.

---

## 2. Multi-Jurisdiction Benchmark Routing

Portfolios can span multiple global markets. Always map the holding's exchange to the correct benchmark index:

| Jurisdiction | Exchange Code | Benchmark Ticker | Index Name |
|---|---|---|---|
| **United States** | `NYSE`, `NASDAQ` | `^GSPC` | S&P 500 |
| **India** | `NSE`, `BSE` | `^NSEI` | NIFTY 50 |
| **United Kingdom** | `LSE` | `^FTSE` | FTSE 100 |
| **Canada** | `TSX` | `^GSPTSE` | S&P/TSX Composite |
| **Germany** | `XETRA` | `^GDAXI` | DAX 40 |
| **All Markets** | `ALL` | `^GSPC` | Global Baseline |

---

## 3. Financial Math & Scraper Safeguards

### A. Array Alignment
When computing portfolio Beta or Annualized Volatility:
- NEVER assume yfinance returned data for all requested tickers.
- Build metric arrays exclusively from `valid_symbols` — tickers present in **both** price return and volatility dictionaries.
- Guard against zero or empty portfolios: return `0.0` or `null` gracefully instead of propagating `NaN` or dividing by zero.

### B. Herfindahl-Hirschman Index (HHI) & Retry Engine
- The diversification score is calculated from sector concentration using the HHI formula:
  $$HHI = \sum (\text{sector\_weight})^2$$
- Normalised to a 0–10 scale:
  $$\text{score} = 10 \times \left(1 - \frac{HHI - HHI_{min}}{1 - HHI_{min}}\right)$$
- **Scraper Resilience**: Fetching sector info via `yf.Ticker().info` is network-dependent and can be throttled. The function `compute_hhi_diversification` MUST use a 3-attempt exponential backoff retry loop.
- **UI Degradation**: If all 3 attempts fail, return `diversification_score = null`. The frontend tile will render an interactive `"📊 Get Diversification Score"` button rather than crashing.

### C. Monte Carlo Projections (Goal Strategist)
- Run 10,000 simulations using vectorized `numpy` geometric Brownian motion.
- Validate percentiles: ensure strictly that $P_{05} \le \text{Median} \le P_{95}$.
- Clamp confidence scores between $0\%$ and $100\%$.

---

## 4. Regional Tax & Regulatory RAG

When generating goal roadmaps:
- Filter the `goal_rules` ChromaDB collection by the user's `country` metadata (e.g. `country="US"` for 401(k) / Roth IRA limits; `country="IN"` for Section 80C and Long-Term Capital Gains).
- Explicitly cite statutory contribution limits for the current tax year in the synthesized report.
