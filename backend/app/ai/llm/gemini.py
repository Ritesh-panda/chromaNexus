import os
import logging
from typing import Optional
import httpx
from backend.app.ai.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini API Provider for cloud LLM reasoning.
    Uses Google Generative Language REST API endpoint.
    Configured strictly via environment variables / secure backend settings.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        timeout: float = 30.0
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return f"gemini ({self.model})"

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2
    ) -> str:
        if not self.api_key:
            msg = "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file."
            logger.warning(msg)
            return f"[Gemini Configuration Error: {msg}]"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_instruction:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System Instructions: {system_instruction}\n\nTask: Please follow the system instructions above."}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will strictly follow these medical safety and clinical guidelines."}]
            })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                    return "[Gemini returned empty response]"
                elif response.status_code == 400:
                    error_msg = f"Gemini API bad request (HTTP 400): {response.text}"
                    logger.error(error_msg)
                    return f"[Gemini Error: {error_msg}]"
                elif response.status_code == 403:
                    error_msg = "Gemini API key is invalid or unauthorized."
                    logger.error(error_msg)
                    return f"[Gemini Authentication Error: {error_msg}]"
                else:
                    error_msg = f"Gemini API returned HTTP {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    return f"[Gemini API Error: {error_msg}]"
        except httpx.TimeoutException:
            msg = f"Gemini API request timed out after {self.timeout}s."
            logger.warning(msg)
            return f"[Gemini Timeout: {msg}]"
        except Exception as e:
            msg = f"Unexpected error communicating with Gemini API: {str(e)}"
            logger.exception(msg)
            return f"[Gemini Error: {msg}]"

    def health_check(self) -> bool:
        """Validates that a non-empty API key is configured."""
        return bool(self.api_key and len(self.api_key.strip()) > 8)
