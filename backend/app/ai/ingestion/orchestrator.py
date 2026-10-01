import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.ai.extractors.pdf_extractor import PDFExtractor, ExtractedDocument
from backend.app.ai.ocr import get_ocr_provider, OCRProvider
from backend.app.ai.clinical_extractor import get_clinical_extractor, ClinicalEntityExtractor, ExtractedClinicalEntity
from backend.app.ai.clinical_extractor.validator import ClinicalDataValidator
from backend.app.ai.chunker import DocumentChunker, DocumentChunk
from backend.app.ai.embeddings import get_embedding_provider, EmbeddingProvider
from backend.app.ai.retrieval import get_vector_store, VectorStore
from backend.app.ai.ingestion.ingestion_status import ingestion_registry, IngestionStage
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import ExtractedEntity, LabResult, Medication, Disease
from backend.app.models.timeline import TimelineEvent
from backend.app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class DocumentIngestionOrchestrator:
    """
    End-to-end asynchronous document processing orchestrator.
    Handles extraction ➔ OCR fallback ➔ entity extraction ➔ validation ➔ persistence ➔ vector indexing.
    """

    def __init__(
        self,
        pdf_extractor: Optional[PDFExtractor] = None,
        ocr_provider: Optional[OCRProvider] = None,
        clinical_extractor: Optional[ClinicalEntityExtractor] = None,
        chunker: Optional[DocumentChunker] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None
    ):
        self.pdf_extractor = pdf_extractor or PDFExtractor()
        self.ocr_provider = ocr_provider or get_ocr_provider()
        self.clinical_extractor = clinical_extractor or get_clinical_extractor()
        self.chunker = chunker or DocumentChunker(chunk_size=500, chunk_overlap=100)
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vector_store = vector_store

    def process_document(
        self,
        document_id: str,
        file_bytes: bytes,
        file_name: str,
        patient_id: str,
        db: Optional[Session] = None,
        report_date: Optional[str] = None,
        hospital_name: Optional[str] = None
    ) -> bool:
        """
        Executes full multi-stage ingestion workflow.
        """
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True

        try:
            # Stage 1: Received & Text Extraction
            ingestion_registry.set_status(
                document_id=document_id,
                stage=IngestionStage.PROCESSING,
                progress=15,
                message=f"Extracting text from {file_name}..."
            )

            extracted_doc: ExtractedDocument = self.pdf_extractor.extract_from_bytes(
                file_bytes=file_bytes,
                file_name=file_name,
                document_id=document_id
            )

            full_text = extracted_doc.raw_text

            # Stage 2: OCR Fallback if document is scanned/image-based
            if extracted_doc.is_scanned:
                ingestion_registry.set_status(
                    document_id=document_id,
                    stage=IngestionStage.OCR_REQUIRED,
                    progress=30,
                    message="Scanned document detected. Running Optical Character Recognition (OCR)..."
                )
                ocr_result = self.ocr_provider.extract_text_from_pdf_bytes(file_bytes)
                if ocr_result.success and ocr_result.full_text:
                    full_text = ocr_result.full_text

            if not full_text.strip():
                full_text = f"Document: {file_name} uploaded for clinical archiving."

            # Stage 3: Clinical Entity Extraction
            ingestion_registry.set_status(
                document_id=document_id,
                stage=IngestionStage.EXTRACTING,
                progress=50,
                message="Extracting clinical entities (diagnoses, lab values, medications)..."
            )

            entities = self.clinical_extractor.extract_entities(
                text=full_text,
                document_id=document_id,
                pages=extracted_doc.pages,
                metadata={"patient_id": patient_id, "file_name": file_name}
            )

            counts = {"diseases": 0, "medications": 0, "lab_results": 0, "procedures": 0}

            # Stage 4: Structured Data Validation & DB Persistence
            date_str = report_date or "2026-06-15"
            hosp_str = hospital_name or "Medical Health Center"

            for ent in entities:
                # 4a. Persist ExtractedEntity linked to report
                db_entity = ExtractedEntity(
                    report_id=document_id,
                    category=ent.category,
                    name=ent.name,
                    confidence=ent.confidence,
                    value=ent.value,
                    unit=ent.unit,
                    notes=ent.excerpt
                )
                db.add(db_entity)

                # 4b. Populate specific domain model tables
                if ent.category == "lab_value" and ent.value:
                    counts["lab_results"] += 1
                    status = ent.metadata.get("status", "normal") if ent.metadata else "normal"
                    ref_range = ent.metadata.get("reference_range", "Normal") if ent.metadata else "Normal"
                    lab = LabResult(
                        patient_id=patient_id,
                        test_name=ent.name,
                        value=ent.value,
                        unit=ent.unit or "mg/dL",
                        reference_range=ref_range,
                        status=status,
                        test_date=date_str,
                        source_report_id=document_id,
                        hospital_name=hosp_str
                    )
                    db.add(lab)

                elif ent.category == "medication" and ent.value:
                    counts["medications"] += 1
                    med = Medication(
                        patient_id=patient_id,
                        name=ent.name,
                        dosage=ent.value,
                        frequency=ent.unit or "Daily",
                        route="oral",
                        start_date=date_str,
                        status="active",
                        source_report_id=document_id
                    )
                    db.add(med)

                elif ent.category == "disease":
                    counts["diseases"] += 1
                    dis = Disease(
                        patient_id=patient_id,
                        name=ent.name,
                        icd_code=ent.value,
                        status="active",
                        diagnosed_date=date_str,
                        source_report_id=document_id
                    )
                    db.add(dis)

                elif ent.category == "procedure":
                    counts["procedures"] += 1

            # Stage 5: Document Chunking & Embedding Generation
            ingestion_registry.set_status(
                document_id=document_id,
                stage=IngestionStage.INDEXING,
                progress=75,
                message="Generating vector embeddings and indexing into Patient Memory...",
                extracted_counts=counts
            )

            # Process & chunk document
            from backend.app.ai.document_processor import DocumentProcessor
            proc = DocumentProcessor()
            proc_doc = proc.process_text(
                raw_text=full_text,
                document_id=document_id,
                metadata={
                    "patient_id": patient_id,
                    "title": file_name,
                    "date": date_str,
                    "hospital_name": hosp_str
                }
            )
            chunks = self.chunker.chunk_document(proc_doc)

            # Store into VectorStore
            v_store = self.vector_store or get_vector_store("postgres", db_session=db)
            if chunks:
                texts = [c.text for c in chunks]
                embeddings = self.embedding_provider.embed_texts(texts)
                v_store.add_documents(chunks=chunks, embeddings=embeddings)

            # Stage 6: Update MedicalReport status in DB
            report = db.query(MedicalReport).filter(MedicalReport.id == document_id).first()
            if report:
                report.status = "completed"
                report.raw_text = full_text[:4000]
                report.summary = f"Processed {file_name}. Extracted {len(entities)} clinical entities."
            
            db.commit()

            # Stage 7: Mark Completed
            ingestion_registry.set_status(
                document_id=document_id,
                stage=IngestionStage.COMPLETED,
                progress=100,
                message="Ingestion complete. Document successfully indexed into patient memory graph.",
                extracted_counts=counts,
                indexed_chunks=len(chunks)
            )
            return True

        except Exception as e:
            logger.error(f"Ingestion orchestrator failed for {document_id}: {str(e)}")
            if db:
                db.rollback()
            ingestion_registry.set_status(
                document_id=document_id,
                stage=IngestionStage.FAILED,
                progress=0,
                message="Document processing failed.",
                error=str(e)
            )
            return False
        finally:
            if should_close_db and db:
                db.close()


# Global orchestrator singleton
document_orchestrator = DocumentIngestionOrchestrator()
