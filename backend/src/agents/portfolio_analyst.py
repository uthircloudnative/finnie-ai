import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, SystemMessage

from src.database import SessionLocal
from src.models.state import FinnieState
from src.models.market_metadata import MarketExchange
from src.utils.vector_store import VectorStoreManager

def portfolio_analyst_node(state: FinnieState) -> dict:
    """
    The Portfolio Analyst Worker.
    1. Maps tickers to their correct yfinance suffixes (e.g. RELIANCE -> RELIANCE.NS)
    2. Computes math (Beta, Volatility) via yfinance.
    3. Performs RAG retrieval from 'analytical_kb' for theory.
    4. Synthesizes a beginner-friendly analysis.
    """
    holdings = state.get("portfolio_data", [])
    if not holdings:
        return {"messages": [AIMessage(content="I don't see any holdings in your portfolio yet. Head to the 'My Holdings' tab to add some stocks!")]}

    # 1. Map tickers to Exchange Suffixes
    # We fetch the master exchange list from SQLite
    db_session = SessionLocal()
    try:
        exchanges = db_session.query(MarketExchange).all()
        suffix_map = {ex.exchange_code: ex.yf_suffix for ex in exchanges}
    finally:
        db_session.close()

    # Build the final search strings (e.g. ["AAPL", "RELIANCE.NS"])
    # We store the original user-facing display name separately
    search_symbols = []
    symbol_to_display = {}
    
    for h in holdings:
        ticker = h["ticker"].upper()
        exchange_code = h.get("exchange", "NYSE") # Default to NYSE
        suffix = suffix_map.get(exchange_code, "")
        
        full_symbol = f"{ticker}{suffix}"
        search_symbols.append(full_symbol)
        symbol_to_display[full_symbol] = ticker

    print(f"\n[FINNIE-AI] 📊 Analyst starting portfolio review for: {search_symbols}")
    
    # 2. MATH ENGINE (yfinance)
    print(f"[FINNIE-AI] 📈 Computing Beta & Volatility via yfinance for: {search_symbols}")
    avg_beta, avg_vol = 1.0, 15.0 # Sensible defaults
    math_summary = ""
    
    try:
        # Fetch 1y history for symbols + S&P 500 benchmark
        query_symbols = search_symbols + ["^GSPC"]
        raw_data = yf.download(query_symbols, period="1y", progress=False)
        
        # Robust column access
        if isinstance(raw_data.columns, pd.MultiIndex):
            data = raw_data['Adj Close'] if 'Adj Close' in raw_data.columns.levels[0] else raw_data['Close']
        else:
            data = raw_data['Adj Close'] if 'Adj Close' in raw_data.columns else raw_data['Close']
        
        # Calculate daily returns
        returns = data.pct_change().dropna()
        
        # Guardrail: Check if we actually got ANY data
        if returns.empty:
            raise ValueError("No price data returned from yfinance (check internet or tickers)")

        # Calculate Volatility
        volatilities = returns.std() * np.sqrt(252) * 100
        
        # Calculate Beta vs S&P 500 (only if benchmark exists)
        betas = {}
        has_benchmark = "^GSPC" in returns.columns
        if not has_benchmark:
            print("[FINNIE-AI] ⚠️ Warning: '^GSPC' missing from returns. Beta calculation skipped.")

        for s in search_symbols:
            if s in returns.columns and has_benchmark:
                covariance = returns[s].cov(returns["^GSPC"])
                variance = returns["^GSPC"].var()
                betas[s] = covariance / variance if variance != 0 else 1.0
            else:
                betas[s] = 1.0 # Default fallback
        
        # Group stats back to original display tickers
        display_betas = [betas[s] for s in search_symbols]
        display_vols = [volatilities[s] for s in search_symbols if s in volatilities]
        
        avg_beta = np.mean(display_betas) if display_betas else 1.0
        avg_vol = np.mean(display_vols) if display_vols else 15.0
        
        math_summary = (
            f"Portfolio Beta: {avg_beta:.2f} (Relative to S&P 500)\n"
            f"Annualized Volatility: {avg_vol:.1f}%\n"
        )
        for s in search_symbols:
            display_name = symbol_to_display[s]
            beta_val = betas.get(s, 1.0)
            vol_val = volatilities.get(s, 15.0)
            math_summary += f"- {display_name}: Beta {beta_val:.2f}, Vol {vol_val:.1f}%\n"

    except Exception as e:
        print(f"[FINNIE-AI] ❌ yfinance error: {e}")
        math_summary = "Error fetching live market data for some tickers. Using historical estimates only."

    # 3. RAG RETRIEVAL (analytical_kb)
    rag_query = f"Explain importance of Sharpe ratio, Beta {avg_beta:.2f}, and volatility {avg_vol:.1f}% for beginners."
    print(f"[FINNIE-AI] 📚 Querying analytical_kb: '{rag_query[:50]}...'")
    db = VectorStoreManager(collection_name="analytical_kb")
    docs = db.search(query=rag_query, k=4, target_country="GLOBAL")
    theory_context = "\n\n".join([d.page_content for d in docs])

    # 4. LLM SYNTHESIS
    system_prompt = (
        "You are Finnie's 'Portfolio Analyst' worker. Your goal is to explain a user's portfolio health.\n"
        "You are given RAW MATH and RAG THEORY. Your job is to combine them into 3 clear, encouraging sections:\n"
        "1. **Your Risk Profile**: Explain the Beta and Volatility in plain English.\n"
        "2. **Diversification Check**: Based on the stocks listed, give a high-level diversification score.\n"
        "3. **What This Means for You**: Beginner-friendly advice based on the RAG theory chunks.\n\n"
        "RULES:\n"
        "- Use ONLY the RAG theory for benchmarks.\n"
        "- Be encouraging and avoid jargon where possible.\n"
        f"--- RAW MATH ---\n{math_summary}\n\n"
        f"--- RAG THEORY ---\n{theory_context}"
    )
    
    messages = [SystemMessage(content=system_prompt), *state["messages"]]
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    llm = init_chat_model(model=model_name, model_provider=provider, temperature=0.7)
    
    print(f"[FINNIE-AI] 🧠 Synthesizing final analysis report...")
    ai_msg = llm.invoke(messages)
    
    return {
        "messages": [ai_msg],
        "analysis_results": {
            "beta": round(float(avg_beta), 2),
            "volatility": round(float(avg_vol), 1),
            "diversification_score": 7,
            "tickers": [symbol_to_display[s] for s in search_symbols]
        }
    }
