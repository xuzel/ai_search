"""Vector Store - Chroma-based vector database for RAG

Implements query caching for improved performance.
"""

import uuid
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from src.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Vector store wrapper for Chroma database with query caching"""

    def __init__(
        self,
        persist_directory: str = "./data/vector_store",
        collection_name: str = "documents",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        embedding_dimension: int = 384,
        cache_size: int = 1000,
        cache_ttl: int = 3600,
    ):
        """
        Initialize Vector Store

        Args:
            persist_directory: Directory to persist the vector store
            collection_name: Name of the collection
            embedding_model: HuggingFace embedding model name
            embedding_dimension: Dimension of embeddings
            cache_size: Maximum number of cached queries (default: 1000)
            cache_ttl: Cache time-to-live in seconds (default: 3600 = 1 hour)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.embedding_dimension = embedding_dimension
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl

        # Query cache: {query_hash: (results, timestamp)}
        self._query_cache: Dict[str, Tuple[List[Dict[str, Any]], float]] = {}

        # Embedding cache: {query_hash: embedding}
        self._embedding_cache: Dict[str, Any] = {}

        # Create persist directory if not exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Load embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Document embeddings for RAG"},
            )
            logger.info(f"Created new collection: {collection_name}")

    def _get_cache_key(self, query: str, k: int, where: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for query

        Args:
            query: Query text
            k: Number of results
            where: Metadata filter

        Returns:
            MD5 hash as cache key
        """
        # Normalize query
        normalized = query.lower().strip()

        # Include k and where filter in cache key
        cache_input = f"{normalized}|k={k}"
        if where:
            import json
            cache_input += f"|where={json.dumps(where, sort_keys=True)}"

        return hashlib.md5(cache_input.encode()).hexdigest()

    def _get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached results if valid

        Args:
            cache_key: Cache key

        Returns:
            Cached results or None if expired/missing
        """
        if cache_key not in self._query_cache:
            return None

        results, timestamp = self._query_cache[cache_key]

        # Check if expired
        if time.time() - timestamp > self.cache_ttl:
            del self._query_cache[cache_key]
            logger.debug(f"Cache expired for key: {cache_key[:8]}...")
            return None

        logger.debug(f"Cache HIT for query: {cache_key[:8]}...")
        return results

    def _cache_results(self, cache_key: str, results: List[Dict[str, Any]]) -> None:
        """Cache query results

        Args:
            cache_key: Cache key
            results: Results to cache
        """
        # Implement simple LRU: if cache too large, clear oldest entries
        if len(self._query_cache) >= self.cache_size:
            # Remove oldest 20% of entries
            sorted_items = sorted(
                self._query_cache.items(),
                key=lambda x: x[1][1]  # Sort by timestamp
            )
            num_to_remove = max(1, len(sorted_items) // 5)
            for key, _ in sorted_items[:num_to_remove]:
                del self._query_cache[key]

            logger.info(f"Cache full, removed {num_to_remove} oldest entries")

        self._query_cache[cache_key] = (results, time.time())
        logger.debug(f"Cached results (cache size: {len(self._query_cache)})")

    def _get_cached_embedding(self, query: str) -> Optional[Any]:
        """Get cached embedding for query

        Args:
            query: Query text

        Returns:
            Cached embedding or None
        """
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
        return self._embedding_cache.get(query_hash)

    def _cache_embedding(self, query: str, embedding: Any) -> None:
        """Cache query embedding

        Args:
            query: Query text
            embedding: Embedding vector
        """
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()

        # Implement simple LRU for embedding cache too
        if len(self._embedding_cache) >= self.cache_size:
            # Remove oldest entries (FIFO approximation)
            keys_to_remove = list(self._embedding_cache.keys())[:len(self._embedding_cache) // 5]
            for key in keys_to_remove:
                del self._embedding_cache[key]

        self._embedding_cache[query_hash] = embedding

    def clear_cache(self) -> None:
        """Clear all caches"""
        self._query_cache.clear()
        self._embedding_cache.clear()
        logger.info("Cleared vector store caches")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        return {
            "query_cache_size": len(self._query_cache),
            "query_cache_max": self.cache_size,
            "embedding_cache_size": len(self._embedding_cache),
            "cache_ttl_seconds": self.cache_ttl,
        }

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents to the vector store

        Args:
            texts: List of text chunks to add
            metadatas: Optional metadata for each chunk
            ids: Optional IDs for each chunk (auto-generated if not provided)

        Returns:
            List of document IDs
        """
        if not texts:
            return []

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)

        # Prepare metadata (Chroma requires non-empty metadata)
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in texts]
        else:
            # Ensure no empty metadata dicts
            metadatas = [m if m else {"source": "unknown"} for m in metadatas]

        # Add to collection
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info(f"Added {len(texts)} documents to vector store")
        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents with caching

        Args:
            query: Query text
            k: Number of results to return
            where: Optional metadata filter

        Returns:
            List of results with text, metadata, and distance
        """
        # Step 1: Check query cache
        cache_key = self._get_cache_key(query, k, where)
        cached_results = self._get_cached_results(cache_key)
        if cached_results is not None:
            return cached_results

        logger.debug(f"Cache MISS for query: {query[:50]}...")

        # Step 2: Try to get cached embedding
        query_embedding = self._get_cached_embedding(query)
        if query_embedding is None:
            # Generate and cache embedding
            query_embedding = self.embedding_model.encode([query])[0]
            self._cache_embedding(query, query_embedding)
            logger.debug("Generated and cached new embedding")
        else:
            logger.debug("Using cached embedding")

        # Step 3: Search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k,
            where=where,
        )

        # Step 4: Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append(
                {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "score": 1 - results["distances"][0][i],  # Convert distance to similarity score
                }
            )

        # Step 5: Cache results
        self._cache_results(cache_key, formatted_results)

        return formatted_results

    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by IDs

        Args:
            ids: List of document IDs to delete
        """
        self.collection.delete(ids=ids)
        # Clear cache since document set changed
        self.clear_cache()
        logger.info(f"Deleted {len(ids)} documents and cleared cache")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_documents": count,
            "persist_directory": self.persist_directory,
        }

    def clear_collection(self) -> None:
        """Clear all documents from the collection"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Document embeddings for RAG"},
        )
        # Clear cache since collection cleared
        self.clear_cache()
        logger.info(f"Cleared collection and cache: {self.collection_name}")

    def update_embedding_model(self, model_name: str) -> None:
        """
        Update the embedding model

        Args:
            model_name: New embedding model name
        """
        logger.info(f"Updating embedding model to: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_model_name = model_name
