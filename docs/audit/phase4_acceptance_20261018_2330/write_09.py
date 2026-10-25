import os

AUDIT_DIR = r'docs/audit/phase4_acceptance_20261018_2330'

md_09 = """# 09 – Reproducibility Guide

All steps in this audit are 100% reproducible using the following commands in a Windows PowerShell / CMD / Bash environment.

## 1. Run the Full Audit Suite

```powershell
# 1. Run Stage 3 & 4 Tests (ChromaDB & SQL Sync)
python docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py

# 2. Run Stage 5 & 6 Tests (BM25 & RRF Mathematics)
python docs/audit/phase4_acceptance_20261018_2330/run_stages_5_6.py

# 3. Run Stage 7 & 8 Tests (Patient Isolation & ETE)
python docs/audit/phase4_acceptance_20261018_2330/run_stages_7_8.py

# 4. Run Synthetic 12-Scenario Benchmark
python tests/benchmarks/retrieval_benchmark.py

# 5. Run Full Backend Regression Suite
python -m pytest backend/tests -v
```

## 2. Database Preservation Verification

```powershell
python -c "import hashlib, os; print('chronanexus.db sha256:', hashlib.sha256(open(r'C:\chromaNexus\chronanexus.db', 'rb').read()).hexdigest())"
```
Expected SHA-256: `be882c255ee738d489d5eb59e97ce6b472d236dfe183513d1b704796ffa5f932` (462,848 bytes).
"""

with open(os.path.join(AUDIT_DIR, '09_REPRODUCE.md'), 'w', encoding='utf-8') as f:
    f.write(md_09)

print('WROTE_09')
