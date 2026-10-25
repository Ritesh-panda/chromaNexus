with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("fruser_{i}'", f"'ruser_{i}'")
text = text.replace("fruser_{ie'", f"'ruser_{i}'")
for var in ["stage4_resultsÉç4.3", "stage4_resultsÉç"]:
    text = text.replace(var, "stage4_results['4.3")
with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('FIXED_ALL')
