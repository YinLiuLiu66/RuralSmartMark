"""演示数据 seed：预置双账号（decisions #4，无注册流程）。

运行：cd backend && uv run python -m ruralsmartmark.seed
幂等：账号已存在则跳过。
"""

import asyncio

from sqlalchemy import select

from ruralsmartmark.auth import hash_password
from ruralsmartmark.db import session_factory
from ruralsmartmark.models import User

DEMO_ACCOUNTS = [
    # (username, password, role) 演示值，进 git 无敏感信息
    ("operator", "operator-demo", "operator"),
    ("coop", "coop-demo", "coop"),
]


async def seed_users() -> None:
    async with session_factory() as session:
        for username, password, role in DEMO_ACCOUNTS:
            existing = await session.scalar(
                select(User).where(User.username == username)
            )
            if existing is not None:
                print(f"skip: {username} 已存在")
                continue
            session.add(
                User(
                    username=username, password_hash=hash_password(password), role=role
                )
            )
            print(f"seed: {username} ({role})")
        await session.commit()


def main() -> None:
    asyncio.run(seed_users())


if __name__ == "__main__":
    main()
