import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Define the absolute path for persistent storage
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

class VectorStoreManager:
    """Manages connections and operations to the local ChromaDB instance."""
    
    def __init__(self, collection_name: str = "educational_kb"):
        # We will use the standard ada-002 embeddings for now (can upgrade to text-embedding-ada-002 later)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key == "dummy_key_for_testing":
            print("Warning: No valid OPENAI_API_KEY found. Using FakeEmbeddings for testing/development.")
            from langchain_core.embeddings import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=1536) # Same size as OpenAI text-embedding-ada-002
        else:
            self.embeddings = OpenAIEmbeddings()
        self.collection_name = collection_name
        self.db = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=DB_DIR
        )

    def add_documents(self, documents):
        """Adds LangChain Document objects to the vector store."""
        print(f"Adding {len(documents)} chunks to the '{self.collection_name}' collection...")
        self.db.add_documents(documents)
        print("Data added successfully.")

    def search(self, query: str, k: int = 3, target_country: str = None):
        """Searches the vector store for the top k most similar chunks, with optional country filtering."""
        filter_dict = None
        if target_country:
             filter_dict = {"country": target_country}
             
        if filter_dict:
            return self.db.similarity_search(query, k=k, filter=filter_dict)
        return self.db.similarity_search(query, k=k)
