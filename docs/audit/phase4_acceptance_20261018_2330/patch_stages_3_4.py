with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'SELECT id FROM document_chunks' in line:
        line = line.replace('SELECT id FROM', 'SELECT chunk_id FROM')
    elif 'u = User(' in line:
        line = "        u = User(id='u_sync', name='Auditor', email='audit@sync.org', hashed_password='x')\n"
    elif 'p = Patient(' in line:
        line = "        p = Patient(id='p_sync', user_id='u_sync', date_of_birth='1990-01-01', gender='male')\n"
    elif 'r = MedicalReport(' in line:
        line = "        r = MedicalReport(id='r_sync', patient_id='p_sync', title='Echo', file_name='echo.pdf', hospital_name='Test Hospital', report_date='2026-10-18')\n"
    elif "id=f'chk_sync_{i}'," in line and 'DocumentChunkModel' in new_lines[-1]:
        line = "                id=f'id_sync_{i}',\n                chunk_id=f'chk_sync_{i}',\n                document_id='r_sync',\n                patient_id='p_sync',\n"
    elif "report_id='r_sync'," in line and 'DocumentChunkModel' in (new_lines[-2] if len(new_lines) >= 2 else ''):
        continue
    elif 'chunk_id=sql_chunks_inserted[i].id,' in line:
        line = line.replace('chunk_id=sql_chunks_inserted[i].id,', 'chunk_id=sql_chunks_inserted[i].chunk_id,')
    elif 'if c.id not in existing_ids' in line:
        line = line.replace('if c.id not in', 'if c.chunk_id not in')
    elif 'chunk_id=c.id,' in line:
        line = line.replace('chunk_id=c.id,', 'chunk_id=c.chunk_id,')
    elif 'id=new_id,' in line and 'DocumentChunkModel' in (new_lines[-1] if len(new_lines) >= 1 else ''):
        line = "            id='id_inc_999',\n            chunk_id=new_id,\n            document_id='r_sync',\n            patient_id='p_sync',\n"
    elif "report_id='r_sync'," in line and 'id_inc_999' in (new_lines[-1] if len(new_lines) >= 1 else ''):
        continue
    new_lines.append(line)

with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('PATCH_APPLIED')
