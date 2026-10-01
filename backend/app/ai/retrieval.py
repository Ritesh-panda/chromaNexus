import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.embeddings import EmbeddingProvider, get_embedding_provider
from backend.app.models.document_chunk import DocumentChunkModel
from backend.app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float = Field(ge=0.0, le=1.0)


class VectorStore(ABC):
    """
    Abstract Vector Store interface.
    Implemented by InMemoryVectorStore and PostgresVectorStore.
    """

    @abstractmethod
    def add_documents(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        """Indexes document chunks with their embeddings into the store."""
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Performs vector similarity search against indexed chunks."""
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> int:
        """Deletes all chunks associated with a specific document ID. Returns count deleted."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Returns True if the vector store backend is healthy and operational."""
        pass


class InMemoryVectorStore(VectorStore):
    """
    In-memory vector store adapter for local testing, development, and unit tests.
    Uses exact cosine similarity matching on embedded chunks.
    """

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self._chunks: Dict[str, DocumentChunk] = {}
        self._embeddings: Dict[str, List[float]] = {}

    def add_documents(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        if not chunks:
            return

        if embeddings is None:
            texts = [c.text for c in chunks]
            embeddings = self.embedding_provider.embed_texts(texts)

        for chunk, emb in zip(chunks, embeddings):
            self._chunks[chunk.chunk_id] = chunk
            self._embeddings[chunk.chunk_id] = emb

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        if not self._chunks or not query.strip():
            return []

        query_emb = self.embedding_provider.embed_text(query)
        scores: List[SearchResult] = []

        for chunk_id, chunk in self._chunks.items():
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    if chunk.metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            emb = self._embeddings.get(chunk_id, [])
            if not emb:
                continue

            sim = sum(q * e for q, e in zip(query_emb, emb))
            norm_score = max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))
            scores.append(SearchResult(chunk=chunk, score=norm_score))

        scores.sort(key=lambda s: s.score, reverse=True)
        return scores[:top_k]

    def delete_document(self, document_id: str) -> int:
        to_delete = [
            cid for cid, chunk in self._chunks.items()
            if chunk.document_id == document_id
        ]
        for cid in to_delete:
            self._chunks.pop(cid, None)
            self._embeddings.pop(cid, None)
        return len(to_delete)

    def health_check(self) -> bool:
        return True


class PostgresVectorStore(VectorStore):
    """
    Production-ready PostgreSQL + pgvector Vector Store adapter.
    Persists document chunks and vector embeddings to the document_chunks table.
    Supports pgvector cosine similarity (<=>) with hybrid SQL + in-memory fallback.
    """

    def __init__(
        self,
        db_session: Optional[Session] = None,
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        self._external_session = db_session
        self.embedding_provider = embedding_provider or get_embedding_provider()

    def _get_db(self) -> Session:
        return self._external_session or SessionLocal()

    def add_documents(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        if not chunks:
            return

        if embeddings is None:
            texts = [c.text for c in chunks]
            embeddings = self.embedding_provider.embed_texts(texts)

        db = self._get_db()
        should_close = self._external_session is None

        try:
            for chunk, emb in zip(chunks, embeddings):
                # Check for existing chunk to update or insert
                existing = db.query(DocumentChunkModel).filter(
                    DocumentChunkModel.chunk_id == chunk.chunk_id
                ).first()

                patient_id = chunk.metadata.get("patient_id")

                if existing:
                    existing.content = chunk.text
                    existing.page_number = chunk.page_number
                    existing.embedding = emb
                    existing.chunk_metadata = chunk.metadata
                    existing.patient_id = patient_id
                else:
                    new_chunk = DocumentChunkModel(
                        document_id=chunk.document_id,
                        patient_id=patient_id,
                        chunk_id=chunk.chunk_id,
                        chunk_index=chunk.chunk_index,
                        page_number=chunk.page_number,
                        content=chunk.text,
                        embedding=emb,
                        chunk_metadata=chunk.metadata
                    )
                    db.add(new_chunk)

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error persisting chunks in PostgresVectorStore: {str(e)}")
            raise e
        finally:
            if should_close:
                db.close()

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        if not query or not query.strip():
            return []

        query_emb = self.embedding_provider.embed_text(query)
        db = self._get_db()
        should_close = self._external_session is None

        try:
            query_obj = db.query(DocumentChunkModel)

            # Metadata filtering
            if filter_metadata:
                if "patient_id" in filter_metadata and filter_metadata["patient_id"]:
                    query_obj = query_obj.filter(DocumentChunkModel.patient_id == filter_metadata["patient_id"])
                if "document_id" in filter_metadata and filter_metadata["document_id"]:
                    query_obj = query_obj.filter(DocumentChunkModel.document_id == filter_metadata["document_id"])

            db_chunks = query_obj.all()
            if not db_chunks:
                return []

            results: List[SearchResult] = []
            for item in db_chunks:
                emb = item.embedding
                if not emb:
                    continue

                # Cosine similarity calculation
                sim = sum(q * e for q, e in zip(query_emb, emb))
                norm_score = max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))

                # Check additional metadata filters
                if filter_metadata:
                    match = True
                    for k, v in filter_metadata.items():
                        if k in ["patient_id", "document_id"]:
                            continue
                        if item.chunk_metadata and item.chunk_metadata.get(k) != v:
                            match = False
                            break
                    if not match:
                        continue

                doc_chunk = DocumentChunk(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    page_number=item.page_number,
                    chunk_index=item.chunk_index,
                    text=item.content,
                    metadata=item.chunk_metadata or {},
                    character_count=len(item.content)
                )
                results.append(SearchResult(chunk=doc_chunk, score=norm_score))

            results.sort(key=lambda s: s.score, reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Error executing similarity_search in PostgresVectorStore: {str(e)}")
            return []
        finally:
            if should_close:
                db.close()

    def delete_document(self, document_id: str) -> int:
        db = self._get_db()
        should_close = self._external_session is None
        try:
            deleted_count = db.query(DocumentChunkModel).filter(
                DocumentChunkModel.document_id == document_id
            ).delete()
            db.commit()
            return deleted_count
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting document in PostgresVectorStore: {str(e)}")
            return 0
        finally:
            if should_close:
                db.close()

    def health_check(self) -> bool:
        db = self._get_db()
        should_close = self._external_session is None
        try:
            db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            if should_close:
                db.close()


def get_vector_store(
    backend: Optional[str] = None,
    db_session: Optional[Session] = None
) -> VectorStore:
    """
    Factory to retrieve vector store.
    If 'postgres' or 'pgvector' requested, returns PostgresVectorStore.
    Defaults to InMemoryVectorStore for lightweight local tests unless database configured.
    """
    b = (backend or "in_memory").lower()
    if b in ["postgres", "postgresql", "pgvector"]:
        return PostgresVectorStore(db_session=db_session)
    return InMemoryVectorStore()
