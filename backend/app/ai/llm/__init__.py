import logging
from typing import Optional
from backend.app.ai.llm.base import LLMProvider
from backend.app.ai.llm.ollama import OllamaProvider
from backend.app.ai.llm.groq import GroqProvider
from backend.app.ai.llm.gemini import GeminiProvider
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class ResilientHybridLLMProvider(LLMProvider):
    """
    Seamless Dual Online/Offline Provider for ChronaNexus.
    Primary: Groq LPU (Ultra-fast cloud inference with openai/gpt-oss-120b).
    Fallback: Ollama (100% on-device private offline inference with llama3.2:3b).
    """

    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary
        self.fallback = fallback

    @property
    def provider_name(self) -> str:
        return f"{self.primary.provider_name} [Auto-Fallback: {self.fallback.provider_name}]"

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.1
    ) -> str:
        try:
            return self.primary.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                max_tokens=max_tokens,
                temperature=temperature
            )
        except Exception as e:
            logger.warning(
                f"Primary provider ({self.primary.provider_name}) unavailable ({e}). "
                f"Engaging local offline fallback ({self.fallback.provider_name})..."
            )
            return self.fallback.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                max_tokens=max_tokens,
                temperature=temperature
            )

    def health_check(self) -> bool:
        return self.primary.health_check() or self.fallback.health_check()


def get_llm_provider(
    provider_name: Optional[str] = None,
    mode: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Factory function to instantiate the configured LLM provider.
    Modes:
      - 'offline': Always uses local Ollama (100% private, no internet).
      - 'online': Uses Groq cloud LPU with automatic local Ollama fallback.
    """
    active_mode = (mode or getattr(settings, "AI_INFERENCE_MODE", "online")).lower()
    prov = (provider_name or getattr(settings, "LLM_PROVIDER", "groq")).lower()

    # Local Ollama Provider instance
    ollama_base_url = kwargs.get("base_url", getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model = kwargs.get("model", getattr(settings, "OLLAMA_MODEL", "llama3.2:3b"))
    ollama_timeout = kwargs.get("timeout", 45.0)
    ollama_provider = OllamaProvider(base_url=ollama_base_url, model=ollama_model, timeout=ollama_timeout)

    # 1. Explicit Offline Mode: Always return Ollama directly
    if active_mode == "offline" or prov == "ollama":
        return ollama_provider

    # 2. Gemini Provider (if explicitly requested)
    if prov == "gemini":
        api_key = kwargs.get("api_key", getattr(settings, "GEMINI_API_KEY", ""))
        model = kwargs.get("model", getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"))
        return GeminiProvider(api_key=api_key, model=model)

    # 3. Mock Provider (for automated unit tests)
    if prov in ["mock", "test", "deterministic"]:
        return MockDeterministicLLMProvider()

    # 4. Default Online Mode: Groq LPU with Ollama Auto-Fallback
    groq_api_key = kwargs.get("api_key", getattr(settings, "GROQ_API_KEY", ""))
    groq_model = kwargs.get("model", getattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b"))
    groq_timeout = kwargs.get("timeout", 30.0)

    if groq_api_key:
        groq_provider = GroqProvider(api_key=groq_api_key, model=groq_model, timeout=groq_timeout)
        return ResilientHybridLLMProvider(primary=groq_provider, fallback=ollama_provider)

    # Fallback to Ollama if no Groq key configured
    logger.warning("No GROQ_API_KEY found; defaulting to local Ollama provider.")
    return ollama_provider


__all__ = [
    "LLMProvider",
    "OllamaProvider",
    "GroqProvider",
    "GeminiProvider",
    "MockDeterministicLLMProvider",
    "ResilientHybridLLMProvider",
    "get_llm_provider"
]
