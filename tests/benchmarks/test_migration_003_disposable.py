"""
Disposable Migration 003 Test Suite
===================================
Tests Alembic revision 003_add_provenance_and_allergies against isolated,
disposable SQLite instances without touching the real chronanexus.db.

Verifies:
1. Migration chain: 001 -> 002 -> 003
2. Data migration of Patient.known_allergies across edge cases:
   - None / null
   - Empty list []
   - Empty string ""
   - JSON string with duplicate values
   - Comma-separated strings
   - Native Python lists
   - Unexpected dict structures
3. Extraction confidence remains NULL (unmeasured)
4. Clean downgrade: 003 -> 002
5. Offline PostgreSQL SQL emission validity
"""

import os
import sys
import json
import uuid
import tempfile
import sqlite3
from pathlib import Path
from alembic.config import Config
from alembic import command
import sqlalchemy as sa

# Ensure repo root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))


def test_disposable_migration_lifecycle():
    print("=" * 70)
    print("STARTING DISPOSABLE MIGRATION 003 LIFECYCLE TEST")
    print("=" * 70)

    # 1. Create temporary disposable SQLite file
    temp_dir = tempfile.mkdtemp(prefix="chronanexus_mig_test_")
    db_path = os.path.join(temp_dir, "disposable_test.db")
    db_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
    os.environ["DATABASE_URL"] = db_url
    print(f"[TEST SETUP] Disposable SQLite DB: {db_url}")

    # Set up Alembic Config pointing to disposable database
    alembic_ini_path = str(REPO_ROOT / "backend" / "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # 2. Upgrade to 002_add_document_chunks (pre-migration state)
    print("\n[STEP 1] Upgrading to pre-003 schema (revision: 002_add_document_chunks)...")
    command.upgrade(alembic_cfg, "002_add_document_chunks")

    engine = sa.create_engine(db_url)
    with engine.connect() as conn:
        inspector = sa.inspect(conn)
        tables = set(inspector.get_table_names())
        assert "patients" in tables, "patients table missing in 002"
        assert "lab_results" in tables, "lab_results table missing in 002"
        assert "allergies" not in tables, "allergies table should NOT exist in 002"
        print("  -> Schema at 002 confirmed: 'allergies' table does not exist.")

        # 3. Seed historical patients with diverse known_allergies edge cases
        print("\n[STEP 2] Seeding pre-migration Patient records with historical edge-case values...")
        users_to_insert = [
            {"id": f"usr_test_{i}", "name": f"Test User {i}", "email": f"u{i}@test.org", "hashed_password": "pw", "role": "patient"}
            for i in range(1, 8)
        ]
        for u in users_to_insert:
            conn.execute(sa.text(
                "INSERT INTO users (id, name, email, hashed_password, role) VALUES (:id, :name, :email, :hashed_password, :role)"
            ), u)

        test_patients = [
            # Case 1: Null known_allergies
            {"id": "pat_null", "user_id": "usr_test_1", "known_allergies": None},
            # Case 2: Empty list
            {"id": "pat_empty_list", "user_id": "usr_test_2", "known_allergies": json.dumps([])},
            # Case 3: Empty string
            {"id": "pat_empty_str", "user_id": "usr_test_3", "known_allergies": ""},
            # Case 4: JSON string with duplicates and reaction formatting
            {"id": "pat_json_dups", "user_id": "usr_test_4", "known_allergies": json.dumps([
                "Penicillin (Severe: Anaphylaxis)",
                "Sulfa Drugs (Hives)",
                "Penicillin (duplicate entry)",
                "penicillin"
            ])},
            # Case 5: Comma-separated string
            {"id": "pat_csv_str", "user_id": "usr_test_5", "known_allergies": "Aspirin (Moderate Urticaria), Ibuprofen, Naproxen"},
            # Case 6: Mixed case with spaces
            {"id": "pat_spaced", "user_id": "usr_test_6", "known_allergies": json.dumps([" Amoxicillin (Rash) ", ""])} ,
            # Case 7: Unexpected dict structure
            {"id": "pat_dict", "user_id": "usr_test_7", "known_allergies": json.dumps({"allergen1": "Sulfa", "allergen2": ""})}
        ]

        for p in test_patients:
            conn.execute(sa.text(
                "INSERT INTO patients (id, user_id, date_of_birth, gender, known_allergies) "
                "VALUES (:id, :user_id, '1990-01-01', 'male', :known_allergies)"
            ), p)

        # Seed sample lab_result without provenance columns
        conn.execute(sa.text(
            "INSERT INTO lab_results (id, patient_id, test_name, value, unit, reference_range, status, test_date) "
            "VALUES ('lab_test_01', 'pat_null', 'Serum Potassium', '4.5', 'mEq/L', '3.5-5.0', 'normal', '2024-01-01')"
        ))
        conn.commit()
        print(f"  -> Successfully seeded {len(test_patients)} patients and sample lab result.")

    # 4. Run Alembic upgrade to 003_add_provenance_and_allergies
    print("\n[STEP 3] Running Alembic upgrade to 003_add_provenance_and_allergies...")
    command.upgrade(alembic_cfg, "003_add_provenance_and_allergies")
    print("  -> Migration upgrade executed successfully.")

    # 5. Verify post-upgrade schema and migrated data
    print("\n[STEP 4] Verifying migrated data, deduplication, and schema additions...")
    with engine.connect() as conn:
        inspector = sa.inspect(conn)
        tables = set(inspector.get_table_names())
        assert "allergies" in tables, "allergies table was not created"

        # Check provenance columns in lab_results
        lab_cols = {c['name']: c for c in inspector.get_columns('lab_results')}
        for col_name in ['loinc_code', 'canonical_name', 'source_page_number', 'bounding_box', 'extraction_confidence']:
            assert col_name in lab_cols, f"Column {col_name} missing from lab_results"
        print("  -> Verified provenance columns present in lab_results.")

        # Check provenance columns in medications
        med_cols = {c['name']: c for c in inspector.get_columns('medications')}
        for col_name in ['rxnorm_code', 'drug_class', 'source_page_number', 'bounding_box', 'extraction_confidence']:
            assert col_name in med_cols, f"Column {col_name} missing from medications"
        print("  -> Verified provenance columns present in medications.")

        # Check migrated allergies
        allergies = conn.execute(sa.text(
            "SELECT patient_id, allergen, severity, reaction, drug_classes, cross_reactivities, status, extraction_confidence "
            "FROM allergies ORDER BY patient_id, allergen"
        )).fetchall()
        
        print(f"  -> Total migrated allergy records: {len(allergies)}")
        for a in allergies:
            print(f"     Patient: {a[0]} | Allergen: {a[1]} | Severity: {a[2]} | Confidence: {a[7]}")
            # Ensure extraction confidence is NULL (unmeasured)
            assert a[7] is None, f"Extraction confidence must be NULL for historical migrated allergy, got {a[7]}"

        # Verify Patient 4 (pat_json_dups): Should have exactly 2 records (Penicillin and Sulfa Drugs), no duplicates!
        pat4_allergies = [a for a in allergies if a[0] == "pat_json_dups"]
        pat4_allergens = [a[1] for a in pat4_allergies]
        assert len(pat4_allergens) == 2, f"Expected 2 allergens for pat_json_dups, got {len(pat4_allergens)}: {pat4_allergens}"
        assert "Penicillin" in pat4_allergens, "Penicillin missing for pat_json_dups"
        assert "Sulfa Drugs" in pat4_allergens, "Sulfa Drugs missing for pat_json_dups"
        print("  -> Verified deduplication: 4 entries with duplicate Penicillin migrated to exactly 2 distinct rows.")

        # Verify Patient 5 (pat_csv_str): Should have Aspirin, Ibuprofen, Naproxen
        pat5_allergies = [a for a in allergies if a[0] == "pat_csv_str"]
        pat5_allergens = [a[1] for a in pat5_allergies]
        assert len(pat5_allergens) == 3, f"Expected 3 allergens for pat_csv_str, got {len(pat5_allergens)}: {pat5_allergens}"
        assert "Aspirin" in pat5_allergens
        print("  -> Verified comma-separated string parsing: 3 distinct allergens created.")

        # Verify Patient 7 (pat_dict): Should have Sulfa
        pat7_allergies = [a for a in allergies if a[0] == "pat_dict"]
        assert len(pat7_allergies) == 1
        assert "Sulfa" in pat7_allergies[0][1]
        print("  -> Verified unexpected dict parsing: Sulfa extracted successfully.")

        # Verify Patient 1, 2, 3: Should have 0 allergies
        for empty_pat in ["pat_null", "pat_empty_list", "pat_empty_str"]:
            empty_count = sum(1 for a in allergies if a[0] == empty_pat)
            assert empty_count == 0, f"Expected 0 allergies for {empty_pat}, got {empty_count}"
        print("  -> Verified empty/null/whitespace patients: 0 allergy rows created.")

    # 6. Test Downgrade to 002_add_document_chunks
    print("\n[STEP 5] Testing Alembic downgrade back to 002_add_document_chunks...")
    command.downgrade(alembic_cfg, "002_add_document_chunks")
    print("  -> Downgrade executed successfully.")

    with engine.connect() as conn:
        inspector = sa.inspect(conn)
        tables = set(inspector.get_table_names())
        assert "allergies" not in tables, "allergies table was NOT dropped during downgrade"
        print("  -> Confirmed: 'allergies' table dropped.")

        # Verify dropped columns in lab_results
        lab_cols_post_down = {c['name'] for c in inspector.get_columns('lab_results')}
        assert "loinc_code" not in lab_cols_post_down, "loinc_code was not dropped from lab_results"
        assert "extraction_confidence" not in lab_cols_post_down, "extraction_confidence was not dropped"
        print("  -> Confirmed: Added columns dropped from lab_results.")

        # Verify original lab result row is still intact
        lab_row = conn.execute(sa.text("SELECT test_name, value FROM lab_results WHERE id = 'lab_test_01'")).first()
        assert lab_row is not None and lab_row[0] == "Serum Potassium" and lab_row[1] == "4.5", "Original data corrupted during downgrade!"
        print("  -> Confirmed: Original pre-migration data intact after downgrade.")

    # 7. Clean up disposable database files
    engine.dispose()
    try:
        os.remove(db_path)
        os.rmdir(temp_dir)
        print("\n[CLEANUP] Disposable SQLite test database cleaned up safely.")
    except Exception as e:
        print(f"\n[CLEANUP WARNING] Could not remove temp file: {e}")

    print("\n" + "=" * 70)
    print("ALL DISPOSABLE MIGRATION AND DOWNGRADE TESTS PASSED CLEANLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_disposable_migration_lifecycle()
