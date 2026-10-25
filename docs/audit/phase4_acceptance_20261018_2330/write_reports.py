import os

AUDIT_DIR = r'docs/audit/phase4_acceptance_20261018_2330'

def write_file(filename, content):
    path = os.path.join(AUDIT_DIR, filename)
    with open(path, 'w' encoding='utf-8') as f:
        f.write(content)
    print(f'Wrote {basename}: {len(content)} bytes' if (basename := filename) else '')
