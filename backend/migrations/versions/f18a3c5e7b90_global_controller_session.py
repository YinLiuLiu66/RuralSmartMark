"""global single controller session

Revision ID: f18a3c5e7b90
Revises: e7b2c9d1a4f6
Create Date: 2026-11-13

总控改为全局唯一会话（decisions #92）：旧会话按批次创建，语义不再成立，
直接清空会话与消息，并把部分唯一索引换成无条件单行唯一索引。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f18a3c5e7b90"
down_revision: str | None = "e7b2c9d1a4f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 先删消息再删会话，不依赖 SQLite 外键级联。
    op.execute("DELETE FROM controller_message")
    op.execute("DELETE FROM controller_session")
    op.execute("DROP INDEX IF EXISTS uq_controller_session_blank")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_controller_session_single
        ON controller_session ((1))
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_controller_session_single")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_controller_session_blank
        ON controller_session ((1))
        WHERE product_id IS NULL AND batch_id IS NULL
        """
    )
