"""
Embedding manager for RAG-based UniFi configuration analysis.

Handles embedding generation, vector storage in Qdrant, and context retrieval
to provide relevant context to the LLM for higher-quality documentation.
"""
import json
import logging
import hashlib
import requests
from typing import Dict, List, Optional

from .config import Config

logger = logging.getLogger('unifi_documenter')


class EmbeddingProvider:
    """Generates embeddings using the configured provider."""

    def __init__(self, config: Config):
        self.config = config
        self.provider = config.EMBEDDING_PROVIDER.lower()
        self.model = config.EMBEDDING_MODEL

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate an embedding vector for the given text."""
        if self.provider == 'ollama':
            return self._ollama_embedding(text)
        elif self.provider == 'openai':
            return self._openai_embedding(text)
        elif self.provider == 'custom':
            return self._custom_embedding(text)
        else:
            logger.error(f"Unknown embedding provider: {self.provider}")
            return None

    def _ollama_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Ollama."""
        try:
            response = requests.post(
                f"{self.config.OLLAMA_URL}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=120,
            )
            if response.status_code == 200:
                return response.json().get("embedding")
            logger.error(
                f"Ollama embedding error - Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Ollama embedding error: {type(e).__name__} - {e}")
            return None

    def _openai_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI-compatible API."""
        try:
            headers = {"Content-Type": "application/json"}
            if self.config.AI_API_KEY:
                headers["Authorization"] = f"Bearer {self.config.AI_API_KEY}"
            response = requests.post(
                f"{self.config.AI_API_URL}/embeddings",
                headers=headers,
                json={"model": self.model, "input": text},
                timeout=120,
            )
            if response.status_code == 200:
                return response.json()["data"][0]["embedding"]
            logger.error(
                f"OpenAI embedding error - Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"OpenAI embedding error: {type(e).__name__} - {e}")
            return None

    def _custom_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using a custom OpenAI-compatible endpoint."""
        try:
            headers = {"Content-Type": "application/json"}
            if self.config.AI_API_KEY:
                headers["Authorization"] = f"Bearer {self.config.AI_API_KEY}"
            response = requests.post(
                f"{self.config.AI_API_URL}/embeddings",
                headers=headers,
                json={"model": self.model, "input": text},
                timeout=120,
            )
            if response.status_code == 200:
                return response.json()["data"][0]["embedding"]
            logger.error(
                f"Custom embedding error - Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Custom embedding error: {type(e).__name__} - {e}")
            return None

    def is_available(self) -> bool:
        """Check whether the embedding provider is reachable."""
        if self.provider == 'ollama':
            try:
                resp = requests.get(
                    f"{self.config.OLLAMA_URL}/api/tags", timeout=10
                )
                return resp.status_code == 200
            except Exception:
                return False
        # For OpenAI / custom providers, assume available if URL is set
        return bool(self.config.AI_API_URL)


class EmbeddingManager:
    """Manages the embedding pipeline: embed → store → retrieve."""

    def __init__(self, config: Config):
        self.config = config
        self.embedding_provider = EmbeddingProvider(config)
        self.qdrant_url = config.QDRANT_URL
        self.collection = config.EMBEDDING_COLLECTION
        self.top_k = config.EMBEDDING_TOP_K
        self._collection_ready = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Check if both the embedding provider and Qdrant are reachable."""
        if not self.embedding_provider.is_available():
            logger.debug("Embedding provider is not available")
            return False
        if not self._qdrant_healthy():
            logger.debug("Qdrant is not reachable")
            return False
        return True

    def embed_documents(self, documents: List[Dict]) -> int:
        """Embed a list of documents and upsert them into Qdrant.

        Each document dict must have at least a ``text`` key.  An optional
        ``metadata`` key will be stored as the Qdrant payload alongside
        ``text``.

        Returns the number of documents successfully embedded.
        """
        if not self._ensure_collection():
            return 0

        points = []
        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue
            embedding = self.embedding_provider.generate_embedding(text)
            if embedding is None:
                logger.warning("Failed to generate embedding, skipping document")
                continue
            doc_id = self._text_to_id(text)
            payload = doc.get("metadata", {})
            payload["text"] = text
            points.append(
                {"id": doc_id, "vector": embedding, "payload": payload}
            )

        if not points:
            return 0

        # Upsert in batches of 100
        batch_size = 100
        total_upserted = 0
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            try:
                resp = requests.put(
                    f"{self.qdrant_url}/collections/{self.collection}/points",
                    json={"points": batch},
                    timeout=60,
                )
                if resp.status_code in (200, 201):
                    total_upserted += len(batch)
                else:
                    logger.error(
                        f"Qdrant upsert error: {resp.status_code} - {resp.text}"
                    )
            except Exception as e:
                logger.error(f"Qdrant upsert error: {type(e).__name__} - {e}")

        logger.info(
            f"Embedded {total_upserted}/{len(documents)} documents into "
            f"collection '{self.collection}'"
        )
        return total_upserted

    def retrieve_context(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """Retrieve the most relevant documents for a query.

        Returns a list of dicts with ``text`` and ``score`` keys.
        """
        k = top_k or self.top_k
        embedding = self.embedding_provider.generate_embedding(query)
        if embedding is None:
            return []

        try:
            resp = requests.post(
                f"{self.qdrant_url}/collections/{self.collection}/points/search",
                json={
                    "vector": embedding,
                    "limit": k,
                    "with_payload": True,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                logger.error(
                    f"Qdrant search error: {resp.status_code} - {resp.text}"
                )
                return []

            results = []
            for hit in resp.json().get("result", []):
                payload = hit.get("payload", {})
                results.append(
                    {
                        "text": payload.get("text", ""),
                        "score": hit.get("score", 0.0),
                        "metadata": {
                            k: v for k, v in payload.items() if k != "text"
                        },
                    }
                )
            return results

        except Exception as e:
            logger.error(f"Qdrant search error: {type(e).__name__} - {e}")
            return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _qdrant_healthy(self) -> bool:
        try:
            resp = requests.get(f"{self.qdrant_url}/healthz", timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def _ensure_collection(self) -> bool:
        """Create the Qdrant collection if it does not already exist."""
        if self._collection_ready:
            return True

        # Determine vector size by generating a probe embedding
        probe = self.embedding_provider.generate_embedding("probe")
        if probe is None:
            logger.error("Cannot determine vector size - embedding failed")
            return False
        vector_size = len(probe)

        try:
            # Check if collection exists
            resp = requests.get(
                f"{self.qdrant_url}/collections/{self.collection}",
                timeout=10,
            )
            if resp.status_code == 200:
                self._collection_ready = True
                return True

            # Create collection
            resp = requests.put(
                f"{self.qdrant_url}/collections/{self.collection}",
                json={
                    "vectors": {
                        "size": vector_size,
                        "distance": "Cosine",
                    }
                },
                timeout=30,
            )
            if resp.status_code in (200, 201):
                logger.info(
                    f"Created Qdrant collection '{self.collection}' "
                    f"(vector_size={vector_size})"
                )
                self._collection_ready = True
                return True

            logger.error(
                f"Failed to create collection: {resp.status_code} - {resp.text}"
            )
            return False

        except Exception as e:
            logger.error(
                f"Qdrant collection setup error: {type(e).__name__} - {e}"
            )
            return False

    @staticmethod
    def _text_to_id(text: str) -> str:
        """Deterministic point ID derived from text content."""
        return hashlib.md5(text.encode("utf-8")).hexdigest()
