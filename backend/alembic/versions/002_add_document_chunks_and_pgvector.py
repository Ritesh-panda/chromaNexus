"""Add document chunks and pgvector extension support

Revision ID: 002_add_document_chunks
Revises: 001_initial
Create Date: 2026-10-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

revision: str = '002_add_document_chunks'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # 1. Enable pgvector extension if running on PostgreSQL
    if dialect == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Handle document_chunks table
    if 'document_chunks' not in existing_tables:
        if dialect == "postgresql" and Vector is not None:
            embedding_type = Vector(384)
        else:
            embedding_type = sa.JSON()

        op.create_table(
            'document_chunks',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('document_id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=True),
            sa.Column('chunk_id', sa.String(length=100), nullable=False),
            sa.Column('chunk_index', sa.Integer(), nullable=False),
            sa.Column('page_number', sa.Integer(), nullable=False, server_default="1"),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('embedding', embedding_type, nullable=True),
            sa.Column('chunk_metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['document_id'], ['medical_reports.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('chunk_id')
        )
        op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
        op.create_index(op.f('ix_document_chunks_patient_id'), 'document_chunks', ['patient_id'], unique=False)
        op.create_index(op.f('ix_document_chunks_chunk_id'), 'document_chunks', ['chunk_id'], unique=True)

    else:
        # Table exists. Migrate embedding column to vector(384) if on PostgreSQL
        if dialect == "postgresql":
            columns = {col['name']: col for col in inspector.get_columns('document_chunks')}
            emb_col = columns.get('embedding')
            if emb_col:
                col_type_str = str(emb_col['type']).lower()
                if 'vector' not in col_type_str:
                    op.execute(
                        "ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(384) "
                        "USING CASE WHEN embedding IS NULL THEN NULL ELSE embedding::text::vector(384) END;"
                    )

        # Ensure indexes exist
        indexes = {idx['name'] for idx in inspector.get_indexes('document_chunks')}
        if 'ix_document_chunks_document_id' not in indexes:
            op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
        if 'ix_document_chunks_patient_id' not in indexes:
            op.create_index(op.f('ix_document_chunks_patient_id'), 'document_chunks', ['patient_id'], unique=False)
        if 'ix_document_chunks_chunk_id' not in indexes:
            op.create_index(op.f('ix_document_chunks_chunk_id'), 'document_chunks', ['chunk_id'], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if 'document_chunks' in existing_tables:
        indexes = {idx['name'] for idx in inspector.get_indexes('document_chunks')}
        if 'ix_document_chunks_chunk_id' in indexes:
            op.drop_index(op.f('ix_document_chunks_chunk_id'), table_name='document_chunks')
        if 'ix_document_chunks_patient_id' in indexes:
            op.drop_index(op.f('ix_document_chunks_patient_id'), table_name='document_chunks')
        if 'ix_document_chunks_document_id' in indexes:
            op.drop_index(op.f('ix_document_chunks_document_id'), table_name='document_chunks')
        op.drop_table('document_chunks')
