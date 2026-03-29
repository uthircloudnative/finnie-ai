"""
ingest_regulatory_kb.py
=======================
Reads the 2026 US and India tax/contribution Markdown files and loads them 
into ChromaDB's 'goal_rules' collection.

This collection provides the 'Regulatory Brain' for the Goal Strategist.
"""
import os
import sys
import argparse
from datetime import date
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# ── Path setup ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from src.utils.vector_store import VectorStoreManager

# ── Configuration ─────────────────────────────────────────────────────────────
CONTENT_DIR = SCRIPT_DIR / "content" / "regulatory_kb"
COLLECTION_NAME = "goal_rules"

# Regulatory data is fairly dense with numbers; we use a slightly larger overlap
CHUNK_SIZE    = 600
CHUNK_OVERLAP = 100


def detect_country(file_path: Path) -> str:
    """Detects country from filename prefix (e.g., 'US_...' -> 'USA')."""
    name = file_path.name.upper()
    if name.startswith("US_"):
        return "USA"
    if name.startswith("INDIA_"):
        return "IN"
    return "GLOBAL"


def process_and_store(use_cloud: bool = None, reset: bool = False) -> None:
    print("=" * 60)
    print("  Finnie AI — goal_rules Regulatory Loader (2026)")
    print("=" * 60)

    # 1. Discover Markdown files
    md_files = sorted(CONTENT_DIR.glob("*.md"))
    if not md_files:
        print(f"❌  No Markdown files found under {CONTENT_DIR}")
        return

    print(f"\n📂  Found {len(md_files)} Markdown file(s) under '{CONTENT_DIR.name}/'")

    # 2. Parse & build Documents
    documents_to_store: list[Document] = []
    for md_path in md_files:
        country = detect_country(md_path)
        print(f"  Parsing {md_path.name} [country={country}] ...")
        
        loader = TextLoader(str(md_path))
        raw_docs = loader.load()
        
        for d in raw_docs:
            d.metadata.update({
                "source": md_path.name,
                "type": "regulatory_rulebook",
                "country": country,
                "ingested_date": str(date.today()),
                "year": "2026"
            })
            documents_to_store.append(d)

    # 3. Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
    )
    print("\nChunking regulatory documents...")
    chunked_documents = text_splitter.split_documents(documents_to_store)
    print(f"Created {len(chunked_documents)} total chunks.")

    # 4. Connect & store
    vector_store = VectorStoreManager(
        collection_name=COLLECTION_NAME,
        use_cloud=use_cloud,
    )

    if reset:
        print(f"🗑️   Resetting collection '{COLLECTION_NAME}'...")
        vector_store.reset_collection()

    print(f"🚀  Adding {len(chunked_documents)} chunks to '{COLLECTION_NAME}'...")
    vector_store.add_documents(chunked_documents)

    print("\n--- Ingestion Complete ---")
    print(f"   Collection : {COLLECTION_NAME}")
    print(f"   Chunks     : {len(chunked_documents)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Regulatory MD files into goal_rules collection.")
    parser.add_argument("--db", choices=["local", "cloud"], default=None)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    use_cloud = None
    if args.db == "cloud": use_cloud = True
    elif args.db == "local": use_cloud = False

    process_and_store(use_cloud=use_cloud, reset=args.reset)
