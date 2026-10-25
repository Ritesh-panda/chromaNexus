from typing import Optional
import re
from backend.app.ai.llm.base import LLMProvider


class MockDeterministicLLMProvider(LLMProvider):
    """
    Deterministic mock LLM provider for unit tests, offline demonstration, and CI/CD pipelines.
    Guarantees deterministic output without external network requests.
    """

    def __init__(self, name: str = "mock-deterministic"):
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2
    ) -> str:
        lower = prompt.lower()
        q_match = re.search(r"PATIENT QUESTION:\s*(.*?)(?:\n\s*INSTRUCTIONS:|$)", prompt, re.DOTALL | re.IGNORECASE)
        q_lower = q_match.group(1).lower() if q_match else lower

        if "extract all entities" in lower or "json output schema" in lower or "clinical report text" in lower:
            return '{"diseases": [{"name": "Asthma", "icd_code": "J45.909", "status": "active"}], "medications": [{"name": "Albuterol", "dosage": "90mcg", "frequency": "As needed", "route": "inhalation"}], "lab_results": [{"test_name": "Peak Flow", "value": "450", "unit": "L/min", "reference_range": ">400"}], "procedures": []}'
        elif "colonoscopy" in q_lower or "brain ct" in q_lower:
            return "Based on your verified medical records, no records or documentation were found regarding a colonoscopy or brain CT scan."
        elif "tsh" in q_lower or "thyroid" in q_lower or "endocrinology" in q_lower:
            return "According to your Endocrinology Follow-up report, your TSH level was 2.15 uIU/mL (Normal, Ref: 0.45-4.50 uIU/mL) and Free T4 was 1.2 ng/dL."
        elif "surgery" in q_lower or "surgeries" in q_lower or "operative" in q_lower or "operation" in q_lower:
            return "Based on your indexed records from 2019 to 2026, no surgical procedures or operative interventions were recorded. Your hospital admissions were medical management for Dengue Fever and conservative physical therapy for knee meniscus strain."
        elif "cholesterol" in q_lower or "lipid" in q_lower:
            if ("quest" in q_lower or re.search(r"\bwhere\b", q_lower)) and ("highest" not in q_lower and "peak" not in q_lower and "latest" not in q_lower):
                return "Your June 12, 2021 lipid profile was performed at Quest Diagnostics, showing Total Cholesterol of 242 mg/dL and Fasting Glucose of 104 mg/dL."
            if "highest" in q_lower or "peak" in q_lower or "max" in q_lower:
                return "Based on your clinical records, your highest recorded total cholesterol was 242 mg/dL on June 12, 2021 (Quest Diagnostics lipid panel). Through dietary intervention and initiation of Atorvastatin 10mg QD, your levels decreased to 198 mg/dL as of your June 15, 2026 panel."
            context_match = re.search(r"(?:Total Cholesterol|Cholesterol)[^\n\r]*?[:|]\s*(?:Value:\s*)?(\d{2,3})\s*mg/dL.*?Date:\s*([0-9\-]+)", prompt, re.IGNORECASE)
            if context_match:
                val, dt = context_match.group(1), context_match.group(2)
                if dt > "2026-06-15":
                    return f"Based on your latest medical report dated {dt}, your recorded Total Cholesterol is {val} mg/dL."
            return "Based on your clinical records, your highest recorded total cholesterol was 242 mg/dL on June 12, 2021 (Quest Diagnostics lipid panel). Through dietary intervention and initiation of Atorvastatin 10mg QD, your levels decreased to 198 mg/dL as of your June 15, 2026 panel."
        elif "hba1c" in q_lower or "diabetes" in q_lower or "metformin" in q_lower or "glucose" in q_lower:
            return "According to your indexed laboratory panels, your HbA1c trajectory showed an initial peak of 7.2% in September 2023 at Type 2 Diabetes diagnosis, improving to 6.7% in June 2026 under continuous Metformin 500mg BID therapy."
        elif "knee" in q_lower or "mri" in q_lower or "meniscus" in q_lower:
            return "Your Right Knee MRI from August 10, 2022 showed a Grade II signal alteration of the posterior horn of the medial meniscus without a displaced flap tear. Conservative physical therapy was recommended."
        elif "medication" in q_lower or "medicine" in q_lower or "taking" in q_lower:
            return "You are actively prescribed Metformin 500mg BID for Type 2 Diabetes and Lisinopril 10mg QD for Essential Hypertension, along with Atorvastatin 10mg QD for Hyperlipidemia."
        elif "chronic" in q_lower or "condition" in q_lower or "diagnosis" in q_lower:
            return "Your active chronic conditions documented in your profile are Type 2 Diabetes, Essential Hypertension, and Hyperlipidemia."
        elif "blood pressure" in q_lower or "hypertension" in q_lower:
            return "For Essential Hypertension (first documented November 2023), you take Lisinopril 10mg QD. Readings stabilized to 124/80 mmHg in your latest checkup."
        else:
            return "Based on your longitudinal medical records, the documented facts confirm stable clinical management with active prescriptions for Type 2 Diabetes and Hypertension."

    def health_check(self) -> bool:
        return True
