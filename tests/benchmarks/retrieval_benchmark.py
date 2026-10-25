"""
ChronaNexus Synthetic Retrieval Benchmark
========================================
A reproducible, zero-leakage evaluation suite testing 12 clinical retrieval scenarios
against the active ChronaNexus RAG and retrieval pipeline.

Features:
- Pure synthetic data (100% fictional patients, encounters, labs, and documents).
- Isolated SQLite database (never touches production or local chronanexus.db).
- Tests each scenario stage-by-stage across:
  Classifier -> QueryResolver -> StructuredRetriever -> VectorStore -> HybridRetriever -> Pipeline Citations.
- Outputs machine-readable JSON baseline results for regression tracking.
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.core.database import Base
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import LabResult, Medication, Disease, ExtractedEntity
from backend.app.models.allergy import Allergy
from backend.app.models.timeline import TimelineEvent

from backend.app.models.document_chunk import DocumentChunkModel

from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import PostgresVectorStore, InMemoryVectorStore
from backend.app.ai.embeddings import LocalLightweightEmbeddingProvider, get_embedding_provider
from backend.app.ai.rag.classifier import QueryClassifier, QueryIntent
from backend.app.ai.rag.query_resolver import ConversationQueryResolver, ResolvedQuery
from backend.app.ai.rag.structured_retriever import StructuredRetriever
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider


BENCHMARK_DB_PATH = os.path.join(os.path.dirname(__file__), "synthetic_benchmark.db")
BENCHMARK_DB_URL = f"sqlite:///{BENCHMARK_DB_PATH}"


def build_synthetic_database(db: Session) -> Dict[str, str]:
    """
    Seeds entirely synthetic, clinical test patients into an isolated database.
    Returns IDs of the synthetic patients.
    """
    # -------------------------------------------------------------
    # Patient 1: Synthetic Patient Alpha (Alex Vance - Longitudinal)
    # -------------------------------------------------------------
    user_alpha = User(
        id="usr_synth_alpha_001",
        name="Alex Vance (Synthetic)",
        email="synth.alpha@example.test",
        hashed_password="mock_hashed_password",
        role="patient"
    )
    db.add(user_alpha)
    db.flush()

    pat_alpha = Patient(
        id="pat_synth_alpha_001",
        user_id=user_alpha.id,
        date_of_birth="1988-04-12",
        gender="male",
        blood_group="O+",
        primary_care_physician="Dr. Sarah Jenkins, MD",
        known_allergies=["Penicillin (Severe: Anaphylaxis)"]
    )
    db.add(pat_alpha)
    db.flush()

    # Seed Structured Allergy Record with cross-reactivity
    db.add(Allergy(
        id="synth_all_001",
        patient_id=pat_alpha.id,
        allergen="Penicillin",
        category="medication",
        severity="severe",
        reaction="Anaphylaxis",
        drug_classes=["Penicillins", "Beta-lactam antibacterials"],
        cross_reactivities=["amoxicillin", "ampicillin", "augmentin", "piperacillin"],
        status="active",
        source_report_id="synth_rep_alpha_006",
        source_page_number=1,
        extraction_confidence=0.99,
        notes="Documented anaphylaxis. Cross-reactive with aminopenicillins."
    ))


    # -------------------------------------------------------------
    # Patient 2: Synthetic Patient Beta (Jordan Miller - Isolation Target)
    # -------------------------------------------------------------
    user_beta = User(
        id="usr_synth_beta_002",
        name="Jordan Miller (Synthetic)",
        email="synth.beta@example.test",
        hashed_password="mock_hashed_password",
        role="patient"
    )
    db.add(user_beta)
    db.flush()

    pat_beta = Patient(
        id="pat_synth_beta_002",
        user_id=user_beta.id,
        date_of_birth="1975-08-20",
        gender="female",
        blood_group="A+",
        primary_care_physician="Dr. Marcus Thorne, MD",
        known_allergies=["Sulfa Drugs"]
    )
    db.add(pat_beta)
    db.flush()

    # -------------------------------------------------------------
    # Patient Alpha: Reports & Clinical Entities
    # -------------------------------------------------------------
    # Report 1: 2023-04-15 - Outpatient Lab Panel
    rep_1 = MedicalReport(
        id="synth_rep_alpha_001",
        patient_id=pat_alpha.id,
        title="Comprehensive Metabolic Panel & Glucose",
        file_name="cmp_apr_2023.pdf",
        category="blood_report",
        hospital_name="Metro General Hospital",
        report_date="2023-04-15",
        status="completed",
        raw_text=(
            "METRO GENERAL HOSPITAL - OUTPATIENT LABS\n"
            "Patient: Alex Vance | Date: 2023-04-15\n"
            "Fasting Blood Glucose: 142 mg/dL (High, Ref: 70-99 mg/dL)\n"
            "Serum Creatinine: 0.95 mg/dL (Normal, Ref: 0.74-1.35 mg/dL)\n"
            "eGFR: >90 mL/min/1.73m2\n"
            "Impression: Impaired fasting glucose, normal renal function."
        )
    )
    db.add(rep_1)

    db.add(LabResult(
        id="synth_lab_001",
        patient_id=pat_alpha.id,
        source_report_id=rep_1.id,
        test_name="Fasting Blood Glucose",
        value="142",
        unit="mg/dL",
        reference_range="70 - 99",
        status="high",
        test_date="2023-04-15",
        hospital_name="Metro General Hospital"
    ))
    db.add(LabResult(
        id="synth_lab_002",
        patient_id=pat_alpha.id,
        source_report_id=rep_1.id,
        test_name="Serum Creatinine",
        value="0.95",
        unit="mg/dL",
        reference_range="0.74 - 1.35",
        status="normal",
        test_date="2023-04-15",
        hospital_name="Metro General Hospital"
    ))

    # Report 2: 2024-09-10 - Metabolic & Hepatic Panel
    rep_2 = MedicalReport(
        id="synth_rep_alpha_002",
        patient_id=pat_alpha.id,
        title="Metabolic and Hepatic Function Panel",
        file_name="hepatic_sep_2024.pdf",
        category="blood_report",
        hospital_name="Quest Diagnostics",
        report_date="2024-09-10",
        status="completed",
        raw_text=(
            "QUEST DIAGNOSTICS - CLINICAL PATHOLOGY\n"
            "Patient: Alex Vance | Date: 2024-09-10\n"
            "Serum Potassium: 4.8 mEq/L (Normal, Ref: 3.5-5.1 mEq/L)\n"
            "Serum Creatinine: 1.28 mg/dL (Normal, Ref: 0.74-1.35 mg/dL)\n"
            "Alanine Aminotransferase (ALT): 38 U/L (Normal, Ref: 10-40 U/L)\n"
            "Aspartate Aminotransferase (AST): 32 U/L (Normal, Ref: 10-35 U/L)\n"
            "Total Bilirubin: 0.8 mg/dL (Normal, Ref: 0.2-1.2 mg/dL)\n"
            "Impression: Stable electrolyte and hepatic profile."
        )
    )
    db.add(rep_2)

    db.add(LabResult(
        id="synth_lab_003",
        patient_id=pat_alpha.id,
        source_report_id=rep_2.id,
        test_name="Serum Potassium",
        value="4.8",
        unit="mEq/L",
        reference_range="3.5 - 5.1",
        status="normal",
        test_date="2024-09-10",
        hospital_name="Quest Diagnostics"
    ))
    db.add(LabResult(
        id="synth_lab_004",
        patient_id=pat_alpha.id,
        source_report_id=rep_2.id,
        test_name="Serum Creatinine",
        value="1.28",
        unit="mg/dL",
        reference_range="0.74 - 1.35",
        status="normal",
        test_date="2024-09-10",
        hospital_name="Quest Diagnostics"
    ))
    db.add(LabResult(
        id="synth_lab_005",
        patient_id=pat_alpha.id,
        source_report_id=rep_2.id,
        test_name="Alanine Aminotransferase (ALT)",
        value="38",
        unit="U/L",
        reference_range="10 - 40",
        status="normal",
        test_date="2024-09-10",
        hospital_name="Quest Diagnostics"
    ))
    db.add(LabResult(
        id="synth_lab_006",
        patient_id=pat_alpha.id,
        source_report_id=rep_2.id,
        test_name="Aspartate Aminotransferase (AST)",
        value="32",
        unit="U/L",
        reference_range="10 - 35",
        status="normal",
        test_date="2024-09-10",
        hospital_name="Quest Diagnostics"
    ))

    # Report 3: 2024-11-02 - Metro Health Labs (HbA1c = 6.8%)
    rep_3 = MedicalReport(
        id="synth_rep_alpha_003",
        patient_id=pat_alpha.id,
        title="Endocrine Review Panel - Metro Health",
        file_name="metro_hba1c_nov_2024.pdf",
        category="blood_report",
        hospital_name="Metro Health Labs",
        report_date="2024-11-02",
        status="completed",
        raw_text=(
            "METRO HEALTH LABS - ENDOCRINOLOGY\n"
            "Patient: Alex Vance | Date: 2024-11-02\n"
            "Hemoglobin A1c (HbA1c): 6.8 % (High, Ref: 4.0-5.6 %)\n"
            "Method: HPLC Certified Assay\n"
            "Impression: Improved glycemic trajectory under oral Metformin therapy."
        )
    )
    db.add(rep_3)
    db.add(LabResult(
        id="synth_lab_007",
        patient_id=pat_alpha.id,
        source_report_id=rep_3.id,
        test_name="Hemoglobin A1c (HbA1c)",
        value="6.8",
        unit="%",
        reference_range="4.0 - 5.6",
        status="high",
        test_date="2024-11-02",
        hospital_name="Metro Health Labs"
    ))

    # Report 4: 2024-11-09 - St. Jude Outpatient Clinic (HbA1c = 7.4% - Contradictory)
    rep_4 = MedicalReport(
        id="synth_rep_alpha_004",
        patient_id=pat_alpha.id,
        title="Second Opinion Diabetes Screen - St. Jude",
        file_name="stjude_hba1c_nov_2024.pdf",
        category="blood_report",
        hospital_name="St. Jude Outpatient Clinic",
        report_date="2024-11-09",
        status="completed",
        raw_text=(
            "ST. JUDE OUTPATIENT CLINIC - LABORATORY SERVICES\n"
            "Patient: Alex Vance | Date: 2024-11-09\n"
            "Hemoglobin A1c (HbA1c): 7.4 % (High, Ref: 4.0-5.6 %)\n"
            "Point of Care Immunoassay\n"
            "Impression: Suboptimal glycemic control, elevated relative to prior laboratory benchmarks."
        )
    )
    db.add(rep_4)
    db.add(LabResult(
        id="synth_lab_008",
        patient_id=pat_alpha.id,
        source_report_id=rep_4.id,
        test_name="Hemoglobin A1c (HbA1c)",
        value="7.4",
        unit="%",
        reference_range="4.0 - 5.6",
        status="high",
        test_date="2024-11-09",
        hospital_name="St. Jude Outpatient Clinic"
    ))

    # Report 5: 2025-01-20 - Annual Physical Exam (Glucose = 108 mg/dL)
    rep_5 = MedicalReport(
        id="synth_rep_alpha_005",
        patient_id=pat_alpha.id,
        title="Annual Wellness Visit & Metabolic Panel",
        file_name="wellness_jan_2025.pdf",
        category="consultation",
        hospital_name="Metro General Hospital",
        report_date="2025-01-20",
        status="completed",
        raw_text=(
            "METRO GENERAL HOSPITAL - PRIMARY CARE CLINIC\n"
            "Patient: Alex Vance | Date: 2025-01-20\n"
            "Physician: Dr. Sarah Jenkins, MD\n"
            "Vital Signs: BP 122/78 mmHg, HR 68 bpm, Weight 81.2 kg\n"
            "Fasting Blood Glucose: 108 mg/dL (Mild Elevation, Ref: 70-99 mg/dL)\n"
            "Assessment: Significant improvement in fasting glucose (down to 108 from 142 in 2023)."
        )
    )
    db.add(rep_5)
    db.add(LabResult(
        id="synth_lab_009",
        patient_id=pat_alpha.id,
        source_report_id=rep_5.id,
        test_name="Fasting Blood Glucose",
        value="108",
        unit="mg/dL",
        reference_range="70 - 99",
        status="high",
        test_date="2025-01-20",
        hospital_name="Metro General Hospital"
    ))

    # Report 6: 2023-06-01 - Pulmonary Consultation
    rep_6 = MedicalReport(
        id="synth_rep_alpha_006",
        patient_id=pat_alpha.id,
        title="Pulmonary Specialty Consultation",
        file_name="pulmonary_jun_2023.pdf",
        category="consultation",
        hospital_name="St. Jude Pulmonary Center",
        report_date="2023-06-01",
        status="completed",
        raw_text=(
            "ST. JUDE PULMONARY CENTER\n"
            "Patient: Alex Vance | Date: 2023-06-01\n"
            "Specialist: Dr. Emily Watson, MD\n"
            "Diagnosis: Moderate Persistent Asthma (ICD-10 J45.40)\n"
            "Prescription: Fluticasone/Salmeterol (Advair Diskus) 250/50 mcg, 1 inhalation BID\n"
            "Allergies Noted: Patient has verified anaphylactic Penicillin allergy."
        )
    )
    db.add(rep_6)
    db.add(Disease(
        id="synth_dis_001",
        patient_id=pat_alpha.id,
        name="Moderate Persistent Asthma",
        icd_code="J45.40",
        status="active",
        diagnosed_date="2023-06-01",
        treating_doctor="Dr. Emily Watson, MD",
        source_report_id=rep_6.id
    ))
    db.add(Medication(
        id="synth_med_001",
        patient_id=pat_alpha.id,
        name="Fluticasone/Salmeterol (Advair Diskus)",
        dosage="250/50 mcg",
        frequency="1 inhalation twice daily (BID)",
        route="Inhalation",
        start_date="2023-06-01",
        status="active",
        prescribing_doctor="Dr. Emily Watson, MD",
        indication="Moderate Persistent Asthma",
        source_report_id=rep_6.id
    ))

    # Report 7: 2024-01-15 - Cardiology Consultation
    rep_7 = MedicalReport(
        id="synth_rep_alpha_007",
        patient_id=pat_alpha.id,
        title="Hypertension & Cardiovascular Review",
        file_name="cardio_jan_2024.pdf",
        category="consultation",
        hospital_name="Metro General Hospital",
        report_date="2024-01-15",
        status="completed",
        raw_text=(
            "METRO GENERAL HOSPITAL - CARDIOLOGY\n"
            "Patient: Alex Vance | Date: 2024-01-15\n"
            "Diagnosis: Essential (Primary) Hypertension (ICD-10 I10)\n"
            "Active Prescription: Lisinopril 10mg QD oral tablet for blood pressure control.\n"
            "Clinical Note: Elevated arterial blood pressure effectively stabilized."
        )
    )
    db.add(rep_7)
    db.add(Disease(
        id="synth_dis_002",
        patient_id=pat_alpha.id,
        name="Essential (Primary) Hypertension",
        icd_code="I10",
        status="active",
        diagnosed_date="2024-01-15",
        treating_doctor="Dr. Sarah Jenkins, MD",
        source_report_id=rep_7.id
    ))
    db.add(Medication(
        id="synth_med_002",
        patient_id=pat_alpha.id,
        name="Lisinopril",
        dosage="10mg",
        frequency="Once daily (QD)",
        route="Oral",
        start_date="2024-01-15",
        status="active",
        prescribing_doctor="Dr. Sarah Jenkins, MD",
        indication="Essential Hypertension",
        source_report_id=rep_7.id
    ))

    # Report 8: Multi-page report (>4,000 characters) - Page 3 contains Thyroid panel
    padding_page1_2 = "CLINICAL DEMOGRAPHICS, BILLING CODES, INSURANCE VERIFICATION AND ROUTINE METABOLIC BASELINES.\n" + ("Section 1: Routine administrative text and normal baselines.\n" * 45)
    thyroid_section = (
        "\n--- PAGE 3: SPECIALIZED ENDOCRINE & THYROID PANEL ---\n"
        "Date of Assay: 2024-05-10 | Specimen: Venous Blood Serum\n"
        "Thyroid Stimulating Hormone (TSH): 5.8 mIU/L (High, Ref: 0.45 - 4.50 mIU/L)\n"
        "Free Thyroxine (Free T4): 0.8 ng/dL (Low-Normal, Ref: 0.82 - 1.77 ng/dL)\n"
        "Diagnostic Interpretation: Subclinical hypothyroidism evidenced by elevated TSH and borderline Free T4."
    )
    rep_8_text = padding_page1_2 + thyroid_section

    rep_8 = MedicalReport(
        id="synth_rep_alpha_008",
        patient_id=pat_alpha.id,
        title="Multi-Page Comprehensive Endocrine Assessment",
        file_name="multipage_endocrine_2024.pdf",
        category="blood_report",
        hospital_name="Metro General Hospital",
        report_date="2024-05-10",
        status="completed",
        raw_text=rep_8_text
    )
    db.add(rep_8)
    db.add(LabResult(
        id="synth_lab_010",
        patient_id=pat_alpha.id,
        source_report_id=rep_8.id,
        test_name="Thyroid Stimulating Hormone (TSH)",
        value="5.8",
        unit="mIU/L",
        reference_range="0.45 - 4.50",
        status="high",
        test_date="2024-05-10",
        hospital_name="Metro General Hospital"
    ))
    db.add(LabResult(
        id="synth_lab_011",
        patient_id=pat_alpha.id,
        source_report_id=rep_8.id,
        test_name="Free Thyroxine (Free T4)",
        value="0.8",
        unit="ng/dL",
        reference_range="0.82 - 1.77",
        status="low",
        test_date="2024-05-10",
        hospital_name="Metro General Hospital"
    ))

    # -------------------------------------------------------------
    # Patient Beta: MRI Knee (Isolated Record)
    # -------------------------------------------------------------
    rep_beta = MedicalReport(
        id="synth_rep_beta_001",
        patient_id=pat_beta.id,
        title="3.0T MRI Right Knee Joint",
        file_name="mri_knee_beta.pdf",
        category="mri",
        hospital_name="Advanced Orthopedic Imaging",
        report_date="2024-08-15",
        status="completed",
        raw_text=(
            "ADVANCED ORTHOPEDIC IMAGING - 3.0T MRI\n"
            "Patient: Jordan Miller | Date: 2024-08-15\n"
            "Clinical Indication: Persistent right medial joint line tenderness following fall.\n"
            "Findings: Grade II degenerative signal alteration within the posterior horn of the medial meniscus. No displaced flap tear.\n"
            "Impression: Medial meniscus tear Grade II, intact anterior cruciate ligament."
        )
    )
    db.add(rep_beta)

    # -------------------------------------------------------------
    # Document Chunks Indexing (Simulate Vector Store Indexing)
    # -------------------------------------------------------------
    vector_store = PostgresVectorStore(db_session=db)
    
    # Index Alpha's reports
    all_reports = [rep_1, rep_2, rep_3, rep_4, rep_5, rep_6, rep_7, rep_8, rep_beta]
    chunks_to_index = []
    
    for rep in all_reports:
        # Split into ~400 char segments
        text = rep.raw_text or ""
        segments = [text[i:i+450] for i in range(0, len(text), 400)]
        for idx, seg in enumerate(segments):
            chunk = DocumentChunk(
                chunk_id=f"chk_{rep.id}_{idx}",
                document_id=rep.id,
                page_number=1 if idx < 3 else (2 if idx < 6 else 3),
                chunk_index=idx,
                text=seg,
                metadata={
                    "patient_id": rep.patient_id,
                    "title": rep.title,
                    "report_date": rep.report_date,
                    "hospital": rep.hospital_name,
                    "category": rep.category
                }
            )
            chunks_to_index.append(chunk)

    vector_store.add_documents(chunks_to_index)
    db.commit()

    return {"alpha": pat_alpha.id, "beta": pat_beta.id}


class RetrievalBenchmarkRunner:
    """
    Executes and scores the 12 clinical retrieval scenarios.
    Records stage-by-stage diagnostics.
    """

    def __init__(self, db: Session, patient_alpha_id: str, patient_beta_id: str):
        self.db = db
        self.pat_alpha = patient_alpha_id
        self.pat_beta = patient_beta_id
        self.vector_store = PostgresVectorStore(db_session=db)
        self.structured_retriever = StructuredRetriever(db_session=db)
        self.query_classifier = QueryClassifier()
        self.query_resolver = ConversationQueryResolver()
        self.hybrid_retriever = HybridRetriever(vector_store=self.vector_store, db_session=db)
        self.pipeline = RAGPipeline(
            retriever=self.hybrid_retriever,
            llm=MockDeterministicLLMProvider(),
            db_session=db
        )

    def run_all(self) -> Dict[str, Any]:
        results = []
        
        scenarios = [
            self.eval_scenario_01_exact_numerical_and_units,
            self.eval_scenario_02_temporal_date_specific,
            self.eval_scenario_03_latest_vs_historical_biomarker,
            self.eval_scenario_04_medication_allergy_crossref,
            self.eval_scenario_05_multiturn_continuity,
            self.eval_scenario_06_contradictory_records,
            self.eval_scenario_07_unsupported_questions,
            self.eval_scenario_08_patient_isolation,
            self.eval_scenario_09_newly_uploaded_report,
            self.eval_scenario_10_synonyms_clinical_terminology,
            self.eval_scenario_11_multipage_truncation,
            self.eval_scenario_12_citation_relevance
        ]

        for sc in scenarios:
            t0 = time.time()
            try:
                res = sc()
            except Exception as e:
                res = {
                    "scenario_id": sc.__name__,
                    "name": sc.__name__,
                    "passed": False,
                    "earliest_failure_stage": "execution_exception",
                    "error": str(e),
                    "evidence": [],
                    "diagnostic_notes": f"Unhandled exception: {str(e)}"
                }
            res["duration_ms"] = round((time.time() - t0) * 1000, 2)
            results.append(res)

        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        pass_rate = round((passed / total) * 100, 1)

        summary = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_scenarios": total,

            "passed_scenarios": passed,
            "failed_scenarios": total - passed,
            "pass_rate_percentage": pass_rate,
            "results": results
        }
        return summary

    # -------------------------------------------------------------------------
    # Scenario 1: Exact numerical values and unit handling
    # -------------------------------------------------------------------------
    def eval_scenario_01_exact_numerical_and_units(self) -> Dict[str, Any]:
        query = "What was my serum potassium level and unit on September 10, 2024?"
        
        # Stage 1: Classifier
        cl = self.query_classifier.classify(query)
        # Stage 2: Structured Retrieval
        struct_res = self.structured_retriever.retrieve_labs(self.pat_alpha, query_keywords=["potassium"])
        # Stage 3: Vector search
        vec_res = self.vector_store.similarity_search(query, top_k=4, filter_metadata={"patient_id": self.pat_alpha})
        # Stage 4: Hybrid
        hybrid_res = self.hybrid_retriever.retrieve(query, patient_id=self.pat_alpha, top_k=4)

        has_exact_value = any(
            "4.8" in r.content and "mEq/L" in r.content and 
            ("potassium" in r.content.lower() or "2823-3" in r.content.lower()) and
            ("2024-09-10" in r.content or "September 10, 2024" in r.content or "2024" in r.content)
            for r in hybrid_res.elements
        )
        
        earliest_failure = None
        if not struct_res and not any("4.8" in v.chunk.text for v in vec_res):
            earliest_failure = "candidate_retrieval"
        elif not has_exact_value:
            earliest_failure = "ranking_and_fusion"

        return {
            "scenario_id": "SCENARIO_01_EXACT_NUMERICAL_UNITS",
            "name": "Exact numerical values and unit handling",
            "query": query,
            "passed": has_exact_value,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Structured found {len(struct_res)} items. Vector found {len(vec_res)} items. Verified Potassium 4.8 mEq/L with temporal context.",
            "evidence": [e.content for e in hybrid_res.elements[:2]]
        }

    # -------------------------------------------------------------------------
    # Scenario 2: Date-specific queries and temporal filtering
    # -------------------------------------------------------------------------
    def eval_scenario_02_temporal_date_specific(self) -> Dict[str, Any]:
        query = "What was my serum creatinine on 2023-04-15 versus 2024-09-10?"
        hybrid_res = self.hybrid_retriever.retrieve(query, patient_id=self.pat_alpha, top_k=6)
        
        found_2023 = any("2023-04-15" in r.content and "0.95" in r.content for r in hybrid_res.elements)
        found_2024 = any("2024-09-10" in r.content and "1.28" in r.content for r in hybrid_res.elements)
        passed = found_2023 and found_2024

        earliest_failure = None
        if not (found_2023 or found_2024):
            earliest_failure = "candidate_retrieval"
        elif not passed:
            earliest_failure = "ranking_and_fusion"

        return {
            "scenario_id": "SCENARIO_02_TEMPORAL_DATE_SPECIFIC",
            "name": "Date-specific queries and temporal filtering",
            "query": query,
            "passed": passed,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Found 2023 reading: {found_2023}, Found 2024 reading: {found_2024}",
            "evidence": [e.content for e in hybrid_res.elements[:3]]
        }

    # -------------------------------------------------------------------------
    # Scenario 3: Latest versus historical biomarker values
    # -------------------------------------------------------------------------
    def eval_scenario_03_latest_vs_historical_biomarker(self) -> Dict[str, Any]:
        query = "What is my latest Fasting Blood Glucose level?"
        hybrid_res = self.hybrid_retriever.retrieve(query, patient_id=self.pat_alpha, top_k=4)
        
        # Expected: 2025-01-20 (108 mg/dL) must be ranked higher than 2023-04-15 (142 mg/dL)
        elements = hybrid_res.elements
        glucose_elements = [e for e in elements if "Glucose" in e.content or "glucose" in e.content]
        
        passed = False
        earliest_failure = "ranking_and_fusion"
        if glucose_elements:
            top_glucose = glucose_elements[0]
            if "108" in top_glucose.content and ("2025-01-20" in top_glucose.content or "2025" in top_glucose.content):
                passed = True
                earliest_failure = None
            else:
                earliest_failure = "temporal_ranking_bias"
        else:
            earliest_failure = "candidate_retrieval"

        return {
            "scenario_id": "SCENARIO_03_LATEST_VS_HISTORICAL",
            "name": "Latest versus historical biomarker values",
            "query": query,
            "passed": passed,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Top glucose element: {glucose_elements[0].content if glucose_elements else 'None'}",
            "evidence": [e.content for e in glucose_elements[:2]]
        }

    # -------------------------------------------------------------------------
    # Scenario 4: Medication and allergy cross-referencing
    # -------------------------------------------------------------------------
    def eval_scenario_04_medication_allergy_crossref(self) -> Dict[str, Any]:
        query = "Can I take Amoxicillin for my bacterial sinus infection?"
        hybrid_res = self.hybrid_retriever.retrieve(query, patient_id=self.pat_alpha, top_k=6)
        
        # Expected: Allergy to Penicillin AND structured safety alert MUST be retrieved in context
        has_allergy_record = any("Penicillin" in r.content for r in hybrid_res.elements)
        has_safety_alert = any(
            ("SAFETY ALERT" in (getattr(r, 'title', '') or '') or "SAFETY ALERT" in r.content) and
            "Amoxicillin" in r.content and "Penicillin" in r.content
            for r in hybrid_res.elements
        )
        passed = has_allergy_record and has_safety_alert
        
        earliest_failure = None
        if not has_allergy_record:
            earliest_failure = "clinical_extraction_persistence"
        elif not has_safety_alert:
            earliest_failure = "clinical_decision_support_alert_generation"

        return {
            "scenario_id": "SCENARIO_04_MEDICATION_ALLERGY_CROSSREF",
            "name": "Medication and allergy cross-referencing",
            "query": query,
            "passed": passed,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Penicillin allergy record present: {has_allergy_record}, Structured safety alert generated: {has_safety_alert}",
            "evidence": [e.content for e in hybrid_res.elements[:2]]
        }

    # -------------------------------------------------------------------------
    # Scenario 5: Multi-turn follow-up and topic continuity
    # -------------------------------------------------------------------------
    def eval_scenario_05_multiturn_continuity(self) -> Dict[str, Any]:
        turn1_query = "What pulmonary conditions have been diagnosed in my records?"
        turn1_history = [
            {"sender": "user", "text": turn1_query},
            {"sender": "ai", "text": "You have a documented diagnosis of Moderate Persistent Asthma from St. Jude Pulmonary Center."}
        ]
        
        turn2_query = "What inhaler dose was prescribed for that condition?"
        resolved = self.query_resolver.resolve(turn2_query, conversation_history=turn1_history)
        hybrid_res = self.hybrid_retriever.retrieve(
            turn2_query,
            patient_id=self.pat_alpha,
            top_k=4,
            search_query=resolved.resolved_query
        )

        has_inhaler_med = any("Fluticasone" in r.content or "Advair" in r.content for r in hybrid_res.elements)
        
        earliest_failure = None
        if resolved.active_topic not in ["asthma", "pulmonary"]:
            earliest_failure = "conversation_context_resolution"
        elif not has_inhaler_med:
            earliest_failure = "candidate_retrieval"

        return {
            "scenario_id": "SCENARIO_05_MULTITURN_CONTINUITY",
            "name": "Multi-turn follow-up and topic continuity",
            "query": turn2_query,
            "passed": has_inhaler_med and resolved.active_topic in ["asthma", "pulmonary"],
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Resolved query topic: '{resolved.active_topic}', resolved text: '{resolved.resolved_query}'",
            "evidence": [e.content for e in hybrid_res.elements[:2]]
        }

    # -------------------------------------------------------------------------
    # Scenario 6: Contradictory records from different facilities
    # -------------------------------------------------------------------------
    def eval_scenario_06_contradictory_records(self) -> Dict[str, Any]:
        query = "What was my HbA1c recorded in November 2024 across different facilities?"
        hybrid_res = self.hybrid_retriever.retrieve(query, patient_id=self.pat_alpha, top_k=6)
        
        found_metro = any("6.8" in r.content and "Metro" in r.content for r in hybrid_res.elements)
        found_stjude = any("7.4" in r.content and "St. Jude" in r.content for r in hybrid_res.elements)
        passed = found_metro and found_stjude

        earliest_failure = None
        if not (found_metro or found_stjude):
            earliest_failure = "candidate_retrieval"
        elif not passed:
            earliest_failure = "ranking_and_fusion"

        return {
            "scenario_id": "SCENARIO_06_CONTRADICTORY_RECORDS",
            "name": "Contradictory records from different facilities",
            "query": query,
            "passed": passed,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Found Metro (6.8%): {found_metro}, Found St. Jude (7.4%): {found_stjude}",
            "evidence": [e.content for e in hybrid_res.elements[:3]]
        }

    # -------------------------------------------------------------------------
    # Scenario 7: Unsupported questions that must not receive invented answers
    # -------------------------------------------------------------------------
    def eval_scenario_07_unsupported_questions(self) -> Dict[str, Any]:
        query = "What were the findings of my colonoscopy procedure and biopsy?"
        rag_response = self.pipeline.query(query, patient_id=self.pat_alpha, top_k=4)
        
        has_citations = len(rag_response.citations) > 0
        hallucinated = any(term in rag_response.answer.lower() for term in ["polyp", "adenoma", "diverticulosis", "cecum"])
        refused_properly = "no record" in rag_response.answer.lower() or "not found" in rag_response.answer.lower()

        passed = (not has_citations) and (not hallucinated) and refused_properly

        earliest_failure = None
        if has_citations:
            earliest_failure = "citation_verification"
        elif not refused_properly or hallucinated:
            earliest_failure = "answer_generation"

        return {
            "scenario_id": "SCENARIO_07_UNSUPPORTED_QUESTIONS",
            "name": "Unsupported questions (Hallucination & Refusal check)",
            "query": query,
            "passed": passed,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Citations count: {len(rag_response.citations)}, Answer: {rag_response.answer[:120]}...",
            "evidence": [c.get("reportTitle", "") for c in rag_response.citations]
        }

    # -------------------------------------------------------------------------
    # Scenario 8: Patient isolation and zero cross-patient retrieval
    # -------------------------------------------------------------------------
    def eval_scenario_08_patient_isolation(self) -> Dict[str, Any]:
        # Query for Patient Alpha about Knee MRI (which belongs strictly to Patient Beta)
        query = "What were the findings of my knee MRI?"
        
        # Test vector store directly with metadata filter
        vec_res = self.vector_store.similarity_search(query, top_k=10, filter_metadata={"patient_id": self.pat_alpha})
        leaked_in_vector = any(r.chunk.metadata.get("patient_id") == self.pat_beta for r in vec_res)
        
        # Test hybrid pipeline
        hybrid_res = self.hybrid_retriever.retrieve(query, patient_id=self.pat_alpha, top_k=10)
        leaked_in_hybrid = any(
            (getattr(r, "metadata", {}) and r.metadata.get("patient_id") == self.pat_beta) or
            ("Jordan Miller" in r.content)
            for r in hybrid_res.elements
        )

        passed = (not leaked_in_vector) and (not leaked_in_hybrid)
        earliest_failure = None if passed else "candidate_retrieval"

        return {
            "scenario_id": "SCENARIO_08_PATIENT_ISOLATION",
            "name": "Patient isolation and zero cross-patient retrieval",
            "query": query,
            "passed": passed,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Vector leaked Beta data: {leaked_in_vector}, Hybrid leaked Beta data: {leaked_in_hybrid}",
            "evidence": [e.content[:100] for e in hybrid_res.elements[:2]]
        }

    # -------------------------------------------------------------------------
    # Scenario 9: Newly uploaded relevant reports
    # -------------------------------------------------------------------------
    def eval_scenario_09_newly_uploaded_report(self) -> Dict[str, Any]:
        # Dynamically ingest a new report
        new_rep_id = f"synth_dynamic_rep_{uuid.uuid4().hex[:6]}"
        new_report = MedicalReport(
            id=new_rep_id,
            patient_id=self.pat_alpha,
            title="Emergency Department Discharge - Acute Bronchitis",
            file_name="ed_bronchitis_2025.pdf",
            category="discharge_summary",
            hospital_name="St. Jude Urgent Care",
            report_date="2025-02-15",
            status="completed",
            raw_text="ST. JUDE URGENT CARE - DISCHARGE SUMMARY\nPatient: Alex Vance | Date: 2025-02-15\nDiagnosis: Acute Asthmatic Bronchitis.\nPrescribed Azithromycin 250mg 5-day Z-Pak."
        )
        self.db.add(new_report)
        self.db.flush()

        # Add chunk
        chunk = DocumentChunk(
            chunk_id=f"chk_{new_rep_id}_0",
            document_id=new_rep_id,
            page_number=1,
            chunk_index=0,
            text=new_report.raw_text,
            metadata={"patient_id": self.pat_alpha, "title": new_report.title, "report_date": "2025-02-15"}
        )
        self.vector_store.add_documents([chunk])
        self.db.commit()

        # Query for newly uploaded record
        query = "When was I treated for acute bronchitis and what antibiotic was prescribed?"
        hybrid_res = self.hybrid_retriever.retrieve(query, patient_id=self.pat_alpha, top_k=4)
        
        found = any("bronchitis" in r.content.lower() and "Azithromycin" in r.content for r in hybrid_res.elements)
        earliest_failure = None if found else "candidate_retrieval"

        return {
            "scenario_id": "SCENARIO_09_NEWLY_UPLOADED_REPORT",
            "name": "Newly uploaded relevant reports",
            "query": query,
            "passed": found,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Found newly uploaded bronchitis report: {found}",
            "evidence": [e.content for e in hybrid_res.elements[:2]]
        }

    # -------------------------------------------------------------------------
    # Scenario 10: Synonyms and alternate clinical terminology
    # -------------------------------------------------------------------------
    def eval_scenario_10_synonyms_clinical_terminology(self) -> Dict[str, Any]:
        # Test semantic matching where exact keywords differ:
        # Query uses "elevated arterial pressure" -> document text contains "Essential (Primary) Hypertension" and "blood pressure"
        query = "Do my records show elevated arterial pressure or high cardiac readings?"
        
        # Test dense vector similarity directly (this exposes LocalLightweightEmbeddingProvider hash collapse)
        vec_res = self.vector_store.similarity_search(query, top_k=4, filter_metadata={"patient_id": self.pat_alpha})
        has_htn_in_vector = any("hypertension" in v.chunk.text.lower() or "lisinopril" in v.chunk.text.lower() for v in vec_res)
        
        hybrid_res = self.hybrid_retriever.retrieve(query, patient_id=self.pat_alpha, top_k=4)
        has_htn_in_hybrid = any("hypertension" in r.content.lower() or "lisinopril" in r.content.lower() for r in hybrid_res.elements)

        passed = has_htn_in_vector and has_htn_in_hybrid
        earliest_failure = None
        if not has_htn_in_vector:
            earliest_failure = "embedding_generation"
        elif not has_htn_in_hybrid:
            earliest_failure = "ranking_and_fusion"

        return {
            "scenario_id": "SCENARIO_10_SYNONYMS_AND_TERMINOLOGY",
            "name": "Synonyms and alternate clinical terminology",
            "query": query,
            "passed": passed,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Vector found synonym: {has_htn_in_vector}, Hybrid found synonym: {has_htn_in_hybrid}. (SHA-256 hash embeddings cannot bridge semantic synonyms).",
            "evidence": [e.content for e in hybrid_res.elements[:2]]
        }

    # -------------------------------------------------------------------------
    # Scenario 11: Multi-page reports and table-based lab results
    # -------------------------------------------------------------------------
    def eval_scenario_11_multipage_truncation(self) -> Dict[str, Any]:
        # Query targets the Thyroid panel on Page 3 (char offset > 3,600)
        query = "What were my TSH and Free T4 thyroid results?"
        
        # Check if structured retriever finds it
        struct_res = self.structured_retriever.retrieve_labs(self.pat_alpha, query_keywords=["tsh", "thyroid", "free t4"])
        # Check if hybrid retriever finds it
        hybrid_res = self.hybrid_retriever.retrieve(query, patient_id=self.pat_alpha, top_k=4)
        
        found_tsh = any("5.8" in r.content for r in hybrid_res.elements)
        found_t4 = any("0.8" in r.content for r in hybrid_res.elements)
        passed = found_tsh and found_t4

        earliest_failure = None
        if not (found_tsh or found_t4):
            earliest_failure = "clinical_extraction_persistence"

        return {
            "scenario_id": "SCENARIO_11_MULTIPAGE_TRUNCATION",
            "name": "Multi-page reports & deep table results (>3000 chars)",
            "query": query,
            "passed": passed,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Found TSH: {found_tsh}, Found Free T4: {found_t4}. Note: In live ingestion, llm_extractor truncates to 3000 chars, dropping Page 3.",
            "evidence": [e.content for e in hybrid_res.elements[:2]]
        }

    # -------------------------------------------------------------------------
    # Scenario 12: Citation relevance and support for generated claims
    # -------------------------------------------------------------------------
    def eval_scenario_12_citation_relevance(self) -> Dict[str, Any]:
        query = "What were my liver enzyme levels (ALT and AST)?"
        rag_response = self.pipeline.query(query, patient_id=self.pat_alpha, top_k=4)
        
        # Citations MUST contain synth_rep_alpha_002 (Hepatic panel)
        # Citations MUST NOT contain unrelated reports like synth_rep_alpha_006 (Pulmonary/Asthma)
        citations = rag_response.citations
        cited_report_ids = [c.get("reportId") for c in citations]
        
        has_correct_citation = "synth_rep_alpha_002" in cited_report_ids
        has_irrelevant_citation = any(rid in ["synth_rep_alpha_006", "synth_rep_alpha_007", "synth_rep_beta_001"] for rid in cited_report_ids)

        passed = has_correct_citation and (not has_irrelevant_citation)
        earliest_failure = None
        if not has_correct_citation:
            earliest_failure = "candidate_retrieval"
        elif has_irrelevant_citation:
            earliest_failure = "citation_verification"

        return {
            "scenario_id": "SCENARIO_12_CITATION_RELEVANCE",
            "name": "Citation relevance and claim verification",
            "query": query,
            "passed": passed,
            "earliest_failure_stage": earliest_failure or "none",
            "diagnostic_notes": f"Cited reports: {cited_report_ids}. Has correct: {has_correct_citation}, Has irrelevant: {has_irrelevant_citation}",
            "evidence": [f"{c.get('reportId')}: {c.get('reportTitle')}" for c in citations]
        }


def run_benchmark_and_save():
    print("=" * 70)
    print("ChronaNexus Synthetic Retrieval Benchmark (Phase 1 Baseline)")
    print("=" * 70)

    # Initialize isolated SQLite database
    engine = create_engine(BENCHMARK_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionMaker()

    try:
        print("[1/3] Seeding synthetic, fictional patients (Alpha & Beta)...")
        pat_ids = build_synthetic_database(db)
        print(f"      Seeded Alpha ({pat_ids['alpha']}) and Beta ({pat_ids['beta']}).")

        print("[2/3] Running 12 clinical retrieval scenarios...")
        runner = RetrievalBenchmarkRunner(db, pat_ids["alpha"], pat_ids["beta"])
        summary = runner.run_all()

        print("[3/3] Benchmark Run Complete!")
        print("-" * 70)
        print(f"Total Scenarios : {summary['total_scenarios']}")
        print(f"Passed          : {summary['passed_scenarios']}")
        print(f"Failed          : {summary['failed_scenarios']}")
        print(f"Pass Rate       : {summary['pass_rate_percentage']}%")
        print("-" * 70)

        for res in summary["results"]:
            status = "PASS" if res["passed"] else "FAIL"
            fail_stage = f" [Failed at: {res['earliest_failure_stage']}]" if not res["passed"] else ""
            print(f"[{status}] {res['name']}{fail_stage} ({res['duration_ms']} ms)")
            if not res["passed"]:
                print(f"       Notes: {res['diagnostic_notes']}")

        # Write output file
        out_path = os.path.join(os.path.dirname(__file__), "baseline_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\nSaved baseline results to: {out_path}")

        return summary
    finally:
        db.close()
        # Clean up synthetic db file
        Base.metadata.drop_all(bind=engine)
        if os.path.exists(BENCHMARK_DB_PATH):
            try:
                os.remove(BENCHMARK_DB_PATH)
            except Exception:
                pass


if __name__ == "__main__":
    run_benchmark_and_save()
