import pytest
from backend.app.models.document_chunk import DocumentChunkModel


def test_document_chunk_model_instantiation():
    chunk = DocumentChunkModel(
        document_id="rep_002",
        patient_id="pat_001",
        chunk_id="rep_002_p1_c0",
        chunk_index=0,
        page_number=1,
        content="Quest Diagnostics Lipid Profile: Total Cholesterol 242 mg/dL.",
        embedding=[0.1, 0.2, 0.3],
        chunk_metadata={"category": "blood_report"}
    )

    assert chunk.document_id == "rep_002"
    assert chunk.patient_id == "pat_001"
    assert chunk.chunk_id == "rep_002_p1_c0"
    assert chunk.page_number == 1
    assert chunk.embedding == [0.1, 0.2, 0.3]
    assert chunk.chunk_metadata["category"] == "blood_report"
