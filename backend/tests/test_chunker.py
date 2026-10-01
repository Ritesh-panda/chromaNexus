import pytest
from backend.app.ai.document_processor import DocumentProcessor
from backend.app.ai.chunker import DocumentChunker, DocumentChunk


def test_chunker_validation():
    with pytest.raises(ValueError):
        DocumentChunker(chunk_size=0)

    with pytest.raises(ValueError):
        DocumentChunker(chunk_size=200, chunk_overlap=250)


def test_chunker_preserves_page_metadata_and_indices():
    processor = DocumentProcessor()
    text_p1 = "Paragraph A. " * 30  # ~390 chars
    text_p2 = "Paragraph B. " * 40  # ~520 chars
    
    doc = processor.process_pages(
        pages_input=[
            {"page_number": 1, "text": text_p1},
            {"page_number": 2, "text": text_p2}
        ],
        document_id="doc_chk_01",
        metadata={"patient_id": "pat_alex_001", "doctor": "Dr. Sarah Jenkins"}
    )

    chunker = DocumentChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 2
    for idx, c in enumerate(chunks):
        assert isinstance(c, DocumentChunk)
        assert c.document_id == "doc_chk_01"
        assert c.page_number in [1, 2]
        assert c.chunk_index == idx
        assert c.metadata["patient_id"] == "pat_alex_001"
        assert c.metadata["doctor"] == "Dr. Sarah Jenkins"
        assert c.character_count > 0


def test_chunker_deterministic_output():
    processor = DocumentProcessor()
    raw = "The patient was prescribed Metformin 500mg BID and Lisinopril 10mg QD on November 4, 2023. Fasting blood sugar levels monitored weekly."
    doc = processor.process_text(raw, document_id="doc_det_01")

    chunker1 = DocumentChunker(chunk_size=60, chunk_overlap=15)
    chunker2 = DocumentChunker(chunk_size=60, chunk_overlap=15)

    chunks1 = chunker1.chunk_document(doc)
    chunks2 = chunker2.chunk_document(doc)

    assert len(chunks1) == len(chunks2)
    for c1, c2 in zip(chunks1, chunks2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.text == c2.text
