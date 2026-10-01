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
    # Tables are auto-managed by SQLAlchemy metadata create_all during app startup
    pass


def downgrade() -> None:
    pass
