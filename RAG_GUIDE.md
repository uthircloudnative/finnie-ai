# Finnie AI: Step-by-Step RAG Implementation Guide

Welcome to the world of Agentic RAG! This guide explains how we will build the intelligence layer for Finnie AI, moving from raw PDFs/Websites to a grounded AI response.

---

## What is RAG?
**Retrieval-Augmented Generation (RAG)** is like giving an LLM (like GPT-4o) an **Open-Book Exam**. Instead of relying only on its memory (training data), it looks up specific facts in our database before answering.

---

## Step 1: Ingestion (The "Loading" Phase)
First, we need to gather our financial knowledge base (Investopedia articles, SEC Filings).
1.  **Extract**: Use a library like `LangChain` to load raw data from PDFs or websites.
2.  **Partition**: Convert HTML/Text into clean strings.

---

## Step 2: Chunking (The "Slicing" Phase)
LLMs have a limit on how much text they can read at once.
- **Goal**: Break large documents into small chunks (e.g., 500-1000 characters).
- **Technique**: Use a `RecursiveCharacterTextSplitter`. We keep a small "overlap" (e.g., 100 characters) between chunks so we don't lose context mid-sentence.

---

## Step 3: Embedding (The "Translation" Phase)
Computers are better at math than words. We must turn text into **Vectors** (lists of numbers).
- **Process**: Pass each chunk through an **Embedding Model** (like OpenAI `text-embedding-3-small`).
- **Result**: Small chunks of text now have a mathematical "location" in space. Similar topics (like "Stocks" and "Equities") will be mathematically close to each other.

---

## Step 4: Storage (The "Brain" Phase)
We store these vectors in a **Vector Database** (like ChromaDB).
- **Why?**: ChromaDB allows us to perform "Similarity Searches"—finding the math-closest vectors to a user's question.

---

## Step 5: Retrieval (The "Look-up" Phase)
When a user asks: *"What is an ETF?"*
1.  **Embed the Question**: Turn the question into a vector using the same model.
2.  **Query the DB**: Ask ChromaDB for the Top 3-5 text chunks that are mathematically closest to that question.

---

## Step 6: Generation (The "Augmentation" Phase)
This is where the agentic magic happens. We send a prompt to the LLM that looks like this:

> **PROMPT**:
> "You are the Financial Q&A Agent. 
> 
> **CONTEXT**: [Chunk 1: ETF definition], [Chunk 2: Tax benefits of ETFs]
> 
> **USER QUESTION**: What is an ETF?
> 
> **INSTRUCTIONS**: Answer the user's question **ONLY** using the provided context. If you don't know, say you don't know."

---

## 💎 Data Sourcing: Where to find your facts
For a beginner-friendly app, here is exactly where we will get the data for each use case:

### 1. Q&A Chatbot (Educational Data)
- **Source**: [Investopedia](https://www.investopedia.com/financial-term-dictionary-4769738)
- **Strategy**: Use a web-scraper (like `BeautifulSoup`) to pull definitions for the top 500 financial terms.
- **Alternative**: [HuggingFace Datasets](https://huggingface.co/datasets) (Search for "Financial" or "Economics" textbooks).

### 2. Market Insights (Regulatory & News Data)
- **Source**: [SEC EDGAR API](https://www.sec.gov/edgar/sec-api-documentation)
- **Strategy**: Download "Form 10-K" (Annual Reports) for S&P 500 companies. This is the "Gold Standard" of truth.
- **News**: [NewsAPI.org](https://newsapi.org/) or [Alpha Vantage News API](https://www.alphavantage.co/documentation/#news-sentiment).

### 3. Portfolio Analyst (Theory & Benchmarks)
- **Source**: [Standard & Poor's (S&P) Indices](https://www.spglobal.com/spdji/en/)
- **Strategy**: Download whitepapers on "Modern Portfolio Theory" or "Asset Allocation" from Vanguard or BlackRock.

### 4. Goal Planning (Tax & Policy Data)
- **Source**: [IRS.gov - Tax Brackets](https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024)
- **Strategy**: Index the latest contribution limits for 401(k), IRA, and Roth IRA. This ensures Finnie doesn't suggest over-contributing.

### 5. Compliance (Safety Standards)
- **Source**: [SEC "Fast Answers" Page](https://www.sec.gov/fast-answers)
- **Strategy**: Index the SEC's own guides on "Investment Advisers" and "Fraud" to help the Guardian Agent recognize prohibited advice.

---

## 🕒 Real-Time News: RAG or Not?
A common question: *"Do I store real-time news in my long-term RAG database?"*

### The Answer: Short-Term vs. Long-Term
1.  **Static RAG**: For facts that don't change often (Investopedia, Taxes, SEC 10-Ks).
2.  **Short-Term RAG / SAG**: For news (e.g., "Earnings report released 5 mins ago"). We usually **don't** store this permanently in the vector DB because it becomes stale within hours.

### Where to get it:
- **Primary Source**: [Alpha Vantage News API](https://www.alphavantage.co/documentation/#news-sentiment). It gives you news + sentiment scores (Bullish/Bearish).
- **Secondary Source**: [NewsAPI.org](https://newsapi.org/). Great for general financial headlines.

### How to Integrate:
1.  **The "Search" Tool**: Instead of just querying ChromaDB, the **Market Insights Agent** has a tool called `fetch_live_news(ticker)`.
2.  **Transient RAG**: If the news is very long, the agent can:
    -   Fetch the news via API.
    -   Store chunks of it in a **temporary** (in-memory) vector store.
    -   Perform a mini-RAG query just for that specific user request.

### Where it fits in the UI:
- **Market Insights Tab**: This is the home for real-time news.
- **Sparklines & Sentiment**: Use the news to populate the "Sentiment Bar" in the UI prototype.

---

## 🏗️ Project Structure: Same or Separate?
Keep RAG in the **same codebase** but separated:
1.  **`backend/scripts/ingest/`**: For "off-line" scraping and DB filling.
2.  **`backend/src/tools/rag_tool.py`**: For "on-line" retrieval used by Agents.

---

## Step 7: Agent Integration (LangGraph)
In Finnie AI, RAG is a **Tool**.
1.  The **Supervisor** hears a question.
2.  The Supervisor routes the state to the **Financial Q&A Worker**.
3.  The Q&A Worker calls the `retrieve_context` tool.
4.  The Worker generates the final answer and sends it back to the Supervisor.


---

## Summary Checklist for Development:
- [ ] Install `chromadb` and `langchain`.
- [ ] Choose an Embedding Model (OpenAI).
- [ ] Setup the `VectorStore` class in `backend/src/utils/vector_store.py`.
- [ ] Create an ingestion script to "prime the pump" with data.
- [ ] Write the retrieval logic for the specialist worker agents.
