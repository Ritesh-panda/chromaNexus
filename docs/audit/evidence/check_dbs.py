import sqlite3

def check_db(path):
    print(f"=== DB: {path} ===")
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print("Tables:", tables)
        if "alembic_version" in tables:
            cur.execute("SELECT version_num FROM alembic_version")
            print("Alembic version:", cur.fetchall())
        else:
            print("No alembic_version table")
        conn.close()
    except Exception as e:
        print("Error:", e)

check_db("chronanexus.db")
check_db("backend/chronanexus.db")
check_db("test_chronanexus.db")
check_db("tests/benchmarks/synthetic_benchmark.db")
check_db("tests/benchmarks/exp_synthetic.db")
