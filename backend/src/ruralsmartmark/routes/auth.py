"""鉴权路由：POST /api/auth/token（03 文档 §3.2 / §4）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ruralsmartmark.auth import authenticate, create_access_token
from ruralsmartmark.db import get_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """用户名密码换 JWT；表单字段为 username / password。"""
    user = await authenticate(session, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(user), role=user.role, username=user.username
    )
