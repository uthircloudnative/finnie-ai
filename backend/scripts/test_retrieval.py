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
        "country",
        nargs="?",
        default=None,
        help="Optional country code filter (e.g. USA)"
    )
    parser.add_argument(
        "--db",
        choices=["local", "cloud"],
        default=None,
        help="Force database mode: 'local' (on-disk) or 'cloud' (Chroma Cloud). Defaults to auto-detect from CHROMA_API_KEY in .env"
    )
    args = parser.parse_args()

    query = args.query
    target_country = args.country

    use_cloud = None
    if args.db == "cloud":
        use_cloud = True
    elif args.db == "local":
        use_cloud = False

    print(f"\n[Test] Connecting to ChromaDB 'educational_kb' collection...\n")
    try:
        vector_store = VectorStoreManager(collection_name="educational_kb", use_cloud=use_cloud)
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        sys.exit(1)

    print(f"[Query] User Question: '{query}'")
    if target_country:
        print(f"[Filter] Target Country: '{target_country}'")
    print(f"Executing Similarity Search...\n")

    # Retrieve top 3 closest chunks using the new optional filter
    results = vector_store.search(query, k=3, target_country=target_country)

    if not results:
        print("No results found in the database. Did you run the ingestion script?")
        sys.exit(0)

    print("-" * 50)
    print("RETRIEVED CONTEXT (Top 3 Chunks):")
    print("-" * 50)
    for i, doc in enumerate(results):
        print(f"\nChunk {i+1} [Similarity Rank #{i+1}]")
        print(f"Source URL: {doc.metadata.get('source', 'Unknown')}")
        print(f"Term: {doc.metadata.get('term', 'Unknown')}")
        print(f"Content:\n{doc.page_content}\n")
    print("-" * 50)

    print("\n[Evaluation] Are these chunks highly relevant to the User Question? If yes, Retrieval is working.")

if __name__ == "__main__":
    main()
