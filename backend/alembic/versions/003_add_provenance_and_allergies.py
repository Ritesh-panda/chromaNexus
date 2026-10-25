"""Add allergy model and clinical data provenance foundations

Revision ID: 003_add_provenance_and_allergies
Revises: 002_add_document_chunks
Create Date: 2026-10-17

"""
from typing import Sequence, Union
import json
import uuid
from alembic import op, context
import sqlalchemy as sa

revision: str = '003_add_provenance_and_allergies'
down_revision: Union[str, None] = '002_add_document_chunks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    is_offline = context.is_offline_mode()
    existing_tables = set()
    inspector = None
    conn = None

    if not is_offline:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_tables = set(inspector.get_table_names())

    # -------------------------------------------------------------------------
    # 1. Create allergies table if not present
    # -------------------------------------------------------------------------
    if is_offline or 'allergies' not in existing_tables:
        op.create_table(
            'allergies',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=False),
            sa.Column('allergen', sa.String(length=255), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=True, server_default="medication"),
            sa.Column('severity', sa.String(length=50), nullable=True, server_default="moderate"),
            sa.Column('reaction', sa.String(length=255), nullable=True),
            sa.Column('drug_classes', sa.JSON(), nullable=True),
            sa.Column('cross_reactivities', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True, server_default="active"),
            sa.Column('source_report_id', sa.String(length=36), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('source_page_number', sa.Integer(), nullable=True),
            sa.Column('bounding_box', sa.JSON(), nullable=True),
            sa.Column('extraction_confidence', sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_allergies_patient_id'), 'allergies', ['patient_id'], unique=False)
        op.create_index(op.f('ix_allergies_allergen'), 'allergies', ['allergen'], unique=False)

    # -------------------------------------------------------------------------
    # 2. Add Provenance & Terminology Columns to lab_results
    # -------------------------------------------------------------------------
    if is_offline or 'lab_results' in existing_tables:
        lab_cols = {col['name'] for col in inspector.get_columns('lab_results')} if inspector else set()
        if 'loinc_code' not in lab_cols:
            op.add_column('lab_results', sa.Column('loinc_code', sa.String(length=50), nullable=True))
        if 'canonical_name' not in lab_cols:
            op.add_column('lab_results', sa.Column('canonical_name', sa.String(length=255), nullable=True))
        if 'source_page_number' not in lab_cols:
            op.add_column('lab_results', sa.Column('source_page_number', sa.Integer(), nullable=True))
        if 'bounding_box' not in lab_cols:
            op.add_column('lab_results', sa.Column('bounding_box', sa.JSON(), nullable=True))
        if 'extraction_confidence' not in lab_cols:
            op.add_column('lab_results', sa.Column('extraction_confidence', sa.Float(), nullable=True))

    # -------------------------------------------------------------------------
    # 3. Add Provenance & Terminology Columns to medications
    # -------------------------------------------------------------------------
    if is_offline or 'medications' in existing_tables:
        med_cols = {col['name'] for col in inspector.get_columns('medications')} if inspector else set()
        if 'rxnorm_code' not in med_cols:
            op.add_column('medications', sa.Column('rxnorm_code', sa.String(length=50), nullable=True))
        if 'drug_class' not in med_cols:
            op.add_column('medications', sa.Column('drug_class', sa.String(length=100), nullable=True))
        if 'source_page_number' not in med_cols:
            op.add_column('medications', sa.Column('source_page_number', sa.Integer(), nullable=True))
        if 'bounding_box' not in med_cols:
            op.add_column('medications', sa.Column('bounding_box', sa.JSON(), nullable=True))
        if 'extraction_confidence' not in med_cols:
            op.add_column('medications', sa.Column('extraction_confidence', sa.Float(), nullable=True))

    # -------------------------------------------------------------------------
    # 4. Add Provenance Columns to diseases
    # -------------------------------------------------------------------------
    if is_offline or 'diseases' in existing_tables:
        dis_cols = {col['name'] for col in inspector.get_columns('diseases')} if inspector else set()
        if 'source_page_number' not in dis_cols:
            op.add_column('diseases', sa.Column('source_page_number', sa.Integer(), nullable=True))
        if 'bounding_box' not in dis_cols:
            op.add_column('diseases', sa.Column('bounding_box', sa.JSON(), nullable=True))
        if 'extraction_confidence' not in dis_cols:
            op.add_column('diseases', sa.Column('extraction_confidence', sa.Float(), nullable=True))

    # -------------------------------------------------------------------------
    # 5. Add Provenance Columns to extracted_entities
    # -------------------------------------------------------------------------
    if is_offline or 'extracted_entities' in existing_tables:
        ent_cols = {col['name'] for col in inspector.get_columns('extracted_entities')} if inspector else set()
        if 'source_page_number' not in ent_cols:
            op.add_column('extracted_entities', sa.Column('source_page_number', sa.Integer(), nullable=True))
        if 'bounding_box' not in ent_cols:
            op.add_column('extracted_entities', sa.Column('bounding_box', sa.JSON(), nullable=True))

    # -------------------------------------------------------------------------
    # 6. Data Migration: Populate allergies table from existing patient.known_allergies
    # -------------------------------------------------------------------------
    if not is_offline and 'patients' in existing_tables:
        results = conn.execute(sa.text("SELECT id, known_allergies FROM patients")).fetchall()
        for pat_id, known_raw in results:
            if known_raw is None:
                continue

            allergies_list = []
            if isinstance(known_raw, str):
                cleaned_raw = known_raw.strip()
                if not cleaned_raw:
                    continue
                try:
                    parsed = json.loads(cleaned_raw)
                    if isinstance(parsed, list):
                        allergies_list = parsed
                    elif isinstance(parsed, dict):
                        allergies_list = [str(v) for v in parsed.values() if v]
                    else:
                        allergies_list = [str(parsed)]
                except Exception:
                    # Handle comma-separated plain strings (e.g. "Penicillin, Sulfa Drugs")
                    if "," in cleaned_raw:
                        allergies_list = [item.strip() for item in cleaned_raw.split(",") if item.strip()]
                    else:
                        allergies_list = [cleaned_raw]
            elif isinstance(known_raw, list):
                allergies_list = known_raw
            elif isinstance(known_raw, dict):
                allergies_list = [str(v) for v in known_raw.values() if v]

            seen_allergens = set()
            for item in allergies_list:
                if not item:
                    continue
                item_str = str(item).strip()
                if not item_str:
                    continue

                allergen_name = item_str.split("(")[0].strip()
                if not allergen_name:
                    continue

                lower_name = allergen_name.lower()
                if lower_name in seen_allergens:
                    continue
                seen_allergens.add(lower_name)

                severity = "severe" if "severe" in item_str.lower() or "anaphylaxis" in item_str.lower() else "moderate"
                
                # Check if already migrated for this patient
                existing = conn.execute(
                    sa.text("SELECT id FROM allergies WHERE patient_id = :p AND LOWER(allergen) = :a"),
                    {"p": pat_id, "a": lower_name}
                ).first()
                
                if not existing:
                    drug_classes = None
                    cross_reactivities = None
                    if "penicillin" in lower_name:
                        drug_classes = json.dumps(["Penicillins", "Beta-lactam antibacterials"])
                        cross_reactivities = json.dumps(["amoxicillin", "ampicillin", "augmentin", "piperacillin"])
                    elif "sulfa" in lower_name:
                        drug_classes = json.dumps(["Sulfonamides"])
                        cross_reactivities = json.dumps(["bactrim", "septra", "sulfamethoxazole"])
                    elif "aspirin" in lower_name or "nsaid" in lower_name or "ibuprofen" in lower_name:
                        drug_classes = json.dumps(["Nonsteroidal Anti-inflammatory Drugs (NSAIDs)"])
                        cross_reactivities = json.dumps(["ibuprofen", "naproxen", "aspirin", "meloxicam", "celecoxib"])

                    # Note: extraction_confidence is explicitly None for historical migrated data
                    conn.execute(
                        sa.text(
                            "INSERT INTO allergies (id, patient_id, allergen, category, severity, reaction, "
                            "drug_classes, cross_reactivities, status, extraction_confidence, notes) "
                            "VALUES (:id, :p, :allergen, 'medication', :severity, :reaction, :classes, :cross, 'active', NULL, 'Migrated from historical patient known_allergies')"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "p": pat_id,
                            "allergen": allergen_name,
                            "severity": severity,
                            "reaction": item_str,
                            "classes": drug_classes,
                            "cross": cross_reactivities
                        }
                    )


def downgrade() -> None:
    is_offline = context.is_offline_mode()
    existing_tables = set()
    inspector = None

    if not is_offline:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_tables = set(inspector.get_table_names())

    # 1. Drop allergies table and indexes
    if is_offline or 'allergies' in existing_tables:
        indexes = {idx['name'] for idx in inspector.get_indexes('allergies')} if inspector else set()
        if is_offline or 'ix_allergies_allergen' in indexes:
            op.drop_index('ix_allergies_allergen', table_name='allergies')
        if is_offline or 'ix_allergies_patient_id' in indexes:
            op.drop_index('ix_allergies_patient_id', table_name='allergies')
        op.drop_table('allergies')

    # 2. Revert columns added to clinical entity tables
    if is_offline or 'lab_results' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('lab_results')} if inspector else {'loinc_code', 'canonical_name', 'source_page_number', 'bounding_box', 'extraction_confidence'}
        with op.batch_alter_table('lab_results') as batch_op:
            for col in ['loinc_code', 'canonical_name', 'source_page_number', 'bounding_box', 'extraction_confidence']:
                if col in cols:
                    batch_op.drop_column(col)

    if is_offline or 'medications' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('medications')} if inspector else {'rxnorm_code', 'drug_class', 'source_page_number', 'bounding_box', 'extraction_confidence'}
        with op.batch_alter_table('medications') as batch_op:
            for col in ['rxnorm_code', 'drug_class', 'source_page_number', 'bounding_box', 'extraction_confidence']:
                if col in cols:
                    batch_op.drop_column(col)

    if is_offline or 'diseases' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('diseases')} if inspector else {'source_page_number', 'bounding_box', 'extraction_confidence'}
        with op.batch_alter_table('diseases') as batch_op:
            for col in ['source_page_number', 'bounding_box', 'extraction_confidence']:
                if col in cols:
                    batch_op.drop_column(col)

    if is_offline or 'extracted_entities' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('extracted_entities')} if inspector else {'source_page_number', 'bounding_box'}
        with op.batch_alter_table('extracted_entities') as batch_op:
            for col in ['source_page_number', 'bounding_box']:
                if col in cols:
                    batch_op.drop_column(col)
