import pytest
from backend.app.ai.llm.base import LLMProvider
from backend.app.ai.llm.ollama import OllamaProvider
from backend.app.ai.llm.gemini import GeminiProvider
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider
from backend.app.ai.llm import get_llm_provider


def test_ollama_provider_graceful_offline_handling():
    # Points to non-existent local port to simulate offline Ollama daemon
    provider = OllamaProvider(base_url="http://127.0.0.1:9999", model="llama3:8b", timeout=0.5)
    assert isinstance(provider, LLMProvider)
    assert "ollama" in provider.provider_name
    assert provider.health_check() is False

    response = provider.generate("What is my cholesterol level?")
    # Should return informative error message without raising an uncaught exception
    assert any(x in response for x in ["Ollama Service Unavailable", "Ollama Error", "Ollama Timeout"])



def test_gemini_provider_unconfigured_key_handling():
    provider = GeminiProvider(api_key="", model="gemini-1.5-flash")
    assert isinstance(provider, LLMProvider)
    assert "gemini" in provider.provider_name
    assert provider.health_check() is False

    response = provider.generate("What is my cholesterol level?")
    assert "Gemini API key is not configured" in response or "Gemini Configuration Error" in response


def test_gemini_provider_with_key_health():
    provider = GeminiProvider(api_key="AIzaSyDummyValidFormatKey12345", model="gemini-1.5-flash")
    assert provider.health_check() is True


def test_mock_deterministic_llm_provider():
    provider = MockDeterministicLLMProvider()
    assert provider.health_check() is True
    
    resp_chol = provider.generate("When was my highest cholesterol recorded?")
    assert "242 mg/dL" in resp_chol
    assert "June 12, 2021" in resp_chol

    resp_hba1c = provider.generate("Tell me about my diabetes and HbA1c trajectory")
    assert "7.2%" in resp_hba1c
    assert "6.7%" in resp_hba1c


def test_llm_provider_switching():
    prov_ollama = get_llm_provider("ollama", base_url="http://localhost:11434")
    assert isinstance(prov_ollama, OllamaProvider)

    prov_gemini = get_llm_provider("gemini", api_key="dummy_key")
    assert isinstance(prov_gemini, GeminiProvider)

    prov_mock = get_llm_provider("mock")
    assert isinstance(prov_mock, MockDeterministicLLMProvider)
