import os, json, hashlib

AUDIT_DIR = 'C:/chromaNexus/docs/audit'
os.makedirs(AUDIT_DIR, exist_ok=True)
os.makedirs(os.path.join(AUDIT_DIR, 'evidence'), exist_ok=True)

def write_doc(filename, content):
    path = os.path.join(AUDIT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f'Wrote {filename} ({len(content)} bytes)')

print('make_dossier scaffold ready.')
