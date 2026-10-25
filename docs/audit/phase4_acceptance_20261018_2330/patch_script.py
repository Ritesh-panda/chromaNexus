with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'r', encoding='utf-8') as f:
    text = f.read()

PREFIX = "sys.path.insert(0, 'C:/chromaNexus')\nsys.path.insert(0, 'C:/chromaNexus/backend')"
text = text.replace("sys.path.insert(0, r_$xxx')", PREFIX)
if 'C/chromaNexus/backend' not in text:
    text = PREFIX + '\n' + text

text = text.replace('from app.db.session import Base', 'from backend.app.core.database import Base')
text = text.replace('from app.models.models', 'from backend.app.models.models')
text = text.replace('from app.ai.retrieval', 'from backend.app.ai.retrieval')
text = text.replace('from app.ai.embeddings', 'from backend.app.ai.embeddings')
text = text.replace('from app.ai.ingestion.orchestrator', 'from backend.app.ai.ingestion.orchestrator')

with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('PATCHED_SUCCESSFULLY')
