"""用户与鉴权表（M1-c JWT 双角色）。

03 文档的 13 张业务表之外追加的演示账号载体（M1-c 拍板）。
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ruralsmartmark.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    # argon2 哈希
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # operator（运营方）| coop（合作社）
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
