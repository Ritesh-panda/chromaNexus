"""Initial schema migration

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # 1. users
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('hashed_password', sa.String(length=255), nullable=False),
            sa.Column('role', sa.String(length=50), nullable=True, server_default='patient'),
            sa.Column('avatar_url', sa.String(length=500), nullable=True),
            sa.Column('phone_number', sa.String(length=50), nullable=True),
            sa.Column('preferences', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. patients
    if 'patients' not in existing_tables:
        op.create_table(
            'patients',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('date_of_birth', sa.String(length=50), nullable=True),
            sa.Column('gender', sa.String(length=20), nullable=True, server_default='other'),
            sa.Column('blood_group', sa.String(length=10), nullable=True, server_default='O+'),
            sa.Column('height_cm', sa.Float(), nullable=True, server_default='175.0'),
            sa.Column('weight_kg', sa.Float(), nullable=True, server_default='78.0'),
            sa.Column('primary_care_physician', sa.String(length=255), nullable=True),
            sa.Column('emergency_contact', sa.JSON(), nullable=True),
            sa.Column('insurance', sa.JSON(), nullable=True),
            sa.Column('known_allergies', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )

    # 3. medical_reports
    if 'medical_reports' not in existing_tables:
        op.create_table(
            'medical_reports',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('file_name', sa.String(length=255), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('file_type', sa.String(length=50), nullable=True, server_default='application/pdf'),
            sa.Column('category', sa.String(length=50), nullable=True, server_default='blood_report'),
            sa.Column('hospital_name', sa.String(length=255), nullable=False),
            sa.Column('doctor_name', sa.String(length=255), nullable=True),
            sa.Column('report_date', sa.String(length=50), nullable=False),
            sa.Column('upload_date', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True, server_default='completed'),
            sa.Column('confidence_score', sa.Float(), nullable=True, server_default='0.98'),
            sa.Column('raw_text', sa.Text(), nullable=True),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('file_url', sa.String(length=500), nullable=True),
            sa.Column('storage_path', sa.String(length=500), nullable=True),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_medical_reports_patient_id'), 'medical_reports', ['patient_id'], unique=False)

    # 4. diseases
    if 'diseases' not in existing_tables:
        op.create_table(
            'diseases',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('icd_code', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True, server_default='active'),
            sa.Column('diagnosed_date', sa.String(length=50), nullable=False),
            sa.Column('resolved_date', sa.String(length=50), nullable=True),
            sa.Column('treating_doctor', sa.String(length=255), nullable=True),
            sa.Column('source_report_id', sa.String(length=36), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_diseases_patient_id'), 'diseases', ['patient_id'], unique=False)

    # 5. medications
    if 'medications' not in existing_tables:
        op.create_table(
            'medications',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('dosage', sa.String(length=100), nullable=False),
            sa.Column('frequency', sa.String(length=100), nullable=False),
            sa.Column('route', sa.String(length=50), nullable=True, server_default='oral'),
            sa.Column('start_date', sa.String(length=50), nullable=False),
            sa.Column('end_date', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True, server_default='active'),
            sa.Column('prescribing_doctor', sa.String(length=255), nullable=True),
            sa.Column('indication', sa.String(length=255), nullable=True),
            sa.Column('source_report_id', sa.String(length=36), nullable=True),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_medications_patient_id'), 'medications', ['patient_id'], unique=False)

    # 6. lab_results
    if 'lab_results' not in existing_tables:
        op.create_table(
            'lab_results',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=False),
            sa.Column('test_name', sa.String(length=255), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=True, server_default='metabolic'),
            sa.Column('value', sa.String(length=100), nullable=False),
            sa.Column('unit', sa.String(length=50), nullable=False),
            sa.Column('reference_range', sa.String(length=100), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=True, server_default='normal'),
            sa.Column('test_date', sa.String(length=50), nullable=False),
            sa.Column('source_report_id', sa.String(length=36), nullable=True),
            sa.Column('hospital_name', sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_lab_results_patient_id'), 'lab_results', ['patient_id'], unique=False)

    # 7. timeline_events
    if 'timeline_events' not in existing_tables:
        op.create_table(
            'timeline_events',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=False),
            sa.Column('date', sa.String(length=50), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=50), nullable=True, server_default='medium'),
            sa.Column('doctor_name', sa.String(length=255), nullable=True),
            sa.Column('facility', sa.String(length=255), nullable=True),
            sa.Column('source_report_id', sa.String(length=36), nullable=True),
            sa.Column('source_report_title', sa.String(length=255), nullable=True),
            sa.Column('connected_entities', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_timeline_events_patient_id'), 'timeline_events', ['patient_id'], unique=False)
        op.create_index(op.f('ix_timeline_events_year'), 'timeline_events', ['year'], unique=False)

    # 8. chat_conversations
    if 'chat_conversations' not in existing_tables:
        op.create_table(
            'chat_conversations',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False, server_default='Medical Inquiry'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_chat_conversations_patient_id'), 'chat_conversations', ['patient_id'], unique=False)

    # 9. chat_messages
    if 'chat_messages' not in existing_tables:
        op.create_table(
            'chat_messages',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('conversation_id', sa.String(length=36), nullable=False),
            sa.Column('sender', sa.String(length=20), nullable=False),
            sa.Column('text', sa.Text(), nullable=False),
            sa.Column('timestamp', sa.String(length=50), nullable=False),
            sa.Column('reasoning_type', sa.String(length=50), nullable=True, server_default='fact'),
            sa.Column('citations', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_chat_messages_conversation_id'), 'chat_messages', ['conversation_id'], unique=False)

    # 10. doctor_summaries
    if 'doctor_summaries' not in existing_tables:
        op.create_table(
            'doctor_summaries',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=False),
            sa.Column('patient_name', sa.String(length=255), nullable=False),
            sa.Column('age', sa.Integer(), nullable=True, server_default='38'),
            sa.Column('gender', sa.String(length=50), nullable=True, server_default='Male (38M)'),
            sa.Column('generated_at', sa.DateTime(), nullable=True),
            sa.Column('summary_overview', sa.Text(), nullable=False),
            sa.Column('current_diseases', sa.JSON(), nullable=True),
            sa.Column('past_diseases', sa.JSON(), nullable=True),
            sa.Column('active_medications', sa.JSON(), nullable=True),
            sa.Column('known_allergies', sa.JSON(), nullable=True),
            sa.Column('abnormal_labs', sa.JSON(), nullable=True),
            sa.Column('risk_factors', sa.JSON(), nullable=True),
            sa.Column('recent_reports', sa.JSON(), nullable=True),
            sa.Column('timeline_highlights', sa.JSON(), nullable=True),
            sa.Column('share_token', sa.String(length=100), nullable=True),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('share_token')
        )
        op.create_index(op.f('ix_doctor_summaries_patient_id'), 'doctor_summaries', ['patient_id'], unique=False)
        op.create_index(op.f('ix_doctor_summaries_share_token'), 'doctor_summaries', ['share_token'], unique=True)

    # 11. extracted_entities
    if 'extracted_entities' not in existing_tables:
        op.create_table(
            'extracted_entities',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('report_id', sa.String(length=36), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('confidence', sa.Float(), nullable=True, server_default='0.95'),
            sa.Column('value', sa.String(length=100), nullable=True),
            sa.Column('unit', sa.String(length=50), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['report_id'], ['medical_reports.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_extracted_entities_report_id'), 'extracted_entities', ['report_id'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    tables_to_drop = [
        'extracted_entities',
        'doctor_summaries',
        'chat_messages',
        'chat_conversations',
        'timeline_events',
        'lab_results',
        'medications',
        'diseases',
        'medical_reports',
        'patients',
        'users',
    ]
    for table in tables_to_drop:
        if table in existing_tables:
            op.drop_table(table)
