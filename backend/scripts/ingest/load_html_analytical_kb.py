"""
load_html_analytical_kb.py

Reads all saved Investopedia HTML files from the content/analtical_kb/ folder
and loads them into ChromaDB's 'analytical_kb' collection.

Pattern mirrors investor_gov_scraper.py:
  - Same RecursiveCharacterTextSplitter config (500 chars / 50 overlap)
  - Same Drop-and-Replace strategy via reset_collection()
  - Same process_and_store(use_cloud) entry point
  - Same --db / --reset CLI flags

Multi-country support:
  Each chunk is tagged with 'country' metadata. These concepts (Sharpe, Beta, etc.)
  are GLOBALLY applicable theory, so they're tagged 'GLOBAL'. When you later add
  country-specific articles (e.g., SEBI regulations for India, FCA for UK) just
  save them in a sub-folder named after the country code and the loader will
  automatically tag them correctly.

  Folder layout (future):
    content/analtical_kb/            ← GLOBAL theory (current)
    content/analtical_kb/IN/         ← India-specific articles
    content/analtical_kb/UK/         ← UK-specific articles
    content/analtical_kb/AU/         ← Australia-specific articles

Usage:
    uv run scripts/ingest/load_html_analytical_kb.py
    uv run scripts/ingest/load_html_analytical_kb.py --db local
    uv run scripts/ingest/load_html_analytical_kb.py --db cloud
    uv run scripts/ingest/load_html_analytical_kb.py --db local --reset
"""

import os
import sys
import argparse
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# ── Path setup (mirrors investor_gov_scraper.py) ──────────────────────────────
SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from src.utils.vector_store import VectorStoreManager

# ── Configuration ─────────────────────────────────────────────────────────────

# Root folder containing HTML files.
# Sub-folders named with ISO country codes (e.g. 'IN', 'UK') are tagged accordingly.
CONTENT_DIR = SCRIPT_DIR / "content" / "analtical_kb"

COLLECTION_NAME = "analytical_kb"

# Investopedia Finance: article body lives inside .article-body-content
# Fallback: article p (broader, picks up more content)
PRIMARY_SELECTOR   = ".article-body-content p"
FALLBACK_SELECTOR  = "article p"

# Drop paragraphs that are too short or are known Investopedia junk
MIN_PARA_LEN = 60
JUNK_PHRASES = [
    "Get personalized, AI-powered answers",   # Investopedia AI widget promo
    "Disclosure: Investopedia does not",       # Legal footer
    "Investopedia requires writers to use",    # Editorial policy note
    "Reviewed by",
    "Fact checked by",
    "Cookie",
    "Privacy Policy",
]

# Mirrors investor_gov_scraper.py chunk settings
CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50


# ── Topic / Category mapping ──────────────────────────────────────────────────
# Maps the HTML filename stem to human-readable topic + category labels.
# This enriches each chunk's metadata for filtered RAG retrieval.
TOPIC_MAP: dict[str, dict[str, str]] = {
    "Alpha":                   {"topic": "Alpha",                   "category": "metric_benchmark"},
    "Beta":                    {"topic": "Beta",                    "category": "metric_benchmark"},
    "Diversification":        {"topic": "Diversification",         "category": "diversification"},
    "EfficientFrontier":      {"topic": "Efficient Frontier",      "category": "theory"},
    "MaximumDrawdown":        {"topic": "Maximum Drawdown",        "category": "metric_benchmark"},
    "ModernPortfolioTheory":  {"topic": "Modern Portfolio Theory", "category": "theory"},
    "RebalancingYourPortfolio": {"topic": "Portfolio Rebalancing", "category": "strategy"},
    "SharpeRatio":            {"topic": "Sharpe Ratio",            "category": "metric_benchmark"},
}


# ── Core helpers ──────────────────────────────────────────────────────────────

def detect_country(html_path: Path) -> str:
    """
    Determine the country tag from the file's parent folder.

    - Files directly in CONTENT_DIR → 'GLOBAL'
    - Files in CONTENT_DIR/IN/      → 'IN'
    - Files in CONTENT_DIR/UK/      → 'UK'
    etc.
    """
    parent = html_path.parent
    if parent == CONTENT_DIR:
        return "GLOBAL"
    return parent.name.upper()


def is_junk(text: str) -> bool:
    """Return True if the paragraph should be discarded."""
    if len(text) < MIN_PARA_LEN:
        return True
    return any(phrase in text for phrase in JUNK_PHRASES)


def parse_html_file(html_path: Path) -> dict | None:
    """
    Parse a single saved Investopedia HTML file.

    Returns a dict with 'text' (joined paragraphs) and 'metadata', or None on failure.
    Mirrors the return structure of investor_gov_scraper.scrape_term().
    """
    stem = html_path.stem          # e.g. "SharpeRatio"
    country = detect_country(html_path)
    topic_info = TOPIC_MAP.get(stem, {"topic": stem, "category": "general"})

    print(f"  Parsing  {html_path.name}  [country={country}] ...")

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Page title for metadata
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else stem

    # -- Content extraction (same two-level fallback as investor_gov_scraper.py) --
    tags = soup.select(PRIMARY_SELECTOR)
    if not tags:
        print(f"    ⚠ Primary selector empty, falling back to '{FALLBACK_SELECTOR}'")
        tags = soup.select(FALLBACK_SELECTOR)

    paragraphs = []
    for tag in tags:
        text = tag.get_text(strip=True)
        if not is_junk(text):
            paragraphs.append(text)

    if not paragraphs:
        print(f"    ❌ No usable content found in {html_path.name} — skipping.")
        return None

    text_content = "\n\n".join(paragraphs)

    # -- Canonical source URL from <link rel="canonical"> if present --
    canonical = soup.find("link", rel="canonical")
    source_url = canonical["href"] if canonical else f"file://{html_path}"

    return {
        "text": text_content,
        "metadata": {
            # ── Standard fields (same as investor_gov_scraper.py) ──
            "source":        source_url,
            "type":          "analytical_theory",
            "ingested_date": str(date.today()),

            # ── Topic fields (same as analytical_kb_seed.json) ──
            "topic":         topic_info["topic"],
            "category":      topic_info["category"],

            # ── Country / market filter ──────────────────────────────
            # 'GLOBAL'  = concept applies everywhere (MPT, Sharpe, etc.)
            # 'IN','UK'  = country-specific article (future sub-folders)
            "country":       country,

            # ── Extra: page title for human-readable debug / retrieval UI ──
            "title":         page_title,
        },
    }


# ── Pipeline ──────────────────────────────────────────────────────────────────

def process_and_store(use_cloud: bool = None, reset: bool = False) -> None:
    """
    Full ingestion pipeline. Mirrors investor_gov_scraper.process_and_store().

    1. Discover all .html files (recursively, to pick up country sub-folders)
    2. Parse & filter content
    3. Chunk with RecursiveCharacterTextSplitter
    4. Store in ChromaDB (Drop-and-Replace when --reset is given)
    """
    print("=" * 60)
    print("  Finnie AI — analytical_kb HTML Loader")
    print("=" * 60)

    # 1. Discover HTML files
    html_files = sorted(CONTENT_DIR.rglob("*.html"))
    if not html_files:
        print(f"❌  No HTML files found under {CONTENT_DIR}")
        return

    print(f"\n📂  Found {len(html_files)} HTML file(s) under '{CONTENT_DIR.name}/'")
    print("--- Starting HTML Ingestion Pipeline ---\n")

    # 2. Parse & build Documents
    documents_to_store: list[Document] = []
    for html_path in html_files:
        parsed = parse_html_file(html_path)
        if parsed and parsed["text"]:
            doc = Document(
                page_content=parsed["text"],
                metadata=parsed["metadata"],
            )
            documents_to_store.append(doc)

    print(f"\n✅  Parsed {len(documents_to_store)} / {len(html_files)} files successfully.")

    if not documents_to_store:
        print("No documents parsed. Exiting.")
        return

    # 3. Chunking — same settings as investor_gov_scraper.py
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
    )
    print("\nChunking documents...")
    chunked_documents = text_splitter.split_documents(documents_to_store)
    print(f"Created {len(chunked_documents)} total chunks.")

    # 4. Connect & store
    print(f"\nConnecting to ChromaDB  (mode: {('cloud' if use_cloud else 'local') if use_cloud is not None else 'auto'})...")
    vector_store = VectorStoreManager(
        collection_name=COLLECTION_NAME,
        use_cloud=use_cloud,
    )

    if reset:
        print(f"🗑️   Resetting collection '{COLLECTION_NAME}' (Drop-and-Replace)...")
        vector_store.reset_collection()

    print(f"🚀  Adding {len(chunked_documents)} chunks to '{COLLECTION_NAME}'...")
    vector_store.add_documents(chunked_documents)

    # 5. Summary
    countries = sorted({d.metadata["country"] for d in chunked_documents})
    categories = sorted({d.metadata["category"] for d in chunked_documents})
    print("\n--- Pipeline Complete ---")
    print(f"   Collection : {COLLECTION_NAME}")
    print(f"   Files      : {len(documents_to_store)}")
    print(f"   Chunks     : {len(chunked_documents)}")
    print(f"   Countries  : {', '.join(countries)}")
    print(f"   Categories : {', '.join(categories)}")
    print("\n💡  Test retrieval:")
    print('   uv run scripts/test_retrieval.py "What is a good Sharpe Ratio?" analytical_kb')
    print('   uv run scripts/test_retrieval.py "Explain Beta in investing" analytical_kb')


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load Investopedia HTML files into the analytical_kb ChromaDB collection."
    )
    parser.add_argument(
        "--db",
        choices=["local", "cloud"],
        default=None,
        help="Force DB mode: 'local' or 'cloud'. Defaults to auto-detect from CHROMA_API_KEY in .env",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the collection before loading (prevents duplicates).",
    )
    args = parser.parse_args()

    use_cloud: bool | None = None
    if args.db == "cloud":
        use_cloud = True
    elif args.db == "local":
        use_cloud = False

    process_and_store(use_cloud=use_cloud, reset=args.reset)
