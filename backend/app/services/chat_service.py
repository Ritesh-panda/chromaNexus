from typing import List, Tuple, Optional, Dict
from sqlalchemy.orm import Session
from backend.app.models.patient import Patient
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from backend.app.ai.retrieval import PostgresVectorStore
from backend.app.ai.llm import get_llm_provider


def process_clinical_chat_query(
    db: Session,
    patient: Patient,
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, str, List[dict]]:
    """
    Evaluates patient memory query against PostgresVectorStore and SQL relational tables using Hybrid RAG.
    Supports bounded conversation history for follow-up resolution and natural dialogue flow.
    Returns: (response_text, reasoning_type, citations)
    """
    vector_store = PostgresVectorStore(db_session=db)
    hybrid_retriever = HybridRetriever(vector_store=vector_store, db_session=db)
    llm_provider = get_llm_provider()
    pipeline = RAGPipeline(retriever=hybrid_retriever, llm=llm_provider, db_session=db)

    rag_response = pipeline.query(
        question=query,
        patient_id=patient.id,
        conversation_history=conversation_history
    )

    return rag_response.answer, rag_response.reasoning_type, rag_response.citations

