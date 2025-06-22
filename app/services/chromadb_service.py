"""
ChromaDB service for storing and querying facial embeddings.
"""
import chromadb
from chromadb.config import Settings
from loguru import logger
from typing import Dict, Any, List, Optional
from app.config import settings
import os

class ChromaDBService:
    def __init__(self, collection_name: str = None) -> None:
        """Initialize ChromaDB client and collection."""
        if collection_name is None:
            collection_name = getattr(settings, "CHROMA_COLLECTION", "face_profiles")

        # Use absolute path for persistent storage
        persist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../chromadb_data"))
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(collection_name)
        logger.info(f"ChromaDB collection '{collection_name}' initialized at {persist_dir}.")

    def add_embedding(self, embedding_id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        """Add a facial embedding and its metadata to the collection."""
        try:
            self.collection.add(
                ids=[embedding_id],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            logger.info(f"Embedding {embedding_id} added to ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to add embedding to ChromaDB: {e}")
            raise

    def query_embedding(self, embedding: List[float], n_results: int = 1) -> dict:
        """Query the collection for nearest neighbors to the given embedding."""
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                include=["distances", "metadatas", "embeddings"]
            )
            logger.info(f"Queried ChromaDB for nearest neighbors.")
            return results
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            raise

    def delete_by_filename(self, filename: str) -> None:
        """Delete embedding(s) from the collection by filename in metadata."""
        try:
            self.collection.delete(where={"filename": filename})
        except Exception as e:
            logger.error(f"Failed to delete embedding by filename '{filename}': {e}")
            raise

# Singleton instance for use across the app
chromadb_service = ChromaDBService()
