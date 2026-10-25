with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("embs_list = real_data['embeddings'] or []", "embs_list = real_data['embeddings'] if real_data['embeddings'] is not None else []")
with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('FIXED')
