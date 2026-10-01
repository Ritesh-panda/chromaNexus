import math
import hashlib
from abc import ABC, abstractmethod
from typing import List, Optional


class EmbeddingProvider(ABC):
    """
    Abstract interface for embedding generation.
    Any concrete embedding provider (local, HuggingFace, OpenAI, Gemini) must implement this interface.
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
    Ensures tests and local development can run without downloading gigabytes of models or requiring a GPU.
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
            # Generate deterministic hash seeds
            h = hashlib.sha256(word.encode("utf-8")).digest()
            for j in range(0, min(len(h) - 4, self._dim), 4):
                idx = (int.from_bytes(h[j:j+4], "big") + i) % self._dim
                # Weight by word length and inverse position
                weight = (len(word) / 10.0) * (1.0 / (1.0 + 0.05 * i))
                vector[idx] += weight

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


def get_embedding_provider(provider_type: Optional[str] = None) -> EmbeddingProvider:
    """
    Factory to retrieve configured embedding provider.
    Defaults to LocalLightweightEmbeddingProvider.
    """
    prov = (provider_type or "local").lower()
    if prov in ["local", "lightweight", "mock", "default"]:
        return LocalLightweightEmbeddingProvider(dim=384)
    
    # Fallback to local lightweight
    return LocalLightweightEmbeddingProvider(dim=384)
