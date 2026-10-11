import re
from enum import Enum
from typing import List, Set
from pydantic import BaseModel


class QueryIntent(str, Enum):
    LAB_HISTORY = "LAB_HISTORY"
    MEDICATION_HISTORY = "MEDICATION_HISTORY"
    DIAGNOSIS_HISTORY = "DIAGNOSIS_HISTORY"
    TIMELINE = "TIMELINE"
    REPORT_CONTENT = "REPORT_CONTENT"
    PROCEDURE_HISTORY = "PROCEDURE_HISTORY"
    MIXED_CLINICAL = "MIXED_CLINICAL"
    GENERAL_DOCUMENT_QUERY = "GENERAL_DOCUMENT_QUERY"


class ClassificationResult(BaseModel):
    primary_intent: QueryIntent
    intents: List[QueryIntent]
    is_hybrid_required: bool
    confidence: float
    keywords_matched: List[str]


class QueryClassifier:
    """
    Deterministic rule-based clinical query intent classifier.
    Analyzes medical terms, temporal references, and multi-facet questions
    to route retrieval to the optimal strategy (Structured DB, Semantic Vector, or Hybrid).
    """

    LAB_KEYWORDS: Set[str] = {
        "cholesterol", "lipid", "hba1c", "a1c", "glucose", "blood sugar", "creatinine",
        "egfr", "hemoglobin", "platelet", "platelets", "wbc", "rbc", "triglyceride",
        "triglycerides", "ldl", "hdl", "vitamin d", "thyroid", "tsh", "alt", "ast",
        "lab", "labs", "test", "tests", "panel", "blood test", "blood report", "value",
        "reading", "readings", "level", "levels", "highest", "lowest", "trend", "trajectory"
    }

    MEDICATION_KEYWORDS: Set[str] = {
        "medication", "medications", "medicine", "medicines", "drug", "drugs", "prescription",
        "prescriptions", "rx", "dose", "dosage", "frequency", "metformin", "lisinopril",
        "atorvastatin", "cholecalciferol", "insulin", "antibiotic", "statin", "taking",
        "prescribed", "mg", "bid", "qd", "daily", "pill", "pills"
    }

    DIAGNOSIS_KEYWORDS: Set[str] = {
        "diagnosis", "diagnoses", "diagnosed", "disease", "diseases", "condition", "conditions",
        "diabetes", "hypertension", "hyperlipidemia", "dengue", "illness", "icd", "chronic",
        "disorder", "syndrome"
    }

    TIMELINE_KEYWORDS: Set[str] = {
        "when", "date", "year", "years", "timeline", "history", "milestone", "milestones",
        "chronological", "event", "events", "first", "last", "latest", "recent", "ago",
        "started", "began", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"
    }

    REPORT_KEYWORDS: Set[str] = {
        "mri", "ct", "ct scan", "x-ray", "xray", "ultrasound", "scan", "imaging", "radiology",
        "meniscus", "knee", "joint", "ligament", "tear", "finding", "findings", "discharge",
        "summary", "consultation", "hospital", "st. jude", "metro general", "quest"
    }

    PROCEDURE_KEYWORDS: Set[str] = {
        "surgery", "surgeries", "procedure", "procedures", "operation", "operative",
        "hospitalized", "hospitalization", "admission", "admitted", "biopsy", "therapy"
    }

    # Health overview / status keywords — trigger full MIXED_CLINICAL retrieval
    HEALTH_OVERVIEW_KEYWORDS: Set[str] = {
        "health", "healthy", "status", "overall", "overview", "summary", "doing",
        "current", "right", "moment", "medical", "wellness", "wellbeing",
        "comprehensive", "complete", "everything", "general", "all",
        "according", "based", "tell", "report", "reports", "records", "give"
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

    def classify(self, query: str) -> ClassificationResult:
        if not query or not query.strip():
            return ClassificationResult(
                primary_intent=QueryIntent.GENERAL_DOCUMENT_QUERY,
                intents=[QueryIntent.GENERAL_DOCUMENT_QUERY],
                is_hybrid_required=False,
                confidence=0.5,
                keywords_matched=[]
            )

        lower = query.lower()
        words = set(re.findall(r"\b[a-z0-9\-]+\b", lower))

        # Check for broad health status / overview inquiry first
        is_overview = any(re.search(pat, lower) for pat in self.OVERVIEW_PATTERNS)
        if is_overview:
            matched_ov = words.intersection(self.HEALTH_OVERVIEW_KEYWORDS)
            return ClassificationResult(
                primary_intent=QueryIntent.MIXED_CLINICAL,
                intents=[QueryIntent.MIXED_CLINICAL],
                is_hybrid_required=True,
                confidence=0.95,
                keywords_matched=list(matched_ov) if matched_ov else ["health", "status"]
            )

        matched_lab = words.intersection(self.LAB_KEYWORDS)
        matched_med = words.intersection(self.MEDICATION_KEYWORDS)
        matched_diag = words.intersection(self.DIAGNOSIS_KEYWORDS)
        matched_time = words.intersection(self.TIMELINE_KEYWORDS)
        matched_report = words.intersection(self.REPORT_KEYWORDS)
        matched_proc = words.intersection(self.PROCEDURE_KEYWORDS)
        matched_health_overview = words.intersection(self.HEALTH_OVERVIEW_KEYWORDS)

        detected_intents: List[QueryIntent] = []
        all_matched_keywords: List[str] = []

        if matched_lab:
            detected_intents.append(QueryIntent.LAB_HISTORY)
            all_matched_keywords.extend(matched_lab)
        if matched_med:
            detected_intents.append(QueryIntent.MEDICATION_HISTORY)
            all_matched_keywords.extend(matched_med)
        if matched_diag:
            detected_intents.append(QueryIntent.DIAGNOSIS_HISTORY)
            all_matched_keywords.extend(matched_diag)
        if matched_time:
            detected_intents.append(QueryIntent.TIMELINE)
            all_matched_keywords.extend(matched_time)
        if matched_report:
            detected_intents.append(QueryIntent.REPORT_CONTENT)
            all_matched_keywords.extend(matched_report)
        if matched_proc:
            detected_intents.append(QueryIntent.PROCEDURE_HISTORY)
            all_matched_keywords.extend(matched_proc)

        # Multi-facet / Mixed detection
        is_hybrid = len(detected_intents) > 1 or (
            QueryIntent.REPORT_CONTENT in detected_intents and
            (QueryIntent.LAB_HISTORY in detected_intents or QueryIntent.MEDICATION_HISTORY in detected_intents)
        )

        if len(detected_intents) >= 2:
            primary_intent = QueryIntent.MIXED_CLINICAL
        elif len(detected_intents) == 1:
            primary_intent = detected_intents[0]
        elif matched_health_overview:
            primary_intent = QueryIntent.MIXED_CLINICAL
            detected_intents = [QueryIntent.MIXED_CLINICAL]
            all_matched_keywords.extend(matched_health_overview)
            is_hybrid = True
        else:
            primary_intent = QueryIntent.GENERAL_DOCUMENT_QUERY
            detected_intents = [QueryIntent.GENERAL_DOCUMENT_QUERY]

        confidence = 0.95 if all_matched_keywords else 0.60

        return ClassificationResult(
            primary_intent=primary_intent,
            intents=detected_intents,
            is_hybrid_required=is_hybrid or primary_intent == QueryIntent.MIXED_CLINICAL,
            confidence=confidence,
            keywords_matched=list(set(all_matched_keywords))
        )
