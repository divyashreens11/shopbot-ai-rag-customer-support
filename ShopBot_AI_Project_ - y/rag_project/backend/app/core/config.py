"""
Configuration Settings
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Google Gemini (Primary - Free tier available!)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")
    GEMINI_MODEL: str = "models/gemini-2.5-flash"  # Latest fast model
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    # OpenAI (Fallback)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chromadb"
    CHROMA_COLLECTION_NAME: str = "ecommerce_support"

    # Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Retrieval
    TOP_K_RESULTS: int = 4
    CONFIDENCE_THRESHOLD: float = 0.35

    # HITL
    HITL_KEYWORDS: list = [
        "refund", "fraud", "legal", "lawsuit", "escalate",
        "manager", "supervisor", "complaint", "urgent", "account suspended"
    ]

    class Config:
        env_file = ".env"

settings = Settings()
