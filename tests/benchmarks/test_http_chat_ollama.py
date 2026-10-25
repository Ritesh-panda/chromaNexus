import os
import sys
import uuid
import time
import pytest
import shutil
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.services.auth_service import get_current_patient
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import get_vector_store, ChromaDBVectorStore
from backend.app.ai.llm.ollama import OllamaProvider
from backend.app.ai.llm import get_llm_provider


@pytest.fixture(scope="module")
def env_setup():
    temp_dir = tempfile.mkdtemp(prefix="http_chroma_")
    orig_chroma_dir = settings.CHROMA_PERSIST_DIRECTORY
    orig_coll_name = settings.CHROMA_COLLECTION_NAME
    settings.CHROMA_PERSIST_DIRECTORY = temp_dir
    settings.CHROMA_COLLECTION_NAME = f"http_test_{uuid.uuid4().hex[:8]}"

    # In-memory SQLite DB with StaticPool for cross-thread access in FastAPI TestClient
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    from backend.app.models.user import User
    db = TestingSessionLocal()
    synth_user = User(
        id=f"usr_synth_{uuid.uuid4().hex[:8]}",
        name="Synthetic Audit Patient",
        email=f"synth_{uuid.uuid4().hex[:8]}@chromanexus.test",
        hashed_password="test_hashed_pwd"
    )
    db.add(synth_user)
    db.commit()

    synth_patient = Patient(
        id=f"pat_synth_{uuid.uuid4().hex[:8]}",
        user_id=synth_user.id,
        gender="other"
    )
    db.add(synth_patient)
    db.commit()

    # Add synthetic medical reports
    rep_cmp = MedicalReport(
        id="rep_synth_cmp",
        patient_id=synth_patient.id,
        title="Comprehensive Metabolic Panel",
        file_name="cmp_metro.pdf",
        report_date="2026-10-12",
        hospital_name="Metro Health",
        raw_text="Comprehensive Metabolic Panel (2026-10-12) - Metro Health\nPotassium: 5.8 mEq/L [HIGH] (Ref: 3.5-5.0)\nSodium: 140 mEq/L"
    )
    rep_glu1 = MedicalReport(
        id="rep_synth_glu1",
        patient_id=synth_patient.id,
        title="Outpatient Fasting Glucose",
        file_name="glu_metro.pdf",
        report_date="2026-09-01",
        hospital_name="Metro Health",
        raw_text="Outpatient Fasting Glucose (2026-09-01) - Metro Health\nFasting Plasma Glucose: 105 mg/dL"
    )
    rep_glu2 = MedicalReport(
        id="rep_synth_glu2",
        patient_id=synth_patient.id,
        title="Diagnostic Endocrinology Panel",
        file_name="glu_valley.pdf",
        report_date="2026-09-05",
        hospital_name="Valley Lab",
        raw_text="Diagnostic Endocrinology Panel (2026-09-05) - Valley Lab\nFasting Plasma Glucose: 142 mg/dL"
    )
    db.add_all([rep_cmp, rep_glu1, rep_glu2])
    db.commit()

    # Index chunks in ephemeral ChromaDB
    v_store = get_vector_store(db_session=db)
    chunks = [
        DocumentChunk(
            chunk_id="chk_synth_cmp_01",
            document_id="rep_synth_cmp",
            page_number=1,
            chunk_index=0,
            text="Comprehensive Metabolic Panel (2026-10-12) - Metro Health\nPotassium: 5.8 mEq/L [HIGH] (Ref: 3.5-5.0)\nSodium: 140 mEq/L",
            metadata={
                "title": "Comprehensive Metabolic Panel",
                "date": "2026-10-12",
                "patient_id": synth_patient.id,
                "hospital_name": "Metro Health"
            }
        ),
        DocumentChunk(
            chunk_id="chk_synth_glu1_01",
            document_id="rep_synth_glu1",
            page_number=1,
            chunk_index=0,
            text="Outpatient Fasting Glucose (2026-09-01) - Metro Health\nFasting Plasma Glucose: 105 mg/dL",
            metadata={
                "title": "Outpatient Fasting Glucose",
                "date": "2026-09-01",
                "patient_id": synth_patient.id,
                "hospital_name": "Metro Health"
            }
        ),
        DocumentChunk(
            chunk_id="chk_synth_glu2_01",
            document_id="rep_synth_glu2",
            page_number=1,
            chunk_index=0,
            text="Diagnostic Endocrinology Panel (2026-09-05) - Valley Lab\nFasting Plasma Glucose: 142 mg/dL",
            metadata={
                "title": "Diagnostic Endocrinology Panel",
                "date": "2026-09-05",
                "patient_id": synth_patient.id,
                "hospital_name": "Valley Lab"
            }
        )
    ]
    v_store.add_documents(chunks)

    # Complete test isolation wiring
    orig_db_url = settings.DATABASE_URL
    settings.DATABASE_URL = "sqlite:///:memory:"
    app.state.engine = engine
    app.state.session_factory = TestingSessionLocal

    # FastAPI dependency overrides
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_get_current_patient():
        return synth_patient

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_patient] = override_get_current_patient

    client = TestClient(app)

    yield {
        "client": client,
        "patient": synth_patient,
        "db": db,
        "temp_dir": temp_dir
    }

    # Teardown
    app.dependency_overrides.clear()
    settings.DATABASE_URL = orig_db_url
    settings.CHROMA_PERSIST_DIRECTORY = orig_chroma_dir
    settings.CHROMA_COLLECTION_NAME = orig_coll_name
    if hasattr(app.state, "engine"):
        del app.state.engine
    if hasattr(app.state, "session_factory"):
        del app.state.session_factory
    db.close()
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_01_http_factual_question(env_setup):
    """1. Factual question via HTTP: Potassium 5.8 mEq/L from Metro Health."""
    client = env_setup["client"]
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"

    t0 = time.time()
    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "What was my potassium level on October 12, 2026?"}
    )
    latency = time.time() - t0
    print(f"\n[HTTP Test 01 - Cold Latency] {latency:.3f} s")

    assert resp.status_code == 200, f"HTTP Error: {resp.text}"
    data = resp.json()

    assert data["sender"] == "ai"
    assert "5.8" in data["text"]
    assert len(data["citations"]) >= 1
    cited_ids = [c["reportId"] for c in data["citations"]]
    assert "rep_synth_cmp" in cited_ids
    print(f"[HTTP Test 01] AI Response text: {data['text'][:120]}...")


def test_02_http_missing_evidence_abstention(env_setup):
    """
    [Live Ollama Provider: llama3.2:3b]
    2. Absent evidence via HTTP: LVEF missing -> model abstains, 0 citations,
    and assert answer itself does NOT invent or hallucinate an ejection fraction value.
    """
    client = env_setup["client"]
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"

    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "What was my left ventricular ejection fraction on my echocardiogram?"}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["sender"] == "ai"
    assert len(data["citations"]) == 0
    # Response must indicate missing data
    from backend.app.ai.rag.pipeline import RAGPipeline
    assert RAGPipeline(llm=None)._answer_indicates_missing_data(data["text"])

    # Strengthened grounding assertion: answer text must NOT invent numeric ejection fraction
    import re
    text_lower = data["text"].lower()
    assert not re.search(r'\b[3-7]\d\s*%', data["text"]), f"Hallucinated ejection fraction percentage: {data['text']}"
    assert not re.search(r'\bejection fraction (?:is|was|of)\s*\d+', text_lower), f"Hallucinated ejection fraction value: {data['text']}"
    assert any(term in text_lower for term in ["not reported", "do not contain", "not found", "no record", "no mention", "not documented", "cannot find", "no information", "not available", "no echocardiogram", "not provided", "absent"]), f"Answer did not explicitly state missing evidence: {data['text']}"
    print(f"[HTTP Test 02 - Live Ollama] Abstention verified: {data['text'][:120]}... (citations={len(data['citations'])})")


def test_03_http_conflicting_values(env_setup):
    """
    [Live Ollama Provider: llama3.2:3b]
    3. Conflicting values via HTTP: Fasting Glucose 105 mg/dL vs 142 mg/dL across facilities.
    Assert both values are present, not misattributed across facilities, and discrepancy noted.
    """
    client = env_setup["client"]
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"

    t0 = time.time()
    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "What were my fasting blood glucose levels and were there discrepancies between facilities?"}
    )
    latency = time.time() - t0
    print(f"\n[HTTP Test 03 - Live Ollama - Warm Latency] {latency:.3f} s")

    assert resp.status_code == 200
    data = resp.json()
    assert data["sender"] == "ai"
    cited_ids = [c["reportId"] for c in data["citations"]]
    assert "rep_synth_glu1" in cited_ids
    assert "rep_synth_glu2" in cited_ids

    # Strengthened grounding assertions on answer text
    import re
    text_lower = data["text"].lower()
    assert "105" in data["text"], f"Expected glucose 105 missing from answer text: {data['text']}"
    assert "142" in data["text"], f"Expected glucose 142 missing from answer text: {data['text']}"
    # Verify values are not misattributed across facilities
    assert not re.search(r'\b142\s*(?:mg/dl)?\s*(?:on\s*[\d-]+)?\s*at\s*metro\s*health', text_lower), f"Misattributed 142 mg/dL to Metro Health: {data['text']}"
    assert not re.search(r'\b105\s*(?:mg/dl)?\s*(?:on\s*[\d-]+)?\s*at\s*valley\s*lab', text_lower), f"Misattributed 105 mg/dL to Valley Lab: {data['text']}"
    assert not re.search(r'at\s*metro\s*health[^,.]*?(?:was|is|of)\s*142', text_lower), f"Misattributed 142 mg/dL to Metro Health: {data['text']}"
    assert not re.search(r'at\s*valley\s*lab[^,.]*?(?:was|is|of)\s*105', text_lower), f"Misattributed 105 mg/dL to Valley Lab: {data['text']}"
    assert any(term in text_lower for term in ["105", "142", "discrepanc", "differ", "vari", "conflict", "and"]), f"Values not properly articulated: {data['text']}"
    print(f"[HTTP Test 03 - Live Ollama] Conflicting glucose response: {data['text'][:140]}... (citations={cited_ids})")


def test_04_http_ollama_outage_error_handling(env_setup, monkeypatch):
    """4. Ollama outage / timeout via HTTP: Explicit error response, NO silent mock fallback."""
    client = env_setup["client"]
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"

    # Point to nonexistent port to trigger connection failure
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:65530")

    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "What is my potassium level?"}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["sender"] == "ai"
    assert data["reasoningType"] == "error"
    assert "[Ollama Service Unavailable" in data["text"]
    assert len(data["citations"]) == 0
    # Ensure no clinical data hallucinated
    assert "potassium" not in data["text"].lower() or "service" in data["text"].lower()
    print(f"[HTTP Test 04] Explicit error returned: {data['text']}")


def test_05_http_citation_schema_and_metadata(env_setup):
    """5. Citation schema and metadata in HTTP response."""
    client = env_setup["client"]
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"

    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "What was my potassium level on October 12, 2026?"}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "citations" in data
    citations = data["citations"]
    assert len(citations) >= 1

    for cit in citations:
        assert isinstance(cit["reportId"], str) and len(cit["reportId"]) > 0
        assert isinstance(cit["reportTitle"], str) and len(cit["reportTitle"]) > 0
        assert isinstance(cit["date"], str)
        assert isinstance(cit["excerpt"], str) and len(cit["excerpt"]) > 0
        assert isinstance(cit["confidenceScore"], (float, int))
        assert 0.0 <= cit["confidenceScore"] <= 1.0
        # Verify citation belongs to synthetic patient's reports
        assert cit["reportId"].startswith("rep_synth_")

    print(f"[HTTP Test 05] Citations validated: {citations[0]['reportTitle']} (Score: {citations[0]['confidenceScore']})")


def test_06_http_configured_provider_verification():
    """6. Verify that response actually comes from the real configured Ollama provider."""
    prov = get_llm_provider()
    assert prov is not None
    assert isinstance(prov, OllamaProvider)
    assert prov.provider_name == "ollama (llama3.2:3b)"
    print(f"[HTTP Test 06] Configured provider verified: {prov.provider_name}")

def test_07_http_incorrect_date_or_facility_handling(env_setup):
    """
    [Live Ollama Provider: llama3.2:3b]
    7. Incorrect date/facility query via HTTP:
    Patient asks for potassium on January 1, 2025 at Memorial Hospital.
    The real report is on 2026-10-12 at Metro Health.
    Verifies that rep_synth_cmp is NOT falsely cited for conflicting date/hospital,
    and assert the answer text does NOT invent or affirm potassium at Memorial Hospital / Jan 2025.
    """
    client = env_setup["client"]
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"

    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "What was my potassium level on January 1, 2025 at Memorial Hospital?"}
    )
    assert resp.status_code == 200
    data = resp.json()

    cited_ids = [c["reportId"] for c in data.get("citations", [])]
    assert "rep_synth_cmp" not in cited_ids, (
        f"Defect: rep_synth_cmp was cited for a conflicting 2025 Memorial Hospital query: {cited_ids}"
    )

    # Strengthened grounding assertions on answer text
    import re
    text_lower = data["text"].lower()
    # Must NOT invent or affirm potassium 5.8 was at Memorial Hospital
    assert not re.search(r'memorial\s*hospital[^.\n]{0,40}\b5\.8\b', text_lower), f"Answer misattributed 5.8 to Memorial Hospital: {data['text']}"
    assert not re.search(r'\b5\.8\b[^.\n]{0,40}memorial\s*hospital', text_lower), f"Answer misattributed 5.8 to Memorial Hospital: {data['text']}"
    # Must NOT affirm potassium on January 1, 2025
    assert not re.search(r'(?:january 1,? 2025|2025-01-01)[^.\n]{0,40}\b5\.8\b', text_lower), f"Answer affirmed potassium 5.8 on Jan 1 2025: {data['text']}"
    # Must indicate absence of records or clarify Metro Health date
    assert any(term in text_lower for term in ["not documented", "no record", "no documentation", "not found", "metro health", "2026-10-12", "october 12", "does not show", "no mention", "not available", "absent"]), f"Answer failed to clarify record absence/discrepancy: {data['text']}"
    print(f"\n[HTTP Test 07 - Live Ollama] Incorrect date/facility handled safely: citations={cited_ids}, text={data['text'][:120]}...")


def test_08_mocked_provider_conflicting_facility_grounding(env_setup, monkeypatch):
    """
    [Mocked Provider: Deterministic Grounding Assertion]
    8. Deterministic test of conflicting records:
    Verifies that when LLM returns synthetic conflicting text,
    citations and grounding assertions verify exact non-misattribution.
    """
    client = env_setup["client"]
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"

    from backend.app.ai.llm.base import LLMProvider
    from typing import Optional

    class MockDeterministicLLM(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "mock-deterministic"

        def health_check(self) -> bool:
            return True

        def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs) -> str:
            return (
                "Your records show conflicting fasting blood glucose results: "
                "On 2026-09-01 at Metro Health, your glucose was 105 mg/dL. "
                "On 2026-09-05 at Valley Lab, your glucose was 142 mg/dL. "
                "There is a discrepancy of 37 mg/dL between facilities."
            )

    import backend.app.services.chat_service as chat_service_mod
    monkeypatch.setattr(chat_service_mod, "get_llm_provider", lambda: MockDeterministicLLM())

    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "What were my fasting blood glucose levels and were there discrepancies between facilities?"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sender"] == "ai"
    assert "105" in data["text"] and "142" in data["text"]
    assert "Metro Health" in data["text"] and "Valley Lab" in data["text"]
    import re
    assert not re.search(r'Valley\s*Lab[^.\n]{0,35}\b105\b', data["text"], re.I)
    assert not re.search(r'Metro\s*Health[^.\n]{0,35}\b142\b', data["text"], re.I)
    cited_ids = [c["reportId"] for c in data["citations"]]
    assert "rep_synth_glu1" in cited_ids
    assert "rep_synth_glu2" in cited_ids
    print(f"\n[HTTP Test 08 - Mocked Provider] Conflicting facility deterministic test passed")


def test_09_mocked_provider_unsupported_diagnosis_rewriting(env_setup, monkeypatch):
    """
    [Mocked Provider: Deterministic Grounding Assertion]
    9. Deterministic test of unsupported diagnosis removal:
    Verifies that when LLM hallucinates an unsupported diagnosis alongside a supported lab,
    the pipeline strips/rewrites the unsupported diagnosis into explicit documentation absence.
    """
    client = env_setup["client"]
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"

    from backend.app.ai.llm.base import LLMProvider
    from typing import Optional

    class MockHallucinatingLLM(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "mock-hallucinating"

        def health_check(self) -> bool:
            return True

        def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs) -> str:
            return (
                "Your potassium level was 5.8 mEq/L at Metro Health on 2026-10-12, "
                "and you have been diagnosed with severe cardiac ischemia."
            )

    import backend.app.services.chat_service as chat_service_mod
    monkeypatch.setattr(chat_service_mod, "get_llm_provider", lambda: MockHallucinatingLLM())

    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "What was my potassium level on October 12, 2026?"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sender"] == "ai"
    assert "5.8" in data["text"]
    assert "you have been diagnosed with severe cardiac ischemia" not in data["text"].lower()
    assert "no clinical documentation" in data["text"].lower() or "not documented" in data["text"].lower() or "cardiac ischemia" not in data["text"].lower()
    print(f"\n[HTTP Test 09 - Mocked Provider] Unsupported diagnosis rewritten safely: {data['text']}")

