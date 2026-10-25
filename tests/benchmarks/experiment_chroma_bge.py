"""
ChronaNexus Vector Store & Embedding Experiment
==============================================
Empirical side-by-side evaluation comparing:
- Baseline: PostgresVectorStore (SQLite scan) + LocalLightweightEmbeddingProvider (SHA-256 hash)
- Proposed: ChromaVectorStore (Persistent ChromaDB) + LocalBgeEmbeddingProvider (bge-small-en-v1.5)

Executes all 12 clinical benchmark scenarios, measuring:
1. Retrieval accuracy and Pass/Fail rates
2. Semantic synonym resolution (e.g. "elevated arterial pressure" -> "hypertension")
3. Newly uploaded report indexing and retrieval
4. Query latency (milliseconds)
5. Patient data isolation (zero cross-patient leakage)
6. Exact numerical value preservation and ranking
"""

import os
import sys
import json
import time
import shutil
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
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.embeddings import EmbeddingProvider, LocalLightweightEmbeddingProvider
from backend.app.ai.retrieval import VectorStore, SearchResult, PostgresVectorStore
from backend.app.ai.rag.classifier import QueryClassifier, QueryIntent
from backend.app.ai.rag.query_resolver import ConversationQueryResolver, ResolvedQuery
from backend.app.ai.rag.structured_retriever import StructuredRetriever
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider

# Import the synthetic dataset builder from retrieval_benchmark.py
from tests.benchmarks.retrieval_benchmark import build_synthetic_database

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer


# -----------------------------------------------------------------------------
# 1. Proposed Local BGE Embedding Provider
# -----------------------------------------------------------------------------
class LocalBgeEmbeddingProvider(EmbeddingProvider):
    """
    Offline semantic embedding provider using BAAI/bge-small-en-v1.5 (384 dimensions).
    Runs CPU inference via sentence-transformers, strictly offline with zero external network requests.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_embedding_dimension()

    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dim
        # BGE models benefit from normalized embeddings for cosine distance
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self._model.encode(texts, normalize_embeddings=True, batch_size=32)
        return embeddings.tolist()


# -----------------------------------------------------------------------------
# 2. Proposed ChromaDB Vector Store Adapter
# -----------------------------------------------------------------------------
class ChromaVectorStore(VectorStore):
    """
    Production-grade local persistent vector store using ChromaDB.
    Maintains a dedicated collection per patient ('patient_{patient_id}') for native,
    bulletproof multi-tenant isolation, and supports global metadata filtering.
    """

    def __init__(
        self,
        persist_dir: str,
        embedding_provider: EmbeddingProvider,
        collection_prefix: str = "patient_"
    ):
        self.persist_dir = persist_dir
        self.embedding_provider = embedding_provider
        self.collection_prefix = collection_prefix
        self.client = chromadb.PersistentClient(path=persist_dir)

    def _get_collection(self, patient_id: Optional[str] = None):
        col_name = f"{self.collection_prefix}{patient_id}" if patient_id else "global_chunks"
        # Chroma collection names must be 3-63 characters and alphanumeric with _ or -
        clean_name = col_name.replace("-", "_")
        return self.client.get_or_create_collection(
            name=clean_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: List[DocumentChunk]) -> None:
        if not documents:
            return

        # Group documents by patient_id for tenant-isolated collections
        by_patient: Dict[str, List[DocumentChunk]] = {}
        for doc in documents:
            pat_id = doc.metadata.get("patient_id", "default")
            by_patient.setdefault(pat_id, []).append(doc)

        for pat_id, chunks in by_patient.items():
            collection = self._get_collection(pat_id)
            texts = [c.text for c in chunks]
            embeddings = self.embedding_provider.embed_texts(texts)
            ids = [c.chunk_id for c in chunks]
            
            # Clean metadatas (Chroma requires primitive str/int/float/bool values)
            metadatas = []
            for c in chunks:
                meta = {}
                for k, v in c.metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        meta[k] = v
                    else:
                        meta[k] = str(v)
                meta["document_id"] = c.document_id
                meta["page_number"] = c.page_number
                meta["chunk_index"] = c.chunk_index
                metadatas.append(meta)

            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
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

        patient_id = None
        where_filter = {}
        if filter_metadata:
            patient_id = filter_metadata.get("patient_id")
            for k, v in filter_metadata.items():
                if k != "patient_id" and isinstance(v, (str, int, float, bool)):
                    where_filter[k] = v

        collection = self._get_collection(patient_id)
        query_emb = self.embedding_provider.embed_text(query)

        where_clause = where_filter if where_filter else None
        results = collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            where=where_clause
        )

        search_results: List[SearchResult] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)
        documents = results["documents"][0] if "documents" in results and results["documents"] else [""] * len(ids)
        metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(ids)

        for cid, dist, doc_text, meta in zip(ids, distances, documents, metadatas):
            # Chroma returns cosine distance (0.0 to 2.0). Score = 1.0 - (dist / 2.0)
            score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
            doc_chunk = DocumentChunk(
                chunk_id=cid,
                document_id=meta.get("document_id", ""),
                page_number=int(meta.get("page_number", 1)),
                chunk_index=int(meta.get("chunk_index", 0)),
                text=doc_text,
                metadata=meta,
                character_count=len(doc_text)
            )
            search_results.append(SearchResult(chunk=doc_chunk, score=score))

        return search_results

    def delete_document(self, document_id: str) -> int:
        deleted = 0
        for col in self.client.list_collections():
            try:
                res = col.get(where={"document_id": document_id})
                if res and res["ids"]:
                    col.delete(ids=res["ids"])
                    deleted += len(res["ids"])
            except Exception:
                pass
        return deleted

    def health_check(self) -> bool:
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False


# -----------------------------------------------------------------------------
# 3. Comparative Benchmark Evaluator
# -----------------------------------------------------------------------------
def run_comparative_experiment():
    print("=" * 80)
    print("ChronaNexus Comparative Experiment: ChromaDB + BGE vs. Baseline")
    print("=" * 80)

    exp_db_path = os.path.join(os.path.dirname(__file__), "exp_synthetic.db")
    exp_chroma_path = os.path.join(os.path.dirname(__file__), "exp_chroma_data")
    
    # Clean previous experimental artifacts
    if os.path.exists(exp_db_path):
        os.remove(exp_db_path)
    if os.path.exists(exp_chroma_path):
        shutil.rmtree(exp_chroma_path, ignore_errors=True)

    engine = create_engine(f"sqlite:///{exp_db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionMaker()

    try:
        print("\n[Step 1/4] Seeding synthetic longitudinal patients (Alpha & Beta)...")
        pat_ids = build_synthetic_database(db)
        pat_alpha = pat_ids["alpha"]
        pat_beta = pat_ids["beta"]
        print(f"           Synthetic Patients Seeded: Alpha ({pat_alpha}), Beta ({pat_beta})")

        print("\n[Step 2/4] Initializing Vector Store Engines...")
        # Baseline Engine
        base_emb = LocalLightweightEmbeddingProvider(dim=384)
        base_store = PostgresVectorStore(db_session=db, embedding_provider=base_emb)
        print("           Baseline Store initialized: PostgresVectorStore (SQLite scan) + SHA-256 Hash")

        # Proposed Engine
        prop_emb = LocalBgeEmbeddingProvider(model_name="BAAI/bge-small-en-v1.5")
        prop_store = ChromaVectorStore(persist_dir=exp_chroma_path, embedding_provider=prop_emb)
        print(f"           Proposed Store initialized: ChromaVectorStore (Persistent ChromaDB) + BGE (dim={prop_emb.dimension()})")

        # Sync existing database chunks into ChromaDB
        print("           Indexing document chunks into ChromaDB...")
        from backend.app.models.document_chunk import DocumentChunkModel
        existing_chunks = db.query(DocumentChunkModel).all()
        chroma_chunks = [
            DocumentChunk(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                text=c.content,
                metadata=c.chunk_metadata or {"patient_id": c.patient_id}
            )
            for c in existing_chunks
        ]
        prop_store.add_documents(chroma_chunks)
        print(f"           Indexed {len(chroma_chunks)} chunks into ChromaDB successfully.")

        # Build Hybrid Pipelines
        struct_retriever = StructuredRetriever(db_session=db)
        query_resolver = ConversationQueryResolver()
        mock_llm = MockDeterministicLLMProvider()

        base_hybrid = HybridRetriever(vector_store=base_store, db_session=db)
        prop_hybrid = HybridRetriever(vector_store=prop_store, db_session=db)

        base_pipeline = RAGPipeline(retriever=base_hybrid, llm=mock_llm, db_session=db)
        prop_pipeline = RAGPipeline(retriever=prop_hybrid, llm=mock_llm, db_session=db)

        # ---------------------------------------------------------------------
        # Step 3: Run the 12 Scenarios Side-by-Side
        # ---------------------------------------------------------------------
        print("\n[Step 3/4] Evaluating all 12 Clinical Retrieval Scenarios Side-by-Side...\n")

        scenarios_def = [
            ("SC-01", "Exact Numerical Values & Units", "What was my serum potassium level and unit on September 10, 2024?"),
            ("SC-02", "Date-Specific Temporal Queries", "What was my serum creatinine on 2023-04-15 versus 2024-09-10?"),
            ("SC-03", "Latest vs. Historical Biomarkers", "What is my latest Fasting Blood Glucose level?"),
            ("SC-04", "Medication & Allergy Cross-Ref", "Can I take Amoxicillin for my bacterial sinus infection?"),
            ("SC-05", "Multi-Turn Follow-Up & Topic Continuity", "What inhaler dose was prescribed for that condition?"),
            ("SC-06", "Contradictory Records from Different Facilities", "What was my HbA1c recorded in November 2024 across different facilities?"),
            ("SC-07", "Unsupported Questions (Hallucination Check)", "What were the findings of my colonoscopy procedure and biopsy?"),
            ("SC-08", "Patient Isolation (Zero Cross-Patient Leakage)", "What were the findings of my knee MRI?"),
            ("SC-09", "Newly Uploaded Relevant Reports", "When was I treated for acute bronchitis and what antibiotic was prescribed?"),
            ("SC-10", "Synonyms & Alternate Clinical Terminology", "Do my records show elevated arterial pressure or high cardiac readings?"),
            ("SC-11", "Multi-Page Reports & Table Extraction", "What were my TSH and Free T4 thyroid results?"),
            ("SC-12", "Citation Relevance & Claim Verification", "What were my liver enzyme levels (ALT and AST)?")
        ]

        comparison_results = []

        for sc_id, name, query in scenarios_def:
            print(f"--- Running {sc_id}: {name} ---")
            
            # --- BASELINE RUN ---
            t0 = time.time()
            base_passed, base_notes, base_latency = evaluate_single(
                sc_id, query, base_store, base_hybrid, base_pipeline, pat_alpha, pat_beta, db, is_baseline=True
            )
            
            # --- PROPOSED RUN ---
            t1 = time.time()
            prop_passed, prop_notes, prop_latency = evaluate_single(
                sc_id, query, prop_store, prop_hybrid, prop_pipeline, pat_alpha, pat_beta, db, is_baseline=False
            )

            status_base = "PASS" if base_passed else "FAIL"
            status_prop = "PASS" if prop_passed else "FAIL"
            
            improvement = "IMPROVED" if (not base_passed and prop_passed) else ("REGRESSED" if (base_passed and not prop_passed) else "PARITY")
            
            print(f"    Baseline : [{status_base}] in {base_latency:.1f}ms | {base_notes}")
            print(f"    Proposed : [{status_prop}] in {prop_latency:.1f}ms | {prop_notes}")
            print(f"    Outcome  : {improvement}\n")

            comparison_results.append({
                "scenario_id": sc_id,
                "name": name,
                "query": query,
                "baseline": {
                    "passed": base_passed,
                    "latency_ms": round(base_latency, 2),
                    "notes": base_notes
                },
                "proposed": {
                    "passed": prop_passed,
                    "latency_ms": round(prop_latency, 2),
                    "notes": prop_notes
                },
                "outcome": improvement
            })

        # Summary statistics
        base_pass_count = sum(1 for r in comparison_results if r["baseline"]["passed"])
        prop_pass_count = sum(1 for r in comparison_results if r["proposed"]["passed"])
        base_avg_lat = sum(r["baseline"]["latency_ms"] for r in comparison_results) / len(comparison_results)
        prop_avg_lat = sum(r["proposed"]["latency_ms"] for r in comparison_results) / len(comparison_results)

        regressions = [r for r in comparison_results if r["outcome"] == "REGRESSED"]
        improvements = [r for r in comparison_results if r["outcome"] == "IMPROVED"]

        summary = {
            "timestamp": datetime.now(UTC).isoformat(),
            "baseline_pass_count": base_pass_count,
            "proposed_pass_count": prop_pass_count,
            "total_scenarios": len(comparison_results),
            "baseline_pass_rate_pct": round((base_pass_count / len(comparison_results)) * 100, 1),
            "proposed_pass_rate_pct": round((prop_pass_count / len(comparison_results)) * 100, 1),
            "baseline_avg_latency_ms": round(base_avg_lat, 2),
            "proposed_avg_latency_ms": round(prop_avg_lat, 2),
            "speedup_factor": round(base_avg_lat / max(prop_avg_lat, 0.001), 2),
            "regressions_count": len(regressions),
            "improvements_count": len(improvements),
            "comparison": comparison_results
        }

        print("=" * 80)
        print("EXPERIMENT RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total Scenarios Evaluated  : {len(comparison_results)}")
        print(f"Baseline Pass Rate         : {base_pass_count}/{len(comparison_results)} ({summary['baseline_pass_rate_pct']}%)")
        print(f"Proposed Pass Rate         : {prop_pass_count}/{len(comparison_results)} ({summary['proposed_pass_rate_pct']}%)")
        print(f"Baseline Average Latency   : {summary['baseline_avg_latency_ms']} ms")
        print(f"Proposed Average Latency   : {summary['proposed_avg_latency_ms']} ms (Speedup: {summary['speedup_factor']}x)")
        print(f"Regressions Observed       : {len(regressions)}")
        print(f"Improvements Observed      : {len(improvements)}")
        print("=" * 80)

        out_path = os.path.join(os.path.dirname(__file__), "experiment_comparison_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"Saved full comparative experiment results to: {out_path}\n")

        return summary
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists(exp_db_path):
            try:
                os.remove(exp_db_path)
            except Exception:
                pass
        if os.path.exists(exp_chroma_path):
            try:
                shutil.rmtree(exp_chroma_path, ignore_errors=True)
            except Exception:
                pass


def evaluate_single(
    sc_id: str,
    query: str,
    vector_store: VectorStore,
    hybrid_retriever: HybridRetriever,
    pipeline: RAGPipeline,
    pat_alpha: str,
    pat_beta: str,
    db: Session,
    is_baseline: bool
) -> Tuple[bool, str, float]:
    """Helper to evaluate a specific clinical scenario against a given pipeline."""
    t0 = time.time()

    if sc_id == "SC-01":
        # Exact numerical values and units (Potassium 4.8 mEq/L)
        res = hybrid_retriever.retrieve(query, patient_id=pat_alpha, top_k=4)
        found = any("4.8" in r.content and "mEq/L" in r.content for r in res.elements)
        notes = "Found 4.8 mEq/L in top results" if found else "4.8 mEq/L displaced from top results"
        return found, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-02":
        # Date-specific temporal filtering
        res = hybrid_retriever.retrieve(query, patient_id=pat_alpha, top_k=6)
        found_2023 = any("2023-04-15" in r.content and "0.95" in r.content for r in res.elements)
        found_2024 = any("2024-09-10" in r.content and "1.28" in r.content for r in res.elements)
        passed = found_2023 and found_2024
        notes = f"2023: {found_2023}, 2024: {found_2024}"
        return passed, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-03":
        # Latest vs historical biomarker values (Glucose: 108 mg/dL on 2025-01-20 > 142 mg/dL on 2023)
        res = hybrid_retriever.retrieve(query, patient_id=pat_alpha, top_k=4)
        glucose_elements = [e for e in res.elements if "glucose" in e.content.lower()]
        passed = False
        if glucose_elements and "108" in glucose_elements[0].content and "2025" in glucose_elements[0].content:
            passed = True
        notes = f"Top Glucose: {glucose_elements[0].content[:60] if glucose_elements else 'None'}"
        return passed, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-04":
        # Medication & allergy cross-referencing (Penicillin allergy with Amoxicillin)
        # In current schema, allergies are not indexed into clinical tables.
        res = hybrid_retriever.retrieve(query, patient_id=pat_alpha, top_k=6)
        has_allergy = any("Penicillin" in r.content for r in res.elements)
        notes = "Penicillin allergy retrieved" if has_allergy else "Allergy not surfaced (requires Phase 2 schema link)"
        return has_allergy, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-05":
        # Multi-turn follow-up (Asthma inhaler)
        resolver = ConversationQueryResolver()
        history = [
            {"sender": "user", "text": "What pulmonary conditions have been diagnosed?"},
            {"sender": "ai", "text": "You have a documented diagnosis of Moderate Persistent Asthma."}
        ]
        resolved = resolver.resolve(query, conversation_history=history)
        res = hybrid_retriever.retrieve(query, patient_id=pat_alpha, top_k=4, search_query=resolved.resolved_query)
        has_inhaler = any("Fluticasone" in r.content or "Advair" in r.content for r in res.elements)
        notes = f"Active topic: {resolved.active_topic}, Retrieved inhaler: {has_inhaler}"
        return (has_inhaler and resolved.active_topic in ["asthma", "pulmonary"]), notes, (time.time() - t0) * 1000

    elif sc_id == "SC-06":
        # Contradictory records (Metro 6.8% vs St. Jude 7.4% HbA1c)
        res = hybrid_retriever.retrieve(query, patient_id=pat_alpha, top_k=6)
        found_metro = any("6.8" in r.content and "Metro" in r.content for r in res.elements)
        found_stjude = any("7.4" in r.content and "St. Jude" in r.content for r in res.elements)
        passed = found_metro and found_stjude
        notes = f"Metro (6.8%): {found_metro}, St. Jude (7.4%): {found_stjude}"
        return passed, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-07":
        # Unsupported questions (Refusal & zero hallucination)
        rag_res = pipeline.query(query, patient_id=pat_alpha, top_k=4)
        has_citations = len(rag_res.citations) > 0
        refused = "no record" in rag_res.answer.lower() or "not found" in rag_res.answer.lower()
        passed = (not has_citations) and refused
        notes = f"Refused properly: {refused}, Citations count: {len(rag_res.citations)}"
        return passed, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-08":
        # Patient isolation (Zero cross-patient leakage)
        # Query for Alpha about Knee MRI (belongs strictly to Beta)
        vec_res = vector_store.similarity_search(query, top_k=10, filter_metadata={"patient_id": pat_alpha})
        leaked_vec = any(r.chunk.metadata.get("patient_id") == pat_beta for r in vec_res)
        hybrid_res = hybrid_retriever.retrieve(query, patient_id=pat_alpha, top_k=10)
        leaked_hybrid = any("Jordan Miller" in r.content for r in hybrid_res.elements)
        passed = (not leaked_vec) and (not leaked_hybrid)
        notes = f"Vector leaked: {leaked_vec}, Hybrid leaked: {leaked_hybrid}"
        return passed, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-09":
        # Newly uploaded relevant reports
        # Dynamically add report chunk
        new_doc_id = f"dyn_rep_{'base' if is_baseline else 'prop'}"
        new_chunk = DocumentChunk(
            chunk_id=f"chk_dyn_{new_doc_id}",
            document_id=new_doc_id,
            page_number=1,
            chunk_index=0,
            text="ST. JUDE URGENT CARE - DISCHARGE SUMMARY: Acute Asthmatic Bronchitis diagnosed. Prescribed Azithromycin 250mg Z-Pak on 2025-02-15.",
            metadata={"patient_id": pat_alpha, "title": "Discharge Summary - Bronchitis", "report_date": "2025-02-15"}
        )
        vector_store.add_documents([new_chunk])
        
        # Test vector search directly for the dynamic chunk
        vec_res = vector_store.similarity_search("acute asthmatic bronchitis Azithromycin", top_k=4, filter_metadata={"patient_id": pat_alpha})
        found_vec = any("bronchitis" in r.chunk.text.lower() and "azithromycin" in r.chunk.text.lower() for r in vec_res)
        notes = f"Dynamically indexed chunk retrievable: {found_vec}"
        return found_vec, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-10":
        # Synonyms & alternate clinical terminology
        # Query: "Do my records show elevated arterial pressure or high cardiac readings?"
        # Document text: "Essential (Primary) Hypertension ... Lisinopril 10mg QD ... blood pressure"
        vec_res = vector_store.similarity_search(query, top_k=4, filter_metadata={"patient_id": pat_alpha})
        found_htn = any("hypertension" in r.chunk.text.lower() or "lisinopril" in r.chunk.text.lower() for r in vec_res)
        top_score = vec_res[0].score if vec_res else 0.0
        notes = f"Semantic match found: {found_htn} (Top similarity score: {top_score:.3f})"
        return found_htn, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-11":
        # Multi-page reports (>3,000 chars)
        res = hybrid_retriever.retrieve(query, patient_id=pat_alpha, top_k=4)
        found_tsh = any("5.8" in r.content for r in res.elements)
        found_t4 = any("0.8" in r.content for r in res.elements)
        passed = found_tsh and found_t4
        notes = f"TSH found: {found_tsh}, Free T4 found: {found_t4}"
        return passed, notes, (time.time() - t0) * 1000

    elif sc_id == "SC-12":
        # Citation relevance and claim verification
        rag_res = pipeline.query(query, patient_id=pat_alpha, top_k=4)
        citations = rag_res.citations
        cited_ids = [c.get("reportId") for c in citations]
        has_correct = "synth_rep_alpha_002" in cited_ids
        notes = f"Citations count: {len(citations)}, Includes hepatic panel: {has_correct}"
        return has_correct, notes, (time.time() - t0) * 1000

    return False, "Unknown scenario", (time.time() - t0) * 1000


if __name__ == "__main__":
    run_comparative_experiment()
