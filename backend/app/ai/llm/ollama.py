import logging
from typing import Optional
import httpx
from backend.app.ai.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama HTTP Client Provider for local, private LLM execution.
    Communicates with Ollama API (/api/generate, /api/tags).
    Does NOT require Ollama to be running during startup.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3:8b",
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return f"ollama ({self.model})"

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2
    ) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        if system_instruction:
            payload["system"] = system_instruction
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "").strip()
                elif response.status_code == 404:
                    error_msg = f"Ollama model '{self.model}' not found on server at {self.base_url}. Please run: ollama pull {self.model}"
                    logger.warning(error_msg)
                    return f"[Ollama Error: {error_msg}]"
                else:
                    error_msg = f"Ollama returned HTTP {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    return f"[Ollama Error: {error_msg}]"
        except httpx.ConnectError:
            msg = f"Could not connect to Ollama at {self.base_url}. Ensure the Ollama daemon is running."
            logger.warning(msg)
            return f"[Ollama Service Unavailable: {msg}]"
        except httpx.TimeoutException:
            msg = f"Ollama request timed out after {self.timeout}s."
            logger.warning(msg)
            return f"[Ollama Timeout: {msg}]"
        except Exception as e:
            msg = f"Unexpected error communicating with Ollama: {str(e)}"
            logger.exception(msg)
            return f"[Ollama Error: {msg}]"

    def health_check(self) -> bool:
        """Checks if Ollama instance is responding."""
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
