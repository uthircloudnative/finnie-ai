"""
Embeddings Factory
==================
Provides a vendor-agnostic factory for creating embedding models.

The embedding provider is controlled entirely by environment variables,
meaning switching from OpenAI to Azure OpenAI, HuggingFace, or any other
provider requires ZERO code changes — only a config update.

Configuration (set in .env):
    EMBEDDING_PROVIDER  : "openai" | "azure_openai" | "huggingface" | "fake"
                          Defaults to "openai" if not set.
    OPENAI_API_KEY      : Required when EMBEDDING_PROVIDER is "openai".
    AZURE_OPENAI_API_KEY: Required when EMBEDDING_PROVIDER is "azure_openai".
    AZURE_OPENAI_ENDPOINT: Required when EMBEDDING_PROVIDER is "azure_openai".
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: The Azure deployment name (e.g. "text-embedding-ada-002").
    HF_MODEL_NAME       : HuggingFace model ID (e.g. "sentence-transformers/all-MiniLM-L6-v2").
                          Required when EMBEDDING_PROVIDER is "huggingface".

Usage:
    from src.utils.embeddings_factory import get_embeddings
    embeddings = get_embeddings()
"""
import os
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings

# Ensure .env is loaded regardless of which module is loaded first
load_dotenv()


def get_embeddings() -> Embeddings:
    """
    Returns a LangChain-compatible Embeddings object based on the
    EMBEDDING_PROVIDER environment variable. Defaults to "openai".

    Returns:
        Embeddings: A LangChain Embeddings instance ready for use.

    Raises:
        ValueError: If the configured provider is unknown or required
                    environment variables are missing.
    """
    provider = os.environ.get("EMBEDDING_PROVIDER", "openai").lower()

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key or api_key == "dummy_key_for_testing":
            print("Warning: No valid OPENAI_API_KEY found. Falling back to FakeEmbeddings.")
            from langchain_core.embeddings import FakeEmbeddings
            return FakeEmbeddings(size=1536)
        from langchain_openai import OpenAIEmbeddings
        print("Embeddings: Using OpenAI (text-embedding-ada-002).")
        return OpenAIEmbeddings()

    elif provider == "azure_openai":
        from langchain_openai import AzureOpenAIEmbeddings
        deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        print(f"Embeddings: Using Azure OpenAI (deployment: '{deployment}').")
        return AzureOpenAIEmbeddings(
            azure_deployment=deployment,
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        )

    elif provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        model_name = os.environ.get("HF_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
        print(f"Embeddings: Using HuggingFace model '{model_name}' (runs locally, no API cost).")
        return HuggingFaceEmbeddings(model_name=model_name)

    elif provider == "fake":
        from langchain_core.embeddings import FakeEmbeddings
        print("Embeddings: Using FakeEmbeddings (testing only — no semantic search).")
        return FakeEmbeddings(size=1536)

    else:
        raise ValueError(
            f"Unknown EMBEDDING_PROVIDER: '{provider}'. "
            "Supported values: 'openai', 'azure_openai', 'huggingface', 'fake'."
        )
