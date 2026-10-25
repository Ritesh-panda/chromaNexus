"""Add checksum deduplication and page count metadata to medical_reports

Revision ID: 004_add_checksum_and_page_metadata
Revises: 003_add_provenance_and_allergies
Create Date: 2026-10-18

"""
from typing import Sequence, Union
from alembic import op, context
import sqlalchemy as sa

revision: str = '004_add_checksum_and_page_metadata'
down_revision: Union[str, None] = '003_add_provenance_and_allergies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    is_offline = context.is_offline_mode()
    existing_tables = set()
    existing_cols = set()
    inspector = None

    if not is_offline:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_tables = set(inspector.get_table_names())
        if 'medical_reports' in existing_tables:
            existing_cols = {c['name'] for c in inspector.get_columns('medical_reports')}

    if is_offline or 'medical_reports' in existing_tables:
        with op.batch_alter_table('medical_reports') as batch_op:
            if 'checksum' not in existing_cols:
                batch_op.add_column(sa.Column('checksum', sa.String(length=64), nullable=True))
                batch_op.create_index('ix_medical_reports_checksum', ['checksum'], unique=False)
            if 'content_checksum' not in existing_cols:
                batch_op.add_column(sa.Column('content_checksum', sa.String(length=64), nullable=True))
            if 'page_count' not in existing_cols:
                batch_op.add_column(sa.Column('page_count', sa.Integer(), nullable=True, server_default='1'))


def downgrade() -> None:
    is_offline = context.is_offline_mode()
    existing_tables = set()
    existing_cols = set()
    inspector = None

    if not is_offline:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_tables = set(inspector.get_table_names())
        if 'medical_reports' in existing_tables:
            existing_cols = {c['name'] for c in inspector.get_columns('medical_reports')}

    if is_offline or 'medical_reports' in existing_tables:
        with op.batch_alter_table('medical_reports') as batch_op:
            if 'checksum' in existing_cols or is_offline:
                try:
                    batch_op.drop_index('ix_medical_reports_checksum')
                except Exception:
                    pass
                batch_op.drop_column('checksum')
            if 'content_checksum' in existing_cols or is_offline:
                batch_op.drop_column('content_checksum')
            if 'page_count' in existing_cols or is_offline:
                batch_op.drop_column('page_count')
