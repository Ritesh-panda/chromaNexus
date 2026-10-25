import io
import os
import hashlib
import pytest
import fitz
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import ExtractedEntity, LabResult, Medication, Disease
from backend.app.models.document_chunk import DocumentChunkModel
from backend.app.ai.extractors.pdf_extractor import (
    PDFExtractor,
    compute_file_checksum,
    compute_content_checksum
)
from backend.app.ai.chunker import DocumentChunker, detect_clinical_section
from backend.app.ai.document_processor import DocumentProcessor
from backend.app.ai.ingestion.orchestrator import DocumentIngestionOrchestrator
from backend.app.ai.retrieval import InMemoryVectorStore
from backend.app.ai.embeddings import LocalLightweightEmbeddingProvider


# ---------------------------------------------------------------------------
# PDF Helper Generators
# ---------------------------------------------------------------------------
def create_multipage_clinical_pdf(num_pages: int = 4) -> bytes:
    """Generates a complete multi-page PDF with > 2,000 characters."""
    doc = fitz.open()

    # Page 1: Hospital Header and Clinical History
    p1 = doc.new_page()
    p1.insert_text((50, 50), "METROPOLITAN GENERAL HOSPITAL\nCLINICAL ENCOUNTER NOTE")
    p1.insert_text((50, 90), "PATIENT: Johnathan Doe | MRN: 984512 | DATE: 2026-04-10")
    p1.insert_text((50, 130), "HISTORY OF PRESENT ILLNESS:\n" + ("The patient is a 54-year-old male with long-standing metabolic syndrome presenting for comprehensive annual review. He reports gradual onset of mild lethargy, intermittent bilateral lower extremity edema, and postprandial fatigue over the preceding three months. Denies acute chest pain, shortness of breath, palpitation, orthopnea, or paroxysmal nocturnal dyspnea. " * 3))

    # Page 2: Multi-column Vitals & Physical Exam
    p2 = doc.new_page()
    p2.insert_text((50, 50), "PHYSICAL EXAMINATION & VITAL SIGNS")
    p2.insert_text((50, 90), "VITAL SIGNS:\nBP: 138/88 mmHg\nPulse: 74 bpm\nTemp: 98.6 F\nSpO2: 99% on room air\nBMI: 29.4 kg/m2\nWaist Circumference: 98 cm")
    p2.insert_text((300, 90), "EXAMINATION:\nHEENT: Normocephalic, atraumatic.\nCardiovascular: Regular rate and rhythm, normal S1/S2, no murmurs, rubs, or gallops.\nPulmonary: Clear to auscultation bilaterally, no wheezes or rales.\nAbdomen: Soft, non-tender, non-distended, no hepatosplenomegaly.\nExtremities: 1+ pitting edema bilateral ankles.")

    # Page 3: Structured Lab Table
    p3 = doc.new_page()
    p3.insert_text((50, 50), "LABORATORY FINDINGS:")
    p3.draw_rect(fitz.Rect(50, 80, 520, 220))
    p3.draw_line(fitz.Point(50, 110), fitz.Point(520, 110))
    p3.draw_line(fitz.Point(200, 80), fitz.Point(200, 220))
    p3.draw_line(fitz.Point(280, 80), fitz.Point(280, 220))
    p3.draw_line(fitz.Point(360, 80), fitz.Point(360, 220))
    p3.draw_line(fitz.Point(460, 80), fitz.Point(460, 220))

    p3.insert_text((60, 100), "Test Name")
    p3.insert_text((210, 100), "Result")
    p3.insert_text((290, 100), "Units")
    p3.insert_text((370, 100), "Reference")
    p3.insert_text((470, 100), "Flag")

    p3.insert_text((60, 130), "Fasting Blood Glucose")
    p3.insert_text((210, 130), "126")
    p3.insert_text((290, 130), "mg/dL")
    p3.insert_text((370, 130), "70 - 99")
    p3.insert_text((470, 130), "HIGH")

    p3.insert_text((60, 160), "HbA1c")
    p3.insert_text((210, 160), "6.8")
    p3.insert_text((290, 160), "%")
    p3.insert_text((370, 160), "4.0 - 5.6")
    p3.insert_text((470, 160), "HIGH")

    p3.insert_text((60, 190), "Total Cholesterol")
    p3.insert_text((210, 190), "225")
    p3.insert_text((290, 190), "mg/dL")
    p3.insert_text((370, 190), "<200")
    p3.insert_text((470, 190), "HIGH")

    # Page 4: Assessment & Medications
    p4 = doc.new_page()
    p4.insert_text((50, 50), "ASSESSMENT & PLAN:")
    p4.insert_text((50, 90), "1. Type 2 Diabetes Mellitus - suboptimally controlled with elevated HbA1c.\n2. Essential Hypertension - borderline controlled.\n3. Hyperlipidemia - elevated total cholesterol.\n4. Comprehensive lifestyle counseling initiated.")
    p4.insert_text((50, 180), "MEDICATIONS:\n- Metformin 1000 mg twice daily\n- Lisinopril 20 mg once daily\n- Atorvastatin 20 mg at bedtime")

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_multipage_complete_extraction_no_truncation():
    """Verify that multi-page PDFs are completely extracted without arbitrary truncation."""
    pdf_bytes = create_multipage_clinical_pdf(num_pages=4)
    extractor = PDFExtractor()
    extracted = extractor.extract_from_bytes(
        file_bytes=pdf_bytes,
        file_name="complete_multipage_report.pdf",
        document_id="doc_mp_001"
    )

    assert extracted.total_pages == 4
    assert len(extracted.pages) == 4
    assert extracted.has_extractable_text is True
    assert extracted.is_scanned is False

    # Verify no arbitrary 3,000-character cap
    assert len(extracted.raw_text) > 1000
    assert "Fasting Blood Glucose" in extracted.raw_text
    assert "Metformin 1000 mg" in extracted.raw_text
    assert "HISTORY OF PRESENT ILLNESS" in extracted.raw_text

    # Page numbers must match 1, 2, 3, 4 exactly
    for idx, page in enumerate(extracted.pages, start=1):
        assert page.page_number == idx
        assert page.character_count > 0


def test_table_parsing_and_bounding_boxes():
    """Verify vector table extraction into markdown format with bounding boxes."""
    pdf_bytes = create_multipage_clinical_pdf(num_pages=4)
    extractor = PDFExtractor()
    extracted = extractor.extract_from_bytes(
        file_bytes=pdf_bytes,
        file_name="lab_table_report.pdf",
        document_id="doc_tbl_001"
    )

    p3 = extracted.pages[2]  # Page 3 contains table
    assert len(p3.tables) >= 1
    table = p3.tables[0]
    assert table.bounding_box is not None
    assert len(table.bounding_box) == 4
    assert table.bounding_box[0] >= 40

    # Ensure markdown table keeps test name, value, units, reference range on one row
    assert "|" in table.markdown
    assert "Fasting Blood Glucose" in table.markdown
    assert "126" in table.markdown
    assert "mg/dL" in table.markdown


def test_unruled_whitespace_table_parsing():
    """Verify that plain text/unruled tables with aligned columns format to markdown."""
    extractor = PDFExtractor()
    unruled_text = """
    Test Name                 Result      Units      Reference Interval    Status
    Hemoglobin A1c            6.8         %          4.0 - 5.6             HIGH
    Fasting Blood Glucose     126         mg/dL      70 - 99               HIGH
    Total Cholesterol         215         mg/dL      <200                  HIGH
    """
    formatted = extractor._format_aligned_text_table(unruled_text.strip())
    assert "| Test Name |" in formatted or "| Hemoglobin A1c |" in formatted
    assert "---" in formatted


def test_clinical_boundary_chunking_protects_table_rows():
    """Verify that chunks never split an individual markdown table row."""
    table_text = """
LABORATORY RESULTS:
| Test Name | Result | Units | Reference Interval | Flag |
| --- | --- | --- | --- | --- |
| Fasting Blood Glucose | 126 | mg/dL | 70 - 99 | HIGH |
| Hemoglobin A1c | 6.8 | % | 4.0 - 5.6 | HIGH |
| Total Cholesterol | 215 | mg/dL | <200 | HIGH |
| HDL Cholesterol | 42 | mg/dL | >40 | NORMAL |
| LDL Cholesterol | 145 | mg/dL | <100 | HIGH |
| Triglycerides | 160 | mg/dL | <150 | HIGH |

ASSESSMENT & PLAN:
Patient diagnosed with metabolic syndrome.
    """.strip()

    processor = DocumentProcessor()
    proc_doc = processor.process_text(table_text, document_id="doc_chunk_tbl")

    # Small chunk size to force table splitting across chunks
    chunker = DocumentChunker(chunk_size=180, chunk_overlap=30, preserve_tables=True)
    chunks = chunker.chunk_document(proc_doc)

    assert len(chunks) >= 2
    for chunk in chunks:
        lines = chunk.text.split("\n")
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("|") and not line_str.startswith("| ---"):
                assert line_str.endswith("|"), f"Table row was split mid-row: {line_str}"
                parts = [p.strip() for p in line_str.split("|")[1:-1]]
                assert len(parts) >= 3, f"Incomplete table columns: {line_str}"


def test_table_continuation_header_repetition():
    """Verify that when a table is split, the continuation chunk repeats the column headers."""
    table_text = """
LABORATORY RESULTS:
| Test Name | Result | Units | Reference Interval | Flag |
| --- | --- | --- | --- | --- |
| Fasting Blood Glucose | 126 | mg/dL | 70 - 99 | HIGH |
| Hemoglobin A1c | 6.8 | % | 4.0 - 5.6 | HIGH |
| Total Cholesterol | 215 | mg/dL | <200 | HIGH |
| HDL Cholesterol | 42 | mg/dL | >40 | NORMAL |
| LDL Cholesterol | 145 | mg/dL | <100 | HIGH |
| Triglycerides | 160 | mg/dL | <150 | HIGH |
    """.strip()

    processor = DocumentProcessor()
    proc_doc = processor.process_text(table_text, document_id="doc_split_hdr")

    chunker = DocumentChunker(chunk_size=200, chunk_overlap=40, preserve_tables=True)
    chunks = chunker.chunk_document(proc_doc)

    assert len(chunks) >= 2
    # Second chunk should contain the table headers
    assert "Test Name" in chunks[1].text
    assert "Result" in chunks[1].text


def test_checksum_deduplication_exact_binary(client: TestClient, db_session: Session):
    """Verify that uploading the exact same file twice returns HTTP 409 and avoids duplicate records."""
    pdf_bytes = create_multipage_clinical_pdf(num_pages=2)
    expected_checksum = hashlib.sha256(pdf_bytes).hexdigest()

    # First upload -> 201 Created
    response1 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("unique_report_v1.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"category": "blood_report", "hospital_name": "Metro General"}
    )
    assert response1.status_code == 201
    body1 = response1.json()
    first_report_id = body1["id"]

    # Verify report in database
    report = db_session.query(MedicalReport).filter(MedicalReport.id == first_report_id).first()
    assert report is not None
    assert report.checksum == expected_checksum

    # Second upload of the EXACT same bytes -> 409 Conflict
    response2 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("unique_report_v1_copy.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"category": "blood_report", "hospital_name": "Metro General", "on_duplicate": "reject"}
    )
    assert response2.status_code == 409
    body2 = response2.json()
    assert "detail" in body2
    assert body2["detail"]["code"] == "DUPLICATE_DOCUMENT"
    assert body2["detail"]["existing_report_id"] == first_report_id
    assert body2["detail"]["checksum"] == expected_checksum

    # Ensure no duplicate record was created
    dup_reports = db_session.query(MedicalReport).filter(MedicalReport.checksum == expected_checksum).all()
    assert len(dup_reports) == 1, "Duplicate report record was improperly created!"


def test_checksum_deduplication_return_existing_option(client: TestClient, db_session: Session):
    """Verify that on_duplicate='return_existing' returns existing report instead of error."""
    pdf_bytes = create_multipage_clinical_pdf(num_pages=2)

    # First upload
    res1 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("cbc_panel_return.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"category": "blood_report"}
    )
    assert res1.status_code == 201
    rep_id1 = res1.json()["id"]

    # Second upload with on_duplicate="return_existing"
    res2 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("cbc_panel_dup_return.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"category": "blood_report", "on_duplicate": "return_existing"}
    )
    assert res2.status_code in (200, 201)
    assert res2.json()["id"] == rep_id1


def test_distinguish_file_checksum_vs_content_checksum():
    """Verify distinct scope: file bytes SHA-256 vs clinical content SHA-256."""
    text1 = "Patient diagnosed with hypertension on 2026-01-01."
    text2 = "   Patient   diagnosed   with  hypertension   on   2026-01-01.   \n"

    bytes1 = text1.encode("utf-8")
    bytes2 = text2.encode("utf-8")
    assert compute_file_checksum(bytes1) != compute_file_checksum(bytes2)

    assert compute_content_checksum(text1) == compute_content_checksum(text2)


def test_safe_handling_scanned_and_empty_pdfs():
    """Verify that empty pages and scanned images are handled safely without exceptions."""
    extractor = PDFExtractor()

    # 1. Empty document
    empty_doc = fitz.open()
    p_empty = empty_doc.new_page()
    empty_bytes = empty_doc.tobytes()
    empty_doc.close()

    res_empty = extractor.extract_from_bytes(empty_bytes, "empty.pdf", "doc_empty")
    assert res_empty.total_pages == 1
    assert res_empty.pages[0].is_empty is True
    assert res_empty.has_extractable_text is False

    # 2. Corrupt bytes
    corrupt_bytes = b"%PDF-1.4\nSome random garbage that is not valid PDF"
    res_corrupt = extractor.extract_from_bytes(corrupt_bytes, "corrupt.pdf", "doc_corrupt")
    assert res_corrupt.has_extractable_text is False
    assert res_corrupt.is_scanned is True
    assert "error" in res_corrupt.metadata


def test_end_to_end_orchestrator_pipeline_preserves_provenance(db_session: Session):
    """
    Test the complete end-to-end upload -> extraction -> chunking -> persistence pipeline.
    Verify page numbers, complete raw text, and checksums are persisted.
    """
    patient = db_session.query(Patient).first()
    assert patient is not None

    pdf_bytes = create_multipage_clinical_pdf(num_pages=4)
    file_checksum = hashlib.sha256(pdf_bytes).hexdigest()

    # Create Report row
    report = MedicalReport(
        patient_id=patient.id,
        title="Complete 4-Page Clinical Note",
        file_name="multipage_note.pdf",
        file_size=len(pdf_bytes),
        file_type="application/pdf",
        category="blood_report",
        hospital_name="Metropolitan Hospital",
        report_date="2026-04-10",
        checksum=file_checksum,
        status="processing"
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    # Ingest through orchestrator with fast local embedding provider
    emb_provider = LocalLightweightEmbeddingProvider()
    v_store = InMemoryVectorStore(embedding_provider=emb_provider)
    orchestrator = DocumentIngestionOrchestrator(
        embedding_provider=emb_provider,
        vector_store=v_store
    )
    success = orchestrator.process_document(
        document_id=report.id,
        file_bytes=pdf_bytes,
        file_name=report.file_name,
        patient_id=patient.id,
        db=db_session,
        report_date=report.report_date,
        hospital_name=report.hospital_name
    )

    assert success is True

    # Verify report record
    db_session.refresh(report)
    assert report.status == "completed"
    assert report.page_count == 4
    assert len(report.raw_text) > 1000
    assert "Fasting Blood Glucose" in report.raw_text

    # Verify extracted entities have page provenance
    entities = db_session.query(ExtractedEntity).filter(ExtractedEntity.report_id == report.id).all()
    assert len(entities) > 0
    for ent in entities:
        assert ent.source_page_number in [1, 2, 3, 4]

    # Verify lab results have page provenance
    labs = db_session.query(LabResult).filter(LabResult.source_report_id == report.id).all()
    assert len(labs) >= 1
    for lab in labs:
        assert lab.source_page_number in [1, 2, 3, 4]
        assert lab.extraction_confidence is not None

    # Verify vector store received chunks with page numbers
    assert len(v_store._chunks) > 1
    page_numbers = {c.page_number for c in v_store._chunks.values()}
    assert len(page_numbers) > 1
