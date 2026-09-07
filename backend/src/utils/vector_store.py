import os
import chromadb
from langchain_chroma import Chroma
from dotenv import load_dotenv
from langsmith import traceable
from src.utils.embeddings_factory import get_embeddings

# Load environment variables from .env file if present
load_dotenv()

# Local fallback: absolute path for persistent storage when running without Chroma Cloud
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DB_DIR = os.environ.get("CHROMA_DB_DIR", os.path.join(BASE_DIR, "chroma_db"))


class VectorStoreManager:
    """
    Manages connections and operations to ChromaDB.
    Automatically connects to Chroma Cloud when CHROMA_API_KEY is set,
    otherwise falls back to a local on-disk instance for development.
    """

    def __init__(self, collection_name: str = "educational_kb", use_cloud: bool = None):
        # --- Embeddings Setup (vendor-agnostic via factory) ---
        # Change the EMBEDDING_PROVIDER env var to switch providers without code changes.
        self.embeddings = get_embeddings()
        self.collection_name = collection_name

        # --- Database Connection Setup ---
        # use_cloud can be explicitly passed (e.g. from CLI flag), otherwise auto-detect from env.
        chroma_api_key = os.environ.get("CHROMA_API_KEY")
        chroma_tenant = os.environ.get("CHROMA_TENANT", "")
        chroma_database = os.environ.get("CHROMA_DATABASE", "")

        connect_to_cloud = use_cloud if use_cloud is not None else bool(chroma_api_key and chroma_api_key.strip())

        if connect_to_cloud:
            # Production: Connect to Chroma Cloud
            print(f"Connecting to Chroma Cloud (database: '{chroma_database}')...")
            cloud_client = chromadb.CloudClient(
                api_key=chroma_api_key,
                tenant=chroma_tenant,
                database=chroma_database,
            )
            self.db = Chroma(
                client=cloud_client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )
            self._is_cloud = True
            print("Connected to Chroma Cloud successfully.")
        else:
            # Development: Use local on-disk ChromaDB
            print(f"No CHROMA_API_KEY found. Using local ChromaDB instance at {LOCAL_DB_DIR}.")
            self.db = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=LOCAL_DB_DIR,
            )
            self._is_cloud = False

    def _make_chroma_db(self):
        """Helper to re-instantiate the Chroma DB connection (used after reset)."""
        if self._is_cloud:
            chroma_api_key = os.environ.get("CHROMA_API_KEY")
            cloud_client = chromadb.CloudClient(
                api_key=chroma_api_key,
                tenant=os.environ.get("CHROMA_TENANT", ""),
                database=os.environ.get("CHROMA_DATABASE", ""),
            )
            return Chroma(
                client=cloud_client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )
        else:
            return Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=LOCAL_DB_DIR,
            )

    def reset_collection(self):
        """
        Completely deletes the current collection and all its documents (Drop-and-Replace strategy).
        Works for both local and Chroma Cloud instances.
        """
        print(f"Resetting the '{self.collection_name}' collection...")
        self.db.delete_collection()
        self.db = self._make_chroma_db()
        print("Collection reset successfully.")

    def add_documents(self, documents):
        """Adds LangChain Document objects to the vector store."""
        print(f"Adding {len(documents)} chunks to the '{self.collection_name}' collection...")
        self.db.add_documents(documents)
        print("Data added successfully.")

    @traceable(name="ChromaDB RAG Search", run_type="retriever")
    def search(self, query: str, k: int = 3, target_country: str = None):
        """Searches the vector store for the top k most similar chunks, with optional country filtering and fallback."""
        if target_country:
            filter_dict = {"country": target_country}
            try:
                results = self.db.similarity_search(query, k=k, filter=filter_dict)
                if results:
                    return results
            except Exception as e:
                print(f"[FINNIE-AI] Warning: search with filter {filter_dict} failed: {e}")
        # Fallback to unfiltered search if filtered search has 0 results or errors
        try:
            return self.db.similarity_search(query, k=k)
        except Exception as e:
            print(f"[FINNIE-AI] Warning: similarity_search failed: {e}")
            return []
