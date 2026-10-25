with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("patient_id='p_sync'", "filter_metadata={'patient_id': 'p_sync'}")
with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('PARAM_FIXED')
