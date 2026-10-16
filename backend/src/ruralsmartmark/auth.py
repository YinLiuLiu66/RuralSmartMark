"""JWT 双角色鉴权（decisions #4 / 03 文档 §4 权限矩阵）。

不注册流：账号由 seed 脚本预置（运营方/合作社各一）。
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ruralsmartmark.config import settings
from ruralsmartmark.db import get_session
from ruralsmartmark.models import User

_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)

ROLE_OPERATOR = "operator"
ROLE_COOP = "coop"


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def create_access_token(user: User) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已过期"
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效"
        ) from e


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Bearer 令牌 → 数据库用户；缺失/无效一律 401。"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效")

    user = await session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已停用"
        )
    return user


def require_role(*allowed: str):
    """角色门槛依赖：require_role(ROLE_OPERATOR) 限定运营方。"""

    async def _dependency(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限执行该操作"
            )
        return user

    return _dependency


async def authenticate(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """用户名密码校验；失败返回 None（不区分账号不存在与密码错误）。"""
    row = await session.scalar(select(User).where(User.username == username))
    if row is None or not row.is_active:
        return None
    if not verify_password(password, row.password_hash):
        return None
    return row
