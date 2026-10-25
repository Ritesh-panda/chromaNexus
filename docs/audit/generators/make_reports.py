# ChronaNexus Forensic Master Audit Dossier Builder
import os, json, hashlib, time, glob

AUDIT_DIR = 'C:/chromaNexus/docs/audit'
os.makedirs(AUDIT_DIR, exist_ok=True)
os.makedirs(os.path.join(AUDIT_DIR, 'evidence'), exist_ok=True)

def save(filename, content):
    p = os.path.join(AUDIT_DIR, filename)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f'SUCCESS: Saved {filename} ({len(content)} characters)')

