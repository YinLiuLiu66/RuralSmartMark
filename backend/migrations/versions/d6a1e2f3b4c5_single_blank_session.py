"""single blank controller session

Revision ID: d6a1e2f3b4c5
Revises: b2f4a1c9d7e3
Create Date: 2026-10-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d6a1e2f3b4c5"
down_revision: str | None = "b2f4a1c9d7e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 旧版本下 StrictMode 双请求可能留下多个未建档空白会话，保留最新一条。
    op.execute(
        """
        DELETE FROM controller_message
        WHERE session_id IN (
            SELECT id FROM controller_session
            WHERE product_id IS NULL AND batch_id IS NULL
              AND id <> (
                  SELECT MAX(id) FROM controller_session
                  WHERE product_id IS NULL AND batch_id IS NULL
              )
        )
        """
    )
    op.execute(
        """
        DELETE FROM controller_session
        WHERE product_id IS NULL AND batch_id IS NULL
          AND id <> (
              SELECT MAX(id) FROM controller_session
              WHERE product_id IS NULL AND batch_id IS NULL
          )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_controller_session_blank
        ON controller_session ((1))
        WHERE product_id IS NULL AND batch_id IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_controller_session_blank")
