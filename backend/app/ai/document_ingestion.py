import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.ai.document_processor import DocumentProcessor, ProcessedDocument
from backend.app.ai.chunker import DocumentChunker, DocumentChunk
from backend.app.ai.embeddings import EmbeddingProvider, get_embedding_provider
from backend.app.ai.retrieval import VectorStore, PostgresVectorStore, InMemoryVectorStore

logger = logging.getLogger(__name__)


class IngestionResult(BaseModel):
    document_id: str
    total_chunks: int
    total_characters: int
    success: bool
    error: Optional[str] = None


class DocumentIngestionPipeline:
    """
    End-to-end document ingestion pipeline:
    Raw Text / OCR ➔ DocumentProcessor ➔ DocumentChunker ➔ EmbeddingProvider ➔ VectorStore
    """

    def __init__(
        self,
        processor: Optional[DocumentProcessor] = None,
        chunker: Optional[DocumentChunker] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None
    ):
        self.processor = processor or DocumentProcessor()
        self.chunker = chunker or DocumentChunker(chunk_size=500, chunk_overlap=100)
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vector_store = vector_store or InMemoryVectorStore(embedding_provider=self.embedding_provider)

    def ingest_document(
        self,
        raw_text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        pages_input: Optional[List[Dict[str, Any]]] = None
    ) -> IngestionResult:
        try:
            # 1. Process & clean text
            if pages_input:
                proc_doc = self.processor.process_pages(
                    pages_input=pages_input,
                    document_id=document_id,
                    metadata=metadata
                )
            else:
                proc_doc = self.processor.process_text(
                    raw_text=raw_text,
                    document_id=document_id,
                    metadata=metadata
                )

            if not proc_doc.pages or proc_doc.total_characters == 0:
                return IngestionResult(
                    document_id=document_id,
                    total_chunks=0,
                    total_characters=0,
                    success=False,
                    error="No valid text extracted from document"
                )

            # 2. Chunk document
            chunks = self.chunker.chunk_document(proc_doc)

            # 3. Generate embeddings
            texts = [c.text for c in chunks]
            embeddings = self.embedding_provider.embed_texts(texts)

            # 4. Store into VectorStore
            self.vector_store.add_documents(chunks=chunks, embeddings=embeddings)

            return IngestionResult(
                document_id=document_id,
                total_chunks=len(chunks),
                total_characters=proc_doc.total_characters,
                success=True
            )
        except Exception as e:
            logger.error(f"Error in DocumentIngestionPipeline for {document_id}: {str(e)}")
            return IngestionResult(
                document_id=document_id,
                total_chunks=0,
                total_characters=0,
                success=False,
                error=str(e)
            )
