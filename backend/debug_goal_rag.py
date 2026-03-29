import os
import sys
from pathlib import Path

# Path setup
SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from src.utils.vector_store import VectorStoreManager

def debug_rag():
    print("--- Debugging Goal Rules RAG ---")
    vsm = VectorStoreManager(collection_name="goal_rules")
    
    # Check total count
    count = vsm.db._collection.count()
    print(f"Total documents in 'goal_rules': {count}")
    
    # Test search for India
    print("\nTesting Search for IN...")
    results = vsm.search("80C limits for India", k=5, target_country="IN")
    print(f"Results for IN ({len(results)}):")
    for i, res in enumerate(results):
        print(f"[{i}] Metadata: {res.metadata}")
        print(f"    Content: {res.page_content[:100]}...")

    # Test search for USA
    print("\nTesting Search for USA...")
    results = vsm.search("401k limits for USA", k=5, target_country="USA")
    print(f"Results for USA ({len(results)}):")
    for i, res in enumerate(results):
        print(f"[{i}] Metadata: {res.metadata}")
        print(f"    Content: {res.page_content[:100]}...")

if __name__ == "__main__":
    debug_rag()
