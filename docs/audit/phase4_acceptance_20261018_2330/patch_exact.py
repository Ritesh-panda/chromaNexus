with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'r', encoding='utf-8') as f:
    text = f.read()

#fix dense
text = text.replace("vstore.similarity_search('aortic stenosis', top_k=3, patient_id='p_sync')", "vstore.similarity_search('aortic stenosis', top_k=3, filter_metadata={'patient_id': 'p_sync'})")

# fix bm25
text = text.replace("bm25.search('aortic stenosis', patient_id='p_sync', top_k=3)", "bm25.search('aortic stenosis', top_k=3, filter_metadata={'patient_id': 'p_sync'})")
text = text.replace("any(new_id in r.chunk_id for r in bm25_res)", "any(new_id in r.chunk.chunk_id for r in bm25_res)")

# fix hybrid
text = text.replace("limit=3", "top_k=3")

# fix success message typo
text = text.replace("STAGES_3_4_EPECUTED_SUCCESSFULLY", "STAGES_3_4_EPECUTED_SUCCESSFULLY")

with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('PATCH_EXACT_DONE')
