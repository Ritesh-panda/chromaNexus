import logging
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.ai.retrieval import VectorStore, InMemoryVectorStore
from backend.app.ai.llm.base import LLMProvider
from backend.app.ai.llm import get_llm_provider
from backend.app.ai.rag.context_builder import RAGContextBuilder, RAGContext
from backend.app.ai.rag.prompts import MEDICAL_SAFETY_SYSTEM_PROMPT, RAG_USER_PROMPT_TEMPLATE
from backend.app.ai.rag.hybrid_retriever import HybridRetriever, HybridRetrievalResult

logger = logging.getLogger(__name__)


class RAGResponse(BaseModel):
    answer: str
    reasoning_type: str = "fact"  # 'fact' or 'inference'
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    sources_used: int = 0
    provider: str = ""
    intent: Optional[str] = None


class RAGPipeline:
    """
    Production Hybrid RAG Orchestration Pipeline for ChronaNexus.
    Connects:
      User Query ➔ Query Intent Classifier ➔ Hybrid Retriever (Structured DB + Vector Store)
      ➔ Result Fusion & Reranking ➔ Context Builder ➔ Medical Safety Guardrails ➔ LLM Provider
    """

    def __init__(
        self,
        retriever: Optional[Union[HybridRetriever, VectorStore]] = None,
        llm: Optional[LLMProvider] = None,
        context_builder: Optional[RAGContextBuilder] = None,
        db_session: Optional[Session] = None
    ):
        if isinstance(retriever, HybridRetriever):
            self.hybrid_retriever = retriever
            self.vector_store = retriever.vector_store
        elif isinstance(retriever, VectorStore):
            self.vector_store = retriever
            self.hybrid_retriever = HybridRetriever(vector_store=retriever, db_session=db_session)
        else:
            self.vector_store = InMemoryVectorStore()
            self.hybrid_retriever = HybridRetriever(vector_store=self.vector_store, db_session=db_session)

        self.llm = llm or get_llm_provider()
        self.context_builder = context_builder or RAGContextBuilder()
        self.db = db_session

    def query(
        self,
        question: str,
        patient_id: Optional[str] = "pat_001",
        top_k: int = 6
    ) -> RAGResponse:
        """
        Executes end-to-end Hybrid RAG query workflow.
        """
        if not question or not question.strip():
            return RAGResponse(
                answer="Please provide a valid question regarding your medical records.",
                reasoning_type="inference",
                citations=[],
                sources_used=0,
                provider=self.llm.provider_name,
                intent="NONE"
            )

        # 1. Execute Hybrid Retrieval (Structured DB + Vector Store + Fusion + Reranker)
        retrieval_result: HybridRetrievalResult = self.hybrid_retriever.retrieve(
            query=question,
            patient_id=patient_id or "pat_001",
            top_k=top_k
        )

        # 2. Build structured medical context and citation metadata
        rag_context: RAGContext = self.context_builder.build_context(retrieval_result.elements)

        # 3. Format grounded prompt with medical safety guardrails
        user_prompt = RAG_USER_PROMPT_TEMPLATE.format(
            context=rag_context.formatted_context,
            query=question.strip()
        )

        # 4. Generate answer via LLM Provider
        try:
            answer = self.llm.generate(
                prompt=user_prompt,
                system_instruction=MEDICAL_SAFETY_SYSTEM_PROMPT,
                temperature=0.1
            )
        except Exception as e:
            logger.error(f"Error executing LLM generation: {str(e)}")
            answer = f"I retrieved relevant medical records for your query, but encountered an error generating the final response: {str(e)}"

        # 5. Classify reasoning type (fact if records found, inference if zero records)
        reasoning_type = "fact" if rag_context.total_sources > 0 else "inference"

        return RAGResponse(
            answer=answer,
            reasoning_type=reasoning_type,
            citations=rag_context.citations,
            sources_used=rag_context.total_sources,
            provider=self.llm.provider_name,
            intent=retrieval_result.intent.value
        )
