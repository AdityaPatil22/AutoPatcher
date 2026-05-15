"""Add per-user daily Gemini usage tracking columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("gemini_requests_today", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("gemini_requests_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "gemini_requests_date")
    op.drop_column("users", "gemini_requests_today")
