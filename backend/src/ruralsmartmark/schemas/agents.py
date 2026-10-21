"""Agent 任务与产出物的请求/响应模型（03 §3.2）。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentTaskCreate(BaseModel):
    agent_type: Literal["story", "copy"]
    product_sku_id: int | None = None


class AgentArtifactUpdate(BaseModel):
    content: str | None = Field(default=None, max_length=20000)
    status: Literal["polished", "final"] | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> "AgentArtifactUpdate":
        if self.content is None and self.status is None:
            raise ValueError("content 与 status 至少提供一个")
        return self


class AgentArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    content: str | None
    asset_url: str | None
    status: str
    updated_at: datetime


class AgentTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_type: str
    status: str
    product_sku_id: int | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    artifacts: list[AgentArtifactOut] = []
