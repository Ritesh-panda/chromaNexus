"""Add audit_logs table for security and compliance audit trails

Revision ID: 005_add_audit_logs
Revises: 004_add_checksum_and_page_metadata
Create Date: 2026-10-24

"""
from typing import Sequence, Union
from alembic import op, context
import sqlalchemy as sa

revision: str = '005_add_audit_logs'
down_revision: Union[str, None] = '004_add_checksum_and_page_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    is_offline = context.is_offline_mode()
    existing_tables = set()

    if not is_offline:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_tables = set(inspector.get_table_names())

    if is_offline or 'audit_logs' not in existing_tables:
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('actor_id', sa.String(length=36), nullable=True),
            sa.Column('patient_id', sa.String(length=36), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('outcome', sa.String(length=50), nullable=False, server_default='SUCCESS'),
            sa.Column('resource_type', sa.String(length=100), nullable=True),
            sa.Column('resource_id', sa.String(length=100), nullable=True),
            sa.Column('correlation_id', sa.String(length=100), nullable=True),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(length=50), nullable=True)
        )
        op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'], unique=False)
        op.create_index('ix_audit_logs_actor_id', 'audit_logs', ['actor_id'], unique=False)
        op.create_index('ix_audit_logs_patient_id', 'audit_logs', ['patient_id'], unique=False)
        op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)


def downgrade() -> None:
    is_offline = context.is_offline_mode()
    existing_tables = set()

    if not is_offline:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_tables = set(inspector.get_table_names())

    if is_offline or 'audit_logs' in existing_tables:
        op.drop_table('audit_logs')
