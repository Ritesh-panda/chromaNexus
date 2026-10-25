# Change & Extension Guide — ChronaNexus

This guide provides developers and AI agents with precise instructions on where and how to modify or extend ChronaNexus safely without causing regressions.

---

## 1. Extension Recipes

### Recipe A: Adding a New Clinical Entity (e.g., Immunizations or Surgical Procedures)

1. **Database Model**:
   - Add model in `backend/app/models/`:
     ```python
     # Example: backend/app/models/procedure.py
     class Procedure(Base):
         __tablename__ = "procedures"
         id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
         patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
         name = Column(String(255), nullable=False)
         procedure_date = Column(String(50))
         facility = Column(String(255))
         # Add provenance fields:
         source_report_id = Column(String(36), ForeignKey("medical_reports.id"))
         source_page_number = Column(Integer)
         extraction_confidence = Column(Float)
     ```
   - Register the model in `backend/app/models/__init__.py`.
   - Add relationship in `backend/app/models/patient.py`.

2. **Schema Definition**:
   - Add Pydantic schemas in `backend/app/schemas/patient.py` (`ProcedureBase`, `ProcedureCreate`, `ProcedureResponse`).

3. **Clinical Extractor**:
   - Update `backend/app/ai/clinical_extractor/llm_extractor.py` to extract the new entity from document pages.
   - Update `backend/app/ai/ingestion/orchestrator.py` to persist extracted procedures into the session.

4. **Timeline & Query Integration**:
   - Update `backend/app/routers/timeline.py` to include `Procedure` entities in the aggregated timeline stream.

5. **Frontend Interface**:
   - Add TypeScript interface in `src/types/`.
   - Update `src/pages/Timeline/TimelinePage.tsx` and `src/components/cards/TimelineCard.tsx`.

6. **Tests to Run**:
   ```powershell
   python -m pytest backend/tests/test_patient_memory.py backend/tests/test_timeline.py -v
   npx tsc -b
   ```

---

### Recipe B: Adding a New LLM Provider (e.g., vLLM or llama.cpp)

1. **Provider Class**:
   - Create class in `backend/app/ai/llm/` inheriting from `BaseLLMProvider`:
     ```python
     from backend.app.ai.llm.base import BaseLLMProvider

     class VLLMProvider(BaseLLMProvider):
         def __init__(self, endpoint_url: str):
             self.endpoint_url = endpoint_url
         
         def generate(self, prompt: str, **kwargs) -> str:
             # Implementation with connection timeouts and error handling
             ...
     ```
2. **Configuration**:
   - Add settings variables in `backend/app/core/config.py` (`VLLM_BASE_URL`, `USE_VLLM_PROVIDER`).
3. **Pipeline Wiring**:
   - Inject the provider in `backend/app/ai/rag/pipeline.py` within `RAGPipeline.__init__()`.
4. **Tests to Run**:
   ```powershell
   python -m pytest backend/tests/test_llm_providers.py backend/tests/test_rag_pipeline.py -v
   ```

---

### Recipe C: Adding a New Clinical Analyte to the LOINC Catalog

1. **Catalog Update**:
   - Open `backend/app/clinical/terminology/biomarkers.py`.
   - Add the biomarker definition to `BIOMARKER_CATALOG`:
     ```python
     "crp": {
         "canonical_name": "C-Reactive Protein",
         "loinc_code": "1988-5",
         "standard_unit": "mg/L",
         "reference_range": "< 5.0 mg/L",
         "category": "inflammatory",
         "synonyms": ["crp", "c reactive protein", "high sensitivity crp", "hs-crp"]
     }
     ```
2. **Intent Detector**:
   - Verify `backend/app/clinical/structured_query/detector.py` recognizes synonyms for the new analyte.
3. **Tests to Run**:
   ```powershell
   python -m pytest backend/tests/test_structured_queries.py -k "synonym" -v
   ```

---

### Recipe D: Modifying UI Components & Styling

1. **Component Design System**:
   - All shared components reside in `src/components/ui/`.
   - Do **not** use ad-hoc Tailwind colors (e.g. `bg-blue-500`). Use approved design tokens from `src/index.css`:
     - Surface: `bg-white dark:bg-[#1B1E23]`
     - Border: `border-[#E5E7EB] dark:border-[#2F3540]`
     - Inset Card: `bg-[#FAF8F5] dark:bg-[#23272E]`
     - Primary Accent: `#10B981` (Emerald)
2. **Dark Mode Variant**:
   - Always verify dark mode compatibility. Ensure classes use the `dark:` prefix.
3. **Verification**:
   ```powershell
   npm run lint
   npx tsc -b
   npm run build
   ```

---

## 2. Regression Testing Checklist

Whenever you modify any core files, run the corresponding test suite before committing:

| Modified Subsystem | Mandatory Verification Command |
|---|---|
| **Database Models / Migrations** | `python -m pytest backend/tests/test_database_protection.py backend/tests/test_allergy_and_provenance.py` |
| **PDF Extraction / Ingestion** | `python -m pytest backend/tests/test_phase3_ingestion.py backend/tests/test_pdf_extractor.py` |
| **RAG / Retrieval / ChromaDB** | `python -m pytest backend/tests/test_chromadb_sync.py backend/tests/test_rag_pipeline.py` |
| **Structured Clinical Queries** | `python -m pytest backend/tests/test_structured_queries.py -v` |
| **Evidence Grounding / Citations**| `python -m pytest backend/tests/test_evidence_grounding.py tests/benchmarks/test_adversarial_grounding.py -v` |
| **Timeline / Lab Trends** | `python -m pytest backend/tests/test_timeline_and_lab_trends.py -v` |
| **Frontend UI / React Code** | `npm run lint && npx tsc -b` |
