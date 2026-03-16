import os
import sys
import requests
from datetime import date
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Determine the absolute path dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
import sys
sys.path.append(BACKEND_DIR)

from src.utils.vector_store import VectorStoreManager

# The targeted list of beginner terms we want to definitively ground Finnie on.
# We map the term to its specific Investor.gov URL stub.
TARGET_TERMS = {
    "Exchange-Traded Fund (ETF)": "exchange-traded-fund-etf",
    "Stocks": "stocks",
    "Bonds": "bonds",
    "Mutual Funds": "mutual-funds",
    "Index Fund": "index-fund",
    "Diversification": "diversification",
    "Asset Allocation": "asset-allocation",
    "Risk Tolerance": "risk-tolerance",
    "Compound Interest": "compound-interest",
    "401(k) Plan": "401k-plan",
    "Individual Retirement Account (IRA)": "individual-retirement-account-ira",
    "Roth IRA": "roth-ira",
    "Inflation": "inflation",
    "Bull Market": "bull-market",
    "Bear Market": "bear-market"
}

BASE_URL = "https://www.investor.gov/introduction-investing/investing-basics/glossary/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_term(term, slug):
    """Scrape the main text content for a specific term from Investor.gov."""
    url = f"{BASE_URL}{slug}"
    print(f"Scraping {term} from {url}...")
    
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"  -> Failed to fetch {term}. Status: {response.status_code}")
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Investor.gov typically puts the glossary definition inside the main content area
    # The actual content is usually inside a div with class 'field-name-body' or similar
    content_div = soup.find('div', class_='field--name-body')
    
    if not content_div:
        # Fallback: just grab all paragraphs in the main article body
        article = soup.find('article')
        if article:
             paragraphs = article.find_all('p')
        else:
             print(f"  -> Could not find article body for {term}")
             return None
    else:
        paragraphs = content_div.find_all('p')

    # Extract text from paragraphs
    text_content = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
    
    if len(text_content) < 50:
        print(f"  -> Warning: Very little content extracted for {term}")
    
    return {
        "text": text_content,
        "metadata": {
            "source": url,
            "term": term,
            "type": "definition",
            "country": "USA", # Crucial for multi-country RAG routing
            "ingested_date": str(date.today()) # Dynamically set to today's date
        }
    }

def process_and_store(use_cloud: bool = None):
    documents_to_store = []
    
    print("--- Starting Investor.gov Ingestion Pipeline (Phase 1) ---")
    
    # 1. Scrape Content
    for term, slug in TARGET_TERMS.items():
        scraped_data = scrape_term(term, slug)
        if scraped_data and scraped_data['text']:
            # Create a LangChain Document
            doc = Document(
                page_content=scraped_data['text'],
                metadata=scraped_data['metadata']
            )
            documents_to_store.append(doc)
            
    print(f"\nSuccessfully scraped {len(documents_to_store)} out of {len(TARGET_TERMS)} terms.")
    
    if not documents_to_store:
        print("No documents scraped. Exiting.")
        return

    # 2. Chunking (Partitioning)
    # We use relatively small chunks (500 chars) because definitions are dense
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " "]
    )
    
    print("Chunking documents...")
    chunked_documents = text_splitter.split_documents(documents_to_store)
    print(f"Created {len(chunked_documents)} total chunks.")

    # 3. Embedding and Storage
    print("Connecting to ChromaDB and generating embeddings...")
    
    # Pre-initialization physical cleanup for local mode to prevent directory bloat
    if use_cloud is False:
        # Import dynamically here to avoid cluttering global scope
        import shutil
        from src.utils.vector_store import LOCAL_DB_DIR
        if os.path.exists(LOCAL_DB_DIR):
            print(f"Pre-emptive cleanup of local database directory: {LOCAL_DB_DIR}")
            try:
                shutil.rmtree(LOCAL_DB_DIR)
                print("Local database directory cleared.")
            except Exception as e:
                print(f"Warning: Could not clear local database directory: {e}")

    vector_store = VectorStoreManager(collection_name="educational_kb", use_cloud=use_cloud)
    
    # Crucial: Drop and Replace strategy to prevent document duplication
    vector_store.reset_collection()
    
    vector_store.add_documents(chunked_documents)
    print("--- Pipeline Complete ---")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Investor.gov RAG Ingestion Pipeline")
    parser.add_argument(
        "--db",
        choices=["local", "cloud"],
        default=None,
        help="Force database mode: 'local' (on-disk) or 'cloud' (Chroma Cloud). Defaults to auto-detect from CHROMA_API_KEY in .env"
    )
    args = parser.parse_args()

    use_cloud = None
    if args.db == "cloud":
        use_cloud = True
    elif args.db == "local":
        use_cloud = False

    process_and_store(use_cloud=use_cloud)
