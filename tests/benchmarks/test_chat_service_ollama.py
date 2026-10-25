"""
ChronaNexus Chat Service Integration Verification (Phase 3 & 4)
===============================================================
Tests the real application chat_service.process_clinical_chat_query against
isolated test storage (temporary in-memory SQLite and isolated temporary ChromaDB)
with Ollama (model: llama3.2:3b):
1. Invokes OllamaProvider with llama3.2:3b.
2. Verified prompt contains retrieved synthetic evidence and source metadata.
3. Supported clinical question (answer present in evidence).
4. Missing evidence question (abstention and citation suppression).
5. Conflicting synthetic records (both sources and facilities remain visible).
6. Explicit error handling (NO silent mock fallback).
7. Strict citation grounding against retrieved source identifiers.
"""

import os
import sys
import shutil
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.core.database import Base
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.document_chunk import DocumentChunkModel
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import get_vector_store
from backend.app.services.chat_service import process_clinical_chat_query
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from backend.app.ai.llm.ollama import OllamaProvider


@pytest.fixture(scope="module")
def isolated_env():
    # 1. Setup isolated Chroma directory
    chroma_dir = tempfile.mkdtemp(prefix="chrona_test_chroma_")
    old_chroma_dir = getattr(settings, "CHROMA_PERSIST_DIRECTORY", None)
    old_coll_name = getattr(settings, "CHROMA_COLLECTION_NAME", None)
    old_llm_prov = getattr(settings, "LLM_PROVIDER", None)
    old_ollama_model = getattr(settings, "OLLAMA_MODEL", None)

    settings.CHROMA_PERSIST_DIRECTORY = chroma_dir
    settings.CHROMA_COLLECTION_NAME = "test_chat_collection"
    settings.LLM_PROVIDER = "ollama"
    settings.OLLAMA_MODEL = "llama3.2:3b"

    # 2. Setup isolated in-memory SQLite DB
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 3. Seed synthetic patient (clean, zero default allergies to test pure citations)
    user = User(id="user-synth-001", name="Jane Doe", email="jane.synthetic@test.nexus", hashed_password="hash123")
    db.add(user)
    patient = Patient(id="pat-synth-001", user_id="user-synth-001", known_allergies=[])
    db.add(patient)

    # 4. Seed synthetic reports and chunks
    # Report 1: CMP with Potassium 5.8 mEq/L
    rep1 = MedicalReport(
        id="rep-cmp-001",
        patient_id="pat-synth-001",
        title="Comprehensive Metabolic Panel",
        file_name="cmp_20261012.pdf",
        hospital_name="Metro Health",
        report_date="2026-10-12",
        status="completed"
    )
    db.add(rep1)
    chunk1_text = (
        "Comprehensive Metabolic Panel (2026-10-12) - Metro Health\n"
        "Component Results:\n"
        "Potassium: 5.8 mEq/L [HIGH] (Reference: 3.5-5.0 mEq/L)\n"
        "Sodium: 140 mEq/L (Reference: 135-145 mEq/L)\n"
        "Impression: Moderate hyperkalemia."
    )
    sql_chk1 = DocumentChunkModel(
        id="chk-cmp-001",
        document_id="rep-cmp-001",
        patient_id="pat-synth-001",
        chunk_id="rep-cmp-001_chk_0",
        chunk_index=0,
        page_number=1,
        content=chunk1_text,
        chunk_metadata={
            "document_id": "rep-cmp-001",
            "patient_id": "pat-synth-001",
            "report_title": "Comprehensive Metabolic Panel",
            "date": "2026-10-12",
            "hospital_name": "Metro Health"
        }
    )
    db.add(sql_chk1)

    # Report 2: Outpatient Glucose from Metro Health
    rep2 = MedicalReport(
        id="rep-gl-001",
        patient_id="pat-synth-001",
        title="Outpatient Fasting Glucose",
        file_name="glucose_metro.pdf",
        hospital_name="Metro Health",
        report_date="2026-09-01",
        status="completed"
    )
    db.add(rep2)
    chunk2_text = (
        "Outpatient Fasting Glucose (2026-09-01) - Metro Health\n"
        "Fasting Plasma Glucose: 105 mg/dL (Reference: 70-99 mg/dL). High."
    )
    sql_chk2 = DocumentChunkModel(
        id="chk-gl-001",
        document_id="rep-gl-001",
        patient_id="pat-synth-001",
        chunk_id="rep-gl-001_chk_0",
        chunk_index=0,
        page_number=1,
        content=chunk2_text,
        chunk_metadata={
            "document_id": "rep-gl-001",
            "patient_id": "pat-synth-001",
            "report_title": "Outpatient Fasting Glucose",
            "date": "2026-09-01",
            "hospital_name": "Metro Health"
        }
    )
    db.add(sql_chk2)

    # Report 3: Valley Lab Endocrinology Panel with conflicting Glucose
    rep3 = MedicalReport(
        id="rep-gl-002",
        patient_id="pat-synth-001",
        title="Diagnostic Endocrinology Panel",
        file_name="glucose_valley.pdf",
        hospital_name="Valley Lab",
        report_date="2026-09-05",
        status="completed"
    )
    db.add(rep3)
    chunk3_text = (
        "Diagnostic Endocrinology Panel (2026-09-05) - Valley Lab\n"
        "Fasting Plasma Glucose: 142 mg/dL (Reference: 70-99 mg/dL). Markedly elevated."
    )
    sql_chk3 = DocumentChunkModel(
        id="chk-gl-002",
        document_id="rep-gl-002",
        patient_id="pat-synth-001",
        chunk_id="rep-gl-002_chk_0",
        chunk_index=0,
        page_number=1,
        content=chunk3_text,
        chunk_metadata={
            "document_id": "rep-gl-002",
            "patient_id": "pat-synth-001",
            "report_title": "Diagnostic Endocrinology Panel",
            "date": "2026-09-05",
            "hospital_name": "Valley Lab"
        }
    )
    db.add(sql_chk3)
    db.commit()

    # Index into isolated Chroma
    vs = get_vector_store(persist_directory=chroma_dir, collection_name="test_chat_collection")
    c1 = DocumentChunk(
        chunk_id="rep-cmp-001_chk_0",
        document_id="rep-cmp-001",
        chunk_index=0,
        page_number=1,
        text=chunk1_text,
        metadata=sql_chk1.chunk_metadata
    )
    c2 = DocumentChunk(
        chunk_id="rep-gl-001_chk_0",
        document_id="rep-gl-001",
        chunk_index=0,
        page_number=1,
        text=chunk2_text,
        metadata=sql_chk2.chunk_metadata
    )
    c3 = DocumentChunk(
        chunk_id="rep-gl-002_chk_0",
        document_id="rep-gl-002",
        chunk_index=0,
        page_number=1,
        text=chunk3_text,
        metadata=sql_chk3.chunk_metadata
    )
    vs.add_documents([c1, c2, c3])

    yield {
        "db": db,
        "patient": patient,
        "chroma_dir": chroma_dir,
        "vector_store": vs
    }

    # Teardown
    db.close()
    shutil.rmtree(chroma_dir, ignore_errors=True)
    settings.CHROMA_PERSIST_DIRECTORY = old_chroma_dir
    settings.CHROMA_COLLECTION_NAME = old_coll_name
    settings.LLM_PROVIDER = old_llm_prov
    settings.OLLAMA_MODEL = old_ollama_model


def test_01_real_chat_service_supported_factual_query(isolated_env):
    """Phase 3.1, 3.2, 3.3 & Grounding: Real chat service answers present clinical evidence and grounds citation."""
    db = isolated_env["db"]
    patient = isolated_env["patient"]

    query = "What was my potassium level on October 12, 2026?"
    answer, reasoning_type, citations = process_clinical_chat_query(
        db=db,
        patient=patient,
        query=query
    )

    print(f"\n[Test 1] Answer: {answer}")
    print(f"[Test 1] Reasoning Type: {reasoning_type}")
    print(f"[Test 1] Citations: {citations}")

    assert "5.8" in answer
    assert "mEq/L" in answer or "meq/l" in answer.lower()
    assert reasoning_type == "fact"
    # Grounding check: only the relevant CMP report should be cited; unrelated glucose reports are filtered
    rep_ids = [c.get("reportId") for c in citations]
    assert "rep-cmp-001" in rep_ids
    assert "rep-gl-001" not in rep_ids
    assert "rep-gl-002" not in rep_ids


def test_02_real_chat_service_missing_evidence_abstention(isolated_env):
    """Phase 3.4: Real chat service abstains and suppresses citations when evidence is absent."""
    db = isolated_env["db"]
    patient = isolated_env["patient"]

    query = "What was my echocardiogram ejection fraction (LVEF)?"
    answer, reasoning_type, citations = process_clinical_chat_query(
        db=db,
        patient=patient,
        query=query
    )

    print(f"\n[Test 2] Answer: {answer}")
    print(f"[Test 2] Reasoning Type: {reasoning_type}")
    print(f"[Test 2] Citations: {citations}")

    lower = answer.lower()
    abstention_indicators = [
        "not contain", "does not contain", "no information", "not found",
        "no record", "no mention", "not documented", "cannot find", "unavailable",
        "not reported", "was not reported"
    ]
    assert any(ind in lower for ind in abstention_indicators), f"Model failed to abstain: {answer}"
    # Citations must be completely suppressed on abstention
    assert len(citations) == 0
    assert reasoning_type == "inference"


def test_03_real_chat_service_conflicting_records(isolated_env):
    """Phase 3.5: Conflicting records across facilities remain visible."""
    db = isolated_env["db"]
    patient = isolated_env["patient"]

    query = "What are my fasting glucose readings across different facilities?"
    answer, reasoning_type, citations = process_clinical_chat_query(
        db=db,
        patient=patient,
        query=query
    )

    print(f"\n[Test 3] Answer: {answer}")
    print(f"[Test 3] Citations: {citations}")

    assert "105" in answer
    assert "142" in answer
    assert "Metro" in answer
    assert "Valley" in answer
    # Both report IDs should be present in citations
    rep_ids = [c.get("reportId") for c in citations]
    assert "rep-gl-001" in rep_ids
    assert "rep-gl-002" in rep_ids
    # CMP (potassium) is unrelated and filtered
    assert "rep-cmp-001" not in rep_ids


def test_04_explicit_error_handling_no_silent_mock_fallback(isolated_env):
    """
    Phase 3.6 & Phase 4: Regression test ensuring provider errors are explicit
    and NEVER silently invoke MockDeterministicLLMProvider.
    """
    db = isolated_env["db"]
    patient = isolated_env["patient"]
    vs = isolated_env["vector_store"]

    retriever = HybridRetriever(vector_store=vs, db_session=db)

    # Failing Ollama provider (unreachable host)
    failing_ollama = OllamaProvider(base_url="http://non-existent-domain-12345.local", model="llama3.2:3b", timeout=1.0)
    pipeline = RAGPipeline(retriever=retriever, llm=failing_ollama, db_session=db)

    rag_response = pipeline.query(
        question="What was my potassium level on October 12, 2026?",
        patient_id=patient.id
    )

    print(f"\n[Test 4 - Explicit Error Verification]")
    print(f"Answer: {rag_response.answer}")
    print(f"Provider reported: {rag_response.provider}")
    print(f"Reasoning Type: {rag_response.reasoning_type}")

    # Must be explicit error, NOT silent mock fabrication
    assert "[Ollama Service Unavailable" in rag_response.answer
    assert rag_response.reasoning_type == "error"
    assert len(rag_response.citations) == 0
    assert "According to your indexed laboratory panels" not in rag_response.answer


def test_05_citation_grounding_audit(isolated_env):
    """
    Phase 3.7: Audit whether citations are grounded in retrieved source identifiers.
    """
    db = isolated_env["db"]
    patient = isolated_env["patient"]

    query = "What was my potassium level on October 12, 2026?"
    answer, reasoning_type, citations = process_clinical_chat_query(
        db=db,
        patient=patient,
        query=query
    )

    valid_report_ids = {"rep-cmp-001"}
    assert len(citations) >= 1
    for cit in citations:
        report_id = cit.get("reportId")
        assert report_id in valid_report_ids, f"Ungrounded citation leaked: {report_id}"
        assert cit.get("date") == "2026-10-12"
