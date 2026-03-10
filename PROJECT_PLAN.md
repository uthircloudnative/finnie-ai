# finnie-ai - Production-Grade Multi-Agent Finance Guide

## 1. Executive Summary
Finnie is a state-of-the-art multi-agent system designed to bridge the financial literacy gap for beginner investors. Unlike generic chatbots, Finnie provides personalized, real-time, and grounded investment insights through a "Dashboard-First, Agent-Assisted" experience.

## 2. Comprehensive Requirements
### 2.1 Multi-Agent Financial Intelligence
- **Supervisor (Orchestrator)**: Uses LLM reasoning to decompose complex user queries and route them to specialized workers.
- **Financial Q&A Worker**: RAG-grounded agent using curated knowledge (Vanguard, Investopedia, SEC).
- **Market Insights Worker**: Real-time tool-use agent (Alpha Vantage, NewsAPI) for stock trends and sentiment.
- **Portfolio Analyst Worker**: Mathematical engine calculating Sharpe ratios, diversification, and risk scores.
- **Goal Strategist Worker**: Probabilistic forecasting using Monte Carlo simulations for goals (e.g., retirement, home buying).
- **Compliance Guardian**: Mandatory post-processor ensuring all outputs contain $NFA (Not Financial Advice) disclaimers and adhere to SEC/FINRA-style safety guidelines.

### 2.2 Technical Requirements
- **Architecture**: Stateful Hub-and-Spoke pattern using **LangGraph**.
- **Grounding**: RAG pipeline with **FAISS/ChromaDB** for educational content.
- **Real-time Data**: API integrations for live market ticks and news feeds.
- **Quality**: 80%+ test coverage (Unit, Integration, E2E).
- **Observability**: Traceability of agent decisions and tool calls.

### 2.3 UI/UX: "Glass-Finance" Dashboard
- **Visuals**: Dark Mode, Glassmorphism, premium typography, and micro-animations.
- **Navigation**: Multi-tab layout (Dashboard, Portfolio, Insights, Chat).
- **Interactivity**: "What-if" sliders for goal planning and visual agent "thinking" states.

## 3. Implementation Plan (Detailed)

### Phase 1: Foundation (Current)
- **Backend**: Setup LangGraph, define Global State, and implement Supervisor routing logic.
- **Frontend**: Scaffolding with Vite/React, implementing the "Glass-Finance" theme and tab navigation.

### Phase 2: Intelligence & Grounding
- **RAG Pipeline**: Scrape and index financial literacy resources. Implement the Financial Q&A agent.
- **Tool Integration**: Connect Market Insights agent to real-time APIs.

### Phase 3: Analysis & Simulation
- **Portfolio Logic**: Implement the Portfolio Analyst with math-heavy tools.
- **Goal Engine**: Developing Monte Carlo simulation tools for the Goal Strategist.

### Phase 4: Hardening & Compliance
- **Compliance**: Implement the Guardian node to scan all messages for risk disclaimers.
- **Testing**: Reach 80%+ coverage with Pytest and Playwright.

### Phase 5: Deployment & Scale
- **Infrastructure**: CI/CD pipeline, FastAPI performance tuning, and Cloud deployment.
## 4. RAG Integration Matrix (Learning Reference)

| UI Tab / Feature | Specialist Agent | RAG Intelligence & Data Sources | Learning Goal |
| :--- | :--- | :--- | :--- |
| **Q&A Chatbot** | Financial Q&A Agent | **Source**: Investopedia, Financial Textbooks.<br>**Use Case**: Defining terms (e.g., "Wash Sale", "ETF vs Mutual Fund"). | Grounding AI in verified educational definitions. |
| **Market Insights** | Market Insights Agent | **Source**: SEC 10-K/10-Q Filings, NewsAPI.<br>**Use Case**: Explaining price movements using official company reports vs rumors. | Bridging real-time news with official regulatory data. |
| **Portfolio Analyst** | Analyst Agent | **Source**: Academic Whitepapers (e.g., Modern Portfolio Theory).<br>**Use Case**: Comparing current allocation against professional benchmarks. | Applying professional investment theories to personal data. |
| **Goal Planning** | Goal Strategist | **Source**: IRS Tax Guidelines, 401k/IRA Limit Databases.<br>**Use Case**: Ensuring simulations account for tax-advantaged account rules. | Validating probabilistic models against rigid legal/tax rules. |
| **Compliance** | Guardian Agent | **Source**: SEC/FINRA Safety Standards, Disclaimer Repository.<br>**Use Case**: Scanning all AI outputs for mandatory risk disclosures. | Ensuring every agentic output is safe and compliant. |
