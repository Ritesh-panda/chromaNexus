import logging
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.ai.retrieval import VectorStore, InMemoryVectorStore
from backend.app.ai.llm.base import LLMProvider
from backend.app.ai.llm import get_llm_provider
from backend.app.ai.rag.context_builder import RAGContextBuilder, RAGContext
from backend.app.ai.rag.prompts import (
    MEDICAL_SAFETY_SYSTEM_PROMPT,
    RAG_USER_PROMPT_TEMPLATE,
    RAG_USER_PROMPT_WITH_HISTORY_TEMPLATE
)
from backend.app.ai.rag.hybrid_retriever import HybridRetriever, HybridRetrievalResult
from backend.app.ai.rag.query_resolver import ConversationQueryResolver, ResolvedQuery

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
      User Query ➔ Conversation Context Resolver ➔ Hybrid Retriever (Structured DB + Vector Store)
      ➔ Result Fusion & Reranking ➔ Context Builder ➔ Medical Safety Guardrails ➔ LLM Provider
    """

    def __init__(
        self,
        retriever: Optional[Union[HybridRetriever, VectorStore]] = None,
        llm: Optional[LLMProvider] = None,
        context_builder: Optional[RAGContextBuilder] = None,
        db_session: Optional[Session] = None,
        query_resolver: Optional[ConversationQueryResolver] = None
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
        self.query_resolver = query_resolver or ConversationQueryResolver()
        self.db = db_session

    def query(
        self,
        question: str,
        patient_id: Optional[str] = "pat_001",
        top_k: int = 6,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> RAGResponse:
        """
        Executes end-to-end Hybrid RAG query workflow with conversation awareness.
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

        # 1. Resolve conversation context and determine query search meaning
        resolved_q: ResolvedQuery = self.query_resolver.resolve(
            query=question,
            conversation_history=conversation_history
        )

        # 2. Execute Hybrid Retrieval using resolved clinical meaning
        retrieval_result: HybridRetrievalResult = self.hybrid_retriever.retrieve(
            query=question,
            patient_id=patient_id or "pat_001",
            top_k=top_k,
            search_query=resolved_q.resolved_query,
            override_intent=resolved_q.intent if (resolved_q.is_overview or resolved_q.is_follow_up) else None,
            override_keywords=resolved_q.keywords
        )

        # 3. Build structured medical context and citation metadata
        rag_context: RAGContext = self.context_builder.build_context(retrieval_result.elements)

        # 4. Format grounded prompt with conversation history and medical safety guardrails
        if resolved_q.formatted_history:
            user_prompt = RAG_USER_PROMPT_WITH_HISTORY_TEMPLATE.format(
                conversation_history=resolved_q.formatted_history,
                context=rag_context.formatted_context,
                query=question.strip()
            )
        else:
            user_prompt = RAG_USER_PROMPT_TEMPLATE.format(
                context=rag_context.formatted_context,
                query=question.strip()
            )

        # 5. Generate answer via single LLM Provider call (no duplicate LLM calls)
        try:
            answer = self.llm.generate(
                prompt=user_prompt,
                system_instruction=MEDICAL_SAFETY_SYSTEM_PROMPT,
                max_tokens=600,
                temperature=0.1
            )
            answer = self._sanitize_answer(answer, question)
        except Exception as e:
            logger.error(f"Error executing LLM generation: {str(e)}")
            answer = f"I retrieved relevant medical records for your query, but encountered an error generating the final response: {str(e)}"

        # 6. Classify reasoning type; suppress unrelated citations when answer
        #    explicitly states the requested information is not available.
        reasoning_type = "fact" if rag_context.total_sources > 0 else "inference"
        final_citations = rag_context.citations
        if self._answer_indicates_missing_data(answer):
            final_citations = []
            reasoning_type = "inference"

        return RAGResponse(
            answer=answer,
            reasoning_type=reasoning_type,
            citations=final_citations,
            sources_used=rag_context.total_sources,
            provider=self.llm.provider_name,
            intent=retrieval_result.intent.value
        )

    # ------------------------------------------------------------------
    # Answer post-processing
    # ------------------------------------------------------------------

    def _sanitize_answer(self, answer: str, original_question: str) -> str:
        """
        Defense-in-depth post-processor that strips common LLM response artifacts:

        1. Leading echo of the user's question (e.g. "Patient: What about my diabetes?")
        2. Conversation-meta openers the LLM sometimes inserts despite prompt instructions.

        This does NOT rewrite or alter the medical content — it only removes
        a leading artifact line when the first line is purely an echo or preamble.
        """
        import re

        if not answer:
            return answer

        lines = answer.splitlines()

        # Remove a leading line that is purely a role-prefixed echo of the question
        echo_prefixes = ("patient:", "user:", "q:")
        first_line = lines[0].strip().lower() if lines else ""
        for prefix in echo_prefixes:
            if first_line.startswith(prefix):
                # Strip only if this line doesn't contain genuine medical content
                # (heuristic: if the stripped remainder is close to the original question)
                stripped_text = lines[0].strip()[len(prefix):].strip().lower()
                question_lower = original_question.strip().lower()
                if (
                    stripped_text == question_lower or
                    question_lower.startswith(stripped_text[:30]) or
                    stripped_text.startswith(question_lower[:30])
                ):
                    lines = lines[1:]
                    # Also drop any blank lines that follow the removed echo
                    while lines and not lines[0].strip():
                        lines = lines[1:]
                break

        # Remove leading conversation-meta openers (entire first sentence)
        META_PATTERNS = [
            r"^based on (?:our |the )?conversation(?: history)?[\s,]",
            r"^as (?:we |i )?discussed(?: earlier| previously)?[\s,]",
            r"^as mentioned(?: previously| earlier)?[\s,]",
            r"^(?:i'?d like to|i would like to) (?:provide|clarify|explain|address)[\s,]",
            r"^i can clarify that[\s,]",
            r"^(?:certainly|sure|of course)[!,.]?\s",
        ]
        reconstructed = "\n".join(lines)
        for pat in META_PATTERNS:
            match = re.match(pat, reconstructed.strip(), re.IGNORECASE)
            if match:
                # Remove just the matched preamble phrase; keep the rest
                reconstructed = reconstructed.strip()[match.end():].lstrip(", \t")
                # Capitalise the first character of what remains
                if reconstructed:
                    reconstructed = reconstructed[0].upper() + reconstructed[1:]
                break

        return reconstructed.strip()

    # ------------------------------------------------------------------
    # Citation quality
    # ------------------------------------------------------------------

    #: Phrases that indicate the LLM found no matching records for the question.
    _NO_DATA_PHRASES = (
        "do not contain",
        "does not contain",
        "no information about",
        "not found in the",
        "not present in",
        "records do not include",
        "no records",
        "not available in the",
        "cannot find",
        "no relevant",
        "records contain no",
        "no kidney",
        "no data",
        "not documented",
    )

    def _answer_indicates_missing_data(self, answer: str) -> bool:
        """
        Returns True when the generated answer tells the user that the requested
        information is not present in the medical records.

        When this is True, any retrieved citations are suppressed. Without this
        guard, the retriever returns the nearest-neighbour records (e.g. MRI,
        HbA1c) even for questions like "what about my kidney function?" where
        no kidney data exists, causing unrelated documents to appear as citations
        alongside a correct 'data not available' answer.
        """
        lower = answer.lower()
        return any(phrase in lower for phrase in self._NO_DATA_PHRASES)
