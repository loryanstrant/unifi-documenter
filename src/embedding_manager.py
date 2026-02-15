"""
Embedding manager for RAG-based UniFi configuration analysis.

Handles embedding generation, vector storage in Qdrant, and context retrieval
to provide relevant context to the LLM for higher-quality documentation.
"""
import json
import logging
import hashlib
import time
import requests
from typing import Dict, List, Optional

from .config import Config
from .ai_integration import RetryableAIError, _is_retryable_error

logger = logging.getLogger('unifi_documenter')


class EmbeddingProvider:
    """Generates embeddings using the configured provider."""

    def __init__(self, config: Config):
        self.config = config
        self.provider = config.EMBEDDING_PROVIDER.lower()
        self.model = config.EMBEDDING_MODEL
        self.context_window = config.EMBEDDING_CONTEXT_WINDOW
        self.chars_per_token = config.EMBEDDING_CHARS_PER_TOKEN

    def _truncate_text(self, text: str) -> str:
        """Truncate text to fit within the embedding model's context window.

        Uses a configurable character-to-token estimate for structured data
        (JSON, config files) which tokenizes more densely than natural language
        due to special characters, brackets, quotes, etc. Limits to 85% of the
        context window to provide a 15% safety buffer.
        
        Note: Different tokenizers may count tokens differently. The default
        estimate (1.0 chars/token) ensures compatibility with most embedding
        models. For qwen3 and similar models, JSON data can tokenize at
        ~1 char per token or worse. This can be adjusted via the
        EMBEDDING_CHARS_PER_TOKEN configuration parameter if needed.
        """
        # Use configured chars-per-token ratio (default 1.0 for worst-case JSON)
        # Limit to 85% of context window to provide 15% safety buffer
        max_tokens = int(self.context_window * 0.85)
        max_chars = int(max_tokens * float(self.chars_per_token))
        
        if len(text) > max_chars:
            logger.info(
                f"Truncating embedding text from {len(text)} to {max_chars} chars "
                f"(target: {max_tokens} tokens, context_window={self.context_window}, "
                f"chars_per_token={self.chars_per_token})"
            )
            text = text[:max_chars]
        return text

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate an embedding vector for the given text."""
        text = self._truncate_text(text)
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
        """Generate embedding using Ollama (uses 'prompt' param, not 'input')."""
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
            if response.status_code == 500 and _is_retryable_error(response.text):
                raise RetryableAIError(response.text)
            return None
        except RetryableAIError:
            raise
        except Exception as e:
            error_str = str(e)
            logger.error(f"Ollama embedding error: {type(e).__name__} - {e}")
            if _is_retryable_error(error_str):
                raise RetryableAIError(error_str) from e
            return None

    def _openai_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI-compatible API."""
        return self._openai_compatible_embedding(text, "OpenAI")

    def _custom_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using a custom OpenAI-compatible endpoint."""
        return self._openai_compatible_embedding(text, "Custom")

    def _openai_compatible_embedding(self, text: str, label: str) -> Optional[List[float]]:
        """Shared implementation for OpenAI-compatible embedding endpoints."""
        try:
            headers = {"Content-Type": "application/json"}
            if self.config.AI_API_KEY:
                headers["Authorization"] = f"Bearer {self.config.AI_API_KEY}"
            
            endpoint = f"{self.config.AI_API_URL}/embeddings"
            payload = {"model": self.model, "input": text}
            
            response = requests.post(
                endpoint,
                headers=headers,
                # OpenAI-compatible APIs use "input" (vs Ollama's "prompt")
                json=payload,
                timeout=120,
            )
            if response.status_code == 200:
                return response.json()["data"][0]["embedding"]
            
            # Enhanced error logging with troubleshooting guidance
            logger.error(
                f"{label} embedding error - Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            logger.error(f"Endpoint: {endpoint}")
            logger.error(f"Model: {self.model}")
            
            # Provide specific troubleshooting guidance based on error patterns
            if response.status_code == 500:
                # Check for common patterns indicating missing/unsupported model
                error_text = response.text.lower()
                if "exceeds" in error_text and "context" in error_text:
                    logger.error("⚠️  TROUBLESHOOTING: Text exceeds the embedding model's context window")
                    logger.error(f"   - The text was too long for model '{self.model}'")
                    logger.error(f"   - Current EMBEDDING_CONTEXT_WINDOW={self.context_window}")
                    logger.error("   - Try reducing document sizes or lowering EMBEDDING_CONTEXT_WINDOW")
                    logger.error("   - If your model supports a larger context, increase context_size in the model config")
                elif "not implemented" in error_text or "unimplemented" in error_text:
                    logger.error("⚠️  TROUBLESHOOTING: 'Method not implemented' or 'Unimplemented' error")
                    logger.error("   This usually means:")
                    logger.error(f"   1. The embedding model '{self.model}' is not loaded in your AI provider")
                    logger.error("   2. The embedding endpoint is not available")
                    logger.error("   3. The model name might be incorrect")
                    logger.error("")
                    logger.error("   For LocalAI:")
                    logger.error(f"   - Ensure '{self.model}' is downloaded and configured")
                    logger.error("   - Check LocalAI logs for model loading errors")
                    logger.error("   - Verify the model supports embeddings (not all models do)")
                    logger.error("   - Try a different model like 'all-MiniLM-L6-v2' or 'bert-cpp'")
                    logger.error("")
                    logger.error("   For Ollama (alternative):")
                    logger.error("   - Set EMBEDDING_PROVIDER=ollama")
                    logger.error("   - Set EMBEDDING_MODEL=nomic-embed-text (or all-minilm)")
                    logger.error("   - Ensure Ollama is running: ollama pull nomic-embed-text")
                else:
                    # Generic 500 error guidance
                    logger.error("⚠️  TROUBLESHOOTING: Internal server error (500)")
                    logger.error(f"   - Check the AI provider logs for detailed error information")
                    logger.error(f"   - Verify the model '{self.model}' is correctly configured")
                    logger.error(f"   - Ensure the embedding service is running properly")
            elif response.status_code == 404:
                logger.error("⚠️  TROUBLESHOOTING: Endpoint not found")
                logger.error(f"   - Verify your AI_API_URL is correct: {self.config.AI_API_URL}")
                logger.error("   - For LocalAI, ensure it's running and accessible")
                logger.error("   - Check if the service requires a different base URL or path")
            
            # Raise retryable error for model loading failures
            if response.status_code == 500 and _is_retryable_error(response.text):
                raise RetryableAIError(response.text)
            
            return None
        except RetryableAIError:
            raise
        except Exception as e:
            error_str = str(e)
            logger.error(f"{label} embedding error: {type(e).__name__} - {e}")
            logger.error(f"Endpoint: {self.config.AI_API_URL}/embeddings")
            logger.error(f"Model: {self.model}")
            if _is_retryable_error(error_str):
                raise RetryableAIError(error_str) from e
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

        max_retries = 5
        retry_delay = 60

        points = []
        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue

            embedding = None
            for attempt in range(max_retries + 1):
                try:
                    embedding = self.embedding_provider.generate_embedding(text)
                    break  # Success or non-retryable failure
                except RetryableAIError as e:
                    if attempt < max_retries:
                        logger.warning(
                            f"Embedding model loading error (attempt {attempt + 1}/{max_retries}): {e}"
                        )
                        logger.warning(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(
                            f"Embedding failed after {max_retries} retries, skipping document"
                        )
                        embedding = None

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
