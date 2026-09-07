"""
portfolio_analyst.py — The LangGraph node for portfolio risk analysis
======================================================================
Computes Beta, Volatility, Diversification (HHI), and synthesises
an LLM report grounded in ChromaDB RAG theory.

Country-Aware Features (Sep 2026):
- Each holding is benchmarked against its home-market index (e.g. NIFTY 50 for India)
- Volatility risk tiers use country-calibrated thresholds
- LLM prompt includes per-country RAG context from analytical_kb
- In All-Markets mode, each country gets its own benchmark row in the report
"""
import os
import time
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage, SystemMessage
from langsmith import traceable

from src.database import SessionLocal
from src.models.state import FinnieState
from src.models.market_metadata import MarketExchange
from src.utils.vector_store import VectorStoreManager
from langchain.chat_models import init_chat_model


def compute_hhi_diversification(valid_symbols: List[str], max_retries: int = 3) -> tuple[Optional[float], Dict[str, int]]:
    """
    Computes HHI diversification score with a retry mechanism (up to max_retries).
    Returns (diversification_score, sectors_dict).
    If all attempts fail, returns (None, {}).
    """
    if not valid_symbols:
        return 0.0, {}

    for attempt in range(1, max_retries + 1):
        sectors: Dict[str, int] = {}
        try:
            for s in valid_symbols:
                info = yf.Ticker(s).info
                sector = info.get("sector", "Unknown")
                sectors[sector] = sectors.get(sector, 0) + 1

            if sectors:
                total = sum(sectors.values())
                weights = [count / total for count in sectors.values()]
                hhi = sum(w ** 2 for w in weights)
                n = len(sectors)
                hhi_min = 1.0 / n if n > 0 else 1.0
                if hhi_min < 1.0:
                    score = round(10 * (1 - (hhi - hhi_min) / (1 - hhi_min)), 1)
                else:
                    score = 0.0
                print(f"[FINNIE-AI] 📊 Sectors: {sectors} → HHI={hhi:.3f} → Score={score} (attempt {attempt}/{max_retries})")
                return score, sectors
        except Exception as e:
            print(f"[FINNIE-AI] ⚠️ HHI fetch attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(1)

    print(f"[FINNIE-AI] ❌ All {max_retries} HHI attempts failed. Returning None.")
    return None, {}

# ── Country → Benchmark mapping ────────────────────────────────────────────
COUNTRY_BENCHMARKS: Dict[str, str] = {
    "US": "^GSPC",    # S&P 500
    "IN": "^NSEI",    # NIFTY 50
    "GB": "^FTSE",    # FTSE 100
    "CA": "^GSPTSE",  # S&P/TSX Composite
    "DE": "^GDAXI",   # DAX
}
BENCHMARK_NAMES: Dict[str, str] = {
    "^GSPC":   "S&P 500",
    "^NSEI":   "NIFTY 50",
    "^FTSE":   "FTSE 100",
    "^GSPTSE": "S&P/TSX",
    "^GDAXI":  "DAX",
}
DEFAULT_BENCHMARK = "^GSPC"

# ── Volatility thresholds calibrated to each market's historical norms ─────
# Tuple: (low_cutoff, high_cutoff)  →  < low = Low Risk, < high = Medium, else High
VOL_THRESHOLDS: Dict[str, tuple] = {
    "US": (15, 25),
    "IN": (20, 35),
    "GB": (15, 28),
    "CA": (15, 25),
    "DE": (15, 28),
}
DEFAULT_VOL_THRESHOLDS = (15, 25)


@traceable(name="yFinance Data Fetch & Math", run_type="tool")
def fetch_yfinance_data(symbols: list) -> pd.DataFrame:
    """Wrapper to cleanly trace the external Yahoo Finance API call."""
    return yf.download(symbols, period="1y", progress=False, auto_adjust=True)


def _get_adj_close(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Robust multi-index / single-index column accessor for yfinance data."""
    if isinstance(raw_data.columns, pd.MultiIndex):
        if "Close" in raw_data.columns.levels[0]:
            return raw_data["Close"]
        if "Adj Close" in raw_data.columns.levels[0]:
            return raw_data["Adj Close"]
    else:
        if "Close" in raw_data.columns:
            return raw_data[["Close"]]
        if "Adj Close" in raw_data.columns:
            return raw_data[["Adj Close"]]
    raise ValueError("Neither 'Close' nor 'Adj Close' found in yfinance response.")


def portfolio_analyst_node(state: FinnieState) -> dict:
    """
    The Portfolio Analyst Worker — country-aware edition.

    1. Maps tickers to yfinance suffixes using the exchange master table
    2. Determines the correct benchmark per country (e.g. ^NSEI for India)
    3. Computes Beta (vs home-market benchmark) and Volatility per holding
    4. Computes real HHI-based Diversification Score
    5. RAG retrieval from analytical_kb — per-country when scoped
    6. Synthesises a country-aware LLM report
    """
    holdings = state.get("portfolio_data", [])
    analysis_country = state.get("analysis_country", "ALL") or "ALL"

    if not holdings:
        return {"messages": [AIMessage(content="I don't see any holdings in your portfolio yet. Head to the 'My Holdings' tab to add some stocks!")]}

    # ── 1. Exchange Suffix Mapping ─────────────────────────────────────────
    db_session = SessionLocal()
    try:
        exchanges = db_session.query(MarketExchange).all()
        suffix_map = {ex.exchange_code: ex.yf_suffix for ex in exchanges}
    finally:
        db_session.close()

    search_symbols: List[str] = []
    symbol_to_display: Dict[str, str] = {}
    symbol_to_country: Dict[str, str] = {}

    for h in holdings:
        ticker = h["ticker"].upper()
        exchange_code = h.get("exchange", "NYSE")
        country_code = h.get("country", "US").upper()
        suffix = suffix_map.get(exchange_code, "")
        full_symbol = f"{ticker}{suffix}"
        search_symbols.append(full_symbol)
        symbol_to_display[full_symbol] = ticker
        symbol_to_country[full_symbol] = country_code

    print(f"\n[FINNIE-AI] 📊 Analyst starting review | scope={analysis_country} | tickers={search_symbols}")

    # ── 2. Determine Benchmarks ────────────────────────────────────────────
    # Build a set of unique benchmarks needed (one per unique country in this run)
    unique_countries = list(dict.fromkeys(symbol_to_country[s] for s in search_symbols))
    country_to_benchmark = {c: COUNTRY_BENCHMARKS.get(c, DEFAULT_BENCHMARK) for c in unique_countries}
    all_benchmarks = list(dict.fromkeys(country_to_benchmark.values()))

    # Primary benchmark: for single-country scope use its benchmark; for ALL use S&P 500 as display default
    primary_country = unique_countries[0] if len(unique_countries) == 1 else "US"
    primary_benchmark = country_to_benchmark.get(primary_country, DEFAULT_BENCHMARK)
    primary_benchmark_name = BENCHMARK_NAMES.get(primary_benchmark, primary_benchmark)

    # Vol thresholds for the primary/selected country
    vol_low, vol_high = VOL_THRESHOLDS.get(primary_country if len(unique_countries) == 1 else "US", DEFAULT_VOL_THRESHOLDS)

    # ── 3. Math Engine (yfinance) ──────────────────────────────────────────
    print(f"[FINNIE-AI] 📈 Fetching 1yr prices | symbols={search_symbols} | benchmarks={all_benchmarks}")
    avg_beta, avg_vol = 1.0, 15.0
    math_summary = ""
    valid_symbols: List[str] = []
    # Per-country beta results for All-Markets display
    country_betas: Dict[str, dict] = {}  # {country_code: {beta, benchmark_name}}

    try:
        query_symbols = search_symbols + all_benchmarks
        raw_data = fetch_yfinance_data(query_symbols)
        data = _get_adj_close(raw_data)

        returns = data.pct_change().dropna()
        if returns.empty:
            raise ValueError("No price data returned from yfinance.")

        volatilities = returns.std() * np.sqrt(252) * 100

        # Compute beta per holding against its home-market benchmark
        betas: Dict[str, float] = {}
        for s in search_symbols:
            c = symbol_to_country[s]
            benchmark = country_to_benchmark.get(c, DEFAULT_BENCHMARK)
            if s in returns.columns and benchmark in returns.columns:
                cov = returns[s].cov(returns[benchmark])
                var = returns[benchmark].var()
                betas[s] = cov / var if var != 0 else 1.0
            else:
                betas[s] = 1.0

        # Guard: only include symbols that have BOTH beta and vol
        valid_symbols = [s for s in search_symbols if s in volatilities and s in betas]
        if not valid_symbols:
            raise ValueError("No valid symbols with complete price data.")

        display_betas = [betas[s] for s in valid_symbols]
        display_vols = [float(volatilities[s]) for s in valid_symbols]

        avg_beta = float(np.mean(display_betas))
        avg_vol = float(np.mean(display_vols))

        # Per-country aggregated betas (for All-Markets card display)
        for c in unique_countries:
            c_symbols = [s for s in valid_symbols if symbol_to_country[s] == c]
            if c_symbols:
                c_betas = [betas[s] for s in c_symbols]
                country_betas[c] = {
                    "beta": round(float(np.mean(c_betas)), 2),
                    "benchmark": country_to_benchmark.get(c, DEFAULT_BENCHMARK),
                    "benchmark_name": BENCHMARK_NAMES.get(country_to_benchmark.get(c, DEFAULT_BENCHMARK), ""),
                }

        math_summary = (
            f"Avg Portfolio Beta: {avg_beta:.2f}\n"
            f"Annualized Volatility: {avg_vol:.1f}%\n"
        )
        for s in valid_symbols:
            benchmark_name = BENCHMARK_NAMES.get(country_to_benchmark.get(symbol_to_country[s], DEFAULT_BENCHMARK), "")
            math_summary += (
                f"- {symbol_to_display[s]} ({symbol_to_country[s]}): "
                f"Beta {betas[s]:.2f} vs {benchmark_name}, "
                f"Vol {float(volatilities[s]):.1f}%\n"
            )

    except Exception as e:
        print(f"[FINNIE-AI] ❌ yfinance error: {e}")
        math_summary = "Error fetching live market data. Using historical estimates only."
        valid_symbols = []

    # ── 4. RAG Retrieval ───────────────────────────────────────────────────
    rag_query = f"Explain Beta {avg_beta:.2f}, volatility {avg_vol:.1f}%, Sharpe ratio, and diversification for investors."
    print(f"[FINNIE-AI] 📚 RAG query for countries: {unique_countries}")
    db = VectorStoreManager(collection_name="analytical_kb")
    theory_context = ""

    if analysis_country != "ALL":
        # Single-country: targeted RAG with country filter
        docs = db.search(rag_query, k=4, target_country=analysis_country)
        if not docs:
            docs = db.search(rag_query, k=4, target_country="GLOBAL")
        theory_context = "\n\n".join([d.page_content for d in docs])
    else:
        # All-Markets: one RAG query per unique country, merged
        all_docs = []
        for c in unique_countries:
            c_docs = db.search(rag_query, k=2, target_country=c)
            if not c_docs:
                c_docs = db.search(rag_query, k=1, target_country="GLOBAL")
            all_docs.extend(c_docs)
        theory_context = "\n\n".join([d.page_content for d in all_docs])

    if not theory_context:
        theory_context = "No specific RAG context found. Using general financial principles."

    # ── 5. LLM Synthesis ──────────────────────────────────────────────────
    is_all_markets = analysis_country == "ALL"
    country_context_str = (
        f"ALL MARKETS ({', '.join(unique_countries)})" if is_all_markets
        else f"{analysis_country} (benchmark: {primary_benchmark_name})"
    )

    system_prompt = (
        "You are Finnie's 'Portfolio Analyst' worker. Your goal is to explain a user's portfolio health.\n"
        f"Country Scope: {country_context_str}\n\n"
        "You are given RAW MATH and RAG THEORY. Produce a report with exactly 3 sections:\n"
        "1. **Your Risk Profile**: Explain Beta and Volatility in plain English. "
        + ("For each country, reference its specific benchmark (e.g. NIFTY 50 for India, S&P 500 for US).\n" if is_all_markets
           else f"Reference the {primary_benchmark_name} as the benchmark.\n")
        + "2. **Diversification Check**: Evaluate sector/country spread based on the stocks listed.\n"
        "3. **What This Means for You**: Beginner-friendly advice grounded in the RAG theory. "
        "Include any country-specific tax or regulatory context you find.\n\n"
        "RULES:\n"
        "- Be encouraging but honest.\n"
        "- Use ONLY the RAG theory for benchmarks and advice.\n"
        f"--- RAW MATH ---\n{math_summary}\n\n"
        f"--- RAG THEORY ---\n{theory_context}"
    )

    messages = [SystemMessage(content=system_prompt), *state["messages"]]
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    llm = init_chat_model(model=model_name, model_provider=provider, temperature=0.7)

    print(f"[FINNIE-AI] 🧠 Synthesising report | scope={analysis_country}...")
    ai_msg = llm.invoke(messages)

    # ── 6. HHI Diversification Score (with 3-attempt retry) ──────────────
    diversification_score, sectors = compute_hhi_diversification(valid_symbols, max_retries=3)

    return {
        "messages": [ai_msg],
        "analysis_results": {
            "beta": round(avg_beta, 2),
            "volatility": round(avg_vol, 1),
            "diversification_score": diversification_score,
            "tickers": [symbol_to_display[s] for s in valid_symbols],
            # Country-awareness fields consumed by the frontend
            "country": analysis_country,
            "benchmark": primary_benchmark,
            "benchmark_name": primary_benchmark_name,
            "vol_thresholds": [vol_low, vol_high],
            "sectors": sectors,
            "country_betas": country_betas,       # {country: {beta, benchmark_name}} for All-Markets card
            "unique_countries": unique_countries,
        }
    }
