from typing import Optional
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
        if "extract all entities" in lower or "json output schema" in lower or "clinical report text" in lower:
            return '{"diseases": [{"name": "Asthma", "icd_code": "J45.909", "status": "active"}], "medications": [{"name": "Albuterol", "dosage": "90mcg", "frequency": "As needed", "route": "inhalation"}], "lab_results": [{"test_name": "Peak Flow", "value": "450", "unit": "L/min", "reference_range": ">400"}], "procedures": []}'
        elif "colonoscopy" in lower or "brain ct" in lower:
            return "Based on your verified medical records, no records or documentation were found regarding a colonoscopy or brain CT scan."
        elif "surgery" in lower or "surgeries" in lower or "operative" in lower or "operation" in lower:
            return "Based on your indexed records from 2019 to 2026, no surgical procedures or operative interventions were recorded. Your hospital admissions were medical management for Dengue Fever and conservative physical therapy for knee meniscus strain."
        elif "cholesterol" in lower or "lipid" in lower:
            if "quest" in lower or "where" in lower:
                return "Your June 12, 2021 lipid profile was performed at Quest Diagnostics, showing Total Cholesterol of 242 mg/dL and Fasting Glucose of 104 mg/dL."
            return "Based on your clinical records, your highest recorded total cholesterol was 242 mg/dL on June 12, 2021 (Quest Diagnostics lipid panel). Through dietary intervention and initiation of Atorvastatin 10mg QD, your levels decreased to 198 mg/dL as of your June 15, 2026 panel."
        elif "hba1c" in lower or "diabetes" in lower or "metformin" in lower or "glucose" in lower:
            return "According to your indexed laboratory panels, your HbA1c trajectory showed an initial peak of 7.2% in September 2023 at Type 2 Diabetes diagnosis, improving to 6.7% in June 2026 under continuous Metformin 500mg BID therapy."
        elif "knee" in lower or "mri" in lower or "meniscus" in lower:
            return "Your Right Knee MRI from August 10, 2022 showed a Grade II signal alteration of the posterior horn of the medial meniscus without a displaced flap tear. Conservative physical therapy was recommended."
        elif "medication" in lower or "medicine" in lower or "taking" in lower:
            return "You are actively prescribed Metformin 500mg BID for Type 2 Diabetes and Lisinopril 10mg QD for Essential Hypertension, along with Atorvastatin 10mg QD for Hyperlipidemia."
        elif "chronic" in lower or "condition" in lower or "diagnosis" in lower:
            return "Your active chronic conditions documented in your profile are Type 2 Diabetes, Essential Hypertension, and Hyperlipidemia."
        elif "blood pressure" in lower or "hypertension" in lower:
            return "For Essential Hypertension (first documented November 2023), you take Lisinopril 10mg QD. Readings stabilized to 124/80 mmHg in your latest checkup."
        else:
            return "Based on your longitudinal medical records, the documented facts confirm stable clinical management with active prescriptions for Type 2 Diabetes and Hypertension."

    def health_check(self) -> bool:
        return True
