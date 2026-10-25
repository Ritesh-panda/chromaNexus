"""
ChronaNexus Ollama Provider Verification Suite (Phase 2)
========================================================
Tests the actual application OllamaProvider against the local Ollama instance:
1. Exact response
2. Numerical value and unit extraction
3. Missing evidence and abstention
4. Conflicting records
5. Connection error and timeout handling
6. Cold-start versus warm-request latency breakdown
"""

import os
import sys
import time
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.ai.llm.ollama import OllamaProvider
from backend.app.ai.rag.prompts import MEDICAL_SAFETY_SYSTEM_PROMPT


@pytest.fixture(scope="module")
def provider():
    return OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b", timeout=120.0)


def test_01_exact_response(provider):
    """1. Exact response verification."""
    prompt = "Respond with the single word: WARM_TEST_OK"
    t0 = time.perf_counter()
    response = provider.generate(prompt=prompt, temperature=0.0)
    elapsed = time.perf_counter() - t0

    print(f"\n[Test 1] Exact Response: {response} (Elapsed: {elapsed:.3f}s)")
    assert "WARM_TEST_OK" in response
    assert elapsed < 15.0


def test_02_numerical_value_and_unit_extraction(provider):
    """2. Numerical value, unit, date, and source report extraction."""
    context = (
        "[REPORT EXCERPT #1 | Comprehensive Metabolic Panel (2026-10-12) | Page 1 | Metro Health]\n"
        "Component Results:\n"
        "- Potassium: 5.8 mEq/L [HIGH] (Reference: 3.5-5.0 mEq/L)\n"
        "Impression: Moderate hyperkalemia.\n"
    )
    prompt = (
        f"VERIFIED PATIENT MEDICAL CONTEXT:\n{context}\n\n"
        "PATIENT QUESTION:\nWhat was the patient's potassium level on October 12, 2026, and reference range?\n\n"
        "INSTRUCTIONS:\nAnswer in 1-2 sentences using ONLY the verified records above. "
        "State the exact value, units, reference range, and cite the report title and date."
    )
    t0 = time.perf_counter()
    response = provider.generate(prompt=prompt, system_instruction=MEDICAL_SAFETY_SYSTEM_PROMPT, max_tokens=150, temperature=0.1)
    elapsed = time.perf_counter() - t0

    print(f"\n[Test 2] Numerical Extraction: {response} (Elapsed: {elapsed:.3f}s)")
    assert "5.8" in response
    assert "mEq/L" in response or "meq/l" in response.lower()
    assert "3.5" in response and "5.0" in response
    assert "2026-10-12" in response or "October 12" in response
    assert "Comprehensive Metabolic Panel" in response


def test_03_missing_evidence_and_abstention(provider):
    """3. Missing evidence and abstention verification."""
    context = (
        "[REPORT EXCERPT #1 | Dermatology Encounter Note (2026-05-10) | Page 1 | West Dermatology]\n"
        "Full body skin examination: No suspicious pigmented lesions or dysplastic nevi observed.\n"
    )
    prompt = (
        f"VERIFIED PATIENT MEDICAL CONTEXT:\n{context}\n\n"
        "PATIENT QUESTION:\nWhat was my most recent echocardiogram left ventricular ejection fraction (LVEF)?\n\n"
        "INSTRUCTIONS:\nAnswer using ONLY the verified records above. "
        "If the records do not contain the requested information, state clearly that the records do not contain this information. "
        "Do not invent or estimate values."
    )
    t0 = time.perf_counter()
    response = provider.generate(prompt=prompt, system_instruction=MEDICAL_SAFETY_SYSTEM_PROMPT, max_tokens=100, temperature=0.1)
    elapsed = time.perf_counter() - t0

    print(f"\n[Test 3] Abstention: {response} (Elapsed: {elapsed:.3f}s)")
    lower = response.lower()
    abstention_indicators = [
        "not contain", "does not contain", "no information", "not found",
        "no record", "no mention", "not documented", "cannot find", "unavailable"
    ]
    assert any(ind in lower for ind in abstention_indicators), f"Model failed to abstain. Response: {response}"
    assert "55%" not in response and "60%" not in response


def test_04_conflicting_records(provider):
    """4. Conflicting records extraction across facilities."""
    context = (
        "[REPORT EXCERPT #1 | Outpatient Lab Report (2026-09-01) | Page 1 | Metro Health]\n"
        "Fasting Plasma Glucose: 105 mg/dL (Reference: 70-99 mg/dL). High.\n\n"
        "[REPORT EXCERPT #2 | Diagnostic Endocrinology Panel (2026-09-05) | Page 1 | Valley Lab]\n"
        "Fasting Plasma Glucose: 142 mg/dL (Reference: 70-99 mg/dL). Markedly elevated.\n"
    )
    prompt = (
        f"VERIFIED PATIENT MEDICAL CONTEXT:\n{context}\n\n"
        "PATIENT QUESTION:\nWhat are my fasting glucose readings across facilities? Note any discrepancy.\n\n"
        "INSTRUCTIONS:\nState both readings, their respective facility names, and dates using ONLY the records above."
    )
    t0 = time.perf_counter()
    response = provider.generate(prompt=prompt, system_instruction=MEDICAL_SAFETY_SYSTEM_PROMPT, max_tokens=150, temperature=0.1)
    elapsed = time.perf_counter() - t0

    print(f"\n[Test 4] Conflicting Records: {response} (Elapsed: {elapsed:.3f}s)")
    assert "105" in response
    assert "142" in response
    assert "Metro" in response
    assert "Valley" in response


def test_05_connection_error_and_timeout_handling():
    """5. Connection error and timeout handling."""
    # Connection error: invalid port
    bad_provider = OllamaProvider(base_url="http://non-existent-domain-12345.local", model="llama3.2:3b", timeout=2.0)
    err_res = bad_provider.generate(prompt="Hello")
    assert "[Ollama Service Unavailable" in err_res

    # Timeout error: 0.001s timeout
    timeout_provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b", timeout=0.001)
    timeout_res = timeout_provider.generate(prompt="Hello")
    assert "[Ollama Timeout" in timeout_res


def test_06_cold_vs_warm_latency_investigation(provider):
    """6. Cold vs warm latency profiling."""
    import httpx

    # Short warm prompt
    short_payload = {
        "model": "llama3.2:3b",
        "prompt": "Say: OK",
        "stream": False,
        "options": {"temperature": 0.0}
    }
    r_short = httpx.post(f"{provider.base_url}/api/generate", json=short_payload, timeout=60.0).json()
    t_short = r_short.get("total_duration", 0) / 1e9

    # Medium clinical prompt
    med_payload = {
        "model": "llama3.2:3b",
        "prompt": "Summarize in 2 words: Patient blood pressure 120/80 mmHg.",
        "stream": False,
        "options": {"temperature": 0.0}
    }
    r_med = httpx.post(f"{provider.base_url}/api/generate", json=med_payload, timeout=60.0).json()
    t_med = r_med.get("total_duration", 0) / 1e9

    print(f"\n[Test 6] Latency Profile:\n  Short total: {t_short:.3f}s (prompt_eval: {r_short.get('prompt_eval_duration', 0)/1e9:.3f}s, eval: {r_short.get('eval_duration', 0)/1e9:.3f}s)")
    print(f"  Med total: {t_med:.3f}s (prompt_eval: {r_med.get('prompt_eval_duration', 0)/1e9:.3f}s, eval: {r_med.get('eval_duration', 0)/1e9:.3f}s)")
    assert t_short < 5.0


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
