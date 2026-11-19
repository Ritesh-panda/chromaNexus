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
        "asthma": {
            "keywords": {
                "asthma", "pulmonary", "respiratory", "inhaler", "albuterol", "fluticasone",
                "advair", "bronchial", "wheezing", "j45.909"
            },
            "expansion": "asthma Moderate Persistent Asthma pulmonary respiratory Inhaler Fluticasone Advair",
            "intent": QueryIntent.MIXED_CLINICAL,
            "test_keywords": ["peak flow", "spirometry"],
            "med_keywords": ["fluticasone", "advair", "albuterol", "inhaler"]
        },
        "bronchitis": {
            "keywords": {
                "bronchitis", "acute bronchitis", "bronchial", "azithromycin", "z-pak", "cough"
            },
            "expansion": "acute bronchitis asthmatic bronchitis Azithromycin Z-Pak urgent care",
            "intent": QueryIntent.REPORT_CONTENT,
            "test_keywords": [],
            "med_keywords": ["azithromycin", "antibiotic"]
        },
        "diabetes": {
            "keywords": {
                "diabetes", "diabetic", "blood sugar", "sugar", "sugar level", "glucose", "a1c", "hba1c",
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

    RED_FLAG_PATTERNS = [
        r"\b(?:chest\s+pain|pain\s+in\s+(?:my\s+)?chest)\b",
        r"\b(?:heart\s+attack|cardiac\s+arrest)\b",
        r"\b(?:can(?:not|'t)\s+breathe|trouble\s+breathing|breathless(?:ness)?|difficulty\s+breathing|shortness\s+of\s+breath)\b",
        r"\b(?:stroke|facial\s+droop|slurred\s+speech|speech\s+is\s+slurred)\b",
        r"\b(?:severe\s+bleed(?:ing)?|hemorrhage|coughing\s+up\s+blood)\b",
        r"\b(?:unconscious(?:ness)?|passed\s+out|lost\s+consciousness|blacked\s+out)\b",
        r"\b(?:seizure|convulsion|fitting)\b",
        r"\b(?:anaphylax(?:is)?|severe\s+allergic\s+reaction)\b",
        r"\b(?:suicid\w*|kill\s+myself|end\s+my\s+life)\b",
        r"\b(?:crushing\s+(?:chest\s+)?pain)\b",
        # Multilingual Indic Emergency Patterns
        r"(?:ଛାତି.*(?:ବିନ୍ଧା|ଯନ୍ତ୍ରଣା|କଷ୍ଟ|ଦରଜ)|ନିଶ୍ୱାସ.*(?:କଷ୍ଟ|ବନ୍ଦ)|ହାର୍ଟ.*ଆଟାକ|ଚେତାଶୂନ୍ୟ|ଅଚେତ|ବେହୋସ|ପ୍ରଚୁର\s*ରକ୍ତ)",
        r"(?:सीने.*दर्द|छाती.*दर्द|सांस.*(?:तकलीफ|फूल|दिक्कत)|हार्ट.*अटैक|बेहोश|खून.*उल्टी|दौरा)",
        r"(?:বুকে.*ব্যথা|শ্বাস.*কষ্ট|হার্ট.*অ্যাটাক|অজ্ঞান|রক্তপাত)",
        r"(?:ఛాతీ.*నొప్పి|శ్వాస.*ఆడక|గుండెపోటు|స్పృహతప్ప)",
        r"(?:நெஞ்சு.*வலி|மூச்சு.*திணறல்|மாரடைப்பு|மயக்கம்)",
        r"\b(?:seene\s+mein\s+dard|saans\s+phool|heart\s+attack\s+lag\s+raha)\b"
    ]

    SYMPTOM_PATTERNS = [
        r"\b(?:i\s+am|i'm|i\s+feel|feeling)\s+(?:sick|unwell|ill|nauseous|dizzy|faint|weak|terrible|awful|poorly|down)\b",
        r"\b(?:i\s+have|i\s+got|having)\s+(?:a\s+)?(?:fever|headache|migraine|nausea|vomiting|vomit|diarrhea|cough|sore\s+throat|chills|cold|body\s+ache|fatigue|pain|stomach\s+ache|belly\s+pain|cramps|acid\s+reflux|heartburn)\b",
        r"\b(?:my\s+(?:head|stomach|throat|back|belly|body|joint|joints|eye|ear|muscle))\s+(?:hurts|aches|is\s+hurting|is\s+aching|is\s+burning|is\s+sore)\b",
        r"\b(?:throw(?:ing)?\s+up|vomit(?:ing)?)\b",
        r"\bfeeling\s+sick\b",
        r"\bam\s+sick\b",
        r"\bi\s+feel\s+like\s+vomiting\b",
        r"\bcatch(?:ing)?\s+a\s+cold\b",
        r"\bi\s+am\s+not\s+feeling\s+well\b",
        # Odia Symptom Expressions
        r"(?:ମୁଁ\s*ଅସୁସ୍ଥ|ଅସୁସ୍ଥ\s*ଅଛି|ଦେହ\s*ଖରାପ|ଭଲ\s*ଲାଗୁନି|ଜ୍ୱର|ମୁଣ୍ଡ\s*(?:ବିନ୍ଧା|ବୁଲା)|ବାନ୍ତି|ପେଟ\s*(?:କାଟୁଛି|ବିନ୍ଧା)|କାଶ|ଥଣ୍ଡା|ଦରଜ|ଦୁର୍ବଳ\s*ଲାଗୁଛି)",
        # Hindi Symptom Expressions
        r"(?:मैं\s*बीमार|तबीयत\s*(?:खराब|ठीक\s*नहीं)|अच्छा\s*नहीं\s*लग\s*रहा|बुखार|सिर\s*दर्द|सर\s*दर्द|उल्टी|चक्कर|पेट\s*दर्द|खांसी|जुकाम|कमजोरी\s*लग\s*रही)",
        # Bengali Symptom Expressions
        r"(?:আমি\s*অসুস্থ|শরীর\s*খারাপ|খারাপ\s*লাগছে|জ্বর|মাথা\s*ব্যথা|বমি|পেট\s*ব্যথা|কাশি|ঠান্ডা)",
        # Telugu Symptom Expressions
        r"(?:నాకు\s*అనారోగ్యం|ఒంట్లో\s*బాగాలేదు|జ్వరం|తలనెప్పి|వాంతులు|కడుపునొప్పి|దగ్గు|నీరసం)",
        # Tamil Symptom Expressions
        r"(?:உடம்பு\s*சரியில்லை|காய்ச்சல்|தலைவலி|வாந்தி|வயிற்று\s*வலி|இருமல்|சோர்வு)",
        # Transliterated Indic Symptoms
        r"\b(?:tabiyat\s+kharab|bimar\s+hoon|bukhar\s+hai|sar\s+dard\s+hai|chakkar\s+aa\s+rahe|deho\s+kharap|asustha\s+achhi)\b"
    ]

    GENERAL_CONVERSATION_PATTERNS = [
        # Friendly Greetings & Wellness Check-Ins (Patient conversational chit-chat)
        r"\b(?:i\s+am|i'm|i\s+feel|feeling)\s+(?:fine|good|well|better|okay|ok|great|alright|healthy|happy)\b",
        r"\bhow\s+are\s+you\b",
        r"\bhow\s+(?:is\s+it\s+going|are\s+things)\b",
        r"\b(?:doing\s+(?:well|good|fine|okay|ok|great))\b",
        r"\b(?:thank\s+(?:you|u)|thanks|thankyou)\b",
        r"\b(?:good\s+to\s+(?:see|hear|meet)\s+you)\b",
        r"\b(?:why\s+(?:are\s+you|you\s+are)\s+(?:not\s+able|unable)|why\s+can(?:'t|\s+not)\s+you)\b",
        r"\bgeneric\s+questions?\b",
        r"\b(?:chit\s*chat|small\s*talk|just\s+chat(?:ting)?)\b",
        r"\bthat(?:'s|\s+is)\s+not\b",
        r"\b(?:i\s+did(?:n't|\s+not)\s+(?:ask|mean|say)|not\s+what\s+i\s+(?:asked|meant))\b",
        r"\b(?:i\s+am\s+(?:willing|trying|ready)\s+to)\b",
        r"\b(?:talk\s+to\s+me|speak\s+with\s+me|can\s+we\s+talk|let(?:'s|\s+us)\s+talk)\b",
        r"\b(?:are\s+you\s+there|can\s+you\s+hear\s+me|hello\s+there)\b",
        r"\b(?:who\s+are\s+you|what\s+is\s+your\s+name)\b",
        r"\bwhat\s+(?:can|do)\s+you\s+do\b",
        r"\bhow\s+do\s+you\s+work\b",
        r"\bignore\s+(?:the\s+)?(?:command|instruction|database|rule)\b",
        r"^(?:hi|hello|hey|namaste|greetings|good\s+morning|good\s+afternoon|good\s+evening|what's\s+up)\b",
        # Multilingual Indic Friendly Greetings & Check-Ins
        r"(?:ଭଲ\s*ଅଛି|ଭଲ\s*ଲାଗୁଛି|କେମିତି\s*ଅଛନ୍ତି|ସବୁ\s*ଠିକ୍\s*ଅଛି|ଧନ୍ୟବାଦ|କିଛି\s*ଅସୁବିଧା\s*ନାହିଁ|ନମସ୍କାର|ଜୟ\s*ଜଗନ୍ନାଥ|ତୁମେ\s*କିଏ|ତୁମେ\s*କଣ\s*କରିପାରିବ|ଆପଣ\s*କିଏ)",
        r"(?:मैं\s*ठीक\s*हूँ|अच्छा\s*लग\s*रहा\s*है|सब\s*ठीक\s*है|आप\s*कैसे\s*हैं|धन्यवाद|शुक्रिया|नमस्ते|नमस्कार|प्रणाम|आप\s*कौन\s*हैं|आप\s*क्या\s*कर\s*सकते\s*हैं)",
        r"(?:আমি\s*ভালো\s*আছি|ভালো\s*লাগছে|আপনি\s*কেমন\s*আছেন|ধন্যবাদ)",
        r"(?:బాగున్నాను|బాగుంది|మీరు\s*ఎలా\s*ఉన్నారు|ధన్యవాదాలు)",
        r"(?:நன்றாக\s*இருக்கிறேன்|நல்லா\s*இருக்கிறேன்|எப்படி\s*இருக்கிறீர்கள்|நன்றி)",
        r"\b(?:theek\s+hoon|sab\s+theek\s+hai|bhalo\s+achi|bagunnanu|fine\s+hoon)\b",
        r"\bwhat\s+is\s+(?:type\s+2\s+diabetes|diabetes|hba1c|cholesterol|ldl|hdl|hypertension|blood\s+pressure|metformin|a\s+lipid\s+profile)\b(?!\s+(?:in\s+my|for\s+me|my\s+level|my\s+reading|my\s+result|my\s+report))",
        r"\bhow\s+does\s+(?:metformin|a\s+statin|atorvastatin|insulin|blood\s+sugar\s+medication)\s+work\b",
        r"\btell\s+me\s+about\s+(?:metformin|diabetes|cholesterol|hyperlipidemia)\b(?!\s+(?:in\s+my|from\s+my|my\s+level|my\s+reading|my\s+report))"
    ]

    def resolve(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        language: Optional[str] = "en"
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

        # 2. Critical Safety Interceptor: Check for life-threatening Red Flags / Emergency
        for pat in self.RED_FLAG_PATTERNS:
            if re.search(pat, lower_query, re.IGNORECASE):
                return ResolvedQuery(
                    original_query=clean_query,
                    resolved_query=clean_query,
                    active_topic="emergency",
                    is_follow_up=False,
                    is_overview=False,
                    intent=QueryIntent.EMERGENCY,
                    keywords=["emergency", "critical", "immediate", "108"],
                    formatted_history=formatted_history
                )

        # 3. Clinical Symptom Presentation / Triage
        for pat in self.SYMPTOM_PATTERNS:
            if re.search(pat, lower_query, re.IGNORECASE):
                return ResolvedQuery(
                    original_query=clean_query,
                    resolved_query=clean_query,
                    active_topic="symptom_triage",
                    is_follow_up=False,
                    is_overview=False,
                    intent=QueryIntent.SYMPTOM_TRIAGE,
                    keywords=["symptom", "triage", "illness", "feeling", "sick"],
                    formatted_history=formatted_history
                )

        # Check if the query contains a specific clinical topic or overview request
        detected_topic = self._detect_topic(lower_query)
        is_overview = self._is_overview_query(lower_query)

        # 4. Meta questions, system capabilities, greetings, & general medical education
        # Only route to GENERAL_CONVERSATION if there is NO clinical topic or overview requested!
        if not detected_topic and not is_overview:
            for pat in self.GENERAL_CONVERSATION_PATTERNS:
                if re.search(pat, lower_query, re.IGNORECASE):
                    return ResolvedQuery(
                        original_query=clean_query,
                        resolved_query=clean_query,
                        active_topic="general_conversation",
                        is_follow_up=False,
                        is_overview=False,
                        intent=QueryIntent.GENERAL_CONVERSATION,
                        keywords=["general", "knowledge", "conversation"],
                        formatted_history=formatted_history
                    )

        # 5. Check for broad health status / overview questions
        if is_overview:
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

        # 7. Multilingual Fallback: If query contains Indic / Non-ASCII text or explicit non-English language
        # and has no explicit documented medical analyte, route to SYMPTOM_TRIAGE or GENERAL_CONVERSATION
        # so it is not erroneously rejected by extractive English document verification.
        is_indic_text = any(ord(c) > 127 for c in clean_query)
        if is_indic_text or (language and str(language).lower()[:2] != "en"):
            return ResolvedQuery(
                original_query=clean_query,
                resolved_query=clean_query,
                active_topic="symptom_triage",
                is_follow_up=False,
                is_overview=False,
                intent=QueryIntent.SYMPTOM_TRIAGE,
                keywords=["symptom", "triage", "illness", "multilingual"],
                formatted_history=formatted_history
            )

        # 8. Default standalone query
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
