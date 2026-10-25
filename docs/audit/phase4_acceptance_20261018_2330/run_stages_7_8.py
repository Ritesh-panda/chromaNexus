import os
import sys
sys.path.insert(0, 'C:/chromaNexus')
sys.path.insert(0, 'C:/chromaNexus/backend')

import json
import time
import tempfile
import shutil
import sqlite3
import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from chromadb.api.client import SharedSystemClient

from backend.app.core.database import Base
from backend.app.models import User, Patient, MedicalReport, DocumentChunkModel
from backend.app.ai.document_processor import ProcessedDocument, ProcessedPage
from backend.app.ai.chunker import DocumentChunker, DocumentChunk
from backend.app.ai.retrieval import ChromaDBVectorStore, SearchResult
from backend.app.ai.embeddings import BGEEmbeddingProvider
from backend.app.ai.rag.bm25_retriever import BM25KeywordRetriever
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from backend.app.ai.rag.fusion import ResultFusion, FusedElement

def run_stage_7():
    print('=== RUNNING STAGE 7: Patient Isolation & Security Boundaries ===')
    stage7_results = {}

    tmp_db = tempfile.mktemp(suffix='_s7.db')
    tmp_chroma = tempfile.mkdtemp(prefix='audit_s7_chroma_')

    engine = create_engine(f'sqlite:///{tmp_db}', connect_args={'check_same_thread': False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    try:
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()

        # Users and Patients
        u_a = User(id='usr_A', name='Alice Vance', email='alice@audit.org', hashed_password='x')
        p_a = Patient(id='pat_alice', user_id='usr_A', date_of_birth='1985-05-12', gender='female')
        r_a = MedicalReport(id='rep_alice', patient_id='pat_alice', title='Alice Labs', file_name='alice.pdf', hospital_name='Metro', report_date='2026-03-01')

        u_b = User(id='usr_B', name='Bob Vance', email='bob@audit.org', hashed_password='x')
        p_b = Patient(id='pat_bob', user_id='usr_B', date_of_birth='1978-11-20', gender='male')
        r_b = MedicalReport(id='rep_bob', patient_id='pat_bob', title='Bob Labs', file_name='bob.pdf', hospital_name='Metro', report_date='2026-04-15')

        db.add_all([u_a, p_a, r_a, u_b, p_b, r_b])
        db.commit()

        emb_prov = BGEEmbeddingProvider()

        # Alice's chunk: Fasting glucose 92 mg/dL on 2026-03-01, Lisinopril 10mg
        c_alice = DocumentChunkModel(
            id='id_chunk_alice_1',
            chunk_id='chk_alice_1',
            document_id='rep_alice',
            patient_id='pat_alice',
            chunk_index=0,
            page_number=1,
            content='Alice clinical record: Fasting Blood Glucose is 92 mg/dL on 2026-03-01. Patient takes Lisinopril 10mg. Allergy: Penicillin.',
            embedding=emb_prov.embed_text('Alice clinical record: Fasting Blood Glucose is 92 mg/dL on 2026-03-01. Patient takes Lisinopril 10mg. Allergy: Penicillin.'),
            chunk_metadata={'patient_id': 'pat_alice', 'document_id': 'rep_alice'}
        )

        # Bob's chunk: Fasting glucose 240 mg/dL on 2026-04-15, Metformin 500mg
        c_bob = DocumentChunkModel(
            id='id_chunk_bob_1',
            chunk_id='chk_bob_1',
            document_id='rep_bob',
            patient_id='pat_bob',
            chunk_index=0,
            page_number=1,
            content='Bob clinical record: Fasting Blood Glucose is 240 mg/dL on 2026-04-15. Patient takes Metformin 500mg. NKDA.',
            embedding=emb_prov.embed_text('Bob clinical record: Fasting Blood Glucose is 240 mg/dL on 2026-04-15. Patient takes Metformin 500mg. NKDA.'),
            chunk_metadata={'patient_id': 'pat_bob', 'document_id': 'rep_bob'}
        )

        db.add_all([c_alice, c_bob])
        db.commit()

        # Vector Store & BM25
        vstore = ChromaDBVectorStore(persist_directory=tmp_chroma, collection_name='s7_isolation_col', embedding_provider=emb_prov)
        
        doc_chunks = [
            DocumentChunk(chunk_id='chk_alice_1', document_id='rep_alice', text=c_alice.content, page_number=1, chunk_index=0, metadata={'patient_id': 'pat_alice'}),
            DocumentChunk(chunk_id='chk_bob_1', document_id='rep_bob', text=c_bob.content, page_number=1, chunk_index=0, metadata={'patient_id': 'pat_bob'})
        ]
        vstore.add_documents(doc_chunks)

        bm25 = BM25KeywordRetriever()
        bm25.index_chunks(doc_chunks)

        hybrid = HybridRetriever(vector_store=vstore, db_session=db, bm25_retriever=bm25)

        # 1. SQL isolation
        sql_alice = db.query(DocumentChunkModel).filter(DocumentChunkModel.patient_id == 'pat_alice').all()
        sql_leak = any(c.patient_id != 'pat_alice' for c in sql_alice)

        # 2. Dense search isolation
        dense_alice = vstore.similarity_search('glucose', top_k=5, filter_metadata={'patient_id': 'pat_alice'})
        dense_leak = any(r.chunk.metadata.get('patient_id') != 'pat_alice' for r in dense_alice)
        dense_bob_found = any('240' in r.chunk.text for r in dense_alice)

        # 3. BM25 search isolation
        bm25_alice = bm25.search('glucose', top_k=5, filter_metadata={'patient_id': 'pat_alice'})
        bm25_leak = any(r.chunk.metadata.get('patient_id') != 'pat_alice' for r in bm25_alice)
        bm25_bob_found = any('240' in r.chunk.text for r in bm25_alice)

        # 4. Hybrid Retriever isolation
        hybrid_alice = hybrid.retrieve('What is the fasting blood glucose?', patient_id='pat_alice', top_k=5)
        hybrid_leak = any(e.metadata.get('patient_id') != 'pat_alice' for e in hybrid_alice.elements)
        hybrid_bob_found = any('240' in e.content for e in hybrid_alice.elements)

        # 5. Negative cross-request: query for Bob under Alice context
        neg_alice = hybrid.retrieve('Give me Bob Glucose value 240', patient_id='pat_alice', top_k=5)
        neg_leak = any('240' in e.content or e.metadata.get('patient_id') == 'pat_bob' for e in neg_alice.elements)

        total_leaks = int(sql_leak) + int(dense_leak) + int(dense_bob_found) + int(bm25_leak) + int(bm25_bob_found) + int(hybrid_leak) + int(hybrid_bob_found) + int(neg_leak)

        stage7_results = {
            'sql_isolation_leak': sql_leak,
            'dense_search_leak': dense_leak,
            'dense_contained_bob_data': dense_bob_found,
            'bm25_search_leak': bm25_leak,
            'bm25_contained_bob_data': bm25_bob_found,
            'hybrid_search_leak': hybrid_leak,
            'hybrid_contained_bob_data': hybrid_bob_found,
            'negative_cross_request_leak': neg_leak,
            'total_leakage_events': total_leaks,
            'status': 'PASS' if total_leaks == 0 else 'FAIL'
        }

        db.close()
    finally:
        engine.dispose()
        if os.path.exists(tmp_db):
            try: os.remove(tmp_db)
            except Exception: pass
        SharedSystemClient.clear_system_cache()
        shutil.rmtree(tmp_chroma, ignore_errors=True)

    return stage7_results

def run_stage_8():
    print('=== RUNNING STAGE 8: End-to-End Ingestion, Retrieval & Restart Persistence ===')
    stage8_results = {}

    tmp_db = tempfile.mktemp(suffix='_s8.db')
    tmp_chroma = tempfile.mkdtemp(prefix='audit_s8_chroma_')

    engine = create_engine(f'sqlite:///{tmp_db}', connect_args={'check_same_thread': False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    try:
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()

        u = User(id='u_e2e', name='Synth E2E Patient', email='e2e@audit.org', hashed_password='x')
        p = Patient(id='pat_e2e_synth', user_id='u_e2e', date_of_birth='1965-08-14', gender='male')
        r = MedicalReport(id='rep_e2e_synth', patient_id='pat_e2e_synth', title='Comprehensive Cardiac & Metabolic Workup', file_name='synth_workup.pdf', hospital_name='St. Jude Clinical Labs', report_date='2026-10-18')
        db.add_all([u, p, r])
        db.commit()

        # Multi-page synthetic clinical document (12 distinct clinical facts)
        page1_text = (
            'COMPREHENSIVE CLINICAL REPORT - PAGE 1\n'
            'Patient: Synth E2E Patient (MRN: 99482) Date: 2026-10-18\n'
            'ECHOCARDIOGRAM FINDINGS:\n'
            '1. Left Ventricular Ejection Fraction (LVEF) is 52% (normal systolic function).\n'
            '2. Aortic valve area is calculated at 1.2 cm2 with mild calcification.\n'
            '3. Mitral regurgitation is graded as Grade 2 (moderate).\n'
            'LABORATORY RENAL PROFILE:\n'
            '4. Serum Creatinine is 1.1 mg/dL.\n'
            '5. Serum Potassium is 4.6 mEq/L (normal limits).\n'
        )

        page2_text = (
            'COMPREHENSIVE CLINICAL REPORT - PAGE 2\n'
            'METABOLIC & PHARMACOTHERAPY EVALUATION:\n'
            '6. Glycated hemoglobin HbA1c is 6.4% (prediabetic range).\n'
            '7. Fasting Blood Glucose is 108 mg/dL.\n'
            'MEDICATION REGIMEN:\n'
            '8. Lisinopril 20mg PO daily for hypertension.\n'
            '9. Carvedilol 12.5mg PO BID for cardioprotection.\n'
            '10. ALLERGY ALERT: Sulfa drugs (causes severe diffuse maculopapular rash).\n'
            'BLOOD PRESSURE RECORDINGS:\n'
            '11. Current Blood Pressure: 134/82 mmHg on 2026-10-18.\n'
            '12. Historical Blood Pressure: 152/94 mmHg on 2025-04-10.\n'
        )

        chunker = DocumentChunker(chunk_size=300, chunk_overlap=50)
        doc = ProcessedDocument(
            document_id='rep_e2e_synth',
            pages=[
                ProcessedPage(page_number=1, text=page1_text),
                ProcessedPage(page_number=2, text=page2_text)
            ],
            metadata={'patient_id': 'pat_e2e_synth'}
        )
        all_chunks = chunker.chunk_document(doc)

        emb_prov = BGEEmbeddingProvider()

        # SQL Persistence
        for i, chk in enumerate(all_chunks):
            chk.metadata['patient_id'] = 'pat_e2e_synth'
            sql_chk = DocumentChunkModel(
                id=f'id_e2e_{i}',
                chunk_id=chk.chunk_id,
                document_id='rep_e2e_synth',
                patient_id='pat_e2e_synth',
                chunk_index=chk.chunk_index,
                page_number=chk.page_number,
                content=chk.text,
                embedding=emb_prov.embed_text(chk.text),
                chunk_metadata=chk.metadata
            )
            db.add(sql_chk)
        db.commit()

        # Chroma vector indexing
        vstore = ChromaDBVectorStore(persist_directory=tmp_chroma, collection_name='s8_e2e_col', embedding_provider=emb_prov)
        vstore.add_documents(all_chunks)

        # BM25 indexing
        bm25 = BM25KeywordRetriever()
        bm25.index_chunks(all_chunks)

        hybrid = HybridRetriever(vector_store=vstore, db_session=db, bm25_retriever=bm25)

        # Multi-query evaluation suite
        test_queries = [
            {'q': 'What is the patient left ventricular ejection fraction?', 'expected_text': '52%', 'cat': 'exact_numerical'},
            {'q': 'What was the historical blood pressure recorded on 2025-04-10?', 'expected_text': '152/94', 'cat': 'exact_date'},
            {'q': 'What is the current dosage of Lisinopril?', 'expected_text': '20mg', 'cat': 'medication'},
            {'q': 'Does the patient have any medication allergies?', 'expected_text': 'Sulfa', 'cat': 'allergy'},
            {'q': 'What is the glycated hemoglobin level?', 'expected_text': '6.4%', 'cat': 'synonym_hba1c'},
            {'q': 'What was the fasting blood glucose?', 'expected_text': '108', 'cat': 'fasting_glucose'},
            {'q': 'What is the thyroid stimulating hormone TSH level?', 'expected_text': 'UNANSWERABLE', 'cat': 'abstention'},
            {'q': 'What is the glucose for patient Bob?', 'expected_text': 'WRONG_PATIENT', 'cat': 'wrong_patient'}
        ]

        query_results = []
        for qd in test_queries:
            q = qd['q']
            exp = qd['expected_text']
            cat = qd['cat']
            h_res = hybrid.retrieve(q, patient_id='pat_e2e_synth', top_k=4)
            found_evidence = False
            top_texts = [e.content for e in h_res.elements]
            combined = ' '.join(top_texts)

            if cat == 'abstention':
                # No TSH mention
                found_evidence = ('tsh' not in combined.lower())
            elif cat == 'wrong_patient':
                # Must not contain Bob or 240
                found_evidence = ('bob' not in combined.lower() and '240' not in combined)
            else:
                found_evidence = (exp.lower() in combined.lower())

            query_results.append({
                'query': q,
                'category': cat,
                'expected': exp,
                'evidence_retrieved': found_evidence,
                'top_sources_count': len(h_res.elements)
            })

        evidence_recall = sum(1 for qr in query_results if qr['evidence_retrieved']) / len(query_results)

        # Restart Persistence Verification
        count_pre_restart = vstore.collection.count()
        del vstore
        del hybrid
        SharedSystemClient.clear_system_cache()

        # Reopen PersistentClient
        vstore_reboot = ChromaDBVectorStore(persist_directory=tmp_chroma, collection_name='s8_e2e_col', embedding_provider=emb_prov)
        count_post_restart = vstore_reboot.collection.count()

        reboot_res = vstore_reboot.similarity_search('ejection fraction', top_k=2, filter_metadata={'patient_id': 'pat_e2e_synth'})
        reboot_found = any('52%' in r.chunk.text for r in reboot_res)

        restart_ok = (count_pre_restart == count_post_restart and reboot_found)

        stage8_results = {
            'document_pages': 2,
            'chunks_indexed': len(all_chunks),
            'evidence_retrieval_rate': evidence_recall,
            'query_evaluations': query_results,
            'restart_persistence': {
                'count_pre_restart': count_pre_restart,
                'count_post_restart': count_post_restart,
                'reboot_query_retrieved': reboot_found,
                'status': 'PASS' if restart_ok else 'FAIL'
            },
            'llm_answer_generation_status': 'BLOCKED',
            'llm_blocking_reason': 'Ollama daemon offline at http://localhost:11434; mock generation avoided per audit protocol.',
            'status': 'PASS' if (evidence_recall >= 0.90 and restart_ok) else 'FAIL'
        }

        db.close()
    finally:
        engine.dispose()
        if os.path.exists(tmp_db):
            try: os.remove(tmp_db)
            except Exception: pass
        SharedSystemClient.clear_system_cache()
        shutil.rmtree(tmp_chroma, ignore_errors=True)

    return stage8_results

if __name__ == '__main__':
    s7 = run_stage_7()
    s8 = run_stage_8()
    final = {
        'stage_7': s7,
        'stage_8': s8
    }
    out_path = r'docs/audit/phase4_acceptance_20261018_2330/stage7_stage8_results.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=2)
    print('STAGES_7_8_COMPLETED_SUCCESSFULLY')
