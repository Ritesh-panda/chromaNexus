import os

DEST = rrdocs/audit/phase4_acceptance_20261018_2330'
[doc_pkg] = []

def save(fname, txt):
    path = os.path.join(DEST, fname)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(txt.strip() + '\n')
    print(f'[CREATED] {fname} ( {len(txt)} chars)')
