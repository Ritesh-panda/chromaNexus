import logging
from typing import Optional
import httpx
from backend.app.ai.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """
    Groq LPU Ultra-Low-Latency Inference Provider for ChronaNexus.
    Uses OpenAI-compatible endpoint at https://api.groq.com/openai/v1/chat/completions.
    Recommended primary model: 'openai/gpt-oss-120b' (flagship clinical reasoning).
    Fallback model: 'openai/gpt-oss-20b' (lightweight, blazing fast).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-120b",
        timeout: float = 30.0
    ):
        self.api_key = api_key.strip() if api_key else ""
        self.model = model
        self.timeout = timeout
        self.base_url = "https://api.groq.com/openai/v1"

    @property
    def provider_name(self) -> str:
        return f"groq ({self.model})"

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = 2048,
        temperature: float = 0.1
    ) -> str:
        if not self.api_key:
            raise ValueError("Groq API key is not configured. Please set GROQ_API_KEY in .env.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ChronaNexus-Medical-AI/1.0"
        }

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "").strip()
                    return ""
                
                # If primary 120B model encounters temporary load, attempt 20B fallback
                if response.status_code in (429, 503) and self.model != "openai/gpt-oss-20b":
                    logger.warning(f"Groq {self.model} returned {response.status_code}. Attempting fallback to openai/gpt-oss-20b...")
                    payload["model"] = "openai/gpt-oss-20b"
                    fb_resp = client.post(url, headers=headers, json=payload)
                    if fb_resp.status_code == 200:
                        fb_data = fb_resp.json()
                        fb_choices = fb_data.get("choices", [])
                        if fb_choices and "message" in fb_choices[0]:
                            return fb_choices[0]["message"].get("content", "").strip()

                err_text = response.text
                logger.error(f"Groq API returned HTTP {response.status_code}: {err_text}")
                raise RuntimeError(f"Groq API error ({response.status_code}): {err_text}")

        except httpx.ConnectError as e:
            logger.warning(f"Could not connect to Groq cloud API: {e}")
            raise
        except httpx.TimeoutException as e:
            logger.warning(f"Groq request timed out after {self.timeout}s: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error communicating with Groq: {e}")
            raise

    def health_check(self) -> bool:
        """Validates if Groq API key is authorized and active."""
        if not self.api_key:
            return False
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            with httpx.Client(timeout=3.0) as client:
                res = client.get(url, headers=headers)
                return res.status_code == 200
        except Exception:
            return False
