import os
import sys
sys.path.insert(0, 'C:/chromaNexus')
sys.path.insert(0, 'C:/chromaNexus/backend')

import json
import time
import math
import numpy as np

from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import SearchResult, ChromaDBVectorStore
from backend.app.ai.embeddings import BGEEmbeddingProvider
from backend.app.ai.rag.bm25_retriever import BM25KeywordRetriever, clinical_bm25_tokenize
from backend.app.ai.rag.fusion import reciprocal_rank_fusion, ResultFusion

def run_stage_5():
    print('=== RUNNING STAGE 5: BM25 Lexical Retrieval & Lifecycle ===')
    stage5_results = {}

    corpus_data = [
        ('chk_med_1', 'pat_A', 'Patient is prescribed Lisinopril 10mg daily for hypertension.', ['lisinopril']),
        ('chk_med_2', 'pat_A', 'Started on Metoprolol succinate 50mg PO quotidianly for cardioprotection.', ['metoprolol', 'succinate']),
        ('chk_med_3', 'pat_A', 'Atorvastatin 40mg at bedtime for hyperlipidemia.', ['atorvastatin']),
        ('chk_acr_1', 'pat_A', 'Electrocardiogram reveals evolving acute STEMI in anterior leads.', ['stemi']),
        ('chk_acr_2', 'pat_A', 'Patient has a long-standing history of COPD with distress.', ['copd']),
        ('chk_acr_3', 'pat_A', 'Chest X-ray shows marked cardiomegaly and congestive heart failure CHF.', ['chf']),
        ('chk_lab_1', 'pat_A', 'Serum Troponin I level is 0.04 ng/mL (reference range < 0.03).', ['troponin', '0.04']),
        ('chk_lab_2', 'pat_A', 'Serum Potassium is 4.8 mEq/L drawn on 2026-09-15.', ['potassium', '4.8', '2026-09-15']),
        ('chk_lab_3', 'pat_A', 'eGFR calculated at 58 mL/min/1.73m2 consistent with Stage 3a CKD.', ['egfr', '58']),
        ('chk_neg_1', 'pat_A', 'Patient denies acute chest pain, nausea, or shortness of breath.', ['denies', 'chest', 'pain']),
        ('chk_neg_2', 'pat_A', 'No known drug allergies (NKDA, negative rash history).', ['nkda']),
        ('chk_patb_1', 'pat_B', 'Patient B Serum Potassium is 3.5 mEq/L on 2026-08-10.', ['potassium', '3.5']),
        ('chk_patb_2', 'pat_B', 'Patient B Troponin I is 0.01 ng/mL (normal).', ['troponin', '0.01']),
        ('chk_patb_3', 'pat_A', 'Allergy present: Penicillin (anaphylaxis risk).', ['penicillin'])
    ]

    doc_chunks = [
        DocumentChunk(
            chunk_id=cid,
            document_id='report_1',
            text=txt,
            page_number=1,
            chunk_index=i,
            metadata={'patient_id': pid}
        )
        for i, (cid, pid, txt, kws) in enumerate(corpus_data)
    ]

    bm25 = BM25KeywordRetriever()
    bm25.index_chunks(doc_chunks)

    queries = [
        {'q': 'Lisinopril', 'expected': 'chk_med_1', 'cat': 'medication'},
        {'q': 'Metoprolol succinate', 'expected': 'chk_med_2', 'cat': 'medication'},
        {'q': 'Atorvastatin', 'expected': 'chk_med_3', 'cat': 'medication'},
        {'q': 'STEMI', 'expected': 'chk_acr_1', 'cat': 'acronym'},
        {'q': 'COPD', 'expected': 'chk_acr_2', 'cat': 'acronym'},
        {'q': 'CHF', 'expected': 'chk_acr_3', 'cat': 'acronym'},
        {'q': 'Troponin I 0.04', 'expected': 'chk_lab_1', 'cat': 'lab_numeric'},
        {'q': 'Potassium 4.8', 'expected': 'chk_lab_2', 'cat': 'lab_numeric'},
        {'q': 'eGFR 58', 'expected': 'chk_lab_3', 'cat': 'lab_numeric'},
        {'q': 'denies chest pain', 'expected': 'chk_neg_1', 'cat': 'negation'},
        {'q': 'NKDA no allergies', 'expected': 'chk_neg_2', 'cat': 'negation'},
        {'q': 'Penicillin allergy', 'expected': 'chk_patb_3', 'cat': 'allergy'}
    ]

    r1_hits, r3_hits, r5_hits = 0, 0, 0
    rrk_list = []
    ndcg_list = []
    latencies = []
    patient_isolation_fails = 0

    for qd in queries:
        q = qd['q']
        exp = qd['expected']
        t0 = time.perf_counter()
        res = bm25.search(q, top_k=10, filter_metadata={'patient_id': 'pat_A'})
        latencies.append((time.perf_counter() - t0) * 1000)

        ret_ids = [r.chunk.chunk_id for r in res]
        
        for r in res:
            if r.chunk.metadata.get('patient_id') != 'pat_A':
                patient_isolation_fails += 1

        if ret_ids and ret_ids[0] == exp:
            r1_hits += 1
        if exp in ret_ids[:3]:
            r3_hits += 1
        if exp in ret_ids[:5]:
            r5_hits += 1

        if exp in ret_ids:
            rank = ret_ids.index(exp) + 1
            rrk_list.append(1.0 / rank)
            ndcg_list.append(1.0 / math.log2(rank + 1))
        else:
            rrk_list.append(0.0)
            ndcg_list.append(0.0)

    total = len(queries)
    stage5_results['5.1_lexical_retrieval'] = {
        'total_queries': total,
        'recall_at_1': r1_hits / total,
        'recall_at_3': r3_hits / total,
        'recall_at_5': r5_hits / total,
        'mrr': sum(rrk_list) / total,
        'ndcg_at_5': sum(ndcg_list) / total,
        'patient_isolation_failures': patient_isolation_fails,
        'median_latency_ms': float(np.median(latencies)),
        'p95_latency_ms': float(np.percentile(latencies, 95)),
        'status': 'PASS' if (patient_isolation_fails == 0 and (r5_hits / total) >= 0.90) else 'FAIL'
    }

    initial_count = len(bm25._chunks)
    new_inc_chunk = DocumentChunk(
        chunk_id='chk_inc_bm25_99',
        document_id='report_2',
        text='Patient has synthetic condition XYZ99 not previously indexed.',
        page_number=1,
        chunk_index=0,
        metadata={'patient_id': 'pat_A'}
    )
    bm25.index_chunks([new_inc_chunk])
    post_count = len(bm25._chunks)
    
    query_inc = bm25.search('XYZ99', top_k=3, filter_metadata={'patient_id': 'pat_A'})
    found_inc = any(r.chunk.chunk_id == 'chk_inc_bm25_99' for r in query_inc)

    bm25.index_chunks([new_inc_chunk])
    post_dup_count = len(bm25._chunks)
    dup_prevented = (post_count == post_dup_count)

    stage5_results['5.2_lifecycle_refresh'] = {
        'initial_chunk_count': initial_count,
        'post_incremental_count': post_count,
        'incremental_chunk_searchable': found_inc,
        'duplicate_prevented': dup_prevented,
        'status': 'PASS' if (found_inc and dup_prevented) else 'FAIL'
    }
    return stage5_results

def run_stage_6():
    print('=== RUNNING STAGE 6: RRF Mathematics & Hybrid Ranking ===')
    stage6_results = {}

    doc_a = DocumentChunk(chunk_id='Doc_A', document_id='d1', text='a', page_number=1, chunk_index=0)
    doc_b = DocumentChunk(chunk_id='Doc_B', document_id='d1', text='b', page_number=1, chunk_index=1)
    doc_c = DocumentChunk(chunk_id='Doc_C', document_id='d1', text='c', page_number=1, chunk_index=2)
    doc_d = DocumentChunk(chunk_id='Doc_D', document_id='d1', text='d', page_number=1, chunk_index=3)

    dense_items = [
        SearchResult(chunk=doc_a, score=0.9),
        SearchResult(chunk=doc_b, score=0.7),
        SearchResult(chunk=doc_d, score=0.5)
    ]

    bm25_items = [
        SearchResult(chunk=doc_a, score=0.85),
        SearchResult(chunk=doc_c, score=0.62),
        SearchResult(chunk=doc_d, score=0.41)
    ]

    rrf_expected = reciprocal_rank_fusion(dense_items, bm25_items, rrf_k=60)
    rrf_ids = [r.chunk.chunk_id for r in rrf_expected]
    
    order_correct = (rrf_ids[0] == 'Doc_A' and rrf_ids[1] == 'Doc_D' and set(rrf_ids[2:]) == {'Doc_B', 'Doc_C'})
    top_score_ok = (rrf_expected[0].score == 1.0)

    empty_dense_res = reciprocal_rank_fusion([], bm25_items, rrf_k=60)
    empty_dense_ok = (len(empty_dense_res) == 3 and empty_dense_res[0].chunk.chunk_id == 'Doc_A')

    both_empty_res = reciprocal_rank_fusion([], [], rrf_k=60)
    both_empty_ok = (len(both_empty_res) == 0)

    stage6_results['6.1_rrf_mathematics'] = {
        'order_correct': order_correct,
        'top_score_normalized_1.0': top_score_ok,
        'empty_dense_supported': empty_dense_ok,
        'both_empty_supported': both_empty_ok,
        'final_ranks': rrf_ids,
        'scores': {r.chunk.chunk_id: r.score for r in rrf_expected},
        'status': 'PASS' if (order_correct and top_score_ok and empty_dense_ok and both_empty_ok) else 'FAIL'
    }

    import tempfile
    import shutil
    from chromadb.api.client import SharedSystemClient
    tmp_c_dir = tempfile.mkdtemp(prefix='audit_s6_cmp_')
    try:
        emb_prov = BGEEmbeddingProvider()
        vstore_tmp = ChromaDBVectorStore(persist_directory=tmp_c_dir, collection_name='s6_cmp_col', embedding_provider=emb_prov)
        
        corpus_data = [
            ('chk_med_1', 'pat_A', 'Patient is prescribed Lisinopril 10mg daily for hypertension.', ['lisinopril']),
            ('chk_med_2', 'pat_A', 'Started on Metoprolol succinate 50mg PO quotidianly for cardioprotection.', ['metoprolol', 'succinate']),
            ('chk_med_3', 'pat_A', 'Atorvastatin 40mg at bedtime for hyperlipidemia.', ['atorvastatin']),
            ('chk_acr_1', 'pat_A', 'Electrocardiogram reveals evolving acute STEMI in anterior leads.', ['stemi']),
            ('chk_acr_2', 'pat_A', 'Patient has a long-standing history of COPD with distress.', ['copd']),
            ('chk_acr_3', 'pat_A', 'Chest X-ray shows marked cardiomegaly and congestive heart failure CHF.', ['chf']),
            ('chk_lab_1', 'pat_A', 'Serum Troponin I level is 0.04 ng/mL (reference range < 0.03).', ['troponin', '0.04']),
            ('chk_lab_2', 'pat_A', 'Serum Potassium is 4.8 mEq/L drawn on 2026-09-15.', ['potassium', '4.8', '2026-09-15']),
            ('chk_lab_3', 'pat_A', 'eGFR calculated at 58 mL/min/1.73m2 consistent with Stage 3a CKD.', ['egfr', '58']),
            ('chk_neg_1', 'pat_A', 'Patient denies acute chest pain, nausea, or shortness of breath.', ['denies', 'chest', 'pain']),
            ('chk_neg_2', 'pat_A', 'No known drug allergies (NKDA, negative rash history).', ['nkda']),
            ('chk_patb_1', 'pat_B', 'Patient B Serum Potassium is 3.5 mEq/L on 2026-08-10.', ['potassium', '3.5']),
            ('chk_patb_2', 'pat_B', 'Patient B Troponin I is 0.01 ng/mL (normal).', ['troponin', '0.01']),
            ('chk_patb_3', 'pat_A', 'Allergy present: Penicillin (anaphylaxis risk).', ['penicillin'])
        ]
        doc_chunks = [
            DocumentChunk(
                chunk_id=cid,
                document_id='report_1',
                text=txt,
                page_number=1,
                chunk_index=i,
                metadata={'patient_id': pid}
            )
            for i, (cid, pid, txt, kws) in enumerate(corpus_data)
        ]
        vstore_tmp.add_documents(doc_chunks)
        bm25_cmp = BM25KeywordRetriever()
        bm25_cmp.index_chunks(doc_chunks)

        queries = [
            {'q': 'Lisinopril', 'expected': 'chk_med_1'},
            {'q': 'Metoprolol succinate', 'expected': 'chk_med_2'},
            {'q': 'Atorvastatin', 'expected': 'chk_med_3'},
            {'q': 'STEMI', 'expected': 'chk_acr_1'},
            {'q': 'COPD', 'expected': 'chk_acr_2'},
            {'q': 'CHF', 'expected': 'chk_acr_3'},
            {'q': 'Troponin I 0.04', 'expected': 'chk_lab_1'},
            {'q': 'Potassium 4.8', 'expected': 'chk_lab_2'},
            {'q': 'eGFR 58', 'expected': 'chk_lab_3'},
            {'q': 'denies chest pain', 'expected': 'chk_neg_1'},
            {'q': 'NKDA no allergies', 'expected': 'chk_neg_2'},
            {'q': 'Penicillin allergy', 'expected': 'chk_patb_3'}
        ]

        dense_r1, dense_r3, dense_r5 = 0, 0, 0
        bm25_r1, bm25_r3, bm25_r5 = 0, 0, 0
        hybrid_r1, hybrid_r3, hybrid_r5 = 0, 0, 0

        for qd in queries:
            q = qd['q']
            exp = qd['expected']
            d_res = vstore_tmp.similarity_search(q, top_k=10, filter_metadata={'patient_id': 'pat_A'})
            d_ids = [r.chunk.chunk_id for r in d_res]
            if d_ids and d_ids[0] == exp: dense_r1 += 1
            if exp in d_ids[:3]: dense_r3 += 1
            if exp in d_ids[:5]: dense_r5 += 1

            b_res = bm25_cmp.search(q, top_k=10, filter_metadata={'patient_id': 'pat_A'})
            b_ids = [r.chunk.chunk_id for r in b_res]
            if b_ids and b_ids[0] == exp: bm25_r1 += 1
            if exp in b_ids[:3]: bm25_r3 += 1
            if exp in b_ids[:5]: bm25_r5 += 1

            r_res = reciprocal_rank_fusion(d_res, b_res, rrf_k=60)
            h_ids = [r.chunk.chunk_id for r in r_res]
            if h_ids and h_ids[0] == exp: hybrid_r1 += 1
            if exp in h_ids[:3]: hybrid_r3 += 1
            if exp in h_ids[:5]: hybrid_r5 += 1

        total = len(queries)
        stage6_results['6.2_strategies_comparison'] = {
            'total_queries': total,
            'dense_only': {'recall_at_1': dense_r1 / total, 'recall_at_3': dense_r3 / total, 'recall_at_5': dense_r5 / total},
            'bm25_only': {'recall_at_1': bm25_r1 / total, 'recall_at_3': bm25_r3 / total, 'recall_at_5': bm25_r5 / total},
            'hybrid_rrf': {'recall_at_1': hybrid_r1 / total, 'recall_at_3': hybrid_r3 / total, 'recall_at_5': hybrid_r5 / total},
            'status': 'PASS' if (hybrid_r5 / total) >= 0.90 else 'FAIL'
        }
    finally:
        SharedSystemClient.clear_system_cache()
        shutil.rmtree(tmp_c_dir, ignore_errors=True)

    return stage6_results

if __name__ == '__main__':
    s5 = run_stage_5()
    s6 = run_stage_6()
    final = {
        'stage_5': s5,
        'stage_6': s6
    }
    out_path = r'docs/audit/phase4_acceptance_20261018_2330/stage5_stage6_results.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=2)
    print('STAGES_5_6_COMPLETED_SUCCESSFULLY')
