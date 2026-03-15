import os
import sys

# Determine the absolute path dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(BACKEND_DIR)

from src.utils.vector_store import VectorStoreManager

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_retrieval.py \"Your financial question here\"")
        print("Example: python test_retrieval.py \"What is an ETF?\"")
        sys.exit(1)

    query = sys.argv[1]
    
    print(f"\n[Test] Connecting to ChromaDB 'educational_kb' collection...\n")
    try:
        vector_store = VectorStoreManager(collection_name="educational_kb")
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        sys.exit(1)
        
    print(f"[Query] User Question: '{query}'\n")
    print(f"Executing Similarity Search...\n")
    
    # Retrieve top 3 closest chunks
    results = vector_store.search(query, k=3)
    
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
