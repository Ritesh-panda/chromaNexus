from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LLMProvider(ABC):
    """
    Provider-independent LLM interface for ChronaNexus.
    RAG pipelines and AI services depend strictly on this abstraction.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2
    ) -> str:
        """
        Generates completion given a prompt and optional system instructions.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Validates if the provider endpoint/credentials are operational.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the human-readable identifier of the provider."""
        pass
