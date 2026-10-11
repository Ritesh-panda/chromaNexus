import math
import hashlib
import logging
import httpx
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """
    Abstract interface for embedding generation.
    Implemented by OllamaEmbeddingProvider (production semantic model)
    and LocalLightweightEmbeddingProvider (lightweight fallback/testing).
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single string."""
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of strings."""
        pass

    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality."""
        pass


class LocalLightweightEmbeddingProvider(EmbeddingProvider):
    """
    Lightweight, fast, deterministic local embedding provider.
    Runs completely on CPU with zero heavy ML dependencies, producing 384-dimensional normalized vectors.
    Ensures unit tests and offline development run fast without external service dependencies.
    """

    def __init__(self, dim: int = 384):
        self._dim = dim

    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self._dim

        # Deterministic token-frequency + hash-projection approach
        vector = [0.0] * self._dim
        words = text.lower().split()
        
        if not words:
            return [0.0] * self._dim

        for i, word in enumerate(words):
            h = hashlib.sha256(word.encode("utf-8")).digest()
            for j in range(0, min(len(h) - 4, self._dim), 4):
                idx = (int.from_bytes(h[j:j+4], "big") + i) % self._dim
                weight = (len(word) / 10.0) * (1.0 / (1.0 + 0.05 * i))
                vector[idx] += weight

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Production-grade Ollama Embedding Provider.
    Generates real semantic embeddings using local Ollama models (e.g., 'all-minilm').
    Provides automatic fallback to LocalLightweightEmbeddingProvider if Ollama is unreachable.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        dim: int = 384,
        timeout: float = 30.0
    ):
        try:
            from backend.app.core.config import settings
            default_model = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "all-minilm")
            default_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
            default_dim = getattr(settings, "EMBEDDING_DIMENSION", 384)
        except Exception:
            default_model = "all-minilm"
            default_url = "http://localhost:11434"
            default_dim = 384

        self._model_name = model_name or default_model
        self._base_url = (base_url or default_url).rstrip("/")
        self._dim = dim or default_dim
        self._timeout = timeout
        self._fallback_provider = LocalLightweightEmbeddingProvider(dim=self._dim)

    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dim

        url = f"{self._base_url}/api/embed"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    url,
                    json={"model": self._model_name, "input": text}
                )
                if response.status_code == 200:
                    data = response.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings and len(embeddings[0]) == self._dim:
                        return embeddings[0]
                    embedding = data.get("embedding", [])
                    if len(embedding) == self._dim:
                        return embedding

                # Legacy Ollama endpoint fallback (/api/embeddings)
                legacy_url = f"{self._base_url}/api/embeddings"
                legacy_resp = client.post(
                    legacy_url,
                    json={"model": self._model_name, "prompt": text}
                )
                if legacy_resp.status_code == 200:
                    data = legacy_resp.json()
                    embedding = data.get("embedding", [])
                    if len(embedding) == self._dim:
                        return embedding
        except Exception as e:
            logger.warning(f"Ollama embedding request failed for model '{self._model_name}': {str(e)}. Falling back to LocalLightweightEmbeddingProvider.")

        return self._fallback_provider.embed_text(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        non_empty_indices = [i for i, t in enumerate(texts) if t and t.strip()]
        if not non_empty_indices:
            return [[0.0] * self._dim for _ in texts]

        url = f"{self._base_url}/api/embed"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                input_texts = [texts[i] for i in non_empty_indices]
                response = client.post(
                    url,
                    json={"model": self._model_name, "input": input_texts}
                )
                if response.status_code == 200:
                    data = response.json()
                    embeddings = data.get("embeddings", [])
                    if len(embeddings) == len(input_texts):
                        result = [[0.0] * self._dim for _ in texts]
                        for idx, emb in zip(non_empty_indices, embeddings):
                            result[idx] = emb
                        return result
        except Exception as e:
            logger.warning(f"Ollama batch embedding request failed for model '{self._model_name}': {str(e)}. Falling back to LocalLightweightEmbeddingProvider.")

        return [self.embed_text(t) for t in texts]


def get_embedding_provider(provider_type: Optional[str] = None) -> EmbeddingProvider:
    """
    Factory to retrieve configured embedding provider.
    Defaults to OllamaEmbeddingProvider (with all-minilm) or LocalLightweightEmbeddingProvider based on configuration.
    """
    prov_str = provider_type
    if not prov_str:
        try:
            from backend.app.core.config import settings
            prov_str = getattr(settings, "EMBEDDING_PROVIDER", "ollama")
        except Exception:
            prov_str = "ollama"

    prov = (prov_str or "ollama").lower()
    if prov in ["ollama", "ollama_embedding", "real"]:
        return OllamaEmbeddingProvider()
    
    return LocalLightweightEmbeddingProvider(dim=384)
