"""
ChronaNexus Strengthened Retrieval Evaluation Benchmark
======================================================
Objective 3: Rigorous, zero-leakage evaluation comparing:
1. BGE Dense Retrieval (BAAI/bge-small-en-v1.5, 384 dimensions)
2. BM25 Lexical Retrieval (Okapi BM25)
3. Hybrid RRF Retrieval (Reciprocal Rank Fusion, k=60)

Uses a fixed synthetic clinical corpus (20 documents) and 10 realistic clinical queries
with explicit relevance labels and hard negatives.
Reports Recall@1, Recall@3, Recall@5, MRR, and nDCG@5 with explicit numerators and denominators.
Strictly isolated from persistent production ChromaDB.
"""

import os
import sys
import math
import json
from typing import List, Dict, Any, Set

# Ensure repo root on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import chromadb
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.embeddings import EmbeddingProvider
from backend.app.ai.retrieval import ChromaDBVectorStore, SearchResult
from backend.app.ai.rag.bm25_retriever import BM25KeywordRetriever
from backend.app.ai.rag.fusion import reciprocal_rank_fusion
from sentence_transformers import SentenceTransformer


class LocalBgeEmbeddingProvider(EmbeddingProvider):
    """Offline semantic embedding provider using BAAI/bge-small-en-v1.5."""
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_embedding_dimension()

    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()


# -----------------------------------------------------------------------------
# 1. Fixed Synthetic Clinical Corpus (20 Chunks)
# -----------------------------------------------------------------------------
SYNTHETIC_CORPUS: List[Dict[str, Any]] = [
    {
        "id": "doc_01",
        "text": "Allergy Assessment: Documented severe anaphylactic reaction to Penicillin presenting with diffuse urticaria, bronchospasm, and facial angioedema. Prescribed azithromycin 500mg daily as antimicrobial alternative.",
        "category": "allergy"
    },
    {
        "id": "doc_02",
        "text": "Medication History: Patient reported mild gastrointestinal intolerance and nausea to Amoxicillin in childhood. Tolerated oral cephalexin without hypersensitivity or rash.",
        "category": "allergy_hard_neg"
    },
    {
        "id": "doc_03",
        "text": "Nephrology Laboratory: Serum potassium measured at 5.8 mEq/L on October 12, 2026, indicating moderate hyperkalemia. Lisinopril 20mg discontinued; patient advised on low-potassium diet.",
        "category": "nephrology"
    },
    {
        "id": "doc_04",
        "text": "Routine Comprehensive Metabolic Panel: Serum potassium 3.9 mEq/L on August 15, 2026, within normal reference range (3.5 to 5.0 mEq/L). Serum sodium 140 mEq/L, BUN 14 mg/dL.",
        "category": "nephrology_hard_neg"
    },
    {
        "id": "doc_05",
        "text": "Endocrinology Note: Hemoglobin A1c measured at 9.4% on September 1, 2026. Diagnosis: Uncontrolled Type 2 Diabetes Mellitus with hyperglycemia. Initiating Metformin 500mg BID and basal insulin glargine.",
        "category": "endocrinology"
    },
    {
        "id": "doc_06",
        "text": "Preventive Care Exam: Random blood glucose was 112 mg/dL. Fasting serum insulin within normal limits. Patient has no personal or family diagnosis of diabetes mellitus.",
        "category": "endocrinology_hard_neg"
    },
    {
        "id": "doc_07",
        "text": "Echocardiogram Report: Transthoracic study shows severe left ventricular systolic dysfunction with left ventricular ejection fraction (LVEF) of 32%, diffuse hypokinesis, and elevated filling pressures.",
        "category": "cardiology"
    },
    {
        "id": "doc_08",
        "text": "Echocardiogram Report: Normal left ventricular systolic function with preserved ejection fraction (LVEF 58%). Mild concentric left ventricular hypertrophy without wall motion abnormalities.",
        "category": "cardiology_hard_neg"
    },
    {
        "id": "doc_09",
        "text": "Diagnostic Radiology: CT pulmonary angiogram negative for pulmonary embolism. Right lower lobe subsegmental atelectasis noted without focal consolidation or pneumothorax.",
        "category": "pulmonology_hard_neg"
    },
    {
        "id": "doc_10",
        "text": "Emergency Radiology: CT pulmonary angiogram demonstrates acute bilateral segmental pulmonary emboli within lower lobe pulmonary arteries with mild right ventricular strain and reflux into IVC.",
        "category": "pulmonology"
    },
    {
        "id": "doc_11",
        "text": "Anticoagulation Clinic: Patient on Warfarin 5mg daily for mechanical mitral valve replacement. Target INR range 2.5 to 3.5. Today's point-of-care INR is 2.8, within therapeutic goal.",
        "category": "pharmacology"
    },
    {
        "id": "doc_12",
        "text": "Cardiology Follow-up: Patient maintained on Apixaban (Eliquis) 5mg twice daily for stroke prophylaxis in non-valvular atrial fibrillation. Creatinine clearance 62 mL/min.",
        "category": "pharmacology_hard_neg"
    },
    {
        "id": "doc_13",
        "text": "Renal Function Tracking: Estimated glomerular filtration rate (eGFR) dropped to 28 mL/min/1.73m2, confirming Chronic Kidney Disease (CKD) Stage 4. Serum creatinine 2.4 mg/dL.",
        "category": "renal"
    },
    {
        "id": "doc_14",
        "text": "Annual Health Check: Normal renal function with eGFR 82 mL/min/1.73m2 and serum creatinine 0.9 mg/dL. Urine albumin-to-creatinine ratio 12 mg/g (normal <30 mg/g).",
        "category": "renal_hard_neg"
    },
    {
        "id": "doc_15",
        "text": "Surgical Pathology: Left breast core needle biopsy confirms invasive ductal carcinoma, Nottingham Grade 2. Receptor status: Estrogen Receptor (ER) positive, Progesterone Receptor (PR) positive, HER2 negative.",
        "category": "oncology"
    },
    {
        "id": "doc_16",
        "text": "Pathology Report: Right breast ultrasound-guided core biopsy reveals benign fibroadenoma with apocrine metaplasia and stromal fibrosis. Negative for ductal carcinoma in situ or invasive malignancy.",
        "category": "oncology_hard_neg"
    },
    {
        "id": "doc_17",
        "text": "Pulmonary Inpatient Summary: Admitted for acute exacerbation of Chronic Obstructive Pulmonary Disease (COPD) with severe wheezing. Managed with intravenous methylprednisolone and nebulized ipratropium-albuterol.",
        "category": "respiratory"
    },
    {
        "id": "doc_18",
        "text": "Pulmonary Function Test: Spirometry reveals mild restrictive ventilatory pattern with FEV1/FVC ratio of 0.82. No evidence of significant obstructive airflow limitation or asthma.",
        "category": "respiratory_hard_neg"
    },
    {
        "id": "doc_19",
        "text": "Cardiac Catheterization Report: Acute anterior wall ST-elevation myocardial infarction (STEMI). Emergent coronary angiography revealed 99% proximal LAD occlusion; successful drug-eluting stent placed.",
        "category": "emergency_cardiology"
    },
    {
        "id": "doc_20",
        "text": "Emergency Department Consult: Atypical non-anginal musculoskeletal chest pain. Serial high-sensitivity troponin assays negative (<0.01 ng/mL). Electrocardiogram normal sinus rhythm without ST changes.",
        "category": "emergency_cardiology_hard_neg"
    }
]

# -----------------------------------------------------------------------------
# 2. Fixed Clinical Benchmark Queries with Explicit Judgments
# -----------------------------------------------------------------------------
EVAL_QUERIES: List[Dict[str, Any]] = [
    {
        "query_id": "Q01",
        "query": "Severe anaphylactic penicillin allergy and angioedema",
        "relevant_ids": {"doc_01"},
        "hard_negatives": {"doc_02"}
    },
    {
        "query_id": "Q02",
        "query": "Elevated serum potassium 5.8 hyperkalemia on October 12",
        "relevant_ids": {"doc_03"},
        "hard_negatives": {"doc_04"}
    },
    {
        "query_id": "Q03",
        "query": "Uncontrolled type 2 diabetes elevated HbA1c 9.4 percent",
        "relevant_ids": {"doc_05"},
        "hard_negatives": {"doc_06"}
    },
    {
        "query_id": "Q04",
        "query": "Reduced ejection fraction systolic heart failure LVEF 32%",
        "relevant_ids": {"doc_07"},
        "hard_negatives": {"doc_08"}
    },
    {
        "query_id": "Q05",
        "query": "CT angiography acute pulmonary embolism bilateral segmental with RV strain",
        "relevant_ids": {"doc_10"},
        "hard_negatives": {"doc_09"}
    },
    {
        "query_id": "Q06",
        "query": "Warfarin anticoagulation mechanical mitral valve target INR 2.5 to 3.5",
        "relevant_ids": {"doc_11"},
        "hard_negatives": {"doc_12"}
    },
    {
        "query_id": "Q07",
        "query": "Chronic kidney disease stage 4 low eGFR 28 creatinine 2.4",
        "relevant_ids": {"doc_13"},
        "hard_negatives": {"doc_14"}
    },
    {
        "query_id": "Q08",
        "query": "Invasive ductal carcinoma ER positive PR positive HER2 negative breast cancer",
        "relevant_ids": {"doc_15"},
        "hard_negatives": {"doc_16"}
    },
    {
        "query_id": "Q09",
        "query": "Acute COPD exacerbation methylprednisolone nebulized ipratropium",
        "relevant_ids": {"doc_17"},
        "hard_negatives": {"doc_18"}
    },
    {
        "query_id": "Q10",
        "query": "Acute anterior wall STEMI myocardial infarction proximal LAD occlusion stent",
        "relevant_ids": {"doc_19"},
        "hard_negatives": {"doc_20"}
    }
]


def compute_metrics(rankings: List[str], relevant_ids: Set[str]) -> Dict[str, float]:
    """Calculates Recall@1, Recall@3, Recall@5, MRR, and nDCG@5."""
    # Recall@K
    rec1 = 1.0 if any(r in relevant_ids for r in rankings[:1]) else 0.0
    rec3 = 1.0 if any(r in relevant_ids for r in rankings[:3]) else 0.0
    rec5 = 1.0 if any(r in relevant_ids for r in rankings[:5]) else 0.0

    # MRR
    mrr = 0.0
    for rank, doc_id in enumerate(rankings, start=1):
        if doc_id in relevant_ids:
            mrr = 1.0 / rank
            break

    # nDCG@5
    dcg5 = 0.0
    for idx, doc_id in enumerate(rankings[:5], start=1):
        rel = 1.0 if doc_id in relevant_ids else 0.0
        dcg5 += rel / math.log2(idx + 1)
    
    # Ideal DCG for 1 relevant document
    idcg5 = 1.0 / math.log2(2)  # 1.0
    ndcg5 = dcg5 / idcg5

    return {
        "recall@1": rec1,
        "recall@3": rec3,
        "recall@5": rec5,
        "mrr": mrr,
        "ndcg@5": ndcg5
    }


def run_strengthened_evaluation() -> Dict[str, Any]:
    """Executes full evaluation comparing BGE Dense, BM25, and Hybrid RRF."""
    # 1. Initialize isolated embedding provider and ephemeral Chroma collection
    bge_provider = LocalBgeEmbeddingProvider()
    client = chromadb.EphemeralClient()
    collection = client.create_collection(
        name="eval_bge_corpus",
        metadata={"hnsw:space": "cosine"}
    )
    vstore = ChromaDBVectorStore(
        collection_name="eval_bge_corpus",
        embedding_provider=bge_provider
    )
    vstore.collection = collection

    # 2. Initialize BM25 retriever
    bm25_retriever = BM25KeywordRetriever()

    # 3. Index corpus
    chunks = [
        DocumentChunk(
            chunk_id=doc["id"],
            document_id=f"doc_{doc['id']}",
            page_number=1,
            chunk_index=i,
            text=doc["text"],
            metadata={"id": doc["id"], "category": doc["category"]}
        )
        for i, doc in enumerate(SYNTHETIC_CORPUS)
    ]
    vstore.add_documents(chunks)
    bm25_retriever.index_chunks(chunks)

    results = {
        "dense_bge": {"recall@1": 0.0, "recall@3": 0.0, "recall@5": 0.0, "mrr": 0.0, "ndcg@5": 0.0, "hard_neg_discrimination": 0},
        "bm25": {"recall@1": 0.0, "recall@3": 0.0, "recall@5": 0.0, "mrr": 0.0, "ndcg@5": 0.0, "hard_neg_discrimination": 0},
        "hybrid_rrf": {"recall@1": 0.0, "recall@3": 0.0, "recall@5": 0.0, "mrr": 0.0, "ndcg@5": 0.0, "hard_neg_discrimination": 0}
    }

    per_query_details = []
    num_queries = len(EVAL_QUERIES)

    for q in EVAL_QUERIES:
        q_text = q["query"]
        rel_ids = q["relevant_ids"]
        hard_negs = q["hard_negatives"]

        # Strategy 1: Dense BGE
        dense_hits = vstore.similarity_search(q_text, top_k=5)
        dense_ranks = [h.chunk.metadata.get("id") or h.chunk.chunk_id for h in dense_hits]
        m_dense = compute_metrics(dense_ranks, rel_ids)

        # Strategy 2: BM25 Lexical
        bm25_hits = bm25_retriever.search(q_text, top_k=5)
        bm25_ranks = [h.chunk.metadata.get("id") or h.chunk.chunk_id for h in bm25_hits]
        m_bm25 = compute_metrics(bm25_ranks, rel_ids)

        # Strategy 3: Hybrid RRF
        rrf_hits = reciprocal_rank_fusion(dense_hits, bm25_hits, rrf_k=60)
        rrf_ranks = [h.chunk.metadata.get("id") or h.chunk.chunk_id for h in rrf_hits[:5]]
        m_rrf = compute_metrics(rrf_ranks, rel_ids)

        # Hard Negative Discrimination: check if target is ranked above hard negative
        def discriminates(ranks: List[str]) -> bool:
            t_rank = next((i for i, d in enumerate(ranks) if d in rel_ids), 999)
            hn_rank = next((i for i, d in enumerate(ranks) if d in hard_negs), 999)
            return t_rank < hn_rank

        dense_disc = discriminates(dense_ranks)
        bm25_disc = discriminates(bm25_ranks)
        rrf_disc = discriminates(rrf_ranks)

        for m_key in ["recall@1", "recall@3", "recall@5", "mrr", "ndcg@5"]:
            results["dense_bge"][m_key] += m_dense[m_key]
            results["bm25"][m_key] += m_bm25[m_key]
            results["hybrid_rrf"][m_key] += m_rrf[m_key]

        if dense_disc:
            results["dense_bge"]["hard_neg_discrimination"] += 1
        if bm25_disc:
            results["bm25"]["hard_neg_discrimination"] += 1
        if rrf_disc:
            results["hybrid_rrf"]["hard_neg_discrimination"] += 1

        per_query_details.append({
            "query_id": q["query_id"],
            "query": q_text,
            "target": list(rel_ids)[0],
            "hard_neg": list(hard_negs)[0],
            "dense_ranks": dense_ranks,
            "bm25_ranks": bm25_ranks,
            "rrf_ranks": rrf_ranks
        })

    # Compute averages across all queries
    summary = {}
    for strat, scores in results.items():
        summary[strat] = {
            "query_count": num_queries,
            "recall@1": {"score": round(scores["recall@1"] / num_queries, 4), "numerator": int(scores["recall@1"]), "denominator": num_queries},
            "recall@3": {"score": round(scores["recall@3"] / num_queries, 4), "numerator": int(scores["recall@3"]), "denominator": num_queries},
            "recall@5": {"score": round(scores["recall@5"] / num_queries, 4), "numerator": int(scores["recall@5"]), "denominator": num_queries},
            "mrr": {"score": round(scores["mrr"] / num_queries, 4), "sum": round(scores["mrr"], 4), "denominator": num_queries},
            "ndcg@5": {"score": round(scores["ndcg@5"] / num_queries, 4), "sum": round(scores["ndcg@5"], 4), "denominator": num_queries},
            "hard_neg_discrimination": {"score": round(scores["hard_neg_discrimination"] / num_queries, 4), "numerator": scores["hard_neg_discrimination"], "denominator": num_queries}
        }

    return {"summary": summary, "per_query_details": per_query_details}


def test_strengthened_retrieval_benchmark():
    """Pytest test asserting that Hybrid RRF maintains >= 0.90 Recall@3, MRR >= 0.85, and 100% hard negative separation."""
    data = run_strengthened_evaluation()
    summary = data["summary"]

    rrf = summary["hybrid_rrf"]
    assert rrf["recall@1"]["score"] >= 0.80
    assert rrf["recall@3"]["score"] >= 0.90
    assert rrf["recall@5"]["score"] == 1.00
    assert rrf["mrr"]["score"] >= 0.85
    assert rrf["ndcg@5"]["score"] >= 0.85
    assert rrf["hard_neg_discrimination"]["score"] == 1.00


if __name__ == "__main__":
    data = run_strengthened_evaluation()
    print(json.dumps(data, indent=2))
    out_file = os.path.join(os.path.dirname(__file__), "strengthened_retrieval_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2))
    print(f"\nSaved benchmark results to {out_file}")
