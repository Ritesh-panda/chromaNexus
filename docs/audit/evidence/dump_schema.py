import os
import json
import sqlite3

DB_PATH = "chronanexus.db"
OUT = os.path.join("docs", "audit", "evidence", "chronanexus_db_schema.json")

conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [r[0] for r in cur.fetchall()]

schema_info = {}

for t in tables:
    cur.execute(f"PRAGMA table_info('{t}');")
    cols = [{"cid": r[0], "name": r[1], "type": r[2], "notnull": bool(r[3]), "dflt_value": r[4], "pk": bool(r[5])} for r in cur.fetchall()]
    
    cur.execute(f"PRAGMA foreign_key_list('{t}');")
    fks = [{"id": r[0], "seq": r[1], "table": r[2], "from": r[3], "to": r[4], "on_update": r[5], "on_delete": r[6]} for r in cur.fetchall()]
    
    cur.execute(f"PRAGMA index_list('{t}');")
    idxs = [{"seq": r[0], "name": r[1], "unique": bool(r[2]), "origin": r[3], "partial": bool(r[4])} for r in cur.fetchall()]
    
    cur.execute(f"SELECT count(*) FROM '{t}';")
    row_count = cur.fetchone()[0]

    schema_info[t] = {
        "columns": cols,
        "foreign_keys": fks,
        "indexes": idxs,
        "row_count": row_count
    }

conn.close()

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(schema_info, f, indent=2)

print(f"Dumped schema for {len(tables)} tables to {OUT}.")
for t, d in schema_info.items():
    print(f" - {t}: {len(d['columns'])} cols, {d['row_count']} rows")
