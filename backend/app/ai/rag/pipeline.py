import logging
import re
from typing import List, Dict, Any, Optional, Union, Tuple
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
    structured_trend: Optional[Dict[str, Any]] = None


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
        from backend.app.clinical.structured_query import StructuredQueryDetector, StructuredClinicalQueryEngine
        self.structured_detector = StructuredQueryDetector()
        self.structured_engine = StructuredClinicalQueryEngine(db_session) if db_session else None
        from backend.app.clinical.verification import EvidenceGroundingPipeline
        self.verification_pipeline = EvidenceGroundingPipeline(db_session=db_session)

    def query(
        self,
        question: str,
        patient_id: str,
        top_k: int = 6,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> RAGResponse:
        """
        Executes end-to-end Hybrid RAG query workflow with conversation awareness.
        Requires authoritative, non-empty patient_id; fails closed if identity is missing.
        """
        if not patient_id or not str(patient_id).strip():
            logger.warning("RAGPipeline.query invoked without a valid patient identity; failing closed.")
            return RAGResponse(
                answer="Error: A valid authenticated patient identity is required to perform clinical retrieval. No records were accessed.",
                reasoning_type="error",
                citations=[],
                sources_used=0,
                provider=self.llm.provider_name if hasattr(self, "llm") and self.llm else "none",
                intent="NONE"
            )

        if not question or not question.strip():
            return RAGResponse(
                answer="Please provide a valid question regarding your medical records.",
                reasoning_type="inference",
                citations=[],
                sources_used=0,
                provider=self.llm.provider_name if hasattr(self, "llm") and self.llm else "none",
                intent="NONE"
            )

        # 1. Resolve conversation context and determine query search meaning
        resolved_q: ResolvedQuery = self.query_resolver.resolve(
            query=question,
            conversation_history=conversation_history
        )

        # 1b. Phase 5: Structured Clinical Query Engine
        # Evaluates exact longitudinal trends, latest values, and comparisons against structured patient records
        if self.structured_engine:
            from backend.app.clinical.structured_query.models import TrendDirection
            structured_intent = self.structured_detector.detect(question)
            if structured_intent.is_structured_query:
                trend_result = self.structured_engine.execute_query(structured_intent, str(patient_id).strip())
                if trend_result.trend_direction != TrendDirection.NOT_FOUND or structured_intent.is_multi_analyte:
                    # Phase 6: Provenance verification of structured result
                    grounded_trend = self.verification_pipeline.verify_structured_trend_response(
                        trend_result,
                        patient_id=str(patient_id).strip()
                    )
                    return RAGResponse(
                        answer=grounded_trend.verified_answer,
                        reasoning_type="fact",
                        citations=grounded_trend.citations,
                        sources_used=len(grounded_trend.citations),
                        provider="structured_clinical_query_engine",
                        intent=structured_intent.query_type.value if structured_intent.query_type else "STRUCTURED_CLINICAL_QUERY",
                        structured_trend=trend_result.model_dump()
                    )

        # 2. Execute Hybrid Retrieval using resolved clinical meaning
        retrieval_result: HybridRetrievalResult = self.hybrid_retriever.retrieve(
            query=question,
            patient_id=str(patient_id).strip(),
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
        provider_error = False
        try:
            answer = self.llm.generate(
                prompt=user_prompt,
                system_instruction=MEDICAL_SAFETY_SYSTEM_PROMPT,
                max_tokens=600,
                temperature=0.1
            )
            # Check for provider failure / timeout strings
            if answer and any(x in answer for x in ["[Ollama Service Unavailable", "[Ollama Error", "[Ollama Timeout", "Gemini API key is not configured"]):
                provider_error = True
                logger.error(f"Configured LLM provider returned error: {answer}")
                # Do NOT silently substitute mock data; preserve explicit error transparency
            else:
                answer = self._sanitize_answer(answer, question)
        except Exception as e:
            logger.error(f"Error executing LLM generation: {str(e)}")
            provider_error = True
            answer = f"[{self.llm.provider_name} Error: {str(e)}]"

        # 6. Phase 6: Evidence-Grounding & Claim-Verification Pipeline
        if provider_error:
            reasoning_type = "error"
            final_citations = []
        else:
            grounding_res = self.verification_pipeline.verify_answer(
                candidate_answer=answer,
                citations=rag_context.citations,
                patient_id=str(patient_id).strip(),
                query=question,
                retrieval_chunks=retrieval_result.elements
            )
            answer = grounding_res.verified_answer
            final_citations = grounding_res.citations
            reasoning_type = grounding_res.reasoning_type

        return RAGResponse(
            answer=answer,
            reasoning_type=reasoning_type,
            citations=final_citations,
            sources_used=len(final_citations),
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
        "not reported",
        "was not reported",
        "is not reported",
        "no mention of",
        "no mention",
        "not provided",
        "no record of",
        "no record",
        "not found",
        "not available",
        "no documentation",
    )

    _NO_DATA_REGEX_PATTERNS = [
        r"\bno\s+(?:clinical\s+)?(?:information|records?|data|evidence|mention|reference|trace)\b",
        r"\b(?:not|never|was\s+not|were\s+not|is\s+not)\s+(?:found|reported|documented|provided|mentioned|included|present|available)\b",
        r"\b(?:do|does|did)\s+not\s+(?:contain|mention|include|show|indicate)\b",
        r"\bcannot\s+(?:find|locate|determine)\b",
        r"\bno\s+relevant\b",
        r"\bno\s+documentation\b",
        r"\bno\s+record\b",
        r"\bunavailable\s+in\b",
        r"\bnot\s+in\s+the\s+records\b",
    ]

    _GENERIC_GROUNDING_STOPWORDS = {
        "patient", "health", "metro", "hospital", "reference", "ref", "date",
        "high", "normal", "low", "result", "results", "test", "level", "panel",
        "report", "documented", "diagnostic", "outpatient", "oral", "daily",
        "your", "yours", "were", "with", "from", "also", "have", "has", "had", "been",
        "these", "this", "that", "excerpt", "page", "labs", "count", "blood", "intake",
        "records", "record", "found", "provided", "files", "data", "claim", "unverified",
        "according", "complete", "order", "profile", "screening", "study", "exam",
        "examination", "note", "notes", "encounter", "findings", "history", "clinical",
        "the", "was", "is", "are", "you", "and", "but", "also", "for", "about",
        "diagnosed", "take", "taking", "start", "stop", "should", "prescribed", "mg"
    }

    _KNOWN_INSTITUTIONAL_FACILITIES = {
        "metro health", "valley lab", "memorial hospital", "quest diagnostics", "metro general hospital"
    }

    def _answer_indicates_missing_data(self, answer: str) -> bool:
        """
        Returns True when the generated answer tells the user that the requested
        information is not present in the medical records.

        When this is True, any retrieved citations are suppressed. Without this
        guard, the retriever returns the nearest-neighbour records (e.g. MRI,
        HbA1c) even for questions like 'what about my kidney function?' where
        no kidney data exists, causing unrelated documents to appear as citations
        alongside a correct 'data not available' answer.
        """
        import re
        lower = answer.lower()
        if any(phrase in lower for phrase in self._NO_DATA_PHRASES):
            return True
        for pat in self._NO_DATA_REGEX_PATTERNS:
            if re.search(pat, lower):
                return True
        return False

    _CONTROLLED_UNIT_CONVERSIONS = {
        ("g/dl", "g/l"): 10.0,
        ("g/l", "g/dl"): 0.1,
    }

    _KNOWN_CLINICAL_UNITS = {
        "x10^3/ul", "x10^6/ul", "x10^3", "x10^6", "k/ul", "m/ul",
        "meq/l", "mg/dl", "g/dl", "g/l", "mmol/l", "umol/l",
        "u/l", "iu/l", "pg", "fl", "%", "mcg", "mg", "g", "ml", "l",
        "uiu/ml", "ng/dl"
    }

    _MONTH_NAMES = {
        "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
        "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
        "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12
    }

    @classmethod
    def _parse_full_dates(cls, text: str) -> List[Tuple[int, int, int]]:
        import re
        found = []
        if not text:
            return found
        # 1. ISO: YYYY-MM-DD
        for m in re.finditer(r"\b(19\d\d|20\d\d)[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b", text):
            found.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
        # 2. US: MM/DD/YYYY
        for m in re.finditer(r"\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](19\d\d|20\d\d)\b", text):
            found.append((int(m.group(3)), int(m.group(1)), int(m.group(2))))
        # 3. Month Day, Year
        for m in re.finditer(r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(0?[1-9]|[12]\d|3[01]),?\s+(19\d\d|20\d\d)\b", text, re.I):
            found.append((int(m.group(3)), cls._MONTH_NAMES[m.group(1).lower()], int(m.group(2))))
        # 4. Day Month Year
        for m in re.finditer(r"\b(0?[1-9]|[12]\d|3[01])\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?),?\s+(19\d\d|20\d\d)\b", text, re.I):
            found.append((int(m.group(3)), cls._MONTH_NAMES[m.group(2).lower()], int(m.group(1))))
        return found

    @staticmethod
    def _normalize_facility(name: str) -> str:
        import re
        if not name:
            return ""
        return re.sub(r"\s+", " ", name.strip().lower())

    @classmethod
    def _extract_facilities_from_sentence(cls, sent: str, candidate_facs: set) -> set:
        import re
        sent_lower = sent.lower()
        found = set()
        for cf in candidate_facs:
            if cf and cf in sent_lower:
                found.add(cf)
        fac_patterns = [
            r"\b(?:at|from)\s+([A-Za-z0-9\.\'\-]+(?:\s+[A-Za-z0-9\.\'\-]+){0,4}(?:\s+(?:Hospital|Clinic|Center|Health|Lab|Laboratory|System|Medical Group|Associates|Outpatient))?)\b",
            r"\b([A-Za-z0-9\.\'\-]+(?:\s+[A-Za-z0-9\.\'\-]+){0,3}\s+(?:Hospital|Clinic|Center|Health|Lab|Laboratory))\b"
        ]
        for pat in fac_patterns:
            for m in re.finditer(pat, sent, re.I):
                cand = cls._normalize_facility(m.group(1))
                if cand and cand not in {
                    "the comprehensive", "the complete", "the diagnostic", "the outpatient",
                    "complete blood", "comprehensive metabolic", "diagnostic endocrinology"
                }:
                    found.add(cand)
        return found

    def _extract_clinical_facts_from_citations(self, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts structured clinical findings (analyte, value, unit, ref_range, date, facility)
        from candidate citation excerpts.
        """
        import re
        facts = []
        lab_line_re = re.compile(
            r"([A-Za-z\s]+?):\s*([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z0-9\/\^\%]+)?(?:\[([A-Z]+)\])?(?:\s*\((?:Ref|Reference):\s*([0-9.]+)-([0-9.]+)\))?",
            re.IGNORECASE
        )
        free_re = re.compile(
            r"\b(Total Cholesterol|Cholesterol|Potassium|Sodium|WBC|Hemoglobin|Glucose|Fasting Plasma Glucose|Fasting Glucose|Creatinine|BUN|Calcium|HbA1c|Lisinopril|Metformin)\s*(?:is|was|level|level was|of|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*(mg\/dL|mEq\/L|g\/dL|x10\^3\/uL|mg|mcg|%|units)?",
            re.IGNORECASE
        )

        for cit in citations:
            cid = cit.get("reportId", "")
            title = cit.get("reportTitle", "")
            date = cit.get("date", "")
            fac = cit.get("facility", "")
            excerpt = cit.get("excerpt", "")

            # If facility not populated in citation metadata, extract from excerpt header or known list
            if not fac and excerpt:
                first_line = excerpt.splitlines()[0] if excerpt.splitlines() else ""
                m_fac = re.search(r"-\s*([A-Za-z0-9\.\'\-]+(?:\s+[A-Za-z0-9\.\'\-]+){0,4})\s*$", first_line)
                if m_fac:
                    fac = m_fac.group(1).strip()
                else:
                    for kf in self._KNOWN_INSTITUTIONAL_FACILITIES:
                        if kf in excerpt.lower():
                            fac = kf
                            break

            # If date not populated in citation metadata, extract from excerpt
            if not date and excerpt:
                parsed_d = self._parse_full_dates(excerpt)
                if parsed_d:
                    pd = parsed_d[0]
                    date = f"{pd[0]:04d}-{pd[1]:02d}-{pd[2]:02d}"

            struct_line_re = re.compile(r'Test:\s*([^|]+)\s*\|\s*Value:\s*([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z0-9/%^]+)?', re.I)
            for line in excerpt.splitlines():
                line = line.strip()
                if not line:
                    continue
                m_st = struct_line_re.search(line)
                if m_st:
                    analyte = m_st.group(1).strip().lower()
                    val = m_st.group(2).strip()
                    unit = m_st.group(3).strip() if m_st.group(3) else ''
                    if not any(f['report_id'] == cid and f['analyte'] == analyte and f['value'] == val for f in facts):
                        facts.append({
                            'analyte': analyte,
                            'value': val,
                            'unit': unit,
                            'ref_range': None,
                            'flag': '',
                            'report_id': cid,
                            'report_title': title,
                            'date': date,
                            'facility': fac
                        })
                m = lab_line_re.search(line)
                if m:
                    analyte = m.group(1).strip().lower()
                    val = m.group(2).strip()
                    unit = m.group(3).strip() if m.group(3) else ""
                    flag = m.group(4) if m.group(4) else ""
                    ref = (m.group(5), m.group(6)) if m.group(5) else None
                    if analyte not in ["comprehensive metabolic panel", "complete blood count", "outpatient fasting glucose", "diagnostic endocrinology panel"]:
                        facts.append({
                            "analyte": analyte,
                            "value": val,
                            "unit": unit,
                            "ref_range": ref,
                            "flag": flag,
                            "report_id": cid,
                            "report_title": title,
                            "date": date,
                            "facility": fac
                        })

            # Markdown table extraction (e.g. |Test Name|Result|Units|... or multi-row cells with <br>)
            for line in excerpt.splitlines():
                line = line.strip()
                if line.startswith('|'):
                    parts = [p.strip() for p in line.strip('|').split('|')]
                    if len(parts) >= 2 and not all(c in '-: ' for c in parts[0]):
                        if not any(hw in parts[0].lower() for hw in ['test name', 'analyte', 'component', 'test', 'parameter']):
                            tests = [t.strip().lower() for t in re.split(r'<br\s*/?>', parts[0], flags=re.I)]
                            vals = [v.strip() for v in re.split(r'<br\s*/?>', parts[1], flags=re.I)]
                            units = [u.strip() for u in re.split(r'<br\s*/?>', parts[2], flags=re.I)] if len(parts) >= 3 else []
                            if len(tests) == len(vals):
                                for i in range(len(tests)):
                                    t_an = tests[i]
                                    v_val = vals[i]
                                    u_unit = units[i] if i < len(units) else ''
                                    if re.match(r'^[0-9]+(?:\.[0-9]+)?$', v_val) and not any(f['report_id'] == cid and f['analyte'] == t_an and f['value'] == v_val for f in facts):
                                        facts.append({
                                            'analyte': t_an,
                                            'value': v_val,
                                            'unit': u_unit,
                                            'ref_range': None,
                                            'flag': '',
                                            'report_id': cid,
                                            'report_title': title,
                                            'date': date,
                                            'facility': fac
                                        })

            for m in free_re.finditer(excerpt):
                analyte = m.group(1).strip().lower()
                val = m.group(2).strip()
                unit = m.group(3).strip() if m.group(3) else ""
                if not any(f["report_id"] == cid and f["analyte"] == analyte and f["value"] == val for f in facts):
                    facts.append({
                        "analyte": analyte,
                        "value": val,
                        "unit": unit,
                        "ref_range": None,
                        "flag": "",
                        "report_id": cid,
                        "report_title": title,
                        "date": date,
                        "facility": fac
                    })

        return facts

    def _reconcile_and_ground_answer(
        self,
        answer: str,
        citations: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Reconciles the answer text with verified clinical facts and validates citations.
        - Resolves false source attribution by replacing falsely named reports with the true source.
        - Enforces exact analyte, value, unit, full date, and facility agreement.
        - Qualifies or abstains from unsupported claims in mixed answers.
        """
        import re

        if not answer or not citations:
            return answer, []

        if self._answer_indicates_missing_data(answer):
            return answer, []

        if answer.startswith("[") and ("Error" in answer or "Timeout" in answer or "Unavailable" in answer):
            return answer, []

        all_facts = self._extract_clinical_facts_from_citations(citations)
        citations_by_id = {cit.get("reportId"): cit for cit in citations}
        cand_facilities = {self._normalize_facility(c.get("facility")) for c in citations if c.get("facility")}

        # Split into sentences and decompose compound sentences joining supported facts with ungrounded claims
        raw_sentences = []
        for s in re.split(r"(?<=[.!?])\s+|;\s*", answer):
            s = s.strip()
            if not s:
                continue
            subparts = re.split(
                r"(?<=,)\s+(?:and\s+you|and\s+the\s+patient|and\s+were|and\s+was|and\s+have|and\s+has|and\s+should|but\s+you|but\s+the\s+patient)\s+",
                s,
                flags=re.I
            )
            if len(subparts) > 1:
                p0 = subparts[0].rstrip(",").strip()
                if p0:
                    raw_sentences.append(p0 + ".")
                for sp in subparts[1:]:
                    sp_clean = sp.rstrip(".!?").strip()
                    if sp_clean:
                        if not sp_clean.lower().startswith(("you", "the patient", "patient")):
                            sp_clean = "You " + sp_clean
                        raw_sentences.append(sp_clean + ".")
            else:
                raw_sentences.append(s)

        reconciled_sentences = []
        grounded_citation_ids = set()

        for sent in raw_sentences:
            sent_lower = sent.lower()

            # Mask dates before extracting numbers so date components (e.g. day 12, month 10, year 2026)
            # do not falsely match lab values
            date_mask_pat = (
                r"\b(19\d\d|20\d\d)[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b|"
                r"\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](19\d\d|20\d\d)\b|"
                r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(?:0?[1-9]|[12]\d|3[01]),?\s+(?:19\d\d|20\d\d)\b"
            )
            s_no_dates = re.sub(date_mask_pat, " ", sent, flags=re.I)
            s_no_years = re.sub(r"\b(19\d\d|20\d\d)\b", " ", s_no_dates)

            words = re.findall(r"[a-zA-Z]{3,}", sent_lower)
            sent_entities = {w for w in words if w not in self._GENERIC_GROUNDING_STOPWORDS}
            sent_nums = set(re.findall(r"\b(?:\d+\.\d+|\d+)\b", s_no_years))
            sent_full_dates = self._parse_full_dates(sent)
            sent_years = set(re.findall(r"\b(19\d\d|20\d\d)\b", sent))
            sent_facilities = self._extract_facilities_from_sentence(sent, cand_facilities)

            # Tokenize units in sentence to match exact units (e.g. 'mg/dl' vs 'mg')
            unit_tokens = re.findall(r"[a-z0-9%\^/]+", sent_lower)
            units_in_sent = [tok for tok in unit_tokens if tok in self._KNOWN_CLINICAL_UNITS]

            # Check for named sources in sentence
            named_sources = []
            for cit in citations:
                t = cit.get("reportTitle", "").lower()
                if t.startswith("lab: ") or t.startswith("rx: "):
                    continue
                for pfx in ["excerpt: ", "report: ", "allergy: ", "lab: "]:
                    if t.startswith(pfx):
                        t = t[len(pfx):]
                t_clean = t.split("(")[0].strip()
                m_page = re.search(r"\(p\.(\d+)\)", t)
                if m_page:
                    p_num = m_page.group(1)
                    if f"(p.{p_num})" in sent_lower or f"p.{p_num}" in sent_lower or f"page {p_num}" in sent_lower or t in sent_lower:
                        named_sources.append(cit)
                else:
                    if t_clean and len(t_clean) > 3 and (t_clean in sent_lower or t in sent_lower):
                        named_sources.append(cit)

            # Match facts against this sentence
            matched_facts = []
            for fact in all_facts:
                analyte_match = (fact["analyte"] in sent_lower) or any(w in sent_lower for w in fact["analyte"].split() if len(w) > 3)
                val_match = fact["value"] in sent_nums

                # Strict unit verification: missing, mismatch, exact, and controlled conversion
                fact_u = (fact.get("unit") or "").strip().lower()
                if fact_u:
                    if not units_in_sent:
                        # Required unit is missing in answer
                        unit_match = False
                    elif fact_u in units_in_sent:
                        unit_match = True
                    else:
                        # Controlled unit conversions
                        conv = False
                        for u in units_in_sent:
                            if (fact_u, u) in self._CONTROLLED_UNIT_CONVERSIONS:
                                factor = self._CONTROLLED_UNIT_CONVERSIONS[(fact_u, u)]
                                try:
                                    if any(abs(float(num) - (float(fact["value"]) * factor)) < 0.05 for num in sent_nums):
                                        conv = True
                                except ValueError:
                                    pass
                        unit_match = conv
                else:
                    unit_match = True

                # Ref range lower bound check: lower reference boundary must not ground measured claim
                is_ref_bound = False
                if fact.get("ref_range") and fact["value"] != fact["ref_range"][0]:
                    if fact["ref_range"][0] in sent_nums and fact["value"] not in sent_nums:
                        is_ref_bound = True

                # Exact full date and year verification
                date_conflict = False
                fact_full_dates = self._parse_full_dates(fact["date"])
                if sent_full_dates and fact_full_dates:
                    if not any(d in sent_full_dates for d in fact_full_dates):
                        date_conflict = True
                elif sent_years:
                    cit_years = set(re.findall(r"\b(19\d\d|20\d\d)\b", fact["date"]))
                    if cit_years and not sent_years.intersection(cit_years):
                        date_conflict = True

                # Facility verification (including unknown/unlisted facilities)
                fac_conflict = False
                f_fac = self._normalize_facility(fact.get("facility"))
                if sent_facilities and f_fac:
                    if not any(f_fac in sf or sf in f_fac for sf in sent_facilities):
                        fac_conflict = True

                if analyte_match and val_match and unit_match and not is_ref_bound and not date_conflict and not fac_conflict:
                    matched_facts.append(fact)

            if named_sources:
                unsupported_named = []
                for src in named_sources:
                    s_id = src.get("reportId", "")
                    if any(f["report_id"] == s_id for f in matched_facts):
                        grounded_citation_ids.add(s_id)
                    else:
                        unsupported_named.append(src)

                if unsupported_named:
                    for src in unsupported_named:
                        named_title = src.get("reportTitle", "")
                        orphaned_facts = [f for f in matched_facts if f["report_id"] not in [ns.get("reportId") for ns in named_sources]]
                        if orphaned_facts:
                            true_fact = orphaned_facts[0]
                            true_title = true_fact["report_title"]
                            true_id = true_fact["report_id"]

                            clean_named_title = named_title
                            for pfx in ["Excerpt: ", "Report: ", "Allergy: ", "Lab: "]:
                                if clean_named_title.startswith(pfx):
                                    clean_named_title = clean_named_title[len(pfx):]
                            clean_named_title = clean_named_title.split("(")[0].strip()

                            clean_true_title = true_title
                            for pfx in ["Excerpt: ", "Report: ", "Allergy: ", "Lab: "]:
                                if clean_true_title.startswith(pfx):
                                    clean_true_title = clean_true_title[len(pfx):]
                            clean_true_title = clean_true_title.split("(")[0].strip()

                            c_named = named_title
                            for pfx in ["Excerpt: ", "Report: ", "Allergy: ", "Lab: "]:
                                if c_named.startswith(pfx):
                                    c_named = c_named[len(pfx):]
                            c_true = true_title
                            for pfx in ["Excerpt: ", "Report: ", "Allergy: ", "Lab: "]:
                                if c_true.startswith(pfx):
                                    c_true = c_true[len(pfx):]

                            if c_named.lower() in sent.lower():
                                sent = re.sub(re.escape(c_named), c_true, sent, flags=re.IGNORECASE)
                            else:
                                sent = re.sub(re.escape(clean_named_title), clean_true_title, sent, flags=re.IGNORECASE)
                            grounded_citation_ids.add(true_id)
                        else:
                            sent = f"The {named_title} does not report the specified clinical findings."
                reconciled_sentences.append(sent)
            else:
                if matched_facts:
                    for f in matched_facts:
                        grounded_citation_ids.add(f["report_id"])
                    reconciled_sentences.append(sent)
                else:
                    if sent_entities or sent_nums:
                        # Clean claim words to state exact absence without leaving affirmative claims
                        claim_words = [w for w in re.findall(r"[a-zA-Z]{3,}", sent.lower()) if w not in self._GENERIC_GROUNDING_STOPWORDS]
                        if sent_nums:
                            nums_str = " ".join(sorted(list(sent_nums)))
                            ents_str = " ".join(claim_words) if claim_words else ""
                            target_claim = f"{ents_str} {nums_str}".strip() if ents_str else nums_str
                        else:
                            target_claim = " ".join(claim_words) if claim_words else ", ".join(sorted(list(sent_entities)))
                        target_claim = target_claim or "the specified clinical findings"
                        reconciled_sentences.append(f"No clinical documentation of {target_claim} was found in the provided records.")
                    else:
                        reconciled_sentences.append(sent)

        reconciled_answer = " ".join(reconciled_sentences)
        final_citations = [citations_by_id[cid] for cid in grounded_citation_ids if cid in citations_by_id]

        return reconciled_answer, final_citations

    def _filter_grounded_citations(self, answer: str, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Application-side defense-in-depth: validates that returned citations are
        actually grounded in and referenced by the generated answer.
        """
        return self._reconcile_and_ground_answer(answer, citations)[1]

    def _audit_claim_grounding(self, answer: str, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sentence-level claim support auditor. Separates message-level citation relevance
        from sentence-level clinical claim verification.
        """
        import re
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
        supported = []
        unsupported = []

        ans_words = re.findall(r"[a-zA-Z]{3,}", answer.lower())
        all_entities = {w for w in ans_words if w not in self._GENERIC_GROUNDING_STOPWORDS}

        for s in sentences:
            s_cits = self._filter_grounded_citations(s, citations)
            s_words = re.findall(r"[a-zA-Z]{3,}", s.lower())
            s_entities = {w for w in s_words if w not in self._GENERIC_GROUNDING_STOPWORDS}
            if s_cits:
                supported.append({"text": s, "citations": [c.get("reportId") for c in s_cits]})
            elif s_entities:
                unsupported.append({"text": s, "unsupported_entities": list(s_entities)})
            else:
                supported.append({"text": s, "citations": []})

        return {
            "supported_sentences": supported,
            "unsupported_sentences": unsupported,
            "grounded_citations": self._filter_grounded_citations(answer, citations)
        }


