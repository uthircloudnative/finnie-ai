# Finnie AI: Progress Log & Next Steps

**Date**: 2026-03-15
**Current Status**: 🟢 Phase 1 (RAG) Hardened & Production-Ready
**Learning Mode**: 🎓 **Instructor-Led Hands-On** (User-led coding with Agent guidance)

---

## ✅ What We Accomplished Today (March 15)
1.  **Vendor-Agnostic Embeddings**: Implemented an **Embeddings Factory Pattern** to decouple from OpenAI, supporting Azure and local Hugging Face models via config.
2.  **Hybrid ChromaDB Setup**: Enabled seamless switching between Local on-disk storage and **Chroma Cloud** via `.env` auto-detection or CLI flags.
3.  **CLI Accessibility**: Added `--db local|cloud` flags to all scripts for dynamic runtime control.
4.  **Storage Optimization**: Automated physical directory cleanup in local mode to prevent orphaned directory bloat.
5.  **Documentation Audit**: Fully updated all technical guides (`INGESTION_PIPELINES`, `DESIGN`, `README`) to reflect production infrastructure.

---

## ✅ Previous Accomplishments (March 10)
1.  **RAG Architectural Deep-Dive**: Confirmed a modular "One DB, Five Collections" structure to balance specialization and simplicity.
2.  **Internationalization (i18n)**: Designed a scalable multi-country strategy using **Metadata Filtering**, avoiding architectural bloat.
3.  **Data Sourcing Blueprint**: Detailed the exact sources (Investor.gov, IRS, SEC, Vanguard, Alpha Vantage), update frequencies, and content types for all 5 collections.
4.  **Visual Logic**: Created a comprehensive **Mermaid Architecture Diagram** in `RAG_GUIDE.md` for future team/reference use.
5.  **Evaluation Strategy**: Defined a two-tier testing framework (Retrieval vs. Generation) and introduced the **RAGAS** framework for automated quality scoring.
6.  **Cloud Strategy**: Finalized the deployment plan (Unified Repo -> Distributed Cloud) using Vercel, Cloud Run, and managed Vector DBs.

---

## ✅ Previous Accomplishments (March 09)
- Production-grade planning (`PROJECT_PLAN.md`).
- Multi-agent orchestrator design (`DESIGN.md`).
- Engineering standards (`STANDARDS.md`).
- High-fidelity interactive prototype (`prototype/index.html`).

---

## 🚀 Plan of Action (Next Session)

We are starting **Phase 1: Intelligence & Data Grounding (Bottom-Up)**.

### 1. RAG Core Pipeline
- Create `backend/scripts/ingest/` and implement the base Ingestion script.
- Setup local ChromaDB and create the `educational_kb` collection.
- Scrape 10-20 core financial terms from Investor.gov to "prime" the system.

### 2. Retrieval Verification
- Build a standalone `test_retrieval.py` to verify the "Search" actually finds relevant snippets.
- Finalize the `OpenAIEmbeddings` configuration.

### 3. Move to Phase 2 (Foundation)
- Once RAG is working, we will build the LangGraph shell and UI to host it.

---

## 📂 Key Files to Review Upon Resume
- [RAG_GUIDE.md](./RAG_GUIDE.md) (The master blueprint for AI intelligence)
- [PROJECT_PLAN.md](./PROJECT_PLAN.md)
- [prototype/index.html](../prototype/index.html)

