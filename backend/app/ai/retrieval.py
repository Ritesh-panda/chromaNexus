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
    Uses native pgvector cosine distance operator (<=>) in PostgreSQL for fast similarity search.
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
                existing = db.query(DocumentChunkModel).filter(
                    DocumentChunkModel.chunk_id == chunk.chunk_id
                ).first()

                patient_id = chunk.metadata.get("patient_id")
                emb_list = list(emb) if emb is not None else None

                if existing:
                    existing.content = chunk.text
                    existing.page_number = chunk.page_number
                    existing.embedding = emb_list
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
                        embedding=emb_list,
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
            is_postgres = False
            if db.bind and hasattr(db.bind, "dialect") and db.bind.dialect.name == "postgresql":
                is_postgres = True

            if is_postgres:
                # Native PostgreSQL + pgvector vector similarity search
                query_obj = db.query(
                    DocumentChunkModel,
                    DocumentChunkModel.embedding.cosine_distance(query_emb).label("distance")
                ).filter(DocumentChunkModel.embedding != None)

                # Metadata filtering
                if filter_metadata:
                    if "patient_id" in filter_metadata and filter_metadata["patient_id"]:
                        query_obj = query_obj.filter(DocumentChunkModel.patient_id == filter_metadata["patient_id"])
                    if "document_id" in filter_metadata and filter_metadata["document_id"]:
                        query_obj = query_obj.filter(DocumentChunkModel.document_id == filter_metadata["document_id"])

                query_obj = query_obj.order_by(DocumentChunkModel.embedding.cosine_distance(query_emb))

                db_rows = query_obj.all()
                results: List[SearchResult] = []

                for item, dist in db_rows:
                    if dist is None:
                        continue
                    distance_val = float(dist)
                    sim = 1.0 - distance_val
                    norm_score = max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))

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

            else:
                # Fallback for SQLite / unit tests
                query_obj = db.query(DocumentChunkModel)
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

                    if hasattr(emb, "tolist"):
                        emb = emb.tolist()

                    sim = sum(q * e for q, e in zip(query_emb, emb))
                    norm_score = max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))

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


class ChromaDBVectorStore(VectorStore):
    """
    Embedded, persistent ChromaDB vector store for ChronaNexus.
    Runs completely in-process using SQLite and HNSW cosine indexing.
    Operates with offline BGE embeddings and supports metadata filtering (patient_id, document_id)
    for strict cross-patient isolation.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "chronanexus_clinical_chunks",
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        import chromadb
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.persist_directory = persist_directory

        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.EphemeralClient()

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        if not chunks:
            return

        import os
        is_test_env = bool(
            os.environ.get("PYTEST_CURRENT_TEST") or
            os.environ.get("CHRONANEXUS_TEST_ENV")
        )
        if is_test_env and self.persist_directory:
            abs_persist = os.path.abspath(self.persist_directory).lower()
            if "data\\chroma_db" in abs_persist or "data/chroma_db" in abs_persist:
                raise RuntimeError(
                    f"CRITICAL TEST ISOLATION FAILURE: Attempted mutation of protected persistent ChromaDB "
                    f"at '{abs_persist}' during test execution! Tests MUST use an isolated temporary directory."
                )

        if embeddings is None:
            texts = [c.text for c in chunks]
            embeddings = self.embedding_provider.embed_texts(texts)

        ids = []
        docs = []
        metadatas = []
        clean_embs = []

        for i, chunk in enumerate(chunks):
            c_id = chunk.chunk_id or f"chk_{chunk.document_id}_{chunk.chunk_index}"
            ids.append(c_id)
            docs.append(chunk.text)
            clean_embs.append(embeddings[i])

            meta = {
                "chunk_id": c_id,
                "document_id": str(chunk.document_id or ""),
                "page_number": int(chunk.page_number or 1),
                "chunk_index": int(chunk.chunk_index or 0)
            }
            if chunk.metadata:
                for k, v in chunk.metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        meta[k] = v
                    else:
                        meta[k] = str(v)
            metadatas.append(meta)

        self.collection.upsert(
            ids=ids,
            documents=docs,
            embeddings=clean_embs,
            metadatas=metadatas
        )

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        if not query or not query.strip():
            return []

        query_emb = self.embedding_provider.embed_text(query)

        where_clause = None
        if filter_metadata:
            conds = []
            for k, v in filter_metadata.items():
                if v is not None:
                    conds.append({k: {"$eq": v}})
            if len(conds) == 1:
                where_clause = conds[0]
            elif len(conds) > 1:
                where_clause = {"$and": conds}

        res = self.collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            where=where_clause
        )

        results: List[SearchResult] = []
        if not res or not res.get("ids") or not res["ids"][0]:
            return []

        for i, chunk_id in enumerate(res["ids"][0]):
            doc_text = res["documents"][0][i]
            meta = res["metadatas"][0][i] if res.get("metadatas") else {}
            dist = res["distances"][0][i] if res.get("distances") else 0.0

            sim = 1.0 - float(dist)
            norm_score = max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=meta.get("document_id", ""),
                page_number=meta.get("page_number", 1),
                chunk_index=meta.get("chunk_index", 0),
                text=doc_text,
                metadata=meta,
                character_count=len(doc_text)
            )
            results.append(SearchResult(chunk=chunk, score=norm_score))

        return results

    def delete_document(self, document_id: str) -> int:
        import os
        is_test_env = bool(
            os.environ.get("PYTEST_CURRENT_TEST") or
            os.environ.get("CHRONANEXUS_TEST_ENV")
        )
        if is_test_env and self.persist_directory:
            abs_persist = os.path.abspath(self.persist_directory).lower()
            if "data\\chroma_db" in abs_persist or "data/chroma_db" in abs_persist:
                raise RuntimeError(
                    f"CRITICAL TEST ISOLATION FAILURE: Attempted deletion from protected persistent ChromaDB "
                    f"at '{abs_persist}' during test execution! Tests MUST use an isolated temporary directory."
                )
        try:
            self.collection.delete(where={"document_id": document_id})
            return 1
        except Exception as e:
            logger.warning(f"ChromaDB delete error: {e}")
            return 0

    def dimension(self) -> int:
        return self.embedding_provider.dimension()

    def get_patient_chunks(self, patient_id: str) -> List[DocumentChunk]:
        """Fetch all indexed DocumentChunks for a specific patient."""
        try:
            res = self.collection.get(where={"patient_id": patient_id})
            if not res or not res.get("ids"):
                return []
            chunks = []
            for i, chunk_id in enumerate(res["ids"]):
                doc_text = res["documents"][i] if res.get("documents") else ""
                meta = res["metadatas"][i] if res.get("metadatas") else {}
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=meta.get("document_id"),
                    text=doc_text,
                    page_number=int(meta.get("page_number", 1)),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    metadata=meta
                ))
            return chunks
        except Exception as e:
            logger.warning(f"Error fetching patient chunks from ChromaDB: {e}")
            return []

    def sync_from_db(self, db: Session) -> int:
        """
        Synchronizes document chunks from the relational database into ChromaDB.
        Performs set-difference reconciliation: only chunks present in SQL but
        missing from ChromaDB are indexed. Existing valid vectors and metadata
        are strictly preserved without deletion or recreation.

        Limitation: Reconciles presence by chunk_id. Stale metadata or incompatible
        embeddings on existing vectors are preserved to avoid unsafe overwrites;
        any full vector re-indexing must be handled via an explicit maintenance process.

        Reuses valid precomputed embeddings (384-dimensional) or generates them if missing.
        Idempotent: safe to run repeatedly without creating duplicates.
        Handles empty SQL databases, empty Chroma collections, and partially
        populated Chroma collections.
        """
        try:
            from backend.app.models.document_chunk import DocumentChunkModel
            import json

            # 1. Read existing ChromaDB IDs
            existing_data = self.collection.get(include=[])
            existing_ids = set(existing_data.get("ids", [])) if existing_data else set()

            # 2. Read authoritative SQL chunks
            db_chunks = db.query(DocumentChunkModel).all()
            if not db_chunks:
                logger.info(f"ChromaDB sync: SQL database has no chunks. Current ChromaDB count: {self.collection.count()}")
                return self.collection.count()

            # 3. Identify missing chunks using set difference
            missing_chunks = [c for c in db_chunks if c.chunk_id and c.chunk_id not in existing_ids]
            if not missing_chunks:
                logger.info(f"ChromaDB sync: All {len(db_chunks)} SQL chunks already present in ChromaDB. No action needed.")
                return self.collection.count()

            logger.info(
                f"ChromaDB sync reconciliation: Found {len(db_chunks)} authoritative SQL chunks, "
                f"{len(existing_ids)} existing in ChromaDB. Indexing {len(missing_chunks)} missing chunks."
            )

            # 4. Prepare missing chunks and metadata
            chunks_to_add = []
            embeddings_to_add = []
            partial_errors = 0

            for c in missing_chunks:
                try:
                    emb = None
                    if c.embedding:
                        try:
                            emb = json.loads(c.embedding) if isinstance(c.embedding, str) else c.embedding
                            if not (isinstance(emb, list) and len(emb) == self.dimension()):
                                logger.warning(
                                    f"Chunk {c.chunk_id} has invalid/incompatible embedding (expected {self.dimension()} dimensions). Will re-embed."
                                )
                                emb = None
                        except Exception as parse_err:
                            logger.warning(f"Could not parse precomputed embedding for chunk {c.chunk_id}: {parse_err}")
                            emb = None

                    meta = dict(c.chunk_metadata or {})
                    meta["patient_id"] = str(c.patient_id or "")
                    meta["document_id"] = str(c.document_id or "")
                    meta["page_number"] = int(c.page_number or 1)
                    meta["chunk_index"] = int(c.chunk_index or 0)

                    chunk = DocumentChunk(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        text=c.content or "",
                        page_number=c.page_number or 1,
                        chunk_index=c.chunk_index or 0,
                        metadata=meta
                    )
                    chunks_to_add.append(chunk)
                    embeddings_to_add.append(emb)
                except Exception as prep_err:
                    partial_errors += 1
                    logger.error(f"Error preparing chunk {getattr(c, 'chunk_id', 'unknown')} for ChromaDB sync: {prep_err}")

            if not chunks_to_add:
                if partial_errors > 0:
                    logger.warning(f"ChromaDB sync: Encountered {partial_errors} preparation errors; no valid chunks to index.")
                return self.collection.count()

            # 5. Index missing chunks (generating embeddings for any missing/invalid ones)
            if all(e is not None and len(e) == self.dimension() for e in embeddings_to_add):
                self.add_documents(chunks_to_add, embeddings=embeddings_to_add)
            else:
                for idx, (chunk, emb) in enumerate(zip(chunks_to_add, embeddings_to_add)):
                    if emb is None:
                        try:
                            embeddings_to_add[idx] = self.embedding_provider.embed_text(chunk.text)
                        except Exception as emb_err:
                            logger.error(f"Failed to generate embedding for chunk {chunk.chunk_id}: {emb_err}")
                            partial_errors += 1

                valid_pairs = [(c, e) for c, e in zip(chunks_to_add, embeddings_to_add) if e is not None and len(e) == self.dimension()]
                if valid_pairs:
                    valid_chunks = [p[0] for p in valid_pairs]
                    valid_embeddings = [p[1] for p in valid_pairs]
                    self.add_documents(valid_chunks, embeddings=valid_embeddings)

            final_count = self.collection.count()
            logger.info(f"ChromaDB sync complete. Total collection count is now {final_count} (errors encountered: {partial_errors}).")
            return final_count
        except Exception as e:
            logger.error(f"Error during ChromaDB sync_from_db: {e}", exc_info=True)
            return self.collection.count()

    def health_check(self) -> bool:
        try:
            self.collection.count()
            return True
        except Exception:
            return False


def get_vector_store(
    backend: Optional[str] = None,
    db_session: Optional[Session] = None,
    persist_directory: Optional[str] = None,
    collection_name: Optional[str] = None,
    embedding_provider: Optional[EmbeddingProvider] = None
) -> VectorStore:
    """
    Factory to retrieve vector store.
    Defaults to configured VECTOR_STORE_BACKEND (e.g., 'chroma').
    """
    if not backend:
        try:
            from backend.app.core.config import settings
            backend = getattr(settings, "VECTOR_STORE_BACKEND", "chroma")
        except Exception:
            backend = "chroma"

    b = (backend or "chroma").lower()
    if b in ["chroma", "chromadb"]:
        if not persist_directory:
            try:
                from backend.app.core.config import settings
                persist_directory = getattr(settings, "CHROMA_PERSIST_DIRECTORY", None)
            except Exception:
                pass
        if not collection_name:
            try:
                from backend.app.core.config import settings
                collection_name = getattr(settings, "CHROMA_COLLECTION_NAME", "chronanexus_clinical_chunks")
            except Exception:
                collection_name = "chronanexus_clinical_chunks"
        return ChromaDBVectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_provider=embedding_provider
        )
    if b in ["postgres", "postgresql", "pgvector"]:
        return PostgresVectorStore(db_session=db_session, embedding_provider=embedding_provider)
    return InMemoryVectorStore(embedding_provider=embedding_provider)
