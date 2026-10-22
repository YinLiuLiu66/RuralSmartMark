"""multi product knowledge uniqueness and controller sessions

Revision ID: b2f4a1c9d7e3
Revises: c550608f545c
Create Date: 2026-10-22 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2f4a1c9d7e3"
down_revision: Union[str, None] = "c550608f545c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _indexes(table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    indexes = _indexes("knowledge_doc")
    if "ix_knowledge_doc_doc_key" in indexes:
        op.drop_index("ix_knowledge_doc_doc_key", table_name="knowledge_doc")
    if "uq_knowledge_doc_product_doc" not in indexes:
        op.create_index(
            "uq_knowledge_doc_product_doc",
            "knowledge_doc",
            ["product_id", "doc_key"],
            unique=True,
        )

    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "controller_session" not in tables:
        op.create_table(
            "controller_session",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("batch_id", sa.Integer(), nullable=True),
            sa.Column("draft_json", sa.JSON(), nullable=True),
            sa.Column("pending_action_json", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["product_id"], ["product_profile.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(["batch_id"], ["batch.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    session_indexes = _indexes("controller_session")
    if "ix_controller_session_product_id" not in session_indexes:
        op.create_index(
            "ix_controller_session_product_id",
            "controller_session",
            ["product_id"],
            unique=False,
        )
    if "ix_controller_session_batch_id" not in session_indexes:
        op.create_index(
            "ix_controller_session_batch_id",
            "controller_session",
            ["batch_id"],
            unique=False,
        )

    if "controller_message" not in tables:
        op.create_table(
            "controller_message",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("action_json", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["session_id"], ["controller_session.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    if "ix_controller_message_session_id" not in _indexes("controller_message"):
        op.create_index(
            "ix_controller_message_session_id",
            "controller_message",
            ["session_id"],
            unique=False,
        )


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "controller_message" in tables:
        if "ix_controller_message_session_id" in _indexes("controller_message"):
            op.drop_index(
                "ix_controller_message_session_id", table_name="controller_message"
            )
        op.drop_table("controller_message")
    if "controller_session" in tables:
        for name in (
            "ix_controller_session_batch_id",
            "ix_controller_session_product_id",
        ):
            if name in _indexes("controller_session"):
                op.drop_index(name, table_name="controller_session")
        op.drop_table("controller_session")

    indexes = _indexes("knowledge_doc")
    if "uq_knowledge_doc_product_doc" in indexes:
        op.drop_index("uq_knowledge_doc_product_doc", table_name="knowledge_doc")
    if "ix_knowledge_doc_doc_key" not in indexes:
        op.create_index(
            "ix_knowledge_doc_doc_key",
            "knowledge_doc",
            ["doc_key"],
            unique=True,
        )
