import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, SystemMessage

from src.models.state import FinnieState
from src.utils.vector_store import VectorStoreManager

def portfolio_analyst_node(state: FinnieState) -> dict:
    """
    The Portfolio Analyst Worker.
    1. Computes math (Beta, Volatility) using yfinance.
    2. Performs RAG retrieval from 'analytical_kb' for theory.
    3. Synthesizes a beginner-friendly analysis.
    """
    print("--- ENTERING PORTFOLIO ANALYST NODE ---")
    
    holdings = state.get("portfolio_data", [])
    if not holdings:
        return {"messages": [AIMessage(content="I don't see any holdings in your portfolio yet. Head to the 'My Holdings' tab to add some stocks!")]}

    tickers = [h["ticker"] for h in holdings]
    
    # --- 1. MATH ENGINE (yfinance) ---
    print(f"Calculating math for: {tickers}")
    avg_beta, avg_vol = 1.0, 15.0 # Sensible defaults if data fetch fails
    
    try:
        # Fetch 1y history for tickers + S&P 500 benchmark
        symbols = tickers + ["^GSPC"]
        raw_data = yf.download(symbols, period="1y")
        
        # Robust column access (yfinance sometimes uses MultiIndex depending on symbol count)
        if isinstance(raw_data.columns, pd.MultiIndex):
            # If MultiIndex, 'Adj Close' is usually the first level
            data = raw_data['Adj Close'] if 'Adj Close' in raw_data.columns.levels[0] else raw_data['Close']
        else:
            data = raw_data['Adj Close'] if 'Adj Close' in raw_data.columns else raw_data['Close']
        
        # Calculate daily returns
        returns = data.pct_change().dropna()
        
        # Calculate Volatility (Annualized StdDev)
        volatilities = returns.std() * np.sqrt(252) * 100
        
        # Calculate Beta vs S&P 500
        market_returns = returns["^GSPC"]
        betas = {}
        for t in tickers:
            covariance = returns[t].cov(market_returns)
            variance = market_returns.var()
            betas[t] = covariance / variance

        avg_beta = np.mean([betas[t] for t in tickers])
        avg_vol = np.mean([volatilities[t] for t in tickers])
        
        math_summary = (
            f"Portfolio Beta: {avg_beta:.2f} (Relative to S&P 500)\n"
            f"Annualized Volatility: {avg_vol:.1f}%\n"
        )
        for t in tickers:
            math_summary += f"- {t}: Beta {betas[t]:.2f}, Vol {volatilities[t]:.1f}%\n"

    except Exception as e:
        print(f"yfinance error: {e}")
        math_summary = "Error fetching live market data. Using historical estimates only."

    # --- 2. RAG RETRIEVAL (analytical_kb) ---
    # We query for concepts relevant to the math results
    rag_query = f"Explain importance of Sharpe ratio, Beta {avg_beta:.2f}, and volatility {avg_vol:.1f}% for beginners."
    db = VectorStoreManager(collection_name="analytical_kb")
    docs = db.search(query=rag_query, k=4, target_country="GLOBAL")
    theory_context = "\n\n".join([d.page_content for d in docs])

    # --- 3. LLM SYNTHESIS ---
    system_prompt = (
        "You are Finnie's 'Portfolio Analyst' worker. Your goal is to explain a user's portfolio health.\n"
        "You are given RAW MATH and RAG THEORY. Your job is to combine them into 3 clear, encouraging sections:\n"
        "1. **Your Risk Profile**: Explain the Beta and Volatility in plain English.\n"
        "2. **Diversification Check**: Based on the stocks listed, give a high-level diversification score.\n"
        "3. **What This Means for You**: Beginner-friendly advice based on the RAG theory chunks.\n\n"
        "RULES:\n"
        "- Use ONLY the RAG theory for benchmarks (e.g., 'A beta above 1.0 means...').\n"
        "- Be encouraging and avoid jargon where possible.\n"
        f"--- RAW MATH ---\n{math_summary}\n\n"
        f"--- RAG THEORY ---\n{theory_context}"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"] 
    ]
    
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    llm = init_chat_model(model=model_name, model_provider=provider, temperature=0.7)
    
    ai_msg = llm.invoke(messages)
    
    # Return both the AI text and the structured results for the frontend
    return {
        "messages": [ai_msg],
        "analysis_results": {
            "beta": round(float(avg_beta), 2),
            "volatility": round(float(avg_vol), 1),
            "diversification_score": 7, # Simple placeholder score for now
            "tickers": tickers
        }
    }
