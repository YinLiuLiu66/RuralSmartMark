"""controller session summary_json

Revision ID: e7b2c9d1a4f6
Revises: d6a1e2f3b4c5
Create Date: 2026-10-26

"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7b2c9d1a4f6"
down_revision: Union[str, None] = "d6a1e2f3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "controller_session",
        sa.Column("summary_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("controller_session", "summary_json")
