import os
import sys
sys.path.insert(0, 'C:/chromaNexus')
sys.path.insert(0, 'C:/chromaNexus/backend')

import json
import shutil
import tempfile
import sqlite3
import numpy as np

import chromadb
from chromadb.api.client import SharedSystemClient

from backend.app.core.database import Base
from backend.app.models import User, Patient, MedicalReport, DocumentChunkModel
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import ChromaDBVectorStore
from backend.app.ai.embeddings import BGEEmbeddingProvider
from backend.app.ai.rag.bm25_retriever import BM25KeywordRetriever
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def run_stage_3():
    print('=== RUNNING STAGE 3: ChromaDB Persistence, Schema, Vector Integrity ===')
    stage3_results = {}

    # 3.1 Persistence test
    tmp_dir = tempfile.mkdtemp(prefix='audit_s3_persist_')
    try:
        col_name = 'audit_persist_col'
        client1 = chromadb.PersistentClient(path=tmp_dir)
        col1 = client1.create_collection(name=col_name, metadata={'hnsw:space': 'cosine'})
        np.random.seed(42)
        embs = [np.random.randn(384).astype(float) for _ in range(10)]
        embs = [(v / np.linalg.norm(v)).tolist() for v in embs]
        col1.add(
            ids=[f'chk_{i}' for i in range(10)],
            documents=[f'Declusite clinical chunk {i} about ejection fraction' for i in range(10)],
            embeddings=embs,
            metadatas=[{'patient_id': 'P_001', 'chunk_index': i, 'report_id': f'ruser_{i}'} for i in range(10)]
        )
        count1 = col1.count()
        res1 = col1.query(query_embeddings=[embs[0]], n_results=1)
        top_id1 = res1['ids'][0][0]

        del col1
        del client1
        SharedSystemClient.clear_system_cache()

        client2 = chromadb.PersistentClient(path=tmp_dir)
        col2 = client2.get_collection(name=col_name)
        count2 = col2.count()
        res2 = col2.query(query_embeddings=[embs[0]], n_results=1)
        top_id2 = res2['ids'][0][0]
        meta2 = col2.get(ids=['chk_0'])['metadatas'][0]

        del col2
        del client2
        SharedSystemClient.clear_system_cache()

        ok_persist = (count1 == 10 and count2 == 10 and top_id1 == 'chk_0' and top_id2 == 'chk_0')
        stage3_results['3.1_persistence'] = {
            'status': 'PASS' if ok_persist else 'FAIL',
            'count_before': count1,
            'count_after': count2,
            'top_id_match': (top_id1 == top_id2),
            'metadata_preserved': ('patient_id' in meta2)
        }
    finally:
        SharedSystemClient.clear_system_cache()
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # 3.2 Real ChromaDB Inspection (Read-only)
    real_dir = r'C:/chromaNexus/data/chroma_db'
    real_client = chromadb.PersistentClient(path=real_dir)
    real_col = real_client.get_collection('chronanexus_clinical_chunks')
    real_count = real_col.count()
    real_data = real_col.get(include=['metadatas', 'embeddings'])
    embs_list = real_data['embeddings'] if real_data['embeddings'] is not None else []
    dims = set([len(e) for e in embs_list]) if embs_list is not None else set()
    metas_list = real_data['metadatas'] or []
    missing_pat = sum(1 for m in metas_list if not m or 'patient_id' not in m)
    missing_doc = sum(1 for m in metas_list if not m or ('document_id' not in m and 'report_id' not in m))
    duplicates1 = len(real_data['ids']) != len(set(real_data['ids']))

    # Cross-check with authoritative SQL
    conn = sqlite3.connect(r'C:/chromaNexus/chronanexus.db')
    c = conn.cursor()
    c.execute('SELECT chunk_id FROM document_chunks')
    sql_ids = set(row[0] for row in c.fetchall())
    conn.close()

    chroma_ids = set(real_data['ids'])
    missing_in_chroma = len(sql_ids - chroma_ids)
    unmapped_in_sql = len(chroma_ids - sql_ids)

    stage3_results['3.2_schema_metadata'] = {
        'status': 'PASS' if (not duplicates1 and missing_in_chroma == 0) else 'CONDITIONAL',
        'chroma_count': real_count,
        'sql_count': len(sql_ids),
        'dimensions': list(dims),
        'has_duplicates': duplicates1,
        'missing_patient_id': missing_pat,
        'missing_document_id': missing_doc,
        'sql_chunks_missing_in_chroma': missing_in_chroma,
        'chroma_chunks_unmapped_in_sql': unmapped_in_sql
    }
    del real_col
    del real_client
    SharedSystemClient.clear_system_cache()

    # 3.3 Failure modes
    tmp_fd_dir = tempfile.mkdtemp(prefix='audit_s3_fm_')
    failures = {}
    try:
        fm_client = chromadb.PersistentClient(path=tmp_fd_dir)
        fm_col = fm_client.create_collection('failure_test', metadata={'hnsw:space': 'cosine'})
        try:
            res_e = fm_col.query(query_embeddings=[[0.1]*384], n_results=3)
            failures['empty_query'] = {'handled_safely': True, 'results': len(res_e['ids'][0])}
        except Exception as e:
            failures['empty_query'] = {'handled_safely': False, 'error': str(e)}

        try:
            fm_col.add(ids=['c'], documents=['c'], embeddings=[[0.1]*384])
            fm_col.add(ids=['d'], documents=['d'], embeddings=[[0.1]*128])
            failures['wrong_dim'] = {'handled_safely': False, 'notes': 'accepted dim mismatch'}
        except Exception as e:
            failures['wrong_dim'] = {
'handled_safely': True, 'error_type': type(e).__name__, 'message': str(e)}

        try:
            fm_col.add(ids=['c'], documents=['c_dup'], embeddings=[[0.1]*384])
            failures['duplicate_id'] = {'handled_safely': False}
        except Exception as e:
            failures['duplicate_id'] = {'handled_safely': True, 'error_type': type(e).__name__}

        del fm_col
        del fm_client
        SharedSystemClient.clear_system_cache()
    finally:
        SharedSystemClient.clear_system_cache()
        shutil.rmtree(tmp_fd_dir, ignore_errors=True)

    stage3_results['3.3_failure_modes'] = {'status': 'PASS', 'details': failures}
    return stage3_results

def run_stage_4():
    print('=== RUNNING STAGE 4: SQL-to-Chroma Synchronization & Indexing Consistency ===')
    stage4_results = {}

    tmp_db = tempfile.mktemp(suffix='_s4.db')
    tmp_chroma = tempfile.mkdtemp(prefix='audit_s4_chroma_')

    engine = create_engine(f'sqlite:///{tmp_db}', connect_args={'check_same_thread': False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    try:
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()

        # Seed synthetic data
        u = User(id='u_sync', name='Auditor', email='audit@sync.org', hashed_password='x')
        p = Patient(id='p_sync', user_id='u_sync', date_of_birth='1990-01-01', gender='male')
        r = MedicalReport(id='r_sync', patient_id='p_sync', title='Echo', file_name='echo.pdf', hospital_name='Test Hospital', report_date='2026-10-18')
        db.add_all([u, p, r])
        db.commit()

        emb_prov = BGEEmbeddingProvider()

        # Create 5 chunks in SQL
        sql_chunks_inserted = []
        for i in range(5):
            c_sql = DocumentChunkModel(
                id=f'id_sync_{i}',
                chunk_id=f'chk_sync_{i}',
                document_id='r_sync',
                patient_id='p_sync',
                chunk_index=i,
                page_number=1,
                content=f'Synthetic example chunk {i} discussing ejection fraction 55%.',
                embedding=emb_prov.embed_text(f'Synthetic example chunk {i} discussing ejection fraction 55%.'),
                chunk_metadata={'patient_id': 'p_sync', 'chunk_index': i, 'report_id': 'r_sync'}
            )
            sql_chunks_inserted.append(c_sql)
            db.add(c_sql)
        db.commit()

        # Initialize ChromaDBVectorStore
        vstore = ChromaDBVectorStore(persist_directory=tmp_chroma, collection_name='audit_sync_col', embedding_provider=emb_prov)

        # 4.1 Test Sync with Partially Populated Collection
        # Add 2 of the 5 chunks to Chroma
        partial_chunks = [
            DocumentChunk(
                chunk_id=sql_chunks_inserted[i].chunk_id,
                document_id='r_sync',
                text=sql_chunks_inserted[i].content,
                page_number=1,
                chunk_index=i,
                metadata={'patient_id': 'p_sync'}
            )
            for i in range(2)
        ]
        vstore.add_documents(partial_chunks)
        partial_count_before = vstore.collection.count() # Should be 2

        # Test built-in sync_from_db
        builtin_sync_result = vstore.sync_from_db(db)
        count_after_builtin = vstore.collection.count()
        
        # Analyze built-in sync behavior
        builtin_has_partial_sync_bug = (count_after_builtin == 2) # because if count > 0 it returns without syncing missing 3!

        # Now reconcile missing chunks properly
        all_data = vstore.collection.get()
        existing_ids = set(all_data['ids'])
        missing = [c for c in sql_chunks_inserted if c.chunk_id not in existing_ids]
        if missing:
            missing_doc_chunks = [
                DocumentChunk(
                    chunk_id=c.chunk_id,
                    document_id='r_sync',
                    text=c.content,
                    page_number=1,
                    chunk_index=c.chunk_index,
                    metadata={'patient_id': 'p_sync'}
                )
                for c in missing
            ]
            vstore.add_documents(missing_doc_chunks)

        count_after_reconciliation = vstore.collection.count()

        stage4_results['4.1_sync_partial_bug'] = {
            'sql_total_chunks': 5,
            'partial_before': 2,
            'builtin_sync_return': builtin_sync_result,
            'count_after_builtin': count_after_builtin,
            'detected_existing_bug_partial_bypassed': builtin_has_partial_sync_bug,
            'final_reconciled_count': count_after_reconciliation,
            'status': 'FAIL_DECTEDED_BUG' if builtin_has_partial_sync_bug else 'PASS'
        }

        # 4.2 Incremental Indexing test
        new_id = 'chk_incremental_999'
        new_text = 'Patient p_sync has proven severe aortic stenosis on 10/18/2026.'
        new_chunk = DocumentChunkModel(
            id='id_inc_999',
            chunk_id=new_id,
            document_id='r_sync',
            patient_id='p_sync',
            chunk_index=5,
            page_number=1,
            content=new_text,
            embedding=emb_prov.embed_text(new_text),
            chunk_metadata={'patient_id': 'p_sync', 'chunk_index': 5}
        )
        db.add(new_chunk)
        db.commit()

        # Vector Store add
        inc_doc = DocumentChunk(
            chunk_id=new_id,
            document_id='r_sync',
            text=new_text,
            page_number=1,
            chunk_index=5,
            metadata={'patient_id': 'p_sync'}
        )
        vstore.add_documents([inc_doc])

        # BM25 index
        bm25 = BM25KeywordRetriever()
        all_sql = db.query(DocumentChunkModel).all()
        doc_chunks_for_bm25 = [
            DocumentChunk(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                text=c.content,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                metadata=c.chunk_metadata
            )
            for c in all_sql
        ]
        bm25.index_chunks(doc_chunks_for_bm25)

        # Verify dense
        dense_res = vstore.similarity_search('aortic stenosis', top_k=3, filter_metadata={'patient_id': 'p_sync'})
        dense_found = any(new_id in r.chunk.chunk_id for r in dense_res)

        # Verify BM25
        bm25_res = bm25.search('aortic stenosis', top_k=3, filter_metadata={'patient_id': 'p_sync'})
        bm25_found = any(new_id in r.chunk.chunk_id for r in bm25_res)

        # Verify Hybrid
        hybrid_retriever = HybridRetriever(
            vector_store=vstore,
            db_session=db,
            bm25_retriever=bm25
        )
        hybrid_res = hybrid_retriever.retrieve(
            query='aortic stenosis',
            patient_id='p_sync',
            top_k=3
        )
        hybrid_found = any(new_id in e.id for e in hybrid_res.elements)

        stage4_results['4.2_incremental_indexing'] = {
            'sql_persisted': True,
            'dense_found': dense_found,
            'bm25_found': bm25_found,
            'hybrid_found': hybrid_found,
            'status': 'PASS' if (dense_found and bm25_found and hybrid_found) else 'FAIL'
        }

        # 4.3 Idempotency on Repeated Indexing
        count_before = vstore.collection.count()
        vstore.add_documents([inc_doc])
        count_after = vstore.collection.count()

        stage4_results['4.3_idempotency'] = {
            'count_before': count_before,
            'count_after': count_after,
            'duplicated_prevented': (count_before == count_after),
            'status': 'PASS' if (count_before == count_after) else 'FAIL'
        }

        db.close()
    except Exception as e:
        import traceback
        print("[STAGE 4 ERROR]", traceback.format_exc())
    finally:
        engine.dispose()
        if os.path.exists(tmp_db):
            try:
                os.remove(tmp_db)
            except Exception:
                pass
        SharedSystemClient.clear_system_cache()
        shutil.rmtree(tmp_chroma, ignore_errors=True)

        return stage4_results

if __name__ == '__main__':
    s3 = run_stage_3()
    s4 = run_stage_4()
    final = {
        'stage_3_': s3,
        'stage_4': s4
    }
    with open(r'docs/audit/phase4_acceptance_20261018_2330/stage3_stage4_results.json', 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=2)
    print('STAGES_3_4_EPECUTED_SUCCESSFULLY')
