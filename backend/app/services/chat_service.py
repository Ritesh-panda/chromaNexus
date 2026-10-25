from typing import List, Tuple, Optional, Dict
from sqlalchemy.orm import Session
from backend.app.models.patient import Patient
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from backend.app.ai.retrieval import get_vector_store
from backend.app.ai.llm import get_llm_provider


def process_clinical_chat_query(
    db: Session,
    patient: Patient,
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    return_trend: bool = False
):
    """
    Evaluates patient memory query against PostgresVectorStore and SQL relational tables using Hybrid RAG.
    Supports bounded conversation history for follow-up resolution and natural dialogue flow.
    Returns: (response_text, reasoning_type, citations)
    """
    if not patient or not getattr(patient, "id", None) or not str(patient.id).strip():
        raise ValueError("A valid authenticated patient identity is required for clinical chat.")

    vector_store = get_vector_store(db_session=db)
    hybrid_retriever = HybridRetriever(vector_store=vector_store, db_session=db)
    llm_provider = get_llm_provider()
    pipeline = RAGPipeline(retriever=hybrid_retriever, llm=llm_provider, db_session=db)

    rag_response = pipeline.query(
        question=query,
        patient_id=patient.id,
        conversation_history=conversation_history
    )

    if return_trend:
        return rag_response.answer, rag_response.reasoning_type, rag_response.citations, rag_response.structured_trend
    return rag_response.answer, rag_response.reasoning_type, rag_response.citations

