import re
from typing import Optional, Tuple
from backend.app.clinical.terminology.biomarkers import resolve_biomarker, BIOMARKER_CATALOG
from backend.app.clinical.structured_query.models import (
    StructuredQueryType,
    StructuredQueryIntent,
    TimeWindow,
)


class StructuredQueryDetector:
    """
    Deterministic clinical query intent and parameter extractor for ChronaNexus Phase 5.
    Identifies structured question types (latest, previous vs latest, trend, multi-analyte,
    comparisons, reference range checks) and resolves canonical biomarker definitions.
    """

    TIME_WINDOW_PATTERNS = [
        (r"\b(?:last|past)\s+(?:six|6)\s+months?\b", 180, "six months"),
        (r"\b(?:last|past)\s+(?:three|3)\s+months?\b", 90, "three months"),
        (r"\b(?:last|past)\s+(?:one|1)?\s*year\b", 365, "one year"),
        (r"\b(?:last|past)\s+12\s+months?\b", 365, "12 months"),
        (r"\b(?:last|past)\s+30\s+days?\b", 30, "30 days"),
        (r"\bin\s+(202[0-9])\b", None, None),  # specific year
    ]

    COMMON_ANALYTE_ALIASES = {
        "sugar": "glucose",
        "blood sugar": "glucose",
        "fasting sugar": "glucose",
        "fasting blood glucose": "glucose",
        "fasting glucose": "glucose",
        "fbg": "glucose",
        "a1c": "hba1c",
        "hb a1c": "hba1c",
        "hemoglobin a1c": "hba1c",
        "hgb": "hemoglobin",
        "hb": "hemoglobin",
        "k": "potassium",
        "k+": "potassium",
        "serum potassium": "potassium",
        "na": "sodium",
        "na+": "sodium",
        "serum sodium": "sodium",
        "cholesterol": "cholesterol",
        "total cholesterol": "cholesterol",
        "lipids": "cholesterol",
        "lipid profile": "cholesterol",
        "creatinine": "creatinine",
        "serum creatinine": "creatinine",
        "tsh": "tsh",
        "thyroid": "tsh",
        "alt": "alt",
        "ast": "ast",
        "platelets": "platelet",
        "platelet": "platelet",
        "wbc": "wbc",
        "white blood cells": "wbc",
        "rbc": "rbc",
        "red blood cells": "rbc",
        "bun": "bun",
        "egfr": "egfr",
        "ferritin": "ferritin",
        "calcium": "calcium",
        "triglycerides": "triglycerides",
        "troponin": "troponin",
        "uric acid": "uric acid",
        "uric": "uric acid",
    }

    def detect(self, query: str) -> StructuredQueryIntent:
        if not query or not query.strip():
            return StructuredQueryIntent(is_structured_query=False, raw_query=query or "")

        q = query.strip()
        q_lower = q.lower()

        # 1. Multi-analyte queries ("Which of my recorded lab values have increased/decreased?")
        if re.search(r"\bwhich\s+(?:of\s+my\s+)?(?:recorded\s+)?(?:lab\s+)?(?:values|results|tests)\s+(?:have\s+)?(?:increased|risen|gone\s+up)\b", q_lower):
            return StructuredQueryIntent(
                is_structured_query=True,
                query_type=StructuredQueryType.ALL_INCREASING,
                is_multi_analyte=True,
                raw_query=q
            )
        if re.search(r"\bwhich\s+(?:of\s+my\s+)?(?:recorded\s+)?(?:lab\s+)?(?:values|results|tests)\s+(?:have\s+)?(?:decreased|dropped|fallen|gone\s+down)\b", q_lower):
            return StructuredQueryIntent(
                is_structured_query=True,
                query_type=StructuredQueryType.ALL_DECREASING,
                is_multi_analyte=True,
                raw_query=q
            )

        # 2. Extract Time Window (if present)
        time_window = self._extract_time_window(q_lower)

        # 3. Determine Query Type
        query_type = self._determine_query_type(q_lower, time_window)

        # 4. Extract Analyte Target
        analyte_term, canonical_name, loinc_code = self._extract_analyte(q_lower)

        # Check if generic latest/previous inquiry without explicit analyte (e.g. 'Show my latest result alongside the previous result')
        is_generic_latest = bool(
            query_type in [StructuredQueryType.PREVIOUS_AND_LATEST, StructuredQueryType.LATEST_VALUE, StructuredQueryType.REFERENCE_RANGE_COMPARISON] and
            re.search(r"\b(?:latest|recent|previous|prior)\s+(?:lab|test|reading|result|value)\b", q_lower)
        )

        if not analyte_term and not is_generic_latest:
            return StructuredQueryIntent(is_structured_query=False, raw_query=q)

        return StructuredQueryIntent(
            is_structured_query=True,
            query_type=query_type,
            analyte_term=analyte_term,
            canonical_name=canonical_name,
            loinc_code=loinc_code,
            time_window=time_window,
            is_multi_analyte=False,
            is_generic_latest=is_generic_latest,
            raw_query=q
        )

    def _extract_analyte(self, q_lower: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        # First check explicit multi-word aliases
        for alias, target in sorted(self.COMMON_ANALYTE_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, q_lower):
                defn = resolve_biomarker(target) or resolve_biomarker(alias)
                if defn:
                    return alias, defn.canonical_name, defn.loinc_code
                return alias, alias.capitalize(), None

        # Check biomarker catalog synonyms
        for key, defn in BIOMARKER_CATALOG.items():
            for syn in defn.synonyms:
                pattern = r"\b" + re.escape(syn.lower()) + r"\b"
                if re.search(pattern, q_lower):
                    return syn, defn.canonical_name, defn.loinc_code

        # Check clinical inquiry patterns: "my <analyte> level/result/reading"
        analyte_match = re.search(r"(?:what(?:'s| is| was)?|show|get|tell me about|check)\s+(?:my\s+)?([a-z0-9\-\s]{2,30}?)\s+(?:level|result|value|reading|test|lab)", q_lower)
        if analyte_match:
            raw_cand = analyte_match.group(1).strip()
            cand = re.sub(r"^(?:latest|recent|previous|prior|most\s+recent|last)\s+", "", raw_cand).strip()
            stop_words = {"most recent", "latest", "last", "previous", "prior", "first"}
            if cand not in stop_words and len(cand) >= 3:
                defn = resolve_biomarker(cand)
                if defn:
                    return cand, defn.canonical_name, defn.loinc_code
                return cand, cand.title(), None

        # Fallback check via resolve_biomarker token matching
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\+]+\b", q_lower)
        for t in tokens:
            if len(t) >= 3 and t not in ["what", "when", "where", "how", "show", "tell", "give", "with", "from", "over", "last", "past"]:
                defn = resolve_biomarker(t)
                if defn:
                    return t, defn.canonical_name, defn.loinc_code

        return None, None, None

    def _extract_time_window(self, q_lower: str) -> Optional[TimeWindow]:
        for pattern, days, descriptor in self.TIME_WINDOW_PATTERNS:
            m = re.search(pattern, q_lower)
            if m:
                if days is not None:
                    return TimeWindow(days=days, descriptor=descriptor)
                else:
                    year = m.group(1)
                    return TimeWindow(
                        start_date=f"{year}-01-01",
                        end_date=f"{year}-12-31",
                        descriptor=year
                    )
        return None

    def _determine_query_type(self, q_lower: str, time_window: Optional[TimeWindow]) -> StructuredQueryType:
                # Extremum queries (highest / lowest)
        if re.search(r"\b(?:highest|peak|maximum|max)\b", q_lower) and not re.search(r"\bhigher\s+or\s+lower\b", q_lower):
            return StructuredQueryType.HIGHEST_VALUE
        if re.search(r"\b(?:lowest|minimum|min)\b", q_lower):
            return StructuredQueryType.LOWEST_VALUE

        # Comparison across facilities or reports
        if re.search(r"\b(?:across|between)\s+(?:facilities|dates|hospitals|reports|labs)\b", q_lower) or \
           re.search(r"\b(?:compare|discrepanc(?:y|ies))\b", q_lower):
            return StructuredQueryType.COMPARISON_ACROSS_SOURCES

        # Previous alongside/versus latest
        if re.search(r"\b(?:previous|prior)\s+(?:result\s+)?(?:alongside|vs|versus|and|compared\s+to)\s+(?:the\s+)?latest\b", q_lower) or \
           re.search(r"\blatest\s+(?:result\s+)?alongside\s+(?:the\s+)?previous\b", q_lower) or \
           re.search(r"\balongside\s+(?:the\s+)?previous\b", q_lower) or \
           re.search(r"\bcompare\s+(?:my\s+)?(?:latest|previous)\b", q_lower):
            return StructuredQueryType.PREVIOUS_AND_LATEST

        # Reference range check
        if re.search(r"\b(?:reference\s+range|normal\s+range|within\s+range|in\s+range)\b", q_lower):
            return StructuredQueryType.REFERENCE_RANGE_COMPARISON

        # Direction of change / Trend / History
        if time_window is not None:
            return StructuredQueryType.MEASUREMENT_HISTORY

        if re.search(r"\b(?:how\s+has\s+my|how\s+have\s+my|changed|change|increasing|decreasing|trend|trajectory|higher\s+or\s+lower)\b", q_lower):
            return StructuredQueryType.DIRECTION_OF_CHANGE

        if re.search(r"\b(?:history|over\s+time|all\s+recorded|all\s+results)\b", q_lower):
            return StructuredQueryType.MEASUREMENT_HISTORY

        # Default to latest value
        return StructuredQueryType.LATEST_VALUE
