import re
import logging
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from backend.app.ai.rag.classifier import QueryIntent

logger = logging.getLogger(__name__)


class ResolvedQuery(BaseModel):
    """
    Structured outcome of resolving a clinical query within conversation context.
    Determines query meaning, active medical topic, clinical search keywords, and formatted history.
    """
    original_query: str
    resolved_query: str
    active_topic: Optional[str] = None
    is_follow_up: bool = False
    is_overview: bool = False
    intent: QueryIntent = QueryIntent.GENERAL_DOCUMENT_QUERY
    keywords: List[str] = Field(default_factory=list)
    formatted_history: str = ""


class ConversationQueryResolver:
    """
    General, deterministic conversation-aware query resolver for ChronaNexus.
    Resolves pronouns, topic continuations, comparisons, and elliptical references
    across recent conversation turns WITHOUT requiring an extra LLM call.
    """

    TAXONOMY: Dict[str, Dict[str, Any]] = {
        "diabetes": {
            "keywords": {
                "diabetes", "diabetic", "blood sugar", "glucose", "a1c", "hba1c",
                "glycemic", "metformin", "insulin", "e11.9"
            },
            "expansion": "diabetes Type 2 Diabetes Mellitus HbA1c blood glucose Metformin glycemic",
            "intent": QueryIntent.MIXED_CLINICAL,
            "test_keywords": ["hba1c", "glucose", "a1c", "blood sugar"],
            "med_keywords": ["metformin"]
        },
        "cholesterol": {
            "keywords": {
                "cholesterol", "lipid", "lipids", "triglyceride", "triglycerides",
                "ldl", "hdl", "statin", "atorvastatin", "hyperlipidemia", "e78.5"
            },
            "expansion": "cholesterol Total Cholesterol lipid panel LDL hyperlipidemia Atorvastatin Calcium",
            "intent": QueryIntent.LAB_HISTORY,
            "test_keywords": ["cholesterol", "lipid", "triglycerides", "ldl", "hdl"],
            "med_keywords": ["atorvastatin", "statin"]
        },
        "hypertension": {
            "keywords": {
                "hypertension", "blood pressure", "bp", "lisinopril", "systolic",
                "diastolic", "i10"
            },
            "expansion": "essential primary hypertension blood pressure Lisinopril cardiovascular",
            "intent": QueryIntent.MEDICATION_HISTORY,
            "test_keywords": [],
            "med_keywords": ["lisinopril"]
        },
        "knee": {
            "keywords": {
                "knee", "meniscus", "tear", "joint", "patella", "ligament",
                "acl", "pcl", "mcl"
            },
            "expansion": "right knee joint MRI medial meniscus strain displaced tear findings impression",
            "intent": QueryIntent.REPORT_CONTENT,
            "test_keywords": [],
            "med_keywords": []
        },
        "kidney": {
            "keywords": {
                "kidney", "kidneys", "renal", "creatinine", "egfr", "nephro"
            },
            "expansion": "serum creatinine egfr renal kidney function",
            "intent": QueryIntent.LAB_HISTORY,
            "test_keywords": ["creatinine", "egfr"],
            "med_keywords": []
        },
        "heart": {
            "keywords": {
                "heart", "cardio", "cardiovascular", "echo", "echocardiogram",
                "ejection fraction", "lvef"
            },
            "expansion": "echocardiogram 2D cardiovascular evaluation lvef normal systolic function",
            "intent": QueryIntent.REPORT_CONTENT,
            "test_keywords": [],
            "med_keywords": []
        },
        "dengue": {
            "keywords": {
                "dengue", "thrombocytopenia", "platelet", "platelets"
            },
            "expansion": "dengue fever platelet count recovery inpatient hospital encounter",
            "intent": QueryIntent.TIMELINE,
            "test_keywords": ["platelet", "platelets"],
            "med_keywords": []
        },
        "vitamin_d": {
            "keywords": {
                "vitamin d", "vit d", "cholecalciferol"
            },
            "expansion": "25-hydroxy vitamin d cholecalciferol deficiency",
            "intent": QueryIntent.LAB_HISTORY,
            "test_keywords": ["vitamin d", "25-hydroxy"],
            "med_keywords": ["cholecalciferol"]
        },
        "medications": {
            "keywords": {
                "medication", "medications", "medicine", "medicines", "drug",
                "drugs", "prescription", "prescriptions", "pills", "dose", "dosage", "taking"
            },
            "expansion": "active prescribed medications dosages frequency Lisinopril Metformin Atorvastatin",
            "intent": QueryIntent.MEDICATION_HISTORY,
            "test_keywords": [],
            "med_keywords": []
        },
        "labs": {
            "keywords": {
                "lab", "labs", "test", "tests", "panel", "blood test", "blood report",
                "reading", "readings", "level", "levels"
            },
            "expansion": "laboratory results metabolic lipid panel HbA1c glucose cholesterol creatinine",
            "intent": QueryIntent.LAB_HISTORY,
            "test_keywords": [],
            "med_keywords": []
        }
    }

    OVERVIEW_PATTERNS: List[str] = [
        r"\bhealth status\b",
        r"\bhow am i\b",
        r"\boverall health\b",
        r"\brecent health\b",
        r"\boverall summary\b",
        r"\bcurrent health\b",
        r"\bgeneral health\b",
        r"\bsummary of my health\b",
        r"\bimportant things about my current health\b",
        r"\bimportant things about my health\b",
        r"\bhow am i right now\b",
        r"\bstate of my health\b",
        r"\bstatus of my health\b",
        r"\baccording to my reports\b"
    ]

    PRONOUNS: Set[str] = {"it", "its", "that", "this", "they", "them", "these", "those"}
    COMPARISONS: Set[str] = {
        "improved", "improving", "improvement", "better", "worse", "worsened",
        "changed", "change", "progress", "progressed", "trend", "trajectory",
        "compare", "comparison", "difference", "stable", "stabilized"
    }

    def resolve(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ResolvedQuery:
        if not query or not query.strip():
            return ResolvedQuery(
                original_query="",
                resolved_query="",
                active_topic=None,
                is_follow_up=False,
                is_overview=False,
                intent=QueryIntent.GENERAL_DOCUMENT_QUERY,
                keywords=[],
                formatted_history=""
            )

        clean_query = query.strip()
        lower_query = clean_query.lower()
        history = conversation_history or []

        # 1. Format bounded recent history string (last 6 messages = 3 full turns)
        formatted_history = self._format_history(history)

        # 2. Check for broad health status / overview questions
        if self._is_overview_query(lower_query):
            return ResolvedQuery(
                original_query=clean_query,
                resolved_query=clean_query,
                active_topic="health_overview",
                is_follow_up=False,
                is_overview=True,
                intent=QueryIntent.MIXED_CLINICAL,
                keywords=["health", "status", "summary", "overview"],
                formatted_history=formatted_history
            )

        words = set(re.findall(r"\b[a-z0-9\-]+\b", lower_query))
        has_pronoun = bool(words.intersection(self.PRONOUNS))
        has_comp = bool(words.intersection(self.COMPARISONS))

        # Check for imaging/scan reference without explicit body part (e.g., "Does the MRI mention...")
        has_imaging_word = any(w in lower_query for w in ["mri", "scan", "imaging", "x-ray", "ct", "ultrasound", "echo"])
        has_body_part = any(w in lower_query for w in ["knee", "chest", "brain", "head", "abdomen", "shoulder", "spine", "heart"])
        is_elliptical_imaging = has_imaging_word and not has_body_part

        # 3. Detect if current query explicitly mentions a clinical domain from taxonomy
        current_topic = self._detect_topic(lower_query)

        # 4. Handle imaging follow-up where anatomical site was in prior turns
        if is_elliptical_imaging:
            for h in reversed(history):
                h_text = h.get("text", "").lower()
                prior_topic = self._detect_topic(h_text)
                if prior_topic and prior_topic in ["knee", "heart", "kidney"]:
                    tax_info = self.TAXONOMY[prior_topic]
                    resolved_text = f"{prior_topic} {clean_query} {tax_info['expansion']}"
                    keywords = list(tax_info["keywords"].union({"mri", "tear", "findings"}))
                    return ResolvedQuery(
                        original_query=clean_query,
                        resolved_query=resolved_text,
                        active_topic=prior_topic,
                        is_follow_up=True,
                        is_overview=False,
                        intent=tax_info["intent"],
                        keywords=keywords,
                        formatted_history=formatted_history
                    )

        # 5. Handle pronoun / comparison follow-ups that lack an explicit clinical topic
        # e.g., "Has it improved?", "Has that improved?", "Is it normal?"
        if (has_pronoun or has_comp) and not current_topic:
            prior_topic = self._find_prior_topic(history)
            if prior_topic:
                tax_info = self.TAXONOMY[prior_topic]
                if has_comp:
                    resolved_text = f"{prior_topic} {clean_query} trend trajectory history previous latest {tax_info['expansion']}"
                    keywords = list(tax_info["keywords"].union({"improved", "trend", "level", "value"}))
                else:
                    resolved_text = f"{prior_topic} {clean_query} {tax_info['expansion']}"
                    keywords = list(tax_info["keywords"])

                return ResolvedQuery(
                    original_query=clean_query,
                    resolved_query=resolved_text,
                    active_topic=prior_topic,
                    is_follow_up=True,
                    is_overview=False,
                    intent=tax_info["intent"],
                    keywords=keywords,
                    formatted_history=formatted_history
                )

        # 6. Query has an explicit clinical topic (topic continuation or switch)
        # e.g., "What about my diabetes?", "What about my cholesterol?", "What about my knee?"
        if current_topic:
            tax_info = self.TAXONOMY[current_topic]
            resolved_text = f"{clean_query} {tax_info['expansion']}"
            keywords = list(tax_info["keywords"])
            is_follow_up = bool(history and any(w in lower_query for w in ["about", "and", "how", "what", "also"]))

            return ResolvedQuery(
                original_query=clean_query,
                resolved_query=resolved_text,
                active_topic=current_topic,
                is_follow_up=is_follow_up,
                is_overview=False,
                intent=tax_info["intent"],
                keywords=keywords,
                formatted_history=formatted_history
            )

        # 7. Default standalone query
        return ResolvedQuery(
            original_query=clean_query,
            resolved_query=clean_query,
            active_topic=None,
            is_follow_up=False,
            is_overview=False,
            intent=QueryIntent.GENERAL_DOCUMENT_QUERY,
            keywords=[],
            formatted_history=formatted_history
        )

    def _is_overview_query(self, lower_text: str) -> bool:
        for pat in self.OVERVIEW_PATTERNS:
            if re.search(pat, lower_text):
                return True
        return False

    def _detect_topic(self, lower_text: str) -> Optional[str]:
        """Identifies clinical topic domain present in text."""
        for topic, data in self.TAXONOMY.items():
            for kw in data["keywords"]:
                # Check for whole-word match or exact phrase
                if re.search(r"\b" + re.escape(kw) + r"\b", lower_text):
                    return topic
        return None

    def _find_prior_topic(self, history: List[Dict[str, str]]) -> Optional[str]:
        """
        Finds the most recent active clinical topic using a strict two-pass priority:

        Pass 1 — User messages only (highest priority).
            User questions are clean, direct, and single-topic. Scanning them first
            guarantees that the most-recently-discussed topic wins.
            Example: 'What about my cholesterol?' → topic = cholesterol, regardless
            of what AI responses said about other domains earlier.

        Pass 2 — AI response messages (fallback only).
            AI answers are verbose and frequently mention multiple medical domains
            in a single response. They are only consulted when no user message
            contains a detectable topic (e.g. all recent user messages were
            pure pronouns like 'Has it improved?').

        This two-pass approach fixes the regression where:
            'What about my cholesterol?' → 'Has that improved?'
        incorrectly resolved to the knee MRI topic because the AI's cholesterol
        answer happened to mention HbA1c or another domain term that matched
        'diabetes' (which precedes 'cholesterol' in taxonomy scan order).
        """
        if not history:
            return None

        EXCLUDED = {"medications", "labs"}

        # Pass 1: user messages only, most-recent first
        for msg in reversed(history):
            if msg.get("sender", "user").lower() != "user":
                continue
            text = msg.get("text", "").lower()
            topic = self._detect_topic(text)
            if topic and topic not in EXCLUDED:
                return topic

        # Pass 2: AI messages only, most-recent first (fallback)
        for msg in reversed(history):
            if msg.get("sender", "user").lower() == "user":
                continue
            text = msg.get("text", "").lower()
            topic = self._detect_topic(text)
            if topic and topic not in EXCLUDED:
                return topic

        return None

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Formats the last up to 6 messages into a concise dialogue transcript.

        Uses neutral Q:/A: role labels (not 'Patient:') so the LLM cannot
        accidentally echo the role prefix into the start of its answer.
        """
        if not history:
            return ""

        recent = history[-6:]
        lines = []
        for msg in recent:
            sender = msg.get("sender", "user").lower()
            role = "Q" if sender == "user" else "A"
            text = msg.get("text", "").strip()
            # Truncate past long assistant messages so prompt remains compact
            if len(text) > 300:
                text = text[:300] + "..."
            lines.append(f"{role}: {text}")

        return "\n".join(lines)
