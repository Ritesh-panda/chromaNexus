from typing import Optional
from backend.app.ai.llm.base import LLMProvider
from backend.app.ai.llm.ollama import OllamaProvider
from backend.app.ai.llm.gemini import GeminiProvider
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider
from backend.app.core.config import settings


def get_llm_provider(
    provider_name: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Factory function to instantiate the configured LLM provider.
    Defaults to settings.LLM_PROVIDER ('ollama', 'gemini', or 'mock').
    """
    prov = (provider_name or getattr(settings, "LLM_PROVIDER", "ollama")).lower()
    
    if prov == "ollama":
        base_url = kwargs.get("base_url", getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"))
        model = kwargs.get("model", getattr(settings, "OLLAMA_MODEL", "llama3:8b"))
        return OllamaProvider(base_url=base_url, model=model)
    elif prov == "gemini":
        api_key = kwargs.get("api_key", getattr(settings, "GEMINI_API_KEY", ""))
        model = kwargs.get("model", getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"))
        return GeminiProvider(api_key=api_key, model=model)
    elif prov in ["mock", "test", "deterministic"]:
        return MockDeterministicLLMProvider()
    else:
        # Default fallback to mock/deterministic if unknown
        return MockDeterministicLLMProvider()


__all__ = [
    "LLMProvider",
    "OllamaProvider",
    "GeminiProvider",
    "MockDeterministicLLMProvider",
    "get_llm_provider"
]
