"""
test_retrieval.py — Finnie AI RAG Retrieval Tester
====================================================
A generic script to test semantic search against any ChromaDB collection.
Run this AFTER running the corresponding ingestion script to verify chunks
are loading and retrieval is returning relevant results.

USAGE:
    uv run scripts/test_retrieval.py "<query>" [collection] [--country CODE] [--db local|cloud] [--top N]

ARGUMENTS:
    query       (required) Natural language question to search
    collection  (optional) Collection name to query — default: educational_kb
    --country   (optional) Filter by country tag (e.g. GLOBAL, USA, IN, UK)
    --db        (optional) Force 'local' or 'cloud' — default: auto from .env
    --top       (optional) Number of chunks to return — default: 3

─────────────────────────────────────────────────────────────
COLLECTION 1: educational_kb  (beginner financial terms)
  Loaded by : scripts/ingest/investor_gov_scraper.py
  Source    : investor.gov glossary pages

  Test locally:
    uv run scripts/test_retrieval.py "What is an ETF?" --db local
    uv run scripts/test_retrieval.py "How does compound interest work?" educational_kb --db local
    uv run scripts/test_retrieval.py "What is a Roth IRA?" educational_kb --country USA --db local

─────────────────────────────────────────────────────────────
COLLECTION 2: analytical_kb  (portfolio analysis theory)
  Loaded by : scripts/ingest/load_html_analytical_kb.py
  Source    : Saved Investopedia HTML pages (content/analtical_kb/)
  Topics    : Sharpe Ratio, Beta, Alpha, Max Drawdown, MPT,
              Efficient Frontier, Diversification, Rebalancing

  Test locally:
    uv run scripts/test_retrieval.py "What is a good Sharpe Ratio?" analytical_kb --db local
    uv run scripts/test_retrieval.py "Explain Beta and market risk" analytical_kb --db local
    uv run scripts/test_retrieval.py "How often should I rebalance my portfolio?" analytical_kb --db local
    uv run scripts/test_retrieval.py "What is Modern Portfolio Theory?" analytical_kb --country GLOBAL --db local

  Country-specific (future — add HTML files to content/analtical_kb/IN/ etc.):
    uv run scripts/test_retrieval.py "Portfolio diversification rules" analytical_kb --country IN --db local

─────────────────────────────────────────────────────────────
PRE-REQUISITES:
  1. .env must have OPENAI_API_KEY (used for embeddings)
  2. Run the ingestion script for the collection you want to test
  3. Always run from the backend/ directory:
       cd backend && uv run scripts/test_retrieval.py ...
"""

import os
import sys
import argparse

# Determine the absolute path dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # .../backend/scripts
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)                 # .../backend
sys.path.append(BACKEND_DIR)

from src.utils.vector_store import VectorStoreManager

def main():
    parser = argparse.ArgumentParser(description="Finnie AI RAG Retrieval Test")
    parser.add_argument("query", help="The financial question to search for")
    parser.add_argument(
        "collection",
        nargs="?",
        default="educational_kb",
        help="ChromaDB collection to query (default: educational_kb). Use 'analytical_kb', 'tax_policy_kb', etc."
    )
    parser.add_argument(
        "--country",
        default=None,
        help="Optional country code filter (e.g. USA, GLOBAL, IN, UK)"
    )
    parser.add_argument(
        "--db",
        choices=["local", "cloud"],
        default=None,
        help="Force database mode: 'local' (on-disk) or 'cloud' (Chroma Cloud). Defaults to auto-detect from CHROMA_API_KEY in .env"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of chunks to retrieve (default: 3)"
    )
    args = parser.parse_args()

    query = args.query
    collection_name = args.collection
    target_country = args.country

    use_cloud = None
    if args.db == "cloud":
        use_cloud = True
    elif args.db == "local":
        use_cloud = False

    print(f"\n[Test] Connecting to ChromaDB '{collection_name}' collection...\n")
    try:
        vector_store = VectorStoreManager(collection_name=collection_name, use_cloud=use_cloud)
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        sys.exit(1)

    print(f"[Query]      : '{query}'")
    print(f"[Collection] : {collection_name}")
    if target_country:
        print(f"[Country]    : {target_country}")
    print(f"[Top-K]      : {args.top}")
    print(f"Executing Similarity Search...\n")

    results = vector_store.search(query, k=args.top, target_country=target_country)

    if not results:
        print("No results found in the database. Did you run the ingestion script?")
        sys.exit(0)

    print("-" * 50)
    print("RETRIEVED CONTEXT (Top 3 Chunks):")
    print("-" * 50)
    for i, doc in enumerate(results):
        # 'term' used by educational_kb, 'topic' used by analytical_kb
        label = doc.metadata.get('topic') or doc.metadata.get('term', 'Unknown')
        country = doc.metadata.get('country', '')
        category = doc.metadata.get('category', '')
        source = doc.metadata.get('source', 'Unknown')
        print(f"\nChunk {i+1}  |  topic={label}  country={country}  category={category}")
        print(f"Source : {source}")
        print(f"Content:\n{doc.page_content}\n")
    print("-" * 50)

    print("\n[Evaluation] Are these chunks highly relevant to the User Question? If yes, Retrieval is working.")

if __name__ == "__main__":
    main()
